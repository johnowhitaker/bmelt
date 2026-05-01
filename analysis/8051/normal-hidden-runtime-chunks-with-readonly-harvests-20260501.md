# Normal Hidden Runtime Chunk Analysis

Date: 2026-05-01

This is an offline analysis of the normal-mode `READ BUFFER id=01/02 offset=0x070000` work-window captures. It treats the window as a rotating `0x40`-byte tile surface, not as one stable linear image.

## Summary

- captures scanned: `669`
- unique chunks: `902`
- chunks with exact visible/currentboot reference match: `501`
- chunks without exact visible/currentboot reference match: `401`
- interesting hidden chunks: `96` shown

The useful new distinction is that several normal-runtime chunks are stable and code-like but do not appear byte-for-byte in F0, the visible 8051 slice, the helper overlay, or the currentboot gateway dump. Those chunks are plausible decoded-controller/runtime material, but their public slot offsets rotate, so a slot like `+0x7140` should not be treated as a fixed CDD decoded address by itself.

## Baseline Window Hashes

| file | sha256 |
| --- | --- |
| `references/evidence/live/normal-read-buffer-work-window-20260501/id01-070000-010000-repeat1.bin` | `1c6b88248e4fdc92...` |
| `references/evidence/live/normal-read-buffer-work-window-20260501/id01-070000-010000-repeat2.bin` | `d9e97157de47943d...` |
| `references/evidence/live/normal-read-buffer-work-window-20260501/id01-070000-010000.bin` | `c3cd6e6d3e25a55e...` |
| `references/evidence/live/normal-read-buffer-work-window-20260501/id02-070000-010000-repeat1.bin` | `7ff6f16aab240dd3...` |
| `references/evidence/live/normal-read-buffer-work-window-20260501/id02-070000-010000-repeat2.bin` | `bc160b7767b3d8c2...` |
| `references/evidence/live/normal-read-buffer-work-window-20260501/id02-070000-010000.bin` | `3c78f44b80e972ea...` |

The differing hashes are expected: even the baseline reads expose different rotating tiles. Repeated chunk identity and adjacency are more trustworthy than whole-window equality.

## Anchor Chunks

| anchor | chunk | obs | top public offsets | exact refs | CDD candidates if offset is trusted |
| --- | --- | --- | --- | --- | --- |
| `public_bridge_8a4c_to_4011` | `20ea2ab16891` | 669 | 0x7140 x314, 0x7180 x219, 0x7100 x136 | - | 0x7140 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80); 0x7100 -> rec 58 (0x80) |
| `public_bridge_8a4d_to_4012` | `20ea2ab16891` | 669 | 0x7140 x314, 0x7180 x219, 0x7100 x136 | - | 0x7140 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80); 0x7100 -> rec 58 (0x80) |
| `public_bridge_8a4e_to_4013` | `20ea2ab16891` | 669 | 0x7140 x314, 0x7180 x219, 0x7100 x136 | - | 0x7140 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80); 0x7100 -> rec 58 (0x80) |
| `getcfg_4099_to_shadow` | `8d8c3b0a22a0` | 44 | 0x7140 x22, 0x7100 x12, 0x7180 x10 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `getcfg_fe_sentinel_branch` | `8d8c3b0a22a0` | 44 | 0x7140 x22, 0x7100 x12, 0x7180 x10 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `controller_addr_4091` | `4037c8574920` | 44 | 0x70c0 x19, 0x7000 x17, 0x7080 x8 | - | 0x70c0 -> rec 58 (0x80); 0x7000 -> rec 58 (0x80); 0x7080 -> rec 58 (0x80) |
| `controller_kick_409c` | `4037c8574920` | 44 | 0x70c0 x19, 0x7000 x17, 0x7080 x8 | - | 0x70c0 -> rec 58 (0x80); 0x7000 -> rec 58 (0x80); 0x7080 -> rec 58 (0x80) |
| `controller_addr_4095` | `28583441dfa8` | 668 | 0x7380 x668 | - | 0x7380 -> rec 60 (0x40) |

The repeated CDD candidate changes for the same chunk are the important sanity check. For example, the public bridge chunk appears at several public offsets, which would place it in different CDD records if we naively trusted the slot number. That argues against using normal public offsets as direct decoded CDD addresses without an additional address/phase model.

## Phase Sanity Check

I also tested the tempting idea that the whole 64 KiB work-window is just globally shifted by the public bridge chunk. It is not. The bridge appears once in every capture and its local phase is real, but using it as a global scroll offset makes the window *less* stable overall.

| view | captures | stable 100% | stable >=95% | stable >=90% | positions |
| --- | --- | --- | --- | --- | --- |
| `raw public offsets` | 669 | 739 | 742 | 742 | 1024 |
| `bridge-aligned` | 669 | 244 | 244 | 244 | 1024 |

Bridge phases:

| phase vs +0x7140 | captures |
| --- | --- |
| `+0x0` | 314 |
| `+0x40` | 219 |
| `-0x40` | 136 |

So the public bridge gives a local anchor for one response-builder island, not a universal address correction for the whole work-window.

## Top Hidden Runtime Chunks

| chunk | obs | top public offsets | exact refs | patterns | interesting refs |
| --- | --- | --- | --- | --- | --- |
| `20ea2ab16891` | 669 | 0x7140 x314, 0x7180 x219, 0x7100 x136 | - | public_bridge_8a4c_to_4011, public_bridge_8a4d_to_4012, public_bridge_8a4e_to_4013 | packet_shadow:5, controller_status:4 |
| `8d8c3b0a22a0` | 44 | 0x7140 x22, 0x7100 x12, 0x7180 x10 | - | getcfg_4099_to_shadow, getcfg_fe_sentinel_branch | controller_status:3, packet_shadow:5 |
| `2111cafaf69c` | 669 | 0x9580 x172, 0x9540 x170, 0x9500 x170, 0x95c0 x157 | - | - | packet_shadow:8, front_panel_or_status:7 |
| `4037c8574920` | 44 | 0x70c0 x19, 0x7000 x17, 0x7080 x8 | - | controller_addr_4091, controller_kick_409c | controller_status:6, packet_shadow:1 |
| `28583441dfa8` | 668 | 0x7380 x668 | - | controller_addr_4095, controller_kick_409c | controller_status:4, packet_shadow:1 |
| `0c9a360d26b8` | 668 | 0x7600 x413, 0x76c0 x255 | - | controller_addr_4091, controller_kick_409c | controller_status:4, packet_shadow:1 |
| `9b673c066ae4` | 666 | 0x74c0 x502, 0x7480 x164 | - | controller_kick_409c | controller_status:5, packet_shadow:4 |
| `c5c0741f5daa` | 644 | 0x8480 x330, 0x84c0 x256, 0x8400 x58 | - | - | profile_string_area:4, packet_shadow:7, front_panel_or_status:2 |
| `580b9228d0b9` | 256 | 0x7640 x256 | - | controller_addr_4095, controller_kick_409c | controller_status:5 |
| `fb00deab088b` | 669 | 0x8780 x271, 0x87c0 x139, 0x8700 x130, 0x8740 x129 | - | controller_addr_4091 | controller_status:8 |
| `95caa55b881e` | 597 | 0x6b80 x268, 0x6b00 x143, 0x6bc0 x125, 0x6b40 x61 | - | - | packet_shadow:7, front_panel_or_status:5 |
| `efcb6299a750` | 336 | 0x7f80 x185, 0x7f40 x91, 0x7fc0 x60 | - | controller_kick_409c | controller_status:5, packet_shadow:3 |
| `70e7ea0193bb` | 669 | 0x8880 x413, 0x8800 x256 | - | - | packet_shadow:7, profile_string_area:2, front_panel_or_status:2 |
| `3465e4783c3d` | 413 | 0x7640 x413 | - | controller_addr_4091 | packet_shadow:2, controller_status:5 |
| `99d4493dc4cf` | 669 | 0x71c0 x669 | - | - | packet_shadow:10 |
| `b69f366c92b6` | 667 | 0x7b00 x413, 0x7b80 x254 | - | controller_addr_4091 | packet_shadow:3, controller_status:3 |
| `ba3aab1d5fd2` | 445 | 0x9b40 x240, 0x9b00 x136, 0x9b80 x62, 0x9bc0 x7 | - | controller_addr_4091 | controller_status:6 |
| `fe343ef73975` | 383 | 0x7e40 x168, 0x7ec0 x139, 0x7e80 x68, 0x7e00 x8 | - | controller_addr_4091 | packet_shadow:4, controller_status:2 |
| `8b2115cd509f` | 32 | 0x7140 x18, 0x7100 x9, 0x7180 x5 | - | controller_addr_4091 | front_panel_or_status:1, controller_status:4, packet_shadow:1 |
| `0c705773105c` | 669 | 0x6080 x174, 0x60c0 x167, 0x6000 x166, 0x6040 x162 | - | - | packet_shadow:4, controller_status:2, front_panel_or_status:3 |
| `8f8e0add044c` | 669 | 0x70c0 x322, 0x7080 x195, 0x7000 x152 | - | - | packet_shadow:6, controller_status:3 |
| `144315176c64` | 669 | 0x9480 x372, 0x94c0 x215, 0x9400 x82 | - | - | packet_shadow:6, front_panel_or_status:3 |
| `25333cae3674` | 668 | 0x7780 x413, 0x77c0 x255 | - | controller_addr_4095 | packet_shadow:3, controller_status:2 |
| `204291444868` | 548 | 0x7800 x511, 0x78c0 x37 | - | controller_kick_409c | controller_status:4, packet_shadow:1 |
| `7106a72e56d9` | 493 | 0x8580 x260, 0x8540 x167, 0x85c0 x66 | - | - | front_panel_or_status:2, packet_shadow:3, profile_string_area:4 |
| `04a2d67cbfff` | 428 | 0x7dc0 x428 | - | - | controller_status:7, packet_shadow:2 |
| `add3eb18b8cc` | 400 | 0x8240 x400 | - | - | front_panel_or_status:6, packet_shadow:3 |
| `6c4f90652e56` | 669 | 0x6180 x222, 0x61c0 x218, 0x6100 x136, 0x6140 x93 | - | - | packet_shadow:3, front_panel_or_status:4, controller_status:1 |
| `b7a129b7d392` | 669 | 0x7200 x413, 0x72c0 x256 | - | - | packet_shadow:8 |
| `85545872cc2b` | 669 | 0x8440 x669 | - | - | packet_shadow:8 |
| `7fabb1c7616c` | 669 | 0x9f40 x283, 0x9f80 x261, 0x9f00 x69, 0x9fc0 x56 | - | - | front_panel_or_status:5, packet_shadow:2, controller_status:1 |
| `24ebe8bb67f5` | 668 | 0x7980 x413, 0x79c0 x255 | - | controller_kick_409c | controller_status:3, packet_shadow:1 |
| `9e474876a043` | 667 | 0x7c40 x413, 0x7c00 x254 | - | controller_addr_4095 | packet_shadow:3, controller_status:1 |
| `0f031dd8ed37` | 652 | 0x6300 x431, 0x6380 x165, 0x6340 x56 | - | - | front_panel_or_status:3, packet_shadow:5 |
| `2598f9591a20` | 644 | 0x6240 x345, 0x6280 x160, 0x62c0 x139 | - | - | packet_shadow:6, front_panel_or_status:2 |
| `03044422ea30` | 338 | 0x9e40 x115, 0x9e00 x92, 0x9ec0 x80, 0x9e80 x51 | - | - | front_panel_or_status:3, packet_shadow:5 |
| `5a65b8a71db9` | 218 | 0x91c0 x118, 0x9180 x100 | - | - | controller_status:4, packet_shadow:4 |
| `5a0c5fbcd38c` | 163 | 0x85c0 x163 | - | controller_addr_4091 | controller_status:4 |
| `ee30d1b5daca` | 162 | 0x6ec0 x162 | - | - | packet_shadow:5, controller_status:3 |
| `5a92e83e04a8` | 54 | 0x8580 x33, 0x85c0 x21 | - | - | front_panel_or_status:5, packet_shadow:3 |
| `0e790c42bd72` | 5 | 0x8740 x2, 0x8700 x2, 0x87c0 x1 | - | - | packet_shadow:6, profile_string_area:2 |
| `fe95f1ed098a` | 669 | 0x63c0 x413, 0x6380 x256 | - | - | packet_shadow:6, front_panel_or_status:1 |
| `cfe0a1406283` | 669 | 0x6e80 x413, 0x6ec0 x256 | - | - | packet_shadow:7 |
| `4cfa6d151318` | 669 | 0x7300 x413, 0x7340 x256 | - | - | packet_shadow:6, front_panel_or_status:1 |
| `037cda80b040` | 669 | 0x8280 x413, 0x82c0 x256 | - | - | packet_shadow:7 |
| `ad2faf50bc31` | 669 | 0x83c0 x669 | - | - | packet_shadow:7 |
| `306eb529b363` | 669 | 0x9880 x515, 0x98c0 x76, 0x9840 x54, 0x9800 x24 | - | - | packet_shadow:7 |
| `71a589c84051` | 669 | 0x9980 x382, 0x9940 x256, 0x9900 x31 | - | - | packet_shadow:7 |
| `80b60d722518` | 486 | 0x6680 x256, 0x6640 x177, 0x66c0 x53 | - | - | front_panel_or_status:4, packet_shadow:3 |
| `4f29221f2e51` | 409 | 0x6cc0 x167, 0x6c40 x125, 0x6c80 x95, 0x6c00 x22 | - | - | packet_shadow:7 |
| `c684e9945319` | 223 | 0x7580 x127, 0x75c0 x96 | - | - | packet_shadow:5, controller_status:2 |
| `99277d40b327` | 114 | 0x6d80 x114 | - | - | packet_shadow:7 |
| `86709485b961` | 43 | 0x69c0 x43 | - | - | packet_shadow:7 |
| `878984a494b8` | 40 | 0x6b80 x14, 0x6b00 x13, 0x6bc0 x7, 0x6b40 x6 | - | - | packet_shadow:6, front_panel_or_status:1 |
| `796c2cf9d837` | 19 | 0x6b00 x6, 0x6b40 x5, 0x6b80 x5, 0x6bc0 x3 | - | - | packet_shadow:4, front_panel_or_status:3 |
| `dbf01786a7ed` | 13 | 0x6b80 x4, 0x6b00 x4, 0x6b40 x4, 0x6bc0 x1 | - | - | packet_shadow:7 |
| `8853b78ca23e` | 669 | 0x6ac0 x310, 0x6a80 x192, 0x6a00 x90, 0x6a40 x77 | - | - | controller_status:5, packet_shadow:1 |
| `25956f88a30e` | 669 | 0x6c80 x243, 0x6cc0 x198, 0x6c00 x188, 0x6c40 x40 | - | - | packet_shadow:6 |
| `404045e0e63c` | 669 | 0x7fc0 x186, 0x7f00 x165, 0x7f80 x160, 0x7f40 x158 | - | - | front_panel_or_status:2, packet_shadow:4 |
| `17a7e3a30d12` | 669 | 0x8500 x669 | - | - | packet_shadow:5, controller_status:1 |
| `23c16a978aa0` | 669 | 0x8840 x413, 0x8880 x256 | - | - | packet_shadow:5, front_panel_or_status:1 |
| `fbb6be935285` | 669 | 0x94c0 x324, 0x9440 x257, 0x9480 x84, 0x9400 x4 | - | - | front_panel_or_status:6 |
| `0b045c0906d5` | 669 | 0x9900 x419, 0x9940 x198, 0x99c0 x52 | - | - | packet_shadow:6 |
| `183ec6fd07c7` | 669 | 0x9ac0 x225, 0x9a40 x172, 0x9a80 x142, 0x9a00 x130 | - | - | packet_shadow:6 |
| `c2560553eb14` | 669 | 0x9c80 x326, 0x9c00 x164, 0x9c40 x163, 0x9cc0 x16 | - | - | packet_shadow:6 |
| `056348c5dbbf` | 634 | 0x6500 x345, 0x6540 x113, 0x65c0 x90, 0x6580 x86 | - | - | front_panel_or_status:4, packet_shadow:2 |
| `2b9a017b9d81` | 632 | 0x7840 x413, 0x78c0 x219 | - | - | packet_shadow:6 |
| `1a8df790ad50` | 597 | 0x68c0 x597 | - | - | profile_string_area:2, front_panel_or_status:4 |
| `0803afdb9f57` | 578 | 0x8300 x427, 0x8380 x151 | - | - | packet_shadow:4, front_panel_or_status:1, profile_string_area:1 |
| `c8c5359c53cb` | 521 | 0x6700 x404, 0x67c0 x117 | - | - | packet_shadow:6 |
| `b4bb17eb1656` | 521 | 0x7540 x256, 0x75c0 x196, 0x7580 x69 | - | - | packet_shadow:3, front_panel_or_status:3 |
| `70221f447d35` | 487 | 0x6480 x243, 0x6440 x186, 0x64c0 x48, 0x6400 x10 | - | - | packet_shadow:4, front_panel_or_status:2 |
| `1fc002817f62` | 318 | 0x9100 x219, 0x9180 x57, 0x91c0 x42 | - | - | packet_shadow:3, controller_status:3 |
| `593d3704fc52` | 256 | 0x6740 x256 | - | - | front_panel_or_status:1, profile_string_area:5 |
| `121190698133` | 256 | 0x6880 x256 | - | - | profile_string_area:3, front_panel_or_status:3 |
| `17e05da2c29c` | 256 | 0x7980 x256 | - | - | packet_shadow:6 |
| `5badff03bdb8` | 148 | 0x8480 x148 | - | - | packet_shadow:6 |
| `39ab42ddd82a` | 130 | 0x6600 x44, 0x66c0 x43, 0x6640 x28, 0x6680 x15 | - | - | packet_shadow:6 |
| `3065e119a794` | 107 | 0x6440 x45, 0x6400 x44, 0x6480 x18 | - | - | packet_shadow:6 |
| `0a8cd35adb0f` | 52 | 0x6580 x35, 0x65c0 x12, 0x6500 x5 | - | - | packet_shadow:6 |
| `3dcd6687529a` | 14 | 0x6ec0 x14 | - | - | front_panel_or_status:4, packet_shadow:2 |
| `eda48f3e289c` | 9 | 0x9f80 x9 | - | - | packet_shadow:4, front_panel_or_status:2 |
| `ac6243637e2d` | 5 | 0x6080 x3, 0x6000 x1, 0x6040 x1 | - | - | front_panel_or_status:1, packet_shadow:5 |
| `a87d03db223d` | 669 | 0x6b40 x358, 0x6bc0 x224, 0x6b00 x65, 0x6b80 x22 | - | - | front_panel_or_status:2, packet_shadow:3 |
| `5fb5a8bf8f9a` | 669 | 0x6f40 x300, 0x6f00 x190, 0x6f80 x93, 0x6fc0 x86 | - | - | packet_shadow:5 |
| `7e15398acc97` | 669 | 0x7000 x334, 0x7040 x256, 0x70c0 x41, 0x7080 x38 | - | - | packet_shadow:3, front_panel_or_status:2 |
| `6d249b0b8b59` | 669 | 0x7500 x413, 0x7580 x256 | - | - | front_panel_or_status:5 |
| `c24221ec1018` | 669 | 0x7940 x413, 0x7900 x256 | - | - | front_panel_or_status:4, packet_shadow:1 |
| `7a8cbb7773e7` | 669 | 0x7bc0 x669 | - | - | packet_shadow:4, front_panel_or_status:1 |
| `97d7a6c10602` | 669 | 0x7d00 x413, 0x7d40 x256 | - | - | controller_status:3, front_panel_or_status:1, packet_shadow:1 |
| `9aa0a39b4424` | 669 | 0x7e80 x413, 0x7e00 x256 | - | - | packet_shadow:4, front_panel_or_status:1 |
| `bd4b736c6b8d` | 669 | 0x8000 x256, 0x8040 x253, 0x8080 x160 | - | - | packet_shadow:5 |
| `d21d30cf6e6b` | 669 | 0x8700 x209, 0x8740 x195, 0x87c0 x140, 0x8780 x125 | - | - | packet_shadow:4, profile_string_area:1 |
| `536f157a8567` | 669 | 0x8b80 x224, 0x8b40 x205, 0x8bc0 x176, 0x8b00 x64 | - | - | front_panel_or_status:5 |
| `4a6f7bda07c9` | 669 | 0x8c40 x413, 0x8c00 x256 | - | - | profile_string_area:2, front_panel_or_status:3 |
| `2b41f440f0be` | 669 | 0x8f00 x669 | - | - | front_panel_or_status:3, packet_shadow:2 |

These are the best current offline targets for reverse engineering normal runtime plumbing. Chunks with `controller_status` references tend to touch the `0x4000..0x409c` controller gateway; chunks with `front_panel_or_status` references are candidates for the LED/button/mechanism fabric, but should be treated carefully because reads of `0x47xx` and related paths have wedged the drive before.

## Practical Read

- The normal work-window is still a promising source of hidden runtime code, probably including decoded-controller or overlay material.
- The work-window is not a clean linear decoded CDD image. The same chunk can occupy multiple public slots, so public offset alone is not enough to map a chunk to a CDD record.
- The stable public response bridge remains the best host-visible patch target once we have a normal-mode write primitive.
- For static CDD work, these chunks are useful known-output candidates only after we learn the missing address/phase relationship between rotating work-window tiles and the controller's decoded address space.
