#!/usr/bin/env python3
"""Probe CDD hard-record hypotheses against known-output records.

This is an offline sanity-check script for the high-coverage CDD records that
now have normal-mode known-output exports.  It does not attempt a full decoder;
it tests a few concrete ideas:

* whether source lengths cluster near DVD-format frame sizes;
* whether the encoded source already looks like post-modulation RLL channel
  bits;
* whether a sparse linear byte projection can explain the known output.

The output is meant to keep failed hypotheses reproducible and to highlight the
next narrow static/live tests.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD_MAP = ROOT / "references/firmware/extracted/liteon-cdd-record-map.json"
DEFAULT_KNOWN_DIR = ROOT / "analysis/8051/cdd-known-output-records-20260501"


DVD_SIZES = {
    "main_data": 2048,
    "data_frame": 2064,
    "recording_frame": 2366,
}


def load_ld5m_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    for image in data["images"]:
        if image["image"] == "LD5M":
            return image["records"]
    raise ValueError(f"LD5M not found in {path}")


def load_all_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    rows: list[dict[str, Any]] = []
    for image in data["images"]:
        for record in image["records"]:
            key = bytes.fromhex(record["operation_key"])
            rows.append(
                {
                    "image": image["image"],
                    "record": record["index"],
                    "mode": record["mode"],
                    "key4": key[4],
                    "key5": key[5],
                    "source_len": record["source_len"],
                    "decoded_span": record["decoded_span"],
                    "operation_key": record["operation_key"],
                }
            )
    return rows


def median(values: list[int]) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    mid = len(values) // 2
    if len(values) & 1:
        return float(values[mid])
    return (values[mid - 1] + values[mid]) / 2


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def bits(data: bytes, *, msb_first: bool, invert: bool = False) -> list[int]:
    out: list[int] = []
    bit_order = range(7, -1, -1) if msb_first else range(8)
    for byte in data:
        if invert:
            byte ^= 0xFF
        out.extend((byte >> bit) & 1 for bit in bit_order)
    return out


def nrzi_to_nrz(channel_bits: list[int]) -> list[int]:
    out = []
    previous = 0
    for bit in channel_bits:
        out.append(bit ^ previous)
        previous = bit
    return out


def rll_stats(seq: list[int]) -> dict[str, Any]:
    zero_runs = []
    zeros = 0
    seen_one = False
    for bit in seq:
        if bit:
            if seen_one:
                zero_runs.append(zeros)
            seen_one = True
            zeros = 0
        elif seen_one:
            zeros += 1
    if not zero_runs:
        return {"runs": 0, "violations": 0, "violation_fraction": 0.0}
    violations = sum(1 for run in zero_runs if run < 2 or run > 10)
    return {
        "runs": len(zero_runs),
        "min_run": min(zero_runs),
        "max_run": max(zero_runs),
        "violations": violations,
        "violation_fraction": violations / len(zero_runs),
        "histogram_0_to_12": {str(i): zero_runs.count(i) for i in range(13)},
    }


def best_rll_view(data: bytes) -> dict[str, Any]:
    rows = []
    for msb_first in (True, False):
        for invert in (False, True):
            raw_bits = bits(data, msb_first=msb_first, invert=invert)
            for view, seq in (("raw", raw_bits), ("nrzi_derivative", nrzi_to_nrz(raw_bits))):
                stats = rll_stats(seq)
                rows.append(
                    {
                        "bit_order": "msb" if msb_first else "lsb",
                        "invert": invert,
                        "view": view,
                        **stats,
                    }
                )
    return min(rows, key=lambda row: row["violation_fraction"])


def known_range(mask: bytes) -> tuple[int, int]:
    ranges = []
    start = None
    for index, byte in enumerate(mask):
        if byte and start is None:
            start = index
        if (not byte or index == len(mask) - 1) and start is not None:
            end = index if not byte else index + 1
            ranges.append((start, end))
            start = None
    if not ranges:
        return (0, 0)
    return max(ranges, key=lambda item: item[1] - item[0])


def bit_reverse_byte(value: int) -> int:
    return int(f"{value:08b}"[::-1], 2)


def transform(value: int, kind: str) -> int:
    if kind == "id":
        return value
    if kind == "not":
        return value ^ 0xFF
    if kind == "bitrev":
        return bit_reverse_byte(value)
    if kind == "bitrev_not":
        return bit_reverse_byte(value) ^ 0xFF
    raise ValueError(kind)


def sparse_projection_probe(src: bytes, known: bytes, out_start: int, out_span: int) -> dict[str, Any]:
    """Try simple monotonic byte projections from source to known output."""

    candidates: list[tuple[int, int]] = [
        (len(src), out_span),
        (len(src) - 1, out_span),
        (len(src) + 1, out_span),
        (len(src) // 2, out_span),
        (len(src) * 2 // 3, out_span),
        (len(src) // 3, out_span),
    ]
    best: dict[str, Any] = {
        "byte_equal_fraction": 0.0,
        "low_nibble_equal_fraction": 0.0,
        "high_nibble_equal_fraction": 0.0,
        "bit_equal_fraction": 0.0,
    }
    for numerator, denominator in candidates:
        if numerator <= 0 or denominator <= 0:
            continue
        for phase in range(-64, 65):
            for kind in ("id", "not", "bitrev", "bitrev_not"):
                total = byte_equal = low_nibble = high_nibble = bit_equal = 0
                for rel, expected in enumerate(known, out_start):
                    index = (rel * numerator) // denominator + phase
                    if not 0 <= index < len(src):
                        continue
                    actual = transform(src[index], kind)
                    total += 1
                    byte_equal += actual == expected
                    low_nibble += (actual & 0x0F) == (expected & 0x0F)
                    high_nibble += (actual >> 4) == (expected >> 4)
                    bit_equal += 8 - (actual ^ expected).bit_count()
                if total < 64:
                    continue
                row = {
                    "byte_equal_fraction": byte_equal / total,
                    "low_nibble_equal_fraction": low_nibble / total,
                    "high_nibble_equal_fraction": high_nibble / total,
                    "bit_equal_fraction": bit_equal / (8 * total),
                    "total": total,
                    "numerator": numerator,
                    "denominator": denominator,
                    "phase": phase,
                    "transform": kind,
                }
                if (
                    row["byte_equal_fraction"],
                    row["low_nibble_equal_fraction"],
                    row["high_nibble_equal_fraction"],
                    row["bit_equal_fraction"],
                ) > (
                    best["byte_equal_fraction"],
                    best["low_nibble_equal_fraction"],
                    best["high_nibble_equal_fraction"],
                    best["bit_equal_fraction"],
                ):
                    best = row
    return best


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    all_records = load_all_records(args.record_map)
    source_summary = []
    macro_position_summary = []
    by_mode_key5: dict[tuple[int, int], list[int]] = defaultdict(list)
    for row in all_records:
        by_mode_key5[(row["mode"], row["key5"])].append(row["source_len"])
        if row["image"] == "LD5M":
            pass
    for (mode, key5), lengths in sorted(by_mode_key5.items()):
        if len(lengths) < 5:
            continue
        source_summary.append(
            {
                "mode": mode,
                "key5": key5,
                "records": len(lengths),
                "source_median": median(lengths),
                "source_mean": sum(lengths) / len(lengths),
                "near_2048_plus_minus_80": sum(abs(value - 2048) <= 80 for value in lengths),
                "near_2064_plus_minus_80": sum(abs(value - 2064) <= 80 for value in lengths),
                "near_2366_plus_minus_80": sum(abs(value - 2366) <= 80 for value in lengths),
            }
        )

    ld5m_rows = [row for row in all_records if row["image"] == "LD5M"]
    for macro_pos in range(12):
        rows = [row for row in ld5m_rows if row["record"] % 12 == macro_pos]
        lengths = [row["source_len"] for row in rows]
        modes = Counter(row["mode"] for row in rows)
        key5 = Counter(row["key5"] for row in rows)
        macro_position_summary.append(
            {
                "macro_position": macro_pos,
                "records": len(rows),
                "source_median": median(lengths),
                "source_mean": sum(lengths) / len(lengths),
                "near_2366_plus_minus_80": sum(abs(value - 2366) <= 80 for value in lengths),
                "modes": {f"0x{mode:02x}": count for mode, count in modes.most_common()},
                "key5": {f"0x{value:x}": count for value, count in key5.most_common()},
            }
        )

    known_records = []
    for source_path in sorted(args.known_dir.glob("record-*-encoded-source.bin")):
        rec = int(source_path.name.split("-")[1])
        out_path = args.known_dir / f"record-{rec:03d}-known-output.bin"
        mask_path = args.known_dir / f"record-{rec:03d}-known-mask.bin"
        if not out_path.exists() or not mask_path.exists():
            continue
        src = source_path.read_bytes()
        out = out_path.read_bytes()
        mask = mask_path.read_bytes()
        start, end = known_range(mask)
        if end <= start:
            continue
        known = out[start:end]
        known_records.append(
            {
                "record": rec,
                "source_len": len(src),
                "decoded_span": len(out),
                "known_range": [start, end],
                "known_bytes": sum(1 for byte in mask if byte),
                "source_entropy": entropy(src),
                "known_entropy": entropy(known),
                "distance_to_dvd_sizes": {name: len(src) - value for name, value in DVD_SIZES.items()},
                "best_rll_view": best_rll_view(src),
                "sparse_projection": sparse_projection_probe(src, known, start, len(out)),
            }
        )

    return {
        "schema": "liteon-cdd-hard-record-hypothesis-probes-v1",
        "record_map": str(args.record_map),
        "known_dir": str(args.known_dir),
        "dvd_reference_sizes": DVD_SIZES,
        "source_length_by_mode_key5": source_summary,
        "ld5m_macro_position_summary": macro_position_summary,
        "known_record_probes": sorted(known_records, key=lambda row: (-row["known_bytes"], row["record"])),
    }


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# CDD Hard-Record Hypothesis Probes",
        "",
        "Date: 2026-05-01",
        "",
        "Offline only. No drive commands were sent.",
        "",
        "This report tests a few concrete hypotheses for the high-coverage",
        "CDD records that now have normal-mode known-output exports.",
        "",
        "## DVD-Format Size Clue",
        "",
        "The hard-record source lengths cluster around byte counts used by DVD",
        "formatting before modulation: 2048-byte main data, 2064-byte data",
        "frames, and especially 2366-byte recording frames. ECMA-267 describes",
        "recording frames as 13 rows of 182 bytes, i.e. 2366 bytes, before",
        "8-to-16 modulation.",
        "",
        "Reference: <https://ecma-international.org/publications-and-standards/standards/Ecma-267/>",
        "",
        md_table(
            ["mode", "key5", "records", "median source", "near 2048", "near 2064", "near 2366"],
            [
                [
                    f"`0x{row['mode']:02x}`",
                    f"`0x{row['key5']:x}`",
                    str(row["records"]),
                    f"{row['source_median']:.0f}",
                    str(row["near_2048_plus_minus_80"]),
                    str(row["near_2064_plus_minus_80"]),
                    str(row["near_2366_plus_minus_80"]),
                ]
                for row in report["source_length_by_mode_key5"]
            ],
        ),
        "",
        "This is not proof that CDD is DVD sector data. It is a strong hint that",
        "the controller designers may be reusing optical/ECC-style block sizes",
        "or hardware datapaths.",
        "",
        "## 12-Record Schedule Check",
        "",
        "The previously observed affine leaf schedule repeats every 12 records.",
        "That is interesting because DVD ECC/recording-frame construction also",
        "has a 12-row cadence before parity interleaving. The LD5M source",
        "lengths are not perfectly periodic, but the first three positions in",
        "each 12-record group are much more often near 2366 bytes, and position",
        "3 is a low-source-length/control-heavy lane.",
        "",
        md_table(
            ["pos mod 12", "records", "median source", "near 2366", "top modes", "top key5"],
            [
                [
                    str(row["macro_position"]),
                    str(row["records"]),
                    f"{row['source_median']:.0f}",
                    str(row["near_2366_plus_minus_80"]),
                    ", ".join(f"`{mode}`:{count}" for mode, count in list(row["modes"].items())[:3]),
                    ", ".join(f"`{key}`:{count}" for key, count in list(row["key5"].items())[:3]),
                ]
                for row in report["ld5m_macro_position_summary"]
            ],
        ),
        "",
        "This makes the DVD-like angle more worth testing, but still only as an",
        "analogy or reused-hardware hypothesis. CDD record counts and decoded",
        "spans do not directly match a vanilla DVD ECC block.",
        "",
        "## RLL/EFMPlus-Like Channel-Bit Test",
        "",
        "If the encoded CDD source were already post-modulation channel bits, its",
        "bitstream should strongly satisfy the DVD RLL(2,10) constraint. It does",
        "not. The best raw/inverted/MSB/LSB/NRZI-derived view still has large",
        "run-length violation fractions, close to random data.",
        "",
        md_table(
            ["record", "source", "known", "best view", "RLL violations", "min/max run"],
            [
                [
                    str(row["record"]),
                    str(row["source_len"]),
                    str(row["known_bytes"]),
                    f"`{row['best_rll_view']['bit_order']},{'inv' if row['best_rll_view']['invert'] else 'norm'},{row['best_rll_view']['view']}`",
                    f"{row['best_rll_view']['violation_fraction']:.0%}",
                    f"{row['best_rll_view'].get('min_run')}/{row['best_rll_view'].get('max_run')}",
                ]
                for row in report["known_record_probes"][:16]
            ],
        ),
        "",
        "So the CDD source is not simply packed EFMPlus/channel data. If the DVD",
        "size clue matters, it is more likely pre-modulation scrambled/ECC-ish",
        "record material or a custom format inspired by those hardware blocks.",
        "",
        "## Sparse Systematic-Byte Probe",
        "",
        "I also tested simple monotonic byte projections of the form",
        "`source[floor(i * numerator / denominator) + phase]`, with identity,",
        "NOT, bit-reversed, and bit-reversed-NOT transforms. These stay at",
        "random-looking match rates.",
        "",
        md_table(
            ["record", "byte eq", "lo nibble", "hi nibble", "bit eq", "best transform"],
            [
                [
                    str(row["record"]),
                    f"{row['sparse_projection']['byte_equal_fraction']:.1%}",
                    f"{row['sparse_projection']['low_nibble_equal_fraction']:.1%}",
                    f"{row['sparse_projection']['high_nibble_equal_fraction']:.1%}",
                    f"{row['sparse_projection']['bit_equal_fraction']:.1%}",
                    f"`{row['sparse_projection'].get('transform')} {row['sparse_projection'].get('numerator')}/{row['sparse_projection'].get('denominator')} phase {row['sparse_projection'].get('phase')}`",
                ]
                for row in report["known_record_probes"][:16]
            ],
        ),
        "",
        "## Current Read",
        "",
        "- The hard records are not lightly scrambled byte streams.",
        "- They are not already post-modulation EFMPlus/RLL channel bits.",
        "- Their source lengths are suspiciously close to DVD-style",
        "  pre-modulation/ECC frame sizes, especially around 2366 bytes.",
        "- `key5` correlates strongly with source-length class, so it likely",
        "  participates in selecting code rate/redundancy/block layout.",
        "- The next static test worth doing is not another broad XOR scan. It is",
        "  a targeted implementation of DVD-like scrambling/ECC/interleave",
        "  hypotheses, compared against high-coverage records' masked known",
        "  outputs.",
        "",
        "Record 87 remains the cleanest first target for generic hard-record",
        "transform work because its known-output export has high coverage and no",
        "slot variants. For the DVD-size clue specifically, records closer to the",
        "2366-byte source length, such as 51, 55, 60, 66, and 68, are the better",
        "cross-checks even though they have more public-slot ambiguity.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-map", type=Path, default=DEFAULT_RECORD_MAP)
    parser.add_argument("--known-dir", type=Path, default=DEFAULT_KNOWN_DIR)
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
