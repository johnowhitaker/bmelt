#!/usr/bin/env python3
"""Probe whether CDD hard records are literal DVD-format frames.

The previous hard-record report found source-length clustering near DVD
recording-frame sizes, especially 2366 bytes (13 rows * 182 bytes).  This
script tests the strongest literal version of that idea:

* does DVD-style scrambling make known decoded 8051 bytes appear directly?
* do 2366-byte source windows satisfy DVD PI row parity?

Negative results are still useful here.  They separate "literal ECMA-267 DVD
recording frame" from the weaker but still plausible "the controller reuses
DVD-ish block/ECC hardware or dimensions."
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KNOWN_DIR = ROOT / "analysis/8051/cdd-known-output-records-20260501"
DEFAULT_RECORDS = [50, 51, 55, 58, 60, 62, 66, 67, 68, 70, 73, 86, 87]

DVD_PRESET_VALUES = [
    0x0001,
    0x5500,
    0x0002,
    0x2A00,
    0x0004,
    0x5400,
    0x0008,
    0x2800,
    0x0010,
    0x5000,
    0x0020,
    0x2001,
    0x0040,
    0x4002,
    0x0080,
    0x0005,
]


def dvd_scrambler(seed: int, length: int) -> bytes:
    """Generate the ECMA-267-style 15-bit DVD scrambling sequence.

    Figure 19 is an LFSR with feedback from r14 and r10.  The low byte
    r7..r0 is emitted before each 8-bit shift.
    """

    state = seed & 0x7FFF
    out = bytearray(length)
    for index in range(length):
        out[index] = state & 0xFF
        for _ in range(8):
            feedback = ((state >> 14) ^ (state >> 10)) & 1
            state = ((state << 1) & 0x7FFF) | feedback
    return bytes(out)


def xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right))


def known_runs(mask: bytes) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, byte in enumerate(mask):
        if byte and start is None:
            start = index
        if (not byte or index == len(mask) - 1) and start is not None:
            end = index if not byte else index + 1
            runs.append((start, end))
            start = None
    return runs


def known_ngram_sets(out: bytes, mask: bytes, lengths: list[int]) -> dict[int, set[bytes]]:
    sets: dict[int, set[bytes]] = {}
    runs = known_runs(mask)
    for length in lengths:
        values: set[bytes] = set()
        for start, end in runs:
            for offset in range(start, end - length + 1):
                values.add(out[offset : offset + length])
        sets[length] = values
    return sets


def best_known_ngram(buffer: bytes, sets: dict[int, set[bytes]]) -> dict[str, Any]:
    for length in sorted(sets, reverse=True):
        values = sets[length]
        if not values:
            continue
        for offset in range(0, len(buffer) - length + 1):
            if buffer[offset : offset + length] in values:
                return {"length": length, "source_offset": offset}
    return {"length": 0, "source_offset": None}


def dvd_frame_shapes(source: bytes) -> list[tuple[str, bytes]]:
    shapes = [("raw", source)]
    if len(source) < 2366:
        return shapes

    for start in range(0, len(source) - 2366 + 1):
        frame = source[start : start + 2366]
        rows = [frame[row * 182 : (row + 1) * 182] for row in range(13)]
        shapes.append((f"frame+0x{start:x}", frame))
        shapes.append((f"frame+0x{start:x}:drop-pi-13x172", b"".join(row[:172] for row in rows)))
        shapes.append((f"frame+0x{start:x}:drop-pi-12x172", b"".join(row[:172] for row in rows[:12])))
    return shapes


def build_gf_tables() -> tuple[list[int], list[int]]:
    exp = [0] * 512
    log = [0] * 256
    value = 1
    for index in range(255):
        exp[index] = value
        log[value] = index
        value <<= 1
        if value & 0x100:
            value ^= 0x11D
    for index in range(255, 512):
        exp[index] = exp[index - 255]
    return exp, log


GF_EXP, GF_LOG = build_gf_tables()


def gf_mul(left: int, right: int) -> int:
    if left == 0 or right == 0:
        return 0
    return GF_EXP[GF_LOG[left] + GF_LOG[right]]


def dvd_pi_syndromes(row: bytes) -> list[int]:
    """Return DVD RS(182,172) PI syndromes for one row.

    The PI generator roots are alpha^0..alpha^9 over primitive polynomial
    x^8 + x^4 + x^3 + x^2 + 1.
    """

    out = []
    for root_power in range(10):
        alpha = GF_EXP[root_power]
        syndrome = 0
        for byte in row:
            syndrome = gf_mul(syndrome, alpha) ^ byte
        out.append(syndrome)
    return out


def count_valid_pi_rows(frame: bytes) -> int:
    rows = [frame[row * 182 : (row + 1) * 182] for row in range(13)]
    return sum(all(value == 0 for value in dvd_pi_syndromes(row)) for row in rows)


def best_pi_window(source: bytes) -> dict[str, Any]:
    if len(source) < 2366:
        return {"valid_rows": 0, "window_offset": None, "variant": "source-shorter-than-2366"}

    best = {"valid_rows": 0, "window_offset": 0, "variant": "raw"}
    for start in range(0, len(source) - 2366 + 1):
        frame = source[start : start + 2366]
        variants = {
            "raw": frame,
            "byte-inverted": bytes(byte ^ 0xFF for byte in frame),
            "row-byte-reversed": b"".join(
                frame[row * 182 : (row + 1) * 182][::-1] for row in range(13)
            ),
            "frame-reversed": frame[::-1],
        }
        for name, candidate in variants.items():
            valid_rows = count_valid_pi_rows(candidate)
            if valid_rows > best["valid_rows"]:
                best = {"valid_rows": valid_rows, "window_offset": start, "variant": name}
    return best


def analyze_record(record: int, known_dir: Path) -> dict[str, Any]:
    source = (known_dir / f"record-{record:03d}-encoded-source.bin").read_bytes()
    output = (known_dir / f"record-{record:03d}-known-output.bin").read_bytes()
    mask = (known_dir / f"record-{record:03d}-known-mask.bin").read_bytes()
    sets = known_ngram_sets(output, mask, [16, 12, 10, 8, 6, 5, 4])

    candidates = []
    for shape_name, shape in dvd_frame_shapes(source):
        raw_match = best_known_ngram(shape, sets)
        candidates.append({"shape": shape_name, "transform": "none", **raw_match})
        for seed in DVD_PRESET_VALUES:
            descrambled = xor_bytes(shape, dvd_scrambler(seed, len(shape)))
            match = best_known_ngram(descrambled, sets)
            candidates.append(
                {
                    "shape": shape_name,
                    "transform": f"dvd-lfsr-seed-0x{seed:04x}",
                    **match,
                }
            )

    candidates.sort(key=lambda item: (-item["length"], item["shape"], item["transform"]))
    return {
        "record": record,
        "source_len": len(source),
        "decoded_span": len(output),
        "known_bytes": sum(1 for byte in mask if byte),
        "distance_to_2366": len(source) - 2366,
        "best_direct_or_dvd_lfsr_ngram": candidates[:8],
        "best_dvd_pi_window": best_pi_window(source),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema": "liteon-cdd-dvd-reuse-hypotheses-v1",
        "known_dir": str(args.known_dir),
        "dvd_reference": {
            "recording_frame_bytes": 2366,
            "recording_frame_shape": "13 rows * 182 bytes",
            "pi_code": "RS(182,172), 10 PI bytes per row",
            "scrambler_presets": [f"0x{value:04x}" for value in DVD_PRESET_VALUES],
        },
        "records": [analyze_record(record, args.known_dir) for record in args.records],
    }


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def render_md(report: dict[str, Any]) -> str:
    rows = report["records"]

    def candidate_label(row: dict[str, Any]) -> str:
        best = row["best_direct_or_dvd_lfsr_ngram"][0]
        if best["length"] == 0:
            return "`none >= 4 bytes`"
        return "`" + best["shape"] + " / " + best["transform"] + "`"

    lines = [
        "# CDD DVD-Reuse Hypothesis Probes",
        "",
        "Date: 2026-05-01",
        "",
        "Offline only. No drive commands were sent.",
        "",
        "This is a targeted follow-up to the hard-record size clue. ECMA-267",
        "DVD recording frames are 2366 bytes, arranged as 13 rows of 182",
        "bytes, with 10 PI Reed-Solomon parity bytes per row. The CDD hard",
        "records often sit near that size, so this report tests the literal",
        "DVD-frame interpretation before treating it as only a loose hardware",
        "reuse clue.",
        "",
        "Reference: <https://ecma-international.org/publications-and-standards/standards/Ecma-267/>",
        "",
        "## DVD LFSR / Direct Known-Output Matches",
        "",
        "For each known-output record, I tried raw source bytes, every possible",
        "2366-byte frame window when present, simple row parity-column drops,",
        "and the 16 ECMA DVD scrambler preset values. The score below is the",
        "longest exact known-output byte sequence found in any transformed",
        "candidate. Values at 4 bytes are random-level evidence; useful hits",
        "would need to be much longer.",
        "",
        md_table(
            ["record", "source", "known", "distance to 2366", "best exact run", "best candidate"],
            [
                [
                    str(row["record"]),
                    str(row["source_len"]),
                    str(row["known_bytes"]),
                    f"{row['distance_to_2366']:+d}",
                    str(row["best_direct_or_dvd_lfsr_ngram"][0]["length"]),
                    candidate_label(row),
                ]
                for row in rows
            ],
        ),
        "",
        "## DVD PI Row-Parity Check",
        "",
        "If a 2366-byte CDD source window were literally a DVD recording frame,",
        "its 13 rows should satisfy the DVD PI RS(182,172) parity check. I tested",
        "raw, byte-inverted, row-byte-reversed, and whole-frame-reversed windows.",
        "",
        md_table(
            ["record", "source", "best valid PI rows", "window", "variant"],
            [
                [
                    str(row["record"]),
                    str(row["source_len"]),
                    str(row["best_dvd_pi_window"]["valid_rows"]),
                    (
                        "n/a"
                        if row["best_dvd_pi_window"]["window_offset"] is None
                        else f"0x{row['best_dvd_pi_window']['window_offset']:x}"
                    ),
                    "`" + row["best_dvd_pi_window"]["variant"] + "`",
                ]
                for row in rows
            ],
        ),
        "",
        "## Current Read",
        "",
        "- The source-length clue is real, but these records are not literal",
        "  ECMA-267 DVD recording frames.",
        "- DVD LFSR descrambling plus simple frame/row extraction does not reveal",
        "  the known decoded 8051 bytes directly.",
        "- No tested 2366-byte source window satisfies even one DVD PI row-parity",
        "  check, so the standard DVD inner-code layout is not present verbatim.",
        "- The better working model is now narrower: CDD may reuse DVD-like",
        "  dimensions, scheduling, or controller ECC datapaths, but the hard",
        "  record format is a custom controller codeword layer.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--known-dir", type=Path, default=DEFAULT_KNOWN_DIR)
    parser.add_argument("--records", type=int, nargs="*", default=DEFAULT_RECORDS)
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
