#!/usr/bin/env python3
"""Build currentboot INQUIRY/EXTRAINQ response hook candidates.

The currentboot identity path reaches the visible 8051 handler at 0x4ec6.
This builder hooks the final response-copy call at 0x4fc9, writes one byte into
the response staging buffer, then executes the original 0x6206 copy.

No drive commands are sent by this script.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "references/firmware/extracted"
DEFAULT_BASE_IMAGE = EXTRACTED / "ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_OUT_DIR = EXTRACTED / "currentboot-response-hook-candidates"
DEFAULT_HOOK_ADDR = 0x4FC9
DEFAULT_CAVE_ADDR = 0x6EE3
RESPONSE_STORAGE_BASE = 0x0220


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-").lower()
    if not slug:
        raise argparse.ArgumentTypeError("name must contain at least one safe character")
    return slug


def parse_addr(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFFFF:
        raise argparse.ArgumentTypeError("address must be 0..0xffff")
    return parsed


def parse_byte(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("value must be 0..0xff")
    return parsed


def parse_positive_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def patch_arg(offset: int, data: bytes) -> str:
    return f"0x{offset:x}:{data.hex()}"


def ljmp(addr: int) -> bytes:
    return bytes([0x02, (addr >> 8) & 0xFF, addr & 0xFF])


def lcall(addr: int) -> bytes:
    return bytes([0x12, (addr >> 8) & 0xFF, addr & 0xFF])


def mov_dptr(addr: int) -> bytes:
    return bytes([0x90, (addr >> 8) & 0xFF, addr & 0xFF])


def mov_rn_imm(register: int, value: int) -> bytes:
    if not 0 <= register <= 7:
        raise ValueError("register must be R0..R7")
    return bytes([0x78 + register, value & 0xFF])


def source_constant(value: int) -> bytes:
    return mov_rn_imm(5, value)


def source_xdata_direct(addr: int) -> bytes:
    return mov_dptr(addr) + bytes([0xE0, 0xFD])


def source_xdata_window(base: int, selector_mask: int) -> bytes:
    low = base & 0xFF
    high = (base >> 8) & 0xFF
    return b"".join(
        [
            mov_dptr(0x818F),  # CDB byte 5; stock accepts 0x40..0x7f.
            bytes([0xE0]),  # MOVX A,@DPTR
            bytes([0x54, selector_mask & 0xFF]),  # ANL A,#mask
            bytes([0x24, low]),  # ADD A,#base_low
            bytes([0xF5, 0x82]),  # MOV DPL,A
            bytes([0x74, high]),  # MOV A,#base_high
            bytes([0x34, 0x00]),  # ADDC A,#0
            bytes([0xF5, 0x83]),  # MOV DPH,A
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
        ]
    )


def source_xdata_cdb_address(selector_mask: int) -> bytes:
    return b"".join(
        [
            mov_dptr(0x818F),  # CDB byte 5: selector in low bits.
            bytes([0xE0, 0x54, selector_mask & 0xFF, 0xFC]),  # MOVX; ANL; MOV R4,A
            mov_dptr(0x8192),  # CDB byte 8: low base-address byte.
            bytes([0xE0, 0x2C, 0xFF]),  # MOVX; ADD A,R4; MOV R7,A
            mov_dptr(0x8191),  # CDB byte 7: high base-address byte.
            bytes([0xE0, 0x34, 0x00, 0xF5, 0x83]),  # MOVX; ADDC A,#0; MOV DPH,A
            bytes([0x8F, 0x82]),  # MOV DPL,R7
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
        ]
    )


def xdata_cdb_address_to_r6_r7(selector_mask: int) -> bytes:
    return b"".join(
        [
            mov_dptr(0x818F),  # CDB byte 5: selector in low bits.
            bytes([0xE0, 0x54, selector_mask & 0xFF, 0xFC]),  # MOVX; ANL; MOV R4,A
            mov_dptr(0x8192),  # CDB byte 8: low base-address byte.
            bytes([0xE0, 0x2C, 0xFF]),  # MOVX; ADD A,R4; MOV R7,A
            mov_dptr(0x8191),  # CDB byte 7: high base-address byte.
            bytes([0xE0, 0x34, 0x00, 0xFE]),  # MOVX; ADDC A,#0; MOV R6,A
        ]
    )


def rel8(from_next: int, target: int) -> int:
    return (target - from_next) & 0xFF


def source_xdata_cdb_bulk(selector_mask: int, storage_offset: int, bulk_len: int) -> bytes:
    if not 1 <= bulk_len <= 0xFF:
        raise ValueError("--bulk-len must be 1..255")
    if not 0 <= storage_offset <= 0xFFFF:
        raise ValueError("response storage offset is outside 16-bit range")

    compute = xdata_cdb_address_to_r6_r7(selector_mask)
    init = b"".join(
        [
            bytes([0xEE, 0xFA, 0xEF, 0xFB]),  # R2:R3 = source XDATA pointer from R6:R7.
            mov_rn_imm(6, (storage_offset >> 8) & 0xFF),  # R6:R7 = response-buffer offset.
            mov_rn_imm(7, storage_offset & 0xFF),
            mov_rn_imm(1, bulk_len),  # R1 = byte count.
        ]
    )
    loop_start = len(compute) + len(init)
    loop_body = bytes.fromhex(
        "8a838b82e0fd"  # MOV DPH,R2 ; MOV DPL,R3 ; MOVX A,@DPTR ; MOV R5,A
        "126012"  # LCALL 0x6012, stock response-byte writer.
        "0beb70010a"  # source++ in R2:R3
        "0fef70010e"  # response offset++ in R6:R7
    )
    djnz_pos = loop_start + len(loop_body)
    djnz = bytes([0xD9, rel8(djnz_pos + 2, loop_start)])  # DJNZ R1,loop_start
    return compute + init + loop_body + djnz


def source_xdata_cdb_rw(selector_mask: int) -> bytes:
    compute = xdata_cdb_address_to_r6_r7(selector_mask)
    read_back = bytes.fromhex("8e838f82e0fd")
    write_block = b"".join(
        [
            mov_dptr(0x8193),  # CDB byte 9: write value.
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
            bytes([0x8E, 0x83, 0x8F, 0x82]),  # MOV DPH,R6 ; MOV DPL,R7
            bytes([0xED, 0xF0]),  # MOV A,R5 ; MOVX @DPTR,A
        ]
    )
    guard = b"".join(
        [
            mov_dptr(0x8194),  # CDB byte 10: magic 0xa5.
            bytes([0xE0, 0x64, 0xA5]),
            bytes([0x70, len(write_block) + 8]),  # JNZ read_back
            mov_dptr(0x8195),  # CDB byte 11: magic 0x5a.
            bytes([0xE0, 0x64, 0x5A]),
            bytes([0x70, len(write_block)]),  # JNZ read_back
        ]
    )
    return compute + guard + write_block + read_back


def source_gateway_cdb_address(selector_mask: int) -> bytes:
    wait_ready = bytes.fromhex("904000e020e7f9")
    return b"".join(
        [
            mov_dptr(0x818F),  # CDB byte 5: selector in low bits.
            bytes([0xE0, 0x54, selector_mask & 0xFF, 0xFC]),  # MOVX; ANL; MOV R4,A
            mov_dptr(0x8193),  # CDB byte 9: low address byte.
            bytes([0xE0, 0x2C, 0xFF]),  # MOVX; ADD A,R4; MOV R7,A
            mov_dptr(0x8192),  # CDB byte 8: middle address byte.
            bytes([0xE0, 0x34, 0x00, 0xFE]),  # MOVX; ADDC A,#0; MOV R6,A
            mov_dptr(0x8191),  # CDB byte 7: high address byte.
            bytes([0xE0, 0x34, 0x00, 0xFD]),  # MOVX; ADDC A,#0; MOV R5,A
            wait_ready,
            mov_dptr(0x4091),
            bytes([0xED, 0xF0, 0xA3, 0xEE, 0xF0, 0xA3, 0xEF, 0xF0]),
            mov_dptr(0x4098),
            bytes([0xE0]),  # Stock 0x6239 does this throwaway read before waiting for data.
            wait_ready,
            mov_dptr(0x4098),
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
        ]
    )


def source_gateway_cdb_bulk(selector_mask: int, storage_offset: int, bulk_len: int) -> bytes:
    if not 1 <= bulk_len <= 0xFF:
        raise ValueError("--bulk-len must be 1..255")
    if not 0 <= storage_offset <= 0xFFFF:
        raise ValueError("response storage offset is outside 16-bit range")
    wait_ready = bytes.fromhex("904000e020e7f9")
    compute = b"".join(
        [
            mov_dptr(0x818F),  # CDB byte 5: selector in low bits.
            bytes([0xE0, 0x54, selector_mask & 0xFF, 0xFC]),  # MOVX; ANL; MOV R4,A
            mov_dptr(0x8193),  # CDB byte 9: low address byte.
            bytes([0xE0, 0x2C, 0xFB]),  # MOVX; ADD A,R4; MOV R3,A
            mov_dptr(0x8192),  # CDB byte 8: middle address byte.
            bytes([0xE0, 0x34, 0x00, 0xFA]),  # MOVX; ADDC A,#0; MOV R2,A
            mov_dptr(0x8191),  # CDB byte 7: high address byte.
            bytes([0xE0, 0x34, 0x00, 0xF8]),  # MOVX; ADDC A,#0; MOV R0,A
        ]
    )
    init = b"".join(
        [
            mov_rn_imm(6, (storage_offset >> 8) & 0xFF),  # R6:R7 = response-buffer offset.
            mov_rn_imm(7, storage_offset & 0xFF),
            mov_rn_imm(1, bulk_len),  # R1 = byte count.
        ]
    )
    setup_gateway_addr = b"".join(
        [
            wait_ready,
            mov_dptr(0x4091),
            bytes([0xE8, 0xF0, 0xA3, 0xEA, 0xF0, 0xA3, 0xEB, 0xF0]),
            mov_dptr(0x4098),
            bytes([0xE0]),  # throwaway read, matching the stock gateway read quirk.
            wait_ready,
            mov_dptr(0x4098),
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
            lcall(0x6012),
        ]
    )
    increment_gateway_addr = bytes.fromhex("0beb70050aea700108")
    increment_response_offset = bytes.fromhex("0fef70010e")
    loop_start = len(compute) + len(init)
    loop_body = setup_gateway_addr + increment_gateway_addr + increment_response_offset
    djnz_pos = loop_start + len(loop_body)
    djnz = bytes([0xD9, rel8(djnz_pos + 2, loop_start)])  # DJNZ R1,loop_start
    return compute + init + loop_body + djnz


def source_gateway_cdb_bulk_with_xdata_write(selector_mask: int, storage_offset: int, bulk_len: int) -> bytes:
    """Gateway bulk read with an optional guarded XDATA write mode.

    Normal mode matches source_gateway_cdb_bulk(): CDB[7:9] is a 24-bit
    controller address. The stock currentboot CDB shadow stores the two guard
    bytes in reverse order at 0x8194/0x8195, so the host sends CDB[10:11] as
    a5/5a for this write mode. The hook writes CDB[9] to XDATA address
    CDB[7:8] + selector and returns the readback byte in R5. build_payload's
    standard response-byte write exposes that readback at response[0x20].
    """

    checks = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8194, 0x5A), (0x8195, 0xA5)):
        checks.extend(mov_dptr(cdb_addr))
        checks.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(checks) - 1)

    write_block = b"".join(
        [
            xdata_cdb_address_to_r6_r7(selector_mask),
            mov_dptr(0x8193),  # CDB byte 9: write value.
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
            bytes([0x8E, 0x83, 0x8F, 0x82]),  # MOV DPH,R6 ; MOV DPL,R7
            bytes([0xED, 0xF0]),  # MOV A,R5 ; MOVX @DPTR,A
            bytes([0x8E, 0x83, 0x8F, 0x82]),  # MOV DPH,R6 ; MOV DPL,R7
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
        ]
    )

    source = bytearray(checks)
    source.extend(write_block)
    skip_gateway_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_gateway_pos + 1] = rel8(skip_gateway_pos + 2, end_source)
    return bytes(source)


def source_gateway_cdb_bulk_with_xdata_rw(selector_mask: int, storage_offset: int, bulk_len: int) -> bytes:
    """Gateway bulk read with optional guarded XDATA read/write modes.

    Normal mode matches source_gateway_cdb_bulk(): CDB[7:9] is a 24-bit
    controller address when CDB[10:11] are both zero. Host CDB[10] 0xa5
    selects XDATA write; host CDB[10] 0x5a selects XDATA read. CDB[11] is
    ignored for the read/write selectors because byte 11 proved easier to get
    wrong than useful. Unknown nonzero selector values return 0xee instead of
    falling through into a controller-gateway read at an unintended address.
    build_payload exposes R5 at response[0x20].
    """

    source = bytearray()

    source.extend(mov_dptr(0x8194))  # CDB byte 10: mode selector.
    source.extend(bytes([0xE0, 0x64, 0x5A, 0x70, 0x00]))  # MOVX; XRL; JNZ write_check
    jump_to_write_check_pos = len(source) - 1

    read_block = b"".join(
        [
            xdata_cdb_address_to_r6_r7(selector_mask),
            bytes([0x8E, 0x83, 0x8F, 0x82]),  # MOV DPH,R6 ; MOV DPL,R7
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
        ]
    )
    source.extend(read_block)
    skip_after_read_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    write_check_start = len(source)
    source.extend(mov_dptr(0x8194))
    source.extend(bytes([0xE0, 0x64, 0xA5, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway_check
    jump_to_gateway_check_pos = len(source) - 1

    write_block = b"".join(
        [
            xdata_cdb_address_to_r6_r7(selector_mask),
            mov_dptr(0x8193),  # CDB byte 9: write value.
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
            bytes([0x8E, 0x83, 0x8F, 0x82]),  # MOV DPH,R6 ; MOV DPL,R7
            bytes([0xED, 0xF0]),  # MOV A,R5 ; MOVX @DPTR,A
            bytes([0x8E, 0x83, 0x8F, 0x82]),  # MOV DPH,R6 ; MOV DPL,R7
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
        ]
    )
    source.extend(write_block)
    skip_after_write_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_check_start = len(source)
    jump_to_unknown_mode_positions: list[int] = []
    for cdb_addr in (0x8194, 0x8195):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x70, 0x00]))  # MOVX; JNZ unknown_mode
        jump_to_unknown_mode_positions.append(len(source) - 1)

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    skip_after_gateway_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    unknown_mode_start = len(source)
    source.extend(mov_rn_imm(5, 0xEE))
    end_source = len(source)

    source[jump_to_write_check_pos] = rel8(jump_to_write_check_pos + 1, write_check_start)
    source[jump_to_gateway_check_pos] = rel8(jump_to_gateway_check_pos + 1, gateway_check_start)
    source[skip_after_read_pos + 1] = rel8(skip_after_read_pos + 2, end_source)
    source[skip_after_write_pos + 1] = rel8(skip_after_write_pos + 2, end_source)
    for position in jump_to_unknown_mode_positions:
        source[position] = rel8(position + 1, unknown_mode_start)
    source[skip_after_gateway_pos + 1] = rel8(skip_after_gateway_pos + 2, end_source)
    return bytes(source)


def write_xdata_run(address: int, values: list[int]) -> bytes:
    source = bytearray(mov_dptr(address))
    for index, value in enumerate(values):
        if value == 0:
            source.append(0xE4)  # CLR A
        else:
            source.extend(bytes([0x74, value & 0xFF]))  # MOV A,#value
        source.append(0xF0)  # MOVX @DPTR,A
        if index != len(values) - 1:
            source.append(0xA3)  # INC DPTR
    return bytes(source)


def source_cdd_field_replay() -> bytes:
    """Write the LD5M CDD field-only mailbox package derived statically."""

    return b"".join(
        [
            write_xdata_run(0x4A00, [0x00, 0x03, 0x00, 0x03]),
            write_xdata_run(0x4A05, [0x14, 0x07]),
            write_xdata_run(0x4A20, [0x03, 0x08, 0x10]),
            write_xdata_run(0x8258, [0x00, 0x0D, 0x90, 0x00]),
            write_xdata_run(0x4A00, [0x01]),
            mov_rn_imm(5, 0xCD),
        ]
    )


def source_gateway_cdb_bulk_with_cdd_field_replay(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with a special CDD-field replay trigger.

    Normal mode matches source_gateway_cdb_bulk(): CDB[7:9] is a 24-bit
    controller address. The special preserved address 0xfcdd00 does not read
    the gateway; it writes the static LD5M CDD field-only mailbox package and
    returns 0xcd at response[0x20].
    """

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xDD), (0x8193, 0x00)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_cdd_field_replay())
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def build_source(args: argparse.Namespace) -> tuple[str, bytes, dict[str, Any]]:
    modes = [
        args.constant is not None,
        args.xdata_direct is not None,
        args.xdata_window is not None,
        args.xdata_cdb_address,
        args.xdata_cdb_bulk,
        args.xdata_cdb_rw,
        args.gateway_cdb_address,
        args.gateway_cdb_bulk,
        args.gateway_cdb_bulk_with_xdata_write,
        args.gateway_cdb_bulk_with_xdata_rw,
        args.gateway_cdb_bulk_with_cdd_field_replay,
    ]
    if sum(modes) != 1:
        raise ValueError(
            "choose exactly one of --constant, --xdata-direct, --xdata-window, "
            "--xdata-cdb-address, --xdata-cdb-bulk, --xdata-cdb-rw, "
            "--gateway-cdb-address, --gateway-cdb-bulk, "
            "--gateway-cdb-bulk-with-xdata-write/--gateway-cdb-bulk-with-xdata-rw, "
            "or --gateway-cdb-bulk-with-cdd-field-replay"
        )
    if args.constant is not None:
        return "constant", source_constant(args.constant), {"constant": args.constant}
    if args.xdata_direct is not None:
        return "xdata_direct", source_xdata_direct(args.xdata_direct), {"xdata_direct": args.xdata_direct}
    if args.gateway_cdb_address:
        return (
            "gateway_cdb_address",
            source_gateway_cdb_address(args.selector_mask),
            {"address_source": "cdb_bytes_7_8_9_plus_control_low_bits", "selector_mask": args.selector_mask},
        )
    if args.gateway_cdb_bulk:
        return (
            "gateway_cdb_bulk",
            source_gateway_cdb_bulk(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "cdb_bytes_7_8_9_plus_control_low_bits",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_xdata_write:
        return (
            "gateway_cdb_bulk_with_xdata_write",
            source_gateway_cdb_bulk_with_xdata_write(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "write_mode": "if host cdb_10_a5_cdb_11_5a, write cdb_byte_9 to xdata[cdb_7_8_plus_control_low_bits]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_xdata_rw:
        return (
            "gateway_cdb_bulk_with_xdata_rw",
            source_gateway_cdb_bulk_with_xdata_rw(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "read_mode": "if host cdb_10_5a, read xdata[cdb_7_8_plus_control_low_bits]",
                "write_mode": "if host cdb_10_a5, write cdb_byte_9 to xdata[cdb_7_8_plus_control_low_bits]",
                "unknown_mode": "nonzero cdb_10/cdb_11 values outside read/write selectors return 0xee",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_field_replay:
        return (
            "gateway_cdb_bulk_with_cdd_field_replay",
            source_gateway_cdb_bulk_with_cdd_field_replay(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_dd_cdb_9_00 replays LD5M CDD field-only mailbox package",
                "trigger_response": "0xcd at response[0x20]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.xdata_cdb_address:
        return (
            "xdata_cdb_address",
            source_xdata_cdb_address(args.selector_mask),
            {"address_source": "cdb_bytes_7_8_plus_control_low_bits", "selector_mask": args.selector_mask},
        )
    if args.xdata_cdb_bulk:
        return (
            "xdata_cdb_bulk",
            source_xdata_cdb_bulk(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "cdb_bytes_7_8_plus_control_low_bits",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.xdata_cdb_rw:
        return (
            "xdata_cdb_rw",
            source_xdata_cdb_rw(args.selector_mask),
            {
                "address_source": "cdb_bytes_7_8_plus_control_low_bits",
                "write_value_source": "cdb_byte_9",
                "write_magic": "cdb_10_a5_cdb_11_5a",
                "selector_mask": args.selector_mask,
            },
        )
    return (
        "xdata_window",
        source_xdata_window(args.xdata_window, args.selector_mask),
        {"xdata_window": args.xdata_window, "selector_mask": args.selector_mask},
    )


def build_payload(base: bytes, args: argparse.Namespace) -> dict[str, Any]:
    original_hook = base[args.hook_addr : args.hook_addr + 3]
    if len(original_hook) != 3:
        raise ValueError("hook bytes are outside base image")
    if args.restore:
        cave_payload = b"\xFF" * args.cave_len
        return {
            "mode": "restore",
            "hook_patch": patch_arg(args.hook_addr, original_hook),
            "cave_patch": patch_arg(args.cave_addr, cave_payload),
            "original_hook_bytes": original_hook.hex(),
            "payload": cave_payload.hex(),
            "payload_len": len(cave_payload),
            "source": {},
        }

    cave_original = base[args.cave_addr : args.cave_addr + args.cave_len]
    if cave_original != b"\xFF" * args.cave_len:
        raise ValueError(
            f"cave 0x{args.cave_addr:04x}..0x{args.cave_addr + args.cave_len:04x} is not all FF"
        )

    source_mode, source_code, source_meta = build_source(args)
    storage_offset = RESPONSE_STORAGE_BASE + args.response_offset
    if not 0 <= storage_offset <= 0xFFFF:
        raise ValueError("response offset is outside 16-bit response storage window")
    payload = b"".join(
        [
            source_code,
            mov_rn_imm(7, storage_offset & 0xFF),
            mov_rn_imm(6, (storage_offset >> 8) & 0xFF),
            lcall(0x6012),
            mov_rn_imm(7, 0x20),
            mov_rn_imm(6, 0x02),
            lcall(0x6206),
            ljmp(args.resume_addr),
        ]
    )
    if len(payload) > args.cave_len:
        raise ValueError(f"payload is {len(payload)} bytes, cave limit is {args.cave_len}")
    return {
        "mode": source_mode,
        "hook_patch": patch_arg(args.hook_addr, ljmp(args.cave_addr)),
        "cave_patch": patch_arg(args.cave_addr, payload),
        "original_hook_bytes": original_hook.hex(),
        "response_offset": args.response_offset,
        "response_storage_offset": storage_offset,
        "payload": payload.hex(),
        "payload_len": len(payload),
        "source": source_meta,
    }


def render_command(args: argparse.Namespace, hook: dict[str, Any]) -> tuple[list[str], Path]:
    name = f"currentboot-response-hook-{args.name}"
    out_dir = args.out_dir / name
    cmd = [
        sys.executable,
        str(ROOT / "scripts/build_liteon_helper_bypass_candidate.py"),
        "--name",
        name,
        "--out-dir",
        str(out_dir),
        "--patch",
        hook["hook_patch"],
        "--patch",
        hook["cave_patch"],
        "--auto-helper-range",
        "--include-pre-tail",
    ]
    return cmd, out_dir


def write_report(args: argparse.Namespace, hook: dict[str, Any], out_dir: Path, cmd: list[str]) -> None:
    report = {
        "status": "currentboot_response_hook_candidate",
        "name": args.name,
        "base_image": str(args.base_image),
        "hook_addr": args.hook_addr,
        "resume_addr": args.resume_addr,
        "cave_addr": args.cave_addr,
        "cave_len": args.cave_len,
        **hook,
        "build_command": cmd,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.name}.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        f"# Currentboot Response Hook Candidate: {args.name}",
        "",
        f"- mode: `{hook['mode']}`",
        f"- hook address: `0x{args.hook_addr:04x}`",
        f"- resume address: `0x{args.resume_addr:04x}`",
        f"- cave address: `0x{args.cave_addr:04x}`",
        f"- original hook bytes: `{hook['original_hook_bytes']}`",
        f"- response offset: `0x{hook.get('response_offset', 0):02x}`",
        f"- hook patch: `{hook['hook_patch']}`",
        f"- cave patch: `{hook['cave_patch']}`",
        "",
        "Build command:",
        "",
        "```sh",
        " ".join(cmd),
        "```",
    ]
    (out_dir / f"{args.name}.md").write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, type=slugify)
    parser.add_argument("--base-image", type=Path, default=DEFAULT_BASE_IMAGE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--hook-addr", type=parse_addr, default=DEFAULT_HOOK_ADDR)
    parser.add_argument("--resume-addr", type=parse_addr, default=0x4FCC)
    parser.add_argument("--cave-addr", type=parse_addr, default=DEFAULT_CAVE_ADDR)
    parser.add_argument("--cave-len", type=parse_positive_int, default=0x80)
    parser.add_argument("--response-offset", type=parse_byte, default=0x20)
    parser.add_argument("--constant", type=parse_byte)
    parser.add_argument("--xdata-direct", type=parse_addr)
    parser.add_argument("--xdata-window", type=parse_addr)
    parser.add_argument(
        "--gateway-cdb-address",
        action="store_true",
        help="read controller gateway address CDB[7:9] + (CDB[5] & --selector-mask)",
    )
    parser.add_argument(
        "--gateway-cdb-bulk",
        action="store_true",
        help="copy --bulk-len bytes from controller gateway address CDB[7:9] + selector into the INQUIRY response",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-xdata-write",
        action="store_true",
        help="like --gateway-cdb-bulk, but host CDB[10:11]=a5/5a writes CDB[9] to XDATA CDB[7:8]+selector instead",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-xdata-rw",
        action="store_true",
        help="like --gateway-cdb-bulk, plus host CDB[10]=a5 XDATA write and CDB[10]=5a XDATA read modes",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-field-replay",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:9]=fc/dd/00 writes the LD5M CDD field-only mailbox package",
    )
    parser.add_argument(
        "--xdata-cdb-address",
        action="store_true",
        help="read XDATA address CDB[7:8] + (CDB[5] & --selector-mask)",
    )
    parser.add_argument(
        "--xdata-cdb-bulk",
        action="store_true",
        help="copy --bulk-len bytes from XDATA address CDB[7:8] + selector into the INQUIRY response",
    )
    parser.add_argument(
        "--xdata-cdb-rw",
        action="store_true",
        help="read XDATA address CDB[7:8] + selector, and write CDB[9] first if CDB[10:11] is a5 5a",
    )
    parser.add_argument("--bulk-len", type=parse_byte, default=0x80)
    parser.add_argument("--selector-mask", type=parse_byte, default=0x3F)
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.restore and (
        any(value is not None for value in (args.constant, args.xdata_direct, args.xdata_window))
        or args.gateway_cdb_address
        or args.gateway_cdb_bulk
        or args.gateway_cdb_bulk_with_xdata_write
        or args.gateway_cdb_bulk_with_xdata_rw
        or args.gateway_cdb_bulk_with_cdd_field_replay
        or args.xdata_cdb_address
        or args.xdata_cdb_bulk
        or args.xdata_cdb_rw
    ):
        raise ValueError("--restore cannot be combined with a source mode")
    base = args.base_image.read_bytes()
    hook = build_payload(base, args)
    cmd, out_dir = render_command(args, hook)
    write_report(args, hook, out_dir, cmd)
    if args.dry_run:
        print(json.dumps(hook, indent=2, sort_keys=True))
        print(f"wrote {out_dir}")
        return 0
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, text=True)
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
