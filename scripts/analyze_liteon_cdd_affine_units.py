#!/usr/bin/env python3
"""Analyze the affine unit-code cells inside LiteOn/PLDS CDD streams.

This is a partial static decoder. It does not decode the full CDD payload.
It extracts the 16-cell affine byte code visible in the short records and in
canonical-tail suffixes of longer records.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import analyze_liteon_cdd_streams as cdd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-cdd-affine-unit-analysis.md"
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-cdd-affine-unit-analysis.json"


def clmul8(a: int, n: int) -> int:
    """Carry-less multiply a byte by a small integer, truncated to 8 bits."""
    out = 0
    shift = 0
    while n:
        if n & 1:
            out ^= a << shift
        n >>= 1
        shift += 1
    return out & 0xFF


AFFINE_MASKS = tuple(clmul8(0x19, cell) for cell in range(16))


@dataclass(frozen=True)
class CanonicalUnit:
    op_key: bytes
    unit_size: int
    tail: bytes
    record_count: int


@dataclass(frozen=True)
class AffineEvidence:
    image: str
    group: int
    record: int
    record_mod4: int
    source_offset_in_record: int
    raw: int
    cell: int
    mask: int
    plain: int
    kind: str
    op_key: str


def affine_plain_for_units(record_index: int, first_bytes: list[int]) -> tuple[int | None, list[int], list[int]]:
    row = record_index & 3
    cells = [4 * row + unit for unit in range(len(first_bytes))]
    plains = [byte ^ AFFINE_MASKS[cell] for byte, cell in zip(first_bytes, cells)]
    return (plains[0] if plains and len(set(plains)) == 1 else None, cells, plains)


def discover_canonical_unit(image: cdd.CddImage) -> CanonicalUnit | None:
    candidates: Counter[tuple[bytes, int, bytes]] = Counter()
    for index, start, end, entry in cdd.source_segments(image):
        key = cdd.operation_key(entry)
        unit_size = key[0]
        source_len = end - start
        if key[-1] != 0 or unit_size not in (12, 13) or source_len != 4 * unit_size:
            continue
        if key[4] != 2 * unit_size:
            continue
        source = image.data[start:end]
        units = [source[offset : offset + unit_size] for offset in range(0, source_len, unit_size)]
        tails = {unit[1:] for unit in units}
        if len(tails) != 1:
            continue
        first_bytes = [unit[0] for unit in units]
        plain, _, _ = affine_plain_for_units(index, first_bytes)
        if plain is None:
            continue
        candidates[(key, unit_size, units[0][1:])] += 1

    if not candidates:
        return None
    (op_key, unit_size, tail), count = candidates.most_common(1)[0]
    return CanonicalUnit(op_key=op_key, unit_size=unit_size, tail=tail, record_count=count)


def find_unit_runs(source: bytes, tail: bytes, unit_size: int) -> list[list[int]]:
    starts: list[int] = []
    position = source.find(tail)
    while position >= 0:
        if position > 0:
            starts.append(position - 1)
        position = source.find(tail, position + 1)

    if not starts:
        return []
    starts.sort()
    runs: list[list[int]] = []
    current = [starts[0]]
    for start in starts[1:]:
        if start == current[-1] + unit_size:
            current.append(start)
        else:
            runs.append(current)
            current = [start]
    runs.append(current)
    return runs


def decode_image(image: cdd.CddImage) -> tuple[CanonicalUnit | None, list[AffineEvidence]]:
    canonical = discover_canonical_unit(image)
    if canonical is None:
        return None, []

    evidence: list[AffineEvidence] = []
    op_suffix = bytes([2 * canonical.unit_size, 0])
    for index, start, end, entry in cdd.source_segments(image):
        key = cdd.operation_key(entry)
        source = image.data[start:end]
        for run in find_unit_runs(source, canonical.tail, canonical.unit_size):
            if len(run) > 4:
                continue
            full_short = (
                end - start == 4 * canonical.unit_size
                and run == [0, canonical.unit_size, 2 * canonical.unit_size, 3 * canonical.unit_size]
                and key[-2:] == op_suffix
            )
            row = index & 3
            if full_short:
                cells = [4 * row + unit for unit in range(4)]
                kind = "full-row"
            else:
                cells = [4 * row + (4 - len(run) + unit) for unit in range(len(run))]
                kind = "suffix"

            for offset, cell in zip(run, cells):
                raw = source[offset]
                mask = AFFINE_MASKS[cell]
                evidence.append(
                    AffineEvidence(
                        image=image.name,
                        group=index // 4,
                        record=index,
                        record_mod4=row,
                        source_offset_in_record=offset,
                        raw=raw,
                        cell=cell,
                        mask=mask,
                        plain=raw ^ mask,
                        kind=kind,
                        op_key=key.hex(),
                    )
                )

    return canonical, evidence


def grouped_evidence(evidence: list[AffineEvidence]) -> dict[int, list[AffineEvidence]]:
    groups: dict[int, list[AffineEvidence]] = defaultdict(list)
    for item in evidence:
        groups[item.group].append(item)
    return dict(sorted(groups.items()))


def group_status(items: list[AffineEvidence]) -> tuple[str, int | None, list[int]]:
    plains = sorted({item.plain for item in items})
    if len(plains) == 1:
        return "ok", plains[0], plains
    return "CONFLICT", None, plains


def suffix_key_summary(image_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize what the operation key does and does not explain yet.

    The suffix decoder is intentionally evidence-driven: it finds literal
    canonical unit tails. This summary records the visible key correlations so
    we do not overstate that the operation key alone predicts suffix length.
    """
    by_record: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for image in image_results:
        for item in image["evidence"]:
            if item["kind"] == "suffix":
                by_record[(image["image"], item["record"])].append(item)

    rows = []
    for (image_name, record), items in sorted(by_record.items()):
        items = sorted(items, key=lambda item: item["cell"])
        op_key = bytes.fromhex(items[0]["op_key"])
        rows.append(
            {
                "image": image_name,
                "record": record,
                "group": record // 4,
                "row": record & 3,
                "k": len(items),
                "cells": [item["cell"] for item in items],
                "op_key": op_key.hex(),
                "op_byte3": op_key[3],
                "op_byte4": op_key[4],
                "op_byte5": op_key[5],
                "decoded_span_field": (op_key[3] & 0x3F) << 4,
            }
        )

    def counter(field: str, items: list[dict[str, Any]]) -> dict[str, int]:
        counts = Counter(item[field] for item in items)
        return {str(key): counts[key] for key in sorted(counts)}

    by_k = {}
    for k in sorted({row["k"] for row in rows}):
        items = [row for row in rows if row["k"] == k]
        by_k[str(k)] = {
            "count": len(items),
            "rows": counter("row", items),
            "op_byte3": {f"0x{int(key):02x}": value for key, value in Counter(row["op_byte3"] for row in items).items()},
            "op_byte4": {f"0x{int(key):02x}": value for key, value in Counter(row["op_byte4"] for row in items).items()},
            "decoded_span_field": {f"0x{int(key):03x}": value for key, value in Counter(row["decoded_span_field"] for row in items).items()},
        }

    non_boundary = [row for row in rows if row["group"] != 96]
    return {
        "total_suffix_records": len(rows),
        "count_by_k": {str(key): value for key, value in sorted(Counter(row["k"] for row in rows).items())},
        "all_op_byte5_zero": all(row["op_byte5"] == 0 for row in rows),
        "non_boundary_op_byte4_values": sorted({row["op_byte4"] for row in non_boundary}),
        "non_boundary_k2_k3_all_decoded_span_0x30": all(
            row["decoded_span_field"] == 0x30 for row in non_boundary if row["k"] in (2, 3)
        ),
        "by_k": by_k,
    }


def serializable_results(images: list[cdd.CddImage]) -> dict[str, Any]:
    image_results = []
    for image in images:
        if image.name == "XD13" or len(image.streams) < 2:
            continue
        canonical, evidence = decode_image(image)
        groups = grouped_evidence(evidence)
        image_results.append(
            {
                "image": image.name,
                "canonical": None
                if canonical is None
                else {
                    "op_key": canonical.op_key.hex(),
                    "unit_size": canonical.unit_size,
                    "tail": canonical.tail.hex(),
                    "record_count": canonical.record_count,
                },
                "groups": [
                    {
                        "group": group,
                        "status": group_status(items)[0],
                        "plain": group_status(items)[1],
                        "plains": group_status(items)[2],
                        "cells": [item.cell for item in sorted(items, key=lambda item: (item.record, item.source_offset_in_record))],
                        "records": sorted({item.record for item in items}),
                        "evidence_count": len(items),
                    }
                    for group, items in groups.items()
                ],
                "evidence": [
                    {
                        "group": item.group,
                        "record": item.record,
                        "record_mod4": item.record_mod4,
                        "source_offset_in_record": item.source_offset_in_record,
                        "raw": item.raw,
                        "cell": item.cell,
                        "mask": item.mask,
                        "plain": item.plain,
                        "kind": item.kind,
                        "op_key": item.op_key,
                    }
                    for item in evidence
                ],
            }
        )

    return {
        "schema": "liteon-cdd-affine-unit-analysis-v1",
        "note": "Partial static decoder for canonical CDD affine unit cells. This is not a full CDD decompressor.",
        "mask_generator": "mask[cell] = carryless_mul8(0x19, cell)",
        "masks": list(AFFINE_MASKS),
        "suffix_key_summary": suffix_key_summary(image_results),
        "images": image_results,
    }


def write_report(results: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# LiteOn CDD Affine Unit Analysis")
    lines.append("")
    lines.append("Offline only. No drive commands were sent.")
    lines.append("")
    lines.append("This is a partial decoder for the affine byte cells visible in DS-8ABSH CDD short records and in matching suffix units inside longer records. It is not a full CDD decompressor.")
    lines.append("")
    lines.append("## Mask Table")
    lines.append("")
    lines.append("The masks are carry-less multiplication by `0x19` over the low 4-bit cell index:")
    lines.append("")
    lines.append("```text")
    lines.append("cell: " + " ".join(f"{cell:02x}" for cell in range(16)))
    lines.append("mask: " + " ".join(f"{mask:02x}" for mask in AFFINE_MASKS))
    lines.append("```")
    lines.append("")
    lines.append("A canonical cell decodes as:")
    lines.append("")
    lines.append("```text")
    lines.append("plain_group_byte = raw_cell_byte ^ mask[cell]")
    lines.append("cell = 4 * (record_index & 3) + unit_index")
    lines.append("```")
    lines.append("")

    lines.append("## Canonical Unit Tails")
    lines.append("")
    lines.append("| image | canonical op key | unit size | matching short records | unit tail |")
    lines.append("|---|---|---:|---:|---|")
    for image in results["images"]:
        canonical = image["canonical"]
        if canonical is None:
            lines.append(f"| {image['image']} | | | | |")
            continue
        lines.append(
            f"| {image['image']} | `{canonical['op_key']}` | {canonical['unit_size']} | "
            f"{canonical['record_count']} | `{canonical['tail']}` |"
        )
    lines.append("")

    by_group: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    for image in results["images"]:
        for group in image["groups"]:
            if group["status"] == "ok":
                by_group[int(group["group"])][str(image["image"])] = group

    image_names = [str(image["image"]) for image in results["images"]]
    stable_rows = []
    partial_rows = []
    for group, image_groups in sorted(by_group.items()):
        plains = {int(item["plain"]) for item in image_groups.values() if item["plain"] is not None}
        if len(plains) != 1:
            continue
        row = (len(image_groups), group, next(iter(plains)), image_groups)
        if len(image_groups) == len(image_names):
            stable_rows.append(row)
        else:
            partial_rows.append(row)

    lines.append("## Cross-Image Stable Group Bytes")
    lines.append("")
    lines.append("These groups decode to the same byte wherever evidence exists. Full-row short records and long-record suffix units are both included.")
    lines.append("")
    header = "| group | plain | " + " | ".join(image_names) + " |"
    lines.append(header)
    lines.append("|---:|---:|" + "|".join("---:" for _ in image_names) + "|")
    for _, group, plain, image_groups in sorted(stable_rows + partial_rows, key=lambda row: (row[1], -row[0])):
        cells = []
        for image_name in image_names:
            item = image_groups.get(image_name)
            if item is None:
                cells.append("")
            else:
                cells.append("`" + ",".join(str(cell) for cell in item["cells"]) + "`")
        lines.append(f"| {group} | `0x{plain:02x}` | " + " | ".join(cells) + " |")
    lines.append("")

    summary = results["suffix_key_summary"]
    lines.append("## Suffix-Key Clues")
    lines.append("")
    lines.append("The current suffix decoder is still evidence-driven: it finds literal canonical unit tails at the ends of source records. The operation key has strong correlations, but it does not yet predict every suffix count by itself.")
    lines.append("")
    lines.append(f"- Suffix records found: {summary['total_suffix_records']}.")
    lines.append("- Suffix unit counts: " + ", ".join(f"`k={key}`: {value}" for key, value in summary["count_by_k"].items()) + ".")
    lines.append(f"- `op_key[5] == 0` for every suffix record: `{summary['all_op_byte5_zero']}`.")
    lines.append("- Excluding boundary group 96, `op_key[4]` is always the canonical doubled unit size: " + ", ".join(f"`0x{value:02x}`" for value in summary["non_boundary_op_byte4_values"]) + ".")
    lines.append(f"- Excluding boundary group 96, every `k=2`/`k=3` suffix record has decoded-span field `0x30`: `{summary['non_boundary_k2_k3_all_decoded_span_0x30']}`.")
    lines.append("")
    lines.append("| k | records | rows | op_key[3] values | op_key[4] values | decoded-span fields |")
    lines.append("|---:|---:|---|---|---|---|")
    for k, item in summary["by_k"].items():
        rows = ", ".join(f"`{row}`:{count}" for row, count in item["rows"].items())
        byte3 = ", ".join(f"`{key}`:{count}" for key, count in sorted(item["op_byte3"].items()))
        byte4 = ", ".join(f"`{key}`:{count}" for key, count in sorted(item["op_byte4"].items()))
        spans = ", ".join(f"`{key}`:{count}" for key, count in sorted(item["decoded_span_field"].items()))
        lines.append(f"| {k} | {item['count']} | {rows} | {byte3} | {byte4} | {spans} |")
    lines.append("")

    lines.append("## Conflicts")
    lines.append("")
    lines.append("Group `96` is expected to be noisy because it crosses the CDD1/CDD2 boundary area around record 387; exclude it from grammar inference for now.")
    lines.append("")
    lines.append("| image | group | plains | records |")
    lines.append("|---|---:|---|---|")
    for image in results["images"]:
        for group in image["groups"]:
            if group["status"] != "CONFLICT":
                continue
            plains = ", ".join(f"`0x{plain:02x}`" for plain in group["plains"])
            records = ", ".join(str(record) for record in group["records"])
            lines.append(f"| {image['image']} | {group['group']} | {plains} | {records} |")
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append("- The previous `m` byte is better described as a raw coded byte for one row of a 16-cell group.")
    lines.append("- Long records often end with the same canonical unit tail and recover the rightmost missing cells for that record row.")
    lines.append("- `op_key[4] == 2 * unit_size` holds for the known canonical unit class, which makes byte 4 look like a doubled unit width or stride.")
    lines.append("- This strengthens the model of CDD as a proprietary controller codeword format, not a standard compressor or encrypted blob.")
    lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", action="append", type=Path, help="F0 image path. May be supplied more than once.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_JSON)
    args = parser.parse_args()

    paths = args.image if args.image else cdd.DEFAULT_IMAGES
    images = [image for path in paths if (image := cdd.load_image(path))]
    if not images:
        raise SystemExit("no CDD-bearing 1 MiB images found")

    results = serializable_results(images)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(write_report(results))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
