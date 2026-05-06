#!/usr/bin/env python3
"""Build a post-materializer multi-blob runtime RAM writer candidate.

No drive commands are sent by this script.

This is a second-stage companion to the bridge-clamp proof. The single-blob
writer is enough for one contiguous runtime edit. A real normal-mode response
hook is more likely to need at least two runtime writes in the same boot, for
example:

    * copy a small hook body into a materialized runtime code cave;
    * replace a hot function entry with an LCALL to that hook body.

The candidate generated here patches:

    0x422c: CLR A; MOV PSW,A  ->  LCALL 0x6ee3

The cave at 0x6ee3 runs after the visible resident materializer path returns.
It saves DPTR and bank-0 R0..R7, walks an embedded table of
`24-bit-address, length, bytes...` entries, writes each blob through the
controller public write gateway (`0x4095..0x4098`), restores saved state, and
exits with the stock `CLR A; MOV PSW,A; RET` epilogue.

Use this only after the smaller bridge-clamp ladder has proven that this
post-materializer hook can alter materialized normal runtime RAM and restore
cleanly.
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
        self.rel_fixups: list[tuple[int, str]] = []
        self.abs_fixups: list[tuple[int, str]] = []

    def emit(self, *values: int) -> None:
        self.code.extend(value & 0xFF for value in values)

    def label(self, name: str) -> None:
        if name in self.labels:
            raise ValueError(f"duplicate label: {name}")
        self.labels[name] = len(self.code)

    def ljmp(self, label: str) -> None:
        self.emit(0x02, 0x00, 0x00)
        self.abs_fixups.append((len(self.code) - 2, label))

    def lcall(self, label: str) -> None:
        self.emit(0x12, 0x00, 0x00)
        self.abs_fixups.append((len(self.code) - 2, label))

    def jb(self, bit_addr: int, label: str) -> None:
        self.emit(0x20, bit_addr)
        self.rel_fixups.append((len(self.code), label))
        self.emit(0x00)

    def djnz_r2(self, label: str) -> None:
        self.emit(0xDA)
        self.rel_fixups.append((len(self.code), label))
        self.emit(0x00)

    def djnz_r7(self, label: str) -> None:
        self.emit(0xDF)
        self.rel_fixups.append((len(self.code), label))
        self.emit(0x00)

    def cjne_r0_imm(self, value: int, label: str) -> None:
        self.emit(0xB8, value)
        self.rel_fixups.append((len(self.code), label))
        self.emit(0x00)

    def resolve(self, base_addr: int) -> bytes:
        for pos, label in self.rel_fixups:
            if label not in self.labels:
                raise ValueError(f"missing label: {label}")
            rel = self.labels[label] - (pos + 1)
            if not -128 <= rel <= 127:
                raise ValueError(f"relative branch to {label} out of range: {rel}")
            self.code[pos] = rel & 0xFF
        for pos, label in self.abs_fixups:
            if label not in self.labels:
                raise ValueError(f"missing label: {label}")
            absolute = base_addr + self.labels[label]
            if absolute > 0xFFFF:
                raise ValueError(f"absolute label {label} outside code address space")
            self.code[pos] = (absolute >> 8) & 0xFF
            self.code[pos + 1] = absolute & 0xFF
        return bytes(self.code)


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def compact_hex(value: str) -> str:
    return "".join(ch for ch in value if ch in "0123456789abcdefABCDEF")


def parse_patch(value: str) -> tuple[int, bytes]:
    try:
        address_text, data_text = value.split(":", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("patch must be ADDRESS:HEX") from exc
    address = parse_int(address_text)
    if address > 0xFFFFFF:
        raise argparse.ArgumentTypeError("patch address must be 24-bit")
    hex_text = compact_hex(data_text)
    if len(hex_text) % 2:
        raise argparse.ArgumentTypeError("patch hex must contain an even number of digits")
    blob = bytes.fromhex(hex_text)
    if not blob:
        raise argparse.ArgumentTypeError("patch blob must not be empty")
    if len(blob) > 0xFF:
        raise argparse.ArgumentTypeError("each patch blob must be <=255 bytes")
    return address, blob


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


def push_direct(addr: int) -> tuple[int, int]:
    return (0xC0, addr & 0xFF)


def pop_direct(addr: int) -> tuple[int, int]:
    return (0xD0, addr & 0xFF)


def build_table(patches: list[tuple[int, bytes]]) -> bytes:
    table = bytearray()
    for address, blob in patches:
        table.extend([(address >> 16) & 0xFF, (address >> 8) & 0xFF, address & 0xFF, len(blob)])
        table.extend(blob)
    return bytes(table)


def build_payload(patches: list[tuple[int, bytes]]) -> bytes:
    if not 1 <= len(patches) <= 0xFF:
        raise ValueError("patch count must be 1..255")

    asm = Asm8051()
    asm.ljmp("main")

    # Returns the next embedded table byte in A and advances R1:R0.
    asm.label("next_table_byte")
    asm.emit(0x85, 0x00, 0x82)  # MOV DPL,R0
    asm.emit(0x85, 0x01, 0x83)  # MOV DPH,R1
    asm.emit(0xE4, 0x93)  # CLR A; MOVC A,@A+DPTR
    asm.emit(0x08)  # INC R0
    asm.cjne_r0_imm(0x00, "next_done")
    asm.emit(0x09)  # INC R1
    asm.label("next_done")
    asm.emit(0x22)  # RET

    asm.label("main")
    asm.emit(*push_direct(0x83))  # DPH
    asm.emit(*push_direct(0x82))  # DPL
    for direct in range(8):
        asm.emit(*push_direct(direct))
    asm.emit(0x75, 0xD0, 0x00)  # MOV PSW,#0

    table_addr_pos = len(asm.code) + 1
    asm.emit(0x78, 0x00)  # MOV R0,#table-low (patched below)
    asm.emit(0x79, 0x00)  # MOV R1,#table-high (patched below)
    asm.emit(0x7F, len(patches))  # MOV R7,#entry-count

    asm.label("entry_loop")
    asm.lcall("next_table_byte")
    asm.emit(0xFC)  # MOV R4,A ; address high
    asm.lcall("next_table_byte")
    asm.emit(0xFD)  # MOV R5,A ; address mid
    asm.lcall("next_table_byte")
    asm.emit(0xFE)  # MOV R6,A ; address low
    asm.lcall("next_table_byte")
    asm.emit(0xFA)  # MOV R2,A ; length

    asm.label("wait_before_address")
    asm.emit(*mov_dptr(0x4000), 0xE0)  # MOVX A,@DPTR
    asm.jb(0xE7, "wait_before_address")  # while ACC.7

    asm.emit(*mov_dptr(0x4095))
    asm.emit(0xEC, 0xF0)  # MOV A,R4; MOVX @DPTR,A
    asm.emit(0xA3, 0xED, 0xF0)  # INC DPTR; MOV A,R5; MOVX @DPTR,A
    asm.emit(0xA3, 0xEE, 0xF0)  # INC DPTR; MOV A,R6; MOVX @DPTR,A

    asm.label("byte_loop")
    asm.lcall("next_table_byte")
    asm.emit(0xC0, 0xE0)  # PUSH ACC
    asm.label("wait_before_fifo")
    asm.emit(*mov_dptr(0x4000), 0xE0)
    asm.jb(0xE7, "wait_before_fifo")
    asm.emit(*mov_dptr(0x4098))
    asm.emit(0xD0, 0xE0)  # POP ACC
    asm.emit(0xF0)  # MOVX @DPTR,A
    asm.djnz_r2("byte_loop")
    asm.djnz_r7("entry_loop")

    for direct in reversed(range(8)):
        asm.emit(*pop_direct(direct))
    asm.emit(*pop_direct(0x82))  # DPL
    asm.emit(*pop_direct(0x83))  # DPH
    asm.emit(0xE4, 0xF5, 0xD0, 0x22)  # CLR A; MOV PSW,A; RET

    code = bytearray(asm.resolve(CAVE_ADDR))
    table_addr = CAVE_ADDR + len(code)
    if table_addr > 0xFFFF:
        raise ValueError("table address exceeds 8051 code address space")
    code[table_addr_pos] = table_addr & 0xFF
    code[table_addr_pos + 2] = (table_addr >> 8) & 0xFF
    payload = bytes(code) + build_table(patches)
    if len(payload) > CAVE_LEN:
        raise ValueError(
            f"payload plus table length {len(payload)} exceeds cave length {CAVE_LEN}; "
            f"payload={len(payload)} code={len(code)} table={len(payload)-len(code)}"
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


def write_note(
    out_dir: Path,
    name: str,
    restore_name: str,
    runtime_patches: list[tuple[int, bytes]],
    payload: bytes,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    note = out_dir / slugify(name) / "post-materializer-multi-blob-writer.md"
    lines = [
        "# Post-Materializer Multi-Blob Writer Candidate",
        "",
        "Offline generated only; no drive commands were sent by the builder.",
        "",
        f"- candidate: `{name}`",
        f"- restore: `{restore_name}`",
        f"- hook: `0x{HOOK_OFFSET:04x} -> LCALL 0x{CAVE_ADDR:04x}`",
        f"- runtime patch count: `{len(runtime_patches)}`",
        f"- cave payload+table length: `{len(payload)}` / `0x{CAVE_LEN:x}`",
        "",
        "| address | length | first bytes |",
        "|---:|---:|---|",
    ]
    for address, blob in runtime_patches:
        preview = blob[:16].hex(" ")
        suffix = "" if len(blob) <= 16 else " ..."
        lines.append(f"| `0x{address:06x}` | `{len(blob)}` | `{preview}{suffix}` |")
    lines.extend(
        [
            "",
            "Use this only after the smaller bridge-clamp proof has shown that the",
            "`0x422c` post-materializer hook can affect materialized normal runtime",
            "RAM and restore cleanly. This candidate is for multi-region runtime",
            "patches such as a cave body plus an entry-point trampoline; it is not",
            "a first proof step.",
            "",
        ]
    )
    note.write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-patch",
        action="append",
        type=parse_patch,
        required=True,
        metavar="ADDRESS:HEX",
        help="runtime/controller-public blob to write after materialization; repeatable",
    )
    parser.add_argument("--name")
    parser.add_argument("--out-dir", type=Path, default=OUT_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime_patches = list(args.runtime_patch)
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

    payload = build_payload(runtime_patches)
    base_name = args.name or f"post-materializer-multi-blob-{len(runtime_patches)}patch-{utc_stamp()}"
    name = slugify(base_name)
    restore_name = slugify(base_name + "-restore")

    run_builder(name, [(HOOK_OFFSET, lcall(CAVE_ADDR)), (CAVE_ADDR, payload)], args.out_dir, args.dry_run)
    run_builder(
        restore_name,
        [(HOOK_OFFSET, STOCK_HOOK_BYTES[:3]), (CAVE_ADDR, b"\xff" * len(payload))],
        args.out_dir,
        args.dry_run,
    )
    write_note(args.out_dir, name, restore_name, runtime_patches, payload, args.dry_run)
    print(
        json.dumps(
            {
                "candidate": name,
                "restore": restore_name,
                "patch_count": len(runtime_patches),
                "runtime_patches": [
                    {"address": f"0x{address:06x}", "blob_len": len(blob)}
                    for address, blob in runtime_patches
                ],
                "payload_len": len(payload),
                "payload_room_remaining": CAVE_LEN - len(payload),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
