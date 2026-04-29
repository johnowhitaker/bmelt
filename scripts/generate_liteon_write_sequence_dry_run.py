#!/usr/bin/env python3
"""Generate an offline LiteOn/PLDS WRITE BUFFER sequence model.

This script never opens the optical drive and has no execute mode. It combines
the current DOS-updater map with the EXTRAINQ-derived AES write transport so we
can inspect concrete CDB bytes, ciphertext previews, and pMac selector-bank
boundaries without sending anything live.

The output is deliberately marked not flashable. It can model the live-probed
byte10 dialect or the official Windows updater byte9 helper layout, and it can
split pre-tail EXTRAINQ metadata from post-profile-tail transport key material.
Source-container packing and accepted LD5M dialect checks remain unresolved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from model_liteon_updater_write_crypto import StreamingCmacState, aes_cbc_encrypt_chunks, self_test
from parse_liteon_extrainq import ascii_field, derive_iv_key, describe_flags, parse_hex_or_file


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXTRAINQ = ROOT / "references/evidence/ld5m-extrainq-reference.log"
DEFAULT_IMAGE = ROOT / "references/firmware/extracted/ad12-filedecrypt/AD12-1.bin"
DEFAULT_OUT_JSON = ROOT / "references/firmware/extracted/liteon-dry-run-write-sequence-ld5m-live.json"
DEFAULT_OUT_MD = ROOT / "references/firmware/extracted/liteon-dry-run-write-sequence-ld5m-live.md"

BLOCK_SIZE = 16
FAMILY_MARKER_SLOT = 0x6FF8
FAMILY_MARKER_LEN = 8


def int_arg(value: str) -> int:
    return int(value, 0)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def hex_bytes(data: bytes) -> str:
    return " ".join(f"{byte:02X}" for byte in data)


def fmt_hex(value: int, width: int = 0) -> str:
    if width:
        return f"0x{value:0{width}x}"
    return f"0x{value:x}"


def printable_ascii(data: bytes) -> str:
    return data.decode("ascii", errors="replace")


def validate_u24(value: int, label: str) -> None:
    if value < 0 or value > 0xFFFFFF:
        raise ValueError(f"{label} must fit 24 bits, got {fmt_hex(value)}")


def validate_u8(value: int, label: str) -> None:
    if value < 0 or value > 0xFF:
        raise ValueError(f"{label} must fit 8 bits, got {fmt_hex(value)}")


def write_buffer_cdb(
    *,
    mode: int,
    buffer_id: int,
    offset: int,
    length: int,
    arg_control: int,
    selector: int = 0,
    pad: int = 0,
    layout: str = "live-byte10",
) -> bytes:
    validate_u8(mode, "mode")
    validate_u8(buffer_id, "buffer id")
    validate_u24(offset, "offset")
    validate_u24(length, "length")
    validate_u8(arg_control, "arg/control")
    validate_u8(selector, "selector")
    validate_u8(pad, "pad")
    if layout == "official-byte9":
        return bytes(
            [
                0x3B,
                mode,
                buffer_id,
                (offset >> 16) & 0xFF,
                (offset >> 8) & 0xFF,
                offset & 0xFF,
                (length >> 16) & 0xFF,
                (length >> 8) & 0xFF,
                length & 0xFF,
                arg_control,
                selector,
                pad,
            ]
        )
    if layout != "live-byte10":
        raise ValueError(f"unknown WRITE BUFFER CDB layout: {layout}")
    # Live LD5M probes show the primary control byte in CDB byte 10, with byte
    # 9 left at zero and byte 11 used for the pMac bank selector/follow-up
    # counter. The official Windows updater helper uses byte9/byte10 instead.
    return bytes(
        [
            0x3B,
            mode,
            buffer_id,
            (offset >> 16) & 0xFF,
            (offset >> 8) & 0xFF,
            offset & 0xFF,
            (length >> 16) & 0xFF,
            (length >> 8) & 0xFF,
            length & 0xFF,
            pad,
            arg_control,
            selector,
        ]
    )


def read_buffer_cdb(
    *,
    mode: int,
    buffer_id: int,
    offset: int,
    length: int,
) -> bytes:
    validate_u8(mode, "mode")
    validate_u8(buffer_id, "buffer id")
    validate_u24(offset, "offset")
    validate_u24(length, "length")
    return bytes(
        [
            0x3C,
            mode,
            buffer_id,
            (offset >> 16) & 0xFF,
            (offset >> 8) & 0xFF,
            offset & 0xFF,
            (length >> 16) & 0xFF,
            (length >> 8) & 0xFF,
            length & 0xFF,
            0x00,
            0x00,
            0x00,
        ]
    )


def parse_selector_list(value: str) -> list[int]:
    if value.strip().lower() in {"", "none", "-"}:
        return []
    selectors = [int_arg(part.strip()) for part in value.split(",") if part.strip()]
    for selector in selectors:
        validate_u8(selector, "profile selector")
    return selectors


def derive_profile_selectors(
    args: argparse.Namespace,
    image_len: int,
    extrainq: dict[str, Any],
) -> tuple[list[int], str, str]:
    value = str(args.profile_selectors).strip().lower()
    if value != "auto":
        return parse_selector_list(args.profile_selectors), "cli_override", "explicit_cli_model"
    if image_len == 0x20000 and extrainq["flags"].get("bAES"):
        return [1, 0], "auto_0x20000_profile_branch", "explicit_selector_special_branch"
    return [], "auto_normal_1m_implicit_selector_path", "implicit_selector_only"


def image_family_marker(image: bytes) -> dict[str, Any]:
    if len(image) < FAMILY_MARKER_SLOT + FAMILY_MARKER_LEN:
        return {
            "offset": FAMILY_MARKER_SLOT,
            "family_ascii": None,
            "boot_marker_ascii": None,
            "status": "image_too_short",
        }
    family = image[FAMILY_MARKER_SLOT : FAMILY_MARKER_SLOT + FAMILY_MARKER_LEN]
    boot_marker = family[-4:]
    return {
        "offset": FAMILY_MARKER_SLOT,
        "family_ascii": printable_ascii(family),
        "family_hex": family.hex(),
        "boot_marker_ascii": printable_ascii(boot_marker),
        "boot_marker_hex": boot_marker.hex(),
        "status": "parsed",
    }


def derive_primary_arg(args: argparse.Namespace, image: bytes, extrainq: dict[str, Any]) -> tuple[int, str, dict[str, Any]]:
    target = image_family_marker(image)
    live_key = str(extrainq.get("key_ascii") or "")
    live_marker = live_key[:4] if len(live_key) >= 4 else None
    target_marker = target.get("boot_marker_ascii")
    mismatch = live_marker is not None and target_marker is not None and live_marker != target_marker
    auto_primary = 0xA0 if mismatch else 0x80
    boot_model = {
        "live_marker_ascii": live_marker,
        "live_marker_source": "EXTRAINQ SecKey first 4 bytes",
        "target_family_ascii": target.get("family_ascii"),
        "target_family_offset": target.get("offset"),
        "target_marker_ascii": target_marker,
        "target_marker_source": "image family marker slot last 4 bytes",
        "boot_mismatch": mismatch,
        "auto_primary_arg": auto_primary,
        "auto_primary_arg_reason": (
            "StartFlash sets 0x35c00 on boot marker mismatch, then selects 0xa0 at 0x22284"
            if mismatch
            else "StartFlash leaves 0x35c00 clear on boot marker match, then selects 0x80 at 0x22284"
        ),
        "risk": (
            "boot-code/bEraseBootCode path; do not live-run without recovery"
            if mismatch
            else "same-boot-marker staging path"
        ),
    }
    if str(args.primary_arg).strip().lower() == "auto":
        return auto_primary, "boot_marker_compare_auto", boot_model
    primary_arg = int_arg(str(args.primary_arg))
    boot_model["cli_primary_arg"] = primary_arg
    boot_model["cli_primary_arg_matches_auto"] = primary_arg == auto_primary
    return primary_arg, "cli_override", boot_model


def find_profile_marker(response: bytes) -> tuple[int, bytes]:
    marker = response.find(b"EXTRAINQ")
    if marker < 0:
        marker = response.find(b"LITEONIT")
    if marker < 0:
        raise ValueError("could not find EXTRAINQ/LITEONIT marker in response")
    return marker, response[marker:]


def parse_extrainq(path: Path) -> tuple[dict[str, Any], bytes, bytes]:
    response = parse_hex_or_file(str(path))
    marker, base = find_profile_marker(response)
    if len(base) < 0x14:
        raise ValueError("EXTRAINQ/LITEONIT profile is truncated before flag bytes")

    iv, key, key_selector, key_off = derive_iv_key(response)
    profile_len = int.from_bytes(base[0x08:0x0A], "big") if len(base) >= 0x0A else 0
    profile_word = int.from_bytes(base[0x0A:0x0C], "big") if len(base) >= 0x0C else 0
    iaes_bank = None
    if len(base) > 0x0F and base[0x0F] > 8:
        iaes_bank = (base[0x0A] + base[0x0B]) % 8

    report = {
        "path": str(path),
        "response_len": len(response),
        "marker_offset": marker,
        "marker": base[:8].decode("ascii", errors="replace"),
        "profile_len": profile_len,
        "profile_word": profile_word,
        "feature_byte": base[0x10],
        "aes_byte": base[0x12],
        "flags": describe_flags(base),
        "iAESBank": iaes_bank,
        "key_selector": key_selector,
        "key_offset": key_off,
        "iv_hex": iv.hex(),
        "iv_ascii": ascii_field(iv),
        "key_hex": key.hex(),
        "key_ascii": ascii_field(key),
    }
    return report, iv, key


def cdb_event(
    *,
    phase: str,
    source: str,
    role: str,
    cdb: bytes,
    data_out_len: int = 0,
    data_out_preview: bytes = b"",
    risk: str,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "phase": phase,
        "source": source,
        "role": role,
        "cdb": hex_bytes(cdb),
        "data_out_len": data_out_len,
        "data_out_preview": data_out_preview.hex(),
        "risk": risk,
        "notes": notes or [],
    }


def build_prelude(
    args: argparse.Namespace,
    extrainq: dict[str, Any],
    boot_marker_model: dict[str, Any],
) -> list[dict[str, Any]]:
    setup_cdb = write_buffer_cdb(
        mode=0x05,
        buffer_id=0x01,
        offset=0,
        length=args.setup_length,
        arg_control=args.primary_arg,
        layout=args.write_cdb_layout,
    )
    events = [
        cdb_event(
            phase="profile_read_reference",
            source="live discovery / updater 0x22670",
            role="EXTRAINQ read used to derive InitVec/SecKey",
            cdb=bytes.fromhex("12 00 00 00 f0 40"),
            data_out_len=0,
            risk="read-only reference, included so the write model records its key source",
            notes=["Observed live as INQUIRY allocation 0xf0, control byte 0x40."],
        ),
        cdb_event(
            phase="startflash_gate",
            source="StartFlash call site 0x22230 via generic builder 0x230f0",
            role="generic zero-length WRITE BUFFER gate",
            cdb=write_buffer_cdb(
                mode=0x07,
                buffer_id=0x00,
                offset=0,
                length=0,
                arg_control=0,
                layout=args.write_cdb_layout,
            ),
            risk="vendor WRITE BUFFER control path; keep offline until purpose is proven",
            notes=["This is not the normal 3B 05 01 data path."],
        ),
        cdb_event(
            phase="startflash_setup",
            source="StartFlash call site 0x222a8 via helper 0x22ba0",
            role="primary pre-program setup",
            cdb=setup_cdb,
            data_out_len=args.setup_length,
            data_out_preview=bytes(args.setup_length),
            risk="enters firmware primary 0x80/0xa0 flash setup branch",
            notes=[
                f"setup_length is modeled as {fmt_hex(args.setup_length)} from global 0x35c49.",
                f"primary_arg is modeled as {fmt_hex(args.primary_arg)} from global 0x35c00.",
                boot_marker_model["auto_primary_arg_reason"],
                boot_marker_model["risk"],
            ],
        ),
    ]

    for index, selector in enumerate(args.profile_selectors):
        arg_control = 0x80 if index == 0 and selector == 1 else args.primary_arg
        source = "BufWrite call site 0x17607" if index == 0 and selector == 1 else "BufWrite call site 0x1764b"
        events.append(
            cdb_event(
                phase="profile_selector_setup",
                source=f"{source} via explicit-selector helper 0x22e10",
                role=f"profile selector {fmt_hex(selector, 2)} setup",
                cdb=write_buffer_cdb(
                    mode=0x05,
                    buffer_id=0x01,
                    offset=0,
                    length=0,
                    arg_control=arg_control,
                    selector=selector,
                    layout=args.write_cdb_layout,
                ),
                risk="profile/control state write; not data-bearing, but not harmless until verified",
                notes=[
                    "Modeled only for the updater's 0x35bf4 special profile branch; normal 1 MiB writes use the implicit CDB byte 10 selector."
                ],
            )
        )

    if args.include_profile_tail_arg00:
        profile_len = int(extrainq["profile_len"])
        events.append(
            cdb_event(
                phase="profile_tail_candidate",
                source="FlashProfileTailVariantA/B non-0x7f paths at 0x23df3 and 0x2414e",
                role="profile tail arg=00 candidate",
                cdb=write_buffer_cdb(
                    mode=0x05,
                    buffer_id=0x01,
                    offset=0x80000,
                    length=profile_len,
                    arg_control=0x00,
                    layout=args.write_cdb_layout,
                ),
                data_out_len=profile_len,
                risk="alternate arg=00 branch; purpose and live safety are unresolved",
                notes=[
                    "The paired arg=7f profile-tail model is intentionally excluded from generated live candidates.",
                    "The transfer length is seeded from the parsed EXTRAINQ profile_len.",
                ],
            )
        )
    return events


def selector_for_bank(bank: int, selector_count: int, descending: bool) -> int:
    if descending:
        return selector_count - bank - 1
    return bank


def primary_arg_for_implicit_selector(args: argparse.Namespace, selector: int) -> int:
    if args.implicit_selector_enabled and selector != 0:
        return 0x80
    return args.primary_arg


def build_chunk_model(
    args: argparse.Namespace,
    image: bytes,
    key: bytes,
    iv: bytes,
    extrainq: dict[str, Any],
    transport_extrainq: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if args.chunk_size <= 0 or args.bank_size <= 0:
        raise ValueError("--chunk-size and --bank-size must be positive")
    if args.chunk_size % BLOCK_SIZE:
        raise ValueError("--chunk-size must be 16-byte aligned")
    if args.bank_size % args.chunk_size:
        raise ValueError("--bank-size must be a multiple of --chunk-size")
    if len(image) % args.chunk_size:
        raise ValueError(f"image length {len(image)} is not a multiple of chunk size {args.chunk_size}")

    chunks = [image[offset : offset + args.chunk_size] for offset in range(0, len(image), args.chunk_size)]
    chunks_per_bank = args.bank_size // args.chunk_size
    bank_count = len(chunks) // chunks_per_bank
    selector_count = len(image) >> 16 if args.implicit_selector_enabled and len(image) >= 0x10000 else bank_count
    descending = bool(int(extrainq["feature_byte"]) & 0x10)
    aes_bank_index = extrainq.get("iAESBank")
    aes_enabled = bool(extrainq["flags"].get("bAES"))
    selected_bank_indices = [
        bank
        for bank in range(bank_count)
        if aes_enabled and aes_bank_index is not None and selector_for_bank(bank, selector_count, descending) == aes_bank_index
    ]
    selected_chunk_indices = {
        chunk_index
        for bank in selected_bank_indices
        for chunk_index in range(bank * chunks_per_bank, min((bank + 1) * chunks_per_bank, len(chunks)))
    }
    selected_plain_chunks = [chunks[index] for index in range(len(chunks)) if index in selected_chunk_indices]
    selected_encrypted_chunks = (
        aes_cbc_encrypt_chunks(key, iv, selected_plain_chunks) if selected_plain_chunks else []
    )
    encrypted_by_index = {
        index: encrypted
        for index, encrypted in zip(
            [index for index in range(len(chunks)) if index in selected_chunk_indices],
            selected_encrypted_chunks,
            strict=True,
        )
    }

    pmac_state = StreamingCmacState(key)
    selected_chunk_order = [index for index in range(len(chunks)) if index in selected_chunk_indices]
    selected_position = {index: pos for pos, index in enumerate(selected_chunk_order)}
    # The updater references pMac at autodata offset 0x3cb48. In the LE image
    # that lands in obj.3.page.zerofill at runtime, so the pre-selected-bank
    # prefix starts as zero until a selected AES bank finalizes a real pMac.
    initial_pmac_state = bytes(BLOCK_SIZE) if aes_enabled else None
    last_known_pmac: bytes | None = initial_pmac_state
    rows = []
    banks = []

    for index, source_chunk in enumerate(chunks):
        source_offset = index * args.chunk_size
        bank = index // chunks_per_bank
        chunk_in_bank = index % chunks_per_bank
        selector = selector_for_bank(bank, selector_count, descending)
        selected_for_aes = index in selected_chunk_indices
        transport_data = encrypted_by_index[index] if selected_for_aes else source_chunk
        selected_pos = selected_position.get(index)
        selected_final = selected_for_aes and selected_pos == len(selected_chunk_order) - 1
        selected_first = selected_for_aes and selected_pos == 0
        pmac = None
        if selected_for_aes:
            pmac = pmac_state.update(transport_data, init=selected_first, final=selected_final)
            if pmac is not None:
                last_known_pmac = pmac

        cdb_selector = selector if args.implicit_selector_enabled else args.implicit_selector
        arg00_selector = cdb_selector if args.write_cdb_layout == "official-byte9" else 0
        arg00_full = write_buffer_cdb(
            mode=0x05,
            buffer_id=0x01,
            offset=source_offset,
            length=args.chunk_size,
            arg_control=0x00,
            selector=arg00_selector,
            layout=args.write_cdb_layout,
        )
        arg00_low16 = write_buffer_cdb(
            mode=0x05,
            buffer_id=0x01,
            offset=source_offset & 0xFFFF,
            length=args.chunk_size,
            arg_control=0x00,
            selector=arg00_selector,
            layout=args.write_cdb_layout,
        )
        selector_primary_arg = primary_arg_for_implicit_selector(args, cdb_selector)
        bank_command_selector = bank if args.write_cdb_layout == "official-byte9" else bank + 1
        data_cdb = write_buffer_cdb(
            mode=0x05,
            buffer_id=0x01,
            offset=0,
            length=0x10,
            arg_control=selector_primary_arg,
            selector=bank_command_selector,
            layout=args.write_cdb_layout,
        )
        flush_cdb = write_buffer_cdb(
            mode=0x05,
            buffer_id=0x01,
            offset=0,
            length=0,
            arg_control=selector_primary_arg,
            selector=bank_command_selector,
            layout=args.write_cdb_layout,
        )

        arg00_primary = arg00_low16 if args.implicit_selector_enabled else arg00_full
        arg00_verify = read_buffer_cdb(
            mode=0x01,
            buffer_id=0x01,
            offset=source_offset & 0xFFFF if args.implicit_selector_enabled else source_offset,
            length=args.chunk_size,
        )
        row = {
            "chunk_index": index,
            "source_offset": source_offset,
            "source_end": source_offset + args.chunk_size,
            "bank": bank,
            "chunk_in_bank": chunk_in_bank,
            "implicit_selector_value": cdb_selector,
            "bank_selector_value": selector,
            "write_cdb_layout": args.write_cdb_layout,
            "arg00_primary_selector_value": arg00_selector,
            "bank_command_selector_value": bank_command_selector,
            "selected_for_aes_transport": selected_for_aes,
            "selected_aes_bank_index": aes_bank_index,
            "selected_aes_chunk_first": selected_first,
            "selected_aes_chunk_final": selected_final,
            "arg00_primary_offset_model": "low16" if args.implicit_selector_enabled else "full",
            "primary_arg_for_implicit_selector": selector_primary_arg,
            "arg00_retry_primary_cdb": hex_bytes(arg00_primary),
            "arg00_retry_full_offset_cdb": hex_bytes(arg00_full),
            "arg00_retry_low16_offset_cdb": hex_bytes(arg00_low16),
            "arg00_readback_verify_cdb": hex_bytes(arg00_verify),
            "arg00_readback_verify_data_in_len": args.chunk_size,
            "arg00_data_out_len": len(transport_data),
            "transport_transform": "aes_cbc_encrypt" if selected_for_aes else "plain_source",
            "transport_first16": transport_data[:16].hex(),
            "transport_sha256": hashlib.sha256(transport_data).hexdigest(),
            "encrypted_first16": transport_data[:16].hex() if selected_for_aes else None,
            "encrypted_sha256": hashlib.sha256(transport_data).hexdigest() if selected_for_aes else None,
            "pmac_if_selected_final": None if pmac is None else pmac.hex(),
            "pmac_prefix_data_cdb": hex_bytes(data_cdb) if pmac is not None else None,
            "pmac_prefix_data_out": None if pmac is None else pmac.hex(),
            "zero_length_followup_cdb": None if aes_enabled else hex_bytes(flush_cdb),
            "notes": [
                "arg00 full-offset and low16-offset variants are both shown; the implicit-selector/global-byte flag selects low16.",
                "Updater helper 0x22f50 reads the same offset/length back through 0x1eb60 and compares it against the transmitted buffer.",
                "AES transport and pMac update are selector-gated by the EXTRAINQ-derived AES bank index.",
                "When implicit selector mode is active, nonzero selector banks force the primary 0x80 control byte.",
                "When the AES pMac-prefix branch sends a 16-byte prefix, it skips the non-AES zero-length follow-up.",
            ],
        }
        rows.append(row)

        if chunk_in_bank == chunks_per_bank - 1 or index == len(chunks) - 1:
            copied_pmac = pmac or last_known_pmac
            bank_primary_arg = primary_arg_for_implicit_selector(args, cdb_selector)
            bank_command_selector = bank if args.write_cdb_layout == "official-byte9" else bank + 1
            bank_data_cdb = write_buffer_cdb(
                mode=0x05,
                buffer_id=0x01,
                offset=0,
                length=0x10,
                arg_control=bank_primary_arg,
                selector=bank_command_selector,
                layout=args.write_cdb_layout,
            )
            bank_flush_cdb = write_buffer_cdb(
                mode=0x05,
                buffer_id=0x01,
                offset=0,
                length=0,
                arg_control=bank_primary_arg,
                selector=bank_command_selector,
                layout=args.write_cdb_layout,
            )
            banks.append(
                {
                    "bank": bank,
                    "selector": selector,
                    "implicit_selector_value": cdb_selector,
                    "write_cdb_layout": args.write_cdb_layout,
                    "bank_command_selector_value": bank_command_selector,
                    "primary_arg_for_implicit_selector": bank_primary_arg,
                    "selected_for_aes_transport": bank in selected_bank_indices,
                    "selected_aes_bank_index": aes_bank_index,
                    "first_chunk": bank * chunks_per_bank,
                    "last_chunk": index,
                    "offset_start": bank * args.bank_size,
                    "offset_end": source_offset + args.chunk_size,
                    "pmac": None if pmac is None else pmac.hex(),
                    "copied_pmac_state_model": None if copied_pmac is None else copied_pmac.hex(),
                    "pmac_prefix_cdb": hex_bytes(bank_data_cdb),
                    "zero_length_followup_cdb": None if aes_enabled else hex_bytes(bank_flush_cdb),
                    "zero_length_followup_emitted": not aes_enabled,
                    "notes": (
                        ["selected AES bank; pMac is finalized here"]
                        if pmac is not None
                        else ["pMac copy source is the current pMac buffer state; initial state is modeled as LE autodata zerofill"]
                    ),
                }
            )

    transport_model = {
        "selector_count": selector_count,
        "selector_order": "descending" if descending else "ascending",
        "write_cdb_layout": args.write_cdb_layout,
        "aes_selection_extrainq_path": extrainq["path"],
        "transport_extrainq_path": transport_extrainq["path"],
        "transport_key_ascii": transport_extrainq["key_ascii"],
        "transport_key_hex": transport_extrainq["key_hex"],
        "transport_iv_ascii": transport_extrainq["iv_ascii"],
        "transport_iv_hex": transport_extrainq["iv_hex"],
        "aes_enabled": aes_enabled,
        "aes_bank_index": aes_bank_index,
        "selected_bank_indices": selected_bank_indices,
        "selected_chunk_indices": sorted(selected_chunk_indices),
        "initial_pmac_state": None if initial_pmac_state is None else initial_pmac_state.hex(),
        "initial_pmac_state_source": "LE obj.3.page.zerofill at autodata offset 0x3cb48"
        if initial_pmac_state is not None
        else "AES disabled",
        "model": "selector_gated_aes_bank",
        "bank_boundary_zero_length_followup": not aes_enabled,
    }
    return rows, banks, transport_model


def derive_implicit_selector(args: argparse.Namespace, extrainq: dict[str, Any]) -> tuple[bool, str]:
    if args.implicit_selector_enabled is not None:
        return bool(args.implicit_selector_enabled), "cli_override"
    enabled = (int(extrainq["feature_byte"]) & 0x03) == 1
    return enabled, "extrainq_feature_low_bits_eq_1"


def derive_setup_length(args: argparse.Namespace, extrainq: dict[str, Any]) -> tuple[int, str]:
    if args.setup_length is not None:
        return int(args.setup_length), "cli_override"
    if extrainq["flags"].get("bAES"):
        return 0x10, "extrainq_aes_flag"
    return 0, "extrainq_aes_flag"


def render_markdown(report: dict[str, Any], detail_chunks: int) -> str:
    lines = [
        "# LiteOn Dry-Run Write Sequence Model",
        "",
        "**Status:** offline model only. Not flashable. Do not execute as a live sequence.",
        "",
        "## Inputs",
        "",
        f"- image: `{report['inputs']['image']}`",
        f"- image length: `{fmt_hex(report['inputs']['image_length'])}`",
        f"- image sha256: `{report['inputs']['image_sha256']}`",
        f"- EXTRAINQ: `{report['extrainq']['path']}`",
        f"- key: `{report['extrainq']['key_ascii']}` / `{report['extrainq']['key_hex']}`",
        f"- iv: `{report['extrainq']['iv_ascii']}` / `{report['extrainq']['iv_hex']}`",
        f"- transport EXTRAINQ: `{report['transport_extrainq']['path']}`",
        f"- transport key: `{report['transport_extrainq']['key_ascii']}` / `{report['transport_extrainq']['key_hex']}`",
        f"- transport iv: `{report['transport_extrainq']['iv_ascii']}` / `{report['transport_extrainq']['iv_hex']}`",
        f"- bAES: `{report['extrainq']['flags'].get('bAES')}`",
        f"- iAESBank: `{report['extrainq']['iAESBank']}`",
        "",
        "## Parameters",
        "",
        f"- chunk size: `{fmt_hex(report['parameters']['chunk_size'])}`",
        f"- bank size: `{fmt_hex(report['parameters']['bank_size'])}`",
        f"- chunks per bank: `{report['parameters']['chunks_per_bank']}`",
        f"- primary arg: `{fmt_hex(report['parameters']['primary_arg'])}`",
        f"- primary arg source: `{report['parameters']['primary_arg_source']}`",
        f"- WRITE BUFFER CDB layout: `{report['parameters']['write_cdb_layout']}`",
        f"- live boot marker: `{report['boot_marker_model']['live_marker_ascii']}`",
        f"- target family marker: `{report['boot_marker_model']['target_family_ascii']}`",
        f"- target boot marker: `{report['boot_marker_model']['target_marker_ascii']}`",
        f"- boot mismatch: `{report['boot_marker_model']['boot_mismatch']}`",
        f"- boot-mismatch risk: `{report['boot_marker_model']['risk']}`",
        f"- setup length: `{fmt_hex(report['parameters']['setup_length'])}`",
        f"- setup length source: `{report['parameters']['setup_length_source']}`",
        f"- explicit profile selectors: `{report['parameters']['profile_selectors']}`",
        f"- profile selector source: `{report['parameters']['profile_selector_source']}`",
        f"- profile selector branch: `{report['parameters']['profile_selector_branch']}`",
        f"- implicit selector enabled: `{report['parameters']['implicit_selector_enabled']}`",
        f"- implicit selector source: `{report['parameters']['implicit_selector_source']}`",
        f"- arg00 primary offset model: `{report['parameters']['arg00_primary_offset_model']}`",
        f"- selector order: `{report['transport_model']['selector_order']}`",
        f"- AES bank index: `{report['transport_model']['aes_bank_index']}`",
        f"- selected AES banks: `{report['transport_model']['selected_bank_indices']}`",
        f"- initial pMac state: `{report['transport_model']['initial_pmac_state']}`",
        f"- initial pMac source: `{report['transport_model']['initial_pmac_state_source']}`",
        "",
        "## Prelude CDB Models",
        "",
        "| phase | source | CDB | data out | risk |",
        "|---|---|---|---:|---|",
    ]

    for event in report["prelude"]:
        lines.append(
            f"| {event['phase']} | {event['source']} | `{event['cdb']}` | "
            f"{event['data_out_len']} | {event['risk']} |"
        )

    lines += [
        "",
        "## Chunk Model",
        "",
        (
            "The chunk rows below model updater selector-gated transport. Chunks in "
            "the EXTRAINQ-selected AES bank are AES-CBC encrypted and fed to the "
            "pMac helper; other chunks remain source bytes in this model."
        ),
        "",
        f"- chunks modeled: `{report['counts']['chunks']}`",
        f"- 0x10000-byte selector banks modeled: `{report['counts']['banks']}`",
        "",
        f"First `{min(detail_chunks, len(report['chunks']))}` chunks:",
        "",
        "| chunk | offset | bank | selector | transform | arg00 primary CDB | transport first16 | pMac if final |",
        "|---:|---:|---:|---:|---|---|---|---|",
    ]

    for row in report["chunks"][:detail_chunks]:
        pmac = row["pmac_if_selected_final"] or ""
        lines.append(
            f"| {row['chunk_index']} | `{fmt_hex(row['source_offset'], 5)}` | {row['bank']} | "
            f"{row['implicit_selector_value']} | {row['transport_transform']} | "
            f"`{row['arg00_retry_primary_cdb']}` | `{row['transport_first16']}` | `{pmac}` |"
        )

    lines += [
        "",
        "## Selector Bank Boundary Values",
        "",
        "| bank | selector | AES-selected | chunk range | offset range | finalized pMac | copied pMac model | 16-byte prefix CDB |",
        "|---:|---:|:---:|---|---|---|---|---|",
    ]

    for bank in report["banks"]:
        pmac = bank["pmac"] or ""
        copied = bank["copied_pmac_state_model"] or ""
        lines.append(
            f"| {bank['bank']} | {bank['selector']} | {bank['selected_for_aes_transport']} | "
            f"{bank['first_chunk']}..{bank['last_chunk']} | "
            f"`{fmt_hex(bank['offset_start'], 5)}..{fmt_hex(bank['offset_end'], 5)}` | "
            f"`{pmac}` | `{copied}` | `{bank['pmac_prefix_cdb']}` |"
        )

    lines += [
        "",
        "## Excluded Or Unresolved",
        "",
        "- The arg=7f profile-tail path is not emitted as an executable candidate; it reaches firmware verify/program-like helpers.",
        "- Explicit selector setup (`1,0`) is only modeled for the updater's 0x35bf4 special profile branch; the normal 1 MiB path uses implicit CDB byte 10 selectors.",
        "- Profile-tail transfer lengths and exact profile IDs remain unresolved for the special profile branch.",
        "- The arg00 retry path has full-offset and low16-offset updater call-site variants; EXTRAINQ feature bits select low16 for the live profile.",
        "- Initial pMac copy data before the selected AES bank is modeled as zeros from the LE autodata zerofill page; runtime tracing is still needed to prove no earlier updater call mutates it.",
        "- The boot marker compare is now modeled explicitly. AD12-on-LD5M selects the high-risk 0xa0 boot-code path, while same-marker LD5M tests select 0x80.",
        "- `official-byte9` CDB layout matches the Windows updater helper trace; `live-byte10` preserves the older live-accepted probing dialect.",
        "- This report is a comparison target for further RE, not a flashing recipe.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--extrainq", type=Path, default=DEFAULT_EXTRAINQ)
    parser.add_argument(
        "--transport-extrainq",
        type=Path,
        default=None,
        help="EXTRAINQ source for AES-CBC transport and pMac key/IV; defaults to --extrainq",
    )
    parser.add_argument("--chunk-size", type=int_arg, default=0x4000)
    parser.add_argument("--bank-size", type=int_arg, default=0x10000)
    parser.add_argument(
        "--write-cdb-layout",
        choices=("live-byte10", "official-byte9"),
        default="live-byte10",
        help=(
            "WRITE BUFFER byte layout: live-byte10 keeps the live-probed byte10 arg/byte11 selector shape; "
            "official-byte9 matches the Windows updater byte9 arg/byte10 selector helper"
        ),
    )
    parser.add_argument(
        "--primary-arg",
        default="auto",
        help="Primary 0x80/0xa0 control arg, or 'auto' to derive from live/target boot marker compare",
    )
    parser.add_argument("--setup-length", type=int_arg, default=None)
    parser.add_argument(
        "--profile-selectors",
        default="auto",
        help=(
            "Comma-separated explicit selector setup list, 'none', or 'auto'. "
            "Auto emits 1,0 only for the 0x20000 special profile branch."
        ),
    )
    parser.add_argument("--include-profile-tail-arg00", action="store_true")
    parser.set_defaults(implicit_selector_enabled=None)
    parser.add_argument(
        "--implicit-selector-enabled",
        dest="implicit_selector_enabled",
        action="store_true",
        help="Force 0x35c47-style implicit selector mode and low16 arg00 offsets",
    )
    parser.add_argument(
        "--implicit-selector-disabled",
        dest="implicit_selector_enabled",
        action="store_false",
        help="Force full-offset arg00 mode instead of deriving 0x35c47 from EXTRAINQ",
    )
    parser.add_argument("--implicit-selector", type=int_arg, default=0)
    parser.add_argument("--detail-chunks", type=int, default=8)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validate_u8(args.implicit_selector, "implicit selector")
    if args.detail_chunks < 0:
        raise ValueError("--detail-chunks must be non-negative")
    primitive_tests = self_test()
    if not primitive_tests["ok"]:
        print("error: crypto primitive self-test failed", file=sys.stderr)
        return 2

    image = args.image.read_bytes()
    extrainq, _base_iv, _base_key = parse_extrainq(args.extrainq)
    transport_extrainq_path = args.transport_extrainq or args.extrainq
    transport_extrainq, transport_iv, transport_key = parse_extrainq(transport_extrainq_path)
    args.primary_arg, primary_arg_source, boot_marker_model = derive_primary_arg(args, image, extrainq)
    validate_u8(args.primary_arg, "primary arg")
    args.profile_selectors, profile_selector_source, profile_selector_branch = derive_profile_selectors(
        args, len(image), extrainq
    )
    args.implicit_selector_enabled, implicit_selector_source = derive_implicit_selector(args, extrainq)
    args.setup_length, setup_length_source = derive_setup_length(args, extrainq)
    validate_u24(args.setup_length, "setup length")
    chunks, banks, transport_model = build_chunk_model(
        args,
        image,
        transport_key,
        transport_iv,
        extrainq,
        transport_extrainq,
    )
    chunks_per_bank = args.bank_size // args.chunk_size
    report: dict[str, Any] = {
        "status": "offline_model_only_not_flashable_do_not_execute",
        "inputs": {
            "image": str(args.image),
            "image_length": len(image),
            "image_sha256": sha256_file(args.image),
        },
        "extrainq": extrainq,
        "transport_extrainq": transport_extrainq,
        "parameters": {
            "chunk_size": args.chunk_size,
            "bank_size": args.bank_size,
            "chunks_per_bank": chunks_per_bank,
            "write_cdb_layout": args.write_cdb_layout,
            "primary_arg": args.primary_arg,
            "primary_arg_source": primary_arg_source,
            "setup_length": args.setup_length,
            "setup_length_source": setup_length_source,
            "profile_selectors": args.profile_selectors,
            "profile_selector_source": profile_selector_source,
            "profile_selector_branch": profile_selector_branch,
            "include_profile_tail_arg00": args.include_profile_tail_arg00,
            "implicit_selector_enabled": args.implicit_selector_enabled,
            "implicit_selector_source": implicit_selector_source,
            "implicit_selector": args.implicit_selector,
            "arg00_primary_offset_model": "low16" if args.implicit_selector_enabled else "full",
            "cbc_transport_model": "selector_gated_aes_bank",
        },
        "boot_marker_model": boot_marker_model,
        "transport_model": transport_model,
        "self_test": primitive_tests,
        "prelude": build_prelude(args, extrainq, boot_marker_model),
        "chunks": chunks,
        "banks": banks,
        "counts": {
            "chunks": len(chunks),
            "banks": len(banks),
            "selected_aes_banks": len(transport_model["selected_bank_indices"]),
            "selected_aes_chunks": len(transport_model["selected_chunk_indices"]),
            "prelude_cdb_models": len(build_prelude(args, extrainq, boot_marker_model)),
        },
        "warnings": [
            "offline-only model; this is not a live flashing sequence",
            "selector-gated AES bank model is statically anchored; use an official trace comparison before trusting a generated plan",
            "transport EXTRAINQ affects only AES-CBC/pMac key material; --extrainq remains the source for profile flags, selector, and boot-marker branching",
            "CDD/source-container packing and writable LD5M dialect checks are unresolved",
            "no arg=7f erase/program/finalize candidate is emitted",
            "implicit selector mode defaults from EXTRAINQ feature low bits; override explicitly for experiments",
            "initial pMac prefix bytes are modeled from LE zerofill but still need runtime trace confirmation",
            "0xa0 primary arg is a boot-code/bEraseBootCode path and remains live-blocked without recovery",
        ],
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report, args.detail_chunks) + "\n", encoding="utf-8")

    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    print(f"status={report['status']}")
    print(f"chunks={len(chunks)} banks={len(banks)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
