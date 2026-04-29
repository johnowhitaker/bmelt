#!/usr/bin/env python3
"""Run one helper payload while sampling the Pico front-panel LED line.

This is a Mac-side orchestrator.  The optical drive is attached to the Linux
host, while the Pico is attached to the Mac.  The script starts a high-Z Pico
sampler on GP26, runs a short helper event-68 candidate on the Linux host, then
recovers the drive back to LD5M.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
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


def sample_pico(
    ser: serial.Serial,
    stop: threading.Event,
    samples: list[dict[str, Any]],
    *,
    started: float,
    interval: float,
    pin: str,
) -> None:
    while not stop.is_set():
        item = send_pico(ser, f"READ {pin}", timeout=0.5)
        now = time.monotonic()
        if item:
            pin_item = item.get("pin") or {}
            samples.append(
                {
                    "t": now - started,
                    "pin": pin_item.get("pin"),
                    "mode": pin_item.get("mode"),
                    "digital": pin_item.get("digital"),
                    "millivolts": pin_item.get("millivolts"),
                    "adc_u16": pin_item.get("adc_u16"),
                }
            )
        time.sleep(interval)


def run_remote(args: argparse.Namespace, remote_command: str, timeout: float) -> dict[str, Any]:
    cmd = ["ssh", args.host, f"cd {args.remote_root} && {remote_command}"]
    print("+ " + " ".join(cmd), flush=True)
    started = time.monotonic()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "elapsed_seconds": time.monotonic() - started,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    values = [int(item["millivolts"]) for item in samples if item.get("millivolts") is not None]
    digitals = [int(item["digital"]) for item in samples if item.get("digital") is not None]
    return {
        "count": len(samples),
        "millivolts_min": min(values) if values else None,
        "millivolts_max": max(values) if values else None,
        "millivolts_avg": (sum(values) / len(values)) if values else None,
        "digital_high_count": sum(1 for value in digitals if value == 1),
        "digital_low_count": sum(1 for value in digitals if value == 0),
    }


def summarize_phases(samples: list[dict[str, Any]], markers: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {item["name"]: item["t"] for item in markers}
    phases = {
        "pre": (0.0, by_name.get("event68_start")),
        "event68": (by_name.get("event68_start"), by_name.get("event68_end")),
        "post_event68": (by_name.get("event68_end"), by_name.get("recovery_start")),
        "recovery": (by_name.get("recovery_start"), by_name.get("recovery_end")),
    }
    out: dict[str, Any] = {}
    for name, (start, end) in phases.items():
        if start is None or end is None:
            continue
        out[name] = summarize([item for item in samples if start <= item["t"] <= end])
    return out


def candidate_remote_path(args: argparse.Namespace) -> str:
    candidate = Path(args.candidate)
    if candidate.is_absolute():
        try:
            return str(Path(args.remote_root) / candidate.relative_to(ROOT))
        except ValueError:
            return str(candidate)
    return str(Path(args.remote_root) / candidate)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, help="Candidate JSON path, local repo-relative or absolute.")
    parser.add_argument("--device", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    parser.add_argument("--pico-port", default=None)
    parser.add_argument("--pin", default="GP26")
    parser.add_argument("--interval", type=float, default=0.02)
    parser.add_argument("--pre-sample", type=float, default=0.5)
    parser.add_argument("--post-sample", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs/pico-led-probes")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_id = datetime.now(timezone.utc).strftime(f"{args.label}-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    samples: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    started = time.monotonic()
    stop = threading.Event()
    pico_port = args.pico_port or find_port()
    remote_candidate = candidate_remote_path(args)
    remote_out = f"runs/pico-led-probes/{run_id}/event68"
    remote_recovery_out = f"runs/pico-led-probes/{run_id}/recovery"

    with serial.Serial(pico_port, DEFAULT_BAUD, timeout=0.05, write_timeout=1.0) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()
        send_pico(ser, "ALLZ")
        thread = threading.Thread(
            target=sample_pico,
            args=(ser, stop, samples),
            kwargs={"started": started, "interval": args.interval, "pin": args.pin},
            daemon=True,
        )
        thread.start()
        try:
            time.sleep(args.pre_sample)
            markers.append({"name": "event68_start", "t": time.monotonic() - started})
            event68 = run_remote(
                args,
                " ".join(
                    [
                        "python3 scripts/run_liteon_linux_persistence_experiment.py",
                        "--candidate",
                        remote_candidate,
                        "--device",
                        args.device,
                        "--skip-pre-f0",
                        "--skip-post-f0",
                        "--end-index",
                        "68",
                        "--out-dir",
                        remote_out,
                    ]
                ),
                args.timeout,
            )
            markers.append({"name": "event68_end", "t": time.monotonic() - started})
            time.sleep(args.post_sample)
            markers.append({"name": "recovery_start", "t": time.monotonic() - started})
            recovery = run_remote(
                args,
                " ".join(
                    [
                        "python3 scripts/recover_liteon_currentboot_linux.py",
                        "--device",
                        args.device,
                        "--out-dir",
                        remote_recovery_out,
                    ]
                ),
                args.timeout,
            )
            markers.append({"name": "recovery_end", "t": time.monotonic() - started})
        finally:
            stop.set()
            thread.join(timeout=2.0)
            send_pico(ser, "ALLZ")

    report = {
        "status": "pico_led_payload_probe",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": args.label,
        "candidate": args.candidate,
        "remote_candidate": remote_candidate,
        "device": args.device,
        "pico_port": pico_port,
        "pin": args.pin,
        "markers": markers,
        "summary": summarize(samples),
        "phase_summary": summarize_phases(samples, markers),
        "samples": samples,
        "event68": event68,
        "recovery": recovery,
    }
    json_path = out_dir / "pico-led-payload-probe.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {json_path}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if event68["returncode"] != 0:
        print(event68["stderr"], file=sys.stderr)
    if recovery["returncode"] != 0:
        print(recovery["stderr"], file=sys.stderr)
    return 0 if recovery["returncode"] == 0 else recovery["returncode"]


if __name__ == "__main__":
    raise SystemExit(main())
