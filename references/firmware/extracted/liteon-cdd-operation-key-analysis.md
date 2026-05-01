# LiteOn CDD Operation-Key Analysis

Offline only. No drive commands were sent.

This report focuses on the six-byte CDD directory operation key: `entry[0:5] + (entry[5] & 0x0f)`. It complements the CDD stream and lane-schedule reports.

## Key Uniqueness

- Records analyzed: `2616`.
- Unique operation keys: `2135`.
- Keys mapping to multiple source lengths: `0`.

Result: within the six sibling images, operation key fully determines encoded source length. The directory still stores source starts, but no observed operation key maps to two different source lengths.

## Fixed Bits

Fixed across all unique keys: `key[1].2=0`, `key[2].5=0`, `key[4].0=0`, `key[5].3=0`, `key[5].4=0`, `key[5].5=0`, `key[5].6=0`, `key[5].7=0`.

The expected constraints are visible here: `key[4]` is always even, and `key[5]` is the low nibble of the split directory byte, so only low values appear. The extra fixed bits `key[1].2=0` and `key[2].5=0` look like real format constraints.

## Modes

| mode (`key[3] & 0xc0`) | records | encoded source | decoded-span candidate | source/decoded | zero-span records | top `key[5]` |
|---:|---:|---:|---:|---:|---:|---|
| `0x00` | 272 | `0x26e80` | `0x13ad0` | 1.98 | 0 | `0x00`:211, `0x01`:32, `0x02`:24, `0x03`:2, `0x04`:2, `0x05`:1 |
| `0x40` | 812 | `0x160cdc` | `0x73810` | 3.05 | 13 | `0x04`:255, `0x03`:225, `0x02`:191, `0x05`:61, `0x01`:50, `0x00`:27, `0x06`:3 |
| `0x80` | 1510 | `0x361d94` | `0x96c50` | 5.74 | 21 | `0x04`:737, `0x05`:463, `0x03`:177, `0x02`:79, `0x00`:22, `0x01`:22, `0x06`:10 |
| `0xc0` | 22 | `0xf50e` | `0x930` | 26.67 | 3 | `0x06`:10, `0x04`:5, `0x05`:4, `0x03`:3 |

## `key[4] / 2` Is Not Universal Unit Size

For the known affine leaf class, `key[4] == 2 * unit_size` (`0x1a` for 13-byte units, `0x18` for 12-byte units). Treating that as a universal record unit size fails on the hard lanes:

| macro lane | records | nonzero `key[4]/2` | source length divisible | near-divisible | top remainders |
|---:|---:|---:|---:|---:|---|
| 0 | 888 | 884 | 151 | 203 | `0`:151, `2`:29, `11`:29, `1`:28, `9`:28, `6`:28, `3`:28, `8`:24 |
| 1 | 864 | 859 | 42 | 103 | `0`:42, `1`:32, `2`:28, `12`:24, `8`:23, `7`:22, `10`:21, `5`:20 |
| 2 | 864 | 855 | 51 | 109 | `0`:51, `3`:35, `1`:28, `4`:26, `5`:25, `2`:22, `8`:22, `13`:20 |

## Linear Field Probe

Affine GF(2) probe over constant + 48 operation-key bits.

The only nontrivial source-length bit recovered as an affine expression is:

- `source_len.bit0 = key[0].0 ^ key[1].3 ^ key[2].6 ^ key[4].1`.

Bits 1..11 of source length are not affine functions of the raw key bits under this probe. Bits 12..15 are trivially zero because observed source lengths are below `0x1000`.

## CHS7/CHS9 Operation-Key Edits

Close-sibling operation-key changes are sparse and local. This supports the broader picture that CDD is deterministic and structured, but it does not expose a simple field map by itself.

| macro lane | changed records | changed key byte positions |
|---:|---:|---|
| 0 | 20 | `0`:17, `1`:11, `2`:14, `3`:9, `4`:10, `5`:2 |
| 1 | 14 | `0`:7, `1`:7, `2`:11, `3`:3, `4`:7, `5`:1 |
| 2 | 22 | `0`:10, `1`:12, `2`:10, `3`:8, `4`:16 |

Examples:

```json
{
  "0": [
    {
      "record": 0,
      "left_key": "f30a57b9a805",
      "right_key": "eff256b8a605",
      "left_source_len": 2957,
      "right_source_len": 2945,
      "left_decoded_span": 912,
      "right_decoded_span": 896
    },
    {
      "record": 1,
      "left_key": "e3cad6b4b005",
      "right_key": "ded296b5b205",
      "left_source_len": 2919,
      "right_source_len": 2919,
      "left_decoded_span": 832,
      "right_decoded_span": 848
    },
    {
      "record": 2,
      "left_key": "bee214ce8406",
      "right_key": "bcfad4cd8406",
      "left_source_len": 3028,
      "right_source_len": 3028,
      "left_decoded_span": 224,
      "right_decoded_span": 208
    },
    {
      "record": 12,
      "left_key": "deaa53b17e05",
      "right_key": "e0aa13b17e05",
      "left_source_len": 2775,
      "right_source_len": 2776,
      "left_decoded_span": 784,
      "right_decoded_span": 784
    }
  ],
  "1": [
    {
      "record": 6,
      "left_key": "82aa50aa6605",
      "right_key": "79c250aa6805",
      "left_source_len": 2547,
      "right_source_len": 2542,
      "left_decoded_span": 672,
      "right_decoded_span": 672
    },
    {
      "record": 7,
      "left_key": "aa1ad5648604",
      "right_key": "a91295648a04",
      "left_source_len": 2339,
      "right_source_len": 2338,
      "left_decoded_span": 576,
      "right_decoded_span": 576
    },
    {
      "record": 19,
      "left_key": "5f32d1a89e05",
      "right_key": "5f2a91a89e05",
      "left_source_len": 2551,
      "right_source_len": 2549,
      "left_decoded_span": 640,
      "right_decoded_span": 640
    },
    {
      "record": 100,
      "left_key": "f212949df204",
      "right_key": "f112549df204",
      "left_source_len": 2659,
      "right_source_len": 2657,
      "left_decoded_span": 464,
      "right_decoded_span": 464
    }
  ],
  "2": [
    {
      "record": 8,
      "left_key": "27b2129e2a04",
      "right_key": "2792529d2c04",
      "left_source_len": 2314,
      "right_source_len": 2308,
      "left_decoded_span": 480,
      "right_decoded_span": 464
    },
    {
      "record": 9,
      "left_key": "5caa52a6ca04",
      "right_key": "5d9252a6d004",
      "left_source_len": 2479,
      "right_source_len": 2480,
      "left_decoded_span": 608,
      "right_decoded_span": 608
    },
    {
      "record": 10,
      "left_key": "ecb113b32205",
      "right_key": "e9b913b31805",
      "left_source_len": 2495,
      "right_source_len": 2488,
      "left_decoded_span": 816,
      "right_decoded_span": 816
    },
    {
      "record": 11,
      "left_key": "6f3a15ad0a04",
      "right_key": "711255ad0e04",
      "left_source_len": 2511,
      "right_source_len": 2511,
      "left_decoded_span": 720,
      "right_decoded_span": 720
    }
  ]
}
```

## Interpretation

- The operation key is stronger than a cosmetic tag: no observed key maps to two source lengths.
- The decoded-span candidate remains the clearest bitfield: `(key[3] & 0x3f) << 4`.
- The encoded source length is not a simple visible bitfield. Only its parity has a clean affine relation to key bits.
- `key[4]` is a unit-size hint for the lane-0 affine leaf class, but it does not explain hard-lane record sizes.
- This keeps pointing at a proprietary controller codeword/packet grammar rather than a stock compressor or encrypted blob.
