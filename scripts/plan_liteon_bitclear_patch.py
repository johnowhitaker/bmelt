#!/usr/bin/env python3
"""Classify LiteOn F0 patch diffs under SPI NOR bit-clearing semantics.

The currently proven helper primitive can program bits from 1 to 0. It cannot
turn 0 back to 1 unless the relevant sector is erased first. This offline tool
compares a base/current image with a target image or explicit patches and
reports which bytes are immediately programmable and which require erase.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from classify_liteon_f0_probe_offsets import classify_offset, make_regions


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "references/firmware/extracted"
DEFAULT_BASE = EXTRACTED / "ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_OUT_JSON = EXTRACTED / "liteon-bitclear-patch-plan.json"
DEFAULT_OUT_MD = EXTRACTED / "liteon-bitclear-patch-plan.md"
HELPER_DEFAULT_START_SECTOR = 0x07


def compact_hex(value: str) -> str:
    return "".join(ch for ch in value if ch in "0123456789abcdefABCDEF")


def parse_patch(value: str) -> tuple[int, bytes]:
    try:
        offset_text, hex_text = value.split(":", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("patch must be OFFSET:HEX") from exc
    offset = int(offset_text, 0)
    payload_hex = compact_hex(hex_text)
    if offset < 0:
        raise argparse.ArgumentTypeError("patch offset must be non-negative")
    if not payload_hex or len(payload_hex) % 2:
        raise argparse.ArgumentTypeError("patch hex must be non-empty whole bytes")
    return offset, bytes.fromhex(payload_hex)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_bits(old: int, new: int) -> dict[str, int]:
    cleared = old & ~new
    raised = (~old) & new & 0xFF
    unchanged_zero = (~old) & (~new) & 0xFF
    unchanged_one = old & new
    return {
        "cleared_1_to_0": cleared,
        "raised_0_to_1": raised,
        "unchanged_zero": unchanged_zero,
        "unchanged_one": unchanged_one,
    }


def apply_patches(image: bytes, patches: list[tuple[int, bytes]]) -> bytes:
    out = bytearray(image)
    for offset, replacement in patches:
        end = offset + len(replacement)
        if end > len(out):
            raise ValueError(f"patch {offset:#x}+{len(replacement):#x} exceeds image length {len(out):#x}")
        out[offset:end] = replacement
    return bytes(out)


def build_target(base: bytes, target_path: Path | None, patches: list[tuple[int, bytes]]) -> bytes:
    if target_path:
        target = target_path.read_bytes()
        if len(target) != len(base):
            raise ValueError(f"target length {len(target):#x} != base length {len(base):#x}")
        return apply_patches(target, patches) if patches else target
    else:
        return apply_patches(base, patches)


def diff_records(base: bytes, target: bytes) -> list[dict[str, Any]]:
    regions = make_regions(base)
    records = []
    for offset, (old, new) in enumerate(zip(base, target, strict=True)):
        if old == new:
            continue
        bits = changed_bits(old, new)
        bit_clear_possible = bits["raised_0_to_1"] == 0
        classification = classify_offset(base, regions, offset)
        sector = offset // 0x1000
        records.append(
            {
                "offset": offset,
                "offset_hex": f"0x{offset:x}",
                "sector_0x1000": sector,
                "sector_start": sector * 0x1000,
                "old": old,
                "new": new,
                "old_hex": f"{old:02x}",
                "new_hex": f"{new:02x}",
                "cleared_1_to_0_hex": f"{bits['cleared_1_to_0']:02x}",
                "raised_0_to_1_hex": f"{bits['raised_0_to_1']:02x}",
                "bit_clear_possible_without_erase": bit_clear_possible,
                "requires_erase": not bit_clear_possible,
                "target_classification": classification,
            }
        )
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    sectors = sorted({record["sector_0x1000"] for record in records})
    impossible = [record for record in records if record["requires_erase"]]
    risky = [
        record
        for record in records
        if record["target_classification"].get("risk") in {"high", "very_high"}
    ]
    return {
        "diff_count": len(records),
        "bit_clear_possible_count": len(records) - len(impossible),
        "requires_erase_count": len(impossible),
        "all_bit_clear_possible_without_erase": not impossible,
        "touched_sectors_0x1000": sectors,
        "touched_sector_ranges": [f"0x{sector * 0x1000:05x}..0x{sector * 0x1000 + 0xfff:05x}" for sector in sectors],
        "risky_diff_count": len(risky),
        "dangerous_offsets": [
            {
                "offset": record["offset"],
                "offset_hex": record["offset_hex"],
                "risk": record["target_classification"].get("risk"),
                "region": record["target_classification"].get("region"),
                "advice": record["target_classification"].get("advice"),
            }
            for record in risky
        ],
        "helper_range_recommendation": helper_range_recommendation(records),
    }


def helper_range_recommendation(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {
            "needed": False,
            "reason": "no diffs",
            "lowest_touched_sector_0x1000": None,
            "lowest_erase_required_sector_0x1000": None,
            "program_start_page_0x100": None,
            "erase_start_sector_0x1000": None,
            "helper_patches": [],
            "notes": ["no diffs"],
        }

    lowest_touched_sector = min(record["sector_0x1000"] for record in records)
    erase_required_records = [record for record in records if record["requires_erase"]]
    lowest_erase_required_sector = (
        min(record["sector_0x1000"] for record in erase_required_records)
        if erase_required_records
        else None
    )

    helper_patches: list[str] = []
    recommendation: dict[str, Any] = {
        "needed": False,
        "lowest_touched_sector_0x1000": lowest_touched_sector,
        "lowest_erase_required_sector_0x1000": lowest_erase_required_sector,
        "program_start_page_0x100": None,
        "erase_start_sector_0x1000": None,
        "helper_patches": helper_patches,
        "notes": [],
    }

    if lowest_touched_sector < HELPER_DEFAULT_START_SECTOR:
        program_start_page = lowest_touched_sector * 0x10
        helper_patches.append(f"0x345:7524{program_start_page:02x}")
        recommendation["needed"] = True
        recommendation["program_start_page_0x100"] = program_start_page
        recommendation["notes"].append(
            "patch helper program start lower than the normal 0x7000 boundary"
        )

    if lowest_erase_required_sector is not None and lowest_erase_required_sector < HELPER_DEFAULT_START_SECTOR:
        helper_patches.append(f"0x169:7522{lowest_erase_required_sector:02x}")
        recommendation["needed"] = True
        recommendation["erase_start_sector_0x1000"] = lowest_erase_required_sector
        recommendation["notes"].append(
            "patch helper erase start for lower-sector bytes that need 0->1 restoration"
        )

    if not recommendation["needed"]:
        recommendation["notes"].append("normal helper range is sufficient for these diffs")
    return recommendation


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    base = args.base.read_bytes()
    current = apply_patches(base, args.current_patch or [])
    target = build_target(base, args.target, args.patch or [])
    records = diff_records(current, target)
    summary = summarize(records)
    return {
        "status": "liteon_bitclear_patch_plan",
        "base": str(args.base),
        "base_sha256": sha256_bytes(base),
        "current_sha256": sha256_bytes(current),
        "target": str(args.target) if args.target else None,
        "target_sha256": sha256_bytes(target),
        "current_patches_assumed": [
            {"offset": offset, "offset_hex": f"0x{offset:x}", "replacement_hex": payload.hex()}
            for offset, payload in (args.current_patch or [])
        ],
        "patches_requested": [
            {"offset": offset, "offset_hex": f"0x{offset:x}", "replacement_hex": payload.hex()}
            for offset, payload in (args.patch or [])
        ],
        "summary": summary,
        "diffs": records[: args.max_diffs],
        "diffs_truncated": len(records) > args.max_diffs,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# LiteOn Bit-Clear Patch Plan",
        "",
        "Offline classification of an F0 target under the currently proven helper programming primitive.",
        "No drive commands were sent.",
        "",
        f"- base: `{report['base']}`",
        f"- target: `{report['target']}`",
        f"- assumed current patches: `{len(report['current_patches_assumed'])}`",
        f"- diff count: `{summary['diff_count']}`",
        f"- bit-clear without erase: `{summary['bit_clear_possible_count']}`",
        f"- requires erase: `{summary['requires_erase_count']}`",
        f"- all possible without erase: `{summary['all_bit_clear_possible_without_erase']}`",
        f"- risky diff count: `{summary['risky_diff_count']}`",
        "",
        "## Helper Range Recommendation",
        "",
    ]
    helper = summary["helper_range_recommendation"]
    lines.extend(
        [
            f"- needed: `{helper['needed']}`",
            f"- program start page: `{helper['program_start_page_0x100']}`",
            f"- erase start sector: `{helper['erase_start_sector_0x1000']}`",
            f"- helper patches: `{', '.join(helper['helper_patches'])}`",
        ]
    )
    for note in helper["notes"]:
        lines.append(f"- {note}")

    lines.extend(
        [
            "",
            "Touched sectors:",
        ]
    )
    for item in summary["touched_sector_ranges"]:
        lines.append(f"- `{item}`")

    if summary["dangerous_offsets"]:
        lines.extend(["", "## Dangerous Offsets", ""])
        for item in summary["dangerous_offsets"]:
            lines.append(
                f"- `{item['offset_hex']}`: `{item['region']}` / `{item['risk']}`. {item['advice']}"
            )

    lines.extend(
        [
            "",
            "## Diffs",
            "",
            "| offset | old | new | sector | bit-clear now | requires erase | region | risk |",
            "|---:|---:|---:|---:|---|---|---|---|",
        ]
    )
    for record in report["diffs"]:
        target = record["target_classification"]
        lines.append(
            f"| `{record['offset_hex']}` | `{record['old_hex']}` | `{record['new_hex']}` | "
            f"`{record['sector_0x1000']}` | `{record['bit_clear_possible_without_erase']}` | "
            f"`{record['requires_erase']}` | `{target['region']}` | `{target['risk']}` |"
        )
    if report["diffs_truncated"]:
        lines.append("")
        lines.append("Diff list truncated by `--max-diffs`.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--target", type=Path)
    parser.add_argument(
        "--current-patch",
        action="append",
        type=parse_patch,
        help="patch assumed to already be present in the current/live image before applying target",
    )
    parser.add_argument("--patch", action="append", type=parse_patch)
    parser.add_argument("--max-diffs", type=int, default=200)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.target and not args.patch:
        raise SystemExit("provide --target and/or at least one --patch")
    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
