#!/usr/bin/env python3
"""Parse LiteOn/PLDS EXTRAINQ responses from raw bytes, hex, or mmcctl logs."""

from __future__ import annotations

import argparse
import binascii
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


HEX_LINE_RE = re.compile(r"^[0-9a-fA-F]{8}\s+((?:[0-9a-fA-F]{2}\s+){1,16})")


def parse_hex_or_file(raw: str) -> bytes:
    compact = "".join(ch for ch in raw if ch in "0123456789abcdefABCDEF")
    compact_no_ws = "".join(raw.split())
    if compact and compact == compact_no_ws:
        if len(compact) % 2:
            raise ValueError("hex input has an odd number of digits")
        return bytes.fromhex(compact)

    path = Path(raw)
    if path.exists():
        data = path.read_bytes()
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return data
        hexdump = bytearray()
        for line in text.splitlines():
            match = HEX_LINE_RE.match(line)
            if not match:
                continue
            for item in match.group(1).split():
                hexdump.append(int(item, 16))
        if hexdump:
            return bytes(hexdump)
        compact_text = "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")
        if compact_text and compact_text == "".join(text.split()):
            if len(compact_text) % 2:
                raise ValueError("hex file has an odd number of digits")
            return bytes.fromhex(compact_text)
        return data

    if len(compact) % 2:
        raise ValueError("hex input has an odd number of digits")
    return bytes.fromhex(compact)


def ascii_field(data: bytes) -> str:
    return data.decode("ascii", errors="replace").strip()


def derive_iv_key(response: bytes) -> tuple[bytes, bytes, int, int]:
    if len(response) < 0x80:
        raise ValueError("EXTRAINQ response must be at least 128 bytes")
    key_selector = response[0x73]
    key_off = 0x74 + key_selector * 8
    key = response[key_off : key_off + 16]
    if len(key) != 16:
        raise ValueError(
            f"SecKey slice needs bytes 0x{key_off:x}..0x{key_off + 15:x}; "
            f"response only has {len(response)} bytes"
        )
    return response[0x10:0x20], key, key_selector, key_off


def aes_cbc_crypt(data: bytes, key: bytes, iv: bytes, *, decrypt: bool) -> bytes:
    n = len(data) & ~0xF
    tail = data[n:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    ctx = cipher.decryptor() if decrypt else cipher.encryptor()
    return ctx.update(data[:n]) + ctx.finalize() + tail


def describe_flags(base: bytes) -> dict[str, int]:
    feature = base[0x10]
    aes = base[0x12]
    flags = {
        "bEconomyFlash": 1 if (feature & 0x03) == 1 else 0,
        "bNotSendProfile": (feature >> 2) & 1,
        "bDummyProfile": (feature >> 3) & 1,
        "bDescending": feature & 0x10,
        "bAES": 1 if ((aes & 0x0F) == 1 or ((aes & 0x0F) >= 2 and (aes & 0x80))) else 0,
    }
    return flags


def print_extrainq(response: bytes) -> tuple[bytes, bytes]:
    marker = response.find(b"EXTRAINQ")
    if marker < 0:
        marker = response.find(b"LITEONIT")
    if marker < 0:
        raise ValueError("could not find EXTRAINQ/LITEONIT marker in response")
    if len(response) < marker + 0x14:
        raise ValueError("response is truncated before the EXTRAINQ flag area")

    base = response[marker:]
    profile_len = int.from_bytes(base[0x08:0x0A], "big")
    profile_word = int.from_bytes(base[0x0A:0x0C], "big")
    selector_read_1d38 = base[0x0A]
    selector_read_1d39 = base[0x0B]
    primary_selector_value = (selector_read_1d38 + selector_read_1d39) & 0x07
    iaes_bank = None
    if len(base) > 0x0F and base[0x0F] > 8:
        iaes_bank = (base[0x0A] + base[0x0B]) % 8

    iv, key, key_selector, key_off = derive_iv_key(response)

    print(f"response_len={len(response)}")
    print(f"peripheral=0x{response[0]:02x} removable={response[1] >> 7}")
    print(f"vendor={ascii_field(response[0x08:0x10])!r}")
    print(f"product={ascii_field(response[0x10:0x20])!r}")
    print(f"revision={ascii_field(response[0x20:0x24])!r}")
    print(f"timestamp={ascii_field(response[0x24:0x34])!r}")
    print(f"marker_offset=0x{marker:x} marker={base[:8].decode('ascii', errors='replace')!r}")
    print(f"profile_len=0x{profile_len:04x} profile_word=0x{profile_word:04x}")
    print(
        "primary_selector_compare_bytes="
        f"0x{selector_read_1d38:02x} 0x{selector_read_1d39:02x} "
        "(controller 0x1d38/0x1d39)"
    )
    print(f"primary_selector_value={primary_selector_value}")
    print(f"feature_byte=0x{base[0x10]:02x} aes_byte=0x{base[0x12]:02x}")
    for name, value in describe_flags(base).items():
        print(f"{name}={value}")
    if iaes_bank is not None:
        print(f"iAESBank={iaes_bank}")
    print(f"key_selector={key_selector} key_offset=0x{key_off:x}")
    print(f"InitVec={iv.hex()} ascii={ascii_field(iv)!r}")
    print(f"SecKey={key.hex()} ascii={ascii_field(key)!r}")
    return iv, key


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("response", help="EXTRAINQ response as file path, mmcctl detail log, or hex string")
    ap.add_argument(
        "--read-buffer",
        help="Optional READ BUFFER capture to AES-CBC decrypt using the EXTRAINQ key",
    )
    args = ap.parse_args()

    response = parse_hex_or_file(args.response)
    iv, key = print_extrainq(response)

    if args.read_buffer:
        encrypted = parse_hex_or_file(args.read_buffer)
        decrypted = aes_cbc_crypt(encrypted, key, iv, decrypt=True)
        zero = all(b == 0 for b in decrypted)
        printable = sum(32 <= b < 127 or b in (9, 10, 13) for b in decrypted)
        print(f"read_buffer_len={len(encrypted)}")
        print(f"read_buffer_aes_cbc_decrypt_all_zero={int(zero)}")
        print(f"read_buffer_decrypted_printable={printable}/{len(decrypted)}")
        print(f"read_buffer_decrypted_first64={decrypted[:64].hex()}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, binascii.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
