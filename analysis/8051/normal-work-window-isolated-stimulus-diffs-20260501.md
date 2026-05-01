# Isolated Normal Work-Window Stimulus Diffs

Each run alternates local baseline captures with one read-only stimulus.
This report compares stimulus captures only against baselines from the
same run to reduce noise from ordinary window rotation.

## Summary

| run | stimulus | baseline caps | stimulus caps | baseline unique | stimulus unique | shared | stimulus-only | recurring stimulus-only | target refs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `normal-work-window-isolated-extrainq-20260501` | `inquiry-extrainq` x6 | 6 | 6 | 718 | 708 | 705 | 3 | 1 | 1 |
| `normal-work-window-isolated-get-config-current-20260501` | `get-configuration-current` x6 | 6 | 6 | 721 | 706 | 703 | 3 | 2 | 2 |
| `normal-work-window-isolated-mode-sense-all-20260501` | `mode-sense10-all` x6 | 6 | 6 | 734 | 711 | 708 | 3 | 0 | 1 |
| `normal-work-window-isolated-event-media-20260501` | `get-event-status-media` x6 | 6 | 6 | 703 | 703 | 703 | 0 | 0 | 0 |

## normal-work-window-isolated-extrainq-20260501

| obs | offsets | target refs | sample |
|---:|---|---|---|
| 3 | `+0x9500`, `+0x95c0` | `0x8a4c` | `7ff9123d89e4fd7f40123d89e4908a33` |
| 1 | `+0x7000` | - | `e0f9a3e0faa3e02fffea3efeed39fdec` |
| 1 | `+0x7140` | - | `12dfc0057c057cd0d092af2290881312` |

## normal-work-window-isolated-get-config-current-20260501

| obs | offsets | target refs | sample |
|---:|---|---|---|
| 2 | `+0x7140`, `+0x7180` | `0x4099`, `0x8a4b`, `0x8a4d`, `0x8a4e`, `0x8a53`, `0x8a54` | `8a4df0904099e0908a4ef0904099e090` |
| 2 | `+0x7080`, `+0x70c0` | `0x4000`, `0x4091`, `0x4093`, `0x4099` | `08eff6904000e020e7f9908ac6e09040` |
| 1 | `+0x60c0` | - | `809840351207235030908124e030e029` |

## normal-work-window-isolated-mode-sense-all-20260501

| obs | offsets | target refs | sample |
|---:|---|---|---|
| 1 | `+0x9540` | `0x8a4c` | `7ff9123d89e4fd7f40123d89e4908a33` |
| 1 | `+0x0300` | - | `0000aff0490000180000aff049000018` |
| 1 | `+0x6b00` | - | `0808161616803c908353e020e735802e` |

## normal-work-window-isolated-event-media-20260501

| obs | offsets | target refs | sample |
|---:|---|---|---|

## Interpretation

- These small isolated runs are still dominated by the normal rotating
  window, so the most useful rows are recurring stimulus-only chunks and
  stimulus-only chunks with target DPTR references.
- A command that produces many recurring stimulus-only chunks is a better
  candidate for a dedicated longer capture than one that only produces
  one-off sampling differences.
