#!/usr/bin/env python3
"""Recover the blank-revision currentboot variant with dynamic slot-5 tails.

This state was observed after helper/LED probing. Standard/currentboot profile
tails are rejected, but the malformed EXTRAINQ response still carries a usable
slot-5 key at bytes 0x9c..0xab. The slot-5 key bytes change after bank
boundaries, so this script re-reads EXTRAINQ before every bank tail.
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
EXTRAINQ_CDB = [0x12, 0x00, 0x00, 0x00, 0xF0, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
PROFILE_TAIL_CDB = [0x3B, 0x05, 0x01, 0x00, 0x00, 0x00, 0x00, 0x0B, 0xD0, 0x7F, 0x00, 0x00]
PLDSVUC_LOCK_CDB = [0xF3, 0x00, 0x50, 0x4C, 0x44, 0x53, 0x56, 0x55, 0x43, 0x80, 0x00, 0x00]


def import_crypto() -> tuple[Any, Any, Any]:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    from model_liteon_updater_write_crypto import (  # noqa: PLC0415
        StreamingCmacState,
        aes_cbc_encrypt_chunks,
        aes_cmac,
    )

    return StreamingCmacState, aes_cbc_encrypt_chunks, aes_cmac


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def bytes_from_cdb(text: str) -> list[int]:
    return [int(part, 16) for part in text.split()]


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def payload_for_event(event: dict[str, Any]) -> bytes:
    model = event.get("payload_model") or {}
    if model.get("kind") == "inline_payload_hex":
        return bytes.fromhex(compact_hex(model.get("payload_hex", "")))
    return b""


def run_sg_raw(
    sg_raw: str,
    device: str,
    cdb: list[int],
    *,
    request_len: int = 0,
    payload: bytes = b"",
    timeout: int = 30,
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


def event_index_for_bank_tail(bank: int) -> int:
    return 1 + bank * 34


def bank_events(events: list[dict[str, Any]], bank: int) -> list[dict[str, Any]]:
    tail = event_index_for_bank_tail(bank)
    start = tail + 1
    end = tail + 33
    rows = [event for event in events if start <= int(event["event_index"]) <= end]
    if len(rows) != 33:
        raise ValueError(f"expected 33 events for bank {bank}, got {len(rows)}")
    return rows


def build_bank2_payloads(
    *,
    image: bytes,
    key: bytes,
    iv: bytes,
) -> tuple[list[bytes], bytes]:
    StreamingCmacState, aes_cbc_encrypt_chunks, _aes_cmac = import_crypto()
    chunks = [image[offset : offset + 0x1000] for offset in range(0x20000, 0x30000, 0x1000)]
    encrypted_chunks = aes_cbc_encrypt_chunks(key, iv, chunks)
    pmac_state = StreamingCmacState(key)
    pmac = None
    for index, chunk in enumerate(encrypted_chunks):
        pmac = pmac_state.update(chunk, init=index == 0, final=index == len(encrypted_chunks) - 1)
    if pmac is None:
        raise ValueError("bank 2 pMac did not finalize")
    return encrypted_chunks, pmac


def build_tail(plain_tail: bytes, response: bytes) -> tuple[bytes, dict[str, Any]]:
    _StreamingCmacState, aes_cbc_encrypt_chunks, aes_cmac = import_crypto()
    iv = response[0x10:0x20]
    key_off = 0x9C
    key = response[key_off : key_off + 16]
    if len(key) != 16:
        raise ValueError("response too short for slot-5 key")
    ciphertext = aes_cbc_encrypt_chunks(key, iv, [plain_tail])[0]
    cmac = aes_cmac(key, ciphertext)
    payload = ciphertext + cmac
    return payload, {
        "key_off": key_off,
        "key_hex": key.hex(),
        "iv_hex": iv.hex(),
        "cmac": cmac.hex(),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "response_sha256": hashlib.sha256(response).hexdigest(),
    }


def run_event(
    args: argparse.Namespace,
    event: dict[str, Any],
    *,
    payload_override: bytes | None = None,
    expected_readback: bytes | None = None,
) -> tuple[dict[str, Any], bytes | None]:
    payload = payload_for_event(event) if payload_override is None else payload_override
    item = run_sg_raw(
        args.sg_raw,
        args.device,
        bytes_from_cdb(event["cdb"]),
        request_len=int(event.get("data_in_len") or 0),
        payload=payload,
        timeout=args.pmac_timeout if event["phase"] == "bank_pmac_prefix" else args.write_timeout,
    )
    item["event_index"] = event["event_index"]
    item["phase"] = event["phase"]
    item["role"] = event.get("role")
    if event["phase"] == "arg00_chunk_transfer" and item["returncode"] == 0:
        return item, payload
    if event["phase"] == "arg00_readback_verify" and item["returncode"] == 0:
        data = bytes.fromhex(item.get("stdout_hex") or "")
        item["readback_matches_previous_chunk"] = expected_readback is not None and data == expected_readback
        if not item["readback_matches_previous_chunk"]:
            item["returncode"] = item["returncode"] or 99
            item["stderr"] += "\nreadback did not match previous chunk"
    return item, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", required=True)
    parser.add_argument("--candidate", type=Path, default=ROOT / "references/firmware/extracted/liteon-full-currentboot-ld5m-base-candidate.json")
    parser.add_argument("--image", type=Path, default=ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin")
    parser.add_argument("--plain-tail", type=Path, default=ROOT / "references/firmware/extracted/liteon-official-profile-tail-ef130045-plain.bin")
    parser.add_argument("--sg-raw", default=shutil.which("sg_raw") or "sg_raw")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "runs/restore/blank-currentboot-dynamic-recovery")
    parser.add_argument("--start-bank", type=int, default=0)
    parser.add_argument("--end-bank", type=int, default=15)
    parser.add_argument("--initial-pmac", help="Hex pMac to carry for banks after 2 when resuming")
    parser.add_argument("--skip-tail-for-start-bank", action="store_true")
    parser.add_argument("--skip-pldsvuc", action="store_true")
    parser.add_argument("--write-timeout", type=int, default=60)
    parser.add_argument("--pmac-timeout", type=int, default=180)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    events = candidate["events"]
    image = args.image.read_bytes()
    plain_tail = args.plain_tail.read_bytes()
    last_pmac = bytes.fromhex(args.initial_pmac) if args.initial_pmac else None
    if last_pmac is not None and len(last_pmac) != 16:
        raise ValueError("--initial-pmac must be 16 bytes")

    run_id = datetime.now(timezone.utc).strftime("blank-dynamic-recovery-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "run_id": run_id,
        "device": args.device,
        "start_bank": args.start_bank,
        "end_bank": args.end_bank,
        "attempts": [],
        "success": False,
    }

    try:
        for bank in range(args.start_bank, args.end_bank + 1):
            if not (args.skip_tail_for_start_bank and bank == args.start_bank):
                extrainq = run_sg_raw(args.sg_raw, args.device, EXTRAINQ_CDB, request_len=0xB0, timeout=args.write_timeout)
                if extrainq["returncode"] != 0 or not extrainq.get("stdout_hex"):
                    result["stopped_on_failure"] = {"bank": bank, "step": "extrainq", "result": extrainq}
                    break
                response = bytes.fromhex(str(extrainq["stdout_hex"]))
                tail_payload, tail_meta = build_tail(plain_tail, response)
                tail = run_sg_raw(args.sg_raw, args.device, PROFILE_TAIL_CDB, payload=tail_payload, timeout=args.write_timeout)
                tail["bank"] = bank
                tail["phase"] = "dynamic_profile_tail_arg7f"
                tail["tail_meta"] = tail_meta
                result["attempts"].append(tail)
                print(f"bank={bank} tail rc={tail['returncode']} key={tail_meta['key_hex']}", flush=True)
                if tail["returncode"] != 0:
                    result["stopped_on_failure"] = {"bank": bank, "step": "tail", "result": tail}
                    break
                active_response = response
            else:
                active_response = bytes(0xB0)

            bank2_chunks: list[bytes] | None = None
            if bank == 2:
                key = active_response[0x9C:0xAC]
                iv = active_response[0x10:0x20]
                bank2_chunks, last_pmac = build_bank2_payloads(image=image, key=key, iv=iv)
                result["bank2_dynamic_pmac"] = last_pmac.hex()

            expected_readback = None
            chunk_index = 0
            for event in bank_events(events, bank):
                payload_override = None
                if bank == 2 and event["phase"] == "arg00_chunk_transfer":
                    if bank2_chunks is None:
                        raise ValueError("missing dynamic bank 2 chunks")
                    payload_override = bank2_chunks[chunk_index]
                    chunk_index += 1
                elif bank > 2 and event["phase"] == "bank_pmac_prefix":
                    if last_pmac is None:
                        raise ValueError("cannot carry pMac before bank 2 has finalized")
                    payload_override = last_pmac

                item, expected_readback = run_event(
                    args,
                    event,
                    payload_override=payload_override,
                    expected_readback=expected_readback,
                )
                result["attempts"].append(item)
                print(
                    f"event={event['event_index']} bank={bank} phase={event['phase']} "
                    f"rc={item['returncode']} out={item['payload_len']} in={item['stdout_len']}",
                    flush=True,
                )
                if item["returncode"] != 0:
                    result["stopped_on_failure"] = {"bank": bank, "step": "event", "result": item}
                    raise RuntimeError(f"event {event['event_index']} failed")

        else:
            if not args.skip_pldsvuc:
                final = run_sg_raw(args.sg_raw, args.device, PLDSVUC_LOCK_CDB, timeout=args.write_timeout)
                final["phase"] = "pldsvuc_lock"
                result["attempts"].append(final)
                print(f"pldsvuc rc={final['returncode']}", flush=True)
                if final["returncode"] != 0:
                    result["stopped_on_failure"] = {"step": "pldsvuc", "result": final}
                else:
                    result["success"] = True
            else:
                result["success"] = True
    except Exception as exc:  # noqa: BLE001
        result.setdefault("stopped_on_failure", {"step": "exception", "error": f"{type(exc).__name__}: {exc}"})

    path = out_dir / "blank-dynamic-recovery-result.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    print(f"success={int(result.get('success', False))}")
    return 0 if result.get("success") else 2


if __name__ == "__main__":
    raise SystemExit(main())
