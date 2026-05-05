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


def gateway_cdb_address_to_r5_r6_r7(selector_mask: int) -> bytes:
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
        ]
    )


def gateway_read_r5_r6_r7_to_r5() -> bytes:
    wait_ready = bytes.fromhex("904000e020e7f9")
    return b"".join(
        [
            wait_ready,
            mov_dptr(0x4091),
            bytes([0xED, 0xF0, 0xA3, 0xEE, 0xF0, 0xA3, 0xEF, 0xF0]),
            mov_dptr(0x4098),
            bytes([0xE0]),  # throwaway read, matching the stock gateway read quirk.
            wait_ready,
            mov_dptr(0x4098),
            bytes([0xE0, 0xFD]),  # MOVX A,@DPTR ; MOV R5,A
        ]
    )


def gateway_write_r5_r6_r7_value_r3() -> bytes:
    wait_ready = bytes.fromhex("904000e020e7f9")
    return b"".join(
        [
            wait_ready,
            mov_dptr(0x4095),
            bytes([0xED, 0xF0, 0xA3, 0xEE, 0xF0, 0xA3, 0xEF, 0xF0]),
            mov_dptr(0x4098),
            bytes([0xEB, 0xF0]),  # MOV A,R3 ; MOVX @DPTR,A
            wait_ready,
        ]
    )


def source_gateway_cdb_rw(selector_mask: int) -> bytes:
    """Read controller gateway, with guarded one-byte write mode.

    Normal mode is the proven one-byte gateway read. Write mode requires
    CDB[10] == 0x5a, writes CDB[11] to the gateway address selected by
    CDB[7:9] plus CDB[5]'s selector bits, then returns readback.

    Keep the guard in the proven preserved parameter window. An earlier v1
    attempt also checked CDB[6], but live smoke tests showed that byte is not
    preserved reliably enough by this currentboot handler.
    """

    source = bytearray()
    source.extend(mov_dptr(0x8194))  # CDB byte 10: write guard.
    source.extend(bytes([0xE0, 0x64, 0x5A, 0x70, 0x00]))  # MOVX; XRL; JNZ read
    jump_to_read_pos = len(source) - 1

    source.extend(gateway_cdb_address_to_r5_r6_r7(selector_mask))
    source.extend(mov_dptr(0x8195))  # CDB byte 11: write value.
    source.extend(bytes([0xE0, 0xFB]))  # MOVX A,@DPTR ; MOV R3,A
    source.extend(gateway_write_r5_r6_r7_value_r3())
    source.extend(gateway_read_r5_r6_r7_to_r5())
    skip_read_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    read_start = len(source)
    source.extend(gateway_cdb_address_to_r5_r6_r7(selector_mask))
    source.extend(gateway_read_r5_r6_r7_to_r5())
    end_source = len(source)

    source[jump_to_read_pos] = rel8(jump_to_read_pos + 1, read_start)
    source[skip_read_pos + 1] = rel8(skip_read_pos + 2, end_source)
    return bytes(source)


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
    controller address. Live smoke tests showed that CDB byte 10 is preserved
    at xdata[0x8194], so the host selects write mode with CDB[10] == 0xa5.
    CDB[11] is ignored. The hook writes CDB[9] to XDATA address CDB[7:8] +
    selector and returns the readback byte in R5. build_payload's standard
    response-byte write exposes that readback at response[0x20].
    """

    checks = bytearray()
    checks.extend(mov_dptr(0x8194))  # CDB byte 10: write selector.
    checks.extend(bytes([0xE0, 0x64, 0xA5, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
    jump_to_gateway_pos = len(checks) - 1

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

    source[jump_to_gateway_pos] = rel8(jump_to_gateway_pos + 1, gateway_start)
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
    accumulator: int | None = None
    for index, value in enumerate(values):
        if accumulator != value:
            if value == 0:
                source.append(0xE4)  # CLR A
            else:
                source.extend(bytes([0x74, value & 0xFF]))  # MOV A,#value
            accumulator = value
        source.append(0xF0)  # MOVX @DPTR,A
        if index != len(values) - 1:
            source.append(0xA3)  # INC DPTR
    return bytes(source)


def write_direct_byte(address: int, value: int) -> bytes:
    return bytes([0x75, address & 0xFF, value & 0xFF])  # MOV direct,#imm


def write_direct_run(address: int, values: list[int]) -> bytes:
    return b"".join(write_direct_byte(address + index, value) for index, value in enumerate(values))


def copy_xdata_to_response_source(address: int, length: int, storage_offset: int) -> bytes:
    if not 1 <= length <= 0xFF:
        raise ValueError("copy length must be 1..255")
    if not 0 <= address <= 0xFFFF:
        raise ValueError("XDATA source address must fit in 16 bits")
    if not 0 <= storage_offset <= 0xFFFF:
        raise ValueError("response storage offset must fit in 16 bits")

    init = b"".join(
        [
            mov_rn_imm(2, (address >> 8) & 0xFF),
            mov_rn_imm(3, address & 0xFF),
            mov_rn_imm(6, (storage_offset >> 8) & 0xFF),
            mov_rn_imm(7, storage_offset & 0xFF),
            mov_rn_imm(1, length),
        ]
    )
    loop_start = len(init)
    read_source = bytes([0x8A, 0x83, 0x8B, 0x82, 0xE0, 0xFD])  # DPH=R2; DPL=R3; MOVX; R5=A
    write_response = lcall(0x6012)
    increment_source = bytes([0x0B, 0xEB, 0x70, 0x01, 0x0A])  # INC R3; if zero INC R2
    increment_response = bytes.fromhex("0fef70010e")  # INC R7; if zero INC R6
    loop_body = read_source + write_response + increment_source + increment_response
    djnz_pos = loop_start + len(loop_body)
    djnz = bytes([0xD9, rel8(djnz_pos + 2, loop_start)])
    return init + loop_body + djnz


def copy_xdata_byte_source(src: int, dst: int) -> bytes:
    if not 0 <= src <= 0xFFFF or not 0 <= dst <= 0xFFFF:
        raise ValueError("XDATA byte copy addresses must fit in 16 bits")
    return mov_dptr(src) + bytes([0xE0]) + mov_dptr(dst) + bytes([0xF0])


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


def source_cdd_prestage_field_replay_compact() -> bytes:
    """Write compact descriptor-prestate plus CDD field package.

    This intentionally writes the nonzero descriptor/status fields, clears the
    doorbell first, writes the full CDD2 start field, then rings the doorbell.
    It omits zero descriptor fields to keep the payload within the 0x6ee3 cave
    when paired with the one-byte gateway reader.
    """

    return b"".join(
        [
            write_xdata_run(0x8246, [0x70]),
            write_xdata_run(0x824A, [0x40]),
            write_xdata_run(0x824D, [0x08]),
            write_xdata_run(0x8252, [0x50]),
            write_xdata_run(0x8254, [0x40]),
            write_xdata_run(0x4E0D, [0x40]),
            write_xdata_run(0x4E1A, [0x14]),
            write_xdata_run(0x4E1C, [0x01]),
            write_direct_byte(0x60, 0x01),
            write_direct_byte(0x61, 0xFF),
            write_xdata_run(0x4A00, [0x00]),
            write_xdata_run(0x4A01, [0x03]),
            write_xdata_run(0x4A03, [0x03]),
            write_xdata_run(0x4A05, [0x14, 0x07]),
            write_xdata_run(0x4A20, [0x03, 0x08, 0x10]),
            write_xdata_run(0x8258, [0x00, 0x0D, 0x90, 0x00]),
            write_xdata_run(0x4A00, [0x01]),
            mov_rn_imm(5, 0xCE),
        ]
    )


def source_cdd_descriptor_field_replay_compact(response_marker: int = 0xCF) -> bytes:
    """Write descriptor-derived fields plus CDD field package.

    This leaves out the derived status/direct bytes so it can fit alongside
    the proven bulk gateway reader in the 0x6ee3 cave.
    """

    return b"".join(
        [
            write_xdata_run(0x8246, [0x70]),
            write_xdata_run(0x824A, [0x40]),
            write_xdata_run(0x824D, [0x08]),
            write_xdata_run(0x8252, [0x50]),
            write_xdata_run(0x8254, [0x40]),
            write_xdata_run(0x4A00, [0x00]),
            write_xdata_run(0x4A01, [0x03]),
            write_xdata_run(0x4A03, [0x03]),
            write_xdata_run(0x4A05, [0x14, 0x07]),
            write_xdata_run(0x4A20, [0x03, 0x08, 0x10]),
            write_xdata_run(0x8258, [0x00, 0x0D, 0x90, 0x00]),
            write_xdata_run(0x4A00, [0x01]),
            mov_rn_imm(5, response_marker),
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


def source_gateway_cdb_bulk_with_cdd_descriptor_replay(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with descriptor-prestage CDD replay trigger.

    Normal mode matches source_gateway_cdb_bulk(). The fake address prefix
    0xfcddxx writes a compact descriptor-derived prestate plus the CDD field
    package and returns 0xcf at response[0x20]. This is intentionally narrower
    than the one-byte-gateway prestage hook so the proven bulk reader still
    fits.
    """

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xDD)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_cdd_descriptor_field_replay_compact())
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_mapped_cdd_header_replay(storage_offset: int) -> bytes:
    """Call resident mapped-header helper and copy xdata[0xc000..0xc01f].

    The resident parser sets 0x8256..0x8257 to 0xc000, prepares IRAM
    0x30..0x33 as the source-end-minus-one value, then calls 0x1717 with the
    CDD header flash address in R4..R7. This helper mirrors that minimum setup
    and copies the mapped XDATA window into response storage + 1. build_payload
    writes the 0xd0 marker at response[0x20] afterward.
    """

    return b"".join(
        [
            write_xdata_run(0x8256, [0xC0, 0x00]),
            write_direct_run(0x30, [0x00, 0x07, 0xFF, 0xFF]),
            mov_rn_imm(4, 0x00),
            mov_rn_imm(5, 0x00),
            mov_rn_imm(6, 0x70),
            mov_rn_imm(7, 0x2C),
            lcall(0x1717),
            copy_xdata_to_response_source(0xC000, 0x20, storage_offset + 1),
            mov_rn_imm(5, 0xD0),
        ]
    )


def source_gateway_cdb_bulk_with_cdd_mapped_header(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with a special mapped-CDD-header trigger."""

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xDE)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_mapped_cdd_header_replay(storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_mapped_cdd_header_status_replay(storage_offset: int) -> bytes:
    """Call mapped-header helper and copy both 0xc000 data and 0x4e80 status."""

    return b"".join(
        [
            write_xdata_run(0x8256, [0xC0, 0x00]),
            write_direct_run(0x30, [0x00, 0x07, 0xFF, 0xFF]),
            mov_rn_imm(4, 0x00),
            mov_rn_imm(5, 0x00),
            mov_rn_imm(6, 0x70),
            mov_rn_imm(7, 0x2C),
            lcall(0x1717),
            copy_xdata_to_response_source(0xC000, 0x20, storage_offset + 1),
            copy_xdata_to_response_source(0x4E80, 0x20, storage_offset + 0x21),
            mov_rn_imm(5, 0xD1),
        ]
    )


def source_gateway_cdb_bulk_with_cdd_mapped_header_status(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with mapped-CDD-header/status trigger."""

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xDF)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_mapped_cdd_header_status_replay(storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_mapped_cdd_header_status64_replay(storage_offset: int) -> bytes:
    """Call mapped-header helper and copy 0xc000 data plus 0x4e80..0x4ebf."""

    return b"".join(
        [
            write_xdata_run(0x8256, [0xC0, 0x00]),
            write_direct_run(0x30, [0x00, 0x07, 0xFF, 0xFF]),
            mov_rn_imm(4, 0x00),
            mov_rn_imm(5, 0x00),
            mov_rn_imm(6, 0x70),
            mov_rn_imm(7, 0x2C),
            lcall(0x1717),
            copy_xdata_to_response_source(0xC000, 0x20, storage_offset + 1),
            copy_xdata_to_response_source(0x4E80, 0x40, storage_offset + 0x21),
            mov_rn_imm(5, 0xD2),
        ]
    )


def source_mapped_cdd_source_replay(
    selector_mask: int, storage_offset: int
) -> bytes:
    """Map a host-selected CDD source address through 0x1717.

    The fixed-header probes proved that 0x1717 maps a CDD source address into
    xdata[0xc000] when xdata[0x8256..0x8257] is set to c000 and IRAM
    0x30..0x33 contains the companion/end-minus-one value. This variant keeps
    the same setup, but fills R5:R6:R7 from the host CDB address bytes so the
    next run can sample arbitrary CDD source records without rebuilding the
    hook for every address.
    """

    return b"".join(
        [
            write_xdata_run(0x8256, [0xC0, 0x00]),
            write_direct_run(0x30, [0x00, 0x07, 0xFF, 0xFF]),
            gateway_cdb_address_to_r5_r6_r7(selector_mask),
            mov_rn_imm(4, 0x00),
            lcall(0x1717),
            copy_xdata_to_response_source(0xC000, 0x20, storage_offset + 1),
            mov_rn_imm(5, 0xD5),
        ]
    )


def source_mapped_cdd_source_status64_replay(
    selector_mask: int, storage_offset: int
) -> bytes:
    """Map a host-selected CDD source address and return 0x4e80 status."""

    return b"".join(
        [
            write_xdata_run(0x8256, [0xC0, 0x00]),
            write_direct_run(0x30, [0x00, 0x07, 0xFF, 0xFF]),
            gateway_cdb_address_to_r5_r6_r7(selector_mask),
            mov_rn_imm(4, 0x00),
            lcall(0x1717),
            copy_xdata_to_response_source(0xC000, 0x20, storage_offset + 1),
            copy_xdata_to_response_source(0x4E80, 0x40, storage_offset + 0x21),
            mov_rn_imm(5, 0xD6),
        ]
    )


def source_cdd_mapped_source_window128_only(selector_mask: int, storage_offset: int) -> bytes:
    """Special-purpose 128-byte mapped-source hook without a fallback reader."""

    source = bytearray()
    source.extend(mov_dptr(0x8194))  # CDB byte 10: mapped-source selector.
    source.extend(bytes([0xE0, 0x64, 0xE3, 0x70, 0x00]))  # MOVX; XRL; JNZ unknown
    jump_to_unknown_pos = len(source) - 1

    source.extend(source_mapped_cdd_source_window128_replay(selector_mask, storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    unknown_start = len(source)
    source.extend(mov_rn_imm(5, 0xEE))
    end_source = len(source)

    source[jump_to_unknown_pos] = rel8(jump_to_unknown_pos + 1, unknown_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_mapped_cdd_source_window128_replay(
    selector_mask: int, storage_offset: int
) -> bytes:
    """Map a host-selected CDD source address and return a wider 0xc000 window."""

    return b"".join(
        [
            write_xdata_run(0x8256, [0xC0, 0x00]),
            write_direct_run(0x30, [0x00, 0x07, 0xFF, 0xFF]),
            gateway_cdb_address_to_r5_r6_r7(selector_mask),
            mov_rn_imm(4, 0x00),
            lcall(0x1717),
            copy_xdata_to_response_source(0xC000, 0x80, storage_offset + 1),
            mov_rn_imm(5, 0xD7),
        ]
    )


def source_gateway_cdb_bulk_with_cdd_mapped_header_status64(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with mapped-CDD-header/status64 trigger."""

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xE0)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_mapped_cdd_header_status64_replay(storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_cdd_mapped_source_status64_only(selector_mask: int, storage_offset: int) -> bytes:
    """Special-purpose mapped-source/status hook without a fallback reader.

    CDB[10] == 0xe3 selects the mapped-source path. Other commands return
    marker 0xee so accidental ordinary currentboot identity probes are obvious.
    This is intentionally narrower than the gateway-preserving variant so the
    64-byte XDATA status copy fits in the known cave.
    """

    source = bytearray()
    source.extend(mov_dptr(0x8194))  # CDB byte 10: mapped-source selector.
    source.extend(bytes([0xE0, 0x64, 0xE3, 0x70, 0x00]))  # MOVX; XRL; JNZ unknown
    jump_to_unknown_pos = len(source) - 1

    source.extend(source_mapped_cdd_source_status64_replay(selector_mask, storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    unknown_start = len(source)
    source.extend(mov_rn_imm(5, 0xEE))
    end_source = len(source)

    source[jump_to_unknown_pos] = rel8(jump_to_unknown_pos + 1, unknown_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_gateway_cdb_bulk_with_cdd_mapped_source(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with arbitrary mapped-CDD-source trigger.

    Normal mode matches source_gateway_cdb_bulk(): CDB[7:9] plus the selector
    bits read the controller gateway. Host CDB[10] == 0xe3 selects the mapped
    source path instead, where the same address convention is passed to 0x1717
    and xdata[0xc000..0xc01f] is returned. If status is needed, the preserved
    gateway bulk path can read xdata[0x4e80..0x4ebf] in a follow-up command.
    """

    source = bytearray()
    source.extend(mov_dptr(0x8194))  # CDB byte 10: mapped-source selector.
    source.extend(bytes([0xE0, 0x64, 0xE3, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
    jump_to_gateway_pos = len(source) - 1

    source.extend(source_mapped_cdd_source_replay(selector_mask, storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    source[jump_to_gateway_pos] = rel8(jump_to_gateway_pos + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_mapped_cdd_parser_call_replay(storage_offset: int) -> bytes:
    """Call resident CDD parser setup and copy xdata[0x4a00..0x4a3f].

    This is the next rung above the mapped-header helper. It seeds the same
    descriptor fields the resident parser expects, calls FUN_CODE_002e with
    descriptor base 0x7000, then returns the controller/mailbox package that
    the parser populated. build_payload writes the 0xd3 marker at
    response[0x20] afterward.
    """

    return b"".join(
        [
            write_xdata_run(0x8196, [0x00]),
            write_xdata_run(0x8227, [0x00, 0x2C]),
            write_xdata_run(
                0x8248,
                [
                    0x00,
                    0x00,
                    0x40,
                    0x00,
                    0x00,
                    0x08,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x50,
                    0x00,
                    0x40,
                    0x00,
                ],
            ),
            bytes([0xE4, 0xFC, 0xFD, 0xFF, 0x7E, 0x70]),  # R4:R5:R6:R7 = 00:00:70:00.
            lcall(0x002E),
            copy_xdata_to_response_source(0x4A00, 0x40, storage_offset + 1),
            mov_rn_imm(5, 0xD3),
        ]
    )


def source_gateway_cdb_bulk_with_cdd_parser_call(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with resident CDD parser-call trigger."""

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xE1)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_mapped_cdd_parser_call_replay(storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_mapped_cdd_parser_mode2_status64_replay(storage_offset: int) -> bytes:
    """Call the CDD parser with xdata[0x8196]=2 and return 0x4e status.

    This guarded materializer probe uses the same descriptor state as the
    proven parser-call hook, but selects the alternate FUN_CODE_002e branch.
    Response bytes 0x21..0x60 receive xdata[0x4e80..0x4ebf].
    """

    return b"".join(
        [
            write_xdata_run(0x8196, [0x02]),
            write_xdata_run(0x8227, [0x00, 0x2C]),
            write_xdata_run(
                0x8248,
                [
                    0x00,
                    0x00,
                    0x40,
                    0x00,
                    0x00,
                    0x08,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x50,
                    0x00,
                    0x40,
                    0x00,
                ],
            ),
            bytes([0xE4, 0xFC, 0xFD, 0xFF, 0x7E, 0x70]),  # R4:R5:R6:R7 = 00:00:70:00.
            lcall(0x002E),
            copy_xdata_to_response_source(0x4E80, 0x40, storage_offset + 1),
            mov_rn_imm(5, 0xD8),
        ]
    )


def source_mapped_cdd_parser_mode2_xdata_window_replay(
    storage_offset: int, xdata_address: int, xdata_length: int, marker: int
) -> bytes:
    """Call the CDD parser mode-2 branch and return a selected XDATA window.

    This is the same non-persistent setup as
    source_mapped_cdd_parser_mode2_status64_replay(), but it lets later probes
    inspect state windows such as 0x4e00, 0x4a00, or 0x8240 after the mode-2
    call without building a custom hook for each window.
    """

    return b"".join(
        [
            write_xdata_run(0x8196, [0x02]),
            write_xdata_run(0x8227, [0x00, 0x2C]),
            write_xdata_run(
                0x8248,
                [
                    0x00,
                    0x00,
                    0x40,
                    0x00,
                    0x00,
                    0x08,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x50,
                    0x00,
                    0x40,
                    0x00,
                ],
            ),
            bytes([0xE4, 0xFC, 0xFD, 0xFF, 0x7E, 0x70]),  # R4:R5:R6:R7 = 00:00:70:00.
            lcall(0x002E),
            copy_xdata_to_response_source(xdata_address, xdata_length, storage_offset + 1),
            mov_rn_imm(5, marker),
        ]
    )


def source_gateway_cdb_bulk_with_cdd_parser_mode2_status64(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with parser mode-2/status64 trigger."""

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xE4)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_mapped_cdd_parser_mode2_status64_replay(storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_gateway_cdb_bulk_with_cdd_parser_mode2_xdata_window(
    selector_mask: int,
    storage_offset: int,
    bulk_len: int,
    xdata_address: int,
    xdata_length: int,
    marker: int,
) -> bytes:
    """Gateway bulk read with parser mode-2 plus selected-XDATA trigger."""

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xE5)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(
        source_mapped_cdd_parser_mode2_xdata_window_replay(
            storage_offset, xdata_address, xdata_length, marker
        )
    )
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_mapped_cdd_parser_second_doorbell_replay(storage_offset: int) -> bytes:
    """Call CDD parser setup, then manually ring the later 0x4a doorbell.

    The parser-call trigger proved that FUN_CODE_002e returns a populated
    0x4a mailbox in currentboot, but 0x4a28/0x4a29 remain zero. The later
    resident helper at 0x08d0 mirrors 0x4a24/0x4a25 into those bytes, writes
    0x4a00 = 1, and calls 0x1667. This compact variant performs the same
    visible side effects directly, then returns only a marker so the normal
    gateway-bulk path remains available for decoded-memory sampling.
    """

    return b"".join(
        [
            write_xdata_run(0x8196, [0x00]),
            write_xdata_run(0x8227, [0x00, 0x2C]),
            write_xdata_run(
                0x8248,
                [
                    0x00,
                    0x00,
                    0x40,
                    0x00,
                    0x00,
                    0x08,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x50,
                    0x00,
                    0x40,
                    0x00,
                ],
            ),
            bytes([0xE4, 0xFC, 0xFD, 0xFF, 0x7E, 0x70]),  # R4:R5:R6:R7 = 00:00:70:00.
            lcall(0x002E),
            write_xdata_run(0x4A00, [0x00]),
            copy_xdata_byte_source(0x4A24, 0x4A28),
            copy_xdata_byte_source(0x4A25, 0x4A29),
            write_xdata_run(0x4A00, [0x01]),
            lcall(0x1667),
            mov_rn_imm(5, 0xD4),
        ]
    )


def source_gateway_cdb_bulk_with_cdd_parser_second_doorbell(
    selector_mask: int, storage_offset: int, bulk_len: int
) -> bytes:
    """Gateway bulk read with parser-call plus second 0x4a doorbell trigger."""

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    # This uses only CDB[8] as the compact trigger guard so the payload fits
    # alongside the gateway-bulk reader. Avoid normal gateway reads whose
    # middle address byte is 0xe2 while this hook is installed.
    source.extend(mov_dptr(0x8192))
    source.extend(bytes([0xE0, 0x64, 0xE2, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
    jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_mapped_cdd_parser_second_doorbell_replay(storage_offset))
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_bulk(selector_mask, storage_offset, bulk_len))
    end_source = len(source)

    for position in jump_to_gateway_positions:
        source[position] = rel8(position + 1, gateway_start)
    source[skip_after_replay_pos + 1] = rel8(skip_after_replay_pos + 2, end_source)
    return bytes(source)


def source_gateway_byte_with_cdd_prestage_replay(selector_mask: int) -> bytes:
    """One-byte gateway read with compact descriptor-prestate replay trigger.

    Normal mode matches source_gateway_cdb_address(). Any command with
    CDB[7:8] == fc dd writes compact descriptor prestate plus the field-only
    CDD package and returns 0xce at response[0x20].
    """

    source = bytearray()
    jump_to_gateway_positions: list[int] = []
    for cdb_addr, expected in ((0x8191, 0xFC), (0x8192, 0xDD)):
        source.extend(mov_dptr(cdb_addr))
        source.extend(bytes([0xE0, 0x64, expected, 0x70, 0x00]))  # MOVX; XRL; JNZ gateway
        jump_to_gateway_positions.append(len(source) - 1)

    source.extend(source_cdd_prestage_field_replay_compact())
    skip_after_replay_pos = len(source)
    source.extend(bytes([0x80, 0x00]))  # SJMP end_source

    gateway_start = len(source)
    source.extend(source_gateway_cdb_address(selector_mask))
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
        args.gateway_cdb_rw,
        args.gateway_cdb_bulk,
        args.gateway_cdb_bulk_with_xdata_write,
        args.gateway_cdb_bulk_with_xdata_rw,
        args.gateway_cdb_bulk_with_cdd_field_replay,
        args.gateway_cdb_bulk_with_cdd_descriptor_replay,
        args.gateway_cdb_bulk_with_cdd_mapped_header,
        args.gateway_cdb_bulk_with_cdd_mapped_header_status,
        args.gateway_cdb_bulk_with_cdd_mapped_header_status64,
        args.cdd_mapped_source_status64_only,
        args.cdd_mapped_source_window128_only,
        args.gateway_cdb_bulk_with_cdd_mapped_source,
        args.gateway_cdb_bulk_with_cdd_parser_call,
        args.gateway_cdb_bulk_with_cdd_parser_mode2_status64,
        args.gateway_cdb_bulk_with_cdd_parser_mode2_xdata_window,
        args.gateway_cdb_bulk_with_cdd_parser_second_doorbell,
        args.gateway_byte_with_cdd_prestage_replay,
    ]
    if sum(modes) != 1:
        raise ValueError(
            "choose exactly one of --constant, --xdata-direct, --xdata-window, "
            "--xdata-cdb-address, --xdata-cdb-bulk, --xdata-cdb-rw, "
            "--gateway-cdb-address, --gateway-cdb-rw, --gateway-cdb-bulk, "
            "--gateway-cdb-bulk-with-xdata-write/--gateway-cdb-bulk-with-xdata-rw, "
            "--gateway-cdb-bulk-with-cdd-field-replay, "
            "--gateway-cdb-bulk-with-cdd-descriptor-replay, or "
            "--gateway-cdb-bulk-with-cdd-mapped-header, or "
            "--gateway-cdb-bulk-with-cdd-mapped-header-status, or "
            "--gateway-cdb-bulk-with-cdd-mapped-header-status64, or "
            "--cdd-mapped-source-status64-only, or "
            "--cdd-mapped-source-window128-only, or "
            "--gateway-cdb-bulk-with-cdd-mapped-source, or "
            "--gateway-cdb-bulk-with-cdd-parser-call, or "
            "--gateway-cdb-bulk-with-cdd-parser-mode2-status64, or "
            "--gateway-cdb-bulk-with-cdd-parser-mode2-xdata-window, or "
            "--gateway-cdb-bulk-with-cdd-parser-second-doorbell, or "
            "--gateway-byte-with-cdd-prestage-replay"
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
    if args.gateway_cdb_rw:
        return (
            "gateway_cdb_rw",
            source_gateway_cdb_rw(args.selector_mask),
            {
                "address_source": "cdb_bytes_7_8_9_plus_control_low_bits",
                "write_value_source": "cdb_byte_11",
                "write_magic": "cdb_10_5a",
                "selector_mask": args.selector_mask,
                "gateway_mode": "one_byte",
            },
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
    if args.gateway_cdb_bulk_with_cdd_descriptor_replay:
        return (
            "gateway_cdb_bulk_with_cdd_descriptor_replay",
            source_gateway_cdb_bulk_with_cdd_descriptor_replay(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_dd replays descriptor prestate plus CDD field package",
                "trigger_response": "0xcf at response[0x20]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_mapped_header:
        return (
            "gateway_cdb_bulk_with_cdd_mapped_header",
            source_gateway_cdb_bulk_with_cdd_mapped_header(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_de calls 0x1717 mapped-header helper and returns xdata[0xc000..0xc01f]",
                "trigger_response": "0xd0 at response[0x20], mapped bytes at response[0x21..0x40]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_mapped_header_status:
        return (
            "gateway_cdb_bulk_with_cdd_mapped_header_status",
            source_gateway_cdb_bulk_with_cdd_mapped_header_status(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_df calls 0x1717 and returns xdata[0xc000..0xc01f] plus xdata[0x4e80..0x4e9f]",
                "trigger_response": "0xd1 at response[0x20], mapped bytes at response[0x21..0x40], status bytes at response[0x41..0x60]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_mapped_header_status64:
        return (
            "gateway_cdb_bulk_with_cdd_mapped_header_status64",
            source_gateway_cdb_bulk_with_cdd_mapped_header_status64(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_e0 calls 0x1717 and returns xdata[0xc000..0xc01f] plus xdata[0x4e80..0x4ebf]",
                "trigger_response": "0xd2 at response[0x20], mapped bytes at response[0x21..0x40], status bytes at response[0x41..0x80]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.cdd_mapped_source_status64_only:
        return (
            "cdd_mapped_source_status64_only",
            source_cdd_mapped_source_status64_only(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
            ),
            {
                "address_source": "mapped-source trigger uses cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_10_e3 calls 0x1717 with source address from cdb_7_8_9_plus_control_low_bits",
                "trigger_response": "0xd6 at response[0x20], mapped bytes at response[0x21..0x40], xdata[0x4e80..0x4ebf] status at response[0x41..0x80]",
                "unknown_mode": "commands without cdb_10_e3 return marker 0xee; no gateway fallback in this compact diagnostic build",
                "selector_mask": args.selector_mask,
            },
        )
    if args.cdd_mapped_source_window128_only:
        return (
            "cdd_mapped_source_window128_only",
            source_cdd_mapped_source_window128_only(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
            ),
            {
                "address_source": "mapped-source trigger uses cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_10_e3 calls 0x1717 with source address from cdb_7_8_9_plus_control_low_bits",
                "trigger_response": "0xd7 at response[0x20], xdata[0xc000..0xc07f] at response[0x21..0xa0]",
                "unknown_mode": "commands without cdb_10_e3 return marker 0xee; no gateway fallback in this compact diagnostic build",
                "selector_mask": args.selector_mask,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_mapped_source:
        return (
            "gateway_cdb_bulk_with_cdd_mapped_source",
            source_gateway_cdb_bulk_with_cdd_mapped_source(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits; mapped-source trigger uses same address convention",
                "trigger": "host cdb_10_e3 calls 0x1717 with source address from cdb_7_8_9_plus_control_low_bits",
                "trigger_response": "0xd5 at response[0x20], mapped bytes at response[0x21..0x40]",
                "status_note": "this variant does not return xdata[0x4e80] status; the preserved fallback is a controller-gateway reader, not an XDATA reader",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_parser_call:
        return (
            "gateway_cdb_bulk_with_cdd_parser_call",
            source_gateway_cdb_bulk_with_cdd_parser_call(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_e1 calls resident CDD parser setup at 0x002e and returns xdata[0x4a00..0x4a3f]",
                "trigger_response": "0xd3 at response[0x20], 0x4a00 mailbox bytes at response[0x21..0x60]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_parser_mode2_status64:
        return (
            "gateway_cdb_bulk_with_cdd_parser_mode2_status64",
            source_gateway_cdb_bulk_with_cdd_parser_mode2_status64(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_e4 writes xdata[0x8196]=2, calls resident CDD parser setup at 0x002e, and returns xdata[0x4e80..0x4ebf]",
                "trigger_response": "0xd8 at response[0x20], 0x4e80 status bytes at response[0x21..0x60]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_parser_mode2_xdata_window:
        return (
            "gateway_cdb_bulk_with_cdd_parser_mode2_xdata_window",
            source_gateway_cdb_bulk_with_cdd_parser_mode2_xdata_window(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
                args.mode2_xdata_address,
                args.mode2_xdata_len,
                args.mode2_marker,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": (
                    "host cdb_7_fc_cdb_8_e5 writes xdata[0x8196]=2, "
                    "calls resident CDD parser setup at 0x002e, and returns "
                    f"xdata[0x{args.mode2_xdata_address:04x}.."
                    f"0x{args.mode2_xdata_address + args.mode2_xdata_len - 1:04x}]"
                ),
                "trigger_response": (
                    f"0x{args.mode2_marker:02x} at response[0x20], selected "
                    "XDATA window at response[0x21..]"
                ),
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
                "mode2_xdata_address": args.mode2_xdata_address,
                "mode2_xdata_len": args.mode2_xdata_len,
            },
        )
    if args.gateway_cdb_bulk_with_cdd_parser_second_doorbell:
        return (
            "gateway_cdb_bulk_with_cdd_parser_second_doorbell",
            source_gateway_cdb_bulk_with_cdd_parser_second_doorbell(
                args.selector_mask,
                RESPONSE_STORAGE_BASE + args.response_offset,
                args.bulk_len,
            ),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits, except cdb_byte_8_e2 is reserved as trigger",
                "trigger": "host cdb_8_e2 calls 0x002e, mirrors 0x4a24/0x4a25 to 0x4a28/0x4a29, rings xdata[0x4a00], and calls 0x1667",
                "trigger_response": "0xd4 at response[0x20]",
                "selector_mask": args.selector_mask,
                "bulk_len": args.bulk_len,
            },
        )
    if args.gateway_byte_with_cdd_prestage_replay:
        return (
            "gateway_byte_with_cdd_prestage_replay",
            source_gateway_byte_with_cdd_prestage_replay(args.selector_mask),
            {
                "address_source": "normal: cdb_bytes_7_8_9_plus_control_low_bits",
                "trigger": "host cdb_7_fc_cdb_8_dd replays compact descriptor prestate plus CDD field package",
                "trigger_response": "0xce at response[0x20]",
                "selector_mask": args.selector_mask,
                "gateway_mode": "one_byte",
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
        "--gateway-cdb-rw",
        action="store_true",
        help="read controller gateway address CDB[7:9] + selector, and write CDB[11] first if CDB[10]=5a",
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
        "--gateway-cdb-bulk-with-cdd-descriptor-replay",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:9]=fc/dd/02 writes compact descriptor prestate plus the CDD field package",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-mapped-header",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:8]=fc/de calls the resident mapped-header helper and returns xdata[0xc000..0xc01f]",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-mapped-header-status",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:8]=fc/df calls the mapped-header helper and returns xdata[0xc000..0xc01f] plus xdata[0x4e80..0x4e9f]",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-mapped-header-status64",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:8]=fc/e0 calls the mapped-header helper and returns xdata[0xc000..0xc01f] plus xdata[0x4e80..0x4ebf]",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-mapped-source",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[10]=e3 calls 0x1717 with source CDB[7:9]+selector and returns xdata[0xc000..0xc01f]",
    )
    parser.add_argument(
        "--cdd-mapped-source-status64-only",
        action="store_true",
        help="compact diagnostic hook: CDB[10]=e3 calls 0x1717 with source CDB[7:9]+selector and returns xdata[0xc000..0xc01f] plus xdata[0x4e80..0x4ebf]; no gateway fallback",
    )
    parser.add_argument(
        "--cdd-mapped-source-window128-only",
        action="store_true",
        help="compact diagnostic hook: CDB[10]=e3 calls 0x1717 with source CDB[7:9]+selector and returns xdata[0xc000..0xc07f]; no gateway fallback",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-parser-call",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:8]=fc/e1 calls the resident CDD parser setup and returns xdata[0x4a00..0x4a3f]",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-parser-mode2-status64",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:8]=fc/e4 sets xdata[0x8196]=2, calls the resident CDD parser, and returns xdata[0x4e80..0x4ebf]",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-parser-mode2-xdata-window",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[7:8]=fc/e5 sets xdata[0x8196]=2, calls the resident CDD parser, and returns --mode2-xdata-len bytes from --mode2-xdata-address",
    )
    parser.add_argument(
        "--gateway-cdb-bulk-with-cdd-parser-second-doorbell",
        action="store_true",
        help="like --gateway-cdb-bulk, but CDB[8]=e2 calls the parser setup then rings the later 0x4a doorbell",
    )
    parser.add_argument(
        "--gateway-byte-with-cdd-prestage-replay",
        action="store_true",
        help="like --gateway-cdb-address, but CDB[7:8]=fc/dd writes compact descriptor prestate plus CDD field package",
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
    parser.add_argument("--mode2-xdata-address", type=parse_addr, default=0x4E00)
    parser.add_argument("--mode2-xdata-len", type=parse_byte, default=0x40)
    parser.add_argument("--mode2-marker", type=parse_byte, default=0xD9)
    parser.add_argument("--selector-mask", type=parse_byte, default=0x3F)
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.restore and (
        any(value is not None for value in (args.constant, args.xdata_direct, args.xdata_window))
        or args.gateway_cdb_address
        or args.gateway_cdb_rw
        or args.gateway_cdb_bulk
        or args.gateway_cdb_bulk_with_xdata_write
        or args.gateway_cdb_bulk_with_xdata_rw
        or args.gateway_cdb_bulk_with_cdd_field_replay
        or args.gateway_cdb_bulk_with_cdd_descriptor_replay
        or args.gateway_cdb_bulk_with_cdd_mapped_header
        or args.gateway_cdb_bulk_with_cdd_mapped_header_status
        or args.gateway_cdb_bulk_with_cdd_mapped_header_status64
        or args.cdd_mapped_source_status64_only
        or args.cdd_mapped_source_window128_only
        or args.gateway_cdb_bulk_with_cdd_mapped_source
        or args.gateway_cdb_bulk_with_cdd_parser_call
        or args.gateway_cdb_bulk_with_cdd_parser_mode2_status64
        or args.gateway_cdb_bulk_with_cdd_parser_mode2_xdata_window
        or args.gateway_cdb_bulk_with_cdd_parser_second_doorbell
        or args.gateway_byte_with_cdd_prestage_replay
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
