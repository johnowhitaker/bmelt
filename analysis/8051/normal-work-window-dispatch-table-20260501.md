# Normal Work-Window Dispatch Stub Table

Source window: `references/evidence/live/normal-work-window-capture-only-20260501/00-capture-only.window.bin`
Start offset: `+0xa17f`
Stop offset: `+0xcaab`
Parsed entries: 1762

The island starts one byte before the public `+0xa180` chunk boundary.
It has a very regular dispatch-stub shape:

- early entries are `MOV A,#selector; LJMP 0x0162`;
- later entries are `MOV DPTR,#param; LJMP resident_handler`.

Important caveat: public offsets in this `READ BUFFER` window are not a
flat mirror of active 8051 code space. The bytes at public `+0x0162` do
not match the static resident bytes at code address `0x0162`. The low
`LJMP` targets do, however, land on plausible resident helper routines in
`analysis/8051/ldm58051.bin`. Treat this as a banked/threaded runtime
artifact until the code-window mapping is pinned down.

## Target Counts

| target | count | resident bytes | public-window bytes |
|---:|---:|---|---|
| `0x0215` | 132 | `ed39fdec38fc908244121df7` | `50dff000000008b8370bb000` |
| `0x0184` | 106 | `fad0e0f9d0e0f8c3ef9bffee` | `f7f2cd35000bf99a1002fccf` |
| `0x01ac` | 94 | `fca3e0fda3e0fea3e0f53a8e` | `00039f04dff00f000044aff0` |
| `0x01ed` | 94 | `90825674c0f0a3e4f0908244` | `000000aff20803aff02401af` |
| `0x01a2` | 86 | `f0904a00e4f0908244e0fca3` | `00ef00000346aff20a050003` |
| `0x0206` | 82 | `27e0fea3e0ffe4fcfdeb2fff` | `51016bf618e6aff15200aff0` |
| `0x0201` | 80 | `a3e0fb908227e0fea3e0ffe4` | `932255aff151016bf618e6af` |
| `0x01de` | 74 | `5cbf0603d38001c350030208` | `04020000aff02501aff00302` |
| `0x0193` | 70 | `99fdec98fc7870121deb904e` | `33fccf00a10000fccf00a100` |
| `0x01d9` | 70 | `1217b312175cbf0603d38001` | `d700c8aff004020000aff025` |
| `0x018e` | 65 | `ffee9afeed99fdec98fc7870` | `fccf00ec0433fccf00a10000` |
| `0x017f` | 61 | `d0e0fbd0e0fad0e0f9d0e0f8` | `f115082d05f7f2cd35000bf9` |
| `0x01b1` | 54 | `e0fea3e0f53a8e398d388c37` | `f00f000044aff00300aff115` |
| `0x0198` | 51 | `7870121deb904e1e7401f090` | `0000fccf00a10000fccf00ef` |
| `0x01fc` | 50 | `e0f9a3e0faa3e0fb908227e0` | `2d05aff160932255aff15101` |
| `0x021a` | 49 | `fc908244121df790824ce0fc` | `0008b8370bb00000b8370bbb` |
| `0x01a7` | 49 | `f0908244e0fca3e0fda3e0fe` | `46aff20a0500039f04dff00f` |
| `0x019d` | 46 | `904e1e7401f0904a00e4f090` | `a10000fccf00ef00000346af` |
| `0x01f7` | 45 | `8244e0f8a3e0f9a3e0faa3e0` | `01aff115082d05aff1609322` |
| `0x01c0` | 40 | `1dc28f3e8e3d8d3c8c3b9082` | `aff1760700d70000aff11508` |
| `0x01bb` | 40 | `8c37786c121dc28f3e8e3d8d` | `f115082d05aff1760700d700` |
| `0x01c5` | 38 | `3d8d3c8c3b908250e0fca3e0` | `d70000aff115082d05aff151` |
| `0x01e8` | 35 | `0208f480ef90825674c0f0a3` | `0302010000000000aff20803` |
| `0x0162` | 32 | `f0908254e0fea3e0ffe4fcfd` | `d70100d7aff115082d05aff1` |
| `0x0210` | 31 | `2fffea3efeed39fdec38fc90` | `aff004030050dff000000008` |
| `0x01d4` | 31 | `fea3e0f5421217b312175cbf` | `aff1760700d700c8aff00402` |
| `0x01cf` | 31 | `a3e0fda3e0fea3e0f5421217` | `f1510c008caff1760700d700` |
| `0x01b6` | 29 | `3a8e398d388c37786c121dc2` | `aff00300aff115082d05aff1` |
| `0x01e3` | 26 | `8001c350030208f480ef9082` | `f02501aff003020100000000` |
| `0x01f2` | 24 | `f0a3e4f0908244e0f8a3e0f9` | `0803aff02401aff115082d05` |
| `0x0189` | 22 | `e0f8c3ef9bffee9afeed99fd` | `0bf99a1002fccf00ec0433fc` |
| `0x01ca` | 21 | `908250e0fca3e0fda3e0fea3` | `15082d05aff1510c008caff1` |
| `0x020b` | 4 | `ffe4fcfdeb2fffea3efeed39` | `e6aff15200aff004030050df` |

## First Entries

| idx | offset | kind | selector/param | target | bytes |
|---:|---:|---|---:|---:|---|
| 0 | `+0xa17f` | mov_a_ljmp | `0x00` | `0x0162` | `7400020162` |
| 1 | `+0xa184` | mov_a_ljmp | `0x01` | `0x0162` | `7401020162` |
| 2 | `+0xa189` | mov_a_ljmp | `0x02` | `0x0162` | `7402020162` |
| 3 | `+0xa18e` | mov_a_ljmp | `0x03` | `0x0162` | `7403020162` |
| 4 | `+0xa193` | mov_a_ljmp | `0x04` | `0x0162` | `7404020162` |
| 5 | `+0xa198` | mov_a_ljmp | `0x05` | `0x0162` | `7405020162` |
| 6 | `+0xa19d` | mov_a_ljmp | `0x06` | `0x0162` | `7406020162` |
| 7 | `+0xa1a2` | mov_a_ljmp | `0x07` | `0x0162` | `7407020162` |
| 8 | `+0xa1a7` | mov_a_ljmp | `0x08` | `0x0162` | `7408020162` |
| 9 | `+0xa1ac` | mov_a_ljmp | `0x09` | `0x0162` | `7409020162` |
| 10 | `+0xa1b1` | mov_a_ljmp | `0x0a` | `0x0162` | `740a020162` |
| 11 | `+0xa1b6` | mov_a_ljmp | `0x0b` | `0x0162` | `740b020162` |
| 12 | `+0xa1bb` | mov_a_ljmp | `0x0c` | `0x0162` | `740c020162` |
| 13 | `+0xa1c0` | mov_a_ljmp | `0x0d` | `0x0162` | `740d020162` |
| 14 | `+0xa1c5` | mov_a_ljmp | `0x0e` | `0x0162` | `740e020162` |
| 15 | `+0xa1ca` | mov_a_ljmp | `0x0f` | `0x0162` | `740f020162` |
| 16 | `+0xa1cf` | mov_a_ljmp | `0x10` | `0x0162` | `7410020162` |
| 17 | `+0xa1d4` | mov_a_ljmp | `0x11` | `0x0162` | `7411020162` |
| 18 | `+0xa1d9` | mov_a_ljmp | `0x12` | `0x0162` | `7412020162` |
| 19 | `+0xa1de` | mov_a_ljmp | `0x13` | `0x0162` | `7413020162` |
| 20 | `+0xa1e3` | mov_a_ljmp | `0x14` | `0x0162` | `7414020162` |
| 21 | `+0xa1e8` | mov_a_ljmp | `0x15` | `0x0162` | `7415020162` |
| 22 | `+0xa1ed` | mov_a_ljmp | `0x16` | `0x0162` | `7416020162` |
| 23 | `+0xa1f2` | mov_a_ljmp | `0x17` | `0x0162` | `7417020162` |
| 24 | `+0xa1f7` | mov_a_ljmp | `0x18` | `0x0162` | `7418020162` |
| 25 | `+0xa1fc` | mov_a_ljmp | `0x19` | `0x0162` | `7419020162` |
| 26 | `+0xa201` | mov_a_ljmp | `0x1a` | `0x0162` | `741a020162` |
| 27 | `+0xa206` | mov_a_ljmp | `0x1b` | `0x0162` | `741b020162` |
| 28 | `+0xa20b` | mov_a_ljmp | `0x1c` | `0x0162` | `741c020162` |
| 29 | `+0xa210` | mov_a_ljmp | `0x1d` | `0x0162` | `741d020162` |
| 30 | `+0xa215` | mov_a_ljmp | `0x1e` | `0x0162` | `741e020162` |
| 31 | `+0xa21a` | mov_a_ljmp | `0x1f` | `0x0162` | `741f020162` |
| 32 | `+0xa21f` | mov_dptr_ljmp | `0xed11` | `0x01e8` | `90ed110201e8` |
| 33 | `+0xa225` | mov_dptr_ljmp | `0xdce5` | `0x01ac` | `90dce50201ac` |
| 34 | `+0xa22b` | mov_dptr_ljmp | `0xf4f4` | `0x01ac` | `90f4f40201ac` |
| 35 | `+0xa231` | mov_dptr_ljmp | `0x89ec` | `0x0206` | `9089ec020206` |
| 36 | `+0xa237` | mov_dptr_ljmp | `0xd239` | `0x01ac` | `90d2390201ac` |
| 37 | `+0xa23d` | mov_dptr_ljmp | `0x9a03` | `0x01ac` | `909a030201ac` |
| 38 | `+0xa243` | mov_dptr_ljmp | `0xfad8` | `0x01ac` | `90fad80201ac` |
| 39 | `+0xa249` | mov_dptr_ljmp | `0xd0bb` | `0x01ac` | `90d0bb0201ac` |
| 40 | `+0xa24f` | mov_dptr_ljmp | `0xe656` | `0x01f2` | `90e6560201f2` |
| 41 | `+0xa255` | mov_dptr_ljmp | `0xdc1a` | `0x01a2` | `90dc1a0201a2` |
| 42 | `+0xa25b` | mov_dptr_ljmp | `0xf0c9` | `0x01a2` | `90f0c90201a2` |
| 43 | `+0xa261` | mov_dptr_ljmp | `0xf0f3` | `0x01f2` | `90f0f30201f2` |
| 44 | `+0xa267` | mov_dptr_ljmp | `0xf851` | `0x01f2` | `90f8510201f2` |
| 45 | `+0xa26d` | mov_dptr_ljmp | `0x57bc` | `0x017f` | `9057bc02017f` |
| 46 | `+0xa273` | mov_dptr_ljmp | `0xe76d` | `0x0198` | `90e76d020198` |
| 47 | `+0xa279` | mov_dptr_ljmp | `0x4014` | `0x017f` | `90401402017f` |
| 48 | `+0xa27f` | mov_dptr_ljmp | `0x4ba3` | `0x017f` | `904ba302017f` |
| 49 | `+0xa285` | mov_dptr_ljmp | `0xdcb1` | `0x021a` | `90dcb102021a` |
| 50 | `+0xa28b` | mov_dptr_ljmp | `0xf0be` | `0x01e8` | `90f0be0201e8` |
| 51 | `+0xa291` | mov_dptr_ljmp | `0xeaff` | `0x01f7` | `90eaff0201f7` |
| 52 | `+0xa297` | mov_dptr_ljmp | `0xb946` | `0x01a7` | `90b9460201a7` |
| 53 | `+0xa29d` | mov_dptr_ljmp | `0x8884` | `0x01f7` | `9088840201f7` |
| 54 | `+0xa2a3` | mov_dptr_ljmp | `0xadd4` | `0x01a7` | `90add40201a7` |
| 55 | `+0xa2a9` | mov_dptr_ljmp | `0xd1c2` | `0x01f7` | `90d1c20201f7` |
| 56 | `+0xa2af` | mov_dptr_ljmp | `0xcacb` | `0x01a7` | `90cacb0201a7` |
| 57 | `+0xa2b5` | mov_dptr_ljmp | `0xf05c` | `0x01e8` | `90f05c0201e8` |
| 58 | `+0xa2bb` | mov_dptr_ljmp | `0xead3` | `0x0198` | `90ead3020198` |
| 59 | `+0xa2c1` | mov_dptr_ljmp | `0x78f4` | `0x0215` | `9078f4020215` |
| 60 | `+0xa2c7` | mov_dptr_ljmp | `0xd6f4` | `0x0215` | `90d6f4020215` |
| 61 | `+0xa2cd` | mov_dptr_ljmp | `0xc2b7` | `0x017f` | `90c2b702017f` |
| 62 | `+0xa2d3` | mov_dptr_ljmp | `0xfe95` | `0x0184` | `90fe95020184` |
| 63 | `+0xa2d9` | mov_dptr_ljmp | `0xef4a` | `0x0184` | `90ef4a020184` |
| 64 | `+0xa2df` | mov_dptr_ljmp | `0xb008` | `0x01a7` | `90b0080201a7` |
| 65 | `+0xa2e5` | mov_dptr_ljmp | `0x9ceb` | `0x017f` | `909ceb02017f` |
| 66 | `+0xa2eb` | mov_dptr_ljmp | `0xc29e` | `0x01a7` | `90c29e0201a7` |
| 67 | `+0xa2f1` | mov_dptr_ljmp | `0xd7b8` | `0x01ed` | `90d7b80201ed` |
| 68 | `+0xa2f7` | mov_dptr_ljmp | `0xf0e5` | `0x0198` | `90f0e5020198` |
| 69 | `+0xa2fd` | mov_dptr_ljmp | `0xcf9a` | `0x01ed` | `90cf9a0201ed` |
| 70 | `+0xa303` | mov_dptr_ljmp | `0xf81f` | `0x0193` | `90f81f020193` |
| 71 | `+0xa309` | mov_dptr_ljmp | `0xe5bf` | `0x01ed` | `90e5bf0201ed` |
| 72 | `+0xa30f` | mov_dptr_ljmp | `0xf29b` | `0x0206` | `90f29b020206` |
| 73 | `+0xa315` | mov_dptr_ljmp | `0xe800` | `0x018e` | `90e80002018e` |
| 74 | `+0xa31b` | mov_dptr_ljmp | `0xefd8` | `0x018e` | `90efd802018e` |
| 75 | `+0xa321` | mov_dptr_ljmp | `0xa636` | `0x0215` | `90a636020215` |
| 76 | `+0xa327` | mov_dptr_ljmp | `0xe631` | `0x01ed` | `90e6310201ed` |
| 77 | `+0xa32d` | mov_dptr_ljmp | `0xf97f` | `0x0193` | `90f97f020193` |
| 78 | `+0xa333` | mov_dptr_ljmp | `0xf792` | `0x0189` | `90f792020189` |
| 79 | `+0xa339` | mov_dptr_ljmp | `0xed55` | `0x0189` | `90ed55020189` |
| 80 | `+0xa33f` | mov_dptr_ljmp | `0xf7e3` | `0x0189` | `90f7e3020189` |
| 81 | `+0xa345` | mov_dptr_ljmp | `0xf320` | `0x0215` | `90f320020215` |
| 82 | `+0xa34b` | mov_dptr_ljmp | `0xc91d` | `0x01a7` | `90c91d0201a7` |
| 83 | `+0xa351` | mov_dptr_ljmp | `0x955d` | `0x01fc` | `90955d0201fc` |
| 84 | `+0xa357` | mov_dptr_ljmp | `0xcd89` | `0x01ac` | `90cd890201ac` |
| 85 | `+0xa35d` | mov_dptr_ljmp | `0xbe80` | `0x01a7` | `90be800201a7` |
| 86 | `+0xa363` | mov_dptr_ljmp | `0xf78a` | `0x0198` | `90f78a020198` |
| 87 | `+0xa369` | mov_dptr_ljmp | `0xf3ab` | `0x0198` | `90f3ab020198` |
| 88 | `+0xa36f` | mov_dptr_ljmp | `0xed90` | `0x01ed` | `90ed900201ed` |
| 89 | `+0xa375` | mov_dptr_ljmp | `0xe94c` | `0x01ed` | `90e94c0201ed` |
| 90 | `+0xa37b` | mov_dptr_ljmp | `0xdd97` | `0x01f2` | `90dd970201f2` |
| 91 | `+0xa381` | mov_dptr_ljmp | `0xde1a` | `0x01ac` | `90de1a0201ac` |
| 92 | `+0xa387` | mov_dptr_ljmp | `0xfb0b` | `0x0193` | `90fb0b020193` |
| 93 | `+0xa38d` | mov_dptr_ljmp | `0xd5e2` | `0x0184` | `90d5e2020184` |
| 94 | `+0xa393` | mov_dptr_ljmp | `0xcb65` | `0x0184` | `90cb65020184` |
| 95 | `+0xa399` | mov_dptr_ljmp | `0xbec6` | `0x0184` | `90bec6020184` |

## Interpretation

- The low branch targets are real resident code offsets in
  `analysis/8051/ldm58051.bin`, even though the public work-window bytes
  at those low offsets are different.
- Entry `0..31` gives a compact default-selector path through
  `0x0162`; those selectors line up with the command-like byte tests seen
  against `xdata[0x8a49]`.
- The `MOV DPTR,#param; LJMP handler` entries look like a second-stage
  threaded-code table with a per-entry parameter. This is a better
  analysis target than treating the `+0xa180..` island as linear code.
