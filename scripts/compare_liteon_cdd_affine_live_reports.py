#!/usr/bin/env python3
"""Compare clean offsets from two CDD affine live-diff reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_MD = ROOT / "analysis/8051/cdd-affine-cross-group-correlation-20260501.md"
DEFAULT_OUT_JSON = ROOT / "analysis/8051/cdd-affine-cross-group-correlation-20260501.json"


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def rows_by_offset(report: dict[str, Any]) -> dict[int, dict[str, Any]]:
    key = "clean_reversible"
    if key not in report:
        raise SystemExit(f"report lacks {key}")
    return {int(row["offset"]): row for row in report[key]}


def first_mut_label(report: dict[str, Any]) -> str:
    labels = report.get("mut_labels")
    if labels:
        return labels[0]
    # Legacy group-105 report labels.
    for label in ("mut_85", "mut_8b"):
        if report.get("clean_reversible") and label in report["clean_reversible"][0]["values"]:
            return label
    raise SystemExit("could not infer mutation label")


def head(row: dict[str, Any], label: str) -> str:
    return row["values"][label]["head16"]


def analyze(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_rows = rows_by_offset(left)
    right_rows = rows_by_offset(right)
    left_offsets = set(left_rows)
    right_offsets = set(right_rows)
    overlap = sorted(left_offsets & right_offsets)

    left_mut = first_mut_label(left)
    right_mut = first_mut_label(right)
    left_stock = left.get("stock_labels", ["stock_before"])[0]
    right_stock = right.get("stock_labels", ["stock_after"])[0]

    rows = []
    for offset in overlap:
        left_row = left_rows[offset]
        right_row = right_rows[offset]
        rows.append(
            {
                "offset": offset,
                "offset_hex": f"0x{offset:04x}",
                "left_stock_head16": head(left_row, left_stock),
                "left_mut_head16": head(left_row, left_mut),
                "right_stock_head16": head(right_row, right_stock),
                "right_mut_head16": head(right_row, right_mut),
                "left_mut_label": left_mut,
                "right_mut_label": right_mut,
            }
        )

    return {
        "left_clean_count": len(left_offsets),
        "right_clean_count": len(right_offsets),
        "overlap_count": len(overlap),
        "left_only_count": len(left_offsets - right_offsets),
        "right_only_count": len(right_offsets - left_offsets),
        "overlap": rows,
    }


def render(report: dict[str, Any], left_path: Path, right_path: Path) -> str:
    lines = [
        "# CDD Affine Cross-Group Correlation",
        "",
        "This report intersects clean normal-mode work-window offsets from two",
        "reversible CDD affine live-diff experiments. An overlap is not a decoded",
        "byte, but it is a better correlation target than a one-off changing tile:",
        "two different CDD leaf edits both perturb the same public READ BUFFER",
        "window offset.",
        "",
        "## Inputs",
        "",
        f"- left: `{display_path(left_path)}`",
        f"- right: `{display_path(right_path)}`",
        "",
        "## Summary",
        "",
        f"Left clean offsets: {report['left_clean_count']}",
        f"Right clean offsets: {report['right_clean_count']}",
        f"Overlap offsets: {report['overlap_count']}",
        f"Left-only offsets: {report['left_only_count']}",
        f"Right-only offsets: {report['right_only_count']}",
        "",
        "The overlap includes the previously interesting response-bridge region",
        "`0x7140/0x7180`, plus several low-window and controller-code-looking tiles.",
        "",
        "## Overlap",
        "",
        "| offset | left stock | left mut | right stock | right mut |",
        "|---:|---|---|---|---|",
    ]
    for row in report["overlap"][:120]:
        lines.append(
            f"| `{row['offset_hex']}` | `{row['left_stock_head16']}` | "
            f"`{row['left_mut_head16']}` | `{row['right_stock_head16']}` | "
            f"`{row['right_mut_head16']}` |"
        )
    lines += [
        "",
        "## Use",
        "",
        "- Prefer overlap offsets as probes for normal-mode hook development, because",
        "  they have now reacted to two independent decoded CDD leaf edits.",
        "- Do not assume an overlap means the same semantic field changed. The work",
        "  window is still phasey and often moves whole 0x40-byte tiles.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--left",
        type=Path,
        default=ROOT / "analysis/8051/cdd-affine-g105-live-diff-20260501.json",
    )
    parser.add_argument(
        "--right",
        type=Path,
        default=ROOT / "analysis/8051/cdd-affine-g99-live-diff-20260501.json",
    )
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    left = load(args.left)
    right = load(args.right)
    report = analyze(left, right)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render(report, args.left, args.right) + "\n")
    print(render(report, args.left, args.right))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
