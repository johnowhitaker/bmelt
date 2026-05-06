#!/usr/bin/env python3
"""Capture the READ BUFFER windows used to test the materialized bridge patch.

This script is read-only. It sends INQUIRY through sg_inq when available and
READ BUFFER(10) mode=1/id=01 requests for the windows relevant to the
post-materializer runtime-bridge-clamp07 candidate:

    0x070000  ordinary public work-window baseline
    0x074000  old marker-check window
    0x0f0000  high-offset clamp proof window

The intended use is to run it before a candidate, after cold boot with the
candidate installed, and after the restore candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from read_liteon_read_buffer_bulk import DEFAULT_SG_RAW, parse_int, run_read


DEFAULT_OFFSETS = [0x070000, 0x074000, 0x0F0000]


def run_identity(device: str) -> dict[str, Any]:
    sg_inq = shutil.which("sg_inq")
    if not sg_inq:
        return {"tool": "sg_inq", "available": False}
    proc = subprocess.run(
        [sg_inq, device],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "tool": sg_inq,
        "available": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", "replace"),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }


def parse_offsets(values: list[str]) -> list[int]:
    if not values:
        return DEFAULT_OFFSETS
    return [parse_int(value) for value in values]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--label", default="bridge-clamp-probe")
    parser.add_argument("--offset", action="append", default=[], help="repeatable; default known proof offsets")
    parser.add_argument("--length", type=parse_int, default=0x80)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.15)
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repeat < 1:
        raise ValueError("--repeat must be >= 1")
    if args.length < 1:
        raise ValueError("--length must be >= 1")

    offsets = parse_offsets(args.offset)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "label": args.label,
        "device": args.device,
        "identity": run_identity(args.device),
        "mode": 0x01,
        "id": 0x01,
        "length": args.length,
        "offsets": offsets,
        "repeat": args.repeat,
        "captures": [],
    }

    for repeat in range(args.repeat):
        for offset in offsets:
            data, record = run_read(
                sg_raw=args.sg_raw,
                device=args.device,
                mode=0x01,
                buffer_id=0x01,
                offset=offset,
                length=args.length,
                timeout=args.timeout,
                process_timeout=args.process_timeout,
            )
            name = f"{args.label}-r{repeat:02d}-id01-off{offset:06x}.bin"
            path = args.out_dir / name
            if record.get("returncode") == 0 and not record.get("timed_out") and len(data) == args.length:
                path.write_bytes(data)
            capture = {
                "repeat": repeat,
                "offset": offset,
                "path": str(path),
                "length": len(data),
                "sha256": hashlib.sha256(data).hexdigest() if data else None,
                "first64_hex": data[:64].hex(),
                "record": record,
            }
            report["captures"].append(capture)
            time.sleep(args.delay)

    summary_path = args.out_dir / f"{args.label}.json"
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    compact = {}
    for capture in report["captures"]:
        key = f"0x{capture['offset']:06x}"
        compact.setdefault(key, []).append(capture["sha256"])
    print(json.dumps({"summary": str(summary_path), "hashes": compact}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
