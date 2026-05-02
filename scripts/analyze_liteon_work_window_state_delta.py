#!/usr/bin/env python3
"""Compare normal work-window tile/edge populations across capture states.

The normal READ BUFFER work window is a rotating tile surface, so a useful
mutation can change where decoded-runtime tiles appear without changing the
tile bytes themselves. This script compares two or more capture directories at
the 0x40-byte tile and adjacent-edge level, then annotates chunks with the
candidate CDD records already present in the known-output corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PAIRS = ROOT / "analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.json"
DEFAULT_CONTIGS = ROOT / "analysis/8051/cdd-runtime-chunk-contigs-20260501.json"


def parse_state(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("state must be LABEL=PATH")
    label, raw_path = value.split("=", 1)
    if not label:
        raise argparse.ArgumentTypeError("state label cannot be empty")
    return label, Path(raw_path)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def short_digest(digest: str) -> str:
    return digest[:12]


def is_informative(chunk: bytes) -> bool:
    return len(set(chunk)) > 1


def stimulus_name(path: Path) -> str:
    stem = path.name.removesuffix(".window.bin")
    parts = stem.split("-", 2)
    if len(parts) == 3 and parts[1].startswith("cycle"):
        return parts[2]
    return stem


def collect_state(path: Path, chunk_size: int) -> dict[str, Any]:
    files = sorted(path.glob("*.window.bin"))
    if not files:
        raise SystemExit(f"no *.window.bin files in {path}")

    chunks: Counter[str] = Counter()
    chunk_offsets: dict[str, Counter[int]] = defaultdict(Counter)
    chunk_stimuli: dict[str, Counter[str]] = defaultdict(Counter)
    edges: Counter[tuple[str, str]] = Counter()
    edge_offsets: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)
    edge_stimuli: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)

    for file_path in files:
        data = file_path.read_bytes()
        stimulus = stimulus_name(file_path)
        digests: list[str | None] = []
        for offset in range(0, len(data) - chunk_size + 1, chunk_size):
            chunk = data[offset : offset + chunk_size]
            if not is_informative(chunk):
                digests.append(None)
                continue
            digest = sha256_hex(chunk)
            digests.append(digest)
            chunks[digest] += 1
            chunk_offsets[digest][offset] += 1
            chunk_stimuli[digest][stimulus] += 1
        for index in range(len(digests) - 1):
            left = digests[index]
            right = digests[index + 1]
            if left is None or right is None:
                continue
            edge = (left, right)
            edges[edge] += 1
            edge_offsets[edge][index * chunk_size] += 1
            edge_stimuli[edge][stimulus] += 1

    return {
        "path": str(path),
        "files": len(files),
        "chunks": chunks,
        "chunk_offsets": chunk_offsets,
        "chunk_stimuli": chunk_stimuli,
        "edges": edges,
        "edge_offsets": edge_offsets,
        "edge_stimuli": edge_stimuli,
    }


def build_chunk_record_index(pair_path: Path, contig_path: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = defaultdict(lambda: {"records": Counter(), "contigs": set()})
    if pair_path.exists():
        pairs = json.loads(pair_path.read_text())
        for pair in pairs.get("pairs", []):
            digest = pair["chunk_sha256"]
            record = int(pair["record"])
            index[digest]["records"][record] += 1
    if contig_path.exists():
        contigs = json.loads(contig_path.read_text())
        for contig in contigs.get("contigs", []):
            for digest in contig.get("chunks", []):
                index[digest]["contigs"].add(int(contig["index"]))
                for record in contig.get("common_records", []):
                    index[digest]["records"][int(record)] += 4
                for record in contig.get("union_records", []):
                    index[digest]["records"][int(record)] += 1
    return index


def top_counter_items(counter: Counter[Any], limit: int = 6) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def annotate_chunk(digest: str, chunk_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item = chunk_index.get(digest, {"records": Counter(), "contigs": set()})
    return {
        "sha256": digest,
        "short": short_digest(digest),
        "records": [
            {"record": record, "count": count}
            for record, count in item["records"].most_common(6)
        ],
        "contigs": sorted(item["contigs"]),
    }


def edge_key_text(edge: tuple[str, str]) -> str:
    return f"{short_digest(edge[0])}->{short_digest(edge[1])}"


def edge_records(edge: tuple[str, str], chunk_index: dict[str, dict[str, Any]]) -> list[dict[str, int]]:
    counts: Counter[int] = Counter()
    for digest in edge:
        item = chunk_index.get(digest)
        if not item:
            continue
        counts.update(item["records"])
    return [{"record": record, "count": count} for record, count in counts.most_common(6)]


def enrichment_rows(
    *,
    states: dict[str, dict[str, Any]],
    labels: list[str],
    key: str,
    offset_key: str,
    stimuli_key: str,
    chunk_index: dict[str, dict[str, Any]],
    min_count: int,
    limit: int,
) -> list[dict[str, Any]]:
    baseline_label = labels[0]
    baseline = states[baseline_label][key]
    rows: list[dict[str, Any]] = []
    all_items = set(baseline)
    for label in labels[1:]:
        all_items.update(states[label][key])

    for item in all_items:
        counts = {label: int(states[label][key].get(item, 0)) for label in labels}
        rates = {
            label: (counts[label] / states[label]["files"]) if states[label]["files"] else 0.0
            for label in labels
        }
        max_count = max(counts.values())
        if max_count < min_count:
            continue
        baseline_rate = rates[baseline_label]
        best_label = max(labels[1:], key=lambda label: rates[label] - baseline_rate)
        delta_rate = rates[best_label] - baseline_rate
        if abs(delta_rate) < 1e-9:
            continue
        if isinstance(item, tuple):
            annotated = {
                "edge": edge_key_text(item),
                "left": annotate_chunk(item[0], chunk_index),
                "right": annotate_chunk(item[1], chunk_index),
                "records": edge_records(item, chunk_index),
            }
        else:
            annotated = annotate_chunk(item, chunk_index)
        rows.append(
            {
                "item": annotated,
                "counts": counts,
                "rates": {label: round(rate, 6) for label, rate in rates.items()},
                "best_delta_rate_vs_baseline": round(delta_rate, 6),
                "best_delta_count_vs_baseline": counts[best_label] - counts[baseline_label],
                "best_state": best_label,
                "offsets": {
                    label: top_counter_items(states[label][offset_key].get(item, Counter()), 5)
                    for label in labels
                },
                "stimuli": {
                    label: top_counter_items(states[label][stimuli_key].get(item, Counter()), 5)
                    for label in labels
                },
            }
        )
    rows.sort(
        key=lambda row: (
            -abs(row["best_delta_rate_vs_baseline"]),
            -max(row["counts"].values()),
        )
    )
    return rows[:limit]


def fmt_count_map(counts: dict[str, int]) -> str:
    return ", ".join(f"`{label}` {count}" for label, count in counts.items())


def fmt_rate_map(rates: dict[str, float]) -> str:
    return ", ".join(f"`{label}` {rate:.3f}" for label, rate in rates.items())


def fmt_records(records: list[dict[str, int]]) -> str:
    if not records:
        return "-"
    return ", ".join(f"`{row['record']}`" for row in records[:4])


def fmt_offsets(rows: list[dict[str, int]]) -> str:
    if not rows:
        return "-"
    return ", ".join(f"`+0x{int(row['value']):04x}` x{row['count']}" for row in rows[:4])


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window State Delta",
        "",
        f"Chunk size: `{report['chunk_size']:#x}`",
        "",
        "## States",
        "",
        "| state | path | captures | unique chunks | unique edges |",
        "|---|---|---:|---:|---:|",
    ]
    for label, state in report["states"].items():
        lines.append(
            f"| `{label}` | `{state['path']}` | {state['files']} | "
            f"{state['unique_chunks']} | {state['unique_edges']} |"
        )

    lines.extend(["", "## Enriched Chunks", ""])
    lines.append("| chunk | records | rates per capture | counts | best rate delta | offsets in best state |")
    lines.append("|---|---|---|---|---:|---|")
    for row in report["enriched_chunks"]:
        item = row["item"]
        best = row["best_state"]
        lines.append(
            f"| `{item['short']}` | {fmt_records(item['records'])} | "
            f"{fmt_rate_map(row['rates'])} | {fmt_count_map(row['counts'])} | "
            f"{row['best_delta_rate_vs_baseline']:.3f} | "
            f"{fmt_offsets(row['offsets'][best])} |"
        )

    lines.extend(["", "## Enriched Edges", ""])
    lines.append("| edge | records | rates per capture | counts | best rate delta | offsets in best state |")
    lines.append("|---|---|---|---|---:|---|")
    for row in report["enriched_edges"]:
        item = row["item"]
        best = row["best_state"]
        lines.append(
            f"| `{item['edge']}` | {fmt_records(item['records'])} | "
            f"{fmt_rate_map(row['rates'])} | {fmt_count_map(row['counts'])} | "
            f"{row['best_delta_rate_vs_baseline']:.3f} | "
            f"{fmt_offsets(row['offsets'][best])} |"
        )
    lines.append("")
    return "\n".join(lines)


def freeze_counter(counter: Counter[Any]) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common()]


def make_jsonable(value: Any) -> Any:
    if isinstance(value, Counter):
        return freeze_counter(value)
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, tuple):
        return [make_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): make_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_jsonable(item) for item in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", action="append", type=parse_state, required=True)
    parser.add_argument("--chunk-size", type=lambda value: int(value, 0), default=0x40)
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--contigs", type=Path, default=DEFAULT_CONTIGS)
    parser.add_argument("--min-count", type=int, default=8)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    labels = [label for label, _path in args.state]
    if len(labels) != len(set(labels)):
        raise SystemExit("state labels must be unique")
    if len(labels) < 2:
        raise SystemExit("at least two --state entries are required")

    states = {label: collect_state(path, args.chunk_size) for label, path in args.state}
    chunk_index = build_chunk_record_index(args.pairs, args.contigs)
    report: dict[str, Any] = {
        "schema": "liteon-work-window-state-delta-v1",
        "chunk_size": args.chunk_size,
        "baseline_state": labels[0],
        "states": {
            label: {
                "path": state["path"],
                "files": state["files"],
                "unique_chunks": len(state["chunks"]),
                "unique_edges": len(state["edges"]),
            }
            for label, state in states.items()
        },
        "enriched_chunks": enrichment_rows(
            states=states,
            labels=labels,
            key="chunks",
            offset_key="chunk_offsets",
            stimuli_key="chunk_stimuli",
            chunk_index=chunk_index,
            min_count=args.min_count,
            limit=args.limit,
        ),
        "enriched_edges": enrichment_rows(
            states=states,
            labels=labels,
            key="edges",
            offset_key="edge_offsets",
            stimuli_key="edge_stimuli",
            chunk_index=chunk_index,
            min_count=args.min_count,
            limit=args.limit,
        ),
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(make_jsonable(report), indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
