#!/usr/bin/env python3
"""Power-cycle the bench drive with the Pico servo, then wait for Linux sg status."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PICO_PORT = "/dev/cu.usbmodem2101"
DEFAULT_HOST = "root@jonathan-thinkpad-t480s"
DEFAULT_REMOTE_DIR = "/home/jonathan/boastermelt"

OPTICAL_RE = re.compile(r"^(?P<dev>/dev/sg\d+): .* rev='(?P<rev>[^']+)'.*<-- optical target")


def run(cmd: list[str], *, cwd: Path | None = None, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def pico_toggle(port: str, timeout: float, hold_ms: int) -> dict[str, object]:
    cmd = [sys.executable, "pico/client.py", "--port", port, "TOGGLE SERVO", str(hold_ms)]
    result = run(cmd, cwd=ROOT, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"Pico servo command failed rc={result.returncode}: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    raise RuntimeError(f"Pico servo command did not return JSON: {result.stdout!r}")


def read_status(host: str, remote_dir: str, timeout: float) -> tuple[str, str | None, str | None]:
    remote = f"cd {remote_dir} && python3 scripts/liteon_linux_status.py"
    result = run(["ssh", host, remote], timeout=timeout)
    text = (result.stdout or "") + (result.stderr or "")
    dev = rev = None
    for line in text.splitlines():
        match = OPTICAL_RE.match(line)
        if match:
            dev = match.group("dev")
            rev = match.group("rev")
            break
    return text, dev, rev


def wait_for_optical(args: argparse.Namespace) -> tuple[str, str, str]:
    deadline = time.monotonic() + args.wait_timeout
    last_text = ""
    while time.monotonic() < deadline:
        text, dev, rev = read_status(args.host, args.remote_dir, args.ssh_timeout)
        last_text = text
        if dev and rev and (args.expect_rev is None or rev == args.expect_rev):
            return text, dev, rev
        time.sleep(args.interval)
    expected = f" rev {args.expect_rev}" if args.expect_rev else ""
    raise TimeoutError(f"Timed out waiting for optical LUN{expected}. Last status:\n{last_text}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pico-port", default=DEFAULT_PICO_PORT)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--remote-dir", default=DEFAULT_REMOTE_DIR)
    parser.add_argument("--expect-rev", default="LD5M", help="expected optical revision, or empty to accept any")
    parser.add_argument("--wait-timeout", type=float, default=30.0)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--pico-timeout", type=float, default=5.0)
    parser.add_argument("--hold-ms", type=int, default=1000, help="servo switch hold time in milliseconds")
    parser.add_argument("--ssh-timeout", type=float, default=8.0)
    parser.add_argument("--status-only", action="store_true", help="do not toggle the servo; only report status")
    args = parser.parse_args()
    if args.expect_rev == "":
        args.expect_rev = None

    if not args.status_only:
        pico_timeout = max(args.pico_timeout, args.hold_ms / 1000 + 3)
        response = pico_toggle(args.pico_port, pico_timeout, args.hold_ms)
        print(json.dumps({"servo": response}, sort_keys=True))

    status, dev, rev = wait_for_optical(args)
    print(status.rstrip())
    print(json.dumps({"optical_device": dev, "revision": rev}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
