# Linux Drive 1 Pico Servo Power-Cycle

Date: 2026-04-30

Goal: verify that the Pico-controlled servo physically cutting the spliced USB
`+5V` line behaves like a real drive/bridge replug.

## Command

From the Mac:

```sh
python3 pico/client.py --port /dev/cu.usbmodem2101 "TOGGLE SERVO"
```

The current Pico firmware moves `GP10` right for one second, then returns it
left.

## Observed Linux State

Before toggle:

```text
sg0:PLDS:DVD+-RW DS-8ABSH:LD5M | sg1:Generic-:SD/MMC:1.00
```

During toggle:

```text
sg1:Generic-:SD/MMC:1.00
```

After power returned:

```text
sg0:PLDS:DVD+-RW DS-8ABSH:LD5M | sg1:Generic-:SD/MMC:1.00
```

The optical LUN disappeared at about `5.330s` in the monitor run and returned
at about `8.991s`, still reporting active revision `LD5M`.

## Interpretation

This is the first confirmed hands-free true power-cycle primitive. It is
stronger than Linux USB deauthorize/reauthorize, SCSI reset, or host reboot for
experiments that need the drive and bridge to lose `+5V`.

Use it before asking for a manual replug, and after risky live tests that leave
the optical LUN missing or wedged.
