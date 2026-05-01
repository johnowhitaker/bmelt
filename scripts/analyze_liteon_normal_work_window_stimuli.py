#!/usr/bin/env python3
"""Summarize normal work-window stimulus captures."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def diff_runs(reference: bytes, candidate: bytes) -> list[tuple[int, int]]:
    diffs = [i for i, (a, b) in enumerate(zip(reference, candidate)) if a != b]
    if not diffs:
        return []
    runs: list[tuple[int, int]] = []
    start = prev = diffs[0]
    for offset in diffs[1:]:
        if offset == prev + 1:
            prev = offset
            continue
        runs.append((start, prev + 1))
        start = prev = offset
    runs.append((start, prev + 1))
    return runs


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Stimulus Analysis",
        "",
        f"Capture directory: `{report['capture_dir']}`",
        "",
        "## Captures",
        "",
        "| index | name | sha256 | diff vs baseline | largest diff run |",
        "|---:|---|---|---:|---:|",
    ]
    for item in report["captures"]:
        largest = max((run["length"] for run in item["diff_runs"]), default=0)
        lines.append(
            f"| {item['index']} | `{item['name']}` | `{item['sha256'][:16]}` | "
            f"{item['diff_count']} | `{largest:#x}` |"
        )

    lines += [
        "",
        "## Variable Pages",
        "",
        "| page | variable bytes |",
        "|---:|---:|",
    ]
    for page in report["variable_pages"][:32]:
        lines.append(f"| `+0x{page['page_start']:04x}` | {page['count']} |")

    lines += [
        "",
        "## Variable Runs",
        "",
    ]
    for run in report["variable_runs"][:80]:
        lines.append(
            f"- `+0x{run['start']:04x}..+0x{run['end']:04x}` len `{run['length']:#x}`"
        )
    if report.get("chunk_inventory"):
        inventory = report["chunk_inventory"]
        lines += [
            "",
            "## Moving Tile Inventory",
            "",
            f"Chunk size: `{inventory['chunk_size']:#x}`",
            f"Informative unique chunks: {inventory['unique_informative_chunks']}",
            f"Chunks seen more than once: {inventory['reused_informative_chunks']}",
            f"Chunks seen at multiple offsets: {inventory['moving_informative_chunks']}",
            "",
            "| index | name | informative chunks | new vs baseline |",
            "|---:|---|---:|---:|",
        ]
        for item in inventory["per_capture"]:
            lines.append(
                f"| {item['index']} | `{item['name']}` | "
                f"{item['informative_chunks']} | {item['new_vs_baseline']} |"
            )
        lines += [
            "",
            "Top moving chunks:",
            "",
        ]
        for chunk in inventory["top_moving_chunks"][:32]:
            offsets = ", ".join(f"`+0x{offset:04x}`" for offset in chunk["offsets"][:8])
            if len(chunk["offsets"]) > 8:
                offsets += ", ..."
            lines.append(
                f"- `{chunk['sha256'][:16]}` observed {chunk['observations']} times "
                f"in {chunk['capture_count']} captures at {offsets}; "
                f"sample `{chunk['sample_hex']}`"
            )
    lines.append("")
    return "\n".join(lines)


def is_informative_chunk(chunk: bytes) -> bool:
    return len(set(chunk)) > 1


def chunk_inventory(
    captures: list[tuple[Path, bytes]], chunk_size: int
) -> dict[str, Any]:
    by_hash: dict[str, dict[str, Any]] = {}
    per_capture: list[dict[str, Any]] = []

    baseline_chunks: set[str] = set()
    for index, (path, data) in enumerate(captures):
        hashes: set[str] = set()
        for offset in range(0, len(data) - chunk_size + 1, chunk_size):
            chunk = data[offset : offset + chunk_size]
            if not is_informative_chunk(chunk):
                continue
            digest = sha256_hex(chunk)
            hashes.add(digest)
            item = by_hash.setdefault(
                digest,
                {
                    "sha256": digest,
                    "sample_hex": chunk[:16].hex(),
                    "observations": 0,
                    "captures": set(),
                    "offsets": set(),
                },
            )
            item["observations"] += 1
            item["captures"].add(index)
            item["offsets"].add(offset)
        if index == 0:
            baseline_chunks = set(hashes)
        per_capture.append(
            {
                "index": index,
                "name": path.name.removesuffix(".window.bin"),
                "informative_chunks": len(hashes),
                "new_vs_baseline": len(hashes - baseline_chunks),
            }
        )

    reused = [
        item for item in by_hash.values() if item["observations"] > 1
    ]
    moving = [
        item for item in by_hash.values() if len(item["offsets"]) > 1
    ]
    moving_sorted = sorted(
        moving,
        key=lambda item: (-len(item["captures"]), -item["observations"], min(item["offsets"])),
    )

    def render_chunk(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "sha256": item["sha256"],
            "sample_hex": item["sample_hex"],
            "observations": item["observations"],
            "capture_count": len(item["captures"]),
            "captures": sorted(item["captures"]),
            "offsets": sorted(item["offsets"]),
        }

    return {
        "chunk_size": chunk_size,
        "unique_informative_chunks": len(by_hash),
        "reused_informative_chunks": len(reused),
        "moving_informative_chunks": len(moving),
        "per_capture": per_capture,
        "top_moving_chunks": [render_chunk(item) for item in moving_sorted[:128]],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--chunk-size", type=lambda value: int(value, 0), default=0x40)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = sorted(args.capture_dir.glob("*.window.bin"))
    if not paths:
        raise SystemExit(f"no *.window.bin captures in {args.capture_dir}")
    captures = [(path, path.read_bytes()) for path in paths]
    baseline = captures[0][1]

    all_values: dict[int, set[int]] = defaultdict(set)
    for _, data in captures:
        for offset, byte in enumerate(data):
            all_values[offset].add(byte)
    variable_offsets = sorted(offset for offset, values in all_values.items() if len(values) > 1)

    variable_runs: list[dict[str, int]] = []
    if variable_offsets:
        start = prev = variable_offsets[0]
        for offset in variable_offsets[1:]:
            if offset == prev + 1:
                prev = offset
                continue
            variable_runs.append({"start": start, "end": prev + 1, "length": prev + 1 - start})
            start = prev = offset
        variable_runs.append({"start": start, "end": prev + 1, "length": prev + 1 - start})

    pages: dict[int, int] = defaultdict(int)
    for offset in variable_offsets:
        pages[offset & ~0xFF] += 1

    report: dict[str, Any] = {
        "capture_dir": str(args.capture_dir),
        "capture_count": len(captures),
        "captures": [],
        "variable_offset_count": len(variable_offsets),
        "variable_pages": [
            {"page_start": page, "count": count}
            for page, count in sorted(pages.items(), key=lambda item: (-item[1], item[0]))
        ],
        "variable_runs": variable_runs,
        "chunk_inventory": chunk_inventory(captures, args.chunk_size),
    }

    for index, (path, data) in enumerate(captures):
        runs = diff_runs(baseline, data)
        report["captures"].append(
            {
                "index": index,
                "name": path.name.removesuffix(".window.bin"),
                "path": str(path),
                "size": len(data),
                "sha256": sha256_hex(data),
                "diff_count": sum(end - start for start, end in runs),
                "diff_runs": [
                    {"start": start, "end": end, "length": end - start}
                    for start, end in runs[:128]
                ],
            }
        )

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render(report))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
