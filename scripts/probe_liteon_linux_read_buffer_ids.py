#!/usr/bin/env python3
"""Map LiteOn READ BUFFER mode=1 IDs via Linux sg_raw."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def cdb_text(cdb: list[int]) -> str:
    return " ".join(f"{byte:02X}" for byte in cdb)


def read_buffer_cdb(buffer_id: int, offset: int, length: int) -> list[int]:
    return [
        0x3C,
        0x01,
        buffer_id & 0xFF,
        (offset >> 16) & 0xFF,
        (offset >> 8) & 0xFF,
        offset & 0xFF,
        (length >> 16) & 0xFF,
        (length >> 8) & 0xFF,
        length & 0xFF,
        0x00,
    ]


def run_read(sg_raw: str, device: str, cdb: list[int], length: int, timeout: int) -> dict[str, Any]:
    cmd = [sg_raw, "-b", "--request", str(length), "--timeout", str(timeout)]
    cmd.extend([device, *[f"{byte:02x}" for byte in cdb]])
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout = proc.stdout
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return {
        "cmd": cmd,
        "cdb": cdb_text(cdb),
        "request_len": length,
        "returncode": proc.returncode,
        "stdout_len": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest() if stdout else None,
        "stdout_first64_hex": stdout[:64].hex(),
        "stdout_hex": stdout.hex() if len(stdout) <= 0x100 else None,
        "stderr": stderr,
        "good": proc.returncode == 0 and "SCSI Status: Good" in stderr,
    }


def standard_cases() -> list[dict[str, int | str]]:
    return [
        {"name": "id01_offset_000000_len40", "id": 0x01, "offset": 0x000000, "length": 0x40},
        {"name": "id01_offset_000030_len10", "id": 0x01, "offset": 0x000030, "length": 0x10},
        {"name": "id01_offset_000738_len20", "id": 0x01, "offset": 0x000738, "length": 0x20},
        {"name": "id01_offset_000748_len10", "id": 0x01, "offset": 0x000748, "length": 0x10},
        {"name": "id01_offset_010030_len10", "id": 0x01, "offset": 0x010030, "length": 0x10},
        {"name": "id01_offset_06b348_len10", "id": 0x01, "offset": 0x06B348, "length": 0x10},
        {"name": "id02_offset_000030_len10", "id": 0x02, "offset": 0x000030, "length": 0x10},
        {"name": "id_e2_offset_000000_len20", "id": 0xE2, "offset": 0x000000, "length": 0x20},
        {"name": "id_f1_offset_000000_len80", "id": 0xF1, "offset": 0x000000, "length": 0x80},
        {"name": "id_f1_offset_000000_len0b60", "id": 0xF1, "offset": 0x000000, "length": 0x0B60},
        {"name": "id_f0_offset_000000_len40", "id": 0xF0, "offset": 0x000000, "length": 0x40},
        {"name": "id_f0_offset_000000_len80", "id": 0xF0, "offset": 0x000000, "length": 0x80},
        {"name": "id_f0_offset_000000_len100", "id": 0xF0, "offset": 0x000000, "length": 0x100},
        {"name": "id_f0_offset_000000_len1000", "id": 0xF0, "offset": 0x000000, "length": 0x1000},
    ]


def controller_status_cases() -> list[dict[str, int | str]]:
    """Extra read-only offsets near the internal finalizer status buffers."""

    rows: list[dict[str, int | str]] = []
    # The 24-bit READ BUFFER offset is not just an xdata-like address on the
    # generic id01/id02 path: static tracing shows the high byte can select the
    # controller command namespace. Keep the 0x008xxx cases for the original
    # xdata-window hypothesis, and add 0x018xxx cases for controller 01:8xxx.
    for buffer_id in (0x01, 0x02, 0xE2, 0xF1):
        prefix = f"id{buffer_id:02x}"
        rows.extend(
            [
                {
                    "name": f"{prefix}_offset_007ff0_len40",
                    "id": buffer_id,
                    "offset": 0x007FF0,
                    "length": 0x40,
                },
                {
                    "name": f"{prefix}_offset_008000_len40",
                    "id": buffer_id,
                    "offset": 0x008000,
                    "length": 0x40,
                },
                {
                    "name": f"{prefix}_offset_008004_len20",
                    "id": buffer_id,
                    "offset": 0x008004,
                    "length": 0x20,
                },
                {
                    "name": f"{prefix}_offset_008006_len80",
                    "id": buffer_id,
                    "offset": 0x008006,
                    "length": 0x80,
                },
                {
                    "name": f"{prefix}_offset_008100_len80",
                    "id": buffer_id,
                    "offset": 0x008100,
                    "length": 0x80,
                },
                {
                    "name": f"{prefix}_offset_00810e_len40",
                    "id": buffer_id,
                    "offset": 0x00810E,
                    "length": 0x40,
                },
                {
                    "name": f"{prefix}_offset_00818a_len20",
                    "id": buffer_id,
                    "offset": 0x00818A,
                    "length": 0x20,
                },
            ]
        )
        if buffer_id in (0x01, 0x02):
            rows.extend(
                [
                    {
                        "name": f"{prefix}_offset_017ff0_len40",
                        "id": buffer_id,
                        "offset": 0x017FF0,
                        "length": 0x40,
                    },
                    {
                        "name": f"{prefix}_offset_018000_len40",
                        "id": buffer_id,
                        "offset": 0x018000,
                        "length": 0x40,
                    },
                    {
                        "name": f"{prefix}_offset_018004_len20",
                        "id": buffer_id,
                        "offset": 0x018004,
                        "length": 0x20,
                    },
                    {
                        "name": f"{prefix}_offset_018006_len80",
                        "id": buffer_id,
                        "offset": 0x018006,
                        "length": 0x80,
                    },
                    {
                        "name": f"{prefix}_offset_018100_len80",
                        "id": buffer_id,
                        "offset": 0x018100,
                        "length": 0x80,
                    },
                    {
                        "name": f"{prefix}_offset_018600_len80",
                        "id": buffer_id,
                        "offset": 0x018600,
                        "length": 0x80,
                    },
                    {
                        "name": f"{prefix}_offset_018620_len20",
                        "id": buffer_id,
                        "offset": 0x018620,
                        "length": 0x20,
                    },
                    {
                        "name": f"{prefix}_offset_01810e_len40",
                        "id": buffer_id,
                        "offset": 0x01810E,
                        "length": 0x40,
                    },
                    {
                        "name": f"{prefix}_offset_01818a_len20",
                        "id": buffer_id,
                        "offset": 0x01818A,
                        "length": 0x20,
                    },
                ]
            )
    return rows


def parse_extra_case(text: str) -> dict[str, int | str]:
    try:
        name, buffer_id, offset, length = text.split(":", 3)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("case must be name:id:offset:length") from exc
    if not name:
        raise argparse.ArgumentTypeError("case name must be non-empty")
    return {
        "name": name,
        "id": int(buffer_id, 0),
        "offset": int(offset, 0),
        "length": int(length, 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg1")
    parser.add_argument("--sg-raw", default=shutil.which("sg_raw") or "sg_raw")
    parser.add_argument("--out-dir", type=Path, default=Path("logs/linux-read-buffer-map"))
    parser.add_argument("--timeout", type=int, default=3)
    parser.add_argument("--scan-ids", action="store_true", help="also scan all 256 IDs at offset 0 len 0x10")
    parser.add_argument(
        "--include-controller-status",
        action="store_true",
        help="also sample xdata-style 0x008xxx windows and id01/id02 controller 01:8xxx windows",
    )
    parser.add_argument(
        "--only-extra",
        action="store_true",
        help="skip the standard case set and run only controller-status and --extra-case probes",
    )
    parser.add_argument(
        "--extra-case",
        action="append",
        type=parse_extra_case,
        default=[],
        metavar="NAME:ID:OFFSET:LENGTH",
        help="additional READ BUFFER mode=1 case, values may be decimal or 0x-prefixed",
    )
    args = parser.parse_args()

    run_id = datetime.now(timezone.utc).strftime("linux-read-buffer-map-%Y%m%dT%H%M%SZ")
    out_dir = args.out_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {"run_id": run_id, "device": args.device, "commands": {}}

    cases: list[dict[str, int | str]] = []
    if not args.only_extra:
        cases.extend(standard_cases())
    if args.include_controller_status:
        cases.extend(controller_status_cases())
    cases.extend(args.extra_case)

    for case in cases:
        cdb = read_buffer_cdb(int(case["id"]), int(case["offset"]), int(case["length"]))
        result["commands"][str(case["name"])] = run_read(
            args.sg_raw,
            args.device,
            cdb,
            int(case["length"]),
            args.timeout,
        )

    if args.scan_ids:
        scan: dict[str, Any] = {}
        for buffer_id in range(256):
            cdb = read_buffer_cdb(buffer_id, 0, 0x10)
            item = run_read(args.sg_raw, args.device, cdb, 0x10, args.timeout)
            if item["good"]:
                scan[f"0x{buffer_id:02x}"] = item
        result["scan_len10_good_ids"] = sorted(scan)
        result["scan_len10_good_results"] = scan

    out_path = out_dir / "read-buffer-map-result.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    for name, item in result["commands"].items():
        print(
            f"{name}: good={int(item['good'])} rc={item['returncode']} "
            f"stdout_len={item['stdout_len']} first16={item['stdout_first64_hex'][:32]}"
        )
    if args.scan_ids:
        print("scan_len10_good_ids=" + ",".join(result["scan_len10_good_ids"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
