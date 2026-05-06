#!/usr/bin/env python3
"""Build a post-materializer runtime RAM blob-writer candidate.

No drive commands are sent by this script.

This is a second-stage companion to the bridge-clamp proof. The bridge-clamp
candidate proves that the visible resident hook at 0x422c can alter decoded
normal runtime RAM. If that proof lands, the next useful primitive is not more
single-byte unrolled writes; it is a compact way to copy a small contiguous
patch into the materialized runtime.

The candidate generated here patches:

    0x422c: CLR A; MOV PSW,A  ->  LCALL 0x6ee3

The cave at 0x6ee3:

    * saves DPTR and bank-0 R0/R1/R7;
    * sets the 24-bit controller write address via 0x4095..0x4097;
    * streams an embedded code-table to 0x4098;
    * restores the saved registers;
    * executes the stock epilogue shape: CLR A; MOV PSW,A; RET.

The stock RET at 0x422f remains in place. The cave RET returns to 0x422f, and
the original function returns normally from there.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "references/firmware/extracted"
BASE_IMAGE = EXTRACTED / "ld5m-f0-window-0x00000-0x100000.bin"
OUT_ROOT = EXTRACTED / "helper-bypass-candidates"
BUILD_HELPER = ROOT / "scripts/build_liteon_helper_bypass_candidate.py"

CAVE_ADDR = 0x6EE3
CAVE_LEN = 0xDD
HOOK_OFFSET = 0x422C
STOCK_HOOK_BYTES = bytes.fromhex("e4 f5 d0 22")


class Asm8051:
    def __init__(self) -> None:
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.code.extend(value & 0xFF for value in values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.code)

    def jb(self, bit_addr: int, label: str) -> None:
        self.emit(0x20, bit_addr)
        self.fixups.append((len(self.code), label))
        self.emit(0x00)

    def djnz_r7(self, label: str) -> None:
        self.emit(0xDF)
        self.fixups.append((len(self.code), label))
        self.emit(0x00)

    def cjne_r0_imm(self, value: int, label: str) -> None:
        self.emit(0xB8, value)
        self.fixups.append((len(self.code), label))
        self.emit(0x00)

    def resolve(self) -> bytes:
        for pos, label in self.fixups:
            if label not in self.labels:
                raise ValueError(f"missing label: {label}")
            rel = self.labels[label] - (pos + 1)
            if not -128 <= rel <= 127:
                raise ValueError(f"relative branch to {label} out of range: {rel}")
            self.code[pos] = rel & 0xFF
        return bytes(self.code)


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def compact_hex(value: str) -> str:
    return "".join(ch for ch in value if ch in "0123456789abcdefABCDEF")


def parse_blob(args: argparse.Namespace) -> bytes:
    if args.hex is not None and args.file is not None:
        raise ValueError("use only one of --hex or --file")
    if args.hex is None and args.file is None:
        raise ValueError("one of --hex or --file is required")
    if args.hex is not None:
        text = compact_hex(args.hex)
        if len(text) % 2:
            raise ValueError("--hex must contain an even number of hex digits")
        return bytes.fromhex(text)
    return args.file.read_bytes()


def slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    slug = "-".join(part for part in slug.split("-") if part)
    if not slug:
        raise ValueError("empty slug")
    return slug


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def lcall(addr: int) -> bytes:
    return bytes([0x12, (addr >> 8) & 0xFF, addr & 0xFF])


def mov_dptr(addr: int) -> tuple[int, int, int]:
    return (0x90, (addr >> 8) & 0xFF, addr & 0xFF)


def mov_a_imm(value: int) -> tuple[int, int]:
    return (0x74, value & 0xFF)


def build_payload(address: int, blob: bytes) -> bytes:
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError("--address must be a 24-bit controller/public address")
    if not 1 <= len(blob) <= 0xFF:
        raise ValueError("blob length must be 1..255 bytes")

    asm = Asm8051()

    # Save the state we intentionally disturb. Stock return state still forces
    # A=0 and PSW=0, so ACC/PSW do not need to be preserved.
    asm.emit(0xC0, 0x83)  # PUSH DPH
    asm.emit(0xC0, 0x82)  # PUSH DPL
    asm.emit(0xC0, 0x00)  # PUSH bank-0 R0
    asm.emit(0xC0, 0x01)  # PUSH bank-0 R1
    asm.emit(0xC0, 0x07)  # PUSH bank-0 R7
    asm.emit(0x75, 0xD0, 0x00)  # MOV PSW,#0

    asm.label("wait_before_address")
    asm.emit(*mov_dptr(0x4000), 0xE0)  # MOVX A,@DPTR
    asm.jb(0xE7, "wait_before_address")  # while ACC.7

    asm.emit(*mov_dptr(0x4095))
    asm.emit(*mov_a_imm((address >> 16) & 0xFF), 0xF0)
    asm.emit(0xA3, *mov_a_imm((address >> 8) & 0xFF), 0xF0)
    asm.emit(0xA3, *mov_a_imm(address & 0xFF), 0xF0)

    table_addr_pos = len(asm.code) + 1
    asm.emit(0x78, 0x00)  # MOV R0,#table-low (patched below)
    asm.emit(0x79, 0x00)  # MOV R1,#table-high (patched below)
    asm.emit(0x7F, len(blob))  # MOV R7,#len

    asm.label("loop")
    asm.emit(0x85, 0x00, 0x82)  # MOV DPL,R0
    asm.emit(0x85, 0x01, 0x83)  # MOV DPH,R1
    asm.emit(0xE4, 0x93)  # CLR A; MOVC A,@A+DPTR
    asm.emit(0xC0, 0xE0)  # PUSH ACC
    asm.emit(0x08)  # INC R0
    asm.cjne_r0_imm(0x00, "no_table_carry")
    asm.emit(0x09)  # INC R1
    asm.label("no_table_carry")
    asm.label("wait_before_fifo")
    asm.emit(*mov_dptr(0x4000), 0xE0)
    asm.jb(0xE7, "wait_before_fifo")
    asm.emit(*mov_dptr(0x4098))
    asm.emit(0xD0, 0xE0)  # POP ACC
    asm.emit(0xF0)  # MOVX @DPTR,A
    asm.djnz_r7("loop")

    asm.emit(0xD0, 0x07)  # POP bank-0 R7
    asm.emit(0xD0, 0x01)  # POP bank-0 R1
    asm.emit(0xD0, 0x00)  # POP bank-0 R0
    asm.emit(0xD0, 0x82)  # POP DPL
    asm.emit(0xD0, 0x83)  # POP DPH
    asm.emit(0xE4, 0xF5, 0xD0, 0x22)  # CLR A; MOV PSW,A; RET

    code = bytearray(asm.resolve())
    table_addr = CAVE_ADDR + len(code)
    if table_addr > 0xFFFF:
        raise ValueError("table address exceeds 8051 code address space")
    code[table_addr_pos] = table_addr & 0xFF
    code[table_addr_pos + 2] = (table_addr >> 8) & 0xFF
    payload = bytes(code) + blob
    if len(payload) > CAVE_LEN:
        raise ValueError(
            f"payload plus table length {len(payload)} exceeds cave length {CAVE_LEN}; "
            f"max blob for this routine is {CAVE_LEN - len(code)} bytes"
        )
    return payload


def patch_arg(offset: int, data: bytes) -> str:
    return f"0x{offset:x}:{data.hex()}"


def run_builder(name: str, patches: list[tuple[int, bytes]], out_dir: Path, dry_run: bool) -> None:
    cmd = [
        sys.executable,
        str(BUILD_HELPER),
        "--name",
        name,
        "--out-dir",
        str(out_dir),
        "--auto-helper-range",
        "--include-pre-tail",
    ]
    for offset, data in patches:
        cmd.extend(["--patch", patch_arg(offset, data)])
    print("+ " + " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, cwd=ROOT, check=True)


def write_note(out_dir: Path, name: str, restore_name: str, address: int, blob: bytes, payload: bytes, dry_run: bool) -> None:
    if dry_run:
        return
    note = out_dir / slugify(name) / "post-materializer-blob-writer.md"
    lines = [
        "# Post-Materializer Blob Writer Candidate",
        "",
        "Offline generated only; no drive commands were sent by the builder.",
        "",
        f"- candidate: `{name}`",
        f"- restore: `{restore_name}`",
        f"- hook: `0x{HOOK_OFFSET:04x} -> LCALL 0x{CAVE_ADDR:04x}`",
        f"- controller/public write address: `0x{address:06x}`",
        f"- blob length: `{len(blob)}`",
        f"- cave payload+table length: `{len(payload)}` / `0x{CAVE_LEN:x}`",
        "",
        "Use this only after the smaller bridge-clamp proof has shown that the",
        "`0x422c` post-materializer hook can affect materialized normal runtime",
        "RAM and restore cleanly. This candidate is for contiguous RAM patches;",
        "it is not a first proof step.",
        "",
    ]
    note.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--hex")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--name")
    parser.add_argument("--out-dir", type=Path, default=OUT_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    blob = parse_blob(args)
    base = BASE_IMAGE.read_bytes()
    actual_hook = base[HOOK_OFFSET : HOOK_OFFSET + len(STOCK_HOOK_BYTES)]
    if actual_hook != STOCK_HOOK_BYTES:
        raise ValueError(
            f"stock hook bytes mismatch at 0x{HOOK_OFFSET:04x}: "
            f"expected {STOCK_HOOK_BYTES.hex()}, got {actual_hook.hex()}"
        )
    cave = base[CAVE_ADDR : CAVE_ADDR + CAVE_LEN]
    if cave != b"\xff" * CAVE_LEN:
        raise ValueError(f"cave 0x{CAVE_ADDR:04x}..0x{CAVE_ADDR + CAVE_LEN:04x} is not all FF")

    payload = build_payload(args.address, blob)
    base_name = args.name or f"post-materializer-blob-{args.address:06x}-{len(blob)}b-{utc_stamp()}"
    name = slugify(base_name)
    restore_name = slugify(base_name + "-restore")

    run_builder(name, [(HOOK_OFFSET, lcall(CAVE_ADDR)), (CAVE_ADDR, payload)], args.out_dir, args.dry_run)
    run_builder(
        restore_name,
        [(HOOK_OFFSET, STOCK_HOOK_BYTES[:3]), (CAVE_ADDR, b"\xff" * len(payload))],
        args.out_dir,
        args.dry_run,
    )
    write_note(args.out_dir, name, restore_name, args.address, blob, payload, args.dry_run)
    print(
        json.dumps(
            {
            "candidate": name,
            "restore": restore_name,
            "address": f"0x{args.address:06x}",
            "blob_len": len(blob),
            "payload_len": len(payload),
            "max_blob_len": len(blob) + (CAVE_LEN - len(payload)),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
