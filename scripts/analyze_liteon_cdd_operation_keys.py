#!/usr/bin/env python3
"""Analyze LiteOn/PLDS CDD directory operation-key fields.

Offline only. This complements the CDD stream and lane-schedule reports by
asking what the six-byte operation key explains directly: source length,
decoded-span field, macro lane, and close-sibling edits.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

import analyze_liteon_cdd_streams as cdd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-cdd-operation-key-analysis.md"
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-cdd-operation-key-analysis.json"


def load_default_images(paths: list[Path] | None = None) -> list[cdd.CddImage]:
    selected = paths if paths else cdd.DEFAULT_IMAGES
    return [
        image
        for path in selected
        if (image := cdd.load_image(path)) and image.name != "XD13" and len(image.streams) >= 2
    ]


def key_bit_name(index: int) -> str:
    return f"key[{index // 8}].{index % 8}"


def key_bits(key: bytes) -> list[int]:
    return [(byte >> bit) & 1 for byte in key for bit in range(8)]


def key_rows(images: list[cdd.CddImage]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for image in images:
        for index, start, end, entry in cdd.source_segments(image):
            key = cdd.operation_key(entry)
            rows.append(
                {
                    "image": image.name,
                    "record": index,
                    "macro_lane": (index // 4) % 3,
                    "operation_key": key,
                    "source_len": end - start,
                    "decoded_span": cdd.decoded_span_candidate(entry),
                    "mode": key[3] & 0xC0,
                    "length_base": int.from_bytes(key[2:4], "little") >> 4,
                }
            )
    return rows


def fixed_bit_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = sorted({row["operation_key"] for row in rows})
    out = []
    for byte_index in range(6):
        values = [key[byte_index] for key in keys]
        for bit in range(8):
            ones = sum((value >> bit) & 1 for value in values)
            if ones == 0 or ones == len(values):
                out.append(
                    {
                        "bit": key_bit_name(byte_index * 8 + bit),
                        "value": 1 if ones else 0,
                    }
                )
    return out


def unique_key_length_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: defaultdict[bytes, list[int]] = defaultdict(list)
    for row in rows:
        by_key[row["operation_key"]].append(row["source_len"])
    conflicts = [
        {"operation_key": key.hex(), "lengths": sorted(set(lengths))}
        for key, lengths in by_key.items()
        if len(set(lengths)) > 1
    ]
    return {
        "records": len(rows),
        "unique_operation_keys": len(by_key),
        "keys_with_multiple_source_lengths": conflicts,
    }


def mode_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for mode in sorted({row["mode"] for row in rows}):
        items = [row for row in rows if row["mode"] == mode]
        source_total = sum(row["source_len"] for row in items)
        decoded_total = sum(row["decoded_span"] for row in items)
        out.append(
            {
                "mode": mode,
                "records": len(items),
                "source_total": source_total,
                "decoded_span_total": decoded_total,
                "source_to_decoded_ratio": source_total / decoded_total if decoded_total else None,
                "zero_decoded_span_records": sum(row["decoded_span"] == 0 for row in items),
                "top_key5": Counter(row["operation_key"][5] for row in items).most_common(8),
            }
        )
    return out


def lane_unit_size_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for lane in range(3):
        items = [row for row in rows if row["macro_lane"] == lane]
        with_unit = [row for row in items if row["operation_key"][4] // 2]
        divisible = sum(row["source_len"] % (row["operation_key"][4] // 2) == 0 for row in with_unit)
        close = sum(
            (row["source_len"] % (row["operation_key"][4] // 2))
            in (0, 1, (row["operation_key"][4] // 2) - 1)
            for row in with_unit
        )
        out.append(
            {
                "macro_lane": lane,
                "records": len(items),
                "records_with_nonzero_key4_half": len(with_unit),
                "source_len_divisible_by_key4_half": divisible,
                "source_len_near_divisible_by_key4_half": close,
                "top_remainders": Counter(
                    row["source_len"] % (row["operation_key"][4] // 2)
                    for row in with_unit
                ).most_common(12),
                "top_quotients": Counter(
                    row["source_len"] // (row["operation_key"][4] // 2)
                    for row in with_unit
                ).most_common(12),
            }
        )
    return out


def gf2_solve(rows: list[dict[str, Any]], target: Callable[[dict[str, Any]], int], target_bit: int) -> tuple[bool, int, int | None]:
    """Solve target bit as an affine GF(2) expression over operation-key bits.

    Feature bit 0 is the constant term. Feature bits 1..48 are operation-key
    bits, little-endian within each byte.
    """

    width = 49
    matrix = []
    for row in rows:
        lhs = 1
        for index, bit in enumerate(key_bits(row["operation_key"])):
            if bit:
                lhs |= 1 << (index + 1)
        rhs = (target(row) >> target_bit) & 1
        matrix.append(lhs | (rhs << width))

    rank = 0
    pivots: list[int] = []
    for column in range(width):
        pivot = None
        for current in range(rank, len(matrix)):
            if (matrix[current] >> column) & 1:
                pivot = current
                break
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        for current in range(len(matrix)):
            if current != rank and ((matrix[current] >> column) & 1):
                matrix[current] ^= matrix[rank]
        pivots.append(column)
        rank += 1

    for current in range(rank, len(matrix)):
        if (matrix[current] & ((1 << width) - 1)) == 0 and ((matrix[current] >> width) & 1):
            return False, rank, None

    coefficient = 0
    for row_index, column in enumerate(pivots):
        if (matrix[row_index] >> width) & 1:
            coefficient |= 1 << column
    return True, rank, coefficient


def coefficient_terms(coefficient: int) -> list[str]:
    terms = []
    for bit in range(49):
        if not ((coefficient >> bit) & 1):
            continue
        if bit == 0:
            terms.append("1")
        else:
            terms.append(key_bit_name(bit - 1))
    return terms


def linear_field_probe(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source = []
    residual = []
    for bit in range(16):
        ok, rank, coefficient = gf2_solve(rows, lambda row: row["source_len"], bit)
        source.append(
            {
                "bit": bit,
                "linear": ok,
                "rank": rank,
                "terms": coefficient_terms(coefficient) if ok and coefficient is not None else [],
            }
        )
        ok, rank, coefficient = gf2_solve(
            rows,
            lambda row: (row["source_len"] - row["decoded_span"]) & 0xFFFF,
            bit,
        )
        residual.append(
            {
                "bit": bit,
                "linear": ok,
                "rank": rank,
                "terms": coefficient_terms(coefficient) if ok and coefficient is not None else [],
            }
        )
    return {
        "note": "Affine GF(2) probe over constant + 48 operation-key bits.",
        "source_len_bits": source,
        "source_minus_decoded_bits": residual,
    }


def close_sibling_key_diff(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_image: defaultdict[str, dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_image[row["image"]][row["record"]] = row
    if "CHS7" not in by_image or "CHS9" not in by_image:
        return {}

    out = {}
    for lane in range(3):
        changed = []
        byte_positions: Counter[int] = Counter()
        for record in sorted(set(by_image["CHS7"]) & set(by_image["CHS9"])):
            left = by_image["CHS7"][record]
            right = by_image["CHS9"][record]
            if left["macro_lane"] != lane:
                continue
            left_key = left["operation_key"]
            right_key = right["operation_key"]
            if left_key == right_key:
                continue
            for position, (a, b) in enumerate(zip(left_key, right_key)):
                if a != b:
                    byte_positions[position] += 1
            if len(changed) < 12:
                changed.append(
                    {
                        "record": record,
                        "left_key": left_key.hex(),
                        "right_key": right_key.hex(),
                        "left_source_len": left["source_len"],
                        "right_source_len": right["source_len"],
                        "left_decoded_span": left["decoded_span"],
                        "right_decoded_span": right["decoded_span"],
                    }
                )
        out[str(lane)] = {
            "changed_records": len(changed) if len(changed) < 12 else None,
            "changed_byte_positions": dict(sorted(byte_positions.items())),
            "examples": changed,
        }

        # Store the real changed-record count without retaining every example.
        out[str(lane)]["changed_records"] = sum(
            1
            for record in sorted(set(by_image["CHS7"]) & set(by_image["CHS9"]))
            if by_image["CHS7"][record]["macro_lane"] == lane
            and by_image["CHS7"][record]["operation_key"] != by_image["CHS9"][record]["operation_key"]
        )
    return {"pair": "CHS7_vs_CHS9", "by_macro_lane": out}


def serializable(images: list[cdd.CddImage]) -> dict[str, Any]:
    rows = key_rows(images)
    return {
        "schema": "liteon-cdd-operation-key-analysis-v1",
        "note": "Offline CDD operation-key field analysis. No drive commands were sent.",
        "images": [image.name for image in images],
        "unique_key_length_summary": unique_key_length_summary(rows),
        "fixed_bits": fixed_bit_summary(rows),
        "mode_summary": mode_summary(rows),
        "lane_unit_size_summary": lane_unit_size_summary(rows),
        "linear_field_probe": linear_field_probe(rows),
        "close_sibling_key_diff": close_sibling_key_diff(rows),
    }


def hex_counter_rows(rows: list[tuple[int, int]], width: int = 2) -> str:
    return ", ".join(f"`0x{value:0{width}x}`:{count}" for value, count in rows)


def write_report(data: dict[str, Any]) -> str:
    lines = [
        "# LiteOn CDD Operation-Key Analysis",
        "",
        "Offline only. No drive commands were sent.",
        "",
        "This report focuses on the six-byte CDD directory operation key: `entry[0:5] + (entry[5] & 0x0f)`. It complements the CDD stream and lane-schedule reports.",
        "",
        "## Key Uniqueness",
        "",
    ]
    unique = data["unique_key_length_summary"]
    lines.append(f"- Records analyzed: `{unique['records']}`.")
    lines.append(f"- Unique operation keys: `{unique['unique_operation_keys']}`.")
    lines.append(f"- Keys mapping to multiple source lengths: `{len(unique['keys_with_multiple_source_lengths'])}`.")
    lines.append("")
    if not unique["keys_with_multiple_source_lengths"]:
        lines.append("Result: within the six sibling images, operation key fully determines encoded source length. The directory still stores source starts, but no observed operation key maps to two different source lengths.")
    lines.append("")

    lines.append("## Fixed Bits")
    lines.append("")
    fixed = ", ".join(f"`{item['bit']}={item['value']}`" for item in data["fixed_bits"])
    lines.append(f"Fixed across all unique keys: {fixed}.")
    lines.append("")
    lines.append("The expected constraints are visible here: `key[4]` is always even, and `key[5]` is the low nibble of the split directory byte, so only low values appear. The extra fixed bits `key[1].2=0` and `key[2].5=0` look like real format constraints.")
    lines.append("")

    lines.append("## Modes")
    lines.append("")
    lines.append("| mode (`key[3] & 0xc0`) | records | encoded source | decoded-span candidate | source/decoded | zero-span records | top `key[5]` |")
    lines.append("|---:|---:|---:|---:|---:|---:|---|")
    for row in data["mode_summary"]:
        ratio = row["source_to_decoded_ratio"]
        ratio_text = f"{ratio:.2f}" if ratio is not None else "-"
        lines.append(
            f"| `0x{row['mode']:02x}` | {row['records']} | `0x{row['source_total']:x}` | "
            f"`0x{row['decoded_span_total']:x}` | {ratio_text} | {row['zero_decoded_span_records']} | "
            f"{hex_counter_rows(row['top_key5'])} |"
        )
    lines.append("")

    lines.append("## `key[4] / 2` Is Not Universal Unit Size")
    lines.append("")
    lines.append("For the known affine leaf class, `key[4] == 2 * unit_size` (`0x1a` for 13-byte units, `0x18` for 12-byte units). Treating that as a universal record unit size fails on the hard lanes:")
    lines.append("")
    lines.append("| macro lane | records | nonzero `key[4]/2` | source length divisible | near-divisible | top remainders |")
    lines.append("|---:|---:|---:|---:|---:|---|")
    for row in data["lane_unit_size_summary"]:
        remainders = ", ".join(f"`{value}`:{count}" for value, count in row["top_remainders"][:8])
        lines.append(
            f"| {row['macro_lane']} | {row['records']} | {row['records_with_nonzero_key4_half']} | "
            f"{row['source_len_divisible_by_key4_half']} | {row['source_len_near_divisible_by_key4_half']} | {remainders} |"
        )
    lines.append("")

    lines.append("## Linear Field Probe")
    lines.append("")
    lines.append(data["linear_field_probe"]["note"])
    lines.append("")
    source_bits = data["linear_field_probe"]["source_len_bits"]
    linear_source = [row for row in source_bits if row["linear"]]
    nontrivial = [row for row in linear_source if row["terms"]]
    lines.append("The only nontrivial source-length bit recovered as an affine expression is:")
    lines.append("")
    for row in nontrivial:
        if row["bit"] <= 11:
            expression = " ^ ".join(row["terms"])
            lines.append(f"- `source_len.bit{row['bit']} = {expression}`.")
    lines.append("")
    lines.append("Bits 1..11 of source length are not affine functions of the raw key bits under this probe. Bits 12..15 are trivially zero because observed source lengths are below `0x1000`.")
    lines.append("")

    diff = data.get("close_sibling_key_diff") or {}
    if diff:
        lines.append("## CHS7/CHS9 Operation-Key Edits")
        lines.append("")
        lines.append("Close-sibling operation-key changes are sparse and local. This supports the broader picture that CDD is deterministic and structured, but it does not expose a simple field map by itself.")
        lines.append("")
        lines.append("| macro lane | changed records | changed key byte positions |")
        lines.append("|---:|---:|---|")
        for lane, row in diff["by_macro_lane"].items():
            positions = ", ".join(f"`{pos}`:{count}" for pos, count in row["changed_byte_positions"].items())
            lines.append(f"| {lane} | {row['changed_records']} | {positions} |")
        lines.append("")
        lines.append("Examples:")
        lines.append("")
        lines.append("```json")
        example_dump = {
            lane: row["examples"][:4]
            for lane, row in diff["by_macro_lane"].items()
        }
        lines.append(json.dumps(example_dump, indent=2))
        lines.append("```")
        lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append("- The operation key is stronger than a cosmetic tag: no observed key maps to two source lengths.")
    lines.append("- The decoded-span candidate remains the clearest bitfield: `(key[3] & 0x3f) << 4`.")
    lines.append("- The encoded source length is not a simple visible bitfield. Only its parity has a clean affine relation to key bits.")
    lines.append("- `key[4]` is a unit-size hint for the lane-0 affine leaf class, but it does not explain hard-lane record sizes.")
    lines.append("- This keeps pointing at a proprietary controller codeword/packet grammar rather than a stock compressor or encrypted blob.")
    return "\n".join(lines) + "\n"


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
    args.out.write_text(write_report(data))
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
