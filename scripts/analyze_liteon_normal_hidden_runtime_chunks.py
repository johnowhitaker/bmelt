#!/usr/bin/env python3
"""Classify normal-mode READ BUFFER work-window chunks.

The normal `READ BUFFER id=01/02 offset=0x070000` window behaves like a
rotating 0x40-byte tile surface. This script builds a chunk corpus from the
normal-mode capture directories, compares each unique tile against visible
firmware/currentboot artifacts, and reports the chunks that look like hidden
normal-runtime code.

It is intentionally offline-only: it reads captured `.window.bin` files and
never opens an optical drive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 0x40

DEFAULT_RUN_GLOB = "references/evidence/live/normal-work-window-*20260501"
DEFAULT_BASELINE_DIR = ROOT / "references/evidence/live/normal-read-buffer-work-window-20260501"
DEFAULT_RECORD_MAP = ROOT / "references/firmware/extracted/liteon-cdd-record-map.json"

REFERENCE_FILES = {
    "ld5m_f0": ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin",
    "visible_8051": ROOT / "analysis/8051/ldm58051.bin",
    "currentboot_gateway_070000": ROOT
    / "references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin",
    "profile_tail_helper_currentboot": ROOT
    / "references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-currentboot.bin",
    "profile_tail_helper_plain": ROOT
    / "references/firmware/extracted/liteon-official-profile-tail-ef130045-plain.bin",
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

INTERESTING_RANGES = {
    "controller_status": (0x4000, 0x4100),
    "front_panel_or_status": (0x4700, 0x4900),
    "profile_string_area": (0x5900, 0x5A00),
    "packet_shadow": (0x8000, 0x8C00),
}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def u16be(data: bytes, offset: int) -> int:
    return (data[offset] << 8) | data[offset + 1]


def scan_dptr_refs(data: bytes) -> list[int]:
    return [
        u16be(data, offset + 1)
        for offset in range(0, max(0, len(data) - 2))
        if data[offset] == 0x90
    ]


def scan_direct_copies(data: bytes) -> list[dict[str, int]]:
    copies = []
    for offset in range(0, max(0, len(data) - 7)):
        if (
            data[offset] == 0x90
            and data[offset + 3] == 0xE0
            and data[offset + 4] == 0x90
            and data[offset + 7] == 0xF0
        ):
            copies.append({"offset": offset, "src": u16be(data, offset + 1), "dst": u16be(data, offset + 5)})
    return copies


def scan_calls_and_jumps(data: bytes) -> list[dict[str, int | str]]:
    refs: list[dict[str, int | str]] = []
    for offset in range(0, max(0, len(data) - 2)):
        opcode = data[offset]
        if opcode == 0x02:
            refs.append({"offset": offset, "kind": "ljmp", "target": u16be(data, offset + 1)})
        elif opcode == 0x12:
            refs.append({"offset": offset, "kind": "lcall", "target": u16be(data, offset + 1)})
    return refs


def category_for_dptr(addr: int) -> str | None:
    for name, (start, end) in INTERESTING_RANGES.items():
        if start <= addr < end:
            return name
    return None


def find_all(data: bytes, needle: bytes) -> list[int]:
    hits: list[int] = []
    start = 0
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return hits
        hits.append(offset)
        start = offset + 1


def load_references() -> dict[str, bytes]:
    refs: dict[str, bytes] = {}
    for name, path in REFERENCE_FILES.items():
        if path.exists():
            refs[name] = path.read_bytes()
    return refs


def load_ld5m_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    for image in data.get("images", []):
        if image.get("image") == "LD5M":
            return image.get("records", [])
    return []


def record_for_public_offset(records: list[dict[str, Any]], offset: int) -> dict[str, Any] | None:
    for record in records:
        start = int(record["decoded_start"])
        end = start + int(record["decoded_span"])
        if start <= offset < end:
            return record
    return None


def compact_counter(counter: Counter[Any], limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    for value, count in counter.most_common(limit):
        if isinstance(value, int):
            display: Any = f"0x{value:04x}"
        else:
            display = value
        rows.append({"value": display, "count": count})
    return rows


def collect_capture_paths(run_dirs: list[Path]) -> list[Path]:
    paths = []
    for run_dir in run_dirs:
        paths.extend(sorted(run_dir.glob("*.window.bin")))
    return paths


def collect_chunks(paths: list[Path]) -> dict[str, dict[str, Any]]:
    chunks: dict[str, dict[str, Any]] = {}
    for path in paths:
        data = path.read_bytes()
        for public_offset in range(0, len(data) - CHUNK_SIZE + 1, CHUNK_SIZE):
            chunk = data[public_offset : public_offset + CHUNK_SIZE]
            digest = sha256_hex(chunk)
            item = chunks.setdefault(
                digest,
                {
                    "sha256": digest,
                    "data": chunk,
                    "observations": 0,
                    "offsets": Counter(),
                    "runs": Counter(),
                    "examples": [],
                },
            )
            item["observations"] += 1
            item["offsets"][public_offset] += 1
            item["runs"][path.parent.name] += 1
            if len(item["examples"]) < 6:
                item["examples"].append({"run": path.parent.name, "capture": path.name, "offset": public_offset})
    return chunks


def classify_chunk(
    item: dict[str, Any],
    refs: dict[str, bytes],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    data = item["data"]
    dptr_refs = scan_dptr_refs(data)
    direct_copies = scan_direct_copies(data)
    call_refs = scan_calls_and_jumps(data)

    exact_refs: dict[str, list[int]] = {}
    for name, ref_data in refs.items():
        hits = find_all(ref_data, data)
        if hits:
            exact_refs[name] = hits[:10]

    pattern_hits = {
        name: find_all(data, pattern)
        for name, pattern in PATTERNS.items()
        if find_all(data, pattern)
    }

    category_counts: Counter[str] = Counter()
    for addr in dptr_refs:
        category = category_for_dptr(addr)
        if category:
            category_counts[category] += 1

    cdd_candidates = []
    for offset, count in item["offsets"].most_common(6):
        record = record_for_public_offset(records, int(offset))
        if not record:
            continue
        cdd_candidates.append(
            {
                "public_offset": f"0x{offset:04x}",
                "count": count,
                "record": record["index"],
                "record_decoded_start": f"0x{int(record['decoded_start']):05x}",
                "record_decoded_span": f"0x{int(record['decoded_span']):x}",
                "record_mode": f"0x{int(record['mode']):02x}",
                "operation_key": record["operation_key"],
            }
        )

    return {
        "short": item["sha256"][:12],
        "sha256": item["sha256"],
        "observations": item["observations"],
        "offsets": compact_counter(item["offsets"]),
        "runs": compact_counter(item["runs"], limit=6),
        "entropy": round(entropy(data), 4),
        "hex": data.hex(),
        "exact_refs": {name: [f"0x{hit:x}" for hit in hits] for name, hits in exact_refs.items()},
        "patterns": {name: [f"0x{hit:x}" for hit in hits] for name, hits in pattern_hits.items()},
        "dptr_refs": compact_counter(Counter(dptr_refs), limit=12),
        "interesting_categories": dict(category_counts),
        "direct_copies": [
            {"offset": f"0x{copy['offset']:02x}", "src": f"0x{copy['src']:04x}", "dst": f"0x{copy['dst']:04x}"}
            for copy in direct_copies[:12]
        ],
        "calls_and_jumps": [
            {"offset": f"0x{ref['offset']:02x}", "kind": ref["kind"], "target": f"0x{int(ref['target']):04x}"}
            for ref in call_refs[:12]
        ],
        "cdd_public_offset_candidates": cdd_candidates,
        "examples": item["examples"],
    }


def chunk_score(row: dict[str, Any]) -> tuple[int, int, int]:
    hidden = 0 if row["exact_refs"] else 1
    interesting = sum(row["interesting_categories"].values())
    pattern_count = len(row["patterns"])
    return (hidden, interesting + pattern_count * 4, row["observations"])


def baseline_hashes(baseline_dir: Path) -> list[dict[str, str]]:
    rows = []
    for path in sorted(baseline_dir.glob("id0*-070000-010000*.bin")):
        data = path.read_bytes()
        rows.append({"path": str(path.relative_to(ROOT)), "sha256": sha256_hex(data)})
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def write_report(path: Path, report: dict[str, Any]) -> None:
    rows = []
    for row in report["top_hidden_runtime_chunks"]:
        exact = ", ".join(row["exact_refs"].keys()) or "-"
        patterns = ", ".join(row["patterns"].keys()) or "-"
        cats = ", ".join(f"{k}:{v}" for k, v in row["interesting_categories"].items()) or "-"
        offsets = ", ".join(f"{item['value']} x{item['count']}" for item in row["offsets"][:4])
        rows.append([f"`{row['short']}`", str(row["observations"]), offsets, exact, patterns, cats])

    anchor_rows = []
    for name, row in report["anchor_chunks"].items():
        exact = ", ".join(row["exact_refs"].keys()) or "-"
        offsets = ", ".join(f"{item['value']} x{item['count']}" for item in row["offsets"][:4])
        cdd = "; ".join(
            f"{cand['public_offset']} -> rec {cand['record']} ({cand['record_mode']})"
            for cand in row["cdd_public_offset_candidates"][:4]
        ) or "-"
        anchor_rows.append([f"`{name}`", f"`{row['short']}`", str(row["observations"]), offsets, exact, cdd])

    lines = [
        "# Normal Hidden Runtime Chunk Analysis",
        "",
        "Date: 2026-05-01",
        "",
        "This is an offline analysis of the normal-mode `READ BUFFER id=01/02 "
        "offset=0x070000` work-window captures. It treats the window as a "
        "rotating `0x40`-byte tile surface, not as one stable linear image.",
        "",
        "## Summary",
        "",
        f"- captures scanned: `{report['captures_scanned']}`",
        f"- unique chunks: `{report['unique_chunks']}`",
        f"- chunks with exact visible/currentboot reference match: `{report['chunks_with_visible_refs']}`",
        f"- chunks without exact visible/currentboot reference match: `{report['chunks_without_visible_refs']}`",
        f"- interesting hidden chunks: `{len(report['top_hidden_runtime_chunks'])}` shown",
        "",
        "The useful new distinction is that several normal-runtime chunks are "
        "stable and code-like but do not appear byte-for-byte in F0, the visible "
        "8051 slice, the helper overlay, or the currentboot gateway dump. Those "
        "chunks are plausible decoded-controller/runtime material, but their "
        "public slot offsets rotate, so a slot like `+0x7140` should not be "
        "treated as a fixed CDD decoded address by itself.",
        "",
        "## Baseline Window Hashes",
        "",
        markdown_table(
            ["file", "sha256"],
            [[f"`{row['path']}`", f"`{row['sha256'][:16]}...`"] for row in report["baseline_hashes"]],
        ),
        "",
        "The differing hashes are expected: even the baseline reads expose "
        "different rotating tiles. Repeated chunk identity and adjacency are more "
        "trustworthy than whole-window equality.",
        "",
        "## Anchor Chunks",
        "",
        markdown_table(
            ["anchor", "chunk", "obs", "top public offsets", "exact refs", "CDD candidates if offset is trusted"],
            anchor_rows,
        ),
        "",
        "The repeated CDD candidate changes for the same chunk are the important "
        "sanity check. For example, the public bridge chunk appears at several "
        "public offsets, which would place it in different CDD records if we "
        "naively trusted the slot number. That argues against using normal "
        "public offsets as direct decoded CDD addresses without an additional "
        "address/phase model.",
        "",
        "## Top Hidden Runtime Chunks",
        "",
        markdown_table(
            ["chunk", "obs", "top public offsets", "exact refs", "patterns", "interesting refs"],
            rows,
        ),
        "",
        "These are the best current offline targets for reverse engineering normal "
        "runtime plumbing. Chunks with `controller_status` references tend to "
        "touch the `0x4000..0x409c` controller gateway; chunks with "
        "`front_panel_or_status` references are candidates for the LED/button/"
        "mechanism fabric, but should be treated carefully because reads of "
        "`0x47xx` and related paths have wedged the drive before.",
        "",
        "## Practical Read",
        "",
        "- The normal work-window is still a promising source of hidden runtime "
        "code, probably including decoded-controller or overlay material.",
        "- The work-window is not a clean linear decoded CDD image. The same "
        "chunk can occupy multiple public slots, so public offset alone is not "
        "enough to map a chunk to a CDD record.",
        "- The stable public response bridge remains the best host-visible patch "
        "target once we have a normal-mode write primitive.",
        "- For static CDD work, these chunks are useful known-output candidates "
        "only after we learn the missing address/phase relationship between "
        "rotating work-window tiles and the controller's decoded address space.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-glob", default=DEFAULT_RUN_GLOB)
    parser.add_argument("--record-map", type=Path, default=DEFAULT_RECORD_MAP)
    parser.add_argument("--baseline-dir", type=Path, default=DEFAULT_BASELINE_DIR)
    parser.add_argument("--out-json", type=Path, default=ROOT / "analysis/8051/normal-hidden-runtime-chunks-20260501.json")
    parser.add_argument("--out-md", type=Path, default=ROOT / "analysis/8051/normal-hidden-runtime-chunks-20260501.md")
    parser.add_argument("--top", type=int, default=28)
    args = parser.parse_args()

    run_dirs = [path for path in sorted(ROOT.glob(args.run_glob)) if path.is_dir()]
    paths = collect_capture_paths(run_dirs)
    refs = load_references()
    records = load_ld5m_records(args.record_map)
    chunks = collect_chunks(paths)

    rows = [classify_chunk(item, refs, records) for item in chunks.values()]
    rows.sort(key=chunk_score, reverse=True)

    chunks_with_refs = sum(1 for row in rows if row["exact_refs"])
    chunks_without_refs = len(rows) - chunks_with_refs

    anchor_chunks: dict[str, Any] = {}
    for row in rows:
        for pattern_name in row["patterns"]:
            anchor_chunks.setdefault(pattern_name, row)

    top_hidden = [
        row
        for row in rows
        if not row["exact_refs"] and (row["patterns"] or row["interesting_categories"])
    ][: args.top]

    report = {
        "captures_scanned": len(paths),
        "run_dirs": [str(path.relative_to(ROOT)) for path in run_dirs],
        "chunk_size": CHUNK_SIZE,
        "unique_chunks": len(rows),
        "chunks_with_visible_refs": chunks_with_refs,
        "chunks_without_visible_refs": chunks_without_refs,
        "baseline_hashes": baseline_hashes(args.baseline_dir),
        "anchor_chunks": anchor_chunks,
        "top_hidden_runtime_chunks": top_hidden,
    }
    write_json(args.out_json, report)
    write_report(args.out_md, report)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
