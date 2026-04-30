#!/usr/bin/env python3
"""Write one XDATA byte through the guarded currentboot response hook.

This assumes the `xdata-cdb-rw` hook is installed and the drive is in
currentboot. The hook only writes when CDB[10:11] are `a5 5a`; otherwise it
behaves as a read-only XDATA hook.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_SG_RAW = "/usr/bin/sg_raw"


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def parse_byte(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("value must be 0..0xff")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--value", required=True, type=parse_byte)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--request-len", type=int, default=176)
    parser.add_argument("--response-offset", type=parse_int, default=0x20)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 <= args.address <= 0xFFFF:
        raise ValueError(f"XDATA address out of 16-bit range: 0x{args.address:x}")
    base = args.address & ~0x3F
    selector = args.address & 0x3F
    cdb = [
        0x12,
        0x00,
        0x00,
        0x00,
        0xF0,
        0x40 | selector,
        0x00,
        (base >> 8) & 0xFF,
        base & 0xFF,
        args.value,
        0xA5,
        0x5A,
    ]
    proc = subprocess.run(
        [
            args.sg_raw,
            "--cmdset=1",
            "-b",
            "--timeout",
            str(args.timeout),
            "--request",
            str(args.request_len),
            args.device,
            *[f"{byte:02x}" for byte in cdb],
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    record: dict[str, Any] = {
        "device": args.device,
        "address": args.address,
        "base": base,
        "selector": selector,
        "value": args.value,
        "cdb": cdb,
        "returncode": proc.returncode,
        "stdout_len": len(proc.stdout),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }
    if proc.returncode != 0:
        raise RuntimeError(record["stderr"].strip())
    if len(proc.stdout) <= args.response_offset:
        raise RuntimeError(f"short INQUIRY response: got {len(proc.stdout)} bytes")
    readback = proc.stdout[args.response_offset]
    record["readback"] = readback
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True))
    return 0 if readback == args.value else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
