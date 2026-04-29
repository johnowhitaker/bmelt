#!/usr/bin/env python3
"""Render a same-F0 candidate with modified profile-tail helper byte(s).

Offline only.  This builds a high-information live-test candidate: keep the F0
image and all chunk/pMac traffic identical to the passing same-image control,
but replace selected currentboot profile-tail payloads with a
re-encrypted/re-CMACed helper plaintext that has a one-byte mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_liteon_profile_tail_payload import profile_tail_cdb  # noqa: E402
from generate_liteon_write_sequence_dry_run import hex_bytes, parse_extrainq  # noqa: E402
from model_liteon_updater_write_crypto import aes_cbc_encrypt_chunks, aes_cmac  # noqa: E402


EXTRACTED = ROOT / "references/firmware/extracted"
DEFAULT_BASE_CANDIDATE = EXTRACTED / "liteon-full-currentboot-ld5m-base-candidate.json"
DEFAULT_PLAIN_TAIL = EXTRACTED / "liteon-official-profile-tail-ef130045-plain.bin"
DEFAULT_CURRENTBOOT_TAIL = EXTRACTED / "liteon-profile-tail-ef130045-ld5m-official-currentboot.json"
DEFAULT_OUT_DIR = EXTRACTED / "profile-tail-mutation-candidates"
DEFAULT_OUT_CANDIDATE = EXTRACTED / "liteon-full-currentboot-ld5m-base-mutated-helper-string-candidate.json"
DEFAULT_OUT_MD = EXTRACTED / "liteon-profile-tail-helper-mutation-candidate.md"
DEFAULT_OUT_JSON = EXTRACTED / "liteon-profile-tail-helper-mutation-candidate.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def path_from_report(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_byte(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("byte value must be 0..255")
    return parsed


def parse_offset(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("offset must be non-negative")
    return parsed


def parse_patch(value: str) -> tuple[int, bytes]:
    try:
        offset_text, hex_text = value.split(":", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("patch must be OFFSET:HEX") from exc
    offset = parse_offset(offset_text)
    compact = "".join(ch for ch in hex_text if ch in "0123456789abcdefABCDEF")
    if not compact or len(compact) % 2:
        raise argparse.ArgumentTypeError("patch hex must be non-empty whole bytes")
    return offset, bytes.fromhex(compact)


def byte_note(byte: int) -> dict[str, Any]:
    return {
        "value": byte,
        "ascii": chr(byte) if 32 <= byte <= 126 else None,
    }


def host_offsets(offset: int) -> dict[str, int | None]:
    return {
        "host_id01_offset_from_018000": 0x018000 + offset,
        "host_id01_offset_from_018006_body": 0x018006 + offset - 6 if offset >= 6 else None,
    }


def mutate_plain_tail(
    plain: bytes,
    *,
    offset: int,
    xor_value: int,
    patches: list[tuple[int, bytes]] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    out = bytearray(plain)
    if patches:
        applied: list[dict[str, Any]] = []
        for patch_offset, replacement in patches:
            end = patch_offset + len(replacement)
            if not 0 <= patch_offset < len(plain) or end > len(plain):
                raise ValueError(
                    f"plain patch {patch_offset:#x}+{len(replacement):#x} outside "
                    f"profile-tail length {len(plain):#x}"
                )
            before = bytes(out[patch_offset:end])
            out[patch_offset:end] = replacement
            patch_report: dict[str, Any] = {
                "plain_offset": patch_offset,
                "body_offset": patch_offset - 6 if patch_offset >= 6 else None,
                "length": len(replacement),
                "before_hex": before.hex(),
                "after_hex": replacement.hex(),
                **host_offsets(patch_offset),
            }
            if len(replacement) == 1:
                patch_report.update(
                    {
                        "before": byte_note(before[0]),
                        "after": byte_note(replacement[0]),
                    }
                )
            applied.append(patch_report)
        first_offset = int(applied[0]["plain_offset"])
        return bytes(out), {
            "kind": "patch_bytes",
            "plain_offset": first_offset,
            "body_offset": first_offset - 6 if first_offset >= 6 else None,
            "patches": applied,
            **host_offsets(first_offset),
        }

    if not 0 <= offset < len(plain):
        raise ValueError(f"plain offset {offset:#x} outside profile-tail length {len(plain):#x}")
    before_byte = out[offset]
    out[offset] ^= xor_value
    after_byte = out[offset]
    return bytes(out), {
        "kind": "xor_byte",
        "plain_offset": offset,
        "body_offset": offset - 6 if offset >= 6 else None,
        "before": before_byte,
        "after": after_byte,
        "xor": xor_value,
        "before_ascii": chr(before_byte) if 32 <= before_byte <= 126 else None,
        "after_ascii": chr(after_byte) if 32 <= after_byte <= 126 else None,
        **host_offsets(offset),
    }


def build_profile_payload(plain: bytes, tail_report: dict[str, Any]) -> dict[str, Any]:
    extrainq_path = path_from_report(tail_report["extrainq"])
    _extrainq, iv, key = parse_extrainq(extrainq_path)
    ciphertext = aes_cbc_encrypt_chunks(key, iv, [plain])[0]
    cmac = aes_cmac(key, ciphertext)
    payload = ciphertext + cmac
    cdb = profile_tail_cdb(offset=0, length=len(payload), arg_control=0x7F)
    if len(payload) != int(tail_report["payload_len"]):
        raise ValueError(f"payload length changed: {len(payload)} != {tail_report['payload_len']}")
    return {
        "extrainq": str(extrainq_path),
        "iv": iv.hex(),
        "key": key.hex(),
        "ciphertext": ciphertext,
        "cmac": cmac,
        "payload": payload,
        "cdb": hex_bytes(cdb),
        "plain_sha256": sha256_bytes(plain),
        "ciphertext_sha256": sha256_bytes(ciphertext),
        "payload_sha256": sha256_bytes(payload),
        "payload_first16": payload[:16].hex(),
    }


def update_inline_event(event: dict[str, Any], payload_info: dict[str, Any], source: dict[str, Any]) -> None:
    payload = payload_info["payload"]
    event["payload_first16"] = payload[:16].hex()
    event["payload_sha256"] = sha256_bytes(payload)
    event["data_out_len"] = len(payload)
    event["cdb"] = payload_info["cdb"]
    model = event.get("payload_model")
    if not isinstance(model, dict) or model.get("kind") != "inline_payload_hex":
        raise ValueError("target event is not an inline payload event")
    model["payload_hex"] = payload.hex()
    model["payload_first16"] = payload[:16].hex()
    model["payload_sha256"] = sha256_bytes(payload)
    model["profile_tail_mutation"] = source


def select_target_events(events: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.all_currentboot_tails:
        targets = [
            event
            for event in events
            if event.get("phase") == "profile_tail_arg7f"
            and "currentboot-key" in str(event.get("role", ""))
        ]
        if not targets:
            raise ValueError("no currentboot-key profile_tail_arg7f events found")
        return targets

    target = next((event for event in events if int(event.get("event_index")) == args.event_index), None)
    if target is None:
        raise ValueError(f"event {args.event_index} not found")
    if target.get("phase") != "profile_tail_arg7f":
        raise ValueError(f"event {args.event_index} is not a profile_tail_arg7f event")
    if not args.allow_pre_tail and "currentboot-key" not in str(target.get("role", "")):
        raise ValueError(f"event {args.event_index} does not look like a currentboot-key tail")
    return [target]


def render_candidate(args: argparse.Namespace) -> dict[str, Any]:
    candidate = load_json(args.base_candidate)
    tail_report = load_json(args.currentboot_tail)
    plain = args.plain_tail.read_bytes()
    mutated_plain, mutation = mutate_plain_tail(
        plain,
        offset=args.plain_offset,
        xor_value=args.xor,
        patches=args.patch,
    )
    payload_info = build_profile_payload(mutated_plain, tail_report)

    events = candidate.get("events")
    if not isinstance(events, list):
        raise ValueError("candidate has no events list")
    targets = select_target_events(events, args)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    mutated_plain_path = args.out_dir / "ef130045-mutated-string-plain.bin"
    mutated_payload_path = args.out_dir / "ef130045-mutated-string-currentboot-payload.bin"
    mutated_plain_path.write_bytes(mutated_plain)
    mutated_payload_path.write_bytes(payload_info["payload"])

    source = {
        "kind": "same_f0_profile_tail_plaintext_mutation",
        "plain_tail_base": str(args.plain_tail),
        "plain_tail_mutated": str(mutated_plain_path),
        "payload_mutated": str(mutated_payload_path),
        "target_event_index": int(targets[0].get("event_index")),
        "target_event_indexes": [int(event.get("event_index")) for event in targets],
        "target_scope": "all_currentboot_tails" if args.all_currentboot_tails else "single_event",
        "mutation": mutation,
        "plain_sha256_before": sha256_bytes(plain),
        "plain_sha256_after": payload_info["plain_sha256"],
        "payload_sha256_after": payload_info["payload_sha256"],
        "cmac_after": payload_info["cmac"].hex(),
        "expected_visible_helper_host_offset": mutation["host_id01_offset_from_018000"],
    }
    for target in targets:
        update_inline_event(target, payload_info, source)
    candidate.setdefault("mutations", []).append(source)
    suffix = "all-currentboot-profile-tail-helper" if args.all_currentboot_tails else "profile-tail-helper"
    candidate["status"] = f"{candidate.get('status', 'candidate')}-mutated-{suffix}"
    candidate["event_count"] = len(events)

    args.out_candidate.parent.mkdir(parents=True, exist_ok=True)
    args.out_candidate.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    expected_offset = mutation["host_id01_offset_from_018000"]
    target_indexes = [int(target.get("event_index")) for target in targets]
    first_target = target_indexes[0]
    target_desc = (
        f"event {first_target}" if len(target_indexes) == 1 else f"first mutated event {first_target}"
    )
    return {
        "status": "offline_profile_tail_helper_mutation_candidate",
        "base_candidate": str(args.base_candidate),
        "out_candidate": str(args.out_candidate),
        "target_scope": source["target_scope"],
        "target_events": [
            {
                "event_index": int(target.get("event_index")),
                "phase": target.get("phase"),
                "role": target.get("role"),
                "cdb": target.get("cdb"),
            }
            for target in targets
        ],
        "outputs": {
            "mutated_plain_tail": str(mutated_plain_path),
            "mutated_payload": str(mutated_payload_path),
            "candidate": str(args.out_candidate),
        },
        "mutation": source,
        "expected_live_signals": [
            f"If {target_desc} fails immediately, the profile-tail payload/plaintext is checked before finalizer admission.",
            f"If the mutated tail events succeed but event 544 rejects, the finalizer admission covers or depends on the helper overlay bytes.",
            f"If event 544 passes and READ BUFFER id=01 around host offset {expected_offset:#08x} shows the changed byte, the helper overlay is mutable independently of the F0 container.",
            "If event 544 passes but the helper window is canonical, the controller re-exposes its own helper copy rather than the staged mutated payload.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    mutation = report["mutation"]["mutation"]
    body_offset = mutation["body_offset"]
    body_offset_text = f"{body_offset:#x}" if body_offset is not None else "n/a (profile-tail header)"
    patches = mutation.get("patches")
    target_indexes = report["mutation"].get("target_event_indexes") or [
        event["event_index"] for event in report["target_events"]
    ]
    target_text = (
        f"event `{target_indexes[0]}`"
        if len(target_indexes) == 1
        else f"{len(target_indexes)} events: `{', '.join(str(index) for index in target_indexes)}`"
    )
    payload_text = (
        "The candidate changes one currentboot profile-tail payload. The staged F0 chunks and all bank pMac/control payloads remain those of the same-image LD5M control."
        if len(target_indexes) == 1
        else "The candidate changes every currentboot-key profile-tail payload. The staged F0 chunks and all bank pMac/control payloads remain those of the same-image LD5M control."
    )
    lines = [
        "# LiteOn Profile-Tail Helper Mutation Candidate",
        "",
        "Offline dry-run artifact. No drive commands were sent.",
        "",
        "## Purpose",
        "",
        "Test whether the `ef130045` profile-tail helper overlay is independently mutable once the F0 image is kept byte-identical to the passing same-image control.",
        "",
        payload_text,
        "",
        f"Selected target scope: `{report['target_scope']}` ({target_text}).",
        "",
        "## Mutation",
        "",
        f"- first plain profile-tail offset: `{mutation['plain_offset']:#x}`.",
        f"- first helper body offset: `{body_offset_text}`.",
    ]
    if patches:
        for patch in patches:
            patch_body = patch["body_offset"]
            patch_body_text = f"{patch_body:#x}" if patch_body is not None else "n/a"
            lines.append(
                f"- patch `{patch['plain_offset']:#x}` body `{patch_body_text}`: "
                f"`{patch['before_hex']}` -> `{patch['after_hex']}`."
            )
    else:
        lines.append(
            f"- byte: `{mutation['before']:#x}`"
            + (f" (`{mutation['before_ascii']}`)" if mutation["before_ascii"] else "")
            + " -> "
            + f"`{mutation['after']:#x}`"
            + (f" (`{mutation['after_ascii']}`)" if mutation["after_ascii"] else "")
            + f" via xor `{mutation['xor']:#x}`."
        )
    lines.extend(
        [
        f"- expected host READ BUFFER id=01 offset if admitted: `{mutation['host_id01_offset_from_018000']:#x}`.",
        "",
        "## Outputs",
        "",
        f"- candidate: `{report['outputs']['candidate']}`",
        f"- mutated plaintext tail: `{report['outputs']['mutated_plain_tail']}`",
        f"- mutated currentboot payload: `{report['outputs']['mutated_payload']}`",
        "",
        "## Expected Live Interpretations",
        "",
        ]
    )
    for item in report["expected_live_signals"]:
        lines.append(f"- {item}")
    expected_offset = mutation["host_id01_offset_from_018000"]
    capture_event = target_indexes[0]
    lines.extend(
        [
            "",
            "## Suggested Probe Shape",
            "",
            "- Run only after explicitly choosing drive #1 as the live sacrificial/recoverable target.",
            f"- Capture the first mutated event (`{capture_event}`) return code, event-544 return code, final revision, and READ BUFFER id `01` around `{expected_offset:#08x}`.",
            "- Auto-recover with the known Linux recovery path if the run enters `0D5C`.",
            "",
            "One suitable Linux runner shape is:",
            "",
            "```bash",
            "python3 scripts/run_liteon_linux_persistence_experiment.py \\",
            f"  --candidate {report['outputs']['candidate']} \\",
            "  --device /dev/sg1 \\",
            "  --skip-pre-f0 --skip-post-f0 \\",
            "  --end-index 544 \\",
            f"  --capture-finalizer-status-after-event {capture_event} \\",
            "  --capture-finalizer-status \\",
            "  --recover-on-currentboot",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-candidate", type=Path, default=DEFAULT_BASE_CANDIDATE)
    parser.add_argument("--plain-tail", type=Path, default=DEFAULT_PLAIN_TAIL)
    parser.add_argument("--currentboot-tail", type=Path, default=DEFAULT_CURRENTBOOT_TAIL)
    parser.add_argument("--event-index", type=int, default=511)
    parser.add_argument(
        "--allow-pre-tail",
        action="store_true",
        help="allow a non-currentboot profile-tail event such as the pre-tail before bank 0",
    )
    parser.add_argument(
        "--all-currentboot-tails",
        action="store_true",
        help="mutate every currentboot-key profile_tail_arg7f event instead of one event",
    )
    parser.add_argument("--plain-offset", type=parse_offset, default=0x620)
    parser.add_argument("--xor", type=parse_byte, default=0x01)
    parser.add_argument(
        "--patch",
        action="append",
        type=parse_patch,
        help="replace bytes in the plaintext profile-tail as OFFSET:HEX; may be repeated",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--out-candidate", type=Path, default=DEFAULT_OUT_CANDIDATE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args(argv)

    report = render_candidate(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(report), encoding="utf-8")
    print(f"wrote {args.out_candidate}")
    print(f"wrote {args.out_json}")
    print(f"wrote {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
