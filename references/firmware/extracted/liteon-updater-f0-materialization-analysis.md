# LiteOn Updater F0 Materialization Analysis

Offline-only static analysis. No drive commands were sent.

## What Was Checked

The unpacked AHS9 Windows updater module was inspected for a point where
the firmware/CDD payload exists in plaintext. The module does not contain
raw `CDD\t` strings before decryption, but it does contain an encrypted
1 MiB F0 object plus the table-driven AES-ECB key schedule used to decrypt
that object.

## AHS9 Updater Extraction

- `BIN_START1`: `0`
- `BIN_SIZE1B`: `1048576`
- metadata range: `0x194c80..0x194dc0`
- encrypted source offset: `0x195dc0`
- encrypted size: `0x100000`
- `COPYF2K8_SIZE` marker offset: `0x819f11`
- key table offset: `0x819f2a`
- selector offset: `0x819f82`
- selector: `0x07`
- derived AES-ECB key: `7ee34f39b34d5c9248473a39ec976508`

Key derivation:

```text
key[i] = table[(selector + i * 0x11) & 0xff]
```

Marker scan before decrypt:

- `CDD`: no hit
- `DU8A6S`: no hit
- `LITE`: `0x1918f6`
- `EXTRAINQ`: `0x1918ff`
- `AHS9`: `0x194d38`
- `S8AB0HS6`: no hit

The AES-ECB decrypted object has the expected firmware markers:

| marker | offsets |
|---|---|
| `CDD` | `0x702c`, `0xd9000` |
| `DU8A6S` | `0xe7ff5` |
| `LITE` | `0xe7ffc` |
| `EXTRAINQ` | `0x3c93` |
| `AHS9` | `0xd8ff0` |
| `S8AB0HS6` | `0x6ff8` |

## COPYF2K8 Postprocess

The AES-ECB output is not yet byte-identical to the final plain image.
The updater applies a compact per-1KiB mask from the `0x1000` bytes
immediately after the metadata block.

- mask offset: `0x194dc0`
- block size: `0x400`
- block count: `1024`
- NEW_FW record: `AHS9`
- record delta: `0x15`

Rule:

```text
table_byte = mask[block_index]
relative_offset = table_byte & 0x3f
xor_delta = record_delta if block_index % 7 in {0, 2} else table_byte
image[block_index * 0x400 + relative_offset] ^= xor_delta
```

- patches: `1024`
- patches that changed bytes: `1021`
- zero-delta/no-change blocks: `0x1a7, 0x1eb, 0x24d`
- postprocess SHA-256: `e556dbed1132638b58600100fcd2c45d731430edc0cad388455cdbf624322af0`

CDD streams visible after decrypt:

Stream-end guesses use `/Users/johno/projects/boastermelt/work/cdd-siblings/AHS9-postprocess-plain.bin` when available, because
the decrypted updater representation still has one sparse altered byte per
`0x400` block and therefore does not contain fully canonical erased gaps.

| stream | range | header dir field | aux guess |
|---:|---:|---:|---:|
| 1 | `0x0702c..0xcfe20` | `0x07dec` | `0x400` |
| 2 | `0xd9000..0xe636a` | `0x07dec` | `0x400` |

Other container fields:

- pre-family word: `c1e2ab08`
- family marker: `S8AB0HS6`
- trailer auth14: `5084d8596db47bd5da64d01ad053`
- raw AES-ECB SHA-256: `6b4b2234be96f32bf258da2e184d203911edfc434a99422df6d2fc1618af7f19`
- postprocess SHA-256: `e556dbed1132638b58600100fcd2c45d731430edc0cad388455cdbf624322af0`

## Relationship To The Existing Plain AHS9 Sample

- raw AES-ECB byte-identical: `False`
- raw AES-ECB total differing bytes: `1021`
- raw AES-ECB chunks with differences: `1021`
- raw AES-ECB single-byte-difference chunks: `1021`
- raw AES-ECB chunks with no difference: `0x1a7, 0x1eb, 0x24d`
- raw AES-ECB differing byte offset inside each `0x400` block ranges `0x0`..`0x3f`
- after COPYF2K8 byte-identical: `True`
- after COPYF2K8 total differing bytes: `0`

Top selected-byte positions:

| offset in 0x400 block | count |
|---:|---:|
| `0x35` | 24 |
| `0x2d` | 23 |
| `0x1f` | 22 |
| `0x32` | 22 |
| `0x03` | 22 |
| `0x3b` | 22 |
| `0x05` | 21 |
| `0x24` | 20 |
| `0x0c` | 20 |
| `0x28` | 20 |
| `0x0d` | 20 |
| `0x16` | 19 |

Top XOR deltas:

| xor | count |
|---:|---:|
| `0x15` | 296 |
| `0xe5` | 8 |
| `0x51` | 8 |
| `0xb1` | 7 |
| `0x72` | 7 |
| `0xc0` | 7 |
| `0x7b` | 7 |
| `0x5d` | 7 |
| `0xd5` | 6 |
| `0x16` | 6 |
| `0xdf` | 6 |
| `0x9e` | 6 |

## Interpretation

The updater does materialize a CDD-bearing firmware object, but not as a
separate decoded controller firmware. The CDD streams appear after the
whole 1 MiB F0 object is AES-ECB decrypted. There is no evidence in this
module that the Windows updater itself decodes or interprets the CDD body;
that still looks like controller-side work.

The remaining mismatch after AES-ECB is exactly the COPYF2K8 layer, and
that layer now reproduces the existing AHS9 plain sample byte-for-byte.
The updater still does not appear to decode the CDD body into controller
runtime form; it materializes the sealed F0 container that the drive later
hands to controller-side CDD machinery.
