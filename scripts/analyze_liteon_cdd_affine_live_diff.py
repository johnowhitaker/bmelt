#!/usr/bin/env python3
"""Compare normal work-window captures across CDD affine-leaf mutations.

This is an offline analyzer for the live CDD group-105 experiments:

* stock LD5M after restoring the affine cells;
* group 105 semantic byte changed from 0x84 to 0x85;
* group 105 semantic byte changed from 0x84 to 0x8b;
* stock LD5M after restoring again.

The normal READ BUFFER work-window is a rotating 0x40-byte tile surface, so a
single before/after diff is misleading. This script first reduces each state to
per-offset chunks that are stable across every capture in that state, then looks
for offsets that reverse cleanly when the CDD bytes are restored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 0x40

DEFAULT_STATES = {
    "stock_before": ROOT / "runs/cdd-affine-g105-restore-live/repeats-restored",
    "mut_85": ROOT / "runs/cdd-affine-g105-live/repeats-mutated",
    "mut_8b": ROOT / "runs/cdd-affine-g105-8b-live/repeats-mutated",
    "stock_after": ROOT / "runs/cdd-affine-g105-restore-after-8b-live/repeats-restored",
}

DEFAULT_OUT_MD = ROOT / "analysis/8051/cdd-affine-g105-live-diff-20260501.md"
DEFAULT_OUT_JSON = ROOT / "analysis/8051/cdd-affine-g105-live-diff-20260501.json"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_paths(path: Path) -> list[Path]:
    paths = sorted(path.glob("*.window.bin")) + sorted(path.glob("*.bin"))
    return [item for item in paths if item.is_file()]


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_state(path: Path, chunk_size: int) -> dict[str, Any]:
    paths = collect_paths(path)
    if not paths:
        raise SystemExit(f"no capture files found in {path}")

    chunks: dict[int, Counter[bytes]] = defaultdict(Counter)
    lengths = Counter()
    for capture in paths:
        data = capture.read_bytes()
        lengths[len(data)] += 1
        for offset in range(0, len(data) - chunk_size + 1, chunk_size):
            chunks[offset][data[offset : offset + chunk_size]] += 1

    stable: dict[int, bytes] = {}
    for offset, counter in chunks.items():
        value, count = counter.most_common(1)[0]
        if count == len(paths):
            stable[offset] = value

    return {
        "path": display_path(path),
        "capture_count": len(paths),
        "lengths": dict(sorted(lengths.items())),
        "stable_chunks": stable,
        "stable_count": len(stable),
        "variant_counts": {offset: len(counter) for offset, counter in chunks.items()},
    }


def byte_diffs(before: bytes, after: bytes, limit: int = 16) -> list[dict[str, int]]:
    rows = []
    for index, (left, right) in enumerate(zip(before, after)):
        if left == right:
            continue
        rows.append({"offset": index, "before": left, "after": right, "xor": left ^ right})
        if len(rows) >= limit:
            break
    return rows


def compact_chunk(value: bytes) -> dict[str, str]:
    return {
        "sha256": sha256_hex(value),
        "short": sha256_hex(value)[:12],
        "head16": value[:16].hex(),
        "hex": value.hex(),
    }


def analyze(states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    names = ["stock_before", "mut_85", "mut_8b", "stock_after"]
    stable = {name: states[name]["stable_chunks"] for name in names}
    common_offsets = sorted(set.intersection(*(set(stable[name]) for name in names)))

    clean_reversible = []
    noisy_sensitive = []
    for offset in common_offsets:
        stock_before = stable["stock_before"][offset]
        mut_85 = stable["mut_85"][offset]
        mut_8b = stable["mut_8b"][offset]
        stock_after = stable["stock_after"][offset]
        values = [stock_before, mut_85, mut_8b, stock_after]
        if len(set(values)) == 1:
            continue

        row = {
            "offset": offset,
            "offset_hex": f"0x{offset:04x}",
            "values": {name: compact_chunk(stable[name][offset]) for name in names},
            "mut_85_diff_count": sum(a != b for a, b in zip(stock_before, mut_85)),
            "mut_8b_diff_count": sum(a != b for a, b in zip(stock_before, mut_8b)),
            "mut_85_diffs": byte_diffs(stock_before, mut_85),
            "mut_8b_diffs": byte_diffs(stock_before, mut_8b),
        }
        if stock_before == stock_after and (mut_85 != stock_before or mut_8b != stock_before):
            clean_reversible.append(row)
        else:
            noisy_sensitive.append(row)

    return {
        "states": {
            name: {
                "path": states[name]["path"],
                "capture_count": states[name]["capture_count"],
                "lengths": states[name]["lengths"],
                "stable_count": states[name]["stable_count"],
            }
            for name in names
        },
        "chunk_size": CHUNK_SIZE,
        "common_stable_offsets": len(common_offsets),
        "clean_reversible_count": len(clean_reversible),
        "noisy_sensitive_count": len(noisy_sensitive),
        "clean_reversible": clean_reversible,
        "noisy_sensitive": noisy_sensitive,
    }


def fmt_diffs(diffs: list[dict[str, int]]) -> str:
    if not diffs:
        return "`none`"
    return " ".join(
        f"`+0x{item['offset']:02x}:{item['before']:02x}->{item['after']:02x}^{item['xor']:02x}`"
        for item in diffs[:8]
    )


def render(report: dict[str, Any]) -> str:
    lines = [
        "# CDD Affine Group 105 Live Diff",
        "",
        "This report compares normal-mode `READ BUFFER id=01/02 offset=0x070000`",
        "captures after reversible edits to CDD stream 2 affine group 105. The",
        "known stock semantic byte is `0x84`; the two live edits rewrote all 12",
        "observed affine lead cells so the group decodes as `0x85` and `0x8b`.",
        "",
        "The work-window is a rotating tile surface, so the useful rows are those",
        "that are stable inside each state and return to the same value after the",
        "stock restore.",
        "",
        "## Summary",
        "",
        f"Chunk size: `0x{report['chunk_size']:x}`",
        f"Common stable offsets across all four states: {report['common_stable_offsets']}",
        f"Clean reversible offsets: {report['clean_reversible_count']}",
        f"Noisy mutation-sensitive offsets: {report['noisy_sensitive_count']}",
        "",
        "| state | captures | stable offsets | path |",
        "|---|---:|---:|---|",
    ]
    for name, state in report["states"].items():
        lines.append(
            f"| `{name}` | {state['capture_count']} | {state['stable_count']} | `{state['path']}` |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- The CDD affine edit is persistable and reversible: stock F0 verification",
        "  returned to byte-identical LD5M after the restore.",
        "- The normal work-window does react, but much of the reaction is tile-phase",
        "  movement rather than a direct decoded-byte oracle.",
        "- The clean rows below are the strongest live evidence that this CDD leaf",
        "  participates in normal runtime state, but they should be treated as",
        "  public-window effects, not as a direct decoded CDD dump.",
        "",
        "## Clean Reversible Offsets",
        "",
        "| offset | mut85 diffs | mut8b diffs | stock head | mut85 head | mut8b head |",
        "|---:|---:|---:|---|---|---|",
    ]
    for row in report["clean_reversible"][:80]:
        values = row["values"]
        lines.append(
            f"| `{row['offset_hex']}` | {row['mut_85_diff_count']} | {row['mut_8b_diff_count']} | "
            f"`{values['stock_before']['head16']}` | `{values['mut_85']['head16']}` | "
            f"`{values['mut_8b']['head16']}` |"
        )

    lines += [
        "",
        "## Low-Window Detail",
        "",
        "The low window contains compact controller-looking records. These are useful",
        "for pattern matching, but not deterministic enough to stand alone as a",
        "semantic oracle because some bytes drift between stock cold boots.",
        "",
    ]
    for target in (0x0180, 0x01C0, 0x0200, 0x0240, 0x0280):
        matching = [
            row
            for row in report["clean_reversible"] + report["noisy_sensitive"]
            if row["offset"] == target
        ]
        if not matching:
            continue
        row = matching[0]
        lines.append(f"### `{row['offset_hex']}`")
        for name in ("stock_before", "mut_85", "mut_8b", "stock_after"):
            value = row["values"][name]
            lines.append(f"- `{name}` `{value['head16']}` sha `{value['short']}`")
        lines.append(f"- `mut_85` first diffs: {fmt_diffs(row['mut_85_diffs'])}")
        lines.append(f"- `mut_8b` first diffs: {fmt_diffs(row['mut_8b_diffs'])}")
        lines.append("")

    lines += [
        "## Next Use",
        "",
        "Use this as a candidate generator, not a final decode. Good next tests are:",
        "",
        "- mutate a second lane-0 group and look for overlapping public-window",
        "  signatures;",
        "- use the clean reversible offsets as trigger/correlation targets while",
        "  developing a normal-mode I/O loop;",
        "- avoid treating the low-window bytes as stable values unless stock-before",
        "  and stock-after agree in the same run.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stock-before", type=Path, default=DEFAULT_STATES["stock_before"])
    parser.add_argument("--mut-85", type=Path, default=DEFAULT_STATES["mut_85"])
    parser.add_argument("--mut-8b", type=Path, default=DEFAULT_STATES["mut_8b"])
    parser.add_argument("--stock-after", type=Path, default=DEFAULT_STATES["stock_after"])
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    states = {
        "stock_before": load_state(args.stock_before, CHUNK_SIZE),
        "mut_85": load_state(args.mut_85, CHUNK_SIZE),
        "mut_8b": load_state(args.mut_8b, CHUNK_SIZE),
        "stock_after": load_state(args.stock_after, CHUNK_SIZE),
    }
    report = analyze(states)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render(report))
    print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
