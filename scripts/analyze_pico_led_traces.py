#!/usr/bin/env python3
"""Analyze Pico GP26 LED traces from helper payload probes.

The raw probe logs are useful but awkward to compare by eye.  This script
extracts phase-local waveform features from one or more
``pico-led-payload-probe.json`` files and optionally plots normalized phase
traces with baseline runs in gray.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def expand_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matched = sorted(Path().glob(pattern))
        if not matched:
            path = Path(pattern)
            if path.exists():
                matched = [path]
        paths.extend(path for path in matched if path.name == "pico-led-payload-probe.json")
    return sorted(dict.fromkeys(paths))


def marker_map(report: dict[str, Any]) -> dict[str, float]:
    return {item["name"]: float(item["t"]) for item in report.get("markers", [])}


def phase_samples(report: dict[str, Any], phase: str) -> list[dict[str, Any]]:
    markers = marker_map(report)
    ranges = {
        "pre": (0.0, markers.get("event68_start")),
        "event68": (markers.get("event68_start"), markers.get("event68_end")),
        "post_event68": (markers.get("event68_end"), markers.get("recovery_start")),
        "recovery": (markers.get("recovery_start"), markers.get("recovery_end")),
    }
    if phase not in ranges:
        raise ValueError(f"unknown phase {phase!r}")
    start, end = ranges[phase]
    if start is None or end is None:
        return []
    return [item for item in report.get("samples", []) if start <= float(item["t"]) <= end]


def longest_run(samples: list[dict[str, Any]], value: int) -> float:
    best = 0.0
    start: float | None = None
    last = None
    for item in samples:
        t = float(item["t"])
        digital = item.get("digital")
        if digital == value:
            if start is None:
                start = t
            last = t
        elif start is not None and last is not None:
            best = max(best, last - start)
            start = None
            last = None
    if start is not None and last is not None:
        best = max(best, last - start)
    return best


def transition_count(samples: list[dict[str, Any]]) -> int:
    transitions = 0
    prev = None
    for item in samples:
        digital = item.get("digital")
        if digital is None:
            continue
        if prev is not None and digital != prev:
            transitions += 1
        prev = digital
    return transitions


def features(report: dict[str, Any], path: Path, phase: str) -> dict[str, Any]:
    samples = phase_samples(report, phase)
    markers = marker_map(report)
    duration = None
    if phase == "event68" and "event68_start" in markers and "event68_end" in markers:
        duration = markers["event68_end"] - markers["event68_start"]
    values = [int(item["millivolts"]) for item in samples if item.get("millivolts") is not None]
    digitals = [int(item["digital"]) for item in samples if item.get("digital") is not None]
    high_count = sum(1 for value in digitals if value == 1)
    low_count = sum(1 for value in digitals if value == 0)
    count = len(samples)
    return {
        "label": report.get("label") or path.parent.name,
        "path": str(path),
        "phase": phase,
        "event68_returncode": (report.get("event68") or {}).get("returncode"),
        "recovery_returncode": (report.get("recovery") or {}).get("returncode"),
        "event68_elapsed_seconds": (report.get("event68") or {}).get("elapsed_seconds"),
        "duration_seconds": duration,
        "count": count,
        "millivolts_min": min(values) if values else None,
        "millivolts_max": max(values) if values else None,
        "millivolts_avg": mean(values) if values else None,
        "millivolts_std": pstdev(values) if len(values) > 1 else 0.0,
        "digital_high_count": high_count,
        "digital_low_count": low_count,
        "digital_high_fraction": high_count / len(digitals) if digitals else None,
        "transition_count": transition_count(samples),
        "longest_high_seconds": longest_run(samples, 1),
        "longest_low_seconds": longest_run(samples, 0),
    }


def baseline_stats(rows: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    keys = [
        "millivolts_avg",
        "millivolts_std",
        "digital_high_fraction",
        "transition_count",
        "longest_high_seconds",
        "longest_low_seconds",
        "event68_elapsed_seconds",
    ]
    out: dict[str, tuple[float, float]] = {}
    for key in keys:
        vals = [float(row[key]) for row in rows if row.get(key) is not None]
        if vals:
            sigma = pstdev(vals) if len(vals) > 1 else 0.0
            out[key] = (mean(vals), sigma)
    return out


def anomaly_score(row: dict[str, Any], stats: dict[str, tuple[float, float]]) -> float:
    score = 0.0
    for key, (mu, sigma) in stats.items():
        value = row.get(key)
        if value is None:
            continue
        scale = sigma if sigma > 1e-9 else max(abs(mu) * 0.05, 1.0)
        score += ((float(value) - mu) / scale) ** 2
    return math.sqrt(score)


def normalized_trace(report: dict[str, Any], phase: str, points: int) -> tuple[list[float], list[float]]:
    samples = phase_samples(report, phase)
    if len(samples) < 2:
        return [], []
    t0 = float(samples[0]["t"])
    t1 = float(samples[-1]["t"])
    if t1 <= t0:
        return [], []
    xs = [(float(item["t"]) - t0) / (t1 - t0) for item in samples]
    ys = [float(item.get("millivolts") or 0) for item in samples]
    out_x = [idx / (points - 1) for idx in range(points)]
    out_y: list[float] = []
    j = 0
    for x in out_x:
        while j + 1 < len(xs) and xs[j + 1] < x:
            j += 1
        if j + 1 >= len(xs):
            out_y.append(ys[-1])
        else:
            span = xs[j + 1] - xs[j]
            if span <= 0:
                out_y.append(ys[j])
            else:
                frac = (x - xs[j]) / span
                out_y.append(ys[j] + frac * (ys[j + 1] - ys[j]))
    return out_x, out_y


def write_plot(
    baseline: list[tuple[Path, dict[str, Any]]],
    candidates: list[tuple[Path, dict[str, Any]]],
    *,
    phase: str,
    out_png: Path,
    top_labels: set[str],
) -> None:
    import matplotlib.pyplot as plt

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6))
    for _path, report in baseline:
        x, y = normalized_trace(report, phase, 200)
        if x:
            ax.plot(x, y, color="#999999", alpha=0.45, linewidth=1.0)
    for _path, report in candidates:
        label = str(report.get("label") or "")
        if label not in top_labels:
            continue
        x, y = normalized_trace(report, phase, 200)
        if x:
            ax.plot(x, y, linewidth=1.5, label=label)
    ax.set_title(f"GP26 {phase} normalized traces")
    ax.set_xlabel("normalized phase time")
    ax.set_ylabel("millivolts")
    if top_labels:
        ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(out_png, dpi=160)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", nargs="+", required=True, help="baseline glob(s)")
    parser.add_argument("--candidate", nargs="+", required=True, help="candidate glob(s)")
    parser.add_argument("--phase", default="event68", choices=("pre", "event68", "post_event68", "recovery"))
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs/pico-led-analysis")
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--plot", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline_paths = expand_paths(args.baseline)
    candidate_paths = expand_paths(args.candidate)
    if not baseline_paths:
        raise SystemExit("no baseline traces found")
    if not candidate_paths:
        raise SystemExit("no candidate traces found")

    baseline_reports = [(path, json.loads(path.read_text(encoding="utf-8"))) for path in baseline_paths]
    candidate_reports = [(path, json.loads(path.read_text(encoding="utf-8"))) for path in candidate_paths]
    baseline_rows = [features(report, path, args.phase) for path, report in baseline_reports]
    candidate_rows = [features(report, path, args.phase) for path, report in candidate_reports]
    stats = baseline_stats(baseline_rows)
    for row in candidate_rows:
        row["anomaly_score"] = anomaly_score(row, stats)

    ranked = sorted(candidate_rows, key=lambda row: float(row.get("anomaly_score") or 0), reverse=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / f"pico-led-{args.phase}-features.csv"
    fieldnames = sorted({key for row in baseline_rows + candidate_rows for key in row})
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in baseline_rows:
            row = dict(row)
            row["anomaly_score"] = 0.0
            writer.writerow(row)
        for row in ranked:
            writer.writerow(row)

    json_path = args.out_dir / f"pico-led-{args.phase}-summary.json"
    summary = {
        "phase": args.phase,
        "baseline_count": len(baseline_rows),
        "candidate_count": len(candidate_rows),
        "baseline_stats": stats,
        "top": ranked[: args.top],
        "csv": str(csv_path),
    }
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.plot:
        top_labels = {str(row["label"]) for row in ranked[: args.top]}
        write_plot(
            baseline_reports,
            candidate_reports,
            phase=args.phase,
            out_png=args.out_dir / f"pico-led-{args.phase}-overlay.png",
            top_labels=top_labels,
        )
    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    for row in ranked[: args.top]:
        print(
            f"{row['anomaly_score']:.2f} {row['label']} "
            f"hi={row.get('digital_high_fraction')} avg={row.get('millivolts_avg')} "
            f"transitions={row.get('transition_count')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
