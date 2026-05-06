#!/usr/bin/env python3
"""Build a bridge-clamp hook candidate from a read-only baseline capture.

The fixed bridge-clamp candidate writes the six most common clamp slots from
the historical corpus. This script narrows that down for a specific drive/run:
scan baseline `READ BUFFER id=01 offset=0x077000` captures, find the stock
bridge-clamp pattern that is actually visible, then generate a candidate whose
cave writes only those observed clamp immediate addresses. The cave preserves
DPTR around the controller-gateway writes, then returns with the stock
`A=0` / `PSW=0` epilogue shape.

No drive commands are sent.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "references/firmware/extracted/helper-bypass-candidates"
BUILD_HELPER = ROOT / "scripts/build_liteon_helper_bypass_candidate.py"
CAVE_ADDR = 0x6EE3
CAVE_LEN = 0xDD
HOOK_OFFSET = 0x422C
PATCH_VALUE = 0x07
CLAMP_PATTERN = bytes.fromhex("90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 0e f0")
CLAMP_IMMEDIATE_INDEX = 13
DEFAULT_PUBLIC_BASE = 0x077000


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    slug = "-".join(part for part in slug.split("-") if part)
    if not slug:
        raise ValueError("empty slug")
    return slug


def mov_dptr(addr: int) -> bytes:
    return bytes([0x90, (addr >> 8) & 0xFF, addr & 0xFF])


def mov_a_imm(value: int) -> bytes:
    return bytes([0x74, value & 0xFF])


def wait_controller_ready() -> bytes:
    return mov_dptr(0x4000) + bytes([0xE0, 0x20, 0xE7, 0xF9])


def write_controller_public_byte(addr: int, value: int) -> bytes:
    return b"".join(
        [
            wait_controller_ready(),
            mov_dptr(0x4095),
            mov_a_imm((addr >> 16) & 0xFF),
            bytes([0xF0, 0xA3]),
            mov_a_imm((addr >> 8) & 0xFF),
            bytes([0xF0, 0xA3]),
            mov_a_imm(addr & 0xFF),
            bytes([0xF0]),
            wait_controller_ready(),
            mov_dptr(0x4098),
            mov_a_imm(value),
            bytes([0xF0]),
        ]
    )


def lcall(addr: int) -> bytes:
    return bytes([0x12, (addr >> 8) & 0xFF, addr & 0xFF])


def push_direct(addr: int) -> bytes:
    return bytes([0xC0, addr & 0xFF])


def pop_direct(addr: int) -> bytes:
    return bytes([0xD0, addr & 0xFF])


def runtime_bridge_clamp_payload(addresses: list[int], value: int) -> bytes:
    payload = b"".join(
        [
            push_direct(0x83),  # DPH
            push_direct(0x82),  # DPL
            *(write_controller_public_byte(addr, value) for addr in addresses),
            pop_direct(0x82),
            pop_direct(0x83),
            bytes([0xE4, 0xF5, 0xD0, 0x22]),  # CLR A; MOV PSW,A; RET
        ]
    )
    if len(payload) > CAVE_LEN:
        raise ValueError(f"payload length {len(payload)} exceeds cave length {CAVE_LEN}")
    return payload


def scan_file(path: Path, public_base: int) -> list[dict[str, Any]]:
    data = path.read_bytes()
    hits = []
    start = 0
    while True:
        idx = data.find(CLAMP_PATTERN, start)
        if idx < 0:
            return hits
        hits.append(
            {
                "path": str(path),
                "file_offset": idx,
                "immediate_file_offset": idx + CLAMP_IMMEDIATE_INDEX,
                "public_addr": public_base + idx + CLAMP_IMMEDIATE_INDEX,
            }
        )
        start = idx + 1


def scan_baseline(baseline_dir: Path, public_base: int) -> tuple[list[dict[str, Any]], Counter[int]]:
    files = sorted(baseline_dir.glob("*-id01-off077000.bin"))
    if not files:
        files = sorted(baseline_dir.glob("*.bin"))
    hits = []
    counter: Counter[int] = Counter()
    for path in files:
        for hit in scan_file(path, public_base):
            hits.append(hit)
            counter[int(hit["public_addr"])] += 1
    return hits, counter


def run_builder(name: str, payload: bytes, out_dir: Path) -> Path:
    cmd = [
        sys.executable,
        str(BUILD_HELPER),
        "--name",
        name,
        "--out-dir",
        str(out_dir),
        "--auto-helper-range",
        "--include-pre-tail",
        "--patch",
        f"0x{HOOK_OFFSET:x}:{lcall(CAVE_ADDR).hex()}",
        "--patch",
        f"0x{CAVE_ADDR:x}:{payload.hex()}",
    ]
    print("+ " + " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)
    return out_dir / slugify(name)


def write_report(candidate_dir: Path, report: dict[str, Any]) -> None:
    json_path = candidate_dir / "dynamic-bridge-clamp-selection.json"
    md_path = candidate_dir / "dynamic-bridge-clamp-selection.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        "# Dynamic Bridge-Clamp Selection",
        "",
        f"baseline dir: `{report['baseline_dir']}`",
        f"candidate: `{report['candidate_name']}`",
        f"payload length: `{report['payload_length']}`",
        "",
        "| rank | address | count |",
        "|---:|---:|---:|",
    ]
    for rank, row in enumerate(report["selected"], start=1):
        lines.append(f"| {rank} | `0x{row['address']:06x}` | {row['count']} |")
    md_path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline_dir", type=Path)
    parser.add_argument("--name", default=None)
    parser.add_argument("--out-dir", type=Path, default=OUT_ROOT)
    parser.add_argument("--public-base", type=lambda value: int(value, 0), default=DEFAULT_PUBLIC_BASE)
    parser.add_argument("--max-writes", type=int, default=6)
    parser.add_argument("--patch-value", type=lambda value: int(value, 0), default=PATCH_VALUE)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_writes < 1:
        raise ValueError("--max-writes must be >= 1")
    if not 0 <= args.patch_value <= 0xFF:
        raise ValueError("--patch-value must be a byte")
    hits, counter = scan_baseline(args.baseline_dir, args.public_base)
    if not counter:
        raise SystemExit(f"no stock bridge-clamp patterns found under {args.baseline_dir}")
    selected_addrs = [addr for addr, _count in counter.most_common(args.max_writes)]
    payload = runtime_bridge_clamp_payload(selected_addrs, args.patch_value)
    name = slugify(args.name or f"post-materializer-runtime-bridge-clamp07-dynamic-{timestamp()}")
    candidate_dir = run_builder(name, payload, args.out_dir)
    report = {
        "baseline_dir": str(args.baseline_dir),
        "candidate_name": name,
        "candidate_dir": str(candidate_dir),
        "public_base": args.public_base,
        "patch_value": args.patch_value,
        "payload_length": len(payload),
        "hit_count": len(hits),
        "all_hits": [
            {
                **hit,
                "public_addr_hex": f"0x{int(hit['public_addr']):06x}",
            }
            for hit in hits
        ],
        "selected": [
            {"address": addr, "address_hex": f"0x{addr:06x}", "count": counter[addr]}
            for addr in selected_addrs
        ],
    }
    write_report(candidate_dir, report)
    print(json.dumps({"candidate_dir": str(candidate_dir), "selected": report["selected"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
