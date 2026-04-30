# CDD / Gateway Known-Plaintext Check

Date: 2026-04-30

This note follows up on the question: could the 8051-looking code in the
`controller[0x070000..0x07ffff]` currentboot gateway dump be decoded CDD output,
giving us a known-plaintext pair for the CDD format?

## Inputs

```text
gateway dump:
  references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin

LD5M F0:
  references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin

visible 8051:
  analysis/8051/ldm58051.bin

CDD record model:
  references/firmware/extracted/liteon-cdd-record-map.json
```

## Result

There are real exact 8051-code overlaps in the gateway dump, but the cleanest
interpretation is **not** yet "we found decoded CDD2 as 8051 code".

The gateway dump is a mixed currentboot/controller work area:

- it contains exact resident/helper 8051 code fragments;
- it contains raw encoded CDD container bytes;
- it contains tables, strings, and currentboot/profile state;
- it is not a single clean decoded CDD image.

## The Tempting Candidate

The first suspicious observation was that CDD record 116's candidate decoded
range lines up with an exact visible-resident 8051 snippet:

```text
CDD rec 116
candidate decoded/gateway range: 0xcc40..0xcc80
encoded CDD source range:        F0 0x4538b..0x45c69
operation key:                   5b2252845c04
mode:                            0x80
decoded span candidate:          0x40
source length:                   0x8de

gateway 0xcc40..0xcc80 == visible resident 0x1a1b..0x1a5b
```

That is a valid known-output window if the CDD decoded-span model maps directly
onto this gateway workspace.

## The Important Correction

The rec-116 match is not an independent record-boundary hit. It is the middle
of a larger exact resident-code run:

```text
gateway 0xcc03..0xcc98 == visible resident 0x19de..0x1a73
```

That larger run crosses the modeled CDD record boundaries:

```text
rec 115: 0xcbe0..0xcc40
rec 116: 0xcc40..0xcc80
rec 117: 0xcc80..0xcf20
```

So the rec-116 "perfect match" is still useful, but it is not proof that a
single CDD record decoded exactly to that resident snippet. It may just be a
resident code copy that happens to cross the candidate record grid.

## Boundary Check

Exact resident-code match starts in the gateway dump do not cluster at CDD
record boundaries:

```text
resident/code matches in gateway 0x4000..0xffff, length >= 0x20: 22
starts within 0 bytes of a candidate CDD boundary:  0
starts within 4 bytes of a candidate CDD boundary:  0
starts within 16 bytes of a candidate CDD boundary: 0
```

That weakens the direct decoded-CDD interpretation.

## Strong Code Overlap Windows

These gateway intervals have substantial exact overlap with visible resident
8051 code and also lie inside candidate CDD decoded spans:

```text
rec 117 gw 0xcc80..0xcf20, source 0x45c69..0x4670e
  exact resident coverage: 0x16c
  op=ba82d5aa2005 mode=0x80

rec 132 gw 0xe810..0xeb60, source 0x4e367..0x4ec6d
  exact resident coverage: 0x144
  op=558a0fb5d803 mode=0x80

rec 120 gw 0xd2c0..0xd510, source 0x47a04..0x483b4
  exact resident coverage: 0x12f
  op=df5194a56205 mode=0x80

rec 116 gw 0xcc40..0xcc80, source 0x4538b..0x45c69
  exact resident coverage: 0x40
  op=5b2252845c04 mode=0x80
```

These remain useful as candidate known-output windows, but they should be
treated as "gateway contains resident code at CDD-modeled offsets", not
"confirmed CDD decode output".

## Raw CDD Mirror Windows

The same gateway dump also contains raw encoded CDD bytes. These are exact
byte-for-byte F0 CDD container material, not decoded output:

```text
gateway 0xf000..0xfda0 == F0 0x704c..0x7deb  (CDD1 post-header table)
gateway 0xfc20..0xfda0 == F0 0xd9020..0xd919f (CDD2 duplicate prefix)
gateway 0xff00..0xff20 == CDD header
gateway 0xff80..0xffa0 == CDD header
```

This is the strongest reason to call the gateway dump a work area rather than a
decoded CDD image.

## Simple Transform Checks

For rec 116:

```text
encoded source length: 0x8de
candidate output length: 0x40
```

Quick checks did not find:

- the output as an exact subsequence of the source;
- a simple stride extraction;
- a fixed XOR or fixed add transform on a stride;
- obvious direct plaintext bytes embedded in the source.

The source is high-entropy and uses the full byte range. If this is a CDD
decode pair, mode `0x80` is doing a high-redundancy/controller-specific
transform, not a trivial unpacking.

The same is true for the larger neighboring code-overlap candidates:

```text
rec 115 source entropy: 7.84,  source len 0x507, decoded span 0x060
rec 116 source entropy: 7.90,  source len 0x8de, decoded span 0x040
rec 117 source entropy: 7.91,  source len 0xaa5, decoded span 0x2a0
rec 120 source entropy: 7.90,  source len 0x9b0, decoded span 0x250
rec 132 source entropy: 7.89,  source len 0x906, decoded span 0x350
```

None of those mode `0x40`/`0x80` candidate source spans has the low-entropy
13-byte motif lane structure. Their 12/13/16-byte autocorrelation is near
random.

That contrasts strongly with the known motif records:

```text
rec 397 op=0d6840031a00
source len 0x34, decoded span 0x30, entropy ~3.1
13-byte autocorrelation: ~0.923
source shape: four repeated 12-byte motif units plus one varying byte per unit
```

So the CDD record grammar is probably multi-mode:

- some mode `0x00` short records are visibly structured 13-byte codeword runs;
- the gateway/resident-code overlap candidates are high-entropy mode
  `0x40`/`0x80` records with no obvious lane structure.

This makes the resident-code overlaps less likely to yield a cheap decode rule
by themselves. They may still be known-output pairs for the hard mode, but they
are not the easy motif mode.

Follow-up with the peer static notes corrected the interpretation of the short
records. The visible shape is very concrete, but the semantic byte is the
varying first byte, not the repeated tail.

```text
source length: 0x34 = 4 * 13
decoded span:  0x30 = 4 * 12

each 13-byte source unit:
  <varying byte> b8 b8 20 17 14 17 14 1a 77 b8 37 60
```

All 16 LD5M records with operation key `0d6840031a00` have this same shape.
The four first bytes in each record obey:

```text
v0 = m
v1 = m ^ 0x19
v2 = m ^ 0x32
v3 = m ^ 0x2b
```

This holds for 104/104 short records across LD5M, AD12, AHS9, CD12, CHS7, and
CHS9 when including the related `0c6000031800` form. The `m` byte is stable by
record index across sibling images. Examples:

```text
record 109: m=80 across all six images
record 110: m=2c across all six images
record 111: m=48 across all six images
record 397: m=6e across all six images
record 423: m=28 across all six images
```

So the previous "drop byte 0" observation should be treated only as a way to
isolate the fixed scaffold. It is not a semantic decoder. The semantic/control
payload currently known for these short records is the single `m` byte encoded
redundantly in the first byte of each unit.

The close sibling versions show a related but not identical easy-mode shape:
AD12/AHS9 use operation key `0c6000031800` at corresponding places, with
source length `0x30` and decoded span `0x30`. Their records are four 12-byte
units, each beginning with the same varying byte sequence seen in LD5M's
13-byte units, followed by an image-specific 11-byte tail. Operation byte
`0x0c` vs `0x0d` likely changes the unit width/scaffold convention, while the
four-way XOR coding of `m` stays the same.

The stable `m` values also show a second-level XOR row in consecutive
short-record runs:

```text
base^0x00, base^0x64, base^0xc8, base^0xac
```

For example, records 312..315 decode to `m = 17 73 df bb`, exactly
`0x17 ^ {00,64,c8,ac}`. Records 109..111, 337..339, 397..399, and 421..423
fit contiguous three-value slices of the same row. This suggests the short
records may be arranged in small interleaved/codeword groups, not just isolated
one-byte literals.

This also means the candidate `decoded_span=0x30` is not yet proven to mean
"48 bytes of ordinary plaintext" for these records. It may be a logical
address-space allocation, controller codeword footprint, or scaffolded control
cell rather than a literal uncompressed byte count.

## Sibling Cross-Check

The same resident code snippets exist in sibling visible prefixes, often at a
different offset:

```text
LD5M  resident run 0x19de..0x1a73 appears at LD5M prefix 0x19de
AD12/AHS9/CD12/CHS7/CHS9: same bytes appear at prefix 0x0969
XD13: no exact hit for this run
```

Meanwhile the same-index CDD records differ substantially across siblings in
decoded span, operation key, and source length. That does not disprove the CDD
known-output idea, but it means same-index record comparison will need to track
semantic code movement and not assume fixed output offsets.

## Current Interpretation

The gateway dump likely contains copied resident/helper routines and copied raw
CDD work buffers in the same controller window. The CDD record decoded-span
model still gives useful coordinate labels inside this window, but the
resident-code islands do not yet prove that CDD records are decoding into those
bytes.

The practical next static path is:

1. Treat `gateway 0xcc03..0xcc98` and neighboring resident-code islands as
   candidate known-output windows, not confirmed decoded records.
2. Search for a second independent artifact where a CDD source span maps to a
   contiguous output span with boundary agreement.
3. Use sibling images to ask whether the same operation-key classes produce
   code-like output in comparable gateway/decoded offsets.
4. Keep the raw `0xf000` CDD mirror separate from decoded-output hypotheses.
