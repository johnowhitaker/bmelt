# Normal Read-Only Work-Window Harvest

Date: 2026-05-01

This was a deliberate pivot away from firmware writes and timing channels. The
idea was to treat normal `READ BUFFER mode=1 id=01 offset=0x070000` as a
passive sampler for decoded normal-runtime/controller tiles.

No data-out, updater, helper, START STOP, or firmware-write commands were sent.
The drive was checked before and after as normal `PLDS DVD+-RW DS-8ABSH LD5M`
on Linux `/dev/sg0`.

## Live Runs

Two read-only harvests were captured from `jonathan-thinkpad-t480s`:

```text
references/evidence/live/normal-work-window-harvest-baseline-20260501/
references/evidence/live/normal-work-window-harvest-safe-stimuli-20260501/
```

The baseline harvest took 40 capture-only work-window snapshots.

The safe-stimulus harvest took 8 cycles over:

```text
baseline-no-stimulus
inquiry-standard-96
inquiry-extrainq
mode-sense10-all
get-configuration-current
get-configuration-all
get-event-status-media
mechanism-status
mode-sense10-read-error-recovery
mode-sense10-caching
mode-sense10-cd-device
mode-sense10-cd-audio
mode-sense10-power-condition
mode-sense10-fault-failure
mode-sense10-capabilities
```

`mode-sense10-fault-failure` returned the expected illegal-request-style
failure (`rc=5`) but the follow-up work-window reads succeeded and the optical
LUN stayed healthy.

## Corpus Growth

Before these harvests, the saved normal work-window corpus had:

```text
captures:      509
unique chunks: 888
```

After the baseline harvest:

```text
captures:      549
unique chunks: 899
novel chunks:  11
```

After the safe-stimulus harvest:

```text
captures:      669
unique chunks: 902
novel chunks:  3 more
```

The read-only strategy has diminishing returns, but it still found new tiles
without touching flash. More importantly, it raised confidence in the recurring
hidden-runtime islands.

## Updated Artifacts

The expanded hidden-runtime classifier output is:

```text
analysis/8051/normal-hidden-runtime-chunks-with-readonly-harvests-20260501.md
analysis/8051/normal-hidden-runtime-chunks-with-readonly-harvests-20260501.json
```

The expanded known-plaintext CDD pair report is:

```text
analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.md
analysis/8051/cdd-known-plaintext-pairs-with-readonly-harvests-20260501.json
```

The known-plaintext corpus now has:

```text
pairs:              247
records with pairs: 35
```

Simple transform checks are still negative:

```text
max direct LCS:        3 bytes
max bitwise-NOT LCS:   2 bytes
max bit-reversed LCS:  3 bytes
max constant-XOR run:  4 bytes
```

So these chunks do not appear literally in their encoded CDD records, nor under
a trivial bytewise transform. This is more evidence that CDD is a real
record-codeword/packing format.

## Best Known-Plaintext Records

The public-slot mapping is not byte-accurate, but it does bucket chunks into
candidate CDD records. The strongest buckets after the harvest are:

| record | mode | operation key | source | decoded span | slot span | role clue |
|---:|---:|---|---:|---:|---:|---|
| 51 | `0x80` | `a98252b3a002` | 2326 | 816 | 800 | broad packet/front-panel-looking code |
| 55 | `0x40` | `a742d3782e04` | 2313 | 896 | 768 | controller/FIFO and packet-shadow code |
| 58 | `0x80` | `66228ca20005` | 2292 | 544 | 496 | GET CONFIG / public response bridge neighborhood |
| 60 | `0x40` | `950a90757805` | 2344 | 848 | 624 | controller command/FIFO neighborhood |
| 66 | `0x80` | `4e8210adb204` | 2411 | 720 | 704 | controller command/read bridge neighborhood |
| 68 | `0x80` | `0fe212a8d404` | 2421 | 640 | 528 | packet/profile/front-panel-looking code |
| 70 | `0x80` | `098ad4a36805` | 2525 | 560 | 448 | controller gateway read code |
| 87 | `0x40` | `0af2177f2e01` | 1947 | 1008 | 896 | packet-dispatch/selector-looking code |

`slot span` is not true decoded coverage. It is the amount of the candidate
record's public-slot range touched by observed chunks. The same public slot can
host multiple chunks, so this is a bucket/phase hint, not a placement proof.

## Key Interpretation

The normal work window is useful as a decoded-runtime sampler, not as a flat
decoded CDD image.

The repeated public response bridge chunk still appears once per capture, but
bridge-aligned views are less stable than raw public offsets. Current phase
counts:

```text
bridge at +0x7140: 314 captures
bridge at +0x7180: 219 captures
bridge at +0x7100: 136 captures
```

So the bridge is a local island anchor, not a global scroll key.

## Why This Matters

This gives us a third path around the CDD problem:

1. static CDD format reverse engineering from sibling images;
2. slow currentboot/controller oracle reads;
3. passive normal-mode decoded-tile harvesting via public `READ BUFFER id=01`.

Path 3 cannot yet dump arbitrary decoded memory, but it can build a growing
known-output corpus for specific CDD records. That may be enough to infer the
mode `0x40`/`0x80` record grammars, and it points at exactly where the normal
response bridge lives if we later learn to patch valid CDD codewords.

## Next Good Moves

- Build a chunk-adjacency graph per candidate CDD record, especially records
  `51`, `55`, `58`, `60`, `66`, `68`, `70`, and `87`.
- Treat the observed chunks as decoded code tiles and reconstruct local
  function order from repeated adjacencies, not public slot order.
- Compare encoded source spans for those records against the decoded tile sets
  to look for mode-specific grammar: source-to-decoded ratios, repeated
  sub-block lengths, and operation-key correlations.
- Keep the read-only harvester available, but do not expect endless new chunks
  from blind repetition. Future harvests should be driven by a specific command
  family or chunk gap.
