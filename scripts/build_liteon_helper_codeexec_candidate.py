#!/usr/bin/env python3
"""Build late-helper code-execution profile-tail candidates.

This is a thin ergonomic wrapper around
``render_liteon_profile_tail_mutation_candidate.py``.  It keeps the currently
known safer hook point fixed:

    helper plaintext 0x02b5 / code 0x32af

and emits candidates that mutate every currentboot-key profile-tail helper
payload while keeping the staged F0 image byte-identical to the LD5M control.
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
DEFAULT_BASE_CANDIDATE = EXTRACTED / "liteon-full-currentboot-ld5m-base-candidate.json"
DEFAULT_OUT_ROOT = EXTRACTED / "helper-codeexec-candidates"

HOOK_PLAIN_OFFSET = 0x02B5
PAYLOAD_PLAIN_OFFSET = 0x0620
PAYLOAD_CODE_ADDR = 0x361A
HELPER_CODE_BASE_FROM_PLAIN = 0x2FFA
SUCCESS_STATUS_CALL_ADDR = 0x32CB


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-").lower()
    if not slug:
        raise argparse.ArgumentTypeError("name must contain at least one safe character")
    return slug


def parse_byte(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("byte value must be 0..255")
    return parsed


def parse_u16(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFFFF:
        raise argparse.ArgumentTypeError("address must be 0..0xffff")
    return parsed


def parse_u8(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("value must be 0..0xff")
    return parsed


def parse_bit(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 7:
        raise argparse.ArgumentTypeError("bit must be 0..7")
    return parsed


def compact_hex(value: str) -> str:
    compact = "".join(ch for ch in value if ch in "0123456789abcdefABCDEF")
    if not compact or len(compact) % 2:
        raise argparse.ArgumentTypeError("hex payload must contain whole bytes")
    return compact.lower()


def hex_patch(offset: int, data_hex: str) -> str:
    return f"0x{offset:x}:{data_hex}"


def ljmp(addr: int) -> str:
    return f"02{addr:04x}"


def helper_code_addr(plain_offset: int) -> int:
    return HELPER_CODE_BASE_FROM_PLAIN + plain_offset


def delay_payload(count: int) -> str:
    if count <= 0:
        return ""
    return f"7f{count:02x}7eff7dffddfedefadff6"


def status_payload(status_byte: int) -> str:
    """Return a small payload that changes the helper's success status byte.

    Original success path:

        0x32c4: LCALL 0x373c
        0x32c7: MOV R5,#0x01
        0x32c9: MOV R7,#0x04
        0x32cb: LCALL 0x3740

    The payload preserves that shape but substitutes R5, then jumps into the
    original path at 0x32cb so the remaining 0x48a0/0x3b6f/cleanup tail stays
    stock.
    """

    return (
        "12373c"  # LCALL 0x373c
        f"7d{status_byte:02x}"  # MOV R5,#status
        "7f04"  # MOV R7,#0x04
        f"02{SUCCESS_STATUS_CALL_ADDR:04x}"  # LJMP 0x32cb
    )


def acc_bit_addr(bit: int) -> int:
    return 0xE0 + bit


def branch_on_acc_bit_payload(prefix_hex: str, bit: int, *, success_on_one: bool) -> str:
    if success_on_one:
        first = 0x32C4
        second = 0x32B2
    else:
        first = 0x32B2
        second = 0x32C4
    return "".join(
        [
            prefix_hex,
            f"30{acc_bit_addr(bit):02x}03",  # JNB ACC.bit,+3
            f"02{first:04x}",
            f"02{second:04x}",
        ]
    )


def immediate_bit_payload(value: int, bit: int, *, success_on_one: bool) -> str:
    return branch_on_acc_bit_payload(f"74{value:02x}", bit, success_on_one=success_on_one)


def movc_bit_payload(addr: int, bit: int, *, success_on_one: bool) -> str:
    prefix = f"90{addr:04x}e493"  # MOV DPTR,#addr; CLR A; MOVC A,@A+DPTR
    return branch_on_acc_bit_payload(prefix, bit, success_on_one=success_on_one)


def movx_bit_payload(addr: int, bit: int, *, success_on_one: bool) -> str:
    prefix = f"90{addr:04x}e0"  # MOV DPTR,#addr; MOVX A,@DPTR
    return branch_on_acc_bit_payload(prefix, bit, success_on_one=success_on_one)


def direct_bit_payload(addr: int, bit: int, *, success_on_one: bool) -> str:
    prefix = f"e5{addr:02x}"  # MOV A,direct
    return branch_on_acc_bit_payload(prefix, bit, success_on_one=success_on_one)


def movx_byte_op_payload(addr: int, op: str, value: int) -> str:
    if op == "write":
        body = f"90{addr:04x}74{value:02x}f0"  # MOV DPTR,#addr; MOV A,#value; MOVX @DPTR,A
    else:
        opcode = {"xor": "64", "or": "44", "and": "54"}[op]
        body = f"90{addr:04x}e0{opcode}{value:02x}f0"  # MOVX A,@DPTR; op A,#value; MOVX @DPTR,A
    return body + ljmp(0x32C4)


def direct_byte_op_payload(addr: int, op: str, value: int) -> str:
    if op == "write":
        body = f"75{addr:02x}{value:02x}"  # MOV direct,#value
    else:
        opcode = {"xor": "64", "or": "44", "and": "54"}[op]
        body = f"e5{addr:02x}{opcode}{value:02x}f5{addr:02x}"  # MOV A,direct; op A,#value; MOV direct,A
    return body + ljmp(0x32C4)


def direct_bit_op_payload(bit_addr: int, op: str) -> str:
    opcode = {"clear": "c2", "set": "d2", "toggle": "b2"}[op]
    return f"{opcode}{bit_addr:02x}" + ljmp(0x32C4)


def delayed_movx_byte_op_payload(addr: int, op: str, value: int, delay_count: int) -> str:
    if op == "write":
        body = f"90{addr:04x}74{value:02x}f0"  # MOV DPTR,#addr; MOV A,#value; MOVX @DPTR,A
    else:
        opcode = {"xor": "64", "or": "44", "and": "54"}[op]
        body = f"90{addr:04x}e0{opcode}{value:02x}f0"  # MOVX A,@DPTR; op A,#value; MOVX @DPTR,A
    return body + delay_payload(delay_count) + ljmp(0x32C4)


def delayed_direct_bit_op_payload(bit_addr: int, op: str, delay_count: int) -> str:
    opcode = {"clear": "c2", "set": "d2", "toggle": "b2"}[op]
    return f"{opcode}{bit_addr:02x}" + delay_payload(delay_count) + ljmp(0x32C4)


def hold_movx_byte_payload(addr: int, value: int, hold_count: int) -> str:
    return (
        f"90{addr:04x}"  # MOV DPTR,#addr
        f"7f{hold_count:02x}"  # MOV R7,#outer
        "7eff"  # outer: MOV R6,#0xff
        "7dff"  # middle: MOV R5,#0xff
        f"74{value:02x}"  # inner: MOV A,#value
        "f0"  # MOVX @DPTR,A
        "ddfb"  # DJNZ R5,inner
        "def7"  # DJNZ R6,middle
        "dff3"  # DJNZ R7,outer
        + ljmp(0x32C4)
    )


def hold_direct_bit_payload(bit_addr: int, op: str, hold_count: int) -> str:
    opcode = {"clear": "c2", "set": "d2"}[op]
    return f"7f{hold_count:02x}7eff7dff{opcode}{bit_addr:02x}ddfcdef8dff4" + ljmp(0x32C4)


def render_command(args: argparse.Namespace, patches: list[str]) -> tuple[list[str], dict[str, Path]]:
    out_dir = args.out_root / args.name
    outputs = {
        "out_dir": out_dir,
        "candidate": out_dir / f"liteon-full-currentboot-ld5m-helper-codeexec-{args.name}-candidate.json",
        "json": out_dir / f"liteon-helper-codeexec-{args.name}.json",
        "md": out_dir / f"liteon-helper-codeexec-{args.name}.md",
    }
    cmd = [
        sys.executable,
        str(ROOT / "scripts/render_liteon_profile_tail_mutation_candidate.py"),
        "--base-candidate",
        str(args.base_candidate),
        "--all-currentboot-tails",
        "--out-dir",
        str(out_dir),
        "--out-candidate",
        str(outputs["candidate"]),
        "--out-json",
        str(outputs["json"]),
        "--out-md",
        str(outputs["md"]),
    ]
    for patch in patches:
        cmd.extend(["--patch", patch])
    return cmd, outputs


def build_report(args: argparse.Namespace, patches: list[str], outputs: dict[str, Path]) -> dict[str, Any]:
    has_payload = args.mode in {
        "status-byte",
        "payload-hex",
        "immediate-bit",
        "movc-bit",
        "movx-bit",
        "direct-bit",
        "movx-byte-op",
        "direct-byte-op",
        "direct-bit-op",
        "delay-only",
        "delayed-movx-byte-op",
        "delayed-direct-bit-op",
        "hold-movx-byte",
        "hold-direct-bit",
    }
    payload_plain_offset = getattr(args, "payload_offset", PAYLOAD_PLAIN_OFFSET) if has_payload else None
    payload_code_addr = helper_code_addr(payload_plain_offset) if payload_plain_offset is not None else None
    mode_args: dict[str, Any] = {}
    for key in (
        "status_byte",
        "payload_hex",
        "value",
        "addr",
        "bit",
        "bit_addr",
        "op",
        "success_on_zero",
        "payload_offset",
        "delay_count",
        "hold_count",
    ):
        if hasattr(args, key):
            mode_args[key] = getattr(args, key)
    return {
        "status": "helper_codeexec_candidate_built",
        "name": args.name,
        "mode": args.mode,
        "mode_args": mode_args,
        "base_candidate": str(args.base_candidate),
        "hook_plain_offset": HOOK_PLAIN_OFFSET,
        "payload_plain_offset": payload_plain_offset,
        "payload_code_addr": payload_code_addr,
        "patches": patches,
        "outputs": {key: str(value) for key, value in outputs.items()},
        "notes": [
            "Mutates every currentboot-key profile-tail helper payload.",
            "The staged F0 image remains byte-identical to the LD5M base candidate.",
            "Use short runs through event 68 while iterating on payload behavior.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, type=slugify)
    parser.add_argument("--base-candidate", type=Path, default=DEFAULT_BASE_CANDIDATE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    sub = parser.add_subparsers(dest="mode", required=True)

    status = sub.add_parser("status-byte", help="call the normal success status path with a substituted R5 byte")
    status.add_argument("--status-byte", type=parse_byte, required=True)

    sub.add_parser("force-error", help="force the original late branch into its error-status path")

    payload = sub.add_parser("payload-hex", help="install an explicit payload at 0x361a")
    payload.add_argument("--payload-hex", type=compact_hex, required=True)

    immediate = sub.add_parser("immediate-bit", help="branch to success/error based on a constant ACC bit")
    immediate.add_argument("--value", type=parse_byte, required=True)
    immediate.add_argument("--bit", type=parse_bit, required=True)
    immediate.add_argument("--success-on-zero", action="store_true")

    movc = sub.add_parser("movc-bit", help="branch based on a code-memory byte bit read with MOVC")
    movc.add_argument("--addr", type=parse_u16, required=True)
    movc.add_argument("--bit", type=parse_bit, required=True)
    movc.add_argument("--success-on-zero", action="store_true")

    movx = sub.add_parser("movx-bit", help="branch based on an xdata byte bit read with MOVX")
    movx.add_argument("--addr", type=parse_u16, required=True)
    movx.add_argument("--bit", type=parse_bit, required=True)
    movx.add_argument("--success-on-zero", action="store_true")

    direct = sub.add_parser("direct-bit", help="branch based on an 8051 direct/SFR byte bit")
    direct.add_argument("--addr", type=parse_u8, required=True)
    direct.add_argument("--bit", type=parse_bit, required=True)
    direct.add_argument("--success-on-zero", action="store_true")

    movx_op = sub.add_parser("movx-byte-op", help="write or read/modify/write one XDATA byte, then report success")
    movx_op.add_argument("--addr", type=parse_u16, required=True)
    movx_op.add_argument("--op", choices=("write", "xor", "or", "and"), required=True)
    movx_op.add_argument("--value", type=parse_byte, required=True)

    direct_op = sub.add_parser("direct-byte-op", help="write or read/modify/write one direct/SFR byte, then report success")
    direct_op.add_argument("--addr", type=parse_u8, required=True)
    direct_op.add_argument("--op", choices=("write", "xor", "or", "and"), required=True)
    direct_op.add_argument("--value", type=parse_byte, required=True)

    bit_op = sub.add_parser("direct-bit-op", help="set, clear, or toggle one bit-addressable direct/SFR bit")
    bit_op.add_argument("--bit-addr", type=parse_u8, required=True)
    bit_op.add_argument("--op", choices=("clear", "set", "toggle"), required=True)

    delay = sub.add_parser("delay-only", help="hold the known helper hook for a visible timing window, then report success")
    delay.add_argument("--payload-offset", type=parse_u16, default=0x0600)
    delay.add_argument("--delay-count", type=parse_byte, default=0x40)

    delayed_movx = sub.add_parser(
        "delayed-movx-byte-op",
        help="write or read/modify/write one XDATA byte, delay, then report success",
    )
    delayed_movx.add_argument("--addr", type=parse_u16, required=True)
    delayed_movx.add_argument("--op", choices=("write", "xor", "or", "and"), required=True)
    delayed_movx.add_argument("--value", type=parse_byte, required=True)
    delayed_movx.add_argument("--payload-offset", type=parse_u16, default=0x0600)
    delayed_movx.add_argument("--delay-count", type=parse_byte, default=0x40)

    delayed_bit = sub.add_parser(
        "delayed-direct-bit-op",
        help="set, clear, or toggle one bit-addressable direct/SFR bit, delay, then report success",
    )
    delayed_bit.add_argument("--bit-addr", type=parse_u8, required=True)
    delayed_bit.add_argument("--op", choices=("clear", "set", "toggle"), required=True)
    delayed_bit.add_argument("--payload-offset", type=parse_u16, default=0x0600)
    delayed_bit.add_argument("--delay-count", type=parse_byte, default=0x40)

    hold_movx = sub.add_parser(
        "hold-movx-byte",
        help="repeatedly write one XDATA byte for a Pico-visible hold window, then report success",
    )
    hold_movx.add_argument("--addr", type=parse_u16, required=True)
    hold_movx.add_argument("--value", type=parse_byte, required=True)
    hold_movx.add_argument("--payload-offset", type=parse_u16, default=0x0600)
    hold_movx.add_argument("--hold-count", type=parse_byte, default=0x40)

    hold_bit = sub.add_parser(
        "hold-direct-bit",
        help="repeatedly set or clear one bit-addressable direct/SFR bit, then report success",
    )
    hold_bit.add_argument("--bit-addr", type=parse_u8, required=True)
    hold_bit.add_argument("--op", choices=("clear", "set"), required=True)
    hold_bit.add_argument("--payload-offset", type=parse_u16, default=0x0600)
    hold_bit.add_argument("--hold-count", type=parse_byte, default=0x40)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "status-byte":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(PAYLOAD_PLAIN_OFFSET, status_payload(args.status_byte)),
        ]
    elif args.mode == "force-error":
        patches = [hex_patch(HOOK_PLAIN_OFFSET, ljmp(0x32B2))]
    elif args.mode == "payload-hex":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(PAYLOAD_PLAIN_OFFSET, args.payload_hex),
        ]
    elif args.mode == "immediate-bit":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(
                PAYLOAD_PLAIN_OFFSET,
                immediate_bit_payload(
                    args.value,
                    args.bit,
                    success_on_one=not args.success_on_zero,
                ),
            ),
        ]
    elif args.mode == "movc-bit":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(
                PAYLOAD_PLAIN_OFFSET,
                movc_bit_payload(
                    args.addr,
                    args.bit,
                    success_on_one=not args.success_on_zero,
                ),
            ),
        ]
    elif args.mode == "movx-bit":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(
                PAYLOAD_PLAIN_OFFSET,
                movx_bit_payload(
                    args.addr,
                    args.bit,
                    success_on_one=not args.success_on_zero,
                ),
            ),
        ]
    elif args.mode == "direct-bit":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(
                PAYLOAD_PLAIN_OFFSET,
                direct_bit_payload(
                    args.addr,
                    args.bit,
                    success_on_one=not args.success_on_zero,
                ),
            ),
        ]
    elif args.mode == "movx-byte-op":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(PAYLOAD_PLAIN_OFFSET, movx_byte_op_payload(args.addr, args.op, args.value)),
        ]
    elif args.mode == "direct-byte-op":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(PAYLOAD_PLAIN_OFFSET, direct_byte_op_payload(args.addr, args.op, args.value)),
        ]
    elif args.mode == "direct-bit-op":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(PAYLOAD_CODE_ADDR)),
            hex_patch(PAYLOAD_PLAIN_OFFSET, direct_bit_op_payload(args.bit_addr, args.op)),
        ]
    elif args.mode == "delay-only":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(helper_code_addr(args.payload_offset))),
            hex_patch(args.payload_offset, delay_payload(args.delay_count) + ljmp(0x32C4)),
        ]
    elif args.mode == "delayed-movx-byte-op":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(helper_code_addr(args.payload_offset))),
            hex_patch(
                args.payload_offset,
                delayed_movx_byte_op_payload(args.addr, args.op, args.value, args.delay_count),
            ),
        ]
    elif args.mode == "delayed-direct-bit-op":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(helper_code_addr(args.payload_offset))),
            hex_patch(
                args.payload_offset,
                delayed_direct_bit_op_payload(args.bit_addr, args.op, args.delay_count),
            ),
        ]
    elif args.mode == "hold-movx-byte":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(helper_code_addr(args.payload_offset))),
            hex_patch(args.payload_offset, hold_movx_byte_payload(args.addr, args.value, args.hold_count)),
        ]
    elif args.mode == "hold-direct-bit":
        patches = [
            hex_patch(HOOK_PLAIN_OFFSET, ljmp(helper_code_addr(args.payload_offset))),
            hex_patch(args.payload_offset, hold_direct_bit_payload(args.bit_addr, args.op, args.hold_count)),
        ]
    else:  # pragma: no cover - argparse prevents this.
        raise AssertionError(args.mode)

    cmd, outputs = render_command(args, patches)
    subprocess.run(cmd, check=True)
    report = build_report(args, patches, outputs)
    report_path = outputs["out_dir"] / f"liteon-helper-codeexec-{args.name}-wrapper.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
