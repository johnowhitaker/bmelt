#!/usr/bin/env python3
"""Plan a CDD mailbox replay from static DS-8ABSH firmware fields.

This is an offline planning tool. It reads a dumped 1 MiB F0 image and emits
the resident 8051 CDD-parser state we can derive statically. It does not open
or command a drive.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-cdd-mailbox-replay-plan.json"
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-cdd-mailbox-replay-plan.md"


def be16(data: bytes) -> int:
    return int.from_bytes(data, "big")


def be24(data: bytes) -> int:
    return int.from_bytes(data, "big")


def be32(data: bytes) -> int:
    return int.from_bytes(data, "big")


def word_bytes(value: int, width: int = 4) -> list[int]:
    return list(value.to_bytes(width, "big"))


def fmt_hex(value: int, width: int = 0) -> str:
    if width:
        return f"0x{value:0{width}x}"
    return f"0x{value:x}"


def byte_write(address: int, value: int, note: str) -> dict[str, Any]:
    value &= 0xFF
    return {
        "address": address,
        "address_hex": fmt_hex(address, 4),
        "value": value,
        "value_hex": fmt_hex(value, 2),
        "note": note,
    }


def u32_xdata_writes(address: int, value: int, note: str) -> list[dict[str, Any]]:
    return [
        byte_write(address + index, byte, note if index == 0 else f"{note} byte +{index}")
        for index, byte in enumerate(word_bytes(value, 4))
    ]


@dataclass(frozen=True)
class DescriptorFields:
    start: int
    length: int
    parser_base: int
    parser_window: int
    parser_source_size: int
    parser_target_size: int
    parser_mode_word: int
    decoded_start_a: int
    decoded_start_b: int
    decoded_end_exclusive: int
    cdd1_end: int
    cdd2_end: int
    final_boundary: int
    raw_hex: str


@dataclass(frozen=True)
class CddHeaderFields:
    start: int
    raw_hex: str
    byte6: int
    stream2_start: int
    directory_end: int
    controller_params: tuple[int, int, int]
    aux_len: int
    aux_len_code: int | None
    low_param: int
    final_boundary: int
    descriptor_start: int
    decoded_start: int
    decoded_end_inclusive_a: int
    decoded_end_inclusive_b: int


def find_cdd_starts(data: bytes) -> list[int]:
    starts: list[int] = []
    cursor = data.find(b"CDD\t")
    while cursor >= 0:
        starts.append(cursor)
        cursor = data.find(b"CDD\t", cursor + 1)
    return starts


def find_descriptor(data: bytes, cdd_start: int) -> DescriptorFields:
    for start in range(max(0, cdd_start - 0x100), cdd_start):
        length = be16(data[start : start + 2])
        if length >= 0x2C and start + length == cdd_start:
            raw = data[start:cdd_start]
            return DescriptorFields(
                start=start,
                length=length,
                parser_base=be32(raw[0x02:0x06]),
                parser_window=be32(raw[0x06:0x0A]),
                parser_source_size=be32(raw[0x0A:0x0E]),
                parser_target_size=be32(raw[0x0E:0x12]),
                parser_mode_word=be16(raw[0x12:0x14]),
                decoded_start_a=be32(raw[0x14:0x18]),
                decoded_start_b=be32(raw[0x18:0x1C]),
                decoded_end_exclusive=be32(raw[0x1C:0x20]),
                cdd1_end=be32(raw[0x20:0x24]),
                cdd2_end=be32(raw[0x24:0x28]),
                final_boundary=be32(raw[0x28:0x2C]),
                raw_hex=raw.hex(),
            )
    raise ValueError(f"no length-prefixed descriptor before CDD at {fmt_hex(cdd_start)}")


def parse_header(data: bytes, start: int) -> CddHeaderFields:
    raw = data[start : start + 0x20]
    if raw[:4] != b"CDD\t":
        raise ValueError(f"no CDD header at {fmt_hex(start)}")
    aux_len = (raw[0x10] & 0xF0) * 8
    aux_len_code_by_len = {0x80: 0, 0x100: 1, 0x200: 2, 0x400: 3}
    return CddHeaderFields(
        start=start,
        raw_hex=raw.hex(),
        byte6=raw[0x06],
        stream2_start=be24(raw[0x07:0x0A]),
        directory_end=be24(raw[0x0A:0x0D]),
        controller_params=(raw[0x0D], raw[0x0E], raw[0x0F]),
        aux_len=aux_len,
        aux_len_code=aux_len_code_by_len.get(aux_len),
        low_param=raw[0x10] & 0x0F,
        final_boundary=be24(raw[0x11:0x14]),
        descriptor_start=be24(raw[0x14:0x17]),
        decoded_start=be24(raw[0x17:0x1A]),
        decoded_end_inclusive_a=be24(raw[0x1A:0x1D]),
        decoded_end_inclusive_b=be24(raw[0x1D:0x20]),
    )


def u32_shr(value: int, bits: int) -> int:
    return (value & 0xFFFFFFFF) >> bits


def derive_plan(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    starts = find_cdd_starts(data)
    if not starts:
        raise ValueError("no CDD marker found")
    descriptor = find_descriptor(data, starts[0])
    header = parse_header(data, starts[0])

    # These names match the raw resident parser staging window around 0x4180
    # and FUN_CODE_002e.
    parser_prestage = {
        "0x8244..0x8247": descriptor.parser_base,
        "0x8248..0x824b": descriptor.parser_window,
        "0x824c..0x824f": descriptor.parser_source_size,
        "0x8250..0x8253": descriptor.parser_target_size,
        "0x8254..0x8255": descriptor.parser_mode_word,
    }

    early_status_fields = {
        "0x4e0d": u32_shr(descriptor.parser_window, 8) & 0xFF,
        "0x4e1a": u32_shr(descriptor.parser_target_size, 10) & 0xFF,
        "0x4e1c": 0 if descriptor.parser_mode_word == 0x8000 else 1,
        "0x60..0x61": (u32_shr(descriptor.parser_source_size, 10) - 1) & 0xFFFF,
    }

    header_pointer = descriptor.parser_base + descriptor.length
    header_window = 0xC000
    header_map_command = {
        "resident_range": "0x01ed..0x0252 then FUN_CODE_1717",
        "purpose": "map/read the 0x20-byte CDD header into XDATA window 0xc000",
        "xdata_0x8244_after_descriptor_len": header_pointer,
        "xdata_0x8256..0x8257": header_window,
        "selector": 2,
        "xdata_0x4e80": (2 << 21) + header_pointer,
        "xdata_0x4e84": (descriptor.parser_source_size - 0x100) & 0xFFFFFFFF,
        "xdata_0x4e88": 0x20,
        "doorbell": "xdata[0x4e8c] = 1, then poll xdata[0x4ea0] == 0x06",
        "note": (
            "0xc000 is not an F0 address. It is a mapped XDATA window; "
            "FUN_CODE_1717/FUN_CODE_16ef appear to configure that window "
            "before the parser reads CDD\\x09 from xdata[0xc000]."
        ),
    }

    mailbox_fields = {
        "0x4a00": 1,
        "0x4a01": header.aux_len_code,
        "0x4a02": 0,
        "0x4a03": header.byte6 & 0x03,
        "0x4a05": header.byte6 >> 2,
        "0x4a06": header.low_param,
        "0x4a20": header.controller_params[0],
        "0x4a21": header.controller_params[1],
        "0x4a22": header.controller_params[2],
        "0x8258..0x825b": header.stream2_start,
    }

    field_only_sequence = [
        byte_write(0x4A00, 0, "clear CDD mailbox doorbell before staging fields"),
        byte_write(0x4A01, header.aux_len_code or 0, "aux length code from header[0x10] high nibble"),
        byte_write(0x4A02, 0, "resident clears this byte before field package"),
        byte_write(0x4A03, header.byte6 & 0x03, "header[0x06] low two bits"),
        byte_write(0x4A05, header.byte6 >> 2, "header[0x06] upper six bits"),
        byte_write(0x4A06, header.low_param, "header[0x10] low nibble"),
        byte_write(0x4A20, header.controller_params[0], "header[0x0d] controller parameter"),
        byte_write(0x4A21, header.controller_params[1], "header[0x0e] controller parameter"),
        byte_write(0x4A22, header.controller_params[2], "header[0x0f] controller parameter"),
        *u32_xdata_writes(0x8258, header.stream2_start, "CDD2 absolute start from header[0x07..0x09]"),
        byte_write(0x4A00, 1, "ring CDD mailbox after staging fields"),
    ]

    suggested_samples = [
        {"kind": "xdata", "address": 0x4A00, "length": 0x30, "why": "CDD mailbox/result window, including 0x4a24..0x4a29"},
        {"kind": "xdata", "address": 0x4E00, "length": 0x30, "why": "nearby 0x4e status fields and 0x4e14/16/18/1a/1c/1e"},
        {"kind": "xdata", "address": 0x4EA0, "length": 0x01, "why": "cheap controller command status byte"},
        {"kind": "gateway", "address": header.decoded_start, "length": 0x100, "why": "advertised decoded CDD base"},
        {"kind": "gateway", "address": header.decoded_start + 0x60, "length": 0x100, "why": "first table-derived decoded target neighborhood"},
        {"kind": "gateway", "address": 0x190690, "length": 0x100, "why": "known affine group 27 oracle target from prior work"},
    ]

    candidate_replay_levels = [
        {
            "name": "field-only CDD mailbox",
            "description": (
                "Set only the header-derived 0x4a fields, then ring 0x4a00. "
                "This is the smallest useful successor to the failed single-byte doorbell test."
            ),
            "writes": mailbox_fields,
            "expected_if_sufficient": "decoded/controller memory near 0x184000 becomes nonzero or 0x4a24..0x4a29 updates",
            "risk": "low-to-medium; no 0x4e8c command issue, but it does ring the CDD mailbox",
            "ordered_byte_writes": field_only_sequence,
            "suggested_samples_after": suggested_samples,
        },
        {
            "name": "descriptor prestate plus field mailbox",
            "description": (
                "Preload 0x8244..0x825b and the early 0x4e status fields to mirror the resident parser, "
                "then ring the 0x4a mailbox."
            ),
            "writes": {**parser_prestage, **early_status_fields, **mailbox_fields},
            "expected_if_sufficient": "same as above, plus 0x4e status fields should match resident assumptions",
            "risk": "medium; still avoids direct 0x4e8c transfer commands",
        },
        {
            "name": "mapped-header command path",
            "description": (
                "Exercise the 0x4e80/84/88/8c path that normal code uses before it trusts xdata[0xc000] as a CDD header."
            ),
            "writes": header_map_command,
            "expected_if_sufficient": "xdata[0xc000..0xc01f] aliases or contains the CDD header, enabling the rest of the parser path",
            "risk": "high; this crosses into controller-memory command issuance, not just passive mailbox fields",
        },
    ]

    return {
        "image": str(path),
        "file_size": len(data),
        "cdd_starts": starts,
        "descriptor": asdict(descriptor),
        "cdd_header": asdict(header),
        "parser_prestage": parser_prestage,
        "early_status_fields": early_status_fields,
        "header_map_command": header_map_command,
        "header_mailbox_fields": mailbox_fields,
        "field_only_ordered_byte_writes": field_only_sequence,
        "suggested_samples_after_field_only": suggested_samples,
        "candidate_replay_levels": candidate_replay_levels,
        "static_conclusion": (
            "The previous xdata[0x4a00]=1 test skipped both the header-derived "
            "0x4a field package and the 0xc000 mapped-header setup. It is a "
            "valid negative for a trivial shortcut, but not a negative for the "
            "resident CDD handoff itself."
        ),
    }


def write_markdown(plan: dict[str, Any]) -> str:
    descriptor = plan["descriptor"]
    header = plan["cdd_header"]
    lines = [
        "# LiteOn CDD Mailbox Replay Plan",
        "",
        "Scope: static only. This file is generated from a dumped 1 MiB F0 image and does not command a drive.",
        "",
        f"Image: `{plan['image']}`",
        "",
        "## Descriptor Fields Used By Resident Code",
        "",
        "The CDD outer descriptor starts immediately before CDD1. The visible 8051 code at `0x12e0..0x13a0` and `0x4180..0x41de` uses the early descriptor fields before calling `FUN_CODE_002e`.",
        "",
        "| field | value | resident use |",
        "|---|---:|---|",
        f"| descriptor start | `{fmt_hex(descriptor['start'], 5)}` | length-prefixed descriptor |",
        f"| length | `{fmt_hex(descriptor['length'], 4)}` | added to parser base to locate CDD header |",
        f"| parser base | `{fmt_hex(descriptor['parser_base'], 8)}` | copied to `xdata[0x8244..0x8247]` |",
        f"| parser window | `{fmt_hex(descriptor['parser_window'], 8)}` | copied to `xdata[0x8248..0x824b]`; becomes `0x4e0d={fmt_hex(plan['early_status_fields']['0x4e0d'], 2)}` |",
        f"| parser source size | `{fmt_hex(descriptor['parser_source_size'], 8)}` | copied to `xdata[0x824c..0x824f]`; gives `0x60..0x61={fmt_hex(plan['early_status_fields']['0x60..0x61'], 4)}` |",
        f"| parser target size | `{fmt_hex(descriptor['parser_target_size'], 8)}` | copied to `xdata[0x8250..0x8253]`; becomes `0x4e1a={fmt_hex(plan['early_status_fields']['0x4e1a'], 2)}` |",
        f"| parser mode word | `{fmt_hex(descriptor['parser_mode_word'], 4)}` | copied to `xdata[0x8254..0x8255]`; gives `0x4e1c={fmt_hex(plan['early_status_fields']['0x4e1c'], 2)}` |",
        f"| decoded start | `{fmt_hex(descriptor['decoded_start_a'], 8)}` | advertised controller decoded range |",
        f"| decoded end exclusive | `{fmt_hex(descriptor['decoded_end_exclusive'], 8)}` | advertised controller decoded range |",
        "",
        "## CDD Header Package",
        "",
        f"CDD1 starts at `{fmt_hex(header['start'], 5)}`. After adding the descriptor length, the parser expects the header at `{fmt_hex(plan['header_map_command']['xdata_0x8244_after_descriptor_len'], 8)}`.",
        "",
        "| field | value | mailbox/register effect |",
        "|---|---:|---|",
        f"| header byte `0x06` | `{fmt_hex(header['byte6'], 2)}` | `0x4a03={fmt_hex(plan['header_mailbox_fields']['0x4a03'], 2)}`, `0x4a05={fmt_hex(plan['header_mailbox_fields']['0x4a05'], 2)}` |",
        f"| CDD2 start | `{fmt_hex(header['stream2_start'], 6)}` | `xdata[0x8258..0x825b]=0x00{header['stream2_start']:06x}` |",
        f"| controller params | `{bytes(header['controller_params']).hex()}` | `xdata[0x4a20..0x4a22]` |",
        f"| aux length | `{fmt_hex(header['aux_len'], 4)}` | `0x4a01={header['aux_len_code']}` |",
        f"| low param | `{fmt_hex(header['low_param'], 2)}` | `0x4a06={fmt_hex(plan['header_mailbox_fields']['0x4a06'], 2)}` |",
        f"| decoded range | `{fmt_hex(header['decoded_start'], 6)}..{fmt_hex(header['decoded_end_inclusive_a'], 6)}` | expected decoded/controller object |",
        "",
        "## Why The Doorbell-Only Test Was Too Small",
        "",
        "The earlier live test wrote only `xdata[0x4a00]=1`. The resident parser does not do that in isolation. Before or around that doorbell it:",
        "",
        "- validates descriptor fields and preloads `xdata[0x8244..0x8255]`;",
        "- derives `0x4e0d`, `0x4e1a`, `0x4e1c`, and the `0x60..0x61` count from descriptor sizes;",
        "- configures an XDATA mapped window at `0xc000` using the `0x4e80/0x4e84/0x4e88/0x4e8c` command path;",
        "- verifies `CDD\\x09 10 16` through that mapped window;",
        "- then writes the `0x4a01/03/05/06/20/21/22` field package and rings `0x4a00`.",
        "",
        "So `0x4a00=1` remains a useful negative for a trivial shortcut, but it does not prove the CDD engine cannot be started from currentboot.",
        "",
        "## Candidate Replay Levels",
        "",
    ]

    for item in plan["candidate_replay_levels"]:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                item["description"],
                "",
                f"Expected if sufficient: {item['expected_if_sufficient']}.",
                "",
                f"Risk: {item['risk']}.",
                "",
                "Static writes/fields:",
                "",
                "```json",
                json.dumps(item["writes"], indent=2, sort_keys=True),
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Practical Next Step",
            "",
            "If we do this live, the next useful experiment is the first replay level: write the header-derived `0x4a` fields plus `xdata[0x8258..0x825b]`, then set `0x4a00=1`, then sample `0x4a24..0x4a29`, `0x4a26..0x4a27`, `0x4ea0`, and the decoded CDD addresses. That adds the missing field package without yet issuing the higher-risk `0x4e8c` mapped-header command.",
            "",
            "Ordered byte writes for that field-only attempt:",
            "",
            "| address | value | note |",
            "|---:|---:|---|",
        ]
    )
    for write in plan["field_only_ordered_byte_writes"]:
        lines.append(f"| `{write['address_hex']}` | `{write['value_hex']}` | {write['note']} |")
    lines.extend(
        [
            "",
            "Suggested samples afterward:",
            "",
            "| kind | address | length | why |",
            "|---|---:|---:|---|",
        ]
    )
    for sample in plan["suggested_samples_after_field_only"]:
        width = 6 if sample["kind"] == "gateway" else 4
        lines.append(
            f"| {sample['kind']} | `{fmt_hex(sample['address'], width)}` | `{fmt_hex(sample['length'])}` | {sample['why']} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--print", action="store_true", help="print the Markdown report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = derive_plan(args.image)
    report = write_markdown(plan)
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(report + "\n")
    if args.print:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
