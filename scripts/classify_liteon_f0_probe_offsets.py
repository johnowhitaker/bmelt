#!/usr/bin/env python3
"""Classify DS-8ABSH F0 offsets for live mutation planning.

This is offline-only. It reads an already dumped F0 image and never opens an
optical drive. The goal is to keep future helper-bypass probes away from
parser-critical CDD header/directory/table bytes.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from analyze_liteon_container_auth_candidates import (
    EXTRACTED,
    FINAL_ERASED,
    F0_SIZE,
    IDENTITY_PROFILE,
    TRAILER,
    TRAILER_AUTH14,
    fmt_hex,
    layout_for,
    load_image,
    printable,
    sha256,
)


DEFAULT_IMAGE = EXTRACTED / "ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_OUT_JSON = EXTRACTED / "liteon-f0-probe-target-map.json"
DEFAULT_OUT_MD = EXTRACTED / "liteon-f0-probe-target-map.md"

PRE_FAMILY_WORD = (0x06FF0, 0x06FF4)
PRE_FAMILY_PAD = (0x06FF4, 0x06FF8)
FAMILY_MARKER = (0x06FF8, 0x07000)
DESCRIPTOR = (0x07000, 0x0702C)
CDD_HEADER_LEN = 0x20
STREAM1_START = 0x0702C
STREAM1_BODY_START = STREAM1_START + CDD_HEADER_LEN
STREAM1_DIRECTORY_END = 0x07DEC
STREAM1_TABLE_END = 0x081EC
STREAM2_START = 0x0D9000
STREAM2_BODY_START = STREAM2_START + CDD_HEADER_LEN
STREAM2_DIRECTORY_END = 0x0D91A0
TRAILER_PAD = (0x0E7FEE, 0x0E7FF5)
TRAILER_DU8A6S = (0x0E7FF5, 0x0E7FFB)
TRAILER_MARKER_PAD = (0x0E7FFB, 0x0E7FFC)
TRAILER_LITE = (0x0E7FFC, 0x0E8000)
RECORD_SIZE = 8


@dataclass(frozen=True)
class Region:
    name: str
    start: int
    end: int
    risk: str
    advice: str
    evidence: str

    def contains(self, offset: int) -> bool:
        return self.start <= offset < self.end

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "length": self.end - self.start,
            "risk": self.risk,
            "advice": self.advice,
            "evidence": self.evidence,
        }


KNOWN_PROBES = [
    {
        "offset": 0x004F81,
        "mutation": "96 -> 97",
        "region": "resident/prefix",
        "outcome": "final GOOD, stayed LD5M, not persisted",
    },
    {
        "offset": 0x006F80,
        "mutation": "ff -> fe",
        "region": "low prefix/padding before family word",
        "outcome": "final GOOD, stayed LD5M, not persisted",
    },
    {
        "offset": 0x00704F,
        "mutation": "b5 -> b4",
        "region": "CDD stream 1 directory record 0",
        "outcome": "event 544 rc=99, finalizer status all ff, PLDS vanished until physical power-cycle",
    },
    {
        "offset": 0x027D4F,
        "mutation": "3f -> 3e",
        "region": "CDD stream 1 later body",
        "outcome": "persisted with helper-status bypass",
    },
    {
        "offset": 0x0D0000,
        "mutation": "ff -> fe",
        "region": "erased gap 1",
        "outcome": "rejected without bypass; canonical erased-gap violation",
    },
    {
        "offset": 0x0D8FF4,
        "mutation": "32 -> 33",
        "region": "identity/profile",
        "outcome": "persisted with helper-status bypass; not reflected in standard INQUIRY",
    },
    {
        "offset": 0x0E7000,
        "mutation": "ff -> fe",
        "region": "erased gap 2",
        "outcome": "rejected without bypass; canonical erased-gap violation",
    },
    {
        "offset": 0x0F0000,
        "mutation": "ff -> fe",
        "region": "final erased tail",
        "outcome": "admitted but not persisted; delayed F0 equals base",
    },
]


def make_regions(data: bytes) -> list[Region]:
    layout = layout_for(data)
    cdd1_end = layout["cdd_streams"][0]["end"]
    cdd2_end = layout["cdd_streams"][1]["end"]
    return [
        Region(
            "resident_prefix_before_preword",
            0x00000,
            PRE_FAMILY_WORD[0],
            "not-useful",
            "Do not use for helper-bypass proof; tested low-prefix bytes were not programmed.",
            "0x4f81 and 0x6f80 staged/finalized but did not persist.",
        ),
        Region(
            "pre_family_word",
            *PRE_FAMILY_WORD,
            "critical",
            "Avoid unless testing family/profile selection with a recovery plan.",
            "Visible auth/profile-adjacent word that varies across valid images.",
        ),
        Region(
            "pre_family_zero_pad",
            *PRE_FAMILY_PAD,
            "critical",
            "Avoid; pad is directly adjacent to the family marker and preword.",
            "Part of the pre-family/family-marker slot.",
        ),
        Region(
            "family_marker",
            *FAMILY_MARKER,
            "critical",
            "Avoid; this selects the visible family identity.",
            "Holds strings such as U8A60D5C/S8AB0D16.",
        ),
        Region(
            "outer_descriptor",
            *DESCRIPTOR,
            "critical",
            "Avoid for live mutation; descriptor fields drive stream boundaries.",
            "Descriptor contains CDD stream ends and final erased boundary.",
        ),
        Region(
            "cdd_stream1_header",
            STREAM1_START,
            STREAM1_BODY_START,
            "critical",
            "Avoid; resident parser checks CDD header magic/control bytes.",
            "0x002e validates CDD 09 10 16 and consumes header byte +0x10.",
        ),
        Region(
            "cdd_stream1_record_directory",
            STREAM1_BODY_START,
            STREAM1_DIRECTORY_END,
            "dangerous",
            "Avoid. This is where the 0x704f hard failure landed.",
            "436 eight-byte directory records; 0x704f is record 0 byte 3.",
        ),
        Region(
            "cdd_stream1_post_directory_table",
            STREAM1_DIRECTORY_END,
            STREAM1_TABLE_END,
            "dangerous",
            "Avoid until the CDD table format is understood.",
            "512 little-endian words with repeated/pointer-like structure.",
        ),
        Region(
            "cdd_stream1_later_body",
            STREAM1_TABLE_END,
            cdd1_end,
            "bypass-proven",
            "Usable only with the helper-status bypass and restore discipline.",
            "0x27d4f in this region persisted with the 0x32af helper patch.",
        ),
        Region(
            "erased_gap_1",
            cdd1_end,
            IDENTITY_PROFILE[0],
            "canonical-ff",
            "Avoid; changing all-ff gaps is a layout violation.",
            "0xd0000 was rejected without bypass and teaches little about useful mutation.",
        ),
        Region(
            "identity_profile",
            *IDENTITY_PROFILE,
            "bypass-proven",
            "Good for low-risk helper-bypass mechanics, but not for live INQUIRY changes.",
            "0xd8ff4 persisted with bypass; standard identity remained canonical LD5M.",
        ),
        Region(
            "cdd_stream2_header",
            STREAM2_START,
            STREAM2_BODY_START,
            "critical",
            "Avoid; stream 2 has the same checked CDD header shape.",
            "CDD header duplicates stream 1's header/control prefix.",
        ),
        Region(
            "cdd_stream2_prefix_directory",
            STREAM2_BODY_START,
            STREAM2_DIRECTORY_END,
            "dangerous",
            "Avoid. This directory is mirrored inside stream 1.",
            "48 eight-byte records at 0xd9020..0xd91a0 are copied at 0x7c6c..0x7dec.",
        ),
        Region(
            "cdd_stream2_later_body",
            STREAM2_DIRECTORY_END,
            cdd2_end,
            "unknown-cdd",
            "Treat as risky CDD payload unless paired with a known restore path.",
            "No helper-bypass persistence probe has targeted this later stream 2 body yet.",
        ),
        Region(
            "erased_gap_2",
            cdd2_end,
            TRAILER[0],
            "canonical-ff",
            "Avoid; changing all-ff gaps is a layout violation.",
            "0xe7000 was rejected without bypass and teaches little about useful mutation.",
        ),
        Region(
            "trailer_auth14",
            *TRAILER_AUTH14,
            "critical",
            "Avoid until the container seal/toolchain is understood.",
            "14-byte trailer material changes across valid images and resists known hash probes.",
        ),
        Region(
            "trailer_ff_pad",
            *TRAILER_PAD,
            "critical",
            "Avoid; pad is inside the trailer window immediately before DU8A6S/LITE.",
            "Part of the fixed trailer layout.",
        ),
        Region(
            "trailer_du8a6s",
            *TRAILER_DU8A6S,
            "critical",
            "Avoid; marker likely identifies the trailer/container.",
            "All valid DS-8ABSH samples preserve DU8A6S.",
        ),
        Region(
            "trailer_marker_pad",
            *TRAILER_MARKER_PAD,
            "critical",
            "Avoid; single pad byte between DU8A6S and LITE.",
            "Part of the fixed trailer marker area.",
        ),
        Region(
            "trailer_lite_marker",
            *TRAILER_LITE,
            "critical",
            "Avoid; resident parser explicitly checks LITE.",
            "0x40b2 seeds 0xe7ffc and requires ASCII LITE.",
        ),
        Region(
            "final_erased_tail",
            *FINAL_ERASED,
            "not-useful",
            "Not useful for persistence; mutations here are admitted but not programmed.",
            "0xf0000 was ignored/canonicalized after delayed F0 readback.",
        ),
    ]


def parse_offset(text: str) -> int:
    value = int(text, 0)
    if value < 0 or value >= F0_SIZE:
        raise argparse.ArgumentTypeError(f"offset {text!r} is outside 0..{fmt_hex(F0_SIZE - 1)}")
    return value


def record_context(offset: int, start: int) -> dict[str, Any]:
    rel = offset - start
    return {
        "record_index": rel // RECORD_SIZE,
        "record_offset": start + (rel // RECORD_SIZE) * RECORD_SIZE,
        "byte_in_record": rel % RECORD_SIZE,
    }


def classify_offset(data: bytes, regions: list[Region], offset: int) -> dict[str, Any]:
    region = next((item for item in regions if item.contains(offset)), None)
    if region is None:
        return {
            "offset": offset,
            "offset_hex": fmt_hex(offset, 5),
            "byte": data[offset],
            "byte_hex": f"{data[offset]:02x}",
            "region": "unclassified",
            "risk": "unknown",
            "advice": "No matching region rule.",
        }

    out: dict[str, Any] = {
        "offset": offset,
        "offset_hex": fmt_hex(offset, 5),
        "byte": data[offset],
        "byte_hex": f"{data[offset]:02x}",
        "region": region.name,
        "region_start": region.start,
        "region_end": region.end,
        "region_relative": offset - region.start,
        "risk": region.risk,
        "advice": region.advice,
        "evidence": region.evidence,
        "context_hex": data[max(0, offset - 8) : min(len(data), offset + 8)].hex(),
        "context_text": printable(data[max(0, offset - 8) : min(len(data), offset + 8)], 16),
    }

    if region.name == "cdd_stream1_record_directory":
        out["record_context"] = record_context(offset, STREAM1_BODY_START)
    elif region.name == "cdd_stream2_prefix_directory":
        out["record_context"] = record_context(offset, STREAM2_BODY_START)
    elif region.name.startswith("cdd_stream1"):
        out["cdd_stream_relative"] = offset - STREAM1_START
        out["cdd_body_relative"] = offset - STREAM1_BODY_START
    elif region.name.startswith("cdd_stream2"):
        out["cdd_stream_relative"] = offset - STREAM2_START
        out["cdd_body_relative"] = offset - STREAM2_BODY_START

    return out


def build_report(data: bytes, offsets: list[int]) -> dict[str, Any]:
    regions = make_regions(data)
    layout = layout_for(data)
    classified = [classify_offset(data, regions, offset) for offset in offsets]
    return {
        "inputs": {
            "image": str(DEFAULT_IMAGE),
            "image_sha256": sha256(data),
        },
        "layout": {
            "family_marker_text": layout["family_marker_text"],
            "stream1_start": STREAM1_START,
            "stream1_end": layout["cdd_streams"][0]["end"],
            "stream2_start": STREAM2_START,
            "stream2_end": layout["cdd_streams"][1]["end"],
            "final_erased_start": FINAL_ERASED[0],
        },
        "regions": [region.to_json() for region in regions],
        "known_probes": KNOWN_PROBES,
        "classified_offsets": classified,
        "next_live_guidance": [
            "After physical replug, first confirm read-only identity and recover if currentboot/0D5C.",
            "Do not retest 0x704f or any byte in 0x704c..0x81ec.",
            "Use 0xd8ff4 for helper-bypass mechanics because it is already proven persistent and easy to restore.",
            "Use 0x27d4f only when deliberately probing later CDD-body persistence with a base-restore plan.",
            "Do not use all-ff erased gaps or the 0xe8000..0x100000 tail for meaningful persistence tests.",
        ],
    }


def md_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    out = []
    for index, row in enumerate(rows):
        out.append("| " + " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)) + " |")
        if index == 0:
            out.append("| " + " | ".join("-" * widths[i] for i in range(len(row))) + " |")
    return out


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# LiteOn F0 Probe Target Map",
        "",
        "Offline static report. No drive commands were sent.",
        "",
        "## Inputs",
        "",
        f"- image: `{report['inputs']['image']}`",
        f"- sha256: `{report['inputs']['image_sha256']}`",
        f"- family marker: `{report['layout']['family_marker_text']}`",
        "",
        "## Practical Guidance",
        "",
    ]
    lines.extend(f"- {item}" for item in report["next_live_guidance"])

    lines.extend(
        [
            "",
            "## Region Map",
            "",
        ]
    )
    region_rows = [["region", "offsets", "risk", "advice"]]
    for region in report["regions"]:
        region_rows.append(
            [
                region["name"],
                f"`{fmt_hex(region['start'])}..{fmt_hex(region['end'])}`",
                f"`{region['risk']}`",
                region["advice"],
            ]
        )
    lines.extend(md_table(region_rows))

    lines.extend(
        [
            "",
            "## Known Live Probe Classification",
            "",
        ]
    )
    probe_rows = [["offset", "mutation", "region", "outcome"]]
    for probe in report["known_probes"]:
        probe_rows.append(
            [
                f"`{fmt_hex(probe['offset'])}`",
                f"`{probe['mutation']}`",
                probe["region"],
                probe["outcome"],
            ]
        )
    lines.extend(md_table(probe_rows))

    lines.extend(
        [
            "",
            "## Selected Offset Details",
            "",
        ]
    )
    detail_rows = [["offset", "byte", "region", "relative", "risk", "note"]]
    for item in report["classified_offsets"]:
        note = item["evidence"]
        if "record_context" in item:
            ctx = item["record_context"]
            note = (
                f"{note} Record {ctx['record_index']} at {fmt_hex(ctx['record_offset'])}, "
                f"byte {ctx['byte_in_record']}."
            )
        detail_rows.append(
            [
                f"`{item['offset_hex']}`",
                f"`{item['byte_hex']}`",
                item["region"],
                f"`{fmt_hex(item.get('region_relative', 0))}`",
                f"`{item['risk']}`",
                note,
            ]
        )
    lines.extend(md_table(detail_rows))

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The dangerous boundary is sharper now: `0x704f` was not just "
            "near the CDD stream, it was inside the first eight-byte record of "
            "the stream1 directory.",
            "- The proven helper-status bypass should be treated as a flash "
            "programming/status bypass, not as a CDD parser bypass. Parser-critical "
            "bytes can still wedge the drive before normal recovery scripts regain contact.",
            "- For the next live phase, keep mutation targets in already-proven "
            "late CDD or identity/profile areas until the CDD directory/table "
            "format is understood.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument(
        "offsets",
        nargs="*",
        type=parse_offset,
        default=[0x4F81, 0x6F80, 0x704F, 0x27D4F, 0xD0000, 0xD8FF4, 0xE7000, 0xF0000],
        help="F0 offsets to classify, decimal or 0x-prefixed hex",
    )
    parser.add_argument("--no-write", action="store_true", help="Print JSON to stdout instead of writing reports.")
    args = parser.parse_args()

    data = load_image(args.image)
    report = build_report(data, args.offsets)
    report["inputs"]["image"] = str(args.image)

    if args.no_write:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
