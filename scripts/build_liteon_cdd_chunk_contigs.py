#!/usr/bin/env python3
"""Build high-confidence contigs from normal work-window chunk adjacency.

This treats 0x40-byte normal READ BUFFER work-window chunks as graph nodes.
Edges are observed host-visible adjacency in raw captures.  The resulting
contigs are decoded-runtime tile neighborhoods; they are not byte-addressed CDD
records until later mapped by record buckets or live perturbations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 0x40
DEFAULT_PAIRS = ROOT / "analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.json"
DEFAULT_HIDDEN = ROOT / "analysis/8051/normal-hidden-runtime-chunks-with-readonly-harvests-20260501.json"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_counter(counter: Counter[Any], limit: int = 8) -> list[dict[str, Any]]:
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def load_chunk_meta(pairs_path: Path) -> dict[str, dict[str, Any]]:
    pairs = json.loads(pairs_path.read_text())["pairs"]
    chunks: dict[str, dict[str, Any]] = {}
    for pair in pairs:
        digest = pair["chunk_sha256"]
        row = chunks.setdefault(
            digest,
            {
                "sha256": digest,
                "short": pair["chunk_short"],
                "bytes": bytes.fromhex(pair["decoded_hex"]),
                "records": set(),
                "public_offsets": Counter(),
                "decoded_relatives": Counter(),
            },
        )
        row["records"].add(int(pair["record"]))
        row["public_offsets"][int(pair["public_offset"])] += 1
        row["decoded_relatives"][(int(pair["record"]), int(pair["decoded_relative"]))] += 1
    return chunks


def collect_capture_paths(hidden_chunks: Path, run_glob: str = "") -> list[Path]:
    report = json.loads(hidden_chunks.read_text())
    run_dirs = [ROOT / path for path in report.get("run_dirs", [])]
    if run_glob:
        run_dirs.extend(path for path in sorted(ROOT.glob(run_glob)) if path.is_dir())

    unique_dirs: list[Path] = []
    seen: set[Path] = set()
    for run_dir in run_dirs:
        resolved = run_dir.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_dirs.append(run_dir)

    paths: list[Path] = []
    for run_dir in unique_dirs:
        paths.extend(sorted(run_dir.glob("*.window.bin")))
    return paths


def add_edge(edges: dict[tuple[str, str], dict[str, Any]], src: str, dst: str, path: Path, offset: int) -> None:
    row = edges.setdefault(
        (src, dst),
        {
            "src": src,
            "dst": dst,
            "count": 0,
            "runs": Counter(),
            "offsets": Counter(),
            "examples": [],
        },
    )
    row["count"] += 1
    row["runs"][path.parent.name] += 1
    row["offsets"][offset] += 1
    if len(row["examples"]) < 6:
        row["examples"].append(
            {
                "run": path.parent.name,
                "capture": path.name,
                "public_offset": offset,
            }
        )


def scan_edges(paths: list[Path], known_chunks: set[str]) -> dict[tuple[str, str], dict[str, Any]]:
    edges: dict[tuple[str, str], dict[str, Any]] = {}
    for path in paths:
        data = path.read_bytes()
        digests = [
            sha256_hex(data[offset : offset + CHUNK_SIZE])
            for offset in range(0, len(data) - CHUNK_SIZE + 1, CHUNK_SIZE)
        ]
        for index, (src, dst) in enumerate(zip(digests, digests[1:])):
            if src in known_chunks and dst in known_chunks:
                add_edge(edges, src, dst, path, index * CHUNK_SIZE)
    return edges


def dominant_edges(
    edges: dict[tuple[str, str], dict[str, Any]], min_count: int, dominance_ratio: float
) -> dict[str, str]:
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in edges.values():
        if row["src"] == row["dst"] or row["count"] < min_count:
            continue
        outgoing[row["src"]].append(row)
        incoming[row["dst"]].append(row)

    def best(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
        rows = sorted(rows, key=lambda item: -item["count"])
        if not rows:
            return None
        if len(rows) == 1:
            return rows[0]
        if rows[0]["count"] >= rows[1]["count"] * dominance_ratio:
            return rows[0]
        return None

    best_out = {node: row for node, rows in outgoing.items() if (row := best(rows))}
    best_in = {node: row for node, rows in incoming.items() if (row := best(rows))}

    kept: dict[str, str] = {}
    for src, row in best_out.items():
        dst = row["dst"]
        if best_in.get(dst, {}).get("src") == src:
            kept[src] = dst
    return kept


def build_contigs(kept_edges: dict[str, str], chunks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    incoming = {dst: src for src, dst in kept_edges.items()}
    starts = sorted(node for node in kept_edges if node not in incoming)
    used: set[str] = set()
    paths: list[list[str]] = []

    for start in starts:
        cur = start
        path: list[str] = []
        seen_local: set[str] = set()
        while cur and cur not in seen_local and cur not in used:
            path.append(cur)
            seen_local.add(cur)
            cur = kept_edges.get(cur, "")
        if len(path) >= 2:
            paths.append(path)
            used.update(path)

    # Capture simple cycles not reachable from a start.
    for node in sorted(kept_edges):
        if node in used:
            continue
        cur = node
        path = []
        seen_local = set()
        while cur and cur not in seen_local and cur not in used:
            path.append(cur)
            seen_local.add(cur)
            cur = kept_edges.get(cur, "")
        if len(path) >= 2:
            paths.append(path)
            used.update(path)

    contigs: list[dict[str, Any]] = []
    for index, path in enumerate(paths):
        record_sets = [set(chunks[digest]["records"]) for digest in path]
        common = set.intersection(*record_sets) if record_sets else set()
        union = set.union(*record_sets) if record_sets else set()
        contigs.append(
            {
                "index": index,
                "chunk_count": len(path),
                "byte_len": len(path) * CHUNK_SIZE,
                "chunks": path,
                "chunk_shorts": [chunks[digest]["short"] for digest in path],
                "common_records": sorted(common),
                "union_records": sorted(union),
                "hex_prefix": chunks[path[0]]["bytes"][:16].hex(),
            }
        )
    contigs.sort(key=lambda row: (-row["chunk_count"], row["chunk_shorts"]))
    for index, row in enumerate(contigs):
        row["index"] = index
    return contigs


def edge_summary(row: dict[str, Any], chunks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "src": row["src"],
        "src_short": chunks[row["src"]]["short"],
        "src_records": sorted(chunks[row["src"]]["records"]),
        "dst": row["dst"],
        "dst_short": chunks[row["dst"]]["short"],
        "dst_records": sorted(chunks[row["dst"]]["records"]),
        "count": row["count"],
        "offsets": compact_counter(row["offsets"]),
        "runs": compact_counter(row["runs"]),
        "examples": row["examples"],
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    chunks = load_chunk_meta(args.pairs)
    paths = collect_capture_paths(args.hidden_chunks, args.run_glob)
    edges = scan_edges(paths, set(chunks))
    kept = dominant_edges(edges, args.min_edge_count, args.dominance_ratio)
    contigs = build_contigs(kept, chunks)

    args.contig_dir.mkdir(parents=True, exist_ok=True)
    for row in contigs[: args.write_contigs]:
        data = b"".join(chunks[digest]["bytes"] for digest in row["chunks"])
        path = args.contig_dir / f"contig-{row['index']:03d}-{row['chunk_count']:02d}chunks.bin"
        path.write_bytes(data)
        row["file"] = str(path)

    self_loops = [row for (src, dst), row in edges.items() if src == dst]
    edge_rows = [row for row in edges.values() if row["src"] != row["dst"]]
    edge_rows.sort(key=lambda row: (-row["count"], row["src"], row["dst"]))
    kept_pairs = {(src, dst) for src, dst in kept.items()}
    kept_rows = [edges[pair] for pair in kept_pairs]
    kept_rows.sort(key=lambda row: (-row["count"], row["src"], row["dst"]))

    return {
        "schema": "liteon-cdd-chunk-contigs-v1",
        "pairs": str(args.pairs),
        "hidden_chunks": str(args.hidden_chunks),
        "captures_scanned": len(paths),
        "known_chunks": len(chunks),
        "edge_count": len(edges),
        "non_self_edge_count": len(edge_rows),
        "self_loop_count": len(self_loops),
        "min_edge_count": args.min_edge_count,
        "dominance_ratio": args.dominance_ratio,
        "dominant_edge_count": len(kept),
        "contig_count": len(contigs),
        "contig_dir": str(args.contig_dir),
        "contigs": contigs,
        "top_edges": [edge_summary(row, chunks) for row in edge_rows[: args.top_edges]],
        "dominant_edges": [edge_summary(row, chunks) for row in kept_rows[: args.top_edges]],
        "top_self_loops": [
            {
                "chunk": chunks[row["src"]]["short"],
                "sha256": row["src"],
                "records": sorted(chunks[row["src"]]["records"]),
                "count": row["count"],
                "offsets": compact_counter(row["offsets"]),
            }
            for row in sorted(self_loops, key=lambda item: -item["count"])[: args.top_edges]
        ],
    }


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# CDD Runtime Chunk Contigs",
        "",
        "Date: 2026-05-01",
        "",
        "Offline only. No drive commands were sent.",
        "",
        "This treats 0x40-byte normal work-window chunks as graph nodes and",
        "uses repeated host-visible adjacency to build local decoded-runtime",
        "contigs. These contigs are more trustworthy than the flat",
        "`record-XXX-known-output.bin` placement arrays, but they are still",
        "runtime tile neighborhoods rather than proven CDD decoded addresses.",
        "",
        "## Summary",
        "",
        f"- captures scanned: `{report['captures_scanned']}`",
        f"- known chunk nodes: `{report['known_chunks']}`",
        f"- directed edges: `{report['edge_count']}`",
        f"- non-self edges: `{report['non_self_edge_count']}`",
        f"- self-loop edges: `{report['self_loop_count']}`",
        f"- dominant edges kept: `{report['dominant_edge_count']}`",
        f"- contigs: `{report['contig_count']}`",
        "",
        "## Contigs",
        "",
        md_table(
            ["contig", "chunks", "bytes", "common records", "union records", "chunk path"],
            [
                [
                    str(row["index"]),
                    str(row["chunk_count"]),
                    str(row["byte_len"]),
                    ",".join(map(str, row["common_records"])) or "-",
                    ",".join(map(str, row["union_records"])) or "-",
                    " -> ".join(f"`{short}`" for short in row["chunk_shorts"][:8]),
                ]
                for row in report["contigs"][:32]
            ],
        ),
        "",
        "## Dominant Edges",
        "",
        md_table(
            ["src", "dst", "count", "src records", "dst records", "top offsets"],
            [
                [
                    f"`{row['src_short']}`",
                    f"`{row['dst_short']}`",
                    str(row["count"]),
                    ",".join(map(str, row["src_records"])),
                    ",".join(map(str, row["dst_records"])),
                    ", ".join(f"`0x{item['value']:04x}` x{item['count']}" for item in row["offsets"][:4]),
                ]
                for row in report["dominant_edges"][:24]
            ],
        ),
        "",
        "## Self-Loops",
        "",
        "Self-loops usually indicate the same public tile repeated in adjacent",
        "slots. They are useful evidence of repetition, but not useful contig",
        "extension edges.",
        "",
        md_table(
            ["chunk", "records", "count", "offsets"],
            [
                [
                    f"`{row['chunk']}`",
                    ",".join(map(str, row["records"])),
                    str(row["count"]),
                    ", ".join(f"`0x{item['value']:04x}` x{item['count']}" for item in row["offsets"][:4]),
                ]
                for row in report["top_self_loops"][:16]
            ],
        ),
        "",
        "## Practical Read",
        "",
        "- Use contigs as decoded-runtime byte runs for static inspection.",
        "- Use common/union record buckets only as candidate provenance.",
        "- If a contig matters, validate its CDD ownership with a live",
        "  perturbation oracle before treating it as a record decode.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--hidden-chunks", type=Path, default=DEFAULT_HIDDEN)
    parser.add_argument("--run-glob", default="")
    parser.add_argument("--min-edge-count", type=int, default=8)
    parser.add_argument("--dominance-ratio", type=float, default=2.0)
    parser.add_argument("--top-edges", type=int, default=64)
    parser.add_argument("--write-contigs", type=int, default=64)
    parser.add_argument("--contig-dir", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report) + "\n")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    print(f"wrote contigs under {args.contig_dir}")


if __name__ == "__main__":
    main()
