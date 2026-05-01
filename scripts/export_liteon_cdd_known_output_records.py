#!/usr/bin/env python3
"""Export per-record CDD known-output kits from normal work-window captures.

This is a convenience layer over the known-plaintext pair and adjacency
reports.  For each CDD record with observed decoded-looking tiles, it writes:

    record-XXX-encoded-source.bin   encoded CDD source span from LD5M F0
    record-XXX-known-output.bin     best public-slot consensus decoded bytes
    record-XXX-known-mask.bin       0xff where known-output has evidence
    record-XXX-slots.json           per-slot tile variants and counts

The output is intentionally labelled "known-output", not "decoded record".
The normal work-window public offsets are rotating slots.  The exported
relative positions are useful grammar hints, not proven decoded addresses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHUNK_SIZE = 0x40


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_ld5m_records(record_map: Path) -> list[dict[str, Any]]:
    data = json.loads(record_map.read_text())
    for image in data["images"]:
        if "LD5M" in image["image"].upper():
            return image["records"]
    raise ValueError(f"no LD5M image in {record_map}")


def record_for_public_offset(records: list[dict[str, Any]], offset: int) -> dict[str, Any] | None:
    for record in records:
        start = int(record["decoded_start"])
        end = start + int(record["decoded_span"])
        if start <= offset < end:
            return record
    return None


def collect_capture_paths(run_dirs: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for run_dir in run_dirs:
        paths.extend(sorted(run_dir.glob("*.window.bin")))
    return paths


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    f0 = args.f0.read_bytes()
    pair_report = json.loads(args.pairs.read_text())
    hidden_report = json.loads(args.hidden_chunks.read_text()) if args.hidden_chunks.exists() else {}
    records = load_ld5m_records(args.record_map)

    known_chunks: dict[str, dict[str, Any]] = {}
    for pair in pair_report["pairs"]:
        digest = pair["chunk_sha256"]
        known_chunks.setdefault(
            digest,
            {
                "short": pair["chunk_short"],
                "hex": pair["decoded_hex"],
                "bytes": bytes.fromhex(pair["decoded_hex"]),
                "pair_records": set(),
            },
        )
        known_chunks[digest]["pair_records"].add(int(pair["record"]))

    run_dirs = [ROOT / path for path in hidden_report.get("run_dirs", [])]
    if args.run_glob:
        run_dirs.extend(path for path in sorted(ROOT.glob(args.run_glob)) if path.is_dir())
    unique_run_dirs: list[Path] = []
    seen: set[Path] = set()
    for run_dir in run_dirs:
        resolved = run_dir.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique_run_dirs.append(run_dir)

    slot_variants: dict[int, dict[int, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    slot_examples: dict[tuple[int, int, str], list[dict[str, Any]]] = defaultdict(list)

    for path in collect_capture_paths(unique_run_dirs):
        data = path.read_bytes()
        for public_offset in range(0, len(data) - CHUNK_SIZE + 1, CHUNK_SIZE):
            chunk = data[public_offset : public_offset + CHUNK_SIZE]
            digest = sha256_hex(chunk)
            if digest not in known_chunks:
                continue
            record = record_for_public_offset(records, public_offset)
            if not record:
                continue
            record_index = int(record["index"])
            rel = public_offset - int(record["decoded_start"])
            slot_variants[record_index][rel][digest] += 1
            key = (record_index, rel, digest)
            if len(slot_examples[key]) < 4:
                slot_examples[key].append(
                    {
                        "run": path.parent.name,
                        "capture": path.name,
                        "public_offset": public_offset,
                    }
                )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    record_rows: list[dict[str, Any]] = []
    for record_index, slots in sorted(slot_variants.items()):
        record = records[record_index]
        decoded_span = int(record["decoded_span"])
        known_output = bytearray(b"\x00" * decoded_span)
        known_mask = bytearray(b"\x00" * decoded_span)
        slot_rows = []
        for rel, counter in sorted(slots.items()):
            top_digest, top_count = counter.most_common(1)[0]
            chunk = known_chunks[top_digest]["bytes"]
            write_start = max(0, rel)
            chunk_start = write_start - rel
            write_end = min(decoded_span, rel + len(chunk))
            if write_end > write_start:
                known_output[write_start:write_end] = chunk[chunk_start : chunk_start + (write_end - write_start)]
                known_mask[write_start:write_end] = b"\xff" * (write_end - write_start)
            slot_rows.append(
                {
                    "record_relative": rel,
                    "top_chunk": known_chunks[top_digest]["short"],
                    "top_sha256": top_digest,
                    "top_count": top_count,
                    "variant_count": len(counter),
                    "variants": [
                        {
                            "chunk": known_chunks[digest]["short"],
                            "sha256": digest,
                            "count": count,
                            "hex_prefix": known_chunks[digest]["hex"][:64],
                            "examples": slot_examples[(record_index, rel, digest)],
                        }
                        for digest, count in counter.most_common()
                    ],
                }
            )

        known_bytes = sum(1 for byte in known_mask if byte)
        if len(slot_rows) < args.min_known_slots:
            continue

        prefix = args.out_dir / f"record-{record_index:03d}"
        encoded = f0[int(record["source_start"]) : int(record["source_end"])]
        (prefix.with_name(prefix.name + "-encoded-source.bin")).write_bytes(encoded)
        (prefix.with_name(prefix.name + "-known-output.bin")).write_bytes(bytes(known_output))
        (prefix.with_name(prefix.name + "-known-mask.bin")).write_bytes(bytes(known_mask))
        (prefix.with_name(prefix.name + "-slots.json")).write_text(json.dumps(slot_rows, indent=2) + "\n")
        record_rows.append(
            {
                "record": record_index,
                "mode": int(record["mode"]),
                "operation_key": record["operation_key"],
                "source_start": int(record["source_start"]),
                "source_end": int(record["source_end"]),
                "source_len": int(record["source_len"]),
                "decoded_start": int(record["decoded_start"]),
                "decoded_span": decoded_span,
                "known_bytes": known_bytes,
                "known_fraction": known_bytes / decoded_span if decoded_span else 0,
                "slot_count": len(slot_rows),
                "variant_slots": sum(1 for row in slot_rows if row["variant_count"] > 1),
                "files": {
                    "encoded_source": str(prefix.with_name(prefix.name + "-encoded-source.bin")),
                    "known_output": str(prefix.with_name(prefix.name + "-known-output.bin")),
                    "known_mask": str(prefix.with_name(prefix.name + "-known-mask.bin")),
                    "slots": str(prefix.with_name(prefix.name + "-slots.json")),
                },
            }
        )

    record_rows.sort(key=lambda row: (-row["known_bytes"], -row["slot_count"], row["record"]))
    report = {
        "schema": "liteon-cdd-known-output-record-export-v1",
        "pairs": str(args.pairs),
        "hidden_chunks": str(args.hidden_chunks),
        "record_map": str(args.record_map),
        "f0": str(args.f0),
        "out_dir": str(args.out_dir),
        "records": record_rows,
    }
    (args.out_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join("---" for _ in headers) + " |")
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def write_md(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# CDD Known-Output Record Export",
        "",
        "This directory contains per-record kits for CDD records that have",
        "decoded-looking normal work-window tile evidence. The exported",
        "`known-output.bin` files are public-slot consensus artifacts, not proven",
        "complete decoded records.",
        "",
        "## Records",
        "",
        md_table(
            ["record", "mode", "op key", "source", "decoded", "known", "slots", "variant slots"],
            [
                [
                    str(row["record"]),
                    f"`0x{row['mode']:02x}`",
                    f"`{row['operation_key']}`",
                    str(row["source_len"]),
                    str(row["decoded_span"]),
                    f"{row['known_bytes']} ({row['known_fraction']:.0%})",
                    str(row["slot_count"]),
                    str(row["variant_slots"]),
                ]
                for row in report["records"]
            ],
        ),
        "",
        "## Use",
        "",
        "For a grammar experiment, start with records that combine high known",
        "coverage and low slot ambiguity. Compare `record-XXX-encoded-source.bin`",
        "against the masked bytes in `record-XXX-known-output.bin`, using",
        "`record-XXX-known-mask.bin` to ignore unknown positions.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pairs",
        type=Path,
        default=Path("analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.json"),
    )
    parser.add_argument(
        "--hidden-chunks",
        type=Path,
        default=Path("analysis/8051/normal-hidden-runtime-chunks-with-readonly-harvests-20260501.json"),
    )
    parser.add_argument(
        "--record-map",
        type=Path,
        default=Path("references/firmware/extracted/liteon-cdd-record-map.json"),
    )
    parser.add_argument(
        "--f0",
        type=Path,
        default=Path("references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"),
    )
    parser.add_argument("--run-glob", default="")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument("--min-known-slots", type=int, default=1)
    args = parser.parse_args()

    report = build_report(args)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    write_md(args.out_md, report)
    print(f"wrote {args.out_dir / 'summary.json'}")
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
