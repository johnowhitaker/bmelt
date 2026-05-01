#!/usr/bin/env python3
"""Rank CDD/runtime chunks and records as normal-mode I/O foothold targets."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PACKET_SHADOW_RANGE = range(0x8A49, 0x8A55)
CONTROLLER_RANGES = (
    range(0x4000, 0x40C0),
    range(0x47B0, 0x47D8),
)
HIGH_VALUE_DPTRS = {
    0x47B1,
    0x4000,
    0x4011,
    0x4012,
    0x4013,
    0x4091,
    0x4092,
    0x4093,
    0x4098,
    0x4099,
    0x409C,
}


def parse_hex_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def score_chunk(chunk: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []

    observations = int(chunk.get("observations", 0))
    if observations:
        score += min(8.0, math.log2(observations + 1))
        reasons.append(f"seen {observations}x")

    categories = chunk.get("interesting_categories", {})
    for name, count in sorted(categories.items()):
        weight = {
            "packet_shadow": 8.0,
            "controller_status": 7.0,
            "front_panel_or_status": 3.0,
        }.get(name, 2.0)
        score += weight * min(int(count), 4)
        reasons.append(f"{name} refs x{count}")

    direct_copies = chunk.get("direct_copies", [])
    if direct_copies:
        score += 4.0 * len(direct_copies)
        copied = []
        for item in direct_copies[:3]:
            copied.append(f"{item.get('src')}->{item.get('dst')}")
        reasons.append("copies " + ", ".join(copied))

    patterns = chunk.get("patterns", {})
    for name in patterns:
        lower = name.lower()
        if "bridge" in lower or "getcfg" in lower:
            score += 9.0
            reasons.append(f"pattern {name}")
        elif "packet" in lower or "shadow" in lower:
            score += 5.0
            reasons.append(f"pattern {name}")

    dptr_refs = chunk.get("dptr_refs", [])
    dptr_hits: list[str] = []
    for ref in dptr_refs:
        value = parse_hex_int(ref.get("value"))
        count = int(ref.get("count", 1))
        if value is None:
            continue
        if value in PACKET_SHADOW_RANGE:
            score += 4.0 * count
            dptr_hits.append(f"{value:#06x}")
        elif value in HIGH_VALUE_DPTRS or any(value in r for r in CONTROLLER_RANGES):
            score += 3.0 * count
            dptr_hits.append(f"{value:#06x}")
    if dptr_hits:
        reasons.append("dptr " + ", ".join(dptr_hits[:8]))

    run_names = [item.get("value", "") for item in chunk.get("runs", [])]
    if any("get-config" in name for name in run_names):
        score += 5.0
        reasons.append("appears in GET CONFIG runs")
    if any("get-performance" in name for name in run_names):
        score += 3.0
        reasons.append("appears in GET PERFORMANCE runs")

    candidates = chunk.get("cdd_public_offset_candidates", [])
    if candidates:
        score += 2.0
        records = sorted(
            {
                cand.get("record")
                for cand in candidates
                if cand.get("record") is not None
            }
        )
        if records:
            reasons.append("CDD candidates " + ", ".join(str(r) for r in records[:6]))

    return score, reasons


def load_hidden_chunks(path: Path) -> list[dict[str, Any]]:
    report = json.loads(path.read_text())
    return report["top_hidden_runtime_chunks"]


def build_pair_index(path: Path) -> dict[str, list[dict[str, Any]]]:
    report = json.loads(path.read_text())
    by_chunk: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in report["pairs"]:
        by_chunk[pair["chunk_sha256"]].append(pair)
    return by_chunk


def build_record_scores(
    chunks: list[dict[str, Any]],
    chunk_scores: dict[str, tuple[float, list[str]]],
    pair_index: dict[str, list[dict[str, Any]]],
) -> dict[int, dict[str, Any]]:
    records: dict[int, dict[str, Any]] = {}

    def entry(record: int) -> dict[str, Any]:
        return records.setdefault(
            record,
            {
                "record": record,
                "score": 0.0,
                "chunks": Counter(),
                "reasons": Counter(),
                "pair_count": 0,
                "source_lens": Counter(),
                "operation_keys": Counter(),
            },
        )

    for chunk in chunks:
        digest = chunk["sha256"]
        score, reasons = chunk_scores[digest]
        for cand in chunk.get("cdd_public_offset_candidates", []):
            record = cand.get("record")
            if record is None:
                continue
            rec = entry(int(record))
            rec["score"] += score * min(float(cand.get("count", 1)), 64.0) / 64.0
            rec["chunks"][chunk["short"]] += int(cand.get("count", 1))
            for reason in reasons[:6]:
                rec["reasons"][reason] += 1
            if cand.get("operation_key"):
                rec["operation_keys"][cand["operation_key"]] += 1

        for pair in pair_index.get(digest, []):
            rec = entry(int(pair["record"]))
            rec["score"] += score * 0.20
            rec["pair_count"] += 1
            rec["source_lens"][int(pair["record_source_len"])] += 1
            rec["operation_keys"][pair["record_operation_key"]] += 1

    result: dict[int, dict[str, Any]] = {}
    for record, rec in records.items():
        result[record] = {
            "record": record,
            "score": round(rec["score"], 3),
            "top_chunks": [
                {"chunk": chunk, "count": count}
                for chunk, count in rec["chunks"].most_common(6)
            ],
            "top_reasons": [
                {"reason": reason, "count": count}
                for reason, count in rec["reasons"].most_common(8)
            ],
            "pair_count": rec["pair_count"],
            "source_lens": [
                {"length": length, "count": count}
                for length, count in rec["source_lens"].most_common(4)
            ],
            "operation_keys": [
                {"key": key, "count": count}
                for key, count in rec["operation_keys"].most_common(4)
            ],
        }
    return result


def score_contigs(
    path: Path,
    chunk_scores: dict[str, tuple[float, list[str]]],
    record_scores: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    report = json.loads(path.read_text())
    results = []
    for contig in report["contigs"]:
        score = 0.0
        reasons: list[str] = []
        for digest in contig["chunks"]:
            chunk_score, chunk_reasons = chunk_scores.get(digest, (0.0, []))
            score += chunk_score
            for reason in chunk_reasons[:2]:
                if reason not in reasons:
                    reasons.append(reason)
        for record in contig.get("common_records", []):
            score += record_scores.get(int(record), {}).get("score", 0.0) * 0.15
        if contig.get("common_records"):
            score += 8.0
            reasons.append("has common CDD record owner")
        if len(contig.get("union_records", [])) <= 2:
            score += 3.0
            reasons.append("narrow record union")
        results.append(
            {
                "index": contig["index"],
                "score": round(score, 3),
                "chunk_count": contig["chunk_count"],
                "file": contig["file"],
                "chunk_shorts": contig["chunk_shorts"],
                "common_records": contig.get("common_records", []),
                "union_records": contig.get("union_records", []),
                "hex_prefix": contig.get("hex_prefix", ""),
                "reasons": reasons[:10],
            }
        )
    return sorted(results, key=lambda item: item["score"], reverse=True)


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Normal I/O CDD Target Ranking",
        "",
        "This is a prioritization pass for the next live perturbation. It ranks",
        "normal-runtime work-window chunks and their candidate CDD records by how",
        "closely they touch packet-shadow, controller-register, and response-bridge",
        "patterns.",
        "",
        "The score is heuristic. It is meant to choose better live targets, not to",
        "prove ownership by itself.",
        "",
        "## Top Runtime Chunks",
        "",
        "| rank | score | chunk | observations | CDD candidates | reasons |",
        "|---:|---:|---|---:|---|---|",
    ]
    for rank, item in enumerate(report["top_chunks"][:20], 1):
        candidates = ", ".join(
            f"r{cand['record']}@{cand['public_offset']}"
            for cand in item["cdd_candidates"][:4]
        )
        reasons = "; ".join(item["reasons"][:4])
        lines.append(
            f"| {rank} | {item['score']:.1f} | `{item['short']}` | "
            f"{item['observations']} | {candidates or '-'} | {reasons} |"
        )

    lines.extend(
        [
            "",
            "## Top Candidate CDD Records",
            "",
            "| rank | score | record | chunks | pair count | operation keys | reasons |",
            "|---:|---:|---:|---|---:|---|---|",
        ]
    )
    for rank, item in enumerate(report["top_records"][:20], 1):
        chunks = ", ".join(f"`{c['chunk']}` x{c['count']}" for c in item["top_chunks"][:3])
        keys = ", ".join(f"`{k['key']}` x{k['count']}" for k in item["operation_keys"][:2])
        reasons = "; ".join(r["reason"] for r in item["top_reasons"][:4])
        lines.append(
            f"| {rank} | {item['score']:.1f} | {item['record']} | "
            f"{chunks or '-'} | {item['pair_count']} | {keys or '-'} | {reasons} |"
        )

    lines.extend(
        [
            "",
            "## Top Contigs",
            "",
            "| rank | score | contig | records | chunks | reasons |",
            "|---:|---:|---:|---|---|---|",
        ]
    )
    for rank, item in enumerate(report["top_contigs"][:20], 1):
        records = (
            "common "
            + ",".join(str(r) for r in item["common_records"])
            + " / union "
            + ",".join(str(r) for r in item["union_records"])
        )
        chunks = ", ".join(f"`{short}`" for short in item["chunk_shorts"][:5])
        reasons = "; ".join(item["reasons"][:4])
        lines.append(
            f"| {rank} | {item['score']:.1f} | {item['index']} | "
            f"{records} | {chunks} | {reasons} |"
        )

    lines.extend(
        [
            "",
            "## Practical Read",
            "",
            "- Records `58` and `59` remain the highest-value bridge records because",
            "  they own chunks with direct `0x8a4c..0x8a4e -> 0x4011..0x4013` and",
            "  `0x4099 -> 0x8a4e/0x8a53/0x8a54` patterns.",
            "- Record `59` already has a strong reversible ownership result from the",
            "  contig-4 live test, so it is the best known perturbation detector.",
            "- Records `84/85` are packet-intake candidates around the `0x47b1 ->",
            "  0x8a4c..0x8a53` CDB shadow copy. They are attractive if the next goal",
            "  is to disturb command parsing rather than response setup.",
            "- The clever shortcut to test next is currentboot-to-normal carryover:",
            "  plant markers in these packet/bridge XDATA locations through the",
            "  currentboot write hook, recover to normal without a hard power cut,",
            "  then capture the same ranked work-window offsets.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--hidden-chunks",
        type=Path,
        default=Path("analysis/8051/normal-hidden-runtime-chunks-with-readonly-harvests-20260501.json"),
    )
    parser.add_argument(
        "--pairs",
        type=Path,
        default=Path("analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.json"),
    )
    parser.add_argument(
        "--contigs",
        type=Path,
        default=Path("analysis/8051/cdd-runtime-chunk-contigs-20260501.json"),
    )
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    chunks = load_hidden_chunks(args.hidden_chunks)
    chunk_scores = {
        chunk["sha256"]: score_chunk(chunk)
        for chunk in chunks
    }
    pair_index = build_pair_index(args.pairs)
    record_scores = build_record_scores(chunks, chunk_scores, pair_index)
    top_contigs = score_contigs(args.contigs, chunk_scores, record_scores)

    top_chunks = []
    for chunk in chunks:
        score, reasons = chunk_scores[chunk["sha256"]]
        top_chunks.append(
            {
                "score": round(score, 3),
                "short": chunk["short"],
                "sha256": chunk["sha256"],
                "observations": chunk.get("observations", 0),
                "offsets": chunk.get("offsets", []),
                "reasons": reasons,
                "patterns": chunk.get("patterns", {}),
                "dptr_refs": chunk.get("dptr_refs", []),
                "direct_copies": chunk.get("direct_copies", []),
                "cdd_candidates": chunk.get("cdd_public_offset_candidates", []),
                "hex": chunk.get("hex", ""),
            }
        )
    top_chunks.sort(key=lambda item: item["score"], reverse=True)

    top_records = sorted(
        record_scores.values(),
        key=lambda item: item["score"],
        reverse=True,
    )
    report = {
        "schema": "liteon-normal-io-cdd-target-ranking-v1",
        "inputs": {
            "hidden_chunks": str(args.hidden_chunks),
            "pairs": str(args.pairs),
            "contigs": str(args.contigs),
        },
        "top_chunks": top_chunks,
        "top_records": top_records,
        "top_contigs": top_contigs,
    }
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True))
    write_markdown(args.out_md, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
