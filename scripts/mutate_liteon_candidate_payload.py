#!/usr/bin/env python3
"""Create a LiteOn candidate variant by changing one inline event payload.

This is meant for narrow control experiments: keep the CDB sequence and staged
image identical, but perturb a single WRITE BUFFER payload so the result can be
attributed to that boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_xor(value: str) -> int:
    parsed = int(value, 0)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("--xor must be a byte value")
    return parsed


def parse_payload_hex(value: str) -> bytes:
    compact = compact_hex(value)
    if len(compact) % 2:
        raise argparse.ArgumentTypeError("--payload-hex must have an even number of hex digits")
    return bytes.fromhex(compact)


def event_matches(event: dict[str, Any], event_index: int) -> bool:
    try:
        return int(event.get("event_index")) == event_index
    except (TypeError, ValueError):
        return False


def update_payload_fields(event: dict[str, Any], payload: bytes) -> None:
    payload_hex = payload.hex()
    payload_sha256 = sha256_hex(payload)
    event["payload_first16"] = payload[:16].hex()
    event["payload_sha256"] = payload_sha256
    event["data_out_len"] = len(payload)

    model = event.get("payload_model")
    if not isinstance(model, dict) or model.get("kind") != "inline_payload_hex":
        raise ValueError("target event payload_model is not inline_payload_hex")
    model["payload_hex"] = payload_hex
    model["payload_first16"] = payload[:16].hex()
    model["payload_sha256"] = payload_sha256


def mutate_candidate(
    candidate: dict[str, Any],
    *,
    event_index: int,
    byte_offset: int | None,
    xor_value: int | None,
    replacement_payload: bytes | None,
    status_suffix: str,
) -> dict[str, Any]:
    events = candidate.get("events")
    if not isinstance(events, list):
        raise ValueError("candidate has no events list")

    for event in events:
        if not event_matches(event, event_index):
            continue
        model = event.get("payload_model") or {}
        if model.get("kind") != "inline_payload_hex":
            raise ValueError(f"event {event_index} payload is not inline_payload_hex")
        payload = bytearray.fromhex(compact_hex(str(model.get("payload_hex", ""))))
        if replacement_payload is not None:
            if len(replacement_payload) != len(payload):
                raise ValueError(
                    f"replacement payload has length {len(replacement_payload)}, expected {len(payload)}"
                )
            before = bytes(payload)
            payload = bytearray(replacement_payload)
            after = bytes(payload)
        else:
            if byte_offset is None or xor_value is None:
                raise ValueError("xor mutation requires byte offset and xor value")
            if not 0 <= byte_offset < len(payload):
                raise ValueError(f"byte offset {byte_offset} outside payload length {len(payload)}")
            before = payload[byte_offset]
            payload[byte_offset] ^= xor_value
            after = payload[byte_offset]
        update_payload_fields(event, bytes(payload))

        mutation = {
            "event_index": event_index,
            "kind": "replace_payload" if replacement_payload is not None else "xor_byte",
            "byte_offset": byte_offset,
            "xor": xor_value,
            "phase": event.get("phase"),
            "role": event.get("role"),
            "cdb": event.get("cdb"),
            "payload_sha256_after": event.get("payload_sha256"),
        }
        if replacement_payload is not None:
            mutation["before_hex"] = before.hex()
            mutation["after_hex"] = after.hex()
        else:
            mutation["before"] = before
            mutation["after"] = after
        candidate.setdefault("mutations", []).append(mutation)
        candidate["status"] = f"{candidate.get('status', 'candidate')}-{status_suffix}"
        candidate["event_count"] = len(events)
        return mutation

    raise ValueError(f"event {event_index} not found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--event-index", type=int, required=True)
    parser.add_argument("--byte-offset", type=lambda value: int(value, 0), default=0)
    parser.add_argument("--xor", type=parse_xor, default=0x01)
    parser.add_argument("--payload-hex", type=parse_payload_hex)
    parser.add_argument("--status-suffix", default="mutated-payload")
    args = parser.parse_args()

    if args.payload_hex is not None and ("--xor" in sys.argv or "--byte-offset" in sys.argv):
        parser.error("--payload-hex cannot be combined with --xor/--byte-offset")

    candidate = json.loads(args.input.read_text(encoding="utf-8"))
    mutation = mutate_candidate(
        candidate,
        event_index=args.event_index,
        byte_offset=None if args.payload_hex is not None else args.byte_offset,
        xor_value=None if args.payload_hex is not None else args.xor,
        replacement_payload=args.payload_hex,
        status_suffix=args.status_suffix,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(mutation, indent=2, sort_keys=True))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
