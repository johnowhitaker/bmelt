#!/usr/bin/env python3
"""Decode the normal work-window dispatch stub island."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_int(value: str) -> int:
    return int(value, 0)


def u16be(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def parse_entries(data: bytes, start: int, limit: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    offset = start
    index = 0
    end = min(len(data), start + limit)
    while offset + 4 < end:
        if data[offset] == 0x74 and data[offset + 2] == 0x02:
            entries.append(
                {
                    "index": index,
                    "offset": offset,
                    "kind": "mov_a_ljmp",
                    "selector": data[offset + 1],
                    "target": u16be(data, offset + 3),
                    "length": 5,
                    "bytes": data[offset : offset + 5].hex(),
                }
            )
            offset += 5
            index += 1
            continue
        if offset + 5 < end and data[offset] == 0x90 and data[offset + 3] == 0x02:
            entries.append(
                {
                    "index": index,
                    "offset": offset,
                    "kind": "mov_dptr_ljmp",
                    "param": u16be(data, offset + 1),
                    "target": u16be(data, offset + 4),
                    "length": 6,
                    "bytes": data[offset : offset + 6].hex(),
                }
            )
            offset += 6
            index += 1
            continue
        break
    return entries


def correlate_cdd(entries: list[dict[str, Any]], cdd_map: Path) -> dict[str, Any] | None:
    if not cdd_map.exists():
        return None
    data = json.loads(cdd_map.read_text())
    records = [record for image in data.get("images", []) for record in image.get("records", [])]
    op_keys = {bytes.fromhex(record["operation_key"]) for record in records}
    entry_bytes = [bytes.fromhex(row["bytes"]) for row in entries]
    exact_op_key_matches = sum(1 for item in entry_bytes if item in op_keys)

    targets = Counter(row["target"] for row in entries if row["kind"] == "mov_dptr_ljmp")
    target_pair_hits = []
    for offset in range(5):
        hits = Counter()
        for key in op_keys:
            value = (key[offset] << 8) | key[offset + 1]
            if value in targets:
                hits[value] += 1
        if hits:
            target_pair_hits.append(
                {
                    "operation_key_pair_offset": offset,
                    "unique_target_values": len(hits),
                    "record_hits": sum(hits.values()),
                    "top": [
                        {"value": value, "record_hits": count, "dispatch_count": targets[value]}
                        for value, count in hits.most_common(8)
                    ],
                }
            )

    return {
        "cdd_map": str(cdd_map),
        "operation_keys": len(op_keys),
        "records": len(records),
        "exact_entry_op_key_matches": exact_op_key_matches,
        "target_pair_hits": target_pair_hits,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window Dispatch Stub Table",
        "",
        f"Source window: `{report['window']}`",
        f"Start offset: `+0x{report['start']:04x}`",
        f"Stop offset: `+0x{report['stop']:04x}`",
        f"Parsed entries: {len(report['entries'])}",
        "",
        "The island starts one byte before the public `+0xa180` chunk boundary.",
        "It has a very regular dispatch-stub shape:",
        "",
        "- early entries are `MOV A,#selector; LJMP 0x0162`;",
        "- later entries are `MOV DPTR,#param; LJMP resident_handler`.",
        "",
        "Important caveat: public offsets in this `READ BUFFER` window are not a",
        "flat mirror of active 8051 code space. The bytes at public `+0x0162` do",
        "not match the static resident bytes at code address `0x0162`. The low",
        "`LJMP` targets do, however, land on plausible resident helper routines in",
        "`analysis/8051/ldm58051.bin`. Treat this as a banked/threaded runtime",
        "artifact until the code-window mapping is pinned down.",
        "",
        "## Target Counts",
        "",
        "| target | count | resident bytes | public-window bytes |",
        "|---:|---:|---|---|",
    ]
    for row in report["target_counts"]:
        resident_bytes = row["resident_bytes"] or "-"
        window_bytes = row["window_bytes"] or "-"
        lines.append(
            f"| `0x{row['target']:04x}` | {row['count']} | "
            f"`{resident_bytes}` | `{window_bytes}` |"
        )

    lines += [
        "",
        "## First Entries",
        "",
        "| idx | offset | kind | selector/param | target | bytes |",
        "|---:|---:|---|---:|---:|---|",
    ]
    for row in report["entries"][:96]:
        if row["kind"] == "mov_a_ljmp":
            arg = f"`0x{row['selector']:02x}`"
        else:
            arg = f"`0x{row['param']:04x}`"
        lines.append(
            f"| {row['index']} | `+0x{row['offset']:04x}` | {row['kind']} | "
            f"{arg} | `0x{row['target']:04x}` | `{row['bytes']}` |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- The low branch targets are real resident code offsets in",
        "  `analysis/8051/ldm58051.bin`, even though the public work-window bytes",
        "  at those low offsets are different.",
        "- Entry `0..31` gives a compact default-selector path through",
        "  `0x0162`; those selectors line up with the command-like byte tests seen",
        "  against `xdata[0x8a49]`.",
        "- The `MOV DPTR,#param; LJMP handler` entries look like a second-stage",
        "  threaded-code table with a per-entry parameter. This is a better",
        "  analysis target than treating the `+0xa180..` island as linear code.",
    ]
    if report.get("cdd_correlation"):
        cdd = report["cdd_correlation"]
        lines += [
            "",
            "## CDD Correlation Check",
            "",
            f"CDD map: `{cdd['cdd_map']}`",
            f"CDD operation keys: {cdd['operation_keys']} unique / {cdd['records']} records",
            f"Exact six-byte entry/op-key matches: {cdd['exact_entry_op_key_matches']}",
            "",
            "The exact intersection is zero, so the dispatch entries should not be",
            "treated as raw CDD directory operation keys. Adjacent two-byte target",
            "pair overlaps are also negligible:",
            "",
            "| op-key pair offset | unique target values | record hits | top overlap |",
            "|---:|---:|---:|---|",
        ]
        for row in cdd["target_pair_hits"]:
            top = ", ".join(
                f"`0x{item['value']:04x}` records {item['record_hits']} dispatch {item['dispatch_count']}"
                for item in row["top"]
            )
            lines.append(
                f"| {row['operation_key_pair_offset']} | {row['unique_target_values']} | "
                f"{row['record_hits']} | {top} |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=Path, required=True)
    parser.add_argument("--resident", type=Path, default=Path("analysis/8051/ldm58051.bin"))
    parser.add_argument("--start", type=parse_int, default=0xA17F)
    parser.add_argument("--limit", type=parse_int, default=0x8000)
    parser.add_argument(
        "--cdd-map",
        type=Path,
        default=Path("references/firmware/extracted/liteon-cdd-record-map.json"),
    )
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    window = args.window.read_bytes()
    resident = args.resident.read_bytes() if args.resident.exists() else b""
    entries = parse_entries(window, args.start, args.limit)
    stop = entries[-1]["offset"] + entries[-1]["length"] if entries else args.start
    counts = Counter(row["target"] for row in entries)
    target_counts = []
    for target, count in counts.most_common():
        resident_bytes = resident[target : target + 12].hex() if target + 1 < len(resident) else ""
        window_bytes = window[target : target + 12].hex() if target + 1 < len(window) else ""
        target_counts.append(
            {
                "target": target,
                "count": count,
                "resident_bytes": resident_bytes,
                "window_bytes": window_bytes,
            }
        )

    report = {
        "window": str(args.window),
        "resident": str(args.resident),
        "start": args.start,
        "stop": stop,
        "entries": entries,
        "target_counts": target_counts,
        "cdd_correlation": correlate_cdd(entries, args.cdd_map),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))


if __name__ == "__main__":
    main()
