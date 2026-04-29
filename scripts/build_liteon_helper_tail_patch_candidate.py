#!/usr/bin/env python3
"""Build helper candidates that patch the final helper success tail.

The late code-execution hook at ``0x32af`` is useful for branching and timing,
but the stock success path can still run after a payload and overwrite hardware
state.  This builder targets the final helper return sequence instead:

    helper plaintext 0x02fc / code 0x32f6

The original 10-byte sequence clears a helper status bit and returns.  These
probes replace it with a tiny action plus padding and a final RET, so the action
happens after the normal helper cleanup.
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
TAIL_PLAIN_OFFSET = 0x02FC
TAIL_PATCH_LEN = 10
DEFAULT_PAYLOAD_PLAIN_OFFSET = 0x0600
HELPER_CODE_BASE_FROM_PLAIN = 0x2FFA


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-").lower()
    if not slug:
        raise argparse.ArgumentTypeError("name must contain at least one safe character")
    return slug


def parse_byte(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("value must be 0..255")
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


def pad_ret(body_hex: str) -> str:
    data = bytes.fromhex(body_hex)
    if len(data) > TAIL_PATCH_LEN:
        raise ValueError(f"tail patch body is {len(data)} bytes, max {TAIL_PATCH_LEN}")
    if not data or data[-1] != 0x22:
        data += b"\x22"
    if len(data) > TAIL_PATCH_LEN:
        raise ValueError(f"tail patch body plus RET is {len(data)} bytes, max {TAIL_PATCH_LEN}")
    return (data + b"\x00" * (TAIL_PATCH_LEN - len(data))).hex()


def ljmp(addr: int) -> str:
    return f"02{addr:04x}"


def delay_payload(count: int) -> str:
    if count <= 0:
        return ""
    return f"7f{count:02x}7eff7dffddfedefadff6"


def movx_byte_op_payload(addr: int, op: str, value: int) -> str:
    if op == "write":
        body = f"90{addr:04x}74{value:02x}f0"  # MOV DPTR,#addr; MOV A,#value; MOVX @DPTR,A
    else:
        opcode = {"xor": "64", "or": "44", "and": "54"}[op]
        body = f"90{addr:04x}e0{opcode}{value:02x}f0"  # MOVX A,@DPTR; op A,#value; MOVX @DPTR,A
    return pad_ret(body)


def direct_bit_op_payload(bit_addr: int, op: str) -> str:
    opcode = {"clear": "c2", "set": "d2", "toggle": "b2"}[op]
    return pad_ret(f"{opcode}{bit_addr:02x}")


def delayed_movx_byte_op_payload(addr: int, op: str, value: int, delay_count: int) -> str:
    if op == "write":
        body = f"90{addr:04x}74{value:02x}f0"
    else:
        opcode = {"xor": "64", "or": "44", "and": "54"}[op]
        body = f"90{addr:04x}e0{opcode}{value:02x}f0"
    return body + delay_payload(delay_count) + "22"


def delayed_direct_bit_op_payload(bit_addr: int, op: str, delay_count: int) -> str:
    opcode = {"clear": "c2", "set": "d2", "toggle": "b2"}[op]
    return f"{opcode}{bit_addr:02x}" + delay_payload(delay_count) + "22"


def tail_trampoline_patch(payload_offset: int) -> str:
    return pad_ret(ljmp(HELPER_CODE_BASE_FROM_PLAIN + payload_offset))


def render_command(args: argparse.Namespace, patches: list[tuple[int, str]]) -> tuple[list[str], dict[str, Path]]:
    out_dir = args.out_root / args.name
    outputs = {
        "out_dir": out_dir,
        "candidate": out_dir / f"liteon-full-currentboot-ld5m-helper-tail-{args.name}-candidate.json",
        "json": out_dir / f"liteon-helper-tail-{args.name}.json",
        "md": out_dir / f"liteon-helper-tail-{args.name}.md",
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
    for offset, patch_hex in patches:
        cmd.extend(["--patch", f"0x{offset:x}:{patch_hex}"])
    return cmd, outputs


def build_report(args: argparse.Namespace, patches: list[tuple[int, str]], outputs: dict[str, Path]) -> dict[str, Any]:
    mode_args: dict[str, Any] = {}
    for key in ("addr", "bit_addr", "op", "value", "payload_offset", "delay_count"):
        if hasattr(args, key):
            mode_args[key] = getattr(args, key)
    return {
        "status": "helper_tail_patch_candidate_built",
        "name": args.name,
        "mode": args.mode,
        "mode_args": mode_args,
        "tail_plain_offset": TAIL_PLAIN_OFFSET,
        "tail_code_addr": HELPER_CODE_BASE_FROM_PLAIN + TAIL_PLAIN_OFFSET,
        "tail_patch_len": TAIL_PATCH_LEN,
        "patches": [
            {
                "plain_offset": offset,
                "code_addr": HELPER_CODE_BASE_FROM_PLAIN + offset,
                "patch_hex": patch_hex,
            }
            for offset, patch_hex in patches
        ],
        "outputs": {key: str(value) for key, value in outputs.items()},
        "notes": [
            "Mutates every currentboot-key profile-tail helper payload.",
            "The staged F0 image remains byte-identical to the LD5M base candidate.",
            "The action replaces the final helper return tail and runs after stock cleanup.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, type=slugify)
    parser.add_argument("--base-candidate", type=Path, default=DEFAULT_BASE_CANDIDATE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    sub = parser.add_subparsers(dest="mode", required=True)

    movx_op = sub.add_parser("movx-byte-op", help="write or read/modify/write one XDATA byte before RET")
    movx_op.add_argument("--addr", type=parse_u16, required=True)
    movx_op.add_argument("--op", choices=("write", "xor", "or", "and"), required=True)
    movx_op.add_argument("--value", type=parse_byte, required=True)

    bit_op = sub.add_parser("direct-bit-op", help="set, clear, or toggle one bit-addressable direct/SFR bit before RET")
    bit_op.add_argument("--bit-addr", type=parse_u8, required=True)
    bit_op.add_argument("--op", choices=("clear", "set", "toggle"), required=True)

    delayed_movx = sub.add_parser(
        "delayed-movx-byte-op",
        help="tail-jump to a payload that writes one XDATA byte, delays, then returns",
    )
    delayed_movx.add_argument("--addr", type=parse_u16, required=True)
    delayed_movx.add_argument("--op", choices=("write", "xor", "or", "and"), required=True)
    delayed_movx.add_argument("--value", type=parse_byte, required=True)
    delayed_movx.add_argument("--payload-offset", type=parse_u16, default=DEFAULT_PAYLOAD_PLAIN_OFFSET)
    delayed_movx.add_argument("--delay-count", type=parse_byte, default=0x40)

    delayed_bit = sub.add_parser(
        "delayed-direct-bit-op",
        help="tail-jump to a payload that changes one direct/SFR bit, delays, then returns",
    )
    delayed_bit.add_argument("--bit-addr", type=parse_u8, required=True)
    delayed_bit.add_argument("--op", choices=("clear", "set", "toggle"), required=True)
    delayed_bit.add_argument("--payload-offset", type=parse_u16, default=0x0620)
    delayed_bit.add_argument("--delay-count", type=parse_byte, default=0x40)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "movx-byte-op":
        patches = [(TAIL_PLAIN_OFFSET, movx_byte_op_payload(args.addr, args.op, args.value))]
    elif args.mode == "direct-bit-op":
        patches = [(TAIL_PLAIN_OFFSET, direct_bit_op_payload(args.bit_addr, args.op))]
    elif args.mode == "delayed-movx-byte-op":
        patches = [
            (TAIL_PLAIN_OFFSET, tail_trampoline_patch(args.payload_offset)),
            (
                args.payload_offset,
                delayed_movx_byte_op_payload(args.addr, args.op, args.value, args.delay_count),
            ),
        ]
    elif args.mode == "delayed-direct-bit-op":
        patches = [
            (TAIL_PLAIN_OFFSET, tail_trampoline_patch(args.payload_offset)),
            (
                args.payload_offset,
                delayed_direct_bit_op_payload(args.bit_addr, args.op, args.delay_count),
            ),
        ]
    else:  # pragma: no cover - argparse prevents this.
        raise AssertionError(args.mode)

    cmd, outputs = render_command(args, patches)
    subprocess.run(cmd, check=True)
    report = build_report(args, patches, outputs)
    report_path = outputs["out_dir"] / f"liteon-helper-tail-{args.name}-wrapper.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
