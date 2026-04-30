# Linux Drive #1 Blank-Currentboot State After LED Probe

Date: 2026-04-30.

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- remote repo: `/home/jonathan/boastermelt`
- device during these runs: `/dev/sg0`
- drive: Linux drive #1, gutted/front-panel Pico setup

## Summary

A Pico-sampled helper code-exec run using
`led-baseline-delay-count50-r4` completed event `68` but did not return to the
ordinary `0D5C` recovery identity. Instead, standard INQUIRY and EXTRAINQ kept
the PLDS vendor/model fields while returning a zeroed or hooked revision/tail.

The final stable identity after long servo power cuts and a Linux host reboot:

```text
vendor  PLDS
model   DVD+-RW DS-8ABSH
rev     00 00 00 00
EXTRAINQ tail mostly 00, with trailing "        LD50 01 00 00 00"
```

This is a distinct failure class from the known `0D5C` currentboot state. The
known `0D5C` recovery sequence does not apply directly.

Update: this state is now recovered. The exit is a dynamic replay that treats
the blank persona as a third currentboot dialect. Its malformed EXTRAINQ does
not contain an `EXTRAINQ` marker, but bytes `0x9c..0xab` still form the active
16-byte profile-tail transport key. That slot-5 key changes after bank
boundaries, so the recovery must re-read EXTRAINQ and rebuild the `arg=0x7f`
profile tail at each boundary.

## What Triggered It

The run:

```text
runs/pico-led-probes/led-baseline-delay-count50-r4-20260430T193327Z/
```

The candidate mutates all currentboot-key profile-tail helpers so the late
helper hook at code `0x32af` jumps to a delay payload and then returns through
the helper success path:

```text
30 e6 12 -> 02 35 fa
payload -> delay loop -> LJMP 0x32c4
```

Event `68` returned GOOD. The Pico saw the LED/front-panel line rise during the
event and stay high afterward. The runner's post-sequence identity capture did
not see stock `0D5C`; it saw a corrupted/hooked revision, so its automatic
recovery refused to start.

## Recovery Attempts

The normal recovery restart was wrong for this state and failed immediately:

```text
recover_liteon_currentboot_linux.py --force
event currentboot-tail-before-bank0: rc=5, Parameter value invalid
```

A full same-image LD5M replay from event `0` also failed at the first
profile-tail write:

```text
event 0 EXTRAINQ: rc=0, in=176
event 1 profile_tail_arg7f: rc=5, Parameter value invalid
```

Continuing the original event sequence from event `69` also failed at the
profile tail. However, ordinary chunk staging still worked:

```text
event 70 arg00_chunk_transfer: rc=0
event 71 arg00_readback_verify: rc=0
```

Completing all bank-2 chunks without the tail worked through readback, but the
bank-2 pMac rejected:

```text
event 102 bank_pmac_prefix: rc=5
```

This proved blank-currentboot still had a live chunk staging/readback path, but
the profile-tail and pMac control paths were not synchronized under the known
`0D5C` key.

## Power And Host Reset

These did not restore `LD5M` or ordinary `0D5C`:

- Pico servo `+5V` cut for 8 seconds;
- Linux host reboot plus 8-second servo cut;
- explicit `ALLZ` on Pico front-panel pins plus 30-second servo cut;
- full manual unplug/replug of both Pico and drive.

The 30-second cut still returned:

```text
standard revision: 00 00 00 00
EXTRAINQ: zeroed tail, trailing "LD50"
```

The manual unplug was useful evidence: it proved the blank persona was not just
a warm USB/bridge latch. The recovery path below supersedes these reset-only
attempts.

## Non-Write Exit Pass

The old non-write recovery/status harness was run once:

```text
runs/restore/blank-mode-nonwrite-recovery-probe-20260430T195407Z/
```

All of these left revision `00 00 00 00`:

- TEST UNIT READY;
- REQUEST SENSE;
- START STOP UNIT variants;
- `PLDSVUC` unlock and lock;
- `DF 00 0D 00 00 11 ...`;
- `sg_reset --device`.

## Dynamic Recovery

The key observations after manual unplug:

- standard INQUIRY still reported `PLDS DVD+-RW DS-8ABSH` with a blank or
  garbage revision;
- EXTRAINQ returned 176 bytes without the normal `EXTRAINQ` marker;
- the tail still ended in `"        LD50 01 00 00 00"`;
- the first profile-tail candidate built from bytes `0x9c..0xab` returned
  GOOD:

```text
key = f9 ef c2 8f 20 20 20 20 20 20 20 20 4c 44 35 30
cdb = 3B 05 01 00 00 00 00 0B D0 7F 00 00
```

After that tail, bank 0 chunks and the bank-0 pMac passed. The next repeated
tail failed because the exposed key bytes had changed. Reading EXTRAINQ after
bank 0 showed a new slot-5 key:

```text
key = 90 82 52 e0 20 20 20 20 20 20 20 20 4c 44 35 30
```

Using that key rebuilt the tail and let bank 1 pass. Bank 2 is the AES-selected
bank for this profile, so its chunks and final pMac had to be regenerated under
the active slot-5 key from after bank 1:

```text
bank2 key  = 3b 28 05 97 20 20 20 20 20 20 20 20 4c 44 35 30
bank2 pMac = 1b 98 d8 75 90 79 7f 12 5e 5f 2e a3 d7 04 c5 31
```

After bank 2, the remaining banks use plain LD5M chunks but keep carrying the
bank-2 pMac at every boundary while the profile tail is rebuilt from the latest
slot-5 key before each bank.

The automated tool is:

```sh
python3 scripts/recover_liteon_blank_currentboot_linux.py --device /dev/sg0
```

For the first live recovery, banks 0..2 were proven by hand and the tool resumed
from bank 3:

```sh
python3 scripts/recover_liteon_blank_currentboot_linux.py \
  --device /dev/sg0 \
  --start-bank 3 \
  --end-bank 15 \
  --initial-pmac 1b98d87590797f125e5f2ea3d704c531
```

The run completed through bank 15 and final `PLDSVUC` with GOOD status:

```text
runs/restore/blank-dynamic-recovery/blank-dynamic-recovery-20260430T201352Z/
```

After a Pico servo cold boot:

```text
/dev/sg0: vendor='PLDS' model='DVD+-RW DS-8ABSH' rev='LD5M'
```

F0 readback after recovery does not match the original stock LD5M image because
the drive currently contains the deliberate
`currentboot-response-hook-gateway-cdb-bulk` resident hook:

```text
sha256 11df18bd19d269b959aa7c2270db96a636c27384669194ed0732c9b05e176771
diffs  0x4fc9..0x4fcb: LJMP 0x6ee3
       0x6ee3..0x6f49: gateway bulk response hook in former FF cave
```

That hash exactly matches the known candidate:

```text
references/firmware/extracted/currentboot-response-hook-candidates/
currentboot-response-hook-gateway-cdb-bulk/currentboot-response-hook-gateway-cdb-bulk/
ld5m-helper-bypass-currentboot-response-hook-gateway-cdb-bulk.bin
```

## Operational Notes

Use `scripts/recover_liteon_blank_currentboot_linux.py` first if this blank
persona recurs. Use `scripts/run_liteon_events_no_preflight.py` only for manual
experiments where INQUIRY/EXTRAINQ may themselves be hooked or stateful. It
sends selected candidate events without the usual identity capture before the
first write.

Do not continue LED/XDATA write probes from this state. Recover to `LD5M`
first, then decide whether to keep or restore any installed resident hook.
