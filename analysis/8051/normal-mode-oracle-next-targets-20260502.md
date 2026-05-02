# Normal-Mode Oracle Next Targets

Date: 2026-05-02

This note is the practical follow-up to the D7/currentboot work. The D7 hook
is useful for targeted currentboot reads, but it does not expose decoded CDD
normal-runtime code. The next normal-mode I/O breakthrough still has to come
from CDD-owned normal-runtime chunks or from a true normal-mode write/read
primitive.

## Current Constraints

- Visible F0 prefix hooks such as `0x542b`, `0x6206`, and `0x4ec6` are
  currentboot/update-path hooks, not normal LD5M command handlers.
- The helper bypass lets us persist selected CDD source byte edits, but it does
  not let us patch decoded runtime bytes directly.
- The public normal `READ BUFFER id=01/02 offset=0x070000` surface is a
  rotating tile/work window. A patch can reorder or remove tiles without
  changing host-visible SCSI response bytes.
- Currentboot gateway writes do not trivially carry through the known recovery
  path into normal mode.
- The record-59 `0x28519: 68 -> 60` edit is a strong ownership proof, but it
  also blocked update entry on one drive. Treat record 59 as valuable evidence,
  not as the first new spare-drive mutation target.

## Updated Target Ranking

### 1. Record 55/56: Packet/Response Output Corridor

This is the target I would promote for the next non-record-59 live ownership
test.

Evidence:

- `normal-io-cdd-target-ranking` ranks record `55` first overall.
- Contigs `16` and `21` are narrow record-55/56 or record-55 components.
- Known chunks repeatedly touch packet shadow and output-ish registers.
- Record 55 includes code shaped like response/FIFO emission:
  - reads `0x8a4c`, `0x8a4d`, `0x8a4e`;
  - writes through `0x4098`;
  - writes through `0x47b1`;
  - copies state into `0x48f4..0x48f6`.

Why this is attractive:

- It is close to host I/O, but not the already-risky record-59 bridge.
- It may let us perturb response/status plumbing without touching START STOP or
  tray mechanics.
- A positive ownership result here would give a new normal-runtime foothold
  independent of the record-58/59 GET CONFIG bridge.

Candidate first perturbation:

```text
record 55 source: 0x25e7a..0x26783
probe byte:        F0[0x2627a] = 0x5d -> 0x5c  (record +0x400, bit-clear)
watch contigs:     16, 21 and chunks 25956f88a30e / 4f29221f2e51 / 95caa55b881e
```

The exact byte is not special yet; it is a conservative bit-clear schedule/body
probe analogous to the prior `+0x400` record-59 perturbation. It should be
wrapped in full before/mutated/restored captures and sequential F0 readback if
restore behavior looks odd.

Record-55 watch set:

```text
8853b78ca23e  0x4000/0x4098 loop, seen at +0x6a00/+0x6a40/+0x6a80/+0x6ac0
95caa55b881e  0x85ef..0x85f3 -> 0x48f4/0x48f5/0x48f6/0x48c8/0x48ef
a87d03db223d  controller/status setup around 0x4834/0x4835/0x4e02
25956f88a30e  packet-shadow arithmetic around 0x8a4c/0x8a4d/0x8a4e
4f29221f2e51  record55/56 boundary chunk, broad command/status logic
796c2cf9d837  rare but direct 0x8a4e/0x8a54 -> 0x47b1 output path
```

The focused safe-stimuli corpus already sees the record-55 island in every
capture at `+0x6a00..+0x6bc0`, so a dedicated ownership test should not need a
mechanical command. The best capture set is a small repeated mix of:

```text
baseline no-stimulus
INQUIRY EXTRAINQ
MODE SENSE(10) all
GET CONFIGURATION current/all
GET PERFORMANCE type 00 and type 04
READ TOC format 0 failure followed by REQUEST SENSE
```

Those commands exercise the island enough to make the tiles visible while
staying away from START STOP and packet-intake mutation.

### 2. Record 58: GET CONFIG Read/Bridge Setup

Record 58 remains the best target for the GET CONFIG response builder.

Evidence:

- Owns the stable public bridge chunk `20ea2ab16891` in two public slots.
- Owns the `4037c8574920` setup chunk and `8d8c3b0a22a0` GET CONFIG-specific
  `0x4099 -> 0x8a4e/0x8a53/0x8a54` chunk.
- Contig `20` has common owner record `58` and is high-ranked.

Why this is attractive:

- The decoded snippets show a plausible controller-read sequence:
  `0x4091..0x4093`, `0x409c = 0x40/0x24`, poll, then read `0x4099`.
- This is the path most likely to become a normal-mode read oracle if we can
  learn how host CDB fields feed the address/count shadow.

Why it is not first:

- It neighbors record 59, and the previous record-59 test affected update entry.
- We should use record 58 deliberately, ideally after the record-55 ownership
  test proves the fresh spare and capture workflow are behaving.

Candidate first perturbation:

```text
record 58 source: 0x27825..0x28119
probe byte:        F0[0x27c25] = 0xd3 -> 0xd2  (record +0x400, bit-clear)
watch contig:      20
watch chunks:      7e15398acc97, 8f8e0add044c, 20ea2ab16891,
                   4037c8574920, 8d8c3b0a22a0
stimuli:           GET CONFIG current/all variants, especially sf=0x0020 and r5 variants
```

### 3. Record 60: Controller Write-Side Partner

Record 60 looks like the write-side complement to the record-58 read/bridge
area.

Evidence:

- Owns `9b673c066ae4`, which copies `0x8a4e/0x8a53/0x8a54 -> 0x4099`.
- Owns `28583441dfa8`, which writes `0x8ac6 -> 0x4095` and kicks the
  controller command side.
- Contig `18` has common owner record `60`.

Use this after record 58/55:

```text
record 60 source: 0x28ab7..0x293df
probe byte:        F0[0x28eb7] = 0xf2 -> 0xf0  (record +0x400, bit-clear)
watch contig:      18
watch chunks:      4cfa6d151318, 28583441dfa8, 9b673c066ae4
```

## Targets To Defer

- Record `59`: best proof so far, but not the next casual mutation target.
- Records `84/85`: attractive packet-intake chunks (`0x47b1 -> 0x8a4c..`),
  but patching command intake is more likely to break host communication.
- Record `57`: ownership-looking result was not cleanly reversible at the tile
  level, even though F0 was restored.
- Record `70`: the tested source byte was negative/insensitive.
- Record `87`: useful static oracle material, but exported public-window
  chunks are repeated/tiled enough that it is not the cleanest live I/O target.

## Recommended Next Live Experiment

Run one fresh, narrow ownership test on the spare, starting with record 55.

1. Recover/cold-boot the spare from currentboot/D7 back to normal LD5M.
2. Capture a stock baseline of the normal work window under:
   - no stimulus;
   - GET CONFIG current/all;
   - GET PERFORMANCE nominal;
   - REQUEST SENSE after one harmless CHECK-condition command.
3. Build and run the record-55 `0x2627a:5d->5c` helper-bypass candidate.
4. Cold boot, repeat the same captures.
5. Restore with same-image or explicit restore candidate, then take the same
   captures again.
6. Analyze contigs 16/21 and actual host-visible response payloads.

The success condition is not "the SCSI response changes" yet. The first success
condition is a clean reversible tile/contig effect outside record 59. If that
works, the next step is to use the affected record as the place to hunt for a
more direct host-visible response hook.

## Practical Takeaway

The current normal-mode path should be:

```text
record 55 ownership proof
  -> record 58 GET CONFIG bridge proof
  -> record 60 write-side proof
  -> pick the cleanest proven normal-runtime island for an actual I/O hook
```

That keeps us moving toward a real normal-mode communication loop while avoiding
the two biggest time sinks: building a faster currentboot D7 reader, and
blindly mutating record 59 again.
