# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `normal-work-window-get-config-variants-20260501` | `get-config-current-sf0000-len0010` x2, `get-config-current-sf0000-len0040` x2, `get-config-current-sf0000-len00fc` x2, `get-config-current-sf0001-len00fc` x2, `get-config-current-sf0010-len00fc` x2, `get-config-current-sf0020-len00fc` x2, `get-config-current-sf0030-len00fc` x2, `get-config-current-sf0040-len00fc` x2, `get-config-current-sf0100-len00fc` x2, `get-config-all-sf0000-len00fc` x2, `get-config-all-sf0010-len00fc` x2, `get-config-all-sf0020-len00fc` x2 | 2 | 24 | 719 | 721 | 714 | 7 | 6 | 3 |

## normal-work-window-get-config-variants-20260501

| obs | offsets | target refs | sample |
|---:|---|---|---|
| 8 | `+0x9e40` | - | `cf9a7d0b7e077f2e12cf9a7d077e077f` |
| 4 | `+0x7140`, `+0x7180` | `0x4099`, `0x8a4b`, `0x8a4d`, `0x8a4e`, `0x8a53`, `0x8a54` | `8a4df0904099e0908a4ef0904099e090` |
| 4 | `+0x7080`, `+0x70c0` | `0x4000`, `0x4091`, `0x4093`, `0x4099` | `08eff6904000e020e7f9908ac6e09040` |
| 4 | `+0x9500`, `+0x9540`, `+0x95c0` | `0x8a4c` | `7ff9123d89e4fd7f40123d89e4908a33` |
| 4 | `+0x6000`, `+0x6040`, `+0x6080` | - | `809840351207235030908124e030e029` |
| 2 | `+0x9a00`, `+0x9a80` | - | `8988e0fca3e0fdc3ef9dffee9cfed3ef` |
| 1 | `+0x9e40` | - | `f09090d6e0fca3e0fdd3ef9dee9c404a` |

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
