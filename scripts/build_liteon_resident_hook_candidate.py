#!/usr/bin/env python3
"""Build persistent resident-code hook candidates via the helper bypass.

The helper-bypass writer can persist arbitrary F0 bytes.  This wrapper keeps a
small normal-mode hook recipe reproducible: replace the first instruction at a
chosen resident 8051 handler with ``LJMP cave``, run a small payload from the
existing FF cave near ``0x6ee3``, then execute the overwritten bytes and jump
back to the original handler.

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
DEFAULT_OUT_DIR = EXTRACTED / "resident-hook-candidates"
DEFAULT_CAVE_ADDR = 0x6EE3


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


def patch_arg(offset: int, data: bytes) -> str:
    return f"0x{offset:x}:{data.hex()}"


def ljmp(addr: int) -> bytes:
    return bytes([0x02, (addr >> 8) & 0xFF, addr & 0xFF])


def delay_payload(count: int) -> bytes:
    if count <= 0:
        return b""
    return bytes.fromhex(f"7f{count:02x}7eff7dffddfedefadff6")


def build_hook_payload(base: bytes, args: argparse.Namespace) -> dict[str, Any]:
    if args.hook_len != 3:
        raise ValueError("only 3-byte hooks are currently supported")
    original = base[args.hook_addr : args.hook_addr + args.hook_len]
    if len(original) != args.hook_len:
        raise ValueError("hook bytes are outside base image")
    cave_original = base[args.cave_addr : args.cave_addr + args.cave_len]
    if cave_original != b"\xff" * args.cave_len:
        raise ValueError(
            f"cave 0x{args.cave_addr:04x}..0x{args.cave_addr + args.cave_len:04x} is not all FF"
        )

    payload = delay_payload(args.delay_count) + original + ljmp(args.resume_addr)
    if len(payload) > args.cave_len:
        raise ValueError(f"payload is {len(payload)} bytes, cave limit is {args.cave_len}")
    return {
        "hook_patch": patch_arg(args.hook_addr, ljmp(args.cave_addr)),
        "cave_patch": patch_arg(args.cave_addr, payload),
        "original_hook_bytes": original.hex(),
        "payload": payload.hex(),
        "payload_len": len(payload),
    }


def render_command(args: argparse.Namespace, hook: dict[str, Any]) -> tuple[list[str], Path]:
    name = f"resident-hook-{args.name}"
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


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, text=True)


def write_report(args: argparse.Namespace, hook: dict[str, Any], out_dir: Path, cmd: list[str]) -> None:
    report = {
        "status": "resident_hook_candidate",
        "name": args.name,
        "base_image": str(args.base_image),
        "hook_addr": args.hook_addr,
        "hook_len": args.hook_len,
        "resume_addr": args.resume_addr,
        "cave_addr": args.cave_addr,
        "cave_len": args.cave_len,
        "delay_count": args.delay_count,
        **hook,
        "build_command": cmd,
        "notes": [
            "Persistent F0 bytes are written by build_liteon_helper_bypass_candidate.py.",
            "The first proof target is host-visible timing on a normal-mode SCSI command.",
            "Default hook 0x5c72 is the REQUEST SENSE handler; trigger with SCSI opcode 0x03.",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{args.name}.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    lines = [
        f"# LiteOn Resident Hook Candidate: {args.name}",
        "",
        f"- hook address: `0x{args.hook_addr:04x}`",
        f"- resume address: `0x{args.resume_addr:04x}`",
        f"- cave address: `0x{args.cave_addr:04x}`",
        f"- delay count: `0x{args.delay_count:02x}`",
        f"- original hook bytes: `{hook['original_hook_bytes']}`",
        f"- hook patch: `{hook['hook_patch']}`",
        f"- cave patch: `{hook['cave_patch']}`",
        "",
        "Build command:",
        "",
        "```sh",
        " ".join(cmd),
        "```",
        "",
        "Default live trigger after persistence:",
        "",
        "```sh",
        "sg_raw -r 18 /dev/sg1 03 00 00 00 12 00 00 00 00 00 00 00",
        "```",
    ]
    (out_dir / f"{args.name}.md").write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, type=slugify)
    parser.add_argument("--base-image", type=Path, default=DEFAULT_BASE_IMAGE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--hook-addr", type=parse_addr, default=0x5C72)
    parser.add_argument("--hook-len", type=int, default=3)
    parser.add_argument("--resume-addr", type=parse_addr)
    parser.add_argument("--cave-addr", type=parse_addr, default=DEFAULT_CAVE_ADDR)
    parser.add_argument("--cave-len", type=int, default=0x80)
    parser.add_argument("--delay-count", type=parse_byte, default=0x20)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.resume_addr is None:
        args.resume_addr = args.hook_addr + args.hook_len
    base = args.base_image.read_bytes()
    hook = build_hook_payload(base, args)
    cmd, out_dir = render_command(args, hook)
    write_report(args, hook, out_dir, cmd)
    if args.dry_run:
        print(json.dumps(hook, indent=2, sort_keys=True))
        print(f"wrote {out_dir}")
        return 0
    run_command(cmd)
    print(f"wrote {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
