# Normal Work-Window Run Comparison

Reference: `references/evidence/live/normal-work-window-capture-only-20260501`
Target: `references/evidence/live/normal-work-window-stimuli-focused-20260501`
Chunk size: `0x40`

## Summary

Reference informative chunks: 704
Target informative chunks: 751
Shared informative chunks: 699
Target-only informative chunks: 52
Reference-only informative chunks: 5

## Target-Only Observations

| capture | target-only chunk observations |
|---|---:|
| `00-cycle00-inquiry-extrainq` | 14 |
| `01-cycle00-mode-sense10-all` | 25 |
| `02-cycle00-get-configuration-current` | 24 |
| `03-cycle00-get-configuration-all` | 24 |
| `04-cycle00-get-event-status-media` | 19 |
| `05-cycle01-inquiry-extrainq` | 24 |
| `06-cycle01-mode-sense10-all` | 29 |
| `07-cycle01-get-configuration-current` | 24 |
| `08-cycle01-get-configuration-all` | 24 |
| `09-cycle01-get-event-status-media` | 22 |
| `10-cycle02-inquiry-extrainq` | 26 |
| `11-cycle02-mode-sense10-all` | 29 |
| `12-cycle02-get-configuration-current` | 26 |
| `13-cycle02-get-configuration-all` | 27 |
| `14-cycle02-get-event-status-media` | 23 |
| `15-cycle03-inquiry-extrainq` | 21 |
| `16-cycle03-mode-sense10-all` | 28 |
| `17-cycle03-get-configuration-current` | 25 |
| `18-cycle03-get-configuration-all` | 25 |
| `19-cycle03-get-event-status-media` | 23 |
| `20-cycle04-inquiry-extrainq` | 27 |
| `21-cycle04-mode-sense10-all` | 27 |
| `22-cycle04-get-configuration-current` | 26 |
| `23-cycle04-get-configuration-all` | 26 |
| `24-cycle04-get-event-status-media` | 24 |
| `25-cycle05-inquiry-extrainq` | 28 |
| `26-cycle05-mode-sense10-all` | 30 |
| `27-cycle05-get-configuration-current` | 26 |
| `28-cycle05-get-configuration-all` | 23 |
| `29-cycle05-get-event-status-media` | 20 |
| `30-cycle06-inquiry-extrainq` | 24 |
| `31-cycle06-mode-sense10-all` | 29 |
| `32-cycle06-get-configuration-current` | 24 |
| `33-cycle06-get-configuration-all` | 25 |
| `34-cycle06-get-event-status-media` | 23 |
| `35-cycle07-inquiry-extrainq` | 25 |
| `36-cycle07-mode-sense10-all` | 30 |
| `37-cycle07-get-configuration-current` | 30 |
| `38-cycle07-get-configuration-all` | 27 |
| `39-cycle07-get-event-status-media` | 20 |

Top target-only pages:

- `+0x7f00`: 79 observations
- `+0x7e00`: 78 observations
- `+0x0200`: 73 observations
- `+0x8300`: 66 observations
- `+0x6400`: 53 observations
- `+0x6600`: 47 observations
- `+0x6500`: 46 observations
- `+0x6c00`: 40 observations
- `+0x7500`: 40 observations
- `+0x9100`: 40 observations
- `+0x9b00`: 40 observations
- `+0x6300`: 39 observations
- `+0x8400`: 39 observations
- `+0x8500`: 39 observations
- `+0x8c00`: 39 observations
- `+0x9f00`: 37 observations
- `+0x9d00`: 35 observations
- `+0x8b00`: 29 observations
- `+0x9a00`: 27 observations
- `+0x6f00`: 26 observations
- `+0x9e00`: 23 observations
- `+0x9900`: 11 observations
- `+0x6900`: 8 observations
- `+0x6e00`: 8 observations
- `+0x8000`: 8 observations
- `+0x8200`: 8 observations
- `+0x7000`: 6 observations
- `+0x7100`: 6 observations
- `+0x6b00`: 2 observations
- `+0x7200`: 1 observations
- `+0x7400`: 1 observations
- `+0x8600`: 1 observations

Target-only chunks:

- `00581718383d99af` obs 39 at `+0x8cc0`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `047f621202fd7d8a7e047f631202fd90`
- `06130683184aef55` obs 39 at `+0x6300`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `516000005920001b5580001b5d40001b`
- `0e790c42bd72ca02` obs 1 at `+0x8700`; `27-cycle05-get-configuration-current`; sample `8634f0e0fea3e07806cec313ce13d8f9`
- `1258bf4e28986abb` obs 5 at `+0x02c0`; `26-cycle05-mode-sense10-all`, `27-cycle05-get-configuration-current`, `28-cycle05-get-configuration-all`, `29-cycle05-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `1591d13743eb4b75` obs 32 at `+0x7f40`, `+0x7f80`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `0512133522afa8c2adc2aac2a822afa8`
- `167b6d557116552a` obs 2 at `+0x7000`, `+0x7080`; `00-cycle00-inquiry-extrainq`, `10-cycle02-inquiry-extrainq`; sample `e0f9a3e0faa3e02fffea3efeed39fdec`
- `17da5fed883a4145` obs 8 at `+0x8080`; `00-cycle00-inquiry-extrainq`, `05-cycle01-inquiry-extrainq`, `10-cycle02-inquiry-extrainq`, `15-cycle03-inquiry-extrainq`, ...; sample `e02fffea3efeed39fdec38fc90895e12`
- `18777a598722877a` obs 39 at `+0x6640`, `+0x6680`, `+0x66c0`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `8058301b09bf02067e0c7ffc804c301c`
- `1de3123ce8f82786` obs 15 at `+0x6f00`, `+0x6f40`, `+0x6f80`, `+0x6fc0`; `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `07-cycle01-get-configuration-current`, `08-cycle01-get-configuration-all`, ...; sample `7c76070876208010a87c760708762880`
- `1fc002817f62a80c` obs 1 at `+0x9180`; `39-cycle07-get-event-status-media`; sample `4093f0908661e0f5a8904098e0ff9040`
- `26f4536528b7d525` obs 32 at `+0x6c80`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `080816a87c0808e6ffe57c2403f8e6fe`
- `29e7ab54af346860` obs 27 at `+0x9a00`, `+0x9a40`, `+0x9ac0`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, ...; sample `11f0e57c2404f8e6904012f07b00e57c`
- `36ba8efee79536b9` obs 39 at `+0x8400`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `8a4df0908a4de0ffc3941250157d00ef`
- `39ab42ddd82a825a` obs 8 at `+0x6640`, `+0x6680`, `+0x66c0`; `01-cycle00-mode-sense10-all`, `06-cycle01-mode-sense10-all`, `11-cycle02-mode-sense10-all`, `16-cycle03-mode-sense10-all`, ...; sample `e4f0a37414f08047908a527403f0a374`
- `3d299423d28f65a7` obs 37 at `+0x8300`, `+0x8380`; `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, `05-cycle01-inquiry-extrainq`, ...; sample `51e09408908a50e094005006e4f608f6`
- `4037c8574920413d` obs 4 at `+0x7000`, `+0x7080`, `+0x70c0`; `03-cycle00-get-configuration-all`, `27-cycle05-get-configuration-current`, `28-cycle05-get-configuration-all`, `37-cycle07-get-configuration-current`; sample `08eff6904000e020e7f9908ac6e09040`
- `48f0fc6574113b3f` obs 8 at `+0x6900`, `+0x69c0`; `01-cycle00-mode-sense10-all`, `06-cycle01-mode-sense10-all`, `11-cycle02-mode-sense10-all`, `16-cycle03-mode-sense10-all`, ...; sample `e03018054420f080034410f09081fde0`
- `4d5cb1339d20b6a8` obs 5 at `+0x02c0`; `31-cycle06-mode-sense10-all`, `32-cycle06-get-configuration-current`, `33-cycle06-get-configuration-all`, `34-cycle06-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `569dea1ed606bdd9` obs 11 at `+0x6f00`, `+0x6f40`, `+0x6f80`, `+0x6fc0`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `05-cycle01-inquiry-extrainq`, `06-cycle01-mode-sense10-all`, ...; sample `c9123430d0d092af22d310af01c3c0d0`
- `5a0c5fbcd38cf67c` obs 39 at `+0x85c0`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `e0fea3e02486ffee3403fee43dfde43c`
- `5a65b8a71db90942` obs 39 at `+0x9180`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, ...; sample `90401ee0908784f090401f800b904022`
- `5fd06abdd6c585d1` obs 39 at `+0x6440`, `+0x6480`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `70031205fd908627e0ffa3e0fd1207c5`
- `6329fea4e8a8dc22` obs 8 at `+0x6c80`; `00-cycle00-inquiry-extrainq`, `05-cycle01-inquiry-extrainq`, `10-cycle02-inquiry-extrainq`, `15-cycle03-inquiry-extrainq`, ...; sample `fad3eb9400ea648094804006ed2f29fd`
- `7e0774d2c5591c17` obs 40 at `+0x7e00`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, ...; sample `5d7401f0a37470f07b0c7df37f007e08`
- `82c6f496d7c4a64a` obs 14 at `+0x6440`, `+0x6480`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `06-cycle01-mode-sense10-all`, `11-cycle02-mode-sense10-all`, ...; sample `413d0841480d415d0e41681a41731d41`
- `837e1e3070152a7e` obs 5 at `+0x02c0`; `21-cycle04-mode-sense10-all`, `22-cycle04-get-configuration-current`, `23-cycle04-get-configuration-all`, `24-cycle04-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `8d8c3b0a22a0fe85` obs 4 at `+0x7140`, `+0x7180`; `03-cycle00-get-configuration-all`, `27-cycle05-get-configuration-current`, `28-cycle05-get-configuration-all`, `37-cycle07-get-configuration-current`; sample `8a4df0904099e0908a4ef0904099e090`
- `957d82183ebfa517` obs 2 at `+0x7140`, `+0x7180`; `00-cycle00-inquiry-extrainq`, `10-cycle02-inquiry-extrainq`; sample `12dfc0057c057cd0d092af2290881312`
- `989fc7d7854ab2f7` obs 1 at `+0x72c0`; `39-cycle07-get-event-status-media`; sample `28908627e0f8a3e0f9a3e0faa3e0fb90`
- `a413e6656d612af3` obs 5 at `+0x02c0`; `06-cycle01-mode-sense10-all`, `07-cycle01-get-configuration-current`, `08-cycle01-get-configuration-all`, `09-cycle01-get-event-status-media`, ...; sample `0000aff0490000180000000000000000`
- `ac2d53c50f9e667a` obs 23 at `+0x9e00`, `+0x9e80`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, ...; sample `cf9a7d0b7e077f2e12cf9a7d077e077f`
- `ba3aab1d5fd2e7d2` obs 40 at `+0x9b00`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, ...; sample `a9e6a3f008e6a3f0d251e57c2406f57c`
- `be704fe59363d021` obs 4 at `+0x02c0`; `36-cycle07-mode-sense10-all`, `37-cycle07-get-configuration-current`, `38-cycle07-get-configuration-all`, `39-cycle07-get-event-status-media`; sample `0000aff0490000180000aff049000018`
- `c27a8a262dcd2e4c` obs 16 at `+0x7f40`, `+0x7f80`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `05-cycle01-inquiry-extrainq`, `06-cycle01-mode-sense10-all`, ...; sample `7c157ca87ceef608eff6157c904000e0`
- `c684e99453191d07` obs 40 at `+0x7580`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, ...; sample `503fa87c0808e6fe08e6ffe4fcfd908a`
- `c8f852122b07334b` obs 37 at `+0x9fc0`; `00-cycle00-inquiry-extrainq`, `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, ...; sample `fcfdfb7a80f9f8d31232fb5046a87c08`
- `ce90f56fac302c4f` obs 5 at `+0x02c0`; `16-cycle03-mode-sense10-all`, `17-cycle03-get-configuration-current`, `18-cycle03-get-configuration-all`, `19-cycle03-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `cfdc22531f0891f0` obs 29 at `+0x8300`, `+0x8380`; `01-cycle00-mode-sense10-all`, `06-cycle01-mode-sense10-all`, `07-cycle01-get-configuration-current`, `08-cycle01-get-configuration-all`, ...; sample `908a4ee0fd7e047f551202fd908acfe0`
- `d55474aa452cf3d3` obs 8 at `+0x8240`; `01-cycle00-mode-sense10-all`, `06-cycle01-mode-sense10-all`, `11-cycle02-mode-sense10-all`, `16-cycle03-mode-sense10-all`, ...; sample `908a4de0fd7e047f4e1202fd908a4ee0`
- `d6adfe6a1a503c03` obs 35 at `+0x9d00`, `+0x9dc0`; `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, `05-cycle01-inquiry-extrainq`, ...; sample `fe12d50e22ef2438ffee3407fe02cf9a`
- `d6f9e03fad223672` obs 5 at `+0x02c0`; `11-cycle02-mode-sense10-all`, `12-cycle02-get-configuration-current`, `13-cycle02-get-configuration-all`, `14-cycle02-get-event-status-media`, ...; sample `0000aff0490000180000aff049000018`
- `d788ecf091a6f8b3` obs 39 at `+0x0280`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, ...; sample `006baff1760700d700c8aff115082d05`
- `dbf01786a7ed72d5` obs 2 at `+0x6b40`, `+0x6b80`; `26-cycle05-mode-sense10-all`, `36-cycle07-mode-sense10-all`; sample `0808161616803c908353e020e735802e`
- `dcc9e0458c04dcf5` obs 15 at `+0x6500`, `+0x65c0`; `01-cycle00-mode-sense10-all`, `02-cycle00-get-configuration-current`, `06-cycle01-mode-sense10-all`, `11-cycle02-mode-sense10-all`, ...; sample `a87cf6800aa87c76058004a87c7601a8`
- `e3d27d74290722d0` obs 1 at `+0x8640`; `27-cycle05-get-configuration-current`; sample `55e0740bf0ef7e0030e3047ffa80027f`
- `ee30d1b5dacac4fc` obs 8 at `+0x6ec0`; `00-cycle00-inquiry-extrainq`, `05-cycle01-inquiry-extrainq`, `10-cycle02-inquiry-extrainq`, `15-cycle03-inquiry-extrainq`, ...; sample `a3e0f9a3e0faa3e02fffea3efeed39fd`
- `eef7607e33437128` obs 29 at `+0x8b00`; `01-cycle00-mode-sense10-all`, `06-cycle01-mode-sense10-all`, `07-cycle01-get-configuration-current`, `08-cycle01-get-configuration-all`, ...; sample `e04410f078b5760678ab76288054204d`
- `ef8be9d51017aa18` obs 11 at `+0x9900`, `+0x99c0`; `06-cycle01-mode-sense10-all`, `11-cycle02-mode-sense10-all`, `16-cycle03-mode-sense10-all`, `21-cycle04-mode-sense10-all`, ...; sample `e47003ee64b0a87c7007762108760280`
- `efcb6299a7509316` obs 31 at `+0x7f40`, `+0x7f80`; `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, `05-cycle01-inquiry-extrainq`, ...; sample `097a00900001122fb7904093f090409c`
- `f35484065b55ae1c` obs 1 at `+0x7440`; `39-cycle07-get-event-status-media`; sample `e93dfde83cfc800e9090dce0fca3e0fd`
- `f62174382fadfe1b` obs 31 at `+0x6500`, `+0x65c0`; `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, `05-cycle01-inquiry-extrainq`, ...; sample `02070578b5760578ab7620e478b0f622`
- `fe343ef73975d676` obs 38 at `+0x7e40`; `02-cycle00-get-configuration-current`, `03-cycle00-get-configuration-all`, `04-cycle00-get-event-status-media`, `05-cycle01-inquiry-extrainq`, ...; sample `f618ee36f6908a4ae0640260030273de`
