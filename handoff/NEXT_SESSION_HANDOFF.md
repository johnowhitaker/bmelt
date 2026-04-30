# Boastermelt Next Session Handoff

Date: 2026-04-29.

This is the clean-slate handoff after the repo spring cleaning. The old
generated logs, Wine prefixes, packaged bundles, and git history were removed
from the active tree. The compact operating set is now in this repo.

## Read First

1. `docs/AI_FIELD_GUIDE.md`
2. `docs/JOURNAL.md`
3. `docs/helper-bypass-write-method.md`
4. `references/evidence/live/linux-drive1-codeexec-timing-poc.md`
5. `references/evidence/live/linux-drive1-helper-bit-channel.md`
6. `references/evidence/live/linux-drive1-helper-xdata-timing-channel.md`
7. `scripts/run_liteon_linux_persistence_experiment.py`
8. `scripts/build_liteon_helper_bypass_candidate.py`
9. `scripts/build_liteon_helper_codeexec_candidate.py`
10. `scripts/read_liteon_xdata_bit_channel.py`
11. `scripts/read_liteon_xdata_timing_channel.py`
12. `scripts/recover_liteon_currentboot_linux.py`
13. `scripts/dump_liteon_linux_f0_window.py`

## Hardware State

- Linux host: `jonathan-thinkpad-t480s`
- Remote repo: `/home/jonathan/boastermelt`
- SSH as `root` works.
- Rediscover the sg device before live work; the optical LUN moves between
  `/dev/sg0` and `/dev/sg1`.
- After cleanup, sysfs still showed `/dev/sg1` rev `0D5C`, but `sg_inq`
  reported `LD5M`; trust the active SCSI INQUIRY over stale sysfs text.
- At cleanup time, Linux drive #1 reported:

```text
PLDS / DVD+-RW DS-8ABSH / LD5M
```

Rediscover:

```sh
python3 scripts/liteon_linux_status.py
```

Power-cycle the bench drive/bridge from the Mac and wait for the Linux optical
LUN:

```sh
python3 scripts/pico_power_cycle_linux_drive.py
```

## Current Capabilities

Live-proven:

- dump/decrypt F0 through Linux `READ BUFFER id=F0`;
- recover known `0D5C` currentboot back to `LD5M`;
- persist selected F0 bytes with the helper-status bypass;
- execute patched helper-overlay code and observe host-visible timing;
- read selected XDATA bits through event-68 GOOD vs DID_ERROR;
- read selected XDATA bits through a safer GOOD/GOOD timing channel.

Still unsolved:

- the real `0xe7fe0` container seal/auth algorithm;
- a fast/general host data-return channel from helper code;
- stable normal-mode persistent F0 resident hooks.

Important 2026-04-30 update: true servo-driven `+5V` power loss did not make
the persisted F0 `INQUIRY` hook at `0x4ec6` live. Direct F0 readback showed the
patch, dmesg showed real disconnect/re-enumeration, but command timing stayed
baseline. A patched identity/profile timestamp at `0xd8ff4` also persisted in
F0 across cold boot while live EXTRAINQ stayed canonical. See:

```text
references/evidence/live/linux-drive1-servo-coldboot-persistence-map.md
```

Follow-up: patching the lower `0D5C2011` identity record at `0x4476` to `3011`
did affect currentboot EXTRAINQ after power loss and event 1. The restore write
and restore-verification run both completed: currentboot EXTRAINQ returned to
`2011/04/28`, then auto-recovery returned to `LD5M`.

## Practical Write Method

The helper-bypass write method patches the mutable `ef130045` profile-tail
helper body. The essential status bypass is:

```text
helper plain 0x02b5 / code 0x32af:
30 e6 12 -> 02 32 c4
```

Build example:

```sh
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name example-d8ff4 \
  --patch 0xd8ff4:33 \
  --include-pre-tail
```

For sectors below `0x7000`, add `--auto-helper-range` only when deliberately
touching that lower range.

Run shape:

```sh
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/helper-bypass-candidates/example-d8ff4/liteon-full-currentboot-ld5m-helper-bypass-example-d8ff4-candidate.json \
  --device /dev/sg1 \
  --skip-pre-f0 \
  --end-index 544 \
  --f0-size 0xe0000 \
  --capture-finalizer-status-after-event 1 \
  --capture-finalizer-status \
  --recover-on-currentboot
```

## Code-Execution Foothold

The current proof hooks the late helper status branch:

```text
helper plain 0x02b5 / code 0x32af:
30 e6 12 -> 02 36 1a
```

Payloads at helper code `0x361a` run a finite delay and `LJMP 0x32c4`.

Observed event-68 timings:

```text
baseline:   0.255830s
delay 0x20: 0.849545s
delay 0x80: 2.638886s
```

Event `34` and event `35` stayed flat, and auto-recovery restored `LD5M`.

Evidence:

```text
references/evidence/live/linux-drive1-codeexec-timing-poc.md
```

## XDATA Bit Channel

The same late hook can now return one bit without timing. Payload code chooses:

```text
LJMP 0x32c4  -> event 68 GOOD
LJMP 0x32b2  -> event 68 DID_ERROR, then auto-recovery restores LD5M
```

`MOVX A,@DPTR` can feed that decision. The first byte read was:

```text
xdata[0x48a0] at event 68 = 0xa0
```

Follow-up selected reads:

```text
xdata[0x47d2] = 0xff
xdata[0x48a5] = 0xff
xdata[0x8221] = 0xff
```

Evidence:

```text
references/evidence/live/linux-drive1-helper-bit-channel.md
references/evidence/live/linux-drive1-helper-xdata-48a0-summary.json
references/evidence/live/linux-drive1-helper-xdata-selected-summary.json
```

Read another byte:

```sh
python3 scripts/read_liteon_xdata_bit_channel.py \
  --device /dev/sg1 \
  --addr 0x48a0 \
  --out-dir runs/helper-xdata-bit-channel \
  --retry-attempts 2 \
  --between-delay 4
```

This is intentionally slow. It is suitable for selected registers, not bulk
memory dumps.

## XDATA Timing Channel

The GOOD/DID_ERROR channel is no longer the preferred first choice for unknown
controller registers. Claude's overnight sweep hit `xdata[0x4704].0 = 0` and
then recovery wedged until physical replug. The safer channel always returns
GOOD and encodes the bit in event-68 latency.

Use payload offset `0x04f6` for conditional timing payloads; the old
`0x0620` `Flash Type Error` string slot is too short for the 20-byte predicate.

Live calibration:

```text
no delay: 0.255969s
delay 0x20: 0.853324s
threshold: 0.554646s
```

Confirmed:

```text
xdata[0x4704] at event 68 = 0x00
xdata[0x4708] at event 68 = 0x90
xdata[0x4709] at event 68 = 0x00
xdata[0x470a] at event 68 = 0x64
xdata[0x470b] at event 68 = 0x06
```

Read shape:

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --addr 0x4704 \
  --calibrate \
  --payload-offset 0x04f6 \
  --between-delay 3
```

Evidence:

```text
references/evidence/live/linux-drive1-helper-xdata-timing-channel.md
```

## Good Next Step

Use the timing XDATA channel to map a short list of high-value registers before
adding hardware. Use the older GOOD/DID_ERROR channel only when the value is
already known not to drive a messy recovery path.

- nearby handoff/status bytes around `0x48a0`;
- controller/finalizer state bytes already seen statically, such as `0x47d2`
  and `0x8221`;
- candidate GPIO/front-panel registers before wiring the Pico into an active
  feedback loop.

If this becomes too slow or cannot see the needed state, use the Pico
front-panel wiring for a faster LED/button channel. Avoid helper-entry
trampolines; those wedged at event `68`.

## Check

```sh
make check
```

At cleanup time, `make check` passed.
