#!/usr/bin/env python3
"""Capture normal work-window snapshots around deliberate START STOP variants.

This tool is for the mechanics-path phase.  START STOP UNIT can move the tray,
spin state, or sled-adjacent mechanisms, so this script refuses to send it
unless --allow-start-stop is supplied.  Without that flag it can still take a
baseline window and print the exact CDBs it would send.
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
class StartStopVariant:
    name: str
    control: int
    note: str

    @property
    def cdb(self) -> tuple[int, int, int, int, int, int]:
        return (0x1B, 0x00, 0x00, 0x00, self.control, 0x00)


VARIANTS = {
    "stop": StartStopVariant("stop", 0x00, "START=0 LOEJ=0"),
    "start": StartStopVariant("start", 0x01, "START=1 LOEJ=0"),
    "eject": StartStopVariant("eject", 0x02, "START=0 LOEJ=1"),
    "load": StartStopVariant("load", 0x03, "START=1 LOEJ=1"),
}

REQUEST_SENSE = (0x03, 0x00, 0x00, 0x00, 0xFC, 0x00)
MECHANISM_STATUS = (0xBD, 0, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument(
        "--variant",
        choices=sorted(VARIANTS),
        action="append",
        default=[],
        help="START STOP variant to run. Repeatable. Requires --allow-start-stop.",
    )
    parser.add_argument(
        "--allow-start-stop",
        action="store_true",
        help="Actually send the selected START STOP UNIT CDBs.",
    )
    parser.add_argument("--capture-before", dest="capture_before", action="store_true", default=True)
    parser.add_argument("--no-capture-before", dest="capture_before", action="store_false")
    parser.add_argument("--capture-after-count", type=int, default=3)
    parser.add_argument("--after-delay", type=float, default=0.15)
    parser.add_argument("--sense-after", action="store_true")
    parser.add_argument("--mechanism-status-before", action="store_true")
    parser.add_argument("--mechanism-status-after", action="store_true")
    parser.add_argument("--mode", type=lambda x: int(x, 0), default=0x01)
    parser.add_argument("--id", type=lambda x: int(x, 0), default=0x01, dest="buffer_id")
    parser.add_argument("--offset", type=lambda x: int(x, 0), default=0x070000)
    parser.add_argument("--length", type=lambda x: int(x, 0), default=0x10000)
    parser.add_argument("--chunk-size", type=lambda x: int(x, 0), default=0x400)
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)
    parser.add_argument("--chunk-delay", type=float, default=0.0)
    return parser.parse_args()


def command_record(
    args: argparse.Namespace,
    *,
    name: str,
    cdb: tuple[int, ...],
    request_len: int,
    out_path: Path,
) -> dict[str, Any]:
    data, record = run_sg_raw(
        sg_raw=args.sg_raw,
        device=args.device,
        cdb=cdb,
        request_len=request_len,
        timeout=args.timeout,
        process_timeout=args.process_timeout,
    )
    out_path.write_bytes(data)
    return {
        **record,
        "name": name,
        "response_path": str(out_path),
        "response_sha256": sha256_hex(data) if data else None,
        "cdb_text": cdb_text(cdb),
    }


def capture_named(args: argparse.Namespace, name: str, report: dict[str, Any]) -> None:
    path = args.out_dir / f"{len(report['captures']):02d}-{name}.window.bin"
    item = capture_window(args, path)
    item["name"] = name
    report["captures"].append(item)
    print(f"{name}: window sha256={item['sha256']}", flush=True)


def main() -> int:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    selected = [VARIANTS[name] for name in args.variant]
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "allow_start_stop": args.allow_start_stop,
        "selected_variants": [variant.name for variant in selected],
        "planned_cdbs": [
            {"name": variant.name, "note": variant.note, "cdb": cdb_text(variant.cdb)}
            for variant in selected
        ],
        "window": {
            "mode": args.mode,
            "id": args.buffer_id,
            "offset": args.offset,
            "length": args.length,
            "chunk_size": args.chunk_size,
        },
        "commands": [],
        "captures": [],
    }

    if not selected:
        print("no --variant selected; capturing baseline only", flush=True)
    elif not args.allow_start_stop:
        print("dry run: START STOP CDBs will not be sent without --allow-start-stop", flush=True)
        for item in report["planned_cdbs"]:
            print(f"would send {item['name']}: {item['cdb']} ({item['note']})", flush=True)

    if args.capture_before:
        capture_named(args, "baseline-before-start-stop", report)

    if args.mechanism_status_before:
        rec = command_record(
            args,
            name="mechanism-status-before",
            cdb=MECHANISM_STATUS,
            request_len=0xFC,
            out_path=args.out_dir / "mechanism-status-before.response.bin",
        )
        report["commands"].append(rec)
        print(
            f"mechanism-status-before: rc={rec['returncode']} good={rec['good']} len={rec['stdout_len']}",
            flush=True,
        )

    if args.allow_start_stop:
        for variant in selected:
            rec = command_record(
                args,
                name=f"start-stop-{variant.name}",
                cdb=variant.cdb,
                request_len=0,
                out_path=args.out_dir / f"start-stop-{variant.name}.response.bin",
            )
            report["commands"].append(rec)
            print(
                f"start-stop-{variant.name}: rc={rec['returncode']} good={rec['good']} "
                f"elapsed={rec['elapsed_s']}s",
                flush=True,
            )
            for index in range(args.capture_after_count):
                if args.after_delay:
                    time.sleep(args.after_delay)
                capture_named(args, f"after-start-stop-{variant.name}-{index:02d}", report)
            if args.sense_after:
                sense = command_record(
                    args,
                    name=f"request-sense-after-{variant.name}",
                    cdb=REQUEST_SENSE,
                    request_len=0xFC,
                    out_path=args.out_dir / f"request-sense-after-{variant.name}.response.bin",
                )
                report["commands"].append(sense)
                print(
                    f"request-sense-after-{variant.name}: rc={sense['returncode']} "
                    f"good={sense['good']} len={sense['stdout_len']}",
                    flush=True,
                )
                capture_named(args, f"after-sense-{variant.name}", report)
            if args.mechanism_status_after:
                mech = command_record(
                    args,
                    name=f"mechanism-status-after-{variant.name}",
                    cdb=MECHANISM_STATUS,
                    request_len=0xFC,
                    out_path=args.out_dir / f"mechanism-status-after-{variant.name}.response.bin",
                )
                report["commands"].append(mech)
                print(
                    f"mechanism-status-after-{variant.name}: rc={mech['returncode']} "
                    f"good={mech['good']} len={mech['stdout_len']}",
                    flush=True,
                )

    (args.out_dir / "summary.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
