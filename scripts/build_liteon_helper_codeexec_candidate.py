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
    has_payload = args.mode in {"status-byte", "payload-hex", "immediate-bit", "movc-bit", "movx-bit"}
    mode_args: dict[str, Any] = {}
    for key in ("status_byte", "payload_hex", "value", "addr", "bit", "success_on_zero"):
        if hasattr(args, key):
            mode_args[key] = getattr(args, key)
    return {
        "status": "helper_codeexec_candidate_built",
        "name": args.name,
        "mode": args.mode,
        "mode_args": mode_args,
        "base_candidate": str(args.base_candidate),
        "hook_plain_offset": HOOK_PLAIN_OFFSET,
        "payload_plain_offset": PAYLOAD_PLAIN_OFFSET if has_payload else None,
        "payload_code_addr": PAYLOAD_CODE_ADDR if has_payload else None,
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
