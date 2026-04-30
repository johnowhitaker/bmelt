#!/usr/bin/env python3
"""Read XDATA or controller-gateway bits through a GOOD/GOOD helper timing channel.

The older bit channel used GOOD for 1 and the helper's DID_ERROR path for 0.
That is easy to interpret but rough on the drive. This tool always returns
through the helper success path. A selected bit value inserts the known delay
loop, and the host classifies the bit from event-68 elapsed time.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE_ROOT = ROOT / "references/firmware/extracted/helper-codeexec-candidates"
DEFAULT_OUT_DIR = ROOT / "runs/helper-xdata-timing-channel"
DEFAULT_CONTROLLER_OUT_DIR = ROOT / "runs/helper-controller-timing-channel"


def parse_addr(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFFFFFF:
        raise argparse.ArgumentTypeError("address must be 0..0xffffff")
    return parsed


def parse_byte(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("value must be 0..0xff")
    return parsed


def parse_skip(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0x20:
        raise argparse.ArgumentTypeError("skip must be 0..0x20")
    return parsed


def parse_bits(value: str) -> list[int]:
    bits: list[int] = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        parsed = int(item, 0)
        if not 0 <= parsed <= 7:
            raise argparse.ArgumentTypeError("bits must be in range 0..7")
        bits.append(parsed)
    if not bits:
        raise argparse.ArgumentTypeError("at least one bit is required")
    return bits


def run_command(cmd: list[str], *, check: bool = False, quiet: bool = False) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.stdout and not quiet:
        print(proc.stdout, end="")
    if proc.stderr and not quiet:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)
    return proc


def latest_result(run_root: Path) -> Path:
    results = sorted(run_root.glob("liteon-persistence-*/persistence-experiment-result.json"))
    if not results:
        raise FileNotFoundError(f"no persistence-experiment-result.json under {run_root}")
    return results[-1]


def event_by_index(result: dict[str, Any], index: int) -> dict[str, Any]:
    for event in result.get("events_attempted", []):
        if int(event.get("event_index", -1)) == index:
            return event
    raise KeyError(f"event {index} not present in result")


def candidate_path(args: argparse.Namespace, name: str) -> Path:
    return args.candidate_root / name / f"liteon-full-currentboot-ld5m-helper-codeexec-{name}-candidate.json"


def build_immediate_candidate(args: argparse.Namespace, name: str, value: int, bit: int) -> Path:
    candidate = candidate_path(args, name)
    if candidate.exists() and not args.rebuild:
        return candidate
    cmd = [
        sys.executable,
        str(ROOT / "scripts/build_liteon_helper_codeexec_candidate.py"),
        "--name",
        name,
        "--out-root",
        str(args.candidate_root),
        "immediate-bit-delay",
        "--value",
        f"0x{value:02x}",
        "--bit",
        str(bit),
        "--payload-offset",
        f"0x{args.payload_offset:04x}",
        "--delay-count",
        f"0x{args.delay_count:02x}",
    ]
    if args.delay_on_zero:
        cmd.append("--delay-on-zero")
    run_command(cmd, check=True, quiet=args.quiet_builder)
    return candidate


def build_xdata_candidate(args: argparse.Namespace, addr: int, bit: int) -> Path:
    if not 0 <= addr <= 0xFFFF:
        raise ValueError("XDATA address must be 0..0xffff")
    name = f"xdata-timing-{addr:04x}-bit{bit}"
    candidate = candidate_path(args, name)
    if candidate.exists() and not args.rebuild:
        return candidate
    cmd = [
        sys.executable,
        str(ROOT / "scripts/build_liteon_helper_codeexec_candidate.py"),
        "--name",
        name,
        "--out-root",
        str(args.candidate_root),
        "movx-bit-delay",
        "--addr",
        f"0x{addr:04x}",
        "--bit",
        str(bit),
        "--payload-offset",
        f"0x{args.payload_offset:04x}",
        "--delay-count",
        f"0x{args.delay_count:02x}",
    ]
    if args.delay_on_zero:
        cmd.append("--delay-on-zero")
    run_command(cmd, check=True, quiet=args.quiet_builder)
    return candidate


def build_controller_candidate(args: argparse.Namespace, addr: int, bit: int) -> Path:
    skip_part = "" if args.controller_skip == 0 else f"-skip{args.controller_skip:02x}"
    name = f"controller-timing-{addr:06x}{skip_part}-bit{bit}"
    candidate = candidate_path(args, name)
    if candidate.exists() and not args.rebuild:
        return candidate
    cmd = [
        sys.executable,
        str(ROOT / "scripts/build_liteon_helper_codeexec_candidate.py"),
        "--name",
        name,
        "--out-root",
        str(args.candidate_root),
        "controller-byte-bit-delay",
        "--addr",
        f"0x{addr:06x}",
        "--bit",
        str(bit),
        "--payload-offset",
        f"0x{args.payload_offset:04x}",
        "--delay-count",
        f"0x{args.delay_count:02x}",
    ]
    if args.controller_skip:
        cmd.extend(["--skip", f"0x{args.controller_skip:02x}"])
    if args.delay_on_zero:
        cmd.append("--delay-on-zero")
    run_command(cmd, check=True, quiet=args.quiet_builder)
    return candidate


def build_data_candidate(args: argparse.Namespace, addr: int, bit: int) -> Path:
    if args.space == "controller":
        return build_controller_candidate(args, addr, bit)
    return build_xdata_candidate(args, addr, bit)


def run_candidate_once(args: argparse.Namespace, candidate: Path, out_dir: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts/run_liteon_linux_persistence_experiment.py"),
        "--candidate",
        str(candidate),
        "--device",
        args.device,
        "--skip-pre-f0",
        "--skip-post-f0",
        "--end-index",
        "68",
        "--recover-on-currentboot",
        "--out-dir",
        str(out_dir),
    ]
    proc = run_command(cmd, check=False, quiet=args.quiet_runner)
    result_path = latest_result(out_dir)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    try:
        event68 = event_by_index(result, 68)
    except KeyError:
        event68 = {}
    recovery = result.get("auto_recovery") or {}
    identity_after_recovery = result.get("identity_after_auto_recovery") or {}
    return {
        "candidate": str(candidate),
        "runner_returncode": proc.returncode,
        "result": str(result_path),
        "event68_returncode": event68.get("returncode"),
        "event68_elapsed_seconds": event68.get("elapsed_seconds"),
        "event68_stderr": event68.get("stderr"),
        "final_revision_after_sequence": result.get("final_revision_after_sequence"),
        "auto_recovery_returncode": recovery.get("returncode"),
        "revision_after_auto_recovery": (identity_after_recovery.get("standard") or {}).get("revision"),
        "error": result.get("error"),
        "stopped_on_failure": result.get("stopped_on_failure"),
    }


def is_retryable_unit_attention(item: dict[str, Any]) -> bool:
    stopped = item.get("stopped_on_failure") or {}
    text = f"{stopped.get('stderr') or ''}\n{item.get('error') or ''}".lower()
    return "unit attention" in text or "power on, reset, or bus device reset occurred" in text


def run_candidate(args: argparse.Namespace, candidate: Path, out_dir: Path) -> dict[str, Any]:
    attempts = []
    for attempt in range(1, args.retry_attempts + 1):
        item = run_candidate_once(args, candidate, out_dir / f"attempt{attempt}")
        attempts.append(item)
        if item.get("event68_elapsed_seconds") is not None:
            break
        if attempt < args.retry_attempts and is_retryable_unit_attention(item):
            time.sleep(args.between_delay)
            continue
        break
    final = dict(attempts[-1])
    final["attempts"] = attempts
    final["attempt_count"] = len(attempts)
    return final


def classify(elapsed: float, threshold: float, *, delay_on_zero: bool) -> int:
    delayed = elapsed >= threshold
    if delay_on_zero:
        return 0 if delayed else 1
    return 1 if delayed else 0


def calibrate(args: argparse.Namespace, run_root: Path) -> dict[str, Any]:
    zero = build_immediate_candidate(args, "timing-cal-imm00-bit0", 0x00, 0)
    one = build_immediate_candidate(args, "timing-cal-imm01-bit0", 0x01, 0)
    zero_result = run_candidate(args, zero, run_root / "cal-imm00-bit0")
    time.sleep(args.between_delay)
    one_result = run_candidate(args, one, run_root / "cal-imm01-bit0")
    zero_elapsed = float(zero_result["event68_elapsed_seconds"])
    one_elapsed = float(one_result["event68_elapsed_seconds"])
    short = min(zero_elapsed, one_elapsed)
    long = max(zero_elapsed, one_elapsed)
    return {
        "zero": zero_result,
        "one": one_result,
        "short_seconds": short,
        "long_seconds": long,
        "threshold_seconds": (short + long) / 2,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        f"# LiteOn {summary['space_label']} Timing-Channel Read",
        "",
        f"- captured at UTC: `{summary['captured_at_utc']}`",
        f"- device: `{summary['device']}`",
        f"- space: `{summary['space']}`",
        f"- address: `{summary['addr_text']}`",
        f"- controller FIFO skip: `{summary['controller_skip']:#04x}`",
        f"- delay count: `{summary['delay_count']:#04x}`",
        f"- payload offset: `{summary['payload_offset']:#06x}`",
        f"- threshold seconds: `{summary['threshold_seconds']:.6f}`",
        f"- value: `{summary['value_text']}`",
        "",
        "| bit | value | event68 seconds | recovery | result |",
        "|---:|---:|---:|---|---|",
    ]
    for item in summary["bits"]:
        rel = Path(item["result"])
        try:
            rel = rel.relative_to(ROOT)
        except ValueError:
            pass
        recovery = item.get("revision_after_auto_recovery") or item.get("auto_recovery_returncode")
        elapsed = item.get("event68_elapsed_seconds")
        elapsed_text = "?" if elapsed is None else f"{elapsed:.6f}"
        value = "?" if item.get("value") is None else str(item["value"])
        lines.append(
            f"| {item['bit']} | {value} | {elapsed_text} | "
            f"`{recovery}` | `{rel}` |"
        )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument(
        "--space",
        choices=("xdata", "controller"),
        default="xdata",
        help="read XDATA directly or read controller address space through 0x4091..0x4098",
    )
    parser.add_argument("--addr", type=parse_addr, required=True)
    parser.add_argument("--bits", type=parse_bits, default=parse_bits("0,1,2,3,4,5,6,7"))
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument(
        "--controller-skip",
        type=parse_skip,
        default=0,
        help="for --space controller, discard this many FIFO bytes after setting the gateway address",
    )
    parser.add_argument(
        "--payload-offset",
        type=parse_addr,
        default=0x04F6,
        help="helper plaintext offset for the payload; default uses a long comment string, not the shorter Flash Type Error slot",
    )
    parser.add_argument("--delay-count", type=parse_byte, default=0x20)
    parser.add_argument("--delay-on-zero", action="store_true")
    parser.add_argument("--threshold-seconds", type=float)
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--retry-attempts", type=int, default=2)
    parser.add_argument("--between-delay", type=float, default=1.0)
    parser.add_argument("--quiet-builder", action="store_true")
    parser.add_argument("--quiet-runner", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.space == "xdata" and args.addr > 0xFFFF:
        raise SystemExit("XDATA address must be <= 0xffff")
    if args.space != "controller" and args.controller_skip:
        raise SystemExit("--controller-skip only applies to --space controller")
    if args.out_dir is None:
        args.out_dir = DEFAULT_CONTROLLER_OUT_DIR if args.space == "controller" else DEFAULT_OUT_DIR
    addr_width = 6 if args.space == "controller" else 4
    run_id = datetime.now(timezone.utc).strftime(
        f"{args.space}-timing-{args.addr:0{addr_width}x}-%Y%m%dT%H%M%SZ"
    )
    run_root = args.out_dir / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    calibration = calibrate(args, run_root) if args.calibrate else None
    if args.threshold_seconds is not None:
        threshold = args.threshold_seconds
    elif calibration is not None:
        threshold = float(calibration["threshold_seconds"])
    else:
        # Known local baseline: event 68 around 0.26s, delay-count 0x20 around 0.85s.
        threshold = 0.55

    bit_results = []
    value = 0
    complete = True
    for bit in args.bits:
        candidate = build_data_candidate(args, args.addr, bit)
        item = run_candidate(args, candidate, run_root / f"bit{bit}")
        elapsed = item.get("event68_elapsed_seconds")
        if item.get("event68_returncode") != 0 or elapsed is None:
            item["value"] = None
            complete = False
        else:
            item["value"] = classify(float(elapsed), threshold, delay_on_zero=args.delay_on_zero)
            value |= int(item["value"]) << bit
        item["bit"] = bit
        bit_results.append(item)
        time.sleep(args.between_delay)

    summary: dict[str, Any] = {
        "status": f"{args.space}_timing_channel_read",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "space": args.space,
        "space_label": "Controller-Gateway" if args.space == "controller" else "XDATA",
        "addr": args.addr,
        "addr_hex": f"0x{args.addr:0{addr_width}x}",
        "addr_text": f"0x{args.addr:0{addr_width}x}",
        "controller_skip": args.controller_skip,
        "bits_requested": args.bits,
        "delay_count": args.delay_count,
        "payload_offset": args.payload_offset,
        "delay_on_zero": args.delay_on_zero,
        "threshold_seconds": threshold,
        "calibration": calibration,
        "bits": bit_results,
        "value": value if complete else None,
        "value_text": f"0x{value:02x}" if complete else "unknown",
    }
    json_path = run_root / f"{args.space}-timing-channel-summary.json"
    md_path = run_root / f"{args.space}-timing-channel-summary.md"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"value={summary['value_text']}")
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
