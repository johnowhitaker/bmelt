#!/usr/bin/env python3
"""Offline structural analysis for LiteOn/PLDS CDD streams.

This script never opens an optical drive. It reads already dumped/postprocessed
1 MiB F0 images and summarizes the CDD stream grammar we have enough evidence
to model: headers, stream directories, the 0x400 post-directory table window,
recurring 12-byte motifs, and exact shifted matches between sibling images.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import zlib
from bisect import bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGES = [
    ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin",
    ROOT / "work/cdd-siblings/AD12-1.bin",
    ROOT / "work/cdd-siblings/AHS9-postprocess-plain.bin",
    ROOT / "work/cdd-siblings/CD12-postprocess-plain.bin",
    ROOT / "work/cdd-siblings/CHS7-postprocess-plain.bin",
    ROOT / "work/cdd-siblings/CHS9-postprocess-plain.bin",
    ROOT / "work/cdd-siblings/XD13-postprocess-plain.bin",
]

SHORT_OPERATION_KEYS = (bytes.fromhex("0d6840031a00"), bytes.fromhex("0c6000031800"))
SHORT_RM_MASKS = (0x00, 0x19, 0x32, 0x2B)
SHORT_RUN_MASKS = (0x00, 0x64, 0xC8, 0xAC)


@dataclass(frozen=True)
class CddStream:
    index: int
    start: int
    end: int
    data: bytes


@dataclass(frozen=True)
class CddImage:
    name: str
    path: Path
    data: bytes
    streams: tuple[CddStream, ...]


def image_name(path: Path) -> str:
    stem = path.name
    for suffix in (
        "-postprocess-plain.bin",
        "-f0-window-0x00000-0x100000.bin",
        "-1.bin",
        ".bin",
    ):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
    return stem.upper()


def sha256_prefix(data: bytes, width: int = 12) -> str:
    return hashlib.sha256(data).hexdigest()[:width]


def ascii_cell(data: bytes) -> str:
    return "".join(chr(byte) if 32 <= byte < 127 else f"\\x{byte:02x}" for byte in data)


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def find_all(data: bytes, needle: bytes) -> list[int]:
    hits: list[int] = []
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
    return len(data)


def load_image(path: Path) -> CddImage | None:
    if not path.exists() or path.stat().st_size != 0x100000:
        return None
    data = path.read_bytes()
    streams = tuple(
        CddStream(i + 1, start, find_ff_run_after(data, start), data[start : find_ff_run_after(data, start)])
        for i, start in enumerate(find_all(data, b"CDD\t"))
    )
    if not streams:
        return None
    return CddImage(image_name(path), path, data, streams)


def cdd1_directory_info(stream: CddStream) -> dict[str, int]:
    header = stream.data[:0x20]
    directory_end_abs = int.from_bytes(header[0x0A:0x0D], "big")
    directory_end_rel = directory_end_abs - stream.start
    entry_count = (directory_end_rel - 0x20) // 8
    aux_len = (header[0x10] & 0xF0) * 8
    nominal_body_start = directory_end_rel + aux_len
    return {
        "directory_end_abs": directory_end_abs,
        "directory_end_rel": directory_end_rel,
        "entry_count": entry_count,
        "aux_len": aux_len,
        "nominal_body_start": nominal_body_start,
        "nominal_body_len": len(stream.data) - nominal_body_start,
    }


def parse_outer_descriptor(image: CddImage) -> dict[str, int] | None:
    if not image.streams or image.streams[0].start < 2:
        return None
    stream1 = image.streams[0]
    # The first two descriptor bytes are a big-endian length; for DS-8ABSH
    # samples this places the descriptor immediately before CDD stream 1.
    for descriptor_start in range(max(0, stream1.start - 0x100), stream1.start):
        descriptor_len = int.from_bytes(image.data[descriptor_start : descriptor_start + 2], "big")
        if descriptor_len and descriptor_start + descriptor_len == stream1.start:
            descriptor = image.data[descriptor_start:stream1.start]
            if len(descriptor) >= 0x2C:
                return {
                    "start": descriptor_start,
                    "length": descriptor_len,
                    "decoded_start_a": int.from_bytes(descriptor[0x14:0x18], "big"),
                    "decoded_start_b": int.from_bytes(descriptor[0x18:0x1C], "big"),
                    "decoded_end": int.from_bytes(descriptor[0x1C:0x20], "big"),
                    "cdd1_end": int.from_bytes(descriptor[0x20:0x24], "big"),
                    "cdd2_end": int.from_bytes(descriptor[0x24:0x28], "big"),
                    "final_boundary": int.from_bytes(descriptor[0x28:0x2C], "big"),
                }
    return None


def parse_stream_header(stream: CddStream) -> dict[str, int]:
    header = stream.data[:0x20]
    return {
        "stream2_start": int.from_bytes(header[0x07:0x0A], "big"),
        "directory_end_abs": int.from_bytes(header[0x0A:0x0D], "big"),
        "control_quad": int.from_bytes(header[0x0D:0x11], "big"),
        "aux_len": (header[0x10] & 0xF0) * 8,
        "final_boundary": int.from_bytes(header[0x11:0x14], "big"),
        "descriptor_start": int.from_bytes(header[0x14:0x17], "big"),
        "decoded_start": int.from_bytes(header[0x17:0x1A], "big"),
        "decoded_end_inclusive_a": int.from_bytes(header[0x1A:0x1D], "big"),
        "decoded_end_inclusive_b": int.from_bytes(header[0x1D:0x20], "big"),
    }


def inferred_cdd2_body_start(image: CddImage) -> int | None:
    if len(image.streams) < 2:
        return None
    stream1, stream2 = image.streams[:2]
    return 0x20 + cdd2_duplicate_len(stream1, stream2)


def cdd2_duplicate_len(stream1: CddStream, stream2: CddStream) -> int:
    duplicate_len = 0
    while (
        0x20 + duplicate_len < len(stream2.data)
        and 0xC40 + duplicate_len < len(stream1.data)
        and stream2.data[0x20 + duplicate_len] == stream1.data[0xC40 + duplicate_len]
    ):
        duplicate_len += 1
    return duplicate_len


def cdd1_source_start_rel(image: CddImage) -> int | None:
    if not image.streams:
        return None
    sources = directory_source_addresses(image.streams[0])
    if not sources:
        return None
    return sources[0] - image.streams[0].start


def cdd2_source_start_rel(image: CddImage) -> int | None:
    if len(image.streams) < 2:
        return None
    sources = directory_source_addresses(image.streams[0])
    if len(sources) <= 388:
        return None
    return sources[388] - image.streams[1].start


def cdd1_table_window(image: CddImage) -> bytes:
    if not image.streams:
        return b""
    info = cdd1_directory_info(image.streams[0])
    source_start_rel = cdd1_source_start_rel(image)
    if source_start_rel is None or source_start_rel <= info["directory_end_rel"]:
        return b""
    return image.streams[0].data[info["directory_end_rel"] : source_start_rel]


def cdd1_table_words(image: CddImage) -> list[int]:
    table = cdd1_table_window(image)
    return [int.from_bytes(table[offset : offset + 2], "little") for offset in range(0, len(table) - 1, 2)]


def table_word_band(word: int) -> str:
    if word < 0x0800:
        return "low"
    if word < 0x1800:
        return "mid"
    return "high"


def table_target_record_range(targets: list[dict[str, int | None]]) -> str:
    records = [int(target["record_index"]) for target in targets if target["record_index"] is not None]
    if not records:
        return ""
    return f"{min(records)}..{max(records)}"


def ratio_rows(image: CddImage) -> list[tuple[str, int, float]]:
    descriptor = parse_outer_descriptor(image)
    if descriptor is None:
        return []
    decoded_len = descriptor["decoded_end"] - descriptor["decoded_start_a"]
    if decoded_len <= 0:
        return []
    stream1 = image.streams[0]
    info1 = cdd1_directory_info(stream1)
    stream2_body_start = inferred_cdd2_body_start(image)
    cdd_total = sum(len(stream.data) for stream in image.streams)
    source_start_rel = cdd1_source_start_rel(image)
    cdd_body_total = len(stream1.data) - source_start_rel if source_start_rel is not None else 0
    if stream2_body_start is not None and len(image.streams) >= 2:
        cdd_body_total += len(image.streams[1].data) - stream2_body_start
    rows = [
        ("descriptor object", descriptor["final_boundary"] - descriptor["start"]),
        ("CDD streams", cdd_total),
        ("CDD bodies", cdd_body_total),
        ("CDD1 source body", len(stream1.data) - source_start_rel if source_start_rel is not None else 0),
    ]
    if stream2_body_start is not None and len(image.streams) >= 2:
        rows.append(("CDD2 source body", len(image.streams[1].data) - stream2_body_start))
    entries = directory_entries(stream1)
    if entries:
        pointers = [entry[6] | (entry[7] << 8) for entry in entries]
        rows.extend(
            [
                ("directory pointer span", pointers[-1] - pointers[0]),
                ("directory final pointer", pointers[-1]),
                ("directory entry388 pointer", pointers[388]),
            ]
        )
    return [(label, size, size / decoded_len) for label, size in rows]


def top_sliding_motif(data: bytes, width: int = 12) -> tuple[bytes, int]:
    if len(data) < width:
        return b"", 0
    counts = Counter(data[offset : offset + width] for offset in range(len(data) - width + 1))
    return counts.most_common(1)[0]


def motif_runs_13(data: bytes, motif: bytes) -> list[tuple[int, int, bytes]]:
    runs: list[tuple[int, int, bytes]] = []
    offset = 0
    while offset + len(motif) <= len(data):
        if data[offset : offset + len(motif)] != motif:
            offset += 1
            continue
        cursor = offset
        pads = bytearray()
        while cursor + len(motif) <= len(data) and data[cursor : cursor + len(motif)] == motif:
            if cursor + len(motif) < len(data):
                pads.append(data[cursor + len(motif)])
            cursor += len(motif) + 1
        if len(pads) > 1:
            runs.append((offset, len(pads), bytes(pads)))
        offset = max(cursor, offset + 1)
    return sorted(runs, key=lambda item: item[1], reverse=True)


def directory_entries(stream: CddStream) -> list[bytes]:
    info = cdd1_directory_info(stream)
    if info["entry_count"] <= 0:
        return []
    return [
        stream.data[0x20 + index * 8 : 0x28 + index * 8]
        for index in range(info["entry_count"])
    ]


def directory_source_addresses(stream: CddStream) -> list[int]:
    # The final little-endian word is a 16-byte paragraph address. The high
    # nibble of byte 5 supplies the low address nibble. This maps directory
    # entries directly into the CDD object.
    return [((entry[6] | (entry[7] << 8)) << 4) | (entry[5] >> 4) for entry in directory_entries(stream)]


def common_source_template(entries: list[bytes]) -> tuple[bytes, int]:
    if not entries:
        return b"", 0
    counts = Counter(entry[:5] for entry in entries)
    return counts.most_common(1)[0]


def source_segments(image: CddImage) -> list[tuple[int, int, int, bytes]]:
    if len(image.streams) < 2:
        return []
    entries = directory_entries(image.streams[0])
    starts = directory_source_addresses(image.streams[0])
    segments: list[tuple[int, int, int, bytes]] = []
    for index, start in enumerate(starts):
        if index < 387:
            end = starts[index + 1]
        elif index == 387:
            end = image.streams[0].end
        elif index < len(starts) - 1:
            end = starts[index + 1]
        else:
            end = image.streams[1].end
        segments.append((index, start, end, entries[index]))
    return segments


def operation_key(entry: bytes) -> bytes:
    # Byte 5 is split: the high nibble is the low source-address nibble,
    # while the low nibble stays stable with the non-source record fields.
    return entry[:5] + bytes([entry[5] & 0x0F])


def decoded_span_from_key(key: bytes) -> int:
    # The low six bits of operation-key byte 3 behave like a decoded/output
    # span in 16-byte paragraphs. This is not a full decoder yet, but the sums
    # line up tightly with the explicit 0x30000 decoded controller range.
    return (key[3] & 0x3F) << 4


def decoded_span_candidate(entry: bytes) -> int:
    return decoded_span_from_key(operation_key(entry))


def segment_for_offset(image: CddImage, offset: int) -> tuple[int, int, int, bytes] | None:
    for segment in source_segments(image):
        _, start, end, _ = segment
        if start <= offset < end:
            return segment
    return None


def exact_matches(a: bytes, b: bytes, seed: int = 16, limit: int = 10) -> list[tuple[int, int, int, int]]:
    table: defaultdict[bytes, list[int]] = defaultdict(list)
    for offset in range(0, len(a) - seed + 1):
        table[a[offset : offset + seed]].append(offset)

    runs: list[tuple[int, int, int, int]] = []
    for right in range(0, len(b) - seed + 1):
        for left in table.get(b[right : right + seed], []):
            if left > 0 and right > 0 and a[left - 1] == b[right - 1]:
                continue
            length = 0
            while left + length < len(a) and right + length < len(b) and a[left + length] == b[right + length]:
                length += 1
            if length >= seed:
                runs.append((length, left, right, right - left))
    return sorted(runs, reverse=True)[:limit]


def common_prefix_len(left: bytes, right: bytes) -> int:
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def same_index_segment_matches(left: CddImage, right: CddImage, limit: int = 8) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    left_segments = source_segments(left)
    right_segments = source_segments(right)
    for (index, left_start, left_end, left_entry), (_, right_start, right_end, right_entry) in zip(
        left_segments, right_segments
    ):
        left_data = left.data[left_start:left_end]
        right_data = right.data[right_start:right_end]
        rows.append(
            {
                "index": index,
                "prefix": common_prefix_len(left_data, right_data),
                "left_start": left_start,
                "right_start": right_start,
                "left_len": left_end - left_start,
                "right_len": right_end - right_start,
                "entry_diff": sum(a != b for a, b in zip(left_entry, right_entry)),
                "left_entry": left_entry.hex(),
                "right_entry": right_entry.hex(),
            }
        )
    return sorted(rows, key=lambda row: (int(row["prefix"]), -int(row["entry_diff"])), reverse=True)[:limit]


def same_index_operation_summary(left: CddImage, right: CddImage) -> dict[str, object]:
    rows = []
    full_match = 0
    op_match = 0
    source_only_change = 0
    op_same_len = 0
    for (index, left_start, left_end, left_entry), (_, right_start, right_end, right_entry) in zip(
        source_segments(left), source_segments(right)
    ):
        left_op = operation_key(left_entry)
        right_op = operation_key(right_entry)
        full = left_entry == right_entry
        same_op = left_op == right_op
        full_match += int(full)
        op_match += int(same_op)
        source_only_change += int(same_op and not full)
        if same_op:
            op_same_len += int((left_end - left_start) == (right_end - right_start))
            rows.append(
                {
                    "index": index,
                    "source_delta": left_start - right_start,
                    "left_len": left_end - left_start,
                    "right_len": right_end - right_start,
                    "left_entry": left_entry.hex(),
                    "right_entry": right_entry.hex(),
                }
            )
    return {
        "full_match": full_match,
        "op_match": op_match,
        "op_same_len": op_same_len,
        "source_only_change": source_only_change,
        "deltas": Counter(int(row["source_delta"]) for row in rows).most_common(6),
        "examples": [row for row in rows if int(row["source_delta"]) != 0][:6],
    }


def operation_length_rows(images: list[CddImage]) -> list[dict[str, object]]:
    by_key: defaultdict[bytes, list[tuple[str, int, int, int, bytes]]] = defaultdict(list)
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        for index, start, end, entry in source_segments(image):
            by_key[operation_key(entry)].append((image.name, index, end - start, start, entry))

    rows: list[dict[str, object]] = []
    for key, items in by_key.items():
        lengths = Counter(item[2] for item in items)
        rows.append(
            {
                "key": key,
                "count": len(items),
                "lengths": lengths,
                "indices": sorted({item[1] for item in items}),
                "images": sorted({item[0] for item in items}),
                "examples": items[:4],
            }
        )
    return sorted(rows, key=lambda row: (int(row["count"]), next(iter(row["lengths"]))), reverse=True)


def operation_length_base_rows(images: list[CddImage]) -> list[tuple[str, int, int, str, int]]:
    rows: list[tuple[str, int, int, str, int]] = []
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        for index, start, end, entry in source_segments(image):
            key = operation_key(entry)
            base = int.from_bytes(key[2:4], "little") >> 4
            rows.append((image.name, index, end - start, key.hex(), (end - start) - base))
    return rows


def decoded_span_summaries(images: list[CddImage]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        cdd1_span = 0
        cdd2_span = 0
        source_len = 0
        for index, start, end, entry in source_segments(image):
            span = decoded_span_candidate(entry)
            if index < 388:
                cdd1_span += span
            else:
                cdd2_span += span
            source_len += end - start
        total = cdd1_span + cdd2_span
        rows.append(
            {
                "image": image.name,
                "total": total,
                "delta": total - 0x30000,
                "cdd1": cdd1_span,
                "cdd2": cdd2_span,
                "source_len": source_len,
                "ratio": source_len / total if total else 0.0,
            }
        )
    return rows


def decoded_candidate_starts(image: CddImage) -> list[int]:
    starts: list[int] = []
    cursor = 0
    for _, _, _, entry in source_segments(image):
        starts.append(cursor)
        cursor += decoded_span_candidate(entry)
    return starts


def decoded_offset_delta_runs(left: CddImage, right: CddImage) -> list[tuple[int, int, int, int]]:
    left_starts = decoded_candidate_starts(left)
    right_starts = decoded_candidate_starts(right)

    left_segments = source_segments(left)
    right_segments = source_segments(right)
    runs: list[tuple[int, int, int, int]] = []
    index = 0
    while index < min(len(left_segments), len(right_segments)):
        if operation_key(left_segments[index][3]) != operation_key(right_segments[index][3]):
            index += 1
            continue
        delta = right_starts[index] - left_starts[index]
        end = index
        while (
            end < min(len(left_segments), len(right_segments))
            and operation_key(left_segments[end][3]) == operation_key(right_segments[end][3])
            and right_starts[end] - left_starts[end] == delta
        ):
            end += 1
        runs.append((end - index, index, end, delta))
        index = end
    return sorted(runs, reverse=True)


def cdd1_table_interval_summary(image: CddImage) -> dict[str, object]:
    table_targets = cdd1_table_targets(image)
    hit_records: Counter[int] = Counter()
    hit_rels: Counter[int] = Counter()
    misses = 0
    for target in table_targets:
        if target["record_index"] is None:
            misses += 1
        else:
            hit_records[int(target["record_index"])] += 1
            hit_rels[int(target["record_rel"])] += 1
    return {
        "words": len(table_targets),
        "hits": sum(hit_records.values()),
        "misses": misses,
        "records": hit_records.most_common(6),
        "rels": hit_rels.most_common(6),
    }


def cdd1_table_repeated_runs(image: CddImage, min_len: int = 2) -> list[dict[str, int | None]]:
    targets = cdd1_table_targets(image)
    runs: list[dict[str, int | None]] = []
    index = 0
    while index < len(targets):
        end = index + 1
        while end < len(targets) and targets[end]["word"] == targets[index]["word"]:
            end += 1
        if end - index >= min_len:
            first = targets[index]
            runs.append(
                {
                    "length": end - index,
                    "start": index,
                    "end": end,
                    "word": first["word"],
                    "decoded_offset": first["decoded_offset"],
                    "record_index": first["record_index"],
                    "record_rel": first["record_rel"],
                }
            )
        index = end
    return sorted(runs, key=lambda run: (int(run["length"]), -int(run["start"])), reverse=True)


def cdd1_table_targets(image: CddImage) -> list[dict[str, int | None]]:
    starts = decoded_candidate_starts(image)
    segments = source_segments(image)
    ends = [start + decoded_span_candidate(entry) for start, (_, _, _, entry) in zip(starts, segments)]
    targets: list[dict[str, int | None]] = []
    for table_index, word in enumerate(cdd1_table_words(image)):
        offset = word << 4
        index = bisect_right(starts, offset) - 1
        if index >= 0 and index < len(ends) and offset < ends[index]:
            targets.append(
                {
                    "table_index": table_index,
                    "word": word,
                    "decoded_offset": offset,
                    "record_index": index,
                    "record_rel": offset - starts[index],
                }
            )
        else:
            targets.append(
                {
                    "table_index": table_index,
                    "word": word,
                    "decoded_offset": offset,
                    "record_index": None,
                    "record_rel": None,
                }
            )
    return targets


def operation_mode_rows(images: list[CddImage]) -> list[dict[str, object]]:
    grouped: defaultdict[int, list[tuple[int, int, bytes]]] = defaultdict(list)
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        for _, start, end, entry in source_segments(image):
            key = operation_key(entry)
            grouped[key[3] & 0xC0].append((end - start, decoded_span_candidate(entry), key))

    rows: list[dict[str, object]] = []
    for mode, items in sorted(grouped.items()):
        source_total = sum(item[0] for item in items)
        decoded_total = sum(item[1] for item in items)
        rows.append(
            {
                "mode": mode,
                "count": len(items),
                "source_total": source_total,
                "decoded_total": decoded_total,
                "ratio": source_total / decoded_total if decoded_total else 0.0,
                "key5": Counter(item[2][5] for item in items).most_common(6),
                "zero_decoded": sum(item[1] == 0 for item in items),
            }
        )
    return rows


def operation_unit_summary(images: list[CddImage], key: bytes) -> dict[str, object]:
    rows = []
    units = []
    units_by_image: defaultdict[str, list[bytes]] = defaultdict(list)
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        for index, start, end, entry in source_segments(image):
            if operation_key(entry) != key:
                continue
            data = image.data[start:end]
            rows.append((image.name, index, start, end, entry, data))
            unit_len = key[0]
            if unit_len and len(data) % unit_len == 0:
                for offset in range(0, len(data), unit_len):
                    unit = data[offset : offset + unit_len]
                    units.append(unit)
                    units_by_image[image.name].append(unit)

    constant_tail = b""
    if units:
        tail = units[0][1:]
        if all(unit[1:] == tail for unit in units):
            constant_tail = tail
    image_rows = []
    for image_name, image_units in units_by_image.items():
        tail = image_units[0][1:] if image_units else b""
        image_rows.append(
            {
                "image": image_name,
                "unit_count": len(image_units),
                "constant_tail": tail if image_units and all(unit[1:] == tail for unit in image_units) else b"",
                "first_bytes": Counter(unit[0] for unit in image_units).most_common(8),
            }
        )
    return {
        "key": key,
        "rows": rows,
        "unit_count": len(units),
        "unit_len": key[0],
        "constant_tail": constant_tail,
        "image_rows": sorted(image_rows, key=lambda row: str(row["image"])),
        "first_bytes": Counter(unit[0] for unit in units).most_common(8) if units else [],
    }


def short_rm_sequence(data: bytes, key: bytes) -> tuple[int, ...] | None:
    unit_len = key[0]
    if key not in SHORT_OPERATION_KEYS or not unit_len or len(data) != 4 * unit_len:
        return None
    return tuple(data[offset] for offset in range(0, len(data), unit_len))


def short_rm_payload(sequence: tuple[int, ...]) -> int | None:
    if len(sequence) != len(SHORT_RM_MASKS):
        return None
    candidate = sequence[0]
    expected = tuple(candidate ^ mask for mask in SHORT_RM_MASKS)
    return candidate if sequence == expected else None


def short_rm_rows(images: list[CddImage]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        decoded_starts = decoded_candidate_starts(image)
        for decoded_start, (index, start, end, entry) in zip(decoded_starts, source_segments(image)):
            key = operation_key(entry)
            if key not in SHORT_OPERATION_KEYS:
                continue
            sequence = short_rm_sequence(image.data[start:end], key)
            if sequence is None:
                payload = None
            else:
                payload = short_rm_payload(sequence)
            rows.append(
                {
                    "image": image.name,
                    "index": index,
                    "operation_key": key,
                    "source_start": start,
                    "source_len": end - start,
                    "decoded_start": decoded_start,
                    "decoded_span": decoded_span_candidate(entry),
                    "sequence": sequence,
                    "payload": payload,
                }
            )
    return rows


def short_rm_stable_payloads(rows: list[dict[str, object]]) -> dict[int, int]:
    payloads_by_index: defaultdict[int, set[int]] = defaultdict(set)
    for row in rows:
        if row["payload"] is not None:
            payloads_by_index[int(row["index"])].add(int(row["payload"]))
    return {index: next(iter(values)) for index, values in payloads_by_index.items() if len(values) == 1}


def consecutive_runs(indices: list[int]) -> list[list[int]]:
    runs: list[list[int]] = []
    position = 0
    while position < len(indices):
        end = position + 1
        while end < len(indices) and indices[end] == indices[end - 1] + 1:
            end += 1
        runs.append(indices[position:end])
        position = end
    return runs


def fit_short_run_masks(sequence: list[int]) -> list[tuple[int, int]]:
    fits: list[tuple[int, int]] = []
    if not sequence or len(sequence) > len(SHORT_RUN_MASKS):
        return fits
    for mask_start in range(len(SHORT_RUN_MASKS) - len(sequence) + 1):
        masks = SHORT_RUN_MASKS[mask_start : mask_start + len(sequence)]
        base = sequence[0] ^ masks[0]
        if all((base ^ masks[index]) == value for index, value in enumerate(sequence)):
            fits.append((mask_start, base))
    return fits


def transformed_printable_score(data: bytes, transform: str, key: int) -> float:
    if transform == "xor":
        transformed = ((byte ^ key) for byte in data)
    elif transform == "add":
        transformed = (((byte + key) & 0xFF) for byte in data)
    elif transform == "sub":
        transformed = (((byte - key) & 0xFF) for byte in data)
    else:
        raise ValueError(transform)
    printable_count = sum(byte == 9 or byte == 10 or byte == 13 or 32 <= byte < 127 for byte in transformed)
    return printable_count / len(data) if data else 0.0


def simple_transform_scan(data: bytes) -> list[tuple[str, int, float]]:
    sample = data[:0x20000]
    rows: list[tuple[str, int, float]] = []
    for transform in ("xor", "add", "sub"):
        best_key = 0
        best_score = 0.0
        for key in range(256):
            score = transformed_printable_score(sample, transform, key)
            if score > best_score:
                best_key = key
                best_score = score
        rows.append((transform, best_key, best_score))
    return rows


def compression_magic_counts(data: bytes) -> list[tuple[str, int]]:
    magics = [
        ("zlib 78 01", b"\x78\x01"),
        ("zlib 78 5e", b"\x78\x5e"),
        ("zlib 78 9c", b"\x78\x9c"),
        ("zlib 78 da", b"\x78\xda"),
        ("gzip", b"\x1f\x8b"),
        ("bzip2", b"BZh"),
        ("xz", b"\xfd7zXZ\x00"),
    ]
    rows: list[tuple[str, int]] = []
    for label, magic in magics:
        rows.append((label, len(find_all(data, magic))))
    return rows


def zlib_success_count(data: bytes) -> int:
    hits: list[int] = []
    for magic in (b"\x78\x01", b"\x78\x5e", b"\x78\x9c", b"\x78\xda"):
        hits.extend(find_all(data, magic))
    successes = 0
    for offset in sorted(set(hits)):
        try:
            out = zlib.decompress(data[offset : offset + 0x40000])
        except zlib.error:
            continue
        if len(out) >= 0x20:
            successes += 1
    return successes


def build_record_map(images: list[CddImage]) -> dict[str, object]:
    mapped_images: list[dict[str, object]] = []
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        decoded_starts = decoded_candidate_starts(image)
        table_targets = cdd1_table_targets(image)
        targets_by_record: defaultdict[int, list[dict[str, int]]] = defaultdict(list)
        for target in table_targets:
            if target["record_index"] is None:
                continue
            targets_by_record[int(target["record_index"])].append(
                {
                    "table_index": int(target["table_index"]),
                    "decoded_offset": int(target["decoded_offset"]),
                    "record_rel": int(target["record_rel"]),
                }
            )
        records = []
        for decoded_start, (index, source_start, source_end, entry) in zip(decoded_starts, source_segments(image)):
            key = operation_key(entry)
            decoded_span = decoded_span_candidate(entry)
            source_data = image.data[source_start:source_end]
            rm_sequence = short_rm_sequence(source_data, key)
            rm_payload = short_rm_payload(rm_sequence) if rm_sequence is not None else None
            record = {
                "index": index,
                "entry_hex": entry.hex(),
                "operation_key": key.hex(),
                "mode": key[3] & 0xC0,
                "source_start": source_start,
                "source_end": source_end,
                "source_len": source_end - source_start,
                "decoded_start": decoded_start,
                "decoded_span": decoded_span,
                "source_minus_decoded": (source_end - source_start) - decoded_span,
                "table_targets": targets_by_record.get(index, []),
            }
            if rm_sequence is not None:
                record["short_rm_sequence"] = list(rm_sequence)
                record["short_rm_payload"] = rm_payload
            records.append(record)
        mapped_images.append(
            {
                "image": image.name,
                "sha256": hashlib.sha256(image.data).hexdigest(),
                "decoded_total": sum(decoded_span_candidate(entry) for _, _, _, entry in source_segments(image)),
                "records": records,
            }
        )
    return {
        "schema": "liteon-cdd-record-map-v2",
        "note": "Offline structural map. decoded_start/decoded_span are candidate fields inferred statically, not a completed CDD decode. short_rm_* fields decode only the two known short-operation records.",
        "images": mapped_images,
    }


def write_report(images: list[CddImage]) -> str:
    lines: list[str] = []
    lines.append("# LiteOn CDD Stream Static Analysis")
    lines.append("")
    lines.append("Offline only. No drive commands were sent.")
    lines.append("")
    lines.append("## Images")
    lines.append("")
    lines.append("| image | sha256 | CDD starts | family | trailer auth14 |")
    lines.append("|---|---:|---:|---|---|")
    for image in images:
        starts = ", ".join(f"`0x{stream.start:05x}`" for stream in image.streams)
        family = image.data[0x6FF8:0x7000]
        family_text = ascii_cell(family) if any(family) else ""
        trailer = image.data[0xE7FE0:0xE7FEE].hex()
        lines.append(f"| {image.name} | `{sha256_prefix(image.data)}` | {starts} | `{family_text}` | `{trailer}` |")
    lines.append("")

    lines.append("## CDD1 Grammar")
    lines.append("")
    lines.append("| image | stream | dir end | entries | nominal 12-byte body | first source | nominal body len | nominal body len mod 12 | top sliding 12-byte motif | motif count | longest 13-stride run |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|")
    for image in images:
        if len(image.streams) < 1 or image.name == "XD13":
            continue
        stream = image.streams[0]
        info = cdd1_directory_info(stream)
        source_start_rel = cdd1_source_start_rel(image) or info["nominal_body_start"]
        body = stream.data[info["nominal_body_start"] :]
        motif, count = top_sliding_motif(body)
        runs = motif_runs_13(body, motif)
        longest = runs[0][1] if runs else 0
        lines.append(
            f"| {image.name} | `0x{stream.start:05x}..0x{stream.end:05x}` | "
            f"`0x{info['directory_end_abs']:05x}` | {info['entry_count']} | "
            f"`0x{info['nominal_body_start']:x}` | `0x{source_start_rel:x}` | "
            f"`0x{len(body):x}` | {len(body) % 12} | "
            f"`{motif.hex()}` | {count} | {longest} |"
        )
    lines.append("")

    lines.append("## Descriptor Logical Range And Size Ratios")
    lines.append("")
    lines.append("The DS-8ABSH descriptor and CDD headers both point at controller/logical range `0x184000..0x1b4000`, length `0x30000`. That is the only decoded/runtime allocation that is currently explicit in the F0 image.")
    lines.append("")
    lines.append("| image | descriptor | decoded range | CDD1 end | CDD2 end | final boundary |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for image in images:
        if not image.streams or image.name == "XD13":
            continue
        descriptor = parse_outer_descriptor(image)
        if descriptor is None:
            continue
        decoded_start = descriptor["decoded_start_a"]
        decoded_end = descriptor["decoded_end"]
        lines.append(
            f"| {image.name} | `0x{descriptor['start']:05x}..0x{descriptor['start'] + descriptor['length']:05x}` | "
            f"`0x{decoded_start:06x}..0x{decoded_end:06x}` | `0x{descriptor['cdd1_end']:05x}` | "
            f"`0x{descriptor['cdd2_end']:05x}` | `0x{descriptor['final_boundary']:05x}` |"
        )
    lines.append("")
    lines.append("Relative to that explicit `0x30000` decoded range, the obvious encoded sizes are much larger than 1.4x. If the remembered ~1.4 factor is real, it is probably a smaller internal work allocation rather than the descriptor-level decoded CDD range.")
    lines.append("")
    lines.append("| image | encoded measure | size | ratio to `0x30000` decoded range |")
    lines.append("|---|---|---:|---:|")
    for image in images:
        if not image.streams or image.name == "XD13":
            continue
        for label, size, ratio in ratio_rows(image):
            lines.append(f"| {image.name} | {label} | `0x{size:x}` | {ratio:.4f} |")
    lines.append("")

    lines.append("## Header Fields")
    lines.append("")
    lines.append("The CDD stream header is mostly 24-bit big-endian fields. The repeated `0x1b3fff` value is inclusive, while the descriptor stores end+1 as `0x1b4000`. The `nominal table guess` column is the old interpretation of header byte `+0x10`; the directory source field below shows the real payload boundary is slightly earlier in CDD1 and much earlier in CDD2.")
    lines.append("")
    lines.append("| image | stream2 start | directory end | control quad | nominal table guess | final boundary | descriptor | decoded start | decoded inclusive end |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for image in images:
        if not image.streams or image.name == "XD13":
            continue
        header = parse_stream_header(image.streams[0])
        lines.append(
            f"| {image.name} | `0x{header['stream2_start']:05x}` | `0x{header['directory_end_abs']:05x}` | "
            f"`0x{header['control_quad']:08x}` | `0x{header['aux_len']:x}` | "
            f"`0x{header['final_boundary']:05x}` | `0x{header['descriptor_start']:05x}` | "
            f"`0x{header['decoded_start']:06x}` | `0x{header['decoded_end_inclusive_a']:06x}` |"
        )
    lines.append("")

    lines.append("## Directory Pointer Column")
    lines.append("")
    lines.append("The final two bytes of each 8-byte CDD1 directory entry form a little-endian monotonically increasing value.")
    lines.append("")
    lines.append("| image | first | entry 388 | last | monotonic | common diffs |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for image in images:
        if len(image.streams) < 1 or image.name == "XD13":
            continue
        entries = directory_entries(image.streams[0])
        values = [entry[6] | (entry[7] << 8) for entry in entries]
        monotonic = all(left < right for left, right in zip(values, values[1:]))
        diffs = Counter(right - left for left, right in zip(values, values[1:])).most_common(5)
        lines.append(
            f"| {image.name} | `0x{values[0]:04x}` | `0x{values[388]:04x}` | "
            f"`0x{values[-1]:04x}` | {monotonic} | "
            + ", ".join(f"`0x{diff:x}` x{count}" for diff, count in diffs)
            + " |"
        )
    lines.append("")

    lines.append("## Directory Source Address Field")
    lines.append("")
    lines.append("The directory pointer column now has a direct file-address interpretation:")
    lines.append("")
    lines.append("```text")
    lines.append("source_start = (u16le(entry[6:8]) << 4) | (entry[5] >> 4)")
    lines.append("```")
    lines.append("")
    lines.append("The resulting addresses are monotonic and land in the CDD payload regions. Entry 388 starts at `0xd91a0`, exactly after CDD2's copied directory prefix. This corrects the earlier CDD2 symmetry guess: despite the copied header byte that looks like a `0x400` table length, CDD2 appears to start source payload immediately after the copied entries.")
    lines.append("")
    lines.append("| image | first source | entry 388 source | last source | final gap to CDD2 end | monotonic | common entry prefix | count | common short segment |")
    lines.append("|---|---:|---:|---:|---:|---:|---|---:|---:|")
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        entries = directory_entries(image.streams[0])
        sources = directory_source_addresses(image.streams[0])
        lengths = [right - left for left, right in zip(sources, sources[1:])]
        template, count = common_source_template(entries)
        template_lengths = [
            lengths[index]
            for index, entry in enumerate(entries[:-1])
            if entry[:5] == template and lengths[index] <= 0x80
        ]
        common_len = Counter(template_lengths).most_common(1)
        common_len_text = f"`0x{common_len[0][0]:x}` x{common_len[0][1]}" if common_len else ""
        monotonic = all(left < right for left, right in zip(sources, sources[1:]))
        final_gap = image.streams[1].end - sources[-1]
        lines.append(
            f"| {image.name} | `0x{sources[0]:05x}` | `0x{sources[388]:05x}` | "
            f"`0x{sources[-1]:05x}` | `0x{final_gap:x}` | {monotonic} | "
            f"`{template.hex()}` | {count} | {common_len_text} |"
        )
    lines.append("")
    lines.append("This is the strongest static CDD grammar clue so far. The small repeated-source templates such as `0d6840031a` and `0c60000318` point at short `0x34`/`0x30` byte spans, matching the visible motif islands. For these templates, byte 0 behaves like `N`, byte 1 is `8*N`, byte 4 is `2*N`, and the source span is `4*N`. That looks like an opcode/length tuple for a repeated packed-stream construct. The broader record format is still unresolved, but the records are no longer plausibly encrypted noise.")
    lines.append("")

    lines.append("## Directory/Table Boundary")
    lines.append("")
    lines.append("The source-address field gives a more precise payload boundary than the copied header bytes. CDD1 has a low-entropy table/control window after the directory, but its first source segment begins before the old nominal `directory + 0x400` boundary. CDD2 is different: after the copied header and copied entries, source payload begins immediately with no separate `0x400` table-like window.")
    lines.append("")
    lines.append("| image | CDD1 directory end rel | CDD1 first source rel | CDD1 table/control len | nominal overlap | CDD1 table entropy | CDD1 table common u16 | CDD2 copied entries end | CDD2 first source rel |")
    lines.append("|---|---:|---:|---:|---:|---:|---|---:|---:|")
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        stream1, stream2 = image.streams[:2]
        info = cdd1_directory_info(stream1)
        cdd1_source_rel = cdd1_source_start_rel(image)
        cdd2_source_rel = cdd2_source_start_rel(image)
        duplicate_end = 0x20 + cdd2_duplicate_len(stream1, stream2)
        table = cdd1_table_window(image)
        words = cdd1_table_words(image)
        common_words = ", ".join(f"`0x{value:04x}` x{count}" for value, count in Counter(words).most_common(3))
        nominal_overlap = info["nominal_body_start"] - cdd1_source_rel if cdd1_source_rel is not None else 0
        lines.append(
            f"| {image.name} | `0x{info['directory_end_rel']:x}` | `0x{(cdd1_source_rel or 0):x}` | "
            f"`0x{len(table):x}` | `0x{nominal_overlap:x}` | {entropy(table):.3f} | "
            f"{common_words} | `0x{duplicate_end:x}` | `0x{(cdd2_source_rel or 0):x}` |"
        )
    lines.append("")

    lines.append("## CDD1 Table As Decoded Paragraph Offsets")
    lines.append("")
    lines.append("Interpreting the CDD1 table/control window as little-endian 16-bit words gives another strong structural clue: every word, shifted left by four, lands inside the explicit decoded range length `0x30000`. This makes the table look like decoded-space paragraph address/control material rather than arbitrary aux bytes.")
    lines.append("")
    lines.append("| image | table words | shifted offset range | low/mid/high bands | most common words |")
    lines.append("|---|---:|---:|---|---|")
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        words = cdd1_table_words(image)
        bands = Counter(table_word_band(word) for word in words)
        common = ", ".join(f"`0x{word:04x}` x{count}" for word, count in Counter(words).most_common(5))
        lines.append(
            f"| {image.name} | {len(words)} | `0x{min(words) << 4:05x}..0x{max(words) << 4:05x}` | "
            f"low {bands['low']}, mid {bands['mid']}, high {bands['high']} | {common} |"
        )
    lines.append("")
    lines.append("Splitting that table at word index 128 exposes two different-looking regions. The front `0x100` bytes carry the high/mid paragraph targets and the repeated `0x0d01`/`0x14e0`/`0x1503`/`0x1490`/`0x1502` runs, and those front words target later candidate decoded records. The remaining words are mostly low decoded offsets with no adjacent repeats, and they target the early decoded records. That makes the front look more like a vector/entrypoint/control table, while the tail looks more like a secondary offset list.")
    lines.append("")
    lines.append("| image | front 128 words | front target records | remaining words | tail target records | long repeated runs in front table |")
    lines.append("|---|---|---:|---|---:|---|")
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        words = cdd1_table_words(image)
        front = words[:128]
        tail = words[128:]
        targets = cdd1_table_targets(image)
        front_bands = Counter(table_word_band(word) for word in front)
        tail_bands = Counter(table_word_band(word) for word in tail)
        run_text = ", ".join(
            f"`0x{int(run['word']):04x}` x{int(run['length'])} @{int(run['start'])} -> rec {run['record_index']}+`0x{int(run['record_rel'] or 0):x}`"
            for run in cdd1_table_repeated_runs(image, min_len=4)
        )
        lines.append(
            f"| {image.name} | low {front_bands['low']}, mid {front_bands['mid']}, high {front_bands['high']} | "
            f"{table_target_record_range(targets[:128])} | "
            f"low {tail_bands['low']}, mid {tail_bands['mid']}, high {tail_bands['high']} | "
            f"{table_target_record_range(targets[128:])} | {run_text} |"
        )
    lines.append("")

    ld5m = next((image for image in images if image.name == "LD5M"), None)
    if ld5m is not None:
        descriptor = parse_outer_descriptor(ld5m)
        decoded_base = int(descriptor["decoded_start_a"]) if descriptor else 0x184000
        targets = cdd1_table_targets(ld5m)
        decoded_starts = decoded_candidate_starts(ld5m)
        segments = source_segments(ld5m)
        oracle_offsets = [
            (0x00000, "decoded base / record 0"),
            (0x00060, "minimum CDD1 table target"),
            (0x0D010, "`0x0d01` x16 repeated front-table target"),
            (0x14900, "`0x1490` x4 front-table target"),
            (0x15030, "`0x1503` x4 front-table target"),
            (0x18020, "`0x1802` x2 front-table target"),
            (0x18800, "`0x1880` x2 front-table target"),
            (0x1C000, "high front-table target"),
            (0x1EFE0, "near-highest LD5M table target"),
        ]
        lines.append("LD5M decoded/controller oracle shortlist for future runtime reads:")
        lines.append("")
        lines.append("| decoded offset | controller address | reason | table index | target record+rel | source range | operation key |")
        lines.append("|---:|---:|---|---:|---:|---:|---|")
        for decoded_offset, reason in oracle_offsets:
            table_hit = next((target for target in targets if target["decoded_offset"] == decoded_offset), None)
            record_index = int(table_hit["record_index"]) if table_hit and table_hit["record_index"] is not None else bisect_right(decoded_starts, decoded_offset) - 1
            if record_index < 0 or record_index >= len(segments):
                continue
            _, source_start, source_end, entry = segments[record_index]
            record_rel = decoded_offset - decoded_starts[record_index]
            table_index = str(table_hit["table_index"]) if table_hit else ""
            lines.append(
                f"| `0x{decoded_offset:05x}` | `0x{decoded_base + decoded_offset:06x}` | {reason} | "
                f"{table_index} | {record_index}+`0x{record_rel:x}` | `0x{source_start:05x}..0x{source_end:05x}` | "
                f"`{operation_key(entry).hex()}` |"
            )
        lines.append("")
    lines.append("Close sibling tables also line up by position. CHS7 and CHS9 have 189 identical same-index table words, including long equal runs, so this table is versioned data with stable structure.")
    lines.append("")
    lines.append("| pair | table words | same-position equal | most common word deltas |")
    lines.append("|---|---:|---:|---|")
    for pair in (("CHS7", "CHS9"), ("AD12", "CD12"), ("LD5M", "CHS9")):
        left = next((image for image in images if image.name == pair[0]), None)
        right = next((image for image in images if image.name == pair[1]), None)
        if not left or not right:
            continue
        left_words = cdd1_table_words(left)
        right_words = cdd1_table_words(right)
        count = min(len(left_words), len(right_words))
        same = sum(left_words[index] == right_words[index] for index in range(count))
        deltas = Counter(right_words[index] - left_words[index] for index in range(count)).most_common(6)
        delta_text = ", ".join(f"`{delta:+#x}` x{delta_count}" for delta, delta_count in deltas)
        lines.append(f"| {pair[0]} vs {pair[1]} | {len(left_words)}/{len(right_words)} | {same} | {delta_text} |")
    lines.append("")
    lines.append("Once the candidate decoded span field is applied, the table lines up even more tightly: every shifted table word falls inside one of the candidate decoded record intervals.")
    lines.append("")
    lines.append("| image | table words in candidate intervals | misses | top target records | common in-record offsets |")
    lines.append("|---|---:|---:|---|---|")
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        summary = cdd1_table_interval_summary(image)
        records = ", ".join(f"`{index}` x{count}" for index, count in summary["records"])  # type: ignore[index]
        rels = ", ".join(f"`0x{rel:x}` x{count}" for rel, count in summary["rels"])  # type: ignore[index]
        lines.append(
            f"| {image.name} | {summary['hits']}/{summary['words']} | {summary['misses']} | "
            f"{records} | {rels} |"
        )
    lines.append("")

    if ld5m is not None:
        lines.append("LD5M source-segment mapping for useful probe offsets:")
        lines.append("")
        lines.append("| offset | source entry | source range | candidate decoded start/span | entry bytes |")
        lines.append("|---:|---:|---:|---:|---|")
        decoded_starts = decoded_candidate_starts(ld5m)
        for offset in (0x704F, 0x81EC, 0x27D4F, 0xD91A0, 0xD95A0, 0xE7FE0):
            segment = segment_for_offset(ld5m, offset)
            if segment is None:
                lines.append(f"| `0x{offset:05x}` | none | outside source spans | | |")
            else:
                index, start, end, entry = segment
                lines.append(
                    f"| `0x{offset:05x}` | {index} | `0x{start:05x}..0x{end:05x}` | "
                    f"`0x{decoded_starts[index]:05x}`/`0x{decoded_span_candidate(entry):03x}` | `{entry.hex()}` |"
                )
        lines.append("")

    lines.append("## CDD2 Directory Duplicate")
    lines.append("")
    lines.append("For DS-8ABSH-style images, stream2 bytes `0x20..0x1a0` duplicate stream1 bytes `0xc40..0xdc0`, i.e. CDD1 entries 388..435. Stream2 source payload starts at `0x1a0`, immediately after those copied entries.")
    lines.append("")
    lines.append("| image | duplicate length | stream2 source body start | stream2 source body len |")
    lines.append("|---|---:|---:|---:|")
    for image in images:
        if len(image.streams) < 2 or image.name == "XD13":
            continue
        stream1, stream2 = image.streams[:2]
        duplicate_len = 0
        while (
            0x20 + duplicate_len < len(stream2.data)
            and 0xC40 + duplicate_len < len(stream1.data)
            and stream2.data[0x20 + duplicate_len] == stream1.data[0xC40 + duplicate_len]
        ):
            duplicate_len += 1
        body_start = inferred_cdd2_body_start(image) or 0x20 + duplicate_len
        lines.append(
            f"| {image.name} | `0x{duplicate_len:x}` | `0x{body_start:x}` | "
            f"`0x{len(stream2.data) - body_start:x}` |"
        )
    lines.append("")

    for pair in (("CHS7", "CHS9"), ("AD12", "CD12"), ("AHS9", "CHS9")):
        left = next((image for image in images if image.name == pair[0]), None)
        right = next((image for image in images if image.name == pair[1]), None)
        if not left or not right or not left.streams or not right.streams:
            continue
        left_info = cdd1_directory_info(left.streams[0])
        right_info = cdd1_directory_info(right.streams[0])
        left_start = cdd1_source_start_rel(left) or left_info["nominal_body_start"]
        right_start = cdd1_source_start_rel(right) or right_info["nominal_body_start"]
        matches = exact_matches(left.streams[0].data[left_start:], right.streams[0].data[right_start:], seed=16, limit=8)
        lines.append(f"## Exact Shifted Body Matches: {pair[0]} vs {pair[1]}")
        lines.append("")
        lines.append("| length | left body rel | right body rel | shift | sample |")
        lines.append("|---:|---:|---:|---:|---|")
        left_body = left.streams[0].data[left_start:]
        for length, left_offset, right_offset, shift in matches:
            sample = left_body[left_offset : left_offset + min(length, 24)].hex()
            lines.append(
                f"| {length} | `0x{left_offset:x}` | `0x{right_offset:x}` | "
                f"`{shift:+#x}` | `{sample}` |"
            )
        lines.append("")

    left = next((image for image in images if image.name == "CHS7"), None)
    right = next((image for image in images if image.name == "CHS9"), None)
    if left is not None and right is not None:
        lines.append("## Same-Index Source Segment Matches: CHS7 vs CHS9")
        lines.append("")
        lines.append("CHS7 and CHS9 are close siblings. Their directory entries are mostly one or two bytes apart, and the source-address model lets us compare the same directory index as a semantic unit rather than searching the whole body blindly.")
        lines.append("")
        lines.append("| entry | common prefix | left source | right source | lengths | entry byte diff | entries |")
        lines.append("|---:|---:|---:|---:|---:|---:|---|")
        for row in same_index_segment_matches(left, right):
            lines.append(
                f"| {row['index']} | {row['prefix']} | `0x{int(row['left_start']):05x}` | "
                f"`0x{int(row['right_start']):05x}` | `0x{int(row['left_len']):x}`/`0x{int(row['right_len']):x}` | "
                f"{row['entry_diff']} | `{row['left_entry']}` / `{row['right_entry']}` |"
            )
        lines.append("")

    lines.append("## Operation Fields Versus Source Fields")
    lines.append("")
    lines.append("The source-address formula splits byte 5: the high nibble is the source low nibble, while the low nibble stays with the non-source record fields. Treating `entry[0:5] + (entry[5] & 0x0f)` as an operation key makes the close-sibling comparison much cleaner.")
    lines.append("")
    lines.append("| pair | exact same entry | same operation key | same-op equal source length | source-only changes | common source deltas |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for pair in (("CHS7", "CHS9"), ("AD12", "CD12"), ("AHS9", "CHS9")):
        left = next((image for image in images if image.name == pair[0]), None)
        right = next((image for image in images if image.name == pair[1]), None)
        if not left or not right:
            continue
        summary = same_index_operation_summary(left, right)
        deltas = ", ".join(f"`{delta:+#x}` x{count}" for delta, count in summary["deltas"])
        lines.append(
            f"| {pair[0]} vs {pair[1]} | {summary['full_match']} | {summary['op_match']} | {summary['op_same_len']} | "
            f"{summary['source_only_change']} | {deltas} |"
        )
    lines.append("")
    lines.append("For CHS7 vs CHS9, 380 of 436 records keep the same operation key; all 380 also keep the same source-segment length, and 377 differ only in the source-address bits. That is strong evidence that the directory entry is not opaque: `entry[0:5]` plus byte5 low nibble likely describes the packed operation/output contract, while byte5 high nibble and bytes 6-7 are the source-address field.")
    lines.append("")
    lines.append("Example CHS7/CHS9 source-only differences:")
    lines.append("")
    lines.append("| entry | source delta | lengths | entries |")
    lines.append("|---:|---:|---:|---|")
    example_left = next((image for image in images if image.name == "CHS7"), None)
    example_right = next((image for image in images if image.name == "CHS9"), None)
    if example_left is not None and example_right is not None:
        for row in same_index_operation_summary(example_left, example_right)["examples"]:
            lines.append(
                f"| {row['index']} | `{int(row['source_delta']):+#x}` | "
                f"`0x{int(row['left_len']):x}`/`0x{int(row['right_len']):x}` | "
                f"`{row['left_entry']}` / `{row['right_entry']}` |"
            )
    lines.append("")

    lines.append("## Operation Key Source-Length Invariant")
    lines.append("")
    operation_rows = operation_length_rows(images)
    inconsistent = [
        row for row in operation_rows if len(row["lengths"]) > 1  # type: ignore[arg-type]
    ]
    lines.append(
        f"Across these DS-8ABSH samples, `{len(operation_rows)}` unique operation keys appear. "
        f"None map to more than one source-span length (`{len(inconsistent)}` inconsistent keys). "
        "That makes the operation key a deterministic source-length descriptor, even though the full field grammar is not solved."
    )
    lines.append("")
    lines.append("| operation key | count | source length | indices | images |")
    lines.append("|---|---:|---:|---|---|")
    for row in operation_rows[:12]:
        lengths = row["lengths"]  # type: ignore[assignment]
        length_text = ", ".join(f"`0x{length:x}` x{count}" for length, count in lengths.most_common())  # type: ignore[attr-defined]
        indices = row["indices"]  # type: ignore[assignment]
        index_text = ", ".join(str(index) for index in indices[:10])  # type: ignore[index]
        if len(indices) > 10:  # type: ignore[arg-type]
            index_text += ", ..."
        lines.append(
            f"| `{row['key'].hex()}` | {row['count']} | {length_text} | "
            f"{index_text} | {', '.join(row['images'])} |"  # type: ignore[arg-type]
        )
    lines.append("")

    base_rows = operation_length_base_rows(images)
    residuals = Counter(residual for _, _, _, _, residual in base_rows)
    exact_count = residuals[0]
    lines.append("A partial length field also falls out of the operation key:")
    lines.append("")
    lines.append("```text")
    lines.append("length_base = u16le(operation_key[2:4]) >> 4")
    lines.append("```")
    lines.append("")
    lines.append(
        f"This equals the source-span length for `{exact_count}` records. "
        "For the rest it is a length-ish base with a structured residual, so bytes 2..3 are probably part of the length coding rather than the complete source-length field."
    )
    lines.append("")
    lines.append("| residual (`source_len - length_base`) | count |")
    lines.append("|---:|---:|")
    for residual, count in residuals.most_common(12):
        lines.append(f"| `{residual:+#x}` | {count} |")
    lines.append("")

    lines.append("## Candidate Decoded Span Field")
    lines.append("")
    lines.append("A second length-like field appears in operation-key byte 3. The candidate decoded/output span is:")
    lines.append("")
    lines.append("```text")
    lines.append("decoded_span = (operation_key[3] & 0x3f) << 4")
    lines.append("```")
    lines.append("")
    lines.append("This is not a full CDD decoder, but it is the first field that lands near the explicit `0x30000` decoded/controller range instead of the much larger encoded source length.")
    lines.append("")
    lines.append("| image | candidate decoded span | delta from `0x30000` | CDD1 entries | CDD2 entries | encoded source / candidate decoded |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in decoded_span_summaries(images):
        lines.append(
            f"| {row['image']} | `0x{int(row['total']):05x}` | `{int(row['delta']):+#x}` | "
            f"`0x{int(row['cdd1']):05x}` | `0x{int(row['cdd2']):05x}` | {float(row['ratio']):.3f}x |"
        )
    lines.append("")
    lines.append("The close siblings keep this field aligned in long same-operation runs. For CHS7 vs CHS9, cumulative decoded offsets have piecewise constant deltas across same-operation records, which is what we would expect from a versioned decoded address stream.")
    lines.append("")
    lines.append("| pair | longest same-op decoded-offset runs |")
    lines.append("|---|---|")
    for pair in (("CHS7", "CHS9"), ("AD12", "CD12")):
        left = next((image for image in images if image.name == pair[0]), None)
        right = next((image for image in images if image.name == pair[1]), None)
        if not left or not right:
            continue
        run_text = ", ".join(
            f"`{start}..{end - 1}` len {length} delta `{delta:+#x}`"
            for length, start, end, delta in decoded_offset_delta_runs(left, right)[:6]
        )
        lines.append(f"| {pair[0]} vs {pair[1]} | {run_text} |")
    lines.append("")
    lines.append("This field also lands on the two visible short-operation islands. `0d6840031a00` consumes four 13-byte source units (`0x34` bytes total), while `0c6000031800` consumes four 12-byte source units (`0x30` bytes total); both claim candidate decoded span `0x30`. The first byte of each unit is not discardable padding: across every known short record it follows the four-copy XOR code `m, m^0x19, m^0x32, m^0x2b`.")
    lines.append("")
    lines.append("The high two bits of the same operation-key byte look like mode flags. They split the stream into different redundancy classes rather than changing the decoded-span unit.")
    lines.append("")
    lines.append("| mode bits (`operation_key[3] & 0xc0`) | records | encoded source | decoded span candidate | encoded / decoded | zero-span records | common byte5 flags |")
    lines.append("|---:|---:|---:|---:|---:|---:|---|")
    for row in operation_mode_rows(images):
        key5 = ", ".join(f"`0x{flag:x}` x{count}" for flag, count in row["key5"])  # type: ignore[index]
        lines.append(
            f"| `0x{int(row['mode']):02x}` | {row['count']} | `0x{int(row['source_total']):x}` | "
            f"`0x{int(row['decoded_total']):x}` | {float(row['ratio']):.3f}x | "
            f"{row['zero_decoded']} | {key5} |"
        )
    lines.append("")

    lines.append("## Short Operation Source Units")
    lines.append("")
    lines.append("The two high-frequency short operations expose a small regular source format. In both cases byte 0 of the operation key is the source unit length, byte 1 is `8 * unit_len`, byte 4 is `2 * unit_len`, and each record source span is `4 * unit_len`.")
    lines.append("")
    rm_rows = short_rm_rows(images)
    rm_ok = [row for row in rm_rows if row["payload"] is not None]
    payloads_by_index: defaultdict[int, set[int]] = defaultdict(set)
    images_by_index: defaultdict[int, set[str]] = defaultdict(set)
    for row in rm_ok:
        payloads_by_index[int(row["index"])].add(int(row["payload"]))
        images_by_index[int(row["index"])].add(str(row["image"]))
    stable_indices = [index for index, values in payloads_by_index.items() if len(values) == 1]
    lines.append(
        f"The byte-0 sequence now has a stronger interpretation: `{len(rm_ok)}/{len(rm_rows)}` "
        "short records match `m, m^0x19, m^0x32, m^0x2b`. "
        f"Across shared entry indices, `{len(stable_indices)}/{len(payloads_by_index)}` indices keep a single `m` value across the sibling set."
    )
    lines.append("")
    lines.append("This corrects the earlier parity-only interpretation. The profile-specific unit tails still look like scaffolding or controller coding material, but byte 0 carries a reproducible one-byte payload/control value.")
    lines.append("")
    lines.append("| operation key | image | records | unit len | source span | decoded span candidate | units | constant unit tail | first-byte samples |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|---|")
    for key in SHORT_OPERATION_KEYS:
        summary = operation_unit_summary(images, key)
        rows = summary["rows"]  # type: ignore[assignment]
        record_count_by_image = Counter(row[0] for row in rows)  # type: ignore[index]
        for image_row in summary["image_rows"]:  # type: ignore[index]
            image_name = str(image_row["image"])
            first_bytes = ", ".join(f"`0x{value:02x}` x{count}" for value, count in image_row["first_bytes"])  # type: ignore[index]
            tail = image_row["constant_tail"]  # type: ignore[assignment]
            tail_text = f"`{tail.hex()}`" if tail else ""
            lines.append(
                f"| `{key.hex()}` | {image_name} | {record_count_by_image[image_name]} | "
                f"`0x{int(summary['unit_len']):x}` | `0x{key[0] * 4:x}` | "
                f"`0x{decoded_span_from_key(key):x}` | {image_row['unit_count']} | {tail_text} | {first_bytes} |"
            )
    lines.append("")
    lines.append("Representative short-record `m` values:")
    lines.append("")
    lines.append("| image | record count | `entry:m` values |")
    lines.append("|---|---:|---|")
    for image in images:
        image_rows = [row for row in rm_ok if row["image"] == image.name]
        if not image_rows:
            continue
        values = ", ".join(f"`{int(row['index'])}:0x{int(row['payload']):02x}`" for row in image_rows[:20])
        if len(image_rows) > 20:
            values += ", ..."
        lines.append(f"| {image.name} | {len(image_rows)} | {values} |")
    lines.append("")
    lines.append("Shared-index examples:")
    lines.append("")
    lines.append("| entry | `m` | byte-0 sequence | images |")
    lines.append("|---:|---:|---|---|")
    shared_rows = []
    for index, values in payloads_by_index.items():
        if len(values) != 1:
            continue
        image_names = sorted(images_by_index[index])
        if len(image_names) < 4:
            continue
        payload = next(iter(values))
        sequence = tuple(payload ^ mask for mask in SHORT_RM_MASKS)
        shared_rows.append((len(image_names), index, payload, sequence, image_names))
    for _, index, payload, sequence, image_names in sorted(shared_rows, reverse=True)[:12]:
        sequence_text = " ".join(f"{byte:02x}" for byte in sequence)
        lines.append(f"| {index} | `0x{payload:02x}` | `{sequence_text}` | {', '.join(image_names)} |")
    lines.append("")

    stable_payloads = short_rm_stable_payloads(rm_rows)
    run_rows = []
    for run in consecutive_runs(sorted(stable_payloads)):
        sequence = [stable_payloads[index] for index in run]
        if len(sequence) < 2:
            continue
        fits = fit_short_run_masks(sequence)
        run_rows.append((run, sequence, fits))
    lines.append("The `m` values also have a second-level pattern in consecutive short-record runs. Every multi-record run fits a contiguous slice of `base^0x00, base^0x64, base^0xc8, base^0xac`; this may be another small codeword or interleave lane.")
    lines.append("")
    lines.append("| entries | `m` sequence | XOR to first | mask-slice fits |")
    lines.append("|---|---|---|---|")
    for run, sequence, fits in run_rows:
        entries = f"{run[0]}" if len(run) == 1 else f"{run[0]}..{run[-1]}"
        sequence_text = " ".join(f"{value:02x}" for value in sequence)
        xors_text = " ".join(f"{value ^ sequence[0]:02x}" for value in sequence)
        fits_text = ", ".join(f"start {start}, base `0x{base:02x}`" for start, base in fits) or ""
        lines.append(f"| {entries} | `{sequence_text}` | `{xors_text}` | {fits_text} |")
    lines.append("")

    lines.append("## Simple Decode/Compression Probes")
    lines.append("")
    lines.append("These are sanity probes, not proof that no transform exists. They rule out the cheap cases: a global one-byte XOR/add/sub mask, obvious text-bearing transform, and standard compression headers at useful rates.")
    lines.append("")
    ld5m = next((image for image in images if image.name == "LD5M"), None)
    if ld5m and ld5m.streams:
        info = cdd1_directory_info(ld5m.streams[0])
        source_start_rel = cdd1_source_start_rel(ld5m) or info["nominal_body_start"]
        body = ld5m.streams[0].data[source_start_rel:]
        lines.append("Best printable score over the first `0x20000` bytes of LD5M CDD1 body:")
        lines.append("")
        lines.append("| transform | best key | printable fraction |")
        lines.append("|---|---:|---:|")
        for transform, key, score in simple_transform_scan(body):
            lines.append(f"| {transform} | `0x{key:02x}` | {score:.4f} |")
        lines.append("")
        lines.append("Common compression magic counts across the full LD5M CDD1 body:")
        lines.append("")
        lines.append("| magic | count |")
        lines.append("|---|---:|")
        for label, count in compression_magic_counts(body):
            lines.append(f"| {label} | {count} |")
        lines.append("")
        lines.append(f"Zlib decompression successes from those LD5M CDD1 body magic-looking offsets: `{zlib_success_count(body)}`.")
        lines.append("")
    lines.append("The body also contains sliding/13-stride motif runs and cross-sibling exact matches that are not aligned like AES-ECB blocks. That makes generic block-cipher brute force a poor fit: the useful attack surface is probably the CDD record grammar, not a blind key search.")
    lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append("This still does not give us a decoded controller firmware image. It does narrow the static picture:")
    lines.append("")
    lines.append("- The updater materializes a sealed F0 container, not decoded CDD runtime bytes.")
    lines.append("- The visible descriptor/header decoded range is `0x30000`, but the encoded CDD object is roughly 4.4x larger; the remembered ~1.4 factor is not present at this level.")
    lines.append("- The directory and aux table are plainly structured, so treating CDD as one encrypted blob is probably the wrong mental model.")
    lines.append("- A blind brute-force decrypt is not realistic without a known algorithm/key/plaintext target. The more promising static route is to reverse the 8-byte directory records, then use sibling shifted matches as anchors.")
    lines.append("")
    lines.append("Best next hybrid test, once live work resumes: sample a few normal-boot decoded/controller bytes around `0x184000`, `0x18481c`, and `0x19191a`. If those bytes resemble CDD directory/body material we get a mapping; if they are a third representation, static decode probably needs that runtime oracle.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", action="append", type=Path, help="F0 image path. May be supplied more than once.")
    parser.add_argument("--out", type=Path, help="Write markdown report to this path instead of stdout.")
    parser.add_argument("--map-json", type=Path, help="Write inferred CDD record map JSON to this path.")
    args = parser.parse_args()

    paths = args.image if args.image else DEFAULT_IMAGES
    images = [image for path in paths if (image := load_image(path))]
    if not images:
        raise SystemExit("no CDD-bearing 1 MiB images found")

    report = write_report(images)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report)
    else:
        print(report, end="")
    if args.map_json:
        args.map_json.parent.mkdir(parents=True, exist_ok=True)
        args.map_json.write_text(json.dumps(build_record_map(images), indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
