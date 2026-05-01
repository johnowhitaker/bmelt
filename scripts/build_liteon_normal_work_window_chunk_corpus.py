#!/usr/bin/env python3
"""Build a unique-chunk corpus from normal work-window capture runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_informative_chunk(chunk: bytes) -> bool:
    return len(set(chunk)) > 1


def capture_label(run_name: str, path: Path) -> str:
    return f"{run_name}/{path.name.removesuffix('.window.bin')}"


def load_run(run_dir: Path, chunk_size: int) -> tuple[str, list[dict[str, Any]]]:
    paths = sorted(run_dir.glob("*.window.bin"))
    if not paths:
        raise SystemExit(f"no *.window.bin captures in {run_dir}")
    run_name = run_dir.name
    captures: list[dict[str, Any]] = []
    for capture_index, path in enumerate(paths):
        data = path.read_bytes()
        chunks = []
        for offset in range(0, len(data) - chunk_size + 1, chunk_size):
            chunk = data[offset : offset + chunk_size]
            if not is_informative_chunk(chunk):
                continue
            chunks.append(
                {
                    "sha256": sha256_hex(chunk),
                    "offset": offset,
                    "sample_hex": chunk[:16].hex(),
                }
            )
        captures.append(
            {
                "run": run_name,
                "capture_index": capture_index,
                "capture_name": path.name.removesuffix(".window.bin"),
                "label": capture_label(run_name, path),
                "chunks": chunks,
            }
        )
    return run_name, captures


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Chunk Corpus",
        "",
        f"Chunk size: `{report['chunk_size']:#x}`",
        f"Runs: {len(report['runs'])}",
        f"Captures: {report['capture_count']}",
        f"Unique informative chunks: {report['unique_chunks']}",
        "",
        "## Runs",
        "",
        "| run | captures | unique chunks | new vs previous runs |",
        "|---|---:|---:|---:|",
    ]
    for run in report["runs"]:
        lines.append(
            f"| `{run['name']}` | {run['capture_count']} | "
            f"{run['unique_chunks']} | {run['new_vs_previous']} |"
        )
    lines += [
        "",
        "## Top Pages",
        "",
        "| page | observations | unique chunks |",
        "|---:|---:|---:|",
    ]
    for page in report["pages"][:32]:
        lines.append(
            f"| `+0x{page['page_start']:04x}` | {page['observations']} | {page['unique_chunks']} |"
        )
    lines += [
        "",
        "## Most Observed Chunks",
        "",
    ]
    for chunk in report["chunks"][:64]:
        offsets = ", ".join(f"`+0x{offset:04x}`" for offset in chunk["offsets"][:8])
        if len(chunk["offsets"]) > 8:
            offsets += ", ..."
        labels = ", ".join(f"`{label}`" for label in chunk["labels"][:3])
        if len(chunk["labels"]) > 3:
            labels += ", ..."
        lines.append(
            f"- `{chunk['sha256'][:16]}` obs {chunk['observations']} "
            f"runs {chunk['run_count']} at {offsets}; {labels}; sample `{chunk['sample_hex']}`"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--chunk-size", type=lambda value: int(value, 0), default=0x40)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chunks: dict[str, dict[str, Any]] = {}
    pages: dict[int, dict[str, Any]] = defaultdict(lambda: {"observations": 0, "chunks": set()})
    run_summaries: list[dict[str, Any]] = []
    seen_before: set[str] = set()
    capture_count = 0

    for run_dir in args.run_dirs:
        run_name, captures = load_run(run_dir, args.chunk_size)
        capture_count += len(captures)
        run_hashes: set[str] = set()
        for capture in captures:
            for obs in capture["chunks"]:
                digest = obs["sha256"]
                run_hashes.add(digest)
                item = chunks.setdefault(
                    digest,
                    {
                        "sha256": digest,
                        "sample_hex": obs["sample_hex"],
                        "observations": 0,
                        "runs": set(),
                        "labels": set(),
                        "offsets": set(),
                    },
                )
                item["observations"] += 1
                item["runs"].add(run_name)
                item["labels"].add(capture["label"])
                item["offsets"].add(obs["offset"])
                page = obs["offset"] & ~0xFF
                pages[page]["observations"] += 1
                pages[page]["chunks"].add(digest)
        run_summaries.append(
            {
                "name": run_name,
                "capture_count": len(captures),
                "unique_chunks": len(run_hashes),
                "new_vs_previous": len(run_hashes - seen_before),
            }
        )
        seen_before |= run_hashes

    rendered_chunks = []
    for item in chunks.values():
        rendered_chunks.append(
            {
                "sha256": item["sha256"],
                "sample_hex": item["sample_hex"],
                "observations": item["observations"],
                "run_count": len(item["runs"]),
                "runs": sorted(item["runs"]),
                "labels": sorted(item["labels"]),
                "offsets": sorted(item["offsets"]),
            }
        )
    rendered_chunks.sort(
        key=lambda item: (-item["observations"], -item["run_count"], item["sha256"])
    )

    rendered_pages = [
        {
            "page_start": page,
            "observations": item["observations"],
            "unique_chunks": len(item["chunks"]),
        }
        for page, item in pages.items()
    ]
    rendered_pages.sort(key=lambda item: (-item["unique_chunks"], -item["observations"], item["page_start"]))

    report: dict[str, Any] = {
        "chunk_size": args.chunk_size,
        "runs": run_summaries,
        "capture_count": capture_count,
        "unique_chunks": len(chunks),
        "pages": rendered_pages,
        "chunks": rendered_chunks,
    }

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
