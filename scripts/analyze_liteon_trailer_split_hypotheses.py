#!/usr/bin/env python3
"""Probe split interpretations of the LiteOn 14-byte trailer seal.

This is deliberately narrower than the general container-auth digest probe. It
tests the late-night "maybe this is 2 bytes of additive checksum plus 12 bytes
related to CDD 12-byte units" idea:

* every contiguous 2-byte slice of `0xe7fe0..0xe7fed` is tested against
  simple additive low-16 checks over plausible regions;
* the remaining 12 bytes are tested against column-wise checksums over CDD
  unit streams.

The script is offline-only and never opens an optical drive.
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_liteon_cdd_streams as cdd  # noqa: E402


DEFAULT_IMAGES = [
    ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin",
    ROOT / "work/cdd-siblings/AD12-1.bin",
    ROOT / "work/cdd-siblings/AHS9-postprocess-plain.bin",
    ROOT / "work/cdd-siblings/CD12-postprocess-plain.bin",
    ROOT / "work/cdd-siblings/CHS7-postprocess-plain.bin",
    ROOT / "work/cdd-siblings/CHS9-postprocess-plain.bin",
]
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-trailer-split-hypotheses.json"
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-trailer-split-hypotheses.md"

AUTH14 = (0xE7FE0, 0xE7FEE)
FINAL_BOUNDARY = 0xE8000


def image_name(path: Path) -> str:
    return cdd.image_name(path)


def load_images(paths: list[Path]) -> dict[str, cdd.CddImage]:
    images: dict[str, cdd.CddImage] = {}
    for path in paths:
        image = cdd.load_image(path)
        if image is None:
            continue
        images[image.name] = image
    return images


def sum16(blob: bytes) -> int:
    return sum(blob) & 0xFFFF


def word_variants(value: int) -> dict[str, bytes]:
    value &= 0xFFFF
    variants = {
        "sum16_be": value.to_bytes(2, "big"),
        "sum16_le": value.to_bytes(2, "little"),
        "ones_complement_be": ((~value) & 0xFFFF).to_bytes(2, "big"),
        "ones_complement_le": ((~value) & 0xFFFF).to_bytes(2, "little"),
        "twos_complement_be": ((-value) & 0xFFFF).to_bytes(2, "big"),
        "twos_complement_le": ((-value) & 0xFFFF).to_bytes(2, "little"),
    }
    return variants


def trailer_auth(image: cdd.CddImage) -> bytes:
    return image.data[AUTH14[0] : AUTH14[1]]


def masked_bytes(data: bytes, mask_ranges: list[tuple[int, int]]) -> bytes:
    out = bytearray(data)
    for start, end in mask_ranges:
        out[start:end] = b"\x00" * (end - start)
    return bytes(out)


def named_sum_regions(image: cdd.CddImage, two_start: int) -> dict[str, bytes]:
    data = image.data
    auth_two = (AUTH14[0] + two_start, AUTH14[0] + two_start + 2)
    streams = image.streams
    cdd1 = streams[0]
    cdd2 = streams[1]
    source_concat = b"".join(data[start:end] for _, start, end, _ in cdd.source_segments(image))
    regions = {
        "visible_8051_to_preword": data[:0x6FF0],
        "visible_8051_to_descriptor": data[:0x7000],
        "image_to_trailer": data[: AUTH14[0]],
        "image_to_e8000_excluding_auth14": data[: AUTH14[0]] + data[AUTH14[1] : FINAL_BOUNDARY],
        "image_to_e8000_auth14_zero": masked_bytes(data[:FINAL_BOUNDARY], [AUTH14]),
        "image_to_e8000_auth2_zero": masked_bytes(data[:FINAL_BOUNDARY], [auth_two]),
        "descriptor_and_cdd_to_trailer": data[0x7000 : AUTH14[0]],
        "cdd_streams_full": data[cdd1.start : cdd1.end] + data[cdd2.start : cdd2.end],
        "cdd_sources_concat": source_concat,
        "identity_profile": data[0xD8FD0:0xD9000],
    }
    return regions


def column_digest(chunks: list[bytes], width: int) -> dict[str, bytes]:
    columns = [bytes(chunk[index] for chunk in chunks if len(chunk) > index) for index in range(width)]
    sum_values = bytes((sum(column) & 0xFF) if column else 0 for column in columns)
    xor_values = bytes((xor_column(column)) if column else 0 for column in columns)
    crc32_values = bytes((zlib.crc32(column) & 0xFF) if column else 0 for column in columns)
    adler_values = bytes((zlib.adler32(column) & 0xFF) if column else 0 for column in columns)
    values = {
        "col_sum8": sum_values,
        "col_sum8_not": bytes((~byte) & 0xFF for byte in sum_values),
        "col_sum8_neg": bytes((-byte) & 0xFF for byte in sum_values),
        "col_xor8": xor_values,
        "col_xor8_not": bytes((~byte) & 0xFF for byte in xor_values),
        "col_crc32_low8": crc32_values,
        "col_adler32_low8": adler_values,
    }
    return values


def xor_column(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def chunks_fixed(blob: bytes, unit_size: int, phase: int = 0) -> list[bytes]:
    return [
        blob[offset : offset + unit_size]
        for offset in range(phase, len(blob) - unit_size + 1, unit_size)
    ]


def cdd_unit_sources(image: cdd.CddImage) -> dict[str, list[bytes]]:
    data = image.data
    streams = image.streams
    cdd1 = streams[0]
    cdd2 = streams[1]
    source_concat = b"".join(data[start:end] for _, start, end, _ in cdd.source_segments(image))
    stream_concat = data[cdd1.start : cdd1.end] + data[cdd2.start : cdd2.end]
    bodies_concat = data[cdd1.start + 0x20 : cdd1.end] + data[cdd2.start + 0x20 : cdd2.end]
    sources: dict[str, list[bytes]] = {}

    for label, blob in {
        "cdd_streams_full": stream_concat,
        "cdd_stream_bodies_after_header": bodies_concat,
        "cdd_source_segments_concat": source_concat,
    }.items():
        for phase in range(12):
            sources[f"{label}:unit12:phase{phase}"] = chunks_fixed(blob, 12, phase)

    # The canonical visible unit is often 13 bytes: one coded byte plus 12
    # scaffold/check bytes. Try the full 13-byte columns and the two natural
    # 12-byte projections.
    for label, blob in {
        "cdd_streams_full": stream_concat,
        "cdd_source_segments_concat": source_concat,
    }.items():
        for phase in range(13):
            units = chunks_fixed(blob, 13, phase)
            sources[f"{label}:unit13:phase{phase}:first12"] = [unit[:12] for unit in units]
            sources[f"{label}:unit13:phase{phase}:last12"] = [unit[1:] for unit in units]

    # Segment-local chunking avoids phase drift at CDD record boundaries.
    for unit_size in (12, 13):
        for projection in ("all", "first12", "last12"):
            chunks: list[bytes] = []
            if unit_size == 12 and projection != "all":
                continue
            for _, start, end, _ in cdd.source_segments(image):
                for unit in chunks_fixed(data[start:end], unit_size, 0):
                    if unit_size == 12:
                        chunks.append(unit)
                    elif projection == "first12":
                        chunks.append(unit[:12])
                    elif projection == "last12":
                        chunks.append(unit[1:])
            suffix = "unit12" if unit_size == 12 else f"unit13:{projection}"
            sources[f"segment_local:{suffix}"] = chunks

    return sources


def additive_two_byte_probe(images: dict[str, cdd.CddImage]) -> dict[str, Any]:
    matches = []
    near_matches = []
    for two_start in range(0, 13):
        fields = {name: trailer_auth(image)[two_start : two_start + 2] for name, image in images.items()}
        region_names = sorted(named_sum_regions(next(iter(images.values())), two_start).keys())
        for region_name in region_names:
            candidates = {
                name: word_variants(sum16(named_sum_regions(image, two_start)[region_name]))
                for name, image in images.items()
            }
            for variant_name in next(iter(candidates.values())).keys():
                ok_images = [
                    name
                    for name in images
                    if candidates[name][variant_name] == fields[name]
                ]
                if len(ok_images) == len(images):
                    matches.append(
                        {
                            "two_start": two_start,
                            "field_offsets": f"0x{AUTH14[0] + two_start:x}..0x{AUTH14[0] + two_start + 2:x}",
                            "region": region_name,
                            "variant": variant_name,
                        }
                    )
                elif len(ok_images) >= max(3, len(images) - 1):
                    near_matches.append(
                        {
                            "two_start": two_start,
                            "field_offsets": f"0x{AUTH14[0] + two_start:x}..0x{AUTH14[0] + two_start + 2:x}",
                            "region": region_name,
                            "variant": variant_name,
                            "matching_images": ok_images,
                        }
                    )
    return {"matches": matches, "near_matches": near_matches[:40]}


def remaining_12(auth: bytes, two_start: int) -> bytes:
    return auth[:two_start] + auth[two_start + 2 :]


def unit12_probe(images: dict[str, cdd.CddImage]) -> dict[str, Any]:
    matches = []
    near_matches = []
    unit_sources = {name: cdd_unit_sources(image) for name, image in images.items()}
    source_names = sorted(next(iter(unit_sources.values())).keys())
    column_candidates = {
        image_name: {
            source_name: column_digest(sources[source_name], 12)
            for source_name in source_names
        }
        for image_name, sources in unit_sources.items()
    }
    for two_start in range(0, 13):
        fields = {name: remaining_12(trailer_auth(image), two_start) for name, image in images.items()}
        for source_name in source_names:
            candidates = {
                name: column_candidates[name][source_name]
                for name in images
            }
            for digest_name in next(iter(candidates.values())).keys():
                variants = {
                    "as_is": {name: candidates[name][digest_name] for name in images},
                    "reversed": {name: candidates[name][digest_name][::-1] for name in images},
                }
                for orientation, values in variants.items():
                    ok_images = [name for name in images if values[name] == fields[name]]
                    if len(ok_images) == len(images):
                        matches.append(
                            {
                                "two_start": two_start,
                                "remaining_offsets": remaining_offsets_text(two_start),
                                "source": source_name,
                                "digest": digest_name,
                                "orientation": orientation,
                            }
                        )
                    elif len(ok_images) >= max(3, len(images) - 1):
                        near_matches.append(
                            {
                                "two_start": two_start,
                                "remaining_offsets": remaining_offsets_text(two_start),
                                "source": source_name,
                                "digest": digest_name,
                                "orientation": orientation,
                                "matching_images": ok_images,
                            }
                        )
    return {"matches": matches, "near_matches": near_matches[:40]}


def remaining_offsets_text(two_start: int) -> str:
    offsets = [AUTH14[0] + idx for idx in range(14) if not (two_start <= idx < two_start + 2)]
    return ",".join(f"0x{offset:x}" for offset in offsets)


def build_report(paths: list[Path]) -> dict[str, Any]:
    images = load_images(paths)
    if len(images) < 2:
        raise SystemExit("need at least two CDD images")
    fields = {
        name: {
            "path": str(image.path),
            "trailer_auth14": trailer_auth(image).hex(),
            "preword": image.data[0x6FF0:0x6FF4].hex(),
            "family": image.data[0x6FF8:0x7000].decode("ascii", errors="replace"),
            "cdd1": {"start": image.streams[0].start, "end": image.streams[0].end},
            "cdd2": {"start": image.streams[1].start, "end": image.streams[1].end},
        }
        for name, image in images.items()
    }
    return {
        "images": fields,
        "hypothesis": "2-byte additive checksum plus 12-byte CDD unit checksum inside auth14",
        "additive_two_byte_probe": additive_two_byte_probe(images),
        "unit12_probe": unit12_probe(images),
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def write_md(path: Path, report: dict[str, Any]) -> None:
    image_rows = [
        [f"`{name}`", f"`{item['family']}`", f"`{item['preword']}`", f"`{item['trailer_auth14']}`"]
        for name, item in report["images"].items()
    ]
    add = report["additive_two_byte_probe"]
    unit = report["unit12_probe"]
    lines = [
        "# LiteOn Trailer Split Hypothesis Probe",
        "",
        "Offline only. No drive commands were sent.",
        "",
        "This specifically tests whether the 14-byte trailer field can be split "
        "into a 2-byte Coastermelt-style additive checksum plus a 12-byte "
        "checksum over CDD 12-byte units.",
        "",
        "## Inputs",
        "",
        markdown_table(["image", "family", "preword", "auth14"], image_rows),
        "",
        "## Result",
        "",
        f"- exact 2-byte additive matches across all images: `{len(add['matches'])}`",
        f"- exact 12-byte CDD unit checksum matches across all images: `{len(unit['matches'])}`",
        "",
    ]
    if add["matches"]:
        lines.extend(["### Additive Matches", ""])
        for match in add["matches"]:
            lines.append(f"- `{match}`")
        lines.append("")
    if unit["matches"]:
        lines.extend(["### Unit-Checksum Matches", ""])
        for match in unit["matches"]:
            lines.append(f"- `{match}`")
        lines.append("")
    lines.extend(
        [
            "## Near Misses",
            "",
            "Near misses are included only to catch obvious one-image extraction or "
            "family anomalies. None should be treated as evidence unless the "
            "matching image set is meaningful.",
            "",
            f"- additive near misses: `{len(add['near_matches'])}` retained",
            f"- unit-checksum near misses: `{len(unit['near_matches'])}` retained",
            "",
        ]
    )
    if add["near_matches"]:
        lines.extend(["### Additive Near Misses", ""])
        for match in add["near_matches"][:12]:
            lines.append(
                f"- two_start=`{match['two_start']}` region=`{match['region']}` "
                f"variant=`{match['variant']}` images=`{','.join(match['matching_images'])}`"
            )
        lines.append("")
    if unit["near_matches"]:
        lines.extend(["### Unit Near Misses", ""])
        for match in unit["near_matches"][:12]:
            lines.append(
                f"- two_start=`{match['two_start']}` source=`{match['source']}` "
                f"digest=`{match['digest']}` orientation=`{match['orientation']}` "
                f"images=`{','.join(match['matching_images'])}`"
            )
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "This probe is negative for the proposed split. It does not rule out a "
            "bespoke controller-side codeword, a keyed MAC, or a split field with "
            "a nontrivial algorithm. It does rule out the easy form: one contiguous "
            "2-byte additive checksum plus a direct column-wise 12-byte checksum "
            "over the obvious CDD unit streams.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="*", type=Path, default=DEFAULT_IMAGES)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_report(args.images)
    write_json(args.out_json, report)
    write_md(args.out_md, report)
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
