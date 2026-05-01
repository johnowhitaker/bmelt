# CDD Contig Ownership Perturbation

This report distills a reversible live test that links one encoded CDD
source byte to one normal-mode decoded-runtime contig.

## Target

- Contig file: `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin`
- Contig bytes: `192`
- Target record: `59`
- Patched F0 offset: `0x28519`
- Mutation: `68 -> 60`

The test is intentionally about the public tile surface, not a flat
decoded CDD address. A positive result means this source byte affects
the appearance/order of the chosen decoded-runtime contig.

## Results

| State | Captures | Full contig sequence hits | Chunk-count histogram |
|---|---:|---:|---|
| stock | 16 | 7 | `{'3': 16}` |
| mutated | 24 | 0 | `{'3': 24}` |
| restored | 24 | 16 | `{'3': 24}` |

## Tile Offsets

### stock
Full-sequence offsets: `0x7180` x7
- chunk 0: `0x7140` x9, `0x7180` x7
- chunk 1: `0x71c0` x16
- chunk 2: `0x7200` x16

### mutated
Full-sequence offsets: none
- chunk 0: `0x7100` x12, `0x71c0` x12
- chunk 1: `0x7140` x24
- chunk 2: `0x7240` x24

### restored
Full-sequence offsets: `0x7180` x16
- chunk 0: `0x7180` x16, `0x7140` x8
- chunk 1: `0x71c0` x24
- chunk 2: `0x7200` x24

## Interpretation

The full three-chunk sequence is present in stock captures, disappears
after the single-bit CDD record-59 mutation, and returns after the
byte is restored. All three component chunks remain visible in the
mutated state, but their public-window offsets are rearranged, so the
effect is not a simple chunk disappearance. This is strong live
ownership evidence for candidate CDD record 59 over this decoded
runtime contig/neighborhood.

Use this as a better oracle pattern for future CDD work: choose a
short contig with a plausible record owner, patch one low-risk
source bit through the helper bypass, capture the normal work-window
before/mutated/restored, and ask whether sequence/order changes
reversibly.
