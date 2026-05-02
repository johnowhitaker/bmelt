# Pico DUT GPIO Controller

This directory contains the MicroPython script installed on the Raspberry Pi Pico and a small Mac-side serial client.

## Files

- `main.py`: copy to the Pico as `:main.py`. On boot it leaves GP26, GP27, and GP28 as high-impedance inputs and sets the GP10 servo to the left position.
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

## USB Power-Cycle Servo

The current bench setup also uses a servo on Pico `GP10` to press a microswitch
that temporarily cuts the spliced USB `+5V` line. This is intentionally a
mechanical high-side switch: USB/data/front-panel grounds remain common, while
the drive/bridge loses `+5V`.

Run from the Mac:

```sh
python3 pico/client.py --port /dev/cu.usbmodem2101 "TOGGLE SERVO"
```

Run from the Linux laptop when the Pico is plugged into that host:

```sh
python3 pico/client.py --port /dev/ttyACM0 "TOGGLE SERVO"
```

If using a hold longer than the default client timeout, pass a longer timeout:

```sh
python3 pico/client.py --port /dev/ttyACM0 --timeout 8 "TOGGLE SERVO 3000"
```

The servo holds the switch for about one second, then returns to the left/rest
position. On 2026-04-30 this was verified from Linux as equivalent to a physical
replug: the optical `PLDS DVD+-RW DS-8ABSH` LUN disappeared, then reappeared as
`LD5M` a few seconds later.

Evidence:

```text
references/evidence/live/linux-drive1-pico-servo-power-cycle.md
```

## Serial

- Baud: `921600`
- Responses: one JSON object per line
- Pins: `GP26`, `GP27`, `GP28`
- Servo: `GP10`, 50 Hz PWM, 1000 us left, 2000 us right

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
TOGGLE SERVO
SERVO STATE
```

Use `Z`, `RELEASE`, or `ALLZ` to return pins to high impedance. The Pico starts in `Z` for all three pins after every boot.

`TOGGLE SERVO` moves GP10 from left to right for one second, then returns it to
left. `TOGGLE SERVO 5000` holds the switch for five seconds. `SERVO RIGHT` and
`SERVO LEFT` manually hold/release the power-cut switch for recovery testing.

## Host Example

```sh
python3 pico/client.py "PING" "STATE ALL" "READ ALL"
python3 pico/client.py "READ GP27" "SET GP27 LOW" "READ GP27" "SET GP27 Z"
python3 pico/client.py "SERVO STATE" "TOGGLE SERVO" "SERVO STATE"
python3 pico/client.py --port /dev/cu.usbmodem2101 "TOGGLE SERVO"
```

## Install Example

```sh
python3 -m mpremote connect /dev/cu.usbmodem2101 fs cp pico/main.py :main.py + reset
```
