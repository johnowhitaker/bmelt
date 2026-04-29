#!/usr/bin/env python3
import argparse
import json
import time

import serial
from serial.tools import list_ports


DEFAULT_BAUD = 921600


def find_port():
    candidates = []
    for port in list_ports.comports():
        text = " ".join(
            str(value)
            for value in (port.device, port.description, port.hwid, port.manufacturer, port.product)
            if value
        )
        if "2E8A" in text.upper() or "MICROPYTHON" in text.upper() or "PICO" in text.upper():
            candidates.append(port.device)
    if candidates:
        return sorted(candidates)[0]
    for port in list_ports.comports():
        if port.device.startswith("/dev/cu.usbmodem"):
            return port.device
    raise SystemExit("No Pico serial port found. Pass --port /dev/cu.usbmodemXXXX.")


def read_json_line(ser, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        line = ser.readline()
        if not line:
            continue
        text = line.decode("utf-8", "replace").strip()
        if not text:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    raise TimeoutError("Timed out waiting for JSON response")


def run_commands(port, baud, commands, timeout):
    with serial.Serial(port, baudrate=baud, timeout=0.05, write_timeout=timeout) as ser:
        time.sleep(0.4)
        ser.reset_input_buffer()
        for command in commands:
            ser.write((command.strip() + "\n").encode("ascii"))
            ser.flush()
            print(json.dumps(read_json_line(ser, timeout), sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description="Send commands to the Pico DUT GPIO controller.")
    parser.add_argument("commands", nargs="*", default=["READ ALL"], help="Commands to send.")
    parser.add_argument("--port", default=None, help="Serial port, such as /dev/cu.usbmodem2101.")
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD, help="Host-side USB CDC baud setting.")
    parser.add_argument("--timeout", type=float, default=2.0, help="Response timeout in seconds.")
    args = parser.parse_args()

    run_commands(args.port or find_port(), args.baud, args.commands, args.timeout)


if __name__ == "__main__":
    main()
