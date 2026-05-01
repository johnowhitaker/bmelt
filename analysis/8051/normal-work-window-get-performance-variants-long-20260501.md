# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `normal-work-window-get-performance-variants-long-20260501` | `gp-type00-max0001` x4, `gp-type00-max0010` x4, `gp-type00-max00ff` x4, `gp-type01-max0010` x4, `gp-type02-max0010` x4, `gp-type03-max0010` x4, `gp-type04-max0010` x4, `gp-type05-max0010` x4, `gp-type10-max0010` x4, `gp-type11-max0010` x4, `gp-type20-max0010` x4, `gp-typeff-max0010` x4, `gp-byte1-01-type00` x4, `gp-byte1-02-type00` x4, `gp-byte1-03-type00` x4, `gp-byte1-01-type03` x4, `gp-startlba1-type00` x4, `gp-startlba1-type03` x4 | 4 | 72 | 755 | 762 | 755 | 7 | 7 | 4 |

## normal-work-window-get-performance-variants-long-20260501

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 58 | `gp-type00-max0001` x4, `gp-type00-max0010` x4, `gp-type00-max00ff` x4, `gp-type02-max0010` x4, `gp-type04-max0010` x4, `gp-type05-max0010` x4, `gp-type10-max0010` x4, `gp-type11-max0010` x3, `gp-type20-max0010` x4, `gp-typeff-max0010` x4, `gp-byte1-01-type00` x4, `gp-byte1-02-type00` x4, `gp-byte1-03-type00` x4, `gp-startlba1-type00` x4, `gp-type01-max0010` x3 | `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0` | `0x8a49`, `0x8a4d` | `8a34e04404f0908a29e020e042105202` |
| 46 | `gp-type00-max0010` x4, `gp-type00-max00ff` x4, `gp-type02-max0010` x3, `gp-type04-max0010` x3, `gp-type05-max0010` x3, `gp-type10-max0010` x3, `gp-type11-max0010` x3, `gp-type20-max0010` x3, `gp-byte1-01-type00` x4, `gp-byte1-02-type00` x2, `gp-byte1-03-type00` x4, `gp-startlba1-type00` x3, `gp-type01-max0010` x2, `gp-typeff-max0010` x3, `gp-type00-max0001` x2 | `+0x9a40`, `+0x9ac0` | `0x8a23` | `dfe054f0f04404f0908a177401f08012` |
| 13 | `gp-type04-max0010` x3, `gp-byte1-01-type00` x2, `gp-startlba1-type00` x2, `gp-type01-max0010` x1, `gp-type05-max0010` x1, `gp-type20-max0010` x1, `gp-byte1-02-type00` x1, `gp-type00-max00ff` x1, `gp-type11-max0010` x1 | `+0x6b00`, `+0x6b80`, `+0x6bc0` | - | `908988e0ffa3e0fd123d899047d07410` |
| 12 | `gp-type04-max0010` x3, `gp-startlba1-type00` x2, `gp-type01-max0010` x1, `gp-type05-max0010` x1, `gp-type20-max0010` x1, `gp-byte1-02-type00` x1, `gp-type00-max00ff` x1, `gp-type11-max0010` x1, `gp-byte1-01-type00` x1 | `+0x7100`, `+0x7140` | `0x4000`, `0x4091`, `0x4093`, `0x4098` | `36f6904762e030e409e054eff0a87c08` |
| 12 | `gp-type04-max0010` x3, `gp-startlba1-type00` x2, `gp-type01-max0010` x1, `gp-type05-max0010` x1, `gp-type20-max0010` x1, `gp-byte1-02-type00` x1, `gp-type00-max00ff` x1, `gp-type11-max0010` x1, `gp-byte1-01-type00` x1 | `+0x7000`, `+0x70c0` | - | `10af01c3c0d0157c157ca87ceef608ef` |
| 10 | `gp-type03-max0010` x3, `gp-byte1-01-type03` x3, `gp-startlba1-type03` x4 | `+0x9a40`, `+0x9ac0` | - | `11f0e57c2404f8e6904012f07b00e57c` |
| 9 | `gp-type00-max0001` x1, `gp-type00-max0010` x1, `gp-type20-max0010` x1, `gp-startlba1-type03` x2, `gp-type02-max0010` x2, `gp-type04-max0010` x1, `gp-byte1-02-type00` x1 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` | `0x8a4c` | `7ff9123d89e4fd7f40123d89e4908a33` |

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
