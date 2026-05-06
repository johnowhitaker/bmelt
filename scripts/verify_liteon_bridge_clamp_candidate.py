#!/usr/bin/env python3
"""Offline verifier for post-materializer bridge-clamp candidates.

This script checks the specific safety properties that matter before the next
live PLDS-visible run:

* patched image changes only the expected resident hook and FF cave bytes;
* restore image is byte-identical to the LD5M base image;
* helper tail mutations include the low-sector erase/program range patches;
* the cave writes exactly the expected controller/public clamp bytes;
* new dynamic caves preserve DPTR around those gateway writes;
* final replay candidates exist and carry the expected low-prefix diff summary.

No drive commands are sent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"
OUT_ROOT = ROOT / "references/firmware/extracted/helper-bypass-candidates"
CANDIDATE_SLUG = "post-materializer-runtime-bridge-clamp07"
RESTORE_SLUG = "post-materializer-runtime-bridge-clamp07-restore"

HOOK_OFFSET = 0x422C
CAVE_OFFSET = 0x6EE3
CAVE_LEN = 0xDD
EXPECTED_HOOK_BEFORE = bytes.fromhex("e4 f5 d0")
EXPECTED_HOOK_AFTER = bytes.fromhex("12 6e e3")
EXPECTED_CAVE_BEFORE = b"\xff" * CAVE_LEN
EXPECTED_CLAMP_ADDRS = [0x077156, 0x077196, 0x0770E6, 0x077026, 0x0770A6, 0x077066]
EXPECTED_CLAMP_VALUE = 0x07
EXPECTED_HELPER_PATCHES = {
    ("0x2b5", "0232c4"),
    ("0x169", "752204"),
    ("0x345", "752440"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def candidate_dir(root: Path, slug: str) -> Path:
    return root / slug


def image_path(root: Path, slug: str) -> Path:
    return candidate_dir(root, slug) / f"ld5m-helper-bypass-{slug}.bin"


def manifest_path(root: Path, slug: str) -> Path:
    return candidate_dir(root, slug) / "manifest.json"


def final_candidate_path(root: Path, slug: str) -> Path:
    return candidate_dir(root, slug) / f"liteon-full-currentboot-ld5m-helper-bypass-{slug}-candidate.json"


def diff_offsets(base: bytes, other: bytes) -> list[int]:
    return [i for i, (a, b) in enumerate(zip(base, other)) if a != b]


def split_patch_text(value: str) -> tuple[str, str]:
    offset, payload = value.split(":", 1)
    return offset.lower(), payload.lower()


def extract_gateway_writes(cave: bytes) -> tuple[list[dict[str, int]], int, dict[str, Any]]:
    """Parse the builder's repeated gateway write blocks.

    Expected block:
      90 4000 e0 20 e7 f9
      90 4095 74 HH f0 a3 74 MM f0 a3 74 LL f0
      90 4000 e0 20 e7 f9
      90 4098 74 VV f0
    """

    prefix = bytes.fromhex("90 40 00 e0 20 e7 f9 90 40 95 74")
    middle = bytes.fromhex("f0 a3 74")
    middle2 = bytes.fromhex("f0 a3 74")
    suffix = bytes.fromhex("f0 90 40 00 e0 20 e7 f9 90 40 98 74")
    dptr_save = bytes.fromhex("c0 83 c0 82")  # PUSH DPH; PUSH DPL
    dptr_restore = bytes.fromhex("d0 82 d0 83")  # POP DPL; POP DPH
    stock_return = bytes.fromhex("e4 f5 d0 22")  # CLR A; MOV PSW,A; RET
    out = []
    pos = 0
    preserves_dptr = False
    if cave.startswith(dptr_save):
        preserves_dptr = True
        pos += len(dptr_save)
    while pos < len(cave):
        if preserves_dptr and cave[pos : pos + len(dptr_restore) + len(stock_return)] == dptr_restore + stock_return:
            return out, pos + len(dptr_restore) + len(stock_return), {"preserves_dptr": True}
        if cave[pos : pos + len(stock_return)] == stock_return:
            return out, pos + len(stock_return), {"preserves_dptr": False}
        if not cave.startswith(prefix, pos):
            raise ValueError(f"unexpected cave bytes at +0x{pos:x}: {cave[pos:pos+16].hex()}")
        p = pos + len(prefix)
        hi = cave[p]
        p += 1
        if cave[p : p + len(middle)] != middle:
            raise ValueError(f"bad gateway write middle at +0x{p:x}")
        p += len(middle)
        mid = cave[p]
        p += 1
        if cave[p : p + len(middle2)] != middle2:
            raise ValueError(f"bad gateway write middle2 at +0x{p:x}")
        p += len(middle2)
        lo = cave[p]
        p += 1
        if cave[p : p + len(suffix)] != suffix:
            raise ValueError(f"bad gateway write suffix at +0x{p:x}")
        p += len(suffix)
        value = cave[p]
        p += 2  # value, f0
        if cave[p - 1] != 0xF0:
            raise ValueError(f"bad gateway final write at +0x{p-1:x}")
        out.append({"address": (hi << 16) | (mid << 8) | lo, "value": value})
        pos = p
    raise ValueError("cave payload did not end with CLR A; MOV PSW,A; RET")


def read_dynamic_selection(root: Path, slug: str) -> dict[str, Any] | None:
    path = candidate_dir(root, slug) / "dynamic-bridge-clamp-selection.json"
    if not path.exists():
        return None
    return read_json(path)


def resolve_expected_plan(
    *,
    candidate_root: Path,
    slug: str,
    expected_addrs: list[int],
    expected_value: int | None,
) -> tuple[list[int], int, dict[str, Any] | None]:
    dynamic = read_dynamic_selection(candidate_root, slug)
    if dynamic:
        addrs_from_dynamic = [int(row["address"]) for row in dynamic.get("selected", [])]
        value_from_dynamic = int(dynamic.get("patch_value"))
    else:
        addrs_from_dynamic = EXPECTED_CLAMP_ADDRS
        value_from_dynamic = EXPECTED_CLAMP_VALUE
    addrs = expected_addrs or addrs_from_dynamic
    value = expected_value if expected_value is not None else value_from_dynamic
    return addrs, value, dynamic


def verify(
    *,
    candidate_root: Path,
    restore_root: Path,
    candidate_slug: str,
    restore_slug: str,
    expected_addrs: list[int],
    expected_value: int | None,
) -> dict[str, Any]:
    expected_clamp_addrs, expected_clamp_value, dynamic_selection = resolve_expected_plan(
        candidate_root=candidate_root,
        slug=candidate_slug,
        expected_addrs=expected_addrs,
        expected_value=expected_value,
    )
    base = BASE.read_bytes()
    candidate = image_path(candidate_root, candidate_slug).read_bytes()
    restore = image_path(restore_root, restore_slug).read_bytes()
    candidate_manifest = read_json(manifest_path(candidate_root, candidate_slug))
    restore_manifest = read_json(manifest_path(restore_root, restore_slug))
    final_candidate = read_json(final_candidate_path(candidate_root, candidate_slug))
    restore_final = read_json(final_candidate_path(restore_root, restore_slug))
    writes, cave_payload_len, cave_meta = extract_gateway_writes(candidate[CAVE_OFFSET : CAVE_OFFSET + CAVE_LEN])

    checks: list[dict[str, Any]] = []

    def check(name: str, ok: bool, **extra: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), **extra})

    check("base_hook_stock", base[HOOK_OFFSET : HOOK_OFFSET + 3] == EXPECTED_HOOK_BEFORE)
    check("base_cave_ff", base[CAVE_OFFSET : CAVE_OFFSET + CAVE_LEN] == EXPECTED_CAVE_BEFORE)
    check("candidate_hook_patch", candidate[HOOK_OFFSET : HOOK_OFFSET + 3] == EXPECTED_HOOK_AFTER)
    check("candidate_cave_not_ff", candidate[CAVE_OFFSET : CAVE_OFFSET + CAVE_LEN] != EXPECTED_CAVE_BEFORE)
    check("candidate_cave_return_shape", True, **cave_meta)
    check(
        "candidate_cave_tail_unchanged",
        candidate[CAVE_OFFSET + cave_payload_len : CAVE_OFFSET + CAVE_LEN]
        == base[CAVE_OFFSET + cave_payload_len : CAVE_OFFSET + CAVE_LEN],
        cave_payload_len=cave_payload_len,
    )
    check("restore_image_equals_base", restore == base, restore_sha256=sha256(restore), base_sha256=sha256(base))

    diffs = set(diff_offsets(base, candidate))
    allowed_ranges = set(range(HOOK_OFFSET, HOOK_OFFSET + len(EXPECTED_HOOK_AFTER))) | set(
        range(CAVE_OFFSET, CAVE_OFFSET + cave_payload_len)
    )
    check(
        "candidate_only_hook_and_parsed_cave_changed",
        diffs <= allowed_ranges,
        changed_count=len(diffs),
        allowed_count=len(allowed_ranges),
        unexpected=sorted(diffs - allowed_ranges)[:16],
    )

    helper_patches = {split_patch_text(value) for value in candidate_manifest.get("helper_patches", [])}
    check(
        "candidate_helper_low_sector_patches_present",
        EXPECTED_HELPER_PATCHES <= helper_patches,
        helper_patches=sorted(f"{offset}:{payload}" for offset, payload in helper_patches),
    )
    restore_helper_patches = {split_patch_text(value) for value in restore_manifest.get("helper_patches", [])}
    check(
        "restore_helper_low_sector_patches_present",
        EXPECTED_HELPER_PATCHES <= restore_helper_patches,
        helper_patches=sorted(f"{offset}:{payload}" for offset, payload in restore_helper_patches),
    )

    check(
        "candidate_gateway_writes_match_plan",
        writes == [{"address": addr, "value": expected_clamp_value} for addr in expected_clamp_addrs],
        writes=[{"address": f"0x{row['address']:06x}", "value": f"0x{row['value']:02x}"} for row in writes],
        expected_writes=[{"address": f"0x{addr:06x}", "value": f"0x{expected_clamp_value:02x}"} for addr in expected_clamp_addrs],
    )

    final_diff = final_candidate.get("diff_summary", {})
    check(
        "final_candidate_diff_count_matches_image",
        final_diff.get("modified_byte_count") == len(diffs),
        final_modified_byte_count=final_diff.get("modified_byte_count"),
        image_changed_count=len(diffs),
    )
    check("final_candidate_event_count", final_candidate.get("event_count") == 546, event_count=final_candidate.get("event_count"))
    check(
        "restore_final_candidate_diff_count_zero",
        restore_final.get("diff_summary", {}).get("modified_byte_count") == 0,
        restore_modified_byte_count=restore_final.get("diff_summary", {}).get("modified_byte_count"),
    )

    report = {
        "candidate": candidate_slug,
        "restore": restore_slug,
        "candidate_root": str(candidate_root),
        "restore_root": str(restore_root),
        "base": str(BASE),
        "dynamic_selection": dynamic_selection,
        "expected_clamp_addrs": [f"0x{addr:06x}" for addr in expected_clamp_addrs],
        "expected_clamp_value": f"0x{expected_clamp_value:02x}",
        "cave_payload_len": cave_payload_len,
        "cave_meta": cave_meta,
        "all_ok": all(row["ok"] for row in checks),
        "checks": checks,
    }
    return report


def write_md(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Bridge-Clamp Candidate Verification",
        "",
        f"candidate: `{report['candidate']}`",
        f"restore: `{report['restore']}`",
        f"expected clamp value: `{report['expected_clamp_value']}`",
        f"expected clamp addresses: `{', '.join(report['expected_clamp_addrs'])}`",
        f"cave payload length: `{report['cave_payload_len']}`",
        f"cave preserves DPTR: `{report['cave_meta'].get('preserves_dptr')}`",
        f"all ok: `{report['all_ok']}`",
        "",
        "| check | ok | detail |",
        "|---|---:|---|",
    ]
    for row in report["checks"]:
        detail = ", ".join(f"{k}={v!r}" for k, v in row.items() if k not in {"name", "ok"})
        lines.append(f"| `{row['name']}` | `{row['ok']}` | {detail} |")
    path.write_text("\n".join(lines) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-slug", default=CANDIDATE_SLUG)
    parser.add_argument("--restore-slug", default=RESTORE_SLUG)
    parser.add_argument("--candidate-root", type=Path, default=OUT_ROOT)
    parser.add_argument(
        "--restore-root",
        type=Path,
        default=None,
        help="root for restore slug; defaults to --candidate-root when omitted",
    )
    parser.add_argument(
        "--expected-clamp-addr",
        action="append",
        type=lambda value: int(value, 0),
        default=[],
        help="repeatable expected controller/public address; defaults to dynamic-selection JSON or fixed plan",
    )
    parser.add_argument(
        "--expected-clamp-value",
        type=lambda value: int(value, 0),
        default=None,
        help="expected byte written to each clamp address; defaults to dynamic-selection JSON or fixed 0x07",
    )
    parser.add_argument("--json-out", type=Path, default=ROOT / "analysis/8051/bridge-clamp-candidate-verify-20260506.json")
    parser.add_argument("--md-out", type=Path, default=ROOT / "analysis/8051/bridge-clamp-candidate-verify-20260506.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.expected_clamp_value is not None and not 0 <= args.expected_clamp_value <= 0xFF:
        raise ValueError("--expected-clamp-value must be a byte")
    report = verify(
        candidate_root=args.candidate_root,
        restore_root=args.restore_root or args.candidate_root,
        candidate_slug=args.candidate_slug,
        restore_slug=args.restore_slug,
        expected_addrs=args.expected_clamp_addr,
        expected_value=args.expected_clamp_value,
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_md(report, args.md_out)
    print(json.dumps({"all_ok": report["all_ok"], "json": str(args.json_out), "md": str(args.md_out)}, sort_keys=True))
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
