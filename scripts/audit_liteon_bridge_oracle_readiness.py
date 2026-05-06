#!/usr/bin/env python3
"""Audit readiness for the materialized bridge-clamp oracle ladder.

This script sends no firmware-update or helper-bypass writes. It is intended
for the current blocked phase where the offline bridge-oracle tooling is ready,
but the Linux bench may only expose the USB bridge fallback.

Checks performed:

* local bridge-oracle scripts compile;
* fixed bridge-clamp candidate verifier passes;
* dynamic builder/verifier/analyzer smoke test passes against synthetic data;
* post-materializer multi-blob writer dry-run fits the selector22
  cave+trampoline smoke target;
* guarded ladder dry-run renders the expected steps;
* optional Linux bench read-only probe reports whether a PLDS optical LUN is
  visible and whether the Pico port exists.

By default, absence of a live PLDS LUN is reported as a blocker but does not
make the command fail. Use `--require-live-ready` when you want CI-like failure
until the drive is actually visible.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_IMAGE = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"

WATCHER = ROOT / "scripts/watch_liteon_plds_preflight.py"
LADDER = ROOT / "scripts/run_liteon_bridge_oracle_ladder.py"
LIVE_TEST = ROOT / "scripts/run_liteon_materialized_bridge_clamp_live_test.py"
DYNAMIC_BUILDER = ROOT / "scripts/build_liteon_dynamic_bridge_clamp_candidate.py"
VERIFIER = ROOT / "scripts/verify_liteon_bridge_clamp_candidate.py"
ANALYZER = ROOT / "scripts/analyze_liteon_materialized_bridge_clamp_live_test.py"
PROBE = ROOT / "scripts/probe_liteon_materialized_bridge_clamp_effect.py"
MULTI_BLOB_BUILDER = ROOT / "scripts/build_liteon_post_materializer_multi_blob_writer_candidate.py"
RESTORE_ROOT = ROOT / "references/firmware/extracted/helper-bypass-candidates"

REQUIRED_SCRIPTS = [
    WATCHER,
    LADDER,
    LIVE_TEST,
    DYNAMIC_BUILDER,
    VERIFIER,
    ANALYZER,
    PROBE,
    MULTI_BLOB_BUILDER,
]

STOCK_CLAMP = bytes.fromhex("90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 0e f0")
PATCH18_CLAMP = bytes.fromhex("90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 18 f0")
SYNTHETIC_CLAMP_IMMEDIATE_OFFSETS = [0x156, 0x196, 0x0E6, 0x026, 0x0A6, 0x066]
CLAMP_IMMEDIATE_INDEX = 13
HOOK_OFFSET = 0x422C
CAVE_OFFSET = 0x6EE3
MULTI_BLOB_PAYLOAD_LEN = 141
STOCK_HOOK = bytes.fromhex("e4 f5 d0")
PATCHED_HOOK = bytes.fromhex("12 6e e3")
EXPECTED_HELPER_PATCHES = {
    ("0x2b5", "0232c4"),
    ("0x169", "752204"),
    ("0x345", "752440"),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: float = 120.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": proc.stdout.decode("utf-8", "replace"),
            "stderr": proc.stderr.decode("utf-8", "replace"),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        return {
            "cmd": cmd,
            "returncode": None,
            "timed_out": True,
            "stdout": stdout.decode("utf-8", "replace") if isinstance(stdout, bytes) else str(stdout),
            "stderr": stderr.decode("utf-8", "replace") if isinstance(stderr, bytes) else str(stderr),
        }


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, **extra: Any) -> None:
    checks.append({"name": name, "ok": bool(ok), **extra})


def py_compile_check(checks: list[dict[str, Any]]) -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_SCRIPTS if not path.exists()]
    add_check(checks, "required_scripts_exist", not missing, missing=missing)
    if missing:
        return
    result = run([sys.executable, "-m", "py_compile", *[str(path) for path in REQUIRED_SCRIPTS]])
    add_check(checks, "required_scripts_py_compile", result["returncode"] == 0, result=result)


def fixed_candidate_check(checks: list[dict[str, Any]], tmp: Path) -> None:
    result = run(
        [
            sys.executable,
            str(VERIFIER),
            "--json-out",
            str(tmp / "fixed-verify.json"),
            "--md-out",
            str(tmp / "fixed-verify.md"),
        ]
    )
    parsed: dict[str, Any] | None = None
    if (tmp / "fixed-verify.json").exists():
        parsed = json.loads((tmp / "fixed-verify.json").read_text())
    add_check(
        checks,
        "fixed_bridge_clamp_candidate_verifies",
        result["returncode"] == 0 and bool(parsed and parsed.get("all_ok")),
        result=result,
        verifier_all_ok=bool(parsed and parsed.get("all_ok")),
    )


def write_synthetic_capture_tree(tmp: Path) -> tuple[Path, Path]:
    baseline = tmp / "synthetic-baseline"
    run_dir = tmp / "synthetic-run"
    baseline.mkdir()
    run_dir.mkdir()

    blob = bytearray([0x55] * 0x1000)
    for immediate_offset in SYNTHETIC_CLAMP_IMMEDIATE_OFFSETS:
        pattern_start = immediate_offset - CLAMP_IMMEDIATE_INDEX
        blob[pattern_start : pattern_start + len(STOCK_CLAMP)] = STOCK_CLAMP
    (baseline / "baseline-r0-id01-off077000.bin").write_bytes(blob)

    for label, pattern in (("baseline", STOCK_CLAMP), ("patched", PATCH18_CLAMP), ("restored", STOCK_CLAMP)):
        out = bytearray([0x11] * 0x1000)
        for immediate_offset in SYNTHETIC_CLAMP_IMMEDIATE_OFFSETS:
            pattern_start = immediate_offset - CLAMP_IMMEDIATE_INDEX
            out[pattern_start : pattern_start + len(pattern)] = pattern
        (run_dir / f"{label}-r0-id01-off077000.bin").write_bytes(out)

    # Minimal direct-effect signatures for the analyzer.
    (run_dir / "baseline-r0-id01-off0f0000.bin").write_bytes(bytes([0x10]) * 0x80)
    (run_dir / "patched-r0-id01-off0f0000.bin").write_bytes(bytes([0x18]) * 0x80)
    (run_dir / "restored-r0-id01-off0f0000.bin").write_bytes(bytes([0x10]) * 0x80)
    (run_dir / "baseline-r0-id01-off184000.bin").write_bytes(bytes([0x20]) * 0x80)
    (run_dir / "patched-r0-id01-off184000.bin").write_bytes(bytes([0x24]) * 0x80)
    (run_dir / "restored-r0-id01-off184000.bin").write_bytes(bytes([0x20]) * 0x80)
    for label in ("baseline", "patched", "restored"):
        captures = []
        for offset in (0x077000, 0x0F0000, 0x184000):
            data_path = run_dir / f"{label}-r0-id01-off{offset:06x}.bin"
            captures.append(
                {
                    "repeat": 0,
                    "offset": offset,
                    "path": str(data_path),
                    "length": 0x80 if offset != 0x077000 else 0x1000,
                    "sha256": "synthetic",
                    "first64_hex": "",
                    "record": {
                        "cdb": f"3C 01 01 {(offset >> 16) & 0xff:02X} {(offset >> 8) & 0xff:02X} {offset & 0xff:02X} 00 00 80 00",
                        "returncode": 0,
                        "timed_out": False,
                        "stdout_len": 0x80 if offset != 0x077000 else 0x1000,
                        "stderr": "SCSI Status: Good",
                        "good": True,
                    },
                }
            )
        captures.append(
            {
                "repeat": 0,
                "offset": 0x198900,
                "path": str(run_dir / f"{label}-r0-id01-off198900.bin"),
                "length": 0,
                "sha256": None,
                "first64_hex": "",
                "record": {
                    "cdb": "3C 01 01 19 89 00 00 00 80 00",
                    "returncode": 2,
                    "timed_out": False,
                    "stdout_len": 0,
                    "stderr": "synthetic CHECK CONDITION",
                    "good": False,
                },
            }
        )
        (run_dir / f"{label}.json").write_text(
            json.dumps(
                {
                    "label": label,
                    "device": "/dev/synthetic",
                    "length": 0x80,
                    "captures": captures,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    return baseline, run_dir


def dynamic_smoke_check(checks: list[dict[str, Any]], tmp: Path) -> None:
    baseline, run_dir = write_synthetic_capture_tree(tmp)
    candidate_root = tmp / "candidates"
    build = run(
        [
            sys.executable,
            str(DYNAMIC_BUILDER),
            str(baseline),
            "--name",
            "codex-readiness-dynamic-clamp18",
            "--out-dir",
            str(candidate_root),
            "--max-writes",
            "6",
            "--patch-value",
            "0x18",
        ]
    )
    candidate_dir = candidate_root / "codex-readiness-dynamic-clamp18"
    verify = run(
        [
            sys.executable,
            str(VERIFIER),
            "--candidate-root",
            str(candidate_root),
            "--restore-root",
            str(RESTORE_ROOT),
            "--candidate-slug",
            candidate_dir.name,
            "--restore-slug",
            "post-materializer-runtime-bridge-clamp07-restore",
            "--json-out",
            str(tmp / "dynamic-verify.json"),
            "--md-out",
            str(tmp / "dynamic-verify.md"),
        ]
    )
    analyze = run(
        [
            sys.executable,
            str(ANALYZER),
            str(run_dir),
            "--json-out",
            str(tmp / "dynamic-analysis.json"),
            "--md-out",
            str(tmp / "dynamic-analysis.md"),
        ]
    )

    verify_report = json.loads((tmp / "dynamic-verify.json").read_text()) if (tmp / "dynamic-verify.json").exists() else {}
    analysis = json.loads((tmp / "dynamic-analysis.json").read_text()) if (tmp / "dynamic-analysis.json").exists() else {}
    selection_path = candidate_dir / "dynamic-bridge-clamp-selection.json"
    selection = json.loads(selection_path.read_text()) if selection_path.exists() else {}
    high = analysis.get("comparisons", {}).get("0x0f0000", {})
    decoded = analysis.get("comparisons", {}).get("0x184000", {})
    rejected_decoded = analysis.get("comparisons", {}).get("0x198900", {}).get("labels", {}).get("patched", {}).get("attempts", {})
    slot = analysis.get("comparisons", {}).get("0x077000", {}).get("labels", {}).get("patched", {})
    ok = (
        build["returncode"] == 0
        and verify["returncode"] == 0
        and analyze["returncode"] == 0
        and verify_report.get("all_ok") is True
        and verify_report.get("cave_meta", {}).get("preserves_dptr") is True
        and len(selection.get("selected", [])) == 6
        and selection.get("payload_length", 9999) <= 0xDD
        and high.get("patched_differs_from_baseline") is True
        and high.get("restored_matches_baseline") is True
        and decoded.get("patched_differs_from_baseline") is True
        and decoded.get("restored_matches_baseline") is True
        and rejected_decoded.get("failed_attempts") == 1
        and slot.get("patched_clamp18_pattern_hits", 0) > 0
    )
    add_check(
        checks,
        "dynamic_0x18_builder_verifier_analyzer_smoke",
        ok,
        build_returncode=build["returncode"],
        verify_returncode=verify["returncode"],
        analyze_returncode=analyze["returncode"],
        verifier_all_ok=verify_report.get("all_ok"),
        verifier_cave_meta=verify_report.get("cave_meta"),
        selected=selection.get("selected"),
        payload_length=selection.get("payload_length"),
        high_offset=high,
        decoded_184000=decoded,
        rejected_decoded_198900=rejected_decoded,
        patched_slot=slot,
    )


def parse_last_json_line(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return {}


def split_patch_text(value: str) -> tuple[str, str]:
    offset, payload = value.split(":", 1)
    return offset.lower(), payload.lower()


def diff_offsets(base: bytes, other: bytes) -> list[int]:
    if len(base) != len(other):
        raise ValueError(f"length mismatch: {len(base)} != {len(other)}")
    return [index for index, (left, right) in enumerate(zip(base, other)) if left != right]


def multi_blob_smoke_check(checks: list[dict[str, Any]], tmp: Path) -> None:
    out_dir = tmp / "multi-blob-candidates"
    result = run(
        [
            sys.executable,
            str(MULTI_BLOB_BUILDER),
            "--runtime-patch",
            "0x077cd6:e4f5d022",
            "--runtime-patch",
            "0x078406:122cd6",
            "--name",
            "readiness-multi-blob-selector22-ret",
            "--out-dir",
            str(out_dir),
        ]
    )
    parsed = parse_last_json_line(result["stdout"])
    candidate_slug = parsed.get("candidate", "readiness-multi-blob-selector22-ret")
    restore_slug = parsed.get("restore", "readiness-multi-blob-selector22-ret-restore")
    candidate_dir = out_dir / candidate_slug
    restore_dir = out_dir / restore_slug

    artifact: dict[str, Any] = {"candidate_dir": str(candidate_dir), "restore_dir": str(restore_dir)}
    artifacts_ok = False
    try:
        base = BASE_IMAGE.read_bytes()
        candidate_image = candidate_dir / f"ld5m-helper-bypass-{candidate_slug}.bin"
        restore_image = restore_dir / f"ld5m-helper-bypass-{restore_slug}.bin"
        candidate_manifest = json.loads((candidate_dir / "manifest.json").read_text())
        restore_manifest = json.loads((restore_dir / "manifest.json").read_text())
        candidate = candidate_image.read_bytes()
        restore = restore_image.read_bytes()
        diffs = diff_offsets(base, candidate)
        expected_diff_ranges = set(range(HOOK_OFFSET, HOOK_OFFSET + len(PATCHED_HOOK))) | set(
            range(CAVE_OFFSET, CAVE_OFFSET + MULTI_BLOB_PAYLOAD_LEN)
        )
        candidate_helper_patches = {split_patch_text(value) for value in candidate_manifest.get("helper_patches", [])}
        restore_helper_patches = {split_patch_text(value) for value in restore_manifest.get("helper_patches", [])}
        artifact = {
            **artifact,
            "candidate_image_exists": candidate_image.exists(),
            "restore_image_exists": restore_image.exists(),
            "candidate_hook_hex": candidate[HOOK_OFFSET : HOOK_OFFSET + len(PATCHED_HOOK)].hex(),
            "base_hook_hex": base[HOOK_OFFSET : HOOK_OFFSET + len(STOCK_HOOK)].hex(),
            "restore_equals_base": restore == base,
            "candidate_changed_count": len(diffs),
            "candidate_unexpected_diff_offsets": [f"0x{offset:05x}" for offset in sorted(set(diffs) - expected_diff_ranges)[:16]],
            "candidate_helper_patches": sorted(f"{offset}:{payload}" for offset, payload in candidate_helper_patches),
            "restore_helper_patches": sorted(f"{offset}:{payload}" for offset, payload in restore_helper_patches),
        }
        artifacts_ok = (
            base[HOOK_OFFSET : HOOK_OFFSET + len(STOCK_HOOK)] == STOCK_HOOK
            and candidate[HOOK_OFFSET : HOOK_OFFSET + len(PATCHED_HOOK)] == PATCHED_HOOK
            and candidate[CAVE_OFFSET : CAVE_OFFSET + MULTI_BLOB_PAYLOAD_LEN] != b"\xff" * MULTI_BLOB_PAYLOAD_LEN
            and restore == base
            and set(diffs) <= expected_diff_ranges
            and len(diffs) == len(expected_diff_ranges)
            and EXPECTED_HELPER_PATCHES <= candidate_helper_patches
            and EXPECTED_HELPER_PATCHES <= restore_helper_patches
        )
    except Exception as exc:  # pragma: no cover - diagnostic path for readiness output
        artifact = {**artifact, "artifact_error": str(exc)}

    ok = (
        result["returncode"] == 0
        and parsed.get("patch_count") == 2
        and parsed.get("payload_len") == MULTI_BLOB_PAYLOAD_LEN
        and parsed.get("payload_room_remaining") == 80
        and parsed.get("runtime_patches")
        == [
            {"address": "0x077cd6", "blob_len": 4},
            {"address": "0x078406", "blob_len": 3},
        ]
        and artifacts_ok
    )
    add_check(
        checks,
        "multi_blob_selector22_artifact_smoke",
        ok,
        result=result,
        parsed=parsed,
        artifact=artifact,
    )


def ladder_dry_run_check(checks: list[dict[str, Any]], device: str, pico_port: str) -> None:
    result = run([sys.executable, str(LADDER), "--device", device, "--pico-port", pico_port])
    ok = result["returncode"] == 0 and "dry_run" in result["stdout"] and "clamp07" in result["stdout"] and "clamp18" in result["stdout"]
    add_check(checks, "bridge_oracle_ladder_dry_run", ok, result=result)


def parse_watcher_stdout(stdout: str) -> dict[str, Any]:
    parsed_lines = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed_lines.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    final = parsed_lines[-1] if parsed_lines else {}
    return {"json_lines": parsed_lines, "final": final}


def remote_readonly_check(checks: list[dict[str, Any]], linux_host: str | None, linux_cwd: str, pico_port: str) -> dict[str, Any]:
    if not linux_host:
        add_check(checks, "linux_bench_readonly_probe", True, skipped=True)
        return {"skipped": True}
    remote_cmd = (
        f"cd {linux_cwd} && "
        "hostname && "
        "(sg_map -i || true) && "
        f"(test -e {pico_port} && echo PICO_PRESENT=1 || echo PICO_PRESENT=0) && "
        f"python3 scripts/watch_liteon_plds_preflight.py --once --pico-port {pico_port}"
    )
    result = run(["ssh", "-o", "ConnectTimeout=8", linux_host, remote_cmd], timeout=30.0)
    parsed = parse_watcher_stdout(result["stdout"])
    plds = parsed.get("final", {}).get("plds_devices", [])
    pico_present = "PICO_PRESENT=1" in result["stdout"]
    ok = result["returncode"] in {0, 2}
    add_check(
        checks,
        "linux_bench_readonly_probe",
        ok,
        result=result,
        watcher=parsed,
        plds_devices=plds,
        pico_present=pico_present,
    )
    return {"plds_devices": plds, "pico_present": pico_present, "result": result, "watcher": parsed}


def build_assessment(report: dict[str, Any]) -> list[str]:
    checks = report["checks"]
    failed = [row["name"] for row in checks if not row["ok"] and row["name"] != "linux_bench_readonly_probe"]
    linux_probe = next((row for row in checks if row["name"] == "linux_bench_readonly_probe"), None)
    lines = []
    if failed:
        lines.append("Offline readiness has failures: " + ", ".join(failed))
    else:
        lines.append("Offline bridge-oracle readiness checks passed.")

    plds = report.get("linux_bench", {}).get("plds_devices") or []
    if plds:
        device = plds[0]
        lines.append(f"Live gate is open: PLDS DS-8ABSH is visible at {device}.")
        lines.append(
            "Next guarded command: "
            f"python3 scripts/run_liteon_bridge_oracle_ladder.py --device {device} "
            f"--pico-port {report['pico_port']} --execute"
        )
    else:
        lines.append("Live gate is closed: no PLDS DS-8ABSH optical LUN is visible.")
    if linux_probe and not linux_probe["ok"]:
        rc = linux_probe.get("result", {}).get("returncode")
        lines.append(f"Linux bench read-only probe failed or timed out (rc={rc}); offline readiness is still reported separately.")
    if report.get("require_live_ready") and not plds:
        lines.append("Because --require-live-ready was set, this is a failing readiness state.")
    return lines


def write_md(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Bridge Oracle Readiness Audit",
        "",
        f"timestamp UTC: `{report['timestamp_utc']}`",
        f"live ready: `{report['live_ready']}`",
        f"all offline ok: `{report['offline_ok']}`",
        "",
        "## Assessment",
        "",
    ]
    lines.extend(f"- {line}" for line in report["assessment"])
    lines.extend(["", "## Checks", "", "| check | ok |", "|---|---:|"])
    for row in report["checks"]:
        lines.append(f"| `{row['name']}` | `{row['ok']}` |")
    path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--pico-port", default="/dev/ttyACM0")
    parser.add_argument("--linux-host", default=None, help="optional ssh host, e.g. root@jonathan-thinkpad-t480s")
    parser.add_argument("--linux-cwd", default="/home/jonathan/boastermelt")
    parser.add_argument("--require-live-ready", action="store_true")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--md-out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="boastermelt-readiness-") as tmp_name:
        tmp = Path(tmp_name)
        py_compile_check(checks)
        fixed_candidate_check(checks, tmp)
        dynamic_smoke_check(checks, tmp)
        multi_blob_smoke_check(checks, tmp)
        ladder_dry_run_check(checks, args.device, args.pico_port)
        linux_bench = remote_readonly_check(checks, args.linux_host, args.linux_cwd, args.pico_port)

    offline_ok = all(row["ok"] for row in checks if row["name"] != "linux_bench_readonly_probe")
    live_ready = bool(linux_bench.get("plds_devices"))
    report = {
        "schema": "liteon-bridge-oracle-readiness-v1",
        "timestamp_utc": utc_now(),
        "device": args.device,
        "pico_port": args.pico_port,
        "linux_host": args.linux_host,
        "linux_cwd": args.linux_cwd,
        "require_live_ready": args.require_live_ready,
        "offline_ok": offline_ok,
        "live_ready": live_ready,
        "linux_bench": linux_bench,
        "checks": checks,
    }
    report["assessment"] = build_assessment(report)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        write_md(report, args.md_out)
    print(json.dumps({"offline_ok": offline_ok, "live_ready": live_ready, "assessment": report["assessment"]}, indent=2))

    if not offline_ok:
        return 1
    if args.require_live_ready and not live_ready:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
