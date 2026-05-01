#!/usr/bin/env python3
"""Plan byte patches for a LiteOn CDD affine leaf group.

The CDD affine decoder is partial: it only covers the lane-0 leaf cells that
we can identify from canonical unit tails. This helper turns that evidence into
a safe, auditable patch plan. For a selected image/group, it rewrites every
observed raw lead cell so the group decodes to the requested plain byte.

It does not talk to a drive.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import analyze_liteon_cdd_affine_units as affine
import analyze_liteon_cdd_streams as cdd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_OUT_JSON = ROOT / "work/cdd-affine-patch-plan.json"
DEFAULT_OUT_MD = ROOT / "work/cdd-affine-patch-plan.md"


def group_rows(image: cdd.CddImage) -> dict[int, list[dict[str, Any]]]:
    _canonical, evidence = affine.decode_image(image)
    rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    segments = {index: (start, end, entry) for index, start, end, entry in cdd.source_segments(image)}
    for item in evidence:
        start, _end, _entry = segments[item.record]
        absolute = start + item.source_offset_in_record
        rows[item.group].append(
            {
                "group": item.group,
                "record": item.record,
                "record_mod4": item.record_mod4,
                "cell": item.cell,
                "mask": item.mask,
                "plain": item.plain,
                "raw": item.raw,
                "absolute_offset": absolute,
                "absolute_offset_hex": f"0x{absolute:05x}",
                "kind": item.kind,
                "op_key": item.op_key,
            }
        )
    return dict(sorted(rows.items()))


def plan_group(image: cdd.CddImage, group: int, target_plain: int) -> dict[str, Any]:
    rows_by_group = group_rows(image)
    if group not in rows_by_group:
        raise SystemExit(f"group {group} has no affine evidence in {image.name}")
    rows = sorted(rows_by_group[group], key=lambda row: (row["record"], row["cell"], row["absolute_offset"]))
    plains = sorted({row["plain"] for row in rows})
    if len(plains) != 1:
        raise SystemExit(f"group {group} has conflicting plains: {plains}")
    seen_offsets: set[int] = set()
    patches = []
    for row in rows:
        offset = int(row["absolute_offset"])
        if offset in seen_offsets:
            raise SystemExit(f"duplicate patch offset 0x{offset:x}")
        seen_offsets.add(offset)
        before = int(row["raw"])
        after = target_plain ^ int(row["mask"])
        patches.append(
            {
                **row,
                "before": before,
                "after": after,
                "before_hex": f"{before:02x}",
                "after_hex": f"{after:02x}",
                "patch_arg": f"0x{offset:x}:{after:02x}",
                "restore_arg": f"0x{offset:x}:{before:02x}",
                "changed": before != after,
            }
        )
    return {
        "image": image.name,
        "image_path": str(image.path),
        "group": group,
        "stock_plain": plains[0],
        "stock_plain_hex": f"0x{plains[0]:02x}",
        "target_plain": target_plain,
        "target_plain_hex": f"0x{target_plain:02x}",
        "cell_count": len(patches),
        "records": sorted({row["record"] for row in patches}),
        "cells": [row["cell"] for row in patches],
        "kinds": sorted({row["kind"] for row in patches}),
        "patches": patches,
        "patch_args": [row["patch_arg"] for row in patches if row["changed"]],
        "restore_args": [row["restore_arg"] for row in patches if row["changed"]],
    }


def list_groups(image: cdd.CddImage) -> dict[str, Any]:
    groups = []
    for group, rows in group_rows(image).items():
        plains = sorted({row["plain"] for row in rows})
        groups.append(
            {
                "group": group,
                "plain": plains[0] if len(plains) == 1 else None,
                "plains": plains,
                "cells": sorted({row["cell"] for row in rows}),
                "cell_count": len(rows),
                "records": sorted({row["record"] for row in rows}),
                "kinds": sorted({row["kind"] for row in rows}),
            }
        )
    return {"image": image.name, "groups": groups}


def render_plan(report: dict[str, Any]) -> str:
    if "groups" in report:
        lines = [
            "# CDD Affine Group Patch Candidates",
            "",
            f"Image: `{report['image']}`",
            "",
            "| group | plain | cells | records | kinds |",
            "|---:|---:|---|---|---|",
        ]
        for row in report["groups"]:
            cells = ", ".join(str(cell) for cell in row["cells"])
            records = ", ".join(str(record) for record in row["records"])
            kinds = ", ".join(row["kinds"])
            plain = "--" if row["plain"] is None else f"`0x{row['plain']:02x}`"
            lines.append(f"| {row['group']} | {plain} | `{cells}` | `{records}` | `{kinds}` |")
        lines.append("")
        return "\n".join(lines)

    lines = [
        "# CDD Affine Group Patch Plan",
        "",
        f"Image: `{report['image']}`",
        f"Group: `{report['group']}`",
        f"Stock plain: `{report['stock_plain_hex']}`",
        f"Target plain: `{report['target_plain_hex']}`",
        f"Cells: `{', '.join(str(cell) for cell in report['cells'])}`",
        f"Records: `{', '.join(str(record) for record in report['records'])}`",
        f"Kinds: `{', '.join(report['kinds'])}`",
        "",
        "Patch args:",
        "",
        "```text",
        " ".join(f"--patch {arg}" for arg in report["patch_args"]),
        "```",
        "",
        "Restore args:",
        "",
        "```text",
        " ".join(f"--patch {arg}" for arg in report["restore_args"]),
        "```",
        "",
        "| offset | record | cell | mask | before | after |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["patches"]:
        lines.append(
            f"| `{row['absolute_offset_hex']}` | {row['record']} | {row['cell']} | "
            f"`0x{row['mask']:02x}` | `0x{row['before']:02x}` | `0x{row['after']:02x}` |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--group", type=int, help="affine group to patch; omit with --list")
    parser.add_argument("--target-plain", type=lambda value: int(value, 0), help="target decoded plain byte")
    parser.add_argument("--list", action="store_true", help="list available affine groups instead of planning patches")
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    image = cdd.load_image(args.image)
    if image is None:
        raise SystemExit(f"could not load CDD image {args.image}")
    if args.list:
        report = list_groups(image)
    else:
        if args.group is None or args.target_plain is None:
            raise SystemExit("--group and --target-plain are required unless --list is used")
        if not 0 <= args.target_plain <= 0xFF:
            raise SystemExit("--target-plain must be a byte")
        report = plan_group(image, args.group, args.target_plain)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_plan(report))
    print(render_plan(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
