#!/usr/bin/env python3
"""Run a LiteOn candidate event slice without any preflight identity reads.

This is for states where INQUIRY/EXTRAINQ are themselves hooked or otherwise
stateful.  It intentionally does not probe identity before or after the write
slice unless --capture-identity-after is requested.
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
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STANDARD_INQUIRY_CDB = [0x12, 0x00, 0x00, 0x00, 0x24, 0x00]
EXTRAINQ_CDB = [0x12, 0x00, 0x00, 0x00, 0xF0, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def bytes_from_cdb(text: str) -> list[int]:
    return [int(part, 16) for part in text.split()]


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def ascii_field(data: bytes) -> str:
    return data.decode("ascii", errors="replace").strip()


def payload_for_event(event: dict[str, Any]) -> bytes:
    model = event.get("payload_model") or {}
    if model.get("kind") == "inline_payload_hex":
        return bytes.fromhex(compact_hex(model.get("payload_hex", "")))
    return b""


def phase_timeout(phase: str, args: argparse.Namespace, payload_len: int) -> int:
    if phase == "bank_pmac_prefix":
        return args.pmac_timeout
    if phase in {"profile_tail_arg7f", "arg00_chunk_transfer"} or payload_len:
        return args.write_timeout
    return args.timeout


def run_sg_raw(
    sg_raw: str,
    device: str,
    cdb: list[int],
    *,
    request_len: int = 0,
    payload: bytes = b"",
    timeout: int = 5,
) -> dict[str, Any]:
    cmd = [sg_raw, "--cmdset=1", "-b", "--timeout", str(timeout)]
    if request_len:
        cmd.extend(["--request", str(request_len)])
    if payload:
        cmd.extend(["--send", str(len(payload))])
    cmd.extend([device, *[f"{byte:02x}" for byte in cdb]])
    started = time.monotonic()
    proc = subprocess.run(cmd, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elapsed = time.monotonic() - started
    stdout = proc.stdout
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return {
        "cmd": cmd,
        "cdb": cdb_text(cdb),
        "request_len": request_len,
        "payload_len": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest() if payload else None,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "stdout_len": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest() if stdout else None,
        "stdout_first64_hex": stdout[:64].hex(),
        "stdout_hex": stdout.hex() if len(stdout) <= 0x1000 else None,
        "stderr": stderr,
        "status_good_text": "SCSI Status: Good" in stderr,
    }


def describe_standard(data: bytes) -> dict[str, Any]:
    return {
        "len": len(data),
        "vendor": ascii_field(data[0x08:0x10]) if len(data) >= 0x10 else "",
        "product": ascii_field(data[0x10:0x20]) if len(data) >= 0x20 else "",
        "revision": ascii_field(data[0x20:0x24]) if len(data) >= 0x24 else "",
        "sha256": hashlib.sha256(data).hexdigest() if data else None,
    }


def capture_identity(args: argparse.Namespace) -> dict[str, Any]:
    standard = run_sg_raw(args.sg_raw, args.device, STANDARD_INQUIRY_CDB, request_len=36, timeout=args.timeout)
    extrainq = run_sg_raw(args.sg_raw, args.device, EXTRAINQ_CDB, request_len=0xF0, timeout=args.timeout)
    return {
        "standard_raw": standard,
        "extrainq_raw": extrainq,
        "standard": describe_standard(bytes.fromhex(standard.get("stdout_hex") or "")),
    }


def execute_events(args: argparse.Namespace, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    attempted: list[dict[str, Any]] = []
    expected_readback: bytes | None = None
    for event in events:
        if args.skip_profile_tails and event.get("phase") == "profile_tail_arg7f":
            continue
        payload = payload_for_event(event)
        request_len = int(event.get("data_in_len") or 0)
        data_out_len = int(event.get("data_out_len") or 0)
        if len(payload) != data_out_len:
            raise ValueError(f"event {event['event_index']} payload len {len(payload)} != {data_out_len}")
        item = run_sg_raw(
            args.sg_raw,
            args.device,
            bytes_from_cdb(event["cdb"]),
            request_len=request_len,
            payload=payload,
            timeout=phase_timeout(str(event.get("phase")), args, len(payload)),
        )
        item["event_index"] = event["event_index"]
        item["phase"] = event["phase"]
        item["role"] = event.get("role")
        if event["phase"] == "arg00_chunk_transfer" and item["returncode"] == 0:
            expected_readback = payload
        elif event["phase"] == "arg00_readback_verify" and item["returncode"] == 0:
            data = bytes.fromhex(item.get("stdout_hex") or "")
            item["readback_matches_previous_chunk"] = expected_readback is not None and data == expected_readback
            if not item["readback_matches_previous_chunk"]:
                item["returncode"] = item["returncode"] or 99
                item["stderr"] += "\nreadback did not match previous chunk"
            expected_readback = None
        attempted.append(item)
        print(
            f"event={event['event_index']} phase={event['phase']} rc={item['returncode']} "
            f"out={len(payload)} in={item['stdout_len']}",
            flush=True,
        )
        if args.delay_ms:
            time.sleep(args.delay_ms / 1000)
        if item["returncode"] != 0 and not args.continue_after_failure:
            return attempted, item
    return attempted, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--sg-raw", default=shutil.which("sg_raw") or "sg_raw")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "logs/linux-no-preflight-events")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--write-timeout", type=int, default=30)
    parser.add_argument("--pmac-timeout", type=int, default=180)
    parser.add_argument("--delay-ms", type=int, default=0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--continue-after-failure", action="store_true")
    parser.add_argument("--skip-profile-tails", action="store_true")
    parser.add_argument("--capture-identity-after", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not shutil.which(args.sg_raw):
        raise RuntimeError(f"sg_raw not found: {args.sg_raw}")
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    events = [
        event
        for event in candidate["events"]
        if int(event["event_index"]) >= args.start_index
        and (args.end_index is None or int(event["event_index"]) <= args.end_index)
    ]
    run_id = datetime.now(timezone.utc).strftime("liteon-no-preflight-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "run_id": run_id,
        "candidate": str(args.candidate),
        "device": args.device,
        "start_index": args.start_index,
        "end_index": args.end_index,
        "skip_profile_tails": args.skip_profile_tails,
        "events_attempted": [],
        "stopped_on_failure": None,
        "success": False,
    }
    try:
        attempted, failure = execute_events(args, events)
        result["events_attempted"] = attempted
        result["stopped_on_failure"] = failure
        result["success"] = failure is None
        if args.capture_identity_after:
            result["identity_after"] = capture_identity(args)
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"

    result_path = out_dir / "no-preflight-events-result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {result_path}")
    print(f"success={int(result.get('success', False))}")
    if result.get("error"):
        print(f"error={result['error']}")
        return 1
    if result.get("stopped_on_failure"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
