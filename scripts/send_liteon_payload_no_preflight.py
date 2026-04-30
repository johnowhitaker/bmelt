#!/usr/bin/env python3
"""Send one SCSI CDB with optional payload and log the result.

This is intentionally small and does not do identity preflight. It is useful
for wedged/currentboot-ish states where the identity path itself may be
stateful or malformed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def parse_cdb(text: str) -> list[int]:
    data = bytes.fromhex(compact_hex(text))
    if not data:
        raise ValueError("--cdb must contain at least one byte")
    return list(data)


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def run_sg_raw(args: argparse.Namespace, payload: bytes) -> dict[str, object]:
    cmd = [args.sg_raw, "--cmdset=1", "-b", "--timeout", str(args.timeout)]
    if args.request:
        cmd.extend(["--request", str(args.request)])
    if payload:
        cmd.extend(["--send", str(len(payload))])
    cdb = parse_cdb(args.cdb)
    cmd.extend([args.device, *[f"{byte:02x}" for byte in cdb]])
    started = time.monotonic()
    proc = subprocess.run(cmd, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elapsed = time.monotonic() - started
    stdout = proc.stdout
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return {
        "cmd": cmd,
        "cdb": cdb_text(cdb),
        "request_len": args.request,
        "payload_len": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest() if payload else None,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "stdout_len": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest() if stdout else None,
        "stdout_first256_hex": stdout[:0x100].hex(),
        "stdout_hex": stdout.hex() if len(stdout) <= 0x1000 else None,
        "stderr": stderr,
        "status_good_text": "SCSI Status: Good" in stderr,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--cdb", required=True, help="CDB bytes, with or without spaces")
    parser.add_argument("--payload", type=Path, help="Optional data-out payload file")
    parser.add_argument("--request", type=int, default=0, help="Optional data-in request length")
    parser.add_argument("--sg-raw", default=shutil.which("sg_raw") or "sg_raw")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs/live/single-cdb")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not shutil.which(args.sg_raw):
        raise RuntimeError(f"sg_raw not found: {args.sg_raw}")
    payload = args.payload.read_bytes() if args.payload else b""
    result = run_sg_raw(args, payload)
    run_id = datetime.now(timezone.utc).strftime("single-cdb-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {result_path}")
    print(f"cdb={result['cdb']}")
    print(f"payload_len={result['payload_len']} rc={result['returncode']} stdout_len={result['stdout_len']}")
    if result["stderr"]:
        print(result["stderr"], end="")
    return int(result["returncode"])


if __name__ == "__main__":
    raise SystemExit(main())
