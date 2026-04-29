# Linux Drive 1 Pico Front-Panel Notes

Date: 2026-04-29

Host setup:

- Optical drive on Linux host `jonathan-thinkpad-t480s`, visible as
  `PLDS DVD+-RW DS-8ABSH LD5M`.
- Pico connected to the Mac at `/dev/cu.usbmodem2101`.
- Pico firmware under `pico/main.py`; host client under `pico/client.py`.

## Wiring

The gutted drive front-panel wiring is:

| Wire | Pico | Meaning |
|---|---|---|
| Blue | `GND` | front-panel/drive ground reference |
| Green | `GP27` | front eject button line, normally open/high |
| Yellow | `GP26` | LED `+` / LED driver candidate |

The drive-inserted switch is separately held closed with a rubber band. That is
not the front eject button line; the eject button itself is not held down.

## Passive Read

With all Pico pins high-Z and blue tied to Pico ground:

```text
GP26/yellow: 1.02-1.24 V, digital 0
GP27/green: 2.85-2.90 V, digital 1
```

That matches the front eject button being normally high. A short Pico-driven
low pulse on GP27 pulled the line to about `15 mV`, then it released back high.
The drive remained enumerated as `LD5M` afterward.

Command shape:

```sh
python3 pico/client.py --port /dev/cu.usbmodem2101 \
  "ALLZ" "READ GP27" "SET GP27 LOW" "READ GP27" "SET GP27 Z" "READ GP27"
```

## LED Candidate

GP26/yellow did not move during a burst of normal INQUIRY traffic; it stayed in
the same low-ish analog range. That is not surprising if normal SCSI polling
does not blink the front LED.

Next useful firmware-side step: use the helper execution hook to test candidate
front-panel/GPIO registers and watch GP26 for a driven transition. GP27 can be
used as an input line if we need host-to-drive signaling.
