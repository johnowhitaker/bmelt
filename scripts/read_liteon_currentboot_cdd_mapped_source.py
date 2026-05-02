#!/usr/bin/env python3
"""Read mapped source/controller bytes through the currentboot response hook.

This assumes the drive is already in currentboot and has a response hook built
with one of the mapped-source variants installed. The usual workflow is:

1. install the hook with the full currentboot/helper-bypass sequence;
2. cold power-cycle the drive;
3. send only event 1/profile-tail to enter currentboot;
4. run this reader while currentboot is live.

Each INQUIRY CDB with CDB[10] == 0xe3 asks the hook to:

- pass CDB[7:9] + (CDB[5] & 0x3f) to resident helper 0x1717;
- copy xdata[0xc000..0xc01f] into response bytes 0x21..0x40;
- return marker 0xd5, 0xd6, or 0xd7 at response byte 0x20.

For the marker-0xd7 wide-window hook, the useful mapped byte is currently
xdata[0xc07f]. Use --d7-c07f-byte-oracle to read one such byte per command.

No writes are performed by this reader.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_SG_RAW = "/usr/bin/sg_raw"


def parse_int(value: str) -> int:
    parsed = int(value, 0)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be non-negative")
    return parsed


def ascii_preview(data: bytes) -> str:
    return "".join(chr(byte) if 0x20 <= byte < 0x7F else "." for byte in data)


def sg_raw_inquiry(
    *,
    sg_raw: str,
    device: str,
    cdb: list[int],
    timeout: int,
    request_len: int,
) -> tuple[bytes, dict[str, Any]]:
    proc = subprocess.run(
        [
            sg_raw,
            "--cmdset=1",
            "-b",
            "--timeout",
            str(timeout),
            "--request",
            str(request_len),
            device,
            *[f"{byte:02x}" for byte in cdb],
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    record: dict[str, Any] = {
        "cdb": cdb,
        "returncode": proc.returncode,
        "stdout_len": len(proc.stdout),
        "stderr": proc.stderr.decode("utf-8", "replace"),
    }
    if proc.returncode != 0:
        raise RuntimeError(f"sg_raw failed: {record['stderr'].strip()}")
    return proc.stdout, record


def address_cdb(address: int, mode_byte10: int) -> tuple[list[int], int, int]:
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError(f"controller address out of 24-bit range: 0x{address:x}")
    base = address & ~0x3F
    selector = address & 0x3F
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
        mode_byte10 & 0xFF,
        0x00,
    ]
    return cdb, base, selector


def read_mapped_source_chunk(
    *,
    sg_raw: str,
    device: str,
    address: int,
    timeout: int,
    request_len: int,
    response_offset: int,
) -> tuple[bytes, dict[str, Any]]:
    cdb, base, selector = address_cdb(address, 0xE3)
    stdout, record = sg_raw_inquiry(
        sg_raw=sg_raw,
        device=device,
        cdb=cdb,
        timeout=timeout,
        request_len=request_len,
    )
    if len(stdout) < response_offset + 0x21:
        raise RuntimeError(
            f"short INQUIRY response at 0x{address:06x}: need "
            f"{response_offset + 0x21}, got {len(stdout)}"
        )
    marker = stdout[response_offset]
    if marker == 0xD7:
        data_len = 0x80
    else:
        data_len = 0x20
    data_end = response_offset + 1 + data_len
    if len(stdout) < data_end:
        raise RuntimeError(
            f"short mapped-source INQUIRY response at 0x{address:06x}: need {data_end}, got {len(stdout)}"
        )
    data = stdout[response_offset + 1 : data_end]
    status = None
    if marker == 0xD6:
        status_end = response_offset + 0x81
        if len(stdout) < status_end:
            raise RuntimeError(
                f"short status INQUIRY response at 0x{address:06x}: need {status_end}, got {len(stdout)}"
            )
        status = stdout[response_offset + 0x21 : status_end]
    record.update(
        {
            "kind": "mapped_source",
            "address": address,
            "base": base,
            "selector": selector,
            "marker": marker,
            "bytes_hex": data.hex(),
            "status_4e80_hex": status.hex() if status is not None else None,
        }
    )
    if marker not in (0xD5, 0xD6, 0xD7):
        raise RuntimeError(f"unexpected mapped-source marker at 0x{address:06x}: 0x{marker:02x}")
    return data, record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="/dev/sg0")
    parser.add_argument("--sg-raw", default=DEFAULT_SG_RAW)
    parser.add_argument("--address", required=True, type=parse_int)
    parser.add_argument("--length", required=True, type=parse_int)
    parser.add_argument("--out", type=Path, help="write mapped source bytes to this path")
    parser.add_argument("--json-out", type=Path, help="write capture metadata to this path")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--request-len", type=int, default=176)
    parser.add_argument("--response-offset", type=parse_int, default=0x20)
    parser.add_argument(
        "--d7-c07f-byte-oracle",
        action="store_true",
        help="for marker 0xd7 wide-window hooks, append only returned xdata[0xc07f] and advance by one byte",
    )
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.length < 1:
        raise ValueError("--length must be at least 1")
    if args.address + args.length > 0x1000000:
        raise ValueError("requested range crosses the 24-bit controller address space")

    data = bytearray()
    records: list[dict[str, Any]] = []
    remaining = args.length
    address = args.address
    while remaining:
        chunk, record = read_mapped_source_chunk(
            sg_raw=args.sg_raw,
            device=args.device,
            address=address,
            timeout=args.timeout,
            request_len=args.request_len,
            response_offset=args.response_offset,
        )
        if args.d7_c07f_byte_oracle:
            if record["marker"] != 0xD7 or len(chunk) < 0x80:
                raise RuntimeError("--d7-c07f-byte-oracle requires a marker 0xd7 128-byte window response")
            oracle_byte = chunk[0x7F]
            record["oracle_source"] = "xdata_0xc07f"
            record["oracle_byte_hex"] = f"{oracle_byte:02x}"
            data.append(oracle_byte)
            take = 1
        else:
            take = min(len(chunk), remaining)
            data.extend(chunk[:take])
        record["used_len"] = take
        records.append(record)
        address += take
        remaining -= take

    blob = bytes(data)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(blob)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(
                {
                    "device": args.device,
                    "address": args.address,
                    "length": args.length,
                    "bytes_hex": blob.hex(),
                    "ascii_preview": ascii_preview(blob),
                    "records": records,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    if not args.quiet:
        print(blob.hex())
        print(ascii_preview(blob), file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
