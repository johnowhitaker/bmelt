#!/usr/bin/env python3
"""Recover a LiteOn/PLDS DS-8ABSH from the 0D5C currentboot view on Linux.

This packages the sequence proven on the spare drive:

1. Send the LD5M currentboot-key profile tail.
2. Send same-family bank 0 chunks/readbacks and the bank 0 0x80 pMac.
3. Continue banks 1..15 with currentboot tails, chunks/readbacks, pMacs.
4. Send the final PLDSVUC lock/status transition.

The script uses Linux sg_raw and logs every CDB result. It verifies chunk
readbacks against the just-sent payloads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK0 = ROOT / "references/firmware/extracted/liteon-same-family-boundary-probe-candidate.json"
DEFAULT_CONTINUATION = ROOT / "references/firmware/extracted/liteon-same-family-currentboot-continuation-candidate.json"
DEFAULT_TAIL = ROOT / "references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-currentboot.bin"
DEFAULT_OUT_DIR = ROOT / "logs/linux-currentboot-recovery"
STANDARD_INQUIRY_CDB = [0x12, 0x00, 0x00, 0x00, 0x24, 0x00]
EXTRAINQ_CDB = [0x12, 0x00, 0x00, 0x00, 0xF0, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
CURRENTBOOT_TAIL_CDB = "3B 05 01 00 00 00 00 0B D0 7F 00 00"


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def bytes_from_cdb(text: str) -> list[int]:
    return [int(part, 16) for part in text.split()]


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def ascii_field(data: bytes) -> str:
    return data.decode("ascii", errors="replace").strip()


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
    proc = subprocess.run(cmd, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = proc.stdout
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return {
        "cmd": cmd,
        "cdb": cdb_text(cdb),
        "request_len": request_len,
        "payload_len": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest() if payload else None,
        "returncode": proc.returncode,
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


def describe_extrainq(data: bytes) -> dict[str, Any]:
    marker = data.find(b"EXTRAINQ")
    out: dict[str, Any] = {
        "len": len(data),
        "marker_found": marker >= 0,
        "marker_offset": marker if marker >= 0 else None,
        "vendor": ascii_field(data[0x08:0x10]) if len(data) >= 0x10 else "",
        "product": ascii_field(data[0x10:0x20]) if len(data) >= 0x20 else "",
        "revision": ascii_field(data[0x20:0x24]) if len(data) >= 0x24 else "",
        "timestamp": ascii_field(data[0x24:0x34]) if len(data) >= 0x34 else "",
        "sha256": hashlib.sha256(data).hexdigest() if data else None,
    }
    if marker >= 0:
        base = data[marker:]
        if len(base) >= 0x14:
            out["profile_len"] = int.from_bytes(base[0x08:0x0A], "big")
            out["profile_word"] = int.from_bytes(base[0x0A:0x0C], "big")
            out["primary_selector_value"] = (base[0x0A] + base[0x0B]) & 7
            out["feature_byte"] = base[0x10]
            out["aes_byte"] = base[0x12]
    if len(data) >= 0x80:
        key_selector = data[0x73]
        key_off = 0x74 + key_selector * 8
        out["key_selector"] = key_selector
        out["key_offset"] = key_off
        if key_off + 16 <= len(data):
            out["sec_key_ascii"] = ascii_field(data[key_off : key_off + 16])
            out["sec_key_hex"] = data[key_off : key_off + 16].hex()
    return out


def capture_identity(sg_raw: str, device: str, timeout: int) -> dict[str, Any]:
    standard = run_sg_raw(sg_raw, device, STANDARD_INQUIRY_CDB, request_len=36, timeout=timeout)
    extrainq = run_sg_raw(sg_raw, device, EXTRAINQ_CDB, request_len=0xF0, timeout=timeout)
    return {
        "standard_raw": standard,
        "extrainq_raw": extrainq,
        "standard": describe_standard(bytes.fromhex(standard.get("stdout_hex") or "")),
        "extrainq": describe_extrainq(bytes.fromhex(extrainq.get("stdout_hex") or "")),
    }


def inline_payload(event: dict[str, Any]) -> bytes:
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


def send_event(
    args: argparse.Namespace,
    event: dict[str, Any],
    *,
    expected_readback: bytes | None,
) -> tuple[dict[str, Any], bytes | None]:
    payload = inline_payload(event)
    request_len = int(event.get("data_in_len") or 0)
    data_out_len = int(event.get("data_out_len") or 0)
    if len(payload) != data_out_len:
        raise ValueError(
            f"event {event['event_index']} payload length {len(payload)} != data_out_len {data_out_len}"
        )
    item = run_sg_raw(
        args.sg_raw,
        args.device,
        bytes_from_cdb(event["cdb"]),
        request_len=request_len,
        payload=payload,
        timeout=phase_timeout(event["phase"], args, len(payload)),
    )
    item["event_index"] = event["event_index"]
    item["phase"] = event["phase"]
    item["role"] = event.get("role")
    if item["returncode"] != 0:
        raise RuntimeError(
            f"event {event['event_index']} {event['phase']} failed rc={item['returncode']}: "
            f"{item['stderr'].strip()}"
        )
    if event["phase"] == "arg00_chunk_transfer":
        expected_readback = payload
    elif event["phase"] == "arg00_readback_verify":
        data = bytes.fromhex(item.get("stdout_hex") or "")
        item["readback_matches_previous_chunk"] = expected_readback is not None and data == expected_readback
        if not item["readback_matches_previous_chunk"]:
            raise RuntimeError(f"event {event['event_index']} readback did not match previous chunk")
        expected_readback = None
    return item, expected_readback


def load_sequence(bank0_path: Path, continuation_path: Path, tail_path: Path) -> list[dict[str, Any]]:
    bank0 = json.loads(bank0_path.read_text(encoding="utf-8"))
    continuation = json.loads(continuation_path.read_text(encoding="utf-8"))
    tail = tail_path.read_bytes()
    first_tail = {
        "event_index": "currentboot-tail-before-bank0",
        "phase": "profile_tail_arg7f",
        "cdb": CURRENTBOOT_TAIL_CDB,
        "data_out_len": len(tail),
        "data_in_len": 0,
        "role": "LD5M currentboot-key profile tail before bank 0",
        "payload_model": {
            "kind": "inline_payload_hex",
            "payload_hex": tail.hex(),
            "payload_first16": tail[:16].hex(),
            "payload_sha256": hashlib.sha256(tail).hexdigest(),
        },
    }
    bank0_events = [event for event in bank0["events"] if 2 <= int(event["event_index"]) <= 34]
    return [first_tail, *bank0_events, *continuation["events"]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg1")
    parser.add_argument("--sg-raw", default=shutil.which("sg_raw") or "sg_raw")
    parser.add_argument("--bank0-candidate", type=Path, default=DEFAULT_BANK0)
    parser.add_argument("--continuation-candidate", type=Path, default=DEFAULT_CONTINUATION)
    parser.add_argument("--currentboot-tail", type=Path, default=DEFAULT_TAIL)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--write-timeout", type=int, default=30)
    parser.add_argument("--pmac-timeout", type=int, default=180)
    parser.add_argument("--delay-ms", type=int, default=0)
    parser.add_argument("--force", action="store_true", help="run even if preflight is not revision 0D5C")
    args = parser.parse_args()

    if shutil.which(args.sg_raw) is None:
        raise RuntimeError(f"sg_raw not found: {args.sg_raw}")
    sequence = load_sequence(args.bank0_candidate, args.continuation_candidate, args.currentboot_tail)
    run_id = datetime.now(timezone.utc).strftime("liteon-currentboot-recovery-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "run_id": run_id,
        "device": args.device,
        "bank0_candidate": str(args.bank0_candidate),
        "continuation_candidate": str(args.continuation_candidate),
        "currentboot_tail": str(args.currentboot_tail),
        "events": [],
        "success": False,
        "error": None,
    }

    try:
        result["identity_before"] = capture_identity(args.sg_raw, args.device, args.timeout)
        before_rev = result["identity_before"]["standard"].get("revision")
        if before_rev != "0D5C" and not args.force:
            raise RuntimeError(f"preflight revision is {before_rev!r}, expected 0D5C; use --force to run anyway")
        expected_readback: bytes | None = None
        for ordinal, event in enumerate(sequence):
            item, expected_readback = send_event(args, event, expected_readback=expected_readback)
            item["ordinal"] = ordinal
            result["events"].append(item)
            print(
                f"{ordinal:03d} event={event['event_index']} phase={event['phase']} "
                f"rc={item['returncode']} out={item['payload_len']} in={item['stdout_len']}",
                flush=True,
            )
            if args.delay_ms:
                time.sleep(args.delay_ms / 1000)
        result["identity_after"] = capture_identity(args.sg_raw, args.device, args.timeout)
        result["final_revision"] = result["identity_after"]["standard"].get("revision")
        result["success"] = result["final_revision"] == "LD5M"
        if not result["success"]:
            result["error"] = f"final revision is {result['final_revision']!r}, expected LD5M"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        try:
            result["identity_after_error"] = capture_identity(args.sg_raw, args.device, args.timeout)
        except Exception as identity_exc:
            result["identity_after_error_failed"] = f"{type(identity_exc).__name__}: {identity_exc}"
    out_path = out_dir / "recovery-result.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"events_sent={len(result['events'])}")
    print(f"success={int(result['success'])}")
    if result.get("final_revision"):
        print(f"final_revision={result['final_revision']}")
    if result["error"]:
        print(f"error={result['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
