# Drive 3 normal mailbox probes - 2026-05-04

Goal: stop treating the public normal work-window as the only possible I/O
surface and test standard normal-mode SCSI/MMC objects that can carry host data
or stable volatile state.

Drive before/after all probes:

```text
/dev/sg0: PLDS DVD+-RW DS-8ABSH LD5M
```

No firmware-update events, CDD edits, tray commands, media writes, or currentboot
entry were used in this pass.

## New harness

Added:

```text
scripts/normal_mailbox_probe.py
```

Implemented subcommands:

- `echo-buffer`: standard SCSI `WRITE BUFFER mode=0x0a` / `READ BUFFER mode=0x0a`
  echo path, with optional public work-window payload search.
- `dvd-auth`: normal MMC `REPORT KEY` / optional `SEND KEY` scaffolding. The
  opt-in send-challenge path is present but was not used because no AGID was
  granted without media.
- `mode-changeable`: read-only `MODE SENSE(10)` current/changeable page survey.
- `mode-mailbox`: one-bit volatile `MODE SELECT(10)` round trip with `PF=1`,
  `SP=0`, immediate restore, and optional work-window capture.

## Echo buffer

Evidence:

```text
references/evidence/live/normal-mailbox-echo-20260504T201130Z/
```

Probe:

```text
READ BUFFER  mode=0x0b id=0 len=4
READ BUFFER  mode=0x0b id=0 len=16
WRITE BUFFER mode=0x0a id=0 payload=5a a5 11 ee
READ BUFFER  mode=0x0a id=0 len=4
```

Result: clean negative.

Every echo descriptor/write/read command returned check condition:

```text
Sense key: Illegal Request
Additional sense: Invalid field in cdb
```

Standard INQUIRY before/after stayed stable as `PLDS DS-8ABSH LD5M`.

Conclusion: the standard echo-buffer diagnostic mailbox is not implemented, or
is blocked by this bridge/drive combination.

## REPORT KEY / SEND KEY auth path

Evidence:

```text
references/evidence/live/normal-mailbox-dvd-auth-20260504T201420Z/
```

Report-only probe:

```text
REPORT KEY key class 0, format 0  # CSS/CPPM AGID
REPORT KEY key class 0, format 5  # ASF
REPORT KEY key class 0, format 8  # RPC state
```

Result:

- AGID and ASF returned `Not Ready / Medium not present - tray closed`.
- RPC state succeeded and returned `0006000064fe0100`.
- No AGID was granted, so the tool did not send a host challenge.
- Identity stayed stable as `LD5M`.

Conclusion: this path remains interesting with media inserted, but without media
it does not provide a nonce-bearing mailbox. The harness is ready for a later
pressed-DVD test.

## MODE SENSE changeable survey

Evidence:

```text
references/evidence/live/normal-mailbox-mode-changeable-20260504T201155Z/
```

Read-only `MODE SENSE(10)` current/changeable pages:

```text
0x01 read-error recovery
0x08 caching
0x0d CD device parameters
0x0e CD audio control
0x1a power condition
0x1c fault/failure reporting
0x2a capabilities/mechanical status
0x3f all pages
```

Most pages responded normally. Page `0x1c` returned check condition, but the
drive stayed healthy.

Important candidate:

```text
page 0x08 current:    00 12 70 00 00 00 00 00 08 0a 04 00 ...
page 0x08 changeable: 00 12 70 00 00 00 00 00 08 0a 04 00 ...
```

Page byte `0x02` has changeable mask `0x04` and current value `0x04`.

## Volatile MODE SELECT round trip

Evidence:

```text
references/evidence/live/normal-mailbox-mode-select-20260504T201722Z/  # dry run
references/evidence/live/normal-mailbox-mode-select-20260504T201731Z/  # execute
references/evidence/live/normal-mailbox-mode-select-20260504T201802Z/  # execute + window snapshots
```

Probe:

```text
MODE SENSE(10) page 0x08 current
MODE SENSE(10) page 0x08 changeable
MODE SELECT(10) PF=1 SP=0 page 0x08 byte 0x02: 0x04 -> 0x00
MODE SENSE(10) page 0x08 current
MODE SELECT(10) PF=1 SP=0 restore page 0x08 byte 0x02: 0x00 -> 0x04
MODE SENSE(10) page 0x08 current
```

Result:

```text
mutate select rc=0 good=True
after mutate current target=0x00
restore select rc=0 good=True
after restore current target=0x04
roundtrip=True
identity_stable=True
```

The repeat with public work-window snapshots produced identical `0x4000`-byte
window hashes in the mutated and restored states:

```text
363eebc5d945fc7612e0ded8e7c87ad1594b8ac0021cf802d0d38d539544dfcf
```

Conclusion: this is the first clean normal-mode mailbox primitive:

- host writes a volatile bit with `MODE SELECT(10)`;
- host reads it back with `MODE SENSE(10)`;
- it restores immediately;
- no public work-window phase change was visible in the small snapshot;
- Drive #3 remains normal `LD5M`.

This is not yet a drive-internal data exfiltration channel. It is a reliable
host-controlled normal-mode state bit. That is still valuable: if we get a
normal-mode response hook or can influence a decoded runtime path, this bit can
serve as a safe host-selected mode/selector without further firmware writes.

## Current ranking after this pass

1. Use page `0x08` byte `0x02` bit `0x04` as the first normal-mode host-writable
   selector bit for future hooks.
2. Try more conservative MODE SELECT bits only if we need multiple selector
   states; page `0x08` is cleaner than mechanics/speed/power pages.
3. Revisit `REPORT KEY/SEND KEY` with known-safe media if we want a richer
   bidirectional normal command family.
4. Echo buffer is closed unless a different bridge/transport changes behavior.
5. Work-window phase remains observational only.

