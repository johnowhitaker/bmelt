#!/usr/bin/env python3
"""Summarize a materialized bridge-clamp live-test capture directory.

This is offline analysis only. It expects files produced by
`probe_liteon_materialized_bridge_clamp_effect.py`, typically labels
`baseline`, `patched`, and `restored`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


CAPTURE_RE = re.compile(r"^(?P<label>.+)-r(?P<repeat>\d+)-id01-off(?P<offset>[0-9a-fA-F]{6})\.bin$")
CLAMP_PREFIX = bytes.fromhex("90 8a 4c e0 c3 94 0e 40 08 90 40 11 74")
CLAMP_SUFFIX = bytes.fromhex("f0")
CLAMP_VALUES_OF_INTEREST = [0x0E, 0x07, 0x18]


def clamp_pattern(value: int) -> bytes:
    return CLAMP_PREFIX + bytes([value & 0xFF]) + CLAMP_SUFFIX


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_captures(run_dir: Path) -> dict[str, dict[int, list[dict[str, Any]]]]:
    captures: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for path in sorted(run_dir.glob("*.bin")):
        match = CAPTURE_RE.match(path.name)
        if not match:
            continue
        label = match.group("label")
        offset = int(match.group("offset"), 16)
        data = path.read_bytes()
        captures.setdefault(label, {}).setdefault(offset, []).append(
            {
                "path": str(path),
                "repeat": int(match.group("repeat")),
                "length": len(data),
                "sha256": sha256(data),
                "first64_hex": data[:64].hex(),
            }
        )
    return captures


def stderr_preview(text: str, limit: int = 220) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def load_probe_attempts(run_dir: Path) -> dict[str, dict[int, list[dict[str, Any]]]]:
    """Load probe JSON summaries, including failed READ BUFFER attempts.

    The `.bin` files tell us what was successfully read. The probe's per-label
    JSON tells us about the important negative case: a candidate offset was
    requested but rejected, timed out, or returned a short response. That
    distinction matters for the bridge-oracle ladder, especially the `0x18`
    decoded-band step.
    """

    attempts: dict[str, dict[int, list[dict[str, Any]]]] = {}
    for path in sorted(run_dir.glob("*.json")):
        try:
            report = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        label = report.get("label")
        captures = report.get("captures")
        if not isinstance(label, str) or not isinstance(captures, list):
            continue
        expected_len = int(report.get("length", 0) or 0)
        for capture in captures:
            if not isinstance(capture, dict):
                continue
            offset = capture.get("offset")
            record = capture.get("record") or {}
            if not isinstance(offset, int) or not isinstance(record, dict):
                continue
            length = int(capture.get("length", 0) or 0)
            ok = (
                record.get("returncode") == 0
                and not record.get("timed_out")
                and (expected_len == 0 or length == expected_len)
            )
            attempts.setdefault(label, {}).setdefault(offset, []).append(
                {
                    "summary_path": str(path),
                    "repeat": capture.get("repeat"),
                    "length": length,
                    "expected_length": expected_len,
                    "sha256": capture.get("sha256"),
                    "returncode": record.get("returncode"),
                    "timed_out": bool(record.get("timed_out")),
                    "good": bool(record.get("good")),
                    "stdout_len": record.get("stdout_len"),
                    "cdb": record.get("cdb"),
                    "stderr_preview": stderr_preview(str(record.get("stderr", ""))),
                    "ok": ok,
                }
            )
    return attempts


def summarize_attempts(entries: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [entry for entry in entries if not entry["ok"]]
    return {
        "attempt_count": len(entries),
        "successful_attempts": len(entries) - len(failures),
        "failed_attempts": len(failures),
        "timed_out_attempts": sum(1 for entry in entries if entry["timed_out"]),
        "returncodes": sorted({str(entry["returncode"]) for entry in entries}),
        "stderr_previews": sorted(
            {entry["stderr_preview"] for entry in failures if entry["stderr_preview"]}
        )[:5],
        "cdbs": sorted({entry["cdb"] for entry in entries if entry.get("cdb")}),
    }


def summarize_hashes(entries: list[dict[str, Any]]) -> dict[str, Any]:
    hashes = [entry["sha256"] for entry in entries]
    return {
        "count": len(entries),
        "unique_hashes": sorted(set(hashes)),
        "stable": len(set(hashes)) == 1,
    }


def count_patterns(entries: list[dict[str, Any]], pattern: bytes) -> int:
    total = 0
    needle = pattern.hex()
    for entry in entries:
        path = Path(entry["path"])
        if not path.exists():
            continue
        total += path.read_bytes().hex().count(needle)
    return total


def count_clamp_values(entries: list[dict[str, Any]]) -> dict[str, int]:
    return {f"0x{value:02x}": count_patterns(entries, clamp_pattern(value)) for value in CLAMP_VALUES_OF_INTEREST}


def compare_labels(
    captures: dict[str, dict[int, list[dict[str, Any]]]],
    attempts: dict[str, dict[int, list[dict[str, Any]]]],
) -> dict[str, Any]:
    labels = sorted(set(captures) | set(attempts))
    offsets = sorted(
        {offset for by_offset in captures.values() for offset in by_offset}
        | {offset for by_offset in attempts.values() for offset in by_offset}
    )
    comparisons: dict[str, Any] = {}
    for offset in offsets:
        per_label = {}
        for label in labels:
            entries = captures.get(label, {}).get(offset, [])
            attempt_entries = attempts.get(label, {}).get(offset, [])
            attempt_summary = summarize_attempts(attempt_entries) if attempt_entries else None
            if entries:
                summary = summarize_hashes(entries)
                summary["clamp_pattern_hits_by_value"] = count_clamp_values(entries)
                summary["stock_clamp_pattern_hits"] = summary["clamp_pattern_hits_by_value"]["0x0e"]
                summary["patched_clamp_pattern_hits"] = summary["clamp_pattern_hits_by_value"]["0x07"]
                summary["patched_clamp18_pattern_hits"] = summary["clamp_pattern_hits_by_value"]["0x18"]
                if attempt_summary:
                    summary["attempts"] = attempt_summary
                per_label[label] = summary
            elif attempt_summary:
                per_label[label] = {
                    "count": 0,
                    "unique_hashes": [],
                    "stable": False,
                    "clamp_pattern_hits_by_value": {"0x0e": 0, "0x07": 0, "0x18": 0},
                    "stock_clamp_pattern_hits": 0,
                    "patched_clamp_pattern_hits": 0,
                    "patched_clamp18_pattern_hits": 0,
                    "attempts": attempt_summary,
                }
        baseline = per_label.get("baseline", {}).get("unique_hashes", [])
        patched = per_label.get("patched", {}).get("unique_hashes", [])
        restored = per_label.get("restored", {}).get("unique_hashes", [])
        comparisons[f"0x{offset:06x}"] = {
            "labels": per_label,
            "patched_differs_from_baseline": bool(baseline and patched and set(baseline) != set(patched)),
            "restored_matches_baseline": bool(baseline and restored and set(baseline) == set(restored)),
        }
    return comparisons


def build_assessment(comparisons: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    high = comparisons.get("0x0f0000")
    ordinary = comparisons.get("0x070000")
    marker = comparisons.get("0x074000")
    slot = comparisons.get("0x077000")
    if high:
        if high["patched_differs_from_baseline"] and high["restored_matches_baseline"]:
            lines.append("SUCCESS-LEANING: high-offset 0x0f0000 changed under patched firmware and restored to baseline.")
        elif high["patched_differs_from_baseline"]:
            lines.append("PARTIAL: high-offset 0x0f0000 changed under patched firmware, but restore did not match baseline.")
        else:
            lines.append("NO HIGH-OFFSET EFFECT: 0x0f0000 did not show a patched-vs-baseline hash change.")
    if ordinary and ordinary["patched_differs_from_baseline"]:
        lines.append("CAUTION: ordinary 0x070000 also changed; this may be phase/noise or a broad behavioral effect.")
    if marker and marker["patched_differs_from_baseline"]:
        lines.append("NOTE: 0x074000 changed; inspect bytes manually to separate old marker behavior from bridge-clamp effects.")
    if slot:
        base_hits = slot["labels"].get("baseline", {}).get("stock_clamp_pattern_hits", 0)
        patched_hits_07 = slot["labels"].get("patched", {}).get("patched_clamp_pattern_hits", 0)
        patched_hits_18 = slot["labels"].get("patched", {}).get("patched_clamp18_pattern_hits", 0)
        if base_hits:
            lines.append(f"BASELINE SLOT CHECK: 0x077000 contains {base_hits} stock clamp-pattern hit(s).")
        else:
            lines.append("BASELINE SLOT CHECK: 0x077000 did not show the stock clamp pattern in captured repeats.")
        if patched_hits_07:
            lines.append(f"PATCH SLOT CHECK: 0x077000 contains {patched_hits_07} clamp-pattern hit(s) patched to 0x07.")
        if patched_hits_18:
            lines.append(f"PATCH SLOT CHECK: 0x077000 contains {patched_hits_18} clamp-pattern hit(s) patched to 0x18.")
    decoded_successes = []
    decoded_partials = []
    for offset_text, comparison in comparisons.items():
        offset = int(offset_text, 16)
        if offset < 0x180000:
            continue
        if comparison["patched_differs_from_baseline"] and comparison["restored_matches_baseline"]:
            decoded_successes.append(offset_text)
        elif comparison["patched_differs_from_baseline"]:
            decoded_partials.append(offset_text)
    if decoded_successes:
        lines.append(
            "ORACLE-LEANING: decoded-band offset(s) changed under patched firmware and restored: "
            + ", ".join(decoded_successes)
        )
    if decoded_partials:
        lines.append(
            "DECODED-BAND PARTIAL: decoded-band offset(s) changed but did not restore to baseline: "
            + ", ".join(decoded_partials)
        )
    decoded_failures = []
    for offset_text, comparison in comparisons.items():
        offset = int(offset_text, 16)
        if offset < 0x180000:
            continue
        labels = comparison.get("labels", {})
        for label in ("baseline", "patched", "restored"):
            attempts = labels.get(label, {}).get("attempts")
            if attempts and attempts.get("failed_attempts", 0):
                decoded_failures.append(
                    f"{offset_text}/{label}: {attempts['failed_attempts']}/{attempts['attempt_count']} failed"
                )
    if decoded_failures:
        lines.append(
            "DECODED-BAND COMMAND FAILURES: " + "; ".join(decoded_failures[:8])
        )
    if not lines:
        lines.append("No baseline/patched/restored comparison could be made from the available files.")
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--md-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    captures = load_captures(args.run_dir)
    attempts = load_probe_attempts(args.run_dir)
    comparisons = compare_labels(captures, attempts)
    report = {
        "run_dir": str(args.run_dir),
        "labels": sorted(captures),
        "probe_summary_labels": sorted(attempts),
        "comparisons": comparisons,
        "assessment": build_assessment(comparisons),
    }
    json_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.write_text(json_text)
    else:
        print(json_text)

    if args.md_out:
        lines = [
            "# Materialized Bridge-Clamp Live-Test Analysis",
            "",
            f"Run directory: `{args.run_dir}`",
            "",
            "## Assessment",
            "",
        ]
        lines.extend(f"- {line}" for line in report["assessment"])
        lines.extend(["", "## Offsets", ""])
        for offset, comparison in comparisons.items():
            lines.append(f"### `{offset}`")
            lines.append("")
            lines.append(f"- patched differs from baseline: `{comparison['patched_differs_from_baseline']}`")
            lines.append(f"- restored matches baseline: `{comparison['restored_matches_baseline']}`")
            for label, summary in comparison["labels"].items():
                hashes = ", ".join(f"`{value[:16]}`" for value in summary["unique_hashes"])
                lines.append(f"- {label}: {summary['count']} captures, stable=`{summary['stable']}`, hashes={hashes}")
                attempts = summary.get("attempts")
                if attempts:
                    lines.append(
                        "  attempts: "
                        f"ok=`{attempts['successful_attempts']}/{attempts['attempt_count']}`, "
                        f"failed=`{attempts['failed_attempts']}`, "
                        f"timed_out=`{attempts['timed_out_attempts']}`, "
                        f"returncodes={', '.join(f'`{value}`' for value in attempts['returncodes'])}"
                    )
                    if attempts["stderr_previews"]:
                        lines.append(
                            "  stderr: "
                            + " | ".join(f"`{value}`" for value in attempts["stderr_previews"])
                        )
                if (
                    summary["stock_clamp_pattern_hits"]
                    or summary["patched_clamp_pattern_hits"]
                    or summary["patched_clamp18_pattern_hits"]
                ):
                    lines.append(
                        "  clamp hits: "
                        f"stock=`{summary['stock_clamp_pattern_hits']}`, "
                        f"patched07=`{summary['patched_clamp_pattern_hits']}`, "
                        f"patched18=`{summary['patched_clamp18_pattern_hits']}`"
                    )
            lines.append("")
        args.md_out.write_text("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
