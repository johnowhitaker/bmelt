#!/usr/bin/env python3
"""Compare normal work-window captures across CDD affine-leaf states.

This is a generic version of the group-105 live-diff analyzer. It reduces each
state to 0x40-byte chunks that are stable across every capture in that state,
then reports offsets where the mutation state differs from the stock state.
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


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def collect_paths(path: Path) -> list[Path]:
    paths = sorted(path.glob("*.window.bin")) + sorted(path.glob("*.bin"))
    return [item for item in paths if item.is_file()]


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


def parse_state(item: str) -> tuple[str, Path]:
    if "=" not in item:
        raise argparse.ArgumentTypeError("state must be LABEL=PATH")
    label, path = item.split("=", 1)
    label = label.strip()
    if not label:
        raise argparse.ArgumentTypeError("state label is empty")
    return label, Path(path)


def analyze(
    states: dict[str, dict[str, Any]],
    stock_labels: list[str],
    mut_labels: list[str],
) -> dict[str, Any]:
    stable = {name: state["stable_chunks"] for name, state in states.items()}
    common_offsets = sorted(set.intersection(*(set(chunks) for chunks in stable.values())))

    clean_reversible = []
    noisy_sensitive = []
    for offset in common_offsets:
        stock_values = [stable[name][offset] for name in stock_labels]
        mut_values = [stable[name][offset] for name in mut_labels]
        all_values = stock_values + mut_values
        if len(set(all_values)) == 1:
            continue

        stock_canonical = stock_values[0]
        row = {
            "offset": offset,
            "offset_hex": f"0x{offset:04x}",
            "values": {
                name: compact_chunk(stable[name][offset])
                for name in list(stock_labels) + list(mut_labels)
            },
            "mutations": {},
        }
        for name in mut_labels:
            value = stable[name][offset]
            row["mutations"][name] = {
                "diff_count": sum(a != b for a, b in zip(stock_canonical, value)),
                "diffs": byte_diffs(stock_canonical, value),
            }

        if all(value == stock_canonical for value in stock_values):
            clean_reversible.append(row)
        else:
            noisy_sensitive.append(row)

    return {
        "states": {
            name: {
                "path": state["path"],
                "capture_count": state["capture_count"],
                "lengths": state["lengths"],
                "stable_count": state["stable_count"],
            }
            for name, state in states.items()
        },
        "stock_labels": stock_labels,
        "mut_labels": mut_labels,
        "chunk_size": CHUNK_SIZE,
        "common_stable_offsets": len(common_offsets),
        "clean_reversible_count": len(clean_reversible),
        "noisy_sensitive_count": len(noisy_sensitive),
        "clean_reversible": clean_reversible,
        "noisy_sensitive": noisy_sensitive,
    }


def render(report: dict[str, Any], title: str, summary: str) -> str:
    stock_labels = report["stock_labels"]
    mut_labels = report["mut_labels"]
    first_stock = stock_labels[0]

    lines = [
        f"# {title}",
        "",
        summary,
        "",
        "The normal READ BUFFER work-window is a rotating tile surface. This",
        "report only compares 0x40-byte chunks that are stable inside each state.",
        "",
        "## Summary",
        "",
        f"Chunk size: `0x{report['chunk_size']:x}`",
        f"Common stable offsets across all states: {report['common_stable_offsets']}",
        f"Clean stock-consistent mutation offsets: {report['clean_reversible_count']}",
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
        "## Clean Offsets",
        "",
        "| offset | " + " | ".join(f"{name} diffs" for name in mut_labels) + " | stock head | "
        + " | ".join(f"{name} head" for name in mut_labels) + " |",
        "|---:|" + "---:|" * len(mut_labels) + "---|" + "---|" * len(mut_labels),
    ]
    for row in report["clean_reversible"][:120]:
        values = row["values"]
        diff_cells = [
            str(row["mutations"][name]["diff_count"])
            for name in mut_labels
        ]
        head_cells = [f"`{values[name]['head16']}`" for name in mut_labels]
        lines.append(
            f"| `{row['offset_hex']}` | "
            + " | ".join(diff_cells)
            + f" | `{values[first_stock]['head16']}` | "
            + " | ".join(head_cells)
            + " |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- A clean row means the stock states agree at that offset and at least one",
        "  mutation state differs. With only one stock capture set, the live F0",
        "  restore verification is the evidence for reversibility.",
        "- Treat these rows as correlation targets. They are public-window effects,",
        "  not direct decoded CDD bytes.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        action="append",
        type=parse_state,
        required=True,
        help="State as LABEL=PATH; repeat for each state.",
    )
    parser.add_argument(
        "--stock-label",
        action="append",
        required=True,
        help="Label to treat as stock; repeat if multiple stock states exist.",
    )
    parser.add_argument(
        "--mut-label",
        action="append",
        required=True,
        help="Label to treat as mutation; repeat if multiple mutation states exist.",
    )
    parser.add_argument("--title", default="CDD Affine Live Diff")
    parser.add_argument("--summary", default="Offline comparison of CDD affine live captures.")
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_paths = dict(args.state)
    for label in args.stock_label + args.mut_label:
        if label not in state_paths:
            raise SystemExit(f"unknown state label: {label}")

    states = {label: load_state(path, CHUNK_SIZE) for label, path in state_paths.items()}
    report = analyze(states, args.stock_label, args.mut_label)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render(report, args.title, args.summary) + "\n")
    print(render(report, args.title, args.summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
