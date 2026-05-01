# CDD Known-Plaintext Pair Corpus

This report pairs encoded CDD record source spans with decoded-looking
normal-runtime 0x40-byte chunks observed through the public normal
`READ BUFFER id=01 offset=0x070000` work window.

The mapping is based on the existing CDD decoded-span model, so the pairs
are candidates rather than proof of a complete decoder. They are still
useful because chunks like the GET CONFIG response bridge are clearly
8051 code-like after decode and consistently land inside specific CDD
records.

## Summary

- pair count: `162`
- records with pairs: `29`
- max direct longest common substring: `3` bytes
- max bitwise-NOT longest common substring: `2` bytes
- max bit-reversed longest common substring: `3` bytes
- max constant-XOR n-gram: `4` bytes

The negative transform checks are useful: these known decoded chunks do
not appear literally in their encoded source spans, nor through a simple
bytewise NOT, bit reversal, or constant XOR. That pushes the CDD body
model toward a real record codeword/packing format rather than a light
obfuscation pass.

## Records With Known Decoded Chunks

| record | mode | op key | source | decoded span | slot span | chunks |
|---:|---:|---|---:|---:|---:|---|
| 87 | `0x40` | `0af2177f2e01` | 1947 | 1008 | 896 (89%) | `183ec6fd07c7` x549, `c2560553eb14` x549, `ba3aab1d5fd2` x334, `71a589c84051` x293 |
| 55 | `0x40` | `a742d3782e04` | 2313 | 896 | 768 (86%) | `8853b78ca23e` x549, `95caa55b881e` x513, `25956f88a30e` x471, `4f29221f2e51` x232 |
| 66 | `0x80` | `4e8210adb204` | 2411 | 720 | 576 (80%) | `404045e0e63c` x549, `04a2d67cbfff` x308, `fe343ef73975` x281, `efcb6299a750` x264 |
| 88 | `0x40` | `37424f6bc203` | 1965 | 688 | 512 (74%) | `7fabb1c7616c` x549, `03044422ea30` x276 |
| 60 | `0x40` | `950a90757805` | 2344 | 848 | 496 (58%) | `4cfa6d151318` x549, `28583441dfa8` x548, `9b673c066ae4` x546, `b7a129b7d392` x256 |
| 70 | `0x80` | `098ad4a36805` | 2525 | 560 | 448 (80%) | `fb00deab088b` x549, `70e7ea0193bb` x549, `23c16a978aa0` x549, `0e790c42bd72` x4 |
| 50 | `0x80` | `6092d29f2405` | 2499 | 496 | 432 (87%) | `6c4f90652e56` x549, `2598f9591a20` x526 |
| 68 | `0x80` | `0fe212a8d404` | 2421 | 640 | 400 (62%) | `c5c0741f5daa` x549, `85545872cc2b` x549, `ad2faf50bc31` x549, `17a7e3a30d12` x549 |
| 58 | `0x80` | `66228ca20005` | 2292 | 544 | 304 (56%) | `8f8e0add044c` x549, `20ea2ab16891` x387, `4037c8574920` x39, `8d8c3b0a22a0` x33 |
| 49 | `0x80` | `428a889c5804` | 2033 | 448 | 256 (57%) | `0c705773105c` x549 |
| 85 | `0x40` | `5f925170d804` | 2238 | 768 | 256 (33%) | `2111cafaf69c` x262, `306eb529b363` x62 |
| 62 | `0x80` | `9fd2119d4c04` | 2419 | 464 | 224 (48%) | `25333cae3674` x548, `3465e4783c3d` x293, `580b9228d0b9` x256, `0c9a360d26b8` x255 |
| 86 | `0x80` | `a3520f8e9004` | 2317 | 224 | 224 (100%) | `0b045c0906d5` x539, `306eb529b363` x487, `71a589c84051` x256 |
| 64 | `0x40` | `93390e6b7c02` | 1604 | 688 | 208 (30%) | `24ebe8bb67f5` x548, `b69f366c92b6` x547 |
| 51 | `0x80` | `a98252b3a002` | 2326 | 816 | 192 (24%) | `fe95f1ed098a` x549, `0f031dd8ed37` x545 |
| 52 | `0x80` | `513ad08ef203` | 2188 | 224 | 192 (86%) | `80b60d722518` x475 |
| 59 | `0x80` | `30ca94930e05` | 2462 | 304 | 192 (63%) | `99d4493dc4cf` x549, `b7a129b7d392` x293, `20ea2ab16891` x162, `8d8c3b0a22a0` x6 |
| 67 | `0x40` | `b0f2d169c404` | 2295 | 656 | 192 (29%) | `037cda80b040` x549, `add3eb18b8cc` x317 |
| 56 | `0x80` | `aba191967205` | 2290 | 352 | 128 (36%) | `4f29221f2e51` x167, `99277d40b327` x114, `25956f88a30e` x78 |
| 57 | `0x40` | `3512d253d403` | 1968 | 304 | 128 (42%) | `cfe0a1406283` x549, `ee30d1b5daca` x152 |
| 65 | `0x80` | `3f690aa24004` | 1844 | 544 | 128 (24%) | `9e474876a043` x547 |
| 84 | `0x80` | `3b0a538aa203` | 2198 | 160 | 128 (80%) | `2111cafaf69c` x287 |
| 63 | `0x80` | `c89256901a00` | 2024 | 256 | 96 (38%) | `204291444868` x432 |
| 83 | `0x80` | `0caa1588de03` | 2256 | 128 | 96 (75%) | `144315176c64` x525, `fbb6be935285` x350 |
| 69 | `0x80` | `2cf2cf97b204` | 2274 | 368 | 64 (17%) | `5a0c5fbcd38c` x88, `7106a72e56d9` x46 |
| 80 | `0x40` | `1f4acc5b4c04` | 1853 | 432 | 64 (15%) | `5a65b8a71db9` x100 |
| 81 | `0x80` | `64cace949404` | 2266 | 320 | 48 (15%) | `144315176c64` x24, `fbb6be935285` x4 |
| 82 | `0x80` | `e1514a838a04` | 1917 | 48 | 32 (67%) | `fbb6be935285` x195 |
| 61 | `0x80` | `80e25282fa04` | 2402 | 32 | 16 (50%) | `0c9a360d26b8` x293 |

## Highest-Signal Pairs

| chunk | record | public offset | rel | mode | op key | source/decoded | decoded prefix |
|---|---:|---:|---:|---:|---|---:|---|
| `71a589c84051` | 87 | `0x9980` | `0x20` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `02bf3790852ee014f0e0700302bf4790...` |
| `0b045c0906d5` | 87 | `0x99c0` | `0x60` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `9dffee9c908988f0a3eff0908a49e0b4...` |
| `183ec6fd07c7` | 87 | `0x9a00` | `0xa0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `fef0908ad9e06401705b90893de030e0...` |
| `183ec6fd07c7` | 87 | `0x9a40` | `0xe0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `fef0908ad9e06401705b90893de030e0...` |
| `183ec6fd07c7` | 87 | `0x9a80` | `0x120` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `fef0908ad9e06401705b90893de030e0...` |
| `183ec6fd07c7` | 87 | `0x9ac0` | `0x160` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `fef0908ad9e06401705b90893de030e0...` |
| `ba3aab1d5fd2` | 87 | `0x9b00` | `0x1a0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `ba3aab1d5fd2` | 87 | `0x9b40` | `0x1e0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `ba3aab1d5fd2` | 87 | `0x9b80` | `0x220` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `ba3aab1d5fd2` | 87 | `0x9bc0` | `0x260` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `c2560553eb14` | 87 | `0x9c00` | `0x2a0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `c3123d8990855ce0fd7f02123d899083...` |
| `c2560553eb14` | 87 | `0x9c40` | `0x2e0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `c3123d8990855ce0fd7f02123d899083...` |
| `c2560553eb14` | 87 | `0x9c80` | `0x320` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `c3123d8990855ce0fd7f02123d899083...` |
| `c2560553eb14` | 87 | `0x9cc0` | `0x360` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `c3123d8990855ce0fd7f02123d899083...` |
| `86709485b961` | 55 | `0x69c0` | `0x80` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `908a4de0fea3e0ff908a53eef0a3eff0...` |
| `8853b78ca23e` | 55 | `0x6a00` | `0xc0` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `98e54cf0904000e020e7f9904098e54d...` |
| `8853b78ca23e` | 55 | `0x6a40` | `0x100` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `98e54cf0904000e020e7f9904098e54d...` |
| `8853b78ca23e` | 55 | `0x6a80` | `0x140` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `98e54cf0904000e020e7f9904098e54d...` |
| `8853b78ca23e` | 55 | `0x6ac0` | `0x180` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `98e54cf0904000e020e7f9904098e54d...` |
| `878984a494b8` | 55 | `0x6b00` | `0x1c0` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `908988e0ffa3e0fd123d899047d07410...` |
| `95caa55b881e` | 55 | `0x6b00` | `0x1c0` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `dbf01786a7ed` | 55 | `0x6b00` | `0x1c0` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `0808161616803c908353e020e735802e...` |
| `878984a494b8` | 55 | `0x6b40` | `0x200` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `908988e0ffa3e0fd123d899047d07410...` |
| `95caa55b881e` | 55 | `0x6b40` | `0x200` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `dbf01786a7ed` | 55 | `0x6b40` | `0x200` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `0808161616803c908353e020e735802e...` |
| `878984a494b8` | 55 | `0x6b80` | `0x240` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `908988e0ffa3e0fd123d899047d07410...` |
| `95caa55b881e` | 55 | `0x6b80` | `0x240` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `dbf01786a7ed` | 55 | `0x6b80` | `0x240` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `0808161616803c908353e020e735802e...` |
| `878984a494b8` | 55 | `0x6bc0` | `0x280` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `908988e0ffa3e0fd123d899047d07410...` |
| `95caa55b881e` | 55 | `0x6bc0` | `0x280` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `25956f88a30e` | 55 | `0x6c00` | `0x2c0` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `8069908a4ce0240dff908a4ee02400fd...` |
| `4f29221f2e51` | 55 | `0x6c00` | `0x2c0` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `8a38e054eff0908a3ae0547ff0e04440...` |
| `25956f88a30e` | 55 | `0x6c40` | `0x300` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `8069908a4ce0240dff908a4ee02400fd...` |
| `4f29221f2e51` | 55 | `0x6c40` | `0x300` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `8a38e054eff0908a3ae0547ff0e04440...` |
| `25956f88a30e` | 55 | `0x6c80` | `0x340` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `8069908a4ce0240dff908a4ee02400fd...` |
| `4f29221f2e51` | 55 | `0x6c80` | `0x340` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `8a38e054eff0908a3ae0547ff0e04440...` |
| `b7a129b7d392` | 60 | `0x72c0` | `0x20` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `e054884efeef4ef07e007f08120a65e4...` |
| `4cfa6d151318` | 60 | `0x7300` | `0x60` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `8a23e054bff0908adfe0540f64036003...` |
| `4cfa6d151318` | 60 | `0x7340` | `0xa0` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `8a23e054bff0908adfe0540f64036003...` |
| `28583441dfa8` | 60 | `0x7380` | `0xe0` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `feef78aa26ffee1836a87c0808f608ef...` |
| `9b673c066ae4` | 60 | `0x7480` | `0x1e0` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `8a4de0904099f0908a4ee0904099f090...` |
| `9b673c066ae4` | 60 | `0x74c0` | `0x220` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `8a4de0904099f0908a4ee0904099f090...` |
| `c684e9945319` | 60 | `0x7580` | `0x2e0` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `503fa87c0808e6fe08e6ffe4fcfd908a...` |
| `c684e9945319` | 60 | `0x75c0` | `0x320` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `503fa87c0808e6fe08e6ffe4fcfd908a...` |
| `0f031dd8ed37` | 51 | `0x6300` | `0x10` | `0x80` | `a98252b3a002` | 2326/816 (2.85x) | `e4f09047b102916e908a4de0ff20e403...` |
| `0f031dd8ed37` | 51 | `0x6380` | `0x90` | `0x80` | `a98252b3a002` | 2326/816 (2.85x) | `e4f09047b102916e908a4de0ff20e403...` |
| `fe95f1ed098a` | 51 | `0x6380` | `0x90` | `0x80` | `a98252b3a002` | 2326/816 (2.85x) | `908a6ff090482de0908a70f0e4908a18...` |
| `fe95f1ed098a` | 51 | `0x63c0` | `0xd0` | `0x80` | `a98252b3a002` | 2326/816 (2.85x) | `908a6ff090482de0908a70f0e4908a18...` |

## Practical Interpretation

- Records `58..62` are currently the most valuable known-plaintext region
  because they contain the normal GET CONFIG / public response bridge
  machinery.
- The public offsets are phase-shifted work-window slots, not direct
  decoded offsets. `decoded_relative` is a record-bucket hint, not a
  proven byte-accurate placement. Multiple different chunks can appear
  at the same public slot.
- The source-to-decoded ratios vary strongly by mode and operation key.
  That variation looks like record grammar/redundancy, not a fixed-size
  stream cipher.
- If we can infer the mode `0x80` grammar from records with known code
  output, the stable response bridge becomes a possible CDD-side patch
  target rather than waiting for a separate normal-mode RAM write
  primitive.
