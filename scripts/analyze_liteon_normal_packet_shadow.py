#!/usr/bin/env python3
"""Analyze normal-runtime work-window chunks around the packet shadow path."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_TARGETS = [
    0x47B1,
    0x8A23,
    *range(0x8A49, 0x8A55),
    0x8ADF,
    0x4000,
    0x4091,
    0x4092,
    0x4093,
    0x4095,
    0x4096,
    0x4097,
    0x4098,
]

CONTROLLER_REGS = {
    0x4000,
    0x4011,
    0x4012,
    0x4013,
    0x40B7,
    *range(0x4091, 0x409A),
}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u16be(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def parse_int(value: str) -> int:
    return int(value, 0)


def load_windows(run_dirs: list[Path]) -> list[dict[str, Any]]:
    windows = []
    for run_dir in run_dirs:
        for path in sorted(run_dir.glob("*.window.bin")):
            windows.append(
                {
                    "run": run_dir.name,
                    "capture": path.name.removesuffix(".window.bin"),
                    "path": str(path),
                    "data": path.read_bytes(),
                }
            )
    return windows


def scan_dptr_refs(data: bytes) -> list[dict[str, int]]:
    refs = []
    for offset in range(0, max(0, len(data) - 2)):
        if data[offset] == 0x90:
            refs.append({"offset": offset, "addr": u16be(data, offset + 1)})
    return refs


def scan_direct_movx_copies(data: bytes) -> list[dict[str, int]]:
    copies = []
    for offset in range(0, max(0, len(data) - 7)):
        if data[offset] == 0x90 and data[offset + 3] == 0xE0 and data[offset + 4] == 0x90 and data[offset + 7] == 0xF0:
            copies.append(
                {
                    "offset": offset,
                    "src": u16be(data, offset + 1),
                    "dst": u16be(data, offset + 5),
                    "kind": "direct",
                }
            )
    return copies


def scan_reg_movx_copies(data: bytes) -> list[dict[str, int | str]]:
    copies: list[dict[str, int | str]] = []
    for offset in range(0, max(0, len(data) - 9)):
        if data[offset] != 0x90 or data[offset + 3] != 0xE0:
            continue
        mov_rn_a = data[offset + 4]
        if not 0xF8 <= mov_rn_a <= 0xFF:
            continue
        reg = mov_rn_a - 0xF8
        if data[offset + 5] != 0x90 or data[offset + 8] != 0xE8 + reg or data[offset + 9] != 0xF0:
            continue
        copies.append(
            {
                "offset": offset,
                "src": u16be(data, offset + 1),
                "dst": u16be(data, offset + 6),
                "kind": f"via_r{reg}",
            }
        )
    return copies


def scan_writes(data: bytes) -> list[dict[str, int | str]]:
    writes: list[dict[str, int | str]] = []
    for offset in range(0, max(0, len(data) - 5)):
        if data[offset] != 0x90:
            continue
        addr = u16be(data, offset + 1)
        tail = data[offset + 3 :]
        if len(tail) >= 3 and tail[0] == 0x74 and tail[2] == 0xF0:
            writes.append({"offset": offset, "addr": addr, "kind": "write_imm", "value": tail[1]})
        if len(tail) >= 2 and tail[0] == 0xE4 and tail[1] == 0xF0:
            writes.append({"offset": offset, "addr": addr, "kind": "write_zero", "value": 0})
        if len(tail) >= 4 and tail[0] == 0xE0 and tail[3] == 0xF0 and tail[1] in {0x44, 0x54}:
            writes.append(
                {
                    "offset": offset,
                    "addr": addr,
                    "kind": "or_mask" if tail[1] == 0x44 else "and_mask",
                    "value": tail[2],
                }
            )
    return writes


def scan_compares(data: bytes) -> list[dict[str, int | str]]:
    compares: list[dict[str, int | str]] = []
    for offset in range(0, max(0, len(data) - 7)):
        if data[offset] != 0x90 or data[offset + 3] != 0xE0:
            continue
        addr = u16be(data, offset + 1)
        if data[offset + 4] == 0x64 and data[offset + 6] in {0x60, 0x70}:
            compares.append(
                {
                    "offset": offset,
                    "addr": addr,
                    "kind": "xrl_a_imm",
                    "value": data[offset + 5],
                    "branch": "jz" if data[offset + 6] == 0x60 else "jnz",
                    "rel": data[offset + 7],
                }
            )
        if data[offset + 4] == 0xB4:
            compares.append(
                {
                    "offset": offset,
                    "addr": addr,
                    "kind": "cjne_a_imm",
                    "value": data[offset + 5],
                    "branch": "cjne",
                    "rel": data[offset + 6],
                }
            )
        if data[offset + 4] == 0xFF and data[offset + 5] == 0x64 and data[offset + 7] in {0x60, 0x70}:
            compares.append(
                {
                    "offset": offset,
                    "addr": addr,
                    "kind": "mov_r7_xrl_imm",
                    "value": data[offset + 6],
                    "branch": "jz" if data[offset + 7] == 0x60 else "jnz",
                    "rel": data[offset + 8],
                }
            )
        if data[offset + 4] == 0xFF and data[offset + 5] == 0xB4:
            compares.append(
                {
                    "offset": offset,
                    "addr": addr,
                    "kind": "mov_r7_cjne_imm",
                    "value": data[offset + 6],
                    "branch": "cjne",
                    "rel": data[offset + 7],
                }
            )
    return compares


def snippet(data: bytes, offset: int, before: int = 16, after: int = 48) -> tuple[int, str]:
    start = max(0, offset - before)
    end = min(len(data), offset + after)
    return start, data[start:end].hex()


def find_fifo_bursts(copies: list[dict[str, int | str]], src: int = 0x47B1) -> list[dict[str, Any]]:
    direct = [copy for copy in copies if copy["src"] == src and copy["kind"] == "direct"]
    direct.sort(key=lambda copy: int(copy["offset"]))
    bursts = []
    i = 0
    while i < len(direct):
        group = [direct[i]]
        j = i + 1
        while j < len(direct):
            prev = group[-1]
            cur = direct[j]
            if int(cur["offset"]) - int(prev["offset"]) == 8 and int(cur["dst"]) == int(prev["dst"]) + 1:
                group.append(cur)
                j += 1
            else:
                break
        if len(group) >= 2:
            bursts.append(
                {
                    "offset": int(group[0]["offset"]),
                    "dst_start": int(group[0]["dst"]),
                    "dst_end": int(group[-1]["dst"]),
                    "count": len(group),
                }
            )
        i = max(j, i + 1)
    return bursts


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Runtime Packet Shadow Analysis",
        "",
        "This report scans complete normal-runtime work-window captures for target",
        "XDATA references and short MOVX idioms. Unlike the overlay atlas, it scans",
        "across `0x40` chunk boundaries, so packet-copy sequences split between",
        "tiles are still detected.",
        "",
        "## Summary",
        "",
        f"- captures: {report['capture_count']}",
        f"- target DPTR observations: {report['target_dptr_observations']}",
        f"- unique target chunks: {report['unique_target_chunks']}",
        f"- direct MOVX copy edges: {len(report['copy_edges'])}",
        f"- write idioms touching target addresses: {len(report['target_writes'])}",
        f"- compare idioms touching target addresses: {len(report['target_compares'])}",
        f"- FIFO bursts from `0x47b1`: {len(report['fifo_bursts'])}",
        "",
        "## Target DPTR References",
        "",
        "| addr | observations | chunks | sample slots |",
        "|---:|---:|---:|---|",
    ]
    for row in report["target_dptr_refs"]:
        slots = ", ".join(f"`+0x{off:04x}`" for off in row["sample_offsets"][:8]) or "-"
        lines.append(
            f"| `0x{row['addr']:04x}` | {row['observations']} | {row['chunk_count']} | {slots} |"
        )

    lines += [
        "",
        "## MOVX Copy Edges",
        "",
        "| src | dst | kind | count | sample offsets |",
        "|---:|---:|---|---:|---|",
    ]
    for row in report["copy_edges"][:80]:
        offsets = ", ".join(f"`+0x{off:04x}`" for off in row["sample_offsets"][:8])
        lines.append(
            f"| `0x{row['src']:04x}` | `0x{row['dst']:04x}` | {row['kind']} | "
            f"{row['count']} | {offsets} |"
        )

    lines += [
        "",
        "## FIFO Bursts From 0x47b1",
        "",
        "| dst range | bytes | observations | sample |",
        "|---|---:|---:|---|",
    ]
    for row in report["fifo_bursts"][:32]:
        lines.append(
            f"| `0x{row['dst_start']:04x}..0x{row['dst_end']:04x}` | {row['count']} | "
            f"{row['observations']} | `{row['sample_capture']}` `+0x{row['sample_offset']:04x}` |"
        )

    lines += [
        "",
        "## Packet Shadow To Controller Edges",
        "",
        "| src | dst | kind | count | sample offsets |",
        "|---:|---:|---|---:|---|",
    ]
    for row in report["controller_edges"][:80]:
        offsets = ", ".join(f"`+0x{off:04x}`" for off in row["sample_offsets"][:8])
        lines.append(
            f"| `0x{row['src']:04x}` | `0x{row['dst']:04x}` | {row['kind']} | "
            f"{row['count']} | {offsets} |"
        )

    lines += [
        "",
        "## Target Writes",
        "",
        "| addr | kind | value | count | sample offsets |",
        "|---:|---|---:|---:|---|",
    ]
    for row in report["target_writes"][:80]:
        offsets = ", ".join(f"`+0x{off:04x}`" for off in row["sample_offsets"][:8])
        lines.append(
            f"| `0x{row['addr']:04x}` | {row['kind']} | `0x{row['value']:02x}` | "
            f"{row['count']} | {offsets} |"
        )

    lines += [
        "",
        "## Target Compares",
        "",
        "| addr | kind | value | branch | count | sample offsets |",
        "|---:|---|---:|---|---:|---|",
    ]
    for row in report["target_compares"][:80]:
        offsets = ", ".join(f"`+0x{off:04x}`" for off in row["sample_offsets"][:8])
        lines.append(
            f"| `0x{row['addr']:04x}` | {row['kind']} | `0x{row['value']:02x}` | "
            f"{row['branch']} | {row['count']} | {offsets} |"
        )

    lines += [
        "",
        "## High-Value Snippets",
        "",
        "| label | capture | offset | bytes |",
        "|---|---|---:|---|",
    ]
    for row in report["snippets"][:40]:
        lines.append(
            f"| {row['label']} | `{row['capture']}` | `+0x{row['offset']:04x}` | `{row['hex']}` |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- The FIFO intake is visible in two pieces: a prefix sequence clears",
        "  `0x47b0` and reads `0x47b1` into `0x8a49..0x8a4b`, then later bursts",
        "  fill the rest of the shadow through `0x8a54`. Because this public",
        "  window is paged/rotating, individual captures expose slightly different",
        "  slices of that burst.",
        "- `xdata[0x8a49]` is compared against command-like values including",
        "  `0x28`, `0xa8`, and `0xbe` immediately after the FIFO burst. This",
        "  makes it the likely opcode/selector byte for the normal packet shadow.",
        "- The strongest packet-to-controller bridge edges are now explicit:",
        "  shadow bytes feed `0x4011..0x4013`, `0x4091`, `0x4095`, `0x4099`,",
        "  and `0x40b7`, while controller setup bytes are mirrored back into",
        "  `0x8ade/0x8aeb/0x8aec`. That is the next static path to reverse.",
    ]
    return "\n".join(lines) + "\n"


def aggregate(run_dirs: list[Path], targets: set[int]) -> dict[str, Any]:
    windows = load_windows(run_dirs)
    dptr_counter: Counter[int] = Counter()
    dptr_chunks: dict[int, set[str]] = defaultdict(set)
    dptr_offsets: dict[int, set[int]] = defaultdict(set)
    copy_counter: Counter[tuple[int, int, str]] = Counter()
    copy_offsets: dict[tuple[int, int, str], set[int]] = defaultdict(set)
    write_counter: Counter[tuple[int, str, int]] = Counter()
    write_offsets: dict[tuple[int, str, int], set[int]] = defaultdict(set)
    compare_counter: Counter[tuple[int, str, int, str]] = Counter()
    compare_offsets: dict[tuple[int, str, int, str], set[int]] = defaultdict(set)
    burst_counter: Counter[tuple[int, int, int]] = Counter()
    burst_samples: dict[tuple[int, int, int], dict[str, Any]] = {}
    snippets: dict[str, dict[str, Any]] = {}

    for win in windows:
        data = win["data"]
        capture_label = f"{win['run']}/{win['capture']}"
        refs = scan_dptr_refs(data)
        copies = scan_direct_movx_copies(data) + scan_reg_movx_copies(data)
        writes = scan_writes(data)
        compares = scan_compares(data)
        for ref in refs:
            addr = ref["addr"]
            if addr not in targets:
                continue
            chunk_start = (ref["offset"] // 0x40) * 0x40
            chunk = data[chunk_start : chunk_start + 0x40]
            digest = sha256_hex(chunk)
            dptr_counter[addr] += 1
            dptr_chunks[addr].add(digest)
            dptr_offsets[addr].add(chunk_start)
        for copy in copies:
            src = int(copy["src"])
            dst = int(copy["dst"])
            key = (src, dst, str(copy["kind"]))
            if src in targets or dst in targets or 0x8A49 <= src <= 0x8A54 or 0x8A49 <= dst <= 0x8A54:
                copy_counter[key] += 1
                copy_offsets[key].add((int(copy["offset"]) // 0x40) * 0x40)
                controller_bridge = (
                    src in CONTROLLER_REGS
                    or dst in CONTROLLER_REGS
                    or (0x8AC0 <= src <= 0x8AFF and dst in CONTROLLER_REGS)
                    or (0x8A49 <= src <= 0x8A54 and dst in CONTROLLER_REGS)
                )
                if (
                    src == 0x47B1
                    or dst in range(0x8A49, 0x8A55)
                    or controller_bridge
                ) and len(snippets) < 120:
                    start, text = snippet(data, int(copy["offset"]))
                    sid = f"copy-{src:04x}-{dst:04x}-{start:04x}"
                    snippets.setdefault(
                        sid,
                        {
                            "label": f"copy 0x{src:04x}->0x{dst:04x}",
                            "capture": capture_label,
                            "offset": start,
                            "hex": text,
                        },
                    )
        for write in writes:
            addr = int(write["addr"])
            if addr not in targets and not 0x8A49 <= addr <= 0x8A54:
                continue
            key = (addr, str(write["kind"]), int(write["value"]))
            write_counter[key] += 1
            write_offsets[key].add((int(write["offset"]) // 0x40) * 0x40)
        for compare in compares:
            addr = int(compare["addr"])
            if addr not in targets and not 0x8A49 <= addr <= 0x8A54:
                continue
            key = (addr, str(compare["kind"]), int(compare["value"]), str(compare["branch"]))
            compare_counter[key] += 1
            compare_offsets[key].add((int(compare["offset"]) // 0x40) * 0x40)
            if len(snippets) < 80:
                start, text = snippet(data, int(compare["offset"]))
                sid = f"compare-{addr:04x}-{compare['value']:02x}-{start:04x}"
                snippets.setdefault(
                    sid,
                    {
                        "label": f"compare 0x{addr:04x} with 0x{int(compare['value']):02x}",
                        "capture": capture_label,
                        "offset": start,
                        "hex": text,
                    },
                )
        for burst in find_fifo_bursts(copies):
            key = (burst["dst_start"], burst["dst_end"], burst["count"])
            burst_counter[key] += 1
            burst_samples.setdefault(
                key,
                {
                    "sample_capture": capture_label,
                    "sample_offset": burst["offset"],
                },
            )

    target_rows = [
        {
            "addr": addr,
            "observations": count,
            "chunk_count": len(dptr_chunks[addr]),
            "sample_offsets": sorted(dptr_offsets[addr]),
        }
        for addr, count in dptr_counter.items()
    ]
    target_rows.sort(key=lambda row: (-row["observations"], row["addr"]))

    copy_rows = [
        {
            "src": src,
            "dst": dst,
            "kind": kind,
            "count": count,
            "sample_offsets": sorted(copy_offsets[(src, dst, kind)]),
        }
        for (src, dst, kind), count in copy_counter.items()
    ]
    copy_rows.sort(key=lambda row: (-row["count"], row["src"], row["dst"], row["kind"]))

    write_rows = [
        {
            "addr": addr,
            "kind": kind,
            "value": value,
            "count": count,
            "sample_offsets": sorted(write_offsets[(addr, kind, value)]),
        }
        for (addr, kind, value), count in write_counter.items()
    ]
    write_rows.sort(key=lambda row: (-row["count"], row["addr"], row["kind"], row["value"]))

    compare_rows = [
        {
            "addr": addr,
            "kind": kind,
            "value": value,
            "branch": branch,
            "count": count,
            "sample_offsets": sorted(compare_offsets[(addr, kind, value, branch)]),
        }
        for (addr, kind, value, branch), count in compare_counter.items()
    ]
    compare_rows.sort(key=lambda row: (-row["count"], row["addr"], row["value"], row["kind"]))

    burst_rows = []
    for (dst_start, dst_end, count), observations in burst_counter.items():
        sample = burst_samples[(dst_start, dst_end, count)]
        burst_rows.append(
            {
                "dst_start": dst_start,
                "dst_end": dst_end,
                "count": count,
                "observations": observations,
                **sample,
            }
        )
    burst_rows.sort(key=lambda row: (-row["observations"], row["dst_start"], row["dst_end"]))

    controller_rows = [
        row
        for row in copy_rows
        if row["src"] in CONTROLLER_REGS
        or row["dst"] in CONTROLLER_REGS
        or (0x8A49 <= row["src"] <= 0x8A54 and row["dst"] in CONTROLLER_REGS)
        or (0x8AC0 <= row["src"] <= 0x8AFF and row["dst"] in CONTROLLER_REGS)
    ]
    controller_rows.sort(key=lambda row: (-row["count"], row["src"], row["dst"], row["kind"]))

    return {
        "capture_count": len(windows),
        "targets": sorted(targets),
        "target_dptr_observations": sum(dptr_counter.values()),
        "unique_target_chunks": len(set().union(*dptr_chunks.values())) if dptr_chunks else 0,
        "target_dptr_refs": target_rows,
        "copy_edges": copy_rows,
        "controller_edges": controller_rows,
        "target_writes": write_rows,
        "target_compares": compare_rows,
        "fifo_bursts": burst_rows,
        "snippets": list(snippets.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--target", action="append", type=parse_int, default=[])
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    targets = set(DEFAULT_TARGETS)
    targets.update(args.target)
    report = aggregate(args.run_dirs, targets)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))


if __name__ == "__main__":
    main()
