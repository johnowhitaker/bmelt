#!/usr/bin/env python3
"""Flip a safe volatile MODE SELECT bit and observe normal-mode responses.

This is a small reproducibility wrapper around `normal_mailbox_probe.py`.
It does not touch firmware, CDD, updater commands, flash, tray mechanics, or
media writes. The default observer is the read-only MMC/CSS RPC-state command:

    REPORT KEY key class 0, key format 8

The default writable bit is the Drive #3 proven volatile caching-page bit:

    MODE SENSE/SELECT(10) page 0x08, page byte 0x02, mask 0x04

The script records before/mutated/restored command responses and optional
normal public work-window captures.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import normal_mailbox_probe as nm  # noqa: E402


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def observer_command(name: str) -> nm.Command:
    if name == "report-key-rpc-state":
        return nm.Command(
            "report-key-css-rpc-state",
            nm.report_key_cdb(key_class=0, key_format=8, allocation_length=8, agid=0),
            request_len=8,
            notes="REPORT KEY key class 0 / key format 8: read-only RPC state",
        )
    if name == "inquiry":
        return nm.inquiry_command()
    if name == "get-config":
        return nm.get_config_command()
    if name == "mode-sense-read-error":
        return nm.mode_sense_read_error_command()
    raise ValueError(f"unknown observer: {name}")


def save(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    report: dict[str, Any],
    index: int,
    command: nm.Command,
    role: str,
) -> tuple[int, dict[str, Any], bytes]:
    record = nm.save_command_result(args=args, out_dir=out_dir, index=index, command=command)
    data = Path(record["response_path"]).read_bytes()
    record["role"] = role
    report["steps"].append(record)
    print(
        f"{index:02d} {role} {command.name} "
        f"good={record.get('good')} len={record.get('length')} "
        f"sha={str(record.get('sha256'))[:12]}",
        flush=True,
    )
    return index + 1, record, data


def capture(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    report: dict[str, Any],
    index: int,
    name: str,
) -> int:
    if not args.capture_window:
        return index
    window = nm.capture_work_window(args=args, out_dir=out_dir, index=index, name=name)
    window["role"] = name
    report["windows"].append(window)
    print(f"{index:02d} {name} window sha={window['sha256'][:12]}", flush=True)
    return index + 1


def run(args: argparse.Namespace) -> int:
    run_id = datetime.now(timezone.utc).strftime("normal-mode-bit-observer-%Y%m%dT%H%M%S%fZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "probe": "mode-bit-observer",
        "notes": (
            "Flip one advertised-changeable volatile MODE SELECT bit, observe a "
            "normal command response, then restore the bit immediately."
        ),
        "observer": args.observer,
        "page": args.page,
        "page_byte": args.page_byte,
        "xor_mask": args.xor_mask,
        "execute": args.execute,
        "capture_window": args.capture_window,
        "steps": [],
        "windows": [],
    }

    idx = 0
    idx, identity_before, identity_data = save(
        args=args,
        out_dir=out_dir,
        report=report,
        index=idx,
        command=nm.inquiry_command(),
        role="identity-before",
    )
    report["identity_before"] = nm.identity_summary(identity_data)

    current_cmd = nm.Command(
        f"mode-sense10-current-page0x{args.page:02x}",
        nm.mode_sense10_cdb(args.page, 0x00, args.alloc_len),
        request_len=args.alloc_len,
    )
    changeable_cmd = nm.Command(
        f"mode-sense10-changeable-page0x{args.page:02x}",
        nm.mode_sense10_cdb(args.page, 0x40, args.alloc_len),
        request_len=args.alloc_len,
    )
    idx, current_record, current_data = save(
        args=args,
        out_dir=out_dir,
        report=report,
        index=idx,
        command=current_cmd,
        role="mode-current-before",
    )
    idx, changeable_record, changeable_data = save(
        args=args,
        out_dir=out_dir,
        report=report,
        index=idx,
        command=changeable_cmd,
        role="mode-changeable",
    )

    page_offset = args.page_offset
    target_offset = page_offset + args.page_byte
    error = None
    if not current_record.get("good") or not changeable_record.get("good"):
        error = "current/changeable MODE SENSE did not both complete"
    elif target_offset >= len(current_data) or target_offset >= len(changeable_data):
        error = f"target page byte 0x{args.page_byte:x} outside response"
    elif current_data[page_offset] != args.page or changeable_data[page_offset] != args.page:
        error = "response page code did not match requested page"
    elif (changeable_data[target_offset] & args.xor_mask) != args.xor_mask:
        error = (
            f"target mask 0x{args.xor_mask:02x} is not advertised changeable "
            f"(changeable byte=0x{changeable_data[target_offset]:02x})"
        )

    if error:
        report["error"] = error
        print(f"error: {error}", flush=True)
    else:
        old_byte = current_data[target_offset]
        new_byte = old_byte ^ args.xor_mask
        report["target"] = {
            "absolute_response_offset": target_offset,
            "old_byte": old_byte,
            "new_byte": new_byte,
            "changeable_byte": changeable_data[target_offset],
        }

        obs = observer_command(args.observer)
        idx, before_obs, before_obs_data = save(
            args=args,
            out_dir=out_dir,
            report=report,
            index=idx,
            command=obs,
            role="observer-before",
        )
        idx = capture(args=args, out_dir=out_dir, report=report, index=idx, name="window-before")

        mutated = bytearray(current_data)
        restored = bytearray(current_data)
        mutated[0] = mutated[1] = 0
        restored[0] = restored[1] = 0
        mutated[target_offset] = new_byte

        if not args.execute:
            report["dry_run_mutated_payload_hex"] = bytes(mutated).hex()
            print(
                f"dry-run target response_offset=0x{target_offset:02x} "
                f"old=0x{old_byte:02x} new=0x{new_byte:02x}",
                flush=True,
            )
        else:
            idx, _, _ = save(
                args=args,
                out_dir=out_dir,
                report=report,
                index=idx,
                command=nm.Command(
                    f"mode-select10-page0x{args.page:02x}-mutated",
                    nm.mode_select10_cdb(len(mutated)),
                    payload=bytes(mutated),
                    notes="MODE SELECT(10) PF=1 SP=0 mutated current page",
                ),
                role="mode-select-mutated",
            )
            idx, after_mutated, after_mutated_data = save(
                args=args,
                out_dir=out_dir,
                report=report,
                index=idx,
                command=current_cmd,
                role="mode-current-after-mutated",
            )
            report["after_mutated_target_byte"] = (
                after_mutated_data[target_offset] if len(after_mutated_data) > target_offset else None
            )
            idx, mutated_obs, mutated_obs_data = save(
                args=args,
                out_dir=out_dir,
                report=report,
                index=idx,
                command=obs,
                role="observer-mutated",
            )
            idx = capture(args=args, out_dir=out_dir, report=report, index=idx, name="window-mutated")

            idx, _, _ = save(
                args=args,
                out_dir=out_dir,
                report=report,
                index=idx,
                command=nm.Command(
                    f"mode-select10-page0x{args.page:02x}-restore",
                    nm.mode_select10_cdb(len(restored)),
                    payload=bytes(restored),
                    notes="MODE SELECT(10) PF=1 SP=0 restore original current page",
                ),
                role="mode-select-restore",
            )
            idx, after_restore, after_restore_data = save(
                args=args,
                out_dir=out_dir,
                report=report,
                index=idx,
                command=current_cmd,
                role="mode-current-after-restore",
            )
            report["after_restore_target_byte"] = (
                after_restore_data[target_offset] if len(after_restore_data) > target_offset else None
            )
            idx, restored_obs, restored_obs_data = save(
                args=args,
                out_dir=out_dir,
                report=report,
                index=idx,
                command=obs,
                role="observer-restored",
            )
            idx = capture(args=args, out_dir=out_dir, report=report, index=idx, name="window-restored")

            report["roundtrip_observed"] = (
                report["after_mutated_target_byte"] == new_byte
                and report["after_restore_target_byte"] == old_byte
            )
            report["observer_response_changed_when_mutated"] = before_obs_data != mutated_obs_data
            report["observer_response_restored"] = before_obs_data == restored_obs_data

    idx, identity_after, identity_after_data = save(
        args=args,
        out_dir=out_dir,
        report=report,
        index=idx,
        command=nm.inquiry_command(),
        role="identity-after",
    )
    report["identity_after"] = nm.identity_summary(identity_after_data)
    report["identity_stable"] = report["identity_before"] == report["identity_after"]

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        f"wrote {summary_path} identity_stable={report['identity_stable']} "
        f"roundtrip={report.get('roundtrip_observed')} "
        f"observer_changed={report.get('observer_response_changed_when_mutated')}",
        flush=True,
    )
    return 0 if report["identity_stable"] and not report.get("error") else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=nm.DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "references/evidence/live")
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)
    parser.add_argument("--page", type=parse_int, default=0x08)
    parser.add_argument("--page-byte", type=parse_int, default=0x02)
    parser.add_argument("--page-offset", type=parse_int, default=8)
    parser.add_argument("--xor-mask", type=parse_int, default=0x04)
    parser.add_argument("--alloc-len", type=parse_int, default=0xFC)
    parser.add_argument(
        "--observer",
        choices=("report-key-rpc-state", "inquiry", "get-config", "mode-sense-read-error"),
        default="report-key-rpc-state",
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--capture-window", action="store_true")
    parser.add_argument("--window-mode", type=parse_int, default=0x01)
    parser.add_argument("--window-id", type=parse_int, default=0x01)
    parser.add_argument("--window-offset", type=parse_int, default=0x070000)
    parser.add_argument("--window-length", type=parse_int, default=0x4000)
    parser.add_argument("--window-chunk-size", type=parse_int, default=0x400)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
