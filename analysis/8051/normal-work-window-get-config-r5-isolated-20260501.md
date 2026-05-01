# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `normal-work-window-get-config-r5-01-isolated-20260501` | `r5-01-current-sf0000` x16 | 16 | 16 | 752 | 749 | 745 | 4 | 3 | 4 |
| `normal-work-window-get-config-r5-f0-isolated-20260501` | `r5-f0-current-sf0000` x16 | 16 | 16 | 745 | 748 | 745 | 3 | 2 | 2 |

## normal-work-window-get-config-r5-01-isolated-20260501

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 6 | `r5-01-current-sf0000` x6 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` | `0x8a4c` | `7ff9123d89e4fd7f40123d89e4908a33` |
| 3 | `r5-01-current-sf0000` x3 | `+0x7100`, `+0x7140` | `0x4099`, `0x8a4b`, `0x8a4d`, `0x8a4e`, `0x8a53`, `0x8a54` | `8a4df0904099e0908a4ef0904099e090` |
| 3 | `r5-01-current-sf0000` x3 | `+0x7000`, `+0x70c0` | `0x4000`, `0x4091`, `0x4093`, `0x4099` | `08eff6904000e020e7f9908ac6e09040` |
| 1 | `r5-01-current-sf0000` x1 | `+0x6080` | `0x47b1`, `0x8a4d` | `540f9047b1f0d378aae6940418e69400` |

## normal-work-window-get-config-r5-f0-isolated-20260501

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 6 | `r5-f0-current-sf0000` x6 | `+0x7100`, `+0x7140` | `0x4099`, `0x8a4b`, `0x8a4d`, `0x8a4e`, `0x8a53`, `0x8a54` | `8a4df0904099e0908a4ef0904099e090` |
| 6 | `r5-f0-current-sf0000` x6 | `+0x7000`, `+0x70c0` | `0x4000`, `0x4091`, `0x4093`, `0x4099` | `08eff6904000e020e7f9908ac6e09040` |
| 1 | `r5-f0-current-sf0000` x1 | `+0x9ec0` | - | `f09090d6e0fca3e0fdd3ef9dee9c404a` |

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
