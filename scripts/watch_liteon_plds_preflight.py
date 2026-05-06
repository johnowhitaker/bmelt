#!/usr/bin/env python3
"""Wait for a PLDS DS-8ABSH optical LUN and optionally run read-only preflight.

This is a convenience wrapper for the current bench state where the Initio
bridge may be present but only expose `Generic External`. It deliberately does
not run the bridge-clamp write candidate. With `--execute-preflight`, it invokes
`run_liteon_materialized_bridge_clamp_live_test.py --execute --preflight-only`,
which captures identity and READ BUFFER baseline windows only.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts/run_liteon_materialized_bridge_clamp_live_test.py"
LADDER = ROOT / "scripts/run_liteon_bridge_oracle_ladder.py"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd: list[str], timeout: float = 8.0) -> dict[str, Any]:
    proc = subprocess.run(
        cmd,
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


def sg_devices() -> list[str]:
    devices = sorted(path for path in glob.glob("/dev/sg*") if re.fullmatch(r"/dev/sg[0-9]+", path))
    if devices:
        return devices
    sg_map = shutil.which("sg_map")
    if not sg_map:
        return []
    result = run([sg_map, "-i"])
    found = []
    for line in result["stdout"].splitlines():
        first = line.split(maxsplit=1)[0] if line.strip() else ""
        if first.startswith("/dev/sg"):
            found.append(first)
    return sorted(set(found))


def inquiry(device: str) -> dict[str, Any]:
    sg_inq = shutil.which("sg_inq") or "sg_inq"
    result = run([sg_inq, device])
    text = result["stdout"] + "\n" + result["stderr"]
    result["plds_ds8absh"] = "PLDS" in text.upper() and "DS-8ABSH" in text.upper()
    return result


def scan() -> dict[str, Any]:
    rows = []
    for device in sg_devices():
        try:
            result = inquiry(device)
        except (OSError, subprocess.SubprocessError) as exc:
            result = {"cmd": ["sg_inq", device], "returncode": None, "stdout": "", "stderr": str(exc), "plds_ds8absh": False}
        rows.append({"device": device, "inquiry": result})
    plds = [row for row in rows if row["inquiry"].get("plds_ds8absh")]
    return {"timestamp_utc": now(), "devices": rows, "plds_devices": [row["device"] for row in plds]}


def send_discord(webhook: str | None, content: str) -> None:
    if not webhook:
        return
    data = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(webhook, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5):
            pass
    except OSError:
        pass


def run_preflight(device: str, pico_port: str, run_name: str, execute: bool) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(PREFLIGHT),
        "--device",
        device,
        "--pico-port",
        pico_port,
        "--run-name",
        run_name,
        "--preflight-only",
    ]
    if execute:
        cmd.append("--execute")
    return run(cmd, timeout=120.0)


def ladder_command(device: str, pico_port: str) -> list[str]:
    return [
        sys.executable,
        str(LADDER),
        "--device",
        device,
        "--pico-port",
        pico_port,
        "--execute",
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="scan once and exit")
    parser.add_argument("--interval-s", type=float, default=10.0)
    parser.add_argument("--max-wait-s", type=float, default=0.0, help="0 means no limit")
    parser.add_argument("--execute-preflight", action="store_true", help="run read-only preflight once PLDS is visible")
    parser.add_argument("--pico-port", default="/dev/ttyACM0")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--discord-webhook", default=os.environ.get("BOASTERMELT_DISCORD_WEBHOOK"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.monotonic()
    history = []
    while True:
        state = scan()
        history.append(state)
        print(json.dumps({"timestamp_utc": state["timestamp_utc"], "plds_devices": state["plds_devices"]}, sort_keys=True))
        if state["plds_devices"]:
            device = state["plds_devices"][0]
            state["next_ladder_command"] = ladder_command(device, args.pico_port)
            send_discord(args.discord_webhook, f"boastermelt: PLDS DS-8ABSH visible at {device}; running preflight={args.execute_preflight}")
            print(json.dumps({"next_ladder_command": state["next_ladder_command"]}, sort_keys=True))
            if args.execute_preflight:
                run_name = args.run_name or f"plds-preflight-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
                state["preflight"] = run_preflight(device, args.pico_port, run_name, execute=True)
                print(json.dumps({"preflight_returncode": state["preflight"]["returncode"], "run_name": run_name}, sort_keys=True))
            if args.json_out:
                args.json_out.parent.mkdir(parents=True, exist_ok=True)
                args.json_out.write_text(json.dumps({"history": history, "final": state}, indent=2, sort_keys=True) + "\n")
            return 0
        if args.once:
            if args.json_out:
                args.json_out.parent.mkdir(parents=True, exist_ok=True)
                args.json_out.write_text(json.dumps({"history": history, "final": state}, indent=2, sort_keys=True) + "\n")
            return 2
        if args.max_wait_s and time.monotonic() - started >= args.max_wait_s:
            if args.json_out:
                args.json_out.parent.mkdir(parents=True, exist_ok=True)
                args.json_out.write_text(json.dumps({"history": history, "final": state}, indent=2, sort_keys=True) + "\n")
            return 2
        time.sleep(args.interval_s)


if __name__ == "__main__":
    raise SystemExit(main())
