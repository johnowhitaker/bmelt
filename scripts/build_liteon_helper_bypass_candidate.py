#!/usr/bin/env python3
"""Build a full-currentboot candidate with the helper-status bypass applied.

This is an offline convenience wrapper. It patches an LD5M F0 image, renders
the normal full-currentboot replay for that image, then mutates every
currentboot-key profile-tail helper payload with the currently working helper
patch:

    helper plaintext offset 0x02b5: 30 e6 12 -> 02 32 c4

No drive commands are sent by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from classify_liteon_f0_probe_offsets import classify_offset, make_regions


ROOT = Path(__file__).resolve().parents[1]
EXTRACTED = ROOT / "references/firmware/extracted"
DEFAULT_BASE_IMAGE = EXTRACTED / "ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_EXTRAINQ = ROOT / "references/evidence/ld5m-extrainq-reference.log"
DEFAULT_TRANSPORT_EXTRAINQ = ROOT / "references/evidence/live/currentboot-extrainq-after-profile-tail.hex"
DEFAULT_OUT_DIR = EXTRACTED / "helper-bypass-candidates"
DEFAULT_HELPER_PATCH = "0x2b5:0232c4"
DEFAULT_PRETAIL_TAIL = EXTRACTED / "liteon-profile-tail-ef130045-ld5m-official-pretail.json"
HELPER_ERASE_START_PATCH_OFFSET = 0x0169
HELPER_PROGRAM_START_PATCH_OFFSET = 0x0345
HELPER_DEFAULT_START_SECTOR = 0x07


def compact_hex(value: str) -> str:
    return "".join(ch for ch in value if ch in "0123456789abcdefABCDEF")


def parse_int(value: str) -> int:
    return int(value, 0)


def parse_patch(value: str) -> tuple[int, bytes]:
    try:
        offset_text, hex_text = value.split(":", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("patch must be OFFSET:HEX") from exc
    payload_hex = compact_hex(hex_text)
    if not payload_hex or len(payload_hex) % 2:
        raise argparse.ArgumentTypeError("patch hex must be non-empty whole bytes")
    offset = parse_int(offset_text)
    if offset < 0:
        raise argparse.ArgumentTypeError("patch offset must be non-negative")
    return offset, bytes.fromhex(payload_hex)


def patch_text_offset(value: str) -> int:
    return parse_patch(value)[0]


def slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    slug = "-".join(part for part in slug.split("-") if part)
    if not slug:
        raise ValueError("--name must contain at least one alphanumeric character")
    return slug


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_helper_mov_patch(offset: int, direct_addr: int, value: int) -> str:
    if not 0 <= value <= 0xFF:
        raise ValueError(f"helper patch byte out of range: {value:#x}")
    return f"0x{offset:x}:75{direct_addr:02x}{value:02x}"


def upsert_helper_patch(patches: list[str], patch: str) -> None:
    patch_offset = patch_text_offset(patch)
    for index, existing in enumerate(patches):
        if patch_text_offset(existing) == patch_offset:
            patches[index] = patch
            return
    patches.append(patch)


def helper_patch_plan(args: argparse.Namespace) -> dict[str, Any]:
    helper_patches = list(args.helper_patch)
    notes: list[dict[str, Any]] = []

    if args.auto_helper_range:
        first_patch_offset = min(offset for offset, _payload in args.patch)
        first_sector = first_patch_offset // 0x1000
        if first_sector < HELPER_DEFAULT_START_SECTOR:
            program_start_page = first_sector * 0x10
            program_patch = format_helper_mov_patch(
                HELPER_PROGRAM_START_PATCH_OFFSET,
                0x24,
                program_start_page,
            )
            erase_patch = format_helper_mov_patch(
                HELPER_ERASE_START_PATCH_OFFSET,
                0x22,
                first_sector,
            )
            upsert_helper_patch(helper_patches, erase_patch)
            upsert_helper_patch(helper_patches, program_patch)
            notes.append(
                {
                    "kind": "auto_helper_range",
                    "first_patch_offset": first_patch_offset,
                    "first_patch_sector_0x1000": first_sector,
                    "erase_start_sector": first_sector,
                    "program_start_page_0x100": program_start_page,
                    "erase_patch": erase_patch,
                    "program_patch": program_patch,
                    "note": (
                        "Auto range is intentionally erase+rewrite, suitable for "
                        "restoring bytes that may need 0->1 transitions."
                    ),
                }
            )
        else:
            notes.append(
                {
                    "kind": "auto_helper_range",
                    "first_patch_offset": first_patch_offset,
                    "first_patch_sector_0x1000": first_sector,
                    "note": "No helper range patch needed; the normal helper starts at sector 0x07.",
                }
            )

    if args.helper_erase_start_sector is not None:
        erase_patch = format_helper_mov_patch(
            HELPER_ERASE_START_PATCH_OFFSET,
            0x22,
            args.helper_erase_start_sector,
        )
        upsert_helper_patch(helper_patches, erase_patch)
        notes.append(
            {
                "kind": "explicit_helper_erase_start_sector",
                "erase_start_sector": args.helper_erase_start_sector,
                "erase_patch": erase_patch,
            }
        )

    if args.helper_program_start_page is not None:
        program_patch = format_helper_mov_patch(
            HELPER_PROGRAM_START_PATCH_OFFSET,
            0x24,
            args.helper_program_start_page,
        )
        upsert_helper_patch(helper_patches, program_patch)
        notes.append(
            {
                "kind": "explicit_helper_program_start_page",
                "program_start_page_0x100": args.helper_program_start_page,
                "program_patch": program_patch,
            }
        )

    return {"helper_patches": helper_patches, "notes": notes}


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def apply_patches(base: bytes, patches: list[tuple[int, bytes]]) -> tuple[bytes, list[dict[str, Any]]]:
    image = bytearray(base)
    records: list[dict[str, Any]] = []
    regions = make_regions(base)
    for offset, replacement in patches:
        end = offset + len(replacement)
        if end > len(image):
            raise ValueError(f"patch {offset:#x}+{len(replacement):#x} exceeds image length {len(image):#x}")
        before = bytes(image[offset:end])
        image[offset:end] = replacement
        records.append(
            {
                "offset": offset,
                "end": end,
                "length": len(replacement),
                "before_hex": before.hex(),
                "after_hex": replacement.hex(),
                "changed": before != replacement,
                "bank": offset // 0x10000,
                "chunk_0x1000": offset // 0x1000,
                "chunk_offset_0x1000": offset % 0x1000,
                "target_classification": classify_offset(base, regions, offset),
            }
        )
    return bytes(image), records


def run_command(cmd: list[str], *, cwd: Path) -> None:
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        message = [f"command failed with rc={proc.returncode}: {' '.join(cmd)}"]
        if proc.stdout:
            message.extend(["stdout:", proc.stdout])
        if proc.stderr:
            message.extend(["stderr:", proc.stderr])
        raise RuntimeError("\n".join(message))


def build(args: argparse.Namespace) -> dict[str, Any]:
    slug = slugify(args.name)
    base_image = args.base_image if args.base_image.is_absolute() else ROOT / args.base_image
    extrainq = args.extrainq if args.extrainq.is_absolute() else ROOT / args.extrainq
    transport_extrainq = (
        args.transport_extrainq if args.transport_extrainq.is_absolute() else ROOT / args.transport_extrainq
    )
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    work_dir = out_dir / slug
    work_dir.mkdir(parents=True, exist_ok=True)

    base = base_image.read_bytes()
    patched, patch_records = apply_patches(base, args.patch)
    image_path = work_dir / f"ld5m-helper-bypass-{slug}.bin"
    image_path.write_bytes(patched)

    dry_json = work_dir / f"liteon-dry-run-write-sequence-helper-bypass-{slug}.json"
    dry_md = work_dir / f"liteon-dry-run-write-sequence-helper-bypass-{slug}.md"
    replay_json = work_dir / f"liteon-full-currentboot-ld5m-helper-bypass-{slug}-pre-helper-candidate.json"
    final_candidate = work_dir / f"liteon-full-currentboot-ld5m-helper-bypass-{slug}-candidate.json"
    currentboot_tail_candidate = (
        work_dir / f"liteon-full-currentboot-ld5m-helper-bypass-{slug}-currentboot-tails-candidate.json"
        if args.include_pre_tail
        else final_candidate
    )
    helper_report_json = work_dir / f"liteon-helper-bypass-{slug}.json"
    helper_report_md = work_dir / f"liteon-helper-bypass-{slug}.md"
    pre_tail_helper_report_json = work_dir / f"liteon-helper-bypass-{slug}-pretail.json"
    pre_tail_helper_report_md = work_dir / f"liteon-helper-bypass-{slug}-pretail.md"
    planned_helper = helper_patch_plan(args)

    run_command(
        [
            sys.executable,
            str(ROOT / "scripts/generate_liteon_write_sequence_dry_run.py"),
            "--image",
            str(image_path),
            "--extrainq",
            str(extrainq),
            "--transport-extrainq",
            str(transport_extrainq),
            "--chunk-size",
            hex(args.chunk_size),
            "--bank-size",
            hex(args.bank_size),
            "--write-cdb-layout",
            "official-byte9",
            "--implicit-selector-enabled",
            "--detail-chunks",
            str(args.detail_chunks),
            "--out-json",
            str(dry_json),
            "--out-md",
            str(dry_md),
        ],
        cwd=ROOT,
    )
    run_command(
        [
            sys.executable,
            str(ROOT / "scripts/render_liteon_same_family_full_currentboot_candidate.py"),
            "--model",
            str(dry_json),
            "--base-image",
            str(base_image),
            "--expected-final-revision",
            args.expected_final_revision,
            "--out-json",
            str(replay_json),
        ],
        cwd=ROOT,
    )

    helper_cmd = [
        sys.executable,
        str(ROOT / "scripts/render_liteon_profile_tail_mutation_candidate.py"),
        "--base-candidate",
        str(replay_json),
        "--all-currentboot-tails",
        "--out-dir",
        str(work_dir / "profile-tail"),
        "--out-candidate",
        str(currentboot_tail_candidate),
        "--out-json",
        str(helper_report_json),
        "--out-md",
        str(helper_report_md),
    ]
    for patch_text in planned_helper["helper_patches"]:
        helper_cmd.extend(["--patch", patch_text])
    run_command(helper_cmd, cwd=ROOT)

    helper_reports = [
        {"scope": "all_currentboot_tails", "json": str(helper_report_json), "md": str(helper_report_md)}
    ]
    if args.include_pre_tail:
        pre_tail_cmd = [
            sys.executable,
            str(ROOT / "scripts/render_liteon_profile_tail_mutation_candidate.py"),
            "--base-candidate",
            str(currentboot_tail_candidate),
            "--currentboot-tail",
            str(args.pretail_tail),
            "--event-index",
            "1",
            "--allow-pre-tail",
            "--out-dir",
            str(work_dir / "profile-tail-pre"),
            "--out-candidate",
            str(final_candidate),
            "--out-json",
            str(pre_tail_helper_report_json),
            "--out-md",
            str(pre_tail_helper_report_md),
        ]
        for patch_text in planned_helper["helper_patches"]:
            pre_tail_cmd.extend(["--patch", patch_text])
        run_command(pre_tail_cmd, cwd=ROOT)
        helper_reports.append(
            {
                "scope": "pre_tail_event_1",
                "json": str(pre_tail_helper_report_json),
                "md": str(pre_tail_helper_report_md),
            }
        )

    report = {
        "status": "helper_bypass_candidate_built",
        "name": args.name,
        "slug": slug,
        "base_image": str(base_image),
        "base_sha256": sha256_bytes(base),
        "patched_image": str(image_path),
        "patched_image_sha256": sha256_file(image_path),
        "patches": patch_records,
        "helper_patches": planned_helper["helper_patches"],
        "helper_patch_plan": planned_helper["notes"],
        "include_pre_tail": args.include_pre_tail,
        "dry_run_json": str(dry_json),
        "dry_run_md": str(dry_md),
        "pre_helper_candidate": str(replay_json),
        "currentboot_tail_candidate": str(currentboot_tail_candidate),
        "final_candidate": str(final_candidate),
        "final_candidate_sha256": sha256_file(final_candidate),
        "helper_report_json": str(helper_report_json),
        "helper_report_md": str(helper_report_md),
        "helper_reports": helper_reports,
        "pretail_tail_report": str(args.pretail_tail),
        "suggested_linux_command": (
            "python3 scripts/run_liteon_linux_persistence_experiment.py "
            f"--candidate {display_path(final_candidate)} "
            "--skip-pre-f0 --end-index 544 --f0-size 0xe0000 "
            f"--capture-finalizer-status-after-event {'1' if args.include_pre_tail else '35'} "
            "--capture-finalizer-status "
            "--recover-on-currentboot"
        ),
    }

    manifest_path = work_dir / "manifest.json"
    manifest_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path = work_dir / "manifest.md"
    md_path.write_text(render_markdown(report) + "\n", encoding="utf-8")
    report["manifest_json"] = str(manifest_path)
    report["manifest_md"] = str(md_path)
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Helper Bypass Candidate: {report['name']}",
        "",
        "Offline generated helper-bypass replay artifact. No drive commands were sent.",
        "",
        f"- patched image: `{report['patched_image']}`",
        f"- patched image sha256: `{report['patched_image_sha256']}`",
        f"- final replay candidate: `{report['final_candidate']}`",
        "",
        "## F0 Patches",
        "",
        "| offset | before | after | bank | chunk | risk | region |",
        "|---:|---|---|---:|---:|---|---|",
    ]
    for patch in report["patches"]:
        target = patch["target_classification"]
        lines.append(
            f"| `{patch['offset']:#x}` | `{patch['before_hex']}` | `{patch['after_hex']}` | "
            f"`{patch['bank']}` | `{patch['chunk_0x1000']}` | `{target['risk']}` | `{target['region']}` |"
        )
    lines += [
        "",
        "## Target Classification",
        "",
    ]
    for patch in report["patches"]:
        target = patch["target_classification"]
        lines.append(
            f"- `{target['offset_hex']}`: `{target['region']}` / `{target['risk']}`. "
            f"{target['advice']}"
        )
    lines += [
        "",
        "## Helper Patches",
        "",
    ]
    for patch in report["helper_patches"]:
        lines.append(f"- `{patch}`")
    if report["helper_patch_plan"]:
        lines += ["", "## Helper Range Plan", ""]
        for item in report["helper_patch_plan"]:
            lines.append(f"- `{item['kind']}`: {item['note'] if 'note' in item else item}")
    if report["include_pre_tail"]:
        lines += [
            "",
            "The helper patches were applied to both the pre-tail event and all currentboot-key tails.",
        ]
    lines += [
        "",
        "## Suggested Linux Command",
        "",
        "```sh",
        report["suggested_linux_command"],
        "```",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="short descriptive name for this candidate")
    parser.add_argument("--patch", action="append", type=parse_patch, required=True, help="F0 patch OFFSET:HEX")
    parser.add_argument("--base-image", type=Path, default=DEFAULT_BASE_IMAGE)
    parser.add_argument("--extrainq", type=Path, default=DEFAULT_EXTRAINQ)
    parser.add_argument("--transport-extrainq", type=Path, default=DEFAULT_TRANSPORT_EXTRAINQ)
    parser.add_argument(
        "--pretail-tail",
        type=Path,
        default=DEFAULT_PRETAIL_TAIL,
        help="profile-tail report/key source to use when mutating pre-tail event 1",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--helper-patch", action="append", default=[DEFAULT_HELPER_PATCH], help="helper plaintext patch OFFSET:HEX")
    parser.add_argument(
        "--auto-helper-range",
        action="store_true",
        help="derive erase/program helper start patches from the lowest requested F0 patch offset",
    )
    parser.add_argument(
        "--helper-erase-start-sector",
        type=parse_int,
        help="explicit helper erase-loop start sector, encoded as patch 0x169:7522NN",
    )
    parser.add_argument(
        "--helper-program-start-page",
        type=parse_int,
        help="explicit helper program-loop start 0x100-byte page, encoded as patch 0x345:7524NN",
    )
    parser.add_argument(
        "--include-pre-tail",
        action="store_true",
        help="also apply the helper patches to pre-tail event 1 after patching all currentboot tails",
    )
    parser.add_argument("--chunk-size", type=parse_int, default=0x1000)
    parser.add_argument("--bank-size", type=parse_int, default=0x10000)
    parser.add_argument("--detail-chunks", type=int, default=0)
    parser.add_argument("--expected-final-revision", default="LD5M")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build(args)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
