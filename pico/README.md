# Pico DUT GPIO Controller

This directory contains the MicroPython script installed on the Raspberry Pi Pico and a small Mac-side serial client.

## Files

- `main.py`: copy to the Pico as `:main.py`. On boot it leaves GP26, GP27, and GP28 as high-impedance inputs.
- `client.py`: sends line-oriented commands over the Pico USB serial port.

## Current Drive Wiring

For the gutted DS-8ABSH front-panel board:

| Wire | Pico connection | Drive-side meaning | Current use |
|---|---|---|---|
| Blue | Pico `GND` | drive/front-panel ground reference | reference only |
| Green | `GP27` | front eject button line, normally open/high unless pressed or pulled low | safe to read; short low pulse simulates button press |
| Yellow | `GP26` | LED `+` side / LED driver candidate | read-only until the firmware GPIO path is mapped |

Do not use `GP28` for this wiring. It was used briefly as a candidate ground
before blue was moved to Pico `GND`; leave it disconnected/high-Z.

There is also a separate drive-inserted switch held closed with a rubber band.
That switch is not the GP27 front eject button, which is not being held down.
If the tray is ejected, the held-closed insert switch may confuse normal
mechanism state.

Observed idle state after blue was moved to Pico `GND`:

```text
GP27 / green button line: ~2.85-2.91 V, digital high
GP26 / yellow LED line:   ~1.02-1.24 V, digital low
```

`SET GP27 LOW` pulls the button line to ~0 V and `SET GP27 Z` releases it back
high. The drive remained enumerated as `LD5M` after a short GP27 low pulse.

## Serial

- Baud: `921600`
- Responses: one JSON object per line
- Pins: `GP26`, `GP27`, `GP28`

## Commands

```text
PING
READ ALL
READ GP26
STATE ALL
SET GP26 Z
SET GP26 LOW
SET GP26 HIGH
RELEASE GP26
ALLZ
```

Use `Z`, `RELEASE`, or `ALLZ` to return pins to high impedance. The Pico starts in `Z` for all three pins after every boot.

## Host Example

```sh
python3 pico/client.py "PING" "STATE ALL" "READ ALL"
python3 pico/client.py "READ GP27" "SET GP27 LOW" "READ GP27" "SET GP27 Z"
```

## Install Example

```sh
python3 -m mpremote connect /dev/cu.usbmodem2101 fs cp pico/main.py :main.py + reset
```
