#!/usr/bin/env python3
"""Summarize normal-runtime packet-shadow selector/field checks."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from analyze_liteon_normal_packet_shadow import (
    CONTROLLER_REGS,
    DEFAULT_TARGETS,
    aggregate,
    load_windows,
    scan_compares,
    snippet,
)


SCSI_OPS = {
    0x00: ("TEST UNIT READY", "read/status"),
    0x03: ("REQUEST SENSE", "read/status"),
    0x12: ("INQUIRY", "read/status"),
    0x13: ("VERIFY(6) / legacy", "unknown"),
    0x1B: ("START STOP UNIT", "mechanical"),
    0x23: ("READ FORMAT CAPACITIES", "read/status"),
    0x25: ("READ CAPACITY(10)", "read/status"),
    0x28: ("READ(10)", "read/data"),
    0x2A: ("WRITE(10)", "write/data"),
    0x43: ("READ TOC/PMA/ATIP", "read/status"),
    0x46: ("GET CONFIGURATION", "read/status"),
    0x4A: ("GET EVENT STATUS NOTIFICATION", "read/status"),
    0x51: ("READ DISC INFORMATION", "read/status"),
    0x52: ("READ TRACK INFORMATION", "read/status"),
    0x55: ("MODE SELECT(10)", "write/config"),
    0x5A: ("MODE SENSE(10)", "read/status"),
    0x6B: ("Vendor / blank-like opcode", "unknown"),
    0x78: ("Vendor / DVD command-class opcode", "unknown"),
    0xA1: ("BLANK / vendor-adjacent", "write/media"),
    0xA3: ("SEND KEY / MMC security", "write/control"),
    0xA4: ("REPORT KEY / MMC security", "read/control"),
    0xA8: ("READ(12)", "read/data"),
    0xB4: ("READ ELEMENT STATUS ATTACHED / vendor", "read/status"),
    0xBD: ("MECHANISM STATUS", "read/status"),
    0xBE: ("READ CD", "read/data"),
    0xCF: ("Vendor-specific", "unknown"),
    0xE3: ("LiteOn/vendor", "vendor"),
    0xE6: ("LiteOn/vendor", "vendor"),
    0xE7: ("LiteOn/vendor", "vendor"),
}

SHADOW_BYTES = {
    0x8A49: "opcode/selector candidate",
    0x8A4A: "CDB byte 1 / op-specific field",
    0x8A4B: "CDB byte 2 / op-specific field",
    0x8A4C: "controller setup high-ish byte",
    0x8A4D: "length/count-ish byte",
    0x8A4E: "subselector/status byte; low nibble tested",
    0x8A4F: "payload/field byte",
    0x8A50: "payload/field byte",
    0x8A51: "payload/field byte",
    0x8A52: "payload/field byte",
    0x8A53: "controller response/data shadow byte",
    0x8A54: "controller response/data shadow byte",
}


def opcode_name(value: int) -> str:
    return SCSI_OPS.get(value, ("unknown/vendor", "unknown"))[0]


def opcode_class(value: int) -> str:
    return SCSI_OPS.get(value, ("unknown/vendor", "unknown"))[1]


def capture_label(path_stem: str) -> str:
    parts = path_stem.split("-", 1)
    return parts[1] if len(parts) == 2 else path_stem


def summarize_compares(run_dirs: list[Path]) -> dict[str, Any]:
    rows: dict[tuple[int, str, int, str], dict[str, Any]] = {}
    addr_values: dict[int, Counter[int]] = defaultdict(Counter)

    for win in load_windows(run_dirs):
        data = win["data"]
        label = f"{win['run']}/{win['capture']}"
        stimulus = capture_label(win["capture"])
        for compare in scan_compares(data):
            addr = int(compare["addr"])
            if not 0x8A49 <= addr <= 0x8A54:
                continue
            value = int(compare["value"])
            key = (addr, str(compare["kind"]), value, str(compare["branch"]))
            row = rows.setdefault(
                key,
                {
                    "addr": addr,
                    "role": SHADOW_BYTES.get(addr, ""),
                    "kind": compare["kind"],
                    "value": value,
                    "branch": compare["branch"],
                    "count": 0,
                    "offsets": Counter(),
                    "stimuli": Counter(),
                    "samples": [],
                },
            )
            row["count"] += 1
            row["offsets"][(int(compare["offset"]) // 0x40) * 0x40] += 1
            row["stimuli"][stimulus] += 1
            if len(row["samples"]) < 4:
                start, text = snippet(data, int(compare["offset"]), before=12, after=36)
                row["samples"].append(
                    {
                        "capture": label,
                        "offset": start,
                        "hex": text,
                    }
                )
            addr_values[addr][value] += 1

    compare_rows = list(rows.values())
    compare_rows.sort(key=lambda row: (row["addr"], -row["count"], row["value"], row["kind"]))

    by_addr = []
    for addr in range(0x8A49, 0x8A55):
        values = addr_values.get(addr, Counter())
        by_addr.append(
            {
                "addr": addr,
                "role": SHADOW_BYTES.get(addr, ""),
                "values": [{"value": value, "count": count} for value, count in values.most_common()],
                "unique_values": len(values),
                "total": sum(values.values()),
            }
        )

    return {"compare_rows": compare_rows, "by_addr": by_addr}


def compact_counter(counter: Counter[Any], limit: int = 6) -> list[dict[str, Any]]:
    return [{"value": key, "count": value} for key, value in counter.most_common(limit)]


def summarize_shadow_edges(shadow_report: dict[str, Any]) -> dict[str, Any]:
    edges_by_addr: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in shadow_report.get("copy_edges", []):
        src = int(edge["src"])
        dst = int(edge["dst"])
        if 0x8A49 <= src <= 0x8A54 or 0x8A49 <= dst <= 0x8A54:
            edges_by_addr[src].append(edge)
            edges_by_addr[dst].append(edge)

    rows = []
    for addr in range(0x8A49, 0x8A55):
        edges = sorted(edges_by_addr.get(addr, []), key=lambda row: -int(row["count"]))[:10]
        rows.append(
            {
                "addr": addr,
                "role": SHADOW_BYTES.get(addr, ""),
                "edges": edges,
            }
        )
    return {"edge_rows": rows}


def edge_text(edge: dict[str, Any]) -> str:
    src = int(edge["src"])
    dst = int(edge["dst"])
    count = int(edge["count"])
    if src in CONTROLLER_REGS or dst in CONTROLLER_REGS:
        tag = "ctrl"
    elif src == 0x47B1 or dst == 0x47B1:
        tag = "fifo"
    else:
        tag = "copy"
    return f"`0x{src:04x}->0x{dst:04x}` {tag} x{count}"


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Normal Packet Selector Map",
        "",
        "This report condenses the normal-runtime packet-shadow evidence into a",
        "selector/field map. It is based on public `READ BUFFER id=01` work-window",
        "captures, so capture labels show when a code/table chunk was visible, not",
        "a proof that the named command executed that exact branch.",
        "",
        "## Summary",
        "",
        f"- captures scanned: {report['capture_count']}",
        f"- packet-shadow compare idioms: {len(report['compare_rows'])}",
        f"- packet-shadow/controller edge rows: {len(report['edge_rows'])}",
        "- `0x8a49` remains the best opcode/selector byte.",
        "- `GET CONFIGURATION` (`0x46`) tags the controller bridge dynamically,",
        "  but a plain `0x8a49 == 0x46` compare has not appeared in the public",
        "  work-window corpus. That means its route may be table-driven, handled",
        "  through an unharvested slice, or dispatched before this compare cluster.",
        "",
        "## 0x8a49 Opcode-Like Compares",
        "",
        "| value | likely meaning | class | compare forms | count | sample slots |",
        "|---:|---|---|---|---:|---|",
    ]

    opcode_rows = [row for row in report["compare_rows"] if row["addr"] == 0x8A49]
    by_value: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in opcode_rows:
        by_value[int(row["value"])].append(row)
    for value, rows in sorted(by_value.items()):
        forms = ", ".join(f"`{row['kind']}->{row['branch']}`" for row in rows)
        count = sum(int(row["count"]) for row in rows)
        offsets = sorted({off for row in rows for off in row["offsets"].keys()})
        sample_slots = ", ".join(f"`+0x{off:04x}`" for off in offsets[:8])
        lines.append(
            f"| `0x{value:02x}` | {opcode_name(value)} | {opcode_class(value)} | "
            f"{forms} | {count} | {sample_slots} |"
        )

    lines += [
        "",
        "## Adjacent Shadow Field Compares",
        "",
        "| addr | role sketch | values seen | total compares |",
        "|---:|---|---|---:|",
    ]
    for row in report["by_addr"]:
        addr = int(row["addr"])
        if addr == 0x8A49:
            continue
        values = ", ".join(
            f"`0x{item['value']:02x}` x{item['count']}" for item in row["values"][:10]
        )
        lines.append(f"| `0x{addr:04x}` | {row['role']} | {values or '-'} | {row['total']} |")

    lines += [
        "",
        "## Shadow Byte Edge Sketch",
        "",
        "| addr | role sketch | strongest observed edges |",
        "|---:|---|---|",
    ]
    for row in report["edge_rows"]:
        addr = int(row["addr"])
        edges = "; ".join(edge_text(edge) for edge in row["edges"][:7])
        lines.append(f"| `0x{addr:04x}` | {row['role']} | {edges or '-'} |")

    lines += [
        "",
        "## Practical Read",
        "",
        "- `0x8a49` is a real command-like selector, but it is not the whole story.",
        "  The visible compare cluster includes ordinary read/write opcodes, MMC",
        "  security-style opcodes, and LiteOn/vendor values. The GET CONFIG path",
        "  that currently looks most useful does not show up as a simple `0x46`",
        "  compare here.",
        "- `0x8a4d` and `0x8a4e` are still the best field-control suspects for a",
        "  future fast oracle. They are checked locally and also bridge into",
        "  `0x4012/0x4013` or `0x4099` paths.",
        "- The safest live-probe candidates remain read/status commands that already",
        "  completed cleanly: `INQUIRY`, `REQUEST SENSE`, `MODE SENSE(10)`,",
        "  `GET CONFIGURATION`, `GET EVENT STATUS`, `READ TOC`, and DVD-structure",
        "  reads. `START STOP`, write/data opcodes, and vendor/security opcodes may",
        "  be informative, but should be separated from benign read-only mapping.",
        "- A useful next live experiment is not a wider random command sweep. It is a",
        "  focused correlation run that captures the work window after controlled",
        "  field variations for one command family, then asks whether the bridge",
        "  snippets move with `0x8a4d/0x8a4e`-like length/subselector fields.",
        "",
        "## Raw Compare Rows",
        "",
        "| addr | role | value | kind | branch | count | sample slots | sample captures |",
        "|---:|---|---:|---|---|---:|---|---|",
    ]

    for row in report["compare_rows"]:
        offsets = ", ".join(f"`+0x{off:04x}`" for off in list(row["offsets"].keys())[:8])
        samples = ", ".join(f"`{sample['capture']}`" for sample in row["samples"][:2])
        lines.append(
            f"| `0x{row['addr']:04x}` | {row['role']} | `0x{row['value']:02x}` | "
            f"{row['kind']} | {row['branch']} | {row['count']} | {offsets} | {samples} |"
        )

    return "\n".join(lines) + "\n"


def make_jsonable(report: dict[str, Any]) -> dict[str, Any]:
    def convert(value: Any) -> Any:
        if isinstance(value, Counter):
            return dict(value)
        if isinstance(value, dict):
            return {str(key): convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        return value

    return convert(report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dirs", nargs="+", type=Path)
    parser.add_argument("--shadow-json", type=Path)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    selector_report = summarize_compares(args.run_dirs)
    if args.shadow_json and args.shadow_json.exists():
        shadow_report = json.loads(args.shadow_json.read_text())
    else:
        shadow_report = aggregate(args.run_dirs, set(DEFAULT_TARGETS))
    edge_report = summarize_shadow_edges(shadow_report)

    report = {
        "capture_count": len(load_windows(args.run_dirs)),
        **selector_report,
        **edge_report,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(make_jsonable(report), indent=2, sort_keys=True) + "\n")
    args.out_md.write_text(render_md(report))


if __name__ == "__main__":
    main()
