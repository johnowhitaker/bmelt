# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `normal-work-window-readstatus-correlation-20260501` | `request-sense` x4, `read-toc-format-0` x4, `read-toc-format-1` x4, `read-toc-format-2` x4, `read-toc-format-4` x4, `get-performance-type00` x4, `get-performance-type03` x4 | 4 | 28 | 726 | 735 | 725 | 10 | 8 | 4 |

## normal-work-window-readstatus-correlation-20260501

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 20 | `read-toc-format-0` x4, `read-toc-format-1` x4, `read-toc-format-2` x4, `read-toc-format-4` x4, `get-performance-type00` x4 | `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0` | `0x8a49`, `0x8a4d` | `8a34e04404f0908a29e020e042105202` |
| 13 | `read-toc-format-0` x2, `read-toc-format-2` x4, `read-toc-format-4` x2, `read-toc-format-1` x3, `get-performance-type00` x2 | `+0x9a00`, `+0x9ac0` | `0x8a23` | `dfe054f0f04404f0908a177401f08012` |
| 9 | `read-toc-format-4` x2, `get-performance-type00` x1, `read-toc-format-0` x2, `read-toc-format-1` x2, `read-toc-format-2` x2 | `+0x6b00`, `+0x6b40`, `+0x6b80` | - | `908988e0ffa3e0fd123d899047d07410` |
| 6 | `get-performance-type00` x1, `read-toc-format-0` x2, `read-toc-format-1` x2, `read-toc-format-2` x1 | `+0x7140`, `+0x7180` | `0x4000`, `0x4091`, `0x4093`, `0x4098` | `36f6904762e030e409e054eff0a87c08` |
| 6 | `get-performance-type03` x2, `request-sense` x1, `read-toc-format-0` x1, `read-toc-format-4` x1, `read-toc-format-2` x1 | `+0x9540`, `+0x9580`, `+0x95c0` | `0x8a4c` | `7ff9123d89e4fd7f40123d89e4908a33` |
| 6 | `get-performance-type00` x1, `read-toc-format-0` x2, `read-toc-format-1` x2, `read-toc-format-2` x1 | `+0x7080`, `+0x70c0` | - | `10af01c3c0d0157c157ca87ceef608ef` |
| 5 | `read-toc-format-1` x2, `read-toc-format-2` x2, `get-performance-type00` x1 | `+0x6000`, `+0x6040`, `+0x60c0` | - | `809840351207235030908124e030e029` |
| 4 | `get-performance-type00` x1, `read-toc-format-1` x1, `read-toc-format-2` x1, `get-performance-type03` x1 | `+0x9ec0` | - | `f09090d6e0fca3e0fdd3ef9dee9c404a` |
| 1 | `get-performance-type03` x1 | `+0x6000` | - | `e0edc0e0eec0e0efc0e09090d2e0fca3` |
| 1 | `get-performance-type03` x1 | `+0x6180` | - | `e0ff9090dce0f8a3e0f9a3e0faa3e0fb` |

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
