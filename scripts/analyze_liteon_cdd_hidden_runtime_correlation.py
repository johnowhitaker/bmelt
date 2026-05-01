#!/usr/bin/env python3
"""Correlate normal hidden-runtime tiles with the LD5M CDD record map.

The normal READ BUFFER work-window exposes code-like 0x40-byte tiles that do
not all appear in visible F0/currentboot/helper artifacts. This script asks a
narrow question: which hidden tiles are stable enough to be plausible fixed
decoded-output candidates, and which CDD records would they correspond to if
their public offset is meaningful?

It is offline-only and never opens an optical drive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_liteon_cdd_streams as cdd  # noqa: E402
import analyze_liteon_normal_hidden_runtime_chunks as normal_chunks  # noqa: E402


DEFAULT_OUT_JSON = ROOT / "analysis/8051/cdd-hidden-runtime-correlation-20260501.json"
DEFAULT_OUT_MD = ROOT / "analysis/8051/cdd-hidden-runtime-correlation-20260501.md"
DEFAULT_RECORD_MAP = ROOT / "references/firmware/extracted/liteon-cdd-record-map.json"
DEFAULT_LD5M = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_RUN_GLOB = "references/evidence/live/normal-work-window-*20260501"


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def load_ld5m_record_map(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    for image in data.get("images", []):
        if image.get("image") == "LD5M":
            return image["records"]
    return []


def record_for_offset(records: list[dict[str, Any]], offset: int) -> dict[str, Any] | None:
    for record in records:
        start = int(record["decoded_start"])
        end = start + int(record["decoded_span"])
        if start <= offset < end:
            return record
    return None


def find_all(data: bytes, needle: bytes) -> list[int]:
    hits = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return hits
        hits.append(offset)
        start = offset + 1


def seed_hit_count(source: bytes, output: bytes, width: int) -> int:
    if len(output) < width:
        return 0
    seen = {output[offset : offset + width] for offset in range(0, len(output) - width + 1)}
    return sum(1 for seed in seen if seed in source)


def best_xor_seed_hits(source: bytes, output: bytes, width: int = 4) -> dict[str, Any]:
    """Find the XOR byte that maximizes fixed-XOR seed hits in source."""
    if len(output) < width:
        return {"xor": None, "hits": 0}
    best = (0, 0)
    for xor_value in range(256):
        transformed = bytes(byte ^ xor_value for byte in output)
        hits = seed_hit_count(source, transformed, width)
        if hits > best[1]:
            best = (xor_value, hits)
    return {"xor": f"0x{best[0]:02x}", "hits": best[1]}


def source_segment_for_record(image: cdd.CddImage, record_index: int) -> bytes:
    for index, start, end, _ in cdd.source_segments(image):
        if index == record_index:
            return image.data[start:end]
    return b""


def compact_offsets(offsets: list[dict[str, Any]], limit: int = 4) -> str:
    return ", ".join(f"{item['value']} x{item['count']}" for item in offsets[:limit])


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    run_dirs = [path for path in sorted(ROOT.glob(args.run_glob)) if path.is_dir()]
    paths = normal_chunks.collect_capture_paths(run_dirs)
    refs = normal_chunks.load_references()
    records = load_ld5m_record_map(args.record_map)
    chunk_items = normal_chunks.collect_chunks(paths)
    ld5m = cdd.load_image(args.ld5m)
    if ld5m is None:
        raise SystemExit(f"could not load LD5M CDD image: {args.ld5m}")

    rows = []
    rotating = []
    for item in chunk_items.values():
        row = normal_chunks.classify_chunk(item, refs, records)
        exact_refs = set(row["exact_refs"].keys())
        top_offset_item = row["offsets"][0]
        top_offset = int(top_offset_item["value"], 16)
        top_count = int(top_offset_item["count"])
        stability = top_count / int(row["observations"])
        hidden = not exact_refs
        if hidden and row["observations"] >= args.min_observations and stability < args.stable_threshold:
            rotating.append(
                {
                    "chunk": row["short"],
                    "observations": row["observations"],
                    "stability": round(stability, 4),
                    "offsets": row["offsets"][:6],
                    "patterns": list(row["patterns"].keys()),
                    "interesting_categories": row["interesting_categories"],
                }
            )
            continue
        if not (hidden and row["observations"] >= args.min_observations and stability >= args.stable_threshold):
            continue

        record = record_for_offset(records, top_offset)
        if record is None:
            continue
        source = source_segment_for_record(ld5m, int(record["index"]))
        output = bytes.fromhex(row["hex"])
        raw_4 = seed_hit_count(source, output, 4)
        raw_8 = seed_hit_count(source, output, 8)
        raw_16 = seed_hit_count(source, output, 16)
        xor4 = best_xor_seed_hits(source, output, 4)
        rows.append(
            {
                "chunk": row["short"],
                "sha256": row["sha256"],
                "observations": row["observations"],
                "top_offset": f"0x{top_offset:04x}",
                "stability": round(stability, 4),
                "offsets": row["offsets"][:6],
                "patterns": list(row["patterns"].keys()),
                "interesting_categories": row["interesting_categories"],
                "record": {
                    "index": record["index"],
                    "decoded_start": f"0x{int(record['decoded_start']):05x}",
                    "decoded_span": f"0x{int(record['decoded_span']):x}",
                    "mode": f"0x{int(record['mode']):02x}",
                    "operation_key": record["operation_key"],
                    "source_start": f"0x{int(record['source_start']):x}",
                    "source_len": f"0x{int(record['source_len']):x}",
                    "source_entropy": round(entropy(source), 4),
                },
                "source_output_seed_hits": {
                    "raw_width4": raw_4,
                    "raw_width8": raw_8,
                    "raw_width16": raw_16,
                    "best_fixed_xor_width4": xor4,
                },
                "hex": row["hex"],
            }
        )

    rows.sort(key=lambda row: (row["source_output_seed_hits"]["raw_width8"], row["observations"]), reverse=True)
    rotating.sort(key=lambda row: row["observations"], reverse=True)
    return {
        "captures": len(paths),
        "min_observations": args.min_observations,
        "stable_threshold": args.stable_threshold,
        "stable_hidden_candidates": rows,
        "rotating_hidden_examples": rotating[:40],
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def write_md(path: Path, report: dict[str, Any]) -> None:
    candidate_rows = []
    for row in report["stable_hidden_candidates"][:40]:
        record = row["record"]
        hits = row["source_output_seed_hits"]
        candidate_rows.append(
            [
                f"`{row['chunk']}`",
                str(row["observations"]),
                f"`{row['top_offset']}`",
                str(row["stability"]),
                f"`{record['index']}`",
                f"`{record['mode']}`",
                f"`{record['operation_key']}`",
                f"`{record['source_len']}`",
                str(hits["raw_width4"]),
                str(hits["raw_width8"]),
                f"{hits['best_fixed_xor_width4']['xor']}:{hits['best_fixed_xor_width4']['hits']}",
            ]
        )
    rotating_rows = [
        [
            f"`{row['chunk']}`",
            str(row["observations"]),
            str(row["stability"]),
            compact_offsets(row["offsets"]),
            ", ".join(row["patterns"]) or "-",
            ", ".join(row["interesting_categories"].keys()) or "-",
        ]
        for row in report["rotating_hidden_examples"][:20]
    ]
    lines = [
        "# CDD / Hidden Runtime Correlation",
        "",
        "Offline only. No drive commands were sent.",
        "",
        "This treats stable normal hidden-runtime chunks as possible known-output "
        "candidates for CDD hard-mode records. It is intentionally conservative: "
        "rotating chunks are listed separately because their public offset is not "
        "a trustworthy decoded address.",
        "",
        "## Summary",
        "",
        f"- captures scanned: `{report['captures']}`",
        f"- stable hidden candidates: `{len(report['stable_hidden_candidates'])}`",
        f"- rotating hidden examples retained: `{len(report['rotating_hidden_examples'])}`",
        "",
        "## Stable Hidden Candidates",
        "",
        markdown_table(
            [
                "chunk",
                "obs",
                "offset",
                "stability",
                "CDD rec",
                "mode",
                "op key",
                "source len",
                "raw 4B hits",
                "raw 8B hits",
                "best xor4",
            ],
            candidate_rows,
        ),
        "",
        "The seed-hit columns are a cheap sanity check for trivial transforms. "
        "A strong decoded-output pair would often leave exact or fixed-XOR byte "
        "seeds in the source. The current candidates do not show that kind of "
        "simple relationship.",
        "",
        "## Rotating Hidden Examples",
        "",
        markdown_table(
            ["chunk", "obs", "stability", "offsets", "patterns", "categories"],
            rotating_rows,
        ),
        "",
        "## Interpretation",
        "",
        "- Several hidden normal-runtime chunks are stable enough to be good code "
        "study targets, but their CDD mapping remains only a hypothesis.",
        "- The stable candidates mostly land on mode `0x40`/`0x80` records with "
        "high-entropy sources, exactly the hard CDD classes already suspected.",
        "- The raw/fixed-XOR seed checks are negative, so these are not cheap "
        "direct unpacking pairs.",
        "- Rotating hidden chunks such as the public response bridge are real "
        "runtime code, but their public slot movement makes them poor direct "
        "CDD known-output pairs until we learn the missing phase/address model.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-glob", default=DEFAULT_RUN_GLOB)
    parser.add_argument("--record-map", type=Path, default=DEFAULT_RECORD_MAP)
    parser.add_argument("--ld5m", type=Path, default=DEFAULT_LD5M)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--min-observations", type=int, default=250)
    parser.add_argument("--stable-threshold", type=float, default=0.95)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    write_json(args.out_json, report)
    write_md(args.out_md, report)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
