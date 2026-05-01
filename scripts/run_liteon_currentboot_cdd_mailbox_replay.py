#!/usr/bin/env python3
"""Replay a planned CDD mailbox sequence through the currentboot RW hook.

This assumes the drive is already in currentboot with a combined
gateway-bulk/XDATA-read-write response hook installed. It uses only INQUIRY
commands interpreted by that hook:

- CDB[10] == 00 and CDB[11] == 00: controller-gateway bulk read
- CDB[10] == a5: guarded XDATA write
- CDB[10] == 5a: guarded XDATA read
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = ROOT / "references/firmware/extracted/liteon-cdd-mailbox-replay-plan.json"
DEFAULT_SG_RAW = "/usr/bin/sg_raw"


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def ascii_preview(data: bytes) -> str:
    return "".join(chr(byte) if 0x20 <= byte < 0x7F else "." for byte in data)


def sg_raw_inquiry(
    *,
    sg_raw: str,
    device: str,
    cdb: list[int],
    timeout: int,
    request_len: int,
) -> tuple[bytes, dict[str, Any]]:
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
        raise RuntimeError(f"sg_raw failed: {record['stderr'].strip()}")
    return proc.stdout, record


def xdata_cdb(address: int, byte9: int, magic: tuple[int, int] | None) -> tuple[list[int], int, int]:
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
        byte9 & 0xFF,
        magic[0] if magic else 0x00,
        magic[1] if magic else 0x00,
    ]
    return cdb, base, selector


def xdata_read(
    *,
    sg_raw: str,
    device: str,
    address: int,
    timeout: int,
    request_len: int,
    response_offset: int,
) -> tuple[int, dict[str, Any]]:
    cdb, base, selector = xdata_cdb(address, 0x00, (0x5A, 0xA5))
    stdout, record = sg_raw_inquiry(
        sg_raw=sg_raw,
        device=device,
        cdb=cdb,
        timeout=timeout,
        request_len=request_len,
    )
    if len(stdout) <= response_offset:
        raise RuntimeError(f"short INQUIRY response for XDATA read 0x{address:04x}")
    value = stdout[response_offset]
    record.update(
        {
            "kind": "xdata_read",
            "address": address,
            "base": base,
            "selector": selector,
            "value": value,
        }
    )
    return value, record


def xdata_write(
    *,
    sg_raw: str,
    device: str,
    address: int,
    value: int,
    timeout: int,
    request_len: int,
    response_offset: int,
) -> dict[str, Any]:
    cdb, base, selector = xdata_cdb(address, value, (0xA5, 0x5A))
    stdout, record = sg_raw_inquiry(
        sg_raw=sg_raw,
        device=device,
        cdb=cdb,
        timeout=timeout,
        request_len=request_len,
    )
    if len(stdout) <= response_offset:
        raise RuntimeError(f"short INQUIRY response for XDATA write 0x{address:04x}")
    readback = stdout[response_offset]
    record.update(
        {
            "kind": "xdata_write",
            "address": address,
            "base": base,
            "selector": selector,
            "value": value & 0xFF,
            "readback": readback,
        }
    )
    return record


def xdata_read_range(
    *,
    sg_raw: str,
    device: str,
    address: int,
    length: int,
    timeout: int,
    request_len: int,
    response_offset: int,
) -> tuple[bytes, list[dict[str, Any]]]:
    data = bytearray()
    records: list[dict[str, Any]] = []
    for offset in range(length):
        value, record = xdata_read(
            sg_raw=sg_raw,
            device=device,
            address=address + offset,
            timeout=timeout,
            request_len=request_len,
            response_offset=response_offset,
        )
        data.append(value)
        records.append(record)
    return bytes(data), records


def gateway_read_chunk(
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
    if not 1 <= length <= 0x80:
        raise ValueError("gateway chunk length must be 1..0x80")
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
    stdout, record = sg_raw_inquiry(
        sg_raw=sg_raw,
        device=device,
        cdb=cdb,
        timeout=timeout,
        request_len=request_len,
    )
    end = response_offset + length
    if len(stdout) < end:
        raise RuntimeError(f"short INQUIRY response for gateway read 0x{address:06x}")
    data = stdout[response_offset:end]
    record.update(
        {
            "kind": "gateway_read",
            "address": address,
            "base": base,
            "selector": selector,
            "length": length,
            "bytes_hex": data.hex(),
        }
    )
    return data, record


def gateway_read_range(
    *,
    sg_raw: str,
    device: str,
    address: int,
    length: int,
    chunk_size: int,
    timeout: int,
    request_len: int,
    response_offset: int,
) -> tuple[bytes, list[dict[str, Any]]]:
    if address + length > 0x1000000:
        raise ValueError("gateway read crosses 24-bit address space")
    data = bytearray()
    records: list[dict[str, Any]] = []
    remaining = length
    cursor = address
    chunk_size = min(chunk_size, 0x7F)
    while remaining:
        chunk_len = min(chunk_size, remaining)
        request_address = cursor
        request_length = chunk_len
        drop_prefix = 0
        if cursor > 0:
            request_address = cursor - 1
            request_length = chunk_len + 1
            drop_prefix = 1
        chunk, record = gateway_read_chunk(
            sg_raw=sg_raw,
            device=device,
            address=request_address,
            length=request_length,
            timeout=timeout,
            request_len=request_len,
            response_offset=response_offset,
        )
        if drop_prefix:
            record["discarded_stale_first_byte"] = chunk[0]
            record["requested_address"] = cursor
            chunk = chunk[1:]
        data.extend(chunk)
        records.append(record)
        cursor += chunk_len
        remaining -= chunk_len
    return bytes(data), records


def sample_one(args: argparse.Namespace, sample: dict[str, Any], out_dir: Path, phase: str) -> dict[str, Any]:
    kind = sample["kind"]
    address = int(sample["address"])
    length = int(sample["length"])
    if kind == "xdata":
        data, records = xdata_read_range(
            sg_raw=args.sg_raw,
            device=args.device,
            address=address,
            length=length,
            timeout=args.timeout,
            request_len=args.request_len,
            response_offset=args.response_offset,
        )
    elif kind == "gateway":
        data, records = gateway_read_range(
            sg_raw=args.sg_raw,
            device=args.device,
            address=address,
            length=length,
            chunk_size=args.chunk_size,
            timeout=args.timeout,
            request_len=args.request_len,
            response_offset=args.response_offset,
        )
    else:
        raise ValueError(f"unknown sample kind: {kind}")

    out_name = f"{phase}-{kind}-{address:06x}-{length:04x}.bin"
    out_path = out_dir / out_name
    out_path.write_bytes(data)
    return {
        "phase": phase,
        "kind": kind,
        "address": address,
        "length": length,
        "why": sample.get("why"),
        "out": str(out_path),
        "bytes_hex": data.hex(),
        "ascii_preview": ascii_preview(data),
        "all_zero": all(byte == 0 for byte in data),
        "records": records,
    }


def load_level(plan: dict[str, Any], level_name: str) -> dict[str, Any]:
    levels = plan["candidate_replay_levels"]
    for level in levels:
        if level["name"] == level_name:
            return level
    names = ", ".join(level["name"] for level in levels)
    raise ValueError(f"unknown replay level {level_name!r}; available: {names}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--level", default="field-only CDD mailbox")
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--request-len", type=int, default=176)
    parser.add_argument("--response-offset", type=parse_int, default=0x20)
    parser.add_argument("--chunk-size", type=parse_int, default=0x7F)
    parser.add_argument("--skip-before", action="store_true")
    parser.add_argument("--skip-gateway", action="store_true")
    parser.add_argument("--no-restore-doorbell", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = json.loads(args.plan.read_text())
    level = load_level(plan, args.level)
    samples = list(level.get("suggested_samples_after", []))
    if args.skip_gateway:
        samples = [sample for sample in samples if sample["kind"] != "gateway"]

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir or (ROOT / "runs/currentboot-cdd-mailbox-replay" / stamp)
    record: dict[str, Any] = {
        "timestamp_utc": stamp,
        "device": args.device,
        "plan": str(args.plan),
        "level": level["name"],
        "description": level.get("description"),
        "risk": level.get("risk"),
        "dry_run": args.dry_run,
        "writes": level["ordered_byte_writes"],
        "samples": samples,
        "results": {},
    }

    if args.dry_run:
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_before:
        before = []
        for sample in samples:
            before.append(sample_one(args, sample, out_dir, "before"))
        record["results"]["before_samples"] = before

    write_records = []
    for item in level["ordered_byte_writes"]:
        address = int(item["address"])
        value = int(item["value"])
        write_records.append(
            xdata_write(
                sg_raw=args.sg_raw,
                device=args.device,
                address=address,
                value=value,
                timeout=args.timeout,
                request_len=args.request_len,
                response_offset=args.response_offset,
            )
        )
    record["results"]["write_records"] = write_records

    after = []
    for sample in samples:
        after.append(sample_one(args, sample, out_dir, "after"))
    record["results"]["after_samples"] = after

    if not args.no_restore_doorbell:
        record["results"]["restore_4a00"] = xdata_write(
            sg_raw=args.sg_raw,
            device=args.device,
            address=0x4A00,
            value=0x00,
            timeout=args.timeout,
            request_len=args.request_len,
            response_offset=args.response_offset,
        )
        record["results"]["after_restore_4a00"], restore_read_record = xdata_read(
            sg_raw=args.sg_raw,
            device=args.device,
            address=0x4A00,
            timeout=args.timeout,
            request_len=args.request_len,
            response_offset=args.response_offset,
        )
        record["results"]["after_restore_4a00_record"] = restore_read_record

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
