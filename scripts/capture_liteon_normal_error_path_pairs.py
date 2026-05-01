#!/usr/bin/env python3
"""Capture normal work-window snapshots after failed read/status commands.

Each pair sends one expected-failing no-data-out/read-style command, captures
the normal READ BUFFER work window, then sends REQUEST SENSE and captures the
window again. This helps distinguish the failing command path from the sense
reporting path without using updater/write commands.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from capture_liteon_normal_work_window_stimuli import (
    capture_window,
    cdb_text,
    run_sg_raw,
    sha256_hex,
)


DEFAULT_SG_RAW = shutil.which("sg_raw") or "/usr/bin/sg_raw"


@dataclass(frozen=True)
class Command:
    name: str
    cdb: tuple[int, ...]
    request_len: int


REQUEST_SENSE = Command("request-sense-after-failure", (0x03, 0, 0, 0, 0xFC, 0), 0xFC)

COMMANDS = (
    Command("read-toc-format-0", (0x43, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Command("read-toc-format-4", (0x43, 0, 0x04, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC),
    Command("get-performance-type00", (0xAC, 0, 0, 0, 0, 0, 0, 0, 0, 0x10, 0, 0), 0xFC),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--mode", type=lambda x: int(x, 0), default=0x01)
    parser.add_argument("--id", type=lambda x: int(x, 0), default=0x01, dest="buffer_id")
    parser.add_argument("--offset", type=lambda x: int(x, 0), default=0x070000)
    parser.add_argument("--length", type=lambda x: int(x, 0), default=0x10000)
    parser.add_argument("--chunk-size", type=lambda x: int(x, 0), default=0x400)
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--chunk-delay", type=float, default=0.0)
    return parser.parse_args()


def run_command(args: argparse.Namespace, command: Command, out_path: Path) -> dict[str, Any]:
    response, record = run_sg_raw(
        sg_raw=args.sg_raw,
        device=args.device,
        cdb=command.cdb,
        request_len=command.request_len,
        timeout=args.timeout,
        process_timeout=args.process_timeout,
    )
    out_path.write_bytes(response)
    return {
        **record,
        "name": command.name,
        "response_path": str(out_path),
        "response_sha256": sha256_hex(response) if response else None,
        "cdb_text": cdb_text(command.cdb),
    }


def main() -> int:
    args = parse_args()
    selected = [
        command
        for command in COMMANDS
        if not args.include or any(term in command.name for term in args.include)
    ]
    if not selected:
        raise SystemExit(f"no commands matched --include filters: {args.include!r}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "cycles": args.cycles,
        "commands": [command.name for command in selected],
        "captures": [],
        "window": {
            "mode": args.mode,
            "id": args.buffer_id,
            "offset": args.offset,
            "length": args.length,
            "chunk_size": args.chunk_size,
        },
    }

    index = 0
    for cycle in range(args.cycles):
        baseline_name = f"{index:02d}-cycle{cycle:02d}-baseline-no-stimulus"
        baseline_path = args.out_dir / f"{baseline_name}.window.bin"
        baseline_record = capture_window(args, baseline_path)
        baseline_record["stimulus"] = "baseline-no-stimulus"
        baseline_record["cycle"] = cycle
        report["captures"].append(baseline_record)
        print(f"{baseline_name}: window sha256={baseline_record['sha256']}", flush=True)
        index += 1

        for command in selected:
            if args.delay:
                time.sleep(args.delay)
            response_name = f"{index:02d}-cycle{cycle:02d}-{command.name}.response.bin"
            command_record = run_command(args, command, args.out_dir / response_name)
            print(
                f"{index:02d} cycle{cycle:02d}-{command.name}: "
                f"rc={command_record['returncode']} good={command_record['good']} "
                f"len={command_record['stdout_len']}",
                flush=True,
            )
            if args.delay:
                time.sleep(args.delay)
            window_name = f"{index:02d}-cycle{cycle:02d}-{command.name}-after-command"
            window_record = capture_window(args, args.out_dir / f"{window_name}.window.bin")
            window_record.update({"stimulus": f"{command.name}-after-command", "cycle": cycle})
            report["captures"].append({"command": command_record, "window": window_record})
            print(f"{window_name}: window sha256={window_record['sha256']}", flush=True)
            index += 1

            if args.delay:
                time.sleep(args.delay)
            sense_name = f"{index:02d}-cycle{cycle:02d}-{command.name}-request-sense.response.bin"
            sense_record = run_command(args, REQUEST_SENSE, args.out_dir / sense_name)
            print(
                f"{index:02d} cycle{cycle:02d}-{command.name}-request-sense: "
                f"rc={sense_record['returncode']} good={sense_record['good']} "
                f"len={sense_record['stdout_len']}",
                flush=True,
            )
            if args.delay:
                time.sleep(args.delay)
            sense_window_name = f"{index:02d}-cycle{cycle:02d}-{command.name}-after-request-sense"
            sense_window = capture_window(args, args.out_dir / f"{sense_window_name}.window.bin")
            sense_window.update({"stimulus": f"{command.name}-after-request-sense", "cycle": cycle})
            report["captures"].append({"command": sense_record, "window": sense_window})
            print(f"{sense_window_name}: window sha256={sense_window['sha256']}", flush=True)
            index += 1

        (args.out_dir / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
