#!/usr/bin/env python3
"""Audit CDD known-output exports for repeated public tiles.

The `record-XXX-known-output.bin` files are useful evidence, but they are not
flat decoded CDD records.  They are public-slot consensus artifacts assembled
from 0x40-byte normal work-window tiles.  This script quantifies how much of
each export is repeated tile placement versus unique chunk evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 0x40
DEFAULT_EXPORT_DIR = ROOT / "analysis/8051/cdd-known-output-records-20260501"
DEFAULT_PAIRS = ROOT / "analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.json"


def load_chunk_record_map(pairs_path: Path) -> dict[str, set[int]]:
    data = json.loads(pairs_path.read_text())
    chunk_records: dict[str, set[int]] = defaultdict(set)
    for pair in data["pairs"]:
        chunk_records[pair["chunk_sha256"]].add(int(pair["record"]))
    return dict(chunk_records)


def count_mask_bytes(path: Path) -> int:
    return sum(1 for byte in path.read_bytes() if byte)


def audit_record(slots_path: Path, chunk_records: dict[str, set[int]]) -> dict[str, Any]:
    record = int(slots_path.name.split("-")[1])
    prefix = slots_path.with_name(slots_path.name.removesuffix("-slots.json"))
    mask_path = prefix.with_name(prefix.name + "-known-mask.bin")
    output_path = prefix.with_name(prefix.name + "-known-output.bin")
    source_path = prefix.with_name(prefix.name + "-encoded-source.bin")
    slots = json.loads(slots_path.read_text())

    top_counts = Counter(slot["top_sha256"] for slot in slots)
    repeated = {digest: count for digest, count in top_counts.items() if count > 1}
    singleton = {digest for digest, count in top_counts.items() if count == 1}
    exclusive = {
        digest
        for digest in top_counts
        if chunk_records.get(digest, set()) == {record}
    }
    exclusive_singleton = singleton & exclusive

    variant_slots = [slot for slot in slots if int(slot["variant_count"]) > 1]
    unique_records = sorted({rec for digest in top_counts for rec in chunk_records.get(digest, set())})

    duplicate_positions = []
    by_digest: dict[str, list[int]] = defaultdict(list)
    for slot in slots:
        by_digest[slot["top_sha256"]].append(int(slot["record_relative"]))
    for digest, positions in sorted(by_digest.items(), key=lambda item: (-len(item[1]), item[1])):
        if len(positions) > 1:
            duplicate_positions.append(
                {
                    "chunk": digest[:12],
                    "sha256": digest,
                    "slot_count": len(positions),
                    "record_relatives": positions,
                    "candidate_records": sorted(chunk_records.get(digest, set())),
                }
            )

    known_bytes = count_mask_bytes(mask_path)
    decoded_span = len(output_path.read_bytes())
    return {
        "record": record,
        "source_len": source_path.stat().st_size,
        "decoded_span": decoded_span,
        "known_bytes": known_bytes,
        "slot_count": len(slots),
        "variant_slot_count": len(variant_slots),
        "unique_top_chunks": len(top_counts),
        "duplicate_slots": len(slots) - len(top_counts),
        "repeated_top_chunks": len(repeated),
        "singleton_top_chunks": len(singleton),
        "record_exclusive_top_chunks": len(exclusive),
        "record_exclusive_singleton_chunks": len(exclusive_singleton),
        "unique_chunk_bytes_upper_bound": min(decoded_span, len(top_counts) * CHUNK_SIZE),
        "singleton_chunk_bytes_upper_bound": min(decoded_span, len(singleton) * CHUNK_SIZE),
        "exclusive_singleton_bytes_upper_bound": min(decoded_span, len(exclusive_singleton) * CHUNK_SIZE),
        "top_chunk_repeat_ratio": (len(slots) - len(top_counts)) / len(slots) if slots else 0.0,
        "candidate_records_seen": unique_records,
        "duplicate_positions": duplicate_positions,
        "variant_slots": [
            {
                "record_relative": int(slot["record_relative"]),
                "top_chunk": slot["top_chunk"],
                "variant_count": int(slot["variant_count"]),
                "top_count": int(slot["top_count"]),
            }
            for slot in variant_slots[:16]
        ],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    chunk_records = load_chunk_record_map(args.pairs)
    records = [
        audit_record(path, chunk_records)
        for path in sorted(args.export_dir.glob("record-*-slots.json"))
    ]
    records.sort(
        key=lambda row: (
            -row["known_bytes"],
            -row["top_chunk_repeat_ratio"],
            row["record"],
        )
    )
    return {
        "schema": "liteon-cdd-known-output-export-audit-v1",
        "export_dir": str(args.export_dir),
        "pairs": str(args.pairs),
        "chunk_size": CHUNK_SIZE,
        "records": records,
    }


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def render_md(report: dict[str, Any]) -> str:
    records = report["records"]
    lines = [
        "# CDD Known-Output Export Audit",
        "",
        "Date: 2026-05-01",
        "",
        "Offline only. No drive commands were sent.",
        "",
        "This audits the `record-XXX-known-output.bin` exports. Those files are",
        "public-slot consensus artifacts, not flat decoded CDD records. The key",
        "question is how many exported slots are repeated copies of the same",
        "0x40-byte public tile.",
        "",
        "## Summary",
        "",
        md_table(
            [
                "record",
                "known bytes",
                "slots",
                "unique chunks",
                "duplicate slots",
                "singleton chunks",
                "exclusive singletons",
                "variant slots",
            ],
            [
                [
                    str(row["record"]),
                    f"{row['known_bytes']}/{row['decoded_span']}",
                    str(row["slot_count"]),
                    str(row["unique_top_chunks"]),
                    str(row["duplicate_slots"]),
                    str(row["singleton_top_chunks"]),
                    str(row["record_exclusive_singleton_chunks"]),
                    str(row["variant_slot_count"]),
                ]
                for row in records[:32]
            ],
        ),
        "",
        "The `known bytes` column is slot coverage. `unique chunks` and",
        "`exclusive singletons` are better proxies for independent evidence. A",
        "record with high slot coverage but few unique chunks should not be used",
        "as a flat source-to-output oracle.",
        "",
        "## Highest-Risk Exports",
        "",
        md_table(
            ["record", "duplicate ratio", "repeated chunks", "duplicate chunk placements"],
            [
                [
                    str(row["record"]),
                    f"{row['top_chunk_repeat_ratio']:.0%}",
                    str(row["repeated_top_chunks"]),
                    "; ".join(
                        "`"
                        + dup["chunk"]
                        + "` @ "
                        + ",".join(f"0x{rel:x}" for rel in dup["record_relatives"][:8])
                        for dup in row["duplicate_positions"][:4]
                    ),
                ]
                for row in sorted(records, key=lambda item: (-item["top_chunk_repeat_ratio"], item["record"]))[:16]
            ],
        ),
        "",
        "## Practical Read",
        "",
        "- Treat the exported `known-output.bin` files as placement evidence.",
        "- Use chunk identity, duplicate counts, adjacency, and live perturbation",
        "  before claiming a flat decoded record.",
        "- Strong static transform targets should have many unique chunks, few",
        "  duplicates, and preferably record-exclusive singleton chunks.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report) + "\n")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
