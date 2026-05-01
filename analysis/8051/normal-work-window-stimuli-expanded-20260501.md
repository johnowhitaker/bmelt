# Normal Work-Window Stimulus Analysis

Capture directory: `references/evidence/live/normal-work-window-stimuli-expanded-20260501`

## Captures

| index | name | sha256 | diff vs baseline | largest diff run |
|---:|---|---|---:|---:|
| 0 | `00-mode-sense10-all` | `601ad0603efc2fa7` | 0 | `0x0` |
| 1 | `01-get-event-status-media` | `6c91e946ac3129a3` | 561 | `0x5b` |
| 2 | `02-read-toc-format-0` | `32576154328563b2` | 2383 | `0x93` |
| 3 | `03-read-dvd-structure-format0` | `bad661719627069d` | 2438 | `0x86` |
| 4 | `04-read-capacity10` | `90ed2628cd0d0afc` | 2809 | `0xab` |
| 5 | `05-read-format-capacities` | `2ebc9bfc4fa88718` | 2681 | `0x84` |
| 6 | `06-mode-sense10-read-error-recovery` | `8673c859d0f7fa04` | 2806 | `0x91` |
| 7 | `07-mode-sense10-caching` | `dc4256421f62912f` | 2628 | `0xab` |
| 8 | `08-mode-sense10-cd-device` | `2b2dbdb5270689a0` | 2869 | `0xbc` |
| 9 | `09-mode-sense10-cd-audio` | `d33a37632b32947b` | 2810 | `0x91` |
| 10 | `10-mode-sense10-power-condition` | `23032cd8e60f6bb8` | 2747 | `0xa5` |
| 11 | `11-mode-sense10-fault-failure` | `18ada9a130cd5d5d` | 3574 | `0xad` |
| 12 | `12-mode-sense10-capabilities` | `c55a264499c62ade` | 3706 | `0x80` |
| 13 | `13-get-event-status-operational` | `8606da08e1f0061a` | 3834 | `0x98` |
| 14 | `14-get-event-status-power` | `828b8a5ab5d8c48f` | 3957 | `0xc0` |
| 15 | `15-get-event-status-external` | `ffde3c54861e8247` | 3577 | `0xc0` |
| 16 | `16-get-event-status-multihost` | `b901bafdfb43505b` | 3891 | `0xc0` |
| 17 | `17-get-event-status-busy` | `a5edbfb851089f83` | 3834 | `0xc0` |
| 18 | `18-read-toc-format-1` | `55ecbec51e372c34` | 4269 | `0xc0` |
| 19 | `19-read-toc-format-2` | `6ccc6467e0334ef4` | 3954 | `0xc0` |
| 20 | `20-read-toc-format-4` | `91eec72ac4d2a3c0` | 4259 | `0xc0` |
| 21 | `21-read-dvd-structure-format1` | `d4135c55e5893d7d` | 4263 | `0xc0` |
| 22 | `22-read-dvd-structure-format2` | `8887674760e695a3` | 3884 | `0xc0` |
| 23 | `23-read-dvd-structure-formatff` | `d9aeb8fa702eb4df` | 4461 | `0xe9` |
| 24 | `24-get-performance-type00` | `9be61f41f920963b` | 4337 | `0xab` |
| 25 | `25-get-performance-type03` | `ac2746ffe02f6350` | 4330 | `0x84` |

## Variable Pages

| page | variable bytes |
|---:|---:|
| `+0x6000` | 256 |
| `+0x8600` | 256 |
| `+0x8700` | 256 |
| `+0x8b00` | 256 |
| `+0x9500` | 256 |
| `+0x9800` | 253 |
| `+0x6a00` | 252 |
| `+0x6b00` | 251 |
| `+0x6100` | 192 |
| `+0x6600` | 192 |
| `+0x7f00` | 192 |
| `+0x9300` | 192 |
| `+0x9c00` | 192 |
| `+0x9e00` | 192 |
| `+0x9a00` | 190 |
| `+0x8100` | 188 |
| `+0x6200` | 128 |
| `+0x6300` | 128 |
| `+0x6400` | 128 |
| `+0x6500` | 128 |
| `+0x9900` | 127 |
| `+0x7100` | 126 |
| `+0x8500` | 125 |
| `+0x9200` | 124 |
| `+0x7000` | 122 |
| `+0x6c00` | 64 |
| `+0x7d00` | 64 |
| `+0x9f00` | 64 |
| `+0x6f00` | 63 |
| `+0x7e00` | 63 |
| `+0x8000` | 63 |
| `+0x8200` | 63 |

## Variable Runs

- `+0x0302..+0x0305` len `0x3`
- `+0x0307..+0x0308` len `0x1`
- `+0x6000..+0x6140` len `0x140`
- `+0x6180..+0x6200` len `0x80`
- `+0x6240..+0x62c0` len `0x80`
- `+0x6300..+0x6340` len `0x40`
- `+0x6380..+0x63c0` len `0x40`
- `+0x6440..+0x64c0` len `0x80`
- `+0x6500..+0x6540` len `0x40`
- `+0x65c0..+0x6600` len `0x40`
- `+0x6640..+0x6700` len `0xc0`
- `+0x6a00..+0x6a3e` len `0x3e`
- `+0x6a3f..+0x6a77` len `0x38`
- `+0x6a78..+0x6a7a` len `0x2`
- `+0x6a7b..+0x6ab6` len `0x3b`
- `+0x6ab7..+0x6b03` len `0x4c`
- `+0x6b04..+0x6b06` len `0x2`
- `+0x6b07..+0x6b10` len `0x9`
- `+0x6b11..+0x6b29` len `0x18`
- `+0x6b2a..+0x6b2e` len `0x4`
- `+0x6b2f..+0x6c00` len `0xd1`
- `+0x6c40..+0x6c80` len `0x40`
- `+0x6d80..+0x6db1` len `0x31`
- `+0x6db4..+0x6dc0` len `0xc`
- `+0x6ec0..+0x6ecd` len `0xd`
- `+0x6ece..+0x6ed2` len `0x4`
- `+0x6ed3..+0x6f12` len `0x3f`
- `+0x6f13..+0x6f40` len `0x2d`
- `+0x7080..+0x708b` len `0xb`
- `+0x708c..+0x70a2` len `0x16`
- `+0x70a3..+0x70ac` len `0x9`
- `+0x70ad..+0x70cb` len `0x1e`
- `+0x70cc..+0x70e2` len `0x16`
- `+0x70e3..+0x70ec` len `0x9`
- `+0x70ed..+0x7100` len `0x13`
- `+0x7140..+0x716e` len `0x2e`
- `+0x716f..+0x71ae` len `0x3f`
- `+0x71af..+0x71c0` len `0x11`
- `+0x7dc0..+0x7e00` len `0x40`
- `+0x7ec0..+0x7ec5` len `0x5`
- `+0x7ec6..+0x7f00` len `0x3a`
- `+0x7f40..+0x8000` len `0xc0`
- `+0x8080..+0x80b2` len `0x32`
- `+0x80b3..+0x80c0` len `0xd`
- `+0x8100..+0x8138` len `0x38`
- `+0x8139..+0x814e` len `0x15`
- `+0x814f..+0x8180` len `0x31`
- `+0x81c0..+0x81e9` len `0x29`
- `+0x81eb..+0x8200` len `0x15`
- `+0x8240..+0x8248` len `0x8`
- `+0x8249..+0x8280` len `0x37`
- `+0x8380..+0x8384` len `0x4`
- `+0x8385..+0x83c0` len `0x3b`
- `+0x8400..+0x8417` len `0x17`
- `+0x8418..+0x8440` len `0x28`
- `+0x8580..+0x859b` len `0x1b`
- `+0x859c..+0x85b4` len `0x18`
- `+0x85b5..+0x85be` len `0x9`
- `+0x85bf..+0x8800` len `0x241`
- `+0x8b00..+0x8c00` len `0x100`
- `+0x8cc0..+0x8ccc` len `0xc`
- `+0x8ccd..+0x8d00` len `0x33`
- `+0x9180..+0x9189` len `0x9`
- `+0x918a..+0x918c` len `0x2`
- `+0x918d..+0x91aa` len `0x1d`
- `+0x91ab..+0x91c0` len `0x15`
- `+0x9240..+0x9247` len `0x7`
- `+0x9248..+0x9262` len `0x1a`
- `+0x9263..+0x9280` len `0x1d`
- `+0x92c0..+0x92c7` len `0x7`
- `+0x92c8..+0x92e2` len `0x1a`
- `+0x92e3..+0x9300` len `0x1d`
- `+0x9340..+0x9400` len `0xc0`
- `+0x9500..+0x9600` len `0x100`
- `+0x9800..+0x9853` len `0x53`
- `+0x9854..+0x9856` len `0x2`
- `+0x9857..+0x98ad` len `0x56`
- `+0x98ae..+0x9909` len `0x5b`
- `+0x990a..+0x9940` len `0x36`
- `+0x99c0..+0x9a00` len `0x40`

## Moving Tile Inventory

Chunk size: `0x40`
Informative unique chunks: 746
Chunks seen more than once: 732
Chunks seen at multiple offsets: 82

| index | name | informative chunks | new vs baseline |
|---:|---|---:|---:|
| 0 | `00-mode-sense10-all` | 700 | 0 |
| 1 | `01-get-event-status-media` | 700 | 3 |
| 2 | `02-read-toc-format-0` | 700 | 18 |
| 3 | `03-read-dvd-structure-format0` | 700 | 16 |
| 4 | `04-read-capacity10` | 700 | 19 |
| 5 | `05-read-format-capacities` | 700 | 17 |
| 6 | `06-mode-sense10-read-error-recovery` | 700 | 15 |
| 7 | `07-mode-sense10-caching` | 700 | 12 |
| 8 | `08-mode-sense10-cd-device` | 700 | 11 |
| 9 | `09-mode-sense10-cd-audio` | 700 | 11 |
| 10 | `10-mode-sense10-power-condition` | 700 | 11 |
| 11 | `11-mode-sense10-fault-failure` | 700 | 20 |
| 12 | `12-mode-sense10-capabilities` | 701 | 10 |
| 13 | `13-get-event-status-operational` | 701 | 9 |
| 14 | `14-get-event-status-power` | 701 | 10 |
| 15 | `15-get-event-status-external` | 701 | 10 |
| 16 | `16-get-event-status-multihost` | 701 | 10 |
| 17 | `17-get-event-status-busy` | 701 | 13 |
| 18 | `18-read-toc-format-1` | 701 | 24 |
| 19 | `19-read-toc-format-2` | 701 | 24 |
| 20 | `20-read-toc-format-4` | 701 | 23 |
| 21 | `21-read-dvd-structure-format1` | 701 | 23 |
| 22 | `22-read-dvd-structure-format2` | 701 | 23 |
| 23 | `23-read-dvd-structure-formatff` | 701 | 25 |
| 24 | `24-get-performance-type00` | 701 | 24 |
| 25 | `25-get-performance-type03` | 701 | 23 |

Top moving chunks:

- `1886905164886340` observed 52 times in 26 captures at `+0xff00`, `+0xff80`; sample `434444091016530d9000007dec030810`
- `0c705773105c535a` observed 26 times in 26 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `ec38fc908996123430800be490896af0`
- `602f0151f661bc5c` observed 26 times in 26 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `83eef090855ee004f080c5908ca5e0ff`
- `19cf1f0ab9c1fac8` observed 26 times in 26 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `e60997ff18e61997fee57c2405f9c3ef`
- `6c4f90652e56f086` observed 26 times in 26 captures at `+0x6100`, `+0x6180`, `+0x61c0`; sample `47c5e09089c8f09047c4e09089c9f090`
- `01d84480073eed3d` observed 26 times in 26 captures at `+0x6100`, `+0x6180`, `+0x61c0`; sample `922e9082dfe030e00e90841fe06005e0`
- `8bf0e900d2ceae35` observed 26 times in 26 captures at `+0x6100`, `+0x6180`, `+0x61c0`; sample `89fd7408f012f76c2039030260d29089`
- `6037190cb4bc9fd9` observed 26 times in 26 captures at `+0x6a00`, `+0x6a80`; sample `fc08e6f5828c83eff0905503e030e1f9`
- `8853b78ca23e154f` observed 26 times in 26 captures at `+0x6a00`, `+0x6a40`; sample `98e54cf0904000e020e7f9904098e54d`
- `2958d3bbf5db423b` observed 26 times in 26 captures at `+0x6a80`, `+0x6ac0`; sample `943fa87c402cee1313543fffe4f608ef`
- `a87d03db223d165c` observed 26 times in 26 captures at `+0x6b00`, `+0x6b80`; sample `900001122fb7904835f0ef4440904834`
- `d71c07c7fcd6f06d` observed 26 times in 26 captures at `+0x6b40`, `+0x6b80`, `+0x6bc0`; sample `c7e0b4a1069047c07404f010490302c3`
- `4f7ce11fed12844c` observed 26 times in 26 captures at `+0x6b80`, `+0x6bc0`; sample `b1e04402f022908db1e04404f022908d`
- `8f8e0add044ccff6` observed 26 times in 26 captures at `+0x7080`, `+0x70c0`; sample `3407fee43dfde43cfc9085fd12343090`
- `d92154cb54aaf0c6` observed 26 times in 26 captures at `+0x7080`, `+0x70c0`; sample `cbefcbd0e0ffd0e0fed0e0fdd0e0fcc3`
- `20ea2ab16891b5c7` observed 26 times in 26 captures at `+0x7140`, `+0x7180`; sample `8a29e0c4540f30e011908a4ce0c3940e`
- `841742a3e15a2d43` observed 26 times in 26 captures at `+0x7140`, `+0x7180`; sample `3311700302a55c908627e0fca3e0fda3`
- `404045e0e63cf82b` observed 26 times in 26 captures at `+0x7f40`, `+0x7f80`, `+0x7fc0`; sample `b404077d007f041205439048237480f0`
- `22c3f9325ca88af0` observed 26 times in 26 captures at `+0x8100`, `+0x81c0`; sample `78b3e61846601508e6540f700f06e618`
- `305ea7ee70e08354` observed 26 times in 26 captures at `+0x8100`, `+0x8140`; sample `70fa904a1de070fa904a40e0fca3e078`
- `0ee20a0462ac5d2d` observed 26 times in 26 captures at `+0x8140`, `+0x81c0`; sample `0ee0fca3e0fd7f5b1208b5908672e090`
- `06ba20adffeda02c` observed 26 times in 26 captures at `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`; sample `20e00c908a51e07004a3e06002d25122`
- `60a76d91539c247b` observed 26 times in 26 captures at `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`; sample `e04408f09047047408f0e4f090474ce5`
- `f52b132a1a9679b1` observed 26 times in 26 captures at `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`; sample `a2e0b4020e908ebde024fff0908ebce0`
- `e586bd150939defc` observed 26 times in 26 captures at `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`; sample `07908a23e04402f0e57c2409f57c2220`
- `d21d30cf6e6b65b0` observed 26 times in 26 captures at `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`; sample `12f2a022908844eff090825be030e627`
- `ec0b96cc1dec61e0` observed 26 times in 26 captures at `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`; sample `02063302063978a976eb08761402711d`
- `ccd665edc6156d36` observed 26 times in 26 captures at `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`; sample `7be06003025bf3025be5908937e07003`
- `fb00deab088bdb7e` observed 26 times in 26 captures at `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`; sample `e0904091f0a3e55ef0a3e55ff0904000`
- `51346671f8c0bb81` observed 26 times in 26 captures at `+0x8b00`, `+0x8b40`, `+0x8b80`; sample `e4ff120f8dd0d092af22e4908259f030`
- `16c6257d08a32c1f` observed 26 times in 26 captures at `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0`; sample `ff7c007d6e12305d7e007f0acfcdcfce`
- `536f157a8567c76e` observed 26 times in 26 captures at `+0x8b80`, `+0x8bc0`; sample `02f0a87c7601a87ce6ff057c057cd0d0`
