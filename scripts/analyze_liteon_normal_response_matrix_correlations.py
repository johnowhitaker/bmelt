#!/usr/bin/env python3
"""Look for CDB-field correlations in normal response-matrix captures.

Literal CDB echoes are easy to miss if only one shadow byte is exposed at a
time. This scans every byte offset in each captured normal work-window and
scores how often it equals a chosen host-side CDB field. It is deliberately
simple: high-scoring offsets are candidates for manual inspection, not proof of
a stable I/O channel.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_cdb(text: str) -> list[int]:
    return [int(part, 16) for part in text.split()]


def load_runs(summary_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report = json.loads(summary_path.read_text())
    root = summary_path.parent
    runs = []
    for run in report["runs"]:
        window_path = Path(run["window"]["path"])
        if not window_path.is_absolute():
            window_path = root / window_path.name
        cdb = parse_cdb(run["command"]["cdb"])
        runs.append(
            {
                "index": run["index"],
                "cycle": run["cycle"],
                "cycle_position": run.get("cycle_position"),
                "command": run["command"]["name"],
                "cdb": cdb,
                "data": window_path.read_bytes(),
            }
        )
    return report, runs


def field_value(cdb: list[int], field: str) -> int | None:
    if field.startswith("cdb"):
        index = int(field[3:], 0)
        return cdb[index] if index < len(cdb) else None
    if field == "opcode":
        return cdb[0]
    if field == "getcfg-rt":
        return cdb[1] & 0x03 if cdb and cdb[0] == 0x46 else None
    if field == "getcfg-feature-hi":
        return cdb[2] if cdb and cdb[0] == 0x46 else None
    if field == "getcfg-feature-lo":
        return cdb[3] if cdb and cdb[0] == 0x46 else None
    if field == "getevent-class":
        return cdb[4] if cdb and cdb[0] == 0x4A else None
    if field == "modesense-page":
        return cdb[2] if cdb and cdb[0] == 0x5A else None
    if field == "alloc-lo":
        if len(cdb) == 6:
            return cdb[4]
        if len(cdb) >= 10:
            return cdb[8]
    return None


def score_field(runs: list[dict[str, Any]], field: str, min_variety: int) -> list[dict[str, Any]]:
    selected = []
    for run in runs:
        value = field_value(run["cdb"], field)
        if value is not None:
            selected.append((run, value))
    if not selected:
        return []
    values = {value for _run, value in selected}
    if len(values) < min_variety:
        return []
    expected_majority = Counter(value for _run, value in selected).most_common(1)[0][1]

    length = min(len(run["data"]) for run, _value in selected)
    rows: list[dict[str, Any]] = []
    for offset in range(length):
        matches = 0
        byte_values: Counter[int] = Counter()
        by_expected: dict[int, Counter[int]] = {}
        for run, expected in selected:
            observed = run["data"][offset]
            byte_values[observed] += 1
            by_expected.setdefault(expected, Counter())[observed] += 1
            if observed == expected:
                matches += 1
        if matches == 0:
            continue
        lift = matches - expected_majority
        if lift <= 0 and len(byte_values) == 1:
            continue
        rows.append(
            {
                "field": field,
                "offset": offset,
                "matches": matches,
                "majority_baseline": expected_majority,
                "lift_over_majority": lift,
                "total": len(selected),
                "match_ratio": matches / len(selected),
                "unique_observed": len(byte_values),
                "unique_expected": len(values),
                "top_observed": [
                    {"value": value, "count": count}
                    for value, count in byte_values.most_common(8)
                ],
                "by_expected": {
                    f"0x{expected:02x}": [
                        {"value": value, "count": count}
                        for value, count in counter.most_common(6)
                    ]
                    for expected, counter in sorted(by_expected.items())
                },
            }
        )
    rows.sort(
        key=lambda row: (
            -row["lift_over_majority"],
            -row["matches"],
            -row["unique_observed"],
            row["offset"],
        )
    )
    return rows


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Response Matrix Correlations",
        "",
        "This scans work-window bytes for simple equality correlations with",
        "host CDB fields. It is a candidate finder; random/code-byte matches",
        "are expected, so the high-value cases are offsets that stay strong",
        "across shuffled command order and have plausible local context.",
        "",
        "## Inputs",
        "",
    ]
    for path in report["inputs"]:
        lines.append(f"- `{path}`")
    lines.extend(["", "## Top Candidates", ""])
    for input_report in report["reports"]:
        lines.append(f"### {input_report['name']}")
        for field, rows in input_report["fields"].items():
            if not rows:
                continue
            lines.append("")
            lines.append(f"#### `{field}`")
            lines.append("")
            lines.append("| offset | matches | total | ratio | observed |")
            lines.append("|---:|---:|---:|---:|---|")
            for row in rows[:20]:
                observed = ", ".join(
                    f"`0x{item['value']:02x}` x{item['count']}"
                    for item in row["top_observed"][:5]
                )
                lines.append(
                    f"| `+0x{row['offset']:04x}` | {row['matches']} | {row['total']} | "
                    f"{row['match_ratio']:.3f} / lift {row['lift_over_majority']} | {observed} |"
                )
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary_json", type=Path, nargs="+")
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    parser.add_argument(
        "--field",
        action="append",
        default=[
            "opcode",
            "cdb1",
            "cdb2",
            "cdb3",
            "cdb4",
            "cdb8",
            "alloc-lo",
            "getcfg-rt",
            "getcfg-feature-hi",
            "getcfg-feature-lo",
            "getevent-class",
            "modesense-page",
        ],
    )
    parser.add_argument("--limit", type=int, default=64)
    parser.add_argument("--min-variety", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output: dict[str, Any] = {"schema": "liteon-response-matrix-correlations-v1", "inputs": [str(path) for path in args.summary_json], "reports": []}
    for summary_path in args.summary_json:
        source_report, runs = load_runs(summary_path)
        fields = {}
        for field in args.field:
            fields[field] = score_field(runs, field, args.min_variety)[: args.limit]
        output["reports"].append(
            {
                "name": summary_path.parent.name,
                "source_timestamp_utc": source_report.get("timestamp_utc"),
                "runs": len(runs),
                "fields": fields,
            }
        )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_markdown(output).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
