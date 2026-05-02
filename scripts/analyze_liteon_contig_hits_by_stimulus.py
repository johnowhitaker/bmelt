#!/usr/bin/env python3
"""Count normal work-window contig hits by capture state and stimulus."""

from __future__ import annotations

import argparse
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


def find_all(haystack: bytes, needle: bytes) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        offset = haystack.find(needle, start)
        if offset < 0:
            return out
        out.append(offset)
        start = offset + 1


def stimulus_name(path: Path) -> str:
    stem = path.name.removesuffix(".window.bin")
    parts = stem.split("-", 2)
    if len(parts) == 3 and parts[1].startswith("cycle"):
        return parts[2]
    return stem


def analyze_state(root: Path, sequence: bytes, chunks: list[bytes]) -> dict[str, Any]:
    files = sorted(root.glob("*.window.bin"))
    by_stimulus: dict[str, Any] = defaultdict(
        lambda: {
            "files": 0,
            "sequence_hits": 0,
            "sequence_offsets": Counter(),
            "chunk_count_histogram": Counter(),
            "chunk_offsets": [Counter() for _ in chunks],
        }
    )
    totals = {
        "files": 0,
        "sequence_hits": 0,
        "sequence_offsets": Counter(),
        "chunk_count_histogram": Counter(),
        "chunk_offsets": [Counter() for _ in chunks],
    }

    for path in files:
        data = path.read_bytes()
        stimulus = stimulus_name(path)
        rows = [by_stimulus[stimulus], totals]
        sequence_offsets = find_all(data, sequence)
        file_chunk_hits = 0
        chunk_offsets_by_index = [find_all(data, chunk) for chunk in chunks]
        for offsets in chunk_offsets_by_index:
            if offsets:
                file_chunk_hits += 1

        for row in rows:
            row["files"] += 1
            if sequence_offsets:
                row["sequence_hits"] += 1
                row["sequence_offsets"].update(sequence_offsets)
            row["chunk_count_histogram"][file_chunk_hits] += 1
            for index, offsets in enumerate(chunk_offsets_by_index):
                row["chunk_offsets"][index].update(offsets)

    def freeze(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "files": row["files"],
            "sequence_hits": row["sequence_hits"],
            "sequence_offsets": [
                {"offset": offset, "count": count}
                for offset, count in row["sequence_offsets"].most_common()
            ],
            "chunk_count_histogram": {
                str(count): hits for count, hits in sorted(row["chunk_count_histogram"].items())
            },
            "chunk_offsets": {
                str(index): [
                    {"offset": offset, "count": count}
                    for offset, count in offsets.most_common()
                ]
                for index, offsets in enumerate(row["chunk_offsets"])
            },
        }

    return {
        "path": str(root),
        "totals": freeze(totals),
        "stimuli": {name: freeze(row) for name, row in sorted(by_stimulus.items())},
    }


def fmt_offsets(items: list[dict[str, int]], limit: int = 4) -> str:
    if not items:
        return "-"
    return ", ".join(f"`+0x{item['offset']:04x}` x{item['count']}" for item in items[:limit])


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Contig Hits By Stimulus",
        "",
        f"Contig: `{report['contig_file']}`",
        f"Length: `{report['contig_bytes']}` bytes / `{report['chunk_count']}` chunks",
        "",
        "## Totals",
        "",
        "| state | captures | full-sequence hits | chunk-count histogram | sequence offsets |",
        "|---|---:|---:|---|---|",
    ]
    for label, state in report["states"].items():
        row = state["totals"]
        lines.append(
            f"| `{label}` | {row['files']} | {row['sequence_hits']} | "
            f"`{row['chunk_count_histogram']}` | {fmt_offsets(row['sequence_offsets'])} |"
        )

    lines.extend(["", "## By Stimulus", ""])
    for label, state in report["states"].items():
        lines.extend(
            [
                f"### {label}",
                "",
                "| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |",
                "|---|---:|---:|---|---|",
            ]
        )
        for stimulus, row in state["stimuli"].items():
            lines.append(
                f"| `{stimulus}` | {row['files']} | {row['sequence_hits']} | "
                f"`{row['chunk_count_histogram']}` | {fmt_offsets(row['sequence_offsets'])} |"
            )
        lines.append("")

    lines.extend(["## Chunk Offsets", ""])
    for label, state in report["states"].items():
        lines.append(f"### {label}")
        for index, offsets in state["totals"]["chunk_offsets"].items():
            lines.append(f"- chunk {index}: {fmt_offsets(offsets)}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contig", type=Path, required=True)
    parser.add_argument("--state", action="append", type=parse_state, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    sequence = args.contig.read_bytes()
    if len(sequence) % 0x40:
        raise ValueError(f"contig length must be a multiple of 0x40: {len(sequence)}")
    chunks = [sequence[offset : offset + 0x40] for offset in range(0, len(sequence), 0x40)]
    report = {
        "schema": "liteon-contig-hits-by-stimulus-v1",
        "contig_file": str(args.contig),
        "contig_bytes": len(sequence),
        "chunk_count": len(chunks),
        "chunk_prefixes": [chunk[:6].hex() for chunk in chunks],
        "states": {
            label: analyze_state(root, sequence, chunks)
            for label, root in args.state
        },
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
