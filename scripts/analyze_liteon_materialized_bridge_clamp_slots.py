#!/usr/bin/env python3
"""Rank observed materialized READ BUFFER bridge clamp slots.

The normal public work-window captures expose a rotating bridge chunk that
contains this 8051 sequence:

    MOV  DPTR,#0x8a4c
    MOVX A,@DPTR
    CLR  C
    SUBB A,#0x0e
    JC   use_cdb_offset
    MOV  DPTR,#0x4011
    MOV  A,#0x0e
    MOVX @DPTR,A

`post-materializer-runtime-bridge-clamp07` targets the second `0x0e`, the
`MOV A,#0x0e` immediate. This script scans saved normal work-window `.bin`
captures, ranks those immediate offsets, and verifies whether the candidate
builder covers the common rotating slots.

Offline only. No drive commands are sent.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCAN_ROOT = ROOT / "references/evidence/live"
DEFAULT_OUT_JSON = ROOT / "analysis/8051/materialized-bridge-clamp-slots-20260506.json"
DEFAULT_OUT_MD = ROOT / "analysis/8051/materialized-bridge-clamp-slots-20260506.md"
BUILDER = ROOT / "scripts/build_liteon_post_materializer_hook_candidates.py"

# Immediate to patch is pattern_start + 13.
CLAMP_PATTERN = bytes.fromhex("908a4ce0c3940e4008904011740ef0")
CLAMP_IMMEDIATE_INDEX = 13


def import_builder_addresses() -> list[int]:
    spec = importlib.util.spec_from_file_location("bridge_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.BRIDGE_CLAMP_IMMEDIATE_ADDRS)


def scan_file(path: Path, public_base: int) -> list[dict[str, Any]]:
    data = path.read_bytes()
    hits = []
    start = data.find(CLAMP_PATTERN)
    while start != -1:
        immediate_offset = start + CLAMP_IMMEDIATE_INDEX
        hits.append(
            {
                "file": str(path.relative_to(ROOT)),
                "file_offset": immediate_offset,
                "public_addr": public_base + immediate_offset,
                "pattern_start": start,
                "context_hex": data[max(0, start - 8) : start + len(CLAMP_PATTERN) + 8].hex(),
            }
        )
        start = data.find(CLAMP_PATTERN, start + 1)
    return hits


def scan_roots(roots: list[Path], public_base: int) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for root in roots:
        if root.is_file():
            if root.suffix == ".bin":
                hits.extend(scan_file(root, public_base))
            continue
        for path in root.rglob("*.bin"):
            try:
                hits.extend(scan_file(path, public_base))
            except OSError:
                continue
    return hits


def write_reports(report: dict[str, Any], json_out: Path, md_out: Path) -> None:
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Materialized Bridge Clamp Slots - 2026-05-06",
        "",
        "Offline scan only; no drive commands were sent.",
        "",
        f"- pattern: `{CLAMP_PATTERN.hex()}`",
        f"- hits: `{report['total_hits']}`",
        f"- files with hits: `{report['files_with_hits']}`",
        f"- public base assumption: `0x{report['public_base']:06x}`",
        "",
        "## Candidate Coverage",
        "",
        f"- builder addresses: {', '.join(f'`0x{x:06x}`' for x in report['builder_addresses'])}",
        f"- covered top slots: `{report['covered_top_slots']}/{report['top_n']}`",
        f"- missing top slots: {', '.join(f'`0x{x:06x}`' for x in report['missing_top_slots']) or '-'}",
        "",
        "## Top Clamp Immediate Slots",
        "",
        "| rank | public addr | file offset | count | covered | example |",
        "|---:|---:|---:|---:|:---:|---|",
    ]
    for row in report["top_slots"]:
        lines.append(
            "| {rank} | `0x{public_addr:06x}` | `0x{file_offset:04x}` | {count} | {covered} | `{example}` |".format(
                rank=row["rank"],
                public_addr=row["public_addr"],
                file_offset=row["file_offset"],
                count=row["count"],
                covered="yes" if row["covered"] else "no",
                example=row["example"],
            )
        )
    lines += [
        "",
        "Interpretation: these are the observed rotating copies of the same",
        "normal READ BUFFER response bridge clamp immediate. The current",
        "`post-materializer-runtime-bridge-clamp07` candidate intentionally",
        "patches the top slots so a high-offset READ BUFFER request has a",
        "direct-response proof signal if the resident hook can patch materialized",
        "runtime RAM after CDD setup.",
        "",
    ]
    md_out.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="*", type=Path, default=[DEFAULT_SCAN_ROOT])
    parser.add_argument("--public-base", type=lambda value: int(value, 0), default=0x070000)
    parser.add_argument("--top-n", type=int, default=6)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    builder_addresses = import_builder_addresses()
    hits = scan_roots(args.roots, args.public_base)

    count_by_addr = Counter(hit["public_addr"] for hit in hits)
    example_by_addr: dict[int, str] = {}
    file_offset_by_addr: dict[int, int] = {}
    files_by_addr: dict[int, set[str]] = defaultdict(set)
    for hit in hits:
        addr = hit["public_addr"]
        example_by_addr.setdefault(addr, hit["file"])
        file_offset_by_addr.setdefault(addr, hit["file_offset"])
        files_by_addr[addr].add(hit["file"])

    top_slots = []
    for rank, (addr, count) in enumerate(count_by_addr.most_common(max(args.top_n, 1)), start=1):
        top_slots.append(
            {
                "rank": rank,
                "public_addr": addr,
                "file_offset": file_offset_by_addr[addr],
                "count": count,
                "file_count": len(files_by_addr[addr]),
                "covered": addr in builder_addresses,
                "example": example_by_addr[addr],
            }
        )

    top_addrs = [row["public_addr"] for row in top_slots[: args.top_n]]
    report = {
        "roots": [str(path) for path in args.roots],
        "public_base": args.public_base,
        "pattern_hex": CLAMP_PATTERN.hex(),
        "total_hits": len(hits),
        "files_with_hits": len({hit["file"] for hit in hits}),
        "unique_slots": len(count_by_addr),
        "top_n": args.top_n,
        "builder_addresses": builder_addresses,
        "top_slots": top_slots,
        "covered_top_slots": sum(1 for addr in top_addrs if addr in builder_addresses),
        "missing_top_slots": [addr for addr in top_addrs if addr not in builder_addresses],
    }
    write_reports(report, args.json_out, args.md_out)
    print(json.dumps({k: report[k] for k in ("total_hits", "files_with_hits", "covered_top_slots", "missing_top_slots")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
