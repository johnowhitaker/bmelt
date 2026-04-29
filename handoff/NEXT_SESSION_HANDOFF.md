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
6. `scripts/run_liteon_linux_persistence_experiment.py`
7. `scripts/build_liteon_helper_bypass_candidate.py`
8. `scripts/build_liteon_helper_codeexec_candidate.py`
9. `scripts/read_liteon_xdata_bit_channel.py`
10. `scripts/recover_liteon_currentboot_linux.py`
11. `scripts/dump_liteon_linux_f0_window.py`

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

## Current Capabilities

Live-proven:

- dump/decrypt F0 through Linux `READ BUFFER id=F0`;
- recover known `0D5C` currentboot back to `LD5M`;
- persist selected F0 bytes with the helper-status bypass;
- execute patched helper-overlay code and observe host-visible timing;
- read selected XDATA bits through event-68 GOOD vs DID_ERROR.

Still unsolved:

- the real `0xe7fe0` container seal/auth algorithm;
- a fast/general host data-return channel from helper code;
- stable normal-mode persistent F0 resident hooks.

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

## Good Next Step

Use the XDATA bit channel to map a short list of high-value registers before
adding hardware:

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
