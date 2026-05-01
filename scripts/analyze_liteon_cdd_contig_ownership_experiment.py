#!/usr/bin/env python3
"""Summarize a live CDD contig ownership perturbation experiment.

The normal work-window is a rotating 0x40-byte tile surface.  For ownership
tests we therefore track whether a decoded-runtime contig appears as an
adjacent sequence, and where each component tile appears when the sequence is
broken.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def parse_int(value: str) -> int:
    return int(value, 0)


def find_all(haystack: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        offset = haystack.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def analyze_capture_dir(root: Path, sequence: bytes, chunks: list[bytes]) -> dict:
    files = sorted(root.glob("*.window.bin"))
    result = {
        "capture_dir": str(root),
        "files": len(files),
        "sequence_hits": [],
        "chunk_count_histogram": {},
        "chunk_offsets": {str(i): [] for i in range(len(chunks))},
        "per_file": [],
    }
    histogram: Counter[int] = Counter()
    chunk_offsets: dict[int, Counter[int]] = {i: Counter() for i in range(len(chunks))}

    for path in files:
        data = path.read_bytes()
        sequence_offsets = find_all(data, sequence)
        if sequence_offsets:
            result["sequence_hits"].append(
                {"file": path.name, "offsets": sequence_offsets}
            )

        file_chunks = []
        for index, chunk in enumerate(chunks):
            offsets = find_all(data, chunk)
            if offsets:
                file_chunks.append({"chunk": index, "offsets": offsets})
                for offset in offsets:
                    chunk_offsets[index][offset] += 1

        histogram[len(file_chunks)] += 1
        result["per_file"].append(
            {
                "file": path.name,
                "sequence_offsets": sequence_offsets,
                "chunk_hits": file_chunks,
            }
        )

    result["chunk_count_histogram"] = {
        str(count): histogram[count] for count in sorted(histogram)
    }
    result["chunk_offsets"] = {
        str(index): [
            {"offset": offset, "count": count}
            for offset, count in offsets.most_common()
        ]
        for index, offsets in chunk_offsets.items()
    }
    return result


def write_markdown(path: Path, report: dict) -> None:
    stock_hits = len(report["states"]["stock"]["sequence_hits"])
    mutated_hits = len(report["states"]["mutated"]["sequence_hits"])
    restored_hits = len(report["states"]["restored"]["sequence_hits"])
    stock_files = report["states"]["stock"]["files"]
    mutated_files = report["states"]["mutated"]["files"]
    restored_files = report["states"]["restored"]["files"]
    if stock_hits and not mutated_hits and restored_hits:
        verdict = (
            "The contig sequence disappears under mutation and returns after "
            "restore. This is strong reversible ownership evidence."
        )
    elif stock_hits and not mutated_hits and not restored_hits:
        verdict = (
            "The contig sequence disappears under mutation but did not return "
            "in the supplied restored captures. This is strong ownership "
            "evidence, but restore/state recovery remains unresolved."
        )
    elif stock_hits and mutated_hits == mutated_files:
        verdict = (
            "The contig sequence remains visible under mutation. This is a "
            "negative or insensitive-target result for this contig/source byte."
        )
    else:
        verdict = (
            "The sequence-hit pattern is mixed. Inspect the per-file offsets in "
            "the JSON before using this as ownership evidence."
        )

    lines = [
        "# CDD Contig Ownership Perturbation",
        "",
        "This report distills a reversible live test that links one encoded CDD",
        "source byte to one normal-mode decoded-runtime contig.",
        "",
        "## Target",
        "",
        f"- Contig file: `{report['contig_file']}`",
        f"- Contig bytes: `{report['contig_bytes']}`",
        f"- Target record: `{report['target']['record']}`",
        f"- Patched F0 offset: `{report['target']['offset_hex']}`",
        f"- Mutation: `{report['target']['before_hex']} -> {report['target']['after_hex']}`",
        "",
        "The test is intentionally about the public tile surface, not a flat",
        "decoded CDD address. A positive result means this source byte affects",
        "the appearance/order of the chosen decoded-runtime contig.",
        "",
        "## Results",
        "",
        "| State | Captures | Full contig sequence hits | Chunk-count histogram |",
        "|---|---:|---:|---|",
    ]

    for label, state in report["states"].items():
        lines.append(
            f"| {label} | {state['files']} | {len(state['sequence_hits'])} | "
            f"`{state['chunk_count_histogram']}` |"
        )

    lines.extend(["", "## Verdict", "", verdict, "", "## Tile Offsets", ""])
    for label, state in report["states"].items():
        lines.append(f"### {label}")
        if state["sequence_hits"]:
            offsets = Counter(
                offset
                for hit in state["sequence_hits"]
                for offset in hit["offsets"]
            )
            lines.append(
                "Full-sequence offsets: "
                + ", ".join(
                    f"`{offset:#06x}` x{count}"
                    for offset, count in offsets.most_common()
                )
            )
        else:
            lines.append("Full-sequence offsets: none")
        for index, offsets in state["chunk_offsets"].items():
            top = ", ".join(
                f"`{item['offset']:#06x}` x{item['count']}"
                for item in offsets[:4]
            )
            lines.append(f"- chunk {index}: {top or 'not seen'}")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            f"Stock sequence hits: `{stock_hits}/{stock_files}`.",
            f"Mutated sequence hits: `{mutated_hits}/{mutated_files}`.",
            f"Restored sequence hits: `{restored_hits}/{restored_files}`.",
            "",
            "The component chunk offsets matter because the public work-window is",
            "a rotating tile surface, not a flat decoded CDD dump. A mutation may",
            "remove a tile, rearrange tiles, or leave the sequence unchanged.",
            "",
            "Use this as a better oracle pattern for future CDD work: choose a",
            "short contig with a plausible record owner, patch one low-risk",
            "source bit through the helper bypass, capture the normal work-window",
            "before/mutated/restored, and ask whether sequence/order changes",
            "reversibly.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contig", type=Path, required=True)
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--mutated", type=Path, required=True)
    parser.add_argument("--restored", type=Path, required=True)
    parser.add_argument("--record", type=int, required=True)
    parser.add_argument("--offset", type=parse_int, required=True)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    sequence = args.contig.read_bytes()
    if len(sequence) % 0x40:
        raise ValueError(f"contig length must be a multiple of 0x40: {len(sequence)}")
    chunks = [sequence[offset : offset + 0x40] for offset in range(0, len(sequence), 0x40)]

    states = {
        "stock": analyze_capture_dir(args.stock, sequence, chunks),
        "mutated": analyze_capture_dir(args.mutated, sequence, chunks),
        "restored": analyze_capture_dir(args.restored, sequence, chunks),
    }
    report = {
        "schema": "liteon-cdd-contig-ownership-experiment-v1",
        "contig_file": str(args.contig),
        "contig_bytes": len(sequence),
        "chunk_count": len(chunks),
        "chunk_prefixes": [chunk[:6].hex() for chunk in chunks],
        "target": {
            "record": args.record,
            "offset": args.offset,
            "offset_hex": f"0x{args.offset:05x}",
            "before_hex": args.before.lower(),
            "after_hex": args.after.lower(),
        },
        "states": states,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(args.out_md, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
