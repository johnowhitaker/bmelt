# CDD Known-Output Export Audit

Date: 2026-05-01

Offline only. No drive commands were sent.

This audits the `record-XXX-known-output.bin` exports. Those files are
public-slot consensus artifacts, not flat decoded CDD records. The key
question is how many exported slots are repeated copies of the same
0x40-byte public tile.

## Summary

| record | known bytes | slots | unique chunks | duplicate slots | singleton chunks | exclusive singletons | variant slots |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 87 | 896/1008 | 14 | 5 | 9 | 2 | 0 | 0 |
| 51 | 800/816 | 13 | 6 | 7 | 2 | 1 | 7 |
| 55 | 768/896 | 12 | 6 | 6 | 2 | 1 | 7 |
| 66 | 704/720 | 11 | 6 | 5 | 2 | 2 | 5 |
| 60 | 624/848 | 10 | 6 | 4 | 2 | 1 | 2 |
| 68 | 528/640 | 9 | 6 | 3 | 4 | 3 | 2 |
| 88 | 512/688 | 8 | 2 | 6 | 0 | 0 | 1 |
| 58 | 496/544 | 8 | 4 | 4 | 0 | 0 | 5 |
| 70 | 448/560 | 7 | 4 | 3 | 2 | 2 | 5 |
| 50 | 432/496 | 7 | 2 | 5 | 0 | 0 | 0 |
| 64 | 336/688 | 6 | 3 | 3 | 0 | 0 | 1 |
| 65 | 320/544 | 5 | 3 | 2 | 1 | 1 | 0 |
| 67 | 272/656 | 5 | 4 | 1 | 3 | 1 | 0 |
| 49 | 256/448 | 4 | 1 | 3 | 0 | 0 | 3 |
| 85 | 256/768 | 4 | 2 | 2 | 0 | 0 | 0 |
| 62 | 224/464 | 4 | 3 | 1 | 2 | 1 | 1 |
| 86 | 224/224 | 4 | 3 | 1 | 2 | 0 | 2 |
| 57 | 208/304 | 4 | 2 | 2 | 0 | 0 | 1 |
| 52 | 192/224 | 3 | 1 | 2 | 0 | 0 | 3 |
| 73 | 192/400 | 3 | 1 | 2 | 0 | 0 | 0 |
| 53 | 192/304 | 3 | 2 | 1 | 1 | 1 | 0 |
| 74 | 192/800 | 3 | 2 | 1 | 1 | 0 | 0 |
| 59 | 192/304 | 3 | 3 | 0 | 3 | 1 | 1 |
| 63 | 160/256 | 3 | 2 | 1 | 1 | 1 | 1 |
| 80 | 128/432 | 2 | 1 | 1 | 0 | 0 | 2 |
| 84 | 128/160 | 2 | 1 | 1 | 0 | 0 | 0 |
| 54 | 128/272 | 2 | 2 | 0 | 2 | 2 | 0 |
| 56 | 128/352 | 2 | 2 | 0 | 2 | 1 | 1 |
| 83 | 96/128 | 2 | 2 | 0 | 2 | 0 | 2 |
| 69 | 64/368 | 1 | 1 | 0 | 1 | 1 | 1 |
| 78 | 64/128 | 1 | 1 | 0 | 1 | 0 | 0 |
| 81 | 48/320 | 1 | 1 | 0 | 1 | 0 | 1 |

The `known bytes` column is slot coverage. `unique chunks` and
`exclusive singletons` are better proxies for independent evidence. A
record with high slot coverage but few unique chunks should not be used
as a flat source-to-output oracle.

## Highest-Risk Exports

| record | duplicate ratio | repeated chunks | duplicate chunk placements |
| --- | --- | --- | --- |
| 49 | 75% | 1 | `0c705773105c` @ 0xc0,0x100,0x140,0x180 |
| 88 | 75% | 2 | `03044422ea30` @ 0xb0,0xf0,0x130,0x170; `7fabb1c7616c` @ 0x1b0,0x1f0,0x230,0x270 |
| 50 | 71% | 2 | `6c4f90652e56` @ 0x0,0x40,0x80,0xc0; `2598f9591a20` @ 0x140,0x180,0x1c0 |
| 52 | 67% | 1 | `80b60d722518` @ 0x20,0x60,0xa0 |
| 73 | 67% | 1 | `536f157a8567` @ 0xd0,0x110,0x150 |
| 87 | 64% | 3 | `183ec6fd07c7` @ 0xa0,0xe0,0x120,0x160; `ba3aab1d5fd2` @ 0x1a0,0x1e0,0x220,0x260; `c2560553eb14` @ 0x2a0,0x2e0,0x320,0x360 |
| 51 | 54% | 4 | `056348c5dbbf` @ 0x210,0x250,0x290,0x2d0; `70221f447d35` @ 0x150,0x190,0x1d0; `0f031dd8ed37` @ 0x10,0x50; `fe95f1ed098a` @ 0x90,0xd0 |
| 55 | 50% | 4 | `8853b78ca23e` @ 0xc0,0x100,0x140,0x180; `95caa55b881e` @ 0x1c0,0x240; `a87d03db223d` @ 0x200,0x280; `25956f88a30e` @ 0x2c0,0x340 |
| 57 | 50% | 2 | `cfe0a1406283` @ 0x60,0xa0; `5fb5a8bf8f9a` @ 0xe0,0x120 |
| 58 | 50% | 4 | `5fb5a8bf8f9a` @ 0x30,0x70; `7e15398acc97` @ 0xb0,0xf0; `8f8e0add044c` @ 0x130,0x170; `20ea2ab16891` @ 0x1b0,0x1f0 |
| 64 | 50% | 3 | `c24221ec1018` @ 0x20,0x60; `24ebe8bb67f5` @ 0xa0,0xe0; `b69f366c92b6` @ 0x220,0x2a0 |
| 80 | 50% | 1 | `5a65b8a71db9` @ 0x40,0x80 |
| 84 | 50% | 1 | `2111cafaf69c` @ 0x20,0x60 |
| 85 | 50% | 2 | `2111cafaf69c` @ 0x0,0x40; `306eb529b363` @ 0x280,0x2c0 |
| 66 | 45% | 4 | `404045e0e63c` @ 0x150,0x190,0x210; `9aa0a39b4424` @ 0x50,0xd0; `fe343ef73975` @ 0x90,0x110; `bd4b736c6b8d` @ 0x250,0x290 |
| 70 | 43% | 2 | `d21d30cf6e6b` @ 0x0,0x40,0xc0; `70e7ea0193bb` @ 0x100,0x180 |

## Practical Read

- Treat the exported `known-output.bin` files as placement evidence.
- Use chunk identity, duplicate counts, adjacency, and live perturbation
  before claiming a flat decoded record.
- Strong static transform targets should have many unique chunks, few
  duplicates, and preferably record-exclusive singleton chunks.

