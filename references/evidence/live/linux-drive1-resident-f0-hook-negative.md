# Linux Drive 1 Resident F0 Hook Probe

Date: 2026-04-30

Goal: find a host-triggerable normal-mode hook after the pre-tail/event-1
shortcut failed.

## Candidates

Two timing-only persistent F0 hooks were tested. Both used the helper-bypass
writer and the FF code cave at `0x6ee3`:

| candidate | hook | trigger | result |
|---|---:|---|---|
| `request-sense-delay20` | `0x5c72` | `REQUEST SENSE` opcode `0x03` | persisted, no timing effect |
| `inquiry-delay20` | `0x4ec6` | `INQUIRY` opcode `0x12` | persisted, no timing effect |

The patch shape was:

```text
hook:
  LJMP 0x6ee3

cave:
  delay loop, count 0x20
  original overwritten 3 bytes
  LJMP hook+3
```

Both patches intentionally touched sectors `0x04..0x06`, avoiding the more
delicate sectors `0x00..0x03`.

## Reset Attempts

After each candidate, timing was checked before and after host-visible reset
attempts:

- SCSI device reset;
- USB deauthorize/reauthorize of the bridge;
- full reboot of `jonathan-thinkpad-t480s`.

The optical LUN reappeared as `LD5M`, but command timing stayed around ordinary
single-digit milliseconds.

## Persistence Verification

The hooks were not hypothetical. Delayed `READ BUFFER F0` showed the modified
bytes in flash:

```text
0x4ec6: 90 81 8b -> 02 6e e3
0x5c72: 90 81 8e -> 02 6e e3
0x6ee3: ff...    -> delay stub + original bytes + LJMP resume
```

After the negative result, a restore candidate rewrote the same sectors back to
stock. A final delayed F0 read over `0x0000..0x7000` matched stock LD5M exactly:

```text
diff_count = 0
```

## Interpretation

The visible F0 prefix can be persistently modified, but these standard host
commands do not execute the patched bytes in normal LD5M mode. That points to
one of these models:

- normal-mode SCSI command handling is running from another ROM/RAM/controller
  image, not directly from this F0 prefix;
- these particular standard commands are handled by a bridge/controller path
  before reaching the visible 8051 handlers;
- the visible prefix is more relevant to currentboot/update/fallback than to
  ordinary post-boot command dispatch.

The practical consequence is that a naive persistent F0 resident hook is not
the quick route to decoded CDD reads. The next runtime route needs either a
live RAM/overlay hook or a hardware-visible signal path.
