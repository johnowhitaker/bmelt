# CDD Runtime Chunk Contigs

Date: 2026-05-01

Offline only. No drive commands were sent.

This treats 0x40-byte normal work-window chunks as graph nodes and
uses repeated host-visible adjacency to build local decoded-runtime
contigs. These contigs are more trustworthy than the flat
`record-XXX-known-output.bin` placement arrays, but they are still
runtime tile neighborhoods rather than proven CDD decoded addresses.

## Summary

- captures scanned: `669`
- known chunk nodes: `96`
- directed edges: `114`
- non-self edges: `114`
- self-loop edges: `0`
- dominant edges kept: `43`
- contigs: `25`

## Contigs

| contig | chunks | bytes | common records | union records | chunk path |
| --- | --- | --- | --- | --- | --- |
| 0 | 5 | 320 | - | 68,69 | `85545872cc2b` -> `c5c0741f5daa` -> `17a7e3a30d12` -> `7106a72e56d9` -> `5a0c5fbcd38c` |
| 1 | 4 | 256 | - | 62,63,64 | `25333cae3674` -> `204291444868` -> `2b9a017b9d81` -> `c24221ec1018` |
| 2 | 4 | 256 | - | 67,68 | `add3eb18b8cc` -> `037cda80b040` -> `0803afdb9f57` -> `ad2faf50bc31` |
| 3 | 3 | 192 | 51 | 51,52 | `0a8cd35adb0f` -> `056348c5dbbf` -> `39ab42ddd82a` |
| 4 | 3 | 192 | 59 | 58,59,60 | `20ea2ab16891` -> `99d4493dc4cf` -> `b7a129b7d392` |
| 5 | 3 | 192 | - | 50,51 | `2598f9591a20` -> `0f031dd8ed37` -> `fe95f1ed098a` |
| 6 | 3 | 192 | - | 52,53 | `80b60d722518` -> `c8c5359c53cb` -> `593d3704fc52` |
| 7 | 3 | 192 | - | 64,65 | `b69f366c92b6` -> `7a8cbb7773e7` -> `9e474876a043` |
| 8 | 3 | 192 | 57 | 57,58 | `cfe0a1406283` -> `ee30d1b5daca` -> `5fb5a8bf8f9a` |
| 9 | 2 | 128 | 86,87 | 86,87 | `0b045c0906d5` -> `71a589c84051` |
| 10 | 2 | 128 | - | 49,50 | `0c705773105c` -> `6c4f90652e56` |
| 11 | 2 | 128 | 62 | 61,62 | `0c9a360d26b8` -> `3465e4783c3d` |
| 12 | 2 | 128 | 54 | 54 | `121190698133` -> `1a8df790ad50` |
| 13 | 2 | 128 | 81,83 | 81,82,83 | `144315176c64` -> `fbb6be935285` |
| 14 | 2 | 128 | 87 | 87 | `183ec6fd07c7` -> `ba3aab1d5fd2` |
| 15 | 2 | 128 | 70 | 70 | `23c16a978aa0` -> `70e7ea0193bb` |
| 16 | 2 | 128 | 55,56 | 55,56 | `25956f88a30e` -> `4f29221f2e51` |
| 17 | 2 | 128 | 66 | 66 | `404045e0e63c` -> `efcb6299a750` |
| 18 | 2 | 128 | 60 | 60 | `4cfa6d151318` -> `28583441dfa8` |
| 19 | 2 | 128 | 74 | 73,74 | `536f157a8567` -> `4a6f7bda07c9` |
| 20 | 2 | 128 | 58 | 58 | `7e15398acc97` -> `8f8e0add044c` |
| 21 | 2 | 128 | 55 | 55 | `95caa55b881e` -> `a87d03db223d` |
| 22 | 2 | 128 | 66 | 66 | `9aa0a39b4424` -> `fe343ef73975` |
| 23 | 2 | 128 | 70 | 70 | `d21d30cf6e6b` -> `fb00deab088b` |
| 24 | 2 | 128 | 88 | 88 | `eda48f3e289c` -> `7fabb1c7616c` |

## Dominant Edges

| src | dst | count | src records | dst records | top offsets |
| --- | --- | --- | --- | --- | --- |
| `0b045c0906d5` | `71a589c84051` | 454 | 86,87 | 86,87 | `0x9900` x256, `0x9940` x198 |
| `0c9a360d26b8` | `3465e4783c3d` | 413 | 61,62 | 62 | `0x7600` x413 |
| `23c16a978aa0` | `70e7ea0193bb` | 413 | 70 | 70 | `0x8840` x413 |
| `99d4493dc4cf` | `b7a129b7d392` | 413 | 59 | 59,60 | `0x71c0` x413 |
| `204291444868` | `2b9a017b9d81` | 369 | 63 | 63 | `0x7800` x369 |
| `85545872cc2b` | `c5c0741f5daa` | 330 | 68 | 68 | `0x8440` x330 |
| `144315176c64` | `fbb6be935285` | 275 | 81,83 | 81,82,83 | `0x9480` x261, `0x9400` x14 |
| `121190698133` | `1a8df790ad50` | 256 | 54 | 54 | `0x6880` x256 |
| `c5c0741f5daa` | `17a7e3a30d12` | 256 | 68 | 68 | `0x84c0` x256 |
| `4cfa6d151318` | `28583441dfa8` | 255 | 60 | 60 | `0x7340` x255 |
| `7a8cbb7773e7` | `9e474876a043` | 254 | 65 | 65 | `0x7bc0` x254 |
| `b69f366c92b6` | `7a8cbb7773e7` | 254 | 64 | 65 | `0x7b80` x254 |
| `add3eb18b8cc` | `037cda80b040` | 253 | 67 | 67 | `0x8240` x253 |
| `404045e0e63c` | `efcb6299a750` | 239 | 66 | 66 | `0x7f40` x107, `0x7f00` x72, `0x7f80` x60 |
| `20ea2ab16891` | `99d4493dc4cf` | 219 | 58,59 | 59 | `0x7180` x219 |
| `2b9a017b9d81` | `c24221ec1018` | 219 | 63 | 64 | `0x78c0` x219 |
| `d21d30cf6e6b` | `fb00deab088b` | 206 | 70 | 70 | `0x8740` x105, `0x8780` x54, `0x8700` x47 |
| `a87d03db223d` | `95caa55b881e` | 203 | 55 | 55 | `0x6b40` x184, `0x6b00` x14, `0x6b80` x5 |
| `4f29221f2e51` | `25956f88a30e` | 197 | 55,56 | 55,56 | `0x6c40` x125, `0x6c80` x72 |
| `fbb6be935285` | `144315176c64` | 190 | 81,82,83 | 81,83 | `0x9440` x111, `0x9480` x79 |
| `17a7e3a30d12` | `7106a72e56d9` | 167 | 68 | 68,69 | `0x8500` x167 |
| `0f031dd8ed37` | `fe95f1ed098a` | 165 | 51 | 51 | `0x6380` x165 |
| `cfe0a1406283` | `ee30d1b5daca` | 162 | 57 | 57 | `0x6e80` x162 |
| `9aa0a39b4424` | `fe343ef73975` | 157 | 66 | 66 | `0x7e80` x110, `0x7e00` x47 |

## Self-Loops

Self-loops usually indicate the same public tile repeated in adjacent
slots. They are useful evidence of repetition, but not useful contig
extension edges.

| chunk | records | count | offsets |
| --- | --- | --- | --- |

## Practical Read

- Use contigs as decoded-runtime byte runs for static inspection.
- Use common/union record buckets only as candidate provenance.
- If a contig matters, validate its CDD ownership with a live
  perturbation oracle before treating it as a record decode.

