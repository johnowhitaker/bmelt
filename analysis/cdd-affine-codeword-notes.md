# CDD Affine Codeword Notes

Date: 2026-04-30

Scope: static only. This follows the peer short-record observation and asks
whether the same pattern generalizes into a known packer/compressor. So far the
answer is no: the strongest visible structure looks like a small proprietary
controller codeword grammar.

## Short-Record Byte 0 Is A 2-Bit Affine Row

For the two high-frequency short operations:

```text
0d6840031a00
0c6000031800
```

each record has four source units. Byte 0 of those units follows:

```text
m, m^0x19, m^0x32, m^0x2b
```

This is not just four arbitrary constants:

```text
0x32 = 0x19 << 1
0x2b = 0x19 ^ 0x32
```

So the unit byte is an affine function over two lane bits:

```text
unit_byte = m ^ lane0*0x19 ^ lane1*0x32
```

That holds for 104/104 known short records across LD5M, AD12, AHS9, CD12,
CHS7, and CHS9. Shared record indices keep the same `m` value across sibling
images.

## Consecutive Short Records Add Another 2-Bit Row

The stable `m` values in consecutive short-record runs follow a second affine
row:

```text
base^0x00, base^0x64, base^0xc8, base^0xac
```

Again these constants are structured:

```text
0x64 = 0x19 << 2
0xc8 = 0x19 << 3
0xac = 0x64 ^ 0xc8
```

So a full four-record by four-unit tile would have byte-0 values:

```text
base
  ^ record0*0x64 ^ record1*0xc8
  ^ unit0*0x19   ^ unit1*0x32
```

Example complete four-record run:

```text
records 312..315: m = 17 73 df bb
0x17 ^ {00, 64, c8, ac}
```

Three-record runs fit contiguous slices of the same row:

```text
records 109..111: m = 80 2c 48, fits base 0xe4 with masks {64,c8,ac}
records 337..339: m = 36 9a fe, fits base 0x52 with masks {64,c8,ac}
records 397..399: m = 6e c2 a6, fits base 0x0a with masks {64,c8,ac}
records 421..423: m = e0 4c 28, fits base 0x84 with masks {64,c8,ac}
```

This makes the repeated motif island look like an affine byte-lane code over a
small 4x4 tile, not a compressor token stream.

## Neighbor Records May Carry Missing Lanes

Some three-record runs are preceded by a non-short record with the same
candidate decoded span `0x30` and a related operation-key suffix. That preceding
record is a plausible "lane 0 encoded in a heavier mode" rather than a missing
record.

Examples:

```text
AD12 record 108: op 2c6200031800, decoded span 0x30
AD12 records 109..111: short m = 80 2c 48

AD12 record 336: op 977a0c031800, decoded span 0x30
AD12 records 337..339: short m = 36 9a fe

LD5M record 312: op 846840031a00, decoded span 0x30
LD5M records 313..315: short m = 73 df bb
```

That is not proof, but it is a useful way to think about the odd run lengths:
the same logical tile may be split across multiple operation modes.

## Negative Generalization Checks

I tried two cheap generalizations beyond the short operations:

1. Same-operation aligned columns: for repeated operation keys, look for
   constant-XOR column relationships across source bytes.
2. Intra-record periodic units: for unit widths 4..64, look for records where
   many unit columns are constant/low entropy or where unit suffixes are
   identical.

Both were negative outside the known short operations. Long records do have
same-index exact-prefix islands between close siblings, especially CHS7/CHS9,
but not constant nonzero-XOR lanes or repeated suffix units.

That suggests the short mode is the easiest visible sub-code, while the common
long modes use a denser grammar.

## Interpretation

This still does not identify a public format. The masks are familiar in the
sense that they form an affine code over byte lanes, but the CDD container does
not look like LZ, Huffman, arithmetic coding, AES, or a named executable packer.
The encoded CDD bodies are much larger than the decoded/controller range, so
the design goal is unlikely to be compression.

The more likely model is:

- proprietary controller-side packed/codeword format;
- small affine redundancy/interleave cells in at least one mode;
- hidden controller expands or consumes it after the visible 8051 parser writes
  mailbox fields;
- obscurity may help security, but the visible shape is consistent with
  hardware-friendly controller packaging rather than a generic anti-RE packer.

Next useful static target: find another operation mode with a comparable small
affine substructure, especially records adjacent to the short runs that share
decoded span `0x30`.
