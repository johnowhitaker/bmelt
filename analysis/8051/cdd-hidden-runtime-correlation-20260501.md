# CDD / Hidden Runtime Correlation

Offline only. No drive commands were sent.

This treats stable normal hidden-runtime chunks as possible known-output candidates for CDD hard-mode records. It is intentionally conservative: rotating chunks are listed separately because their public offset is not a trustworthy decoded address.

## Summary

- captures scanned: `509`
- stable hidden candidates: `98`
- rotating hidden examples retained: `40`

## Stable Hidden Candidates

| chunk | obs | offset | stability | CDD rec | mode | op key | source len | raw 4B hits | raw 8B hits | best xor4 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `3a50ba32dcc7` | 509 | `0x6200` | 1.0 | `50` | `0x80` | `6092d29f2405` | `0x9c3` | 0 | 0 | 0x00:0 |
| `3ebc7de3a789` | 509 | `0x6340` | 1.0 | `51` | `0x80` | `a98252b3a002` | `0x916` | 0 | 0 | 0x00:0 |
| `5440ade962f4` | 509 | `0x6e00` | 1.0 | `56` | `0x80` | `aba191967205` | `0x8f2` | 0 | 0 | 0x00:0 |
| `99d4493dc4cf` | 509 | `0x71c0` | 1.0 | `59` | `0x80` | `30ca94930e05` | `0x99e` | 0 | 0 | 0x00:0 |
| `4204b670e74f` | 509 | `0x7680` | 1.0 | `62` | `0x80` | `9fd2119d4c04` | `0x973` | 0 | 0 | 0x00:0 |
| `7f81167f4ffb` | 509 | `0x7b40` | 1.0 | `64` | `0x40` | `93390e6b7c02` | `0x644` | 0 | 0 | 0x00:0 |
| `7a8cbb7773e7` | 509 | `0x7bc0` | 1.0 | `65` | `0x80` | `3f690aa24004` | `0x734` | 0 | 0 | 0x00:0 |
| `e5039685def3` | 509 | `0x7c80` | 1.0 | `65` | `0x80` | `3f690aa24004` | `0x734` | 0 | 0 | 0x00:0 |
| `ff754e0abf59` | 509 | `0x7f00` | 0.9823 | `66` | `0x80` | `4e8210adb204` | `0x96b` | 0 | 0 | 0x00:0 |
| `424cec152d74` | 509 | `0x8180` | 1.0 | `67` | `0x40` | `b0f2d169c404` | `0x8f7` | 0 | 0 | 0x00:0 |
| `434cccd4312b` | 509 | `0x8340` | 1.0 | `68` | `0x80` | `0fe212a8d404` | `0x975` | 0 | 0 | 0x00:0 |
| `ad2faf50bc31` | 509 | `0x83c0` | 1.0 | `68` | `0x80` | `0fe212a8d404` | `0x975` | 0 | 0 | 0x00:0 |
| `85545872cc2b` | 509 | `0x8440` | 1.0 | `68` | `0x80` | `0fe212a8d404` | `0x975` | 0 | 0 | 0x6f:1 |
| `17a7e3a30d12` | 509 | `0x8500` | 1.0 | `68` | `0x80` | `0fe212a8d404` | `0x975` | 0 | 0 | 0x00:0 |
| `e95d665104e3` | 509 | `0x88c0` | 1.0 | `70` | `0x80` | `098ad4a36805` | `0x9dd` | 0 | 0 | 0x00:0 |
| `50a077ef46c0` | 509 | `0x8940` | 1.0 | `71` | `0xc0` | `331254c59e05` | `0xa99` | 0 | 0 | 0x00:0 |
| `a49e0d0f6ea3` | 509 | `0x8e80` | 1.0 | `74` | `0x80` | `ccc295b29405` | `0xb18` | 0 | 0 | 0x00:0 |
| `2b41f440f0be` | 509 | `0x8f00` | 1.0 | `75` | `0x00` | `01a353031a00` | `0x58f` | 0 | 0 | 0x00:0 |
| `f2e5273adc82` | 509 | `0x9600` | 1.0 | `85` | `0x40` | `5f925170d804` | `0x8be` | 0 | 0 | 0x00:0 |
| `f0e964b101a5` | 509 | `0x9700` | 1.0 | `85` | `0x40` | `5f925170d804` | `0x8be` | 0 | 0 | 0x00:0 |
| `c94244a64f8e` | 509 | `0x9d40` | 1.0 | `87` | `0x40` | `0af2177f2e01` | `0x79b` | 0 | 0 | 0x00:0 |
| `562cd56163da` | 509 | `0x9d80` | 1.0 | `88` | `0x40` | `37424f6bc203` | `0x7ad` | 0 | 0 | 0x00:0 |
| `28583441dfa8` | 508 | `0x7380` | 1.0 | `60` | `0x40` | `950a90757805` | `0x928` | 0 | 0 | 0x7b:1 |
| `83125549fc8a` | 508 | `0x7a80` | 1.0 | `64` | `0x40` | `93390e6b7c02` | `0x644` | 0 | 0 | 0x00:0 |
| `9b673c066ae4` | 506 | `0x74c0` | 0.9921 | `60` | `0x40` | `950a90757805` | `0x928` | 0 | 0 | 0x00:0 |
| `f9a9de295b57` | 446 | `0x8080` | 1.0 | `67` | `0x40` | `b0f2d169c404` | `0x8f7` | 0 | 0 | 0x00:0 |
| `1a8df790ad50` | 437 | `0x68c0` | 1.0 | `54` | `0x80` | `268ace91e605` | `0x931` | 0 | 0 | 0x00:0 |
| `c8c5359c53cb` | 361 | `0x6700` | 1.0 | `53` | `0x80` | `eee94e93cc04` | `0x87e` | 0 | 0 | 0x00:0 |
| `4b871b3b7ee4` | 327 | `0x6780` | 1.0 | `53` | `0x80` | `eee94e93cc04` | `0x87e` | 0 | 0 | 0x00:0 |
| `add3eb18b8cc` | 277 | `0x8240` | 1.0 | `67` | `0x40` | `b0f2d169c404` | `0x8f7` | 0 | 0 | 0x00:0 |
| `04a2d67cbfff` | 268 | `0x7dc0` | 1.0 | `66` | `0x80` | `4e8210adb204` | `0x96b` | 0 | 0 | 0x00:0 |
| `720a73f330f1` | 256 | `0x0000` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `4df9cdaefef5` | 256 | `0x0040` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `6be734872748` | 256 | `0x0080` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `483557107b6c` | 256 | `0x00c0` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `ba1c5d1a3160` | 256 | `0x0100` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `15ef73bfc65b` | 256 | `0x0140` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `84ef62c7f656` | 256 | `0x0200` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `991f5f05babf` | 256 | `0x02c0` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |
| `6d5551d353b7` | 256 | `0x0300` | 1.0 | `0` | `0x80` | `ef7a96b5bc05` | `0xb72` | 0 | 0 | 0x00:0 |

The seed-hit columns are a cheap sanity check for trivial transforms. A strong decoded-output pair would often leave exact or fixed-XOR byte seeds in the source. The current candidates do not show that kind of simple relationship.

## Rotating Hidden Examples

| chunk | obs | stability | offsets | patterns | categories |
| --- | --- | --- | --- | --- | --- |
| `19cf1f0ab9c1` | 509 | 0.2849 | 0x6040 x145, 0x6080 x124, 0x6000 x120, 0x60c0 x120 | - | packet_shadow |
| `0c705773105c` | 509 | 0.277 | 0x6080 x141, 0x60c0 x127, 0x6040 x127, 0x6000 x114 | - | packet_shadow, controller_status, front_panel_or_status |
| `0c7ad71c6007` | 509 | 0.5128 | 0x6100 x261, 0x6140 x188, 0x6180 x60 | - | packet_shadow |
| `8bf0e900d2ce` | 509 | 0.3949 | 0x61c0 x201, 0x6180 x163, 0x6140 x86, 0x6100 x59 | - | packet_shadow |
| `6c4f90652e56` | 509 | 0.332 | 0x6180 x169, 0x61c0 x153, 0x6100 x109, 0x6140 x78 | - | packet_shadow, front_panel_or_status, controller_status |
| `c460b2840920` | 509 | 0.5029 | 0x6280 x256, 0x62c0 x253 | - | packet_shadow |
| `fe95f1ed098a` | 509 | 0.5029 | 0x6380 x256, 0x63c0 x253 | - | packet_shadow, front_panel_or_status |
| `22700a264cc6` | 509 | 0.5029 | 0x64c0 x256, 0x6400 x253 | - | packet_shadow |
| `2eed30eee3d0` | 509 | 0.4872 | 0x64c0 x248, 0x6480 x234, 0x6440 x27 | - | packet_shadow |
| `2220a28bb58c` | 509 | 0.5029 | 0x6580 x256, 0x6540 x253 | - | packet_shadow |
| `53a8cf6985d9` | 509 | 0.5029 | 0x67c0 x256, 0x6740 x253 | - | front_panel_or_status, packet_shadow |
| `8e062e65d4f9` | 509 | 0.5029 | 0x6800 x256, 0x6840 x253 | - | packet_shadow |
| `1c9126d7efa7` | 509 | 0.5029 | 0x6900 x256, 0x6940 x253 | - | - |
| `8853b78ca23e` | 509 | 0.5285 | 0x6ac0 x269, 0x6a80 x165, 0x6a00 x56, 0x6a40 x19 | - | controller_status, packet_shadow |
| `2958d3bbf5db` | 509 | 0.5403 | 0x6a40 x275, 0x6a00 x140, 0x6ac0 x70, 0x6a80 x24 | - | front_panel_or_status |
| `d71c07c7fcd6` | 509 | 0.4185 | 0x6bc0 x213, 0x6b80 x130, 0x6b00 x101, 0x6b40 x65 | - | front_panel_or_status, packet_shadow |
| `4f7ce11fed12` | 509 | 0.446 | 0x6b00 x227, 0x6b40 x125, 0x6b80 x95, 0x6bc0 x62 | - | - |
| `a87d03db223d` | 509 | 0.5305 | 0x6b40 x270, 0x6bc0 x164, 0x6b00 x53, 0x6b80 x22 | - | front_panel_or_status, packet_shadow |
| `25956f88a30e` | 509 | 0.4774 | 0x6c80 x243, 0x6c00 x188, 0x6c40 x40, 0x6cc0 x38 | - | packet_shadow |
| `a5db36cf56db` | 509 | 0.5029 | 0x6dc0 x256, 0x6d40 x253 | - | packet_shadow |

## Interpretation

- Several hidden normal-runtime chunks are stable enough to be good code study targets, but their CDD mapping remains only a hypothesis.
- The stable candidates mostly land on mode `0x40`/`0x80` records with high-entropy sources, exactly the hard CDD classes already suspected.
- The raw/fixed-XOR seed checks are negative, so these are not cheap direct unpacking pairs.
- Rotating hidden chunks such as the public response bridge are real runtime code, but their public slot movement makes them poor direct CDD known-output pairs until we learn the missing phase/address model.
