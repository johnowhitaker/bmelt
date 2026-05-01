# LiteOn CDD Affine Unit Analysis

Offline only. No drive commands were sent.

This is a partial decoder for the affine byte cells visible in DS-8ABSH CDD short records and in matching suffix units inside longer records. It is not a full CDD decompressor.

## Mask Table

The masks are carry-less multiplication by `0x19` over the low 4-bit cell index:

```text
cell: 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
mask: 00 19 32 2b 64 7d 56 4f c8 d1 fa e3 ac b5 9e 87
```

A canonical cell decodes as:

```text
plain_group_byte = raw_cell_byte ^ mask[cell]
cell = 4 * (record_index & 3) + unit_index
```

## Leaf Schedule

The same affine unit tail is now treated in three positions: full rows, prefix runs starting at record offset `0`, and suffix runs ending at the record end. The prior boundary conflict at group `96` was a prefix run, not a suffix run.

The observed affine leaves all land in one lane of a 12-record macro schedule:

```text
record_group = record_index // 4
macro        = record_group // 3
macro_lane   = record_group % 3
observed lane = 0
```

- Total affine-cell observations: `624`.
- Kind counts: `full-row`: 416, `prefix`: 15, `suffix`: 193.
- Macro lane counts: `0`: 624.
- All observations in macro lane 0: `True`.

| image | decoded groups | cell observations | conflicts | kind counts | macro-lane counts |
|---|---:|---:|---:|---|---|
| LD5M | 22 | 97 | 0 | `full-row`:64, `suffix`:33 | `0`:97 |
| AD12 | 22 | 100 | 0 | `full-row`:72, `prefix`:3, `suffix`:25 | `0`:100 |
| AHS9 | 21 | 98 | 0 | `full-row`:64, `prefix`:3, `suffix`:31 | `0`:98 |
| CD12 | 25 | 109 | 0 | `full-row`:72, `prefix`:3, `suffix`:34 | `0`:109 |
| CHS7 | 25 | 110 | 0 | `full-row`:72, `prefix`:3, `suffix`:35 | `0`:110 |
| CHS9 | 25 | 110 | 0 | `full-row`:72, `prefix`:3, `suffix`:35 | `0`:110 |

## Canonical Unit Tails

| image | canonical op key | unit size | matching short records | unit tail |
|---|---|---:|---:|---|
| LD5M | `0d6840031a00` | 13 | 16 | `b8b820171417141a77b83760` |
| AD12 | `0c6000031800` | 12 | 18 | `cf6b016b016b00c8d60680` |
| AHS9 | `0c6000031800` | 12 | 16 | `d33ac13ac13ac0c9560668` |
| CD12 | `0d6840031a00` | 13 | 18 | `c6582018c818c810d1706780` |
| CHS7 | `0d6840031a00` | 13 | 18 | `c07820180c180c0d15706740` |
| CHS9 | `0d6840031a00` | 13 | 18 | `bef82017dc17dc0c3d706740` |

## Cross-Image Stable Group Bytes

These groups decode to the same byte wherever evidence exists. Full-row short records and long-record suffix units are both included.

| group | plain | LD5M | AD12 | AHS9 | CD12 | CHS7 | CHS9 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | `0xd2` | `15` | `14,15` | `14,15` | `12,13,14,15` | `7,12,13,14,15` | `7,12,13,14,15` |
| 6 | `0x95` |  | `15` | `14,15` | `15` | `14,15` | `14,15` |
| 9 | `0x5c` | `14,15` |  |  |  |  |  |
| 12 | `0x1b` |  | `13,14,15` | `13,14,15` | `13,14,15` | `12,13,14,15` | `12,13,14,15` |
| 15 | `0xc9` | `15` | `15` | `15` | `15` | `15` | `15` |
| 18 | `0xb8` | `14,15` | `15` |  | `15` | `15` | `15` |
| 21 | `0x8c` |  | `15` | `15` | `15` | `15` | `15` |
| 24 | `0x36` | `14,15` | `15` |  | `14,15` |  |  |
| 27 | `0xe4` | `4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` |
| 30 | `0xa3` |  | `15` | `15` | `14,15` | `14,15` | `14,15` |
| 33 | `0x06` | `13,14,15` |  |  |  |  |  |
| 36 | `0x41` | `15` | `13,14,15` | `13,14,15` | `13,14,15` | `13,14,15` | `13,14,15` |
| 48 | `0x6c` |  |  |  | `15` | `15` | `15` |
| 51 | `0xbe` | `6,7,8,9,10,11,12,13,14,15` |  |  |  |  |  |
| 57 | `0x30` | `15` | `15` | `15` | `14,15` | `14,15` | `14,15` |
| 60 | `0x77` | `14,15` |  |  |  |  |  |
| 66 | `0x0c` | `13,14,15` |  | `15` |  | `15` | `15` |
| 69 | `0x38` | `12,13,14,15` | `12,13,14,15` | `13,14,15` | `13,14,15` | `13,14,15` | `13,14,15` |
| 72 | `0x82` | `15` | `15` | `15` | `14,15` | `14,15` | `14,15` |
| 75 | `0x50` | `14,15` |  |  | `15` | `15` | `15` |
| 78 | `0x17` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `1,2,3,4,5,6,7,8,9,10,11,12,13,14,15` |
| 81 | `0x15` | `12,13,14,15` | `12,13,14,15` | `12,13,14,15` | `12,13,14,15` | `12,13,14,15` | `12,13,14,15` |
| 84 | `0x52` | `14,15` | `2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `2,3,4,5,6,7,8,9,10,11,12,13,14,15` | `2,3,4,5,6,7,8,9,10,11,12,13,14,15` |
| 87 | `0x80` |  | `15` | `15` | `15` | `15` | `15` |
| 90 | `0x3a` | `13,14,15` | `15` | `15` | `15` | `15` | `15` |
| 93 | `0x0e` |  |  |  | `14,15` | `14,15` | `14,15` |
| 96 | `0xd8` |  | `12,13,14` | `12,13,14` | `12,13,14` | `12,13,14` | `12,13,14` |
| 99 | `0x0a` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` |
| 105 | `0x84` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` | `4,5,6,7,8,9,10,11,12,13,14,15` |
| 108 | `0xc3` | `14,15` | `14,15` | `14,15` | `14,15` | `14,15` | `14,15` |

## Suffix-Key Clues

The current suffix decoder is still evidence-driven: it finds literal canonical unit tails at the ends of source records. The operation key has strong correlations, but it does not yet predict every suffix count by itself.

- Suffix records found: 109.
- Suffix unit counts: `k=1`: 49, `k=2`: 36, `k=3`: 24.
- `op_key[5] == 0` for every suffix record: `True`.
- Excluding boundary group 96, `op_key[4]` is always the canonical doubled unit size: `0x18`, `0x1a`.
- Excluding boundary group 96, every `k=2`/`k=3` suffix record has decoded-span field `0x30`: `True`.

| k | records | rows | op_key[3] values | op_key[4] values | decoded-span fields |
|---:|---:|---|---|---|---|
| 1 | 49 | `1`:2, `3`:47 | `0x10`:1, `0x21`:2, `0x25`:1, `0x27`:1, `0x28`:1, `0x29`:2, `0x2b`:1, `0x3a`:2, `0x41`:1, `0x49`:1, `0x4a`:2, `0x4b`:3, `0x4e`:1, `0x53`:1, `0x5a`:1, `0x5b`:1, `0x5f`:1, `0x61`:2, `0x67`:1, `0x68`:3, `0x69`:2, `0x6d`:1, `0x79`:1, `0x83`:2, `0x88`:1, `0x8b`:1, `0x8f`:2, `0x90`:1, `0x94`:2, `0xa1`:1, `0xa3`:2, `0xa9`:1, `0xb7`:3 | `0x18`:18, `0x1a`:31 | `0x010`:1, `0x030`:2, `0x080`:1, `0x090`:1, `0x0a0`:2, `0x0b0`:4, `0x0e0`:1, `0x0f0`:2, `0x100`:2, `0x130`:1, `0x140`:2, `0x1a0`:1, `0x1b0`:1, `0x1f0`:1, `0x210`:5, `0x230`:2, `0x250`:1, `0x270`:2, `0x280`:4, `0x290`:5, `0x2b0`:1, `0x2d0`:1, `0x370`:3, `0x390`:1, `0x3a0`:2 |
| 2 | 36 | `0`:5, `1`:1, `3`:30 | `0x03`:36 | `0x18`:7, `0x1a`:29 | `0x030`:36 |
| 3 | 24 | `0`:9, `3`:15 | `0x03`:24 | `0x18`:8, `0x1a`:16 | `0x030`:24 |

## Conflicts

The previous group `96` conflict is resolved by treating record 387 as a prefix run. Any remaining conflicts should be treated as decoder bugs or unsupported record forms until proven otherwise.

| image | group | plains | records |
|---|---:|---|---|

## Interpretation

- The previous `m` byte is better described as a raw coded byte for one row of a 16-cell group.
- Long records often end with the same canonical unit tail and recover the rightmost missing cells for that record row.
- `op_key[4] == 2 * unit_size` holds for the known canonical unit class, which makes byte 4 look like a doubled unit width or stride.
- This strengthens the model of CDD as a proprietary controller codeword format, not a standard compressor or encrypted blob.

