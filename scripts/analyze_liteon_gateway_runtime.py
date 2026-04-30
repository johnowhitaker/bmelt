#!/usr/bin/env python3
"""Offline analysis for the LiteOn currentboot controller-gateway dump.

The input is a 64 KiB blob read through the currentboot gateway hook from
controller address 0x070000.  This script deliberately does not talk to an
optical drive.  It builds a compact, repeatable report: page shape, strings,
direct 8051 MOV-DPTR references, heuristic call/jump targets, and exact overlaps
against the known LD5M F0 image / 8051 resident / profile-tail helper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_GATEWAY = (
    ROOT / "references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin"
)
DEFAULT_F0 = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_8051 = ROOT / "analysis/8051/ldm58051.bin"
DEFAULT_HELPER = ROOT / "references/firmware/extracted/liteon-official-profile-tail-ef130045-plain.bin"
DEFAULT_OUT_MD = ROOT / "analysis/8051/currentboot-gateway-070000-analysis.md"
DEFAULT_OUT_JSON = ROOT / "analysis/8051/currentboot-gateway-070000-analysis.json"

GATEWAY_BASE = 0x070000

INTERESTING_RANGES = (
    (0x4000, 0x40FF, "controller gateway/status"),
    (0x4700, 0x48FF, "controller/front-panel/status fabric"),
    (0x5900, 0x5AFF, "servo/mechanics-looking hardware cluster"),
    (0x8000, 0x82FF, "shared command/status buffers"),
)

SERVO_REGS = {
    0x5904,
    0x5905,
    0x5906,
    0x5907,
    0x590B,
    0x592A,
    0x592B,
    0x5945,
    0x594B,
    0x5954,
    0x5997,
    0x599E,
    0x59A4,
    0x59C0,
    0x59F0,
    0x59F1,
    0x5A00,
    0x5A01,
    0x5A24,
    0x5A31,
}


@dataclass(frozen=True)
class Match:
    length: int
    gateway_offset: int
    other_offset: int
    sample_hex: str

    def as_dict(self) -> dict[str, object]:
        return {
            "length": self.length,
            "gateway_offset": self.gateway_offset,
            "gateway_controller_address": GATEWAY_BASE + self.gateway_offset,
            "other_offset": self.other_offset,
            "sample_hex": self.sample_hex,
        }


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def ascii_preview(data: bytes) -> str:
    return "".join(chr(b) if 32 <= b < 127 else "." for b in data)


def find_strings(data: bytes, min_len: int = 4) -> list[dict[str, object]]:
    strings: list[dict[str, object]] = []
    i = 0
    while i < len(data):
        if 32 <= data[i] < 127:
            start = i
            while i < len(data) and 32 <= data[i] < 127:
                i += 1
            if i - start >= min_len:
                strings.append(
                    {
                        "offset": start,
                        "controller_address": GATEWAY_BASE + start,
                        "text": data[start:i].decode("ascii", errors="replace"),
                    }
                )
        else:
            i += 1
    return strings


def page_stats(data: bytes, page_size: int = 0x1000) -> list[dict[str, object]]:
    stats: list[dict[str, object]] = []
    for offset in range(0, len(data), page_size):
        page = data[offset : offset + page_size]
        zeros = page.count(0)
        ffs = page.count(0xFF)
        stats.append(
            {
                "offset": offset,
                "controller_address": GATEWAY_BASE + offset,
                "size": len(page),
                "zeros": zeros,
                "ffs": ffs,
                "nonzero": len(page) - zeros,
                "nonff": len(page) - ffs,
                "entropy": round(entropy(page), 4),
            }
        )
    return stats


def long_uniform_runs(data: bytes, min_len: int = 0x100) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    i = 0
    while i < len(data):
        if data[i] not in (0, 0xFF):
            i += 1
            continue
        value = data[i]
        start = i
        while i < len(data) and data[i] == value:
            i += 1
        if i - start >= min_len:
            runs.append(
                {
                    "value": value,
                    "offset": start,
                    "end": i,
                    "controller_address": GATEWAY_BASE + start,
                    "length": i - start,
                }
            )
    return runs


def in_interesting_range(addr: int) -> str | None:
    for start, end, label in INTERESTING_RANGES:
        if start <= addr <= end:
            return label
    return None


def dptr_refs(data: bytes) -> list[dict[str, object]]:
    refs: dict[int, list[int]] = defaultdict(list)
    for offset in range(0, len(data) - 2):
        if data[offset] == 0x90:
            addr = (data[offset + 1] << 8) | data[offset + 2]
            refs[addr].append(offset)
    rows: list[dict[str, object]] = []
    for addr, offsets in sorted(refs.items()):
        label = in_interesting_range(addr)
        rows.append(
            {
                "addr": addr,
                "count": len(offsets),
                "offsets": offsets[:12],
                "controller_addresses": [GATEWAY_BASE + off for off in offsets[:12]],
                "label": label,
                "servo_candidate": addr in SERVO_REGS,
            }
        )
    return rows


def branch_target_hist(data: bytes, opcode: int) -> list[dict[str, object]]:
    targets: dict[int, list[int]] = defaultdict(list)
    for offset in range(0, len(data) - 2):
        if data[offset] == opcode:
            target = (data[offset + 1] << 8) | data[offset + 2]
            targets[target].append(offset)
    rows = [
        {
            "target": target,
            "count": len(offsets),
            "offsets": offsets[:10],
            "target_zero_page": 0x02EA <= target < 0x4000,
        }
        for target, offsets in targets.items()
    ]
    rows.sort(key=lambda row: (-int(row["count"]), int(row["target"])))
    return rows


def is_low_information(chunk: bytes) -> bool:
    if not chunk:
        return True
    if all(byte == 0 for byte in chunk) or all(byte == 0xFF for byte in chunk):
        return True
    counts = Counter(chunk)
    most_common = counts.most_common(1)[0][1]
    return most_common / len(chunk) > 0.85


def exact_matches(gateway: bytes, other: bytes, *, k: int = 16, min_len: int = 0x20) -> list[Match]:
    index: dict[bytes, list[int]] = defaultdict(list)
    for offset in range(0, len(other) - k + 1):
        chunk = other[offset : offset + k]
        if is_low_information(chunk):
            continue
        index[chunk].append(offset)

    seen: set[tuple[int, int, int]] = set()
    matches: list[Match] = []
    for gateway_offset in range(0, len(gateway) - k + 1):
        chunk = gateway[gateway_offset : gateway_offset + k]
        if is_low_information(chunk):
            continue
        for other_offset in index.get(chunk, [])[:32]:
            gi = gateway_offset
            oi = other_offset
            while gi > 0 and oi > 0 and gateway[gi - 1] == other[oi - 1]:
                gi -= 1
                oi -= 1
            ge = gateway_offset + k
            oe = other_offset + k
            while ge < len(gateway) and oe < len(other) and gateway[ge] == other[oe]:
                ge += 1
                oe += 1
            length = ge - gi
            if length < min_len or is_low_information(gateway[gi:ge]):
                continue
            key = (gi, oi, length)
            if key in seen:
                continue
            seen.add(key)
            matches.append(Match(length, gi, oi, gateway[gi : min(ge, gi + 16)].hex()))

    matches.sort(key=lambda match: (-match.length, match.gateway_offset, match.other_offset))
    filtered: list[Match] = []
    for match in matches:
        contained = False
        for existing in filtered:
            if (
                existing.gateway_offset <= match.gateway_offset
                and match.gateway_offset + match.length <= existing.gateway_offset + existing.length
                and existing.other_offset <= match.other_offset
                and match.other_offset + match.length <= existing.other_offset + existing.length
            ):
                contained = True
                break
        if not contained:
            filtered.append(match)
        if len(filtered) >= 40:
            break
    return filtered


def find_all(data: bytes, needle: bytes) -> list[int]:
    hits: list[int] = []
    offset = data.find(needle)
    while offset >= 0:
        hits.append(offset)
        offset = data.find(needle, offset + 1)
    return hits


def cdd_annotations(gateway: bytes, f0: bytes) -> dict[str, object]:
    starts = find_all(f0, b"CDD\t")
    if len(starts) < 2:
        return {"error": "expected at least two CDD streams in F0"}

    cdd1, cdd2 = starts[:2]
    header = f0[cdd1 : cdd1 + 0x20]
    directory_end = int.from_bytes(header[0x0A:0x0D], "big")
    cdd1_prefix = f0[cdd1 + 0x20 : directory_end]
    cdd2_duplicate = f0[cdd2 + 0x20 : cdd2 + 0x1A0]

    cdd1_prefix_hits = find_all(gateway, cdd1_prefix)
    cdd2_duplicate_hits = find_all(gateway, cdd2_duplicate)
    header_hits = find_all(gateway, header)

    return {
        "cdd1_start": cdd1,
        "cdd2_start": cdd2,
        "cdd1_header_hex": header.hex(),
        "cdd1_directory_end_abs": directory_end,
        "cdd1_post_header_prefix_len": len(cdd1_prefix),
        "cdd1_post_header_prefix_gateway_hits": cdd1_prefix_hits,
        "cdd2_duplicate_prefix_len": len(cdd2_duplicate),
        "cdd2_duplicate_prefix_gateway_hits": cdd2_duplicate_hits,
        "cdd_header_gateway_hits": header_hits,
    }


def load_optional(path: Path) -> bytes | None:
    if path.exists():
        return path.read_bytes()
    return None


def build_analysis(args: argparse.Namespace) -> dict[str, object]:
    gateway = args.gateway.read_bytes()
    if len(gateway) != 0x10000:
        raise ValueError(f"gateway dump must be 0x10000 bytes, got 0x{len(gateway):x}")

    analysis: dict[str, object] = {
        "gateway": {
            "path": str(args.gateway),
            "base": GATEWAY_BASE,
            "size": len(gateway),
            "sha256": sha256_hex(gateway),
        },
        "page_stats": page_stats(gateway),
        "long_uniform_runs": long_uniform_runs(gateway),
        "strings": find_strings(gateway),
        "dptr_refs": dptr_refs(gateway),
        "lcall_targets": branch_target_hist(gateway, 0x12)[:80],
        "ljmp_targets": branch_target_hist(gateway, 0x02)[:80],
        "overlaps": {},
    }

    comparisons: list[tuple[str, Path, int, int]] = [
        ("ld5m_f0", args.f0, 16, 0x20),
        ("ldm58051_resident", args.resident_8051, 16, 0x20),
        ("profile_tail_helper", args.helper, 16, 0x20),
    ]
    for name, path, k, min_len in comparisons:
        other = load_optional(path)
        if other is None:
            continue
        analysis["overlaps"][name] = {
            "path": str(path),
            "size": len(other),
            "sha256": sha256_hex(other),
            "matches": [match.as_dict() for match in exact_matches(gateway, other, k=k, min_len=min_len)],
        }

    f0 = load_optional(args.f0)
    if f0 is not None:
        analysis["cdd_annotations"] = cdd_annotations(gateway, f0)

    return analysis


def hex_addr(value: int, width: int = 4) -> str:
    return f"0x{value:0{width}x}"


def render_md(analysis: dict[str, object]) -> str:
    gateway = analysis["gateway"]
    lines: list[str] = [
        "# Currentboot Gateway 0x070000 Analysis",
        "",
        "Date: 2026-04-30",
        "",
        "This is an offline analysis of the 64 KiB controller-gateway dump read",
        "from Linux drive #1 while the drive was in currentboot. No live drive",
        "access is performed by this report generator.",
        "",
        "## Artifact",
        "",
        "```text",
        f"path   {gateway['path']}",
        f"base   {hex_addr(int(gateway['base']), 6)}",
        f"size   0x{int(gateway['size']):x}",
        f"sha256 {gateway['sha256']}",
        "```",
        "",
        "## Main Read",
        "",
        "This 64 KiB window is mixed material, not a plain reset-vector firmware",
        "image. The low pages contain compact tables/records and `PBDS` markers,",
        "`0x02ea..0x3fff` is zero, `0x4000..0x5fff` is string/profile/table-heavy,",
        "and `0x6000..0xffff` contains substantial 8051-like code mixed with tables.",
        "",
        "The most important new finding is that the tail of this gateway window",
        "contains exact LD5M CDD bytes. In particular, the dump at gateway offset",
        "`0xf000` mirrors F0 bytes starting at `0x704c`, the first post-header",
        "CDD1 directory/table material. This is not decoded servo code; it is the",
        "sealed/encoded CDD container material visible in F0. The same window also",
        "contains the expected duplicate of the CDD2 prefix and repeated CDD headers.",
        "",
        "So the gateway is a better live oracle than the earlier zero `0x184000`",
        "guess, but it is not yet the decoded `0x184000..0x1b3fff` runtime payload.",
        "",
    ]

    lines += ["## Page Shape", "", "| page | nonzero | non-ff | entropy | note |", "|---:|---:|---:|---:|---|"]
    for row in analysis["page_stats"]:
        note = ""
        if row["zeros"] == row["size"]:
            note = "all zero"
        elif row["ffs"] == row["size"]:
            note = "all ff"
        elif int(row["offset"]) < 0x4000:
            note = "low table/record area"
        elif int(row["offset"]) < 0x6000:
            note = "profile/string/table area"
        elif int(row["offset"]) >= 0xF000:
            note = "CDD mirror/header tail"
        else:
            note = "code-like/table mixed"
        lines.append(
            f"| `{hex_addr(int(row['offset']))}` | {row['nonzero']} | {row['nonff']} | {row['entropy']:.4f} | {note} |"
        )

    lines += ["", "Long zero/ff runs:", "", "```text"]
    for run in analysis["long_uniform_runs"]:
        kind = "00" if run["value"] == 0 else "ff"
        lines.append(
            f"{kind} {hex_addr(int(run['offset']))}..{hex_addr(int(run['end']) - 1)} len=0x{int(run['length']):x}"
        )
    lines += ["```", ""]

    cdd = analysis.get("cdd_annotations", {})
    if cdd and "error" not in cdd:
        lines += [
            "## CDD Overlap",
            "",
            "| item | F0 source | gateway hit(s) | length |",
            "|---|---:|---:|---:|",
            (
                f"| CDD1 post-header prefix | `0x{int(cdd['cdd1_start']) + 0x20:05x}` | "
                f"`{', '.join(hex_addr(x) for x in cdd['cdd1_post_header_prefix_gateway_hits'])}` | "
                f"`0x{int(cdd['cdd1_post_header_prefix_len']):x}` |"
            ),
            (
                f"| CDD2 duplicate prefix | `0x{int(cdd['cdd2_start']) + 0x20:05x}` | "
                f"`{', '.join(hex_addr(x) for x in cdd['cdd2_duplicate_prefix_gateway_hits'])}` | "
                f"`0x{int(cdd['cdd2_duplicate_prefix_len']):x}` |"
            ),
            (
                f"| CDD header | `0x{int(cdd['cdd1_start']):05x}` | "
                f"`{', '.join(hex_addr(x) for x in cdd['cdd_header_gateway_hits'])}` | `0x20` |"
            ),
            "",
            "The `0xf000` CDD1 hit runs exactly through F0 `0x704c..0x7deb`.",
            "The `0xfc20` CDD2-prefix hit is contained inside that CDD1 region,",
            "matching the known CDD2-prefix duplicate inside CDD1. The repeated",
            "headers at `0xff00` and `0xff80` look like controller-side CDD work",
            "slots or copied descriptors, not decoded output.",
            "",
        ]

    lines += [
        "## Exact Overlaps",
        "",
        "Nontrivial exact byte matches against known artifacts:",
        "",
    ]
    overlaps = analysis["overlaps"]
    for name in ("profile_tail_helper", "ldm58051_resident", "ld5m_f0"):
        if name not in overlaps:
            continue
        section = overlaps[name]
        lines += [f"### {name}", "", "| len | gateway | other | sample |", "|---:|---:|---:|---|"]
        for match in section["matches"][:12]:
            width = 6 if name == "ld5m_f0" else 4
            lines.append(
                f"| `0x{int(match['length']):x}` | `{hex_addr(int(match['gateway_offset']))}` | "
                f"`0x{int(match['other_offset']):0{width}x}` | `{match['sample_hex']}` |"
            )
        lines.append("")

    interesting_refs = [
        row
        for row in analysis["dptr_refs"]
        if row["label"] is not None or row["servo_candidate"]
    ]
    lines += [
        "## Direct Register References",
        "",
        "These are linear `MOV DPTR,#imm16` sightings. They are useful waypoints,",
        "not proof of valid function boundaries because the image mixes code and data.",
        "",
        "| addr | count | first gateway offsets | label |",
        "|---:|---:|---|---|",
    ]
    for row in interesting_refs:
        first = ", ".join(hex_addr(x) for x in row["offsets"][:6])
        label = str(row["label"] or "")
        if row["servo_candidate"]:
            label = (label + "; " if label else "") + "servo/mechanics shortlist"
        lines.append(f"| `{hex_addr(int(row['addr']))}` | {row['count']} | `{first}` | {label} |")

    lcall_zero = [row for row in analysis["lcall_targets"] if row["target_zero_page"]]
    ljmp_zero = [row for row in analysis["ljmp_targets"] if row["target_zero_page"]]
    lines += [
        "",
        "## Disassembly Caution",
        "",
        "Many apparent calls/jumps target `0x02ea..0x3fff`, which is all zero in",
        "this captured window. That argues against treating the dump as a complete",
        "standalone 8051 code image at base zero. Plausible explanations are missing",
        "bank/common-ROM code, banked address spaces, and false positives from",
        "linear-disassembling data.",
        "",
        f"- top-80 `LCALL` targets in the zero range: {len(lcall_zero)}",
        f"- top-80 `LJMP` targets in the zero range: {len(ljmp_zero)}",
        "",
    ]

    lines += [
        "## Sled / Servo Side Quest",
        "",
        "The gateway dump gives a much stronger static foothold for the mechanics",
        "goal. The `0x59xx` and `0x5axx` cluster is touched by several coherent",
        "routines, and exact overlap shows the LD5M resident routine around F0",
        "`0x59f3` is present at gateway offset `0x6059`. That routine clears or",
        "masks `0x5904`, `0x5905`, `0x5906`, `0x592a`, `0x59f0`, `0x59f1`,",
        "`0x5a00`, `0x5a24`, `0x5a31`, and then initializes nearby `0x4860..0x486a`",
        "state. Other gateway routines around `0x642c`, `0x6fe0`, and `0x8278`",
        "manipulate the same cluster.",
        "",
        "That lines up with the live observation that blind probes in this area",
        "moved the sled or changed recovery behavior. Practically, this is now a",
        "servo/mechanics command cluster to reverse, not a front-LED latch to poke.",
        "The safer next static step is to map the call graph and state-machine inputs",
        "around these `0x59xx` routines before issuing any live movement tests.",
        "",
        "Promising static waypoints:",
        "",
        "- gateway `0x6059`: resident/helper init-like hardware setup, exact F0 overlap;",
        "- gateway `0x642c`: masks `0x5904/0x590b`, writes `0x4864=0x36`, loops through data while polling `0x4000.7`;",
        "- gateway `0x6fe0`: enables/disables `0x59a4/0x5907/0x599e/0x592b/0x5997/0x5945` paths;",
        "- gateway `0x8278`: state-gated path that clears `0x5905.6`, then branches into larger mechanics/state routines.",
        "",
        "## Practical Consequence",
        "",
        "The new artifact narrows the next work. For CDD, it proves the gateway can",
        "show copied encoded CDD work buffers, but not yet decoded controller code at",
        "`0x184000`. For mechanics, it gives a concrete `0x59xx` control cluster to",
        "reverse from real runtime bytes. For LED output, it reinforces that the LED",
        "is probably controller-owned or coupled to controller state, not an easy",
        "8051 GPIO latch.",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", type=Path, default=DEFAULT_GATEWAY)
    parser.add_argument("--f0", type=Path, default=DEFAULT_F0)
    parser.add_argument("--resident-8051", type=Path, default=DEFAULT_8051)
    parser.add_argument("--helper", type=Path, default=DEFAULT_HELPER)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    args = parser.parse_args()

    analysis = build_analysis(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(analysis, indent=2) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_md(analysis) + "\n")
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_json}")


if __name__ == "__main__":
    main()
