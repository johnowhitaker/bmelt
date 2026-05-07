#!/usr/bin/env python3
"""Run the guarded bridge-clamp proof before the decoded-oracle attempt.

Dry-run by default. With `--execute`, this script:

1. Runs the dynamic `0x07` bridge-clamp live test.
2. Analyzes that run and requires high-offset `0x0f0000` to change and restore.
3. Only then runs the dynamic `0x18` test with decoded-oracle offsets included.
4. Analyzes the `0x18` run.

All live writes are still performed by
`run_liteon_materialized_bridge_clamp_live_test.py`, which refuses to run write
paths unless `sg_inq` reports a visible PLDS DS-8ABSH optical LUN.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIVE_TEST = ROOT / "scripts/run_liteon_materialized_bridge_clamp_live_test.py"
ANALYZER = ROOT / "scripts/analyze_liteon_materialized_bridge_clamp_live_test.py"


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_cmd(cmd: list[str], *, execute: bool, check: bool = True) -> dict[str, Any]:
    print("+ " + " ".join(cmd))
    if not execute:
        return {"cmd": cmd, "dry_run": True}
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    record = {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", "replace"),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed rc={proc.returncode}: {' '.join(cmd)}\n"
            f"stdout={record['stdout']}\nstderr={record['stderr']}"
        )
    return record


def run_live_test(
    *,
    device: str,
    pico_port: str,
    out_root: Path,
    run_name: str,
    patch_kind: str,
    patch_value: int,
    dynamic_max_writes: int,
    include_decoded_oracle_offsets: bool,
    probe_repeat: int,
    execute: bool,
) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(LIVE_TEST),
        "--device",
        device,
        "--pico-port",
        pico_port,
        "--out-root",
        str(out_root),
        "--run-name",
        run_name,
        "--probe-repeat",
        str(probe_repeat),
        "--build-dynamic-candidate-from-baseline",
        "--dynamic-patch-kind",
        patch_kind,
        "--dynamic-patch-value",
        f"0x{patch_value:02x}",
        "--dynamic-max-writes",
        str(dynamic_max_writes),
    ]
    if include_decoded_oracle_offsets:
        cmd.append("--include-decoded-oracle-offsets")
    if execute:
        cmd.append("--execute")
    return run_cmd(cmd, execute=True)


def analyze_run(out_root: Path, run_name: str, execute: bool) -> dict[str, Any]:
    run_dir = out_root / run_name
    json_out = run_dir / f"{run_name}.analysis.json"
    md_out = run_dir / f"{run_name}.analysis.md"
    cmd = [sys.executable, str(ANALYZER), str(run_dir), "--json-out", str(json_out), "--md-out", str(md_out)]
    record = run_cmd(cmd, execute=execute)
    if not execute:
        return record
    report = json.loads(json_out.read_text())
    record["json_out"] = str(json_out)
    record["md_out"] = str(md_out)
    record["analysis"] = report
    return record


def high_offset_proof_passed(analysis: dict[str, Any]) -> bool:
    high = analysis.get("comparisons", {}).get("0x0f0000")
    if not high:
        return False
    return bool(high.get("patched_differs_from_baseline") and high.get("restored_matches_baseline"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--pico-port", default="/dev/ttyACM0")
    parser.add_argument("--out-root", type=Path, default=ROOT / "references/evidence/live")
    parser.add_argument("--run-prefix", default=f"bridge-oracle-ladder-{timestamp()}")
    parser.add_argument("--probe-repeat", type=int, default=3)
    parser.add_argument(
        "--dynamic-max-writes",
        type=int,
        default=6,
        help="maximum observed bridge-clamp slots to patch in each dynamic live-test candidate",
    )
    parser.add_argument(
        "--oracle-patch-kind",
        choices=("clamp-immediate", "threshold-immediate"),
        default="clamp-immediate",
        help="dynamic patch kind for the second decoded-oracle step",
    )
    parser.add_argument(
        "--oracle-patch-value",
        type=lambda value: int(value, 0),
        default=0x18,
        help="dynamic patch value for the second decoded-oracle step",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--force-0x18",
        action="store_true",
        help="with --execute, run the 0x18 step even if the 0x07 high-offset proof check fails",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run07 = f"{args.run_prefix}-clamp07"
    run18 = f"{args.run_prefix}-{args.oracle_patch_kind}-{args.oracle_patch_value:02x}"
    report: dict[str, Any] = {
        "run_prefix": args.run_prefix,
        "execute": args.execute,
        "run07": run07,
        "run18": run18,
        "dynamic_max_writes": args.dynamic_max_writes,
        "oracle_patch_kind": args.oracle_patch_kind,
        "oracle_patch_value": args.oracle_patch_value,
        "steps": [],
    }

    report["steps"].append(
        {
            "name": "run-0x07",
            "result": run_live_test(
                device=args.device,
                pico_port=args.pico_port,
                out_root=args.out_root,
                run_name=run07,
                patch_kind="clamp-immediate",
                patch_value=0x07,
                dynamic_max_writes=args.dynamic_max_writes,
                include_decoded_oracle_offsets=False,
                probe_repeat=args.probe_repeat,
                execute=args.execute,
            ),
        }
    )
    analysis07 = analyze_run(args.out_root, run07, args.execute)
    report["steps"].append({"name": "analyze-0x07", "result": analysis07})
    proof_ok = args.execute and high_offset_proof_passed(analysis07["analysis"])
    report["proof_0x07_ok"] = proof_ok
    if args.execute and not proof_ok and not args.force_0x18:
        summary = args.out_root / f"{args.run_prefix}.json"
        summary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        raise RuntimeError("0x07 high-offset proof did not pass; refusing 0x18 without --force-0x18")

    report["steps"].append(
        {
            "name": "run-0x18",
            "result": run_live_test(
                device=args.device,
                pico_port=args.pico_port,
                out_root=args.out_root,
                run_name=run18,
                patch_kind=args.oracle_patch_kind,
                patch_value=args.oracle_patch_value,
                dynamic_max_writes=args.dynamic_max_writes,
                include_decoded_oracle_offsets=True,
                probe_repeat=args.probe_repeat,
                execute=args.execute,
            ),
        }
    )
    report["steps"].append({"name": "analyze-0x18", "result": analyze_run(args.out_root, run18, args.execute)})

    if args.execute:
        summary = args.out_root / f"{args.run_prefix}.json"
        summary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"summary": str(summary), "proof_0x07_ok": proof_ok}, indent=2, sort_keys=True))
    else:
        print(json.dumps({"dry_run": True, "run07": run07, "run18": run18}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
