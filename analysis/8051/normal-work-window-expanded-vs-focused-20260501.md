# Normal Work-Window Run Comparison

Reference: `references/evidence/live/normal-work-window-stimuli-focused-20260501`
Target: `references/evidence/live/normal-work-window-stimuli-expanded-20260501`
Chunk size: `0x40`

## Summary

Reference informative chunks: 751
Target informative chunks: 746
Shared informative chunks: 717
Target-only informative chunks: 29
Reference-only informative chunks: 34

## Target-Only Observations

| capture | target-only chunk observations |
|---|---:|
| `00-mode-sense10-all` | 2 |
| `01-get-event-status-media` | 2 |
| `02-read-toc-format-0` | 11 |
| `03-read-dvd-structure-format0` | 10 |
| `04-read-capacity10` | 11 |
| `05-read-format-capacities` | 9 |
| `06-mode-sense10-read-error-recovery` | 10 |
| `07-mode-sense10-caching` | 8 |
| `08-mode-sense10-cd-device` | 8 |
| `09-mode-sense10-cd-audio` | 8 |
| `10-mode-sense10-power-condition` | 8 |
| `11-mode-sense10-fault-failure` | 12 |
| `12-mode-sense10-capabilities` | 6 |
| `13-get-event-status-operational` | 5 |
| `14-get-event-status-power` | 6 |
| `15-get-event-status-external` | 6 |
| `16-get-event-status-multihost` | 6 |
| `17-get-event-status-busy` | 8 |
| `18-read-toc-format-1` | 15 |
| `19-read-toc-format-2` | 15 |
| `20-read-toc-format-4` | 15 |
| `21-read-dvd-structure-format1` | 12 |
| `22-read-dvd-structure-format2` | 14 |
| `23-read-dvd-structure-formatff` | 12 |
| `24-get-performance-type00` | 15 |
| `25-get-performance-type03` | 17 |

Top target-only pages:

- `+0x7e00`: 27 observations
- `+0x0200`: 26 observations
- `+0x6200`: 24 observations
- `+0x9100`: 24 observations
- `+0x7f00`: 19 observations
- `+0x6c00`: 18 observations
- `+0x6e00`: 13 observations
- `+0x6f00`: 12 observations
- `+0x9b00`: 12 observations
- `+0x9c00`: 12 observations
- `+0x8b00`: 10 observations
- `+0x6600`: 9 observations
- `+0x6d00`: 9 observations
- `+0x9f00`: 9 observations
- `+0x9a00`: 7 observations
- `+0x6a00`: 6 observations
- `+0x6500`: 5 observations
- `+0x6400`: 2 observations
- `+0x6b00`: 1 observations
- `+0x7d00`: 1 observations
- `+0x8000`: 1 observations
- `+0x8200`: 1 observations
- `+0x8300`: 1 observations
- `+0x8400`: 1 observations
- `+0x8500`: 1 observations

Target-only chunks:

- `0a8cd35adb0f75b2` obs 5 at `+0x6500`; `06-mode-sense10-read-error-recovery`, `07-mode-sense10-caching`, `08-mode-sense10-cd-device`, `09-mode-sense10-cd-audio`, ...; sample `7403f0a374108034908a527403f0a374`
- `0b41e4ce22c5621b` obs 17 at `+0x7f40`, `+0x7f80`, `+0x7fc0`; `02-read-toc-format-0`, `03-read-dvd-structure-format0`, `04-read-capacity10`, `05-read-format-capacities`, ...; sample `f078a9e69047b1f008e6f0d25178b5e6`
- `290ecf6a7b7bfaf2` obs 26 at `+0x02c0`; `00-mode-sense10-all`, `01-get-event-status-media`, `02-read-toc-format-0`, `03-read-dvd-structure-format0`, ...; sample `0000aff0490000180000aff049000018`
- `3065e119a794fea3` obs 2 at `+0x6440`, `+0x6480`; `24-get-performance-type00`, `25-get-performance-type03`; sample `78b5760578ab763078b0760202698890`
- `3dcd6687529a6953` obs 13 at `+0x6ec0`; `13-get-event-status-operational`, `14-get-event-status-power`, `15-get-event-status-external`, `16-get-event-status-multihost`, ...; sample `01122fb79047b1f0803e78a976000876`
- `490c2adfea7a5631` obs 1 at `+0x7fc0`; `25-get-performance-type03`; sample `e0c3301e0c9496ffee9400feed940080`
- `4f29221f2e5100fc` obs 17 at `+0x6c40`; `02-read-toc-format-0`, `03-read-dvd-structure-format0`, `04-read-capacity10`, `05-read-format-capacities`, ...; sample `8a38e054eff0908a3ae0547ff0e04440`
- `506ab0f9ed3795e5` obs 24 at `+0x9180`; `02-read-toc-format-0`, `03-read-dvd-structure-format0`, `04-read-capacity10`, `05-read-format-capacities`, ...; sample `0675908a49e0b4a40d908a53e0543fff`
- `58ff801d203925de` obs 1 at `+0x8400`; `25-get-performance-type03`; sample `a9e6fe08e6ffef2404ffe43efee433fd`
- `5b72c3082bd0ebfd` obs 1 at `+0x8080`; `25-get-performance-type03`; sample `e618cee6ce70010614ff908a4de0fd12`
- `607403b72a7e992b` obs 6 at `+0x6ac0`; `06-mode-sense10-read-error-recovery`, `07-mode-sense10-caching`, `08-mode-sense10-cd-device`, `09-mode-sense10-cd-audio`, ...; sample `30e00606e618700106d378aae6940818`
- `63ade08676a04436` obs 12 at `+0x6f00`; `02-read-toc-format-0`, `04-read-capacity10`, `05-read-format-capacities`, `06-mode-sense10-read-error-recovery`, ...; sample `78b0f612b09212f846908a23e0ffc454`
- `66265afa2b5f7487` obs 9 at `+0x6d80`; `17-get-event-status-busy`, `18-read-toc-format-1`, `19-read-toc-format-2`, `20-read-toc-format-4`, ...; sample `08eff6908acfe0ff7e007c017d151230`
- `66bbba48126cd1c7` obs 1 at `+0x8240`; `25-get-performance-type03`; sample `ce70010614ff908a4ee0fd12039f301f`
- `68d23a4efeb7e50e` obs 1 at `+0x6c40`; `25-get-performance-type03`; sample `5102698802697c908a53e0fdb4010930`
- `69db5ec92ba82af9` obs 1 at `+0x7fc0`; `03-read-dvd-structure-format0`; sample `a3e0ff02cdee9048f8e020e10a30aa07`
- `6c198885fad1b4f1` obs 12 at `+0x9c00`, `+0x9cc0`; `02-read-toc-format-0`, `04-read-capacity10`, `05-read-format-capacities`, `06-mode-sense10-read-error-recovery`, ...; sample `78a9cff608eff62290f0b0e493fd7e00`
- `707389d4505f57b2` obs 10 at `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0`; `02-read-toc-format-0`, `03-read-dvd-structure-format0`, `04-read-capacity10`, `11-mode-sense10-fault-failure`, ...; sample `8a34e04404f0908a29e020e042105202`
- `715666d47b610f41` obs 26 at `+0x7e00`; `00-mode-sense10-all`, `01-get-event-status-media`, `02-read-toc-format-0`, `03-read-dvd-structure-format0`, ...; sample `908a53e0fea3e0fbcaeecae4f9f8908a`
- `7453a22727263be9` obs 9 at `+0x6680`; `17-get-event-status-busy`, `18-read-toc-format-1`, `19-read-toc-format-2`, `20-read-toc-format-4`, ...; sample `e0ff54039047b1f0d378aae6940418e6`
- `77f654ba6e65d365` obs 1 at `+0x7dc0`; `25-get-performance-type03`; sample `f478a90806e618cee6ce70010614ff7d`
- `878984a494b8a3a2` obs 1 at `+0x6bc0`; `18-read-toc-format-1`; sample `908988e0ffa3e0fd123d899047d07410`
- `8aa375a0a32ceef3` obs 1 at `+0x7ec0`; `25-get-performance-type03`; sample `cee6ce70010614ffe4fd12039f78a908`
- `8d3ce5504635b161` obs 7 at `+0x9a80`, `+0x9ac0`; `02-read-toc-format-0`, `03-read-dvd-structure-format0`, `04-read-capacity10`, `11-mode-sense10-fault-failure`, ...; sample `dfe054f0f04404f0908a177401f08012`
- `91f9c0d473b71e42` obs 1 at `+0x85c0`; `25-get-performance-type03`; sample `0003122fb79047b1f0e4f0f0f0f079a9`
- `9671ef47fbfece4a` obs 24 at `+0x6240`, `+0x6280`; `02-read-toc-format-0`, `03-read-dvd-structure-format0`, `04-read-capacity10`, `05-read-format-capacities`, ...; sample `65e0ffe48f68f567f566f5657f211203`
- `9ff3d3a8d8e30ef3` obs 1 at `+0x8380`; `25-get-performance-type03`; sample `0614ffe4fd12039f78a90806e618cee6`
- `da8c52872ce4c624` obs 12 at `+0x9b00`; `02-read-toc-format-0`, `03-read-dvd-structure-format0`, `04-read-capacity10`, `05-read-format-capacities`, ...; sample `e008cff608eff690897ce0ffa3e0789d`
- `eda48f3e289c7ffe` obs 9 at `+0x9f80`; `14-get-event-status-power`, `15-get-event-status-external`, `16-get-event-status-multihost`, `17-get-event-status-busy`, ...; sample `90ec908ae4e060030290ecee30e60990`
