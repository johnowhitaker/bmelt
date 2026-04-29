#!/usr/bin/env python3
"""Render a full currentboot replay candidate.

The candidate starts from normal LD5M state:

1. read EXTRAINQ
2. send the pre-tail LD5M profile-tail payload
3. stage bank 0 and cross the bank-0 pMac/currentboot boundary
4. send currentboot-key profile tails before banks 1..15
5. stage/read back every remaining bank and pMac boundary
6. send the final PLDSVUC lock/status transition

This script is offline only; it writes an inline JSON replay artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from model_liteon_updater_write_crypto import aes_cbc_encrypt_chunks  # noqa: E402


DEFAULT_MODEL = ROOT / "references/firmware/extracted/liteon-dry-run-write-sequence-ld5m-sentinel-official-style.json"
DEFAULT_PRETAIL = ROOT / "references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-pretail.json"
DEFAULT_CURRENTBOOT_TAIL = (
    ROOT / "references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-currentboot.json"
)
DEFAULT_BASE_IMAGE = ROOT / "references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin"
DEFAULT_OUT = ROOT / "references/firmware/extracted/liteon-same-family-full-currentboot-candidate.json"

LIVE_EXTRAINQ_CDB = "12 00 00 00 F0 40 00 00 00 00 00 00"
PLDSVUC_LOCK_CDB = "F3 00 50 4C 44 53 56 55 43 80 00 00"
BASELINE_LD5M_SHA256 = "488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39"


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prefix_hashes(data: bytes) -> dict[str, str]:
    sizes = [0x8000, 0x30000, 0xE0000, 0x100000]
    return {f"0x{size:x}": sha256_bytes(data[:size]) for size in sizes if size <= len(data)}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_from_report(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def hex_bytes(data: bytes) -> str:
    return " ".join(f"{item:02X}" for item in data)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_profile_tail(path: Path) -> tuple[dict[str, Any], bytes]:
    report = load_json(path)
    payload_path = path_from_report(report["payload_path"])
    payload = payload_path.read_bytes()
    if len(payload) != int(report["payload_len"]):
        raise ValueError(f"profile-tail length mismatch for {payload_path}")
    expected_sha = report.get("payload_sha256")
    if expected_sha and sha256_bytes(payload) != expected_sha:
        raise ValueError(f"profile-tail hash mismatch for {payload_path}")
    return report, payload


def inline_event(
    index: int,
    phase: str,
    cdb: str,
    *,
    payload: bytes = b"",
    data_in_len: int = 0,
    role: str,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_model: dict[str, Any]
    if payload:
        payload_model = {
            "kind": "inline_payload_hex",
            "payload_hex": payload.hex(),
            "payload_first16": payload[:16].hex(),
            "payload_sha256": sha256_bytes(payload),
        }
    else:
        payload_model = {"kind": "no_data"}
    if source:
        payload_model.update(source)
    return {
        "event_index": index,
        "phase": phase,
        "cdb": cdb,
        "data_out_len": len(payload),
        "data_in_len": data_in_len,
        "payload_first16": payload[:16].hex(),
        "payload_sha256": sha256_bytes(payload) if payload else None,
        "payload_model": payload_model,
        "role": role,
    }


def readback_event(index: int, chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_index": index,
        "phase": "arg00_readback_verify",
        "cdb": chunk["arg00_readback_verify_cdb"],
        "data_out_len": 0,
        "data_in_len": int(chunk["arg00_readback_verify_data_in_len"]),
        "payload_first16": "",
        "payload_sha256": None,
        "payload_model": {
            "kind": "readback_compare",
            "source_offset": chunk["source_offset"],
            "source_end": chunk["source_end"],
            "transport_first16": chunk["transport_first16"],
            "transport_sha256": chunk["transport_sha256"],
            "chunk_index": chunk["chunk_index"],
            "bank": chunk["bank"],
            "chunk_in_bank": chunk["chunk_in_bank"],
        },
        "role": f"readback verify bank {chunk['bank']} chunk {chunk['chunk_in_bank']}",
    }


def encrypted_payloads_by_chunk(model: dict[str, Any], image: bytes) -> dict[int, bytes]:
    key = bytes.fromhex(model["transport_model"]["transport_key_hex"])
    iv = bytes.fromhex(model["transport_model"]["transport_iv_hex"])
    selected_indices = set(model["transport_model"]["selected_chunk_indices"])
    selected_chunks = [chunk for chunk in model["chunks"] if chunk["chunk_index"] in selected_indices]
    selected_plain = [image[chunk["source_offset"] : chunk["source_end"]] for chunk in selected_chunks]
    selected_encrypted = aes_cbc_encrypt_chunks(key, iv, selected_plain)
    return {
        chunk["chunk_index"]: encrypted
        for chunk, encrypted in zip(selected_chunks, selected_encrypted, strict=True)
    }


def diff_summary(base: bytes | None, target: bytes) -> dict[str, Any] | None:
    if base is None or len(base) != len(target):
        return None
    offsets = [index for index, (old, new) in enumerate(zip(base, target, strict=True)) if old != new]
    first = [
        {
            "offset": offset,
            "old": base[offset],
            "new": target[offset],
            "bank": offset // 0x10000,
            "chunk": offset // 0x1000,
        }
        for offset in offsets[:16]
    ]
    return {"modified_byte_count": len(offsets), "first_modified_offsets": first}


def build_candidate(args: argparse.Namespace) -> dict[str, Any]:
    model = load_json(args.model)
    image_path = path_from_report(model["inputs"]["image"])
    image = image_path.read_bytes()
    base = args.base_image.read_bytes() if args.base_image and args.base_image.exists() else None
    pretail_report, pretail_payload = load_profile_tail(args.pretail)
    currentboot_report, currentboot_payload = load_profile_tail(args.currentboot_tail)
    encrypted_by_index = encrypted_payloads_by_chunk(model, image)

    events: list[dict[str, Any]] = []
    index = 0
    events.append(
        inline_event(
            index,
            "live_extrainq_read",
            LIVE_EXTRAINQ_CDB,
            data_in_len=0xF0,
            role="read live EXTRAINQ before first profile-tail transition",
        )
    )
    index += 1
    events.append(
        inline_event(
            index,
            "profile_tail_arg7f",
            pretail_report["cdb"],
            payload=pretail_payload,
            role="pre-tail LD5M profile tail before bank 0",
            source={
                "payload_path": pretail_report["payload_path"],
                "profile_tail_kind": "same_family_ld5m_official_pretail",
                "plain_sha256": pretail_report.get("plain_sha256"),
                "cmac": pretail_report.get("cmac"),
            },
        )
    )
    index += 1

    chunks_by_bank: dict[int, list[dict[str, Any]]] = {}
    for chunk in model["chunks"]:
        chunks_by_bank.setdefault(int(chunk["bank"]), []).append(chunk)
    for chunks in chunks_by_bank.values():
        chunks.sort(key=lambda item: int(item["chunk_in_bank"]))

    for bank in range(len(model["banks"])):
        if bank > 0:
            events.append(
                inline_event(
                    index,
                    "profile_tail_arg7f",
                    currentboot_report["cdb"],
                    payload=currentboot_payload,
                    role=f"currentboot-key LD5M profile tail before bank {bank}",
                    source={
                        "payload_path": currentboot_report["payload_path"],
                        "profile_tail_kind": "same_family_ld5m_official_currentboot",
                        "plain_sha256": currentboot_report.get("plain_sha256"),
                        "cmac": currentboot_report.get("cmac"),
                    },
                )
            )
            index += 1

        for chunk in chunks_by_bank.get(bank, []):
            plain = image[chunk["source_offset"] : chunk["source_end"]]
            payload = encrypted_by_index.get(chunk["chunk_index"], plain)
            expected_sha = chunk["transport_sha256"]
            actual_sha = sha256_bytes(payload)
            if actual_sha != expected_sha:
                raise ValueError(
                    f"chunk {chunk['chunk_index']} transport sha mismatch: {actual_sha} != {expected_sha}"
                )
            events.append(
                inline_event(
                    index,
                    "arg00_chunk_transfer",
                    chunk["arg00_retry_primary_cdb"],
                    payload=payload,
                    role=f"stage bank {bank} chunk {chunk['chunk_in_bank']}",
                    source={
                        "source_offset": chunk["source_offset"],
                        "source_end": chunk["source_end"],
                        "chunk_index": chunk["chunk_index"],
                        "bank": chunk["bank"],
                        "chunk_in_bank": chunk["chunk_in_bank"],
                        "transport_transform": chunk["transport_transform"],
                    },
                )
            )
            index += 1
            events.append(readback_event(index, chunk))
            index += 1

        bank_row = model["banks"][bank]
        pmac_hex = bank_row.get("pmac") or bank_row.get("copied_pmac_state_model")
        pmac = bytes.fromhex(compact_hex(pmac_hex or ""))
        if len(pmac) != 16:
            raise ValueError(f"bank {bank} pMac prefix is not 16 bytes")
        events.append(
            inline_event(
                index,
                "bank_pmac_prefix",
                bank_row["pmac_prefix_cdb"],
                payload=pmac,
                role=f"bank {bank} pMac/control prefix",
                source={
                    "bank": bank_row["bank"],
                    "selector": bank_row["selector"],
                    "selected_for_aes_transport": bank_row["selected_for_aes_transport"],
                    "copied_pmac_state_model": bank_row.get("copied_pmac_state_model"),
                    "pmac": bank_row.get("pmac"),
                },
            )
        )
        index += 1

    events.append(
        inline_event(
            index,
            "pldsvuc_lock",
            PLDSVUC_LOCK_CDB,
            role="final PLDSVUC lock/status transition",
        )
    )

    phase_counts = Counter(str(event["phase"]) for event in events)
    return {
        "status": "offline_same_family_full_currentboot_candidate",
        "inputs": {
            "model": str(args.model),
            "model_sha256": sha256_file(args.model),
            "target_image": str(image_path),
            "target_image_sha256": sha256_bytes(image),
            "base_image": str(args.base_image) if args.base_image else None,
            "base_image_sha256": sha256_file(args.base_image) if args.base_image and args.base_image.exists() else None,
            "pretail": str(args.pretail),
            "pretail_sha256": sha256_file(args.pretail),
            "currentboot_tail": str(args.currentboot_tail),
            "currentboot_tail_sha256": sha256_file(args.currentboot_tail),
        },
        "parameters": {
            **model["parameters"],
            "start_revision": "LD5M",
            "expected_final_revision": args.expected_final_revision,
            "normal_start_pretail_before_bank0": True,
            "currentboot_tail_before_banks": list(range(1, len(model["banks"]))),
            "final_pldsvuc_lock": True,
        },
        "expected_hashes_for_live_execution": {
            "expect_pre_sha256": BASELINE_LD5M_SHA256,
            "expect_post_sha256": sha256_bytes(image),
            "expect_pre_sha256_by_size": prefix_hashes(base),
            "expect_post_sha256_by_size": prefix_hashes(image),
            "note": "Post hash is a strict persistence proof target for decrypted READ BUFFER F0.",
        },
        "diff_summary": diff_summary(base, image),
        "event_count": len(events),
        "phase_counts": dict(phase_counts),
        "total_data_out_bytes": sum(int(event["data_out_len"]) for event in events),
        "events": events,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--pretail", type=Path, default=DEFAULT_PRETAIL)
    parser.add_argument("--currentboot-tail", type=Path, default=DEFAULT_CURRENTBOOT_TAIL)
    parser.add_argument("--base-image", type=Path, default=DEFAULT_BASE_IMAGE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--expected-final-revision",
        default="LD5M",
        help="metadata for live runners; use the target image revision for official-image probes",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidate = build_candidate(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.out_json}")
    print(json.dumps({key: candidate[key] for key in ["status", "event_count", "phase_counts", "total_data_out_bytes"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
