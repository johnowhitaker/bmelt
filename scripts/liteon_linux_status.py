#!/usr/bin/env python3
"""List Linux sg devices and identify the PLDS/LiteOn optical target."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def read_text(path: Path) -> str:
    try:
        return path.read_text(errors="replace").strip()
    except OSError:
        return ""


def list_sg() -> list[dict[str, str]]:
    devices = []
    for sg_dir in sorted(Path("/sys/class/scsi_generic").glob("sg*")):
        device_dir = sg_dir / "device"
        devices.append(
            {
                "sg": f"/dev/{sg_dir.name}",
                "vendor": read_text(device_dir / "vendor"),
                "model": read_text(device_dir / "model"),
                "rev": read_text(device_dir / "rev"),
                "type": read_text(device_dir / "type"),
            }
        )
    return devices


def sg_inq(device: str, timeout: int) -> str:
    proc = subprocess.run(
        ["sg_inq", device],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if proc.returncode:
        return proc.stderr.decode("utf-8", "replace").strip()
    stdout = proc.stdout.decode("utf-8", "replace")
    lines = []
    for line in stdout.splitlines():
        if any(label in line for label in ("Vendor identification", "Product identification", "Product revision")):
            lines.append(line.strip())
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-inq", action="store_true", help="only use sysfs, do not call sg_inq")
    parser.add_argument("--timeout", type=int, default=5)
    args = parser.parse_args()

    devices = list_sg()
    if not devices:
        print("no /dev/sg* devices found")
        return 1

    for item in devices:
        marker = ""
        if item["vendor"].strip() == "PLDS" or "DS-8ABSH" in item["model"]:
            marker = "  <-- optical target"
        print(
            f"{item['sg']}: vendor={item['vendor']!r} model={item['model']!r} "
            f"rev={item['rev']!r} type={item['type']!r}{marker}"
        )
        if not args.no_inq:
            detail = sg_inq(item["sg"], args.timeout)
            if detail:
                for line in detail.splitlines():
                    print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
