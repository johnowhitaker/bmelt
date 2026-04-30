#!/usr/bin/env python3
"""Time selected read-only normal-mode SCSI commands repeatedly."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from probe_liteon_normal_mode_readonly import PROBES, Probe, run_probe


DEFAULT_NAMES = (
    "inquiry-standard-96",
    "inquiry-extrainq",
    "mode-sense10-all",
    "get-configuration-current",
    "get-configuration-all",
    "get-event-status-media",
    "mechanism-status",
)


def probe_by_name() -> dict[str, Probe]:
    return {probe.name: probe for probe in PROBES}


def summarize(items: list[dict[str, Any]]) -> dict[str, Any]:
    elapsed = [float(item["elapsed_s"]) for item in items]
    return {
        "count": len(items),
        "returncodes": sorted({str(item.get("returncode")) for item in items}),
        "all_good": all(
            item.get("returncode") == 0
            and item.get("status_good_text")
            and not item.get("timed_out")
            for item in items
        ),
        "median_s": statistics.median(elapsed),
        "min_s": min(elapsed),
        "max_s": max(elapsed),
        "stdout_lens": sorted({int(item.get("stdout_len") or 0) for item in items}),
        "stdout_sha256s": sorted(
            {item["stdout_sha256"] for item in items if item.get("stdout_sha256")}
        ),
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal-Mode Command Timing",
        "",
        f"Date: {report['timestamp_utc']}",
        "",
        "## Target",
        "",
        "```text",
        f"host   {report['host']}",
        f"device {report['device']}",
        "```",
        "",
        "## Summary",
        "",
        "| command | good | median | min | max | bytes | return codes |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in report["summary"]:
        lines.append(
            f"| `{row['name']}` | {str(row['all_good']).lower()} | "
            f"{row['median_s']:.6f}s | {row['min_s']:.6f}s | {row['max_s']:.6f}s | "
            f"`{','.join(map(str, row['stdout_lens']))}` | `{','.join(row['returncodes'])}` |"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default="/usr/bin/sg_raw")
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--process-timeout", type=int, default=8)
    parser.add_argument("--host", default="jonathan-thinkpad-t480s")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--name", action="append", choices=sorted(probe_by_name()))
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--keep-hex-limit", type=int, default=0x400)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    probes = probe_by_name()
    selected_names = args.name or list(DEFAULT_NAMES)
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": args.host,
        "device": args.device,
        "repeat": args.repeat,
        "runs": [],
        "summary": [],
    }
    for name in selected_names:
        probe = probes[name]
        rows: list[dict[str, Any]] = []
        for index in range(args.repeat):
            item = run_probe(args, probe)
            item["iteration"] = index
            rows.append(item)
            report["runs"].append(item)
            print(
                f"{name} #{index + 1}: rc={item['returncode']} "
                f"good={item['status_good_text']} timeout={item.get('timed_out', False)} "
                f"len={item['stdout_len']} elapsed={item['elapsed_s']:.6f}s",
                flush=True,
            )
            if args.delay:
                time.sleep(args.delay)
        summary = {"name": name, **summarize(rows)}
        report["summary"].append(summary)
        print(
            f"{name}: median={summary['median_s']:.6f}s max={summary['max_s']:.6f}s",
            flush=True,
        )
        if args.out_json:
            args.out_json.parent.mkdir(parents=True, exist_ok=True)
            args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        if args.out_md:
            args.out_md.parent.mkdir(parents=True, exist_ok=True)
            args.out_md.write_text(render_md(report))
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_md(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
