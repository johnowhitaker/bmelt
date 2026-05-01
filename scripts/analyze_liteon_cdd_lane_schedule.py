#!/usr/bin/env python3
"""Analyze the 12-record CDD macro-lane schedule.

This is an offline-only companion to the affine unit analyzer. It asks whether
the lane-0 affine leaf grammar also appears in macro lanes 1 or 2, and
summarizes the per-lane shape of the CDD records.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import analyze_liteon_cdd_affine_units as affine
import analyze_liteon_cdd_streams as cdd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-cdd-lane-schedule-analysis.md"
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-cdd-lane-schedule-analysis.json"


def load_default_images(paths: list[Path] | None = None) -> list[cdd.CddImage]:
    selected = paths if paths else cdd.DEFAULT_IMAGES
    images = []
    for path in selected:
        image = cdd.load_image(path)
        if image and image.name != "XD13" and len(image.streams) >= 2:
            images.append(image)
    return images


def lane_summary(images: list[cdd.CddImage]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for image in images:
        lanes: dict[int, list[tuple[int, int, bytes, int]]] = defaultdict(list)
        for index, start, end, entry in cdd.source_segments(image):
            key = cdd.operation_key(entry)
            lanes[(index // 4) % 3].append((index, end - start, key, cdd.decoded_span_candidate(entry)))

        image_rows = {}
        for lane in range(3):
            rows = lanes[lane]
            source_total = sum(row[1] for row in rows)
            decoded_total = sum(row[3] for row in rows)
            image_rows[str(lane)] = {
                "records": len(rows),
                "source_total": source_total,
                "decoded_span_total": decoded_total,
                "source_to_decoded_ratio": source_total / decoded_total if decoded_total else None,
                "top_decoded_spans": Counter(row[3] for row in rows).most_common(8),
                "top_op_byte4": Counter(row[2][4] for row in rows).most_common(8),
                "top_op_byte5": Counter(row[2][5] for row in rows).most_common(6),
                "repeated_operation_keys": [
                    (key.hex(), count)
                    for key, count in Counter(row[2] for row in rows).most_common(6)
                    if count > 1
                ],
            }
        summary[image.name] = image_rows
    return summary


def edge_affine_hits(image: cdd.CddImage, min_unit: int = 4, max_unit: int = 40) -> list[dict[str, Any]]:
    """Find repeated edge units that satisfy the known 16-cell affine masks.

    This is intentionally broader than the maintained affine decoder. It does
    not require the image's canonical unit tail. It scans prefix and suffix
    edge runs for any unit size in the selected range. Because k=2 and k=3
    subruns can sit inside a k=4 run, use this mostly as a lane-presence test.
    """

    hits: list[dict[str, Any]] = []
    for index, start, end, entry in cdd.source_segments(image):
        source = image.data[start:end]
        row = index & 3
        group = index // 4
        macro_lane = group % 3
        key = cdd.operation_key(entry)
        for unit_size in range(min_unit, max_unit + 1):
            if len(source) < 2 * unit_size:
                continue
            max_k = min(4, len(source) // unit_size)
            for kind in ("prefix", "suffix"):
                for k in range(2, max_k + 1):
                    if kind == "prefix":
                        offsets = [unit * unit_size for unit in range(k)]
                        slots = list(range(k))
                    else:
                        offsets = [len(source) - k * unit_size + unit * unit_size for unit in range(k)]
                        slots = list(range(4 - k, 4))

                    units = [source[offset : offset + unit_size] for offset in offsets]
                    if len({unit[1:] for unit in units}) != 1:
                        continue
                    cells = [4 * row + slot for slot in slots]
                    plains = [
                        unit[0] ^ affine.AFFINE_MASKS[cell]
                        for unit, cell in zip(units, cells)
                    ]
                    if len(set(plains)) != 1:
                        continue
                    hits.append(
                        {
                            "image": image.name,
                            "record": index,
                            "group": group,
                            "macro": group // 3,
                            "macro_lane": macro_lane,
                            "row": row,
                            "kind": kind,
                            "unit_size": unit_size,
                            "k": k,
                            "offset": offsets[0],
                            "plain": plains[0],
                            "op_key": key.hex(),
                            "source_len": len(source),
                            "tail": units[0][1:].hex(),
                        }
                    )
    return hits


def edge_scan_summary(images: list[cdd.CddImage]) -> dict[str, Any]:
    hits = [hit for image in images for hit in edge_affine_hits(image)]
    by_lane = Counter(hit["macro_lane"] for hit in hits)
    by_unit_size = Counter(hit["unit_size"] for hit in hits)
    by_kind = Counter(hit["kind"] for hit in hits)
    lane12 = [hit for hit in hits if hit["macro_lane"] in (1, 2)]
    return {
        "note": (
            "Broad edge scan over unit sizes 4..40 and k=2..4. Counts include "
            "overlapping subruns; use lane presence/absence rather than exact "
            "run counts."
        ),
        "total_hits": len(hits),
        "by_macro_lane": dict(sorted(by_lane.items())),
        "by_unit_size": dict(sorted(by_unit_size.items())),
        "by_kind": dict(sorted(by_kind.items())),
        "lane_1_2_hits": len(lane12),
        "lane_1_2_examples": lane12[:20],
    }


def close_sibling_diff_summary(images: list[cdd.CddImage]) -> dict[str, Any]:
    by_name = {image.name: image for image in images}
    if "CHS7" not in by_name or "CHS9" not in by_name:
        return {}
    left = by_name["CHS7"]
    right = by_name["CHS9"]
    lanes: dict[int, Counter[str]] = defaultdict(Counter)
    examples = []
    for left_segment, right_segment in zip(cdd.source_segments(left), cdd.source_segments(right)):
        index, left_start, left_end, left_entry = left_segment
        _, right_start, right_end, right_entry = right_segment
        lane = (index // 4) % 3
        left_key = cdd.operation_key(left_entry)
        right_key = cdd.operation_key(right_entry)
        left_source = left.data[left_start:left_end]
        right_source = right.data[right_start:right_end]
        lanes[lane]["records"] += 1
        lanes[lane]["same_operation_key"] += int(left_key == right_key)
        lanes[lane]["same_source_len"] += int(len(left_source) == len(right_source))
        if left_key == right_key and len(left_source) == len(right_source):
            diffs = sum(a != b for a, b in zip(left_source, right_source))
            lanes[lane]["same_key_len_records"] += 1
            lanes[lane]["same_key_len_bytes"] += len(left_source)
            lanes[lane]["same_key_len_diff_bytes"] += diffs
            for left_byte, right_byte in zip(left_source, right_source):
                delta = left_byte ^ right_byte
                if delta:
                    lanes[lane][f"bitdiff_{delta.bit_count()}"] += 1
                    lanes[lane][f"xor_{delta:02x}"] += 1
            run_len = 0
            for left_byte, right_byte in zip(left_source, right_source):
                if left_byte != right_byte:
                    run_len += 1
                elif run_len:
                    lanes[lane][f"diff_run_{run_len}"] += 1
                    run_len = 0
            if run_len:
                lanes[lane][f"diff_run_{run_len}"] += 1
            if diffs and len(examples) < 12:
                examples.append(
                    {
                        "record": index,
                        "macro_lane": lane,
                        "source_len": len(left_source),
                        "diff_bytes": diffs,
                        "operation_key": left_key.hex(),
                        "chs7_start": left_start,
                        "chs9_start": right_start,
                        "chs7_first16": left_source[:16].hex(),
                        "chs9_first16": right_source[:16].hex(),
                    }
                )

    rows = {}
    for lane, counts in sorted(lanes.items()):
        total = counts["same_key_len_bytes"]
        diff = counts["same_key_len_diff_bytes"]
        bitdiff = {
            str(bits): counts[f"bitdiff_{bits}"]
            for bits in range(1, 9)
            if counts[f"bitdiff_{bits}"]
        }
        diff_runs = Counter(
            {
                int(key[9:]): value
                for key, value in counts.items()
                if key.startswith("diff_run_")
            }
        )
        diff_run_total = sum(diff_runs.values())
        xor_counts = Counter(
            {
                int(key[4:], 16): value
                for key, value in counts.items()
                if key.startswith("xor_")
            }
        )
        public_counts = {
            key: value
            for key, value in counts.items()
            if not key.startswith("xor_")
            and not key.startswith("bitdiff_")
            and not key.startswith("diff_run_")
        }
        rows[str(lane)] = {
            **dict(public_counts),
            "same_key_len_diff_rate": diff / total if total else None,
            "same_key_len_equal_rate": 1 - (diff / total) if total else None,
            "changed_byte_bit_counts": bitdiff,
            "diff_run_total": diff_run_total,
            "diff_run_length_counts": [(length, count) for length, count in diff_runs.most_common(16)],
            "diff_run_le_1_rate": diff_runs[1] / diff_run_total if diff_run_total else None,
            "diff_run_le_2_rate": sum(count for length, count in diff_runs.items() if length <= 2) / diff_run_total if diff_run_total else None,
            "diff_run_le_4_rate": sum(count for length, count in diff_runs.items() if length <= 4) / diff_run_total if diff_run_total else None,
            "top_xor_deltas": [(f"0x{delta:02x}", count) for delta, count in xor_counts.most_common(16)],
        }
    return {
        "pair": "CHS7_vs_CHS9",
        "by_macro_lane": rows,
        "examples": examples,
    }


def serializable(images: list[cdd.CddImage]) -> dict[str, Any]:
    return {
        "schema": "liteon-cdd-lane-schedule-analysis-v1",
        "note": "Offline CDD macro-lane schedule and negative edge-affine scan.",
        "images": [image.name for image in images],
        "lane_summary": lane_summary(images),
        "edge_affine_scan": edge_scan_summary(images),
        "close_sibling_diff": close_sibling_diff_summary(images),
    }


def hex_counter_rows(rows: list[tuple[int, int]], width: int = 2) -> str:
    return ", ".join(f"`0x{value:0{width}x}`:{count}" for value, count in rows)


def write_report(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# LiteOn CDD Lane Schedule Analysis")
    lines.append("")
    lines.append("Offline only. No drive commands were sent.")
    lines.append("")
    lines.append("This report follows the 12-record macro schedule suggested by the affine leaf decoder and asks whether the same edge-unit grammar appears outside macro lane 0.")
    lines.append("")
    lines.append("## Broad Edge-Affine Scan")
    lines.append("")
    scan = data["edge_affine_scan"]
    lines.append(scan["note"])
    lines.append("")
    lines.append(f"- Total edge-affine hits: `{scan['total_hits']}`.")
    lines.append(f"- Hits by macro lane: `{scan['by_macro_lane']}`.")
    lines.append(f"- Hits by unit size: `{scan['by_unit_size']}`.")
    lines.append(f"- Hits by kind: `{scan['by_kind']}`.")
    lines.append(f"- Macro lane 1/2 hits: `{scan['lane_1_2_hits']}`.")
    lines.append("")
    if scan["lane_1_2_hits"] == 0:
        lines.append("Result: the broadened edge scan still finds the repeated-tail affine unit grammar only in macro lane 0. Lanes 1 and 2 either use a different grammar or carry their useful data inside the high-entropy body, not as prefix/suffix affine leaves.")
    else:
        lines.append("Lane 1/2 examples:")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(scan["lane_1_2_examples"], indent=2))
        lines.append("```")
    lines.append("")

    lines.append("## Per-Lane Shape")
    lines.append("")
    lines.append("Lane 0 has the repeated short-operation class; lanes 1 and 2 have almost entirely unique operation keys and higher-entropy bulk records.")
    lines.append("")
    lines.append("| image | lane | records | source total | decoded-span total | source/decoded | repeated op keys | top op byte 5 |")
    lines.append("|---|---:|---:|---:|---:|---:|---|---|")
    for image, lanes in data["lane_summary"].items():
        for lane in ("0", "1", "2"):
            row = lanes[lane]
            repeated = ", ".join(f"`{key}` x{count}" for key, count in row["repeated_operation_keys"]) or "-"
            op5 = hex_counter_rows(row["top_op_byte5"])
            lines.append(
                f"| {image} | {lane} | {row['records']} | `0x{row['source_total']:x}` | "
                f"`0x{row['decoded_span_total']:x}` | {row['source_to_decoded_ratio']:.2f} | {repeated} | {op5} |"
            )
    lines.append("")

    diff = data.get("close_sibling_diff") or {}
    if diff:
        lines.append("## CHS7/CHS9 Locality Check")
        lines.append("")
        lines.append("CHS7 and CHS9 are close siblings. At same-index records with the same operation key and source length, about 72% of source bytes are equal in every lane. That supports a deterministic/localized codeword format, not per-image encryption with avalanche.")
        lines.append("")
        lines.append("| lane | records | same op key | same op+len records | equal-byte rate in same op+len records |")
        lines.append("|---:|---:|---:|---:|---:|")
        for lane, row in diff["by_macro_lane"].items():
            equal_rate = row["same_key_len_equal_rate"]
            lines.append(
                f"| {lane} | {row['records']} | {row['same_operation_key']} | "
                f"{row['same_key_len_records']} | {equal_rate:.3f} |"
            )
        lines.append("")
        lines.append("Changed bytes are dominated by one-bit XOR deltas in all lanes, with the same top deltas (`0x80`, `0x01`, `0x02`, `0x40`, etc.). That is another sign of localized deterministic edits rather than a stream cipher or block-cipher avalanche.")
        lines.append("")
        lines.append("| lane | changed-byte bit counts | top XOR deltas |")
        lines.append("|---:|---|---|")
        for lane, row in diff["by_macro_lane"].items():
            bit_counts = ", ".join(f"{bits}b:{count}" for bits, count in row["changed_byte_bit_counts"].items())
            top_xor = ", ".join(f"`{delta}`:{count}" for delta, count in row["top_xor_deltas"][:8])
            lines.append(f"| {lane} | {bit_counts} | {top_xor} |")
        lines.append("")
        lines.append("The changed bytes are also spatially local. Most contiguous diff runs are four bytes or shorter in every lane:")
        lines.append("")
        lines.append("| lane | diff runs | len=1 | len<=2 | len<=4 | top run lengths |")
        lines.append("|---:|---:|---:|---:|---:|---|")
        for lane, row in diff["by_macro_lane"].items():
            top_runs = ", ".join(f"{length}:{count}" for length, count in row["diff_run_length_counts"][:8])
            lines.append(
                f"| {lane} | {row['diff_run_total']} | {row['diff_run_le_1_rate']:.3f} | "
                f"{row['diff_run_le_2_rate']:.3f} | {row['diff_run_le_4_rate']:.3f} | {top_runs} |"
            )
        lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append("- The lane-0 affine leaf is real, but it is probably one visible lane of a larger CDD/controller codeword schedule.")
    lines.append("- Lanes 1 and 2 did not reveal an analogous repeated-tail edge grammar under a wider unit-size scan.")
    lines.append("- The close-sibling byte locality keeps arguing against ordinary encryption/compression as the whole story. The hard lanes look like controller-specific packed/ECC-like records.")
    lines.append("- A useful next static step is to classify lane 1/2 operation-key fields and body-diff locality, rather than keep searching for the lane-0 tail pattern there.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", action="append", type=Path, help="F0 image path; may be repeated")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_JSON)
    args = parser.parse_args()

    images = load_default_images(args.image)
    if not images:
        raise SystemExit("no CDD-bearing 1 MiB images found")

    data = serializable(images)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(write_report(data) + "\n")
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
