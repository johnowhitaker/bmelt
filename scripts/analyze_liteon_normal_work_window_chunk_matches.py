#!/usr/bin/env python3
"""Match normal work-window chunks against static reference binaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_informative_chunk(chunk: bytes) -> bool:
    return len(set(chunk)) > 1


def load_chunks(run_dirs: list[Path], chunk_size: int) -> dict[str, dict[str, Any]]:
    chunks: dict[str, dict[str, Any]] = {}
    for run_dir in run_dirs:
        for path in sorted(run_dir.glob("*.window.bin")):
            data = path.read_bytes()
            for offset in range(0, len(data) - chunk_size + 1, chunk_size):
                chunk = data[offset : offset + chunk_size]
                if not is_informative_chunk(chunk):
                    continue
                digest = sha256_hex(chunk)
                item = chunks.setdefault(
                    digest,
                    {
                        "sha256": digest,
                        "data": chunk,
                        "sample_hex": chunk[:16].hex(),
                        "observations": [],
                    },
                )
                item["observations"].append(
                    {
                        "run": run_dir.name,
                        "capture": path.name.removesuffix(".window.bin"),
                        "offset": offset,
                    }
                )
    return chunks


def parse_reference(value: str) -> tuple[str, Path]:
    if "=" not in value:
        path = Path(value)
        return path.stem, path
    name, path_text = value.split("=", 1)
    return name, Path(path_text)


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Chunk Static Matches",
        "",
        f"Chunk size: `{report['chunk_size']:#x}`",
        f"Unique informative chunks: {report['unique_chunks']}",
        "",
        "## Reference Matches",
        "",
        "| reference | size | exact chunk matches |",
        "|---|---:|---:|",
    ]
    for ref in report["references"]:
        lines.append(f"| `{ref['name']}` | `{ref['size']:#x}` | {ref['match_count']} |")
    lines += [
        "",
        f"Chunks matching at least one reference: {report['matched_any_count']}",
        f"Chunks not matching any reference: {report['unmatched_any_count']}",
        "",
        "## Unmatched Observation Pages",
        "",
        "| page | observations |",
        "|---:|---:|",
    ]
    for page in report["unmatched_pages"][:32]:
        lines.append(f"| `+0x{page['page_start']:04x}` | {page['observations']} |")
    lines += [
        "",
        "## Most Observed Unmatched Chunks",
        "",
    ]
    for chunk in report["top_unmatched_chunks"][:64]:
        offsets = ", ".join(f"`+0x{offset:04x}`" for offset in chunk["offsets"][:8])
        if len(chunk["offsets"]) > 8:
            offsets += ", ..."
        lines.append(
            f"- `{chunk['sha256'][:16]}` obs {chunk['observations']} at {offsets}; "
            f"sample `{chunk['sample_hex']}`"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--reference", action="append", default=[], help="NAME=PATH or PATH")
    parser.add_argument("--chunk-size", type=lambda value: int(value, 0), default=0x40)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.reference:
        raise SystemExit("provide at least one --reference NAME=PATH")
    chunks = load_chunks(args.run_dirs, args.chunk_size)
    reference_reports = []
    matched_any: set[str] = set()
    for ref_arg in args.reference:
        name, path = parse_reference(ref_arg)
        data = path.read_bytes()
        matches = []
        for digest, item in chunks.items():
            position = data.find(item["data"])
            if position != -1:
                matches.append({"sha256": digest, "position": position})
                matched_any.add(digest)
        reference_reports.append(
            {
                "name": name,
                "path": str(path),
                "size": len(data),
                "match_count": len(matches),
                "matches": sorted(matches, key=lambda item: item["position"]),
            }
        )

    unmatched = set(chunks) - matched_any
    page_counts: Counter[int] = Counter()
    for digest in unmatched:
        for obs in chunks[digest]["observations"]:
            page_counts[obs["offset"] & ~0xFF] += 1

    top_unmatched = []
    for digest in unmatched:
        item = chunks[digest]
        top_unmatched.append(
            {
                "sha256": digest,
                "sample_hex": item["sample_hex"],
                "observations": len(item["observations"]),
                "offsets": sorted({obs["offset"] for obs in item["observations"]}),
            }
        )
    top_unmatched.sort(key=lambda item: (-item["observations"], item["offsets"], item["sha256"]))

    report: dict[str, Any] = {
        "chunk_size": args.chunk_size,
        "unique_chunks": len(chunks),
        "references": reference_reports,
        "matched_any_count": len(matched_any),
        "unmatched_any_count": len(unmatched),
        "unmatched_pages": [
            {"page_start": page, "observations": count}
            for page, count in page_counts.most_common()
        ],
        "top_unmatched_chunks": top_unmatched[:256],
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
