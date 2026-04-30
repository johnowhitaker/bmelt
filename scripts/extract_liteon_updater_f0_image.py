#!/usr/bin/env python3
"""Extract the embedded F0 image from an unpacked LiteOn Windows updater.

This is an offline-only static-analysis helper. It does not talk to an optical
drive. The currently mapped AHS9 updater module stores a 1 MiB firmware object
at a fixed memory-image offset, encrypted with AES-ECB. The AES key is derived
from the 256-byte table that follows the `COPYF2K8_SIZE=...` marker:

    key[i] = table[(selector + i * 0x11) & 0xff]

where `selector` is the byte at table offset `0x58` for the observed AHS9
module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODULE = ROOT / "work/cdd-siblings/ahs9-updater-module.bin"
DEFAULT_COMPARE = ROOT / "work/cdd-siblings/AHS9-postprocess-plain.bin"
DEFAULT_OUT_BIN = ROOT / "work/updater-cdd-static/derived/AHS9-updater-aesecb-plain.bin"
DEFAULT_OUT_POSTPROCESS_BIN = ROOT / "work/updater-cdd-static/derived/AHS9-updater-f2k8-plain.bin"
DEFAULT_OUT_JSON = ROOT / "work/updater-cdd-static/derived/AHS9-updater-aesecb-report.json"
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-updater-f0-materialization-analysis.md"

FIRMWARE_SIZE = 0x100000
AHS9_SOURCE_OFFSET = 0x195DC0
COPYF2K8_PREFIX = b"COPYF2K8_SIZE="
KEY_TABLE_LENGTH = 0x100
SELECTOR_OFFSET_FROM_TABLE = 0x58
KEY_STRIDE = 0x11
MASK_WINDOW_SIZE = 0x1000
F2K8_BLOCK_SIZE = 0x400
SOURCE_BASE_DELTA = 0x1000
BIN_METADATA_PREFIXES = ("BIN_START", "BIN_SIZE", "NEW_FW", "NEW_BOOTFW")

MARKERS = {
    "CDD": b"CDD\t",
    "DU8A6S": b"DU8A6S",
    "LITE": b"LITE",
    "EXTRAINQ": b"EXTRAINQ",
    "DS-8ABSH": b"DS-8ABSH",
    "AHS9": b"AHS9",
    "S8AB0HS6": b"S8AB0HS6",
}


@dataclass(frozen=True)
class KeyDerivation:
    marker_offset: int
    table_offset: int
    selector_offset: int
    selector: int
    indexes: tuple[int, ...]
    key: bytes


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def parse_int(value: str) -> int:
    return int(value, 0)


def find_all(data: bytes, needle: bytes) -> list[int]:
    hits: list[int] = []
    offset = data.find(needle)
    while offset >= 0:
        hits.append(offset)
        offset = data.find(needle, offset + 1)
    return hits


def parse_decimal_field(data: bytes, name: bytes) -> int | None:
    marker = name + b"="
    offset = data.find(marker)
    if offset < 0:
        return None
    cursor = offset + len(marker)
    digits = bytearray()
    while cursor < len(data) and 0x30 <= data[cursor] <= 0x39:
        digits.append(data[cursor])
        cursor += 1
    if not digits:
        return None
    return int(digits.decode("ascii"), 10)


def parse_metadata(data: bytes) -> dict[str, Any]:
    start = data.find(b"BIN_START1=")
    if start < 0:
        raise ValueError("BIN_START1 metadata not found")

    fields: dict[str, str] = {}
    offset = start
    metadata_end = start
    while offset < len(data):
        end = data.find(b"\x00", offset)
        if end < 0:
            raise ValueError("unterminated metadata string")
        raw = data[offset:end]
        if not raw:
            offset = end + 1
            metadata_end = offset
            continue
        try:
            text = raw.decode("ascii")
        except UnicodeDecodeError:
            break
        if not text.startswith(BIN_METADATA_PREFIXES):
            break
        if "=" in text:
            key, value = text.split("=", 1)
            fields[key.strip()] = value.strip()
        offset = end + 1
        metadata_end = offset

    return {
        "start": start,
        "end": metadata_end,
        "fields": fields,
        "bin_start1": int(fields["BIN_START1"], 10) if "BIN_START1" in fields else None,
        "bin_size1b": int(fields["BIN_SIZE1B"], 10) if "BIN_SIZE1B" in fields else None,
    }


def new_fw_record_delta(data: bytes, metadata: dict[str, Any], slot_index: int = 0) -> dict[str, Any]:
    needle = f"NEW_FW{slot_index + 1}=".encode("ascii")
    offset = data.find(needle, int(metadata["start"]), int(metadata["end"]))
    if offset < 0:
        raise ValueError(f"{needle.decode('ascii')} metadata is missing")
    record_offset = offset + len(needle)
    record = data[record_offset : record_offset + 4]
    if len(record) != 4:
        raise ValueError("NEW_FW record is truncated")
    return {
        "slot_index": slot_index,
        "record_offset": record_offset,
        "record_first4": record,
        "record_text": record.decode("ascii", errors="replace"),
        "delta": sum(record) & 0xFF,
    }


def derive_key(data: bytes, *, table_offset: int | None, selector_offset: int | None) -> KeyDerivation:
    marker_offset = data.find(COPYF2K8_PREFIX)
    if marker_offset < 0 and table_offset is None:
        raise ValueError("COPYF2K8_SIZE marker was not found and no table offset was supplied")

    if table_offset is None:
        cursor = marker_offset + len(COPYF2K8_PREFIX)
        while cursor < len(data) and 0x30 <= data[cursor] <= 0x39:
            cursor += 1
        if cursor >= len(data) or data[cursor] != 0:
            raise ValueError("COPYF2K8_SIZE field is not NUL-terminated as expected")
        table_offset = cursor + 1

    if table_offset < 0 or table_offset + KEY_TABLE_LENGTH > len(data):
        raise ValueError(f"key table offset 0x{table_offset:x} is outside the module")

    if selector_offset is None:
        selector_offset = table_offset + SELECTOR_OFFSET_FROM_TABLE
    if selector_offset < 0 or selector_offset >= len(data):
        raise ValueError(f"selector offset 0x{selector_offset:x} is outside the module")

    table = data[table_offset : table_offset + KEY_TABLE_LENGTH]
    selector = data[selector_offset]
    indexes = tuple((selector + index * KEY_STRIDE) & 0xFF for index in range(16))
    key = bytes(table[index] for index in indexes)
    return KeyDerivation(
        marker_offset=marker_offset,
        table_offset=table_offset,
        selector_offset=selector_offset,
        selector=selector,
        indexes=indexes,
        key=key,
    )


def aes_ecb_decrypt(data: bytes, key: bytes) -> bytes:
    if len(data) % 16:
        raise ValueError("AES-ECB input must be 16-byte aligned")
    decryptor = Cipher(algorithms.AES(key), modes.ECB()).decryptor()
    return decryptor.update(data) + decryptor.finalize()


def f2k8_delta(block_index: int, table_byte: int, record_delta: int) -> int:
    if block_index % 7 in {0, 2}:
        return record_delta
    return table_byte


def apply_f2k8_mask(image: bytes, table: bytes, record_delta: int) -> tuple[bytes, list[dict[str, Any]]]:
    if len(image) % F2K8_BLOCK_SIZE:
        raise ValueError(f"image length is not 0x400-byte aligned: {len(image)}")
    block_count = len(image) // F2K8_BLOCK_SIZE
    if len(table) < block_count:
        raise ValueError(f"F2K8 mask table has {len(table)} bytes, need {block_count}")

    out = bytearray(image)
    patches: list[dict[str, Any]] = []
    for block_index in range(block_count):
        table_byte = table[block_index]
        rel = table_byte & 0x3F
        delta = f2k8_delta(block_index, table_byte, record_delta)
        absolute = block_index * F2K8_BLOCK_SIZE + rel
        old = out[absolute]
        out[absolute] ^= delta
        patches.append(
            {
                "block": block_index,
                "absolute": absolute,
                "relative_offset": rel,
                "table_byte": table_byte,
                "xor_delta": delta,
                "old": old,
                "new": out[absolute],
                "changed": old != out[absolute],
            }
        )
    return bytes(out), patches


def marker_hits(data: bytes) -> dict[str, list[int]]:
    return {name: find_all(data, marker) for name, marker in MARKERS.items()}


def find_ff_run_after(data: bytes, start: int, min_len: int = 0x1000) -> int:
    cursor = start
    while cursor < len(data):
        if data[cursor] != 0xFF:
            cursor += 1
            continue
        end = cursor + 1
        while end < len(data) and data[end] == 0xFF:
            end += 1
        if end - cursor >= min_len:
            return cursor
        cursor = end
    return len(data)


def cdd_streams(data: bytes, *, end_source: bytes | None = None) -> list[dict[str, Any]]:
    if end_source is None:
        end_source = data
    streams = []
    for index, start in enumerate(find_all(data, b"CDD\t"), start=1):
        end = find_ff_run_after(end_source, start)
        item: dict[str, Any] = {
            "index": index,
            "start": start,
            "end": end,
            "length": end - start,
        }
        if start + 0x20 <= len(data):
            header = data[start : start + 0x20]
            directory_end_field = int.from_bytes(header[0x0A:0x0D], "big")
            item.update(
                {
                    "directory_end_field": directory_end_field,
                    "directory_end_rel_if_absolute": directory_end_field - start,
                    "aux_len_guess": (header[0x10] & 0xF0) * 8,
                }
            )
        streams.append(item)
    return streams


def compare_images(left: bytes, right: bytes) -> dict[str, Any]:
    if len(left) != len(right):
        raise ValueError("comparison inputs must have equal length")
    diffs_by_chunk = []
    total_diffs = 0
    for chunk in range((len(left) + 0x3FF) // 0x400):
        base = chunk * 0x400
        chunk_diffs = []
        for offset, (a, b) in enumerate(zip(left[base : base + 0x400], right[base : base + 0x400], strict=False)):
            if a == b:
                continue
            chunk_diffs.append(
                {
                    "offset": offset,
                    "absolute": base + offset,
                    "left": a,
                    "right": b,
                    "xor": a ^ b,
                }
            )
        total_diffs += len(chunk_diffs)
        if chunk_diffs:
            diffs_by_chunk.append({"chunk": chunk, "diffs": chunk_diffs})

    single_byte_chunks = [item for item in diffs_by_chunk if len(item["diffs"]) == 1]
    first_diffs = [item["diffs"][0] for item in single_byte_chunks]
    return {
        "equal": left == right,
        "sha256_left": sha256(left),
        "sha256_right": sha256(right),
        "total_diffs": total_diffs,
        "chunks_with_diffs": len(diffs_by_chunk),
        "single_byte_diff_chunks": len(single_byte_chunks),
        "missing_diff_chunks": [
            chunk
            for chunk in range(len(left) // 0x400)
            if all(item["chunk"] != chunk for item in diffs_by_chunk)
        ],
        "diff_offset_min": min((item["offset"] for item in first_diffs), default=None),
        "diff_offset_max": max((item["offset"] for item in first_diffs), default=None),
        "top_diff_offsets": Counter(item["offset"] for item in first_diffs).most_common(12),
        "top_xors": Counter(item["xor"] for item in first_diffs).most_common(12),
        "sample_chunks": diffs_by_chunk[:24],
    }


def build_report(args: argparse.Namespace) -> tuple[bytes, dict[str, Any]]:
    module = args.module.read_bytes()
    metadata = parse_metadata(module)
    key_info = derive_key(module, table_offset=args.table_offset, selector_offset=args.selector_offset)
    size = args.size if args.size is not None else int(metadata["bin_size1b"] or FIRMWARE_SIZE)
    source_offset = args.source_offset
    if source_offset is None:
        source_offset = int(metadata["end"]) + SOURCE_BASE_DELTA if metadata["end"] else AHS9_SOURCE_OFFSET
    if source_offset < 0 or source_offset + size > len(module):
        raise ValueError(f"source span 0x{source_offset:x}..0x{source_offset + size:x} is outside the module")
    encrypted = module[source_offset : source_offset + size]
    raw_plain = aes_ecb_decrypt(encrypted, key_info.key)

    record_delta_info = new_fw_record_delta(module, metadata)
    mask_offset = int(metadata["end"])
    mask_window = module[mask_offset : mask_offset + MASK_WINDOW_SIZE]
    if len(mask_window) != MASK_WINDOW_SIZE:
        raise ValueError("F2K8 mask window is truncated")
    post_plain, patches = apply_f2k8_mask(raw_plain, mask_window, int(record_delta_info["delta"]))

    compare = None
    post_compare = None
    compare_plain = None
    if args.compare_plain and args.compare_plain.exists():
        compare_plain = args.compare_plain.read_bytes()
        compare = compare_images(raw_plain, compare_plain)
        post_compare = compare_images(post_plain, compare_plain)

    report = {
        "offline_only": True,
        "inputs": {
            "module": str(args.module),
            "module_size": len(module),
            "compare_plain": str(args.compare_plain) if args.compare_plain else None,
        },
        "embedded_params": {
            "metadata_start": metadata["start"],
            "metadata_end": metadata["end"],
            "fields": metadata["fields"],
            "bin_start1": metadata["bin_start1"],
            "bin_size1b": metadata["bin_size1b"],
        },
        "key_derivation": {
            "copyf2k8_marker_offset": key_info.marker_offset,
            "table_offset": key_info.table_offset,
            "selector_offset": key_info.selector_offset,
            "selector": key_info.selector,
            "stride": KEY_STRIDE,
            "indexes": list(key_info.indexes),
            "key_hex": key_info.key.hex(),
        },
        "decryption": {
            "source_offset": source_offset,
            "size": size,
            "encrypted_sha256": sha256(encrypted),
            "raw_plain_sha256": sha256(raw_plain),
            "raw_plain_entropy": entropy(raw_plain),
            "raw_plain_first16": raw_plain[:16].hex(),
            "raw_plain_last16": raw_plain[-16:].hex(),
            "raw_marker_hits": marker_hits(raw_plain),
            "postprocess_plain_sha256": sha256(post_plain),
            "postprocess_plain_entropy": entropy(post_plain),
            "postprocess_marker_hits": marker_hits(post_plain),
            "cdd_streams": cdd_streams(post_plain, end_source=compare_plain),
            "cdd_stream_end_source": str(args.compare_plain) if compare_plain is not None else "decrypted image",
            "pre_family_word": post_plain[0x6FF0:0x6FF4].hex() if len(post_plain) >= 0x7000 else None,
            "family_marker": post_plain[0x6FF8:0x7000].decode("ascii", errors="replace") if len(post_plain) >= 0x7000 else None,
            "trailer_auth14": post_plain[0xE7FE0:0xE7FEE].hex() if len(post_plain) >= 0xE7FEE else None,
        },
        "f2k8_postprocess": {
            "mask_offset": mask_offset,
            "mask_window_size": MASK_WINDOW_SIZE,
            "mask_sha256": sha256(mask_window),
            "mask_first64": mask_window[:64].hex(),
            "block_size": F2K8_BLOCK_SIZE,
            "block_count": len(raw_plain) // F2K8_BLOCK_SIZE,
            "record_delta_source": "sum(first four bytes of NEW_FW1) & 0xff",
            "record_delta_record": {
                **record_delta_info,
                "record_first4": record_delta_info["record_first4"].hex(),
            },
            "rule": "relative_offset=table[i]&0x3f; xor_delta=record_delta for i%7 in {0,2}, otherwise table[i]",
            "patch_count": len(patches),
            "changed_count": sum(1 for item in patches if item["changed"]),
            "unchanged_blocks": [item["block"] for item in patches if not item["changed"]],
            "first24_patches": patches[:24],
        },
        "module_marker_hits_before_decrypt": marker_hits(module),
        "compare_raw_aesecb_to_plain": compare,
        "compare_postprocess_to_plain": post_compare,
    }
    return raw_plain, post_plain, report


def fmt_hex(value: int | None) -> str:
    return "n/a" if value is None else f"0x{value:x}"


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# LiteOn Updater F0 Materialization Analysis",
        "",
        "Offline-only static analysis. No drive commands were sent.",
        "",
        "## What Was Checked",
        "",
        "The unpacked AHS9 Windows updater module was inspected for a point where",
        "the firmware/CDD payload exists in plaintext. The module does not contain",
        "raw `CDD\\t` strings before decryption, but it does contain an encrypted",
        "1 MiB F0 object plus the table-driven AES-ECB key schedule used to decrypt",
        "that object.",
        "",
        "## AHS9 Updater Extraction",
        "",
    ]
    kd = report["key_derivation"]
    dec = report["decryption"]
    f2k8 = report["f2k8_postprocess"]
    params = report["embedded_params"]
    lines.extend(
        [
            f"- `BIN_START1`: `{params['bin_start1']}`",
            f"- `BIN_SIZE1B`: `{params['bin_size1b']}`",
            f"- metadata range: `{fmt_hex(params['metadata_start'])}..{fmt_hex(params['metadata_end'])}`",
            f"- encrypted source offset: `{fmt_hex(dec['source_offset'])}`",
            f"- encrypted size: `{fmt_hex(dec['size'])}`",
            f"- `COPYF2K8_SIZE` marker offset: `{fmt_hex(kd['copyf2k8_marker_offset'])}`",
            f"- key table offset: `{fmt_hex(kd['table_offset'])}`",
            f"- selector offset: `{fmt_hex(kd['selector_offset'])}`",
            f"- selector: `0x{kd['selector']:02x}`",
            f"- derived AES-ECB key: `{kd['key_hex']}`",
            "",
            "Key derivation:",
            "",
            "```text",
            "key[i] = table[(selector + i * 0x11) & 0xff]",
            "```",
            "",
            "Marker scan before decrypt:",
            "",
        ]
    )
    before_hits = report.get("module_marker_hits_before_decrypt", {})
    for marker in ("CDD", "DU8A6S", "LITE", "EXTRAINQ", "AHS9", "S8AB0HS6"):
        hits = before_hits.get(marker, [])
        if hits:
            lines.append(f"- `{marker}`: " + ", ".join(f"`0x{hit:x}`" for hit in hits[:16]))
        else:
            lines.append(f"- `{marker}`: no hit")
    lines.extend(
        [
            "",
            "The AES-ECB decrypted object has the expected firmware markers:",
            "",
            "| marker | offsets |",
            "|---|---|",
        ]
    )
    for marker, hits in dec["raw_marker_hits"].items():
        if hits:
            lines.append(f"| `{marker}` | " + ", ".join(f"`0x{hit:x}`" for hit in hits) + " |")
    lines.extend(
        [
            "",
            "## COPYF2K8 Postprocess",
            "",
            "The AES-ECB output is not yet byte-identical to the final plain image.",
            "The updater applies a compact per-1KiB mask from the `0x1000` bytes",
            "immediately after the metadata block.",
            "",
            f"- mask offset: `{fmt_hex(f2k8['mask_offset'])}`",
            f"- block size: `{fmt_hex(f2k8['block_size'])}`",
            f"- block count: `{f2k8['block_count']}`",
            f"- NEW_FW record: `{f2k8['record_delta_record']['record_text']}`",
            f"- record delta: `0x{f2k8['record_delta_record']['delta']:02x}`",
            "",
            "Rule:",
            "",
            "```text",
            "table_byte = mask[block_index]",
            "relative_offset = table_byte & 0x3f",
            "xor_delta = record_delta if block_index % 7 in {0, 2} else table_byte",
            "image[block_index * 0x400 + relative_offset] ^= xor_delta",
            "```",
            "",
            f"- patches: `{f2k8['patch_count']}`",
            f"- patches that changed bytes: `{f2k8['changed_count']}`",
            f"- zero-delta/no-change blocks: `{', '.join(hex(item) for item in f2k8['unchanged_blocks'])}`",
            f"- postprocess SHA-256: `{dec['postprocess_plain_sha256']}`",
            "",
            "CDD streams visible after decrypt:",
            "",
            f"Stream-end guesses use `{dec['cdd_stream_end_source']}` when available, because",
            "the decrypted updater representation still has one sparse altered byte per",
            "`0x400` block and therefore does not contain fully canonical erased gaps.",
            "",
            "| stream | range | header dir field | aux guess |",
            "|---:|---:|---:|---:|",
        ]
    )
    for stream in dec["cdd_streams"]:
        lines.append(
            f"| {stream['index']} | `0x{stream['start']:05x}..0x{stream['end']:05x}` | "
            f"`0x{stream.get('directory_end_field', 0):05x}` | `0x{stream.get('aux_len_guess', 0):x}` |"
        )
    lines.extend(
        [
            "",
            "Other container fields:",
            "",
            f"- pre-family word: `{dec['pre_family_word']}`",
            f"- family marker: `{dec['family_marker']}`",
            f"- trailer auth14: `{dec['trailer_auth14']}`",
            f"- raw AES-ECB SHA-256: `{dec['raw_plain_sha256']}`",
            f"- postprocess SHA-256: `{dec['postprocess_plain_sha256']}`",
            "",
            "## Relationship To The Existing Plain AHS9 Sample",
            "",
        ]
    )
    raw_compare = report.get("compare_raw_aesecb_to_plain")
    post_compare = report.get("compare_postprocess_to_plain")
    if raw_compare is None:
        lines.append("No comparison image was supplied.")
    else:
        lines.extend(
            [
                f"- raw AES-ECB byte-identical: `{raw_compare['equal']}`",
                f"- raw AES-ECB total differing bytes: `{raw_compare['total_diffs']}`",
                f"- raw AES-ECB chunks with differences: `{raw_compare['chunks_with_diffs']}`",
                f"- raw AES-ECB single-byte-difference chunks: `{raw_compare['single_byte_diff_chunks']}`",
                f"- raw AES-ECB chunks with no difference: `{', '.join(hex(item) for item in raw_compare['missing_diff_chunks'][:24])}`",
                f"- raw AES-ECB differing byte offset inside each `0x400` block ranges `{fmt_hex(raw_compare['diff_offset_min'])}`..`{fmt_hex(raw_compare['diff_offset_max'])}`",
                f"- after COPYF2K8 byte-identical: `{post_compare['equal'] if post_compare else None}`",
                f"- after COPYF2K8 total differing bytes: `{post_compare['total_diffs'] if post_compare else None}`",
                "",
                "Top selected-byte positions:",
                "",
                "| offset in 0x400 block | count |",
                "|---:|---:|",
            ]
        )
        for offset, count in raw_compare["top_diff_offsets"]:
            lines.append(f"| `0x{offset:02x}` | {count} |")
        lines.extend(
            [
                "",
                "Top XOR deltas:",
                "",
                "| xor | count |",
                "|---:|---:|",
            ]
        )
        for value, count in raw_compare["top_xors"]:
            lines.append(f"| `0x{value:02x}` | {count} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The updater does materialize a CDD-bearing firmware object, but not as a",
            "separate decoded controller firmware. The CDD streams appear after the",
            "whole 1 MiB F0 object is AES-ECB decrypted. There is no evidence in this",
            "module that the Windows updater itself decodes or interprets the CDD body;",
            "that still looks like controller-side work.",
            "",
            "The remaining mismatch after AES-ECB is exactly the COPYF2K8 layer, and",
            "that layer now reproduces the existing AHS9 plain sample byte-for-byte.",
            "The updater still does not appear to decode the CDD body into controller",
            "runtime form; it materializes the sealed F0 container that the drive later",
            "hands to controller-side CDD machinery.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", type=Path, default=DEFAULT_MODULE, help="Unpacked updater module/memory image.")
    parser.add_argument("--source-offset", type=parse_int, default=None, help="Encrypted F0 source offset. Defaults to the mapped AHS9 offset.")
    parser.add_argument("--size", type=parse_int, default=None, help="Encrypted F0 size. Defaults to BIN_SIZE1B or 0x100000.")
    parser.add_argument("--table-offset", type=parse_int, default=None, help="Override key table offset.")
    parser.add_argument("--selector-offset", type=parse_int, default=None, help="Override selector byte offset.")
    parser.add_argument("--compare-plain", type=Path, default=DEFAULT_COMPARE, help="Optional known plain/postprocessed image for diff reporting.")
    parser.add_argument("--out-bin", type=Path, default=DEFAULT_OUT_BIN, help="Write decrypted image here.")
    parser.add_argument("--out-postprocess-bin", type=Path, default=DEFAULT_OUT_POSTPROCESS_BIN, help="Write COPYF2K8-postprocessed image here.")
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON, help="Write machine-readable report here.")
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD, help="Write markdown report here.")
    parser.add_argument("--no-write-bin", action="store_true", help="Do not write the decrypted image.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.module.exists():
        print(f"error: missing module: {args.module}", file=sys.stderr)
        return 1
    raw_plain, post_plain, report = build_report(args)
    if not args.no_write_bin:
        args.out_bin.parent.mkdir(parents=True, exist_ok=True)
        args.out_bin.write_bytes(raw_plain)
        args.out_postprocess_bin.parent.mkdir(parents=True, exist_ok=True)
        args.out_postprocess_bin.write_bytes(post_plain)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(args.out_md, report)

    print(f"module: {args.module}")
    print(f"key: {report['key_derivation']['key_hex']}")
    print(f"raw plain sha256: {report['decryption']['raw_plain_sha256']}")
    print(f"postprocess sha256: {report['decryption']['postprocess_plain_sha256']}")
    print(f"wrote report: {args.out_json}")
    print(f"wrote markdown: {args.out_md}")
    if not args.no_write_bin:
        print(f"wrote raw image: {args.out_bin}")
        print(f"wrote postprocess image: {args.out_postprocess_bin}")
    compare = report.get("compare_raw_aesecb_to_plain")
    if compare:
        print(f"raw comparison diffs: {compare['total_diffs']} bytes in {compare['chunks_with_diffs']} chunks")
    post_compare = report.get("compare_postprocess_to_plain")
    if post_compare:
        print(f"postprocess comparison diffs: {post_compare['total_diffs']} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
