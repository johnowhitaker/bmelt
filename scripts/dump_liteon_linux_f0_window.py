#!/usr/bin/env python3
"""Dump and AES-decrypt a LiteOn/PLDS READ BUFFER id F0 window on Linux."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import parse_liteon_extrainq


EXTRAINQ_CDB = [0x12, 0x00, 0x00, 0x00, 0xF0, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]


def read_buffer_cdb(buffer_id: int, offset: int, length: int) -> list[int]:
    return [
        0x3C,
        0x01,
        buffer_id & 0xFF,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
        (length >> 16) & 0xFF,
        (length >> 8) & 0xFF,
        length & 0xFF,
        0x00,
    ]


def aes_cbc_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    if len(data) % 16:
        raise ValueError("encrypted chunk length must be a multiple of 16")
    ctx = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    return ctx.update(data) + ctx.finalize()


def aes_cbc_decrypt_reset_window(data: bytes, key: bytes, iv: bytes, reset: int) -> bytes:
    if reset <= 0 or reset % 16:
        raise ValueError("crypto reset interval must be a positive multiple of 16")
    if len(data) % 16:
        raise ValueError("encrypted window length must be a multiple of 16")
    out = bytearray()
    for offset in range(0, len(data), reset):
        out.extend(aes_cbc_decrypt(data[offset : offset + reset], key, iv))
    return bytes(out)


def run_read(
    *,
    sg_raw: str,
    device: str,
    cmdset: int | None,
    cdb: list[int],
    length: int,
    timeout: int,
    require_good_status: bool = True,
) -> bytes:
    cmd = [sg_raw]
    if cmdset is not None:
        cmd.append(f"--cmdset={cmdset}")
    cmd.extend(["-b", "--request", str(length), "--timeout", str(timeout)])
    cmd.extend([device, *[f"{byte:02x}" for byte in cdb]])
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stderr = proc.stderr.decode("utf-8", errors="replace")
    if proc.returncode != 0 or len(proc.stdout) != length:
        cdb_text = " ".join(f"{byte:02X}" for byte in cdb)
        raise RuntimeError(
            f"READ BUFFER failed rc={proc.returncode} got={len(proc.stdout)} "
            f"expected={length} cdb={cdb_text}\n{stderr}"
        )
    if require_good_status and "SCSI Status: Good" not in stderr:
        cdb_text = " ".join(f"{byte:02X}" for byte in cdb)
        raise RuntimeError(f"READ BUFFER missing GOOD status cdb={cdb_text}\n{stderr}")
    return proc.stdout


def dump_raw(args: argparse.Namespace) -> bytes:
    out = bytearray()
    end = args.start + args.size
    offset = args.start
    while offset < end:
        length = min(args.chunk, end - offset)
        cdb = read_buffer_cdb(args.buffer_id, offset, length)
        last_error: Exception | None = None
        for attempt in range(args.retries + 1):
            try:
                out.extend(
                    run_read(
                        sg_raw=args.sg_raw,
                        device=args.device,
                        cmdset=args.cmdset,
                        cdb=cdb,
                        length=length,
                        timeout=args.timeout,
                    )
                )
                break
            except RuntimeError as exc:
                last_error = exc
                if attempt >= args.retries:
                    raise
        offset += length
        done = offset - args.start
        if done == args.size or done % args.progress_interval == 0:
            print(f"offset=0x{offset:06x} done={done}/{args.size}", flush=True)
    return bytes(out)


def maybe_prime_extrainq(args: argparse.Namespace) -> None:
    if not args.prime_extrainq:
        return
    live = run_read(
        sg_raw=args.sg_raw,
        device=args.device,
        cmdset=args.cmdset,
        cdb=EXTRAINQ_CDB,
        length=0xB0,
        timeout=args.timeout,
        require_good_status=False,
    )
    print(f"primed EXTRAINQ len={len(live)} sha256={hashlib.sha256(live).hexdigest()}")
    if args.prime_extrainq_out:
        args.prime_extrainq_out.parent.mkdir(parents=True, exist_ok=True)
        args.prime_extrainq_out.write_bytes(live)
        print(f"wrote live EXTRAINQ {args.prime_extrainq_out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=shutil.which("sg_raw") or "sg_raw")
    parser.add_argument(
        "--cmdset",
        type=lambda value: None if value.lower() == "none" else int(value, 0),
        default=1,
        help="sg_raw command set value; use 'none' to omit --cmdset",
    )
    parser.add_argument("--extrainq", required=True, help="EXTRAINQ response as log/file/hex")
    parser.add_argument("--out", type=Path, required=True, help="decrypted output path")
    parser.add_argument("--raw-out", type=Path, help="encrypted output path")
    parser.add_argument("--buffer-id", type=lambda value: int(value, 0), default=0xF0)
    parser.add_argument("--start", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--size", type=lambda value: int(value, 0), default=0x10000)
    parser.add_argument("--chunk", type=lambda value: int(value, 0), default=0x80)
    parser.add_argument("--crypto-reset", type=lambda value: int(value, 0), default=0x80)
    parser.add_argument(
        "--prime-extrainq",
        action="store_true",
        help="send a live EXTRAINQ read before READ BUFFER; useful after currentboot/finalizer transitions",
    )
    parser.add_argument("--prime-extrainq-out", type=Path, help="optional path to save the live EXTRAINQ response")
    parser.add_argument("--timeout", type=int, default=3)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--progress-interval", type=lambda value: int(value, 0), default=0x10000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.chunk <= 0 or args.chunk > 0x80 or args.chunk % 16:
        raise ValueError("--chunk must be a positive 16-byte multiple no larger than 0x80")
    if args.crypto_reset <= 0 or args.crypto_reset % 16:
        raise ValueError("--crypto-reset must be a positive 16-byte multiple")
    if args.start % args.crypto_reset:
        raise ValueError("--start must be aligned to --crypto-reset")
    if args.size <= 0 or args.size % 16:
        raise ValueError("--size must be a positive 16-byte multiple")
    if args.progress_interval <= 0:
        raise ValueError("--progress-interval must be positive")

    response = parse_liteon_extrainq.parse_hex_or_file(args.extrainq)
    iv, key, _, _ = parse_liteon_extrainq.derive_iv_key(response)

    maybe_prime_extrainq(args)
    raw = dump_raw(args)
    decrypted = aes_cbc_decrypt_reset_window(raw, key, iv, args.crypto_reset)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(decrypted)
    print(f"wrote decrypted {args.out} len={len(decrypted)} sha256={hashlib.sha256(decrypted).hexdigest()}")

    if args.raw_out:
        args.raw_out.parent.mkdir(parents=True, exist_ok=True)
        args.raw_out.write_bytes(raw)
        print(f"wrote encrypted {args.raw_out} len={len(raw)} sha256={hashlib.sha256(raw).hexdigest()}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
