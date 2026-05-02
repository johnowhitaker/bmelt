# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `stock` | `std-current-sf0000-len00fc` x8, `r5-0f-current-sf0000` x8, `r5-f0-current-sf0000` x8 | 8 | 24 | 718 | 714 | 711 | 3 | 0 | 2 |
| `mutated` | `std-current-sf0000-len00fc` x8, `r5-0f-current-sf0000` x8, `r5-f0-current-sf0000` x8 | 8 | 24 | 714 | 708 | 706 | 2 | 2 | 2 |

## stock

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 1 | `r5-f0-current-sf0000` x1 | `+0x7140` | `0x4099`, `0x8a4b`, `0x8a4d`, `0x8a4e`, `0x8a53`, `0x8a54` | `8a4df0904099e0908a4ef0904099e090` |
| 1 | `r5-f0-current-sf0000` x1 | `+0x7040` | `0x4000`, `0x4091`, `0x4093`, `0x4099` | `08eff6904000e020e7f9908ac6e09040` |
| 1 | `std-current-sf0000-len00fc` x1 | `+0x9e40` | - | `f09090d6e0fca3e0fdd3ef9dee9c404a` |

## mutated

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 4 | `r5-f0-current-sf0000` x4 | `+0x7140`, `+0x7180` | `0x4099`, `0x8a4b`, `0x8a4d`, `0x8a4e`, `0x8a53`, `0x8a54` | `8a4df0904099e0908a4ef0904099e090` |
| 4 | `r5-f0-current-sf0000` x4 | `+0x7080`, `+0x70c0` | `0x4000`, `0x4091`, `0x4093`, `0x4099` | `08eff6904000e020e7f9908ac6e09040` |

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
