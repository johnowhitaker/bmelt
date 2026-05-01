# Normal Hidden Runtime Chunk Analysis

Date: 2026-05-01

This is an offline analysis of the normal-mode `READ BUFFER id=01/02 offset=0x070000` work-window captures. It treats the window as a rotating `0x40`-byte tile surface, not as one stable linear image.

## Summary

- captures scanned: `549`
- unique chunks: `899`
- chunks with exact visible/currentboot reference match: `501`
- chunks without exact visible/currentboot reference match: `398`
- interesting hidden chunks: `64` shown

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
| `public_bridge_8a4c_to_4011` | `20ea2ab16891` | 549 | 0x7140 x251, 0x7180 x162, 0x7100 x136 | - | 0x7140 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80); 0x7100 -> rec 58 (0x80) |
| `public_bridge_8a4d_to_4012` | `20ea2ab16891` | 549 | 0x7140 x251, 0x7180 x162, 0x7100 x136 | - | 0x7140 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80); 0x7100 -> rec 58 (0x80) |
| `public_bridge_8a4e_to_4013` | `20ea2ab16891` | 549 | 0x7140 x251, 0x7180 x162, 0x7100 x136 | - | 0x7140 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80); 0x7100 -> rec 58 (0x80) |
| `getcfg_4099_to_shadow` | `8d8c3b0a22a0` | 39 | 0x7140 x21, 0x7100 x12, 0x7180 x6 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `getcfg_fe_sentinel_branch` | `8d8c3b0a22a0` | 39 | 0x7140 x21, 0x7100 x12, 0x7180 x6 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `controller_addr_4091` | `4037c8574920` | 39 | 0x70c0 x17, 0x7000 x15, 0x7080 x7 | - | 0x70c0 -> rec 58 (0x80); 0x7000 -> rec 58 (0x80); 0x7080 -> rec 58 (0x80) |
| `controller_kick_409c` | `4037c8574920` | 39 | 0x70c0 x17, 0x7000 x15, 0x7080 x7 | - | 0x70c0 -> rec 58 (0x80); 0x7000 -> rec 58 (0x80); 0x7080 -> rec 58 (0x80) |
| `controller_addr_4095` | `28583441dfa8` | 548 | 0x7380 x548 | - | 0x7380 -> rec 60 (0x40) |

The repeated CDD candidate changes for the same chunk are the important sanity check. For example, the public bridge chunk appears at several public offsets, which would place it in different CDD records if we naively trusted the slot number. That argues against using normal public offsets as direct decoded CDD addresses without an additional address/phase model.

## Phase Sanity Check

I also tested the tempting idea that the whole 64 KiB work-window is just globally shifted by the public bridge chunk. It is not. The bridge appears once in every capture and its local phase is real, but using it as a global scroll offset makes the window *less* stable overall.

| view | captures | stable 100% | stable >=95% | stable >=90% | positions |
| --- | --- | --- | --- | --- | --- |
| `raw public offsets` | 549 | 739 | 742 | 746 | 1024 |
| `bridge-aligned` | 549 | 244 | 244 | 244 | 1024 |

Bridge phases:

| phase vs +0x7140 | captures |
| --- | --- |
| `+0x0` | 251 |
| `+0x40` | 162 |
| `-0x40` | 136 |

So the public bridge gives a local anchor for one response-builder island, not a universal address correction for the whole work-window.

## Top Hidden Runtime Chunks

| chunk | obs | top public offsets | exact refs | patterns | interesting refs |
| --- | --- | --- | --- | --- | --- |
| `20ea2ab16891` | 549 | 0x7140 x251, 0x7180 x162, 0x7100 x136 | - | public_bridge_8a4c_to_4011, public_bridge_8a4d_to_4012, public_bridge_8a4e_to_4013 | packet_shadow:5, controller_status:4 |
| `8d8c3b0a22a0` | 39 | 0x7140 x21, 0x7100 x12, 0x7180 x6 | - | getcfg_4099_to_shadow, getcfg_fe_sentinel_branch | controller_status:3, packet_shadow:5 |
| `2111cafaf69c` | 549 | 0x9540 x150, 0x9580 x139, 0x9500 x137, 0x95c0 x123 | - | - | packet_shadow:8, front_panel_or_status:7 |
| `4037c8574920` | 39 | 0x70c0 x17, 0x7000 x15, 0x7080 x7 | - | controller_addr_4091, controller_kick_409c | controller_status:6, packet_shadow:1 |
| `c5c0741f5daa` | 549 | 0x8480 x293, 0x84c0 x256 | - | - | profile_string_area:4, packet_shadow:7, front_panel_or_status:2 |
| `28583441dfa8` | 548 | 0x7380 x548 | - | controller_addr_4095, controller_kick_409c | controller_status:4, packet_shadow:1 |
| `0c9a360d26b8` | 548 | 0x7600 x293, 0x76c0 x255 | - | controller_addr_4091, controller_kick_409c | controller_status:4, packet_shadow:1 |
| `9b673c066ae4` | 546 | 0x74c0 x502, 0x7480 x44 | - | controller_kick_409c | controller_status:5, packet_shadow:4 |
| `580b9228d0b9` | 256 | 0x7640 x256 | - | controller_addr_4095, controller_kick_409c | controller_status:5 |
| `fb00deab088b` | 549 | 0x8780 x257, 0x8740 x118, 0x87c0 x93, 0x8700 x81 | - | controller_addr_4091 | controller_status:8 |
| `95caa55b881e` | 513 | 0x6b80 x248, 0x6b00 x117, 0x6bc0 x103, 0x6b40 x45 | - | - | packet_shadow:7, front_panel_or_status:5 |
| `efcb6299a750` | 264 | 0x7f80 x185, 0x7fc0 x60, 0x7f40 x19 | - | controller_kick_409c | controller_status:5, packet_shadow:3 |
| `70e7ea0193bb` | 549 | 0x8880 x293, 0x8800 x256 | - | - | packet_shadow:7, profile_string_area:2, front_panel_or_status:2 |
| `3465e4783c3d` | 293 | 0x7640 x293 | - | controller_addr_4091 | packet_shadow:2, controller_status:5 |
| `99d4493dc4cf` | 549 | 0x71c0 x549 | - | - | packet_shadow:10 |
| `b69f366c92b6` | 547 | 0x7b00 x293, 0x7b80 x254 | - | controller_addr_4091 | packet_shadow:3, controller_status:3 |
| `ba3aab1d5fd2` | 334 | 0x9b00 x136, 0x9b40 x129, 0x9b80 x62, 0x9bc0 x7 | - | controller_addr_4091 | controller_status:6 |
| `fe343ef73975` | 281 | 0x7e40 x116, 0x7ec0 x89, 0x7e80 x68, 0x7e00 x8 | - | controller_addr_4091 | packet_shadow:4, controller_status:2 |
| `8b2115cd509f` | 27 | 0x7140 x13, 0x7100 x9, 0x7180 x5 | - | controller_addr_4091 | front_panel_or_status:1, controller_status:4, packet_shadow:1 |
| `0c705773105c` | 549 | 0x6080 x145, 0x60c0 x139, 0x6040 x134, 0x6000 x131 | - | - | packet_shadow:4, controller_status:2, front_panel_or_status:3 |
| `8f8e0add044c` | 549 | 0x70c0 x262, 0x7080 x153, 0x7000 x134 | - | - | packet_shadow:6, controller_status:3 |
| `144315176c64` | 549 | 0x9480 x310, 0x94c0 x215, 0x9400 x24 | - | - | packet_shadow:6, front_panel_or_status:3 |
| `25333cae3674` | 548 | 0x7780 x293, 0x77c0 x255 | - | controller_addr_4095 | packet_shadow:3, controller_status:2 |
| `204291444868` | 432 | 0x7800 x395, 0x78c0 x37 | - | controller_kick_409c | controller_status:4, packet_shadow:1 |
| `7106a72e56d9` | 432 | 0x8580 x219, 0x8540 x167, 0x85c0 x46 | - | - | front_panel_or_status:2, packet_shadow:3, profile_string_area:4 |
| `add3eb18b8cc` | 317 | 0x8240 x317 | - | - | front_panel_or_status:6, packet_shadow:3 |
| `04a2d67cbfff` | 308 | 0x7dc0 x308 | - | - | controller_status:7, packet_shadow:2 |
| `6c4f90652e56` | 549 | 0x61c0 x170, 0x6180 x169, 0x6100 x125, 0x6140 x85 | - | - | packet_shadow:3, front_panel_or_status:4, controller_status:1 |
| `b7a129b7d392` | 549 | 0x7200 x293, 0x72c0 x256 | - | - | packet_shadow:8 |
| `85545872cc2b` | 549 | 0x8440 x549 | - | - | packet_shadow:8 |
| `7fabb1c7616c` | 549 | 0x9f40 x256, 0x9f80 x217, 0x9f00 x50, 0x9fc0 x26 | - | - | front_panel_or_status:5, packet_shadow:2, controller_status:1 |
| `24ebe8bb67f5` | 548 | 0x7980 x293, 0x79c0 x255 | - | controller_kick_409c | controller_status:3, packet_shadow:1 |
| `9e474876a043` | 547 | 0x7c40 x293, 0x7c00 x254 | - | controller_addr_4095 | packet_shadow:3, controller_status:1 |
| `0f031dd8ed37` | 545 | 0x6300 x431, 0x6380 x114 | - | - | front_panel_or_status:3, packet_shadow:5 |
| `2598f9591a20` | 526 | 0x6240 x256, 0x62c0 x139, 0x6280 x131 | - | - | packet_shadow:6, front_panel_or_status:2 |
| `03044422ea30` | 276 | 0x9e40 x84, 0x9ec0 x80, 0x9e00 x77, 0x9e80 x35 | - | - | front_panel_or_status:3, packet_shadow:5 |
| `ee30d1b5daca` | 152 | 0x6ec0 x152 | - | - | packet_shadow:5, controller_status:3 |
| `5a65b8a71db9` | 100 | 0x9180 x100 | - | - | controller_status:4, packet_shadow:4 |
| `5a0c5fbcd38c` | 88 | 0x85c0 x88 | - | controller_addr_4091 | controller_status:4 |
| `0e790c42bd72` | 4 | 0x8700 x2, 0x8740 x1, 0x87c0 x1 | - | - | packet_shadow:6, profile_string_area:2 |
| `5a92e83e04a8` | 2 | 0x8580 x2 | - | - | front_panel_or_status:5, packet_shadow:3 |
| `fe95f1ed098a` | 549 | 0x63c0 x293, 0x6380 x256 | - | - | packet_shadow:6, front_panel_or_status:1 |
| `cfe0a1406283` | 549 | 0x6e80 x293, 0x6ec0 x256 | - | - | packet_shadow:7 |
| `4cfa6d151318` | 549 | 0x7300 x293, 0x7340 x256 | - | - | packet_shadow:6, front_panel_or_status:1 |
| `037cda80b040` | 549 | 0x8280 x293, 0x82c0 x256 | - | - | packet_shadow:7 |
| `ad2faf50bc31` | 549 | 0x83c0 x549 | - | - | packet_shadow:7 |
| `306eb529b363` | 549 | 0x9880 x471, 0x9840 x43, 0x9800 x19, 0x98c0 x16 | - | - | packet_shadow:7 |
| `71a589c84051` | 549 | 0x9980 x293, 0x9940 x256 | - | - | packet_shadow:7 |
| `80b60d722518` | 475 | 0x6680 x256, 0x6640 x166, 0x66c0 x53 | - | - | front_panel_or_status:4, packet_shadow:3 |
| `4f29221f2e51` | 399 | 0x6cc0 x167, 0x6c40 x125, 0x6c80 x85, 0x6c00 x22 | - | - | packet_shadow:7 |
| `c684e9945319` | 133 | 0x7580 x81, 0x75c0 x52 | - | - | packet_shadow:5, controller_status:2 |
| `99277d40b327` | 114 | 0x6d80 x114 | - | - | packet_shadow:7 |
| `86709485b961` | 40 | 0x69c0 x40 | - | - | packet_shadow:7 |
| `878984a494b8` | 33 | 0x6b80 x13, 0x6b00 x10, 0x6bc0 x7, 0x6b40 x3 | - | - | packet_shadow:6, front_panel_or_status:1 |
| `dbf01786a7ed` | 3 | 0x6b00 x1, 0x6b80 x1, 0x6b40 x1 | - | - | packet_shadow:7 |
| `8853b78ca23e` | 549 | 0x6ac0 x269, 0x6a80 x165, 0x6a40 x59, 0x6a00 x56 | - | - | controller_status:5, packet_shadow:1 |
| `25956f88a30e` | 549 | 0x6c80 x243, 0x6c00 x188, 0x6cc0 x78, 0x6c40 x40 | - | - | packet_shadow:6 |
| `404045e0e63c` | 549 | 0x7fc0 x186, 0x7f80 x160, 0x7f40 x158, 0x7f00 x45 | - | - | front_panel_or_status:2, packet_shadow:4 |
| `17a7e3a30d12` | 549 | 0x8500 x549 | - | - | packet_shadow:5, controller_status:1 |
| `23c16a978aa0` | 549 | 0x8840 x293, 0x8880 x256 | - | - | packet_shadow:5, front_panel_or_status:1 |
| `fbb6be935285` | 549 | 0x94c0 x266, 0x9440 x195, 0x9480 x84, 0x9400 x4 | - | - | front_panel_or_status:6 |
| `0b045c0906d5` | 549 | 0x9900 x419, 0x9940 x120, 0x99c0 x10 | - | - | packet_shadow:6 |
| `183ec6fd07c7` | 549 | 0x9ac0 x170, 0x9a80 x137, 0x9a40 x123, 0x9a00 x119 | - | - | packet_shadow:6 |
| `c2560553eb14` | 549 | 0x9c80 x206, 0x9c00 x164, 0x9c40 x163, 0x9cc0 x16 | - | - | packet_shadow:6 |

These are the best current offline targets for reverse engineering normal runtime plumbing. Chunks with `controller_status` references tend to touch the `0x4000..0x409c` controller gateway; chunks with `front_panel_or_status` references are candidates for the LED/button/mechanism fabric, but should be treated carefully because reads of `0x47xx` and related paths have wedged the drive before.

## Practical Read

- The normal work-window is still a promising source of hidden runtime code, probably including decoded-controller or overlay material.
- The work-window is not a clean linear decoded CDD image. The same chunk can occupy multiple public slots, so public offset alone is not enough to map a chunk to a CDD record.
- The stable public response bridge remains the best host-visible patch target once we have a normal-mode write primitive.
- For static CDD work, these chunks are useful known-output candidates only after we learn the missing address/phase relationship between rotating work-window tiles and the controller's decoded address space.
