#!/usr/bin/env python3
"""Model the LiteOn DOS updater's write-side AES helpers offline.

This script does not talk to the optical drive. It implements the primitives
identified in the DOS updater:

- AES-CBC transport encryption for the outgoing scratch buffer.
- AES-CMAC-style pMac generation with the standard Rb=0x87 subkey rule.

The exact updater bank/profile sequencing is still under reverse engineering,
so the optional image simulation is a hypothesis aid, not a flash recipe.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = ROOT / "references/firmware/extracted/ad12-filedecrypt/AD12-1.bin"
DEFAULT_OUT = ROOT / "references/firmware/extracted/liteon-updater-write-crypto-model.json"
DEFAULT_KEY_ASCII = "0D5C1D50-1  LD5M"
DEFAULT_IV_ASCII = "DVD+-RW DS-8ABSH"
BLOCK_SIZE = 16
RB = 0x87


def fmt_hex(value: int) -> str:
    return f"0x{value:x}"


def xor_bytes(left: bytes, right: bytes) -> bytes:
    if len(left) != len(right):
        raise ValueError("xor inputs must have equal length")
    return bytes(a ^ b for a, b in zip(left, right, strict=True))


def aes_encrypt_block(key: bytes, block: bytes) -> bytes:
    if len(block) != BLOCK_SIZE:
        raise ValueError("AES block must be 16 bytes")
    encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
    return encryptor.update(block) + encryptor.finalize()


def dbl(block: bytes) -> bytes:
    if len(block) != BLOCK_SIZE:
        raise ValueError("CMAC dbl input must be 16 bytes")
    carry = 0
    out = bytearray(BLOCK_SIZE)
    for index in range(BLOCK_SIZE - 1, -1, -1):
        value = block[index]
        out[index] = ((value << 1) & 0xFF) | carry
        carry = 1 if value & 0x80 else 0
    if block[0] & 0x80:
        out[-1] ^= RB
    return bytes(out)


def cmac_subkeys(key: bytes) -> tuple[bytes, bytes]:
    l_value = aes_encrypt_block(key, bytes(BLOCK_SIZE))
    k1 = dbl(l_value)
    k2 = dbl(k1)
    return k1, k2


def pad_cmac(block: bytes) -> bytes:
    if len(block) >= BLOCK_SIZE:
        raise ValueError("CMAC padding only applies to partial blocks")
    return block + b"\x80" + bytes(BLOCK_SIZE - len(block) - 1)


def aes_cmac(key: bytes, message: bytes) -> bytes:
    k1, k2 = cmac_subkeys(key)
    if not message:
        blocks = [xor_bytes(pad_cmac(b""), k2)]
    else:
        full_blocks = [message[offset : offset + BLOCK_SIZE] for offset in range(0, len(message), BLOCK_SIZE)]
        if len(full_blocks[-1]) == BLOCK_SIZE:
            full_blocks[-1] = xor_bytes(full_blocks[-1], k1)
        else:
            full_blocks[-1] = xor_bytes(pad_cmac(full_blocks[-1]), k2)
        blocks = full_blocks

    state = bytes(BLOCK_SIZE)
    for block in blocks:
        state = aes_encrypt_block(key, xor_bytes(state, block))
    return state


@dataclass
class StreamingCmacState:
    key: bytes
    chain: bytes = bytes(BLOCK_SIZE)

    def update(self, data: bytes, *, init: bool = False, final: bool = False) -> bytes | None:
        """Emulate updater helper 0x10e70 for 16-byte-aligned buffers."""
        if len(data) % BLOCK_SIZE:
            raise ValueError("updater streaming pMac helper expects 16-byte-aligned data")
        if init:
            self.chain = bytes(BLOCK_SIZE)
        if not data:
            raise ValueError("updater streaming pMac helper was not modeled for empty buffers")

        blocks = [data[offset : offset + BLOCK_SIZE] for offset in range(0, len(data), BLOCK_SIZE)]
        if final:
            k1, _ = cmac_subkeys(self.key)
            middle = blocks[:-1]
            last = xor_bytes(blocks[-1], k1)
        else:
            middle = blocks
            last = None

        for block in middle:
            self.chain = aes_encrypt_block(self.key, xor_bytes(self.chain, block))
        if last is not None:
            self.chain = aes_encrypt_block(self.key, xor_bytes(self.chain, last))
            return self.chain
        return None


def aes_cbc_encrypt_chunks(key: bytes, iv: bytes, chunks: list[bytes]) -> list[bytes]:
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    out = []
    for chunk in chunks:
        if len(chunk) % BLOCK_SIZE:
            raise ValueError("CBC chunks must be 16-byte aligned")
        out.append(encryptor.update(chunk))
    encryptor.finalize()
    return out


def parse_key(value: str, *, label: str) -> bytes:
    if value.startswith("hex:"):
        data = bytes.fromhex(value[4:])
    else:
        data = value.encode("ascii")
    if len(data) != BLOCK_SIZE:
        raise ValueError(f"{label} must be 16 bytes, got {len(data)}")
    return data


def self_test() -> dict[str, Any]:
    key = bytes.fromhex("2b7e151628aed2a6abf7158809cf4f3c")
    tests = [
        {
            "name": "nist_empty",
            "message": b"",
            "expected": "bb1d6929e95937287fa37d129b756746",
        },
        {
            "name": "nist_one_block",
            "message": bytes.fromhex("6bc1bee22e409f96e93d7e117393172a"),
            "expected": "070a16b46b4d4144f79bdd9dd04a287c",
        },
    ]
    results = []
    for item in tests:
        actual = aes_cmac(key, item["message"]).hex()
        results.append(
            {
                "name": item["name"],
                "expected": item["expected"],
                "actual": actual,
                "matches": actual == item["expected"],
            }
        )

    streaming = StreamingCmacState(key)
    streaming_actual = streaming.update(tests[1]["message"], init=True, final=True)
    results.append(
        {
            "name": "streaming_one_block",
            "expected": tests[1]["expected"],
            "actual": None if streaming_actual is None else streaming_actual.hex(),
            "matches": streaming_actual is not None and streaming_actual.hex() == tests[1]["expected"],
        }
    )
    return {"tests": results, "ok": all(item["matches"] for item in results)}


def simulate_image(path: Path, key: bytes, iv: bytes, chunk_size: int, bank_size: int, limit_chunks: int) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) % chunk_size:
        raise ValueError(f"image length {len(data)} is not a multiple of chunk size {chunk_size}")
    if chunk_size % BLOCK_SIZE or bank_size % chunk_size:
        raise ValueError("chunk size must be 16-byte aligned and divide bank size")

    chunks = [data[offset : offset + chunk_size] for offset in range(0, len(data), chunk_size)]
    encrypted_chunks = aes_cbc_encrypt_chunks(key, iv, chunks)
    chunks_per_bank = bank_size // chunk_size
    banks: dict[int, StreamingCmacState] = {}
    rows = []
    for index, encrypted in enumerate(encrypted_chunks):
        bank = index // chunks_per_bank
        chunk_in_bank = index % chunks_per_bank
        final = chunk_in_bank == chunks_per_bank - 1
        state = banks.setdefault(bank, StreamingCmacState(key))
        pmac = state.update(encrypted, init=(chunk_in_bank == 0), final=final)
        if index < limit_chunks:
            rows.append(
                {
                    "chunk_index": index,
                    "offset": index * chunk_size,
                    "bank": bank,
                    "chunk_in_bank": chunk_in_bank,
                    "encrypted_first16": encrypted[:16].hex(),
                    "pmac_if_final": None if pmac is None else pmac.hex(),
                    "send_arg00_cdb_model": f"3B 05 01 {index * chunk_size:06x} {chunk_size:06x} 00 00 00",
                }
            )
    return {
        "image": str(path),
        "image_length": len(data),
        "chunk_size": chunk_size,
        "bank_size": bank_size,
        "chunks": len(chunks),
        "chunks_per_bank": chunks_per_bank,
        "limited_rows": rows,
        "status": "hypothesis: bank/profile sequencing is not yet verified against the updater runtime",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE, help="Optional source image for offline simulation")
    parser.add_argument("--key", default=DEFAULT_KEY_ASCII, help="16-byte ASCII key, or hex:<32 hex chars>")
    parser.add_argument("--iv", default=DEFAULT_IV_ASCII, help="16-byte ASCII IV, or hex:<32 hex chars>")
    parser.add_argument("--chunk-size", type=lambda value: int(value, 0), default=0x4000)
    parser.add_argument("--bank-size", type=lambda value: int(value, 0), default=0x10000)
    parser.add_argument("--limit-chunks", type=int, default=8)
    parser.add_argument("--no-image-sim", action="store_true", help="Only run primitive self-tests")
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    key = parse_key(args.key, label="key")
    iv = parse_key(args.iv, label="iv")
    report: dict[str, Any] = {
        "self_test": self_test(),
        "defaults": {
            "key_hex": key.hex(),
            "iv_hex": iv.hex(),
            "chunk_size": args.chunk_size,
            "bank_size": args.bank_size,
        },
    }
    if not report["self_test"]["ok"]:
        print("error: AES-CMAC self-test failed", file=sys.stderr)
        return 2
    if not args.no_image_sim:
        report["image_simulation"] = simulate_image(args.image, key, iv, args.chunk_size, args.bank_size, args.limit_chunks)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.out_json}")
    print("self_test=ok")
    if "image_simulation" in report:
        sim = report["image_simulation"]
        print(
            "image_simulation="
            f"chunks={sim['chunks']} chunk_size={fmt_hex(sim['chunk_size'])} "
            f"bank_size={fmt_hex(sim['bank_size'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
