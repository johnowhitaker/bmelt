# Materialized Bridge Clamp Slots - 2026-05-06

Offline scan only; no drive commands were sent.

- pattern: `908a4ce0c3940e4008904011740ef0`
- hits: `3934`
- files with hits: `1967`
- public base assumption: `0x070000`

## Candidate Coverage

- builder addresses: `0x077156`, `0x077196`, `0x0770e6`, `0x077026`, `0x0770a6`, `0x077066`
- covered top slots: `6/6`
- missing top slots: -

## Top Clamp Immediate Slots

| rank | public addr | file offset | count | covered | example |
|---:|---:|---:|---:|:---:|---|
| 1 | `0x077156` | `0x7156` | 931 | yes | `references/evidence/live/drive3-router-cd-readonly-corrected-20260504T205514Z/31-id01-window-after-read10-lba16.bin` |
| 2 | `0x077196` | `0x7196` | 814 | yes | `references/evidence/live/normal-work-window-harvest-baseline-20260501/27-cycle27-baseline-no-stimulus.window.bin` |
| 3 | `0x0770e6` | `0x70e6` | 716 | yes | `references/evidence/live/normal-work-window-harvest-baseline-20260501/27-cycle27-baseline-no-stimulus.window.bin` |
| 4 | `0x077026` | `0x7026` | 604 | yes | `references/evidence/live/drive3-normal-response-matrix-core-repeat-20260504/051-cycle01-modesense-capabilities.window.bin` |
| 5 | `0x0770a6` | `0x70a6` | 404 | yes | `references/evidence/live/drive3-router-cd-readonly-corrected-20260504T205514Z/31-id01-window-after-read10-lba16.bin` |
| 6 | `0x077066` | `0x7066` | 243 | yes | `references/evidence/live/normal-start-stop-start-20260501/03-after-start-stop-start-02.window.bin` |

Interpretation: these are the observed rotating copies of the same
normal READ BUFFER response bridge clamp immediate. The current
`post-materializer-runtime-bridge-clamp07` candidate intentionally
patches the top slots so a high-offset READ BUFFER request has a
direct-response proof signal if the resident hook can patch materialized
runtime RAM after CDD setup.

## All Observed Slots

| rank | public addr | file offset | count | phase bucket | covered |
|---:|---:|---:|---:|---:|:---:|
| 1 | `0x077156` | `0x7156` | 931 | `0x16` | yes |
| 2 | `0x077196` | `0x7196` | 814 | `0x16` | yes |
| 3 | `0x0770e6` | `0x70e6` | 716 | `0x26` | yes |
| 4 | `0x077026` | `0x7026` | 604 | `0x26` | yes |
| 5 | `0x0770a6` | `0x70a6` | 404 | `0x26` | yes |
| 6 | `0x077066` | `0x7066` | 243 | `0x26` | yes |
| 7 | `0x077116` | `0x7116` | 199 | `0x16` | no |
| 8 | `0x0771d6` | `0x71d6` | 23 | `0x16` | no |

Phase buckets are file offsets modulo `0x40`. Slots outside the
builder-covered set are useful diagnostics: if a future baseline exposes
only those rare slots, the dynamic builder can still target them from the
run-local baseline rather than relying on historical fixed addresses.
