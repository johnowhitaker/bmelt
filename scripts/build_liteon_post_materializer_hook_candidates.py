#!/usr/bin/env python3
"""Build safer resident-prefix materializer hook candidates.

No drive commands are sent by this script.

The first Drive #3 materializer hook patched the call at 0x41de:

    LCALL 0x002e
    JNC   0x422f

The marker variant programmed cleanly but was not visible; the delay variant
made the drive stop enumerating as PLDS after cold boot. Raw assembly shows why
that site is fragile: it runs before the 0x40b2 continuation restores controller
shadow state and may call FUN_CODE_111a(2).

This builder prepares later, non-blocking marker variants for a future fresh
drive. They still carry risk, but they avoid blocking in the middle of the
materializer transaction.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "references/firmware/extracted"
BASE_IMAGE = EXTRACTED / "ld5m-f0-window-0x00000-0x100000.bin"
OUT_ROOT = EXTRACTED / "helper-bypass-candidates"
BUILD_HELPER = ROOT / "scripts/build_liteon_helper_bypass_candidate.py"

CAVE_ADDR = 0x6EE3
CAVE_LEN = 0xDD
MARKER_ADDR = 0x074030
MARKER_VALUE = 0x5A

# Normal public work-window bridge chunks observed at +0x7100/+0x7140/+0x7180
# contain a clamp immediate in the response-offset path:
#
#   ... 90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 0e f0 ...
#
# Changing the `MOV A,#0x0e` immediate to 0x07 should affect only high public
# READ BUFFER offsets that stock would clamp near 0x0e0000. If this RAM patch
# lands after materialization, a host READ BUFFER out-of-range probe should
# return a different window without changing ordinary 0x070000..0x07ffff reads.
#
# The bridge chunk rotates in the public window. These are the six most common
# observed file-relative clamp-immediate offsets from the normal work-window
# corpus, plus the public 0x070000 base.
BRIDGE_CLAMP_IMMEDIATE_ADDRS = [
    0x077156,
    0x077196,
    0x0770E6,
    0x077026,
    0x0770A6,
    0x077066,
]
BRIDGE_CLAMP_PATCH_VALUE = 0x07


def lcall(addr: int) -> bytes:
    return bytes([0x12, (addr >> 8) & 0xFF, addr & 0xFF])


def mov_dptr(addr: int) -> bytes:
    return bytes([0x90, (addr >> 8) & 0xFF, addr & 0xFF])


def mov_a_imm(value: int) -> bytes:
    return bytes([0x74, value & 0xFF])


def wait_controller_ready() -> bytes:
    # 90 4000 ; E0 ; 20 E7 F9
    return mov_dptr(0x4000) + bytes([0xE0, 0x20, 0xE7, 0xF9])


def write_controller_public_byte(addr: int, value: int) -> bytes:
    return b"".join(
        [
            wait_controller_ready(),
            mov_dptr(0x4095),
            mov_a_imm((addr >> 16) & 0xFF),
            bytes([0xF0, 0xA3]),
            mov_a_imm((addr >> 8) & 0xFF),
            bytes([0xF0, 0xA3]),
            mov_a_imm(addr & 0xFF),
            bytes([0xF0]),
            wait_controller_ready(),
            mov_dptr(0x4098),
            mov_a_imm(value),
            bytes([0xF0]),
        ]
    )


def push_direct(addr: int) -> bytes:
    return bytes([0xC0, addr & 0xFF])


def pop_direct(addr: int) -> bytes:
    return bytes([0xD0, addr & 0xFF])


def patch_arg(offset: int, data: bytes) -> str:
    return f"0x{offset:x}:{data.hex()}"


def stock_40b2_return_payload() -> bytes:
    """Replace 0x422c `CLR A; MOV PSW,A; RET` with `LCALL cave; RET`.

    The cave writes a tiny public marker after the materializer continuation,
    then restores the stock return state (`A=0`, `PSW=0`) and returns to the
    original RET at 0x422f.
    """

    return b"".join(
        [
            write_controller_public_byte(MARKER_ADDR, MARKER_VALUE),
            bytes([0xE4, 0xF5, 0xD0, 0x22]),  # CLR A; MOV PSW,A; RET
        ]
    )


def post_40b2_call_payload() -> bytes:
    """Replace caller 0x26fb `LCALL 0x40b2` with a wrapper.

    This runs the original 0x40b2, then writes the same marker while preserving
    the caller-visible PSW/ACC/DPTR state. It is higher risk than the return
    epilogue hook because 0x26fb may be in a repeated service loop.
    """

    return b"".join(
        [
            lcall(0x40B2),
            push_direct(0xD0),  # PSW
            push_direct(0xE0),  # ACC
            push_direct(0x83),  # DPH
            push_direct(0x82),  # DPL
            write_controller_public_byte(MARKER_ADDR, MARKER_VALUE),
            pop_direct(0x82),
            pop_direct(0x83),
            pop_direct(0xE0),
            pop_direct(0xD0),
            bytes([0x22]),  # RET
        ]
    )


def runtime_bridge_clamp_payload() -> bytes:
    """Patch materialized normal READ BUFFER bridge clamp immediates in RAM."""

    return b"".join(
        [write_controller_public_byte(addr, BRIDGE_CLAMP_PATCH_VALUE) for addr in BRIDGE_CLAMP_IMMEDIATE_ADDRS]
        + [
            bytes([0xE4, 0xF5, 0xD0, 0x22]),  # CLR A; MOV PSW,A; RET
        ]
    )


def check_stock_bytes(base: bytes, offset: int, expected: bytes) -> None:
    actual = base[offset : offset + len(expected)]
    if actual != expected:
        raise ValueError(
            f"stock byte check failed at 0x{offset:04x}: "
            f"expected {expected.hex()}, got {actual.hex()}"
        )


def run_builder(name: str, patches: list[tuple[int, bytes]], dry_run: bool) -> None:
    cmd = [
        sys.executable,
        str(BUILD_HELPER),
        "--name",
        name,
        "--out-dir",
        str(OUT_ROOT),
        "--auto-helper-range",
        "--include-pre-tail",
    ]
    for offset, payload in patches:
        cmd.extend(["--patch", patch_arg(offset, payload)])

    print("+ " + " ".join(cmd))
    if dry_run:
        return
    subprocess.run(cmd, cwd=ROOT, check=True)


def write_note(dry_run: bool) -> None:
    if dry_run:
        return
    note = OUT_ROOT / "post-materializer-hook-candidates-20260506.md"
    note.write_text(
        "\n".join(
            [
                "# Post-Materializer Hook Candidates - 2026-05-06",
                "",
                "Offline generated only; no drive commands were sent.",
                "",
                "These candidates are follow-ups to the Drive #3 `0x41de`",
                "materializer test. The delay at `0x41de` wedged normal",
                "enumeration, so these variants move the side effect later and",
                "avoid blocking in the middle of the materializer transaction.",
                "",
                "## Candidates",
                "",
                "- `post-materializer-ret-marker-074030`: patches",
                "  `0x422c` (`CLR A; MOV PSW,A; RET`) to call the cave,",
                "  then returns through the original `RET`. This is the",
                "  preferred next fresh-drive test because it runs after the",
                "  `0x40b2` materializer continuation.",
                "- `post-materializer-ret-marker-074030-restore`: rewrites",
                "  that hook and cave region back to stock.",
                "- `post-materializer-runtime-bridge-clamp07`: patches the",
                "  same return epilogue but writes `0x07` into materialized",
                "  normal response-bridge clamp immediates at the six most",
                "  common rotating public slots:",
                "  `0x077156`, `0x077196`, `0x0770e6`, `0x077026`,",
                "  `0x0770a6`, and `0x077066`. This is a RAM patch of",
                "  materialized runtime code, not a CDD source mutation.",
                "  Expected proof is that a",
                "  high-offset `READ BUFFER id=01` probe changes direct",
                "  response bytes while ordinary `0x070000` reads still work.",
                "- `post-materializer-runtime-bridge-clamp07-restore`: rewrites",
                "  the resident hook and cave region back to stock. The runtime",
                "  bridge patch is volatile and should disappear after a cold",
                "  boot with the stock resident restored.",
                "- `post-40b2-caller-marker-074030`: patches the caller at",
                "  `0x26fb` to call original `0x40b2`, then write the marker",
                "  while preserving PSW/ACC/DPTR. This is more likely to run",
                "  after normal startup, but may execute repeatedly, so keep it",
                "  second.",
                "- `post-40b2-caller-marker-074030-restore`: rewrites the",
                "  caller wrapper and cave region back to stock.",
                "",
                "## Live Rules",
                "",
                "- Do not run any candidate on the current `Generic External`",
                "  bridge fallback.",
                "- On the next PLDS-visible drive, baseline `READ BUFFER id=01`",
                "  at `0x070000`, `0x074000`, and `0x0f0000` first.",
                "- Prefer the runtime bridge clamp candidate if the high-offset",
                "  baseline is stable; it has a direct response proof signal.",
                "- Run the matching restore candidate and cold boot as soon as",
                "  any direct response change is observed.",
                "- Do not use a delay loop at `0x41de` again.",
                "",
            ]
        )
        + "\n"
    )
    print(f"wrote {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = BASE_IMAGE.read_bytes()
    cave_original = base[CAVE_ADDR : CAVE_ADDR + CAVE_LEN]
    if cave_original != b"\xff" * CAVE_LEN:
        raise ValueError(f"cave 0x{CAVE_ADDR:04x}..0x{CAVE_ADDR + CAVE_LEN:04x} is not all FF")

    check_stock_bytes(base, 0x422C, bytes.fromhex("e4f5d022"))
    check_stock_bytes(base, 0x26FB, lcall(0x40B2))

    ret_payload = stock_40b2_return_payload()
    bridge_payload = runtime_bridge_clamp_payload()
    caller_payload = post_40b2_call_payload()
    if len(ret_payload) > CAVE_LEN:
        raise ValueError("return payload exceeds cave")
    if len(bridge_payload) > CAVE_LEN:
        raise ValueError("bridge payload exceeds cave")
    if len(caller_payload) > CAVE_LEN:
        raise ValueError("caller payload exceeds cave")

    run_builder(
        "post-materializer-ret-marker-074030",
        [(0x422C, lcall(CAVE_ADDR)), (CAVE_ADDR, ret_payload)],
        args.dry_run,
    )
    run_builder(
        "post-materializer-ret-marker-074030-restore",
        [(0x422C, bytes.fromhex("e4f5d0")), (CAVE_ADDR, b"\xff" * len(ret_payload))],
        args.dry_run,
    )
    run_builder(
        "post-materializer-runtime-bridge-clamp07",
        [(0x422C, lcall(CAVE_ADDR)), (CAVE_ADDR, bridge_payload)],
        args.dry_run,
    )
    run_builder(
        "post-materializer-runtime-bridge-clamp07-restore",
        [(0x422C, bytes.fromhex("e4f5d0")), (CAVE_ADDR, b"\xff" * len(bridge_payload))],
        args.dry_run,
    )
    run_builder(
        "post-40b2-caller-marker-074030",
        [(0x26FB, lcall(CAVE_ADDR)), (CAVE_ADDR, caller_payload)],
        args.dry_run,
    )
    run_builder(
        "post-40b2-caller-marker-074030-restore",
        [(0x26FB, lcall(0x40B2)), (CAVE_ADDR, b"\xff" * len(caller_payload))],
        args.dry_run,
    )
    write_note(args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
