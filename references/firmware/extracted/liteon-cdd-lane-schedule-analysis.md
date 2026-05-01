# LiteOn CDD Lane Schedule Analysis

Offline only. No drive commands were sent.

This report follows the 12-record macro schedule suggested by the affine leaf decoder and asks whether the same edge-unit grammar appears outside macro lane 0.

## Broad Edge-Affine Scan

Broad edge scan over unit sizes 4..40 and k=2..4. Counts include overlapping subruns; use lane presence/absence rather than exact run counts.

- Total edge-affine hits: `718`.
- Hits by macro lane: `{0: 718}`.
- Hits by unit size: `{12: 231, 13: 487}`.
- Hits by kind: `{'prefix': 322, 'suffix': 396}`.
- Macro lane 1/2 hits: `0`.

Result: the broadened edge scan still finds the repeated-tail affine unit grammar only in macro lane 0. Lanes 1 and 2 either use a different grammar or carry their useful data inside the high-entropy body, not as prefix/suffix affine leaves.

## Per-Lane Shape

Lane 0 has the repeated short-operation class; lanes 1 and 2 have almost entirely unique operation keys and higher-entropy bulk records.

| image | lane | records | source total | decoded-span total | source/decoded | repeated op keys | top op byte 5 |
|---|---:|---:|---:|---:|---:|---|---|
| LD5M | 0 | 148 | `0x4531b` | `0xedc0` | 4.66 | `0d6840031a00` x16 | `0x04`:45, `0x05`:40, `0x00`:34, `0x03`:16, `0x02`:6, `0x01`:6 |
| LD5M | 1 | 144 | `0x4423c` | `0x10570` | 4.17 | - | `0x04`:60, `0x03`:30, `0x02`:21, `0x05`:19, `0x01`:8, `0x00`:5 |
| LD5M | 2 | 144 | `0x4a762` | `0xf080` | 4.95 | - | `0x04`:69, `0x05`:27, `0x03`:25, `0x02`:20, `0x01`:2, `0x06`:1 |
| AD12 | 0 | 148 | `0x45b00` | `0x10120` | 4.34 | `0c6000031800` x18 | `0x04`:47, `0x05`:38, `0x00`:38, `0x02`:10, `0x03`:7, `0x01`:6 |
| AD12 | 1 | 144 | `0x44442` | `0x10f00` | 4.03 | - | `0x04`:51, `0x03`:32, `0x05`:26, `0x02`:19, `0x01`:9, `0x00`:5 |
| AD12 | 2 | 144 | `0x4aba4` | `0xec00` | 5.07 | - | `0x04`:67, `0x05`:30, `0x03`:25, `0x02`:19, `0x01`:3 |
| AHS9 | 0 | 148 | `0x45e7e` | `0xff20` | 4.38 | `0c6000031800` x16 | `0x04`:47, `0x05`:37, `0x00`:37, `0x03`:11, `0x02`:9, `0x01`:6 |
| AHS9 | 1 | 144 | `0x44339` | `0x10a70` | 4.10 | - | `0x04`:53, `0x03`:34, `0x05`:23, `0x02`:18, `0x01`:9, `0x00`:5 |
| AHS9 | 2 | 144 | `0x4ac73` | `0xfd90` | 4.72 | - | `0x04`:68, `0x03`:25, `0x05`:24, `0x02`:22, `0x01`:3, `0x06`:2 |
| CD12 | 0 | 148 | `0x447cc` | `0xfb00` | 4.37 | `0d6840031a00` x18 | `0x04`:47, `0x00`:40, `0x05`:38, `0x02`:9, `0x03`:8, `0x01`:5 |
| CD12 | 1 | 144 | `0x448c7` | `0x11490` | 3.97 | - | `0x04`:51, `0x03`:34, `0x05`:23, `0x02`:20, `0x01`:9, `0x00`:5 |
| CD12 | 2 | 144 | `0x4ac33` | `0xeec0` | 5.01 | - | `0x04`:66, `0x05`:33, `0x03`:23, `0x02`:19, `0x01`:3 |
| CHS7 | 0 | 148 | `0x447c3` | `0xf7c0` | 4.42 | `0d6840031a00` x18 | `0x04`:47, `0x00`:41, `0x05`:36, `0x03`:9, `0x02`:9, `0x01`:5 |
| CHS7 | 1 | 144 | `0x44772` | `0x10bf0` | 4.09 | - | `0x04`:48, `0x03`:38, `0x05`:24, `0x02`:19, `0x01`:9, `0x00`:5 |
| CHS7 | 2 | 144 | `0x4ae4f` | `0xffa0` | 4.69 | - | `0x04`:68, `0x05`:26, `0x02`:23, `0x03`:22, `0x01`:3, `0x06`:2 |
| CHS9 | 0 | 148 | `0x447de` | `0xf430` | 4.49 | `0d6840031a00` x18 | `0x04`:48, `0x00`:40, `0x05`:35, `0x03`:9, `0x02`:9, `0x01`:6 |
| CHS9 | 1 | 144 | `0x447c5` | `0x10fb0` | 4.03 | - | `0x04`:49, `0x03`:37, `0x05`:24, `0x02`:19, `0x01`:9, `0x00`:5 |
| CHS9 | 2 | 144 | `0x4ae48` | `0xfbf0` | 4.76 | - | `0x04`:68, `0x05`:26, `0x02`:23, `0x03`:22, `0x01`:3, `0x06`:2 |

## CHS7/CHS9 Locality Check

CHS7 and CHS9 are close siblings. At same-index records with the same operation key and source length, about 72% of source bytes are equal in every lane. That supports a deterministic/localized codeword format, not per-image encryption with avalanche.

| lane | records | same op key | same op+len records | equal-byte rate in same op+len records |
|---:|---:|---:|---:|---:|
| 0 | 148 | 128 | 128 | 0.718 |
| 1 | 144 | 130 | 130 | 0.715 |
| 2 | 144 | 122 | 122 | 0.724 |

Changed bytes are dominated by one-bit XOR deltas in all lanes, with the same top deltas (`0x80`, `0x01`, `0x02`, `0x40`, etc.). That is another sign of localized deterministic edits rather than a stream cipher or block-cipher avalanche.

| lane | changed-byte bit counts | top XOR deltas |
|---:|---|---|
| 0 | 1b:32971, 2b:16841, 3b:7280, 4b:5384, 5b:2439, 6b:854, 7b:308, 8b:66 | `0x80`:6062, `0x01`:5969, `0x02`:3997, `0x40`:3980, `0x04`:3432, `0x20`:3227, `0x08`:3198, `0x10`:3106 |
| 1 | 1b:33693, 2b:18222, 3b:7916, 4b:6623, 5b:3191, 6b:1025, 7b:387, 8b:78 | `0x80`:6234, `0x01`:6047, `0x40`:4036, `0x02`:4029, `0x04`:3493, `0x20`:3375, `0x08`:3285, `0x10`:3194 |
| 2 | 1b:34551, 2b:17852, 3b:7829, 4b:5906, 5b:2741, 6b:865, 7b:378, 8b:74 | `0x80`:6410, `0x01`:6179, `0x02`:4341, `0x40`:4018, `0x04`:3602, `0x20`:3345, `0x10`:3333, `0x08`:3323 |

The changed bytes are also spatially local. Most contiguous diff runs are four bytes or shorter in every lane:

| lane | diff runs | len=1 | len<=2 | len<=4 | top run lengths |
|---:|---:|---:|---:|---:|---|
| 0 | 39138 | 0.603 | 0.880 | 0.980 | 1:23614, 2:10826, 3:2950, 4:963, 5:378, 6:246, 7:74, 8:28 |
| 1 | 41387 | 0.607 | 0.885 | 0.983 | 1:25120, 2:11491, 3:3125, 4:940, 5:427, 6:133, 7:60, 8:25 |
| 2 | 41835 | 0.611 | 0.886 | 0.983 | 1:25581, 2:11474, 3:3047, 4:1024, 5:448, 6:131, 7:46, 8:21 |

## Interpretation

- The lane-0 affine leaf is real, but it is probably one visible lane of a larger CDD/controller codeword schedule.
- Lanes 1 and 2 did not reveal an analogous repeated-tail edge grammar under a wider unit-size scan.
- The close-sibling byte locality keeps arguing against ordinary encryption/compression as the whole story. The hard lanes look like controller-specific packed/ECC-like records.
- A useful next static step is to classify lane 1/2 operation-key fields and body-diff locality, rather than keep searching for the lane-0 tail pattern there.
