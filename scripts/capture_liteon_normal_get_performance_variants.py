#!/usr/bin/env python3
"""Capture normal work-window snapshots after GET PERFORMANCE variants.

This stays in read-only/no-data-out territory.  Each probe sends a SCSI/MMC
GET PERFORMANCE command, saves the response, then captures the public normal
runtime work window:

    READ BUFFER mode=1 id=01 offset=0x070000

The goal is to harvest additional normal-runtime overlay tiles, not to control
mechanics or modify device state.
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
    byte1: int = 0x00
    start_lba: int = 0x00000000
    max_descriptors: int = 0x0010
    data_type: int = 0x00
    request_len: int = 0xFC

    @property
    def cdb(self) -> tuple[int, ...]:
        return (
            0xAC,
            self.byte1 & 0xFF,
            (self.start_lba >> 24) & 0xFF,
            (self.start_lba >> 16) & 0xFF,
            (self.start_lba >> 8) & 0xFF,
            self.start_lba & 0xFF,
            0x00,
            0x00,
            (self.max_descriptors >> 8) & 0xFF,
            self.max_descriptors & 0xFF,
            self.data_type & 0xFF,
            0x00,
        )


VARIANTS: tuple[Variant, ...] = (
    Variant("gp-type00-max0001", data_type=0x00, max_descriptors=0x0001),
    Variant("gp-type00-max0010", data_type=0x00, max_descriptors=0x0010),
    Variant("gp-type00-max00ff", data_type=0x00, max_descriptors=0x00FF),
    Variant("gp-type01-max0010", data_type=0x01),
    Variant("gp-type02-max0010", data_type=0x02),
    Variant("gp-type03-max0010", data_type=0x03),
    Variant("gp-type04-max0010", data_type=0x04),
    Variant("gp-type05-max0010", data_type=0x05),
    Variant("gp-type10-max0010", data_type=0x10),
    Variant("gp-type11-max0010", data_type=0x11),
    Variant("gp-type20-max0010", data_type=0x20),
    Variant("gp-typeff-max0010", data_type=0xFF),
    Variant("gp-byte1-01-type00", byte1=0x01, data_type=0x00),
    Variant("gp-byte1-02-type00", byte1=0x02, data_type=0x00),
    Variant("gp-byte1-03-type00", byte1=0x03, data_type=0x00),
    Variant("gp-byte1-01-type03", byte1=0x01, data_type=0x03),
    Variant("gp-startlba1-type00", start_lba=0x00000001, data_type=0x00),
    Variant("gp-startlba1-type03", start_lba=0x00000001, data_type=0x03),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=2)
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
    if args.cycles < 1:
        raise SystemExit("--cycles must be >= 1")
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
