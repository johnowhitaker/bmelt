#!/usr/bin/env python3
"""Read XDATA or direct/SFR bytes through the helper success/error bit channel.

This runs on the Linux host with the drive attached.  For each requested bit it:

1. builds a currentboot profile-tail helper candidate whose payload reads one
   XDATA bit with MOVX, or an 8051 direct/SFR bit with MOV direct;
2. replays only through event 68;
3. interprets event-68 GOOD as bit=1 and the known DID_ERROR helper error-exit
   as bit=0;
4. auto-recovers the drive back to LD5M before the next bit.

It is intentionally slow and simple.  The point is to turn the first
host-visible helper code-execution primitive into a repeatable internal-state
read tool without requiring front-panel wiring.
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
DEFAULT_OUT_DIR = ROOT / "runs/helper-xdata-bit-channel"


def parse_addr(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFFFF:
        raise argparse.ArgumentTypeError("address must be 0..0xffff")
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


def run_command(
    cmd: list[str],
    *,
    check: bool = False,
    quiet: bool = False,
) -> subprocess.CompletedProcess[str]:
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


def interpret_bit(event68: dict[str, Any]) -> int | None:
    rc = int(event68.get("returncode", -1))
    stderr = str(event68.get("stderr") or "")
    if rc == 0:
        return 1
    if rc == 99 and "DID_ERROR" in stderr:
        return 0
    return None


def build_candidate(args: argparse.Namespace, addr: int, bit: int) -> Path:
    if args.source == "direct" and addr > 0xFF:
        raise ValueError("direct/SFR source addresses must be 0..0xff")
    name_addr = f"{addr:02x}" if args.source == "direct" else f"{addr:04x}"
    name = f"{args.source}-{name_addr}-bit{bit}"
    candidate = (
        args.candidate_root
        / name
        / f"liteon-full-currentboot-ld5m-helper-codeexec-{name}-candidate.json"
    )
    if candidate.exists() and not args.rebuild:
        return candidate
    cmd = [
        sys.executable,
        str(ROOT / "scripts/build_liteon_helper_codeexec_candidate.py"),
        "--name",
        name,
        "--out-root",
        str(args.candidate_root),
        "direct-bit" if args.source == "direct" else "movx-bit",
        "--addr",
        f"0x{name_addr}",
        "--bit",
        str(bit),
    ]
    run_command(cmd, check=True)
    return candidate


def run_bit_once(
    args: argparse.Namespace,
    addr: int,
    bit: int,
    candidate: Path,
    attempt_out_dir: Path,
) -> dict[str, Any]:
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
        str(attempt_out_dir),
    ]
    proc = run_command(cmd, check=False, quiet=args.quiet_runner)
    result_path = latest_result(attempt_out_dir)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    try:
        event68 = event_by_index(result, 68)
    except KeyError:
        event68 = None
    value = interpret_bit(event68) if event68 is not None else None
    failed_event = result.get("stopped_on_failure")
    return {
        "addr": addr,
        "bit": bit,
        "candidate": str(candidate),
        "result": str(result_path),
        "runner_returncode": proc.returncode,
        "event68_present": event68 is not None,
        "event68_returncode": None if event68 is None else event68.get("returncode"),
        "event68_elapsed_seconds": None if event68 is None else event68.get("elapsed_seconds"),
        "event68_stderr": None if event68 is None else event68.get("stderr"),
        "failed_event_index": None if not failed_event else failed_event.get("event_index"),
        "failed_event_returncode": None if not failed_event else failed_event.get("returncode"),
        "failed_event_stderr": None if not failed_event else failed_event.get("stderr"),
        "value": value,
        "final_revision_after_sequence": result.get("final_revision_after_sequence"),
        "auto_recovery_returncode": (result.get("auto_recovery") or {}).get("returncode"),
        "revision_after_auto_recovery": (
            (result.get("identity_after_auto_recovery") or {}).get("standard") or {}
        ).get("revision"),
    }


def run_bit(args: argparse.Namespace, addr: int, bit: int, candidate: Path, run_root: Path) -> dict[str, Any]:
    attempts = []
    for attempt in range(1, args.retry_attempts + 1):
        attempt_out_dir = run_root / f"bit{bit}" / f"attempt{attempt}"
        item = run_bit_once(args, addr, bit, candidate, attempt_out_dir)
        attempts.append(item)
        if item["value"] is not None:
            break
        if attempt != args.retry_attempts:
            print(
                f"bit {bit}: no interpretable event-68 channel result; "
                f"sleeping {args.between_delay:.1f}s before retry",
                flush=True,
            )
            time.sleep(args.between_delay)
    final = dict(attempts[-1])
    final["attempts"] = attempts
    final["attempt_count"] = len(attempts)
    return final


def render_markdown(summary: dict[str, Any]) -> str:
    known = [item for item in summary["bits"] if item["value"] is not None]
    lines = [
        "# LiteOn XDATA Bit-Channel Read",
        "",
        f"- captured at UTC: `{summary['captured_at_utc']}`",
        f"- device: `{summary['device']}`",
        f"- source: `{summary['source']}`",
        f"- address: `{summary['addr']:#06x}`",
        f"- value: `{summary['value_text']}`",
        "",
        "| bit | value | event68 rc | recovery | result |",
        "|---:|---:|---:|---|---|",
    ]
    for item in summary["bits"]:
        rel = Path(item["result"])
        try:
            rel = rel.relative_to(ROOT)
        except ValueError:
            pass
        value = "?" if item["value"] is None else str(item["value"])
        recovery = item.get("revision_after_auto_recovery") or item.get("auto_recovery_returncode")
        lines.append(
            f"| {item['bit']} | {value} | {item['event68_returncode']} | `{recovery}` | `{rel}` |"
        )
    if len(known) != len(summary["bits"]):
        lines.extend(["", "Some bits could not be interpreted as the known GOOD/DID_ERROR channel."])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--source", choices=("xdata", "direct"), default="xdata")
    parser.add_argument("--addr", type=parse_addr, required=True)
    parser.add_argument("--bits", type=parse_bits, default=parse_bits("0,1,2,3,4,5,6,7"))
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--retry-attempts", type=int, default=2)
    parser.add_argument("--between-delay", type=float, default=3.0)
    parser.add_argument(
        "--quiet-runner",
        action="store_true",
        help="suppress verbose per-event runner output; raw logs are still written under --out-dir",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = datetime.now(timezone.utc).strftime(
        f"{args.source}-{args.addr:04x}-%Y%m%dT%H%M%SZ"
    )
    run_root = args.out_dir / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    bits: list[dict[str, Any]] = []
    for index, bit in enumerate(args.bits):
        candidate = build_candidate(args, args.addr, bit)
        item = run_bit(args, args.addr, bit, candidate, run_root)
        bits.append(item)
        print(
            f"bit {bit}: value={item['value']} event68_rc={item['event68_returncode']} "
            f"attempts={item['attempt_count']}",
            flush=True,
        )
        if index != len(args.bits) - 1 and args.between_delay:
            print(f"sleeping {args.between_delay:.1f}s before next bit", flush=True)
            time.sleep(args.between_delay)

    value: int | None = 0
    for item in bits:
        if item["value"] is None:
            value = None
            break
        value |= int(item["value"]) << int(item["bit"])
    summary = {
        "status": "xdata_bit_channel_read",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "source": args.source,
        "addr": args.addr,
        "bits": bits,
        "value": value,
        "value_text": "unknown" if value is None else f"0x{value:02x}",
    }
    json_path = run_root / "xdata-bit-channel-summary.json"
    md_path = run_root / "xdata-bit-channel-summary.md"
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"value={summary['value_text']}")
    return 0 if value is not None else 3


if __name__ == "__main__":
    raise SystemExit(main())
