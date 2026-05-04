#!/usr/bin/env python3
"""Track selected byte patterns in normal-mode work-window captures.

This is the lightweight companion to analyze_liteon_work_window_watch_chunks.py.
The older chunk watcher is useful when we have exact 64-byte tiles.  During
normal-mode triage we often only need stable 12-byte or 16-byte signatures from
the known-output reports, so this script accepts arbitrary hex patterns and
summarizes where they appear by stimulus.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_state(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("state must be LABEL=PATH")
    label, path = value.split("=", 1)
    if not label:
        raise argparse.ArgumentTypeError("state label cannot be empty")
    return label, Path(path)


def parse_pattern(value: str) -> tuple[str, bytes]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("pattern must be NAME=HEX")
    name, raw_hex = value.split("=", 1)
    compact = "".join(ch for ch in raw_hex if ch in "0123456789abcdefABCDEF")
    if not name:
        raise argparse.ArgumentTypeError("pattern name cannot be empty")
    if len(compact) < 8 or len(compact) % 2:
        raise argparse.ArgumentTypeError("pattern hex must be >=4 bytes and byte-aligned")
    return name, bytes.fromhex(compact)


def stimulus_name(path: Path) -> str:
    stem = path.name.removesuffix(".window.bin")
    parts = stem.split("-", 2)
    if len(parts) == 3 and parts[1].startswith("cycle"):
        return parts[2]
    return stem


def find_all(haystack: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        offset = haystack.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def layout_key(names: list[str], offsets_by_name: dict[str, list[int]]) -> str:
    parts = []
    for name in names:
        offsets = offsets_by_name.get(name, [])
        parts.append(f"{name}@{'-' if not offsets else f'+0x{min(offsets):04x}'}")
    return " ".join(parts)


def analyze_state(path: Path, patterns: list[tuple[str, bytes]]) -> dict[str, Any]:
    files = sorted(path.glob("*.window.bin"))
    if not files:
        raise SystemExit(f"no *.window.bin captures in {path}")

    names = [name for name, _pattern in patterns]
    totals: dict[str, Any] = {
        "files": 0,
        "pattern_offsets": {name: Counter() for name in names},
        "layout_histogram": Counter(),
    }
    by_stimulus: dict[str, Any] = defaultdict(
        lambda: {
            "files": 0,
            "pattern_offsets": {name: Counter() for name in names},
            "layout_histogram": Counter(),
        }
    )

    for file in files:
        data = file.read_bytes()
        offsets_by_name = {name: find_all(data, pattern) for name, pattern in patterns}
        stim = stimulus_name(file)
        for row in (totals, by_stimulus[stim]):
            row["files"] += 1
            row["layout_histogram"][layout_key(names, offsets_by_name)] += 1
            for name, offsets in offsets_by_name.items():
                row["pattern_offsets"][name].update(offsets)

    def freeze(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "files": row["files"],
            "pattern_offsets": {
                name: [
                    {"offset": offset, "count": count}
                    for offset, count in counter.most_common()
                ]
                for name, counter in row["pattern_offsets"].items()
            },
            "layout_histogram": dict(row["layout_histogram"].most_common()),
        }

    return {
        "path": str(path),
        "totals": freeze(totals),
        "stimuli": {name: freeze(row) for name, row in sorted(by_stimulus.items())},
    }


def fmt_offsets(items: list[dict[str, int]], limit: int = 8) -> str:
    if not items:
        return "-"
    return ", ".join(f"`+0x{item['offset']:04x}` x{item['count']}" for item in items[:limit])


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Watch Patterns",
        "",
        "## Patterns",
        "",
        "| name | bytes | hex |",
        "|---|---:|---|",
    ]
    for item in report["patterns"]:
        lines.append(f"| `{item['name']}` | {item['length']} | `{item['hex']}` |")

    lines.extend(["", "## Totals", ""])
    for label, state in report["states"].items():
        totals = state["totals"]
        lines.extend(
            [
                f"### {label}",
                "",
                f"- captures: `{totals['files']}`",
                f"- layouts: `{totals['layout_histogram']}`",
                "",
                "| pattern | offsets |",
                "|---|---|",
            ]
        )
        for name, offsets in totals["pattern_offsets"].items():
            lines.append(f"| `{name}` | {fmt_offsets(offsets)} |")
        lines.append("")

    lines.extend(["## By Stimulus", ""])
    for label, state in report["states"].items():
        lines.append(f"### {label}")
        for stimulus, row in state["stimuli"].items():
            lines.extend(
                [
                    "",
                    f"#### {stimulus}",
                    "",
                    f"- captures: `{row['files']}`",
                    f"- layouts: `{row['layout_histogram']}`",
                    "",
                    "| pattern | offsets |",
                    "|---|---|",
                ]
            )
            for name, offsets in row["pattern_offsets"].items():
                lines.append(f"| `{name}` | {fmt_offsets(offsets)} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", action="append", type=parse_state, required=True)
    parser.add_argument("--pattern", action="append", type=parse_pattern, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    report = {
        "schema": "liteon-work-window-watch-patterns-v1",
        "patterns": [
            {"name": name, "length": len(pattern), "hex": pattern.hex()}
            for name, pattern in args.pattern
        ],
        "states": {label: analyze_state(path, args.pattern) for label, path in args.state},
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
