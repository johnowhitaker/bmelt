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

During helper/currentboot and recovery runs, GP26 does move and the physical LED
blinks. A Pico sampler around the Linux event-68 helper run sees GP26 swing
from near `0 mV` to about `2.0 V`, then settle high before recovery starts.

The first Pico-sampled firmware probes used the already-proven helper hook at
plain `0x02b5` / code `0x32af`. The important timing lesson was that a
post-command read only catches latched state. To avoid missing short pulses, the
current probe builder can instead jump to payload space at plain `0x0600`,
drive or rewrite a candidate value in a loop, and only then return to the normal
helper success path.

Validated timing windows:

| Probe | Event-68 behavior |
|---|---|
| baseline helper event | roughly `1.8 s` with normal LED blink pattern |
| delay payload at plain `0x0600` | roughly `2.7 s`, proving the sampled hold window executes |
| looped XDATA hold at plain `0x0600` | roughly `3.1 s`, repeatedly asserting the candidate value |

Negative LED-control probes so far:

- direct/SFR `P1.6` set and clear, including looped hold;
- XDATA `0x4023`, `0x4844`, and `0x90fc`, written as both `0x00` and `0xff`
  with looped hold;
- XDATA `0x5904`, `0x5905`, `0x59c0`, `0x5906`, `0x592a`, `0x59f0`, `0x59f1`,
  `0x5a00`, `0x5a01`, `0x5a24`, `0x5a31`, and `0x5954` in the earlier
  final-tail write probes.

Current interpretation: GP26 is definitely usable as an observed front-panel
LED line, but the tested helper-visible registers are not its latch. GP27 can
still be used as an input line if we want to map the button path and use that to
find the surrounding GPIO block.
