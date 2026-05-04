#!/usr/bin/env python3
"""Capture normal-mode response/sense/work-window correlations.

This is a read-only normal-mode mapper. It sends a bounded set of standard
SCSI/MMC no-data-out commands, saves the direct response, optionally saves
REQUEST SENSE after failures, and snapshots the public normal work window after
each step.

The target is not broad device probing. It is a compact correlation matrix:
which host command fields change host-visible responses, sense state, or the
known XD13/LD5M work-window snippets around the packet/bridge paths.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import time
from collections import Counter, defaultdict
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
class CommandVariant:
    name: str
    cdb: tuple[int, ...]
    request_len: int = 0
    profile: str = "core"
    notes: str = ""


@dataclass(frozen=True)
class WatchPattern:
    name: str
    data: bytes
    notes: str = ""


REQUEST_SENSE = CommandVariant(
    "request-sense",
    (0x03, 0x00, 0x00, 0x00, 0xFC, 0x00),
    0xFC,
    "core",
    "standard sense read",
)


WATCH_PATTERNS: tuple[WatchPattern, ...] = (
    WatchPattern(
        "rec58-edge-a",
        bytes.fromhex("20ea2ab16891"),
        "record58 phase/adjacency watch signature",
    ),
    WatchPattern(
        "rec58-edge-b",
        bytes.fromhex("99d4493dc4cf"),
        "record58 phase/adjacency watch signature",
    ),
    WatchPattern(
        "rec58-edge-c",
        bytes.fromhex("b7a129b7d392"),
        "record58 phase/adjacency watch signature",
    ),
    WatchPattern(
        "rec58-bridge-long",
        bytes.fromhex("8a29e0c4540f30e011908a4ce0c3940e"),
        "XD13-derived bridge/packet snippet",
    ),
    WatchPattern(
        "rec58b-ctrl-long",
        bytes.fromhex("08eff6904000e020e7f9908ac6e09040"),
        "XD13-derived controller-register snippet",
    ),
    WatchPattern(
        "rec60-a",
        bytes.fromhex("4cfa6d151318"),
        "record60 shifted-phase watch signature",
    ),
    WatchPattern(
        "rec60-b",
        bytes.fromhex("28583441dfa8"),
        "record60 shifted-phase watch signature",
    ),
    WatchPattern(
        "rec60-c",
        bytes.fromhex("9b673c066ae4"),
        "record60 shifted-phase watch signature",
    ),
    WatchPattern(
        "rec60-bridge-long",
        bytes.fromhex("8a4de0904099f0908a4ee0904099f090"),
        "GET CONFIG-adjacent controller FIFO snippet",
    ),
)


def get_config(name: str, rt: int, feature: int, alloc: int = 0xFC) -> CommandVariant:
    return CommandVariant(
        name,
        (
            0x46,
            rt & 0x03,
            (feature >> 8) & 0xFF,
            feature & 0xFF,
            0x00,
            0x00,
            0x00,
            (alloc >> 8) & 0xFF,
            alloc & 0xFF,
            0x00,
        ),
        alloc,
        "core",
        f"GET CONFIGURATION rt={rt} start_feature=0x{feature:04x}",
    )


def mode_sense(name: str, page: int, alloc: int = 0xFC) -> CommandVariant:
    return CommandVariant(
        name,
        (0x5A, 0x00, page & 0x3F, 0x00, 0x00, 0x00, 0x00, (alloc >> 8) & 0xFF, alloc & 0xFF, 0x00),
        alloc,
        "core",
        f"MODE SENSE(10) page=0x{page:02x}",
    )


def get_event(name: str, klass: int, alloc: int = 0xFC) -> CommandVariant:
    return CommandVariant(
        name,
        (0x4A, 0x01, 0x00, 0x00, klass & 0xFF, 0x00, 0x00, (alloc >> 8) & 0xFF, alloc & 0xFF, 0x00),
        alloc,
        "core",
        f"GET EVENT STATUS NOTIFICATION class=0x{klass:02x}",
    )


def read_toc(name: str, fmt: int, alloc: int = 0xFC) -> CommandVariant:
    return CommandVariant(
        name,
        (0x43, 0x00, fmt & 0x0F, 0x00, 0x00, 0x00, 0x00, (alloc >> 8) & 0xFF, alloc & 0xFF, 0x00),
        alloc,
        "disc",
        f"READ TOC/PMA/ATIP format=0x{fmt:02x}",
    )


def read_dvd_structure(name: str, fmt: int, alloc: int = 0xFC) -> CommandVariant:
    return CommandVariant(
        name,
        (0xAD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, fmt & 0xFF, (alloc >> 8) & 0xFF, alloc & 0xFF, 0x00, 0x00),
        alloc,
        "disc",
        f"READ DVD STRUCTURE format=0x{fmt:02x}",
    )


COMMANDS: tuple[CommandVariant, ...] = (
    CommandVariant("baseline-test-unit-ready", (0x00, 0, 0, 0, 0, 0), 0, "core", "TEST UNIT READY"),
    REQUEST_SENSE,
    CommandVariant("inquiry-standard-36", (0x12, 0, 0, 0, 0x24, 0), 0x24, "core", "standard INQUIRY"),
    CommandVariant("inquiry-standard-96", (0x12, 0, 0, 0, 0x60, 0), 0x60, "core", "standard INQUIRY"),
    CommandVariant(
        "inquiry-extrainq-176",
        (0x12, 0, 0, 0, 0xB0, 0x40, 0, 0, 0, 0, 0, 0),
        0xB0,
        "core",
        "LiteOn EXTRAINQ-sized read",
    ),
    CommandVariant(
        "inquiry-extrainq-240",
        (0x12, 0, 0, 0, 0xF0, 0x40, 0, 0, 0, 0, 0, 0),
        0xF0,
        "core",
        "LiteOn EXTRAINQ maximal read",
    ),
    get_config("getcfg-current-0000", 2, 0x0000),
    get_config("getcfg-current-0001", 2, 0x0001),
    get_config("getcfg-current-0010", 2, 0x0010),
    get_config("getcfg-current-0020", 2, 0x0020),
    get_config("getcfg-current-0100", 2, 0x0100),
    get_config("getcfg-all-0000", 0, 0x0000),
    get_config("getcfg-one-0000", 1, 0x0000),
    get_config("getcfg-current-0000-len16", 2, 0x0000, 0x10),
    get_config("getcfg-current-0000-len64", 2, 0x0000, 0x40),
    mode_sense("modesense-read-error", 0x01),
    mode_sense("modesense-caching", 0x08),
    mode_sense("modesense-cd-device", 0x0D),
    mode_sense("modesense-cd-audio", 0x0E),
    mode_sense("modesense-power", 0x1A),
    mode_sense("modesense-fault-failure", 0x1C),
    mode_sense("modesense-capabilities", 0x2A),
    mode_sense("modesense-all", 0x3F),
    get_event("getevent-operational", 0x01),
    get_event("getevent-power", 0x02),
    get_event("getevent-external", 0x04),
    get_event("getevent-media", 0x10),
    get_event("getevent-multihost", 0x20),
    get_event("getevent-busy", 0x40),
    CommandVariant("read-format-capacities", (0x23, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC, "disc"),
    CommandVariant("read-disc-information", (0x51, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC, "disc"),
    CommandVariant("read-track-information-lba0", (0x52, 0x01, 0, 0, 0, 0, 0, 0, 0xFC, 0), 0xFC, "disc"),
    read_toc("readtoc-format-0", 0),
    read_toc("readtoc-format-1", 1),
    read_toc("readtoc-format-2", 2),
    read_toc("readtoc-format-4", 4),
    read_dvd_structure("readdvdstruct-format-0", 0),
    read_dvd_structure("readdvdstruct-format-1", 1),
    read_dvd_structure("readdvdstruct-format-2", 2),
    read_dvd_structure("readdvdstruct-format-ff", 0xFF),
    CommandVariant("mechanism-status", (0xBD, 0, 0, 0, 0, 0, 0, 0, 0, 0xFC, 0, 0), 0xFC, "disc"),
)


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def search_patterns(data: bytes) -> list[dict[str, Any]]:
    hits = []
    for pattern in WATCH_PATTERNS:
        offsets = find_all(data, pattern.data)
        if offsets:
            hits.append(
                {
                    "name": pattern.name,
                    "hex": pattern.data.hex(),
                    "offsets": offsets[:24],
                    "count": len(offsets),
                }
            )
    return hits


def sense_summary(data: bytes) -> dict[str, Any] | None:
    if len(data) < 3:
        return None
    response_code = data[0] & 0x7F
    if response_code in {0x70, 0x71}:
        sense_key = data[2] & 0x0F
        asc = data[12] if len(data) > 12 else None
        ascq = data[13] if len(data) > 13 else None
        return {
            "format": "fixed",
            "response_code": response_code,
            "sense_key": sense_key,
            "asc": asc,
            "ascq": ascq,
            "key_asc_ascq": (
                None
                if asc is None or ascq is None
                else f"{sense_key:02x}/{asc:02x}/{ascq:02x}"
            ),
        }
    if response_code in {0x72, 0x73}:
        sense_key = data[1] & 0x0F if len(data) > 1 else None
        asc = data[2] if len(data) > 2 else None
        ascq = data[3] if len(data) > 3 else None
        return {
            "format": "descriptor",
            "response_code": response_code,
            "sense_key": sense_key,
            "asc": asc,
            "ascq": ascq,
            "key_asc_ascq": (
                None
                if sense_key is None or asc is None or ascq is None
                else f"{sense_key:02x}/{asc:02x}/{ascq:02x}"
            ),
        }
    return {"format": "unknown", "response_code": response_code}


def compact_response(data: bytes) -> dict[str, Any]:
    return {
        "length": len(data),
        "sha256": sha256_hex(data) if data else None,
        "prefix_hex": data[:64].hex(),
        "watch_hits": search_patterns(data),
        "sense": sense_summary(data),
    }


def should_run_sense(mode: str, command_record: dict[str, Any]) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    return not bool(command_record.get("good"))


def capture_named_window(args: argparse.Namespace, path: Path) -> dict[str, Any]:
    record = capture_window(args, path)
    data = path.read_bytes()
    record["watch_hits"] = search_patterns(data)
    return record


def run_command(args: argparse.Namespace, command: CommandVariant, response_path: Path) -> tuple[bytes, dict[str, Any]]:
    response, record = run_sg_raw(
        sg_raw=args.sg_raw,
        device=args.device,
        cdb=command.cdb,
        request_len=command.request_len,
        timeout=args.timeout,
        process_timeout=args.process_timeout,
    )
    response_path.write_bytes(response)
    return response, record | compact_response(response) | {"response_path": str(response_path)}


def profile_rank(profile: str) -> int:
    return {"core": 0, "disc": 1, "extended": 2}.get(profile, 9)


def select_commands(args: argparse.Namespace) -> list[CommandVariant]:
    allowed = {"core"} if args.profile == "core" else {"core", "disc"} if args.profile == "disc" else {"core", "disc", "extended"}
    selected = [
        command
        for command in COMMANDS
        if command.profile in allowed
        and (not args.include or any(term in command.name for term in args.include))
        and not any(term in command.name for term in args.exclude)
    ]
    selected.sort(key=lambda command: (profile_rank(command.profile), command.name))
    return selected


def window_layout_key(window: dict[str, Any]) -> str:
    parts = []
    hits = {hit["name"]: hit["offsets"] for hit in window.get("watch_hits", [])}
    for pattern in WATCH_PATTERNS:
        offsets = hits.get(pattern.name) or []
        parts.append(f"{pattern.name}@{'-' if not offsets else '+0x%04x' % min(offsets)}")
    return " ".join(parts)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Response Matrix",
        "",
        "This report captures standard read-only normal-mode command responses,",
        "REQUEST SENSE after failures, and the public `READ BUFFER id=01`",
        "work-window. The purpose is to find a host-controlled normal-mode",
        "observation bit without touching CDD/F0 bytes.",
        "",
        "## Run",
        "",
        f"- device: `{report['device']}`",
        f"- timestamp UTC: `{report['timestamp_utc']}`",
        f"- profile: `{report['profile']}`",
        f"- cycles: `{report['cycles']}`",
        f"- shuffled per cycle: `{report['shuffle_per_cycle']}`",
        f"- shuffle seed: `{report['seed']}`",
        f"- sense mode: `{report['sense_mode']}`",
        "",
        "## Commands",
        "",
        "| name | profile | cdb | request | notes |",
        "|---|---|---|---:|---|",
    ]
    for command in report["commands"]:
        lines.append(
            f"| `{command['name']}` | `{command['profile']}` | `{command['cdb']}` | "
            f"{command['request_len']} | {command['notes']} |"
        )

    response_counts: dict[str, Counter[str]] = defaultdict(Counter)
    sense_counts: dict[str, Counter[str]] = defaultdict(Counter)
    layout_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for run in report["runs"]:
        command_name = run["command"]["name"]
        response_counts[command_name][run["response"]["sha256"] or "empty"] += 1
        if run.get("sense"):
            sense = run["sense"]["response"].get("sense") or {}
            sense_counts[command_name][sense.get("key_asc_ascq") or sense.get("format") or "none"] += 1
        layout_counts[command_name][window_layout_key(run["window"])] += 1
        if run.get("sense_window"):
            layout_counts[f"{command_name}/after-sense"][window_layout_key(run["sense_window"])] += 1

    lines.extend(["", "## Response Stability", "", "| command | response variants | top response | sense variants | window layouts |", "|---|---:|---|---|---:|"])
    for command in report["commands"]:
        name = command["name"]
        responses = response_counts.get(name, Counter())
        senses = sense_counts.get(name, Counter())
        layouts = layout_counts.get(name, Counter())
        top = responses.most_common(1)[0][0][:12] if responses else "-"
        sense_text = ", ".join(f"`{key}` x{count}" for key, count in senses.most_common(4)) or "-"
        lines.append(f"| `{name}` | {len(responses)} | `{top}` | {sense_text} | {len(layouts)} |")

    lines.extend(["", "## Interesting Window Layouts", ""])
    for name, counter in sorted(layout_counts.items()):
        if len(counter) <= 1:
            continue
        lines.append(f"### {name}")
        for layout, count in counter.most_common(8):
            lines.append(f"- x{count}: `{layout}`")
        lines.append("")

    lines.extend(["## Raw Files", "", f"- JSON: `{report['json_path']}`", ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--profile", choices=("core", "disc", "all"), default="core")
    parser.add_argument("--cycles", type=int, default=2)
    parser.add_argument(
        "--shuffle-per-cycle",
        action="store_true",
        help="Shuffle command order separately for each cycle using --seed.",
    )
    parser.add_argument("--seed", type=int, default=0xC0DE)
    parser.add_argument("--include", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--sense-mode", choices=("never", "on-failure", "always"), default="on-failure")
    parser.add_argument("--capture-sense-window", action="store_true")
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


def main() -> int:
    args = parse_args()
    if args.cycles < 1:
        raise SystemExit("--cycles must be >= 1")
    commands = select_commands(args)
    if not commands:
        raise SystemExit("no commands selected")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "summary.json"
    md_path = args.out_dir / "summary.md"
    report: dict[str, Any] = {
        "schema": "liteon-normal-response-matrix-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "profile": args.profile,
        "cycles": args.cycles,
        "shuffle_per_cycle": args.shuffle_per_cycle,
        "seed": args.seed,
        "sense_mode": args.sense_mode,
        "capture_sense_window": args.capture_sense_window,
        "json_path": str(json_path),
        "window": {
            "mode": args.mode,
            "id": args.buffer_id,
            "offset": args.offset,
            "length": args.length,
            "chunk_size": args.chunk_size,
        },
        "watch_patterns": [
            {"name": pattern.name, "hex": pattern.data.hex(), "notes": pattern.notes}
            for pattern in WATCH_PATTERNS
        ],
        "commands": [
            {
                "name": command.name,
                "profile": command.profile,
                "cdb": cdb_text(command.cdb),
                "request_len": command.request_len,
                "notes": command.notes,
            }
            for command in commands
        ],
        "runs": [],
    }

    index = 0
    rng = random.Random(args.seed)
    for cycle in range(args.cycles):
        cycle_commands = list(commands)
        if args.shuffle_per_cycle:
            rng.shuffle(cycle_commands)
        for cycle_position, command in enumerate(cycle_commands):
            stem = f"{index:03d}-cycle{cycle:02d}-{command.name}"
            response_path = args.out_dir / f"{stem}.response.bin"
            response, command_record = run_command(args, command, response_path)
            if args.delay:
                time.sleep(args.delay)
            window_path = args.out_dir / f"{stem}.window.bin"
            window_record = capture_named_window(args, window_path)

            run_item: dict[str, Any] = {
                "index": index,
                "cycle": cycle,
                "cycle_position": cycle_position,
                "command": {
                    "name": command.name,
                    "profile": command.profile,
                    "cdb": cdb_text(command.cdb),
                    "request_len": command.request_len,
                    "notes": command.notes,
                },
                "response": command_record,
                "window": window_record,
            }
            print(
                f"{index:03d} {command.name}: rc={command_record['returncode']} "
                f"good={command_record['good']} resp_len={len(response)} "
                f"window_hits={len(window_record['watch_hits'])}",
                flush=True,
            )

            if should_run_sense(args.sense_mode, command_record):
                if args.delay:
                    time.sleep(args.delay)
                sense_stem = f"{stem}-request-sense"
                sense_response, sense_record = run_command(
                    args,
                    REQUEST_SENSE,
                    args.out_dir / f"{sense_stem}.response.bin",
                )
                run_item["sense"] = {
                    "response": sense_record,
                    "response_len": len(sense_response),
                }
                print(
                    f"{index:03d} {command.name}: sense "
                    f"{(sense_record.get('sense') or {}).get('key_asc_ascq')}",
                    flush=True,
                )
                if args.capture_sense_window:
                    if args.delay:
                        time.sleep(args.delay)
                    sense_window = capture_named_window(
                        args,
                        args.out_dir / f"{sense_stem}.window.bin",
                    )
                    run_item["sense_window"] = sense_window

            report["runs"].append(run_item)
            json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            md_path.write_text(render_markdown(report).rstrip() + "\n")
            index += 1
            if args.delay:
                time.sleep(args.delay)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    md_path.write_text(render_markdown(report).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
