#!/usr/bin/env python3
"""Analyze adjacency between normal-mode decoded-looking work-window tiles.

The normal `READ BUFFER id=01 offset=0x070000` window exposes a rotating
surface of 0x40-byte chunks.  The known-plaintext pair corpus maps some of
those chunks to candidate CDD records.  This script asks a different question:

    when decoded-looking chunks appear in the same captured window, which
    chunks are physically adjacent in the host-visible tile surface?

That does not make public offsets byte-accurate decoded CDD addresses.  It does
give a repeatable graph of local decoded-output neighborhoods.  Edges that
repeat across many captures are good targets for later CDD grammar work and for
normal-mode patch planning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 0x40


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_ld5m_records(record_map: Path) -> list[dict[str, Any]]:
    data = json.loads(record_map.read_text())
    for image in data["images"]:
        if "LD5M" in image["image"].upper():
            return image["records"]
    raise ValueError(f"no LD5M image in {record_map}")


def record_for_public_offset(records: list[dict[str, Any]], offset: int) -> dict[str, Any] | None:
    for record in records:
        start = int(record["decoded_start"])
        end = start + int(record["decoded_span"])
        if start <= offset < end:
            return record
    return None


def compact_counter(counter: Counter[Any], limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for value, count in counter.most_common(limit):
        rows.append({"value": value, "count": count})
    return rows


def collect_capture_paths(run_dirs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for run_dir in run_dirs:
        paths.extend(sorted(run_dir.glob("*.window.bin")))
    return paths


def edge_key(src: str, dst: str) -> str:
    return f"{src}->{dst}"


def add_edge(
    edges: dict[str, dict[str, Any]],
    src: str,
    dst: str,
    path: Path,
    public_offset: int,
    extra: dict[str, Any] | None = None,
) -> None:
    key = edge_key(src, dst)
    row = edges.setdefault(
        key,
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
    row["offsets"][public_offset] += 1
    if len(row["examples"]) < 6:
        example = {
            "run": path.parent.name,
            "capture": path.name,
            "public_offset": public_offset,
        }
        if extra:
            example.update(extra)
        row["examples"].append(example)


def connected_components(edge_rows: list[dict[str, Any]]) -> list[list[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for row in edge_rows:
        graph[row["src"]].add(row["dst"])
        graph[row["dst"]].add(row["src"])

    seen: set[str] = set()
    components: list[list[str]] = []
    for node in sorted(graph):
        if node in seen:
            continue
        queue = deque([node])
        seen.add(node)
        component: list[str] = []
        while queue:
            cur = queue.popleft()
            component.append(cur)
            for nxt in sorted(graph[cur]):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        components.append(sorted(component))
    components.sort(key=lambda item: (-len(item), item[0]))
    return components


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    pair_report = json.loads(args.pairs.read_text())
    records = load_ld5m_records(args.record_map)
    hidden_report = json.loads(args.hidden_chunks.read_text()) if args.hidden_chunks.exists() else {}

    chunk_meta: dict[str, dict[str, Any]] = {}
    chunk_records: dict[str, set[int]] = defaultdict(set)
    for pair in pair_report["pairs"]:
        digest = pair["chunk_sha256"]
        chunk_meta.setdefault(
            digest,
            {
                "short": pair["chunk_short"],
                "sha256": digest,
                "hex": pair["decoded_hex"],
                "records": set(),
            },
        )
        chunk_meta[digest]["records"].add(int(pair["record"]))
        chunk_records[digest].add(int(pair["record"]))

    run_dirs = [ROOT / path for path in hidden_report.get("run_dirs", [])]
    if args.run_glob:
        run_dirs.extend(path for path in sorted(ROOT.glob(args.run_glob)) if path.is_dir())
    # Preserve order while removing duplicates.
    unique_run_dirs: list[Path] = []
    seen_dirs: set[Path] = set()
    for run_dir in run_dirs:
        resolved = run_dir.resolve()
        if resolved not in seen_dirs:
            seen_dirs.add(resolved)
            unique_run_dirs.append(run_dir)

    paths = collect_capture_paths(unique_run_dirs)

    raw_edges: dict[str, dict[str, Any]] = {}
    shared_record_edges: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    slot_record_edges: dict[int, dict[str, dict[str, Any]]] = defaultdict(dict)
    same_record_slot_observations = 0
    known_adjacent_observations = 0

    known_chunks = set(chunk_meta)
    windows_with_known_edges: set[str] = set()

    for path in paths:
        data = path.read_bytes()
        digests = [
            sha256_hex(data[offset : offset + CHUNK_SIZE])
            for offset in range(0, len(data) - CHUNK_SIZE + 1, CHUNK_SIZE)
        ]
        for index, (src, dst) in enumerate(zip(digests, digests[1:])):
            public_offset = index * CHUNK_SIZE
            if src not in known_chunks or dst not in known_chunks:
                continue
            known_adjacent_observations += 1
            windows_with_known_edges.add(str(path))
            add_edge(raw_edges, src, dst, path, public_offset)

            shared_records = chunk_records[src] & chunk_records[dst]
            for record_index in sorted(shared_records):
                add_edge(shared_record_edges[record_index], src, dst, path, public_offset)

            rec_a = record_for_public_offset(records, public_offset)
            rec_b = record_for_public_offset(records, public_offset + CHUNK_SIZE)
            if rec_a and rec_b and rec_a["index"] == rec_b["index"]:
                same_record_slot_observations += 1
                record_index = int(rec_a["index"])
                rel = public_offset - int(rec_a["decoded_start"])
                add_edge(
                    slot_record_edges[record_index],
                    src,
                    dst,
                    path,
                    public_offset,
                    {"record_relative": rel},
                )

    def finalize_edges(edges: dict[str, dict[str, Any]], limit: int | None = None) -> list[dict[str, Any]]:
        rows = sorted(edges.values(), key=lambda row: (-row["count"], row["src"], row["dst"]))
        if limit is not None:
            rows = rows[:limit]
        final = []
        for row in rows:
            src_meta = chunk_meta[row["src"]]
            dst_meta = chunk_meta[row["dst"]]
            final.append(
                {
                    "src": row["src"],
                    "src_short": src_meta["short"],
                    "src_records": sorted(src_meta["records"]),
                    "dst": row["dst"],
                    "dst_short": dst_meta["short"],
                    "dst_records": sorted(dst_meta["records"]),
                    "count": row["count"],
                    "offsets": compact_counter(row["offsets"]),
                    "runs": compact_counter(row["runs"]),
                    "examples": row["examples"],
                    "src_hex_prefix": src_meta["hex"][:32],
                    "dst_hex_prefix": dst_meta["hex"][:32],
                }
            )
        return final

    per_record = []
    for record_index in sorted(set(shared_record_edges) | set(slot_record_edges)):
        record = records[record_index]
        shared_rows = finalize_edges(shared_record_edges.get(record_index, {}), limit=24)
        slot_rows = finalize_edges(slot_record_edges.get(record_index, {}), limit=24)
        components = connected_components(slot_rows or shared_rows)
        per_record.append(
            {
                "record": record_index,
                "mode": record["mode"],
                "operation_key": record["operation_key"],
                "source_len": record["source_len"],
                "decoded_span": record["decoded_span"],
                "shared_record_edge_count": len(shared_record_edges.get(record_index, {})),
                "slot_edge_count": len(slot_record_edges.get(record_index, {})),
                "slot_observations": sum(row["count"] for row in slot_record_edges.get(record_index, {}).values()),
                "shared_observations": sum(row["count"] for row in shared_record_edges.get(record_index, {}).values()),
                "components": components[:8],
                "top_shared_record_edges": shared_rows,
                "top_slot_edges": slot_rows,
            }
        )

    return {
        "schema": "liteon-cdd-tile-adjacency-v1",
        "pairs": str(args.pairs),
        "hidden_chunks": str(args.hidden_chunks),
        "record_map": str(args.record_map),
        "run_dirs": [str(path.relative_to(ROOT)) for path in unique_run_dirs],
        "captures_scanned": len(paths),
        "known_chunks": len(known_chunks),
        "windows_with_known_edges": len(windows_with_known_edges),
        "known_adjacent_observations": known_adjacent_observations,
        "same_record_slot_observations": same_record_slot_observations,
        "raw_edge_count": len(raw_edges),
        "shared_record_edge_count": sum(len(edges) for edges in shared_record_edges.values()),
        "slot_record_edge_count": sum(len(edges) for edges in slot_record_edges.values()),
        "top_raw_edges": finalize_edges(raw_edges, limit=args.top_edges),
        "records": sorted(
            per_record,
            key=lambda row: (
                -row["slot_observations"],
                -row["shared_observations"],
                row["record"],
            ),
        ),
    }


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Tile Adjacency For CDD Known-Output Chunks",
        "",
        "This report looks at decoded-looking normal-mode work-window tiles that",
        "already have candidate CDD record buckets. It records which 0x40-byte",
        "tiles sit next to each other in actual host-visible captures.",
        "",
        "Two edge types matter:",
        "",
        "- `slot edge`: both adjacent tiles occupy public offsets that fall inside",
        "  the same candidate CDD decoded-span bucket in that capture.",
        "- `shared-record edge`: both tile identities have previously been mapped",
        "  somewhere into the same CDD record, regardless of their current public",
        "  slot.",
        "",
        "Neither edge type proves byte-accurate decoded CDD addresses. Repeated",
        "edges are still useful because they expose local decoded-output",
        "neighborhoods without another live write experiment.",
        "",
        "## Summary",
        "",
        f"- captures scanned: `{report['captures_scanned']}`",
        f"- known chunks in pair corpus: `{report['known_chunks']}`",
        f"- captures containing adjacent known chunks: `{report['windows_with_known_edges']}`",
        f"- adjacent known-chunk observations: `{report['known_adjacent_observations']}`",
        f"- same-record slot observations: `{report['same_record_slot_observations']}`",
        f"- unique raw edges: `{report['raw_edge_count']}`",
        f"- unique shared-record edges: `{report['shared_record_edge_count']}`",
        f"- unique slot-record edges: `{report['slot_record_edge_count']}`",
        "",
        "## Records With Strongest Local Structure",
        "",
        md_table(
            ["record", "mode", "op key", "source", "decoded", "slot obs", "shared obs", "slot edges", "shared edges"],
            [
                [
                    str(row["record"]),
                    f"`0x{row['mode']:02x}`",
                    f"`{row['operation_key']}`",
                    str(row["source_len"]),
                    str(row["decoded_span"]),
                    str(row["slot_observations"]),
                    str(row["shared_observations"]),
                    str(row["slot_edge_count"]),
                    str(row["shared_record_edge_count"]),
                ]
                for row in report["records"][:24]
            ],
        ),
        "",
        "## Top Raw Edges",
        "",
        md_table(
            ["src", "dst", "count", "top offsets", "src recs", "dst recs", "src prefix", "dst prefix"],
            [
                [
                    f"`{row['src_short']}`",
                    f"`{row['dst_short']}`",
                    str(row["count"]),
                    ", ".join(f"`0x{item['value']:04x}` x{item['count']}" for item in row["offsets"][:4]),
                    ",".join(map(str, row["src_records"])),
                    ",".join(map(str, row["dst_records"])),
                    f"`{row['src_hex_prefix']}...`",
                    f"`{row['dst_hex_prefix']}...`",
                ]
                for row in report["top_raw_edges"][:24]
            ],
        ),
        "",
    ]

    for record in report["records"][:12]:
        lines.extend(
            [
                f"## Record {record['record']}",
                "",
                f"- mode: `0x{record['mode']:02x}`",
                f"- op key: `{record['operation_key']}`",
                f"- source/decoded: `{record['source_len']}/{record['decoded_span']}`",
                f"- slot/shared observations: `{record['slot_observations']}/{record['shared_observations']}`",
                "",
            ]
        )
        if record["top_slot_edges"]:
            lines.extend(
                [
                    "Top same-slot-record edges:",
                    "",
                    md_table(
                        ["src", "dst", "count", "offsets", "src prefix", "dst prefix"],
                        [
                            [
                                f"`{edge['src_short']}`",
                                f"`{edge['dst_short']}`",
                                str(edge["count"]),
                                ", ".join(
                                    f"`0x{item['value']:04x}` x{item['count']}" for item in edge["offsets"][:4]
                                ),
                                f"`{edge['src_hex_prefix']}...`",
                                f"`{edge['dst_hex_prefix']}...`",
                            ]
                            for edge in record["top_slot_edges"][:8]
                        ],
                    ),
                    "",
                ]
            )
        if record["top_shared_record_edges"]:
            lines.extend(
                [
                    "Top shared-record identity edges:",
                    "",
                    md_table(
                        ["src", "dst", "count", "offsets", "src prefix", "dst prefix"],
                        [
                            [
                                f"`{edge['src_short']}`",
                                f"`{edge['dst_short']}`",
                                str(edge["count"]),
                                ", ".join(
                                    f"`0x{item['value']:04x}` x{item['count']}" for item in edge["offsets"][:4]
                                ),
                                f"`{edge['src_hex_prefix']}...`",
                                f"`{edge['dst_hex_prefix']}...`",
                            ]
                            for edge in record["top_shared_record_edges"][:8]
                        ],
                    ),
                    "",
                ]
            )
        if record["components"]:
            lines.extend(
                [
                    "Largest local components:",
                    "",
                    md_table(
                        ["size", "chunks"],
                        [
                            [str(len(component)), ", ".join(f"`{item[:12]}`" for item in component[:10])]
                            for component in record["components"][:6]
                        ],
                    ),
                    "",
                ]
            )

    lines.extend(
        [
            "## Practical Read",
            "",
            "The adjacency graph is a better guide than public offset alone. It lets",
            "us pick compact CDD records where several decoded-looking tiles form a",
            "repeatable local neighborhood. Those are the records most worth using",
            "as known-output anchors for the next static grammar attack.",
            "",
            "The strongest records here should be cross-checked against the encoded",
            "source spans before assuming any exact placement. A useful next script",
            "would export each strong record as `source.bin` plus ordered tile",
            "components so brute-force grammar tests can operate on one record at a",
            "time.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pairs",
        type=Path,
        default=Path("analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.json"),
    )
    parser.add_argument(
        "--hidden-chunks",
        type=Path,
        default=Path("analysis/8051/normal-hidden-runtime-chunks-with-readonly-harvests-20260501.json"),
    )
    parser.add_argument(
        "--record-map",
        type=Path,
        default=Path("references/firmware/extracted/liteon-cdd-record-map.json"),
    )
    parser.add_argument("--run-glob", default="")
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--top-edges", type=int, default=64)
    args = parser.parse_args()

    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report) + "\n")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
