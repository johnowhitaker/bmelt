# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `normal-work-window-error-path-pairs-20260501` | `read-toc-format-0-after-command` x3, `read-toc-format-0-after-request-sense` x3, `read-toc-format-4-after-command` x3, `read-toc-format-4-after-request-sense` x3, `get-performance-type00-after-command` x3, `get-performance-type00-after-request-sense` x3 | 3 | 18 | 707 | 713 | 704 | 9 | 9 | 6 |

## normal-work-window-error-path-pairs-20260501

| obs | stimuli | offsets | target refs | sample |
|---:|---|---|---|---|
| 12 | `read-toc-format-0-after-command` x3, `read-toc-format-0-after-request-sense` x2, `read-toc-format-4-after-command` x2, `read-toc-format-4-after-request-sense` x2, `get-performance-type00-after-command` x2, `get-performance-type00-after-request-sense` x1 | `+0x9c00`, `+0x9c80` | `0x4000`, `0x4098` | `78a9cff608eff62290f0b0e493fd7e00` |
| 12 | `read-toc-format-0-after-command` x3, `read-toc-format-0-after-request-sense` x2, `read-toc-format-4-after-command` x2, `read-toc-format-4-after-request-sense` x2, `get-performance-type00-after-command` x2, `get-performance-type00-after-request-sense` x1 | `+0x6f80` | `0x8a23` | `78b0f612b09212f846908a23e0ffc454` |
| 12 | `read-toc-format-4-after-command` x3, `read-toc-format-4-after-request-sense` x2, `get-performance-type00-after-command` x2, `read-toc-format-0-after-command` x2, `read-toc-format-0-after-request-sense` x2, `get-performance-type00-after-request-sense` x1 | `+0x9a00`, `+0x9ac0` | `0x8a23` | `dfe054f0f04404f0908a177401f08012` |
| 3 | `get-performance-type00-after-command` x2, `get-performance-type00-after-request-sense` x1 | `+0x6440`, `+0x6480` | `0x8a4a`, `0x8a4f`, `0x8a53` | `78b5760578ab763078b0760202698890` |
| 2 | `read-toc-format-0-after-command` x2 | `+0x7180` | `0x4000`, `0x4091`, `0x4093`, `0x4098` | `36f6904762e030e409e054eff0a87c08` |
| 2 | `read-toc-format-4-after-command` x1, `get-performance-type00-after-command` x1 | `+0x9500`, `+0x9580` | `0x8a4c` | `7ff9123d89e4fd7f40123d89e4908a33` |
| 2 | `read-toc-format-0-after-command` x1, `read-toc-format-4-after-command` x1 | `+0x6000`, `+0x6080` | - | `809840351207235030908124e030e029` |
| 2 | `read-toc-format-0-after-command` x2 | `+0x6b80` | - | `908988e0ffa3e0fd123d899047d07410` |
| 2 | `read-toc-format-0-after-command` x2 | `+0x70c0` | - | `10af01c3c0d0157c157ca87ceef608ef` |

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
