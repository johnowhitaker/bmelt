#!/usr/bin/env python3
"""Locate a button-sensitive XDATA bit with parity/syndrome helper probes.

This is a Mac-side orchestrator.  The optical drive is attached to the Linux
host and the Pico is attached to the Mac.  For each generated helper predicate
candidate, it runs event 68 twice:

1. with the Pico button line released/high-Z;
2. with the Pico pulling the button line low.

The helper predicate reports one bit through the known GOOD/DID_ERROR channel.
If exactly one candidate bit in the scanned XDATA range changes between the two
button states, the XOR of the predicate outputs reconstructs that bit's index.

Safety: GP27 is the real eject button line on the current front-panel wiring.
The script refuses to pull it low unless --allow-button-low is passed.  The
default low scope is event68 only; full-sequence low can move the sled before
the helper is reached.
"""

from __future__ import annotations

import argparse
import json
import math
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import serial
from serial.tools import list_ports


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE_ROOT = "/home/jonathan/boastermelt"
DEFAULT_HOST = "root@jonathan-thinkpad-t480s"
DEFAULT_BAUD = 921600
DEFAULT_CANDIDATE_ROOT = ROOT / "references/firmware/extracted/helper-codeexec-candidates"


def parse_u16(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFFFF:
        raise argparse.ArgumentTypeError("address must be 0..0xffff")
    return parsed


def parse_length(value: str) -> int:
    parsed = int(value, 0)
    if not 1 <= parsed <= 0x100:
        raise argparse.ArgumentTypeError("length must be 1..0x100")
    return parsed


def find_port() -> str:
    candidates = []
    for port in list_ports.comports():
        text = " ".join(
            str(value)
            for value in (port.device, port.description, port.hwid, port.manufacturer, port.product)
            if value
        )
        if "2E8A" in text.upper() or "MICROPYTHON" in text.upper() or "PICO" in text.upper():
            candidates.append(port.device)
    if candidates:
        return sorted(candidates)[0]
    for port in list_ports.comports():
        if port.device.startswith("/dev/cu.usbmodem"):
            return port.device
    raise SystemExit("No Pico serial port found. Pass --pico-port /dev/cu.usbmodemXXXX.")


def read_json_line(ser: serial.Serial, timeout: float) -> dict[str, Any] | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = ser.readline()
        if not line:
            continue
        text = line.decode("utf-8", "replace").strip()
        if not text:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    return None


def send_pico(ser: serial.Serial, command: str, timeout: float = 2.0) -> dict[str, Any] | None:
    ser.write((command.strip() + "\n").encode("ascii"))
    ser.flush()
    return read_json_line(ser, timeout)


def run_local(cmd: list[str], *, quiet: bool = False) -> subprocess.CompletedProcess[str]:
    if not quiet:
        print("+ " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.stdout and not quiet:
        print(proc.stdout, end="")
    if proc.stderr and not quiet:
        print(proc.stderr, end="", file=sys.stderr)
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, cmd, proc.stdout, proc.stderr)
    return proc


def run_remote(args: argparse.Namespace, remote_command: str, timeout: float) -> subprocess.CompletedProcess[str]:
    cmd = ["ssh", args.host, f"cd {shlex.quote(args.remote_root)} && {remote_command}"]
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)


def candidate_remote_path(args: argparse.Namespace, candidate: Path) -> str:
    if candidate.is_absolute():
        try:
            return str(Path(args.remote_root) / candidate.relative_to(ROOT))
        except ValueError:
            return str(candidate)
    return str(Path(args.remote_root) / candidate)


def predicate_name(args: argparse.Namespace, predicate: int | None) -> str:
    suffix = "total" if predicate is None else f"idxbit{predicate}"
    return f"button-xdata-{args.addr:04x}-len{args.length:03x}-{suffix}"


def build_candidate(args: argparse.Namespace, predicate: int | None) -> Path:
    name = predicate_name(args, predicate)
    candidate = (
        args.candidate_root
        / name
        / f"liteon-full-currentboot-ld5m-helper-codeexec-{name}-candidate.json"
    )
    if candidate.exists() and not args.rebuild:
        return candidate
    syndrome = "total" if predicate is None else str(predicate)
    run_local(
        [
            sys.executable,
            str(ROOT / "scripts/build_liteon_helper_codeexec_candidate.py"),
            "--name",
            name,
            "--out-root",
            str(args.candidate_root),
            "xdata-parity-range",
            "--addr",
            f"0x{args.addr:04x}",
            "--length",
            f"0x{args.length:x}",
            "--syndrome-bit",
            syndrome,
            "--payload-offset",
            f"0x{args.payload_offset:x}",
        ],
        quiet=args.quiet_build,
    )
    return candidate


def sync_remote(args: argparse.Namespace) -> None:
    excludes = [".git", "old", "logs", "runs", "work", ".tmp"]
    cmd = ["rsync", "-a", "--delete"]
    for item in excludes:
        cmd.extend(["--exclude", item])
    cmd.extend(["./", f"{args.host}:{args.remote_root}/"])
    run_local(cmd, quiet=False)


def parse_remote_json(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return {"status": "no_json_summary", "stdout_tail": stdout[-2000:]}


def interpret_event(summary: dict[str, Any]) -> int | None:
    rc = summary.get("target_event_returncode")
    stderr = str(summary.get("target_event_stderr") or "")
    if rc == 0:
        return 1
    if rc == 99 and "DID_ERROR" in stderr:
        return 0
    return None


def run_event_range(
    args: argparse.Namespace,
    candidate: Path,
    remote_out: str,
    *,
    start_index: int,
    end_index: int,
    force: bool = False,
) -> dict[str, Any]:
    remote_candidate = candidate_remote_path(args, candidate)
    remote_out_q = shlex.quote(remote_out)
    runner_parts = [
        "python3 scripts/run_liteon_linux_persistence_experiment.py",
        "--candidate",
        shlex.quote(remote_candidate),
        "--device",
        shlex.quote(args.device),
        "--skip-pre-f0",
        "--skip-post-f0",
        "--start-index",
        str(start_index),
        "--end-index",
        str(end_index),
        "--out-dir",
        remote_out_q,
    ]
    if force:
        runner_parts.append("--force")
    cmd = " ".join(
        [
            "set +e;",
            *runner_parts,
            ">/tmp/liteon_button_predicate_runner.out 2>/tmp/liteon_button_predicate_runner.err;",
            "runner_rc=$?;",
            "python3 -",
            remote_out_q,
            "$runner_rc",
            str(end_index),
            "<<'PY'\n"
            "import json, pathlib, sys\n"
            "root = pathlib.Path(sys.argv[1])\n"
            "runner_rc = int(sys.argv[2])\n"
            "target_index = int(sys.argv[3])\n"
            "out = {'runner_returncode': runner_rc, 'result': None}\n"
            "paths = sorted(root.glob('liteon-persistence-*/persistence-experiment-result.json'))\n"
            "if paths:\n"
            "    result = json.loads(paths[-1].read_text())\n"
            "    target = next((e for e in result.get('events_attempted', []) if int(e.get('event_index', -1)) == target_index), None)\n"
            "    out.update({\n"
            "        'result': str(paths[-1]),\n"
            "        'start_index': result.get('start_index'),\n"
            "        'end_index': result.get('end_index'),\n"
            "        'final_revision_after_sequence': result.get('final_revision_after_sequence'),\n"
            "        'stopped_on_failure': result.get('stopped_on_failure'),\n"
            "        'target_event_index': target_index,\n"
            "        'target_event_present': target is not None,\n"
            "        'target_event_returncode': None if target is None else target.get('returncode'),\n"
            "        'target_event_elapsed_seconds': None if target is None else target.get('elapsed_seconds'),\n"
            "        'target_event_stderr': None if target is None else target.get('stderr'),\n"
            "    })\n"
            "print(json.dumps(out, sort_keys=True))\n"
            "PY\n"
            "exit 0",
        ]
    )
    proc = run_remote(args, cmd, args.timeout)
    summary = parse_remote_json(proc.stdout)
    summary.update(
        {
            "ssh_returncode": proc.returncode,
            "ssh_stderr": proc.stderr,
            "remote_out": remote_out,
            "start_index": start_index,
            "end_index": end_index,
            "force": force,
        }
    )
    summary["value"] = interpret_event(summary)
    return summary


def run_event68(args: argparse.Namespace, candidate: Path, remote_out: str, *, force: bool = False) -> dict[str, Any]:
    return run_event_range(args, candidate, remote_out, start_index=68, end_index=68, force=force)


def recover(args: argparse.Namespace, remote_out: str) -> dict[str, Any]:
    cmd = " ".join(
        [
            "python3 scripts/recover_liteon_currentboot_linux.py",
            "--device",
            shlex.quote(args.device),
            "--out-dir",
            shlex.quote(remote_out),
        ]
    )
    proc = run_remote(args, cmd, args.timeout)
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "remote_out": remote_out,
    }


def run_state(
    args: argparse.Namespace,
    ser: serial.Serial,
    *,
    candidate: Path,
    predicate_label: str,
    state: str,
    run_id: str,
) -> dict[str, Any]:
    remote_base = f"runs/button-syndrome/{run_id}/{predicate_label}/{state}"
    if state == "low" and not args.allow_button_low:
        raise RuntimeError("refusing to pull button line low without --allow-button-low")
    before = send_pico(ser, f"SET {args.button_pin} Z")
    read_before = send_pico(ser, f"READ {args.button_pin}")
    setup = None
    if args.low_scope == "event68":
        setup = run_event_range(
            args,
            candidate,
            f"{remote_base}/setup",
            start_index=0,
            end_index=67,
            force=False,
        )
        if state == "low":
            before = send_pico(ser, f"SET {args.button_pin} LOW")
            read_before = send_pico(ser, f"READ {args.button_pin}")
    try:
        if args.low_scope == "full-sequence":
            if state == "low":
                before = send_pico(ser, f"SET {args.button_pin} LOW")
                read_before = send_pico(ser, f"READ {args.button_pin}")
            event = run_event_range(
                args,
                candidate,
                f"{remote_base}/event68",
                start_index=0,
                end_index=68,
                force=False,
            )
        else:
            event = run_event68(args, candidate, f"{remote_base}/event68", force=True)
    finally:
        released = send_pico(ser, f"SET {args.button_pin} Z")
    read_after = send_pico(ser, f"READ {args.button_pin}")
    recovery = recover(args, f"{remote_base}/recovery")
    if args.between_delay:
        time.sleep(args.between_delay)
    return {
        "state": state,
        "pico_set": before,
        "pico_read_before_event": read_before,
        "pico_release": released,
        "pico_read_after_release": read_after,
        "setup": setup,
        "event68": event,
        "recovery": recovery,
        "value": event.get("value"),
    }


def run_predicate(
    args: argparse.Namespace,
    ser: serial.Serial,
    *,
    predicate: int | None,
    candidate: Path,
    run_id: str,
) -> dict[str, Any]:
    label = "total" if predicate is None else f"idxbit{predicate}"
    states = {}
    for state in ("z", "low"):
        print(f"predicate {label}: state={state}", flush=True)
        states[state] = run_state(
            args,
            ser,
            candidate=candidate,
            predicate_label=label,
            state=state,
            run_id=run_id,
        )
    z_value = states["z"].get("value")
    low_value = states["low"].get("value")
    delta = None if z_value is None or low_value is None else int(z_value) ^ int(low_value)
    return {
        "predicate": predicate,
        "label": label,
        "candidate": str(candidate),
        "states": states,
        "z_value": z_value,
        "low_value": low_value,
        "delta": delta,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Pico Button Syndrome Scan",
        "",
        f"- captured at UTC: `{report['captured_at_utc']}`",
        f"- device: `{report['device']}`",
        f"- range: `0x{report['addr']:04x}..0x{report['addr'] + report['length'] - 1:04x}`",
        f"- candidate bits: `{report['candidate_bit_count']}`",
        f"- total parity changed: `{report.get('total_delta')}`",
        f"- decoded candidate: `{report.get('decoded_candidate_text')}`",
        "",
        "| predicate | released | low | delta |",
        "|---|---:|---:|---:|",
    ]
    for item in report["predicates"]:
        delta = "?" if item["delta"] is None else str(item["delta"])
        z_value = "?" if item["z_value"] is None else str(item["z_value"])
        low_value = "?" if item["low_value"] is None else str(item["low_value"])
        lines.append(f"| `{item['label']}` | {z_value} | {low_value} | {delta} |")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--addr", type=parse_u16, required=True)
    parser.add_argument("--length", type=parse_length, default=0x100)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    parser.add_argument("--candidate-root", type=Path, default=DEFAULT_CANDIDATE_ROOT)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs/button-syndrome")
    parser.add_argument("--pico-port", default=None)
    parser.add_argument("--button-pin", default="GP27")
    parser.add_argument("--payload-offset", type=parse_u16, default=0x0600)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--between-delay", type=float, default=0.5)
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--quiet-build", action="store_true")
    parser.add_argument("--sync-remote", action="store_true")
    parser.add_argument(
        "--allow-button-low",
        action="store_true",
        help="actually pull the Pico button line low; without this the scanner refuses low-state runs",
    )
    parser.add_argument(
        "--low-scope",
        choices=("event68", "full-sequence"),
        default="event68",
        help="hold the button low only for event 68, or for the full sequence; full-sequence can eject the sled",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.allow_button_low:
        raise SystemExit(
            "Refusing to pull the button line low without --allow-button-low. "
            "Use --low-scope event68 to limit the low pulse to the helper event."
        )
    run_id = datetime.now(timezone.utc).strftime(f"xdata-{args.addr:04x}-len{args.length:03x}-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    candidate_bit_count = args.length * 8
    syndrome_bits = math.ceil(math.log2(candidate_bit_count))
    predicates = [None] + list(range(syndrome_bits))
    candidates = {predicate: build_candidate(args, predicate) for predicate in predicates}
    if args.sync_remote:
        sync_remote(args)
    results = []
    pico_port = args.pico_port or find_port()
    with serial.Serial(pico_port, DEFAULT_BAUD, timeout=0.05, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()
        send_pico(ser, "ALLZ")
        try:
            for predicate in predicates:
                result = run_predicate(
                    args,
                    ser,
                    predicate=predicate,
                    candidate=candidates[predicate],
                    run_id=run_id,
                )
                results.append(result)
                print(
                    f"{result['label']}: released={result['z_value']} low={result['low_value']} "
                    f"delta={result['delta']}",
                    flush=True,
                )
        finally:
            send_pico(ser, "ALLZ")

    total_delta = results[0]["delta"]
    decoded_index: int | None = None
    decoded_candidate: dict[str, Any] | None = None
    decoded_candidate_text = "unknown"
    if total_delta == 1 and all(item["delta"] is not None for item in results[1:]):
        decoded_index = 0
        for bit, item in enumerate(results[1:]):
            decoded_index |= int(item["delta"]) << bit
        if decoded_index < candidate_bit_count:
            decoded_candidate = {
                "index": decoded_index,
                "addr": args.addr + decoded_index // 8,
                "bit": decoded_index % 8,
            }
            decoded_candidate_text = f"0x{decoded_candidate['addr']:04x}.bit{decoded_candidate['bit']}"
        else:
            decoded_candidate_text = f"out-of-range index {decoded_index}"
    elif total_delta == 0:
        decoded_candidate_text = "no odd number of bit changes detected"

    report = {
        "status": "pico_button_syndrome_scan",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "device": args.device,
        "host": args.host,
        "remote_root": args.remote_root,
        "pico_port": pico_port,
        "button_pin": args.button_pin,
        "addr": args.addr,
        "length": args.length,
        "candidate_bit_count": candidate_bit_count,
        "syndrome_bits": syndrome_bits,
        "predicates": results,
        "total_delta": total_delta,
        "decoded_index": decoded_index,
        "decoded_candidate": decoded_candidate,
        "decoded_candidate_text": decoded_candidate_text,
    }
    json_path = out_dir / "button-syndrome-summary.json"
    md_path = out_dir / "button-syndrome-summary.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    print(f"decoded_candidate={decoded_candidate_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
