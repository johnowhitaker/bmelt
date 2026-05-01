#!/usr/bin/env python3
"""Write one controller-gateway byte through the guarded currentboot hook.

This assumes the `gateway-cdb-rw` currentboot response hook is installed. The
v2 hook writes only when CDB[10] is `0x5a`; otherwise the same CDB shape is a
one-byte gateway read. The hook returns the readback byte at response byte
0x20.

By default the tool keeps CDB[5] at the canonical EXTRAINQ value `0x40` and
puts the full 24-bit address in CDB[7:9]. The older CDB[5] selector form is
still available for reproducing old logs. Both forms smoke-tested cleanly on
2026-05-01 when the hook was actually installed; earlier `0x30` readbacks were
caused by testing after canonical recovery had wiped the hook.
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
    parser.add_argument(
        "--use-cdb5-selector",
        action="store_true",
        help="legacy mode: put address low six bits in CDB[5] instead of CDB[9]",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not 0 <= args.address <= 0xFFFFFF:
        raise ValueError(f"controller address out of 24-bit range: 0x{args.address:x}")
    if args.use_cdb5_selector:
        cdb_address = args.address & ~0x3F
        selector = args.address & 0x3F
    else:
        cdb_address = args.address
        selector = 0
    cdb = [
        0x12,
        0x00,
        0x00,
        0x00,
        0xF0,
        0x40 | selector,
        0x00,
        (cdb_address >> 16) & 0xFF,
        (cdb_address >> 8) & 0xFF,
        cdb_address & 0xFF,
        0x5A,
        args.value,
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
        "cdb_address": cdb_address,
        "selector": selector,
        "use_cdb5_selector": args.use_cdb5_selector,
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
