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

For static 8051 work, treat `ldm58051.bin` disassembled as 8051 at base 0 as
ground truth. The Ghidra C export is useful for search/navigation, but it has
duplicate XDATA declarations and can mislead around `MOVX` pointer flow. The
current raw-disassembly CDD mailbox note is:

```text
analysis/8051/cdd-mailbox-handoff-static-notes.md
```

Static replay planner:

```text
scripts/plan_liteon_cdd_mailbox_replay.py
references/firmware/extracted/liteon-cdd-mailbox-replay-plan.md
```

Latest 8051 mailbox detail: the `0x4e80/0x4e84/0x4e88/0x4e8c` command wrapper
uses `r7 = 0/1/2` as a controller address-bank selector. The wrapper shifts the
selector left by `0x15` bits (`selector << 21`, a `0x200000`-byte bank offset),
adds it to the first pointer, validates local ranges against the 2 MiB bank
window, then rings `xdata[0x4e8c] = 1`. That makes the wrapper a banked
controller-memory command surface, not just a generic small-opcode mailbox.

CDD-parser correction: the failed live `xdata[0x4a00] = 1` doorbell test is
only a negative for the trivial one-byte shortcut. The resident setup also
preloads descriptor fields into `xdata[0x8244..0x8255]`, derives `0x4e0d`,
`0x4e1a`, `0x4e1c`, maps/checks the CDD header through an `xdata[0xc000]`
window, and only then packages `0x4a01/03/05/06/20/21/22`. The lowest-risk next
live replay would write that header-derived `0x4a` field package and sample
`0x4a24..0x4a29`, `0x4ea0`, and decoded CDD targets before attempting the
higher-risk `0x4e8c` mapped-header command.

Replay helper:

```text
scripts/run_liteon_currentboot_cdd_mailbox_replay.py
```

This script assumes the combined gateway/XDATA read-write currentboot hook is
installed. It samples baseline windows, writes the generated ordered field
package, samples the same windows afterward, and restores `xdata[0x4a00]` to
zero unless told otherwise.

Newer special-trigger variant: build with
`--gateway-cdb-bulk-with-cdd-field-replay`. Normal commands still read the
controller gateway. The preserved CDB address `fc dd 00` instead replays the
LD5M field package internally and returns `0xcd` at `response[0x20]`. Use the
runner with `--trigger-mode cdb-fcdd00`; by default that mode samples only
gateway windows so it does not depend on fragile CDB[10]/CDB[11] selectors.

Live result: the trigger executed, but decoded CDD targets remained zero:

```text
references/evidence/live/currentboot-cdd-field-trigger-v1.md
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
  source span is `4*N`.
- Those short operations have a source-unit format: byte 0 of each unit is a
  coded cell in a 16-cell affine group. The mask table is
  `mask[cell] = carryless_mul8(0x19, cell)`, giving
  `00 19 32 2b 64 7d 56 4f c8 d1 fa e3 ac b5 9e 87`.
  The old row-local `m` value was the raw coded byte, not the final semantic
  byte. Decode with
  `plain_group_byte = raw_cell_byte ^ mask[4 * (record_index & 3) + unit]`.
- Matching canonical unit tails also appear in longer records. The current
  partial decoder accepts three positions: full rows, prefix runs starting at
  record offset `0`, and suffix runs ending at the record end. That resolved
  the old group-96 boundary conflict: record 387 is a prefix run and decodes
  group 96 to `0xd8`.
- All currently confident affine leaves land in one lane of a 12-record macro
  schedule:
  `record_group = record_index // 4`, `macro_lane = record_group % 3`,
  observed lane `0`. The regenerated report has 624 cell observations, zero
  conflicts, and macro lane counts of `0:624`.
- Prefix/suffix records are still decoded from literal canonical-tail evidence,
  not from a solved op-key formula. Current constraints: `op_key[5] == 0`;
  non-boundary suffix records keep `op_key[4] == 0x18/0x1a` as
  `2 * unit_size`; and every non-boundary `k=2`/`k=3` suffix has decoded-span
  field `0x30`.
- Current reports:
  `references/firmware/extracted/liteon-cdd-affine-unit-analysis.md`,
  `references/firmware/extracted/liteon-cdd-affine-oracle-targets.md`, and
  `analysis/cdd-affine-codeword-notes.md`.
- A broader lane-schedule scan over edge affine units with unit sizes `4..40`
  found `718` repeated-tail affine hits, all in macro lane `0`; macro lanes
  `1` and `2` had zero hits. CHS7/CHS9 same-op same-length records still keep
  about 72% equal bytes in all lanes, with changed bytes dominated by one-bit
  XOR deltas. Contiguous diff runs are usually tiny: about 60% length 1, 88%
  length <=2, and 98% length <=4 in every lane. This makes lanes `1`/`2` look
  like deterministic localized controller codewords, not encryption avalanche
  and not the lane-0 tail grammar. Report:
  `references/firmware/extracted/liteon-cdd-lane-schedule-analysis.md`.
- The lane-schedule scan now also allows any nonzero carry-less affine
  multiplier for complete four-unit edge rows. It still finds only lane `0`,
  only multiplier `0x19`, and only unit sizes `12`/`13`. This reduces the
  chance that lanes `1`/`2` are hiding the same repeated-tail grammar under a
  different affine mask.
- Operation-key analysis is now split out into
  `references/firmware/extracted/liteon-cdd-operation-key-analysis.md`. Across
  2,616 records and 2,135 unique operation keys, no observed key maps to two
  different source lengths, so the key is a real packet/codeword selector. But
  source length is not a simple visible bitfield: a GF(2) linear probe only
  recovers the parity relation
  `source_len.bit0 = key[0].0 ^ key[1].3 ^ key[2].6 ^ key[4].1`. Bits 1..11
  are not affine functions of the raw key bits. `key[4] / 2` remains a valid
  unit-size hint for the lane-0 affine class, but it fails as a universal unit
  size on lanes `1`/`2`.
- Treat the affine byte as proven structure but not yet proven runtime payload.
  It may be semantic data, parity/control material, or one lane of a larger
  controller codeword. A runtime oracle for one known short record would settle
  that ambiguity.
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

After the Pico servo power-cycle primitive was added, the `INQUIRY` hook was
retested across a true mechanical `+5V` power loss. The result stayed negative:
F0 still contained the jump/stub patch, Linux dmesg showed a real USB
disconnect/re-enumeration, and post-cold-boot `INQUIRY` timing remained the same
roughly 5 ms baseline. Treat visible F0-prefix command handlers as non-live
normal-mode code unless a later test proves a more exact activation path.

Evidence:

```text
references/evidence/live/linux-drive1-resident-f0-hook-negative.md
references/evidence/live/linux-drive1-servo-coldboot-persistence-map.md
```

A related cold-boot data test patched the F0 identity/profile timestamp at
`0xd8ff4` from `2016` to `3016`. Direct F0 dumps after power loss showed the
patched byte persisted, but live EXTRAINQ still reported canonical
`2016/10/18 14:18`. So `0xd8fd0..0xd8fff` is writable persistent data, but not
the normal runtime EXTRAINQ source.

The lower-prefix `0D5C` identity copy is different. Patching `0x4476` from
`2011` to `3011` with `--auto-helper-range`, cold-booting, and then running only
event 1 made currentboot EXTRAINQ report `0D5C3011/04/28 09:20`. Auto-recovery
returned to `LD5M`. This is a useful currentboot-visible lower-prefix data
hook, even though the normal LD5M identity stayed canonical.

## Normal-Mode Read-Only Surface

After the cold-boot negative on visible F0 resident hooks, we ran a standard
read-only normal-mode command survey to find better host-visible trigger
surfaces. The probe script deliberately avoids updater commands, data-out
commands, START STOP, LOAD/UNLOAD, MODE SELECT, SEND DIAGNOSTIC, and FORMAT.

Run from the Linux host:

```sh
python3 scripts/probe_liteon_normal_mode_readonly.py \
  --device /dev/sg0 \
  --out-json runs/normal-mode-readonly/standard-only-probe.json \
  --out-md runs/normal-mode-readonly/standard-only-probe.md
```

Important default: `READ BUFFER` probes are opt-in with
`--include-read-buffer`. During an earlier manual survey,
normal-mode `READ BUFFER id=02` hung the optical LUN and required the Pico servo
power-cycle. `GET PERFORMANCE` also returned `DID_TIME_OUT` after about ten
seconds, so do not use it as a casual trigger.

Fast, no-disc, host-visible response channels:

```text
INQUIRY standard       96 bytes, ~7 ms
EXTRAINQ              176 bytes, ~9 ms
MODE SENSE(10)        224 bytes, ~9 ms
GET CONFIGURATION     60/252 bytes, ~8-14 ms
GET EVENT STATUS      8 bytes, ~10 ms
MECHANISM STATUS      8 bytes, ~8 ms
```

Offline matching shows `INQUIRY` and `EXTRAINQ` contain exact strings from both
visible F0 identity copies (`0x04452` and `0xd8fd0`). That is a source clue, but
not proof of direct normal-runtime reads from those offsets: live edits to
`0xd8fd0..0xd8fff` persisted in F0 and still did not change normal EXTRAINQ.
Treat these as normal-mode command surfaces to localize later, not as solved
handler locations.

Artifacts:

```text
scripts/probe_liteon_normal_mode_readonly.py
scripts/analyze_liteon_normal_mode_responses.py
references/evidence/live/normal-mode-readonly/linux-drive1-standard-only-probe.md
references/evidence/live/normal-mode-readonly/linux-drive1-standard-only-probe.json
analysis/8051/normal-mode-response-surface-analysis.md
```

The next normal-runtime foothold experiment should be a state-carryover test
or a better handler-source localization pass, not another blind patch to the
visible F0 prefix handlers.

Follow-up live timing hooks made that warning stronger. Two broad hooks were
installed and cold-booted:

```text
0x6206 response-copy helper: 90 80 3e -> LJMP delay cave
0x542b packet-intake helper: 90 81 79 -> LJMP delay cave
```

Both patches persisted in F0 and both were negative for normal LD5M timing
across `INQUIRY`, `EXTRAINQ`, `MODE SENSE(10)`, `GET CONFIGURATION`,
`GET EVENT STATUS`, and `MECHANISM STATUS`. The `0x6206` hook did, however,
slow the next currentboot update run, proving the hook was live in currentboot
but not in ordinary normal-mode response handling.

The stock restore then rewrote `0x1ea0`, `0x542b`, `0x6206`, and the `0x6ee3`
cave, and a live-key F0 dump of `0x1000..0x6fff` matched stock with zero diffs.

The normal-response static comparison also found a tempting currentboot XDATA
copy of the model string at `0x811e`. A guarded XDATA write changed
`xdata[0x811e]` from `D` to `X` and read it back, but the next currentboot
identity response still returned canonical `DVD+-RW DS-8ABSH`; only the
deliberate hook readback byte changed. Treat `0x811e` as metadata/key-window
state, not a live response template.

Evidence:

```text
references/evidence/live/normal-mode-hook-tests/normal-mode-hook-tests-summary.md
references/evidence/live/xdata-source-localizer/currentboot-xdata-811e-source-test.md
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

## Currentboot Response-Hook Readout

The slow helper timing/error channels are now mostly superseded for currentboot
mapping. The visible currentboot identity handler at code `0x4ec6` executes
after a hardware cold boot plus event-1/profile-tail entry into currentboot.
Hook its final response-copy call:

```text
0x4fc9: 12 62 06 -> 02 6e e3
```

Payloads at `0x6ee3` write one byte into response offset `0x20`, call the
original `0x6206` response copy, and jump back to `0x4fcc`.

Builder:

```sh
python3 scripts/build_liteon_currentboot_response_hook_candidate.py --help
```

Important candidate modes:

```sh
# constant response byte, used for the XD5C proof
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name revision-x-constant \
  --constant 0x58

# controller gateway read: CDB[7:9] + (CDB[5] & 0x3f)
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-cdb-byte-v3 \
  --gateway-cdb-address

# controller gateway bulk read: copy 128 bytes into response[0x20..0x9f]
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-cdb-bulk \
  --gateway-cdb-bulk

# combined gateway bulk read plus guarded XDATA write:
# normal mode is gateway bulk; host CDB[10:11]=a5 5a writes CDB[9] to XDATA
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-cdb-bulk-xdata-write-v2 \
  --cave-len 0xdd \
  --gateway-cdb-bulk-with-xdata-write

# combined gateway bulk read plus guarded XDATA read/write:
# normal mode is gateway bulk; host CDB[10]=a5 writes XDATA;
# host CDB[10]=5a reads XDATA into response[0x20].
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-cdb-bulk-xdata-rw-v2 \
  --cave-len 0xdd \
  --gateway-cdb-bulk-with-xdata-rw

# XDATA read: CDB[7:8] + (CDB[5] & 0x3f)
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name xdata-cdb-byte \
  --xdata-cdb-address

# XDATA guarded byte read/write: write CDB[9] if CDB[10:11] == a5 5a
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name xdata-cdb-rw \
  --xdata-cdb-rw

# XDATA bulk read: copy 128 bytes into response[0x20..0x9f]
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name xdata-cdb-bulk-v2 \
  --xdata-cdb-bulk
```

Install a response hook using the normal helper-bypass full-currentboot runner,
then power-cycle the drive with the Pico servo and enter currentboot with event
1:

```sh
python3 scripts/pico_power_cycle_linux_drive.py

ssh root@jonathan-thinkpad-t480s \
  'cd /home/jonathan/boastermelt && python3 scripts/run_liteon_linux_persistence_experiment.py \
    --candidate references/firmware/extracted/liteon-full-currentboot-ld5m-base-candidate.json \
    --device /dev/sg0 \
    --skip-pre-f0 --skip-post-f0 \
    --end-index 1 \
    --capture-finalizer-status-after-event 1 \
    --out-dir runs/currentboot-response-hook/event1-no-recover'
```

Controller-gateway read example:

```sh
ssh root@jonathan-thinkpad-t480s \
  'cd /home/jonathan/boastermelt && python3 scripts/read_liteon_currentboot_gateway.py \
    --device /dev/sg0 \
    --address 0x018620 \
    --length 32'
```

Known output:

```text
Flash Type Error
```

The controller-gateway hook must do a throwaway `0x4098` read before the real
read. Without that, reads returned stale `0x05` bytes.

The bulk gateway reader has a related one-byte pipeline quirk: the first byte
of each 128-byte response is stale. `scripts/read_liteon_currentboot_gateway_bulk.py`
compensates by requesting `address - 1` and dropping the stale first byte, so
use the script rather than hand-parsing raw INQUIRY output.

Gateway bulk read example:

```sh
ssh root@jonathan-thinkpad-t480s \
  'cd /home/jonathan/boastermelt && python3 scripts/read_liteon_currentboot_gateway_bulk.py \
    --device /dev/sg0 \
    --address 0x018620 \
    --length 64'
```

Known settled output:

```text
Flash Type Error
```

The live-proven combined hook is currently the most ergonomic currentboot
instrument when both controller reads and small XDATA writes are needed:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-cdb-bulk-xdata-write-v2/currentboot-response-hook-gateway-cdb-bulk-xdata-write-v2/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-gateway-cdb-bulk-xdata-write-v2-candidate.json
```

Write mode uses:

```text
CDB[5] low six bits = selector
CDB[7:8]            = 16-bit XDATA base
CDB[9]              = write value
CDB[10:11]          = write magic a5 5a
response[0x20]      = readback byte
```

There is also a newer combined read/write hook with the same default gateway
bulk mode. Use `v2`; `v1` used a brittle two-byte guard and its XDATA-read
branch timed out in the first live smoke test.

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2/currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2-candidate.json
```

The host-facing convention for v2 is:

```text
normal gateway read     CDB[10] = 00 and CDB[11] = 00
guarded XDATA write     CDB[10] = a5, CDB[9] = value
guarded XDATA read      CDB[10] = 5a
unknown nonzero selector returns 0xee instead of falling into gateway mode
```

For the read path, use:

```sh
ssh root@jonathan-thinkpad-t480s \
  'cd /home/jonathan/boastermelt && python3 scripts/read_liteon_currentboot_xdata.py \
    --device /dev/sg0 \
    --address 0x4a00 \
    --length 0x30 \
    --read-magic 5aa5'
```

Do not reuse the failed v1 idea of guarding on CDB byte `6`; that byte was not
reliably preserved by this currentboot handler. Bytes `7..11` are the proven
parameter window for this hook.

The currentboot-phase decoded CDD candidate range is still blank when sampled
in bulk:

```text
controller[0x184000..0x184fff] = all 00
```

A sparse gateway sweep then found the more useful live currentboot window:

```text
controller[0x070000..0x07ffff]
controller[0x170000..0x17ffff]  mirror of 0x070000 sample pages
```

The first full dump is tracked:

```text
references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin
sha256 5f517adeab1647dbedf7b93f8be097b1641164fd49e87776364b9e134b9cbc0b
```

Offline analysis:

```text
analysis/8051/currentboot-gateway-070000-analysis.md
analysis/8051/currentboot-gateway-070000-analysis.json
analysis/8051/servo-mechanics-static-notes.md
```

This 64 KiB region contains live profile/calibration strings such as
`PLDS CORPORATION`, `KEYPARA`, media-profile names, and per-drive-looking serial
material. It also disassembles plausibly as 8051 in several regions and
references the same `0x4098`, `0x47xx`, `0x48xx`, and `0x59xx` register
clusters we have been probing.

Important correction: this is not a decoded CDD payload. The tail of the
`0x070000` window contains exact sealed LD5M CDD bytes:

```text
gateway+0xf000 == F0 0x704c..0x7deb   CDD1 post-header directory/table prefix
gateway+0xfc20 == F0 0xd9020..0xd919f CDD2 duplicate prefix
gateway+0xff00 and +0xff80            repeated CDD headers
```

The same dump has exact overlaps against the resident 8051 and the
profile-tail helper, but many apparent calls target the zero
`0x02ea..0x3fff` region. Treat it as a mixed currentboot controller/work
window, not as a complete standalone code image at base zero.

For mechanics work, the useful static clue is the `0x59xx`/`0x5axx` cluster.
The LD5M routine at F0 `0x59f3` appears at gateway offset `0x6059` and touches
`0x5904`, `0x5905`, `0x5906`, `0x592a`, `0x59f0`, `0x5a00`, `0x5a24`,
`0x5a31`, and nearby `0x4860..0x486a` state. Other gateway routines around
`0x642c`, `0x6fe0`, and `0x8278` manipulate the same cluster. This fits the
live sled movement from earlier probes: this is a servo/mechanics command area,
not a safe LED latch.

XDATA read example:

```sh
ssh root@jonathan-thinkpad-t480s \
  'cd /home/jonathan/boastermelt && python3 scripts/read_liteon_currentboot_xdata.py \
    --device /dev/sg0 \
    --address 0x4704 \
    --length 16'
```

Known output starts:

```text
00 50 00 04 90 00 64 06 78 ...
```

The `0x4704` read confirms the earlier bit-channel finding
(`xdata[0x4704].0 = 0`) without jumping into the helper `DID_ERROR` path.

The guarded read/write variant is live-proven too. With magic CDB bytes
`a5 5a`, `scripts/write_liteon_currentboot_xdata.py` wrote `0xa6` to
`xdata[0x8000]`, the next read saw `a6`, and a second guarded write restored it
to `00`. Treat this as currentboot XDATA/RAM mutation only; it is not a direct
flash writer and should not be aimed at hardware registers casually.

Bulk XDATA read example:

```sh
ssh root@jonathan-thinkpad-t480s \
  'cd /home/jonathan/boastermelt && python3 scripts/read_liteon_currentboot_xdata_bulk.py \
    --device /dev/sg0 \
    --address 0x0000 \
    --length 0x10000 \
    --out runs/currentboot-response-hook/xdata-bulk-v2-smoke/currentboot-xdata-0000-ffff.bin \
    --quiet'
```

The v2 bulk hook uses the stock `FUN_CODE_6012` response-byte writer in a loop.
The first bulk attempt wrote directly to XDATA and returned the unchanged stock
response because the host response buffer is controller-side, not ordinary
XDATA. Calling `0x6012` for each byte fixed it.

First full dump:

```text
references/evidence/live/linux-drive1-currentboot-xdata-0000-ffff-bulk-v2.bin
sha256 6862a4c5ddceab9fa6b9e490ff3b14bd4447fe039f0ad2e3556b0d3761fb5d82
```

Button differential with the Pico:

```text
GP27 released: xdata[0x4814] = d9
GP27 low:      xdata[0x4814] = c9
```

So `xdata[0x4814].4` is the cleanest current front eject button-sense
candidate. `xdata[0x48f7].7` also tracks the button. The LED output latch is
still unknown.

Current limitation: these hooks observe the currentboot/helper phase. The
decoded CDD range around controller `0x184000` remains all zero here, so a
decoded CDD dump still needs either a later controller phase or a normal-runtime
hook.

2026-05-01 update: the passive gateway path used by
`gateway-cdb-bulk-xdata-write-v2` appears to mirror every `0x100000` bytes in
currentboot. Simple banked reads at `0x184000 + 0x100000*n` and
`0x184000 + 0x200000*n` are still all zero, as are the CDD table oracle targets
around `0x191010`, `0x198900`, and `0x1a0000`.

Useful currentboot gateway windows now known:

```text
0x000000..0x006fff  live staging buffer; exact F0 CDD2 overlap at +0x2c
0x018000..0x018bbf  active plain ef130045 helper overlay
0x06b000..0x06bfff  low-entropy serial/profile-looking table
0x070000..0x07ffff  mixed currentboot work/code/profile window
```

New evidence/report:

```text
analysis/8051/currentboot-gateway-extra-20260501.md
references/evidence/live/currentboot-gateway-extra-20260501/
```

Normal `LD5M` also exposes the `0x070000` work window through public
`READ BUFFER mode=1` IDs `0x01` and `0x02`; no currentboot hook is required.
Use:

```sh
python3 scripts/read_liteon_read_buffer_bulk.py \
  --device /dev/sg0 \
  --id 0x01 \
  --offset 0x070000 \
  --length 0x10000 \
  --out runs/normal-read-buffer/id01-070000-010000.bin \
  --json-out runs/normal-read-buffer/id01-070000-010000.json \
  --quiet
```

The normal-mode decoded CDD target offsets are still zero for IDs `0x01` and
`0x02`, but this is now the fastest normal-runtime read surface for the
controller/work window. Evidence:

```text
analysis/8051/normal-read-buffer-work-window-20260501.md
analysis/8051/normal-read-buffer-070000-analysis.md
references/evidence/live/normal-read-buffer-work-window-20260501/
```

Evidence:

```text
references/evidence/live/linux-drive1-currentboot-response-hook.md
references/evidence/live/currentboot-cdd-mailbox-doorbell-v2.md
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

The 2026-04-30 static cross-reference pass backs up that interpretation.
`0x4748` sits in a controller transaction path: stock code writes command bytes
to `0x474d/0x474e`, clears/sets `0x4748.7`, and waits through `FUN_CODE_60c4`.
That makes it a controller kick/ack register, not a clean LED latch. `0x4780`
is only touched inside a broad initialization/config sequence.

Higher-value static clues now are:

- `0x4814` is a packed front-panel/status byte. Live Pico reads show bit 4
  tracks the eject button, while `FUN_CODE_63cb` waits on bit 7 after writing
  `0x4821/0x4822`.
- `0x482b/0x482c/0x482d` look like a small controller query/status port: helper
  functions write a command to `0x482b` and read a 16-bit result from
  `0x482c/0x482d`.
- `0x483f` is a sparse visible 0/1 latch and is worth keeping on a future
  Pico-sampled shortlist, but it is not yet evidence of LED control.

Static reports:

```text
analysis/8051/controller-command-static-notes.md
analysis/8051/xdata-front-panel-static-notes.md
analysis/8051/xdata-register-crossref.md
analysis/8051/xdata-register-crossref.json
```

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

Preferred wrapper, which also waits for Linux to see the optical LUN:

```sh
python3 scripts/pico_power_cycle_linux_drive.py
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
references/evidence/live/linux-drive1-servo-coldboot-persistence-map.md
```

## Blank-Currentboot Recovery

The `led-baseline-delay-count50-r4` Pico probe completed event `68` but left
Linux drive #1 in a new blank-currentboot identity:

```text
standard INQUIRY: PLDS DVD+-RW DS-8ABSH, blank/garbage revision
EXTRAINQ: 176 bytes, no EXTRAINQ marker, trailing "        LD50 01 00 00 00"
```

This is not the known `0D5C` state. The known recovery tail before bank 0
rejects with `Parameter value invalid`; normal event-1 profile-tail also
rejects. `arg=00` chunks still stage and read back, but pMac/control rejects, so
the data path and control path are out of phase.

Recovery/status attempts that did not exit blank mode:

- 8-second servo cold boot;
- Linux host reboot plus 8-second servo cold boot;
- Pico `ALLZ` plus 30-second servo cold boot;
- TEST UNIT READY, REQUEST SENSE, START STOP variants, `PLDSVUC`
  lock/unlock, `DF 0D/11`, and `sg_reset`.

The exit is now live-proven. Treat blank-currentboot as a third currentboot
dialect. Its malformed EXTRAINQ still exposes an active slot-5 transport key at
`0x9c..0xab`. That key changes after bank boundaries, so the profile-tail
payload must be rebuilt dynamically. Bank 2 is the AES-selected bank; its chunks
and pMac must be regenerated under the slot-5 key visible immediately before
bank 2. Later banks use plain LD5M chunks and carry the bank-2 pMac.

Recovery command:

```sh
python3 scripts/recover_liteon_blank_currentboot_linux.py --device /dev/sg0
```

The first live recovery was hand-proven through bank 2, then resumed:

```sh
python3 scripts/recover_liteon_blank_currentboot_linux.py \
  --device /dev/sg0 \
  --start-bank 3 \
  --end-bank 15 \
  --initial-pmac 1b98d87590797f125e5f2ea3d704c531
```

It completed through final `PLDSVUC`, and a Pico servo cold boot re-enumerated
as `LD5M`.

Superseded live-drive note: after blank-currentboot recovery, F0 briefly
carried the known `currentboot-response-hook-gateway-cdb-bulk` candidate:

```text
sha256 11df18bd19d269b959aa7c2270db96a636c27384669194ed0732c9b05e176771
diffs  0x4fc9..0x4fcb -> LJMP 0x6ee3
       0x6ee3..0x6f49 -> currentboot gateway bulk hook payload
```

The later normal-mode hook test phase restored stock bytes. A live-key F0 dump
of `0x1000..0x6fff` matched stock LD5M with zero diffs, including:

```text
0x4fc9..0x4fcb = 12 62 06
0x6ee3..       = ff...
```

Reinstall a currentboot response hook before using the bulk gateway/XDATA
readout scripts that depend on `0x4fc9 -> 0x6ee3`.

Evidence:

```text
references/evidence/live/linux-drive1-blank-currentboot-after-led-probe.md
```

Operational advice: do not keep issuing LED/XDATA write probes from this state.
Recover to `LD5M` first. If testing recovery commands where identity reads may
be hooked/stateful, use:

```sh
python3 scripts/run_liteon_events_no_preflight.py --help
```

This sends selected candidate events without the usual preflight INQUIRY.

## Next Work

Immediate useful directions:

1. Keep `recover_liteon_blank_currentboot_linux.py` as the first response to
   blank/garbage-revision currentboot. It is now faster and more reliable than
   reset-only attempts.
2. Prefer a different external input that does not actuate the mechanism. GP27
   should be considered an eject actuator, not a debug input.
3. Treat XDATA `0x4748` and `0x4780` as controller-path clues, not LED latches.
   Any further tests there should be bit-level, restored, and followed by an
   immediate state check.
4. Use the XDATA bit channel to map a small set of high-value helper/controller
   registers around `0x48a0`, `0x47d2`, `0x8221`, and likely GPIO/status
   candidates.
5. If the LED/button GPIO block is found, switch from timing/error-status output
   to a faster Pico-visible channel.
6. Keep live tests short through event `68` while iterating on helper code.
7. Do not assume visible F0-prefix functions are live normal-mode handlers.
   Persistent hooks at `0x4ec6` and `0x5c72` were visible in F0 but did not
   affect `INQUIRY` or `REQUEST SENSE` timing. The `0x4ec6` negative now holds
   even across a true servo-driven `+5V` power cycle.
8. For sled/focus/laser goals, statically reverse the `0x59xx` routines from
   the gateway report before any more live mechanics pokes.
9. Public normal-mode `READ BUFFER mode=1` IDs `0x01` and `0x02` mirror at
   1 MiB granularity across the 24-bit offset field. Do not expect addresses
   like `0x184000` to reach decoded CDD through this path unless a different
   buffer ID or command mode is found.
10. The first broad READ BUFFER scan did not find that different mode. Modes
    `0x00..0x1f` were scanned at offset zero and only mode `0x01` produced any
    data. In mode `0x01`, IDs `0xe2` and `0xf1` are only aliases into the
    public work window: `e2:0 == id01:0x074000`, `e2:0x1000 == id01:0x075000`,
    and `f1:0 == id01:0x075000`. `e2` rejects page-start offsets `0x2000` and
    above; `f1` is only `0x0b60` bytes long and rejects at `0x0b60`. These are
    narrow profile/table aliases, not decoded CDD surfaces.
11. Allocation length matters. Normal `READ BUFFER mode=1 id=f0/f2` respond to
    exact `0x80`-byte chunks even though broad 64-byte scans miss them. `id=f0`
    is encrypted F0 readback; issue EXTRAINQ immediately before dumping, then
    decrypt with the EXTRAINQ IV/key and AES-CBC reset every `0x80`. `id=f2`
    exposes encoded container material around CDD2/profile/trailer, not decoded
    CDD.
12. Do not model `id=f2` as a branch of the visible F0-prefix READ BUFFER
    handler. The disassembly at `FUN_CODE_385c` accepts only `01/02/e2/f0/f1`.
    The normal `id01:0x070000` work/code dump has a separate READ BUFFER-like
    accept list at `+0x6747` that includes `f2`; its CDB shadow appears to live
    around `xdata[0x8a49..]`.
13. The normal `id01/id02:0x070000` work window is partly live state, not a
    frozen ROM. Across six captures, most bytes are stable, but pages around
    `+0x6000`, `+0x8700`, `+0x9500`, `+0x9ac0`, and `+0x9e00` move. The `f2`
    accept list and the `0x47b1 -> xdata[0x8a49..]` packet-shadow copy are in
    stable areas; the `+0xa2xx` dispatch island is alignment-sensitive and
    should not be linear-disassembled as ordinary code without checking exact
    branch targets.
14. A follow-up exact-`0x80` high-ID scan at offset zero found no hidden
    siblings beyond the known `e2/f0/f1/f2` responders. The drive stayed normal
    `LD5M` afterwards. An exact-size mode sweep for those four IDs also found
    only mode `0x01`; modes `0x00..0x1f` otherwise rejected or returned no
    data.
15. A 12-byte `READ BUFFER id=f2` tail-byte probe also closed a tempting hidden
    selector theory. CDB tail values `0000`, `0001`, `0002`, `0100`, `5aa5`,
    `a55a`, and `ffff` all returned the same 128-byte CDD2-header page hash.
    The drive stayed normal `LD5M`. The extra bytes are not an obvious f2 bank
    selector.
16. The ordinary 10-byte CDB control byte is not an obvious f2 selector either.
    Control values `00`, `01`, `02`, `5a`, `a5`, and `ff` all returned the
    same page hash and left the drive normal.
17. The next currentboot CDD mailbox candidate is
    `--gateway-byte-with-cdd-prestage-replay`. It uses only proven-preserved
    `CDB[7:8] == fc dd` as the trigger, returns `0xce`, and falls back to a
    one-byte gateway reader to fit in the `0x6ee3` cave. It preloads compact
    descriptor/status state (`0x8246/4a/4d/52/54`, `0x4e0d/1a/1c`, direct
    `0x60/0x61`) before writing the `0x4a` CDD field package and ringing
    `0x4a00`. Use `run_liteon_currentboot_cdd_mailbox_replay.py` with
    `--trigger-mode cdb-fcdd01 --gateway-read-mode byte --max-sample-length
    0x20` for the first live pass; without the length cap this path is slow.
    Live correction: this hook installed, but its first high-address byte-mode
    gateway read timed out before the trigger, and a Pico cold boot recovered
    the drive. Prefer the bulk-reader descriptor variant below.
18. `--gateway-cdb-bulk-with-cdd-descriptor-replay` is the live-tested safer
    successor. It keeps the proven bulk gateway reader and uses `CDB[7:8] ==
    fc dd` as a compact trigger returning `0xcf`. It writes descriptor-derived
    fields plus the `0x4a` CDD field package, but omits `0x4e` status/direct
    prestate to fit. Live result: trigger executed, `0x070000` smoke still
    worked, but decoded CDD targets `0x184000`, `0x184060`, and `0x190690`
    stayed all zero. Evidence:
    `references/evidence/live/currentboot-cdd-descriptor-trigger-v1.md`.
19. `--gateway-cdb-bulk-with-cdd-mapped-header` is the first positive
    controller-CDD foothold. It keeps the proven bulk gateway reader and uses
    `CDB[7:8] == fc de` as a compact trigger returning `0xd0`. The trigger sets
    the `0x1717` mapped-header call up for source `0x0000702c` and destination
    `xdata[0xc000]`, then copies `xdata[0xc000..0xc01f]` into the response.
    Live result: response byte `0x20` was `0xd0`, and response `0x21..0x40`
    contained the LD5M CDD header beginning `43 44 44 09 10 16`. Decoded CDD
    target addresses still stayed zero, so this is not the full expansion
    trigger, but it proves the currentboot hook can safely call `0x1717` and
    observe the mapped `0xc000` window. Evidence:
    `references/evidence/live/currentboot-cdd-mapped-header-trigger-v1.md`.
20. `--gateway-cdb-bulk-with-cdd-mapped-header-status` extends that foothold.
    It uses `CDB[7:8] == fc df`, returns `0xd1`, copies the mapped CDD header
    from `xdata[0xc000..0xc01f]`, and also copies
    `xdata[0x4e80..0x4e9f]` after the `0x1717` call. Live result:
    `0x4e80..0x4e9f` was
    `000000000000000000000000010000000040704c0008001f0000000000000000`;
    decoded CDD target addresses still stayed zero. Evidence:
    `references/evidence/live/currentboot-cdd-mapped-header-status-trigger-v1.md`.
21. `--gateway-cdb-bulk-with-cdd-mapped-header-status64` widens the status
    capture through `0x4ebf`. It uses `CDB[7:8] == fc e0`, returns `0xd2`,
    and copies `xdata[0xc000..0xc01f]` plus `xdata[0x4e80..0x4ebf]`.
    Live result: `0x4ea0 = 0x06`, matching the resident completion poll after
    `0x17bb`; `0x4e90..0x4e97 = 00 40 70 4c 00 08 00 1f`, matching the
    computed end values for source `0x0040702c` and companion `0x0007ffff`
    after a `0x20` byte transfer. Decoded CDD target addresses still stayed
    zero. Evidence:
    `references/evidence/live/currentboot-cdd-mapped-header-status64-trigger-v1.md`.
22. `--gateway-cdb-bulk-with-cdd-parser-call` uses `CDB[7:8] == fc e1`,
    returns `0xd3`, seeds the resident descriptor state, calls `FUN_CODE_002e`
    at `0x002e`, and returns `xdata[0x4a00..0x4a3f]` in response bytes
    `0x21..0x60`. Live result: the trigger returned a populated mailbox,
    including `0x4a00 = 01`, `0x4a01 = 03`, `0x4a03 = 03`,
    `0x4a05..0x4a06 = 14 07`, `0x4a20..0x4a22 = 03 08 10`, and
    `0x4a24..0x4a25 = 03 fe`. Immediate and delayed decoded-target gateway
    reads stayed zero. Evidence:
    `references/evidence/live/currentboot-cdd-parser-call-trigger-v1.md`.
23. `--gateway-cdb-bulk-with-cdd-parser-second-doorbell` uses `CDB[8] == e2`
    as a compact trigger, returns `0xd4`, calls `0x002e`, mirrors
    `xdata[0x4a24/25]` into `xdata[0x4a28/29]`, clears/sets `xdata[0x4a00]`,
    and calls `0x1667`. Live result: trigger executed and the drive recovered,
    but immediate and delayed decoded-target gateway reads still stayed zero.
    Evidence:
    `references/evidence/live/currentboot-cdd-parser-second-doorbell-trigger-v1.md`.
24. Currentboot CDD conclusion as of the parser-call/second-doorbell tests:
    the visible 8051 side of the mailbox can be replayed and observed, but the
    decoded controller range at `0x184000..` still does not appear. Treat
    currentboot as useful for exercising visible parser helpers and command
    mailboxes, not as a proven environment for decoded CDD extraction. The next
    serious readout route probably needs a normal-runtime hook, a hardware
    side-channel, or a deeper controller state transition than `0x002e` plus
    the `0x4a` doorbells.
25. Normal-runtime `READ BUFFER mode=1 id=01 offset=0x070000` now looks like a
    page-frame/cache surface, not just a fixed code/table dump. Repeated
    capture-only reads rotate a small set of informative `0x40` chunks around
    pages like `+0x6000`, `+0x8600`, and `+0x9500`.
26. Safe read-only/no-data-out normal SCSI/MMC stimuli pull additional tiles
    into that same public window. The capture-only control had 704 informative
    unique chunks; the safe-stimulus run had 752, sharing all 704 control
    chunks plus 48 stimulus-only chunks. Evidence:
    `analysis/8051/normal-work-window-tile-harvest-20260501.md`,
    `analysis/8051/normal-work-window-capture-only-20260501.md`,
    `analysis/8051/normal-work-window-stimuli-full-20260501.md`, and
    `analysis/8051/normal-work-window-stimuli-vs-capture-only-20260501.md`.
27. Treat this as a third decoded-material extraction path alongside static CDD
    decoding and slow currentboot gateway readout. Public offsets are probably
    frame slots rather than stable logical addresses, because the same tile can
    appear at multiple offsets. Next useful work is to run broader repeated
    safe-stimulus corpora and correlate unique chunks with known 8051 code and
    command handlers.
28. A focused eight-cycle repeat of EXTRAINQ, `MODE SENSE(10)`,
    `GET CONFIGURATION` current/all, and `GET EVENT STATUS NOTIFICATION`
    produced 751 informative chunks, 15 of them new relative to the first
    full-stimulus run. The aggregate corpus across capture-only, full-stimulus,
    and focused-stimulus runs is now 68 captures and 767 unique informative
    `0x40` chunks. Evidence:
    `analysis/8051/normal-work-window-chunk-corpus-20260501.md`.
29. An expanded safe-command pass added read capacity, read format capacities,
    individual mode-sense pages, additional event classes, TOC/DVD-structure
    variants, and get-performance. The drive stayed normal `LD5M`; some
    commands returned expected CHECK CONDITION/ILLEGAL REQUEST with no disc.
    This added 18 aggregate chunks. The corpus is now 94 captures and 785
    unique informative `0x40` chunks.
30. Static exact-match correlation against
    `references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin` finds
    only 63 exact chunk matches; against `analysis/8051/ldm58051.bin`, only 8.
    So most harvested chunks are not verbatim 64-byte slices of the known F0 or
    visible 8051 prefix. Evidence:
    `analysis/8051/normal-work-window-chunk-static-matches-20260501.md`.
31. A crude 8051 `MOV DPTR,#xxxx` scan of the harvested chunks finds expected
    anchors like `0x47b1`, `0x4000`, `0x4091`, `0x4098`, and `0x825b`, plus a
    high-frequency runtime-only cluster around `0x8a23` and
    `0x8a4a..0x8a54`. This supports the earlier interpretation that normal
    runtime keeps CDB/packet shadow state around `xdata[0x8a49..]` and that the
    public window is exposing overlay/runtime code that touches it. Evidence:
    `analysis/8051/normal-work-window-dptr-refs-20260501.md`.
32. The overlay/frame atlas for those captures is:
    `analysis/8051/normal-work-window-overlay-map-20260501.md` and
    `analysis/8051/normal-work-window-overlay-map-20260501.json`. It merges
    the capture-only, full-stimulus, focused-stimulus, and expanded-stimulus
    runs into a public-slot map. Current counts: 702 public slots, 785 unique
    informative chunks, 63 exact static matches, 722 runtime/unmatched chunks,
    and 159 chunks seen at multiple public slots.
33. The best immediate runtime-code target from the overlay map is chunk
    `2111cafaf69c` at the rotating `+0x9500/+0x9540/+0x9580/+0x95c0` slots.
    Its bytes include the repeated pattern
    `90 47 b1 e0 90 8a 4c f0 ...`, i.e. copy from `xdata[0x47b1]` into
    `xdata[0x8a4c..]`. This is strong live evidence for the normal-mode
    packet/FIFO-to-CDB-shadow path. Prioritize `0x8a49..0x8a54`, `0x8a23`, and
    `0x8adf` when correlating harvested chunks with command handling.
34. Do not linear-disassemble the `+0xa180..+0xad40` island blindly. The
    overlay analyzer now marks dense low-`LJMP` and branch-plus-DPTR chunks as
    `runtime_branch_table_like_chunks`. Treat that region as a dispatch/table
    structure until the entry width and base targets are mapped.
