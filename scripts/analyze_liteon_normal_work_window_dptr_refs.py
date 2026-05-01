#!/usr/bin/env python3
"""Scan harvested normal work-window chunks for 8051 MOV DPTR immediates."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_informative_chunk(chunk: bytes) -> bool:
    return len(set(chunk)) > 1


def scan_dptr(data: bytes) -> list[tuple[int, int]]:
    refs: list[tuple[int, int]] = []
    for offset in range(0, max(0, len(data) - 2)):
        if data[offset] == 0x90:
            refs.append((offset, (data[offset + 1] << 8) | data[offset + 2]))
    return refs


def load_chunk_refs(run_dirs: list[Path], chunk_size: int) -> dict[int, dict[str, Any]]:
    refs: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"chunks": set(), "observations": [], "public_offsets": set(), "samples": []}
    )
    for run_dir in run_dirs:
        for path in sorted(run_dir.glob("*.window.bin")):
            data = path.read_bytes()
            for public_offset in range(0, len(data) - chunk_size + 1, chunk_size):
                chunk = data[public_offset : public_offset + chunk_size]
                if not is_informative_chunk(chunk):
                    continue
                digest = sha256_hex(chunk)
                for inner_offset, addr in scan_dptr(chunk):
                    item = refs[addr]
                    item["chunks"].add(digest)
                    item["public_offsets"].add(public_offset)
                    if len(item["samples"]) < 8:
                        start = max(0, inner_offset - 4)
                        end = min(len(chunk), inner_offset + 12)
                        item["samples"].append(chunk[start:end].hex())
                    item["observations"].append(
                        {
                            "run": run_dir.name,
                            "capture": path.name.removesuffix(".window.bin"),
                            "public_offset": public_offset,
                            "inner_offset": inner_offset,
                        }
                    )
    return refs


def load_reference_refs(references: list[tuple[str, Path]]) -> dict[str, dict[int, int]]:
    out: dict[str, dict[int, int]] = {}
    for name, path in references:
        data = path.read_bytes()
        counts: dict[int, int] = defaultdict(int)
        for _, addr in scan_dptr(data):
            counts[addr] += 1
        out[name] = dict(counts)
    return out


def parse_reference(value: str) -> tuple[str, Path]:
    if "=" not in value:
        path = Path(value)
        return path.stem, path
    name, path_text = value.split("=", 1)
    return name, Path(path_text)


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Work-Window DPTR References",
        "",
        f"Chunk size: `{report['chunk_size']:#x}`",
        f"Distinct DPTR immediates: {report['distinct_refs']}",
        "",
        "## Top XDATA-Like References",
        "",
        "| addr | observations | chunks | public offsets | refs also in | samples |",
        "|---:|---:|---:|---:|---|---|",
    ]
    for item in report["top_xdata_refs"][:80]:
        refs = ", ".join(f"`{name}`" for name in item["reference_names"]) or "-"
        samples = "<br>".join(f"`{sample}`" for sample in item["samples"][:2])
        lines.append(
            f"| `0x{item['addr']:04x}` | {item['observations']} | {item['chunk_count']} | "
            f"{item['public_offset_count']} | {refs} | {samples} |"
        )
    lines += [
        "",
        "## XDATA-Like References Not Seen In Static References",
        "",
        "| addr | observations | chunks | public offsets | samples |",
        "|---:|---:|---:|---:|---|",
    ]
    for item in report["xdata_refs_not_in_references"][:80]:
        samples = "<br>".join(f"`{sample}`" for sample in item["samples"][:2])
        lines.append(
            f"| `0x{item['addr']:04x}` | {item['observations']} | {item['chunk_count']} | "
            f"{item['public_offset_count']} | {samples} |"
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
    references = [parse_reference(value) for value in args.reference]
    chunk_refs = load_chunk_refs(args.run_dirs, args.chunk_size)
    reference_refs = load_reference_refs(references)

    rows = []
    for addr, item in chunk_refs.items():
        reference_names = [
            name for name, refs in reference_refs.items() if addr in refs
        ]
        rows.append(
            {
                "addr": addr,
                "observations": len(item["observations"]),
                "chunk_count": len(item["chunks"]),
                "public_offset_count": len(item["public_offsets"]),
                "public_offsets": sorted(item["public_offsets"]),
                "samples": item["samples"],
                "reference_names": reference_names,
                "reference_counts": {
                    name: refs.get(addr, 0) for name, refs in reference_refs.items()
                },
            }
        )
    rows.sort(key=lambda item: (-item["observations"], item["addr"]))

    xdata_refs = [
        row for row in rows if 0x4000 <= row["addr"] <= 0xFFFF
    ]
    not_in_refs = [
        row for row in xdata_refs if not row["reference_names"]
    ]
    report: dict[str, Any] = {
        "chunk_size": args.chunk_size,
        "distinct_refs": len(rows),
        "top_refs": rows[:256],
        "top_xdata_refs": xdata_refs[:256],
        "xdata_refs_not_in_references": not_in_refs[:256],
    }

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
