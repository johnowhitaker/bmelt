#!/usr/bin/env python3
"""Probe low-risk normal-mode host I/O mailboxes on LiteOn/PLDS drives.

This tool is intentionally separate from the firmware-update helpers. It sends
only normal-mode SCSI/MMC commands by default and records exact CDBs, data-out
payloads, responses, sense/status text, hashes, and optional public work-window
snapshots.

The first implemented probe is the standard SCSI echo-buffer pair:

    READ BUFFER  mode=0x0b id=0 len=4       (descriptor)
    WRITE BUFFER mode=0x0a id=0 payload=P   (echo data)
    READ BUFFER  mode=0x0a id=0 len=len(P)  (echo readback)

No firmware download, save, deferred microcode, CDD, tray, or media-write modes
are used by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SG_RAW = shutil.which("sg_raw") or "/usr/bin/sg_raw"


@dataclass(frozen=True)
class Command:
    name: str
    cdb: tuple[int, ...]
    request_len: int = 0
    payload: bytes = b""
    notes: str = ""


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def parse_byte(value: str) -> int:
    parsed = parse_int(value)
    if not 0 <= parsed <= 0xFF:
        raise argparse.ArgumentTypeError("value must be 0..0xff")
    return parsed


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def parse_hex_bytes(text: str) -> bytes:
    compact = compact_hex(text)
    if len(compact) % 2:
        raise argparse.ArgumentTypeError("hex string must contain whole bytes")
    return bytes.fromhex(compact)


def cdb_text(cdb: tuple[int, ...] | list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ascii_preview(data: bytes, limit: int = 96) -> str:
    return "".join(chr(byte) if 0x20 <= byte < 0x7F else "." for byte in data[:limit])


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    if not needle:
        return offsets
    while True:
        offset = data.find(needle, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def payload_hits(data: bytes, payload: bytes) -> dict[str, Any]:
    if not payload:
        return {}
    fragments: list[dict[str, Any]] = []
    for size in sorted({4, 8, 16, len(payload)}):
        if size > len(payload):
            continue
        seen: set[bytes] = set()
        for start in range(0, len(payload) - size + 1):
            frag = payload[start : start + size]
            if frag in seen:
                continue
            seen.add(frag)
            offsets = find_all(data, frag)
            if offsets:
                fragments.append(
                    {
                        "payload_offset": start,
                        "length": size,
                        "hex": frag.hex(),
                        "count": len(offsets),
                        "offsets": offsets[:32],
                    }
                )
    return {
        "exact_offsets": find_all(data, payload),
        "fragments": fragments[:128],
    }


def sense_summary(data: bytes) -> dict[str, Any] | None:
    if len(data) < 3:
        return None
    response_code = data[0] & 0x7F
    if response_code in {0x70, 0x71}:
        sense_key = data[2] & 0x0F
        asc = data[12] if len(data) > 12 else None
        ascq = data[13] if len(data) > 13 else None
        return {
            "format": "fixed",
            "response_code": response_code,
            "sense_key": sense_key,
            "asc": asc,
            "ascq": ascq,
            "key_asc_ascq": None
            if asc is None or ascq is None
            else f"{sense_key:02x}/{asc:02x}/{ascq:02x}",
        }
    if response_code in {0x72, 0x73}:
        sense_key = data[1] & 0x0F if len(data) > 1 else None
        asc = data[2] if len(data) > 2 else None
        ascq = data[3] if len(data) > 3 else None
        return {
            "format": "descriptor",
            "response_code": response_code,
            "sense_key": sense_key,
            "asc": asc,
            "ascq": ascq,
            "key_asc_ascq": None
            if sense_key is None or asc is None or ascq is None
            else f"{sense_key:02x}/{asc:02x}/{ascq:02x}",
        }
    return {"format": "unknown", "response_code": response_code}


def compact_response(data: bytes) -> dict[str, Any]:
    return {
        "length": len(data),
        "sha256": sha256_hex(data) if data else None,
        "prefix_hex": data[:128].hex(),
        "ascii_preview": ascii_preview(data),
        "sense": sense_summary(data),
    }


def read_buffer_cdb(mode: int, buffer_id: int, offset: int, length: int) -> tuple[int, ...]:
    if not 0 <= mode <= 0x1F:
        raise ValueError(f"READ BUFFER mode out of range: 0x{mode:x}")
    if not 0 <= buffer_id <= 0xFF:
        raise ValueError(f"READ BUFFER id out of range: 0x{buffer_id:x}")
    if not 0 <= offset <= 0xFFFFFF:
        raise ValueError(f"READ BUFFER offset out of range: 0x{offset:x}")
    if not 0 <= length <= 0xFFFFFF:
        raise ValueError(f"READ BUFFER length out of range: 0x{length:x}")
    return (
        0x3C,
        mode & 0x1F,
        buffer_id,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
        (length >> 16) & 0xFF,
        (length >> 8) & 0xFF,
        length & 0xFF,
        0x00,
    )


def write_buffer_echo_cdb(buffer_id: int, offset: int, payload_len: int) -> tuple[int, ...]:
    if not 0 <= buffer_id <= 0xFF:
        raise ValueError(f"WRITE BUFFER id out of range: 0x{buffer_id:x}")
    if not 0 <= offset <= 0xFFFFFF:
        raise ValueError(f"WRITE BUFFER offset out of range: 0x{offset:x}")
    if not 0 <= payload_len <= 0xFFFFFF:
        raise ValueError(f"WRITE BUFFER payload length out of range: 0x{payload_len:x}")
    return (
        0x3B,
        0x0A,
        buffer_id,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
        (payload_len >> 16) & 0xFF,
        (payload_len >> 8) & 0xFF,
        payload_len & 0xFF,
        0x00,
    )


def report_key_cdb(
    *,
    key_class: int,
    key_format: int,
    allocation_length: int,
    agid: int = 0,
    lba_or_offset: int = 0,
    block_count_function: int = 0,
) -> tuple[int, ...]:
    if not 0 <= key_class <= 0xFF:
        raise ValueError(f"key class out of range: 0x{key_class:x}")
    if not 0 <= key_format <= 0x3F:
        raise ValueError(f"key format out of range: 0x{key_format:x}")
    if not 0 <= allocation_length <= 0xFFFF:
        raise ValueError(f"allocation length out of range: 0x{allocation_length:x}")
    if not 0 <= agid <= 0x03:
        raise ValueError(f"AGID out of range: {agid}")
    if not 0 <= lba_or_offset <= 0xFFFFFFFF:
        raise ValueError(f"LBA/offset out of range: 0x{lba_or_offset:x}")
    return (
        0xA4,
        0x00,
        (lba_or_offset >> 24) & 0xFF,
        (lba_or_offset >> 16) & 0xFF,
        (lba_or_offset >> 8) & 0xFF,
        lba_or_offset & 0xFF,
        block_count_function & 0xFF,
        key_class,
        (allocation_length >> 8) & 0xFF,
        allocation_length & 0xFF,
        ((agid & 0x03) << 6) | (key_format & 0x3F),
        0x00,
    )


def send_key_cdb(
    *,
    key_class: int,
    key_format: int,
    parameter_list_length: int,
    agid: int = 0,
    function: int = 0,
) -> tuple[int, ...]:
    if not 0 <= key_class <= 0xFF:
        raise ValueError(f"key class out of range: 0x{key_class:x}")
    if not 0 <= key_format <= 0x3F:
        raise ValueError(f"key format out of range: 0x{key_format:x}")
    if not 0 <= parameter_list_length <= 0xFFFF:
        raise ValueError(f"parameter list length out of range: 0x{parameter_list_length:x}")
    if not 0 <= agid <= 0x03:
        raise ValueError(f"AGID out of range: {agid}")
    return (
        0xA3,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        function & 0xFF,
        key_class,
        (parameter_list_length >> 8) & 0xFF,
        parameter_list_length & 0xFF,
        ((agid & 0x03) << 6) | (key_format & 0x3F),
        0x00,
    )


def inquiry_command() -> Command:
    return Command("inquiry-standard-36", (0x12, 0, 0, 0, 0x24, 0), request_len=0x24)


def request_sense_command() -> Command:
    return Command("request-sense", (0x03, 0, 0, 0, 0xFC, 0), request_len=0xFC)


def get_config_command() -> Command:
    return Command(
        "get-configuration-current",
        (0x46, 0x02, 0, 0, 0, 0, 0, 0, 0xFC, 0),
        request_len=0xFC,
    )


def mode_sense_read_error_command() -> Command:
    return Command(
        "mode-sense10-read-error",
        (0x5A, 0, 0x01, 0, 0, 0, 0, 0, 0xFC, 0),
        request_len=0xFC,
    )


def mode_sense10_cdb(page: int, pc_bits: int, alloc_len: int) -> tuple[int, ...]:
    return (
        0x5A,
        0x00,
        (pc_bits & 0xC0) | (page & 0x3F),
        0x00,
        0x00,
        0x00,
        0x00,
        (alloc_len >> 8) & 0xFF,
        alloc_len & 0xFF,
        0x00,
    )


def mode_select10_cdb(parameter_list_length: int) -> tuple[int, ...]:
    if not 0 <= parameter_list_length <= 0xFFFF:
        raise ValueError(f"MODE SELECT parameter length out of range: 0x{parameter_list_length:x}")
    # PF=1, SP=0. This asks for current volatile values only, not saved pages.
    return (
        0x55,
        0x10,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        (parameter_list_length >> 8) & 0xFF,
        parameter_list_length & 0xFF,
        0x00,
    )


def run_sg_raw(
    *,
    sg_raw: str,
    device: str,
    command: Command,
    timeout: int,
    process_timeout: float,
) -> tuple[bytes, dict[str, Any]]:
    cmd = [sg_raw, "--cmdset=1", "-b", "--timeout", str(timeout)]
    if command.request_len:
        cmd.extend(["--request", str(command.request_len)])
    if command.payload:
        cmd.extend(["--send", str(len(command.payload))])
    cmd.extend([device, *[f"{byte:02x}" for byte in command.cdb]])

    started = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            input=command.payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=process_timeout,
            check=False,
        )
        elapsed = time.monotonic() - started
        stdout = proc.stdout
        stderr = proc.stderr.decode("utf-8", "replace")
        return stdout, {
            "name": command.name,
            "notes": command.notes,
            "cmd": cmd,
            "cdb": cdb_text(command.cdb),
            "request_len": command.request_len,
            "payload_len": len(command.payload),
            "payload_sha256": sha256_hex(command.payload) if command.payload else None,
            "returncode": proc.returncode,
            "timed_out": False,
            "elapsed_s": round(elapsed, 6),
            "stdout_len": len(stdout),
            "stdout_sha256": sha256_hex(stdout) if stdout else None,
            "stdout_prefix_hex": stdout[:128].hex(),
            "stderr": stderr,
            "good": proc.returncode == 0 and "SCSI Status: Good" in stderr,
        }
    except subprocess.TimeoutExpired as exc:
        elapsed = time.monotonic() - started
        stdout = exc.stdout or b""
        stderr = (
            exc.stderr.decode("utf-8", "replace")
            if isinstance(exc.stderr, bytes)
            else str(exc.stderr or "")
        )
        return stdout, {
            "name": command.name,
            "notes": command.notes,
            "cmd": cmd,
            "cdb": cdb_text(command.cdb),
            "request_len": command.request_len,
            "payload_len": len(command.payload),
            "payload_sha256": sha256_hex(command.payload) if command.payload else None,
            "returncode": None,
            "timed_out": True,
            "elapsed_s": round(elapsed, 6),
            "stdout_len": len(stdout),
            "stdout_sha256": sha256_hex(stdout) if stdout else None,
            "stdout_prefix_hex": stdout[:128].hex(),
            "stderr": stderr,
            "good": False,
        }


def save_command_result(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    index: int,
    command: Command,
    payload_for_hits: bytes = b"",
) -> dict[str, Any]:
    data, record = run_sg_raw(
        sg_raw=args.sg_raw,
        device=args.device,
        command=command,
        timeout=args.timeout,
        process_timeout=args.process_timeout,
    )
    prefix = f"{index:02d}-{command.name}"
    if command.payload:
        payload_path = out_dir / f"{prefix}.payload.bin"
        payload_path.write_bytes(command.payload)
        record["payload_path"] = str(payload_path)
    response_path = out_dir / f"{prefix}.response.bin"
    response_path.write_bytes(data)
    record |= compact_response(data)
    record["response_path"] = str(response_path)
    if payload_for_hits:
        record["payload_hits"] = payload_hits(data, payload_for_hits)
    return record


def capture_work_window(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    index: int,
    name: str,
    payload: bytes = b"",
) -> dict[str, Any]:
    data = bytearray()
    records: list[dict[str, Any]] = []
    remaining = args.window_length
    offset = args.window_offset
    while remaining:
        chunk_len = min(args.window_chunk_size, remaining)
        command = Command(
            name=f"{name}-window-chunk-0x{offset:06x}",
            cdb=read_buffer_cdb(args.window_mode, args.window_id, offset, chunk_len),
            request_len=chunk_len,
        )
        chunk, record = run_sg_raw(
            sg_raw=args.sg_raw,
            device=args.device,
            command=command,
            timeout=args.timeout,
            process_timeout=args.process_timeout,
        )
        records.append(record)
        if record.get("returncode") != 0 or record.get("timed_out") or len(chunk) != chunk_len:
            raise RuntimeError(
                f"work-window read failed at 0x{offset:06x}: rc={record.get('returncode')} "
                f"timeout={record.get('timed_out')} got={len(chunk)} expected={chunk_len}"
            )
        data.extend(chunk)
        offset += chunk_len
        remaining -= chunk_len

    blob = bytes(data)
    path = out_dir / f"{index:02d}-{name}.work-window.bin"
    path.write_bytes(blob)
    report = {
        "name": name,
        "path": str(path),
        "mode": args.window_mode,
        "id": args.window_id,
        "offset": args.window_offset,
        "length": args.window_length,
        "chunk_size": args.window_chunk_size,
        "sha256": sha256_hex(blob),
        "prefix_hex": blob[:128].hex(),
        "payload_hits": payload_hits(blob, payload) if payload else {},
        "records": records,
    }
    return report


def identity_summary(data: bytes) -> dict[str, Any]:
    return {
        "vendor": data[8:16].decode("ascii", "replace").strip() if len(data) >= 16 else "",
        "product": data[16:32].decode("ascii", "replace").strip() if len(data) >= 32 else "",
        "revision": data[32:36].decode("ascii", "replace").strip() if len(data) >= 36 else "",
        "sha256": sha256_hex(data) if data else None,
        "prefix_hex": data[:64].hex(),
    }


def default_echo_payloads() -> list[tuple[str, bytes]]:
    return [
        ("p4", bytes.fromhex("5a a5 11 ee")),
        (
            "p16",
            bytes.fromhex("42 4d 49 4f 00 00 00 01 5a a5 11 ee c3 3c 7e 81"),
        ),
        ("p80", bytes(((i * 37 + 0x5A) & 0xFF) for i in range(0x80))),
    ]


def parse_named_payloads(values: list[str]) -> list[tuple[str, bytes]]:
    if not values:
        return default_echo_payloads()
    payloads: list[tuple[str, bytes]] = []
    for idx, value in enumerate(values):
        if "=" in value:
            name, hex_text = value.split("=", 1)
            if not name:
                raise argparse.ArgumentTypeError("payload name must not be empty")
        else:
            name, hex_text = f"payload{idx:02d}", value
        payload = parse_hex_bytes(hex_text)
        if not payload:
            raise argparse.ArgumentTypeError("payload must not be empty")
        payloads.append((name, payload))
    return payloads


def interleave_commands(args: argparse.Namespace) -> list[Command]:
    names = args.interleave or ["inquiry", "get-config", "mode-sense-read-error"]
    commands = []
    for name in names:
        if name == "inquiry":
            commands.append(inquiry_command())
        elif name == "get-config":
            commands.append(get_config_command())
        elif name == "mode-sense-read-error":
            commands.append(mode_sense_read_error_command())
        elif name == "request-sense":
            commands.append(request_sense_command())
        else:
            raise ValueError(f"unknown interleave command: {name}")
    return commands


def run_echo_buffer(args: argparse.Namespace) -> int:
    run_id = datetime.now(timezone.utc).strftime("normal-mailbox-echo-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"writing {out_dir}", flush=True)

    report: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": "jonathan-thinkpad-t480s" if "linux" in str(args.out_dir) else None,
        "device": args.device,
        "probe": "echo-buffer",
        "notes": (
            "Standard SCSI echo-buffer probe only: READ BUFFER mode 0x0b and "
            "WRITE/READ BUFFER mode 0x0a. No firmware download modes are used."
        ),
        "settings": {
            "buffer_id": args.buffer_id,
            "offset": args.offset,
            "capture_window": args.capture_window,
            "window_mode": args.window_mode,
            "window_id": args.window_id,
            "window_offset": args.window_offset,
            "window_length": args.window_length,
        },
        "commands": [],
        "payload_results": [],
    }

    idx = 0
    identity_record = save_command_result(
        args=args,
        out_dir=out_dir,
        index=idx,
        command=inquiry_command(),
    )
    report["commands"].append(identity_record | {"role": "identity-before"})
    identity_data = Path(identity_record["response_path"]).read_bytes()
    report["identity_before"] = identity_summary(identity_data)
    idx += 1
    print(
        "identity "
        f"{report['identity_before']['vendor']} {report['identity_before']['product']} "
        f"{report['identity_before']['revision']}",
        flush=True,
    )

    descriptor_lengths = [4]
    if args.descriptor_len not in descriptor_lengths:
        descriptor_lengths.append(args.descriptor_len)
    for length in descriptor_lengths:
        command = Command(
            f"read-buffer-echo-descriptor-len{length}",
            read_buffer_cdb(0x0B, args.buffer_id, args.offset, length),
            request_len=length,
            notes="READ BUFFER echo-buffer descriptor",
        )
        record = save_command_result(args=args, out_dir=out_dir, index=idx, command=command)
        report["commands"].append(record | {"role": "echo-descriptor"})
        print(
            f"{idx:02d} descriptor len={length} rc={record['returncode']} "
            f"good={record['good']} out={record['length']}",
            flush=True,
        )
        idx += 1

    if args.capture_window:
        window = capture_work_window(
            args=args,
            out_dir=out_dir,
            index=idx,
            name="baseline-before-echo",
        )
        report["commands"].append({"role": "work-window-before", "window": window})
        print(f"{idx:02d} baseline window sha={window['sha256'][:16]}", flush=True)
        idx += 1

    interleaves = interleave_commands(args)
    for payload_name, payload in parse_named_payloads(args.payload):
        payload_result: dict[str, Any] = {
            "name": payload_name,
            "payload_len": len(payload),
            "payload_sha256": sha256_hex(payload),
            "payload_hex": payload.hex() if len(payload) <= 0x100 else None,
            "steps": [],
        }
        write_cmd = Command(
            f"write-buffer-echo-{payload_name}",
            write_buffer_echo_cdb(args.buffer_id, args.offset, len(payload)),
            payload=payload,
            notes="WRITE BUFFER echo mode 0x0a only",
        )
        write_record = save_command_result(
            args=args,
            out_dir=out_dir,
            index=idx,
            command=write_cmd,
            payload_for_hits=payload,
        )
        payload_result["steps"].append(write_record | {"role": "echo-write"})
        print(
            f"{idx:02d} {payload_name} write rc={write_record['returncode']} "
            f"good={write_record['good']}",
            flush=True,
        )
        idx += 1

        read_cmd = Command(
            f"read-buffer-echo-{payload_name}-immediate",
            read_buffer_cdb(0x0A, args.buffer_id, args.offset, len(payload)),
            request_len=len(payload),
            notes="READ BUFFER echo mode 0x0a immediate readback",
        )
        read_record = save_command_result(
            args=args,
            out_dir=out_dir,
            index=idx,
            command=read_cmd,
            payload_for_hits=payload,
        )
        read_data = Path(read_record["response_path"]).read_bytes()
        read_record["matches_payload"] = read_data == payload
        payload_result["steps"].append(read_record | {"role": "echo-read-immediate"})
        print(
            f"{idx:02d} {payload_name} read immediate rc={read_record['returncode']} "
            f"good={read_record['good']} match={read_record['matches_payload']}",
            flush=True,
        )
        idx += 1

        if args.capture_window:
            window = capture_work_window(
                args=args,
                out_dir=out_dir,
                index=idx,
                name=f"after-{payload_name}-immediate-read",
                payload=payload,
            )
            payload_result["steps"].append({"role": "work-window-after-immediate-read", "window": window})
            print(
                f"{idx:02d} {payload_name} window exact_hits="
                f"{len(window['payload_hits'].get('exact_offsets', [])) if window.get('payload_hits') else 0} "
                f"sha={window['sha256'][:16]}",
                flush=True,
            )
            idx += 1

        for interleave in interleaves:
            inter_record = save_command_result(
                args=args,
                out_dir=out_dir,
                index=idx,
                command=interleave,
                payload_for_hits=payload,
            )
            payload_result["steps"].append(inter_record | {"role": f"interleave-{interleave.name}"})
            print(
                f"{idx:02d} {payload_name} interleave {interleave.name} "
                f"rc={inter_record['returncode']} good={inter_record['good']}",
                flush=True,
            )
            idx += 1

            read_after = Command(
                f"read-buffer-echo-{payload_name}-after-{interleave.name}",
                read_buffer_cdb(0x0A, args.buffer_id, args.offset, len(payload)),
                request_len=len(payload),
                notes="READ BUFFER echo mode 0x0a after interleaved normal command",
            )
            read_after_record = save_command_result(
                args=args,
                out_dir=out_dir,
                index=idx,
                command=read_after,
                payload_for_hits=payload,
            )
            read_after_data = Path(read_after_record["response_path"]).read_bytes()
            read_after_record["matches_payload"] = read_after_data == payload
            payload_result["steps"].append(
                read_after_record | {"role": f"echo-read-after-{interleave.name}"}
            )
            print(
                f"{idx:02d} {payload_name} read after {interleave.name} "
                f"rc={read_after_record['returncode']} good={read_after_record['good']} "
                f"match={read_after_record['matches_payload']}",
                flush=True,
            )
            idx += 1

            if args.capture_window:
                window = capture_work_window(
                    args=args,
                    out_dir=out_dir,
                    index=idx,
                    name=f"after-{payload_name}-{interleave.name}",
                    payload=payload,
                )
                payload_result["steps"].append(
                    {"role": f"work-window-after-{interleave.name}", "window": window}
                )
                print(
                    f"{idx:02d} {payload_name} window after {interleave.name} "
                    f"exact_hits={len(window['payload_hits'].get('exact_offsets', [])) if window.get('payload_hits') else 0} "
                    f"sha={window['sha256'][:16]}",
                    flush=True,
                )
                idx += 1

        report["payload_results"].append(payload_result)

    after_identity_record = save_command_result(
        args=args,
        out_dir=out_dir,
        index=idx,
        command=inquiry_command(),
    )
    report["commands"].append(after_identity_record | {"role": "identity-after"})
    after_identity_data = Path(after_identity_record["response_path"]).read_bytes()
    report["identity_after"] = identity_summary(after_identity_data)
    idx += 1

    report["drive_identity_stable"] = report["identity_before"] == report["identity_after"]
    report["any_echo_write_good"] = any(
        bool(step.get("good"))
        for result in report["payload_results"]
        for step in result["steps"]
        if step.get("role") == "echo-write"
    )
    report["any_echo_read_matches"] = any(
        bool(step.get("matches_payload"))
        for result in report["payload_results"]
        for step in result["steps"]
        if str(step.get("role", "")).startswith("echo-read")
    )
    report["any_work_window_exact_payload_hit"] = any(
        bool(step.get("window", {}).get("payload_hits", {}).get("exact_offsets"))
        for result in report["payload_results"]
        for step in result["steps"]
        if "window" in step
    )

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {summary_path}", flush=True)
    print(
        "summary "
        f"identity_stable={report['drive_identity_stable']} "
        f"echo_write_good={report['any_echo_write_good']} "
        f"echo_read_matches={report['any_echo_read_matches']} "
        f"window_payload_hit={report['any_work_window_exact_payload_hit']}",
        flush=True,
    )
    return 0 if report["drive_identity_stable"] else 2


def run_mode_changeable(args: argparse.Namespace) -> int:
    """Read MODE SENSE changeable/current pages without writing MODE SELECT."""
    run_id = datetime.now(timezone.utc).strftime("normal-mailbox-mode-changeable-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "probe": "mode-changeable",
        "notes": "Read-only MODE SENSE(10) current/changeable survey. MODE SELECT is not sent.",
        "pages": [],
    }
    idx = 0
    for page in args.page:
        for pc_name, pc_bits in (("current", 0x00), ("changeable", 0x40)):
            cdb = (0x5A, 0x00, (pc_bits | (page & 0x3F)), 0, 0, 0, 0, 0, args.alloc_len, 0)
            command = Command(
                f"mode-sense10-{pc_name}-page0x{page:02x}",
                cdb,
                request_len=args.alloc_len,
            )
            record = save_command_result(args=args, out_dir=out_dir, index=idx, command=command)
            report["pages"].append(record | {"page": page, "pc": pc_name})
            print(
                f"{idx:02d} page=0x{page:02x} pc={pc_name} "
                f"rc={record['returncode']} good={record['good']} len={record['length']}",
                flush=True,
            )
            idx += 1
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {summary_path}", flush=True)
    return 0


def run_mode_mailbox(args: argparse.Namespace) -> int:
    """Try one volatile MODE SELECT bit round-trip, restoring immediately."""
    run_id = datetime.now(timezone.utc).strftime("normal-mailbox-mode-select-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    page = args.page
    page_byte = args.page_byte
    xor_mask = args.xor_mask
    report: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "probe": "mode-mailbox",
        "notes": "Volatile MODE SELECT(10) SP=0 one-bit round-trip; restore is attempted immediately.",
        "execute": args.execute,
        "page": page,
        "page_byte": page_byte,
        "xor_mask": xor_mask,
        "steps": [],
        "windows": [],
    }
    idx = 0
    identity = save_command_result(args=args, out_dir=out_dir, index=idx, command=inquiry_command())
    report["steps"].append(identity | {"role": "identity-before"})
    report["identity_before"] = identity_summary(Path(identity["response_path"]).read_bytes())
    print(
        "identity "
        f"{report['identity_before']['vendor']} {report['identity_before']['product']} "
        f"{report['identity_before']['revision']}",
        flush=True,
    )
    idx += 1

    current_cmd = Command(
        f"mode-sense10-current-page0x{page:02x}",
        mode_sense10_cdb(page, 0x00, args.alloc_len),
        request_len=args.alloc_len,
    )
    current = save_command_result(args=args, out_dir=out_dir, index=idx, command=current_cmd)
    report["steps"].append(current | {"role": "current-before"})
    current_data = Path(current["response_path"]).read_bytes()
    print(f"{idx:02d} current rc={current['returncode']} good={current['good']} len={current['length']}", flush=True)
    idx += 1

    changeable_cmd = Command(
        f"mode-sense10-changeable-page0x{page:02x}",
        mode_sense10_cdb(page, 0x40, args.alloc_len),
        request_len=args.alloc_len,
    )
    changeable = save_command_result(args=args, out_dir=out_dir, index=idx, command=changeable_cmd)
    report["steps"].append(changeable | {"role": "changeable"})
    changeable_data = Path(changeable["response_path"]).read_bytes()
    print(
        f"{idx:02d} changeable rc={changeable['returncode']} good={changeable['good']} "
        f"len={changeable['length']}",
        flush=True,
    )
    idx += 1

    page_offset = 8
    target_offset = page_offset + page_byte
    if not current.get("good") or not changeable.get("good"):
        report["error"] = "current/changeable MODE SENSE did not both complete"
    elif target_offset >= len(current_data) or target_offset >= len(changeable_data):
        report["error"] = f"target page byte 0x{page_byte:x} outside response"
    elif current_data[page_offset] != page or changeable_data[page_offset] != page:
        report["error"] = "response page code did not match requested page"
    elif (changeable_data[target_offset] & xor_mask) != xor_mask:
        report["error"] = (
            f"target mask 0x{xor_mask:02x} is not fully advertised changeable "
            f"(changeable byte=0x{changeable_data[target_offset]:02x})"
        )
    else:
        old_byte = current_data[target_offset]
        new_byte = old_byte ^ xor_mask
        report["target"] = {
            "absolute_response_offset": target_offset,
            "page_byte": page_byte,
            "old_byte": old_byte,
            "new_byte": new_byte,
            "changeable_byte": changeable_data[target_offset],
        }
        mutated = bytearray(current_data)
        restored = bytearray(current_data)
        # MODE SELECT parameter lists reserve the mode-data-length field.
        mutated[0] = mutated[1] = 0
        restored[0] = restored[1] = 0
        mutated[target_offset] = new_byte
        if not args.execute:
            report["dry_run_select_payload_hex"] = bytes(mutated).hex()
            print(
                f"dry-run target response_offset=0x{target_offset:02x} "
                f"old=0x{old_byte:02x} new=0x{new_byte:02x}",
                flush=True,
            )
        else:
            select_mut = Command(
                f"mode-select10-page0x{page:02x}-mutate",
                mode_select10_cdb(len(mutated)),
                payload=bytes(mutated),
                notes="MODE SELECT(10) PF=1 SP=0 mutated current page",
            )
            mutate_record = save_command_result(args=args, out_dir=out_dir, index=idx, command=select_mut)
            report["steps"].append(mutate_record | {"role": "mode-select-mutated"})
            print(
                f"{idx:02d} mutate select rc={mutate_record['returncode']} good={mutate_record['good']}",
                flush=True,
            )
            idx += 1

            after_mut = save_command_result(args=args, out_dir=out_dir, index=idx, command=current_cmd)
            after_mut_data = Path(after_mut["response_path"]).read_bytes()
            after_byte = after_mut_data[target_offset] if len(after_mut_data) > target_offset else None
            after_mut["target_byte"] = after_byte
            report["steps"].append(after_mut | {"role": "current-after-mutated"})
            report["after_mutated_target_byte"] = after_byte
            print(
                f"{idx:02d} after mutate current rc={after_mut['returncode']} "
                f"good={after_mut['good']} target={after_byte}",
                flush=True,
            )
            idx += 1

            if args.capture_window:
                window = capture_work_window(
                    args=args,
                    out_dir=out_dir,
                    index=idx,
                    name="after-mode-select-mutated",
                )
                report["windows"].append(window | {"role": "work-window-after-mutated"})
                print(f"{idx:02d} mutated window sha={window['sha256'][:16]}", flush=True)
                idx += 1

            select_restore = Command(
                f"mode-select10-page0x{page:02x}-restore",
                mode_select10_cdb(len(restored)),
                payload=bytes(restored),
                notes="MODE SELECT(10) PF=1 SP=0 restore original current page",
            )
            restore_record = save_command_result(args=args, out_dir=out_dir, index=idx, command=select_restore)
            report["steps"].append(restore_record | {"role": "mode-select-restore"})
            print(
                f"{idx:02d} restore select rc={restore_record['returncode']} good={restore_record['good']}",
                flush=True,
            )
            idx += 1

            after_restore = save_command_result(args=args, out_dir=out_dir, index=idx, command=current_cmd)
            after_restore_data = Path(after_restore["response_path"]).read_bytes()
            restore_byte = after_restore_data[target_offset] if len(after_restore_data) > target_offset else None
            after_restore["target_byte"] = restore_byte
            report["steps"].append(after_restore | {"role": "current-after-restore"})
            report["after_restore_target_byte"] = restore_byte
            report["roundtrip_observed"] = after_byte == new_byte and restore_byte == old_byte
            print(
                f"{idx:02d} after restore current rc={after_restore['returncode']} "
                f"good={after_restore['good']} target={restore_byte} "
                f"roundtrip={report['roundtrip_observed']}",
                flush=True,
            )
            idx += 1

            if args.capture_window:
                window = capture_work_window(
                    args=args,
                    out_dir=out_dir,
                    index=idx,
                    name="after-mode-select-restore",
                )
                report["windows"].append(window | {"role": "work-window-after-restore"})
                print(f"{idx:02d} restored window sha={window['sha256'][:16]}", flush=True)
                idx += 1

    after_identity = save_command_result(args=args, out_dir=out_dir, index=idx, command=inquiry_command())
    report["steps"].append(after_identity | {"role": "identity-after"})
    report["identity_after"] = identity_summary(Path(after_identity["response_path"]).read_bytes())
    report["drive_identity_stable"] = report["identity_before"] == report["identity_after"]
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {summary_path}", flush=True)
    print(
        f"summary identity_stable={report['drive_identity_stable']} "
        f"error={report.get('error')} roundtrip={report.get('roundtrip_observed')}",
        flush=True,
    )
    return 0 if report["drive_identity_stable"] else 2


def parse_css_agid(data: bytes) -> int | None:
    if len(data) < 8:
        return None
    # MMC-6 Table 516 places the granted AGID in bits 7..6 of the last byte.
    return (data[7] >> 6) & 0x03


def default_auth_nonce() -> bytes:
    return bytes.fromhex("42 4d 49 4f 4e 4f 4e 43 45 01")


def send_dvd_auth_command(
    *,
    args: argparse.Namespace,
    out_dir: Path,
    index: int,
    command: Command,
    role: str,
    nonce: bytes = b"",
) -> tuple[int, dict[str, Any], bytes]:
    record = save_command_result(
        args=args,
        out_dir=out_dir,
        index=index,
        command=command,
        payload_for_hits=nonce,
    )
    data = Path(record["response_path"]).read_bytes()
    record["role"] = role
    if nonce:
        record["nonce_hits"] = payload_hits(data, nonce)
    print(
        f"{index:02d} {role} {command.name} rc={record['returncode']} "
        f"good={record['good']} len={record['length']}",
        flush=True,
    )
    return index + 1, record, data


def run_dvd_auth(args: argparse.Namespace) -> int:
    """Probe normal REPORT KEY/SEND KEY traffic without touching firmware or media writes."""
    run_id = datetime.now(timezone.utc).strftime("normal-mailbox-dvd-auth-%Y%m%dT%H%M%S%fZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    nonce = parse_hex_bytes(args.nonce) if args.nonce else default_auth_nonce()
    if len(nonce) != 10:
        raise ValueError("CSS challenge nonce must be exactly 10 bytes")
    report: dict[str, Any] = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": args.device,
        "probe": "dvd-auth",
        "notes": (
            "Normal MMC REPORT KEY/SEND KEY authentication probe. This exercises "
            "standard command paths only; SEND KEY challenge is opt-in."
        ),
        "nonce_hex": nonce.hex(),
        "send_challenge": args.send_challenge,
        "capture_step_windows": args.capture_step_windows,
        "steps": [],
        "windows": [],
    }
    idx = 0

    def maybe_capture_step_window(index: int, role: str) -> int:
        if not args.capture_step_windows:
            return index
        window = capture_work_window(
            args=args,
            out_dir=out_dir,
            index=index,
            name=f"after-{role}",
            payload=nonce,
        )
        window["role"] = f"work-window-after-{role}"
        report["windows"].append(window)
        print(
            f"{index:02d} window after {role} exact_nonce_hits="
            f"{len(window['payload_hits'].get('exact_offsets', [])) if window.get('payload_hits') else 0} "
            f"sha={window['sha256'][:16]}",
            flush=True,
        )
        return index + 1

    identity_record = save_command_result(args=args, out_dir=out_dir, index=idx, command=inquiry_command())
    report["steps"].append(identity_record | {"role": "identity-before"})
    report["identity_before"] = identity_summary(Path(identity_record["response_path"]).read_bytes())
    print(
        "identity "
        f"{report['identity_before']['vendor']} {report['identity_before']['product']} "
        f"{report['identity_before']['revision']}",
        flush=True,
    )
    idx += 1

    idx, agid_record, agid_data = send_dvd_auth_command(
        args=args,
        out_dir=out_dir,
        index=idx,
        command=Command(
            "report-key-css-agid",
            report_key_cdb(key_class=0x00, key_format=0x00, allocation_length=8),
            request_len=8,
            notes="REPORT KEY key class 0 / key format 0: request CSS/CPPM AGID",
        ),
        role="report-key-css-agid",
        nonce=nonce,
    )
    report["steps"].append(agid_record)
    agid = parse_css_agid(agid_data) if agid_record.get("good") else None
    report["agid"] = agid
    print(f"parsed_agid={agid}", flush=True)
    idx = maybe_capture_step_window(idx, "report-key-css-agid")

    # These formats are useful even when AGID grant fails: ASF and RPC are
    # specified as reserved/ignored AGID in MMC-6.
    for name, key_format, alloc in (
        ("report-key-css-asf", 0x05, 8),
        ("report-key-css-rpc-state", 0x08, 8),
    ):
        idx, record, _ = send_dvd_auth_command(
            args=args,
            out_dir=out_dir,
            index=idx,
            command=Command(
                name,
                report_key_cdb(
                    key_class=0x00,
                    key_format=key_format,
                    allocation_length=alloc,
                    agid=agid or 0,
                ),
                request_len=alloc,
            ),
            role=name,
            nonce=nonce,
        )
        report["steps"].append(record)
        idx = maybe_capture_step_window(idx, name)

    if agid is not None:
        if args.send_challenge:
            # CSS authentication is order-sensitive: the drive rejects the
            # challenge/key path with "command sequence error" until it sees a
            # host challenge for the granted AGID.
            payload = b"\x00\x0e\x00\x00" + nonce + b"\x00\x00"
            idx, send_record, _ = send_dvd_auth_command(
                args=args,
                out_dir=out_dir,
                index=idx,
                command=Command(
                    "send-key-css-host-challenge",
                    send_key_cdb(
                        key_class=0x00,
                        key_format=0x01,
                        parameter_list_length=len(payload),
                        agid=agid,
                    ),
                    payload=payload,
                    notes="SEND KEY key class 0 / key format 1: host challenge",
                ),
                role="send-key-css-host-challenge",
                nonce=nonce,
            )
            report["steps"].append(send_record)
            idx = maybe_capture_step_window(idx, "send-key-css-host-challenge")

            idx, key1_record, _ = send_dvd_auth_command(
                args=args,
                out_dir=out_dir,
                index=idx,
                command=Command(
                    "report-key-css-key1",
                    report_key_cdb(
                        key_class=0x00,
                        key_format=0x02,
                        allocation_length=12,
                        agid=agid,
                    ),
                    request_len=12,
                ),
                role="report-key-css-key1-after-host-challenge",
                nonce=nonce,
            )
            report["steps"].append(key1_record)
            idx = maybe_capture_step_window(idx, "report-key-css-key1")

            idx, challenge_record, _ = send_dvd_auth_command(
                args=args,
                out_dir=out_dir,
                index=idx,
                command=Command(
                    "report-key-css-drive-challenge",
                    report_key_cdb(
                        key_class=0x00,
                        key_format=0x01,
                        allocation_length=16,
                        agid=agid,
                    ),
                    request_len=16,
                ),
                role="report-key-css-drive-challenge-after-host-challenge",
                nonce=nonce,
            )
            report["steps"].append(challenge_record)
            idx = maybe_capture_step_window(idx, "report-key-css-drive-challenge")
        else:
            report["challenge_path_skipped"] = (
                "CSS challenge/key commands require a host challenge first; "
                "rerun with --send-challenge to exercise the bidirectional path."
            )

        idx, invalidate_record, _ = send_dvd_auth_command(
            args=args,
            out_dir=out_dir,
            index=idx,
            command=Command(
                "report-key-css-invalidate-agid",
                report_key_cdb(
                    key_class=0x00,
                    key_format=0x3F,
                    allocation_length=0,
                    agid=agid,
                ),
                request_len=0,
            ),
            role="report-key-css-invalidate-agid",
            nonce=nonce,
        )
        report["steps"].append(invalidate_record)
        idx = maybe_capture_step_window(idx, "report-key-css-invalidate-agid")

    if args.capture_window:
        window = capture_work_window(
            args=args,
            out_dir=out_dir,
            index=idx,
            name="after-dvd-auth",
            payload=nonce,
        )
        report["windows"].append(window)
        print(
            f"{idx:02d} window exact_nonce_hits="
            f"{len(window['payload_hits'].get('exact_offsets', [])) if window.get('payload_hits') else 0} "
            f"sha={window['sha256'][:16]}",
            flush=True,
        )
        idx += 1

    after_identity = save_command_result(args=args, out_dir=out_dir, index=idx, command=inquiry_command())
    report["steps"].append(after_identity | {"role": "identity-after"})
    report["identity_after"] = identity_summary(Path(after_identity["response_path"]).read_bytes())
    report["drive_identity_stable"] = report["identity_before"] == report["identity_after"]
    report["any_nonce_hit"] = any(
        bool(step.get("nonce_hits", {}).get("exact_offsets"))
        for step in report["steps"]
    ) or any(
        bool(window.get("payload_hits", {}).get("exact_offsets"))
        for window in report["windows"]
    )
    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {summary_path}", flush=True)
    print(
        f"summary identity_stable={report['drive_identity_stable']} "
        f"agid={agid} any_nonce_hit={report['any_nonce_hit']}",
        flush=True,
    )
    return 0 if report["drive_identity_stable"] else 2


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "references/evidence/live")
    parser.add_argument("--timeout", type=int, default=4)
    parser.add_argument("--process-timeout", type=float, default=8.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    echo = subparsers.add_parser("echo-buffer", help="probe standard WRITE/READ BUFFER echo modes")
    add_common_args(echo)
    echo.add_argument("--buffer-id", type=parse_byte, default=0)
    echo.add_argument("--offset", type=parse_int, default=0)
    echo.add_argument("--descriptor-len", type=parse_int, default=0x10)
    echo.add_argument(
        "--payload",
        action="append",
        default=[],
        help="Optional named payload NAME=HEX or bare HEX. Repeatable. Defaults to 4/16/0x80 patterns.",
    )
    echo.add_argument(
        "--interleave",
        action="append",
        choices=("inquiry", "get-config", "mode-sense-read-error", "request-sense"),
        default=None,
        help="Normal command to interleave between echo write/readback checks. Repeatable.",
    )
    echo.add_argument("--capture-window", action="store_true")
    echo.add_argument("--window-mode", type=parse_byte, default=0x01)
    echo.add_argument("--window-id", type=parse_byte, default=0x01)
    echo.add_argument("--window-offset", type=parse_int, default=0x070000)
    echo.add_argument("--window-length", type=parse_int, default=0x4000)
    echo.add_argument("--window-chunk-size", type=parse_int, default=0x400)
    echo.set_defaults(func=run_echo_buffer)

    mode = subparsers.add_parser(
        "mode-changeable",
        help="read-only MODE SENSE current/changeable survey for future volatile MODE SELECT planning",
    )
    add_common_args(mode)
    mode.add_argument(
        "--page",
        type=parse_byte,
        action="append",
        default=[0x01, 0x08, 0x0D, 0x0E, 0x1A, 0x1C, 0x2A, 0x3F],
    )
    mode.add_argument("--alloc-len", type=parse_byte, default=0xFC)
    mode.set_defaults(func=run_mode_changeable)

    mode_mailbox = subparsers.add_parser(
        "mode-mailbox",
        help="try one volatile MODE SELECT round-trip for a changeable bit",
    )
    add_common_args(mode_mailbox)
    mode_mailbox.add_argument("--page", type=parse_byte, default=0x08)
    mode_mailbox.add_argument(
        "--page-byte",
        type=parse_int,
        default=0x02,
        help="byte offset within the mode page, where page byte 0 is the page code",
    )
    mode_mailbox.add_argument("--xor-mask", type=parse_byte, default=0x04)
    mode_mailbox.add_argument("--alloc-len", type=parse_int, default=0xFC)
    mode_mailbox.add_argument(
        "--execute",
        action="store_true",
        help="actually send MODE SELECT(10); without this, only plan and save payload",
    )
    mode_mailbox.add_argument("--capture-window", action="store_true")
    mode_mailbox.add_argument("--window-mode", type=parse_byte, default=0x01)
    mode_mailbox.add_argument("--window-id", type=parse_byte, default=0x01)
    mode_mailbox.add_argument("--window-offset", type=parse_int, default=0x070000)
    mode_mailbox.add_argument("--window-length", type=parse_int, default=0x4000)
    mode_mailbox.add_argument("--window-chunk-size", type=parse_int, default=0x400)
    mode_mailbox.set_defaults(func=run_mode_mailbox)

    dvd = subparsers.add_parser("dvd-auth", help="probe normal REPORT KEY/SEND KEY auth paths")
    add_common_args(dvd)
    dvd.add_argument("--nonce", help="10-byte CSS challenge nonce as hex. Default is a BMIO marker.")
    dvd.add_argument(
        "--send-challenge",
        action="store_true",
        help="also send a standard CSS host challenge with the nonce after AGID grant",
    )
    dvd.add_argument("--capture-window", action="store_true")
    dvd.add_argument(
        "--capture-step-windows",
        action="store_true",
        help="capture the public work window after each auth command; this intentionally interleaves READ BUFFER commands",
    )
    dvd.add_argument("--window-mode", type=parse_byte, default=0x01)
    dvd.add_argument("--window-id", type=parse_byte, default=0x01)
    dvd.add_argument("--window-offset", type=parse_int, default=0x070000)
    dvd.add_argument("--window-length", type=parse_int, default=0x4000)
    dvd.add_argument("--window-chunk-size", type=parse_int, default=0x400)
    dvd.set_defaults(func=run_dvd_auth)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return args.func(args)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
