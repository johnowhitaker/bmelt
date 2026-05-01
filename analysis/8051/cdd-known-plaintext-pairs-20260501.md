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

- pair count: `72`
- records with pairs: `20`
- max direct longest common substring: `2` bytes
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
| 66 | `0x80` | `4e8210adb204` | 2411 | 720 | 512 (71%) | `fe343ef73975` x281, `04a2d67cbfff` x268, `efcb6299a750` x264 |
| 70 | `0x80` | `098ad4a36805` | 2525 | 560 | 384 (69%) | `fb00deab088b` x509, `70e7ea0193bb` x509 |
| 58 | `0x80` | `66228ca20005` | 2292 | 544 | 304 (56%) | `8f8e0add044c` x509, `20ea2ab16891` x387, `4037c8574920` x39, `8d8c3b0a22a0` x33 |
| 49 | `0x80` | `428a889c5804` | 2033 | 448 | 256 (57%) | `0c705773105c` x509 |
| 50 | `0x80` | `6092d29f2405` | 2499 | 496 | 256 (52%) | `6c4f90652e56` x509 |
| 55 | `0x40` | `a742d3782e04` | 2313 | 896 | 256 (29%) | `95caa55b881e` x473 |
| 87 | `0x40` | `0af2177f2e01` | 1947 | 1008 | 256 (25%) | `ba3aab1d5fd2` x334 |
| 62 | `0x80` | `9fd2119d4c04` | 2419 | 464 | 224 (48%) | `25333cae3674` x508, `580b9228d0b9` x256, `0c9a360d26b8` x255, `3465e4783c3d` x253 |
| 68 | `0x80` | `0fe212a8d404` | 2421 | 640 | 208 (32%) | `c5c0741f5daa` x509, `7106a72e56d9` x346 |
| 60 | `0x40` | `950a90757805` | 2344 | 848 | 192 (23%) | `28583441dfa8` x508, `9b673c066ae4` x506 |
| 59 | `0x80` | `30ca94930e05` | 2462 | 304 | 128 (42%) | `99d4493dc4cf` x509, `20ea2ab16891` x122, `8d8c3b0a22a0` x6, `8b2115cd509f` x5 |
| 84 | `0x80` | `3b0a538aa203` | 2198 | 160 | 128 (80%) | `2111cafaf69c` x273 |
| 85 | `0x40` | `5f925170d804` | 2238 | 768 | 128 (17%) | `2111cafaf69c` x236 |
| 63 | `0x80` | `c89256901a00` | 2024 | 256 | 96 (38%) | `204291444868` x432 |
| 83 | `0x80` | `0caa1588de03` | 2256 | 128 | 96 (75%) | `144315176c64` x485 |
| 64 | `0x40` | `93390e6b7c02` | 1604 | 688 | 80 (12%) | `b69f366c92b6` x507 |
| 67 | `0x40` | `b0f2d169c404` | 2295 | 656 | 64 (10%) | `add3eb18b8cc` x277 |
| 69 | `0x80` | `2cf2cf97b204` | 2274 | 368 | 64 (17%) | `7106a72e56d9` x46 |
| 81 | `0x80` | `64cace949404` | 2266 | 320 | 48 (15%) | `144315176c64` x24 |
| 61 | `0x80` | `80e25282fa04` | 2402 | 32 | 16 (50%) | `0c9a360d26b8` x253 |

## Highest-Signal Pairs

| chunk | record | public offset | rel | mode | op key | source/decoded | decoded prefix |
|---|---:|---:|---:|---:|---|---:|---|
| `ba3aab1d5fd2` | 87 | `0x9b00` | `0x1a0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `ba3aab1d5fd2` | 87 | `0x9b40` | `0x1e0` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `ba3aab1d5fd2` | 87 | `0x9b80` | `0x220` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `ba3aab1d5fd2` | 87 | `0x9bc0` | `0x260` | `0x40` | `0af2177f2e01` | 1947/1008 (1.93x) | `a9e6a3f008e6a3f0d251e57c2406f57c...` |
| `95caa55b881e` | 55 | `0x6b00` | `0x1c0` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `95caa55b881e` | 55 | `0x6b40` | `0x200` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `95caa55b881e` | 55 | `0x6b80` | `0x240` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `95caa55b881e` | 55 | `0x6bc0` | `0x280` | `0x40` | `a742d3782e04` | 2313/896 (2.58x) | `007e02120b079085efe09048f4f09085...` |
| `28583441dfa8` | 60 | `0x7380` | `0xe0` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `feef78aa26ffee1836a87c0808f608ef...` |
| `9b673c066ae4` | 60 | `0x7480` | `0x1e0` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `8a4de0904099f0908a4ee0904099f090...` |
| `9b673c066ae4` | 60 | `0x74c0` | `0x220` | `0x40` | `950a90757805` | 2344/848 (2.76x) | `8a4de0904099f0908a4ee0904099f090...` |
| `2111cafaf69c` | 85 | `0x9580` | `0x0` | `0x40` | `5f925170d804` | 2238/768 (2.91x) | `47b1e0908a4cf09047b1e0908a4df090...` |
| `2111cafaf69c` | 85 | `0x95c0` | `0x40` | `0x40` | `5f925170d804` | 2238/768 (2.91x) | `47b1e0908a4cf09047b1e0908a4df090...` |
| `04a2d67cbfff` | 66 | `0x7dc0` | `0x10` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `b7904097f0904000e020e7f99040b6e4...` |
| `fe343ef73975` | 66 | `0x7e00` | `0x50` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `f618ee36f6908a4ae0640260030273de...` |
| `fe343ef73975` | 66 | `0x7e40` | `0x90` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `f618ee36f6908a4ae0640260030273de...` |
| `fe343ef73975` | 66 | `0x7e80` | `0xd0` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `f618ee36f6908a4ae0640260030273de...` |
| `fe343ef73975` | 66 | `0x7ec0` | `0x110` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `f618ee36f6908a4ae0640260030273de...` |
| `efcb6299a750` | 66 | `0x7f40` | `0x190` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `097a00900001122fb7904093f090409c...` |
| `efcb6299a750` | 66 | `0x7f80` | `0x1d0` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `097a00900001122fb7904093f090409c...` |
| `efcb6299a750` | 66 | `0x7fc0` | `0x210` | `0x80` | `4e8210adb204` | 2411/720 (3.35x) | `097a00900001122fb7904093f090409c...` |
| `b69f366c92b6` | 64 | `0x7b00` | `0x220` | `0x40` | `93390e6b7c02` | 1604/688 (2.33x) | `fe08e6ff90891fe02fff90891ee03ea8...` |
| `b69f366c92b6` | 64 | `0x7b80` | `0x2a0` | `0x40` | `93390e6b7c02` | 1604/688 (2.33x) | `fe08e6ff90891fe02fff90891ee03ea8...` |
| `add3eb18b8cc` | 67 | `0x8240` | `0x1c0` | `0x40` | `b0f2d169c404` | 2295/656 (3.50x) | `e436f69047d7e054fef0908a4fe09047...` |
| `c5c0741f5daa` | 68 | `0x8480` | `0x170` | `0x80` | `0fe212a8d404` | 2421/640 (3.78x) | `862cf090596ae090862df0905906e090...` |
| `c5c0741f5daa` | 68 | `0x84c0` | `0x1b0` | `0x80` | `0fe212a8d404` | 2421/640 (3.78x) | `862cf090596ae090862df0905906e090...` |
| `7106a72e56d9` | 68 | `0x8540` | `0x230` | `0x80` | `0fe212a8d404` | 2421/640 (3.78x) | `30e054df904863f0908631e054fd9048...` |
| `7106a72e56d9` | 68 | `0x8580` | `0x270` | `0x80` | `0fe212a8d404` | 2421/640 (3.78x) | `30e054df904863f0908631e054fd9048...` |
| `fb00deab088b` | 70 | `0x8700` | `0x0` | `0x80` | `098ad4a36805` | 2525/560 (4.51x) | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `fb00deab088b` | 70 | `0x8740` | `0x40` | `0x80` | `098ad4a36805` | 2525/560 (4.51x) | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `fb00deab088b` | 70 | `0x8780` | `0x80` | `0x80` | `098ad4a36805` | 2525/560 (4.51x) | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `fb00deab088b` | 70 | `0x87c0` | `0xc0` | `0x80` | `098ad4a36805` | 2525/560 (4.51x) | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `70e7ea0193bb` | 70 | `0x8800` | `0x100` | `0x80` | `098ad4a36805` | 2525/560 (4.51x) | `908633e0905906f090862fe090590df0...` |
| `70e7ea0193bb` | 70 | `0x8880` | `0x180` | `0x80` | `098ad4a36805` | 2525/560 (4.51x) | `908633e0905906f090862fe090590df0...` |
| `4037c8574920` | 58 | `0x7000` | `0xb0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `08eff6904000e020e7f9908ac6e09040...` |
| `8f8e0add044c` | 58 | `0x7000` | `0xb0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `3407fee43dfde43cfc9085fd12343090...` |
| `4037c8574920` | 58 | `0x7080` | `0x130` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `08eff6904000e020e7f9908ac6e09040...` |
| `8f8e0add044c` | 58 | `0x7080` | `0x130` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `3407fee43dfde43cfc9085fd12343090...` |
| `4037c8574920` | 58 | `0x70c0` | `0x170` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `08eff6904000e020e7f9908ac6e09040...` |
| `8f8e0add044c` | 58 | `0x70c0` | `0x170` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `3407fee43dfde43cfc9085fd12343090...` |
| `20ea2ab16891` | 58 | `0x7100` | `0x1b0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `8b2115cd509f` | 58 | `0x7100` | `0x1b0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `36f6904762e030e409e054eff0a87c08...` |
| `8d8c3b0a22a0` | 58 | `0x7100` | `0x1b0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `8a4df0904099e0908a4ef0904099e090...` |
| `20ea2ab16891` | 58 | `0x7140` | `0x1f0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `8b2115cd509f` | 58 | `0x7140` | `0x1f0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `36f6904762e030e409e054eff0a87c08...` |
| `8d8c3b0a22a0` | 58 | `0x7140` | `0x1f0` | `0x80` | `66228ca20005` | 2292/544 (4.21x) | `8a4df0904099e0908a4ef0904099e090...` |
| `6c4f90652e56` | 50 | `0x6100` | `0x0` | `0x80` | `6092d29f2405` | 2499/496 (5.04x) | `47c5e09089c8f09047c4e09089c9f090...` |
| `6c4f90652e56` | 50 | `0x6140` | `0x40` | `0x80` | `6092d29f2405` | 2499/496 (5.04x) | `47c5e09089c8f09047c4e09089c9f090...` |

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
