# Normal Hidden Runtime Chunk Analysis

Date: 2026-05-01

This is an offline analysis of the normal-mode `READ BUFFER id=01/02 offset=0x070000` work-window captures. It treats the window as a rotating `0x40`-byte tile surface, not as one stable linear image.

## Summary

- captures scanned: `509`
- unique chunks: `888`
- chunks with exact visible/currentboot reference match: `501`
- chunks without exact visible/currentboot reference match: `387`
- interesting hidden chunks: `28` shown

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
| `public_bridge_8a4c_to_4011` | `20ea2ab16891` | 509 | 0x7140 x251, 0x7100 x136, 0x7180 x122 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `public_bridge_8a4d_to_4012` | `20ea2ab16891` | 509 | 0x7140 x251, 0x7100 x136, 0x7180 x122 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `public_bridge_8a4e_to_4013` | `20ea2ab16891` | 509 | 0x7140 x251, 0x7100 x136, 0x7180 x122 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `getcfg_4099_to_shadow` | `8d8c3b0a22a0` | 39 | 0x7140 x21, 0x7100 x12, 0x7180 x6 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `getcfg_fe_sentinel_branch` | `8d8c3b0a22a0` | 39 | 0x7140 x21, 0x7100 x12, 0x7180 x6 | - | 0x7140 -> rec 58 (0x80); 0x7100 -> rec 58 (0x80); 0x7180 -> rec 59 (0x80) |
| `controller_addr_4091` | `4037c8574920` | 39 | 0x70c0 x17, 0x7000 x15, 0x7080 x7 | - | 0x70c0 -> rec 58 (0x80); 0x7000 -> rec 58 (0x80); 0x7080 -> rec 58 (0x80) |
| `controller_kick_409c` | `4037c8574920` | 39 | 0x70c0 x17, 0x7000 x15, 0x7080 x7 | - | 0x70c0 -> rec 58 (0x80); 0x7000 -> rec 58 (0x80); 0x7080 -> rec 58 (0x80) |
| `controller_addr_4095` | `28583441dfa8` | 508 | 0x7380 x508 | - | 0x7380 -> rec 60 (0x40) |

The repeated CDD candidate changes for the same chunk are the important sanity check. For example, the public bridge chunk appears at several public offsets, which would place it in different CDD records if we naively trusted the slot number. That argues against using normal public offsets as direct decoded CDD addresses without an additional address/phase model.

## Phase Sanity Check

I also tested the tempting idea that the whole 64 KiB work-window is just globally shifted by the public bridge chunk. It is not. The bridge appears once in every capture and its local phase is real, but using it as a global scroll offset makes the window *less* stable overall.

| view | captures | stable 100% | stable >=95% | stable >=90% | positions |
| --- | --- | --- | --- | --- | --- |
| `raw public offsets` | 509 | 741 | 746 | 746 | 1024 |
| `bridge-aligned` | 509 | 244 | 244 | 244 | 1024 |

Bridge phases:

| phase vs +0x7140 | captures |
| --- | --- |
| `+0x0` | 251 |
| `-0x40` | 136 |
| `+0x40` | 122 |

So the public bridge gives a local anchor for one response-builder island, not a universal address correction for the whole work-window.

## Top Hidden Runtime Chunks

| chunk | obs | top public offsets | exact refs | patterns | interesting refs |
| --- | --- | --- | --- | --- | --- |
| `20ea2ab16891` | 509 | 0x7140 x251, 0x7100 x136, 0x7180 x122 | - | public_bridge_8a4c_to_4011, public_bridge_8a4d_to_4012, public_bridge_8a4e_to_4013 | packet_shadow:5, controller_status:4 |
| `8d8c3b0a22a0` | 39 | 0x7140 x21, 0x7100 x12, 0x7180 x6 | - | getcfg_4099_to_shadow, getcfg_fe_sentinel_branch | controller_status:3, packet_shadow:5 |
| `2111cafaf69c` | 509 | 0x9540 x143, 0x9500 x130, 0x9580 x125, 0x95c0 x111 | - | - | packet_shadow:8, front_panel_or_status:7 |
| `4037c8574920` | 39 | 0x70c0 x17, 0x7000 x15, 0x7080 x7 | - | controller_addr_4091, controller_kick_409c | controller_status:6, packet_shadow:1 |
| `c5c0741f5daa` | 509 | 0x84c0 x256, 0x8480 x253 | - | - | profile_string_area:4, packet_shadow:7, front_panel_or_status:2 |
| `28583441dfa8` | 508 | 0x7380 x508 | - | controller_addr_4095, controller_kick_409c | controller_status:4, packet_shadow:1 |
| `0c9a360d26b8` | 508 | 0x76c0 x255, 0x7600 x253 | - | controller_addr_4091, controller_kick_409c | controller_status:4, packet_shadow:1 |
| `9b673c066ae4` | 506 | 0x74c0 x502, 0x7480 x4 | - | controller_kick_409c | controller_status:5, packet_shadow:4 |
| `580b9228d0b9` | 256 | 0x7640 x256 | - | controller_addr_4095, controller_kick_409c | controller_status:5 |
| `fb00deab088b` | 509 | 0x8780 x217, 0x8740 x118, 0x87c0 x93, 0x8700 x81 | - | controller_addr_4091 | controller_status:8 |
| `95caa55b881e` | 473 | 0x6b80 x248, 0x6b00 x117, 0x6bc0 x63, 0x6b40 x45 | - | - | packet_shadow:7, front_panel_or_status:5 |
| `efcb6299a750` | 264 | 0x7f80 x185, 0x7fc0 x60, 0x7f40 x19 | - | controller_kick_409c | controller_status:5, packet_shadow:3 |
| `70e7ea0193bb` | 509 | 0x8800 x256, 0x8880 x253 | - | - | packet_shadow:7, profile_string_area:2, front_panel_or_status:2 |
| `3465e4783c3d` | 253 | 0x7640 x253 | - | controller_addr_4091 | packet_shadow:2, controller_status:5 |
| `99d4493dc4cf` | 509 | 0x71c0 x509 | - | - | packet_shadow:10 |
| `b69f366c92b6` | 507 | 0x7b80 x254, 0x7b00 x253 | - | controller_addr_4091 | packet_shadow:3, controller_status:3 |
| `ba3aab1d5fd2` | 334 | 0x9b00 x136, 0x9b40 x129, 0x9b80 x62, 0x9bc0 x7 | - | controller_addr_4091 | controller_status:6 |
| `fe343ef73975` | 281 | 0x7e40 x116, 0x7ec0 x89, 0x7e80 x68, 0x7e00 x8 | - | controller_addr_4091 | packet_shadow:4, controller_status:2 |
| `8b2115cd509f` | 27 | 0x7140 x13, 0x7100 x9, 0x7180 x5 | - | controller_addr_4091 | front_panel_or_status:1, controller_status:4, packet_shadow:1 |
| `0c705773105c` | 509 | 0x6080 x141, 0x60c0 x127, 0x6040 x127, 0x6000 x114 | - | - | packet_shadow:4, controller_status:2, front_panel_or_status:3 |
| `8f8e0add044c` | 509 | 0x70c0 x222, 0x7080 x153, 0x7000 x134 | - | - | packet_shadow:6, controller_status:3 |
| `144315176c64` | 509 | 0x9480 x270, 0x94c0 x215, 0x9400 x24 | - | - | packet_shadow:6, front_panel_or_status:3 |
| `25333cae3674` | 508 | 0x77c0 x255, 0x7780 x253 | - | controller_addr_4095 | packet_shadow:3, controller_status:2 |
| `204291444868` | 432 | 0x7800 x395, 0x78c0 x37 | - | controller_kick_409c | controller_status:4, packet_shadow:1 |
| `7106a72e56d9` | 392 | 0x8580 x179, 0x8540 x167, 0x85c0 x46 | - | - | front_panel_or_status:2, packet_shadow:3, profile_string_area:4 |
| `add3eb18b8cc` | 277 | 0x8240 x277 | - | - | front_panel_or_status:6, packet_shadow:3 |
| `04a2d67cbfff` | 268 | 0x7dc0 x268 | - | - | controller_status:7, packet_shadow:2 |
| `6c4f90652e56` | 509 | 0x6180 x169, 0x61c0 x153, 0x6100 x109, 0x6140 x78 | - | - | packet_shadow:3, front_panel_or_status:4, controller_status:1 |

These are the best current offline targets for reverse engineering normal runtime plumbing. Chunks with `controller_status` references tend to touch the `0x4000..0x409c` controller gateway; chunks with `front_panel_or_status` references are candidates for the LED/button/mechanism fabric, but should be treated carefully because reads of `0x47xx` and related paths have wedged the drive before.

## Practical Read

- The normal work-window is still a promising source of hidden runtime code, probably including decoded-controller or overlay material.
- The work-window is not a clean linear decoded CDD image. The same chunk can occupy multiple public slots, so public offset alone is not enough to map a chunk to a CDD record.
- The stable public response bridge remains the best host-visible patch target once we have a normal-mode write primitive.
- For static CDD work, these chunks are useful known-output candidates only after we learn the missing address/phase relationship between rotating work-window tiles and the controller's decoded address space.
