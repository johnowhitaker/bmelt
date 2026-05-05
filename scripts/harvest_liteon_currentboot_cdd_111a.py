#!/usr/bin/env python3
"""Harvest FUN_CODE_111a materializer windows.

This is a live Linux helper for the currentboot response hook built with
`--gateway-cdb-bulk-with-cdd-111a-selector`,
`--cdd-111a-selector-from-cdb9`, and `--cdd-111a-source-from-cdb`.

For each requested source offset it:

1. cold-cycles the drive with the Pico servo, unless disabled;
2. confirms the optical LUN is back as LD5M;
3. sends the candidate profile-tail event to enter currentboot;
4. triggers FUN_CODE_111a with a selected case and source from CDB[10]/[6]/[7];
5. reads configured controller-gateway bands through the hook fallback;
6. optionally cold-cycles back to LD5M.

It does not edit CDD bytes or persistent F0 contents. The only data-out command
is the known profile-tail/currentboot entry payload from the supplied candidate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SG_RAW = "/usr/bin/sg_raw"
DEFAULT_DEVICE = "/dev/sg0"
DEFAULT_PICO_PORT = "/dev/ttyACM0"
DEFAULT_CANDIDATE = (
    ROOT
    / "references/firmware/extracted/currentboot-response-hook-candidates"
    / "currentboot-response-hook-gateway-bulk-cdd-111a-selector-cdb9-source-cdb10"
    / "currentboot-response-hook-gateway-bulk-cdd-111a-selector-cdb9-source-cdb10"
    / "liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-gateway-bulk-cdd-111a-selector-cdb9-source-cdb10-candidate.json"
)
DEFAULT_OUT_ROOT = ROOT / "references/evidence/live"
STANDARD_INQUIRY_CDB = [0x12, 0x00, 0x00, 0x00, 0x24, 0x00]
EXTRAINQ_CDB = [0x12, 0x00, 0x00, 0x00, 0xF0, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
TEST_UNIT_READY_CDB = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def parse_band(value: str) -> tuple[int, int]:
    if ":" not in value:
        raise argparse.ArgumentTypeError("band must be START:LENGTH")
    start_text, length_text = value.split(":", 1)
    start = parse_int(start_text)
    length = parse_int(length_text)
    if length <= 0:
        raise argparse.ArgumentTypeError("band length must be positive")
    if start + length > 0x1000000:
        raise argparse.ArgumentTypeError("band crosses 24-bit controller address space")
    return start, length


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def ascii_preview(data: bytes) -> str:
    return "".join(chr(byte) if 0x20 <= byte < 0x7F else "." for byte in data)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact_hex(text: str) -> str:
    return "".join(ch for ch in text if ch in "0123456789abcdefABCDEF")


def bytes_from_hex_text(text: str) -> bytes:
    compact = compact_hex(text)
    if len(compact) % 2:
        raise ValueError("hex payload has odd length")
    return bytes.fromhex(compact)


def run(
    cmd: list[str],
    *,
    input_bytes: bytes = b"",
    timeout: float | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        cmd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def run_text(cmd: list[str], *, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def sg_raw(
    *,
    sg_raw_path: str,
    device: str,
    cdb: list[int],
    request_len: int = 0,
    payload: bytes = b"",
    timeout: int = 10,
) -> dict[str, Any]:
    cmd = [sg_raw_path, "--cmdset=1", "-b", "--timeout", str(timeout)]
    if request_len:
        cmd.extend(["--request", str(request_len)])
    if payload:
        cmd.extend(["--send", str(len(payload))])
    cmd.extend([device, *[f"{byte:02x}" for byte in cdb]])
    started = time.monotonic()
    proc = run(cmd, input_bytes=payload, timeout=timeout + 5)
    elapsed = time.monotonic() - started
    return {
        "cmd": cmd,
        "cdb": cdb_text(cdb),
        "request_len": request_len,
        "payload_len": len(payload),
        "payload_sha256": sha256_hex(payload) if payload else None,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "stdout_len": len(proc.stdout),
        "stdout_sha256": sha256_hex(proc.stdout) if proc.stdout else None,
        "stdout_first64_hex": proc.stdout[:64].hex(),
        "stdout_hex": proc.stdout.hex() if len(proc.stdout) <= 0x1000 else None,
        "stderr": proc.stderr.decode("utf-8", "replace"),
        "stdout": proc.stdout,
    }


def describe_standard(data: bytes) -> dict[str, Any]:
    def field(start: int, end: int) -> str:
        return data[start:end].decode("ascii", "replace").strip() if len(data) >= end else ""

    return {
        "vendor": field(0x08, 0x10),
        "product": field(0x10, 0x20),
        "revision": field(0x20, 0x24),
        "sha256": sha256_hex(data) if data else None,
    }


def capture_identity(args: argparse.Namespace) -> dict[str, Any]:
    standard = sg_raw(
        sg_raw_path=args.sg_raw,
        device=args.device,
        cdb=STANDARD_INQUIRY_CDB,
        request_len=36,
        timeout=args.timeout,
    )
    identity = {
        "standard": {k: v for k, v in standard.items() if k != "stdout"},
        "standard_decoded": describe_standard(standard["stdout"]),
    }
    if not getattr(args, "identity_standard_only", False):
        extrainq = sg_raw(
            sg_raw_path=args.sg_raw,
            device=args.device,
            cdb=EXTRAINQ_CDB,
            request_len=0xF0,
            timeout=args.timeout,
        )
        identity["extrainq"] = {k: v for k, v in extrainq.items() if k != "stdout"}
    return identity


def wait_for_ld5m(args: argparse.Namespace) -> dict[str, Any]:
    deadline = time.monotonic() + args.wait_timeout
    last_identity: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        identity = capture_identity(args)
        last_identity = identity
        decoded = identity.get("standard_decoded") or {}
        if decoded.get("product") == "DVD+-RW DS-8ABSH" and decoded.get("revision") == "LD5M":
            return identity
        time.sleep(args.wait_interval)
    raise RuntimeError(f"timed out waiting for LD5M; last identity={last_identity}")


def is_becoming_ready_status(item: dict[str, Any]) -> bool:
    return "becoming ready" in str(item.get("stderr", "")).lower()


def wait_until_not_becoming_ready(args: argparse.Namespace) -> dict[str, Any]:
    """Wait past optical/media spin-up without requiring media-ready GOOD status.

    A drive with no medium may legitimately report Not Ready / medium not
    present, and that state has historically been fine for the currentboot
    update-entry event. What breaks event1 is the transient "logical unit is in
    process of becoming ready" state seen while an inserted disc is spinning up.
    """

    deadline = time.monotonic() + args.wait_timeout
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        tur = sg_raw(
            sg_raw_path=args.sg_raw,
            device=args.device,
            cdb=TEST_UNIT_READY_CDB,
            timeout=args.timeout,
        )
        tur.pop("stdout", None)
        last = tur
        if not is_becoming_ready_status(tur):
            return tur
        time.sleep(args.wait_interval)
    raise RuntimeError(f"timed out waiting for TEST UNIT READY to leave becoming-ready state; last={last}")


def pico_toggle(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "pico/client.py",
        "--port",
        args.pico_port,
        "TOGGLE SERVO",
        str(args.servo_hold_ms),
    ]
    proc = run_text(cmd, timeout=max(args.pico_timeout, args.servo_hold_ms / 1000 + 3))
    out: dict[str, Any] = {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    if proc.returncode != 0:
        raise RuntimeError(f"Pico servo command failed: {proc.stderr.strip()}")
    for line in proc.stdout.splitlines():
        try:
            out["response_json"] = json.loads(line)
            break
        except json.JSONDecodeError:
            pass
    return out


def load_event1(candidate_path: Path) -> tuple[list[int], bytes]:
    candidate = json.loads(candidate_path.read_text())
    events = candidate.get("events") or []
    if len(events) < 2 or events[1].get("phase") != "profile_tail_arg7f":
        raise ValueError("candidate does not have profile_tail_arg7f at event 1")
    event = events[1]
    cdb = [int(part, 16) for part in str(event["cdb"]).split()]
    model = event.get("payload_model") or {}
    if model.get("kind") != "inline_payload_hex":
        raise ValueError("event 1 payload is not inline_payload_hex")
    payload = bytes_from_hex_text(model.get("payload_hex", ""))
    return cdb, payload


def trigger_cdb(source: int, selector: int) -> list[int]:
    if not 0 <= source <= 0xFFFFFF:
        raise ValueError("source must fit 24 bits")
    if not 0 <= selector <= 0xFF:
        raise ValueError("selector must fit one byte")
    return [
        0x12,
        0x00,
        0x00,
        0x00,
        0xF0,
        0x40,
        (source >> 8) & 0xFF,
        source & 0xFF,
        0xEA,
        selector,
        (source >> 16) & 0xFF,
        0x00,
    ]


def read_gateway_chunk(
    *,
    args: argparse.Namespace,
    address: int,
    length: int,
    response_offset: int = 0x20,
) -> tuple[bytes, list[dict[str, Any]]]:
    if length < 1:
        return b"", []
    if address + length > 0x1000000:
        raise ValueError("gateway read crosses address space")
    data = bytearray()
    records: list[dict[str, Any]] = []
    remaining = length
    cur = address
    chunk_size = min(args.gateway_chunk_size, 0x7F)
    while remaining:
        take = min(chunk_size, remaining)
        request_address = cur
        request_len = take
        drop = 0
        if args.discard_stale_first and cur > 0:
            request_address = cur - 1
            request_len = take + 1
            drop = 1
        base = request_address & ~0x3F
        selector = request_address & 0x3F
        cdb = [
            0x12,
            0x00,
            0x00,
            0x00,
            0xF0,
            0x40 | selector,
            0x00,
            (base >> 16) & 0xFF,
            (base >> 8) & 0xFF,
            base & 0xFF,
            0x00,
            0x00,
        ]
        item = sg_raw(
            sg_raw_path=args.sg_raw,
            device=args.device,
            cdb=cdb,
            request_len=args.request_len,
            timeout=args.timeout,
        )
        stdout = item.pop("stdout")
        item.update(
            {
                "gateway_address": cur,
                "request_address": request_address,
                "request_length": request_len,
                "drop_prefix": drop,
            }
        )
        if item["returncode"] != 0:
            raise RuntimeError(f"gateway read failed at 0x{cur:06x}: {item['stderr'].strip()}")
        end = response_offset + request_len
        if len(stdout) < end:
            raise RuntimeError(f"short gateway response at 0x{cur:06x}: need {end}, got {len(stdout)}")
        chunk = stdout[response_offset:end]
        if drop:
            item["discarded_stale_first_byte"] = chunk[0]
            chunk = chunk[1:]
        data.extend(chunk)
        records.append(item)
        cur += take
        remaining -= take
    return bytes(data), records


def write_gateway_bands(args: argparse.Namespace, out_dir: Path) -> list[dict[str, Any]]:
    band_dir = out_dir / "gateway-band"
    band_dir.mkdir(parents=True, exist_ok=True)
    reports = []
    for start, length in args.gateway_bands:
        remaining = length
        cur = start
        while remaining:
            take = min(args.band_file_size, remaining)
            blob, records = read_gateway_chunk(args=args, address=cur, length=take)
            bin_path = band_dir / f"{cur:06x}.bin"
            json_path = band_dir / f"{cur:06x}.json"
            bin_path.write_bytes(blob)
            report = {
                "gateway_address": cur,
                "length": take,
                "path": str(bin_path),
                "sha256": sha256_hex(blob),
                "nonzero": blob != b"\x00" * len(blob),
                "ascii_preview": ascii_preview(blob[:0x80]),
                "records": records,
            }
            json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            reports.append({k: v for k, v in report.items() if k != "records"})
            cur += take
            remaining -= take
    return reports


def parse_sources(args: argparse.Namespace) -> list[int]:
    sources: list[int] = []
    if args.source:
        sources.extend(args.source)
    if args.source_start is not None:
        if args.source_end is None:
            raise ValueError("--source-end is required with --source-start")
        cur = args.source_start
        while cur <= args.source_end:
            sources.append(cur)
            cur += args.source_step
    if args.source_file:
        for line in args.source_file.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                sources.append(int(line, 0))
    out: list[int] = []
    seen = set()
    for source in sources:
        if source not in seen:
            if not 0 <= source <= 0xFFFFFF:
                raise ValueError(f"source out of range: 0x{source:x}")
            seen.add(source)
            out.append(source)
    if not out:
        raise ValueError("no sources requested")
    return out


def run_one_source(
    args: argparse.Namespace,
    *,
    source: int,
    sample_index: int | None = None,
    event1_cdb: list[int],
    event1_payload: bytes,
    run_dir: Path,
) -> dict[str, Any]:
    suffix = "" if sample_index is None else f"-r{sample_index:03d}"
    source_dir = run_dir / f"sel{args.selector:02x}-src-{source:06x}{suffix}"
    source_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "source": source,
        "sample_index": sample_index,
        "selector": args.selector,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_dir": str(source_dir),
    }

    if args.cycle_before:
        result["servo_before"] = pico_toggle(args)
    result["identity_before_event1"] = wait_for_ld5m(args)
    if args.wait_not_becoming_ready:
        result["tur_before_event1"] = wait_until_not_becoming_ready(args)

    if args.pre_extrainq:
        pre = sg_raw(
            sg_raw_path=args.sg_raw,
            device=args.device,
            cdb=EXTRAINQ_CDB,
            request_len=args.request_len,
            timeout=args.timeout,
        )
        pre.pop("stdout", None)
        result["pre_extrainq"] = pre

    if args.after_identity_delay:
        time.sleep(args.after_identity_delay)

    event1 = sg_raw(
        sg_raw_path=args.sg_raw,
        device=args.device,
        cdb=event1_cdb,
        payload=event1_payload,
        timeout=args.write_timeout,
    )
    event1.pop("stdout", None)
    result["event1"] = event1
    if event1["returncode"] != 0:
        raise RuntimeError(f"event1 failed for source 0x{source:06x}: {event1['stderr'].strip()}")

    if args.post_event1_identity:
        result["identity_after_event1"] = capture_identity(args)

    time.sleep(args.after_event1_delay)

    trigger = sg_raw(
        sg_raw_path=args.sg_raw,
        device=args.device,
        cdb=trigger_cdb(source, args.selector),
        request_len=args.request_len,
        timeout=args.timeout,
    )
    trigger_stdout = trigger.pop("stdout")
    (source_dir / "trigger-response.bin").write_bytes(trigger_stdout)
    result["trigger"] = trigger
    result["trigger_marker"] = trigger_stdout[0x20] if len(trigger_stdout) > 0x20 else None
    if trigger["returncode"] != 0:
        raise RuntimeError(f"trigger failed for source 0x{source:06x}: {trigger['stderr'].strip()}")
    time.sleep(args.after_trigger_delay)

    result["gateway_bands"] = write_gateway_bands(args, source_dir)

    if args.cycle_after:
        result["servo_after"] = pico_toggle(args)
        result["identity_after_cycle"] = wait_for_ld5m(args)
    else:
        try:
            result["identity_after_no_cycle"] = capture_identity(args)
        except Exception as exc:  # noqa: BLE001
            result["identity_after_no_cycle_error"] = f"{type(exc).__name__}: {exc}"

    result["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (source_dir / "source-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--run-name", default="")
    parser.add_argument("--selector", type=parse_int, default=0x22)
    parser.add_argument("--source", type=parse_int, action="append", help="single source offset; repeatable")
    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--source-start", type=parse_int)
    parser.add_argument("--source-end", type=parse_int)
    parser.add_argument("--source-step", type=parse_int, default=0x1000)
    parser.add_argument(
        "--samples-per-source",
        type=parse_int,
        default=1,
        help="repeat each requested source this many times, using separate -rNNN directories",
    )
    parser.add_argument(
        "--gateway-band",
        dest="gateway_bands",
        type=parse_band,
        action="append",
        default=[],
        help="controller band START:LENGTH; repeatable",
    )
    parser.add_argument("--band-file-size", type=parse_int, default=0x1000)
    parser.add_argument("--gateway-chunk-size", type=parse_int, default=0x7F)
    parser.add_argument("--request-len", type=parse_int, default=176)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--write-timeout", type=int, default=20)
    parser.add_argument("--pico-port", default=DEFAULT_PICO_PORT)
    parser.add_argument("--servo-hold-ms", type=int, default=1500)
    parser.add_argument("--pico-timeout", type=float, default=8.0)
    parser.add_argument("--wait-timeout", type=float, default=45.0)
    parser.add_argument("--wait-interval", type=float, default=1.0)
    parser.add_argument(
        "--wait-not-becoming-ready",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "after LD5M identity appears, poll TEST UNIT READY until the transient "
            "'logical unit is in process of becoming ready' state clears"
        ),
    )
    parser.add_argument(
        "--identity-standard-only",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="during readiness waits, use only standard INQUIRY; avoids EXTRAINQ priming",
    )
    parser.add_argument("--after-identity-delay", type=float, default=0.0)
    parser.add_argument(
        "--post-event1-identity",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="after currentboot event1, read standard INQUIRY and EXTRAINQ before selector trigger",
    )
    parser.add_argument("--after-event1-delay", type=float, default=0.5)
    parser.add_argument("--after-trigger-delay", type=float, default=0.2)
    parser.add_argument("--cycle-before", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--cycle-after", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--pre-extrainq", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--discard-stale-first", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--continue-on-error", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    if not args.gateway_bands:
        args.gateway_bands = [(0x070000, 0x11000), (0x400000, 0x1000)]
    if not 1 <= args.gateway_chunk_size <= 0x7F:
        raise ValueError("--gateway-chunk-size must be 1..0x7f")
    if args.band_file_size <= 0:
        raise ValueError("--band-file-size must be positive")
    if args.source_step <= 0:
        raise ValueError("--source-step must be positive")
    if args.samples_per_source <= 0:
        raise ValueError("--samples-per-source must be positive")
    return args


def main() -> int:
    args = parse_args()
    event1_cdb, event1_payload = load_event1(args.candidate)
    sources = parse_sources(args)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_name = args.run_name or f"drive3-currentboot-cdd-111a-harvest-{stamp}"
    run_dir = args.out_root / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "run_name": run_name,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": str(args.candidate),
        "event1_cdb": cdb_text(event1_cdb),
        "event1_payload_sha256": sha256_hex(event1_payload),
        "selector": args.selector,
        "sources": sources,
        "samples_per_source": args.samples_per_source,
        "gateway_bands": [{"start": start, "length": length} for start, length in args.gateway_bands],
        "results": [],
        "errors": [],
    }
    manifest_path = run_dir / "harvest-manifest.json"

    total = len(sources) * args.samples_per_source
    item_index = 0
    for source in sources:
        for repeat_index in range(args.samples_per_source):
            item_index += 1
            sample_index = repeat_index if args.samples_per_source > 1 else None
            repeat_text = "" if sample_index is None else f" repeat={repeat_index + 1}/{args.samples_per_source}"
            print(
                f"[{item_index}/{total}] selector=0x{args.selector:02x} source=0x{source:06x}{repeat_text}",
                flush=True,
            )
            try:
                result = run_one_source(
                    args,
                    source=source,
                    sample_index=sample_index,
                    event1_cdb=event1_cdb,
                    event1_payload=event1_payload,
                    run_dir=run_dir,
                )
                manifest["results"].append(
                    {
                        "source": source,
                        "sample_index": sample_index,
                        "source_dir": result["source_dir"],
                        "trigger_marker": result.get("trigger_marker"),
                        "gateway_bands": result.get("gateway_bands", []),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                error = {
                    "source": source,
                    "sample_index": sample_index,
                    "error": f"{type(exc).__name__}: {exc}",
                    "at_utc": datetime.now(timezone.utc).isoformat(),
                }
                print(f"error source=0x{source:06x}: {error['error']}", file=sys.stderr, flush=True)
                manifest["errors"].append(error)
                if args.continue_on_error:
                    try:
                        error["servo_after_error"] = pico_toggle(args)
                        error["identity_after_error_cycle"] = wait_for_ld5m(args)
                    except Exception as recovery_exc:  # noqa: BLE001
                        error["post_error_cycle_failed"] = f"{type(recovery_exc).__name__}: {recovery_exc}"
                        manifest_path.write_text(
                            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8",
                        )
                        return 2
                else:
                    manifest_path.write_text(
                        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
                    return 1
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0 if not manifest["errors"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130)
