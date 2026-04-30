#!/usr/bin/env python3
"""Read controller-gateway bytes through the bulk currentboot response hook.

This assumes the drive is already in currentboot and has a `gateway-cdb-bulk`
response hook installed. Each INQUIRY CDB asks the hook to copy a contiguous
controller-gateway chunk into response bytes starting at offset 0x20.
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


def read_chunk(
    *,
    sg_raw: str,
    device: str,
    address: int,
    length: int,
    timeout: int,
    request_len: int,
    response_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError(f"controller address out of 24-bit range: 0x{address:x}")
    if not 1 <= length <= 0xFF:
        raise ValueError("chunk length must be 1..255")
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
        (base >> 16) & 0xFF,
        (base >> 8) & 0xFF,
        base & 0xFF,
        0x00,
        0x00,
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
        "length": length,
        "cdb": cdb,
        "returncode": proc.returncode,
        "stdout_len": len(proc.stdout),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }
    if proc.returncode != 0:
        raise RuntimeError(f"sg_raw failed at 0x{address:06x}: {record['stderr'].strip()}")
    end = response_offset + length
    if len(proc.stdout) < end:
        raise RuntimeError(
            f"short INQUIRY response at 0x{address:06x}: need {end}, got {len(proc.stdout)}"
        )
    data = proc.stdout[response_offset:end]
    record["bytes_hex"] = data.hex()
    return data, record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--length", required=True, type=parse_int)
    parser.add_argument("--chunk-size", type=parse_int, default=0x80)
    parser.add_argument("--out", type=Path, help="write raw bytes to this path")
    parser.add_argument("--json-out", type=Path, help="write per-chunk metadata to this path")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--request-len", type=int, default=176)
    parser.add_argument("--response-offset", type=parse_int, default=0x20)
    parser.add_argument("--progress-every", type=parse_int, default=0x1000)
    parser.add_argument("--quiet", action="store_true", help="do not print raw hex/ascii output")
    parser.add_argument(
        "--no-discard-stale-first",
        action="store_true",
        help="disable the default address-1 compensation for the first stale gateway byte",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.length < 1:
        raise ValueError("--length must be at least 1")
    if not 1 <= args.chunk_size <= 0x80:
        raise ValueError("--chunk-size must be 1..0x80 for the current hook")
    discard_stale_first = not args.no_discard_stale_first
    if discard_stale_first and args.chunk_size > 0x7F:
        args.chunk_size = 0x7F
    if args.address + args.length > 0x1000000:
        raise ValueError("requested range crosses the 24-bit controller address space")

    data = bytearray()
    records: list[dict[str, Any]] = []
    remaining = args.length
    address = args.address
    while remaining:
        chunk_len = min(args.chunk_size, remaining)
        request_address = address
        request_length = chunk_len
        drop_prefix = 0
        if discard_stale_first and address > 0:
            request_address = address - 1
            request_length = chunk_len + 1
            drop_prefix = 1

        chunk, record = read_chunk(
            sg_raw=args.sg_raw,
            device=args.device,
            address=request_address,
            length=request_length,
            timeout=args.timeout,
            request_len=args.request_len,
            response_offset=args.response_offset,
        )
        if drop_prefix:
            record["discarded_stale_first_byte"] = chunk[0]
            record["requested_address"] = address
            chunk = chunk[drop_prefix:]
        data.extend(chunk)
        records.append(record)
        address += chunk_len
        remaining -= chunk_len
        if args.progress_every and len(data) % args.progress_every == 0:
            print(f"read {len(data)}/{args.length} bytes through 0x{address - 1:06x}", file=sys.stderr)

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
                    "chunk_size": args.chunk_size,
                    "bytes_hex": blob.hex(),
                    "ascii_preview": ascii_preview(blob),
                    "records": records,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    if args.quiet:
        print(f"read {len(blob)} bytes from controller[0x{args.address:06x}..0x{args.address + len(blob) - 1:06x}]")
    else:
        print(f"bytes_hex={blob.hex()}")
        print(f"ascii={ascii_preview(blob)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
