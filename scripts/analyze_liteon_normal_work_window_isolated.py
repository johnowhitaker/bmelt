#!/usr/bin/env python3
"""Compare isolated normal work-window stimulus captures against local baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TARGET_ADDRS = {
    0x47B1,
    0x8A23,
    *range(0x8A49, 0x8A55),
    0x8ADF,
    0x4000,
    *range(0x4091, 0x409A),
}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_informative(chunk: bytes) -> bool:
    return len(set(chunk)) > 1


def scan_dptrs(data: bytes) -> list[int]:
    out = []
    for offset in range(0, max(0, len(data) - 2)):
        if data[offset] == 0x90:
            out.append((data[offset + 1] << 8) | data[offset + 2])
    return out


def capture_kind(path: Path) -> str:
    stem = path.name.removesuffix(".window.bin")
    if "baseline-no-stimulus" in stem:
        return "baseline"
    return "stimulus"


def stimulus_name(path: Path) -> str:
    stem = path.name.removesuffix(".window.bin")
    parts = stem.split("-", 2)
    if len(parts) == 3 and parts[1].startswith("cycle"):
        return parts[2]
    if len(parts) >= 2:
        return "-".join(parts[1:])
    return stem


def load_dir(run_dir: Path, chunk_size: int) -> dict[str, Any]:
    chunks: dict[str, Any] = {}
    kinds = Counter()
    stimulus_names = Counter()
    for path in sorted(run_dir.glob("*.window.bin")):
        kind = capture_kind(path)
        kinds[kind] += 1
        if kind == "stimulus":
            stimulus_names[stimulus_name(path)] += 1
        data = path.read_bytes()
        for public_offset in range(0, len(data) - chunk_size + 1, chunk_size):
            chunk = data[public_offset : public_offset + chunk_size]
            if not is_informative(chunk):
                continue
            digest = sha256_hex(chunk)
            item = chunks.setdefault(
                digest,
                {
                    "sha256": digest,
                    "sample_hex": chunk[:16].hex(),
                    "dptr_refs": sorted(set(scan_dptrs(chunk))),
                    "target_refs": [],
                    "observations": [],
                    "kinds": Counter(),
                    "offsets": set(),
                },
            )
            item["target_refs"] = sorted(addr for addr in item["dptr_refs"] if addr in TARGET_ADDRS)
            item["observations"].append(
                {
                    "capture": path.name.removesuffix(".window.bin"),
                    "kind": kind,
                    "public_offset": public_offset,
                }
            )
            item["kinds"][kind] += 1
            item["offsets"].add(public_offset)

    baseline = {digest for digest, item in chunks.items() if item["kinds"]["baseline"]}
    stimulus = {digest for digest, item in chunks.items() if item["kinds"]["stimulus"]}
    stimulus_only = stimulus - baseline
    baseline_only = baseline - stimulus
    recurring_stimulus_only = {
        digest
        for digest in stimulus_only
        if chunks[digest]["kinds"]["stimulus"] >= 2
    }
    target_stimulus_only = {
        digest
        for digest in stimulus_only
        if chunks[digest]["target_refs"]
    }

    top = []
    for digest in stimulus_only:
        item = chunks[digest]
        top.append(
            {
                "sha256": digest,
                "stimulus_observations": item["kinds"]["stimulus"],
                "offsets": sorted(item["offsets"]),
                "target_refs": item["target_refs"],
                "sample_hex": item["sample_hex"],
            }
        )
    top.sort(
        key=lambda row: (
            -row["stimulus_observations"],
            -len(row["target_refs"]),
            row["offsets"],
            row["sha256"],
        )
    )

    return {
        "run": run_dir.name,
        "path": str(run_dir),
        "stimulus_names": dict(stimulus_names),
        "baseline_captures": kinds["baseline"],
        "stimulus_captures": kinds["stimulus"],
        "baseline_unique_chunks": len(baseline),
        "stimulus_unique_chunks": len(stimulus),
        "shared_chunks": len(baseline & stimulus),
        "stimulus_only_chunks": len(stimulus_only),
        "baseline_only_chunks": len(baseline_only),
        "recurring_stimulus_only_chunks": len(recurring_stimulus_only),
        "target_stimulus_only_chunks": len(target_stimulus_only),
        "top_stimulus_only_chunks": top[:96],
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Isolated Normal Work-Window Stimulus Diffs",
        "",
        "Each run alternates local baseline captures with one read-only stimulus.",
        "This report compares stimulus captures only against baselines from the",
        "same run to reduce noise from ordinary window rotation.",
        "",
        "## Summary",
        "",
        "| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["runs"]:
        stim = ", ".join(f"`{name}` x{count}" for name, count in row["stimulus_names"].items()) or "-"
        lines.append(
            f"| `{row['run']}` | {stim} | {row['baseline_captures']} | {row['stimulus_captures']} | "
            f"{row['baseline_unique_chunks']} | {row['stimulus_unique_chunks']} | {row['shared_chunks']} | "
            f"{row['stimulus_only_chunks']} | {row['recurring_stimulus_only_chunks']} | "
            f"{row['target_stimulus_only_chunks']} |"
        )

    for row in report["runs"]:
        lines += [
            "",
            f"## {row['run']}",
            "",
            "| obs | offsets | target refs | sample |",
            "|---:|---|---|---|",
        ]
        for chunk in row["top_stimulus_only_chunks"][:24]:
            refs = ", ".join(f"`0x{addr:04x}`" for addr in chunk["target_refs"]) or "-"
            offsets = ", ".join(f"`+0x{off:04x}`" for off in chunk["offsets"][:8])
            lines.append(
                f"| {chunk['stimulus_observations']} | {offsets} | {refs} | `{chunk['sample_hex']}` |"
            )

    lines += [
        "",
        "## Interpretation",
        "",
        "- These small isolated runs are still dominated by the normal rotating",
        "  window, so the most useful rows are recurring stimulus-only chunks and",
        "  stimulus-only chunks with target DPTR references.",
        "- A command that produces many recurring stimulus-only chunks is a better",
        "  candidate for a dedicated longer capture than one that only produces",
        "  one-off sampling differences.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--chunk-size", type=lambda x: int(x, 0), default=0x40)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    report = {
        "chunk_size": args.chunk_size,
        "runs": [load_dir(run_dir, args.chunk_size) for run_dir in args.run_dirs],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))


if __name__ == "__main__":
    main()
