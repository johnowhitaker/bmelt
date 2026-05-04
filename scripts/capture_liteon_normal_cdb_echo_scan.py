#!/usr/bin/env python3
"""Probe whether normal-mode work-window tiles expose host CDB bytes.

This sends only no-data-out/read-style SCSI/MMC commands and captures the
normal READ BUFFER work window after each command.  The variants put distinctive
byte patterns into standard command parameter/reserved fields, then the script
searches the response and work-window bytes for those patterns.

The goal is a slow normal-mode communication primitive: if a host-chosen CDB
field reliably appears in the public work window, the host can influence a
drive-internal shadow byte and read it back without firmware writes.
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
class EchoVariant:
    name: str
    cdb: tuple[int, ...]
    request_len: int
    probes: tuple[bytes, ...]
    notes: str = ""


def get_config_variant(name: str, r4: int, r5: int, r6: int) -> EchoVariant:
    cdb = (0x46, 0x02, 0x00, 0x00, r4, r5, r6, 0x00, 0xFC, 0x00)
    return EchoVariant(
        name=name,
        cdb=cdb,
        request_len=0xFC,
        probes=(bytes((r4, r5, r6)), bytes((0x46, 0x02, r4, r5, r6))),
        notes="GET CONFIGURATION current, reserved bytes 4..6 varied",
    )


def mode_sense_variant(name: str, byte2: int, subpage: int, control: int) -> EchoVariant:
    cdb = (0x5A, 0x00, byte2, subpage, 0x00, 0x00, 0x00, 0x00, 0xFC, control)
    return EchoVariant(
        name=name,
        cdb=cdb,
        request_len=0xFC,
        probes=(bytes((byte2, subpage, control)), bytes((0x5A, byte2, subpage))),
        notes="MODE SENSE(10), page/subpage/control varied",
    )


def read_toc_variant(name: str, fmt: int, track: int, control: int) -> EchoVariant:
    cdb = (0x43, 0x00, fmt, 0x00, 0x00, 0x00, track, 0x00, 0xFC, control)
    return EchoVariant(
        name=name,
        cdb=cdb,
        request_len=0xFC,
        probes=(bytes((fmt, track, control)), bytes((0x43, fmt, track))),
        notes="READ TOC/PMA/ATIP, format/track/control varied",
    )


VARIANTS: tuple[EchoVariant, ...] = (
    get_config_variant("getcfg-r456-a55ac3", 0xA5, 0x5A, 0xC3),
    get_config_variant("getcfg-r456-3cc35a", 0x3C, 0xC3, 0x5A),
    get_config_variant("getcfg-r456-5aa53c", 0x5A, 0xA5, 0x3C),
    mode_sense_variant("modesense-page-a5-sub5a-ctrlc3", 0xA5, 0x5A, 0xC3),
    mode_sense_variant("modesense-page-3c-subc3-ctrl5a", 0x3C, 0xC3, 0x5A),
    read_toc_variant("readtoc-fmt05-tracka5-ctrlc3", 0x05, 0xA5, 0xC3),
    read_toc_variant("readtoc-fmt0a-track5a-ctrl3c", 0x0A, 0x5A, 0x3C),
)


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def search_blob(data: bytes, probes: tuple[bytes, ...]) -> list[dict[str, Any]]:
    hits = []
    for probe in probes:
        offsets = find_all(data, probe)
        if offsets:
            hits.append({"hex": probe.hex(), "offsets": offsets[:16], "count": len(offsets)})
    return hits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=3)
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
    variants = [
        variant
        for variant in VARIANTS
        if not args.include or any(term in variant.name for term in args.include)
    ]
    if not variants:
        raise SystemExit(f"no variants matched --include filters: {args.include!r}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "cycles": args.cycles,
        "window": {
            "mode": args.mode,
            "id": args.buffer_id,
            "offset": args.offset,
            "length": args.length,
            "chunk_size": args.chunk_size,
        },
        "variants": [
            {
                "name": variant.name,
                "cdb": cdb_text(variant.cdb),
                "request_len": variant.request_len,
                "probes": [probe.hex() for probe in variant.probes],
                "notes": variant.notes,
            }
            for variant in variants
        ],
        "runs": [],
    }

    index = 0
    for cycle in range(args.cycles):
        for variant in variants:
            response, command_record = run_sg_raw(
                sg_raw=args.sg_raw,
                device=args.device,
                cdb=variant.cdb,
                request_len=variant.request_len,
                timeout=args.timeout,
                process_timeout=args.process_timeout,
            )
            response_path = args.out_dir / f"{index:02d}-cycle{cycle:02d}-{variant.name}.response.bin"
            response_path.write_bytes(response)
            if args.delay:
                time.sleep(args.delay)

            window_path = args.out_dir / f"{index:02d}-cycle{cycle:02d}-{variant.name}.window.bin"
            window_record = capture_window(args, window_path)
            window = window_path.read_bytes()
            item = {
                "index": index,
                "cycle": cycle,
                "name": variant.name,
                "cdb": cdb_text(variant.cdb),
                "request_len": variant.request_len,
                "command": command_record
                | {
                    "response_path": str(response_path),
                    "response_sha256": sha256_hex(response) if response else None,
                    "response_hits": search_blob(response, variant.probes),
                },
                "window": window_record
                | {
                    "window_hits": search_blob(window, variant.probes),
                },
            }
            report["runs"].append(item)
            (args.out_dir / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(
                f"{index:02d} {variant.name}: rc={command_record['returncode']} "
                f"good={command_record['good']} response_hits={len(item['command']['response_hits'])} "
                f"window_hits={len(item['window']['window_hits'])}",
                flush=True,
            )
            index += 1
            if args.delay:
                time.sleep(args.delay)

    (args.out_dir / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
