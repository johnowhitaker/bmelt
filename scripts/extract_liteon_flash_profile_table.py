#!/usr/bin/env python3
"""Extract the Dell/LiteOn updater flash-profile table.

This is an offline helper. It reads the DOS updater executable, parses the
autodata tables used by the profile-tail helpers, and emits a model of the
candidate profile-tail WRITE BUFFER length/arg choices. It does not talk to the
drive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPDATER = (
    ROOT
    / "references/firmware/DS-8ABSH_AD12/DS-8ABSH_AD12 FW utility/"
    / "DS-8ABSH_AD12 FW utility/DOS/DS-8ABSH_AD12_DOS.EXe"
)
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-flash-profile-table.json"
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-flash-profile-table.md"

AUTODATA_FILE_OFFSET = 0x42F54
PROFILE_ID_TABLE = 0x34820
PROFILE_GROUP_TABLE = 0x34DBC
PROFILE_BODY_BASE = 0x36B1C
PROFILE_ENTRY_COUNT = 0xEF


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def obj3_slice(data: bytes, offset: int, size: int) -> bytes:
    start = AUTODATA_FILE_OFFSET + offset
    end = start + size
    if start < 0 or end > len(data):
        raise ValueError(f"autodata slice outside updater: offset=0x{offset:x} size=0x{size:x}")
    return data[start:end]


def u32le(data: bytes, offset: int) -> int:
    return int.from_bytes(obj3_slice(data, offset, 4), "little")


def ascii_label(blob: bytes) -> str:
    matches = re.findall(rb"[ -~]{4,}", blob)
    if not matches:
        return ""
    label = matches[0].split(b"\x00", 1)[0]
    return label.decode("ascii", errors="replace")


def align16(value: int) -> int:
    return (value + 15) & ~15


def parse_profiles(data: bytes) -> list[dict[str, Any]]:
    raw_entries = [
        obj3_slice(data, PROFILE_ID_TABLE + index * 6, 6)
        for index in range(PROFILE_ENTRY_COUNT)
    ]
    lengths = [int.from_bytes(entry[4:6], "big") for entry in raw_entries]
    groups = [u32le(data, PROFILE_GROUP_TABLE + index * 4) for index in range(PROFILE_ENTRY_COUNT)]

    body_offsets: list[int] = []
    cursor = 0
    for index in range(PROFILE_ENTRY_COUNT):
        if index and groups[index] != groups[index - 1]:
            cursor += lengths[index - 1]
        body_offsets.append(cursor)

    profiles = []
    for index, entry in enumerate(raw_entries):
        body_offset = body_offsets[index]
        body_len = lengths[index]
        body = obj3_slice(data, PROFILE_BODY_BASE + body_offset, min(body_len, 0x100))
        profile_tail_mode = 1 if index > 1 else 2
        header_len = 6 if profile_tail_mode == 1 else 4
        suppress_header_len_add = index in {2, 3, 4}
        even_body_len = body_len + (body_len & 1)
        plain_tail_len = even_body_len
        if not suppress_header_len_add:
            plain_tail_len += header_len
        encrypted_tail_len = align16(plain_tail_len)
        aes_mac_appended_len = encrypted_tail_len + 0x10
        profiles.append(
            {
                "index": index,
                "profile_id_hex": entry[:4].hex(),
                "profile_id_bytes": list(entry[:4]),
                "record_length": body_len,
                "group": groups[index],
                "shared_group_with_previous": bool(index and groups[index] == groups[index - 1]),
                "body_offset": body_offset,
                "body_autodata_offset": PROFILE_BODY_BASE + body_offset,
                "body_preview_hex": body[:32].hex(),
                "body_label": ascii_label(body),
                "profile_tail_mode": profile_tail_mode,
                "profile_tail_arg": "0x7f" if profile_tail_mode == 1 else "0x00",
                "profile_tail_offset": "0x00000" if profile_tail_mode == 1 else "0x80000",
                "header_len": header_len,
                "suppress_header_len_add": suppress_header_len_add,
                "plain_tail_len_before_aes": plain_tail_len,
                "aes_padded_tail_len": encrypted_tail_len,
                "aes_plus_cmac_tail_len": aes_mac_appended_len,
            }
        )
    return profiles


def render_markdown(report: dict[str, Any], detail_count: int) -> str:
    profiles = report["profiles"]
    arg00 = [item for item in profiles if item["profile_tail_arg"] == "0x00"]
    arg7f = [item for item in profiles if item["profile_tail_arg"] == "0x7f"]
    lines = [
        "# LiteOn Flash Profile Table",
        "",
        "Offline extraction from the Dell/LiteOn DOS updater. No drive access.",
        "",
        "## Inputs",
        "",
        f"- updater: `{report['input']['path']}`",
        f"- sha256: `{report['input']['sha256']}`",
        "",
        "## Table Model",
        "",
        f"- profile entries: `{len(profiles)}`",
        f"- profile id table autodata offset: `0x{PROFILE_ID_TABLE:x}`",
        f"- group table autodata offset: `0x{PROFILE_GROUP_TABLE:x}`",
        f"- body base autodata offset: `0x{PROFILE_BODY_BASE:x}`",
        f"- arg 00 entries: `{len(arg00)}`",
        f"- arg 7f entries: `{len(arg7f)}`",
        "",
        "The profile-tail helpers match the first four bytes of the profile buffer",
        "against this table. Matched indices `0` and `1` choose `arg=0x00` with",
        "offset `0x80000`; later indices choose `arg=0x7f` with offset `0`.",
        "When `bAES` is active, the helper AES-CBC encrypts the tail, pads to a",
        "16-byte boundary, appends a one-shot CMAC block, and then sends the",
        "resulting length.",
        "",
        f"## First {min(detail_count, len(profiles))} Entries",
        "",
        "| idx | id | group | body len | arg | plain len | AES+CMAC len | label |",
        "|---:|---|---:|---:|---|---:|---:|---|",
    ]
    for item in profiles[:detail_count]:
        lines.append(
            f"| {item['index']} | `{item['profile_id_hex']}` | {item['group']} | "
            f"{item['record_length']} | `{item['profile_tail_arg']}` | "
            f"{item['plain_tail_len_before_aes']} | {item['aes_plus_cmac_tail_len']} | "
            f"{item['body_label']} |"
        )
    lines += [
        "",
        "## Current Limits",
        "",
        "- The table model explains how a matched profile id selects arg `0x00` versus arg `0x7f` and tail length.",
        "- The live drive's exact profile id has not been captured from this helper path yet.",
        "- Because most table entries select `arg=0x7f`, live profile-tail replay remains off limits until the matched profile id is known and a recovery path exists.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--updater", type=Path, default=DEFAULT_UPDATER)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--detail-count", type=int, default=32)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = args.updater.read_bytes()
    profiles = parse_profiles(data)
    report = {
        "status": "offline_model_only_no_drive_access",
        "input": {
            "path": str(args.updater),
            "length": len(data),
            "sha256": sha256(data),
        },
        "constants": {
            "autodata_file_offset": AUTODATA_FILE_OFFSET,
            "profile_id_table": PROFILE_ID_TABLE,
            "profile_group_table": PROFILE_GROUP_TABLE,
            "profile_body_base": PROFILE_BODY_BASE,
            "profile_entry_count": PROFILE_ENTRY_COUNT,
        },
        "profiles": profiles,
        "counts": {
            "profiles": len(profiles),
            "arg00_entries": sum(1 for item in profiles if item["profile_tail_arg"] == "0x00"),
            "arg7f_entries": sum(1 for item in profiles if item["profile_tail_arg"] == "0x7f"),
            "shared_group_entries": sum(1 for item in profiles if item["shared_group_with_previous"]),
        },
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report, args.detail_count) + "\n", encoding="utf-8")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    print(
        "profiles={profiles} arg00={arg00_entries} arg7f={arg7f_entries}".format(
            **report["counts"]
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}")
        raise SystemExit(1)
