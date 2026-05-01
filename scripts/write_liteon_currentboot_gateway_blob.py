#!/usr/bin/env python3
"""Write a byte string through the guarded currentboot controller-gateway hook."""

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


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def parse_payload(args: argparse.Namespace) -> bytes:
    if args.hex is not None and args.file is not None:
        raise ValueError("use only one of --hex or --file")
    if args.hex is None and args.file is None:
        raise ValueError("one of --hex or --file is required")
    if args.hex is not None:
        text = compact_hex(args.hex)
        if len(text) % 2:
            raise ValueError("--hex must contain an even number of hex digits")
        return bytes.fromhex(text)
    return args.file.read_bytes()


def ascii_preview(data: bytes) -> str:
    return "".join(chr(byte) if 0x20 <= byte < 0x7F else "." for byte in data)


def gateway_cdb(address: int, *, value: int | None) -> list[int]:
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError(f"controller address out of 24-bit range: 0x{address:x}")
    base = address & ~0x3F
    selector = address & 0x3F
    return [
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
        0x5A if value is not None else 0x00,
        value if value is not None else 0x00,
    ]


def run_inquiry(
    *,
    sg_raw: str,
    device: str,
    cdb: list[int],
    timeout: int,
    request_len: int,
) -> tuple[int, dict[str, Any]]:
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
        "cdb": cdb,
        "returncode": proc.returncode,
        "stdout_len": len(proc.stdout),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }
    if proc.returncode != 0:
        raise RuntimeError(record["stderr"].strip())
    return proc.stdout[0x20] if len(proc.stdout) > 0x20 else -1, record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--hex", help="hex bytes to write")
    parser.add_argument("--file", type=Path, help="file bytes to write")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--request-len", type=int, default=176)
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="do not fail if a returned readback byte differs from the written byte",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = parse_payload(args)
    if not payload:
        raise ValueError("payload is empty")
    records: list[dict[str, Any]] = []
    readback = bytearray()
    for offset, value in enumerate(payload):
        address = args.address + offset
        cdb = gateway_cdb(address, value=value)
        got, record = run_inquiry(
            sg_raw=args.sg_raw,
            device=args.device,
            cdb=cdb,
            timeout=args.timeout,
            request_len=args.request_len,
        )
        record.update({"address": address, "value": value, "readback": got})
        records.append(record)
        if got < 0:
            raise RuntimeError(f"short INQUIRY response at 0x{address:06x}")
        readback.append(got)
        if got != value and not args.no_verify:
            raise RuntimeError(f"readback mismatch at 0x{address:06x}: got 0x{got:02x}, wanted 0x{value:02x}")

    report = {
        "device": args.device,
        "address": args.address,
        "length": len(payload),
        "bytes_hex": payload.hex(),
        "readback_hex": bytes(readback).hex(),
        "ascii_preview": ascii_preview(payload),
        "readback_ascii_preview": ascii_preview(bytes(readback)),
        "records": records,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: report[key] for key in report if key != "records"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
