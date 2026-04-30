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
        family_text = family.decode("ascii", errors="replace") if any(family) else ""
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
