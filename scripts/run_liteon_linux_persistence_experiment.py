#!/usr/bin/env python3
"""Run a Linux LiteOn persistence experiment through sg_raw.

This runner executes an inline candidate JSON, verifies arg=00 readbacks against
the just-sent payload, captures identity and F0 before/after, and writes a
single structured result directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STANDARD_INQUIRY_CDB = [0x12, 0x00, 0x00, 0x00, 0x24, 0x00]
EXTRAINQ_CDB = [0x12, 0x00, 0x00, 0x00, 0xF0, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
FINALIZER_STATUS_READS = [
    ("id01_offset_017ff0_len40", 0x01, 0x017FF0, 0x40),
    ("id01_offset_018000_len40", 0x01, 0x018000, 0x40),
    ("id01_offset_018004_len20", 0x01, 0x018004, 0x20),
    ("id01_offset_018006_len80", 0x01, 0x018006, 0x80),
    ("id01_offset_018100_len80", 0x01, 0x018100, 0x80),
    ("id01_offset_018600_len80", 0x01, 0x018600, 0x80),
    ("id01_offset_018620_len20", 0x01, 0x018620, 0x20),
    ("id01_offset_01818a_len20", 0x01, 0x01818A, 0x20),
    ("id02_offset_018006_len80", 0x02, 0x018006, 0x80),
    ("id02_offset_018600_len80", 0x02, 0x018600, 0x80),
    ("id02_offset_018620_len20", 0x02, 0x018620, 0x20),
    ("id02_offset_01818a_len20", 0x02, 0x01818A, 0x20),
]


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def bytes_from_cdb(text: str) -> list[int]:
    return [int(part, 16) for part in text.split()]


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def ascii_field(data: bytes) -> str:
    return data.decode("ascii", errors="replace").strip()


def sysfs_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace").strip()
    except OSError:
        return ""


def list_sg_devices() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for sg_dir in sorted(Path("/sys/class/scsi_generic").glob("sg*")):
        device_dir = sg_dir / "device"
        out.append(
            {
                "sg": f"/dev/{sg_dir.name}",
                "vendor": sysfs_text(device_dir / "vendor"),
                "model": sysfs_text(device_dir / "model"),
                "rev": sysfs_text(device_dir / "rev"),
                "type": sysfs_text(device_dir / "type"),
            }
        )
    return out


def choose_device(explicit: str | None) -> str:
    if explicit:
        return explicit
    devices = list_sg_devices()
    optical = [
        item
        for item in devices
        if item.get("type") == "5"
        or "DS-8ABSH" in item.get("model", "")
        or item.get("vendor", "").strip() == "PLDS"
    ]
    if len(optical) == 1:
        return optical[0]["sg"]
    if devices:
        print("sg devices:", file=sys.stderr)
        for item in devices:
            print(
                f"  {item['sg']}: vendor={item['vendor']!r} model={item['model']!r} "
                f"rev={item['rev']!r} type={item['type']!r}",
                file=sys.stderr,
            )
    if not optical:
        raise RuntimeError("no optical / PLDS sg device found; pass --device /dev/sgX")
    raise RuntimeError("multiple optical / PLDS sg devices found; pass --device /dev/sgX")


def read_buffer_cdb(buffer_id: int, offset: int, length: int) -> list[int]:
    return [
        0x3C,
        0x01,
        buffer_id,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
        (length >> 16) & 0xFF,
        (length >> 8) & 0xFF,
        length & 0xFF,
        0x00,
    ]


def run_sg_raw(
    sg_raw: str,
    device: str,
    cdb: list[int],
    *,
    request_len: int = 0,
    payload: bytes = b"",
    timeout: int = 5,
) -> dict[str, Any]:
    cmd = [sg_raw, "--cmdset=1", "-b", "--timeout", str(timeout)]
    if request_len:
        cmd.extend(["--request", str(request_len)])
    if payload:
        cmd.extend(["--send", str(len(payload))])
    cmd.extend([device, *[f"{byte:02x}" for byte in cdb]])
    started = time.monotonic()
    proc = subprocess.run(cmd, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elapsed = time.monotonic() - started
    stdout = proc.stdout
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return {
        "cmd": cmd,
        "cdb": cdb_text(cdb),
        "request_len": request_len,
        "payload_len": len(payload),
        "payload_sha256": hashlib.sha256(payload).hexdigest() if payload else None,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "stdout_len": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest() if stdout else None,
        "stdout_first64_hex": stdout[:64].hex(),
        "stdout_hex": stdout.hex() if len(stdout) <= 0x1000 else None,
        "stderr": stderr,
        "status_good_text": "SCSI Status: Good" in stderr,
        "check_condition_text": "Check Condition" in stderr or "CHECK CONDITION" in stderr,
    }


def should_retry_f0_read(item: dict[str, Any]) -> bool:
    stderr = str(item.get("stderr") or "").lower()
    return (
        item.get("returncode") != 0
        and "not ready" in stderr
        and "becoming ready" in stderr
    )


def describe_standard(data: bytes) -> dict[str, Any]:
    return {
        "len": len(data),
        "vendor": ascii_field(data[0x08:0x10]) if len(data) >= 0x10 else "",
        "product": ascii_field(data[0x10:0x20]) if len(data) >= 0x20 else "",
        "revision": ascii_field(data[0x20:0x24]) if len(data) >= 0x24 else "",
        "sha256": hashlib.sha256(data).hexdigest() if data else None,
    }


def describe_extrainq(data: bytes) -> dict[str, Any]:
    marker = data.find(b"EXTRAINQ")
    if marker < 0:
        marker = data.find(b"LITEONIT")
    out: dict[str, Any] = {
        "len": len(data),
        "marker_found": marker >= 0,
        "marker_offset": marker if marker >= 0 else None,
        "vendor": ascii_field(data[0x08:0x10]) if len(data) >= 0x10 else "",
        "product": ascii_field(data[0x10:0x20]) if len(data) >= 0x20 else "",
        "revision": ascii_field(data[0x20:0x24]) if len(data) >= 0x24 else "",
        "timestamp": ascii_field(data[0x24:0x34]) if len(data) >= 0x34 else "",
        "sha256": hashlib.sha256(data).hexdigest() if data else None,
    }
    if marker >= 0:
        base = data[marker:]
        if len(base) >= 0x14:
            out["profile_len"] = int.from_bytes(base[0x08:0x0A], "big")
            out["profile_word"] = int.from_bytes(base[0x0A:0x0C], "big")
            out["primary_selector_value"] = (base[0x0A] + base[0x0B]) & 7
            out["feature_byte"] = base[0x10]
            out["aes_byte"] = base[0x12]
    if len(data) >= 0x80:
        key_selector = data[0x73]
        key_off = 0x74 + key_selector * 8
        out["key_selector"] = key_selector
        out["key_offset"] = key_off
        out["init_vec_hex"] = data[0x10:0x20].hex()
        out["init_vec_ascii"] = ascii_field(data[0x10:0x20])
        if key_off + 16 <= len(data):
            out["sec_key_ascii"] = ascii_field(data[key_off : key_off + 16])
            out["sec_key_hex"] = data[key_off : key_off + 16].hex()
    return out


def capture_identity(sg_raw: str, device: str, timeout: int) -> dict[str, Any]:
    standard = run_sg_raw(sg_raw, device, STANDARD_INQUIRY_CDB, request_len=36, timeout=timeout)
    extrainq = run_sg_raw(sg_raw, device, EXTRAINQ_CDB, request_len=0xF0, timeout=timeout)
    return {
        "standard_raw": standard,
        "extrainq_raw": extrainq,
        "standard": describe_standard(bytes.fromhex(standard.get("stdout_hex") or "")),
        "extrainq": describe_extrainq(bytes.fromhex(extrainq.get("stdout_hex") or "")),
    }


def candidate_finalizer_status_reads(candidate: dict[str, Any]) -> list[tuple[str, int, int, int]]:
    reads = list(FINALIZER_STATUS_READS)
    seen = {(buffer_id, offset, length) for _, buffer_id, offset, length in reads}
    mutations = []
    if isinstance(candidate.get("mutations"), list):
        mutations.extend(item for item in candidate["mutations"] if isinstance(item, dict))
    if isinstance(candidate.get("mutation"), dict):
        mutations.append(candidate["mutation"])
    for index, mutation in enumerate(mutations):
        offset = mutation.get("expected_visible_helper_host_offset")
        if offset is None:
            detail = mutation.get("mutation") or {}
            offset = detail.get("host_id01_offset_from_018000")
        if offset is None:
            continue
        start = max(0, int(offset) & ~0x0F)
        length = 0x40
        for buffer_id in (0x01, 0x02):
            key = (buffer_id, start, length)
            if key in seen:
                continue
            seen.add(key)
            reads.append(
                (
                    f"id{buffer_id:02x}_candidate{index}_offset_{start:06x}_len{length:x}",
                    buffer_id,
                    start,
                    length,
                )
            )
    return reads


def capture_finalizer_status(
    sg_raw: str,
    device: str,
    timeout: int,
    reads: list[tuple[str, int, int, int]],
) -> dict[str, Any]:
    commands: dict[str, Any] = {}
    for name, buffer_id, offset, length in reads:
        item = run_sg_raw(
            sg_raw,
            device,
            read_buffer_cdb(buffer_id, offset, length),
            request_len=length,
            timeout=timeout,
        )
        commands[name] = item
        print(
            f"finalizer-status {name}: rc={item['returncode']} "
            f"in={item['stdout_len']} first16={item['stdout_first64_hex'][:32]}",
            flush=True,
        )
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases": [
            {"name": name, "id": buffer_id, "offset": offset, "length": length}
            for name, buffer_id, offset, length in reads
        ],
        "commands": commands,
    }


def aes_decrypt_reset_window(data: bytes, key: bytes, iv: bytes, reset: int) -> bytes:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    if reset <= 0 or reset % 16:
        raise ValueError("crypto reset interval must be a positive multiple of 16")
    if len(data) % 16:
        raise ValueError("encrypted window length must be a multiple of 16")
    out = bytearray()
    for offset in range(0, len(data), reset):
        ctx = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        out.extend(ctx.update(data[offset : offset + reset]) + ctx.finalize())
    return bytes(out)


def maybe_decrypt_f0(encrypted: bytes, extrainq: bytes, *, crypto_reset: int) -> tuple[bytes | None, str | None]:
    try:
        if len(extrainq) < 0x80:
            raise ValueError("EXTRAINQ response is too short for key derivation")
        key_selector = extrainq[0x73]
        key_off = 0x74 + key_selector * 8
        key = extrainq[key_off : key_off + 16]
        if len(key) != 16:
            raise ValueError("EXTRAINQ key slice is truncated")
        iv = extrainq[0x10:0x20]
        return aes_decrypt_reset_window(encrypted, key, iv, crypto_reset), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def dump_f0(
    sg_raw: str,
    device: str,
    out_dir: Path,
    label: str,
    *,
    extrainq: bytes,
    f0_size: int,
    f0_chunk: int,
    buffer_id: int,
    crypto_reset: int,
    timeout: int,
    read_retries: int,
    read_retry_delay: float,
) -> dict[str, Any]:
    raw = bytearray()
    commands = []
    offset = 0
    while offset < f0_size:
        length = min(f0_chunk, f0_size - offset)
        item = run_sg_raw(
            sg_raw,
            device,
            read_buffer_cdb(buffer_id, offset, length),
            request_len=length,
            timeout=timeout,
        )
        retry_count = 0
        while should_retry_f0_read(item) and retry_count < read_retries:
            retry_count += 1
            print(
                f"{label}: offset=0x{offset:06x} transient not-ready; "
                f"retry {retry_count}/{read_retries}",
                flush=True,
            )
            time.sleep(read_retry_delay)
            item = run_sg_raw(
                sg_raw,
                device,
                read_buffer_cdb(buffer_id, offset, length),
                request_len=length,
                timeout=timeout,
            )
        if retry_count:
            item["retry_count"] = retry_count
        commands.append(item)
        if item["returncode"] != 0:
            raise RuntimeError(f"{label} F0 read failed at 0x{offset:06x}: {item['stderr'].strip()}")
        if item["stdout_len"] != length:
            raise RuntimeError(f"{label} F0 read at 0x{offset:06x} returned {item['stdout_len']} != {length}")
        raw.extend(bytes.fromhex(item["stdout_hex"] or ""))
        done = offset + length
        progress_interval = max(0x10000, f0_chunk)
        if offset == 0 or done == f0_size or done % progress_interval == 0:
            print(f"{label}: offset=0x{offset:06x} done={done}/{f0_size}", flush=True)
        offset += length

    raw_bytes = bytes(raw)
    raw_path = out_dir / f"{label}-f0-read-buffer-raw.bin"
    raw_path.write_bytes(raw_bytes)
    report: dict[str, Any] = {
        "label": label,
        "buffer_id": buffer_id,
        "size": f0_size,
        "chunk": f0_chunk,
        "raw_path": str(raw_path),
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "commands": commands,
    }
    decrypted, error = maybe_decrypt_f0(raw_bytes, extrainq, crypto_reset=crypto_reset)
    if decrypted is None:
        report["decrypt_error"] = error
    else:
        dec_path = out_dir / f"{label}-f0-read-buffer-decrypted.bin"
        dec_path.write_bytes(decrypted)
        report["decrypted_path"] = str(dec_path)
        report["decrypted_sha256"] = hashlib.sha256(decrypted).hexdigest()
    return report


def payload_for_event(event: dict[str, Any]) -> bytes:
    model = event.get("payload_model") or {}
    if model.get("kind") == "inline_payload_hex":
        return bytes.fromhex(compact_hex(model.get("payload_hex", "")))
    return b""


def phase_timeout(phase: str, args: argparse.Namespace, payload_len: int) -> int:
    if phase == "bank_pmac_prefix":
        return args.pmac_timeout
    if phase in {"profile_tail_arg7f", "arg00_chunk_transfer"} or payload_len:
        return args.write_timeout
    return args.timeout


def execute_events(args: argparse.Namespace, events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    attempted = []
    expected_readback: bytes | None = None
    for event in events:
        payload = payload_for_event(event)
        request_len = int(event.get("data_in_len") or 0)
        data_out_len = int(event.get("data_out_len") or 0)
        if len(payload) != data_out_len:
            raise ValueError(f"event {event['event_index']} payload len {len(payload)} != {data_out_len}")
        if payload and request_len:
            raise ValueError(f"event {event['event_index']} is bidirectional")
        item = run_sg_raw(
            args.sg_raw,
            args.device,
            bytes_from_cdb(event["cdb"]),
            request_len=request_len,
            payload=payload,
            timeout=phase_timeout(str(event.get("phase")), args, len(payload)),
        )
        item["event_index"] = event["event_index"]
        item["phase"] = event["phase"]
        item["role"] = event.get("role")
        if event["phase"] == "arg00_chunk_transfer" and item["returncode"] == 0:
            expected_readback = payload
        elif event["phase"] == "arg00_readback_verify" and item["returncode"] == 0:
            data = bytes.fromhex(item.get("stdout_hex") or "")
            expected_sha = (event.get("payload_model") or {}).get("transport_sha256")
            item["readback_matches_previous_chunk"] = expected_readback is not None and data == expected_readback
            item["readback_matches_transport_sha256"] = (
                expected_sha is not None and hashlib.sha256(data).hexdigest() == expected_sha
            )
            if not item["readback_matches_previous_chunk"]:
                item["returncode"] = item["returncode"] or 99
                item["stderr"] += "\nreadback did not match previous chunk"
            expected_readback = None
        attempted.append(item)
        print(
            f"event={event['event_index']} phase={event['phase']} rc={item['returncode']} "
            f"out={len(payload)} in={item['stdout_len']}",
            flush=True,
        )
        if args.capture_finalizer_status_after_event == int(event["event_index"]):
            item["finalizer_status_after_event"] = capture_finalizer_status(
                args.sg_raw,
                args.device,
                args.timeout,
                args.finalizer_status_reads,
            )
        if args.delay_ms:
            time.sleep(args.delay_ms / 1000)
        if item["returncode"] != 0 and not args.continue_after_failure:
            return attempted, item
    return attempted, None


def run_recovery(args: argparse.Namespace, out_dir: Path) -> dict[str, Any]:
    recovery_script = ROOT / "scripts/recover_liteon_currentboot_linux.py"
    cmd = [
        sys.executable,
        str(recovery_script),
        "--device",
        args.device,
        "--out-dir",
        str(out_dir / "auto-recovery"),
        "--timeout",
        str(args.timeout),
        "--write-timeout",
        str(args.write_timeout),
        "--pmac-timeout",
        str(args.pmac_timeout),
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def expected_final_revision(candidate: dict[str, Any], cli_value: str | None) -> str:
    if cli_value:
        return cli_value
    parameters = candidate.get("parameters") or {}
    return str(parameters.get("expected_final_revision") or "LD5M")


def expected_sha_for_size(expected: dict[str, Any], key: str, size: int | None) -> str | None:
    by_size = expected.get(f"{key}_by_size")
    if isinstance(by_size, dict) and size is not None:
        return by_size.get(f"0x{size:x}") or by_size.get(str(size))
    if size in {None, 0x100000}:
        value = expected.get(key)
        return str(value) if value else None
    return None


def should_recover_after_run(
    *,
    recover_on_currentboot: bool,
    final_revision: str | None,
    baseline_revision: str,
    expected_revision: str,
) -> bool:
    if not recover_on_currentboot:
        return False
    if not final_revision:
        return True
    # A successful official-image probe may legitimately report AD12/AHS9/etc.
    # Do not immediately overwrite that evidence with the LD5M recovery path.
    if final_revision in {baseline_revision, expected_revision}:
        return False
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--device")
    parser.add_argument("--sg-raw", default=shutil.which("sg_raw") or "sg_raw")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "logs/linux-persistence-experiments")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--write-timeout", type=int, default=30)
    parser.add_argument("--pmac-timeout", type=int, default=180)
    parser.add_argument("--delay-ms", type=int, default=0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int)
    parser.add_argument("--continue-after-failure", action="store_true")
    parser.add_argument("--preflight-revision", default="LD5M")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--skip-pre-f0", action="store_true")
    parser.add_argument("--skip-post-f0", action="store_true")
    parser.add_argument("--f0-size", type=lambda value: int(value, 0), default=0x100000)
    parser.add_argument("--f0-chunk", type=lambda value: int(value, 0), default=0x80)
    parser.add_argument("--currentboot-f0-size", type=lambda value: int(value, 0), default=0x30000)
    parser.add_argument("--currentboot-f0-chunk", type=lambda value: int(value, 0), default=0x80)
    parser.add_argument("--buffer-id", type=lambda value: int(value, 0), default=0xF0)
    parser.add_argument("--crypto-reset", type=lambda value: int(value, 0), default=0x80)
    parser.add_argument("--recover-on-currentboot", action="store_true")
    parser.add_argument("--f0-read-retries", type=int, default=8)
    parser.add_argument("--f0-read-retry-delay", type=float, default=2.0)
    parser.add_argument(
        "--expected-final-revision",
        help="override candidate metadata when deciding whether the final revision is expected",
    )
    parser.add_argument(
        "--recovery-baseline-revision",
        default="LD5M",
        help="normal baseline revision; --recover-on-currentboot will not recover this revision",
    )
    parser.add_argument(
        "--capture-finalizer-status",
        action="store_true",
        help="capture corrected id01/id02 READ BUFFER 0x018xxx windows immediately after replay stops",
    )
    parser.add_argument(
        "--capture-finalizer-status-after-event",
        type=int,
        default=-1,
        metavar="INDEX",
        help="capture corrected id01/id02 READ BUFFER 0x018xxx windows immediately after one event",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not shutil.which(args.sg_raw):
        raise RuntimeError(f"sg_raw not found: {args.sg_raw}")
    args.device = choose_device(args.device)
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    args.finalizer_status_reads = candidate_finalizer_status_reads(candidate)
    expected_revision = expected_final_revision(candidate, args.expected_final_revision)
    events = list(candidate["events"])
    if args.end_index is not None:
        events = [event for event in events if args.start_index <= int(event["event_index"]) <= args.end_index]
    else:
        events = [event for event in events if int(event["event_index"]) >= args.start_index]

    run_id = datetime.now(timezone.utc).strftime("liteon-persistence-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "persistence-experiment-result.json"
    result: dict[str, Any] = {
        "run_id": run_id,
        "candidate": str(args.candidate),
        "candidate_status": candidate.get("status"),
        "device": args.device,
        "sg_devices": list_sg_devices(),
        "start_index": args.start_index,
        "end_index": args.end_index,
        "expected_hashes": candidate.get("expected_hashes_for_live_execution"),
        "expected_final_revision": expected_revision,
        "recovery_baseline_revision": args.recovery_baseline_revision,
        "events_attempted": [],
        "stopped_on_failure": None,
        "success": False,
    }

    try:
        result["identity_before"] = capture_identity(args.sg_raw, args.device, args.timeout)
        before_rev = result["identity_before"]["standard"].get("revision")
        if before_rev != args.preflight_revision and not args.force:
            raise RuntimeError(
                f"preflight revision is {before_rev!r}, expected {args.preflight_revision!r}; use --force to run"
            )
        before_extrainq = bytes.fromhex(result["identity_before"]["extrainq_raw"].get("stdout_hex") or "")
        if not args.skip_pre_f0:
            result["pre_f0"] = dump_f0(
                args.sg_raw,
                args.device,
                out_dir,
                "pre",
                extrainq=before_extrainq,
                f0_size=args.f0_size,
                f0_chunk=args.f0_chunk,
                buffer_id=args.buffer_id,
                crypto_reset=args.crypto_reset,
                timeout=args.timeout,
                read_retries=args.f0_read_retries,
                read_retry_delay=args.f0_read_retry_delay,
            )

        attempted, failure = execute_events(args, events)
        result["events_attempted"] = attempted
        result["stopped_on_failure"] = failure
        if args.capture_finalizer_status:
            result["finalizer_status_after_sequence_before_identity"] = capture_finalizer_status(
                args.sg_raw,
                args.device,
                args.timeout,
                args.finalizer_status_reads,
            )
        result["identity_after_sequence"] = capture_identity(args.sg_raw, args.device, args.timeout)
        final_rev = result["identity_after_sequence"]["standard"].get("revision")
        result["final_revision_after_sequence"] = final_rev
        after_extrainq = bytes.fromhex(result["identity_after_sequence"]["extrainq_raw"].get("stdout_hex") or "")

        if not args.skip_post_f0:
            if final_rev == "LD5M":
                post_size = args.f0_size
                post_chunk = args.f0_chunk
                post_label = "post"
            else:
                post_size = args.currentboot_f0_size
                post_chunk = args.currentboot_f0_chunk
                post_label = "post-currentboot"
            result["post_f0"] = dump_f0(
                args.sg_raw,
                args.device,
                out_dir,
                post_label,
                extrainq=after_extrainq,
                f0_size=post_size,
                f0_chunk=post_chunk,
                buffer_id=args.buffer_id,
                crypto_reset=args.crypto_reset,
                timeout=args.timeout,
                read_retries=args.f0_read_retries,
                read_retry_delay=args.f0_read_retry_delay,
            )

        expected = candidate.get("expected_hashes_for_live_execution") or {}
        pre_sha = (result.get("pre_f0") or {}).get("decrypted_sha256")
        post_sha = (result.get("post_f0") or {}).get("decrypted_sha256")
        pre_size = (result.get("pre_f0") or {}).get("size")
        post_size = (result.get("post_f0") or {}).get("size")
        expect_pre_sha = expected_sha_for_size(expected, "expect_pre_sha256", pre_size)
        expect_post_sha = expected_sha_for_size(expected, "expect_post_sha256", post_size)
        result["hash_comparison"] = {
            "pre_matches_expected": bool(pre_sha and expect_pre_sha and pre_sha == expect_pre_sha),
            "post_matches_expected_target": bool(post_sha and expect_post_sha and post_sha == expect_post_sha),
            "post_matches_expected_pre": bool(post_sha and expect_pre_sha and post_sha == expect_pre_sha),
            "expected_pre_sha256_for_size": expect_pre_sha,
            "expected_post_sha256_for_size": expect_post_sha,
            "pre_decrypted_sha256": pre_sha,
            "post_decrypted_sha256": post_sha,
            "pre_size": pre_size,
            "post_size": post_size,
        }
        post_matches_target = bool(result["hash_comparison"]["post_matches_expected_target"])
        result["success"] = (
            failure is None
            and (
                post_matches_target
                or (
                    not result.get("post_f0")
                    and final_rev == expected_revision
                )
            )
        )

        if should_recover_after_run(
            recover_on_currentboot=args.recover_on_currentboot,
            final_revision=final_rev,
            baseline_revision=args.recovery_baseline_revision,
            expected_revision=expected_revision,
        ):
            result["auto_recovery"] = run_recovery(args, out_dir)
            result["identity_after_auto_recovery"] = capture_identity(args.sg_raw, args.device, args.timeout)
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
        try:
            result["identity_after_error"] = capture_identity(args.sg_raw, args.device, args.timeout)
            after_error_rev = result["identity_after_error"]["standard"].get("revision")
            if should_recover_after_run(
                recover_on_currentboot=args.recover_on_currentboot,
                final_revision=after_error_rev,
                baseline_revision=args.recovery_baseline_revision,
                expected_revision=expected_revision,
            ):
                result["auto_recovery"] = run_recovery(args, out_dir)
                result["identity_after_auto_recovery"] = capture_identity(args.sg_raw, args.device, args.timeout)
        except Exception as identity_exc:  # noqa: BLE001
            result["identity_after_error_failed"] = f"{type(identity_exc).__name__}: {identity_exc}"

    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {result_path}")
    print(f"success={int(result.get('success', False))}")
    if result.get("final_revision_after_sequence"):
        print(f"final_revision_after_sequence={result['final_revision_after_sequence']}")
    if result.get("hash_comparison"):
        print(json.dumps(result["hash_comparison"], indent=2, sort_keys=True))
    if result.get("error"):
        print(f"error={result['error']}", file=sys.stderr)
        return 1
    if result.get("stopped_on_failure"):
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
