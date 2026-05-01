#!/usr/bin/env python3
"""Capture normal work-window snapshots after GET CONFIG field variants.

This is a focused read-only/no-data-out probe for the normal-mode controller
bridge.  The ordinary GET CONFIGURATION CDB is:

    46 RT SF_hi SF_lo 00 00 00 AL_hi AL_lo 00

Earlier work-window captures tie the suspicious bridge path to packet-shadow
bytes around xdata[0x8a4d] and xdata[0x8a4e], which correspond to CDB bytes 4
and 5 in the START STOP anchor.  Those bytes are reserved for GET
CONFIGURATION, so this probe varies them cautiously and captures the public
work window after each command.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from capture_liteon_normal_work_window_stimuli import (
    capture_window,
    cdb_text,
    run_sg_raw,
    sha256_hex,
)


DEFAULT_SG_RAW = shutil.which("sg_raw") or "/usr/bin/sg_raw"


@dataclass(frozen=True)
class Variant:
    name: str
    cdb: tuple[int, ...]
    request_len: int = 0xFC


def get_config_cdb(
    *,
    rt: int = 0x02,
    start_feature: int = 0x0000,
    reserved4: int = 0x00,
    reserved5: int = 0x00,
    reserved6: int = 0x00,
    allocation: int = 0x00FC,
    control: int = 0x00,
) -> tuple[int, ...]:
    return (
        0x46,
        rt & 0x03,
        (start_feature >> 8) & 0xFF,
        start_feature & 0xFF,
        reserved4 & 0xFF,
        reserved5 & 0xFF,
        reserved6 & 0xFF,
        (allocation >> 8) & 0xFF,
        allocation & 0xFF,
        control & 0xFF,
    )


VARIANTS: tuple[Variant, ...] = (
    Variant("std-current-sf0000-len00fc", get_config_cdb()),
    Variant("std-current-sf0020-len00fc", get_config_cdb(start_feature=0x0020), request_len=0x18),
    Variant("r4-01-current-sf0000", get_config_cdb(reserved4=0x01)),
    Variant("r4-fe-current-sf0000", get_config_cdb(reserved4=0xFE)),
    Variant("r5-01-current-sf0000", get_config_cdb(reserved5=0x01)),
    Variant("r5-0f-current-sf0000", get_config_cdb(reserved5=0x0F)),
    Variant("r5-f0-current-sf0000", get_config_cdb(reserved5=0xF0)),
    Variant("r6-01-current-sf0000", get_config_cdb(reserved6=0x01)),
    Variant("ctrl-01-current-sf0000", get_config_cdb(control=0x01)),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=4)
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--mode", type=lambda x: int(x, 0), default=0x01)
    parser.add_argument("--id", type=lambda x: int(x, 0), default=0x01, dest="buffer_id")
    parser.add_argument("--offset", type=lambda x: int(x, 0), default=0x070000)
    parser.add_argument("--length", type=lambda x: int(x, 0), default=0x10000)
    parser.add_argument("--chunk-size", type=lambda x: int(x, 0), default=0x400)
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--chunk-delay", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected = [
        variant
        for variant in VARIANTS
        if not args.include or any(term in variant.name for term in args.include)
    ]
    if not selected:
        raise SystemExit(f"no variants matched --include filters: {args.include!r}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "window": {
            "mode": args.mode,
            "id": args.buffer_id,
            "offset": args.offset,
            "length": args.length,
            "chunk_size": args.chunk_size,
        },
        "cycles": args.cycles,
        "variant_defs": [
            {
                "name": variant.name,
                "cdb": cdb_text(variant.cdb),
                "request_len": variant.request_len,
            }
            for variant in selected
        ],
        "variants": [],
        "captures": [],
    }

    index = 0
    for cycle in range(args.cycles):
        baseline = f"{index:02d}-cycle{cycle:02d}-baseline-no-stimulus"
        baseline_path = args.out_dir / f"{baseline}.window.bin"
        baseline_record = capture_window(args, baseline_path)
        baseline_record["stimulus"] = "baseline-no-stimulus"
        baseline_record["cycle"] = cycle
        report["captures"].append(baseline_record)
        index += 1
        time.sleep(args.delay)

        for variant in selected:
            response, record = run_sg_raw(
                sg_raw=args.sg_raw,
                device=args.device,
                cdb=variant.cdb,
                request_len=variant.request_len,
                timeout=args.timeout,
                process_timeout=args.process_timeout,
            )
            response_path = args.out_dir / f"{index:02d}-cycle{cycle:02d}-{variant.name}.response.bin"
            response_path.write_bytes(response)
            record.update(
                {
                    "stimulus": variant.name,
                    "cycle": cycle,
                    "response_path": str(response_path),
                    "response_sha256": sha256_hex(response) if response else None,
                    "cdb_text": cdb_text(variant.cdb),
                }
            )
            report["variants"].append(record)
            if args.delay:
                time.sleep(args.delay)

            window_path = args.out_dir / f"{index:02d}-cycle{cycle:02d}-{variant.name}.window.bin"
            window_record = capture_window(args, window_path)
            window_record["stimulus"] = variant.name
            window_record["cycle"] = cycle
            window_record["preceding_response"] = record
            report["captures"].append(window_record)
            index += 1
            if args.delay:
                time.sleep(args.delay)

    (args.out_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
