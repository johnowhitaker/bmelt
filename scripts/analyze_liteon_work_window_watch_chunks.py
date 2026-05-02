#!/usr/bin/env python3
"""Track selected 64-byte work-window chunks by stimulus and state.

This is a compact phase/adjacency analyzer for normal-mode READ BUFFER id=01
work-window captures. It is intentionally simpler than the broad state-delta
tool: pass the exact chunks you care about, and it reports where they appear,
which stimulus made them visible, and whether the listed chunks form adjacent
64-byte runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_state(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("state must be LABEL=PATH")
    label, raw_path = value.split("=", 1)
    if not label:
        raise argparse.ArgumentTypeError("state label cannot be empty")
    return label, Path(raw_path)


def parse_chunk(value: str) -> tuple[str, bytes]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("chunk must be NAME=HEX")
    name, raw_hex = value.split("=", 1)
    if not name:
        raise argparse.ArgumentTypeError("chunk name cannot be empty")
    compact = "".join(ch for ch in raw_hex if ch in "0123456789abcdefABCDEF")
    if len(compact) != 128:
        raise argparse.ArgumentTypeError("chunk hex must be exactly 64 bytes")
    return name, bytes.fromhex(compact)


def parse_chunk_file(value: str) -> tuple[str, bytes]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("chunk-file must be NAME=PATH[:INDEX]")
    name, raw_spec = value.split("=", 1)
    if not name:
        raise argparse.ArgumentTypeError("chunk-file name cannot be empty")
    path_text, sep, index_text = raw_spec.rpartition(":")
    if sep and index_text.isdigit():
        path = Path(path_text)
        index = int(index_text)
    else:
        path = Path(raw_spec)
        index = 0
    data = path.read_bytes()
    start = index * 0x40
    end = start + 0x40
    if end > len(data):
        raise argparse.ArgumentTypeError(f"{path} does not contain chunk index {index}")
    return name, data[start:end]


def stimulus_name(path: Path) -> str:
    stem = path.name.removesuffix(".window.bin")
    parts = stem.split("-", 2)
    if len(parts) == 3 and parts[1].startswith("cycle"):
        return parts[2]
    return stem


def find_all(haystack: bytes, needle: bytes) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        offset = haystack.find(needle, start)
        if offset < 0:
            return out
        out.append(offset)
        start = offset + 1


def first_offset(offsets: list[int]) -> int | None:
    if not offsets:
        return None
    return min(offsets)


def layout_key(chunk_names: list[str], offsets_by_name: dict[str, list[int]]) -> str:
    parts = []
    for name in chunk_names:
        offset = first_offset(offsets_by_name.get(name, []))
        parts.append(f"{name}@{'-' if offset is None else f'+0x{offset:04x}'}")
    return " ".join(parts)


def adjacency_key(chunk_names: list[str], offsets_by_name: dict[str, list[int]]) -> str:
    offsets = [first_offset(offsets_by_name.get(name, [])) for name in chunk_names]
    if any(offset is None for offset in offsets):
        return "missing"
    adjacent = [
        int(offsets[index] + 0x40 == offsets[index + 1])  # type: ignore[operator]
        for index in range(len(offsets) - 1)
    ]
    if all(adjacent):
        return "full-adjacent"
    return "edge-bits:" + "".join(str(bit) for bit in adjacent)


def analyze_state(root: Path, chunks: list[tuple[str, bytes]]) -> dict[str, Any]:
    paths = sorted(root.glob("*.window.bin"))
    if not paths:
        raise SystemExit(f"no *.window.bin captures in {root}")
    chunk_names = [name for name, _chunk in chunks]
    totals: dict[str, Any] = {
        "files": 0,
        "chunk_offsets": {name: Counter() for name in chunk_names},
        "layout_histogram": Counter(),
        "adjacency_histogram": Counter(),
    }
    by_stimulus: dict[str, Any] = defaultdict(
        lambda: {
            "files": 0,
            "chunk_offsets": {name: Counter() for name in chunk_names},
            "layout_histogram": Counter(),
            "adjacency_histogram": Counter(),
        }
    )

    for path in paths:
        data = path.read_bytes()
        offsets_by_name = {name: find_all(data, chunk) for name, chunk in chunks}
        stim = stimulus_name(path)
        for row in (totals, by_stimulus[stim]):
            row["files"] += 1
            for name, offsets in offsets_by_name.items():
                row["chunk_offsets"][name].update(offsets)
            row["layout_histogram"][layout_key(chunk_names, offsets_by_name)] += 1
            row["adjacency_histogram"][adjacency_key(chunk_names, offsets_by_name)] += 1

    def freeze(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "files": row["files"],
            "chunk_offsets": {
                name: [
                    {"offset": offset, "count": count}
                    for offset, count in counter.most_common()
                ]
                for name, counter in row["chunk_offsets"].items()
            },
            "layout_histogram": dict(row["layout_histogram"].most_common()),
            "adjacency_histogram": dict(row["adjacency_histogram"].most_common()),
        }

    return {
        "path": str(root),
        "totals": freeze(totals),
        "stimuli": {name: freeze(row) for name, row in sorted(by_stimulus.items())},
    }


def fmt_offsets(items: list[dict[str, int]], limit: int = 5) -> str:
    if not items:
        return "-"
    return ", ".join(f"`+0x{item['offset']:04x}` x{item['count']}" for item in items[:limit])


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Watch Chunks",
        "",
        "## Chunks",
        "",
        "| name | sha256 | first bytes |",
        "|---|---|---|",
    ]
    for item in report["chunks"]:
        lines.append(f"| `{item['name']}` | `{item['sha256']}` | `{item['first16_hex']}` |")

    lines.extend(["", "## Totals", ""])
    for label, state in report["states"].items():
        totals = state["totals"]
        lines.extend(
            [
                f"### {label}",
                "",
                f"- captures: `{totals['files']}`",
                f"- adjacency: `{totals['adjacency_histogram']}`",
                f"- layouts: `{totals['layout_histogram']}`",
                "",
                "| chunk | offsets |",
                "|---|---|",
            ]
        )
        for name, offsets in totals["chunk_offsets"].items():
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
                    f"- adjacency: `{row['adjacency_histogram']}`",
                    f"- layouts: `{row['layout_histogram']}`",
                    "",
                    "| chunk | offsets |",
                    "|---|---|",
                ]
            )
            for name, offsets in row["chunk_offsets"].items():
                lines.append(f"| `{name}` | {fmt_offsets(offsets)} |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", action="append", type=parse_state, required=True)
    parser.add_argument("--chunk", action="append", type=parse_chunk, default=[])
    parser.add_argument("--chunk-file", action="append", type=parse_chunk_file, default=[])
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    chunks = args.chunk + args.chunk_file
    if not chunks:
        raise SystemExit("at least one --chunk or --chunk-file is required")
    for name, chunk in chunks:
        if len(chunk) != 0x40:
            raise ValueError(f"{name} is {len(chunk)} bytes, expected 64")

    report = {
        "schema": "liteon-work-window-watch-chunks-v1",
        "chunks": [
            {
                "name": name,
                "sha256": hashlib.sha256(chunk).hexdigest(),
                "first16_hex": chunk[:16].hex(),
            }
            for name, chunk in chunks
        ],
        "states": {label: analyze_state(path, chunks) for label, path in args.state},
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(render_md(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
