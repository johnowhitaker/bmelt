#!/usr/bin/env python3
"""Build an updater-modeled LiteOn profile-tail WRITE BUFFER payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import extract_liteon_flash_profile_table  # noqa: E402
from generate_liteon_write_sequence_dry_run import hex_bytes, parse_extrainq  # noqa: E402
from model_liteon_updater_write_crypto import aes_cbc_encrypt_chunks, aes_cmac  # noqa: E402


DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-profile-tail-ef130045.json"
DEFAULT_OUT_BIN = ROOT / "references/firmware/extracted/liteon-profile-tail-ef130045.bin"
DEFAULT_EXTRAINQ = ROOT / "references/evidence/ld5m-extrainq-reference.log"


def align16(value: int) -> int:
    return (value + 15) & ~15


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def obj3_slice(data: bytes, offset: int, size: int) -> bytes:
    return extract_liteon_flash_profile_table.obj3_slice(data, offset, size)


def profile_tail_cdb(*, offset: int, length: int, arg_control: int) -> bytes:
    if not 0 <= offset <= 0xFFFFFF:
        raise ValueError(f"profile-tail offset must fit 24 bits: 0x{offset:x}")
    if not 0 <= length <= 0xFFFFFF:
        raise ValueError(f"profile-tail length must fit 24 bits: 0x{length:x}")
    if not 0 <= arg_control <= 0xFF:
        raise ValueError(f"profile-tail arg/control must fit 8 bits: 0x{arg_control:x}")
    return bytes(
        [
            0x3B,
            0x05,
            0x01,
            (offset >> 16) & 0xFF,
            (offset >> 8) & 0xFF,
            offset & 0xFF,
            (length >> 16) & 0xFF,
            (length >> 8) & 0xFF,
            length & 0xFF,
            arg_control,
            0x00,
            0x00,
        ]
    )


def build_plain_tail(updater: bytes, profile: dict[str, Any]) -> tuple[bytes, bytes]:
    entry = bytes(profile["profile_id_bytes"]) + int(profile["record_length"]).to_bytes(2, "big")
    body = obj3_slice(
        updater,
        int(profile["body_autodata_offset"]),
        int(profile["record_length"]),
    )
    if profile["profile_tail_mode"] == 1:
        header = entry
    else:
        header = entry[:4]

    plain = header + body
    if len(body) & 1:
        plain += b"\x00"
    if profile["suppress_header_len_add"]:
        plain = body + (b"\x00" if len(body) & 1 else b"")
    padded_len = align16(len(plain))
    plain += bytes(padded_len - len(plain))
    return entry, plain


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--updater", type=Path, default=extract_liteon_flash_profile_table.DEFAULT_UPDATER)
    parser.add_argument("--extrainq", type=Path, default=DEFAULT_EXTRAINQ)
    parser.add_argument("--profile-id", default="ef130045")
    parser.add_argument(
        "--plain-tail",
        type=Path,
        help=(
            "Use a prebuilt 16-byte-aligned profile-tail plaintext instead of "
            "the DOS updater profile-body table model"
        ),
    )
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-bin", type=Path, default=DEFAULT_OUT_BIN)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    extrainq, iv, key = parse_extrainq(args.extrainq)
    profile = None
    entry = bytes.fromhex(args.profile_id)
    plain_source = "dos_updater_profile_table"
    if args.plain_tail is not None:
        plain = args.plain_tail.read_bytes()
        if len(plain) % 16:
            raise ValueError("--plain-tail length must be 16-byte aligned")
        if len(plain) < 6:
            raise ValueError("--plain-tail must include the six-byte profile header")
        entry = plain[:6]
        plain_source = "plain_tail_file"
    else:
        updater = args.updater.read_bytes()
        profiles = extract_liteon_flash_profile_table.parse_profiles(updater)
        profile_id = bytes.fromhex(args.profile_id)
        if len(profile_id) != 4:
            raise ValueError("--profile-id must be exactly four bytes")
        profile = next((item for item in profiles if bytes(item["profile_id_bytes"]) == profile_id), None)
        if profile is None:
            raise ValueError(f"profile id not found in updater table: {args.profile_id}")
        if profile["profile_tail_arg"] != "0x7f":
            raise ValueError(f"profile {args.profile_id} is not an arg=0x7f tail")
        entry, plain = build_plain_tail(updater, profile)

    ciphertext = aes_cbc_encrypt_chunks(key, iv, [plain])[0]
    cmac = aes_cmac(key, ciphertext)
    payload = ciphertext + cmac
    expected_len = len(plain) + 0x10
    if profile is not None:
        expected_len = int(profile["aes_plus_cmac_tail_len"])
        if len(payload) != expected_len:
            raise ValueError(f"payload length mismatch: {len(payload)} != {expected_len}")

    cdb = profile_tail_cdb(
        offset=0 if profile is None else int(profile["profile_tail_offset"], 0),
        length=len(payload),
        arg_control=0x7F,
    )
    report = {
        "status": "offline_profile_tail_payload_model",
        "updater": str(args.updater),
        "extrainq": str(args.extrainq),
        "plain_source": plain_source,
        "plain_tail": str(args.plain_tail) if args.plain_tail is not None else None,
        "profile": profile,
        "entry_hex": entry.hex(),
        "plain_len": len(plain),
        "plain_sha256": sha256_bytes(plain),
        "ciphertext_len": len(ciphertext),
        "ciphertext_first16": ciphertext[:16].hex(),
        "ciphertext_sha256": sha256_bytes(ciphertext),
        "cmac": cmac.hex(),
        "payload_len": len(payload),
        "payload_first16": payload[:16].hex(),
        "payload_sha256": sha256_bytes(payload),
        "payload_path": str(args.out_bin),
        "cdb": hex_bytes(cdb),
        "notes": [
            "Payload is AES-CBC(profile row/body plaintext) plus AES-CMAC(ciphertext).",
            "The profile-tail helper uses the static updater layout: byte 9 arg/control=0x7f, byte 10 zero, byte 11 zero.",
            "Use --plain-tail with the official trace-decrypted plaintext to reproduce the Windows updater payloads.",
        ],
    }
    args.out_bin.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_bin.write_bytes(payload)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
