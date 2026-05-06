#!/usr/bin/env python3
"""Guarded live test for the materialized READ BUFFER bridge-clamp hook.

Dry-run by default. With `--execute`, this script:

1. Refuses to continue unless `sg_inq` reports a PLDS DS-8ABSH optical LUN.
2. Captures baseline READ BUFFER windows with
   `probe_liteon_materialized_bridge_clamp_effect.py`.
3. Installs the `post-materializer-runtime-bridge-clamp07` helper-bypass
   candidate using the existing persistence experiment runner.
4. Cold-cycles with the Pico servo, then captures the same READ BUFFER windows.
5. Installs the matching restore candidate, cold-cycles, and captures again.

It does not invent new CDBs. The only write steps are the already-rendered
helper-bypass candidates, and they are gated on visible PLDS identity.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = (
    ROOT
    / "references/firmware/extracted/helper-bypass-candidates/post-materializer-runtime-bridge-clamp07/"
    / "liteon-full-currentboot-ld5m-helper-bypass-post-materializer-runtime-bridge-clamp07-candidate.json"
)
RESTORE = (
    ROOT
    / "references/firmware/extracted/helper-bypass-candidates/post-materializer-runtime-bridge-clamp07-restore/"
    / "liteon-full-currentboot-ld5m-helper-bypass-post-materializer-runtime-bridge-clamp07-restore-candidate.json"
)
PROBE = ROOT / "scripts/probe_liteon_materialized_bridge_clamp_effect.py"
RUN_EXPERIMENT = ROOT / "scripts/run_liteon_linux_persistence_experiment.py"
PICO_CLIENT = ROOT / "pico/client.py"
BUILD_CANDIDATES = ROOT / "scripts/build_liteon_post_materializer_hook_candidates.py"
BUILD_DYNAMIC_CANDIDATE = ROOT / "scripts/build_liteon_dynamic_bridge_clamp_candidate.py"
STOCK_CLAMP_PATTERN = bytes.fromhex("90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 0e f0")


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_cmd(cmd: list[str], *, execute: bool, cwd: Path = ROOT, check: bool = True) -> dict[str, Any]:
    print("+ " + " ".join(cmd))
    if not execute:
        return {"cmd": cmd, "dry_run": True}
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
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


def check_plds_identity(device: str, execute: bool) -> dict[str, Any]:
    sg_inq = shutil.which("sg_inq") or "/usr/bin/sg_inq"
    record = run_cmd([sg_inq, device], execute=execute, check=execute)
    if not execute:
        return record
    text = (record["stdout"] + "\n" + record["stderr"]).upper()
    ok = "PLDS" in text and "DS-8ABSH" in text
    record["plds_ds8absh"] = ok
    if not ok:
        raise RuntimeError(
            f"refusing write path: {device} is not a visible PLDS DS-8ABSH optical LUN\n{text}"
        )
    return record


def ensure_candidate_files(execute: bool) -> dict[str, Any]:
    missing = [path for path in (CANDIDATE, RESTORE) if not path.exists()]
    record: dict[str, Any] = {
        "candidate": str(CANDIDATE),
        "restore": str(RESTORE),
        "missing": [str(path) for path in missing],
    }
    if not missing:
        record["generated"] = False
        return record
    cmd = [sys.executable, str(BUILD_CANDIDATES)]
    record["generate_result"] = run_cmd(cmd, execute=execute)
    record["generated"] = execute
    if execute:
        still_missing = [str(path) for path in (CANDIDATE, RESTORE) if not path.exists()]
        record["still_missing"] = still_missing
        if still_missing:
            raise FileNotFoundError("candidate generation did not produce: " + ", ".join(still_missing))
    return record


def capture_probe(device: str, out_dir: Path, label: str, repeat: int, execute: bool) -> dict[str, Any]:
    return run_cmd(
        [
            sys.executable,
            str(PROBE),
            "--device",
            device,
            "--out-dir",
            str(out_dir),
            "--label",
            label,
            "--repeat",
            str(repeat),
        ],
        execute=execute,
    )


def count_baseline_clamp_hits(out_dir: Path, label: str) -> dict[str, Any]:
    files = sorted(out_dir.glob(f"{label}-r*-id01-off077000.bin"))
    hits = 0
    for path in files:
        hits += path.read_bytes().count(STOCK_CLAMP_PATTERN)
    return {"label": label, "files": [str(path) for path in files], "stock_clamp_hits": hits}


def run_candidate(candidate: Path, device: str, execute: bool) -> dict[str, Any]:
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    return run_cmd(
        [
            sys.executable,
            str(RUN_EXPERIMENT),
            "--candidate",
            str(candidate.relative_to(ROOT)),
            "--device",
            device,
            "--skip-pre-f0",
            "--end-index",
            "544",
            "--f0-size",
            "0xe0000",
            "--capture-finalizer-status-after-event",
            "1",
            "--capture-finalizer-status",
            "--recover-on-currentboot",
        ],
        execute=execute,
    )


def build_dynamic_candidate(out_dir: Path, run_name: str, max_writes: int, execute: bool) -> dict[str, Any]:
    name = f"{run_name}-dynamic-bridge-clamp"
    record = run_cmd(
        [
            sys.executable,
            str(BUILD_DYNAMIC_CANDIDATE),
            str(out_dir),
            "--name",
            name,
            "--max-writes",
            str(max_writes),
        ],
        execute=execute,
    )
    if not execute:
        record["candidate"] = None
        return record

    candidate_dir = None
    for line in reversed(record["stdout"].splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "candidate_dir" in parsed:
            candidate_dir = Path(parsed["candidate_dir"])
            record["selection"] = parsed
            break
    if candidate_dir is None:
        raise RuntimeError("dynamic candidate builder did not report candidate_dir")
    slug = candidate_dir.name
    candidate = candidate_dir / f"liteon-full-currentboot-ld5m-helper-bypass-{slug}-candidate.json"
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    record["candidate"] = str(candidate)
    return record


def cold_cycle(pico_port: str | None, hold_ms: int, execute: bool) -> dict[str, Any]:
    if not pico_port:
        print("# skipping Pico cold cycle: no --pico-port")
        return {"skipped": True, "reason": "no pico port"}
    return run_cmd(
        [
            sys.executable,
            str(PICO_CLIENT),
            "--port",
            pico_port,
            "--timeout",
            str(max(8, (hold_ms // 1000) + 5)),
            f"TOGGLE SERVO {hold_ms}",
        ],
        execute=execute,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--pico-port", default="/dev/ttyACM0")
    parser.add_argument("--out-root", type=Path, default=ROOT / "references/evidence/live")
    parser.add_argument("--run-name", default=f"materialized-bridge-clamp-live-{timestamp()}")
    parser.add_argument("--probe-repeat", type=int, default=3)
    parser.add_argument("--servo-hold-ms", type=int, default=3000)
    parser.add_argument("--settle-s", type=float, default=8.0)
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="with --execute, run identity + baseline probe only; do not install candidates",
    )
    parser.add_argument(
        "--allow-no-baseline-clamp-hit",
        action="store_true",
        help="allow install even if baseline 0x077000 captures do not show the stock bridge clamp pattern",
    )
    parser.add_argument(
        "--build-dynamic-candidate-from-baseline",
        action="store_true",
        help="after baseline capture, build/install a candidate that patches only clamp slots visible in this run",
    )
    parser.add_argument("--dynamic-max-writes", type=int, default=3)
    parser.add_argument("--skip-restore", action="store_true")
    parser.add_argument("--execute", action="store_true", help="actually run live commands")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = args.out_root / args.run_name
    active_candidate = CANDIDATE
    report: dict[str, Any] = {
        "run_name": args.run_name,
        "device": args.device,
        "candidate": str(active_candidate),
        "restore": str(RESTORE),
        "dynamic_candidate_from_baseline": args.build_dynamic_candidate_from_baseline,
        "execute": args.execute,
        "steps": [],
    }
    if args.execute:
        out_dir.mkdir(parents=True, exist_ok=True)

    report["steps"].append({"name": "ensure-candidates", "result": ensure_candidate_files(args.execute)})
    report["steps"].append({"name": "identity-baseline", "result": check_plds_identity(args.device, args.execute)})
    report["steps"].append(
        {"name": "probe-baseline", "result": capture_probe(args.device, out_dir, "baseline", args.probe_repeat, args.execute)}
    )
    if args.execute:
        clamp_check = count_baseline_clamp_hits(out_dir, "baseline")
        report["steps"].append({"name": "baseline-clamp-check", "result": clamp_check})
    if args.preflight_only:
        if args.execute:
            summary_path = out_dir / f"{args.run_name}.json"
            summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"summary": str(summary_path), "preflight_only": True}, indent=2, sort_keys=True))
        else:
            print(json.dumps({"dry_run": True, "run_name": args.run_name, "preflight_only": True}, indent=2, sort_keys=True))
        return 0

    if args.execute:
        clamp_check = report["steps"][-1]["result"]
        if clamp_check["stock_clamp_hits"] < 1 and not args.allow_no_baseline_clamp_hit:
            summary_path = out_dir / f"{args.run_name}.json"
            summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            raise RuntimeError(
                "baseline 0x077000 captures did not show the stock bridge clamp pattern; "
                "refusing install without --allow-no-baseline-clamp-hit"
            )

    if args.build_dynamic_candidate_from_baseline:
        dynamic_result = build_dynamic_candidate(out_dir, args.run_name, args.dynamic_max_writes, args.execute)
        report["steps"].append({"name": "build-dynamic-candidate", "result": dynamic_result})
        if args.execute:
            active_candidate = Path(dynamic_result["candidate"])
            report["candidate"] = str(active_candidate)

    report["steps"].append({"name": "install-candidate", "result": run_candidate(active_candidate, args.device, args.execute)})
    report["steps"].append({"name": "cold-cycle-patched", "result": cold_cycle(args.pico_port, args.servo_hold_ms, args.execute)})
    if args.execute:
        time.sleep(args.settle_s)
    report["steps"].append({"name": "identity-patched", "result": check_plds_identity(args.device, args.execute)})
    report["steps"].append(
        {"name": "probe-patched", "result": capture_probe(args.device, out_dir, "patched", args.probe_repeat, args.execute)}
    )

    if not args.skip_restore:
        report["steps"].append({"name": "install-restore", "result": run_candidate(RESTORE, args.device, args.execute)})
        report["steps"].append({"name": "cold-cycle-restored", "result": cold_cycle(args.pico_port, args.servo_hold_ms, args.execute)})
        if args.execute:
            time.sleep(args.settle_s)
        report["steps"].append({"name": "identity-restored", "result": check_plds_identity(args.device, args.execute)})
        report["steps"].append(
            {
                "name": "probe-restored",
                "result": capture_probe(args.device, out_dir, "restored", args.probe_repeat, args.execute),
            }
        )

    if args.execute:
        summary_path = out_dir / f"{args.run_name}.json"
        summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"summary": str(summary_path)}, indent=2, sort_keys=True))
    else:
        print(json.dumps({"dry_run": True, "run_name": args.run_name}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
