# Normal START STOP Eject Live Test

Date: 2026-05-01
Host: `jonathan-thinkpad-t480s`
Drive: `PLDS DVD+-RW DS-8ABSH LD5M`

Evidence:

```text
references/evidence/live/normal-start-stop-eject-20260501/
references/evidence/live/normal-start-stop-eject-late-20260501/
references/evidence/live/normal-start-stop-eject-delayed-20260501/
analysis/8051/normal-start-stop-eject-late-compare-20260501.md
analysis/8051/normal-start-stop-eject-late-compare-20260501.json
```

This was the first deliberate START STOP mechanics-path probe after the
`+0x8bxx` static clue. It did not involve firmware writes or updater traffic,
but it did intentionally send a mechanical START STOP UNIT command.

## Command

The sent CDB was the eject-style START STOP variant:

```text
1B 00 00 00 02 00
```

That is `START=0`, `LOEJ=1`, matching the static branch:

```text
xdata[0x8a49] == 0x1b
(xdata[0x8a4d] & 0x0f) == 0x02
```

## Observed Result

The mechanism visibly reacted. The user observed that "the sled did the eject
dance."

Host-side behavior:

```text
baseline-before-start-stop window:
  sha256 23fb24c6c0522c211940a7f0930d05ab84de6e6a05b50bfcc84f2e22467d1a1d

start-stop-eject:
  sg_raw rc=99
  elapsed 5.173883 s
  response length 0

immediate after-window:
  READ BUFFER id=01 offset=0x070000 timed out at the first 0x400-byte chunk
```

The script version on the Linux host still aborted on the immediate capture
failure, so there is no full `summary.json` for the first run. The local script
has since been hardened to save summaries incrementally and record capture
failures instead of aborting.

## Delayed State

A delayed follow-up with no START STOP command succeeded:

```text
late baseline window:
  sha256 100d732eacdeb44ddd453510c0d3e83e6db313f26b287f1489a4990706d59f82

MECHANISM STATUS response:
  00 00 00 00 00 00 00 00

status after run:
  /dev/sg0 PLDS DVD+-RW DS-8ABSH LD5M
  /dev/sg1 Generic SD/MMC 1.00
```

So the immediate timeout appears to be a busy/mechanics-transition window, not
a persistent loss of the optical LUN or a currentboot-style wedge.

## Repeated Delayed Capture

After hardening the capture script, the same eject-style START STOP was run
again with one-second delays between post-command capture attempts:

```text
baseline-before-start-stop:
  sha256 03cf2a8e715e0b19bd458bf82eca2931879705f758e7bdb80c7638fa31cb28da

MECHANISM STATUS before:
  00 00 00 00 00 00 00 00

start-stop-eject:
  sg_raw rc=99
  elapsed 4.283215 s
  response length 0

after-start-stop-eject-00:
  READ BUFFER timed out

after-start-stop-eject-01:
  READ BUFFER timed out

after-start-stop-eject-02:
  sha256 c73dbe36d795ad97a73c8b496d2f7dd217d139646a7e32203192aecfca502804

after-start-stop-eject-03:
  sha256 144ea2659df4a0bb7dd8b54c3f60ff97ff9df5b49c615fc372a909c5bc551212

REQUEST SENSE after:
  70 00 00 00 00 00 00 0a 00 00 00 00 00 00 00 00 00 00 00 00

MECHANISM STATUS after:
  00 00 00 00 00 00 00 00

status after run:
  /dev/sg0 PLDS DVD+-RW DS-8ABSH LD5M
```

The repeated run confirms the timing behavior: at least the first couple of
post-command work-window reads can time out after visible movement, but the
normal window comes back without a power cycle.

## Interpretation

This confirms that the static START STOP branch is not just dead code or an
unrelated error-path artifact. A host-level START STOP eject CDB reaches a real
mechanics path on this drive/bridge setup.

It also shows that the public `READ BUFFER id=01` work window is not reliable
immediately during the mechanical transition. Future runs should either:

- wait longer before the first post-command capture;
- capture several post-command windows while tolerating early timeouts;
- record Pico/front-panel timing in parallel;
- pair with the servo power-cycler in case the bridge or LUN wedges.

## Static Tie-In

The live behavior supports the current model:

```text
host START STOP CDB
  -> xdata[0x8a49..] packet shadow
  -> 0x1b / low-nibble 0x02 branch
  -> state gates around 0x480e, 0x48a5, 0x4762
  -> 0x4860 / 0x4864 controller-facing mechanics state
  -> 0x5905 / 0x5a01 mechanics/servo family
  -> visible mechanism movement
```

The next useful live test is not more blind START STOP. It is a cleaner
instrumented run with the hardened capture script, longer post-command delays,
and/or a helper hook that records the state-byte set around the branch.
