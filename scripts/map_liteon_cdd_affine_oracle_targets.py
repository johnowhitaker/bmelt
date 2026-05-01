#!/usr/bin/env python3
"""Map CDD affine group evidence onto candidate decoded-address intervals.

This is an offline bridge between the static CDD affine-unit analysis and live
controller-memory oracle reads. It does not decode the CDD body. It lists the
candidate decoded ranges that correspond to records with affine group evidence,
so runtime reads can be aimed at structurally meaningful addresses.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import analyze_liteon_cdd_affine_units as affine
import analyze_liteon_cdd_streams as cdd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-cdd-affine-oracle-targets.md"
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-cdd-affine-oracle-targets.json"
DEFAULT_DECODED_BASE = 0x184000


def record_layout(image: cdd.CddImage, decoded_base: int) -> dict[int, dict[str, Any]]:
    decoded_offset = 0
    records: dict[int, dict[str, Any]] = {}
    for index, source_start, source_end, entry in cdd.source_segments(image):
        span = cdd.decoded_span_candidate(entry)
        records[index] = {
            "index": index,
            "operation_key": cdd.operation_key(entry).hex(),
            "source_start": source_start,
            "source_end": source_end,
            "source_len": source_end - source_start,
            "decoded_start": decoded_base + decoded_offset,
            "decoded_span": span,
            "decoded_end_exclusive": decoded_base + decoded_offset + span,
        }
        decoded_offset += span
    return records


def target_rows(image: cdd.CddImage, decoded_base: int) -> list[dict[str, Any]]:
    _canonical, evidence = affine.decode_image(image)
    grouped: dict[int, list[affine.AffineEvidence]] = defaultdict(list)
    for item in evidence:
        grouped[item.group].append(item)
    layout = record_layout(image, decoded_base)

    rows: list[dict[str, Any]] = []
    for group, items in sorted(grouped.items()):
        plains = sorted({item.plain for item in items})
        if len(plains) != 1:
            continue
        record_indices = list(range(group * 4, min(group * 4 + 4, max(layout) + 1)))
        records = [layout[index] for index in record_indices if index in layout]
        rows.append(
            {
                "group": group,
                "plain": plains[0],
                "evidence_records": sorted({item.record for item in items}),
                "evidence_cells": [item.cell for item in sorted(items, key=lambda item: (item.record, item.source_offset_in_record))],
                "decoded_start": records[0]["decoded_start"] if records else None,
                "decoded_end_exclusive": records[-1]["decoded_end_exclusive"] if records else None,
                "decoded_span_total": sum(int(record["decoded_span"]) for record in records),
                "records": records,
            }
        )
    return rows


def serializable(images: list[cdd.CddImage], decoded_base: int) -> dict[str, Any]:
    return {
        "schema": "liteon-cdd-affine-oracle-targets-v1",
        "note": "Candidate decoded-address targets for runtime oracle reads. These are inferred intervals, not confirmed decoded bytes.",
        "decoded_base": decoded_base,
        "images": [
            {
                "image": image.name,
                "path": str(image.path),
                "targets": target_rows(image, decoded_base),
            }
            for image in images
            if image.name != "XD13" and len(image.streams) >= 2
        ],
    }


def write_report(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# LiteOn CDD Affine Oracle Targets")
    lines.append("")
    lines.append("Offline only. No drive commands were sent.")
    lines.append("")
    lines.append("These are candidate runtime/controller addresses for live oracle reads. They combine the inferred decoded-span layout with the affine unit evidence. A hit or miss here tests what the affine byte means at runtime; it is not a completed CDD decode.")
    lines.append("")
    lines.append(f"Decoded base: `0x{data['decoded_base']:06x}`")
    lines.append("")
    for image in data["images"]:
        lines.append(f"## {image['image']}")
        lines.append("")
        lines.append("| group | plain | evidence records | cells | candidate decoded interval | span | source/opkey summary |")
        lines.append("|---:|---:|---|---|---|---:|---|")
        for row in image["targets"]:
            if row["decoded_start"] is None:
                continue
            evidence_records = ",".join(str(record) for record in row["evidence_records"])
            cells = ",".join(str(cell) for cell in row["evidence_cells"])
            interval = f"`0x{row['decoded_start']:06x}..0x{row['decoded_end_exclusive'] - 1:06x}`"
            summaries = []
            for record in row["records"]:
                summaries.append(
                    f"{record['index']}:src `0x{record['source_start']:05x}..0x{record['source_end'] - 1:05x}` op `{record['operation_key']}`"
                )
            lines.append(
                f"| {row['group']} | `0x{row['plain']:02x}` | `{evidence_records}` | `{cells}` | "
                f"{interval} | `0x{row['decoded_span_total']:x}` | " + "<br>".join(summaries) + " |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", action="append", type=Path, help="F0 image path; may be repeated")
    parser.add_argument("--decoded-base", type=lambda value: int(value, 0), default=DEFAULT_DECODED_BASE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_JSON)
    args = parser.parse_args()

    paths = args.image if args.image else cdd.DEFAULT_IMAGES
    images = [image for path in paths if (image := cdd.load_image(path))]
    if not images:
        raise SystemExit("no CDD-bearing 1 MiB images found")

    data = serializable(images, args.decoded_base)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(write_report(data) + "\n")
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
