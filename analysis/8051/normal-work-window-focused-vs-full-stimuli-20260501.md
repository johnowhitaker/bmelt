# Normal Work-Window Run Comparison

Reference: `references/evidence/live/normal-work-window-stimuli-full-20260501`
Target: `references/evidence/live/normal-work-window-stimuli-focused-20260501`
Chunk size: `0x40`

## Summary

Reference informative chunks: 752
Target informative chunks: 751
Shared informative chunks: 736
Target-only informative chunks: 15
Reference-only informative chunks: 16

## Target-Only Observations

| capture | target-only chunk observations |
|---|---:|
| `00-cycle00-inquiry-extrainq` | 2 |
| `01-cycle00-mode-sense10-all` | 1 |
| `02-cycle00-get-configuration-current` | 1 |
| `03-cycle00-get-configuration-all` | 3 |
| `04-cycle00-get-event-status-media` | 1 |
| `05-cycle01-inquiry-extrainq` | 1 |
| `06-cycle01-mode-sense10-all` | 2 |
| `07-cycle01-get-configuration-current` | 2 |
| `08-cycle01-get-configuration-all` | 2 |
| `09-cycle01-get-event-status-media` | 2 |
| `10-cycle02-inquiry-extrainq` | 4 |
| `11-cycle02-mode-sense10-all` | 2 |
| `12-cycle02-get-configuration-current` | 2 |
| `13-cycle02-get-configuration-all` | 2 |
| `14-cycle02-get-event-status-media` | 2 |
| `15-cycle03-inquiry-extrainq` | 2 |
| `16-cycle03-mode-sense10-all` | 2 |
| `17-cycle03-get-configuration-current` | 2 |
| `18-cycle03-get-configuration-all` | 2 |
| `19-cycle03-get-event-status-media` | 2 |
| `20-cycle04-inquiry-extrainq` | 2 |
| `21-cycle04-mode-sense10-all` | 2 |
| `22-cycle04-get-configuration-current` | 2 |
| `23-cycle04-get-configuration-all` | 2 |
| `24-cycle04-get-event-status-media` | 2 |
| `25-cycle05-inquiry-extrainq` | 2 |
| `26-cycle05-mode-sense10-all` | 3 |
| `27-cycle05-get-configuration-current` | 6 |
| `28-cycle05-get-configuration-all` | 4 |
| `29-cycle05-get-event-status-media` | 2 |
| `30-cycle06-inquiry-extrainq` | 2 |
| `31-cycle06-mode-sense10-all` | 2 |
| `32-cycle06-get-configuration-current` | 2 |
| `33-cycle06-get-configuration-all` | 2 |
| `34-cycle06-get-event-status-media` | 2 |
| `35-cycle07-inquiry-extrainq` | 2 |
| `36-cycle07-mode-sense10-all` | 3 |
| `37-cycle07-get-configuration-current` | 4 |
| `38-cycle07-get-configuration-all` | 2 |
| `39-cycle07-get-event-status-media` | 2 |

Top target-only pages:

- `+0x0200`: 73 observations
- `+0x7000`: 6 observations
- `+0x7100`: 6 observations
- `+0x6b00`: 2 observations
- `+0x8600`: 1 observations
- `+0x8700`: 1 observations

Target-only chunks:

- `0e790c42bd72ca02` obs 1 at `+0x8700`; `27-cycle05-get-configuration-current`; sample `8634f0e0fea3e07806cec313ce13d8f9`
- `1258bf4e28986abb` obs 5 at `+0x02c0`; `26-cycle05-mode-sense10-all`, `27-cycle05-get-configuration-current`, `28-cycle05-get-configuration-all`, `29-cycle05-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `167b6d557116552a` obs 2 at `+0x7000`, `+0x7080`; `00-cycle00-inquiry-extrainq`, `10-cycle02-inquiry-extrainq`; sample `e0f9a3e0faa3e02fffea3efeed39fdec`
- `4037c8574920413d` obs 4 at `+0x7000`, `+0x7080`, `+0x70c0`; `03-cycle00-get-configuration-all`, `27-cycle05-get-configuration-current`, `28-cycle05-get-configuration-all`, `37-cycle07-get-configuration-current`; sample `08eff6904000e020e7f9908ac6e09040`
- `4d5cb1339d20b6a8` obs 5 at `+0x02c0`; `31-cycle06-mode-sense10-all`, `32-cycle06-get-configuration-current`, `33-cycle06-get-configuration-all`, `34-cycle06-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `837e1e3070152a7e` obs 5 at `+0x02c0`; `21-cycle04-mode-sense10-all`, `22-cycle04-get-configuration-current`, `23-cycle04-get-configuration-all`, `24-cycle04-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `8d8c3b0a22a0fe85` obs 4 at `+0x7140`, `+0x7180`; `03-cycle00-get-configuration-all`, `27-cycle05-get-configuration-current`, `28-cycle05-get-configuration-all`, `37-cycle07-get-configuration-current`; sample `8a4df0904099e0908a4ef0904099e090`
- `957d82183ebfa517` obs 2 at `+0x7140`, `+0x7180`; `00-cycle00-inquiry-extrainq`, `10-cycle02-inquiry-extrainq`; sample `12dfc0057c057cd0d092af2290881312`
- `a413e6656d612af3` obs 5 at `+0x02c0`; `06-cycle01-mode-sense10-all`, `07-cycle01-get-configuration-current`, `08-cycle01-get-configuration-all`, `09-cycle01-get-event-status-media`, ...; sample `0000aff0490000180000000000000000`
- `be704fe59363d021` obs 4 at `+0x02c0`; `36-cycle07-mode-sense10-all`, `37-cycle07-get-configuration-current`, `38-cycle07-get-configuration-all`, `39-cycle07-get-event-status-media`; sample `0000aff0490000180000aff049000018`
- `ce90f56fac302c4f` obs 5 at `+0x02c0`; `16-cycle03-mode-sense10-all`, `17-cycle03-get-configuration-current`, `18-cycle03-get-configuration-all`, `19-cycle03-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `d6f9e03fad223672` obs 5 at `+0x02c0`; `11-cycle02-mode-sense10-all`, `12-cycle02-get-configuration-current`, `13-cycle02-get-configuration-all`, `14-cycle02-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `d788ecf091a6f8b3` obs 39 at `+0x0280`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `006baff1760700d700c8aff115082d05`
- `dbf01786a7ed72d5` obs 2 at `+0x6b40`, `+0x6b80`; `26-cycle05-mode-sense10-all`, `36-cycle07-mode-sense10-all`; sample `0808161616803c908353e020e735802e`
- `e3d27d74290722d0` obs 1 at `+0x8640`; `27-cycle05-get-configuration-current`; sample `55e0740bf0ef7e0030e3047ffa80027f`
