#!/usr/bin/env python3
"""Read XDATA bytes through the currentboot response hook.

This script assumes the drive is already in currentboot and has an
`xdata-cdb-address` response hook installed. It sends read-only INQUIRY CDBs
whose spare bytes are interpreted by the hook as:

    CDB[5] low six bits: byte offset within a 64-byte window
    CDB[7:8]:            16-bit big-endian XDATA base address

The hook writes the selected XDATA byte into response byte 0x20.
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


def ascii_preview(data: bytes) -> str:
    return "".join(chr(byte) if 0x20 <= byte < 0x7F else "." for byte in data)


def read_one(
    *,
    sg_raw: str,
    device: str,
    address: int,
    read_magic: tuple[int, int] | None,
    timeout: int,
    request_len: int,
    response_offset: int,
) -> tuple[int, dict[str, Any]]:
    if not 0 <= address <= 0xFFFF:
        raise ValueError(f"XDATA address out of 16-bit range: 0x{address:x}")
    base = address & ~0x3F
    selector = address & 0x3F
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
        0x00,
        read_magic[0] if read_magic else 0x00,
        read_magic[1] if read_magic else 0x00,
    ]
    proc = subprocess.run(
        [
            sg_raw,
            "--cmdset=1",
            "-b",
            "--timeout",
            str(timeout),
            "--request",
            str(request_len),
            device,
            *[f"{byte:02x}" for byte in cdb],
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    record: dict[str, Any] = {
        "address": address,
        "base": base,
        "selector": selector,
        "read_magic": list(read_magic) if read_magic else None,
        "cdb": cdb,
        "returncode": proc.returncode,
        "stdout_len": len(proc.stdout),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }
    if proc.returncode != 0:
        raise RuntimeError(f"sg_raw failed at 0x{address:04x}: {record['stderr'].strip()}")
    if len(proc.stdout) <= response_offset:
        raise RuntimeError(
            f"short INQUIRY response at 0x{address:04x}: got {len(proc.stdout)} bytes"
        )
    value = proc.stdout[response_offset]
    record["value"] = value
    return value, record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--length", required=True, type=parse_int)
    parser.add_argument("--out", type=Path, help="write raw bytes to this path")
    parser.add_argument("--json-out", type=Path, help="write per-byte metadata to this path")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--request-len", type=int, default=176)
    parser.add_argument("--response-offset", type=parse_int, default=0x20)
    parser.add_argument("--progress-every", type=int, default=256)
    parser.add_argument(
        "--read-magic",
        choices=("none", "5aa5"),
        default="none",
        help=(
            "set CDB[10:11] read magic for combined gateway/XDATA hooks. "
            "The rebuilt gateway-cdb-bulk-xdata-rw-v2 read branch hung live "
            "on 2026-05-01; use only with the explicit hazard acknowledgement."
        ),
    )
    parser.add_argument(
        "--allow-known-hanging-combined-read",
        action="store_true",
        help="allow --read-magic 5aa5 despite the live timeout observed for the combined RW hook",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.length < 1:
        raise ValueError("--length must be at least 1")
    if args.address + args.length > 0x10000:
        raise ValueError("requested range crosses the 16-bit XDATA address space")
    if args.read_magic == "5aa5" and not args.allow_known_hanging_combined_read:
        raise SystemExit(
            "--read-magic 5aa5 is guarded because the combined RW hook's XDATA-read "
            "branch timed out live; pass --allow-known-hanging-combined-read only "
            "when intentionally reproducing that path"
        )
    read_magic = (0x5A, 0xA5) if args.read_magic == "5aa5" else None
    data = bytearray()
    records: list[dict[str, Any]] = []
    for offset in range(args.length):
        address = args.address + offset
        value, record = read_one(
            sg_raw=args.sg_raw,
            device=args.device,
            address=address,
            read_magic=read_magic,
            timeout=args.timeout,
            request_len=args.request_len,
            response_offset=args.response_offset,
        )
        data.append(value)
        records.append(record)
        if args.progress_every and (offset + 1) % args.progress_every == 0:
            print(f"read {offset + 1}/{args.length} bytes through 0x{address:04x}", file=sys.stderr)

    blob = bytes(data)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(blob)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(
                {
                    "device": args.device,
                    "address": args.address,
                    "length": args.length,
                    "bytes_hex": blob.hex(),
                    "ascii_preview": ascii_preview(blob),
                    "records": records,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    print(f"bytes_hex={blob.hex()}")
    print(f"ascii={ascii_preview(blob)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
