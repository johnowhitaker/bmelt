#!/usr/bin/env python3
"""Capture the normal-mode READ BUFFER work window after safe SCSI stimuli.

The normal LD5M runtime exposes a useful public window via:

    READ BUFFER mode=1 id=01 offset=0x070000

Several pages in that window change after otherwise read-only SCSI commands.
This tool sends a conservative set of no-data-out/read-style commands, captures
their responses, then snapshots the public work window after each stimulus.
It avoids updater, write, load/eject, mode-select, diagnostic, and broad
mechanics commands.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SG_RAW = shutil.which("sg_raw") or "/usr/bin/sg_raw"


@dataclass(frozen=True)
class Stimulus:
    name: str
    cdb: tuple[int, ...]
    request_len: int = 0


STIMULI: tuple[Stimulus, ...] = (
    Stimulus("baseline-no-stimulus", ()),
    Stimulus("test-unit-ready", (0x00, 0, 0, 0, 0, 0)),
    Stimulus("request-sense", (0x03, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("inquiry-standard-96", (0x12, 0, 0, 0, 0x60, 0), 0x60),
    Stimulus(
        "inquiry-extrainq",
        (0x12, 0, 0, 0, 0xF0, 0x40, 0, 0, 0, 0, 0, 0),
        0xF0,
    ),
    Stimulus("mode-sense10-all", (0x5A, 0, 0x3F, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-configuration-current", (0x46, 0x02, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-configuration-all", (0x46, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-event-status-media", (0x4A, 0x01, 0, 0, 0x10, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("read-toc-format-0", (0x43, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("read-disc-information", (0x51, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("read-track-information-lba0", (0x52, 0x01, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mechanism-status", (0xBD, 0, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0, 0), 0xFC),
    Stimulus("read-dvd-structure-format0", (0xAD, 0, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0, 0), 0xFC),
    Stimulus("read-capacity10", (0x25, 0, 0, 0, 0, 0, 0, 0, 0, 0), 0x08),
    Stimulus("read-format-capacities", (0x23, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mode-sense10-read-error-recovery", (0x5A, 0, 0x01, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mode-sense10-caching", (0x5A, 0, 0x08, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mode-sense10-cd-device", (0x5A, 0, 0x0D, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mode-sense10-cd-audio", (0x5A, 0, 0x0E, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mode-sense10-power-condition", (0x5A, 0, 0x1A, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mode-sense10-fault-failure", (0x5A, 0, 0x1C, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("mode-sense10-capabilities", (0x5A, 0, 0x2A, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-event-status-operational", (0x4A, 0x01, 0, 0, 0x01, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-event-status-power", (0x4A, 0x01, 0, 0, 0x02, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-event-status-external", (0x4A, 0x01, 0, 0, 0x04, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-event-status-multihost", (0x4A, 0x01, 0, 0, 0x20, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("get-event-status-busy", (0x4A, 0x01, 0, 0, 0x40, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("read-toc-format-1", (0x43, 0, 0x01, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("read-toc-format-2", (0x43, 0, 0x02, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("read-toc-format-4", (0x43, 0, 0x04, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Stimulus("read-dvd-structure-format1", (0xAD, 0, 0, 0, 0, 0, 0, 0, 1, 0xFC, 0, 0), 0xFC),
    Stimulus("read-dvd-structure-format2", (0xAD, 0, 0, 0, 0, 0, 0, 0, 2, 0xFC, 0, 0), 0xFC),
    Stimulus("read-dvd-structure-formatff", (0xAD, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xFC, 0, 0), 0xFC),
    Stimulus("get-performance-type00", (0xAC, 0, 0, 0, 0, 0, 0, 0, 0, 0x10, 0, 0), 0xFC),
    Stimulus("get-performance-type03", (0xAC, 0, 0, 0, 0, 0, 0, 0, 0, 0x10, 3, 0), 0xFC),
)


def cdb_text(cdb: tuple[int, ...] | list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_sg_raw(
    *,
    sg_raw: str,
    device: str,
    cdb: tuple[int, ...] | list[int],
    request_len: int,
    timeout: int,
    process_timeout: float,
) -> tuple[bytes, dict[str, Any]]:
    cmd = [sg_raw, "--cmdset=1", "-b", "--timeout", str(timeout)]
    if request_len:
        cmd.extend(["--request", str(request_len)])
    cmd.extend([device, *[f"{byte:02x}" for byte in cdb]])
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
        stdout = proc.stdout
        stderr = proc.stderr.decode("utf-8", "replace")
        return stdout, {
            "cmd": cmd,
            "cdb": cdb_text(cdb),
            "request_len": request_len,
            "returncode": proc.returncode,
            "timed_out": False,
            "elapsed_s": round(elapsed, 6),
            "stdout_len": len(stdout),
            "stdout_sha256": sha256_hex(stdout) if stdout else None,
            "stderr": stderr,
            "good": proc.returncode == 0 and "SCSI Status: Good" in stderr,
        }
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
            "request_len": request_len,
            "returncode": None,
            "timed_out": True,
            "elapsed_s": round(elapsed, 6),
            "stdout_len": len(stdout),
            "stdout_sha256": sha256_hex(stdout) if stdout else None,
            "stderr": stderr,
            "good": False,
        }


def read_buffer_cdb(buffer_id: int, offset: int, length: int, mode: int = 0x01) -> list[int]:
    return [
        0x3C,
        mode & 0x1F,
        buffer_id & 0xFF,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
        (length >> 16) & 0xFF,
        (length >> 8) & 0xFF,
        length & 0xFF,
        0,
    ]


def capture_window(args: argparse.Namespace, out_path: Path) -> dict[str, Any]:
    blob = bytearray()
    records: list[dict[str, Any]] = []
    remaining = args.length
    offset = args.offset
    while remaining:
        chunk_len = min(args.chunk_size, remaining)
        cdb = read_buffer_cdb(args.buffer_id, offset, chunk_len, args.mode)
        data, record = run_sg_raw(
            sg_raw=args.sg_raw,
            device=args.device,
            cdb=cdb,
            request_len=chunk_len,
            timeout=args.timeout,
            process_timeout=args.process_timeout,
        )
        records.append(record)
        if record["returncode"] != 0 or record["timed_out"] or len(data) != chunk_len:
            raise RuntimeError(
                f"READ BUFFER capture failed at offset 0x{offset:06x}: "
                f"rc={record['returncode']} timeout={record['timed_out']} "
                f"got={len(data)} expected={chunk_len}"
            )
        blob.extend(data)
        offset += chunk_len
        remaining -= chunk_len
        if args.chunk_delay:
            time.sleep(args.chunk_delay)

    out_path.write_bytes(bytes(blob))
    return {
        "path": str(out_path),
        "mode": args.mode,
        "id": args.buffer_id,
        "offset": args.offset,
        "length": args.length,
        "chunk_size": args.chunk_size,
        "sha256": sha256_hex(bytes(blob)),
        "records": records,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--mode", type=lambda x: int(x, 0), default=0x01)
    parser.add_argument("--id", type=lambda x: int(x, 0), default=0x01, dest="buffer_id")
    parser.add_argument("--offset", type=lambda x: int(x, 0), default=0x070000)
    parser.add_argument("--length", type=lambda x: int(x, 0), default=0x10000)
    parser.add_argument("--chunk-size", type=lambda x: int(x, 0), default=0x400)
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--chunk-delay", type=float, default=0.0)
    parser.add_argument(
        "--cycles",
        type=int,
        default=1,
        help="Repeat the selected stimulus list this many times.",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Only run stimuli whose names contain this substring. Repeatable.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.cycles < 1:
        raise SystemExit("--cycles must be >= 1")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    selected_stimuli = [
        stimulus
        for stimulus in STIMULI
        if not args.include or any(term in stimulus.name for term in args.include)
    ]
    if not selected_stimuli:
        raise SystemExit(f"no stimuli matched --include filters: {args.include!r}")
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "window": {
            "mode": args.mode,
            "id": args.buffer_id,
            "offset": args.offset,
            "length": args.length,
            "chunk_size": args.chunk_size,
        },
        "cycles": args.cycles,
        "include": args.include,
        "captures": [],
    }

    index = 0
    for cycle in range(args.cycles):
        for stimulus in selected_stimuli:
            capture_name = (
                f"cycle{cycle:02d}-{stimulus.name}" if args.cycles > 1 else stimulus.name
            )
            item: dict[str, Any] = {
                "index": index,
                "cycle": cycle,
                "name": stimulus.name,
                "capture_name": capture_name,
            }
            if stimulus.cdb:
                response_path = args.out_dir / f"{index:02d}-{capture_name}.response.bin"
                response, stimulus_record = run_sg_raw(
                    sg_raw=args.sg_raw,
                    device=args.device,
                    cdb=stimulus.cdb,
                    request_len=stimulus.request_len,
                    timeout=args.timeout,
                    process_timeout=args.process_timeout,
                )
                response_path.write_bytes(response)
                item["stimulus"] = stimulus_record | {"response_path": str(response_path)}
                print(
                    f"{index:02d} {capture_name}: stimulus rc={stimulus_record['returncode']} "
                    f"good={stimulus_record['good']} len={len(response)}",
                    flush=True,
                )
                if args.delay:
                    time.sleep(args.delay)
            else:
                item["stimulus"] = None
                print(f"{index:02d} {capture_name}: capture only", flush=True)

            capture_path = args.out_dir / f"{index:02d}-{capture_name}.window.bin"
            item["window"] = capture_window(args, capture_path)
            print(
                f"{index:02d} {capture_name}: window sha256={item['window']['sha256']}",
                flush=True,
            )
            report["captures"].append(item)
            (args.out_dir / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            if args.delay:
                time.sleep(args.delay)
            index += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
