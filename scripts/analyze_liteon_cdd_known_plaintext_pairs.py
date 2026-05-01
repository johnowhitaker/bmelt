#!/usr/bin/env python3
"""Build known-plaintext pairs between encoded CDD records and normal chunks.

Normal-mode READ BUFFER work-window captures expose rotating 0x40-byte chunks
that look like decoded controller/runtime code.  The hidden-runtime classifier
maps many of those chunks back to candidate CDD records using the decoded-span
layout.  This script collects those pairs in one place:

    encoded CDD source span from the F0 image
    observed decoded 0x40-byte normal-runtime chunk
    candidate public-slot bucket inside the CDD record

The goal is not to claim a full decoder.  It gives the next static pass a
small known-plaintext corpus and records which simple encodings are already
implausible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


def parse_int(value: str) -> int:
    return int(value, 0)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def bit_reverse_byte(value: int) -> int:
    return int(f"{value:08b}"[::-1], 2)


def longest_common_substring(a: bytes, b: bytes) -> dict[str, int]:
    """Return the longest direct contiguous match between two byte strings."""

    best_len = 0
    best_a = 0
    best_b = 0
    previous = [0] * (len(b) + 1)
    for i, byte_a in enumerate(a, 1):
        current = [0] * (len(b) + 1)
        for j, byte_b in enumerate(b, 1):
            if byte_a == byte_b:
                current[j] = previous[j - 1] + 1
                if current[j] > best_len:
                    best_len = current[j]
                    best_a = i - best_len
                    best_b = j - best_len
        previous = current
    return {"length": best_len, "decoded_offset": best_a, "source_offset": best_b}


def longest_xor_ngram(decoded: bytes, source: bytes, max_len: int = 8, min_len: int = 3) -> dict[str, int | None]:
    """Find the longest constant-XOR n-gram match, bounded for speed.

    This is not a full longest-common-substring over all XOR constants.  It is a
    cheap negative check for obvious bytewise XOR encodings.
    """

    for length in range(max_len, min_len - 1, -1):
        source_windows = {source[offset : offset + length]: offset for offset in range(0, len(source) - length + 1)}
        for xor_value in range(256):
            for decoded_offset in range(0, len(decoded) - length + 1):
                transformed = bytes(byte ^ xor_value for byte in decoded[decoded_offset : decoded_offset + length])
                source_offset = source_windows.get(transformed)
                if source_offset is not None:
                    return {
                        "length": length,
                        "xor": xor_value,
                        "decoded_offset": decoded_offset,
                        "source_offset": source_offset,
                    }
    return {"length": 0, "xor": None, "decoded_offset": 0, "source_offset": 0}


def load_ld5m_records(record_map: Path) -> list[dict[str, Any]]:
    data = json.loads(record_map.read_text())
    for image in data["images"]:
        if "LD5M" in image["image"].upper() or "LD5M" in image["image"]:
            return image["records"]
    raise ValueError(f"no LD5M image in {record_map}")


def compact_hex(data: bytes, limit: int = 24) -> str:
    if len(data) <= limit:
        return data.hex()
    return data[:limit].hex() + "..."


def interval_union(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return sum(end - start for start, end in merged)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    f0 = args.f0.read_bytes()
    records = load_ld5m_records(args.record_map)
    hidden = json.loads(args.hidden_chunks.read_text())

    transforms: dict[str, Callable[[bytes], bytes]] = {
        "direct": lambda data: data,
        "bitwise_not": lambda data: bytes((~byte) & 0xFF for byte in data),
        "bit_reverse": lambda data: bytes(bit_reverse_byte(byte) for byte in data),
    }

    pairs: list[dict[str, Any]] = []
    per_record_intervals: dict[int, list[tuple[int, int]]] = defaultdict(list)
    per_record_chunks: dict[int, Counter[str]] = defaultdict(Counter)

    for chunk in hidden["top_hidden_runtime_chunks"]:
        decoded = bytes.fromhex(chunk["hex"])
        decoded_sha = sha256_hex(decoded)
        for candidate in chunk.get("cdd_public_offset_candidates", []):
            record_index = int(candidate["record"])
            record = records[record_index]
            source = f0[record["source_start"] : record["source_end"]]
            public_offset = int(str(candidate["public_offset"]), 16)
            decoded_relative = public_offset - int(record["decoded_start"])
            clipped_start = max(0, decoded_relative)
            clipped_end = min(int(record["decoded_span"]), decoded_relative + len(decoded))
            if clipped_end > clipped_start:
                per_record_intervals[record_index].append((clipped_start, clipped_end))
                per_record_chunks[record_index][chunk["short"]] += int(candidate["count"])

            transform_checks = {}
            for name, transform in transforms.items():
                transform_checks[name] = longest_common_substring(transform(decoded), source)
            transform_checks["constant_xor_ngram"] = longest_xor_ngram(decoded, source)

            pairs.append(
                {
                    "chunk_short": chunk["short"],
                    "chunk_sha256": chunk["sha256"],
                    "decoded_sha256": decoded_sha,
                    "decoded_hex": decoded.hex(),
                    "decoded_entropy": entropy(decoded),
                    "public_offset": public_offset,
                    "record": record_index,
                    "decoded_relative": decoded_relative,
                    "decoded_clipped_start": clipped_start,
                    "decoded_clipped_end": clipped_end,
                    "record_operation_key": record["operation_key"],
                    "record_mode": record["mode"],
                    "record_decoded_start": record["decoded_start"],
                    "record_decoded_span": record["decoded_span"],
                    "record_source_start": record["source_start"],
                    "record_source_end": record["source_end"],
                    "record_source_len": record["source_len"],
                    "record_source_sha256": sha256_hex(source),
                    "record_source_entropy": entropy(source),
                    "record_source_prefix": compact_hex(source[:48], 48),
                    "record_source_suffix": compact_hex(source[-48:], 48),
                    "source_to_decoded_ratio": record["source_len"] / record["decoded_span"]
                    if record["decoded_span"]
                    else None,
                    "transform_checks": transform_checks,
                }
            )

    record_rows = []
    for record_index, intervals in sorted(per_record_intervals.items()):
        record = records[record_index]
        known = interval_union(intervals)
        record_rows.append(
            {
                "record": record_index,
                "operation_key": record["operation_key"],
                "mode": record["mode"],
                "source_len": record["source_len"],
                "decoded_span": record["decoded_span"],
                "known_decoded_bytes": known,
                "known_decoded_fraction": known / record["decoded_span"] if record["decoded_span"] else 0,
                "chunks": [
                    {"chunk": chunk, "observations": count}
                    for chunk, count in per_record_chunks[record_index].most_common()
                ],
            }
        )

    return {
        "schema": "liteon-cdd-known-plaintext-pairs-v1",
        "f0": str(args.f0),
        "record_map": str(args.record_map),
        "hidden_chunks": str(args.hidden_chunks),
        "pair_count": len(pairs),
        "records_with_pairs": len(record_rows),
        "records": record_rows,
        "pairs": pairs,
        "summary": {
            "max_direct_lcs": max(
                (pair["transform_checks"]["direct"]["length"] for pair in pairs),
                default=0,
            ),
            "max_not_lcs": max(
                (pair["transform_checks"]["bitwise_not"]["length"] for pair in pairs),
                default=0,
            ),
            "max_bit_reverse_lcs": max(
                (pair["transform_checks"]["bit_reverse"]["length"] for pair in pairs),
                default=0,
            ),
            "max_constant_xor_ngram": max(
                (pair["transform_checks"]["constant_xor_ngram"]["length"] for pair in pairs),
                default=0,
            ),
        },
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# CDD Known-Plaintext Pair Corpus",
        "",
        "This report pairs encoded CDD record source spans with decoded-looking",
        "normal-runtime 0x40-byte chunks observed through the public normal",
        "`READ BUFFER id=01 offset=0x070000` work window.",
        "",
        "The mapping is based on the existing CDD decoded-span model, so the pairs",
        "are candidates rather than proof of a complete decoder. They are still",
        "useful because chunks like the GET CONFIG response bridge are clearly",
        "8051 code-like after decode and consistently land inside specific CDD",
        "records.",
        "",
        "## Summary",
        "",
        f"- pair count: `{report['pair_count']}`",
        f"- records with pairs: `{report['records_with_pairs']}`",
        f"- max direct longest common substring: `{report['summary']['max_direct_lcs']}` bytes",
        f"- max bitwise-NOT longest common substring: `{report['summary']['max_not_lcs']}` bytes",
        f"- max bit-reversed longest common substring: `{report['summary']['max_bit_reverse_lcs']}` bytes",
        f"- max constant-XOR n-gram: `{report['summary']['max_constant_xor_ngram']}` bytes",
        "",
        "The negative transform checks are useful: these known decoded chunks do",
        "not appear literally in their encoded source spans, nor through a simple",
        "bytewise NOT, bit reversal, or constant XOR. That pushes the CDD body",
        "model toward a real record codeword/packing format rather than a light",
        "obfuscation pass.",
        "",
        "## Records With Known Decoded Chunks",
        "",
        "| record | mode | op key | source | decoded span | slot span | chunks |",
        "|---:|---:|---|---:|---:|---:|---|",
    ]
    for row in sorted(report["records"], key=lambda item: (-item["known_decoded_bytes"], item["record"])):
        chunks = ", ".join(f"`{item['chunk']}` x{item['observations']}" for item in row["chunks"][:4])
        lines.append(
            f"| {row['record']} | `0x{row['mode']:02x}` | `{row['operation_key']}` | "
            f"{row['source_len']} | {row['decoded_span']} | "
            f"{row['known_decoded_bytes']} ({row['known_decoded_fraction']:.0%}) | {chunks} |"
        )

    lines += [
        "",
        "## Highest-Signal Pairs",
        "",
        "| chunk | record | public offset | rel | mode | op key | source/decoded | decoded prefix |",
        "|---|---:|---:|---:|---:|---|---:|---|",
    ]
    for pair in sorted(
        report["pairs"],
        key=lambda item: (
            -item["record_decoded_span"],
            item["record"],
            item["decoded_relative"],
            item["chunk_short"],
        ),
    )[:48]:
        lines.append(
            f"| `{pair['chunk_short']}` | {pair['record']} | `0x{pair['public_offset']:04x}` | "
            f"`0x{pair['decoded_relative']:x}` | `0x{pair['record_mode']:02x}` | "
            f"`{pair['record_operation_key']}` | {pair['record_source_len']}/{pair['record_decoded_span']} "
            f"({pair['source_to_decoded_ratio']:.2f}x) | `{pair['decoded_hex'][:32]}...` |"
        )

    lines += [
        "",
        "## Practical Interpretation",
        "",
        "- Records `58..62` are currently the most valuable known-plaintext region",
        "  because they contain the normal GET CONFIG / public response bridge",
        "  machinery.",
        "- The public offsets are phase-shifted work-window slots, not direct",
        "  decoded offsets. `decoded_relative` is a record-bucket hint, not a",
        "  proven byte-accurate placement. Multiple different chunks can appear",
        "  at the same public slot.",
        "- The source-to-decoded ratios vary strongly by mode and operation key.",
        "  That variation looks like record grammar/redundancy, not a fixed-size",
        "  stream cipher.",
        "- If we can infer the mode `0x80` grammar from records with known code",
        "  output, the stable response bridge becomes a possible CDD-side patch",
        "  target rather than waiting for a separate normal-mode RAM write",
        "  primitive.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--f0",
        type=Path,
        default=Path("references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"),
    )
    parser.add_argument(
        "--record-map",
        type=Path,
        default=Path("references/firmware/extracted/liteon-cdd-record-map.json"),
    )
    parser.add_argument(
        "--hidden-chunks",
        type=Path,
        default=Path("analysis/8051/normal-hidden-runtime-chunks-20260501.json"),
    )
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))


if __name__ == "__main__":
    main()
