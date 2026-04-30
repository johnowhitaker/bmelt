#!/usr/bin/env python3
"""Build a compact cross-reference map for LiteOn 8051 XDATA registers.

The Ghidra C export names external-memory objects as DAT_EXTMEM_xxxx.  This
script is intentionally heuristic: it keeps the report small enough to guide
manual reverse engineering, not to prove a complete data-flow model.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


REF_RE = re.compile(r"DAT_EXTMEM_([0-9a-fA-F]{4})")
FUNC_DEF_RE = re.compile(
    r"^\s*(?:[A-Za-z_][A-Za-z0-9_\s\*]+?)\s+(FUN_CODE_[0-9a-fA-F]{4})\s*\([^;]*\)\s*$"
)
ASSIGN_RE = re.compile(r"^\s*DAT_EXTMEM_([0-9a-fA-F]{4})\s*=")


DEFAULT_RANGES = (
    (0x4000, 0x40FF),
    (0x4700, 0x48FF),
    (0x5900, 0x5AFF),
    (0x8100, 0x82FF),
)

INTERESTING_ADDRS = {
    0x4023,
    0x4700,
    0x4703,
    0x4704,
    0x4748,
    0x4773,
    0x4774,
    0x4780,
    0x4814,
    0x4815,
    0x4819,
    0x4821,
    0x4822,
    0x482B,
    0x482C,
    0x482D,
    0x4844,
    0x4862,
    0x4863,
    0x48A0,
    0x48D0,
    0x48D1,
    0x48D5,
    0x48F7,
    0x8221,
}


@dataclass
class Ref:
    line_no: int
    function: str
    kind: str
    text: str


@dataclass
class Entry:
    addr: int
    refs: list[Ref] = field(default_factory=list)
    constants_written: set[int] = field(default_factory=set)
    masks: set[str] = field(default_factory=set)
    currentboot_value: int | None = None

    @property
    def kinds(self) -> set[str]:
        return {ref.kind for ref in self.refs}


def parse_int_auto(text: str) -> int:
    return int(text, 0)


def parse_ranges(values: list[str]) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for value in values:
        if ":" in value:
            start_s, end_s = value.split(":", 1)
        elif "-" in value:
            start_s, end_s = value.split("-", 1)
        else:
            start_s = end_s = value
        start = parse_int_auto(start_s)
        end = parse_int_auto(end_s)
        if end < start:
            raise ValueError(f"invalid descending range: {value}")
        ranges.append((start, end))
    return ranges


def in_ranges(addr: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= addr <= end for start, end in ranges)


def classify_line(line: str, addr_hex: str) -> str:
    stripped = line.strip()
    name = f"DAT_EXTMEM_{addr_hex.lower()}"
    name_upper = f"DAT_EXTMEM_{addr_hex.upper()}"
    target = ASSIGN_RE.match(stripped)
    if target and int(target.group(1), 16) == int(addr_hex, 16):
        rhs = stripped.split("=", 1)[1]
        if name in rhs or name_upper in rhs:
            return "read-modify-write"
        return "write"
    if stripped.startswith("if ") or stripped.startswith("if("):
        return "test"
    if stripped.startswith("while") or stripped.startswith("} while") or stripped.startswith("do "):
        return "wait/test"
    if "=" in stripped:
        lhs, rhs = stripped.split("=", 1)
        if name in rhs or name_upper in rhs:
            return "read"
        if name in lhs or name_upper in lhs:
            return "write"
    return "read"


def extract_constant_write(line: str, addr: int) -> int | None:
    match = ASSIGN_RE.match(line)
    if not match or int(match.group(1), 16) != addr:
        return None
    rhs = line.split("=", 1)[1].strip().rstrip(";")
    const_match = re.fullmatch(r"(0x[0-9a-fA-F]+|\d+)", rhs)
    if const_match:
        return int(const_match.group(1), 0)
    return None


def extract_masks(line: str) -> list[str]:
    masks: list[str] = []
    for op, value in re.findall(r"([&|^])\s*(0x[0-9a-fA-F]+|\d+)", line):
        masks.append(f"{op}{value}")
    return masks


def load_dump_values(path: Path | None) -> bytes | None:
    if path is None or not path.exists():
        return None
    data = path.read_bytes()
    if len(data) < 0x10000:
        raise ValueError(f"XDATA dump too short: {path} ({len(data)} bytes)")
    return data


def build_map(c_path: Path, ranges: list[tuple[int, int]], dump: bytes | None) -> dict[int, Entry]:
    entries: dict[int, Entry] = defaultdict(lambda: Entry(addr=-1))
    current_function: str | None = None
    lines = c_path.read_text(errors="replace").splitlines()

    for line_no, line in enumerate(lines, 1):
        func_match = FUNC_DEF_RE.match(line)
        if func_match:
            current_function = func_match.group(1)

        refs = sorted(set(REF_RE.findall(line)))
        if not refs:
            continue
        if current_function is None:
            continue

        for addr_hex in refs:
            addr = int(addr_hex, 16)
            if not in_ranges(addr, ranges):
                continue
            entry = entries[addr]
            entry.addr = addr
            kind = classify_line(line, addr_hex)
            entry.refs.append(
                Ref(
                    line_no=line_no,
                    function=current_function,
                    kind=kind,
                    text=line.strip(),
                )
            )
            const = extract_constant_write(line, addr)
            if const is not None:
                entry.constants_written.add(const & 0xFF)
            for mask in extract_masks(line):
                entry.masks.add(mask)
            if dump is not None:
                entry.currentboot_value = dump[addr]

    return dict(sorted(entries.items()))


def summarize_entry(entry: Entry) -> str:
    kind_order = ["write", "read-modify-write", "read", "test", "wait/test"]
    kinds = ", ".join(kind for kind in kind_order if kind in entry.kinds)
    if not kinds:
        kinds = ", ".join(sorted(entry.kinds))
    funcs = sorted({ref.function for ref in entry.refs})
    parts = [f"{len(entry.refs)} refs", kinds, f"{len(funcs)} funcs"]
    if entry.currentboot_value is not None:
        parts.append(f"cur=0x{entry.currentboot_value:02x}")
    if entry.constants_written:
        consts = ",".join(f"0x{x:02x}" for x in sorted(entry.constants_written))
        parts.append(f"consts={consts}")
    if entry.masks:
        parts.append("masks=" + ",".join(sorted(entry.masks)))
    return "; ".join(parts)


def likely_role(addr: int, entry: Entry) -> str:
    texts = "\n".join(ref.text for ref in entry.refs)
    if addr in (0x4000, 0x4091, 0x4092, 0x4093, 0x4095, 0x4096, 0x4097, 0x4098):
        return "controller gateway/FIFO"
    if addr in (0x47B0, 0x47B1):
        return "packet FIFO/window"
    if addr in (0x818A, 0x818B, 0x818C, 0x818D, 0x818E, 0x818F, 0x8190, 0x8191, 0x8192, 0x8193, 0x8194, 0x8195):
        return "CDB/packet shadow"
    if "DAT_EXTMEM_482b" in texts or addr in (0x482B, 0x482C, 0x482D):
        return "small handshake/status port"
    if addr == 0x4814:
        return "front-button/status byte candidate"
    if addr in (0x4748, 0x4780, 0x4773, 0x4774, 0x4700, 0x4704):
        return "controller-path/status candidate"
    if addr in (0x4860, 0x4861, 0x4862, 0x4863, 0x4864, 0x4865, 0x4867, 0x486A, 0x486B):
        return "hardware init/config cluster"
    if addr in (0x5904, 0x5905, 0x59C0, 0x5906, 0x592A, 0x59F0, 0x59F1, 0x5A00, 0x5A01, 0x5A24, 0x5A31, 0x5954):
        return "helper-init hardware cluster"
    if {"write", "read-modify-write"} & entry.kinds and not ({"read", "test", "wait/test"} & entry.kinds):
        return "mostly-written config/state"
    if {"test", "wait/test"} & entry.kinds and not ({"write", "read-modify-write"} & entry.kinds):
        return "mostly-read status"
    return "mixed/unknown"


def write_json(path: Path, entries: dict[int, Entry]) -> None:
    serializable = []
    for addr, entry in entries.items():
        serializable.append(
            {
                "addr": f"0x{addr:04x}",
                "currentboot_value": None
                if entry.currentboot_value is None
                else f"0x{entry.currentboot_value:02x}",
                "summary": summarize_entry(entry),
                "likely_role": likely_role(addr, entry),
                "constants_written": [f"0x{x:02x}" for x in sorted(entry.constants_written)],
                "masks": sorted(entry.masks),
                "refs": [
                    {
                        "line": ref.line_no,
                        "function": ref.function,
                        "kind": ref.kind,
                        "text": ref.text,
                    }
                    for ref in entry.refs
                ],
            }
        )
    path.write_text(json.dumps(serializable, indent=2) + "\n")


def write_markdown(path: Path, entries: dict[int, Entry], c_path: Path, dump_path: Path | None) -> None:
    lines: list[str] = []
    lines.append("# LiteOn 8051 XDATA Register Cross-Reference")
    lines.append("")
    lines.append("Generated from the Ghidra C export. This is a heuristic map for triage,")
    lines.append("not a complete proof of register semantics.")
    lines.append("")
    lines.append(f"- source: `{c_path}`")
    if dump_path is not None:
        lines.append(f"- currentboot values: `{dump_path}`")
    lines.append("")

    lines.append("## High-Value Addresses")
    lines.append("")
    lines.append("| address | summary | likely role | notable refs |")
    lines.append("|---|---|---|---|")
    for addr in sorted(entries):
        if addr not in INTERESTING_ADDRS:
            continue
        entry = entries[addr]
        refs = "; ".join(
            f"{ref.function}:{ref.line_no} {ref.kind}" for ref in entry.refs[:4]
        )
        if len(entry.refs) > 4:
            refs += f"; +{len(entry.refs) - 4} more"
        lines.append(
            f"| `0x{addr:04x}` | {summarize_entry(entry)} | {likely_role(addr, entry)} | {refs} |"
        )
    lines.append("")

    lines.append("## Dense Address Summary")
    lines.append("")
    lines.append("| address | summary | likely role |")
    lines.append("|---|---|---|")
    for addr, entry in entries.items():
        lines.append(f"| `0x{addr:04x}` | {summarize_entry(entry)} | {likely_role(addr, entry)} |")
    lines.append("")

    lines.append("## Function Clusters")
    lines.append("")
    by_func: dict[str, list[tuple[int, Ref]]] = defaultdict(list)
    for addr, entry in entries.items():
        for ref in entry.refs:
            by_func[ref.function].append((addr, ref))
    for func in sorted(by_func):
        refs = by_func[func]
        if len(refs) < 4 and func not in {"FUN_CODE_48e7", "FUN_CODE_5a68", "FUN_CODE_6048", "FUN_CODE_6087", "FUN_CODE_60c4", "FUN_CODE_63cb"}:
            continue
        addrs = ", ".join(f"`0x{addr:04x}`" for addr in sorted({addr for addr, _ in refs}))
        lines.append(f"### `{func}`")
        lines.append("")
        lines.append(addrs)
        lines.append("")
        for addr, ref in refs[:24]:
            lines.append(f"- `{ref.line_no}` `{ref.kind}` `0x{addr:04x}`: `{ref.text}`")
        if len(refs) > 24:
            lines.append(f"- ... {len(refs) - 24} more refs")
        lines.append("")

    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--c-file", type=Path, default=Path("analysis/8051/ldm58051_c.c"))
    parser.add_argument("--xdata-dump", type=Path)
    parser.add_argument("--range", dest="ranges", action="append", default=[], help="address range, e.g. 0x4700:0x48ff")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()

    ranges = parse_ranges(args.ranges) if args.ranges else list(DEFAULT_RANGES)
    dump = load_dump_values(args.xdata_dump)
    entries = build_map(args.c_file, ranges, dump)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.json_out, entries)
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        write_markdown(args.md_out, entries, args.c_file, args.xdata_dump)
    if not args.json_out and not args.md_out:
        for addr, entry in entries.items():
            print(f"0x{addr:04x}: {summarize_entry(entry)} [{likely_role(addr, entry)}]")


if __name__ == "__main__":
    main()
