#!/usr/bin/env python3
"""Scan LiteOn READ BUFFER IDs at selected offsets.

This is intentionally read-only and low-volume. It asks each selected buffer ID
for a small fixed-length sample at one or more offsets, then groups the results
by hash/shape. By default it uses the known LiteOn-useful READ BUFFER mode 1.
Use it to look for public normal-mode windows before reaching for helper hooks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import string
import subprocess
import time
from pathlib import Path
from typing import Any

from read_liteon_read_buffer_bulk import DEFAULT_SG_RAW, parse_byte, parse_int, run_read


def ascii_preview(data: bytes, limit: int = 64) -> str:
    allowed = set(string.printable.encode("ascii")) - {0x0B, 0x0C}
    return "".join(chr(byte) if byte in allowed and byte >= 0x20 else "." for byte in data[:limit])


def parse_id_list(value: str) -> list[int]:
    ids: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = parse_byte(start_s)
            end = parse_byte(end_s)
            if end < start:
                raise argparse.ArgumentTypeError("ID range end must be >= start")
            ids.extend(range(start, end + 1))
        else:
            ids.append(parse_byte(part))
    return sorted(set(ids))


def parse_offsets(values: list[str]) -> list[int]:
    offsets: list[int] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part:
                offsets.append(parse_int(part))
    return offsets


def is_interesting(record: dict[str, Any], data: bytes) -> bool:
    if record.get("returncode") != 0 or record.get("timed_out"):
        return False
    if len(data) != record.get("length"):
        return False
    return any(byte != 0x00 for byte in data)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--mode", type=parse_byte, default=0x01)
    parser.add_argument("--ids", default="0x00-0xff", help="comma/range list, e.g. 0x01,0x02,0xe0-0xff")
    parser.add_argument("--offset", action="append", required=True, help="offset, repeatable or comma-separated")
    parser.add_argument("--length", type=parse_int, default=0x40)
    parser.add_argument("--timeout", type=int, default=2)
    parser.add_argument("--process-timeout", type=float, default=4.0)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--jsonl-out", type=Path)
    parser.add_argument("--summary-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ids = parse_id_list(args.ids)
    offsets = parse_offsets(args.offset)
    if not ids:
        raise ValueError("no IDs selected")
    if not offsets:
        raise ValueError("no offsets selected")
    if not 1 <= args.length <= 0x1000:
        raise ValueError("--length must be 1..0x1000 for this scanner")

    args.jsonl_out.parent.mkdir(parents=True, exist_ok=True) if args.jsonl_out else None
    args.summary_out.parent.mkdir(parents=True, exist_ok=True) if args.summary_out else None

    rows: list[dict[str, Any]] = []
    with (args.jsonl_out.open("w") if args.jsonl_out else open("/dev/null", "w")) as jsonl:
        for offset in offsets:
            for buffer_id in ids:
                data, record = run_read(
                    sg_raw=args.sg_raw,
                    device=args.device,
                    mode=args.mode,
                    buffer_id=buffer_id,
                    offset=offset,
                    length=args.length,
                    timeout=args.timeout,
                    process_timeout=args.process_timeout,
                )
                row = {
                    "id": buffer_id,
                    "offset": offset,
                    "returncode": record.get("returncode"),
                    "timed_out": record.get("timed_out"),
                    "stdout_len": len(data),
                    "sha256": hashlib.sha256(data).hexdigest() if data else None,
                    "first64_hex": data[:64].hex(),
                    "ascii": ascii_preview(data),
                    "interesting": is_interesting(record, data),
                    "stderr": record.get("stderr", "").strip(),
                }
                rows.append(row)
                jsonl.write(json.dumps(row, sort_keys=True) + "\n")
                if row["interesting"]:
                    print(
                        f"mode=0x{args.mode:02x} id=0x{buffer_id:02x} off=0x{offset:06x} "
                        f"sha={row['sha256'][:16]} ascii={row['ascii']}"
                    )
                if args.delay:
                    time.sleep(args.delay)

    by_shape: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        key = (
            row["offset"],
            row["returncode"],
            row["timed_out"],
            row["stdout_len"],
            row["sha256"],
            row["first64_hex"],
        )
        by_shape.setdefault(key, []).append(row)

    lines = [
        f"rows {len(rows)}",
        f"mode 0x{args.mode:02x} ids {len(ids)} offsets {len(offsets)} length {args.length}",
    ]
    for key, members in sorted(by_shape.items(), key=lambda item: (item[0][0], str(item[0][4] or ""), item[0][1] or -1)):
        offset, returncode, timed_out, stdout_len, sha256, first64_hex = key
        ids_text = " ".join(f"0x{row['id']:02x}" for row in members[:32])
        if len(members) > 32:
            ids_text += " ..."
        interesting = sum(1 for row in members if row["interesting"])
        lines.append(
            f"offset=0x{offset:06x} rc={returncode} timeout={timed_out} len={stdout_len} "
            f"count={len(members)} interesting={interesting} sha={(sha256 or '')[:16]} ids={ids_text}"
        )
        if interesting:
            sample = next(row for row in members if row["interesting"])
            lines.append(f"  ascii={sample['ascii']}")
            lines.append(f"  hex={first64_hex}")

    summary = "\n".join(lines) + "\n"
    print(summary)
    if args.summary_out:
        args.summary_out.write_text(summary)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=__import__("sys").stderr)
        raise SystemExit(1)
