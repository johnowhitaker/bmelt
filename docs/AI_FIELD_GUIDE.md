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

## Updater/CDD Static Path

The unpacked AHS9 Windows updater module in ignored scratch space contains an
encrypted 1 MiB F0 object, not a raw decoded CDD image. The static extractor is:

```sh
python3 scripts/extract_liteon_updater_f0_image.py
```

Mapped AHS9 facts:

- encrypted source offset: `0x195dc0`;
- key table offset: `0x819f2a`;
- selector offset: `0x819f82`, selector `0x07`;
- FileDecrypt key: `7ee34f39b34d5c9248473a39ec976508`;
- COPYF2K8 mask offset: `0x194dc0`;
- final postprocess SHA-256:
  `e556dbed1132638b58600100fcd2c45d731430edc0cad388455cdbf624322af0`.

COPYF2K8 postprocess patches one byte per `0x400` block:

```text
rel = mask[i] & 0x3f
delta = sum(NEW_FW1[0:4]) & 0xff if i % 7 in {0, 2} else mask[i]
image[i * 0x400 + rel] ^= delta
```

This reproduces `AHS9-postprocess-plain.bin` exactly. The Windows updater does
not appear to decode the CDD body into controller runtime memory; it
materializes the sealed F0 container that the drive later hands to the
controller.

The current CDD static report is:

```sh
python3 scripts/analyze_liteon_cdd_streams.py \
  --out references/firmware/extracted/liteon-cdd-stream-static-analysis.md \
  --map-json references/firmware/extracted/liteon-cdd-record-map.json
```

The JSON map is a decoder skeleton: per image it lists each CDD directory
record, source span, operation key, candidate decoded start/span, mode bits, and
CDD1 table targets that land inside that decoded interval. It is intentionally
marked as inferred structure, not decoded bytes.

Key CDD facts:

- DS-8ABSH descriptor and CDD headers both name logical/controller range
  `0x184000..0x1b4000`, length `0x30000`.
- The encoded descriptor object `0x7000..0xe8000` is about 4.69x that decoded
  range; the CDD streams/bodies are about 4.4x. A remembered ~1.4x ratio does
  not appear at the descriptor level.
- CDD1 starts with 436 8-byte directory records, then a low-entropy
  table/control window. The copied header suggests a nominal `0x400` table, but
  the source-address field places the first payload bytes slightly earlier
  (`0x1194..0x11a4` depending on image).
- CDD2 bytes `0x20..0x1a0` duplicate CDD1 entries 388..435. CDD2 source payload
  starts immediately at stream-relative `0x1a0`; there is no separate `0x400`
  CDD2 table-like window despite the copied header byte.
- The directory source address is now modeled as
  `(u16le(entry[6:8]) << 4) | (entry[5] >> 4)`. These addresses are monotonic;
  entry 388 starts at `0xd91a0`, immediately after CDD2's copied directory.
- Byte 5 is split: the high nibble feeds the source-address formula, while the
  low nibble groups with bytes 0..4 as a non-source operation key. In CHS7 vs
  CHS9, 380/436 same-index records keep that operation key and all 380 keep the
  same source-span length; 377 differ only in source-address bits.
- The CDD1 post-directory table/control window looks like decoded-space
  address material: interpreted as little-endian u16 words, every word shifted
  left by four lands inside the explicit `0x30000` decoded range. CHS7/CHS9
  share 189 same-index table words. Stronger: once records are laid out using
  the candidate decoded-span field below, every shifted table word in all six
  samples falls inside one of those candidate decoded record intervals.
- That CDD1 table has two visible regions. The first 128 words (`0x100` bytes)
  hold all high decoded paragraph targets plus stable repeated runs such as
  `0x0d01` x16 at table indices 16..31 and `0x1503`/`0x1490`/`0x1502` x4 runs.
  These front words target later candidate decoded records. The remaining words
  are almost entirely low decoded offsets, have no adjacent repeats, and target
  early candidate decoded records. Treat the front as
  vector/entrypoint/control-table-like, and the tail as a different
  offset-list-like structure until proven otherwise.
- If runtime decoded/controller reads resume, good LD5M oracle addresses from
  this table are `0x184060` (minimum table target), `0x191010` (`0x0d01` x16
  target), `0x198900`/`0x199030` (x4 front-table targets), and
  `0x1a0000`/`0x1a2fe0` (high front-table targets). These are structurally
  motivated probes, not arbitrary samples.
- Across the current six DS-8ABSH samples, 2,135 unique operation keys appear
  and none maps to more than one source-span length. A partial length field is
  `u16le(operation_key[2:4]) >> 4`, exact for 106 records and close for many
  more.
- A second operation-key field now looks like decoded/output length:
  `(operation_key[3] & 0x3f) << 4`. Its per-image sum lands near the explicit
  `0x30000` decoded range: CHS9 is `0x2ffd0`, CD12 `0x2fe50`, AD12 `0x2fc20`,
  CHS7 `0x30350`, AHS9 `0x30720`, LD5M `0x2e3b0`.
- The high two bits of operation-key byte 3 look like mode flags. Across the
  six samples they split records into redundancy classes with encoded/decoded
  ratios around 2.0x (`0x00`), 3.1x (`0x40`), 5.7x (`0x80`), and rare
  control-like 26.7x (`0xc0`) records.
- Repeated templates `0d6840031a` and `0c60000318` point at short
  `0x34`/`0x30` byte spans, matching the visible motif islands. In these
  records, byte 0 behaves like `N`, byte 1 is `8*N`, byte 4 is `2*N`, and the
  source span is `4*N`. For the `0d...` operation, four 13-byte source units map
  to a `0x30` decoded span: exactly four 12-byte units plus one extra
  parity/check/control byte per unit.
- Those short operations have a source-unit format: one payload-looking first
  byte followed by an image/profile-specific constant tail. Shared indices
  often keep the same four first bytes across all six images even when the unit
  tail and operation key differ.
- CHS7 vs CHS9 same-index source-span comparison has common prefixes up to
  56 bytes, so record indices appear stable across close sibling revisions.
- Cheap decode probes did not find a global XOR/add/sub mask or standard zlib
  payload. Treat CDD as a structured controller-specific packed format, not as
  a single generic encrypted blob.

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

## Helper Timing Channel

The GOOD/DID_ERROR channel is useful but rough: a `0` deliberately enters the
helper's error path. After an overnight sweep wedged on `xdata[0x4704].0 = 0`,
we added a GOOD/GOOD timing channel.

The timing reader still uses the late helper hook at code `0x32af`, but jumps
to a larger payload slot:

```text
helper plaintext 0x04f6 / code 0x34f0
```

The old `0x0620` `Flash Type Error` string is only 16 bytes; the conditional
timing payload is 20 bytes, so use `0x04f6` or another known-large string slot
for these predicates.

Live calibration with delay `0x20`:

| case | event 68 |
|---|---:|
| no delay / bit `0` | `0.255969s` |
| delay / bit `1` | `0.853324s` |
| threshold | `0.554646s` |

First confirmed timing read:

```text
xdata[0x4704] at the late event-68 hook = 0x00
```

Nearby controller cluster timing reads:

| address | value |
|---:|---:|
| `0x4704` | `0x00` |
| `0x4708` | `0x90` |
| `0x4709` | `0x00` |
| `0x470a` | `0x64` |
| `0x470b` | `0x06` |

Tool:

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --addr 0x4704 \
  --calibrate \
  --payload-offset 0x04f6
```

Evidence:

```text
references/evidence/live/linux-drive1-helper-xdata-timing-channel.md
```

The same timing reader can now sample the 8051/controller gateway:

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --space controller \
  --addr 0x184000 \
  --payload-offset 0x04f6
```

This sets `0x4091..0x4093`, reads one byte from the `0x4098` FIFO, and reports
bits through the GOOD/GOOD timing split. `--controller-skip N` can discard a
few FIFO bytes after setting the gateway address.

First CDD-related live follow-up:

| target | value |
|---:|---:|
| controller `0x184000` | `0x00` |
| controller `0x18481c` | `0x00` |
| controller `0x000000`, skip 1 | `0xce` |
| xdata `0x803c` | `0x00` |
| xdata `0x803d` | `0x00` |

Interpretation: the controller FIFO timing primitive works, but the guessed
decoded CDD address `0x184000` is not exposed as useful decoded memory at the
currentboot helper event-68 hook. The next decoded-CDD attempt likely needs a
resident/runtime hook after normal LD5M boot, or a more exact model of the
controller stream selector.

Evidence:

```text
references/evidence/live/linux-drive1-controller-gateway-timing-cdd-attempt.md
```

The timing reader also has a pre-tail/event-1 mode:

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --tail-scope pretail \
  --space controller \
  --addr 0x000000 \
  --controller-skip 1 \
  --bits 0 \
  --calibrate \
  --payload-offset 0x04f6
```

That was a negative for the known helper hook. Constant timing payloads did not
split at event `1`, and a force-error payload still returned GOOD. Event `1`
accepts mutated pre-tail helper bytes, but it does not execute the late helper
branch at helper plaintext `0x02b5` / code `0x32af`.

Evidence:

```text
references/evidence/live/linux-drive1-pretail-codeexec-event1-negative.md
```

After that, we tested a direct persistent F0 resident-hook route. A helper-built
candidate patched the normal-looking `REQUEST SENSE` handler at `0x5c72`, then
another patched the normal-looking `INQUIRY` handler at `0x4ec6`. In both
cases, delayed F0 readback proved the bytes persisted, but live host command
timing did not change after SCSI reset, USB bridge deauth/reauth, or a full
Linux host reboot.

The restore candidate returned `0x0000..0x7000` to byte-identical stock LD5M.

Evidence:

```text
references/evidence/live/linux-drive1-resident-f0-hook-negative.md
```

Second pass, after the directory source-address model, also returned zeros:

| target | value |
|---:|---:|
| controller `0x184000` | `0x00` |
| controller `0x18481c` | `0x00` |
| controller `0x19191a` | `0x00` |

Evidence:

```text
references/evidence/live/linux-drive1-controller-gateway-cdd-second-pass.md
```

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

For hazardous candidates, prefer the read/modify/write form so only one bit is
changed in the held window:

```sh
python3 scripts/build_liteon_helper_codeexec_candidate.py \
  --name led-4748-or01-count04 \
  hold-movx-byte-op --addr 0x4748 --op or --value 0x01 \
  --payload-offset 0x0600 --hold-count 0x04 --restore-original
```

Validated windows:

| mode | observed event-68 behavior |
|---|---|
| delay at plain `0x0600` | stretches event 68 to roughly `2.7s` |
| looped XDATA hold at plain `0x0600` | stretches event 68 to roughly `3.1s` |

Negative LED-control candidates so far: direct/SFR `P1.0..P1.7` and
`P3.0..P3.5`, XDATA `0x4023`, `0x4844`, `0x90fc`, and the earlier
`0x59xx/0x5axx` helper-init shortlist.

Do not repeat direct/SFR `P3.6` casually. Clearing `P3.6` in the held-window
probe wedged the optical LUN, left the LED stuck on, and did not recover by
host reboot; it needed a physical drive/bridge power cycle followed by the
normal currentboot recovery sequence. This matches the standard 8051 `WR`
strobe role and should be treated as a bus/control pin.

The first strong LED-path candidate is XDATA `0x4748`. Static references make
it look like a small controller command/control register rather than a plain
GPIO latch: stock code writes `0x88`/`0x98`, clears bit 7, and later sets bit 7
while related command bytes live at `0x474d/0x474e`. A held-window
`0x4748=0x00` probe completed and recovered normally. The paired
`0x4748=0xff` probe completed event 68, but GP26 stayed high through the
following recovery attempt (`5379/5379` recovery samples high, about `1.98 V`)
and the USB/optical LUN then disappeared with descriptor timeouts. This is a
real clue, not a safe output primitive yet: next tests should isolate non-stock
bits of `0x4748` with `--restore-original` instead of writing whole-byte
`0xff`, and stop on any optical-LUN loss.

Follow-up narrowed this:

- `xdata[0x4748]` reads as `0xff` at the event-68 helper hook.
- restored `0x4748=0xff` and restored one-bit `OR` probes complete/recover
  normally, so the earlier hard failure was likely from leaving the controller
  in a bad state across recovery, not from the transient write itself.
- restored `0x4726` and `0x479e` `00`/`ff` probes look normal.
- restored neighbor probes through `0x4784`, `0x4788`, `0x4756`, `0x47a7`,
  `0x4728`, and `0x4780=0x00` look normal.
- restored `0x4780=0xff` completes event 68, then recovery sees currentboot
  with GP26 stuck high. The known recovery sequence brings it back to `LD5M`.
  Treat `0x4780` as another hazardous controller-path lead.

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

## Pico Power Cycle

The Pico now also drives a servo on `GP10` which presses a microswitch in the
spliced USB `+5V` line. This is a real high-side/mechanical power cut for the
drive/bridge, not a USB logical reset.

Run from the Mac:

```sh
python3 pico/client.py --port /dev/cu.usbmodem2101 "TOGGLE SERVO"
```

Verified behavior on 2026-04-30:

```text
before: sg0:PLDS:DVD+-RW DS-8ABSH:LD5M | sg1:Generic-:SD/MMC:1.00
during: sg1:Generic-:SD/MMC:1.00
after:  sg0:PLDS:DVD+-RW DS-8ABSH:LD5M | sg1:Generic-:SD/MMC:1.00
```

Use this before requesting a manual replug, especially after tests that wedge
the optical LUN or when a true cold boot is needed to validate whether F0 flash
patches load into runtime state.

Evidence:

```text
references/evidence/live/linux-drive1-pico-servo-power-cycle.md
```

## Next Work

Immediate useful directions:

1. Prefer a different external input that does not actuate the mechanism. GP27
   should be considered an eject actuator, not a debug input.
2. Treat XDATA `0x4748` and `0x4780` as controller-path clues, not LED latches.
   Any further tests there should be bit-level, restored, and followed by an
   immediate state check.
3. Use the XDATA bit channel to map a small set of high-value helper/controller
   registers around `0x48a0`, `0x47d2`, `0x8221`, and likely GPIO/status
   candidates.
4. If the LED/button GPIO block is found, switch from timing/error-status output
   to a faster Pico-visible channel.
5. Keep live tests short through event `68` while iterating on helper code.
6. Do not assume visible F0-prefix functions are live normal-mode handlers.
   Persistent hooks at `0x4ec6` and `0x5c72` were visible in F0 but did not
   affect `INQUIRY` or `REQUEST SENSE` timing.
