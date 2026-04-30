# CDD Affine Codeword Notes

Date: 2026-04-30

Scope: static only. This follows the peer affine-unit observation and asks how
far the visible CDD unit code can be decoded without a runtime oracle.

## 16-Cell Mask Table

The short-record masks are not two unrelated XOR rows. They are one 16-cell
mask table:

```text
cell: 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
mask: 00 19 32 2b 64 7d 56 4f c8 d1 fa e3 ac b5 9e 87
```

Equivalently:

```text
mask[cell] = carryless_mul8(0x19, cell)
```

For the canonical short units:

```text
cell = 4 * (record_index & 3) + unit_index
plain_group_byte = raw_cell_byte ^ mask[cell]
```

The row-local values we previously called `m` were raw coded bytes, not final
decoded payload. Example: record 423 has raw first bytes:

```text
28 31 1a 03
```

Record 423 has `record_index & 3 == 3`, so those are cells 12..15:

```text
28 ^ ac = 84
31 ^ b5 = 84
1a ^ 9e = 84
03 ^ 87 = 84
```

So record 423 contributes decoded group byte `0x84`.

## Canonical Tails

Each image has a canonical unit tail. The unit size is 12 or 13 bytes, and the
operation key byte 4 is `2 * unit_size`:

```text
LD5M  op 0d6840031a00, N=13, tail b8b820171417141a77b83760
AD12  op 0c6000031800, N=12, tail cf6b016b016b00c8d60680
AHS9  op 0c6000031800, N=12, tail d33ac13ac13ac0c9560668
CD12  op 0d6840031a00, N=13, tail c6582018c818c810d1706780
CHS7  op 0d6840031a00, N=13, tail c07820180c180c0d15706740
CHS9  op 0d6840031a00, N=13, tail bef82017dc17dc0c3d706740
```

A full short record is four units:

```text
raw_cell_byte || canonical_tail
```

This full-row rule holds for 104/104 known short records across the six
DS-8ABSH sibling images.

## Long Records Contain Suffix Cells

The important new result is that the same `raw_cell_byte || canonical_tail`
motif appears at the ends of many longer records. These suffixes usually fill
the rightmost missing cells of the current row:

```text
row = record_index & 3
k = number of trailing canonical units
cell[j] = 4 * row + (4 - k + j)
```

Concrete CHS9 example:

```text
record 108 row 0 suffix raw bytes: fd d6 cf
cells 1,2,3:
fd ^ 19 = e4
d6 ^ 32 = e4
cf ^ 2b = e4

records 109..111 then supply cells 4..15
all 15 observations agree: group 27 = 0xe4
```

So at least some long records are partially statically decodable. The CDD is no
longer "all opaque until runtime"; it has a visible suffix-cell layer.

## Suffix-Key Correlations

The maintained analyzer found 115 long-record suffix observations:

```text
k=1: 49 records
k=2: 37 records
k=3: 29 records
```

The operation key has strong correlations, but it does not yet predict the
suffix count by itself:

- `op_key[5] == 0` for every suffix record.
- Excluding boundary group 96, `op_key[4]` is always the canonical doubled unit
  size: `0x18` for 12-byte units or `0x1a` for 13-byte units.
- Every non-boundary `k=2`/`k=3` suffix record has decoded-span field `0x30`
  from `(op_key[3] & 0x3f) << 4`.
- `k=1` suffix records have varied decoded-span fields and are almost always
  row 3 cells; the two exceptions are row 1.

That means the safe static rule is still evidence-driven: find literal
canonical unit tails and decode the cells they expose. Do not yet invent a
pure op-key formula for suffix length.

## Current Static Artifacts

The maintained analyzer is:

```sh
python3 scripts/analyze_liteon_cdd_affine_units.py
```

It writes:

```text
references/firmware/extracted/liteon-cdd-affine-unit-analysis.md
references/firmware/extracted/liteon-cdd-affine-unit-analysis.json
```

The broader CDD structural report now treats short records as full-row affine
cells and marks the record map as schema v3:

```text
references/firmware/extracted/liteon-cdd-stream-static-analysis.md
references/firmware/extracted/liteon-cdd-record-map.json
```

## Interpretation

This still does not identify a public format. The masks are familiar in the
sense that they form a small affine code over byte lanes, but the CDD container
does not look like LZ, Huffman, arithmetic coding, AES, or a named executable
packer. The encoded CDD bodies are much larger than the decoded/controller
range, so compression is unlikely to be the design goal.

The better model is now:

- proprietary controller-side packed/codeword format;
- a visible 16-cell affine byte layer for one canonical unit class;
- long records can include suffix cells from that same layer;
- hidden controller still owns the dense body grammar and final expansion.

One caution: this affine byte is proven structure, but its role is not fully
settled. It might be a semantic group byte, a parity/control byte for a
larger unit, or part of a controller codeword. The short-record decoded-span
field still says `0x30` bytes, so an oracle result for one known short record is
still the cleanest way to decide which parts become runtime bytes.

Next static target: use the suffix-key correlations to search for analogous
canonical tails in other unit classes, then test any candidate against sibling
shifted matches before promoting it to the decoder.
