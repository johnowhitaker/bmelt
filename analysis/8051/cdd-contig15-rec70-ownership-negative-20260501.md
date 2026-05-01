# CDD Contig Ownership Perturbation

This report distills a reversible live test that links one encoded CDD
source byte to one normal-mode decoded-runtime contig.

## Target

- Contig file: `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-015-02chunks.bin`
- Contig bytes: `128`
- Target record: `70`
- Patched F0 offset: `0x2e59c`
- Mutation: `ce -> c6`

The test is intentionally about the public tile surface, not a flat
decoded CDD address. A positive result means this source byte affects
the appearance/order of the chosen decoded-runtime contig.

## Results

| State | Captures | Full contig sequence hits | Chunk-count histogram |
|---|---:|---:|---|
| stock | 24 | 24 | `{'2': 24}` |
| mutated | 24 | 24 | `{'2': 24}` |
| restored | 8 | 3 | `{'1': 5, '2': 3}` |

## Verdict

The contig sequence remains visible under mutation. This is a negative or insensitive-target result for this contig/source byte.

## Tile Offsets

### stock
Full-sequence offsets: `0x8840` x24
- chunk 0: `0x8840` x24
- chunk 1: `0x8880` x24

### mutated
Full-sequence offsets: `0x8840` x24
- chunk 0: `0x8840` x24
- chunk 1: `0x8880` x24

### restored
Full-sequence offsets: `0x8840` x3
- chunk 0: `0x8840` x8
- chunk 1: `0x8880` x3

## Interpretation

Stock sequence hits: `24/24`.
Mutated sequence hits: `24/24`.
Restored sequence hits: `3/8`.

The component chunk offsets matter because the public work-window is
a rotating tile surface, not a flat decoded CDD dump. A mutation may
remove a tile, rearrange tiles, or leave the sequence unchanged.

Use this as a better oracle pattern for future CDD work: choose a
short contig with a plausible record owner, patch one low-risk
source bit through the helper bypass, capture the normal work-window
before/mutated/restored, and ask whether sequence/order changes
reversibly.
