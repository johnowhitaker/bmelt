#!/usr/bin/env python3
"""Compare host-visible normal-mode response payloads across perturbation states.

The normal work-window is noisy and tile-like.  This script checks a simpler
question first: did a CDD/F0 perturbation change any actual SCSI command
response payload in a reversible way?
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RESPONSE_RE = re.compile(r"^\d+-cycle\d+-(?P<stimulus>.+)\.response\.bin$")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def first_diffs(a: bytes, b: bytes, limit: int = 16) -> list[dict[str, int | None]]:
    diffs: list[dict[str, int | None]] = []
    max_len = max(len(a), len(b))
    for offset in range(max_len):
        av = a[offset] if offset < len(a) else None
        bv = b[offset] if offset < len(b) else None
        if av != bv:
            diffs.append({"offset": offset, "a": av, "b": bv})
            if len(diffs) >= limit:
                break
    return diffs


def stimulus_from_name(path: Path) -> str:
    match = RESPONSE_RE.match(path.name)
    if match:
        return match.group("stimulus")
    return path.name.removesuffix(".response.bin")


def summarize_state(label: str, root: Path) -> dict[str, Any]:
    by_stimulus: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(root.glob("*.response.bin")):
        by_stimulus[stimulus_from_name(path)].append(path)

    stimuli: dict[str, Any] = {}
    for stimulus, paths in sorted(by_stimulus.items()):
        variants: dict[str, dict[str, Any]] = {}
        counts: Counter[str] = Counter()
        for path in paths:
            data = path.read_bytes()
            digest = sha256_hex(data)
            counts[digest] += 1
            if digest not in variants:
                variants[digest] = {
                    "sha256": digest,
                    "length": len(data),
                    "example": path.name,
                    "prefix_hex": data[:32].hex(),
                }
        ordered_variants = []
        for digest, count in counts.most_common():
            item = dict(variants[digest])
            item["count"] = count
            ordered_variants.append(item)
        stimuli[stimulus] = {
            "files": len(paths),
            "unique_variants": len(ordered_variants),
            "stable": len(ordered_variants) == 1,
            "variants": ordered_variants,
        }

    return {
        "label": label,
        "path": str(root),
        "response_files": sum(item["files"] for item in stimuli.values()),
        "stimuli": stimuli,
    }


def compare_states(states: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    stimulus_names = sorted(
        {
            stimulus
            for state in states.values()
            for stimulus in state["stimuli"].keys()
        }
    )
    comparisons: list[dict[str, Any]] = []
    for stimulus in stimulus_names:
        row: dict[str, Any] = {
            "stimulus": stimulus,
            "states": {},
            "stable_hashes": {},
            "reversible_mutation": False,
        }
        for label, state in states.items():
            item = state["stimuli"].get(stimulus)
            if not item:
                row["states"][label] = None
                continue
            row["states"][label] = {
                "files": item["files"],
                "unique_variants": item["unique_variants"],
                "stable": item["stable"],
                "top_sha256": item["variants"][0]["sha256"],
                "top_count": item["variants"][0]["count"],
                "top_length": item["variants"][0]["length"],
                "top_prefix_hex": item["variants"][0]["prefix_hex"],
            }
            if item["stable"]:
                row["stable_hashes"][label] = item["variants"][0]["sha256"]

        stable = row["stable_hashes"]
        if {"stock", "mutated", "restored"} <= set(stable):
            row["reversible_mutation"] = (
                stable["stock"] == stable["restored"]
                and stable["mutated"] != stable["stock"]
            )
        comparisons.append(row)
    return comparisons


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Normal Response Diff Under CDD Perturbations",
        "",
        "This is an offline check for a shortcut normal-mode side channel.",
        "Instead of trying to interpret the rotating `READ BUFFER` work-window,",
        "it asks whether any existing CDD perturbation changed an actual",
        "host-visible SCSI response payload.",
        "",
    ]

    reversible = [
        row for experiment in report["experiments"] for row in experiment["comparisons"]
        if row["reversible_mutation"]
    ]
    if reversible:
        lines.extend(
            [
                "## Shortcut Candidates",
                "",
                "These responses changed under mutation and returned after restore:",
                "",
                "| Experiment | Stimulus | Stock/restored SHA-256 | Mutated SHA-256 |",
                "|---|---|---|---|",
            ]
        )
        for item in reversible:
            lines.append(
                f"| `{item['experiment']}` | `{item['stimulus']}` | "
                f"`{item['stable_hashes']['stock'][:12]}` | "
                f"`{item['stable_hashes']['mutated'][:12]}` |"
            )
        lines.append("")
    else:
        lines.extend(
            [
                "## Result",
                "",
                "No reversible host-visible response payload changes were found in",
                "the existing captures. The CDD edits clearly perturb the normal",
                "work-window, but the captured command responses stayed stable or",
                "the experiment lacked complete stock/mutated/restored states.",
                "",
            ]
        )

    lines.extend(["## Experiments", ""])
    for experiment in report["experiments"]:
        lines.append(f"### {experiment['name']}")
        lines.append("")
        lines.append("| State | Path | Response files | Stimuli | Stable stimuli |")
        lines.append("|---|---|---:|---:|---:|")
        for label, state in experiment["states"].items():
            stable_count = sum(1 for item in state["stimuli"].values() if item["stable"])
            lines.append(
                f"| `{label}` | `{state['path']}` | {state['response_files']} | "
                f"{len(state['stimuli'])} | {stable_count} |"
            )
        lines.append("")
        lines.append("| Stimulus | State summary |")
        lines.append("|---|---|")
        for row in experiment["comparisons"]:
            pieces = []
            for label, state in row["states"].items():
                if not state:
                    pieces.append(f"{label}: missing")
                    continue
                pieces.append(
                    f"{label}: {state['unique_variants']} variant(s), "
                    f"top `{state['top_sha256'][:12]}` x{state['top_count']}"
                )
            marker = " reversible" if row["reversible_mutation"] else ""
            lines.append(f"| `{row['stimulus']}` | {'; '.join(pieces)}{marker} |")
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "A positive result here would have been very useful: it would mean we",
            "could use ordinary SCSI responses as a normal-mode code/logic oracle.",
            "The negative result does not reduce the importance of the CDD",
            "perturbations. It just says the existing mutations landed in runtime",
            "work tiles rather than in the specific response path we captured.",
            "",
            "The next shortcut is to rank CDD records whose affected tiles sit near",
            "response-handling contigs, then test those as targeted perturbations.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def parse_state(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("state must be LABEL=PATH")
    label, raw_path = value.split("=", 1)
    if not label:
        raise argparse.ArgumentTypeError("state label cannot be empty")
    return label, Path(raw_path)


def parse_experiment(value: str) -> tuple[str, dict[str, Path]]:
    name, *state_parts = value.split(",")
    if not name:
        raise argparse.ArgumentTypeError("experiment name cannot be empty")
    states = dict(parse_state(part) for part in state_parts if part)
    if not states:
        raise argparse.ArgumentTypeError(
            "experiment must include state specs: NAME,stock=PATH,mutated=PATH"
        )
    return name, states


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment",
        action="append",
        type=parse_experiment,
        required=True,
        help="NAME,LABEL=PATH,LABEL=PATH...; use labels stock/mutated/restored when available",
    )
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    experiments = []
    for name, state_paths in args.experiment:
        states = {
            label: summarize_state(label, root)
            for label, root in sorted(state_paths.items())
        }
        comparisons = compare_states(states)
        for row in comparisons:
            row["experiment"] = name
        experiments.append(
            {
                "name": name,
                "states": states,
                "comparisons": comparisons,
            }
        )

    report = {
        "schema": "liteon-normal-response-diff-v1",
        "experiments": experiments,
    }
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True))
    write_markdown(args.out_md, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
