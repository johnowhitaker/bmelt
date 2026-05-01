# CDD Contig Ownership Perturbation

This report distills a reversible live test that links one encoded CDD
source byte to one normal-mode decoded-runtime contig.

## Target

- Contig file: `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-008-03chunks.bin`
- Contig bytes: `192`
- Target record: `57`
- Patched F0 offset: `0x27410`
- Mutation: `3a -> 32`

The test is intentionally about the public tile surface, not a flat
decoded CDD address. A positive result means this source byte affects
the appearance/order of the chosen decoded-runtime contig.

## Results

| State | Captures | Full contig sequence hits | Chunk-count histogram |
|---|---:|---:|---|
| stock | 24 | 24 | `{'3': 24}` |
| mutated | 24 | 0 | `{'2': 24}` |
| restored | 8 | 0 | `{'2': 8}` |

## Verdict

The contig sequence disappears under mutation but did not return in the supplied restored captures. This is strong ownership evidence, but restore/state recovery remains unresolved.

## Tile Offsets

### stock
Full-sequence offsets: `0x6e80` x24
- chunk 0: `0x6e80` x24
- chunk 1: `0x6ec0` x24
- chunk 2: `0x6f00` x24

### mutated
Full-sequence offsets: none
- chunk 0: `0x6e80` x24
- chunk 1: not seen
- chunk 2: `0x6f00` x24

### restored
Full-sequence offsets: none
- chunk 0: `0x6e80` x8
- chunk 1: not seen
- chunk 2: `0x6f80` x8

## Interpretation

Stock sequence hits: `24/24`.
Mutated sequence hits: `0/24`.
Restored sequence hits: `0/8`.

The component chunk offsets matter because the public work-window is
a rotating tile surface, not a flat decoded CDD dump. A mutation may
remove a tile, rearrange tiles, or leave the sequence unchanged.

Use this as a better oracle pattern for future CDD work: choose a
short contig with a plausible record owner, patch one low-risk
source bit through the helper bypass, capture the normal work-window
before/mutated/restored, and ask whether sequence/order changes
reversibly.
