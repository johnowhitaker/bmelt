#!/usr/bin/env python3
"""Build an overlay/frame atlas for normal work-window captures."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_informative_chunk(chunk: bytes) -> bool:
    return len(set(chunk)) > 1


def parse_reference(value: str) -> tuple[str, Path]:
    if "=" not in value:
        path = Path(value)
        return path.stem, path
    name, path_text = value.split("=", 1)
    return name, Path(path_text)


def scan_dptr(data: bytes) -> list[dict[str, int]]:
    refs = []
    for offset in range(0, max(0, len(data) - 2)):
        if data[offset] == 0x90:
            refs.append({"offset": offset, "addr": (data[offset + 1] << 8) | data[offset + 2]})
    return refs


def scan_absolute_branches(data: bytes) -> list[dict[str, int | str]]:
    refs: list[dict[str, int | str]] = []
    for offset in range(0, max(0, len(data) - 2)):
        opcode = data[offset]
        if opcode == 0x02:
            refs.append(
                {
                    "offset": offset,
                    "kind": "ljmp",
                    "target": (data[offset + 1] << 8) | data[offset + 2],
                }
            )
        elif opcode == 0x12:
            refs.append(
                {
                    "offset": offset,
                    "kind": "lcall",
                    "target": (data[offset + 1] << 8) | data[offset + 2],
                }
            )
    return refs


def load_captures(run_dirs: list[Path], chunk_size: int) -> tuple[dict[str, Any], dict[int, Any]]:
    chunks: dict[str, Any] = {}
    slots: dict[int, Any] = defaultdict(lambda: {"observations": 0, "chunks": set(), "runs": set()})
    for run_dir in run_dirs:
        for path in sorted(run_dir.glob("*.window.bin")):
            data = path.read_bytes()
            for public_offset in range(0, len(data) - chunk_size + 1, chunk_size):
                chunk = data[public_offset : public_offset + chunk_size]
                if not is_informative_chunk(chunk):
                    continue
                digest = sha256_hex(chunk)
                item = chunks.setdefault(
                    digest,
                    {
                        "sha256": digest,
                        "data": chunk,
                        "sample_hex": chunk[:16].hex(),
                        "observations": [],
                        "offsets": set(),
                        "runs": set(),
                    },
                )
                obs = {
                    "run": run_dir.name,
                    "capture": path.name.removesuffix(".window.bin"),
                    "public_offset": public_offset,
                }
                item["observations"].append(obs)
                item["offsets"].add(public_offset)
                item["runs"].add(run_dir.name)
                slot = slots[public_offset]
                slot["observations"] += 1
                slot["chunks"].add(digest)
                slot["runs"].add(run_dir.name)
    return chunks, slots


def annotate_static_matches(chunks: dict[str, Any], references: list[tuple[str, Path]]) -> None:
    ref_data = [(name, path, path.read_bytes()) for name, path in references]
    for item in chunks.values():
        matches = []
        data = item["data"]
        for name, path, blob in ref_data:
            pos = blob.find(data)
            if pos != -1:
                matches.append({"reference": name, "path": str(path), "position": pos})
        item["static_matches"] = matches


def annotate_code_features(chunks: dict[str, Any]) -> None:
    for item in chunks.values():
        data = item["data"]
        dptrs = scan_dptr(data)
        branches = scan_absolute_branches(data)
        xdata_like = [ref for ref in dptrs if 0x4000 <= ref["addr"] <= 0xFFFF]
        runtime_shadow = [ref for ref in dptrs if 0x8A00 <= ref["addr"] <= 0x8AFF]
        low_ljmps = [
            ref
            for ref in branches
            if ref["kind"] == "ljmp" and 0x0100 <= int(ref["target"]) <= 0x0220
        ]
        branch_table_like = (
            len(branches) >= 8
            and len(low_ljmps) * 10 >= len(branches) * 6
            and data.count(0x02) >= 8
        )
        branch_dptr_pairs = sum(
            1
            for offset in range(0, max(0, len(data) - 5))
            if data[offset] in {0x02, 0x12} and data[offset + 3] == 0x90
        )
        branch_dptr_table_like = branch_dptr_pairs >= 5 and len(branches) >= 5
        item["dptr_refs"] = dptrs
        item["branches"] = branches
        item["branch_table_like"] = branch_table_like or branch_dptr_table_like
        item["branch_dptr_pairs"] = branch_dptr_pairs
        item["code_score"] = (
            len(xdata_like)
            + 2 * len(runtime_shadow)
            + 2 * len(branches)
            + min(len(set(ref["addr"] for ref in dptrs)), 8)
        )


def compact_chunk(item: dict[str, Any]) -> dict[str, Any]:
    dptr_counts = Counter(ref["addr"] for ref in item["dptr_refs"])
    branch_counts = Counter((ref["kind"], ref["target"]) for ref in item["branches"])
    return {
        "sha256": item["sha256"],
        "sample_hex": item["sample_hex"],
        "observations": len(item["observations"]),
        "offsets": sorted(item["offsets"]),
        "run_count": len(item["runs"]),
        "static_matches": item["static_matches"],
        "code_score": item["code_score"],
        "top_dptr_refs": [
            {"addr": addr, "count": count} for addr, count in dptr_counts.most_common(12)
        ],
        "top_branches": [
            {"kind": kind, "target": target, "count": count}
            for (kind, target), count in branch_counts.most_common(12)
        ],
        "branch_table_like": item["branch_table_like"],
        "branch_dptr_pairs": item["branch_dptr_pairs"],
    }


def build_report(
    chunks: dict[str, Any],
    slots: dict[int, Any],
    chunk_size: int,
) -> dict[str, Any]:
    matched = {digest for digest, item in chunks.items() if item["static_matches"]}
    moving = {digest for digest, item in chunks.items() if len(item["offsets"]) > 1}

    slot_rows = []
    for public_offset, item in slots.items():
        chunk_ids = item["chunks"]
        unmatched = chunk_ids - matched
        moving_here = chunk_ids & moving
        dptr_counter: Counter[int] = Counter()
        branch_counter: Counter[tuple[str, int]] = Counter()
        score = 0
        for digest in sorted(chunk_ids):
            chunk = chunks[digest]
            score += chunk["code_score"]
            dptr_counter.update(ref["addr"] for ref in chunk["dptr_refs"])
            branch_counter.update((ref["kind"], ref["target"]) for ref in chunk["branches"])
        slot_rows.append(
            {
                "public_offset": public_offset,
                "observations": item["observations"],
                "unique_chunks": len(chunk_ids),
                "unmatched_chunks": len(unmatched),
                "moving_chunks": len(moving_here),
                "run_count": len(item["runs"]),
                "aggregate_code_score": score,
                "top_dptr_refs": [
                    {"addr": addr, "count": count}
                    for addr, count in dptr_counter.most_common(10)
                ],
                "top_branches": [
                    {"kind": kind, "target": target, "count": count}
                    for (kind, target), count in branch_counter.most_common(10)
                ],
                "chunk_ids": sorted(chunk_ids),
            }
        )
    slot_rows.sort(
        key=lambda row: (
            -row["unique_chunks"],
            -row["unmatched_chunks"],
            -row["aggregate_code_score"],
            row["public_offset"],
        )
    )

    moving_rows = [
        compact_chunk(chunks[digest])
        for digest in moving
    ]
    moving_rows.sort(
        key=lambda row: (-len(row["offsets"]), -row["observations"], row["offsets"], row["sha256"])
    )

    runtime_code_rows = [
        compact_chunk(item)
        for digest, item in chunks.items()
        if digest not in matched and item["code_score"] > 0 and not item["branch_table_like"]
    ]
    runtime_code_rows.sort(
        key=lambda row: (-row["code_score"], -row["observations"], row["offsets"], row["sha256"])
    )

    table_rows = [
        compact_chunk(item)
        for digest, item in chunks.items()
        if digest not in matched and item["branch_table_like"]
    ]
    table_rows.sort(
        key=lambda row: (-row["observations"], row["offsets"], row["sha256"])
    )

    dptr_counter: Counter[int] = Counter()
    dptr_chunk_counter: dict[int, set[str]] = defaultdict(set)
    branch_counter: Counter[tuple[str, int]] = Counter()
    branch_chunk_counter: dict[tuple[str, int], set[str]] = defaultdict(set)
    for digest, item in chunks.items():
        for ref in item["dptr_refs"]:
            dptr_counter[ref["addr"]] += len(item["observations"])
            dptr_chunk_counter[ref["addr"]].add(digest)
        for ref in item["branches"]:
            key = (str(ref["kind"]), int(ref["target"]))
            branch_counter[key] += len(item["observations"])
            branch_chunk_counter[key].add(digest)

    return {
        "chunk_size": chunk_size,
        "unique_chunks": len(chunks),
        "public_slots": len(slots),
        "static_matched_chunks": len(matched),
        "runtime_unmatched_chunks": len(chunks) - len(matched),
        "moving_chunks": len(moving),
        "slot_atlas": slot_rows,
        "moving_chunk_examples": moving_rows[:128],
        "runtime_code_like_chunks": runtime_code_rows[:256],
        "runtime_branch_table_like_chunks": table_rows[:128],
        "top_dptr_refs": [
            {"addr": addr, "weighted_observations": count, "chunk_count": len(dptr_chunk_counter[addr])}
            for addr, count in dptr_counter.most_common(128)
        ],
        "top_branches": [
            {
                "kind": kind,
                "target": target,
                "weighted_observations": count,
                "chunk_count": len(branch_chunk_counter[(kind, target)]),
            }
            for (kind, target), count in branch_counter.most_common(128)
        ],
    }


def render_refs(refs: list[dict[str, int]], key: str = "addr", limit: int = 6) -> str:
    if not refs:
        return "-"
    return ", ".join(f"`0x{item[key]:04x}`" for item in refs[:limit])


def render_branches(refs: list[dict[str, int | str]], limit: int = 6) -> str:
    if not refs:
        return "-"
    return ", ".join(f"`{item['kind']} 0x{item['target']:04x}`" for item in refs[:limit])


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Overlay Map",
        "",
        f"Chunk size: `{report['chunk_size']:#x}`",
        f"Public slots: {report['public_slots']}",
        f"Unique informative chunks: {report['unique_chunks']}",
        f"Static-matched chunks: {report['static_matched_chunks']}",
        f"Runtime/unmatched chunks: {report['runtime_unmatched_chunks']}",
        f"Chunks observed at multiple public slots: {report['moving_chunks']}",
        "",
        "## Hottest Public Slots",
        "",
        "| slot | unique | unmatched | moving | score | top DPTR refs | top branches |",
        "|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in report["slot_atlas"][:80]:
        lines.append(
            f"| `+0x{row['public_offset']:04x}` | {row['unique_chunks']} | "
            f"{row['unmatched_chunks']} | {row['moving_chunks']} | "
            f"{row['aggregate_code_score']} | {render_refs(row['top_dptr_refs'])} | "
            f"{render_branches(row['top_branches'])} |"
        )

    lines += [
        "",
        "## Moving Chunk Examples",
        "",
        "| chunk | obs | slots | static? | score | sample |",
        "|---|---:|---|---|---:|---|",
    ]
    for row in report["moving_chunk_examples"][:48]:
        slots = ", ".join(f"`+0x{offset:04x}`" for offset in row["offsets"][:8])
        if len(row["offsets"]) > 8:
            slots += ", ..."
        static = ", ".join(
            f"`{match['reference']}@0x{match['position']:x}`"
            for match in row["static_matches"]
        ) or "-"
        lines.append(
            f"| `{row['sha256'][:12]}` | {row['observations']} | {slots} | "
            f"{static} | {row['code_score']} | `{row['sample_hex']}` |"
        )

    lines += [
        "",
        "## Runtime Branch-Table-Like Chunks",
        "",
        "These chunks are runtime/unmatched, but their byte pattern is dominated by",
        "dense low `LJMP` entries or repeated branch-plus-DPTR records. Treat them",
        "as dispatch/vector tables until proven executable in-line.",
        "",
        "| chunk | obs | slots | branches | sample |",
        "|---|---:|---|---|---|",
    ]
    for row in report["runtime_branch_table_like_chunks"][:48]:
        slots = ", ".join(f"`+0x{offset:04x}`" for offset in row["offsets"][:8])
        if len(row["offsets"]) > 8:
            slots += ", ..."
        lines.append(
            f"| `{row['sha256'][:12]}` | {row['observations']} | {slots} | "
            f"{render_branches(row['top_branches'])} | `{row['sample_hex']}` |"
        )

    lines += [
        "",
        "## Runtime Code-Like Chunks",
        "",
        "| chunk | score | obs | slots | DPTR refs | branches | sample |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for row in report["runtime_code_like_chunks"][:80]:
        slots = ", ".join(f"`+0x{offset:04x}`" for offset in row["offsets"][:8])
        if len(row["offsets"]) > 8:
            slots += ", ..."
        lines.append(
            f"| `{row['sha256'][:12]}` | {row['code_score']} | {row['observations']} | "
            f"{slots} | {render_refs(row['top_dptr_refs'])} | "
            f"{render_branches(row['top_branches'])} | `{row['sample_hex']}` |"
        )

    lines += [
        "",
        "## Top Absolute Branch Targets",
        "",
        "| target | kind | weighted observations | chunks |",
        "|---:|---|---:|---:|",
    ]
    for row in report["top_branches"][:64]:
        lines.append(
            f"| `0x{row['target']:04x}` | `{row['kind']}` | "
            f"{row['weighted_observations']} | {row['chunk_count']} |"
        )

    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", type=Path, nargs="+")
    parser.add_argument("--reference", action="append", default=[], help="NAME=PATH or PATH")
    parser.add_argument("--chunk-size", type=lambda value: int(value, 0), default=0x40)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    chunks, slots = load_captures(args.run_dirs, args.chunk_size)
    references = [parse_reference(value) for value in args.reference]
    annotate_static_matches(chunks, references)
    annotate_code_features(chunks)
    report = build_report(chunks, slots, args.chunk_size)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render(report))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
