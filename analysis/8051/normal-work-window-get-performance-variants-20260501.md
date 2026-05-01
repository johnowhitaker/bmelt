# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `normal-work-window-get-performance-variants-20260501` | `gp-type00-max0001` x2, `gp-type00-max0010` x2, `gp-type00-max00ff` x2, `gp-type01-max0010` x2, `gp-type02-max0010` x2, `gp-type03-max0010` x2, `gp-type04-max0010` x2, `gp-type05-max0010` x2, `gp-type10-max0010` x2, `gp-type11-max0010` x2, `gp-type20-max0010` x2, `gp-typeff-max0010` x2, `gp-byte1-01-type00` x2, `gp-byte1-02-type00` x2, `gp-byte1-03-type00` x2, `gp-byte1-01-type03` x2, `gp-startlba1-type00` x2, `gp-startlba1-type03` x2 | 2 | 36 | 765 | 770 | 757 | 13 | 12 | 8 |

## normal-work-window-get-performance-variants-20260501

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 30 | `gp-type00-max0001` x2, `gp-type00-max0010` x2, `gp-type00-max00ff` x2, `gp-type01-max0010` x2, `gp-type02-max0010` x2, `gp-type04-max0010` x2, `gp-type05-max0010` x2, `gp-type10-max0010` x2, `gp-type11-max0010` x2, `gp-type20-max0010` x2, `gp-typeff-max0010` x2, `gp-byte1-01-type00` x2, `gp-byte1-02-type00` x2, `gp-byte1-03-type00` x2, `gp-startlba1-type00` x2 | `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0` | `0x8a49`, `0x8a4d` | `8a34e04404f0908a29e020e042105202` |
| 27 | `gp-type00-max0001` x2, `gp-type00-max0010` x2, `gp-type00-max00ff` x1, `gp-type01-max0010` x2, `gp-type04-max0010` x1, `gp-type05-max0010` x2, `gp-type11-max0010` x2, `gp-type20-max0010` x1, `gp-typeff-max0010` x2, `gp-byte1-01-type00` x2, `gp-byte1-02-type00` x2, `gp-byte1-03-type00` x1, `gp-byte1-01-type03` x1, `gp-startlba1-type00` x2, `gp-type02-max0010` x1, `gp-type03-max0010` x1, `gp-type10-max0010` x1, `gp-startlba1-type03` x1 | `+0x6f00` | `0x8a23` | `78b0f612b09212f846908a23e0ffc454` |
| 25 | `gp-type00-max0010` x2, `gp-type00-max00ff` x1, `gp-type01-max0010` x2, `gp-type04-max0010` x1, `gp-type05-max0010` x2, `gp-type11-max0010` x2, `gp-type20-max0010` x1, `gp-typeff-max0010` x2, `gp-byte1-02-type00` x2, `gp-byte1-03-type00` x1, `gp-byte1-01-type03` x1, `gp-startlba1-type00` x2, `gp-type00-max0001` x1, `gp-type02-max0010` x1, `gp-type03-max0010` x1, `gp-type10-max0010` x1, `gp-byte1-01-type00` x1, `gp-startlba1-type03` x1 | `+0x9c40`, `+0x9cc0` | `0x4000`, `0x4098` | `78a9cff608eff62290f0b0e493fd7e00` |
| 25 | `gp-type00-max0001` x2, `gp-type00-max0010` x2, `gp-type00-max00ff` x2, `gp-type01-max0010` x1, `gp-type02-max0010` x2, `gp-type04-max0010` x2, `gp-type05-max0010` x1, `gp-type10-max0010` x2, `gp-type11-max0010` x2, `gp-type20-max0010` x1, `gp-typeff-max0010` x2, `gp-byte1-01-type00` x2, `gp-byte1-02-type00` x2, `gp-byte1-03-type00` x1, `gp-startlba1-type00` x1 | `+0x9a00` | `0x8a23` | `dfe054f0f04404f0908a177401f08012` |
| 22 | `gp-type00-max0001` x1, `gp-type00-max0010` x1, `gp-type00-max00ff` x2, `gp-type01-max0010` x2, `gp-type02-max0010` x2, `gp-type10-max0010` x2, `gp-type11-max0010` x2, `gp-type20-max0010` x2, `gp-typeff-max0010` x2, `gp-byte1-01-type00` x2, `gp-type04-max0010` x1, `gp-type05-max0010` x1, `gp-byte1-02-type00` x1, `gp-byte1-03-type00` x1 | `+0x9e00` | `0x47b1`, `0x8a4d` | `78aae69047d6f09047afe4f09047b1f0` |
| 9 | `gp-type00-max0001` x2, `gp-type00-max00ff` x1, `gp-type04-max0010` x1, `gp-type05-max0010` x1, `gp-type20-max0010` x2, `gp-typeff-max0010` x1, `gp-byte1-03-type00` x1 | `+0x6040`, `+0x6080`, `+0x60c0` | - | `809840351207235030908124e030e029` |
| 7 | `gp-type00-max0001` x1, `gp-type00-max00ff` x1, `gp-type20-max0010` x2, `gp-byte1-02-type00` x1, `gp-type02-max0010` x1, `gp-type05-max0010` x1 | `+0x6b00`, `+0x6b80`, `+0x6bc0` | - | `908988e0ffa3e0fd123d899047d07410` |
| 6 | `gp-type00-max0001` x1, `gp-type00-max00ff` x1, `gp-type20-max0010` x2, `gp-byte1-02-type00` x1, `gp-type02-max0010` x1 | `+0x7100`, `+0x7140` | `0x4000`, `0x4091`, `0x4093`, `0x4098` | `36f6904762e030e409e054eff0a87c08` |
| 6 | `gp-type00-max0001` x1, `gp-type00-max00ff` x1, `gp-type20-max0010` x2, `gp-byte1-02-type00` x1, `gp-type02-max0010` x1 | `+0x7000`, `+0x70c0` | - | `10af01c3c0d0157c157ca87ceef608ef` |
| 5 | `gp-type00-max0001` x1, `gp-type00-max0010` x1, `gp-type00-max00ff` x1, `gp-type01-max0010` x1, `gp-type02-max0010` x1 | `+0x7e80` | `0x4000`, `0x4091`, `0x8a4a` | `f618ee36f6908a4ae0640260030273de` |
| 5 | `gp-startlba1-type00` x1, `gp-type01-max0010` x1, `gp-type05-max0010` x1, `gp-type20-max0010` x1, `gp-byte1-03-type00` x1 | `+0x9a00` | - | `8988e0fca3e0fdc3ef9dffee9cfed3ef` |
| 2 | `gp-type00-max0001` x1, `gp-type00-max00ff` x1 | `+0x7f80` | - | `a3e0ff02cdee9048f8e020e10a30aa07` |
| 1 | `gp-byte1-03-type00` x1 | `+0x6000` | `0x47b1`, `0x8a4d` | `540f9047b1f0d378aae6940418e69400` |

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
