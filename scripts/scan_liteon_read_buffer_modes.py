#!/usr/bin/env python3
"""Scan LiteOn READ BUFFER mode-byte variants for selected IDs.

Earlier mode scans covered the standard low 5-bit SCSI READ BUFFER mode range.
This helper scans the whole CDB byte 1 value.  It is still read-only: every
probe is a READ BUFFER request with no data-out payload.
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

import sys

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from read_liteon_read_buffer_bulk import DEFAULT_SG_RAW, parse_byte, parse_int
from scan_liteon_read_buffer_ids import parse_id_list, parse_offsets


def ascii_preview(data: bytes, limit: int = 64) -> str:
    allowed = set(string.printable.encode("ascii")) - {0x0B, 0x0C}
    return "".join(chr(byte) if byte in allowed and byte >= 0x20 else "." for byte in data[:limit])


def parse_modes(value: str) -> list[int]:
    modes: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = parse_byte(start_s)
            end = parse_byte(end_s)
            if end < start:
                raise argparse.ArgumentTypeError("mode range end must be >= start")
            modes.extend(range(start, end + 1))
        else:
            modes.append(parse_byte(part))
    return sorted(set(modes))


def is_interesting(record: dict[str, Any], data: bytes) -> bool:
    if record.get("returncode") != 0 or record.get("timed_out"):
        return False
    if len(data) != record.get("length"):
        return False
    return any(byte not in (0x00, 0xFF) for byte in data)


def read_buffer_cdb_full_mode(buffer_id: int, offset: int, length: int, mode: int) -> list[int]:
    if not 0 <= offset <= 0xFFFFFF:
        raise ValueError(f"READ BUFFER offset out of 24-bit range: 0x{offset:x}")
    if not 0 <= length <= 0xFFFFFF:
        raise ValueError(f"READ BUFFER length out of 24-bit range: 0x{length:x}")
    if not 0 <= mode <= 0xFF:
        raise ValueError(f"READ BUFFER mode byte out of range: 0x{mode:x}")
    return [
        0x3C,
        mode & 0xFF,
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


def run_read_full_mode(
    *,
    sg_raw: str,
    device: str,
    mode: int,
    buffer_id: int,
    offset: int,
    length: int,
    timeout: int,
    process_timeout: float,
) -> tuple[bytes, dict[str, Any]]:
    cdb = read_buffer_cdb_full_mode(buffer_id, offset, length, mode)
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
    parser.add_argument("--modes", default="0x00-0xff", help="comma/range list, e.g. 0x01,0x80-0x8f")
    parser.add_argument("--ids", default="0x01,0x02,0xe2,0xf0,0xf1,0xf2")
    parser.add_argument("--offset", action="append", required=True, help="offset, repeatable or comma-separated")
    parser.add_argument("--length", type=parse_int, default=0x80)
    parser.add_argument("--timeout", type=int, default=2)
    parser.add_argument("--process-timeout", type=float, default=4.0)
    parser.add_argument("--delay", type=float, default=0.0)
    parser.add_argument("--jsonl-out", type=Path)
    parser.add_argument("--summary-out", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    modes = parse_modes(args.modes)
    ids = parse_id_list(args.ids)
    offsets = parse_offsets(args.offset)
    if not modes:
        raise ValueError("no modes selected")
    if not ids:
        raise ValueError("no IDs selected")
    if not offsets:
        raise ValueError("no offsets selected")
    if not 1 <= args.length <= 0x1000:
        raise ValueError("--length must be 1..0x1000 for this scanner")

    if args.jsonl_out:
        args.jsonl_out.parent.mkdir(parents=True, exist_ok=True)
    if args.summary_out:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    with (args.jsonl_out.open("w") if args.jsonl_out else open("/dev/null", "w")) as jsonl:
        for offset in offsets:
            for mode in modes:
                for buffer_id in ids:
                    data, record = run_read_full_mode(
                        sg_raw=args.sg_raw,
                        device=args.device,
                        mode=mode,
                        buffer_id=buffer_id,
                        offset=offset,
                        length=args.length,
                        timeout=args.timeout,
                        process_timeout=args.process_timeout,
                    )
                    row = {
                        "mode": mode,
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
                            f"mode=0x{mode:02x} id=0x{buffer_id:02x} off=0x{offset:06x} "
                            f"sha={str(row['sha256'])[:16]} ascii={row['ascii']}"
                        )
                    if args.delay:
                        time.sleep(args.delay)

    good = [row for row in rows if row["returncode"] == 0 and not row["timed_out"] and row["stdout_len"]]
    interesting = [row for row in rows if row["interesting"]]
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
        f"modes {len(modes)} ids {len(ids)} offsets {len(offsets)} length {args.length}",
        f"good_with_data {len(good)}",
        f"interesting {len(interesting)}",
        "",
        "interesting rows:",
    ]
    for row in interesting:
        lines.append(
            f"  mode=0x{row['mode']:02x} id=0x{row['id']:02x} off=0x{row['offset']:06x} "
            f"len={row['stdout_len']} sha={str(row['sha256'])[:16]} ascii={row['ascii']}"
        )

    lines += ["", "shapes:"]
    for key, members in sorted(
        by_shape.items(),
        key=lambda item: (item[0][0], item[0][1] or -1, item[0][2] or False, item[0][3], str(item[0][4] or "")),
    ):
        offset, returncode, timed_out, stdout_len, sha256, first64_hex = key
        members_text = " ".join(
            f"m=0x{row['mode']:02x}/id=0x{row['id']:02x}" for row in members[:24]
        )
        if len(members) > 24:
            members_text += " ..."
        lines.append(
            f"offset=0x{offset:06x} rc={returncode} timeout={timed_out} len={stdout_len} "
            f"count={len(members)} sha={(sha256 or '')[:16]} members={members_text}"
        )
        if stdout_len and first64_hex:
            lines.append(f"  hex={first64_hex}")
            lines.append(f"  ascii={members[0]['ascii']}")

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
