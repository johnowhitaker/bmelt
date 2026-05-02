#!/usr/bin/env python3
"""Summarize the decoded-runtime neighborhood around CDD record 59.

The output is intentionally simple: it ties the CDD directory map, known
runtime chunks, and decoded 8051-looking bytes together so the record-59
update-entry clue is reproducible without re-reading every prior note.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD_MAP = ROOT / "references/firmware/extracted/liteon-cdd-record-map.json"
DEFAULT_KNOWN_DIR = ROOT / "analysis/8051/cdd-known-output-records-20260501"
DEFAULT_F0 = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"


FOCUS_RECORDS = (57, 58, 59, 60, 66, 70, 84, 85)
INTERESTING_XDATA = {
    0x4000: "controller busy/status",
    0x4011: "controller CDB/arg byte 0",
    0x4012: "controller CDB/arg byte 1",
    0x4013: "controller CDB/arg byte 2",
    0x4095: "controller command/address byte 0",
    0x4096: "controller command/address byte 1",
    0x4097: "controller command/address byte 2",
    0x4098: "controller FIFO",
    0x4099: "controller FIFO/status-adjacent",
    0x47B1: "packet FIFO/data port",
    0x4762: "front-panel/status fabric byte seen in normal work window",
    0x8A29: "CDB/status mode byte used by bridge branch",
    0x8A4C: "CDB shadow byte 0",
    0x8A4D: "CDB shadow byte 1",
    0x8A4E: "CDB shadow byte 2",
    0x8A50: "CDB shadow byte 4/transfer high",
    0x8A51: "CDB shadow byte 5/transfer low",
    0x8857: "response/setup source byte 0",
    0x8858: "response/setup source byte 1",
    0x8859: "response/setup length/command high",
    0x885D: "response/setup destination byte 0",
    0x885E: "response/setup destination byte 1",
    0x885F: "response/setup destination byte 2",
    0x8860: "response/setup destination byte 3",
    0x893C: "response/setup control byte",
}


def load_ld5m_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    image = next(row for row in data["images"] if row["image"] == "LD5M")
    return image["records"]


def known_mask_ranges(mask: bytes) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    start: int | None = None
    for idx, byte in enumerate(mask):
        if byte and start is None:
            start = idx
        elif not byte and start is not None:
            ranges.append((start, idx))
            start = None
    if start is not None:
        ranges.append((start, len(mask)))
    return ranges


def insn_len(op: int) -> int:
    """Return an 8051 instruction length for the opcodes we need to walk.

    This is not a full disassembler, but it is enough to avoid counting
    overlapping byte patterns like `f0 90 ...` as fake calls.
    """

    if op in {0x02, 0x12, 0x43, 0x53, 0x75, 0x85, 0xB4, 0xB5, 0xD5}:
        return 3
    if op in {0x10, 0x20, 0x30}:
        return 3
    if 0xB6 <= op <= 0xBF:
        return 3
    if op == 0x90:
        return 3
    if op in {
        0x01,
        0x11,
        0x21,
        0x31,
        0x41,
        0x51,
        0x61,
        0x71,
        0x81,
        0x91,
        0xA1,
        0xB1,
        0xC1,
        0xD1,
        0xE1,
        0xF1,
    }:
        return 2
    if op in {
        0x05,
        0x15,
        0x25,
        0x35,
        0x40,
        0x44,
        0x45,
        0x50,
        0x54,
        0x55,
        0x60,
        0x64,
        0x65,
        0x70,
        0x74,
        0x76,
        0x77,
        0x80,
        0x94,
        0x95,
        0xA8,
        0xA9,
        0xAA,
        0xAB,
        0xAC,
        0xAD,
        0xAE,
        0xAF,
        0xC0,
        0xC2,
        0xD0,
        0xD2,
        0xE5,
        0xF5,
    }:
        return 2
    if 0x78 <= op <= 0x7F:
        return 2
    if 0x88 <= op <= 0x8F:
        return 2
    return 1


def scan_immediates(code: bytes) -> dict[str, Any]:
    calls: Counter[int] = Counter()
    jumps: Counter[int] = Counter()
    dptrs: Counter[int] = Counter()
    idx = 0
    while idx < len(code):
        op = code[idx]
        length = insn_len(op)
        if length == 3 and idx + 2 < len(code):
            value = (code[idx + 1] << 8) | code[idx + 2]
        else:
            value = None
        if op == 0x12 and value is not None:
            calls[value] += 1
        elif op == 0x02 and value is not None:
            jumps[value] += 1
        elif op == 0x90 and value is not None:
            dptrs[value] += 1
        idx += length
    return {
        "lcalls": [{"target": target, "count": count} for target, count in calls.most_common()],
        "ljmps": [{"target": target, "count": count} for target, count in jumps.most_common()],
        "dptrs": [{"target": target, "count": count} for target, count in dptrs.most_common()],
    }


def owner_for_decoded(records: list[dict[str, Any]], address: int) -> dict[str, Any] | None:
    for record in records:
        start = int(record["decoded_start"])
        end = start + int(record["decoded_span"])
        if start <= address < end:
            return record
    return None


def record_summary(records: list[dict[str, Any]], known_dir: Path, f0: bytes, record_index: int) -> dict[str, Any]:
    record = records[record_index]
    output_path = known_dir / f"record-{record_index:03d}-known-output.bin"
    mask_path = known_dir / f"record-{record_index:03d}-known-mask.bin"
    slots_path = known_dir / f"record-{record_index:03d}-slots.json"
    code = output_path.read_bytes() if output_path.exists() else b""
    mask = mask_path.read_bytes() if mask_path.exists() else b""
    immediates = scan_immediates(code) if code else {"lcalls": [], "ljmps": [], "dptrs": []}
    slots = json.loads(slots_path.read_text()) if slots_path.exists() else []
    source_start = int(record["source_start"])
    source_len = int(record["source_len"])
    source = f0[source_start : source_start + source_len]
    return {
        "record": record_index,
        "source_start": source_start,
        "source_end": int(record["source_end"]),
        "source_len": source_len,
        "decoded_start": int(record["decoded_start"]),
        "decoded_span": int(record["decoded_span"]),
        "mode": int(record["mode"]),
        "operation_key": record["operation_key"],
        "source_minus_decoded": int(record["source_minus_decoded"]),
        "table_target_count": len(record.get("table_targets", [])),
        "known_ranges": known_mask_ranges(mask),
        "slot_count": len(slots),
        "top_slots": [
            {
                "record_relative": int(slot["record_relative"]),
                "top_chunk": slot["top_chunk"],
                "top_count": int(slot["top_count"]),
                "variant_count": int(slot["variant_count"]),
            }
            for slot in slots[:6]
        ],
        "source_rel_0x400": source[0x400] if len(source) > 0x400 else None,
        "source_rel_0x400_window": source[0x3F8:0x410].hex() if len(source) >= 0x410 else "",
        "immediates": immediates,
    }


def enrich_targets(records: list[dict[str, Any]], targets: list[dict[str, int]]) -> list[dict[str, Any]]:
    rows = []
    for item in targets:
        target = int(item["target"])
        owner = owner_for_decoded(records, target)
        rows.append(
            {
                "target": target,
                "count": int(item["count"]),
                "owner_record": owner["index"] if owner else None,
                "owner_decoded_start": owner["decoded_start"] if owner else None,
                "owner_decoded_span": owner["decoded_span"] if owner else None,
                "owner_operation_key": owner["operation_key"] if owner else None,
                "note": INTERESTING_XDATA.get(target, ""),
            }
        )
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    records = load_ld5m_records(args.record_map)
    f0 = args.f0.read_bytes()
    summaries = {
        str(index): record_summary(records, args.known_dir, f0, index)
        for index in args.records
    }
    rec59 = summaries["59"]
    rec59_calls = enrich_targets(records, rec59["immediates"]["lcalls"])
    rec59_jumps = enrich_targets(records, rec59["immediates"]["ljmps"])
    rec59_dptrs = enrich_targets(records, rec59["immediates"]["dptrs"])
    return {
        "schema": "liteon-rec59-static-neighborhood-v1",
        "records": summaries,
        "record59_call_targets": rec59_calls,
        "record59_jump_targets": rec59_jumps,
        "record59_dptr_targets": rec59_dptrs,
        "interpretation": [
            "Record 59's known decoded output is a controller-command bridge, not identity text.",
            "It copies CDB shadow bytes 0x8a4c..0x8a4e into controller argument registers 0x4011..0x4013.",
            "Its decoded code calls other CDD-overlay records, including record 5 at 0x0a65/0x0a6b and record 137 at 0xefb6.",
            "The source byte patched live, record-relative +0x400, did not alter visible chunk bytes in saved captures; it likely affects schedule/interleaver/control placement for this bridge neighborhood.",
        ],
    }


def fmt_hex(value: int | None, width: int = 0) -> str:
    if value is None:
        return "-"
    return f"0x{value:0{width}x}" if width else f"0x{value:x}"


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Record 59 Static Neighborhood")
    lines.append("")
    lines.append(
        "This note ties the record-59 live perturbation back to the decoded CDD "
        "runtime bytes. It is static analysis only."
    )
    lines.append("")
    lines.append("## Focus Records")
    lines.append("")
    lines.append("| record | source | len | decoded | span | mode | op key | known ranges | rel +0x400 |")
    lines.append("|---:|---:|---:|---:|---:|---:|---|---|---:|")
    for key in sorted(report["records"], key=lambda item: int(item)):
        row = report["records"][key]
        ranges = ", ".join(f"+{start:#x}..+{end - 1:#x}" for start, end in row["known_ranges"]) or "-"
        lines.append(
            "| {record} | `{source:#06x}` | `{source_len:#x}` | `+{decoded_start:#05x}` | "
            "`{decoded_span:#x}` | `{mode:#04x}` | `{operation_key}` | {ranges} | `{rel}` |".format(
                record=row["record"],
                source=row["source_start"],
                source_len=row["source_len"],
                decoded_start=row["decoded_start"],
                decoded_span=row["decoded_span"],
                mode=row["mode"],
                operation_key=row["operation_key"],
                ranges=ranges,
                rel=fmt_hex(row["source_rel_0x400"], 2),
            )
        )
    lines.append("")
    lines.append("## Record 59 Decoded Shape")
    lines.append("")
    lines.append(
        "The known output for record 59 is exactly one 192-byte contig at "
        "`+0x10..+0xcf`. The first function is a controller-command bridge:"
    )
    lines.append("")
    lines.append("- reads `xdata[0x8a29]`, swaps/masks the high nibble, and branches on bit 0;")
    lines.append("- copies or clamps CDB shadow byte `xdata[0x8a4c]` into `xdata[0x4011]`;")
    lines.append("- copies `xdata[0x8a4d]` and `xdata[0x8a4e]` into `xdata[0x4012]` and `xdata[0x4013]`;")
    lines.append("- copies `xdata[0x8a50..0x8a51]` into IRAM scratch around `0xa9..0xaa`;")
    lines.append("- sets an IRAM flag byte to `0x01`, calls `0xefb6`, advances `0x7c` twice, then returns.")
    lines.append("")
    lines.append(
        "The second visible function copies `0x8857/0x8858/0x84af/0x84b0` into "
        "`0x885d..0x8860`, writes command-like pairs through `0x8859/0x885a` "
        "and `0x893c`, then calls `0x0a65` and `0x0a6b`."
    )
    lines.append("")
    lines.append("## Record 59 Call Targets")
    lines.append("")
    lines.append("| target | count | owner record | owner decoded span | op key |")
    lines.append("|---:|---:|---:|---:|---|")
    for row in report["record59_call_targets"]:
        owner = "-" if row["owner_record"] is None else str(row["owner_record"])
        span = (
            "-"
            if row["owner_record"] is None
            else f"`+{row['owner_decoded_start']:#x}..+{row['owner_decoded_start'] + row['owner_decoded_span'] - 1:#x}`"
        )
        key = row["owner_operation_key"] or "-"
        lines.append(f"| `{row['target']:#06x}` | {row['count']} | {owner} | {span} | `{key}` |")
    lines.append("")
    lines.append(
        "This is a useful correction: the `0xefb6`, `0x0a65`, and `0x0a6b` "
        "targets are not useful resident-prefix disassembly targets. They are "
        "inside other CDD decoded records."
    )
    lines.append("")
    lines.append("## Interesting DPTR Immediates")
    lines.append("")
    lines.append("| dptr | count | note |")
    lines.append("|---:|---:|---|")
    for row in report["record59_dptr_targets"]:
        note = row["note"]
        if not note:
            continue
        lines.append(f"| `{row['target']:#06x}` | {row['count']} | {note} |")
    lines.append("")
    lines.append("## Practical Read")
    lines.append("")
    lines.extend(
        [
            "- Record 59 is now best treated as an update/response bridge control neighborhood, not a payload string or simple response buffer.",
            "- The live `0x28519: 0x68 -> 0x60` byte is record-relative `+0x400`. Saved captures showed chunk placement changes without byte changes, so it probably modified a CDD schedule/interleaver/control cell for this bridge neighborhood.",
            "- Because this same mutation blocked update entry on the previous drive, avoid record 58/59 writes on the spare unless the experiment explicitly needs that risk.",
            "- Safer static follow-up: target the call owners, especially record 137 around `0xefb6`, for read-only work-window harvests or source/known-output recovery. That may reveal the bridge submit routine without perturbing record 59 again.",
        ]
    )
    lines.append("")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-map", type=Path, default=DEFAULT_RECORD_MAP)
    parser.add_argument("--known-dir", type=Path, default=DEFAULT_KNOWN_DIR)
    parser.add_argument("--f0", type=Path, default=DEFAULT_F0)
    parser.add_argument("--json-out", type=Path, default=ROOT / "analysis/8051/rec59-static-neighborhood-20260501.json")
    parser.add_argument("--md-out", type=Path, default=ROOT / "analysis/8051/rec59-static-neighborhood-20260501.md")
    parser.add_argument("--records", type=int, nargs="*", default=list(FOCUS_RECORDS))
    args = parser.parse_args()

    report = build_report(args)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, args.md_out)
    print(args.md_out)
    print(args.json_out)


if __name__ == "__main__":
    main()
