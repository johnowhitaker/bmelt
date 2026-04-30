# AI Field Guide

This is the compact technical handoff for the current clean repo. It is meant
to let a future agent start from a plugged-in LiteOn/PLDS `DS-8ABSH` drive and
reach the current helper-code execution foothold without reading the old 10GB
evidence tree.

## Hardware And Host

- Linux host: `jonathan-thinkpad-t480s`
- Remote repo path: `/home/jonathan/boastermelt`
- SSH as `root` works.
- The optical drive may appear as `/dev/sg0` or `/dev/sg1`; rediscover before
  every live run.
- Known normal identity: `PLDS DVD+-RW DS-8ABSH LD5M`.
- Known recoverable failure identity: `PLDS DVD+-RW DS-8ABSH 0D5C`.

Rediscover:

```sh
ssh root@jonathan-thinkpad-t480s 'cd /home/jonathan/boastermelt && python3 scripts/liteon_linux_status.py'
```

## Minimal Artifacts

Base image and keys:

```text
references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin
references/evidence/ld5m-extrainq-reference.log
references/evidence/live/currentboot-extrainq-after-profile-tail.hex
```

Profile-tail helper:

```text
references/firmware/extracted/liteon-official-profile-tail-ef130045-plain.bin
references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-currentboot.bin
references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-currentboot.json
references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-pretail.json
```

Currentboot/recovery candidates:

```text
references/firmware/extracted/liteon-full-currentboot-ld5m-base-candidate.json
references/firmware/extracted/liteon-same-family-boundary-probe-candidate.json
references/firmware/extracted/liteon-same-family-currentboot-continuation-candidate.json
```

8051 material:

```text
analysis/8051/ldm58051.bin
analysis/8051/ldm58051_c.c
analysis/8051/ldm58051_c.h
```

Code-execution evidence:

```text
references/evidence/live/linux-drive1-codeexec-timing-poc.md
references/evidence/live/linux-drive1-helper-bit-channel.md
references/evidence/live/linux-drive1-helper-xdata-48a0-summary.json
references/evidence/live/linux-drive1-helper-xdata-selected-summary.json
```

## Firmware Layout

For the 1 MiB LD5M F0 image:

| Range | Meaning | Notes |
|---:|---|---|
| `0x00000..0x06fef` | resident 8051/prefix/tables | low prefix is protected or skipped by helper programming |
| `0x06ff0..0x06ff3` | pre-family word | image/profile-adjacent auth-ish word |
| `0x06ff8..0x06fff` | family marker | LD5M marker area |
| `0x07000..0x0702b` | outer descriptor | describes CDD stream boundaries |
| `0x0702c..0xcec18` | CDD stream 1 | early directory/table area is dangerous |
| `0xcec18..0xd8fcf` | erased gap 1 | canonical `ff` |
| `0xd8fd0..0xd8fff` | identity/profile area | writable; not necessarily live INQUIRY source |
| `0xd9000..0xe6401` | CDD stream 2 | likely controller-consumed payload |
| `0xe6401..0xe7fdf` | erased gap 2 | canonical `ff` |
| `0xe7fe0..0xe7fed` | trailer auth14 | visible container seal material |
| `0xe7ff5..0xe7fff` | `DU8A6S` / `LITE` markers | keep intact |
| `0xe8000..0xfffff` | final erased tail | outside programmed/validated object in live tests |

Important boundaries:

- Helper normal program range starts at `0x7000`.
- Helper main object range ends at `0xe8000`.
- Low prefix changes at `0x4f81` and `0x6f80` staged but did not persist
  without helper range extension.
- CDD directory-adjacent `0x704f` caused a hard failure; avoid that area.

## Read/Dump Path

The useful read-only surface is SCSI `READ BUFFER mode=1`.

- `id=F0` returns encrypted F0 bytes.
- F0 decrypts with AES-CBC using EXTRAINQ-derived IV/key.
- The crypto reset interval is `0x80`.
- Linux reads are stable with `--chunk 0x80`.

Dump:

```sh
python3 scripts/dump_liteon_linux_f0_window.py \
  --device /dev/sg1 \
  --extrainq references/evidence/ld5m-extrainq-reference.log \
  --start 0 \
  --size 0x100000 \
  --chunk 0x80 \
  --out runs/f0/f0-decrypted.bin \
  --raw-out runs/f0/f0-raw.bin
```

## Recovery Path

Known `0D5C` currentboot recovery is live-proven. It replays the LD5M
currentboot-key sequence and returns the drive to `LD5M`.

```sh
python3 scripts/recover_liteon_currentboot_linux.py --device /dev/sg1
```

If the bridge is still visible, software recovery usually works. For the older
helper-entry wedge class, rebooting the Linux host was enough to re-enumerate
the optical LUN, then recovery worked.

## Helper-Bypass Write Method

The controller rejects arbitrary modified sealed F0 containers at finalization.
The practical bypass is to keep the currentboot flow but mutate the mutable
profile-tail helper body.

The essential helper final-status patch:

```text
helper plaintext 0x02b5 / code 0x32af:
30 e6 12 -> 02 32 c4
```

This forces the helper's final status path to report success. It has persisted
selected F0 bytes, including:

- `0xd8ff4: 32 -> 33` and restore;
- `0xd8fd8: 50 -> 40` and restore;
- `0x27d4f: 3f -> 3e` in later CDD stream 1 body;
- lower-prefix restores when helper erase/program range patches are included.

Build:

```sh
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name example \
  --patch 0xd8ff4:33 \
  --include-pre-tail
```

For lower-prefix sectors below `0x7000`, add:

```sh
--auto-helper-range
```

Run:

```sh
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/helper-bypass-candidates/example/liteon-full-currentboot-ld5m-helper-bypass-example-candidate.json \
  --device /dev/sg1 \
  --skip-pre-f0 \
  --end-index 544 \
  --f0-size 0xe0000 \
  --capture-finalizer-status-after-event 1 \
  --capture-finalizer-status \
  --recover-on-currentboot
```

## Helper Code-Execution Foothold

The first clean host-visible code execution proof was timing-based.

Hook:

```text
helper plaintext 0x02b5 / code 0x32af:
30 e6 12 -> 02 36 1a
```

Payload location:

```text
helper plaintext 0x0620 / code 0x361a
```

Payload shape:

```text
mov r7,#N
outer:
  mov r6,#0xff
middle:
  mov r5,#0xff
inner:
  djnz r5,inner
  djnz r6,middle
  djnz r7,outer
ljmp 0x32c4
```

Observed event-68 timing:

| Run | Event 68 |
|---|---:|
| baseline | `0.255830s` |
| delay `0x20` | `0.849545s` |
| delay `0x80` | `2.638886s` |

Event `34` and event `35` stayed flat, so this is payload-controlled helper
execution, not ordinary bank variance.

Negative result: `MOVX` self-write to `0x361a` did not alter public
`READ BUFFER 01:018620`; that window appears to expose the staged helper copy,
not live helper XDATA/code memory.

## Helper Bit Channel

The timing foothold has been widened into a slow no-hardware XDATA read
channel. The same late hook jumps to payload at `0x361a`, and the payload
chooses either:

```text
LJMP 0x32c4  -> event 68 returns GOOD
LJMP 0x32b2  -> event 68 returns DID_ERROR, then recovery restores LD5M
```

Confirmed payload-controlled cases:

| probe | event 68 |
|---|---:|
| constant `0x01.bit0` | `GOOD` |
| constant `0x00.bit0` | `DID_ERROR` |
| `MOVX xdata[0x48a0].6`, success-on-zero | `GOOD` |
| `MOVX xdata[0x48a0].6`, success-on-one | `DID_ERROR` |

`MOVC` at helper code address `0x32af` did not distinguish bit `0` from bit
`1`, so code-memory reads probably do not see the mutable helper overlay.

Reusable tools:

```sh
python3 scripts/build_liteon_helper_codeexec_candidate.py --help
python3 scripts/read_liteon_xdata_bit_channel.py --device /dev/sg1 --addr 0x48a0
```

Live byte read:

```text
xdata[0x48a0] at the late event-68 hook = 0xa0
```

Selected follow-up reads at the same hook:

| address | value |
|---:|---:|
| `0x47d2` | `0xff` |
| `0x48a0` | `0xa0` |
| `0x48a5` | `0xff` |
| `0x8221` | `0xff` |

This is too slow for bulk dumping, but useful for mapping selected XDATA
registers and validating GPIO/status candidates before using external wiring.

## Pico Front-Panel Probe

The gutted-drive front board is wired to a Pico:

| Pico | line |
|---|---|
| `GP26` | yellow, LED-plus line, sampled high-Z |
| `GP27` | green, eject button line, normally high and pull-low active |
| `GND` | blue, front-panel ground |

Use the Mac-side Pico sampler while running a Linux helper event:

```sh
python3 scripts/probe_liteon_pico_led_payload.py \
  --candidate references/firmware/extracted/helper-codeexec-candidates/<name>/liteon-full-currentboot-ld5m-helper-codeexec-<name>-candidate.json \
  --device /dev/sg1 \
  --label <name>
```

The probe writes phase summaries for `pre`, `event68`, `post_event68`, and
`recovery` under `runs/pico-led-probes/`.

Do not use `GP27` low as a casual input test. It is the real eject button line:
holding it low moved the sled and caused tray-open / not-ready sense before the
helper event, and a later event-scoped pulse still tried to eject. The syndrome
scanner therefore refuses button-low runs unless `--allow-button-low` is passed,
but the practical default should be to avoid GP27-low probing while the
mechanism is connected.

Timing-safe LED probes should use the event-68 helper hook, not a post-command
snapshot. The codeexec builder now has held-window modes:

```sh
python3 scripts/build_liteon_helper_codeexec_candidate.py \
  --name held-loop3-movx-4023-write00-count20 \
  hold-movx-byte --addr 0x4023 --value 0x00 --payload-offset 0x0600 --hold-count 0x20
```

Validated windows:

| mode | observed event-68 behavior |
|---|---|
| delay at plain `0x0600` | stretches event 68 to roughly `2.7s` |
| looped XDATA hold at plain `0x0600` | stretches event 68 to roughly `3.1s` |

Negative LED-control candidates so far: `P1.6`, XDATA `0x4023`, `0x4844`,
`0x90fc`, and the earlier `0x59xx/0x5axx` helper-init shortlist.

For input mapping, the efficient path is a parity/syndrome scan rather than
one-bit-at-a-time reads:

```sh
python3 scripts/scan_liteon_pico_button_syndrome.py \
  --device /dev/sg1 \
  --addr 0x4700 \
  --length 0x100 \
  --sync-remote \
  --allow-button-low \
  --low-scope event68
```

This generates helper predicates over a whole XDATA page. Comparing released
versus low button states gives the index of a single changed bit in about
`1 + ceil(log2(length * 8))` predicates. Because GP27 actuates the sled, treat
this command as disabled unless the mechanism has been made safe and the drive
can still reach the helper hook.

## Next Work

Immediate useful directions:

1. Prefer a different external input that does not actuate the mechanism. GP27
   should be considered an eject actuator, not a debug input.
2. Use the XDATA bit channel to map a small set of high-value helper/controller
   registers around `0x48a0`, `0x47d2`, `0x8221`, and likely GPIO/status
   candidates.
3. If the LED/button GPIO block is found, switch from timing/error-status output
   to a faster Pico-visible channel.
4. Keep live tests short through event `68` while iterating on helper code.
5. Avoid boot-critical persistent F0 hooks until the live normal-mode handler
   path is mapped.
