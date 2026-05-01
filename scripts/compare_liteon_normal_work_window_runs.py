#!/usr/bin/env python3
"""Compare two normal work-window capture runs by informative fixed-size chunks."""

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


def load_corpus(capture_dir: Path, chunk_size: int) -> dict[str, Any]:
    paths = sorted(capture_dir.glob("*.window.bin"))
    if not paths:
        raise SystemExit(f"no *.window.bin captures in {capture_dir}")

    chunks: dict[str, dict[str, Any]] = {}
    captures: list[dict[str, Any]] = []
    for index, path in enumerate(paths):
        data = path.read_bytes()
        capture_hashes: set[str] = set()
        for offset in range(0, len(data) - chunk_size + 1, chunk_size):
            chunk = data[offset : offset + chunk_size]
            if not is_informative_chunk(chunk):
                continue
            digest = sha256_hex(chunk)
            capture_hashes.add(digest)
            item = chunks.setdefault(
                digest,
                {
                    "sha256": digest,
                    "sample_hex": chunk[:16].hex(),
                    "observations": [],
                },
            )
            item["observations"].append(
                {
                    "capture_index": index,
                    "capture_name": path.name.removesuffix(".window.bin"),
                    "offset": offset,
                }
            )
        captures.append(
            {
                "index": index,
                "name": path.name.removesuffix(".window.bin"),
                "informative_chunks": len(capture_hashes),
                "chunks": sorted(capture_hashes),
            }
        )
    return {
        "capture_dir": str(capture_dir),
        "chunk_size": chunk_size,
        "captures": captures,
        "chunks": chunks,
    }


def summarize_new_chunks(
    target: dict[str, Any], reference_hashes: set[str]
) -> dict[str, Any]:
    new_hashes = sorted(set(target["chunks"]) - reference_hashes)
    by_page: dict[int, int] = defaultdict(int)
    by_capture: dict[int, int] = defaultdict(int)
    chunks = []
    for digest in new_hashes:
        item = target["chunks"][digest]
        for obs in item["observations"]:
            by_page[obs["offset"] & ~0xFF] += 1
            by_capture[obs["capture_index"]] += 1
        offsets = sorted({obs["offset"] for obs in item["observations"]})
        capture_names = sorted({obs["capture_name"] for obs in item["observations"]})
        chunks.append(
            {
                "sha256": digest,
                "sample_hex": item["sample_hex"],
                "observations": len(item["observations"]),
                "capture_names": capture_names,
                "offsets": offsets,
            }
        )
    return {
        "new_chunk_count": len(new_hashes),
        "new_chunks": chunks,
        "by_page": [
            {"page_start": page, "count": count}
            for page, count in sorted(by_page.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "by_capture": [
            {
                "index": capture["index"],
                "name": capture["name"],
                "new_chunk_observations": by_capture.get(capture["index"], 0),
            }
            for capture in target["captures"]
        ],
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Run Comparison",
        "",
        f"Reference: `{report['reference']['capture_dir']}`",
        f"Target: `{report['target']['capture_dir']}`",
        f"Chunk size: `{report['chunk_size']:#x}`",
        "",
        "## Summary",
        "",
        f"Reference informative chunks: {report['reference_unique_chunks']}",
        f"Target informative chunks: {report['target_unique_chunks']}",
        f"Shared informative chunks: {report['shared_chunks']}",
        f"Target-only informative chunks: {report['target_only']['new_chunk_count']}",
        f"Reference-only informative chunks: {report['reference_only']['new_chunk_count']}",
        "",
        "## Target-Only Observations",
        "",
        "| capture | target-only chunk observations |",
        "|---|---:|",
    ]
    for item in report["target_only"]["by_capture"]:
        lines.append(f"| `{item['name']}` | {item['new_chunk_observations']} |")
    lines += [
        "",
        "Top target-only pages:",
        "",
    ]
    for page in report["target_only"]["by_page"][:32]:
        lines.append(f"- `+0x{page['page_start']:04x}`: {page['count']} observations")
    lines += [
        "",
        "Target-only chunks:",
        "",
    ]
    for chunk in report["target_only"]["new_chunks"][:64]:
        offsets = ", ".join(f"`+0x{offset:04x}`" for offset in chunk["offsets"][:8])
        if len(chunk["offsets"]) > 8:
            offsets += ", ..."
        captures = ", ".join(f"`{name}`" for name in chunk["capture_names"][:4])
        if len(chunk["capture_names"]) > 4:
            captures += ", ..."
        lines.append(
            f"- `{chunk['sha256'][:16]}` obs {chunk['observations']} at {offsets}; "
            f"{captures}; sample `{chunk['sample_hex']}`"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--chunk-size", type=lambda value: int(value, 0), default=0x40)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reference = load_corpus(args.reference, args.chunk_size)
    target = load_corpus(args.target, args.chunk_size)
    reference_hashes = set(reference["chunks"])
    target_hashes = set(target["chunks"])

    report: dict[str, Any] = {
        "chunk_size": args.chunk_size,
        "reference": {
            "capture_dir": reference["capture_dir"],
            "capture_count": len(reference["captures"]),
        },
        "target": {
            "capture_dir": target["capture_dir"],
            "capture_count": len(target["captures"]),
        },
        "reference_unique_chunks": len(reference_hashes),
        "target_unique_chunks": len(target_hashes),
        "shared_chunks": len(reference_hashes & target_hashes),
        "target_only": summarize_new_chunks(target, reference_hashes),
        "reference_only": summarize_new_chunks(reference, target_hashes),
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
