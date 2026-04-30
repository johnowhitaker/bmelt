#!/usr/bin/env python3
"""Compare normal-mode SCSI response bytes against known firmware artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SURVEY = (
    ROOT / "references/evidence/live/normal-mode-readonly/linux-drive1-standard-only-probe.json"
)
DEFAULT_F0 = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_GATEWAY = (
    ROOT / "references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin"
)
DEFAULT_XDATA = (
    ROOT / "references/evidence/live/linux-drive1-currentboot-xdata-0000-ffff-bulk-v2.bin"
)
DEFAULT_OUT = ROOT / "analysis/8051/normal-mode-response-surface-analysis.md"


F0_LANDMARKS = (
    (0x04450, 0x044b0, "lower/currentboot identity copy"),
    (0x06FF0, 0x07000, "pre-family word / family marker"),
    (0x07000, 0x0702C, "CDD outer descriptor"),
    (0x0702C, 0xCEC18, "CDD stream 1"),
    (0xD8FD0, 0xD9000, "identity/profile area"),
    (0xD9000, 0xE6401, "CDD stream 2"),
    (0xE7FE0, 0xE8000, "trailer seal / marker"),
)

GATEWAY_LANDMARKS = (
    (0x0000, 0xF000, "mixed currentboot controller/work window"),
    (0xF000, 0xFC20, "sealed CDD1 table mirror"),
    (0xFC20, 0xFDA0, "sealed CDD2 duplicate-prefix mirror"),
    (0xFF00, 0x10000, "repeated sealed CDD headers"),
)

XDATA_LANDMARKS = (
    (0x4000, 0x4020, "controller/status registers"),
    (0x4091, 0x4099, "controller address/FIFO registers"),
    (0x47b0, 0x47d8, "packet/controller status FIFO area"),
    (0x4E00, 0x4E60, "currentboot work/status table"),
    (0x803C, 0x803F, "response base pointer"),
    (0x810E, 0x8130, "currentboot identity/key/model window"),
    (0x818A, 0x8196, "CDB/packet shadow"),
)

PAD_BYTES = {0x00, 0x20, 0xFF}


def is_low_info(data: bytes) -> bool:
    if not data:
        return True
    if all(byte == 0 for byte in data) or all(byte == 0xFF for byte in data):
        return True
    return max(data.count(byte) for byte in set(data)) / len(data) > 0.8


def info_score(data: bytes) -> int:
    non_pad = [byte for byte in data if byte not in PAD_BYTES]
    printable = sum(1 for byte in data if 0x21 <= byte <= 0x7E)
    distinct_non_pad = len(set(non_pad))
    transitions = sum(1 for i in range(1, len(data)) if data[i] != data[i - 1])
    return len(non_pad) * 4 + printable * 2 + distinct_non_pad * 5 + transitions


def is_informative(data: bytes) -> bool:
    if len(data) < 8 or is_low_info(data):
        return False
    if sum(1 for byte in data if byte in PAD_BYTES) / len(data) > 0.75:
        return False
    non_pad_count = sum(1 for byte in data if byte not in PAD_BYTES)
    distinct_non_pad = len({byte for byte in data if byte not in PAD_BYTES})
    if non_pad_count < max(4, len(data) // 8):
        return False
    return distinct_non_pad >= 3


def ascii_sample(data: bytes, limit: int = 40) -> str:
    text = "".join(chr(byte) if 32 <= byte < 127 else "." for byte in data[:limit])
    return text.replace("|", "\\|")


def landmark_label(target_offset: int, landmarks: tuple[tuple[int, int, str], ...]) -> str:
    for start, end, label in landmarks:
        if start <= target_offset < end:
            return label
    return ""


def find_hits(
    response: bytes,
    target: bytes,
    min_len: int,
    landmarks: tuple[tuple[int, int, str], ...],
) -> list[dict[str, Any]]:
    """Find informative exact matches, suppressing padding-only coincidences."""
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int]] = set()
    if len(response) < min_len:
        return []
    for response_offset in range(0, len(response) - min_len + 1):
        seed = response[response_offset : response_offset + min_len]
        if not is_informative(seed):
            continue
        target_start = 0
        occurrences = 0
        while True:
            target_offset = target.find(seed, target_start)
            if target_offset < 0:
                break
            occurrences += 1
            # Extend both ways so adjacent seeds collapse to the same maximal match.
            left = 0
            while (
                response_offset - left > 0
                and target_offset - left > 0
                and response[response_offset - left - 1] == target[target_offset - left - 1]
            ):
                left += 1
            right = min_len
            while (
                response_offset + right < len(response)
                and target_offset + right < len(target)
                and response[response_offset + right] == target[target_offset + right]
            ):
                right += 1
            final_response_offset = response_offset - left
            final_target_offset = target_offset - left
            final_length = left + right
            key = (final_response_offset, final_target_offset, final_length)
            final_chunk = response[
                final_response_offset : final_response_offset + final_length
            ]
            if key not in seen and is_informative(final_chunk):
                seen.add(key)
                candidates.append(
                    {
                        "response_offset": final_response_offset,
                        "target_offset": final_target_offset,
                        "length": final_length,
                        "score": info_score(final_chunk),
                        "sample_hex": final_chunk[:16].hex(),
                        "sample_ascii": ascii_sample(final_chunk),
                        "landmark": landmark_label(final_target_offset, landmarks),
                    }
                )
            target_start = target_offset + 1
            if occurrences >= 64:
                break

    candidates.sort(key=lambda hit: (hit["length"], hit["score"]), reverse=True)
    hits: list[dict[str, Any]] = []
    for hit in candidates:
        contained = False
        for existing in hits:
            response_contained = (
                existing["response_offset"] <= hit["response_offset"]
                and hit["response_offset"] + hit["length"]
                <= existing["response_offset"] + existing["length"]
            )
            target_contained = (
                existing["target_offset"] <= hit["target_offset"]
                and hit["target_offset"] + hit["length"]
                <= existing["target_offset"] + existing["length"]
            )
            if response_contained and target_contained:
                contained = True
                break
        if contained:
            continue
        hits.append(hit)
        if len(hits) >= 12:
            break
    return hits


def parse_sense(stderr: str) -> str:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        if line.startswith("Sense key:"):
            return line
        if "Sense key:" in line:
            return line.split("Sense key:", 1)[1].strip()
    if lines:
        return "; ".join(lines[:2])
    return ""


def render(report: dict[str, Any], f0: bytes, gateway: bytes, xdata: bytes) -> str:
    rows: list[dict[str, Any]] = []
    for item in report["probes"]:
        hx = item.get("stdout_hex")
        data = bytes.fromhex(hx) if hx else b""
        rows.append(
            {
                "name": item["name"],
                "returncode": item["returncode"],
                "good": (
                    item.get("returncode") == 0
                    and item.get("status_good_text")
                    and not item.get("timed_out")
                ),
                "elapsed_s": item["elapsed_s"],
                "length": len(data),
                "sense": parse_sense(item.get("stderr") or ""),
                "f0_hits": find_hits(data, f0, 8, F0_LANDMARKS) if data else [],
                "gateway_hits": find_hits(data, gateway, 8, GATEWAY_LANDMARKS)
                if data
                else [],
                "xdata_hits": find_hits(data, xdata, 8, XDATA_LANDMARKS)
                if data
                else [],
            }
        )

    lines = [
        "# Normal-Mode Response Surface Analysis",
        "",
        "Date: 2026-04-30",
        "",
        "This is an offline comparison of the normal LD5M read-only command survey",
        "against the known F0 image, the `0x070000` currentboot gateway dump,",
        "and the captured currentboot XDATA dump.",
        "",
        "## Summary",
        "",
        "The normal drive has several fast host-visible response channels even with",
        "no disc inserted: standard `INQUIRY`, vendor `EXTRAINQ`, `MODE SENSE(10)`,",
        "`GET CONFIGURATION`, `GET EVENT STATUS`, and `MECHANISM STATUS`.",
        "`GET PERFORMANCE` timed out and should not be used as a casual trigger.",
        "`READ BUFFER id=02` is now excluded from the default survey because it hung",
        "the optical LUN once and required a Pico servo power cycle.",
        "",
        "The strongest response-source clue is paradoxical: normal `INQUIRY` and",
        "`EXTRAINQ` contain long exact byte strings that also exist in two visible",
        "F0 identity copies, but live edits to those copies did not affect normal",
        "LD5M identity after cold boot. So exact F0 equality here means the normal",
        "runtime uses the same template data, not necessarily that it reads those",
        "specific flash offsets.",
        "",
        "A second useful clue is that currentboot XDATA also contains partial",
        "normal-response material: the model string appears at `xdata[0x811e]`,",
        "`GET CONFIGURATION` feature bytes appear near `xdata[0x40a4]`, and a",
        "`MODE SENSE(10)` fragment appears near `xdata[0x4e1b]`. These are not",
        "yet proven normal-runtime sources, but they are better carryover/localizer",
        "targets than another blind visible-F0 hook.",
        "",
        "Follow-up live test: `xdata[0x811e] <- 0x58` read back correctly through",
        "the guarded currentboot XDATA hook, but the next currentboot identity",
        "response still returned canonical `DVD+-RW DS-8ABSH`; only the deliberate",
        "hook readback byte changed. So `0x811e` is not the live currentboot",
        "identity source.",
        "",
        "## Command Surface",
        "",
        "| command | rc | good | elapsed | bytes | sense / note |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        note = row["sense"].replace("|", "\\|")
        lines.append(
            f"| `{row['name']}` | {row['returncode']} | {str(row['good']).lower()} | "
            f"{row['elapsed_s']:.6f}s | {row['length']} | {note} |"
        )

    lines += [
        "",
        "## Exact Matches",
        "",
        "| command | target | response offset | target offset | len | sample |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in rows:
        for target_name, key in (
            ("F0", "f0_hits"),
            ("gateway+0x070000", "gateway_hits"),
            ("currentboot XDATA", "xdata_hits"),
        ):
            for hit in row[key][:6]:
                label = f" ({hit['landmark']})" if hit.get("landmark") else ""
                lines.append(
                    f"| `{row['name']}` | {target_name} | `0x{hit['response_offset']:02x}` | "
                    f"`0x{hit['target_offset']:05x}`{label} | `0x{hit['length']:x}` | "
                    f"`{hit['sample_hex']}` `{hit['sample_ascii']}` |"
                )

    lines += [
        "",
        "## Foothold Implications",
        "",
        "For a host-visible normal-runtime PoC, the best triggers are now:",
        "",
        "- `INQUIRY` / `EXTRAINQ`: fastest and richest responses, but the visible F0",
        "  identity copies are known not to be the live normal source.",
        "- `GET CONFIGURATION`: fast, returns structured feature data, and is likely",
        "  handled by the real optical runtime rather than only by the bridge.",
        "- `MODE SENSE(10)`: fast and returns a large response without media.",
        "- `GET EVENT STATUS` and `MECHANISM STATUS`: small but likely close to",
        "  runtime state machines.",
        "",
        "The immediate next experiment should not be another visible-F0 prefix hook.",
        "Better candidates are:",
        "",
        "1. a currentboot-to-LD5M RAM carryover marker test using the currentboot",
        "   XDATA write hook. Skip `xdata[0x811e]` as a live-template source; it",
        "   is now tested negative. Better remaining markers are `xdata[0x40a4]`",
        "   (GET CONFIG feature-list fragment) and `xdata[0x4e1b]` (MODE SENSE",
        "   fragment), though both are lower-confidence because the matches are",
        "   shorter and more structured;",
        "2. a normal-mode standard-command source-localization pass, patching only",
        "   already-proven restorable template bytes if a new candidate source is",
        "   identified;",
        "3. CDD/decoded-runtime work if we need to hook the actual normal command",
        "   handlers rather than visible fallback/currentboot handlers.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--survey", type=Path, default=DEFAULT_SURVEY)
    parser.add_argument("--f0", type=Path, default=DEFAULT_F0)
    parser.add_argument("--gateway", type=Path, default=DEFAULT_GATEWAY)
    parser.add_argument("--xdata", type=Path, default=DEFAULT_XDATA)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    report = json.loads(args.survey.read_text())
    f0 = args.f0.read_bytes()
    gateway = args.gateway.read_bytes()
    xdata = args.xdata.read_bytes()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(report, f0, gateway, xdata) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
