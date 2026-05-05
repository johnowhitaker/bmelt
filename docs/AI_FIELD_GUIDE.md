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
- Current live status as of 2026-05-04: Drive #3 is a fresh stock `LD5M`
  target on the Linux host. Its full F0 dump matches the local LD5M reference
  byte-for-byte. A benign helper-bypass write changed only identity date byte
  `F0[0xd8ff4]` from `0x32` to `0x33`, and the matching restore returned the
  full F0 image to the stock SHA-256. Drive #3 is therefore the current clean
  live target for bounded experiments. The original drive is alive but
  non-stock; the spare is bridge/card-reader-only.
- The Linux live workspace is now also a git repo at
  `/home/jonathan/boastermelt`, branch `linux-live-drive3`, with bare sync
  remote `/home/jonathan/bmelt-live.git`. From the Mac repo, fetch it with:

```sh
git fetch linux-live linux-live-drive3
```

Rediscover:

```sh
ssh root@jonathan-thinkpad-t480s 'cd /home/jonathan/boastermelt && python3 scripts/liteon_linux_status.py'
```

## Latest Checkpoint

The fresh-drive pause is over, but Drive #3 should be kept as clean and
well-instrumented as possible:

- DS-8ABSH CDD hard-body decode remains unsolved.
- A broad static pass is contained under `cdd_cracking/`.
- XD13 is the useful new static clue: it has a plaintext-style CDD 8051
  code/data object, useful as a semantic atlas for LD5M decoded/runtime
  fragments.
- Drive #3 baseline evidence and reversible helper-bypass smoke evidence are
  committed on Linux branch `linux-live-drive3`:
  - `3993170 Capture Drive 3 clean LD5M baseline`
  - `80a390c Capture Drive 3 helper-bypass patch restore smoke`
  - Drive #3 also reproduced the currentboot CDD parser-call and
    second-doorbell mailbox tests without touching CDD bytes. Both triggers
    executed (`0xd3` and `0xd4` respectively), but decoded-target gateway
    reads at `0x184000`, `0x184060`, and `0x190690` remained all zero. The
    final full F0 verification returned to stock SHA-256.
- Drive #3 appears to have shipped with media inserted. If event-1/profile-tail
  entry fails with `Not Ready / Logical unit is in process of becoming ready`
  after a Pico power cycle, wait 25 to 30 seconds and retry. The tray was
  ejected after the 2026-05-04 parser pass so the media can be removed.
- Drive #3 later passed the normal READ BUFFER hook carryover safety gate in
  the negative direction: a harmless currentboot gateway marker at controller
  `0x074030` wrote and read back while currentboot was active, but `sg_reset`
  and USB reauth stayed in currentboot, while stock recovery returned to
  `LD5M` and wiped the marker. Do not attempt the planned shared-code normal
  hook through currentboot volatile carryover. See
  `analysis/8051/drive3-normal-hook-carryover-20260504.md`.

Start with these scratch summaries if revisiting the CDD/static angle:

```text
cdd_cracking/cdd_hail_mary_summary_20260502.md
cdd_cracking/completion_audit.md
cdd_cracking/cdd-xd13-structure.md
cdd_cracking/cdd-xd13-high-confidence-homologs.md
cdd_cracking/cdd-runtime-control-targets.md
cdd_cracking/cdd-controller-gateway-atlas.md
```

Important XD13 interpretation: use it as a semantic/register atlas, not as a
byte-patch source. The stable cross-family anchors are the hardware-facing
`0x40xx` controller gateway and `0x47b1` packet/FIFO stream. Family-local
normal-runtime shadow addresses around `0x88xx..0x8axx` retarget.

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

Mapped-source/currentboot byte-oracle hook:

```text
scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-bulk-cdd-mapped-source-v1 \
  --gateway-cdb-bulk-with-cdd-mapped-source \
  --cave-len 0xdd

references/firmware/extracted/currentboot-response-hook-candidates/
  currentboot-response-hook-gateway-bulk-cdd-mapped-source-v1/

scripts/read_liteon_currentboot_cdd_mapped_source.py
```

The corrected live workflow is important:

1. Install the currentboot response hook through the full helper-bypass replay.
2. Cold power-cycle the drive/bridge.
3. Send only the profile-tail/event-1 entry step.
4. Query the hook while the drive remains in currentboot.

If the hook is admitted and the drive boots normal `LD5M`, normal mode no
longer reaches the currentboot response handler at `0x4fc9`.

Live spare result:

```text
references/evidence/live/currentboot-mapped-source-hook-v1-spare-20260502/
```

Current state of the primitive:

- The original normal-mode attempt was a useful negative: after successful
  admission/normal boot, the special CDB returned stock `"LD5M..."`, not marker
  `0xd5`.
- In currentboot, the fixed-header call to resident helper `0x1717` returns the
  LD5M CDD header from source `0x702c`.
- The status64 diagnostic proved arbitrary host-selected source addresses reach
  `0x1717`; `xdata[0x4e90..0x4e93]` reported
  `0x400000 + requested_address + 0x20`.
- The compact `0xd7` window hook exposes the useful mapped byte at
  `xdata[0xc07f]`.
- `scripts/read_liteon_currentboot_cdd_mapped_source.py` has
  `--d7-c07f-byte-oracle`, which reads one mapped byte per SCSI command.

Proof read:

```text
source 0x28119 -> d8 19 20 0a 7a dd 2a ad 9f 56 a3 49 38 51 aa cc
```

That matches stock `F0[0x28119..0x28128]`, so this is a reliable CDD
source/controller-address read oracle. It is much faster and safer than the old
timing/bit channels for targeted byte reads.

The same oracle can read nonzero bytes around controller `0x184000`, but the
sampled bytes look high-entropy and do not disassemble like the known
normal-mode record-59 overlay. Treat this as a controller address surface, not
as a solved flat decoded CDD dump.

Normal-mode I/O status:

- `normal_mailbox_probe.py` found a real volatile MODE SELECT bit on page
  `0x08`, but no direct response channel yet.
- `analysis/8051/normal-mode-read-buffer-hook-plan-20260504.md` lays out a
  conservative READ BUFFER response-redirect proof.
- `analysis/8051/drive3-normal-hook-carryover-20260504.md` closes the first
  proposed delivery route: currentboot gateway writes do not carry into normal
  mode through the available soft/recovery transitions.
- Pressed-DVD `REPORT KEY` / `SEND KEY` is a real normal bidirectional command
  path. The host challenge affects key1 deterministically, but the nonce does
  not appear in the public work-window.
- `REPORT KEY format 8` is the safest grounded normal branch. The selector
  jumps to `0x6f62`, and branch-body evidence points at a mechanics/status
  routine around `0x4867`, `0x486a`, `0x486b`, and `0x590x`, not a direct
  response generator. See
  `analysis/8051/drive3-normal-hook-poc-status-20260505.md`.
- The proven MODE SELECT bit was tested as a selector for `REPORT KEY format 8`;
  it round-tripped cleanly but did not change the direct RPC-state response.
  Re-run with `scripts/probe_liteon_mode_bit_observer.py` if needed.
- The next normal-mode work should look for a true normal writable mailbox or
  an explicitly approved safe CDD/runtime delivery route, not patch shared code
  through unproven currentboot carryover.

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

Live correction from 2026-05-01: the builder now checks `CDB[10] == a5`
directly. An earlier write-only build used the wrong guard-byte order and fell
through to the gateway reader. The corrected candidate was installed and
smoke-tested with both a bulk gateway read and an XDATA write.

Write mode uses:

```text
CDB[5] low six bits = selector
CDB[7:8]            = 16-bit XDATA base
CDB[9]              = write value
CDB[10:11]          = write magic a5 5a
response[0x20]      = readback byte
```

There is also a rebuilt combined read/write hook with the same default gateway
bulk mode. As of the 2026-05-01 smoke test, prefer the write-only candidate
above; if using the RW candidate, use it only as:

```text
bulk gateway read + guarded XDATA write
```

Do not use the RW candidate's XDATA-read branch for routine work. The
`CDB[10] = 5a` read branch timed out live and blocked the SCSI path until the
stuck host process was killed and the drive was Pico power-cycled.

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2/currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2-candidate.json
```

The host-facing convention for v2 is:

```text
normal gateway read     CDB[10] = 00 and CDB[11] = 00
guarded XDATA write     CDB[10] = a5, CDB[9] = value
guarded XDATA read      CDB[10] = 5a   # live-hangs; avoid
unknown nonzero selector returns 0xee instead of falling into gateway mode
```

Working write smoke:

```sh
ssh root@jonathan-thinkpad-t480s \
  'cd /home/jonathan/boastermelt && python3 scripts/write_liteon_currentboot_xdata.py \
    --device /dev/sg0 \
    --address 0x8000 \
    --value 0x5a'
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
34. Do not linear-disassemble the `+0xa180..+0xcaab` island blindly. The
    overlay analyzer now marks dense low-`LJMP` and branch-plus-DPTR chunks as
    `runtime_branch_table_like_chunks`. Treat that region as a dispatch/table
    structure until the entry width and base targets are mapped.
35. The packet-shadow focused report is
    `analysis/8051/normal-packet-shadow-analysis-20260501.md`. It scans whole
    captured windows for `MOV DPTR; MOVX` idioms across chunk boundaries. Main
    result: the normal runtime copies bytes from `xdata[0x47b1]` into the
    command shadow `xdata[0x8a49..0x8a54]`. `0x8a49` is the best current
    selector/opcode candidate; it is compared with values including `0x28`,
    `0x03`, `0x2a`, `0x55`, `0xa3`, and `0xa4`.
36. The same report maps the next handoff layer. Shadow/controller edges
    include `0x8a4c..0x8a4e -> 0x4011..0x4013`,
    `0x8ac6 -> 0x4091/0x4095`, `0x8a4e/0x8a53/0x8a54 -> 0x4099`,
    `0x8a54 -> 0x40b7`, and `0x8a5b/0x8a5c -> 0x4096/0x4097`.
    Controller setup bytes are also mirrored back from `0x4095..0x4097` into
    `0x8ade/0x8aeb/0x8aec`. Prioritize snippets around public offsets
    `+0x7140/+0x7180`, `+0x7380`, `+0x74c0`, `+0x95xx`, and
    `+0xdc00/+0xdc40`.
37. Four isolated read-only normal captures were run after the packet-shadow
    report. Evidence dirs:
    `references/evidence/live/normal-work-window-isolated-extrainq-20260501`,
    `normal-work-window-isolated-get-config-current-20260501`,
    `normal-work-window-isolated-mode-sense-all-20260501`, and
    `normal-work-window-isolated-event-media-20260501`. Summary report:
    `analysis/8051/normal-work-window-isolated-stimulus-diffs-20260501.md`.
    The drive stayed normal `LD5M`. GET CONFIGURATION current had the clearest
    recurring stimulus-only chunks with target references; event-status media
    added no stimulus-only chunks in the short six-cycle pass.
38. The dispatch/table island now has a concrete parser:
    `scripts/analyze_liteon_normal_dispatch_table.py`. It decodes
    `analysis/8051/normal-work-window-dispatch-table-20260501.md/json` from
    the normal capture-only window. The regular table starts at public
    `+0xa17f`, ends at `+0xcaab`, and contains 1,762 entries:
    entries `0..31` are `MOV A,#selector; LJMP 0x0162`; entries `32..1761`
    are `MOV DPTR,#param; LJMP 0x01xx/0x02xx`.
39. Mapping caveat for that table: public low offsets in the `0x070000` window
    do not match `analysis/8051/ldm58051.bin`, but the low `LJMP` targets land
    on plausible resident helper offsets such as `0x0215`, `0x0184`,
    `0x01ac`, `0x01ed`, `0x01a2`, `0x0206`, and `0x0201`. Do not claim this
    is a flat code-space dump. The current best label is a banked/threaded
    runtime artifact. The next questions are what indexes the first 32
    selector entries, what the 16-bit `param` values mean, and whether table
    indices correlate with `xdata[0x8a49]` packet selectors or the CDD
    record/lane schedule.
40. A longer read-only isolated GET CONFIGURATION current run was captured in
    `references/evidence/live/normal-work-window-get-config-current-long-20260501`
    and summarized in
    `analysis/8051/normal-work-window-get-config-current-long-20260501.md`.
    It alternated 16 baseline captures with 16 GET CONFIGURATION current
    captures. The drive stayed normal `LD5M`. The run added no new aggregate
    chunks, but it cleanly tagged two recurring stimulus-only chunks in the
    controller bridge corridor.
41. Those tagged GET CONFIGURATION chunks are the best current concrete code
    snippets for the normal packet/controller handoff. One waits on
    `xdata[0x4000].7`, writes `xdata[0x8ac6]` and IRAM-derived bytes into
    `0x4091..0x4093`, kicks/polls `0x409c`, then reads `0x4099`. The companion
    chunk reads `0x4099` back into `xdata[0x8a4e]`, `0x8a53`, and `0x8a54`.
    This confirms `0x8a4b..0x8a54` is an active packet/controller shadow, not
    merely a passive CDB copy.
42. `scripts/analyze_liteon_normal_packet_shadow.py` now has a small
    linear-DPTR stream pass for local `MOVX` idioms. It is deliberately
    heuristic, but it catches the important `INC DPTR` and repeated-command
    patterns that direct `MOV DPTR; MOVX` copy scans miss. The current report
    names six recurring controller transaction classes: read-side setup
    through `0x4091..0x4093`, write-side setup through `0x4095..0x4097`,
    `0x409c=0x40/0x24` read kicks, packet-shadow commands that stream bytes
    through `0x4099` and then write `0x409a=0`, `0x409b=1`, `0x409c=0x14`,
    a controller FIFO writer through `0x4098`, and restoration of the mirrored
    controller setup from `0x8ade/0x8aec/0x8aeb`.
43. That matters because it turns the normal-mode bridge into a small protocol
    sketch. The host packet stream enters through `0x47b1`, is shadowed around
    `0x8a49..0x8a54`, then gets translated into two controller register
    families: `0x4091..0x4093` for read-like setup and `0x4095..0x4097` for
    write/FIFO setup. `0x4099` is a data/FIFO port, while `0x409c` is the
    command/kick/poll register. The `0x4860..0x486a` cluster also appears
    frequently near the `0x4099/0x409c=0x14` path and remains a good
    mechanics/servo-adjacent candidate, but do not treat it as confirmed LED
    or sled control yet.
44. The first dedicated note on that cluster is
    `analysis/8051/normal-4860-cluster-20260501.md`. Current interpretation:
    `0x4860.2` and `0x4864.0` behave like paired enable/ack bits in normal
    runtime paths; `0x4867.7` is toggled together with `0x480b.4`; `0x4863`
    is mirrored through `xdata[0x8630]`; and `0x4862` is written or bit2-cleared
    in a separate path. This looks hardware-control or mechanics-adjacent, but
    it may be a controller mailbox rather than raw actuator GPIO.
45. The normal controller bridge may also be a future fast read oracle. See
    `analysis/8051/normal-controller-read-primitive-hypothesis-20260501.md`.
    The candidate path waits on `0x4000.7`, writes setup bytes into
    `0x4091..0x4093`, writes `0x409c=0x40` and then `0x20` or `0x24`, polls
    `0x409c.5`, and reads from `0x4098` or `0x4099`. Packet-shadow bytes
    `0x8a4d` and `0x8a4e` look especially relevant: `0x8a4d` is capped at
    `0x12`, rounded if odd, and copied to `0x47d6`; `0x8a4e & 0x0f` selects
    a subpath/status slot. If legal host commands control those fields, this
    could become a much faster decoded/controller-memory oracle than the
    currentboot bit channel.
46. A read-only GET CONFIGURATION variant run is tracked in
    `references/evidence/live/normal-work-window-get-config-variants-20260501`
    and summarized in
    `analysis/8051/normal-work-window-get-config-variants-20260501.md`.
    It varied request type, starting feature, and allocation length over two
    cycles. All commands returned GOOD, host response lengths varied as expected,
    and the drive stayed normal `LD5M`. The bridge chunks recurred, but the
    two-cycle run did not cleanly separate them by GET CONFIG field value; treat
    it as "GET CONFIG tags the bridge" evidence, not yet as proof of address
    control.
47. The selector compare map is now separated into
    `scripts/analyze_liteon_normal_packet_selectors.py` and
    `analysis/8051/normal-packet-selector-map-20260501.md/json`. It condenses
    the `0x8a49..0x8a54` shadow checks and copy edges. `0x8a49` is compared
    against opcode-like values including `0x03`, `0x1b`, `0x28`, `0x2a`,
    `0x55`, `0xa3`, `0xa4`, and LiteOn/vendor `0xe3/0xe6/0xe7`. The
    `+0x8bxx` START STOP snippet anchors the byte map: it checks
    `0x8a49 == 0x1b` and `(0x8a4d & 0x0f) == 0x02`, matching CDB byte 4's
    load/eject/start control bits. Treat `0x8a49..0x8a54` as CDB bytes 0..11,
    with later bytes also reused as controller data/status-shadow bytes in some
    paths. A plain `0x8a49 == 0x46` GET
    CONFIGURATION compare is still absent even though GET CONFIG tags the
    bridge dynamically, so that path is likely table-driven, handled through an
    unharvested slice, or dispatched before this compare cluster.
48. A focused read/status correlation run is in
    `references/evidence/live/normal-work-window-readstatus-correlation-20260501`
    with reports
    `analysis/8051/normal-work-window-readstatus-correlation-20260501.md`,
    `analysis/8051/normal-packet-selector-map-readstatus-20260501.md`, and
    `analysis/8051/normal-readstatus-correlation-20260501.md`. It ran four
    cycles of baseline, REQUEST SENSE, READ TOC formats `0/1/2/4`, and GET
    PERFORMANCE types `0/3`; the drive stayed normal `LD5M`. The no-disc
    READ TOC and GET PERFORMANCE type00 failure paths consistently exposed a
    stimulus-only `+0x8bxx` chunk referencing `0x8a49` and `0x8a4d`, plus a
    less frequent `+0x7140/+0x7180` `0x4098` gateway-looking chunk. The `+0x8bxx`
    bytes also identify an eject-style START STOP check, making it both an
    error/status-path clue and a mechanics-path clue. This is separate from the
    GET CONFIG good-response `0x4099` bridge.
49. A paired failure/sense follow-up is in
    `references/evidence/live/normal-work-window-error-path-pairs-20260501`
    with reports
    `analysis/8051/normal-work-window-error-path-pairs-20260501.md`,
    `analysis/8051/normal-packet-selector-map-error-pairs-20260501.md`, and
    `analysis/8051/normal-error-path-pairs-20260501.md`. It sends a failing
    READ TOC or GET PERFORMANCE type00, captures the work window, then sends
    REQUEST SENSE and captures again. It did not produce a clean after-command
    versus after-sense split; recurring chunks touched `0x4098` and `0x8a23`
    in both phases. Treat it as evidence that this public window is sampling a
    longer shared error/status path rather than a neatly command-bounded one.
50. `analysis/8051/normal-start-stop-mechanics-path-20260501.md` pulls the
    `+0x8bxx` START STOP clue together with the `0x4860` cluster. The branch
    checks `0x8a49 == 0x1b` and `(0x8a4d & 0x0f) == 0x02`, then nearby code
    gates on `0x480e`, clears `0x48a5.4` and `0x4762.4`, and prepares
    `0x4860.2` handling. A complete paired setter appears separately in the
    `+0x92xx` family as `0x4860.2` plus `0x4864.0`, while the cleanup side
    clears `0x4864.0`, `0x5905` bits, `0x5a01` bits, and `0x4860.2`.
    Current working model: host CDB -> `0x8a49..` packet shadow -> START
    STOP/control check -> `0x480e/0x48a5/0x4762` state gates ->
    `0x4860/0x4864` controller-facing mechanics state -> `0x5905/0x5a01`
    mechanics/servo family. Do not write those registers blindly; the next
    useful live step is branch/state telemetry around a natural or deliberate
    START STOP event. `scripts/capture_liteon_normal_start_stop_path.py` is the
    gated capture tool for that pass; it prints CDBs and captures baseline by
    default, and requires `--allow-start-stop` before sending any START STOP
    command.
51. The START STOP capture tool was sanity-checked on
    `jonathan-thinkpad-t480s` without `--allow-start-stop`; see
    `analysis/8051/normal-start-stop-path-dryrun-20260501.md` and
    `references/evidence/live/normal-start-stop-path-dryrun-20260501`. It
    planned `1B 00 00 00 02 00` (`eject`) but did not send it, captured a
    baseline `READ BUFFER id=01 offset=0x070000` window, and the drive stayed
    normal `LD5M`.
52. The first deliberate START STOP eject run is summarized in
    `analysis/8051/normal-start-stop-eject-live-20260501.md` with evidence in
    `references/evidence/live/normal-start-stop-eject-20260501` and
    `normal-start-stop-eject-late-20260501`, plus a repeated delayed capture
    in `normal-start-stop-eject-delayed-20260501`. Sent CDB:
    `1B 00 00 00 02 00`. The user saw the sled/eject dance, so the static
    `0x8a49 == 0x1b` / `(0x8a4d & 0x0f) == 0x02` branch is a real mechanics
    route. Immediate post-command `READ BUFFER id=01` timed out during the
    transition. A repeated run with one-second post-command delays still timed
    out on the first two after-windows, then recovered; `REQUEST SENSE`,
    `MECHANISM STATUS`, and `/dev/sg0` all ended normal `LD5M`. The capture
    script now records failures and saves summaries incrementally.
53. `analysis/8051/normal-start-stop-variant-matrix-20260501.md` compares all
    four ordinary START STOP low-nibble variants. `stop` (`0x00`) and `start`
    (`0x01`) returned quick CHECK/Not Ready with no post-window failures.
    `load` (`0x03`) returned quick CHECK/Illegal Request with no post-window
    failures. Only `eject` (`0x02`) caused visible motion, rc `99`
    DID_TIME_OUT, and temporary `READ BUFFER id=01` timeouts. This strongly
    supports that the `+0x8bxx` branch is specifically the eject case, not
    generic START STOP handling.
54. `analysis/8051/normal-start-stop-hook-plan-20260501.md` is the current
    hook plan after the live eject confirmation. Main caution: START STOP eject
    is a good trigger, but not a good immediate reply channel because the drive
    is busy for several seconds. A useful hook should capture state first and
    read it later through a boring command path, or eventually suppress the
    actuator path after capture. The bigger blocker is patchability: the
    `+0x8bxx` work-window bytes are normal-runtime overlay material, not proven
    visible F0-prefix bytes. Prior visible-F0 hooks at `0x4ec6` and `0x5c72`
    persisted but did not affect normal command timing. Next priority is a
    normal-mode response hook that is live and patchable; only after that should
    START STOP be used again for telemetry.
55. `analysis/8051/normal-work-window-reference-localization-20260501.md` and
    `analysis/8051/normal-currentboot-work-window-overlap-20260501.md` compare
    the normal work-window chunks against F0, the visible 8051 prefix, the
    helper, currentboot XDATA, currentboot gateway `0x070000`, and normal
    `id01/id02` snapshots. Out of 908 unique normal chunks, only 63 match F0,
    8 match the visible prefix, 0 match the helper, and 2 match currentboot
    XDATA, but 510 match the currentboot gateway and 693 match each normal
    `id01/id02` reference. The currentboot/normal exact same-offset overlap is
    strongest at `+0xa000..+0xde80`, `+0xe000..+0xfd80`, and `+0x4000..+0x4500`.
    The START STOP `+0x8bxx` branch still does not localize to F0/helper or an
    obvious currentboot gateway chunk, while the `+0x92xx/+0x93xx/+0x95xx`
    mechanics cluster has several small shifted currentboot overlaps.
56. `analysis/8051/currentboot-gateway-write-hook-plan-20260501.md` adds the
    next volatile primitive: `--gateway-cdb-rw` in
    `scripts/build_liteon_currentboot_response_hook_candidate.py`, plus
    `scripts/write_liteon_currentboot_gateway.py` and
    `scripts/write_liteon_currentboot_gateway_blob.py`. The hook reads the
    controller gateway normally, but if CDB[10] is `5a`, it writes CDB[11]
    through `0x4095..0x4098` and returns readback. Use a v2 artifact name: v1
    also checked CDB[6], installed cleanly, and read `Flash Type Error` from
    `0x018620`, but its write branch did not fire. V2 is live-proven:
    `0x018620` changed from `Flash Type Error` to `Glash Type Error` and was
    restored. A harmless `0x074030` marker showed no trivial carryover into
    normal mode: bare `PLDSVUC` stayed currentboot, and full recovery wiped the
    marker before normal `READ BUFFER`. The Linux persistence runner also has
    `--gateway-patch-after-event EVENT:ADDR:HEX` and
    `--gateway-patch-after-phase PHASE:ADDR:HEX`; a live event-1 smoke test
    used it to patch the helper string to `Glash` immediately after profile
    tail entry.
57. `scripts/capture_liteon_normal_get_config_field_variants.py` probes the
    GET CONFIGURATION bridge without data-out or mechanics. Evidence is in
    `references/evidence/live/normal-work-window-get-config-field-variants-20260501`,
    `normal-work-window-get-config-field-variants-r5-long-20260501`,
    `normal-work-window-get-config-r5-01-isolated-20260501`, and
    `normal-work-window-get-config-r5-f0-isolated-20260501`; the summary is
    `analysis/8051/normal-get-config-field-variant-findings-20260501.md`.
    Varying reserved GET CONFIG CDB bytes 4, 5, 6, and 9 was tolerated: every
    variant returned GOOD and the drive stayed `LD5M`. The host-visible response
    was unchanged for reserved-field variants. Bridge chunks touching
    `0x4091`, `0x4093`, `0x4099`, and `0x8a4d/0x8a4e` recurred, but longer
    isolated byte-5 runs show this is still mostly "GET CONFIG tags the bridge"
    evidence, not proof that those reserved bytes control the bridge address or
    returned data. Use plain GET CONFIG/current as a safe bridge tagger; do not
    treat reserved-byte fuzzing as a solved normal read oracle.
58. `analysis/8051/normal-read-buffer-capture-bridge-correction-20260501.md`
    corrects the bridge interpretation. The normal stimulus captures always
    end with a `READ BUFFER id=01 offset=0x070000` work-window read. The
    strongest bridge edge, `0x8a4c..0x8a4e -> 0x4011..0x4013`, lines up exactly
    with READ BUFFER CDB bytes 3..5, the 24-bit buffer offset. So this bridge
    is most likely the normal READ BUFFER handler's public offset path, not a
    GET CONFIG hidden-address path. Practical consequence: we already control
    this stock oracle, but its mapped surface is constrained to the public
    work-window/mirror space. It still does not reach decoded CDD memory at
    `0x184000..0x1b3fff`.
59. `scripts/scan_liteon_read_buffer_modes.py` scans READ BUFFER CDB byte 1 as
    a full 8-bit mode byte while staying read-only/no-data-out. Evidence is in
    `references/evidence/live/normal-read-buffer-mode-byte-scan-20260501` and
    the summary is
    `analysis/8051/normal-read-buffer-high-mode-and-get-performance-harvest-20260501.md`.
    A smoke pass over representative high values and a full pass over
    `0x20..0xff` against IDs `0x01`, `0x02`, `0xe2`, `0xf0`, `0xf1`, and
    `0xf2` found no hidden selector: all 1344 full-pass reads returned `rc=5`
    with no data, no partial windows, and no timeouts.
60. `scripts/capture_liteon_normal_get_performance_variants.py` sends
    read-only GET PERFORMANCE variants and captures
    `READ BUFFER mode=1 id=01 offset=0x070000` after each one. Evidence is in
    `references/evidence/live/normal-work-window-get-performance-variants-20260501`
    and
    `references/evidence/live/normal-work-window-get-performance-variants-long-20260501`.
    The first two-cycle pass added 77 new chunks to the normal work-window
    corpus; the four-cycle repeat added zero more. Current combined corpus:
    6 runs, 208 captures, 862 unique informative chunks, 63 static-matched
    chunks, 799 runtime/unmatched chunks. GET PERFORMANCE is useful as a
    one-time normal-runtime tile harvest, but does not look like a direct
    decoded-memory oracle.
61. Interpret the GET PERFORMANCE `+0x8bxx` tile carefully. It references
    `0x8a49` and `0x8a4d`, but the branch checks match the already-confirmed
    START STOP eject condition: opcode `0x1b` and low nibble `0x02`. This is
    an overlay tile made visible during the capture sequence, not evidence
    that GET PERFORMANCE executes the eject path.
62. `analysis/8051/normal-packet-shadow-all-runs-findings-20260501.md`
    updates the packet-shadow view using every saved normal work-window
    directory: 19 dirs, 509 captures. Reports are
    `analysis/8051/normal-packet-shadow-all-runs-20260501.md/json` and
    `analysis/8051/normal-packet-selector-map-all-runs-20260501.md/json`.
    Main correction: `0x8a49` remains the opcode-like selector, but later
    bytes such as `0x8a4d`, `0x8a4e`, `0x8a53`, and `0x8a54` are reused as
    controller/status scratch, not permanently just CDB bytes.
63. The GET CONFIG-specific slice is now sharper:
    `0x4099 -> 0x8a4d/0x8a4e/0x8a53/0x8a54`, followed by
    `0x8a4d == 0xfe`. That pattern appears 39 times and only in
    GET CONFIG-oriented capture directories. Treat it as a controller-backed
    feature-list/response-builder sentinel, not as an arbitrary memory oracle.
    The generic `0x8a4c..0x8a4e -> 0x4011..0x4013` pattern appears in all
    captures and belongs to public READ BUFFER response plumbing.
64. `scripts/stitch_liteon_normal_controller_islands.py` and
    `analysis/8051/normal-controller-island-stitch-20260501.md/json` treat the
    normal work-window as rotating `0x40`-byte tiles instead of a guaranteed
    linear image. The strongest GET CONFIG path is
    `4037c8574920 -> 8d8c3b0a22a0 -> 20ea2ab16891`: wait on `0x4000.7`,
    set `0x4091..0x4093`, kick `0x409c=0x40/0x24`, read four bytes from
    `0x4099` into `0x8a4d/0x8a4e/0x8a53/0x8a54`, branch on
    `0x8a4d == 0xfe`, then feed the public `0x4011..0x4013` response bridge.
65. `analysis/8051/normal-controller-island-patchability-20260501.md`
    checks exact localization. The GET CONFIG-specific setup/seed chunks are
    not in F0, the saved currentboot gateway dump, or baseline normal id01/id02.
    They are transient/stimulus-visible. The public bridge chunk
    `20ea2ab16891` is stable in baseline normal id01/id02 at `+0x7140`, but
    currentboot `+0x7140` is unrelated. Practical patch implication: a normal
    response hook should target a true normal-mode RAM/controller write or a
    proven state-carryover primitive, not a guessed visible-F0 offset.
66. `scripts/analyze_liteon_normal_hidden_runtime_chunks.py` and
    `analysis/8051/normal-hidden-runtime-chunks-20260501.md/json` classify all
    saved normal-mode `0x070000` work-window captures as rotating `0x40`-byte
    tiles. Corpus: 509 captures, 888 unique chunks, 501 chunks with exact
    visible/currentboot/helper reference matches, and 387 chunks without such
    matches. Hidden-but-stable chunks include the public response bridge
    `20ea2ab16891`, GET CONFIG seed `8d8c3b0a22a0`, and controller setup
    chunk `4037c8574920`. The important caution is that the same chunk appears
    at multiple public offsets, so public slot numbers like `+0x7140` cannot
    be treated as direct decoded CDD addresses without a separate phase/address
    model. A bridge-aligned global phase test made stability worse
    (`746` raw positions >=95% stable versus `244` bridge-aligned), so the
    bridge is only a local anchor, not a universal window scroll key. Use this
    corpus as hidden-runtime code evidence, not as a linear decoded CDD dump.
67. `analysis/8051/normal-controller-write-side-overlap-20260501.md` identifies
    a better currentboot-to-normal patchability candidate than the response
    bridge. Normal chunks `e2488fa3edce` (`+0xdbc0`), `cf3469eae7d0`
    (`+0xdc00`), and `ebaf1ca1d57c` (`+0xdc40`) appear in every normal capture
    and exactly match the saved currentboot gateway dump. They save
    `0x4095..0x4097` into `0x8ade/0x8aec/0x8aeb`, write a temporary controller
    command through `0x4095..0x4098`, then restore the old state. This is not a
    safe casual patch site, but it is the best current marker-carryover test
    region because it is genuinely shared between currentboot and normal.
68. `scripts/analyze_liteon_trailer_split_hypotheses.py` and
    `references/firmware/extracted/liteon-trailer-split-hypotheses.md/json`
    specifically test the "2-byte additive checksum + 12-byte CDD unit
    checksum" idea for trailer auth14. Across LD5M, AD12, AHS9, CD12, CHS7,
    and CHS9 there are zero exact matches and zero retained near misses. It
    tried every contiguous 2-byte auth14 slice against low-16 additive
    variants over plausible regions, then tried the remaining 12 bytes as
    column-wise checksums over obvious 12-byte and 13-byte CDD unit streams.
    Treat this split as negative unless a new nontrivial algorithm appears.
69. `scripts/analyze_liteon_cdd_hidden_runtime_correlation.py` and
    `analysis/8051/cdd-hidden-runtime-correlation-20260501.md/json` treat
    stable normal hidden-runtime chunks as possible known-output candidates for
    CDD hard-mode records. Under the naive public-offset mapping, stable hidden
    chunks mostly land on mode `0x40`/`0x80` records, but raw/fixed-XOR seed
    checks against those source spans are negative. This does not disprove a
    CDD relationship; it says the relationship is not simple copying, fixed
    XOR, or obvious byte unpacking.
70. `scripts/analyze_liteon_cdd_affine_live_diff.py` and
    `analysis/8051/cdd-affine-g105-live-diff-20260501.md/json` compare the
    reversible live edits to CDD stream 2 affine group 105. Stock group 105
    decodes as `0x84`; the live tests rewrote all 12 observed affine lead
    cells so it decoded as `0x85` and `0x8b`, then restored it. Both mutated
    states cold-booted as `LD5M`, and the final restore verified byte-identical
    F0. This proves at least this affine leaf class is mutable through the
    helper bypass without solving trailer auth14.
71. The group-105 normal work-window result is not a direct decoded-byte
    oracle. The analyzer finds 62 clean reversible public-window chunk offsets,
    plus another noisy mutation-sensitive set. Many rows are full 0x40-byte
    tile moves. Treat the result as evidence that the CDD leaf influences
    normal runtime state, not as a linear CDD dump or stable internal address.
    Low offsets `+0x01c0` and `+0x0280` are useful correlation targets, but
    `+0x0180/+0x0200/+0x0240` also show stock-to-stock drift between cold
    boots.
72. For post-currentboot/finalizer F0 verification, send a live EXTRAINQ before
    trusting F0 READ BUFFER decrypts. After the `0x84->0x8b` test, F0 reads
    decrypted as nonsense until a live EXTRAINQ primed the readback state; the
    same static LD5M key then produced the normal `BOOT` prefix again. Use
    `scripts/dump_liteon_linux_f0_window.py --prime-extrainq` for this case.
73. `scripts/plan_liteon_cdd_affine_group_patch.py` plans structured CDD
    affine leaf edits. Given an image, group, and target decoded byte, it emits
    exact `--patch offset:byte` arguments plus matching restore arguments for
    every observed affine lead cell. This keeps live CDD edits consistent with
    the affine mask model instead of flipping one arbitrary encoded byte.
74. The second live CDD affine edit targeted CDD stream 2 group 99. Stock
    group 99 decodes as `0x0a`; the live test rewrote all 12 observed lead
    cells so it decoded as `0x0b`, then restored them. Both mutation and
    restore were verified after hardware cold boot with live EXTRAINQ-primed
    F0 dumps. Target bytes changed to
    `6f 76 5d 44 c3 da f1 e8 a7 be 95 8c`, then restored to
    `6e 77 5c 45 c2 db f0 e9 a6 bf 94 8d`.
75. `scripts/analyze_liteon_cdd_affine_experiment.py` and
    `analysis/8051/cdd-affine-g99-live-diff-20260501.md/json` compare the
    group-99 normal-mode captures. The analyzer found 1013 common stable
    offsets and 107 clean stock-consistent mutation offsets. As with group 105,
    treat these as public-window correlation targets, not decoded CDD memory.
76. `scripts/compare_liteon_cdd_affine_live_reports.py` and
    `analysis/8051/cdd-affine-cross-group-correlation-20260501.md/json`
    intersect the group-105 and group-99 reports. There are 31 overlapping
    clean offsets. The useful ones to try first for normal-mode hook detection
    are `+0x01c0`, `+0x0280`, `+0x7140`, `+0x7180`, and the
    `+0x9b00/+0x9b40/+0x9b80` tile-rotation trio.
77. `analysis/8051/normal-mode-io-correlation-plan-20260501.md` summarizes how
    to use the CDD affine overlap set. The important shift is to use overlap
    offsets as a detector for future normal-mode hooks or state-carryover
    tests. Do not patch the public work-window by offset; it is a viewing
    surface with rotating 0x40-byte tiles.
78. `scripts/dump_liteon_linux_f0_window.py --prime-extrainq` now accepts a
    successful EXTRAINQ prime even when `sg_raw` prints `NVMe Result=0x0`
    rather than `SCSI Status: Good`. This matters on the Linux bridge path
    after finalizer transitions.
79. A third live CDD affine edit targeted CDD stream 1 group 27. Stock group
    27 decodes as `0xe4`; the live test rewrote all 12 observed full-row lead
    cells so it decoded as `0xe5`, then restored them. The drive cold-booted as
    `LD5M` after mutation and restore, and the group-27 normal-mode report
    found 78 clean stock-consistent offsets:
    `analysis/8051/cdd-affine-g27-live-diff-20260501.md/json`.
80. CDD1 F0 spot readback is more awkward than the late CDD2 pages. Around
    `0x43800..0x43a00`, some single aligned `0x80` reads decrypt correctly
    while adjacent/multi-chunk reads can decrypt as nonsense. Do not treat one
    bad CDD1 multi-chunk decrypt as proof of zeroed flash; use the runner's
    staged readbacks, normal boot, and repeated single aligned reads.
81. `analysis/8051/cdd-affine-triple-correlation-20260501.md` intersects the
    group-27, group-99, and group-105 reports. Counts: `g27=78`, `g99=107`,
    `g105=62`; pairwise overlaps `g27/g99=64`, `g27/g105=24`,
    `g99/g105=31`; triple overlap `21`. General normal-mode hook detector
    offsets should start with `+0x01c0`, `+0x0280`, `+0x8f40`, `+0x8fc0`,
    `+0x9d80`, and `+0x9dc0`. The response bridge pair `+0x7140/+0x7180`
    reacts to the two late CDD2 edits but not to group 27, so treat it as a
    specific bridge probe rather than a universal CDD detector.
82. `fw_static_re_bundle_20260501.zip` is the current external-AI CDD/static
    bundle. It includes `START_HERE.md`, sibling F0 images, the 8051 binary and
    decompile, CDD record maps, affine-lane reports, trailer/auth negatives,
    recent CDD affine live reports, and Claude's short-op plaintext artifacts.
83. `scripts/analyze_liteon_cdd_known_plaintext_pairs.py` builds a candidate
    known-output corpus by pairing encoded CDD record source spans with
    decoded-looking 0x40-byte normal-runtime chunks from the public normal
    work-window. Use the `with-readonly-harvests` report first:
    `analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.md/json`.
84. `analysis/8051/normal-readonly-harvest-20260501.md` documents the latest
    no-write normal-mode harvesting pass. It captured 40 baseline-only windows
    and 8 cycles of safe standard commands from `/dev/sg0`; the drive stayed
    normal `LD5M`. The corpus is now 669 captures / 902 unique 0x40-byte
    chunks.
85. Treat the normal work-window as a passive decoded-runtime tile sampler, not
    as a flat decoded CDD image. The bridge chunk appears at `+0x7140`,
    `+0x7180`, or `+0x7100`; aligning on it makes the rest of the window less
    stable, not more. Use chunk identity and adjacency, not public slot order,
    to reconstruct local hidden-runtime code.
86. The best candidate CDD records for known-output grammar work are currently
    records `51`, `55`, `58`, `60`, `66`, `68`, `70`, and `87`. They have
    enough decoded-looking tile evidence to attack mode `0x40`/`0x80` record
    grammars, and record `58` remains the GET CONFIG / public response-bridge
    neighborhood.
87. `scripts/analyze_liteon_cdd_tile_adjacency.py` builds a graph of adjacent
    decoded-looking normal work-window tiles. The current report is
    `analysis/8051/cdd-tile-adjacency-with-readonly-harvests-20260501.md/json`:
    669 captures, 11,146 adjacent known-chunk observations, 8,850 same-record
    slot observations, and 95 unique same-record slot edges. Use this when you
    need local chunk order rather than just a list of CDD record buckets.
88. `scripts/export_liteon_cdd_known_output_records.py` writes per-record CDD
    known-output kits under
    `analysis/8051/cdd-known-output-records-20260501/`. Each record gets an
    encoded source span, a public-slot consensus `known-output.bin`, a mask,
    and slot metadata. These are not full decoded CDD records, but they are the
    best compact targets for grammar attacks.
89. `analysis/8051/cdd-known-output-code-shape-20260501.md` summarizes the key
    result from those exports: several records are mostly covered and
    disassemble as plausible 8051. Record `87` is 896/1008 bytes known with no
    slot variants; record `51` is 800/816; record `66` is 704/720; record `58`
    is 496/544. The strongest records touch `0x47b1`, `0x4000`, `0x4098`,
    `0x8a4d`, and related packet/controller shadows.
90. This means at least part of the CDD-decoded material is 8051-side overlay
    or 8051-executable code. Do not assume the CDDs are only ARM/DSP/servo
    payloads. The high-coverage known-output records are now a cleaner static
    route than blind whole-stream CDD decoding.
91. `scripts/analyze_liteon_cdd_hard_record_hypotheses.py` and
    `analysis/8051/cdd-hard-record-hypothesis-probes-20260501.md/json` test
    hard-record transform ideas against the known-output exports. Results:
    sparse byte projections are random-like, and the source bitstreams do not
    satisfy RLL/EFMPlus post-modulation constraints.
92. The same hard-record probe found a useful size clue. Many CDD hard-record
    source lengths cluster near DVD-format sizes, especially the 2366-byte
    recording-frame size (`13 * 182`) from ECMA-267. `key5` correlates strongly
    with source-length class, which makes it look like part of a code-rate or
    block-layout selector.
93. The DVD-like clue lines up with the existing 12-record affine schedule:
    LD5M positions 0, 1, and 2 modulo 12 have the strongest near-2366 source
    clustering, while position 3 is much shorter/control-heavy. This is not a
    vanilla DVD ECC block mapping, but it makes a reused optical ECC/frame
    datapath plausible. Record 87 is the cleanest no-variant hard-record
    transform target; records 51, 55, 60, 66, and 68 are better cross-checks
    for the 2366-byte DVD-size clue.
94. `scripts/analyze_liteon_cdd_dvd_reuse_hypotheses.py` and
    `analysis/8051/cdd-dvd-reuse-hypothesis-probes-20260501.md/json` test the
    literal DVD-frame interpretation. Results are negative: DVD LFSR
    descrambling plus simple 2366-byte frame/row extraction does not reveal
    known decoded 8051 chunks, and no tested 2366-byte source window satisfies
    even one DVD PI RS(182,172) row check.
95. Refined CDD hard-record model: keep the DVD insight as a reused-dimension
    or reused-controller-ECC clue, not a direct ECMA-267 pipeline. The hard
    records are likely custom shortened/punctured/interleaved controller
    codewords with DVD-ish sizes/cadence.
96. `scripts/audit_liteon_cdd_known_output_exports.py` and
    `analysis/8051/cdd-known-output-export-audit-20260501.md/json` audit the
    per-record known-output exports. Important correction: those exports are
    public-slot consensus artifacts, not flat decoded CDD records. Example:
    record 87 has 896 covered slot bytes, but only five unique top chunks and
    zero record-exclusive singleton chunks.
97. `scripts/build_liteon_cdd_chunk_contigs.py` and
    `analysis/8051/cdd-runtime-chunk-contigs-20260501.md/json` build contigs
    from 0x40-byte normal work-window chunk adjacency. Current corpus: 96 known
    nodes, 114 directed edges, 43 dominant edges, 25 contigs. The best contig
    is 5 chunks / 320 bytes around candidate records 68/69.
98. Treat chunk contigs as the current best decoded-runtime artifacts. They are
    real adjacent tile runs, but their record labels are still candidate
    provenance. Validate a contig's CDD ownership with a live perturbation
    oracle before treating it as a decoded record span.
99. Top contig disassemblies under
    `analysis/8051/cdd-runtime-chunk-contigs-20260501/*-r2-8051.asm` look like
    plausible 8051 overlays and touch `0x47b1`, `0x4000`, `0x4091`, `0x4095`,
    `0x4097`, `0x4011`, `0x8a4d`, `0x8a52`, and related controller/packet
    state. Use these contigs for static code reading before doing more CDD
    decode brute force.
100. `scripts/analyze_liteon_cdd_contig_ownership_experiment.py` and
    `analysis/8051/cdd-contig4-rec59-ownership-20260501.md/json` summarize the
    first reversible contig ownership oracle. The target was
    `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin`,
    a 192-byte / 3-tile decoded-runtime contig with candidate common CDD record
    `59`.
101. Live patch: F0 offset `0x28519` inside CDD stream 1 record 59 changed
    `0x68 -> 0x60`. The mutation persisted through the helper bypass and the
    drive stayed/cold-booted as normal `LD5M`.
102. Ownership result: stock captures had the full 3-tile contig sequence in
    `7/16` windows at public offset `+0x7180`; mutated captures had `0/24`
    full-sequence hits, while all three component tiles remained visible at
    rearranged offsets; later captures labelled restored had `16/24`
    full-sequence hits. Treat this as strong evidence that record 59 owns or
    controls this runtime contig/neighborhood, but do not treat the restored
    label as flash proof unless a sequential F0 read verifies `0x28519 = 0x68`.
103. `analysis/8051/cdd-contig15-rec70-ownership-negative-20260501.md/json`
    records a useful negative. Contig 15 is a stable 2-tile sequence with
    common record label `70`; patching CDD1 record 70 at `0x2e59c`
    (`0xce -> 0xc6`) left the full sequence unchanged in `24/24` mutated
    captures. Do not assume a candidate record label means every source byte in
    that record controls the chosen contig.
104. `analysis/8051/cdd-contig8-rec57-ownership-unrestored-20260501.md/json`
    recorded a sharper but initially confusing perturbation. Contig 8 is a
    3-tile sequence with common record label `57`; patching `0x27410`
    (`0x3a -> 0x32`) removed only the middle tile in `24/24` mutated captures,
    while tile 0 and tile 2 remained visible.
105. `analysis/8051/cdd-contig8-rec57-readback-resolution-20260501.md/json`
    resolves the flash side of that result. CDD1 spot reads at `0x27400` are
    not reliable restore oracles, even with `sg_raw --cmdset=1`; sequential F0
    reads from offset `0` are. After restoring the lingering `0x4fc9 -> 0x6ee3`
    response hook with `restore-4fc9-cave`, a full 1 MiB sequential F0 read
    matched stock LD5M byte-for-byte (`sha256
    488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39`), and
    `F0[0x27410]` was back to `0x3a`.
106. The record-57 public tile still did not return after cold boot despite a
    byte-stock F0 image. Treat record 57 as a warning about public work-window
    instability or hidden controller/runtime state, not as a clean reversible
    ownership proof. Record 59 / contig 4 remains the stronger reversible live
    CDD ownership oracle.
107. `scripts/analyze_liteon_normal_response_diffs.py` checks whether CDD
    perturbations changed saved host-visible response payloads. Current result:
    no. Existing ownership captures only saved empty `GET PERFORMANCE type 00`
    responses, so the useful oracle is still the public normal work-window.
108. `scripts/rank_liteon_normal_io_cdd_targets.py` ranks decoded-runtime
    chunks and candidate CDD records for normal-mode IO work. Records 58/59
    are the response/bridge neighborhood (`0x8a4c..0x8a4e -> 0x4011..0x4013`,
    plus `0x4099 -> 0x8a4e/0x8a53/0x8a54`). Record 59 remains the preferred
    live target because contig 4 already has reversible ownership.
109. Records 84/85 are the packet-intake neighborhood (`0x47b1 ->
    0x8a4c..0x8a53`). They are high value but higher risk, because breaking
    normal packet intake may break SCSI access rather than merely changing a
    response bridge.
110. `references/evidence/live/normal-getcfg-r5-focused-20260501/` is the
    latest focused read-only GET CONFIG run. `reserved byte 5 = 0xf0` is the
    best current trigger for making the GET CONFIG bridge tiles visible, but
    the effect is still dominated by public-window rotation rather than direct
    field control.
111. Currentboot-to-normal carryover is still a weak shortcut. Gateway writes
    work inside currentboot when the gateway-RW hook is installed, but the full
    known recovery path reloads/canonicalizes normal pages. The currently
    installed service hook was the safer XDATA-write variant and the drive was
    recovered to normal `LD5M` after checking it.
112. `scripts/analyze_liteon_contig_hits_by_stimulus.py` and
    `analysis/8051/rec59-getcfg-contig4-hits-by-stimulus-20260501.md/json`
    summarize the focused record-59 GET CONFIG follow-up. Host-visible GET
    CONFIG response payloads stayed byte-identical stock vs mutated; the
    ordinary response is not a shortcut channel here. The concise narrative is
    `analysis/8051/rec59-getcfg-update-entry-block-20260501.md`.
113. The same follow-up changed the hidden work-window phase: stock GET CONFIG
    captures had `0/32` full contig-4 sequence hits, while the record-59 mutated
    state had `15/32` hits at `+0x7180`. All three component chunks were still
    visible. This reinforces that record 59 affects tile ordering/placement in
    the normal decoded-runtime surface. Static alignment is clean: record 59's
    encoded source starts at `0x28119`, so the patched byte `0x28519` is
    record-relative `+0x400`; its candidate decoded span starts at public
    `+0x7170`, and the contig hits at `+0x7180`. The record-059 known-output
    mask covers `+0x10..+0xcf`, exactly the 192-byte contig 4 bytes. Because
    component chunks stayed byte-identical and only placement/adjacency changed,
    `0x28519` is likely schedule/interleaver/control material rather than a
    direct encoded instruction byte.
114. Important live-drive state caveat: after reinstalling `0x28519: 0x68 ->
    0x60`, the Linux drive still cold-boots as `LD5M`, but the normal update
    entry/data path is currently blocked. The LD5M pre-tail, currentboot-key
    tail, direct `arg=00` chunk, and "failed tail then chunk" probes all timed
    out with host transport errors. A live-key sequential F0 read confirms
    `F0[0x28519] = 0x60`. Avoid more record-59 live mutation work on this drive
    unless the plan includes a fresh/sacrificial drive or an out-of-band restore
    path.
115. Currentboot D7 correction: `0x184000`, `0x18b170`, and `0x191010` through
    the current D7 byte oracle are stock-F0 modulo aliases, not decoded CDD
    runtime bytes. The interesting currentboot alias is the erased F0 tail:
    `0xe8000..0xe9fff` exposes currentboot work/gateway-like data,
    `0xf0000..0xfdfff` exposes repeated live profile/key pages, and
    `0xfe000..0xfffff` is back to `ff`. Evidence:
    `references/evidence/live/currentboot-byte-oracle-targeted-20260502T0150Z/`.
    Analysis: `analysis/8051/currentboot-d7-tail-alias-20260502.md`.
116. `analysis/8051/normal-mode-oracle-next-targets-20260502.md` promotes the
    next normal-mode live target away from record 59. Record 55/56 is now the
    preferred fresh ownership test because it is a high-ranked packet/response
    output corridor with `0x8a4c..0x8a4e`, `0x4098`, `0x47b1`, and
    `0x48f4..0x48f6` behavior, without reusing the risky record-59 bridge.
    The proposed first probe is `F0[0x2627a] 0x5d -> 0x5c` (record 55
    `+0x400`, bit-clear), watching contigs 16/21. Record 58 remains the best
    GET CONFIG read/bridge target (`0x27c25: 0xd3 -> 0xd2`), and record 60 is
    the write-side partner (`0x28eb7: 0xf2 -> 0xf0`). Defer records 84/85
    until packet-intake risk is acceptable.
117. `references/evidence/live/normal-oracle-record55-stock-20260502T022556Z/`
    is the stock baseline for that record-55 plan. It confirmed the target was
    not a rare tile: `8853b78ca23e`, `95caa55b881e`, `a87d03db223d`,
    `25956f88a30e`, and the contig-16/21 sequences appeared across ordinary
    baseline, GET CONFIG, GET PERFORMANCE, and READ TOC/sense captures.
118. The first record-55 hard-lane mutation was hazardous. Candidate
    `normal-oracle-rec55-plus400-5d-to-5c` changed `F0[0x2627a] 0x5d -> 0x5c`.
    Like the older record-59 mutation, the replay staged/readback-verified all
    chunks and hit `DID_ERROR` at final event 544 while immediate identity still
    reported `LD5M`. Unlike record 59, subsequent servo power cycles returned
    only the bridge's Generic SD/MMC LUN, with no PLDS optical LUN. Treat this
    exact byte as boot-critical or at least unsafe until a physical replug
    proves otherwise. Evidence:
    `references/evidence/live/normal-oracle-record55-5d-to-5c-20260502T022801Z/`.
    A stock restore candidate is prepared under
    `runs/helper-bypass-candidates/record55-restore-20260502/`, but it requires
    the optical LUN to reappear before it can be used.
119. `analysis/8051/normal-io-affine-safer-targets-20260502.md` re-ranks the
    normal IO targets after the record-55 hazard. The better next live strategy
    is not another arbitrary hard-lane `+0x400` byte. Record 60's group
    (`60..63`) has LD5M affine evidence, so the prepared safer probe is
    `F0[0x2ae8f] 0x4e -> 0x4c`, changing affine plain `0xc9 -> 0xcb` with a
    raw bit-clear. Generated plans:
    `analysis/8051/record60-affine-group15-c9-to-cb-bitclear-plan-20260502.*`.
    Do not run it until the record-55 drive state is resolved/restored.
120. The Pico has been moved to the Linux laptop and is usable as
    `/dev/ttyACM0`. `pyserial` is installed there, so normal commands work with
    `python3 pico/client.py --port /dev/ttyACM0 ...`. A 3-second servo power
    cut from Linux did remove and re-enumerate the Initio bridge, and the servo
    returned to `LEFT`, but the record-55-mutated spare still came back only as
    `Generic- SD/MMC`; there is no `/dev/sr*` and no PLDS optical `/dev/sg0`.
    Kernel logs show earlier good LD5M optical enumeration at 18:49, then later
    bridge-only re-enumerations after the record-55 event. No SCSI recovery or
    stock restore can run while the optical LUN is absent.
121. After swapping back to the original drive, Linux sees the optical target
    again as `/dev/sg0` / `/dev/sr0`, normal `PLDS DVD+-RW DS-8ABSH LD5M`.
    A reliable sequential 1 MiB F0 read is not stock. It differs in exactly
    four ranges: the resident response-hook trampoline at `0x04fc9..0x04fcb`
    (`12 62 06` -> `02 6e e3`), hook cave code at `0x06ee3..0x06ef6` and
    `0x06ef8..0x06f78`, and the record-59 CDD byte `0x28519` (`0x68 ->
    0x60`). Known record-55 and record-60 probe bytes are stock
    (`0x2627a = 0x5d`, `0x2ae8f = 0x4e`), and record-57 `0x27410` is stock.
    This drive is usable for normal-mode read-only captures and possibly for
    studying the already-installed hook, but it is not a clean candidate for
    fresh helper-bypass write experiments until we either restore it or
    consciously accept the existing mutations.
122. `analysis/8051/original-drive-retriage-20260502.md` summarizes the
    follow-up read-only work on the original drive. The installed `0x6ee3`
    cave payload matches `currentboot-response-hook-gateway-cdb-bulk`, but
    normal LD5M responses for EXTRAINQ and GET CONFIG remain byte-identical to
    stock; the hook is inert for these normal commands. The original drive's
    record-59 mutation is active: contig 4 appears as a full sequence at
    public offset `+0x7180` in `50/96` focused read-only captures, versus
    `0/32` in the stock reference and `15/32` in the older mutated corpus.
    `GET PERFORMANCE nominal` is unhealthy in this state and wedged the
    transport until a Pico servo power cycle; the focused safe set excluding it
    completed cleanly and left the optical LUN visible.
123. A larger read-only focused-safe run on the same original-drive state
    produced 288 work-window captures and again left the optical LUN visible.
    Evidence:
    `references/evidence/live/original-drive-rec59-focused-safe-20260502T030437Z/`.
    Contig 4 was present as a full sequence at `+0x7180` in `134/288`
    captures. The three component chunks were present in every capture; the
    record-59 mutation mainly moves their adjacency/placement. In the mutated
    state, chunk 1 is fixed at `+0x71c0` and chunk 2 at `+0x7200`; chunk 0
    alternates between `+0x7140` and `+0x7180`, and the full sequence appears
    when chunk 0 is at `+0x7180`. This reinforces that `0x28519:68->60` is
    not a direct decoded instruction-byte edit. It may be a
    schedule/interleaver/tile-placement byte, or more interestingly a
    correctable CDD-codeword error: stock-vs-mutated unique chunks had no near
    one-byte decoded variants (nearest only-mutated chunk was 35/64 bytes
    different from any only-stock chunk), while known decoded tiles stayed
    byte-identical and changed phase. Analysis:
    `analysis/8051/original-drive-rec59-expanded-readonly-20260502.md` and
    `analysis/8051/original-drive-rec59-expanded-contig4-hits-20260502.md`.
    New offline helper:
    `scripts/analyze_liteon_work_window_state_delta.py`.
124. The normal-mode I/O primitive phase plan was partially executed on the
    original drive. Baseline state was confirmed with a live-key F0 read:
    `0x2627a = 0x5d`, `0x28519 = 0x60`, and `0x2ae8f = 0x4e`. A focused-safe
    baseline showed record59 as a phase oracle (`rec59-c0` alternates
    `+0x7140`/`+0x7180`; `rec59-c1 = +0x71c0`; `rec59-c2 = +0x7200`) and
    record60 as stable (`rec60-c0 = +0x7300`, `rec60-c1 = +0x7380`,
    `rec60-c2 = +0x7480`). Evidence:
    `references/evidence/live/original-drive-normal-io-baseline-20260502T032421Z/`.
    Analysis:
    `analysis/8051/original-drive-normal-mode-io-primitive-20260502.md`.
125. Do not attempt ordinary helper-bypass writes on the current original drive
    unless deliberately testing recovery/write-entry behavior. The record60
    affine patch/restore artifacts were built offline, but the live viability
    gate failed at event 1: `profile_tail_arg7f rc=99`, then sg status/recovery
    hung until a Pico servo cycle. The record60 patch itself was never sent.
    A post-cycle live-key F0 read confirmed no change: `0x2ae8f` remained
    `0x4e`; record59 remained `0x60`; record55 remained `0x5d`.
126. Read-only GET CONFIG field variants did not yet yield a normal-mode
    communication primitive. GET CONFIG responses were byte-stable, record60
    tiles stayed fixed in all captures, and record59 phase ratios showed only
    weak/noisy bias rather than a clean host-controlled bit. Evidence:
    `references/evidence/live/original-drive-normal-io-getconfig-variants-20260502T033434Z/`
    and
    `references/evidence/live/original-drive-normal-io-getconfig-phase-bias-20260502T033558Z/`.
    New focused analyzer:
    `scripts/analyze_liteon_work_window_watch_chunks.py`.
127. Drive #3 normal-mode side-channel work used the XD13 plaintext islands as
    an atlas. The read-only part validated XD13-derived record55/58/60
    signatures in the public normal work-window, but GET CONFIG field variants,
    CDB echo scans, and a broader read-only status/error screen did not expose
    a reliable host-controlled response bit. The useful lightweight analyzer is
    `scripts/analyze_liteon_work_window_watch_patterns.py`.
128. The structured record60 affine probe on Drive #3 changed
    `F0[0x2ae8f] 0x4e -> 0x4c` (record60/group15 affine plain
    `0xc9 -> 0xcb`). Drive #3 stayed `LD5M`, and record60 watch signatures
    shifted locally in the normal work-window, for example
    `4cfa6d151318` moved from `+0x7380` to `+0x7300`. The restore candidate
    then returned the full zero-based 1 MiB F0 dump to the stock LD5M SHA-256,
    but the public work-window stayed shifted across further cold boots. Treat
    this as evidence of runtime/tile-surface state, not as a proven
    firmware-byte-to-bit oracle.
129. Current Drive #3 rule: do not run more CDD edits without explicit approval.
    Full sequential F0 readback is the restore truth source; spot CDD reads can
    lie. The next write-path control, if desired, should be a byte-identical
    stock replay control, but it still exercises the update/write machinery and
    should be approved before running. Detailed note:
    `analysis/8051/drive3-normal-mode-sidechannel-20260504.md`.
130. The byte-identical stock replay control has now been run on Drive #3. It
    reused the zero-diff record60 restore candidate, completed with
    `success=1`, and Drive #3 returned as normal `LD5M` after a Pico cold boot.
    The post-control full zero-based F0 dump still matched stock LD5M
    (`488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39`).
    The shifted normal work-window layout was unchanged before/after the stock
    replay. Conclusion: same-image replay is not the simple cause of the
    record60 phase shift and does not reset it. Report:
    `analysis/8051/drive3-stock-replay-control-watch-20260504.md`.
131. A fully read-only normal-response matrix was run on Drive #3. New tools:
    `scripts/capture_liteon_normal_response_matrix.py` and
    `scripts/analyze_liteon_normal_response_matrix_correlations.py`. Evidence:
    `references/evidence/live/drive3-normal-response-matrix-core-20260504/`,
    `drive3-normal-response-matrix-core-repeat-20260504/`,
    `drive3-normal-response-matrix-core-shuffled-20260504/`,
    `drive3-normal-response-matrix-modesense-cddevice-ab-20260504/`, and
    `drive3-normal-response-matrix-disc-status-20260504/`.
132. The normal-response matrix is a useful negative. Standard read-only command
    responses are byte-stable across repeated/shuffled runs, but none exposed a
    usable internal bit. XD13-derived record58/60 work-window snippets still
    appear, but their offsets track public-window phase drift rather than a
    command-controlled state. A weak `MODE SENSE cd-device` lead failed a
    randomized A/B test against TEST UNIT READY and standard INQUIRY controls.
133. A single-byte work-window correlation scan did not find a convincing CDB
    shadow leak. Treat the public normal work-window as an observation surface,
    not a communication primitive. The next high-ROI options are a carefully
    targeted normal-mode response hook, or static ranking of XD13/LD5M response
    construction islands before asking for approval for any further live CDD
    mutation. Detailed note:
    `analysis/8051/drive3-normal-response-matrix-20260504.md`.
134. `scripts/normal_mailbox_probe.py` is now the main harness for low-risk
    normal-mode mailbox tests. It logs exact CDBs, payloads, responses, sense,
    hashes, and optional work-window captures. Subcommands currently cover
    `echo-buffer`, `dvd-auth`, `mode-changeable`, and `mode-mailbox`.
135. Standard SCSI echo buffer is closed on Drive #3. `READ BUFFER mode=0x0b`,
    `WRITE BUFFER mode=0x0a`, and `READ BUFFER mode=0x0a` all returned
    `Illegal Request / Invalid field in CDB`. Evidence:
    `references/evidence/live/normal-mailbox-echo-20260504T201130Z/`.
136. `REPORT KEY` without media gives a normal no-media answer for AGID/ASF,
    while RPC state succeeds with `0006000064fe0100`. No AGID means no host
    challenge was sent. This path is still worth revisiting with known-safe
    pressed media. Evidence:
    `references/evidence/live/normal-mailbox-dvd-auth-20260504T201420Z/`.
137. We now have a clean normal-mode host-writable/readable volatile bit:
    `MODE SELECT(10) PF=1 SP=0` on caching page `0x08`, page byte `0x02`,
    mask `0x04`, followed by `MODE SENSE(10)` readback. Drive #3 accepted
    `0x04 -> 0x00`, then restored `0x00 -> 0x04`; `roundtrip=True` and
    identity remained `LD5M`. This is not a memory exfil channel, but it is a
    reliable host-controlled selector bit for future normal-mode hooks.
    Evidence:
    `references/evidence/live/normal-mailbox-mode-select-20260504T201731Z/`.
138. A repeat of the MODE SELECT round trip with `0x4000`-byte public
    work-window snapshots showed identical mutated/restored hashes
    `363eebc5d945fc7612e0ded8e7c87ad1594b8ac0021cf802d0d38d539544dfcf`.
    So this bit should be treated as a direct MODE SENSE/MODE SELECT mailbox,
    not as a public work-window phase control. Detailed report:
    `analysis/8051/drive3-normal-mailbox-probes-20260504.md`.
139. With a router software CD-ROM inserted, Drive #3 behaves as a normal
    readable CD-ROM target. READ CAPACITY(10) reports last LBA `0x8390` and
    block size `2048`; GET CONFIGURATION current profile is `0x0008`
    CD-ROM; READ(10) of LBA 16 returns an ISO9660 `CD001` primary volume
    descriptor. A 64 KiB public `READ BUFFER id=01 offset=0x070000` snapshot
    after the read had no targeted hits for the sector payload, so the public
    window is not a simple last-sector buffer. Evidence:
    `analysis/8051/drive3-router-cd-readonly-20260504.md`.
140. `REPORT KEY` with the CD inserted gives media-aware incompatibility:
    CSS AGID and ASF return `Illegal Request / Cannot read medium -
    incompatible format`; RPC state still succeeds. This confirms the router
    CD is useful for CD media-present paths but not for DVD CSS nonce work.
    A pressed DVD is still needed for the real `REPORT KEY` / `SEND KEY`
    mailbox test.
141. A pressed movie DVD unlocks the real normal-mode CSS/MMC auth path. Drive
    #3 reports current profile `0x0010` DVD-ROM, READ DVD STRUCTURE format `0`
    succeeds, and `REPORT KEY` grants AGID `3`. The auth sequence is
    order-sensitive: asking for the drive challenge before sending a host
    challenge returns `Command sequence error`.
142. `scripts/normal_mailbox_probe.py dvd-auth --send-challenge` now uses the
    observed host-challenge-first order. On Drive #3 it succeeded end-to-end:
    `SEND KEY` host challenge GOOD, `REPORT KEY` key1 returned
    `000a00007e4bea0202000000`, `REPORT KEY` drive challenge returned
    `000e00007e2f16a7be83358bace60000`, AGID invalidated cleanly, and identity
    stayed `LD5M`. The sampled public window had no nonce hit. Detailed report:
    `analysis/8051/drive3-movie-dvd-auth-20260505.md`.
143. Follow-up DVD auth nonce tests prove the path is host-controlled. Four
    different host challenges produced four different key1 responses; repeating
    nonce `535445503157494e3033` produced the same key1
    `000a00005539c62770000000` three times, while the drive challenge changed
    each session. This is a real normal-mode bidirectional auth transform, not
    arbitrary memory I/O.
144. `dvd-auth --capture-step-windows` can now interleave public work-window
    captures after each auth command. A 16 KiB step run showed identical window
    hashes and no nonce hits. A 64 KiB step run showed phase changes across the
    auth sequence and exposed an A3/A4 selector island at public offset
    `+0x91c2`. Selector analysis:
    `analysis/8051/drive3-dvd-auth-step-selector-20260505.md`.
145. The `+0x91c2` island checks `xdata[0x8a49] == 0xa4` with
    `(xdata[0x8a53] & 0x3f) == 0x08`, then jumps to `0x6f62`; it also checks
    `xdata[0x8a49] == 0xa3` with low format `0x06`, then jumps to `0x6f73`.
    Treat `REPORT KEY` format `8` as the safe read-only branch. Treat
    `SEND KEY` format `6` as hazardous because it is likely the DVD RPC/region
    write/config side. Caveat: `0x6f62`/`0x6f73` are 8051 code targets, not
    public-window offsets. The public work-window is tiled, so do not assume
    `+0x6f62` is the branch body.
146. A read-only `REPORT KEY` format scan with the pressed DVD and AGID `3`
    found successful formats `0x00` AGID, `0x05` ASF, and `0x08` RPC state;
    format `0x3f` invalidated AGID cleanly at the end. Formats `0x01/0x02`
    fail with `Command sequence error` without the required host-challenge
    sequence, format `0x04` reports key exchange not established, and most
    others are invalid field. Evidence:
    `references/evidence/live/drive3-dvd-report-key-scan-20260505T034858209881Z/`.
147. Current safe next target: find the actual body or public-window tile for
    the `REPORT KEY format 8 -> 0x6f62` branch, then map its state effects. Do
    not broad-fuzz CSS, and do not send `SEND KEY format 6` unless deliberately
    choosing to risk DVD region/RPC state. Follow-up note:
    `analysis/8051/drive3-dvd-auth-followup-20260505.md`.
