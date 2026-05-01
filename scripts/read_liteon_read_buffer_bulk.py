#!/usr/bin/env python3
"""Read a LiteOn READ BUFFER mode=1 window in chunks.

This is a generic wrapper around SCSI READ BUFFER(10):

    3C 01 <id> <24-bit offset> <24-bit length> 00

It is useful for normal-mode public buffer IDs such as 0x01/0x02, where large
single requests may be less predictable than small chunked reads.
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


DEFAULT_SG_RAW = shutil.which("sg_raw") or "/usr/bin/sg_raw"


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


def ascii_preview(data: bytes, limit: int = 96) -> str:
    return "".join(chr(byte) if 0x20 <= byte < 0x7F else "." for byte in data[:limit])


def read_buffer_cdb(buffer_id: int, offset: int, length: int) -> list[int]:
    if not 0 <= offset <= 0xFFFFFF:
        raise ValueError(f"READ BUFFER offset out of 24-bit range: 0x{offset:x}")
    if not 0 <= length <= 0xFFFFFF:
        raise ValueError(f"READ BUFFER length out of 24-bit range: 0x{length:x}")
    return [
        0x3C,
        0x01,
        buffer_id & 0xFF,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
        (length >> 16) & 0xFF,
        (length >> 8) & 0xFF,
        length & 0xFF,
        0x00,
    ]


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def run_read(
    *,
    sg_raw: str,
    device: str,
    buffer_id: int,
    offset: int,
    length: int,
    timeout: int,
    process_timeout: float,
) -> tuple[bytes, dict[str, Any]]:
    cdb = read_buffer_cdb(buffer_id, offset, length)
    cmd = [
        sg_raw,
        "-b",
        "--request",
        str(length),
        "--timeout",
        str(timeout),
        device,
        *[f"{byte:02x}" for byte in cdb],
    ]
    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=process_timeout,
            check=False,
        )
        elapsed = time.monotonic() - started
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        stdout = exc.stdout or b""
        stderr = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc.stderr, bytes)
            else str(exc.stderr or "")
        )
        return stdout, {
            "cmd": cmd,
            "cdb": cdb_text(cdb),
            "offset": offset,
            "length": length,
            "returncode": None,
            "timed_out": True,
            "elapsed_s": round(elapsed, 6),
            "stdout_len": len(stdout),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest() if stdout else None,
            "stderr": stderr,
        }

    stdout = proc.stdout
    stderr = proc.stderr.decode("utf-8", "replace")
    return stdout, {
        "cmd": cmd,
        "cdb": cdb_text(cdb),
        "offset": offset,
        "length": length,
        "returncode": proc.returncode,
        "timed_out": False,
        "elapsed_s": round(elapsed, 6),
        "stdout_len": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest() if stdout else None,
        "stdout_first64_hex": stdout[:64].hex(),
        "stderr": stderr,
        "good": proc.returncode == 0 and "SCSI Status: Good" in stderr,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--id", required=True, type=parse_byte, dest="buffer_id")
    parser.add_argument("--offset", required=True, type=parse_int)
    parser.add_argument("--length", required=True, type=parse_int)
    parser.add_argument("--chunk-size", type=parse_int, default=0x400)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.length < 1:
        raise ValueError("--length must be at least 1")
    if not 1 <= args.chunk_size <= 0xFFFF:
        raise ValueError("--chunk-size must be 1..0xffff")
    if args.offset + args.length > 0x1000000:
        raise ValueError("requested range crosses the 24-bit READ BUFFER address space")

    blob = bytearray()
    records: list[dict[str, Any]] = []
    remaining = args.length
    offset = args.offset
    while remaining:
        chunk_len = min(args.chunk_size, remaining)
        chunk, record = run_read(
            sg_raw=args.sg_raw,
            device=args.device,
            buffer_id=args.buffer_id,
            offset=offset,
            length=chunk_len,
            timeout=args.timeout,
            process_timeout=args.process_timeout,
        )
        records.append(record)
        if record.get("returncode") != 0 or record.get("timed_out") or len(chunk) != chunk_len:
            raise RuntimeError(
                f"READ BUFFER id=0x{args.buffer_id:02x} offset=0x{offset:06x} "
                f"failed/short: rc={record.get('returncode')} timed_out={record.get('timed_out')} "
                f"got={len(chunk)} expected={chunk_len} stderr={record.get('stderr', '').strip()}"
            )
        blob.extend(chunk)
        offset += chunk_len
        remaining -= chunk_len
        if args.delay:
            time.sleep(args.delay)

    data = bytes(blob)
    report = {
        "device": args.device,
        "id": args.buffer_id,
        "offset": args.offset,
        "length": args.length,
        "chunk_size": args.chunk_size,
        "sha256": hashlib.sha256(data).hexdigest(),
        "ascii_preview": ascii_preview(data),
        "records": records,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(data)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.quiet:
        print(
            f"read {len(data)} bytes from READ BUFFER id=0x{args.buffer_id:02x} "
            f"offset=0x{args.offset:06x} sha256={report['sha256']}"
        )
    else:
        print(json.dumps({k: v for k, v in report.items() if k != "records"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
