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
import math
import zlib
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
    body_start = directory_end_rel + aux_len
    return {
        "directory_end_abs": directory_end_abs,
        "directory_end_rel": directory_end_rel,
        "entry_count": entry_count,
        "aux_len": aux_len,
        "body_start": body_start,
        "body_len": len(stream.data) - body_start,
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
    duplicate_len = 0
    while (
        0x20 + duplicate_len < len(stream2.data)
        and 0xC40 + duplicate_len < len(stream1.data)
        and stream2.data[0x20 + duplicate_len] == stream1.data[0xC40 + duplicate_len]
    ):
        duplicate_len += 1
    return 0x20 + duplicate_len + cdd1_directory_info(stream1)["aux_len"]


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
    cdd_body_total = len(stream1.data) - info1["body_start"]
    if stream2_body_start is not None and len(image.streams) >= 2:
        cdd_body_total += len(image.streams[1].data) - stream2_body_start
    rows = [
        ("descriptor object", descriptor["final_boundary"] - descriptor["start"]),
        ("CDD streams", cdd_total),
        ("CDD bodies", cdd_body_total),
        ("CDD1 body", len(stream1.data) - info1["body_start"]),
    ]
    if stream2_body_start is not None and len(image.streams) >= 2:
        rows.append(("CDD2 inferred body", len(image.streams[1].data) - stream2_body_start))
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
    lines.append("| image | stream | dir end | entries | aux len | body start | body len | body len mod 12 | top sliding 12-byte motif | motif count | longest 13-stride run |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|")
    for image in images:
        if len(image.streams) < 1 or image.name == "XD13":
            continue
        stream = image.streams[0]
        info = cdd1_directory_info(stream)
        body = stream.data[info["body_start"] :]
        motif, count = top_sliding_motif(body)
        runs = motif_runs_13(body, motif)
        longest = runs[0][1] if runs else 0
        lines.append(
            f"| {image.name} | `0x{stream.start:05x}..0x{stream.end:05x}` | "
            f"`0x{info['directory_end_abs']:05x}` | {info['entry_count']} | "
            f"`0x{info['aux_len']:x}` | `0x{info['body_start']:x}` | "
            f"`0x{info['body_len']:x}` | {info['body_len'] % 12} | "
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
    lines.append("The CDD stream header is mostly 24-bit big-endian fields. The repeated `0x1b3fff` value is inclusive, while the descriptor stores end+1 as `0x1b4000`.")
    lines.append("")
    lines.append("| image | stream2 start | directory end | control quad | aux len | final boundary | descriptor | decoded start | decoded inclusive end |")
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
    lines.append("The resulting addresses are monotonic and land in the CDD payload/aux regions. Entry 388 starts at `0xd91a0`, exactly after CDD2's copied directory prefix and before its inferred `0x400` aux window.")
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
    ld5m = next((image for image in images if image.name == "LD5M"), None)
    if ld5m is not None:
        lines.append("LD5M source-segment mapping for useful probe offsets:")
        lines.append("")
        lines.append("| offset | source entry | source range | entry bytes |")
        lines.append("|---:|---:|---:|---|")
        for offset in (0x704F, 0x81EC, 0x27D4F, 0xD91A0, 0xD95A0, 0xE7FE0):
            segment = segment_for_offset(ld5m, offset)
            if segment is None:
                lines.append(f"| `0x{offset:05x}` | none | outside source spans | |")
            else:
                index, start, end, entry = segment
                lines.append(
                    f"| `0x{offset:05x}` | {index} | `0x{start:05x}..0x{end:05x}` | `{entry.hex()}` |"
                )
        lines.append("")

    lines.append("## CDD2 Directory Duplicate")
    lines.append("")
    lines.append("For DS-8ABSH-style images, stream2 bytes `0x20..0x1a0` duplicate stream1 bytes `0xc40..0xdc0`, i.e. CDD1 entries 388..435.")
    lines.append("")
    lines.append("| image | duplicate length | stream2 inferred body start | stream2 body len |")
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
        body_start = 0x20 + duplicate_len + cdd1_directory_info(stream1)["aux_len"]
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
        matches = exact_matches(
            left.streams[0].data[left_info["body_start"] :],
            right.streams[0].data[right_info["body_start"] :],
            seed=16,
            limit=8,
        )
        lines.append(f"## Exact Shifted Body Matches: {pair[0]} vs {pair[1]}")
        lines.append("")
        lines.append("| length | left body rel | right body rel | shift | sample |")
        lines.append("|---:|---:|---:|---:|---|")
        left_body = left.streams[0].data[left_info["body_start"] :]
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

    lines.append("## Simple Decode/Compression Probes")
    lines.append("")
    lines.append("These are sanity probes, not proof that no transform exists. They rule out the cheap cases: a global one-byte XOR/add/sub mask, obvious text-bearing transform, and standard compression headers at useful rates.")
    lines.append("")
    ld5m = next((image for image in images if image.name == "LD5M"), None)
    if ld5m and ld5m.streams:
        info = cdd1_directory_info(ld5m.streams[0])
        body = ld5m.streams[0].data[info["body_start"] :]
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
