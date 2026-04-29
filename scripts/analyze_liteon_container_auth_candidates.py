#!/usr/bin/env python3
"""Compare LiteOn/PLDS F0 container authentication candidates.

This is offline-only. It reads already dumped/decrypted F0 images and never
opens an optical drive.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import zlib
from collections import Counter
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "references/firmware/extracted"

DEFAULT_LD5M = EXTRACTED / "ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_AD12 = EXTRACTED / "ad12-filedecrypt/AD12-1.bin"
DEFAULT_AHS9 = EXTRACTED / "windows-dump-filedecrypt/AHS9-postprocess-plain.bin"
DEFAULT_CHS7 = EXTRACTED / "windows-dump-filedecrypt/CHS7-postprocess-plain.bin"
DEFAULT_CHS9 = EXTRACTED / "windows-dump-filedecrypt/CHS9-postprocess-plain.bin"
DEFAULT_CD12 = EXTRACTED / "windows-dump-filedecrypt/CD12-postprocess-plain.bin"
DEFAULT_SENTINEL_D0000 = EXTRACTED / "ld5m-f0-window-0x00000-0x100000-sentinel-0xd0000-fe.bin"
DEFAULT_SENTINEL_27D4F = EXTRACTED / "ld5m-f0-window-0x00000-0x100000-sentinel-0x27d4f-3e.bin"
DEFAULT_OUT_JSON = EXTRACTED / "liteon-container-auth-candidates.json"
DEFAULT_OUT_MD = EXTRACTED / "liteon-container-auth-candidates.md"

VALID_IMAGE_NAMES = ("ld5m", "ad12", "ahs9", "chs7", "chs9", "cd12")
FAILED_IMAGE_NAMES = ("sentinel_0xd0000", "sentinel_0x27d4f")

F0_SIZE = 0x100000
PRE_FAMILY_WORD = (0x06FF0, 0x06FF4)
FAMILY_MARKER = (0x06FF8, 0x07000)
DESCRIPTOR = (0x07000, 0x0702C)
CDD1 = (0x0702C, None)
IDENTITY_PROFILE = (0x0D8FD0, 0x0D9000)
CDD2 = (0x0D9000, None)
TRAILER = (0x0E7FE0, 0x0E8000)
TRAILER_AUTH14 = (0x0E7FE0, 0x0E7FEE)
FINAL_ERASED = (0x0E8000, 0x100000)


def fmt_hex(value: int, width: int = 0) -> str:
    if width:
        return f"0x{value:0{width}x}"
    return f"0x{value:x}"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def printable(data: bytes, max_len: int = 64) -> str:
    out = []
    for byte in data[:max_len]:
        if 32 <= byte <= 126:
            out.append(chr(byte))
        elif byte == 0:
            out.append("\\x00")
        else:
            out.append(f"\\x{byte:02x}")
    if len(data) > max_len:
        out.append("...")
    return "".join(out)


def find_all(data: bytes, needle: bytes) -> list[int]:
    hits = []
    offset = data.find(needle)
    while offset >= 0:
        hits.append(offset)
        offset = data.find(needle, offset + 1)
    return hits


def find_ff_run_after(data: bytes, start: int, min_len: int = 0x1000) -> int:
    offset = start
    while offset < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        end = offset + 1
        while end < len(data) and data[end] == 0xFF:
            end += 1
        if end - offset >= min_len:
            return offset
        offset = end
    raise ValueError(f"no {fmt_hex(min_len)}-byte 0xff run after {fmt_hex(start)}")


def xor8(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def load_image(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) != F0_SIZE:
        raise ValueError(f"{path} has length {len(data)}, expected {F0_SIZE}")
    return data


def layout_for(data: bytes) -> dict[str, Any]:
    cdd_starts = find_all(data, b"CDD\t")
    if len(cdd_starts) != 2:
        raise ValueError(f"expected exactly two CDD starts, found {len(cdd_starts)}")
    cdd1_start, cdd2_start = cdd_starts
    cdd1_end = find_ff_run_after(data, cdd1_start)
    cdd2_end = find_ff_run_after(data, cdd2_start)
    descriptor = data[DESCRIPTOR[0] : DESCRIPTOR[1]]
    family_marker = data[FAMILY_MARKER[0] : FAMILY_MARKER[1]]
    return {
        "family_marker_hex": family_marker.hex(),
        "family_marker_text": printable(family_marker, len(family_marker)),
        "descriptor_length": int.from_bytes(descriptor[:2], "big"),
        "descriptor_hex": descriptor.hex(),
        "descriptor_fields": {
            "declared_length": int.from_bytes(descriptor[0x00:0x02], "big"),
            "base_or_header_ref": int.from_bytes(descriptor[0x02:0x06], "big"),
            "cdd_logical_start_1": int.from_bytes(descriptor[0x14:0x18], "big"),
            "cdd_logical_start_2": int.from_bytes(descriptor[0x18:0x1C], "big"),
            "cdd_logical_end_plus_1": int.from_bytes(descriptor[0x1C:0x20], "big"),
            "stream1_end": int.from_bytes(descriptor[0x20:0x24], "big"),
            "stream2_end": int.from_bytes(descriptor[0x24:0x28], "big"),
            "final_erased_start": int.from_bytes(descriptor[0x28:0x2C], "big"),
        },
        "cdd_streams": [
            {"start": cdd1_start, "end": cdd1_end, "length": cdd1_end - cdd1_start},
            {"start": cdd2_start, "end": cdd2_end, "length": cdd2_end - cdd2_start},
        ],
        "erased_gap_1": {"start": cdd1_end, "end": IDENTITY_PROFILE[0], "length": IDENTITY_PROFILE[0] - cdd1_end},
        "erased_gap_2": {"start": cdd2_end, "end": TRAILER[0], "length": TRAILER[0] - cdd2_end},
        "final_erased": {"start": FINAL_ERASED[0], "end": FINAL_ERASED[1], "length": FINAL_ERASED[1] - FINAL_ERASED[0]},
    }


def region_bytes(data: bytes, start: int, end: int) -> bytes:
    return data[start:end]


def region_summary(data: bytes, start: int, end: int, *, max_hex: int = 64) -> dict[str, Any]:
    blob = data[start:end]
    return {
        "start": start,
        "end": end,
        "length": end - start,
        "sha256": sha256(blob),
        "entropy": entropy(blob),
        "all_ff": all(byte == 0xFF for byte in blob),
        "hex": blob[:max_hex].hex() + ("..." if len(blob) > max_hex else ""),
        "text": printable(blob, max_hex),
    }


def named_regions(layout: dict[str, Any]) -> list[tuple[str, int, int]]:
    cdd1 = layout["cdd_streams"][0]
    cdd2 = layout["cdd_streams"][1]
    return [
        ("pre_family_word", PRE_FAMILY_WORD[0], PRE_FAMILY_WORD[1]),
        ("pre_family_padding", PRE_FAMILY_WORD[1], FAMILY_MARKER[0]),
        ("family_marker", FAMILY_MARKER[0], FAMILY_MARKER[1]),
        ("descriptor", DESCRIPTOR[0], DESCRIPTOR[1]),
        ("cdd_stream_1_prefix32", cdd1["start"], cdd1["start"] + 0x20),
        ("cdd_stream_1_full", cdd1["start"], cdd1["end"]),
        ("erased_gap_1", cdd1["end"], IDENTITY_PROFILE[0]),
        ("identity_profile", IDENTITY_PROFILE[0], IDENTITY_PROFILE[1]),
        ("cdd_stream_2_prefix32", cdd2["start"], cdd2["start"] + 0x20),
        ("cdd_stream_2_full", cdd2["start"], cdd2["end"]),
        ("erased_gap_2", cdd2["end"], TRAILER[0]),
        ("trailer_auth14", TRAILER_AUTH14[0], TRAILER_AUTH14[1]),
        ("trailer_gap_after_auth", TRAILER_AUTH14[1], 0x0E7FF5),
        ("trailer_du8a6s", 0x0E7FF5, 0x0E7FFB),
        ("trailer_marker_gap", 0x0E7FFB, 0x0E7FFC),
        ("trailer_lite", 0x0E7FFC, 0x0E8000),
        ("final_erased", FINAL_ERASED[0], FINAL_ERASED[1]),
    ]


def region_name_for_offset(layout: dict[str, Any], offset: int) -> str:
    for name, start, end in named_regions(layout):
        if start <= offset < end:
            return name
    return "unclassified"


def diff_offsets(base: bytes, candidate: bytes) -> list[dict[str, int]]:
    diffs = []
    for offset, (left, right) in enumerate(zip(base, candidate, strict=True)):
        if left != right:
            diffs.append({"offset": offset, "base": left, "candidate": right})
    return diffs


def image_ranges_for_digest(data: bytes, layout: dict[str, Any]) -> dict[str, bytes]:
    cdd1 = layout["cdd_streams"][0]
    cdd2 = layout["cdd_streams"][1]
    trailer_auth_zero = bytearray(data[: TRAILER[1]])
    trailer_auth_zero[TRAILER_AUTH14[0] : TRAILER_AUTH14[1]] = b"\x00" * (TRAILER_AUTH14[1] - TRAILER_AUTH14[0])
    trailer_auth_ff = bytearray(data[: TRAILER[1]])
    trailer_auth_ff[TRAILER_AUTH14[0] : TRAILER_AUTH14[1]] = b"\xff" * (TRAILER_AUTH14[1] - TRAILER_AUTH14[0])
    pre_family_zero = bytearray(data[: FAMILY_MARKER[0]])
    pre_family_zero[PRE_FAMILY_WORD[0] : PRE_FAMILY_WORD[1]] = b"\x00" * (PRE_FAMILY_WORD[1] - PRE_FAMILY_WORD[0])
    pre_family_ff = bytearray(data[: FAMILY_MARKER[0]])
    pre_family_ff[PRE_FAMILY_WORD[0] : PRE_FAMILY_WORD[1]] = b"\xff" * (PRE_FAMILY_WORD[1] - PRE_FAMILY_WORD[0])
    return {
        "prefix_to_pre_family_word": data[: PRE_FAMILY_WORD[0]],
        "prefix_to_family_marker": data[: FAMILY_MARKER[0]],
        "prefix_to_family_marker_prefield_zero": bytes(pre_family_zero),
        "prefix_to_family_marker_prefield_ff": bytes(pre_family_ff),
        "descriptor": data[DESCRIPTOR[0] : DESCRIPTOR[1]],
        "cdd_stream_1_full": data[cdd1["start"] : cdd1["end"]],
        "cdd_stream_1_body_after_prefix32": data[cdd1["start"] + 0x20 : cdd1["end"]],
        "cdd_stream_2_full": data[cdd2["start"] : cdd2["end"]],
        "cdd_stream_2_body_after_prefix32": data[cdd2["start"] + 0x20 : cdd2["end"]],
        "combined_cdd_streams": data[cdd1["start"] : cdd1["end"]] + data[cdd2["start"] : cdd2["end"]],
        "descriptor_and_cdd_streams": data[DESCRIPTOR[0] : DESCRIPTOR[1]] + data[cdd1["start"] : cdd1["end"]] + data[cdd2["start"] : cdd2["end"]],
        "container_to_trailer": data[DESCRIPTOR[0] : TRAILER[0]],
        "image_to_trailer": data[: TRAILER[0]],
        "image_to_e8000_with_trailer_auth": data[: TRAILER[1]],
        "image_to_e8000_trailer_auth_zero": bytes(trailer_auth_zero),
        "image_to_e8000_trailer_auth_ff": bytes(trailer_auth_ff),
    }


def digest_functions() -> dict[str, Callable[[bytes], bytes]]:
    return {
        "md5": lambda blob: hashlib.md5(blob, usedforsecurity=False).digest(),
        "sha1": lambda blob: hashlib.sha1(blob, usedforsecurity=False).digest(),
        "sha224": lambda blob: hashlib.sha224(blob).digest(),
        "sha256": lambda blob: hashlib.sha256(blob).digest(),
        "sha384": lambda blob: hashlib.sha384(blob).digest(),
        "sha512": lambda blob: hashlib.sha512(blob).digest(),
        "blake2s": lambda blob: hashlib.blake2s(blob).digest(),
        "blake2b": lambda blob: hashlib.blake2b(blob).digest(),
    }


def contiguous_digest_slices(digest: bytes, width: int) -> dict[str, bytes]:
    slices: dict[str, bytes] = {}
    if width > len(digest):
        return slices
    for offset in range(0, len(digest) - width + 1):
        slices[f"offset_{offset}"] = digest[offset : offset + width]
        slices[f"offset_{offset}_reversed"] = digest[offset : offset + width][::-1]
    return slices


def scalar_digest_values(blob: bytes) -> dict[str, bytes]:
    values = {
        "crc32_be": (zlib.crc32(blob) & 0xFFFFFFFF).to_bytes(4, "big"),
        "crc32_le": (zlib.crc32(blob) & 0xFFFFFFFF).to_bytes(4, "little"),
        "adler32_be": (zlib.adler32(blob) & 0xFFFFFFFF).to_bytes(4, "big"),
        "adler32_le": (zlib.adler32(blob) & 0xFFFFFFFF).to_bytes(4, "little"),
        "sum32_be": (sum(blob) & 0xFFFFFFFF).to_bytes(4, "big"),
        "sum32_le": (sum(blob) & 0xFFFFFFFF).to_bytes(4, "little"),
        "xor8": bytes([xor8(blob)]),
    }
    return values


def digest_probe(valid_images: dict[str, bytes], layouts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    field_specs = {
        "pre_family_word": PRE_FAMILY_WORD,
        "trailer_auth14": TRAILER_AUTH14,
    }
    fields = {
        image_name: {
            field_name: data[start:end]
            for field_name, (start, end) in field_specs.items()
        }
        for image_name, data in valid_images.items()
    }
    ranges = {
        image_name: image_ranges_for_digest(data, layouts[image_name])
        for image_name, data in valid_images.items()
    }
    matches = []
    for field_name in field_specs:
        width = len(next(iter(fields.values()))[field_name])
        for range_name in ranges["ld5m"]:
            for algo_name, algo in digest_functions().items():
                candidates = {
                    image_name: contiguous_digest_slices(algo(image_ranges[range_name]), width)
                    for image_name, image_ranges in ranges.items()
                }
                for slice_name in candidates["ld5m"]:
                    if all(candidates[image_name][slice_name] == fields[image_name][field_name] for image_name in valid_images):
                        matches.append(
                            {
                                "field": field_name,
                                "range": range_name,
                                "algorithm": algo_name,
                                "slice": slice_name,
                            }
                        )
            if width == 4:
                candidates = {
                    image_name: scalar_digest_values(image_ranges[range_name])
                    for image_name, image_ranges in ranges.items()
                }
                for scalar_name in candidates["ld5m"]:
                    if all(candidates[image_name][scalar_name] == fields[image_name][field_name] for image_name in valid_images):
                        matches.append(
                            {
                                "field": field_name,
                                "range": range_name,
                                "algorithm": scalar_name,
                                "slice": "scalar",
                            }
                        )
    return {
        "fields": {
            image_name: {field_name: value.hex() for field_name, value in image_fields.items()}
            for image_name, image_fields in fields.items()
        },
        "ranges_tested": list(ranges["ld5m"].keys()),
        "algorithms_tested": list(digest_functions().keys()) + ["crc32", "adler32", "sum32", "xor8"],
        "same_algorithm_matches": matches,
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    images = {
        "ld5m": {"path": args.ld5m, "data": load_image(args.ld5m), "kind": "valid"},
        "ad12": {"path": args.ad12, "data": load_image(args.ad12), "kind": "valid"},
        "ahs9": {"path": args.ahs9, "data": load_image(args.ahs9), "kind": "valid"},
        "chs7": {"path": args.chs7, "data": load_image(args.chs7), "kind": "valid"},
        "chs9": {"path": args.chs9, "data": load_image(args.chs9), "kind": "valid"},
        "cd12": {"path": args.cd12, "data": load_image(args.cd12), "kind": "valid_sibling"},
        "sentinel_0xd0000": {"path": args.sentinel_d0000, "data": load_image(args.sentinel_d0000), "kind": "failed_modified_ld5m"},
        "sentinel_0x27d4f": {"path": args.sentinel_27d4f, "data": load_image(args.sentinel_27d4f), "kind": "failed_modified_ld5m"},
    }
    layouts = {name: layout_for(item["data"]) for name, item in images.items()}
    ld5m = images["ld5m"]["data"]

    summaries: dict[str, Any] = {}
    for name, item in images.items():
        data = item["data"]
        layout = layouts[name]
        summaries[name] = {
            "path": str(item["path"]),
            "kind": item["kind"],
            "sha256": sha256(data),
            "reset_ljmp": int.from_bytes(data[1:3], "big") if data[0] == 0x02 else None,
            "layout": layout,
            "small_regions": {
                region_name: region_summary(data, start, end)
                for region_name, start, end in named_regions(layout)
                if end - start <= 0x100
            },
            "large_regions": {
                region_name: {
                    "start": start,
                    "end": end,
                    "length": end - start,
                    "sha256": sha256(data[start:end]),
                    "all_ff": all(byte == 0xFF for byte in data[start:end]),
                    "entropy": entropy(data[start:end]),
                }
                for region_name, start, end in named_regions(layout)
                if end - start > 0x100
            },
        }

    sentinel_diffs = {}
    auth_regions = [
        "pre_family_word",
        "family_marker",
        "descriptor",
        "cdd_stream_1_prefix32",
        "identity_profile",
        "cdd_stream_2_prefix32",
        "trailer_auth14",
        "trailer_du8a6s",
        "trailer_lite",
    ]
    ld5m_layout = layouts["ld5m"]
    ld5m_regions = {name: (start, end) for name, start, end in named_regions(ld5m_layout)}
    for name in FAILED_IMAGE_NAMES:
        diffs = diff_offsets(ld5m, images[name]["data"])
        sentinel_diffs[name] = {
            "diff_count": len(diffs),
            "diffs": [
                {
                    **diff,
                    "offset_hex": fmt_hex(diff["offset"]),
                    "base_hex": f"{diff['base']:02x}",
                    "candidate_hex": f"{diff['candidate']:02x}",
                    "region": region_name_for_offset(ld5m_layout, diff["offset"]),
                }
                for diff in diffs
            ],
            "auth_regions_equal_to_ld5m": {
                region_name: images[name]["data"][start:end] == ld5m[start:end]
                for region_name in auth_regions
                for start, end in [ld5m_regions[region_name]]
            },
        }

    valid_images = {name: images[name]["data"] for name in VALID_IMAGE_NAMES}
    valid_layouts = {name: layouts[name] for name in VALID_IMAGE_NAMES}
    return {
        "summary": {
            "hypothesis": "final persistence rejects staged images whose CDD/container auth material was not recomputed",
            "valid_images": list(VALID_IMAGE_NAMES),
            "failed_modified_ld5m_images": list(FAILED_IMAGE_NAMES),
        },
        "images": summaries,
        "sentinel_diffs": sentinel_diffs,
        "digest_probe": digest_probe(valid_images, valid_layouts),
    }


def write_json(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def short_hash(value: str) -> str:
    return value[:16]


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# LiteOn Container Auth Candidate Analysis")
    lines.append("")
    lines.append("Offline static analysis. No drive commands were sent.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    for name, image in report["images"].items():
        reset = image["reset_ljmp"]
        reset_text = fmt_hex(reset, 4) if reset is not None else "-"
        lines.append(
            f"- `{name}` `{image['path']}` kind=`{image['kind']}` "
            f"sha256=`{image['sha256']}` reset=`{reset_text}`"
        )
    lines.append("")
    lines.append("## Auth-Relevant Region Matrix")
    lines.append("")
    matrix_image_names = list(VALID_IMAGE_NAMES) + list(FAILED_IMAGE_NAMES)
    display_names = {
        "ld5m": "LD5M",
        "ad12": "AD12",
        "ahs9": "AHS9",
        "chs7": "CHS7",
        "chs9": "CHS9",
        "cd12": "CD12",
        "sentinel_0xd0000": "sentinel 0xd0000",
        "sentinel_0x27d4f": "sentinel 0x27d4f",
    }
    lines.append("| region | offsets | " + " | ".join(display_names[name] for name in matrix_image_names) + " |")
    lines.append("|---|---:|" + "|".join("---" for _ in matrix_image_names) + "|")
    key_regions = [
        "pre_family_word",
        "family_marker",
        "descriptor",
        "cdd_stream_1_prefix32",
        "identity_profile",
        "cdd_stream_2_prefix32",
        "trailer_auth14",
        "trailer_du8a6s",
        "trailer_lite",
    ]
    for region_name in key_regions:
        ld_region = report["images"]["ld5m"]["small_regions"][region_name]
        row = [region_name, f"`{fmt_hex(ld_region['start'])}..{fmt_hex(ld_region['end'])}`"]
        for image_name in matrix_image_names:
            region = report["images"][image_name]["small_regions"][region_name]
            if image_name == "ld5m":
                text = f"`{region['hex']}`"
            elif report["images"][image_name]["small_regions"][region_name]["sha256"] == ld_region["sha256"]:
                text = "same as LD5M"
            else:
                text = f"`{region['hex']}`"
            row.append(text)
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## Descriptor Boundary Fields")
    lines.append("")
    lines.append("| image | family | stream1 end | stream2 end | final erased | descriptor sha256 |")
    lines.append("|---|---|---:|---:|---:|---|")
    for image_name in matrix_image_names:
        image = report["images"][image_name]
        fields = image["layout"]["descriptor_fields"]
        family = image["layout"]["family_marker_text"]
        descriptor_hash = image["small_regions"]["descriptor"]["sha256"]
        lines.append(
            f"| `{image_name}` | `{family}` | `{fmt_hex(fields['stream1_end'])}` | "
            f"`{fmt_hex(fields['stream2_end'])}` | `{fmt_hex(fields['final_erased_start'])}` | "
            f"`{short_hash(descriptor_hash)}` |"
        )
    lines.append("")
    lines.append("## Sentinel Classification")
    lines.append("")
    for name, info in report["sentinel_diffs"].items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- diff count vs LD5M: `{info['diff_count']}`")
        for diff in info["diffs"]:
            lines.append(
                f"- `{diff['offset_hex']}` `{diff['base_hex']}` -> `{diff['candidate_hex']}` "
                f"in `{diff['region']}`"
            )
        unchanged = [region for region, equal in info["auth_regions_equal_to_ld5m"].items() if equal]
        changed = [region for region, equal in info["auth_regions_equal_to_ld5m"].items() if not equal]
        lines.append(f"- auth-ish fixed regions unchanged: `{len(unchanged)}/{len(info['auth_regions_equal_to_ld5m'])}`")
        if changed:
            lines.append(f"- changed auth-ish regions: {', '.join(f'`{region}`' for region in changed)}")
        lines.append("")
    lines.append("## Digest Probe")
    lines.append("")
    probe = report["digest_probe"]
    lines.append("- fields tested:")
    for image_name, fields in probe["fields"].items():
        lines.append(
            f"  - `{image_name}` pre-family=`{fields['pre_family_word']}` "
            f"trailer-auth14=`{fields['trailer_auth14']}`"
        )
    lines.append(f"- ranges tested: `{len(probe['ranges_tested'])}`")
    lines.append(f"- algorithms tested: `{', '.join(probe['algorithms_tested'])}`")
    if probe["same_algorithm_matches"]:
        lines.append("- same-algorithm field matches:")
        for match in probe["same_algorithm_matches"]:
            lines.append(
                f"  - field=`{match['field']}` range=`{match['range']}` "
                f"algorithm=`{match['algorithm']}` slice=`{match['slice']}`"
            )
    else:
        lines.append("- no same-algorithm match was found for the valid images against tested direct digest/checksum slices.")
    lines.append("")
    lines.append("## Working Interpretation")
    lines.append("")
    lines.append(
        "- The `0xd0000` sentinel changes an LD5M erased gap byte from `ff` to `fe`; "
        "that is a canonical layout violation before any deeper CDD authentication question."
    )
    lines.append(
        "- The `0x27d4f` sentinel changes CDD stream 1 while leaving the visible family word, "
        "descriptor, CDD prefixes, identity window, and trailer auth bytes unchanged. That is the stronger "
        "evidence for an unrecomputed CDD/container auth rule."
    )
    lines.append(
        "- The valid image set demonstrates the fields that move between accepted containers: the pre-family word, "
        "family marker, descriptor stream-end fields, CDD bodies, identity/profile text, and the 14 bytes at "
        "`0xe7fe0..0xe7fee`. The CHS7/CHS9 pair keeps the same pre-family word while changing trailer auth14."
    )
    lines.append(
        "- The tested direct CRC/adler/sum/xor/hash truncation models do not explain either the 4-byte "
        "`0x6ff0` word or the 14-byte trailer material across the valid images."
    )
    lines.append("")
    lines.append("Next static target: use the six valid containers to search for the transform behind the 4-byte pre-family word and 14-byte trailer material, then test whether an auth-preserving metadata-only mutation exists.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ld5m", type=Path, default=DEFAULT_LD5M)
    parser.add_argument("--ad12", type=Path, default=DEFAULT_AD12)
    parser.add_argument("--ahs9", type=Path, default=DEFAULT_AHS9)
    parser.add_argument("--chs7", type=Path, default=DEFAULT_CHS7)
    parser.add_argument("--chs9", type=Path, default=DEFAULT_CHS9)
    parser.add_argument("--cd12", type=Path, default=DEFAULT_CD12)
    parser.add_argument("--sentinel-d0000", type=Path, default=DEFAULT_SENTINEL_D0000)
    parser.add_argument("--sentinel-27d4f", type=Path, default=DEFAULT_SENTINEL_27D4F)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args)
    write_json(args.out_json, report)
    write_md(args.out_md, report)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
