# Normal Tile Adjacency For CDD Known-Output Chunks

This report looks at decoded-looking normal-mode work-window tiles that
already have candidate CDD record buckets. It records which 0x40-byte
tiles sit next to each other in actual host-visible captures.

Two edge types matter:

- `slot edge`: both adjacent tiles occupy public offsets that fall inside
  the same candidate CDD decoded-span bucket in that capture.
- `shared-record edge`: both tile identities have previously been mapped
  somewhere into the same CDD record, regardless of their current public
  slot.

Neither edge type proves byte-accurate decoded CDD addresses. Repeated
edges are still useful because they expose local decoded-output
neighborhoods without another live write experiment.

## Summary

- captures scanned: `669`
- known chunks in pair corpus: `96`
- captures containing adjacent known chunks: `669`
- adjacent known-chunk observations: `11146`
- same-record slot observations: `8850`
- unique raw edges: `114`
- unique shared-record edges: `114`
- unique slot-record edges: `95`

## Records With Strongest Local Structure

| record | mode | op key | source | decoded | slot obs | shared obs | slot edges | shared edges |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 68 | `0x80` | `0fe212a8d404` | 2421 | 640 | 1316 | 1350 | 8 | 10 |
| 66 | `0x80` | `4e8210adb204` | 2411 | 720 | 908 | 908 | 8 | 8 |
| 70 | `0x80` | `098ad4a36805` | 2525 | 560 | 873 | 873 | 8 | 8 |
| 60 | `0x40` | `950a90757805` | 2344 | 848 | 833 | 833 | 5 | 5 |
| 64 | `0x40` | `93390e6b7c02` | 1604 | 688 | 668 | 668 | 2 | 2 |
| 59 | `0x80` | `30ca94930e05` | 2462 | 304 | 647 | 723 | 4 | 8 |
| 55 | `0x40` | `a742d3782e04` | 2313 | 896 | 529 | 612 | 17 | 18 |
| 58 | `0x80` | `66228ca20005` | 2292 | 544 | 460 | 492 | 15 | 15 |
| 67 | `0x40` | `b0f2d169c404` | 2295 | 656 | 401 | 401 | 2 | 2 |
| 63 | `0x80` | `c89256901a00` | 2024 | 256 | 369 | 369 | 1 | 1 |
| 83 | `0x80` | `0caa1588de03` | 2256 | 128 | 340 | 465 | 2 | 2 |
| 57 | `0x40` | `3512d253d403` | 1968 | 304 | 275 | 275 | 3 | 3 |
| 86 | `0x80` | `a3520f8e9004` | 2317 | 224 | 258 | 477 | 2 | 3 |
| 54 | `0x80` | `268ace91e605` | 2353 | 272 | 256 | 256 | 1 | 1 |
| 65 | `0x80` | `3f690aa24004` | 1844 | 544 | 254 | 254 | 1 | 1 |
| 51 | `0x80` | `a98252b3a002` | 2326 | 816 | 236 | 236 | 6 | 6 |
| 53 | `0x80` | `eee94e93cc04` | 2174 | 304 | 108 | 108 | 1 | 1 |
| 87 | `0x40` | `0af2177f2e01` | 1947 | 1008 | 58 | 512 | 4 | 5 |
| 74 | `0x80` | `ccc295b29405` | 2840 | 800 | 42 | 42 | 1 | 1 |
| 88 | `0x40` | `37424f6bc203` | 1965 | 688 | 9 | 9 | 1 | 1 |
| 52 | `0x80` | `513ad08ef203` | 2188 | 224 | 6 | 10 | 1 | 2 |
| 49 | `0x80` | `428a889c5804` | 2033 | 448 | 4 | 4 | 2 | 2 |
| 81 | `0x80` | `64cace949404` | 2266 | 320 | 0 | 465 | 0 | 2 |
| 62 | `0x80` | `9fd2119d4c04` | 2419 | 464 | 0 | 413 | 0 | 1 |

## Top Raw Edges

| src | dst | count | top offsets | src recs | dst recs | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `0b045c0906d5` | `71a589c84051` | 454 | `0x9900` x256, `0x9940` x198 | 86,87 | 86,87 | `9dffee9c908988f0a3eff0908a49e0b4...` | `02bf3790852ee014f0e0700302bf4790...` |
| `0c9a360d26b8` | `3465e4783c3d` | 413 | `0x7600` x413 | 61,62 | 62 | `8ac6e0904091f0a87c0808e6a3f07b00...` | `3090891ce0fea3e0a87c08080826f618...` |
| `23c16a978aa0` | `70e7ea0193bb` | 413 | `0x8840` x413 | 70 | 70 | `c251c249908a37e054f7f0d23e904834...` | `908633e0905906f090862fe090590df0...` |
| `99d4493dc4cf` | `b7a129b7d392` | 413 | `0x71c0` x413 | 59 | 59,60 | `f608760112efb6057c057c22908857e0...` | `e054884efeef4ef07e007f08120a65e4...` |
| `c24221ec1018` | `24ebe8bb67f5` | 413 | `0x7940` x413 | 64 | 64 | `f0908e2fe09047b1f0908e30e09047b1...` | `e43440f583e0904099f074a32ff582e4...` |
| `204291444868` | `2b9a017b9d81` | 369 | `0x7800` x369 | 63 | 63 | `097a00900001122fb7904097f090409c...` | `78b0f67f0122908a4ae054037004a3e0...` |
| `85545872cc2b` | `c5c0741f5daa` | 330 | `0x8440` x330 | 68 | 68 | `b43c13908a14e004f07006908a13e004...` | `862cf090596ae090862df0905906e090...` |
| `144315176c64` | `fbb6be935285` | 275 | `0x9480` x261, `0x9400` x14 | 81,83 | 81,82,83 | `8a23e04401f09088f1e04440f0908940...` | `9ff090480be054eff0904867e04480f0...` |
| `121190698133` | `1a8df790ad50` | 256 | `0x6880` x256 | 54 | 54 | `9059f074def0a374c0f0905a00e04407...` | `6003029464905a31e0540ff022ee707b...` |
| `b4bb17eb1656` | `6d249b0b8b59` | 256 | `0x7540` x256 | 60 | 60 | `0278ab760478b07608908a4de0700302...` | `7cf0904864e030e004e054fef0904860...` |
| `c5c0741f5daa` | `17a7e3a30d12` | 256 | `0x84c0` x256 | 68 | 68 | `862cf090596ae090862df0905906e090...` | `e0c3943c500ae004f0e4908974f0a3f0...` |
| `17e05da2c29c` | `24ebe8bb67f5` | 255 | `0x7980` x255 | 64 | 64 | `9085f4e0ff6012908970e0feefc39e50...` | `e43440f583e0904099f074a32ff582e4...` |
| `4cfa6d151318` | `28583441dfa8` | 255 | `0x7340` x255 | 60 | 60 | `8a23e054bff0908adfe0540f64036003...` | `feef78aa26ffee1836a87c0808f608ef...` |
| `7a8cbb7773e7` | `9e474876a043` | 254 | `0x7bc0` x254 | 65 | 65 | `f0121437908aede030e2259089dde060...` | `4000e020e7f990891fe02438ff90891e...` |
| `b69f366c92b6` | `7a8cbb7773e7` | 254 | `0x7b80` x254 | 64 | 65 | `fe08e6ff90891fe02fff90891ee03ea8...` | `f0121437908aede030e2259089dde060...` |
| `add3eb18b8cc` | `037cda80b040` | 253 | `0x8240` x253 | 67 | 67 | `e436f69047d7e054fef0908a4fe09047...` | `908d2ce004f09089fce06003e014f090...` |
| `9b673c066ae4` | `6d249b0b8b59` | 247 | `0x74c0` x247 | 60 | 60 | `8a4de0904099f0908a4ee0904099f090...` | `7cf0904864e030e004e054fef0904860...` |
| `404045e0e63c` | `efcb6299a750` | 239 | `0x7f40` x107, `0x7f00` x72, `0x7f80` x60 | 66 | 66 | `b404077d007f041205439048237480f0...` | `097a00900001122fb7904093f090409c...` |
| `20ea2ab16891` | `99d4493dc4cf` | 219 | `0x7180` x219 | 58,59 | 59 | `8a29e0c4540f30e011908a4ce0c3940e...` | `f608760112efb6057c057c22908857e0...` |
| `2b9a017b9d81` | `c24221ec1018` | 219 | `0x78c0` x219 | 63 | 64 | `78b0f67f0122908a4ae054037004a3e0...` | `f0908e2fe09047b1f0908e30e09047b1...` |
| `d21d30cf6e6b` | `fb00deab088b` | 206 | `0x8740` x105, `0x8780` x54, `0x8700` x47 | 70 | 70 | `12f2a022908844eff090825be030e627...` | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `a87d03db223d` | `95caa55b881e` | 203 | `0x6b40` x184, `0x6b00` x14, `0x6b80` x5 | 55 | 55 | `900001122fb7904835f0ef4440904834...` | `007e02120b079085efe09048f4f09085...` |
| `4f29221f2e51` | `25956f88a30e` | 197 | `0x6c40` x125, `0x6c80` x72 | 55,56 | 55,56 | `8a38e054eff0908a3ae0547ff0e04440...` | `8069908a4ce0240dff908a4ee02400fd...` |
| `b4bb17eb1656` | `0c9a360d26b8` | 196 | `0x75c0` x196 | 60 | 61,62 | `0278ab760478b07608908a4de0700302...` | `8ac6e0904091f0a87c0808e6a3f07b00...` |

## Record 68

- mode: `0x80`
- op key: `0fe212a8d404`
- source/decoded: `2421/640`
- slot/shared observations: `1316/1350`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `85545872cc2b` | `c5c0741f5daa` | 330 | `0x8440` x330 | `b43c13908a14e004f07006908a13e004...` | `862cf090596ae090862df0905906e090...` |
| `c5c0741f5daa` | `17a7e3a30d12` | 256 | `0x84c0` x256 | `862cf090596ae090862df0905906e090...` | `e0c3943c500ae004f0e4908974f0a3f0...` |
| `17a7e3a30d12` | `7106a72e56d9` | 167 | `0x8500` x167 | `e0c3943c500ae004f0e4908974f0a3f0...` | `30e054df904863f0908631e054fd9048...` |
| `0803afdb9f57` | `ad2faf50bc31` | 151 | `0x8380` x151 | `12014a9085f1e0fea3e0ffee4f24ff22...` | `596ac39089d1e094b89089d0e0940b50...` |
| `5badff03bdb8` | `c5c0741f5daa` | 148 | `0x8480` x148 | `90824ee064017058908133e0c4135407...` | `862cf090596ae090862df0905906e090...` |
| `85545872cc2b` | `5badff03bdb8` | 148 | `0x8440` x148 | `b43c13908a14e004f07006908a13e004...` | `90824ee064017058908133e0c4135407...` |
| `ad2faf50bc31` | `c5c0741f5daa` | 58 | `0x83c0` x58 | `596ac39089d1e094b89089d0e0940b50...` | `862cf090596ae090862df0905906e090...` |
| `c5c0741f5daa` | `85545872cc2b` | 58 | `0x8400` x58 | `862cf090596ae090862df0905906e090...` | `b43c13908a14e004f07006908a13e004...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `85545872cc2b` | `c5c0741f5daa` | 330 | `0x8440` x330 | `b43c13908a14e004f07006908a13e004...` | `862cf090596ae090862df0905906e090...` |
| `c5c0741f5daa` | `17a7e3a30d12` | 256 | `0x84c0` x256 | `862cf090596ae090862df0905906e090...` | `e0c3943c500ae004f0e4908974f0a3f0...` |
| `17a7e3a30d12` | `7106a72e56d9` | 167 | `0x8500` x167 | `e0c3943c500ae004f0e4908974f0a3f0...` | `30e054df904863f0908631e054fd9048...` |
| `0803afdb9f57` | `ad2faf50bc31` | 151 | `0x8380` x151 | `12014a9085f1e0fea3e0ffee4f24ff22...` | `596ac39089d1e094b89089d0e0940b50...` |
| `5badff03bdb8` | `c5c0741f5daa` | 148 | `0x8480` x148 | `90824ee064017058908133e0c4135407...` | `862cf090596ae090862df0905906e090...` |
| `85545872cc2b` | `5badff03bdb8` | 148 | `0x8440` x148 | `b43c13908a14e004f07006908a13e004...` | `90824ee064017058908133e0c4135407...` |
| `ad2faf50bc31` | `c5c0741f5daa` | 58 | `0x83c0` x58 | `596ac39089d1e094b89089d0e0940b50...` | `862cf090596ae090862df0905906e090...` |
| `c5c0741f5daa` | `85545872cc2b` | 58 | `0x8400` x58 | `862cf090596ae090862df0905906e090...` | `b43c13908a14e004f07006908a13e004...` |

Largest local components:

| size | chunks |
| --- | --- |
| 7 | `0803afdb9f57`, `17a7e3a30d12`, `5badff03bdb8`, `7106a72e56d9`, `85545872cc2b`, `ad2faf50bc31`, `c5c0741f5daa` |

## Record 66

- mode: `0x80`
- op key: `4e8210adb204`
- source/decoded: `2411/720`
- slot/shared observations: `908/908`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `404045e0e63c` | `efcb6299a750` | 239 | `0x7f40` x107, `0x7f00` x72, `0x7f80` x60 | `b404077d007f041205439048237480f0...` | `097a00900001122fb7904093f090409c...` |
| `9aa0a39b4424` | `fe343ef73975` | 157 | `0x7e80` x110, `0x7e00` x47 | `8571e5a8f075a890203e06204f03303f...` | `f618ee36f6908a4ae0640260030273de...` |
| `04a2d67cbfff` | `9aa0a39b4424` | 146 | `0x7dc0` x146 | `b7904097f0904000e020e7f99040b6e4...` | `8571e5a8f075a890203e06204f03303f...` |
| `fe343ef73975` | `9aa0a39b4424` | 121 | `0x7e40` x121 | `f618ee36f6908a4ae0640260030273de...` | `8571e5a8f075a890203e06204f03303f...` |
| `404045e0e63c` | `bd4b736c6b8d` | 109 | `0x7fc0` x109 | `b404077d007f041205439048237480f0...` | `f09089e5e06003e014f0908921e06003...` |
| `efcb6299a750` | `404045e0e63c` | 78 | `0x7f80` x78 | `097a00900001122fb7904093f090409c...` | `b404077d007f041205439048237480f0...` |
| `fe343ef73975` | `404045e0e63c` | 50 | `0x7ec0` x50 | `f618ee36f6908a4ae0640260030273de...` | `b404077d007f041205439048237480f0...` |
| `04a2d67cbfff` | `fe343ef73975` | 8 | `0x7dc0` x8 | `b7904097f0904000e020e7f99040b6e4...` | `f618ee36f6908a4ae0640260030273de...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `404045e0e63c` | `efcb6299a750` | 239 | `0x7f40` x107, `0x7f00` x72, `0x7f80` x60 | `b404077d007f041205439048237480f0...` | `097a00900001122fb7904093f090409c...` |
| `9aa0a39b4424` | `fe343ef73975` | 157 | `0x7e80` x110, `0x7e00` x47 | `8571e5a8f075a890203e06204f03303f...` | `f618ee36f6908a4ae0640260030273de...` |
| `04a2d67cbfff` | `9aa0a39b4424` | 146 | `0x7dc0` x146 | `b7904097f0904000e020e7f99040b6e4...` | `8571e5a8f075a890203e06204f03303f...` |
| `fe343ef73975` | `9aa0a39b4424` | 121 | `0x7e40` x121 | `f618ee36f6908a4ae0640260030273de...` | `8571e5a8f075a890203e06204f03303f...` |
| `404045e0e63c` | `bd4b736c6b8d` | 109 | `0x7fc0` x109 | `b404077d007f041205439048237480f0...` | `f09089e5e06003e014f0908921e06003...` |
| `efcb6299a750` | `404045e0e63c` | 78 | `0x7f80` x78 | `097a00900001122fb7904093f090409c...` | `b404077d007f041205439048237480f0...` |
| `fe343ef73975` | `404045e0e63c` | 50 | `0x7ec0` x50 | `f618ee36f6908a4ae0640260030273de...` | `b404077d007f041205439048237480f0...` |
| `04a2d67cbfff` | `fe343ef73975` | 8 | `0x7dc0` x8 | `b7904097f0904000e020e7f99040b6e4...` | `f618ee36f6908a4ae0640260030273de...` |

Largest local components:

| size | chunks |
| --- | --- |
| 6 | `04a2d67cbfff`, `404045e0e63c`, `9aa0a39b4424`, `bd4b736c6b8d`, `efcb6299a750`, `fe343ef73975` |

## Record 70

- mode: `0x80`
- op key: `098ad4a36805`
- source/decoded: `2525/560`
- slot/shared observations: `873/873`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `23c16a978aa0` | `70e7ea0193bb` | 413 | `0x8840` x413 | `c251c249908a37e054f7f0d23e904834...` | `908633e0905906f090862fe090590df0...` |
| `d21d30cf6e6b` | `fb00deab088b` | 206 | `0x8740` x105, `0x8780` x54, `0x8700` x47 | `12f2a022908844eff090825be030e627...` | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `fb00deab088b` | `d21d30cf6e6b` | 129 | `0x8700` x52, `0x8780` x51, `0x8740` x26 | `e0904091f0a3e55ef0a3e55ff0904000...` | `12f2a022908844eff090825be030e627...` |
| `d21d30cf6e6b` | `70e7ea0193bb` | 62 | `0x87c0` x62 | `12f2a022908844eff090825be030e627...` | `908633e0905906f090862fe090590df0...` |
| `fb00deab088b` | `70e7ea0193bb` | 59 | `0x87c0` x59 | `e0904091f0a3e55ef0a3e55ff0904000...` | `908633e0905906f090862fe090590df0...` |
| `d21d30cf6e6b` | `0e790c42bd72` | 2 | `0x8700` x2 | `12f2a022908844eff090825be030e627...` | `8634f0e0fea3e07806cec313ce13d8f9...` |
| `0e790c42bd72` | `fb00deab088b` | 1 | `0x8740` x1 | `8634f0e0fea3e07806cec313ce13d8f9...` | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `fb00deab088b` | `0e790c42bd72` | 1 | `0x8780` x1 | `e0904091f0a3e55ef0a3e55ff0904000...` | `8634f0e0fea3e07806cec313ce13d8f9...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `23c16a978aa0` | `70e7ea0193bb` | 413 | `0x8840` x413 | `c251c249908a37e054f7f0d23e904834...` | `908633e0905906f090862fe090590df0...` |
| `d21d30cf6e6b` | `fb00deab088b` | 206 | `0x8740` x105, `0x8780` x54, `0x8700` x47 | `12f2a022908844eff090825be030e627...` | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `fb00deab088b` | `d21d30cf6e6b` | 129 | `0x8700` x52, `0x8780` x51, `0x8740` x26 | `e0904091f0a3e55ef0a3e55ff0904000...` | `12f2a022908844eff090825be030e627...` |
| `d21d30cf6e6b` | `70e7ea0193bb` | 62 | `0x87c0` x62 | `12f2a022908844eff090825be030e627...` | `908633e0905906f090862fe090590df0...` |
| `fb00deab088b` | `70e7ea0193bb` | 59 | `0x87c0` x59 | `e0904091f0a3e55ef0a3e55ff0904000...` | `908633e0905906f090862fe090590df0...` |
| `d21d30cf6e6b` | `0e790c42bd72` | 2 | `0x8700` x2 | `12f2a022908844eff090825be030e627...` | `8634f0e0fea3e07806cec313ce13d8f9...` |
| `0e790c42bd72` | `fb00deab088b` | 1 | `0x8740` x1 | `8634f0e0fea3e07806cec313ce13d8f9...` | `e0904091f0a3e55ef0a3e55ff0904000...` |
| `fb00deab088b` | `0e790c42bd72` | 1 | `0x8780` x1 | `e0904091f0a3e55ef0a3e55ff0904000...` | `8634f0e0fea3e07806cec313ce13d8f9...` |

Largest local components:

| size | chunks |
| --- | --- |
| 5 | `0e790c42bd72`, `23c16a978aa0`, `70e7ea0193bb`, `d21d30cf6e6b`, `fb00deab088b` |

## Record 60

- mode: `0x40`
- op key: `950a90757805`
- source/decoded: `2344/848`
- slot/shared observations: `833/833`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `b4bb17eb1656` | `6d249b0b8b59` | 256 | `0x7540` x256 | `0278ab760478b07608908a4de0700302...` | `7cf0904864e030e004e054fef0904860...` |
| `4cfa6d151318` | `28583441dfa8` | 255 | `0x7340` x255 | `8a23e054bff0908adfe0540f64036003...` | `feef78aa26ffee1836a87c0808f608ef...` |
| `9b673c066ae4` | `6d249b0b8b59` | 247 | `0x74c0` x247 | `8a4de0904099f0908a4ee0904099f090...` | `7cf0904864e030e004e054fef0904860...` |
| `c684e9945319` | `b4bb17eb1656` | 53 | `0x7580` x53 | `503fa87c0808e6fe08e6ffe4fcfd908a...` | `0278ab760478b07608908a4de0700302...` |
| `b4bb17eb1656` | `c684e9945319` | 22 | `0x7580` x22 | `0278ab760478b07608908a4de0700302...` | `503fa87c0808e6fe08e6ffe4fcfd908a...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `b4bb17eb1656` | `6d249b0b8b59` | 256 | `0x7540` x256 | `0278ab760478b07608908a4de0700302...` | `7cf0904864e030e004e054fef0904860...` |
| `4cfa6d151318` | `28583441dfa8` | 255 | `0x7340` x255 | `8a23e054bff0908adfe0540f64036003...` | `feef78aa26ffee1836a87c0808f608ef...` |
| `9b673c066ae4` | `6d249b0b8b59` | 247 | `0x74c0` x247 | `8a4de0904099f0908a4ee0904099f090...` | `7cf0904864e030e004e054fef0904860...` |
| `c684e9945319` | `b4bb17eb1656` | 53 | `0x7580` x53 | `503fa87c0808e6fe08e6ffe4fcfd908a...` | `0278ab760478b07608908a4de0700302...` |
| `b4bb17eb1656` | `c684e9945319` | 22 | `0x7580` x22 | `0278ab760478b07608908a4de0700302...` | `503fa87c0808e6fe08e6ffe4fcfd908a...` |

Largest local components:

| size | chunks |
| --- | --- |
| 4 | `6d249b0b8b59`, `9b673c066ae4`, `b4bb17eb1656`, `c684e9945319` |
| 2 | `28583441dfa8`, `4cfa6d151318` |

## Record 64

- mode: `0x40`
- op key: `93390e6b7c02`
- source/decoded: `1604/688`
- slot/shared observations: `668/668`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `c24221ec1018` | `24ebe8bb67f5` | 413 | `0x7940` x413 | `f0908e2fe09047b1f0908e30e09047b1...` | `e43440f583e0904099f074a32ff582e4...` |
| `17e05da2c29c` | `24ebe8bb67f5` | 255 | `0x7980` x255 | `9085f4e0ff6012908970e0feefc39e50...` | `e43440f583e0904099f074a32ff582e4...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `c24221ec1018` | `24ebe8bb67f5` | 413 | `0x7940` x413 | `f0908e2fe09047b1f0908e30e09047b1...` | `e43440f583e0904099f074a32ff582e4...` |
| `17e05da2c29c` | `24ebe8bb67f5` | 255 | `0x7980` x255 | `9085f4e0ff6012908970e0feefc39e50...` | `e43440f583e0904099f074a32ff582e4...` |

Largest local components:

| size | chunks |
| --- | --- |
| 3 | `17e05da2c29c`, `24ebe8bb67f5`, `c24221ec1018` |

## Record 59

- mode: `0x80`
- op key: `30ca94930e05`
- source/decoded: `2462/304`
- slot/shared observations: `647/723`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `99d4493dc4cf` | `b7a129b7d392` | 413 | `0x71c0` x413 | `f608760112efb6057c057c22908857e0...` | `e054884efeef4ef07e007f08120a65e4...` |
| `20ea2ab16891` | `99d4493dc4cf` | 219 | `0x7180` x219 | `8a29e0c4540f30e011908a4ce0c3940e...` | `f608760112efb6057c057c22908857e0...` |
| `8d8c3b0a22a0` | `99d4493dc4cf` | 10 | `0x7180` x10 | `8a4df0904099e0908a4ef0904099e090...` | `f608760112efb6057c057c22908857e0...` |
| `8b2115cd509f` | `99d4493dc4cf` | 5 | `0x7180` x5 | `36f6904762e030e409e054eff0a87c08...` | `f608760112efb6057c057c22908857e0...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `99d4493dc4cf` | `b7a129b7d392` | 413 | `0x71c0` x413 | `f608760112efb6057c057c22908857e0...` | `e054884efeef4ef07e007f08120a65e4...` |
| `20ea2ab16891` | `99d4493dc4cf` | 219 | `0x7180` x219 | `8a29e0c4540f30e011908a4ce0c3940e...` | `f608760112efb6057c057c22908857e0...` |
| `20ea2ab16891` | `8d8c3b0a22a0` | 24 | `0x7100` x14, `0x7140` x10 | `8a29e0c4540f30e011908a4ce0c3940e...` | `8a4df0904099e0908a4ef0904099e090...` |
| `8d8c3b0a22a0` | `20ea2ab16891` | 20 | `0x7100` x12, `0x7140` x8 | `8a4df0904099e0908a4ef0904099e090...` | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `8b2115cd509f` | `20ea2ab16891` | 18 | `0x7100` x9, `0x7140` x9 | `36f6904762e030e409e054eff0a87c08...` | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `20ea2ab16891` | `8b2115cd509f` | 14 | `0x7100` x9, `0x7140` x5 | `8a29e0c4540f30e011908a4ce0c3940e...` | `36f6904762e030e409e054eff0a87c08...` |
| `8d8c3b0a22a0` | `99d4493dc4cf` | 10 | `0x7180` x10 | `8a4df0904099e0908a4ef0904099e090...` | `f608760112efb6057c057c22908857e0...` |
| `8b2115cd509f` | `99d4493dc4cf` | 5 | `0x7180` x5 | `36f6904762e030e409e054eff0a87c08...` | `f608760112efb6057c057c22908857e0...` |

Largest local components:

| size | chunks |
| --- | --- |
| 5 | `20ea2ab16891`, `8b2115cd509f`, `8d8c3b0a22a0`, `99d4493dc4cf`, `b7a129b7d392` |

## Record 55

- mode: `0x40`
- op key: `a742d3782e04`
- source/decoded: `2313/896`
- slot/shared observations: `529/612`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `a87d03db223d` | `95caa55b881e` | 203 | `0x6b40` x184, `0x6b00` x14, `0x6b80` x5 | `900001122fb7904835f0ef4440904834...` | `007e02120b079085efe09048f4f09085...` |
| `4f29221f2e51` | `25956f88a30e` | 125 | `0x6c40` x125 | `8a38e054eff0908a3ae0547ff0e04440...` | `8069908a4ce0240dff908a4ee02400fd...` |
| `95caa55b881e` | `a87d03db223d` | 99 | `0x6b80` x54, `0x6b00` x38, `0x6b40` x7 | `007e02120b079085efe09048f4f09085...` | `900001122fb7904835f0ef4440904834...` |
| `8853b78ca23e` | `95caa55b881e` | 26 | `0x6ac0` x26 | `98e54cf0904000e020e7f9904098e54d...` | `007e02120b079085efe09048f4f09085...` |
| `95caa55b881e` | `25956f88a30e` | 14 | `0x6bc0` x14 | `007e02120b079085efe09048f4f09085...` | `8069908a4ce0240dff908a4ee02400fd...` |
| `878984a494b8` | `a87d03db223d` | 12 | `0x6b00` x8, `0x6b80` x4 | `908988e0ffa3e0fd123d899047d07410...` | `900001122fb7904835f0ef4440904834...` |
| `8853b78ca23e` | `a87d03db223d` | 11 | `0x6ac0` x11 | `98e54cf0904000e020e7f9904098e54d...` | `900001122fb7904835f0ef4440904834...` |
| `a87d03db223d` | `878984a494b8` | 11 | `0x6b40` x10, `0x6b00` x1 | `900001122fb7904835f0ef4440904834...` | `908988e0ffa3e0fd123d899047d07410...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `a87d03db223d` | `95caa55b881e` | 203 | `0x6b40` x184, `0x6b00` x14, `0x6b80` x5 | `900001122fb7904835f0ef4440904834...` | `007e02120b079085efe09048f4f09085...` |
| `4f29221f2e51` | `25956f88a30e` | 197 | `0x6c40` x125, `0x6c80` x72 | `8a38e054eff0908a3ae0547ff0e04440...` | `8069908a4ce0240dff908a4ee02400fd...` |
| `95caa55b881e` | `a87d03db223d` | 99 | `0x6b80` x54, `0x6b00` x38, `0x6b40` x7 | `007e02120b079085efe09048f4f09085...` | `900001122fb7904835f0ef4440904834...` |
| `8853b78ca23e` | `95caa55b881e` | 26 | `0x6ac0` x26 | `98e54cf0904000e020e7f9904098e54d...` | `007e02120b079085efe09048f4f09085...` |
| `95caa55b881e` | `25956f88a30e` | 14 | `0x6bc0` x14 | `007e02120b079085efe09048f4f09085...` | `8069908a4ce0240dff908a4ee02400fd...` |
| `878984a494b8` | `a87d03db223d` | 12 | `0x6b00` x8, `0x6b80` x4 | `908988e0ffa3e0fd123d899047d07410...` | `900001122fb7904835f0ef4440904834...` |
| `25956f88a30e` | `4f29221f2e51` | 11 | `0x6c80` x11 | `8069908a4ce0240dff908a4ee02400fd...` | `8a38e054eff0908a3ae0547ff0e04440...` |
| `8853b78ca23e` | `a87d03db223d` | 11 | `0x6ac0` x11 | `98e54cf0904000e020e7f9904098e54d...` | `900001122fb7904835f0ef4440904834...` |

Largest local components:

| size | chunks |
| --- | --- |
| 8 | `25956f88a30e`, `4f29221f2e51`, `796c2cf9d837`, `878984a494b8`, `8853b78ca23e`, `95caa55b881e`, `a87d03db223d`, `dbf01786a7ed` |

## Record 58

- mode: `0x80`
- op key: `66228ca20005`
- source/decoded: `2292/544`
- slot/shared observations: `460/492`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `8f8e0add044c` | `7e15398acc97` | 141 | `0x7000` x120, `0x7080` x21 | `3407fee43dfde43cfc9085fd12343090...` | `6401704b90893de030e0447f0012050d...` |
| `8f8e0add044c` | `20ea2ab16891` | 136 | `0x70c0` x136 | `3407fee43dfde43cfc9085fd12343090...` | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `5fb5a8bf8f9a` | `7e15398acc97` | 66 | `0x6fc0` x66 | `9081f5e0ff908672e0fe6f6015908c84...` | `6401704b90893de030e0447f0012050d...` |
| `7e15398acc97` | `8f8e0add044c` | 26 | `0x7080` x26 | `6401704b90893de030e0447f0012050d...` | `3407fee43dfde43cfc9085fd12343090...` |
| `4037c8574920` | `7e15398acc97` | 15 | `0x7000` x14, `0x7080` x1 | `08eff6904000e020e7f9908ac6e09040...` | `6401704b90893de030e0447f0012050d...` |
| `20ea2ab16891` | `8d8c3b0a22a0` | 14 | `0x7100` x14 | `8a29e0c4540f30e011908a4ce0c3940e...` | `8a4df0904099e0908a4ef0904099e090...` |
| `4037c8574920` | `8d8c3b0a22a0` | 12 | `0x70c0` x12 | `08eff6904000e020e7f9908ac6e09040...` | `8a4df0904099e0908a4ef0904099e090...` |
| `8d8c3b0a22a0` | `20ea2ab16891` | 12 | `0x7100` x12 | `8a4df0904099e0908a4ef0904099e090...` | `8a29e0c4540f30e011908a4ce0c3940e...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `8f8e0add044c` | `7e15398acc97` | 141 | `0x7000` x120, `0x7080` x21 | `3407fee43dfde43cfc9085fd12343090...` | `6401704b90893de030e0447f0012050d...` |
| `8f8e0add044c` | `20ea2ab16891` | 136 | `0x70c0` x136 | `3407fee43dfde43cfc9085fd12343090...` | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `5fb5a8bf8f9a` | `7e15398acc97` | 66 | `0x6fc0` x66 | `9081f5e0ff908672e0fe6f6015908c84...` | `6401704b90893de030e0447f0012050d...` |
| `7e15398acc97` | `8f8e0add044c` | 26 | `0x7080` x26 | `6401704b90893de030e0447f0012050d...` | `3407fee43dfde43cfc9085fd12343090...` |
| `20ea2ab16891` | `8d8c3b0a22a0` | 24 | `0x7100` x14, `0x7140` x10 | `8a29e0c4540f30e011908a4ce0c3940e...` | `8a4df0904099e0908a4ef0904099e090...` |
| `8d8c3b0a22a0` | `20ea2ab16891` | 20 | `0x7100` x12, `0x7140` x8 | `8a4df0904099e0908a4ef0904099e090...` | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `8b2115cd509f` | `20ea2ab16891` | 18 | `0x7100` x9, `0x7140` x9 | `36f6904762e030e409e054eff0a87c08...` | `8a29e0c4540f30e011908a4ce0c3940e...` |
| `4037c8574920` | `7e15398acc97` | 15 | `0x7000` x14, `0x7080` x1 | `08eff6904000e020e7f9908ac6e09040...` | `6401704b90893de030e0447f0012050d...` |

Largest local components:

| size | chunks |
| --- | --- |
| 7 | `20ea2ab16891`, `4037c8574920`, `5fb5a8bf8f9a`, `7e15398acc97`, `8b2115cd509f`, `8d8c3b0a22a0`, `8f8e0add044c` |

## Record 67

- mode: `0x40`
- op key: `b0f2d169c404`
- source/decoded: `2295/656`
- slot/shared observations: `401/401`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `add3eb18b8cc` | `037cda80b040` | 253 | `0x8240` x253 | `e436f69047d7e054fef0908a4fe09047...` | `908d2ce004f09089fce06003e014f090...` |
| `037cda80b040` | `0803afdb9f57` | 148 | `0x82c0` x148 | `908d2ce004f09089fce06003e014f090...` | `12014a9085f1e0fea3e0ffee4f24ff22...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `add3eb18b8cc` | `037cda80b040` | 253 | `0x8240` x253 | `e436f69047d7e054fef0908a4fe09047...` | `908d2ce004f09089fce06003e014f090...` |
| `037cda80b040` | `0803afdb9f57` | 148 | `0x82c0` x148 | `908d2ce004f09089fce06003e014f090...` | `12014a9085f1e0fea3e0ffee4f24ff22...` |

Largest local components:

| size | chunks |
| --- | --- |
| 3 | `037cda80b040`, `0803afdb9f57`, `add3eb18b8cc` |

## Record 63

- mode: `0x80`
- op key: `c89256901a00`
- source/decoded: `2024/256`
- slot/shared observations: `369/369`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `204291444868` | `2b9a017b9d81` | 369 | `0x7800` x369 | `097a00900001122fb7904097f090409c...` | `78b0f67f0122908a4ae054037004a3e0...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `204291444868` | `2b9a017b9d81` | 369 | `0x7800` x369 | `097a00900001122fb7904097f090409c...` | `78b0f67f0122908a4ae054037004a3e0...` |

Largest local components:

| size | chunks |
| --- | --- |
| 2 | `204291444868`, `2b9a017b9d81` |

## Record 83

- mode: `0x80`
- op key: `0caa1588de03`
- source/decoded: `2256/128`
- slot/shared observations: `340/465`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `144315176c64` | `fbb6be935285` | 261 | `0x9480` x261 | `8a23e04401f09088f1e04440f0908940...` | `9ff090480be054eff0904867e04480f0...` |
| `fbb6be935285` | `144315176c64` | 79 | `0x9480` x79 | `9ff090480be054eff0904867e04480f0...` | `8a23e04401f09088f1e04440f0908940...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `144315176c64` | `fbb6be935285` | 275 | `0x9480` x261, `0x9400` x14 | `8a23e04401f09088f1e04440f0908940...` | `9ff090480be054eff0904867e04480f0...` |
| `fbb6be935285` | `144315176c64` | 190 | `0x9440` x111, `0x9480` x79 | `9ff090480be054eff0904867e04480f0...` | `8a23e04401f09088f1e04440f0908940...` |

Largest local components:

| size | chunks |
| --- | --- |
| 2 | `144315176c64`, `fbb6be935285` |

## Record 57

- mode: `0x40`
- op key: `3512d253d403`
- source/decoded: `1968/304`
- slot/shared observations: `275/275`

Top same-slot-record edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `cfe0a1406283` | `ee30d1b5daca` | 162 | `0x6e80` x162 | `f0e054fbf01297dd22908672eff09081...` | `a3e0f9a3e0faa3e02fffea3efeed39fd...` |
| `ee30d1b5daca` | `5fb5a8bf8f9a` | 99 | `0x6ec0` x99 | `a3e0f9a3e0faa3e02fffea3efeed39fd...` | `9081f5e0ff908672e0fe6f6015908c84...` |
| `cfe0a1406283` | `3dcd6687529a` | 14 | `0x6e80` x14 | `f0e054fbf01297dd22908672eff09081...` | `01122fb79047b1f0803e78a976000876...` |

Top shared-record identity edges:

| src | dst | count | offsets | src prefix | dst prefix |
| --- | --- | --- | --- | --- | --- |
| `cfe0a1406283` | `ee30d1b5daca` | 162 | `0x6e80` x162 | `f0e054fbf01297dd22908672eff09081...` | `a3e0f9a3e0faa3e02fffea3efeed39fd...` |
| `ee30d1b5daca` | `5fb5a8bf8f9a` | 99 | `0x6ec0` x99 | `a3e0f9a3e0faa3e02fffea3efeed39fd...` | `9081f5e0ff908672e0fe6f6015908c84...` |
| `cfe0a1406283` | `3dcd6687529a` | 14 | `0x6e80` x14 | `f0e054fbf01297dd22908672eff09081...` | `01122fb79047b1f0803e78a976000876...` |

Largest local components:

| size | chunks |
| --- | --- |
| 4 | `3dcd6687529a`, `5fb5a8bf8f9a`, `cfe0a1406283`, `ee30d1b5daca` |

## Practical Read

The adjacency graph is a better guide than public offset alone. It lets
us pick compact CDD records where several decoded-looking tiles form a
repeatable local neighborhood. Those are the records most worth using
as known-output anchors for the next static grammar attack.

The strongest records here should be cross-checked against the encoded
source spans before assuming any exact placement. A useful next script
would export each strong record as `source.bin` plus ordered tile
components so brute-force grammar tests can operate on one record at a
time.

