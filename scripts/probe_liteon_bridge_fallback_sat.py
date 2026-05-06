#!/usr/bin/env python3
"""Read-only SAT diagnostic for the Initio/Generic bridge fallback.

When the optical LUN disappears, this bridge may still expose a Direct-Access
`Generic External 1.14` device. Surprisingly, SAT IDENTIFY PACKET DEVICE can
still see the attached PLDS drive underneath. This script records that state
without sending any firmware or flash commands.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run(cmd: list[str]) -> dict[str, Any]:
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", "replace"),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }


def extract_identify_strings(raw: bytes) -> dict[str, str]:
    def ata_string(word_start: int, word_count: int) -> str:
        field = raw[word_start * 2 : (word_start + word_count) * 2]
        swapped = bytearray()
        for i in range(0, len(field), 2):
            if i + 1 < len(field):
                swapped.extend([field[i + 1], field[i]])
        return swapped.decode("ascii", "replace").strip()

    if len(raw) < 512:
        return {}
    return {
        "serial": ata_string(10, 10),
        "firmware": ata_string(23, 4),
        "model": ata_string(27, 20),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sg_inq = shutil.which("sg_inq") or "sg_inq"
    sg_sat_identify = shutil.which("sg_sat_identify") or "sg_sat_identify"

    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "device": args.device,
        "identity": run([sg_inq, args.device]),
        "identify_packet_text": run([sg_sat_identify, "-p", args.device]),
    }

    raw_proc = subprocess.run(
        [sg_sat_identify, "-p", "--raw", args.device],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    report["identify_packet_raw"] = {
        "cmd": [sg_sat_identify, "-p", "--raw", args.device],
        "returncode": raw_proc.returncode,
        "stderr": raw_proc.stderr.decode("utf-8", "replace"),
        "length": len(raw_proc.stdout),
        "strings": extract_identify_strings(raw_proc.stdout),
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(json.dumps({"out": str(args.out), "strings": report["identify_packet_raw"]["strings"]}, sort_keys=True))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
