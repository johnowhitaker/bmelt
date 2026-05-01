# Normal START STOP Variant Matrix

Date: 2026-05-01
Host: `jonathan-thinkpad-t480s`
Drive: `PLDS DVD+-RW DS-8ABSH LD5M`

Evidence directories:

```text
references/evidence/live/normal-start-stop-stop-20260501/
references/evidence/live/normal-start-stop-start-20260501/
references/evidence/live/normal-start-stop-eject-delayed-20260501/
references/evidence/live/normal-start-stop-load-20260501/
```

This run compares the four ordinary START STOP UNIT control-byte low-nibble
variants. It is the live counterpart to the static `+0x8bxx` branch that checks
`xdata[0x8a49] == 0x1b` and `(xdata[0x8a4d] & 0x0f) == 0x02`.

## Summary

| variant | CDB | meaning | sg_raw result | elapsed | post-window failures | sense / status |
|---|---|---|---:|---:|---:|---|
| stop | `1B 00 00 00 00 00` | `START=0 LOEJ=0` | rc `2`, CHECK | `0.011439s` | 0 | Not Ready, medium not present, tray closed |
| start | `1B 00 00 00 01 00` | `START=1 LOEJ=0` | rc `2`, CHECK | `0.011762s` | 0 | Not Ready, medium not present, tray closed |
| eject | `1B 00 00 00 02 00` | `START=0 LOEJ=1` | rc `99`, DID_TIME_OUT | `4.283215s` | 2 | Later REQUEST SENSE clean; MECHANISM STATUS all zero |
| load | `1B 00 00 00 03 00` | `START=1 LOEJ=1` | rc `5`, CHECK | `0.012046s` | 0 | Illegal Request, invalid field in CDB |

All runs ended with `/dev/sg0` still identifying as normal `LD5M`.

## Interpretation

The exact low nibble `0x02` is special on this drive state. It is the only
variant that caused visible motion, a multi-second host timeout, and temporary
unavailability of the public `READ BUFFER id=01` work window.

The other three variants returned quickly:

- `stop` and `start` failed as "medium not present - tray closed";
- `load` failed as "invalid field in CDB";
- all post-command work-window captures succeeded;
- mechanism status before/after was `00 00 00 00 00 00 00 00`.

That lines up tightly with the static branch:

```text
90 8a 49 e0 64 1b 70 27      ; opcode must be START STOP UNIT
90 8a 4d e0 54 0f ff bf 02   ; low control nibble must be 0x02
```

The branch is not merely "generic START STOP." It is specifically the eject
case.

## Practical Consequences

For future mechanics experiments:

- use `eject` as the host-visible trigger when we need to reach this path;
- expect a several-second busy period where immediate `READ BUFFER id=01`
  capture may time out;
- do not interpret that timeout as currentboot or permanent loss if delayed
  INQUIRY/REQUEST SENSE recovers;
- use `stop`, `start`, and `load` as low-risk contrast commands when looking
  for generic START STOP dispatcher chunks.

For future hooks:

- the state telemetry should focus on the `0x02` branch, not the broader opcode
  handler;
- useful state bytes remain `0x8a49`, `0x8a4d`, `0x8a2d`, `0x8a34`, `0x480e`,
  `0x48a5`, `0x4762`, `0x4860`, `0x4864`, `0x5905`, and `0x5a01`;
- any hook that returns data to the host through SCSI should avoid relying on
  an immediate post-eject READ BUFFER transfer, because that path is busy during
  exactly the window we care about.
