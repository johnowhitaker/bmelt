# Normal Work-Window Run Comparison

Reference: `references/evidence/live/normal-work-window-capture-only-20260501`
Target: `references/evidence/live/normal-work-window-stimuli-full-20260501`
Chunk size: `0x40`

## Summary

Reference informative chunks: 704
Target informative chunks: 752
Shared informative chunks: 704
Target-only informative chunks: 48
Reference-only informative chunks: 0

## Target-Only Observations

| capture | target-only chunk observations |
|---|---:|
| `00-baseline-no-stimulus` | 10 |
| `01-test-unit-ready` | 15 |
| `02-request-sense` | 12 |
| `03-inquiry-standard-96` | 15 |
| `04-inquiry-extrainq` | 23 |
| `05-mode-sense10-all` | 28 |
| `06-get-configuration-current` | 21 |
| `07-get-configuration-all` | 24 |
| `08-get-event-status-media` | 20 |
| `09-read-toc-format-0` | 11 |
| `10-read-disc-information` | 11 |
| `11-read-track-information-lba0` | 10 |
| `12-mechanism-status` | 7 |
| `13-read-dvd-structure-format0` | 9 |

Top target-only pages:

- `+0x8300`: 14 observations
- `+0x7e00`: 13 observations
- `+0x8400`: 12 observations
- `+0x9000`: 12 observations
- `+0x6200`: 10 observations
- `+0x6600`: 10 observations
- `+0x8b00`: 10 observations
- `+0x9f00`: 10 observations
- `+0x7f00`: 9 observations
- `+0x9a00`: 9 observations
- `+0x9d00`: 8 observations
- `+0x6400`: 7 observations
- `+0x6f00`: 7 observations
- `+0x6500`: 6 observations
- `+0x6900`: 6 observations
- `+0x7200`: 6 observations
- `+0x7400`: 6 observations
- `+0x8200`: 6 observations
- `+0x8500`: 6 observations
- `+0x9100`: 6 observations
- `+0x9b00`: 6 observations
- `+0x0200`: 5 observations
- `+0x6c00`: 5 observations
- `+0x7500`: 5 observations
- `+0x6300`: 4 observations
- `+0x8c00`: 4 observations
- `+0x9c00`: 4 observations
- `+0x9e00`: 4 observations
- `+0x6b00`: 1 observations
- `+0x6e00`: 1 observations
- `+0x7000`: 1 observations
- `+0x7100`: 1 observations

Target-only chunks:

- `00581718383d99af` obs 4 at `+0x8cc0`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `047f621202fd7d8a7e047f631202fd90`
- `06130683184aef55` obs 4 at `+0x6300`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `516000005920001b5580001b5d40001b`
- `0745cd5069d58a07` obs 12 at `+0x9040`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `9055c6e04430f0908243e0c4540f30e0`
- `1591d13743eb4b75` obs 4 at `+0x7f80`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `0512133522afa8c2adc2aac2a822afa8`
- `17da5fed883a4145` obs 1 at `+0x8080`; `04-inquiry-extrainq`; sample `e02fffea3efeed39fdec38fc90895e12`
- `18777a598722877a` obs 9 at `+0x6680`, `+0x66c0`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `8058301b09bf02067e0c7ffc804c301c`
- `1de3123ce8f82786` obs 2 at `+0x6f00`; `06-get-configuration-current`, `07-get-configuration-all`; sample `7c76070876208010a87c760708762880`
- `1fc002817f62a80c` obs 1 at `+0x9180`; `00-baseline-no-stimulus`; sample `4093f0908661e0f5a8904098e0ff9040`
- `26f4536528b7d525` obs 4 at `+0x6c40`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `080816a87c0808e6ffe57c2403f8e6fe`
- `29e7ab54af346860` obs 5 at `+0x9a00`, `+0x9a40`, `+0x9ac0`; `03-inquiry-standard-96`, `04-inquiry-extrainq`, `05-mode-sense10-all`, `07-get-configuration-all`, ...; sample `11f0e57c2404f8e6904012f07b00e57c`
- `36ba8efee79536b9` obs 12 at `+0x8400`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `8a4df0908a4de0ffc3941250157d00ef`
- `39ab42ddd82a825a` obs 1 at `+0x6680`; `05-mode-sense10-all`; sample `e4f0a37414f08047908a527403f0a374`
- `3d299423d28f65a7` obs 8 at `+0x8380`; `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`, `09-read-toc-format-0`, ...; sample `51e09408908a50e094005006e4f608f6`
- `48f0fc6574113b3f` obs 6 at `+0x69c0`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `e03018054420f080034410f09081fde0`
- `569dea1ed606bdd9` obs 1 at `+0x6f00`; `04-inquiry-extrainq`; sample `c9123430d0d092af22d310af01c3c0d0`
- `5a0c5fbcd38cf67c` obs 4 at `+0x85c0`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `e0fea3e02486ffee3403fee43dfde43c`
- `5a65b8a71db90942` obs 5 at `+0x9180`; `04-inquiry-extrainq`, `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, ...; sample `90401ee0908784f090401f800b904022`
- `5a92e83e04a8bbd5` obs 2 at `+0x8580`; `12-mechanism-status`, `13-read-dvd-structure-format0`; sample `9047b1e4f080069047b17410f0908a4e`
- `5fd06abdd6c585d1` obs 4 at `+0x6440`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `70031205fd908627e0ffa3e0fd1207c5`
- `6329fea4e8a8dc22` obs 1 at `+0x6c40`; `04-inquiry-extrainq`; sample `fad3eb9400ea648094804006ed2f29fd`
- `63ade08676a04436` obs 4 at `+0x6f00`; `09-read-toc-format-0`, `10-read-disc-information`, `11-read-track-information-lba0`, `13-read-dvd-structure-format0`; sample `78b0f612b09212f846908a23e0ffc454`
- `6a54a908c3ffa4a7` obs 5 at `+0x0280`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `006baff1760700d700c8aff115082d05`
- `6c198885fad1b4f1` obs 4 at `+0x9cc0`; `09-read-toc-format-0`, `10-read-disc-information`, `11-read-track-information-lba0`, `13-read-dvd-structure-format0`; sample `78a9cff608eff62290f0b0e493fd7e00`
- `707389d4505f57b2` obs 8 at `+0x8b00`, `+0x8b40`, `+0x8bc0`; `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, `04-inquiry-extrainq`, ...; sample `8a34e04404f0908a29e020e042105202`
- `7e0774d2c5591c17` obs 5 at `+0x7ec0`; `04-inquiry-extrainq`, `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, ...; sample `5d7401f0a37470f07b0c7df37f007e08`
- `82c6f496d7c4a64a` obs 3 at `+0x6480`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`; sample `413d0841480d415d0e41681a41731d41`
- `878984a494b8a3a2` obs 1 at `+0x6b00`; `01-test-unit-ready`; sample `908988e0ffa3e0fd123d899047d07410`
- `8b2115cd509fb860` obs 1 at `+0x7180`; `01-test-unit-ready`; sample `36f6904762e030e409e054eff0a87c08`
- `8d3ce5504635b161` obs 4 at `+0x9a40`; `01-test-unit-ready`, `02-request-sense`, `09-read-toc-format-0`, `10-read-disc-information`; sample `dfe054f0f04404f0908a177401f08012`
- `9671ef47fbfece4a` obs 10 at `+0x6240`; `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, `04-inquiry-extrainq`, ...; sample `65e0ffe48f68f567f566f5657f211203`
- `989fc7d7854ab2f7` obs 6 at `+0x7280`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `28908627e0f8a3e0f9a3e0faa3e0fb90`
- `ac2d53c50f9e667a` obs 4 at `+0x9e40`, `+0x9e80`; `03-inquiry-standard-96`, `04-inquiry-extrainq`, `05-mode-sense10-all`, `07-get-configuration-all`; sample `cf9a7d0b7e077f2e12cf9a7d077e077f`
- `ba3aab1d5fd2e7d2` obs 6 at `+0x9b40`; `03-inquiry-standard-96`, `04-inquiry-extrainq`, `05-mode-sense10-all`, `06-get-configuration-current`, ...; sample `a9e6a3f008e6a3f0d251e57c2406f57c`
- `c27a8a262dcd2e4c` obs 2 at `+0x7f40`; `04-inquiry-extrainq`, `05-mode-sense10-all`; sample `7c157ca87ceef608eff6157c904000e0`
- `c684e99453191d07` obs 5 at `+0x75c0`; `04-inquiry-extrainq`, `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`, ...; sample `503fa87c0808e6fe08e6ffe4fcfd908a`
- `c8f852122b07334b` obs 10 at `+0x9fc0`; `03-inquiry-standard-96`, `04-inquiry-extrainq`, `05-mode-sense10-all`, `07-get-configuration-all`, ...; sample `fcfdfb7a80f9f8d31232fb5046a87c08`
- `cfdc22531f0891f0` obs 6 at `+0x8300`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `908a4ee0fd7e047f551202fd908acfe0`
- `d55474aa452cf3d3` obs 6 at `+0x8240`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `908a4de0fd7e047f4e1202fd908a4ee0`
- `d6adfe6a1a503c03` obs 8 at `+0x9d00`; `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`, `09-read-toc-format-0`, ...; sample `fe12d50e22ef2438ffee3407fe02cf9a`
- `dcc9e0458c04dcf5` obs 3 at `+0x65c0`; `05-mode-sense10-all`, `06-get-configuration-current`, `07-get-configuration-all`; sample `a87cf6800aa87c76058004a87c7601a8`
- `ee30d1b5dacac4fc` obs 1 at `+0x6ec0`; `04-inquiry-extrainq`; sample `a3e0f9a3e0faa3e02fffea3efeed39fd`
- `eec973076bacae14` obs 1 at `+0x70c0`; `01-test-unit-ready`; sample `10af01c3c0d0157c157ca87ceef608ef`
- `eef7607e33437128` obs 2 at `+0x8b40`; `05-mode-sense10-all`, `12-mechanism-status`; sample `e04410f078b5760678ab76288054204d`
- `ef8be9d51017aa18` obs 1 at `+0x99c0`; `05-mode-sense10-all`; sample `e47003ee64b0a87c7007762108760280`
- `efcb6299a7509316` obs 3 at `+0x7f40`; `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `097a00900001122fb7904093f090409c`
- `f35484065b55ae1c` obs 6 at `+0x74c0`; `00-baseline-no-stimulus`, `01-test-unit-ready`, `02-request-sense`, `03-inquiry-standard-96`, ...; sample `e93dfde83cfc800e9090dce0fca3e0fd`
- `f62174382fadfe1b` obs 3 at `+0x6500`; `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`; sample `02070578b5760578ab7620e478b0f622`
- `fe343ef73975d676` obs 8 at `+0x7e00`; `06-get-configuration-current`, `07-get-configuration-all`, `08-get-event-status-media`, `09-read-toc-format-0`, ...; sample `f618ee36f6908a4ae0640260030273de`
