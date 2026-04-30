#!/usr/bin/env python3
"""Probe safe read-only normal-mode SCSI/MMC command surfaces.

This script is intended for an LD5M-normal LiteOn/PLDS DS-8ABSH drive.  It sends
only no-data-out commands: inquiry/status/read-style queries with allocation
lengths.  It deliberately avoids START STOP, LOAD/UNLOAD, WRITE BUFFER, SEND
DIAGNOSTIC, FORMAT, MODE SELECT, and other commands that can alter media or
mechanics state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SG_RAW = shutil.which("sg_raw") or "/usr/bin/sg_raw"


@dataclass(frozen=True)
class Probe:
    name: str
    cdb: tuple[int, ...]
    request_len: int = 0
    notes: str = ""
    group: str = "standard"


PROBES: tuple[Probe, ...] = (
    Probe("test-unit-ready", (0x00, 0x00, 0x00, 0x00, 0x00, 0x00), 0),
    Probe("request-sense", (0x03, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("inquiry-standard-96", (0x12, 0x00, 0x00, 0x00, 0x60, 0x00), 0x60),
    Probe("inquiry-vpd-supported", (0x12, 0x01, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("inquiry-vpd-serial", (0x12, 0x01, 0x80, 0x00, 0xFC, 0x00), 0xFC),
    Probe("inquiry-vpd-device-id", (0x12, 0x01, 0x83, 0x00, 0xFC, 0x00), 0xFC),
    Probe("inquiry-extrainq", (0x12, 0x00, 0x00, 0x00, 0xF0, 0x40, 0, 0, 0, 0, 0, 0), 0xF0),
    Probe("mode-sense6-all", (0x1A, 0x00, 0x3F, 0x00, 0xFC, 0x00), 0xFC),
    Probe("mode-sense6-cd-dvd-cap", (0x1A, 0x00, 0x2A, 0x00, 0xFC, 0x00), 0xFC),
    Probe("mode-sense10-all", (0x5A, 0x00, 0x3F, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("get-configuration-current", (0x46, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("get-configuration-all", (0x46, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("get-event-status-media", (0x4A, 0x01, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("read-toc-format-0", (0x43, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("read-disc-information", (0x51, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("read-track-information-lba0", (0x52, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00), 0xFC),
    Probe("mechanism-status", (0xBD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00, 0x00), 0xFC),
    Probe("read-dvd-structure-format0", (0xAD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFC, 0x00, 0x00), 0xFC),
    Probe("get-performance-nominal", (0xAC, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x03, 0x00), 8),
    Probe("read-buffer-id01", (0x3C, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00), 0x100, group="read-buffer"),
    Probe("read-buffer-id02", (0x3C, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00), 0x100, group="read-buffer"),
    Probe("read-buffer-idE2", (0x3C, 0x01, 0xE2, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00), 0x100, group="read-buffer"),
    Probe("read-buffer-idF0-small", (0x3C, 0x01, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00), 0x100, group="read-buffer"),
    Probe("read-buffer-idF1", (0x3C, 0x01, 0xF1, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00), 0x100, group="read-buffer"),
)


def cdb_text(cdb: tuple[int, ...]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def ascii_preview(data: bytes) -> str:
    return "".join(chr(byte) if 32 <= byte < 127 else "." for byte in data)


def run_probe(args: argparse.Namespace, probe: Probe) -> dict[str, Any]:
    cmd = [args.sg_raw, "--cmdset=1", "-b", "--timeout", str(args.timeout)]
    if probe.request_len:
        cmd.extend(["--request", str(probe.request_len)])
    cmd.extend([args.device, *[f"{byte:02x}" for byte in probe.cdb]])
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.process_timeout,
        )
        elapsed = time.monotonic() - start
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - start
        stdout = exc.stdout or b""
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or "")
        return {
            "name": probe.name,
            "group": probe.group,
            "notes": probe.notes,
            "cdb": cdb_text(probe.cdb),
            "request_len": probe.request_len,
            "returncode": None,
            "elapsed_s": round(elapsed, 6),
            "stdout_len": len(stdout),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest() if stdout else None,
            "stdout_first128_hex": stdout[:128].hex(),
            "stdout_ascii_preview": ascii_preview(stdout[:128]),
            "stdout_hex": stdout.hex() if len(stdout) <= args.keep_hex_limit else None,
            "stderr": stderr,
            "status_good_text": False,
            "timed_out": True,
        }
    elapsed = time.monotonic() - start
    out = proc.stdout
    err = proc.stderr.decode("utf-8", errors="replace")
    return {
        "name": probe.name,
        "group": probe.group,
        "notes": probe.notes,
        "cdb": cdb_text(probe.cdb),
        "request_len": probe.request_len,
        "returncode": proc.returncode,
        "elapsed_s": round(elapsed, 6),
        "stdout_len": len(out),
        "stdout_sha256": hashlib.sha256(out).hexdigest() if out else None,
        "stdout_first128_hex": out[:128].hex(),
        "stdout_ascii_preview": ascii_preview(out[:128]),
        "stdout_hex": out.hex() if len(out) <= args.keep_hex_limit else None,
        "stderr": err,
        "status_good_text": proc.returncode == 0 and "SCSI Status: Good" in err,
        "timed_out": False,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal-Mode Read-Only SCSI Surface Probe",
        "",
        f"Date: {report['timestamp_utc']}",
        "",
        "This probe sends only no-data-out status/inquiry/read-style CDBs. It is",
        "intended to catalog host-visible normal LD5M response channels, not to",
        "exercise updater or mechanics commands.",
        "",
        "## Target",
        "",
        "```text",
        f"host   {report['host']}",
        f"device {report['device']}",
        "```",
        "",
        "## Results",
        "",
        "| name | group | rc | good | elapsed | bytes | first bytes / ascii |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in report["probes"]:
        first = item["stdout_first128_hex"][:48]
        ascii_text = item["stdout_ascii_preview"].replace("|", "\\|")
        if len(ascii_text) > 40:
            ascii_text = ascii_text[:40] + "..."
        lines.append(
            f"| `{item['name']}` | `{item['group']}` | {item['returncode']} | {str(item['status_good_text']).lower()} | "
            f"{item['elapsed_s']:.6f}s | {item['stdout_len']} | `{first}` `{ascii_text}` |"
        )
    lines += [
        "",
        "## Notes",
        "",
        "- Nonzero `returncode` here usually means CHECK CONDITION/illegal request/no media,",
        "  not necessarily a transport failure.",
        "- If a future persistent hook needs a host-visible normal-mode trigger, prefer",
        "  commands that return data quickly and consistently in this report.",
        "- `READ BUFFER` probes are opt-in because normal-mode `id=02` has hung the",
        "  optical LUN once and required a Pico servo power cycle.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    parser.add_argument("--host", default="jonathan-thinkpad-t480s")
    parser.add_argument("--keep-hex-limit", type=int, default=0x400)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--process-timeout", type=int, default=15)
    parser.add_argument("--include-read-buffer", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": args.host,
        "device": args.device,
        "probes": [],
    }
    selected = [
        probe for probe in PROBES if args.include_read_buffer or probe.group != "read-buffer"
    ]
    for probe in selected:
        item = run_probe(args, probe)
        report["probes"].append(item)
        print(
            f"{probe.name}: rc={item['returncode']} good={item['status_good_text']} "
            f"timeout={item.get('timed_out', False)} len={item['stdout_len']} "
            f"elapsed={item['elapsed_s']:.6f}s",
            flush=True,
        )
        if args.out_json:
            args.out_json.parent.mkdir(parents=True, exist_ok=True)
            args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        if args.out_md:
            args.out_md.parent.mkdir(parents=True, exist_ok=True)
            args.out_md.write_text(render_md(report))
        if args.delay:
            time.sleep(args.delay)

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(render_md(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
