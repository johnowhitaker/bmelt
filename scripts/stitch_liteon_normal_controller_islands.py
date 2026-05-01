#!/usr/bin/env python3
"""Stitch normal-runtime controller/packet-shadow work-window chunks.

The normal `READ BUFFER id=01 offset=0x070000` work-window does not expose a
single stable linear code image. Runtime chunks rotate through public 0x40-byte
slots, so forcing adjacent public slots into one disassembly can create false
neighbors. This script treats the captures as a chunk-adjacency corpus instead:
find anchor byte patterns, collect the chunks that contain them, then report the
neighbor graph around those chunks inside selected public slot ranges.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any


CHUNK_SIZE = 0x40

DEFAULT_RANGES = {
    "get_config_read_side": [(0x7000, 0x7240)],
    "controller_4099_burst": [(0x7480, 0x7680)],
    "controller_4095_writer": [(0xDBC0, 0xDCC0)],
}

PATTERNS = {
    "getcfg_4099_to_shadow": bytes.fromhex(
        "90 40 99 e0 90 8a 4e f0 "
        "90 40 99 e0 90 8a 53 f0 "
        "90 40 99 e0 90 8a 54 f0"
    ),
    "getcfg_fe_sentinel_branch": bytes.fromhex("90 8a 4d e0 b4 fe 02 80 14"),
    "public_bridge_8a4c_to_4011": bytes.fromhex("90 8a 4c e0 90 40 11 f0"),
    "public_bridge_8a4d_to_4012": bytes.fromhex("90 8a 4d e0 90 40 12 f0"),
    "public_bridge_8a4e_to_4013": bytes.fromhex("90 8a 4e e0 90 40 13 f0"),
    "controller_addr_4091": bytes.fromhex("90 40 91"),
    "controller_addr_4095": bytes.fromhex("90 40 95"),
    "controller_kick_409c": bytes.fromhex("90 40 9c"),
}

SEED_PATTERNS = {
    "getcfg_4099_to_shadow",
    "getcfg_fe_sentinel_branch",
}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16be(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def parse_range(value: str) -> tuple[int, int]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("ranges must be START:END")
    start_text, end_text = value.split(":", 1)
    start = int(start_text, 0)
    end = int(end_text, 0)
    if start < 0 or end <= start:
        raise argparse.ArgumentTypeError(f"bad range {value!r}")
    return start, end


def scan_dptr_refs(data: bytes) -> list[int]:
    return [
        u16be(data, offset + 1)
        for offset in range(0, max(0, len(data) - 2))
        if data[offset] == 0x90
    ]


def scan_branches(data: bytes) -> list[dict[str, int | str]]:
    refs: list[dict[str, int | str]] = []
    for offset in range(0, max(0, len(data) - 2)):
        opcode = data[offset]
        if opcode == 0x02:
            refs.append({"offset": offset, "kind": "ljmp", "target": u16be(data, offset + 1)})
        elif opcode == 0x12:
            refs.append({"offset": offset, "kind": "lcall", "target": u16be(data, offset + 1)})
    return refs


def scan_direct_copies(data: bytes) -> list[dict[str, int]]:
    copies = []
    for offset in range(0, max(0, len(data) - 7)):
        if (
            data[offset] == 0x90
            and data[offset + 3] == 0xE0
            and data[offset + 4] == 0x90
            and data[offset + 7] == 0xF0
        ):
            copies.append(
                {
                    "offset": offset,
                    "src": u16be(data, offset + 1),
                    "dst": u16be(data, offset + 5),
                }
            )
    return copies


def in_ranges(offset: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= offset < end for start, end in ranges)


def compact_counter(counter: Counter[Any], limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    for value, count in counter.most_common(limit):
        if isinstance(value, int):
            display: Any = f"0x{value:04x}"
        else:
            display = value
        rows.append({"value": display, "count": count})
    return rows


def compact_observations(observations: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return observations[:limit]


def find_pattern_hits(data: bytes, pattern: bytes) -> list[int]:
    hits = []
    start = 0
    while True:
        offset = data.find(pattern, start)
        if offset < 0:
            return hits
        hits.append(offset)
        start = offset + 1


def load_corpus(run_dirs: list[Path], ranges: list[tuple[int, int]]) -> dict[str, Any]:
    chunks: dict[str, dict[str, Any]] = {}
    edge_counts: Counter[tuple[str, str]] = Counter()
    edge_examples: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    slot_chunks: dict[int, Counter[str]] = defaultdict(Counter)
    pattern_hits: dict[str, list[dict[str, Any]]] = defaultdict(list)
    captures = 0

    for run_dir in run_dirs:
        for path in sorted(run_dir.glob("*.window.bin")):
            data = path.read_bytes()
            captures += 1
            chunk_hashes = []
            for public_offset in range(0, len(data) - CHUNK_SIZE + 1, CHUNK_SIZE):
                chunk = data[public_offset : public_offset + CHUNK_SIZE]
                digest = sha256_hex(chunk)
                chunk_hashes.append(digest)
                if not in_ranges(public_offset, ranges):
                    continue
                item = chunks.setdefault(
                    digest,
                    {
                        "sha256": digest,
                        "data": chunk,
                        "observations": [],
                    },
                )
                obs = {
                    "run": run_dir.name,
                    "capture": path.name.removesuffix(".window.bin"),
                    "public_offset": public_offset,
                }
                item["observations"].append(obs)
                slot_chunks[public_offset][digest] += 1

            for idx in range(len(chunk_hashes) - 1):
                public_offset = idx * CHUNK_SIZE
                next_offset = public_offset + CHUNK_SIZE
                if not (in_ranges(public_offset, ranges) and in_ranges(next_offset, ranges)):
                    continue
                edge = (chunk_hashes[idx], chunk_hashes[idx + 1])
                edge_counts[edge] += 1
                if len(edge_examples[edge]) < 8:
                    edge_examples[edge].append(
                        {
                            "run": run_dir.name,
                            "capture": path.name.removesuffix(".window.bin"),
                            "public_offset": public_offset,
                        }
                    )

            for name, pattern in PATTERNS.items():
                for hit in find_pattern_hits(data, pattern):
                    chunk_offset = hit - (hit % CHUNK_SIZE)
                    if not in_ranges(chunk_offset, ranges):
                        continue
                    digest = chunk_hashes[chunk_offset // CHUNK_SIZE]
                    hit_record = {
                        "run": run_dir.name,
                        "capture": path.name.removesuffix(".window.bin"),
                        "offset": hit,
                        "chunk_offset": chunk_offset,
                        "chunk_sha256": digest,
                        "rel": hit - chunk_offset,
                    }
                    pattern_hits[name].append(hit_record)

    return {
        "captures": captures,
        "chunks": chunks,
        "edge_counts": edge_counts,
        "edge_examples": edge_examples,
        "slot_chunks": slot_chunks,
        "pattern_hits": pattern_hits,
    }


def chunk_row(
    digest: str,
    chunks: dict[str, dict[str, Any]],
    edge_counts: Counter[tuple[str, str]],
    edge_examples: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    item = chunks[digest]
    data = item["data"]
    observations = item["observations"]
    offset_counter = Counter(obs["public_offset"] for obs in observations)
    run_counter = Counter(obs["run"] for obs in observations)
    prev_counter = Counter({a: count for (a, b), count in edge_counts.items() if b == digest})
    next_counter = Counter({b: count for (a, b), count in edge_counts.items() if a == digest})
    dptr_counter = Counter(scan_dptr_refs(data))
    branch_counter = Counter(
        f"{ref['kind']} 0x{int(ref['target']):04x}" for ref in scan_branches(data)
    )
    copies = scan_direct_copies(data)
    return {
        "sha256": digest,
        "short": digest[:12],
        "observations": len(observations),
        "offsets": compact_counter(offset_counter),
        "runs": compact_counter(run_counter),
        "sample_hex": data.hex(),
        "top_dptr_refs": compact_counter(dptr_counter),
        "top_branches": compact_counter(branch_counter),
        "direct_copies": copies,
        "prev": [
            {
                "short": prev[:12],
                "sha256": prev,
                "count": count,
                "examples": edge_examples.get((prev, digest), []),
            }
            for prev, count in prev_counter.most_common(8)
        ],
        "next": [
            {
                "short": nxt[:12],
                "sha256": nxt,
                "count": count,
                "examples": edge_examples.get((digest, nxt), []),
            }
            for nxt, count in next_counter.most_common(8)
        ],
        "example_observations": compact_observations(observations),
    }


def component_from_seeds(
    seeds: set[str],
    chunks: dict[str, dict[str, Any]],
    edge_counts: Counter[tuple[str, str]],
    min_edge_count: int,
) -> set[str]:
    graph: dict[str, set[str]] = defaultdict(set)
    for (left, right), count in edge_counts.items():
        if count < min_edge_count:
            continue
        if left not in chunks or right not in chunks:
            continue
        graph[left].add(right)
        graph[right].add(left)

    seen = set(seed for seed in seeds if seed in chunks)
    queue = deque(seen)
    while queue:
        current = queue.popleft()
        for neighbor in graph[current]:
            if neighbor in seen:
                continue
            seen.add(neighbor)
            queue.append(neighbor)
    return seen


def build_report(corpus: dict[str, Any], min_edge_count: int) -> dict[str, Any]:
    chunks = corpus["chunks"]
    edge_counts = corpus["edge_counts"]
    edge_examples = corpus["edge_examples"]
    pattern_hits = corpus["pattern_hits"]
    slot_chunks = corpus["slot_chunks"]

    pattern_summary = {}
    seed_chunks: set[str] = set()
    for name, hits in pattern_hits.items():
        offsets = Counter(hit["offset"] for hit in hits)
        runs = Counter(hit["run"] for hit in hits)
        hit_chunks = Counter(hit["chunk_sha256"] for hit in hits)
        if name in SEED_PATTERNS:
            seed_chunks.update(hit_chunks)
        pattern_summary[name] = {
            "hits": len(hits),
            "offsets": compact_counter(offsets),
            "runs": compact_counter(runs, limit=12),
            "chunks": [
                {"short": digest[:12], "sha256": digest, "count": count}
                for digest, count in hit_chunks.most_common(12)
            ],
            "examples": compact_observations(hits),
        }

    component = component_from_seeds(seed_chunks, chunks, edge_counts, min_edge_count)
    component_rows = [
        chunk_row(digest, chunks, edge_counts, edge_examples)
        for digest in component
    ]
    component_rows.sort(
        key=lambda row: (
            min(int(item["value"], 16) for item in row["offsets"]) if row["offsets"] else 0,
            -row["observations"],
            row["short"],
        )
    )

    slot_rows = []
    for public_offset, counter in sorted(slot_chunks.items()):
        slot_rows.append(
            {
                "public_offset": public_offset,
                "unique_chunks": len(counter),
                "observations": sum(counter.values()),
                "chunks": [
                    {
                        "short": digest[:12],
                        "sha256": digest,
                        "count": count,
                    }
                    for digest, count in counter.most_common(10)
                ],
            }
        )

    return {
        "captures": corpus["captures"],
        "chunk_size": CHUNK_SIZE,
        "range_chunks": len(chunks),
        "range_edges": len(edge_counts),
        "min_edge_count": min_edge_count,
        "patterns": pattern_summary,
        "seed_chunks": sorted(seed_chunks),
        "seed_component_chunks": component_rows,
        "slots": slot_rows,
    }


def md_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    out = []
    for row_index, row in enumerate(rows):
        out.append("| " + " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)) + " |")
        if row_index == 0:
            out.append("| " + " | ".join("-" * widths[index] for index in range(len(row))) + " |")
    return "\n".join(out)


def render_markdown(report: dict[str, Any], ranges: list[tuple[int, int]]) -> str:
    lines = [
        "# Normal Controller Island Stitch Report",
        "",
        "This report treats the normal work-window as a rotating 0x40-byte tile",
        "surface. Publicly adjacent slots are useful evidence, but they are not",
        "assumed to be one stable code image unless repeated adjacency supports it.",
        "",
        "## Summary",
        "",
        f"- captures scanned: `{report['captures']}`",
        f"- chunk size: `0x{report['chunk_size']:x}`",
        f"- selected ranges: `{', '.join(f'0x{a:04x}:0x{b:04x}' for a, b in ranges)}`",
        f"- unique chunks in selected ranges: `{report['range_chunks']}`",
        f"- observed adjacent chunk edges in selected ranges: `{report['range_edges']}`",
        f"- seed component chunks at edge threshold `{report['min_edge_count']}`: `{len(report['seed_component_chunks'])}`",
        "",
        "## Anchor Patterns",
        "",
    ]

    pattern_rows = [["pattern", "hits", "offsets", "top runs", "chunks"]]
    for name, item in report["patterns"].items():
        pattern_rows.append(
            [
                f"`{name}`",
                str(item["hits"]),
                ", ".join(f"`{row['value']}` x{row['count']}" for row in item["offsets"]) or "-",
                ", ".join(f"`{row['value']}` x{row['count']}" for row in item["runs"][:4]) or "-",
                ", ".join(f"`{row['short']}` x{row['count']}" for row in item["chunks"][:4]) or "-",
            ]
        )
    lines.append(md_table(pattern_rows))

    lines += [
        "",
        "## GET CONFIG Seed Component",
        "",
        "The main seed is the chunk containing the `0x4099 -> 0x8a4e/0x8a53/0x8a54`",
        "burst and the `0x8a4d == 0xfe` branch. Its neighbors form a small",
        "rotating component around the response builder.",
        "",
    ]
    component_rows = [["chunk", "obs", "offsets", "top DPTR refs", "direct copies", "top next"]]
    for row in report["seed_component_chunks"]:
        direct = ", ".join(
            f"`0x{copy['src']:04x}->0x{copy['dst']:04x}`" for copy in row["direct_copies"][:4]
        )
        component_rows.append(
            [
                f"`{row['short']}`",
                str(row["observations"]),
                ", ".join(f"`{item['value']}` x{item['count']}" for item in row["offsets"][:4]) or "-",
                ", ".join(f"`{item['value']}` x{item['count']}" for item in row["top_dptr_refs"][:6]) or "-",
                direct or "-",
                ", ".join(f"`{item['short']}` x{item['count']}" for item in row["next"][:4]) or "-",
            ]
        )
    lines.append(md_table(component_rows))

    lines += [
        "",
        "## Seed Chunk Hex",
        "",
    ]
    for row in report["seed_component_chunks"]:
        interesting = row["direct_copies"] or any(
            ref["value"] in {"0x4099", "0x8a4d", "0x4011", "0x4091", "0x409c"}
            for ref in row["top_dptr_refs"]
        )
        if not interesting:
            continue
        lines += [
            f"### `{row['short']}`",
            "",
            f"- observations: `{row['observations']}`",
            f"- offsets: {', '.join(f'`{item['value']}` x{item['count']}' for item in row['offsets'])}",
            "",
            "```text",
            row["sample_hex"],
            "```",
            "",
        ]

    lines += [
        "## Interpretation",
        "",
        "- The GET CONFIG-specific anchor is confined to one rotating chunk.",
        "- The common `0x8a4c..0x8a4e -> 0x4011..0x4013` chunk is shared by all",
        "  normal captures, so it is public response plumbing rather than a",
        "  GET CONFIG-only oracle.",
        "- The immediately preceding `0x4091/0x4093/0x409c/0x4099` chunk is the",
        "  best concrete controller-read setup to reverse next.",
        "- The adjacency graph is a safer guide than public slot order; the same",
        "  chunk can appear before or after the seed depending on capture phase.",
        "",
        "A likely linear path, when the `4037c8574920 -> 8d8c3b0a22a0 ->",
        "20ea2ab16891` adjacency is present, is:",
        "",
        "```text",
        "wait for 0x4000.7 clear",
        "xdata[0x8ac6] -> controller[0x4091]",
        "IRAM/local pointer bytes -> controller[0x4092]",
        "LCALL 0x2fb7 with DPTR=0x0001, result -> controller[0x4093]",
        "controller[0x409c] = 0x40, then 0x24",
        "wait for controller[0x409c].5 clear",
        "read controller[0x4099] four times into 0x8a4d,0x8a4e,0x8a53,0x8a54",
        "advance local byte count by four",
        "if 0x8a4d == 0xfe, skip the dynamic length-difference calculation",
        "copy/clamp 0x8a4c..0x8a4e into controller[0x4011..0x4013]",
        "copy 0x8a50..0x8a51 into the IRAM 0xa9/0xaa length/state pair",
        "```",
        "",
        "That makes the cleanest current patch idea a response-builder redirect:",
        "either alter the address material before the `0x4091..0x4093/0x409c`",
        "kick, or replace the four bytes after the `0x4099` reads and before the",
        "`0x4011..0x4013` public response setup. It still needs a safe normal-mode",
        "patch foothold before it becomes a live oracle.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--range", dest="ranges", action="append", type=parse_range)
    parser.add_argument("--min-edge-count", type=int, default=1)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args()

    ranges = args.ranges
    if ranges is None:
        ranges = [item for group in DEFAULT_RANGES.values() for item in group]

    corpus = load_corpus(args.run_dirs, ranges)
    report = build_report(corpus, min_edge_count=args.min_edge_count)

    jsonable = json.loads(json.dumps(report))
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(jsonable, indent=2) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_markdown(report, ranges))
    if not args.out_json and not args.out_md:
        print(json.dumps(jsonable, indent=2))


if __name__ == "__main__":
    main()
