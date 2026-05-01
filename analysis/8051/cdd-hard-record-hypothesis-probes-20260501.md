# CDD Hard-Record Hypothesis Probes

Date: 2026-05-01

Offline only. No drive commands were sent.

This report tests a few concrete hypotheses for the high-coverage
CDD records that now have normal-mode known-output exports.

## DVD-Format Size Clue

The hard-record source lengths cluster around byte counts used by DVD
formatting before modulation: 2048-byte main data, 2064-byte data
frames, and especially 2366-byte recording frames. ECMA-267 describes
recording frames as 13 rows of 182 bytes, i.e. 2366 bytes, before
8-to-16 modulation.

Reference: <https://ecma-international.org/publications-and-standards/standards/Ecma-267/>

| mode | key5 | records | median source | near 2048 | near 2064 | near 2366 |
| --- | --- | --- | --- | --- | --- | --- |
| `0x00` | `0x0` | 211 | 61 | 0 | 0 | 0 |
| `0x00` | `0x1` | 32 | 908 | 0 | 0 | 0 |
| `0x00` | `0x2` | 24 | 1099 | 0 | 0 | 0 |
| `0x40` | `0x0` | 27 | 1673 | 0 | 0 | 0 |
| `0x40` | `0x1` | 50 | 1260 | 0 | 0 | 0 |
| `0x40` | `0x2` | 191 | 1418 | 6 | 6 | 0 |
| `0x40` | `0x3` | 225 | 1827 | 38 | 26 | 14 |
| `0x40` | `0x4` | 255 | 2034 | 88 | 98 | 27 |
| `0x40` | `0x5` | 61 | 2267 | 19 | 16 | 27 |
| `0x80` | `0x0` | 22 | 2092 | 13 | 15 | 1 |
| `0x80` | `0x1` | 22 | 2152 | 7 | 8 | 3 |
| `0x80` | `0x2` | 79 | 2156 | 12 | 18 | 13 |
| `0x80` | `0x3` | 177 | 2143 | 54 | 53 | 42 |
| `0x80` | `0x4` | 737 | 2338 | 64 | 80 | 241 |
| `0x80` | `0x5` | 463 | 2529 | 10 | 10 | 88 |
| `0x80` | `0x6` | 10 | 2732 | 0 | 0 | 0 |
| `0xc0` | `0x4` | 5 | 2880 | 0 | 0 | 0 |
| `0xc0` | `0x6` | 10 | 3020 | 0 | 0 | 0 |

This is not proof that CDD is DVD sector data. It is a strong hint that
the controller designers may be reusing optical/ECC-style block sizes
or hardware datapaths.

## 12-Record Schedule Check

The previously observed affine leaf schedule repeats every 12 records.
That is interesting because DVD ECC/recording-frame construction also
has a 12-row cadence before parity interleaving. The LD5M source
lengths are not perfectly periodic, but the first three positions in
each 12-record group are much more often near 2366 bytes, and position
3 is a low-source-length/control-heavy lane.

| pos mod 12 | records | median source | near 2366 | top modes | top key5 |
| --- | --- | --- | --- | --- | --- |
| 0 | 37 | 2291 | 13 | `0x80`:24, `0x40`:11, `0x00`:2 | `0x4`:15, `0x5`:11, `0x3`:8 |
| 1 | 37 | 2355 | 13 | `0x80`:27, `0x40`:5, `0x00`:5 | `0x4`:15, `0x5`:13, `0x0`:5 |
| 2 | 37 | 2422 | 11 | `0x80`:26, `0x00`:5, `0x40`:5 | `0x5`:15, `0x4`:13, `0x0`:5 |
| 3 | 37 | 1327 | 3 | `0x00`:20, `0x80`:12, `0x40`:4 | `0x0`:23, `0x1`:5, `0x3`:3 |
| 4 | 36 | 1982 | 4 | `0x40`:17, `0x80`:16, `0x00`:2 | `0x3`:12, `0x4`:9, `0x2`:7 |
| 5 | 36 | 1944 | 5 | `0x40`:18, `0x80`:13, `0x00`:4 | `0x4`:16, `0x3`:7, `0x2`:5 |
| 6 | 36 | 1968 | 4 | `0x40`:20, `0x80`:14, `0x00`:2 | `0x4`:14, `0x5`:9, `0x3`:7 |
| 7 | 36 | 2156 | 9 | `0x80`:19, `0x40`:15, `0x00`:2 | `0x4`:21, `0x2`:5, `0x5`:4 |
| 8 | 36 | 2104 | 5 | `0x80`:20, `0x40`:14, `0x00`:2 | `0x4`:16, `0x3`:9, `0x2`:6 |
| 9 | 36 | 2150 | 6 | `0x80`:23, `0x40`:11, `0x00`:2 | `0x4`:18, `0x5`:6, `0x3`:6 |
| 10 | 36 | 2211 | 9 | `0x80`:25, `0x40`:11 | `0x4`:17, `0x5`:8, `0x3`:6 |
| 11 | 36 | 2248 | 5 | `0x80`:28, `0x40`:7, `0xc0`:1 | `0x4`:18, `0x5`:9, `0x3`:4 |

This makes the DVD-like angle more worth testing, but still only as an
analogy or reused-hardware hypothesis. CDD record counts and decoded
spans do not directly match a vanilla DVD ECC block.

## RLL/EFMPlus-Like Channel-Bit Test

If the encoded CDD source were already post-modulation channel bits, its
bitstream should strongly satisfy the DVD RLL(2,10) constraint. It does
not. The best raw/inverted/MSB/LSB/NRZI-derived view still has large
run-length violation fractions, close to random data.

| record | source | known | best view | RLL violations | min/max run |
| --- | --- | --- | --- | --- | --- |
| 87 | 1947 | 896 | `msb,inv,raw` | 73% | 0/13 |
| 51 | 2326 | 800 | `msb,inv,raw` | 73% | 0/11 |
| 55 | 2313 | 768 | `msb,inv,raw` | 73% | 0/12 |
| 66 | 2411 | 704 | `msb,inv,raw` | 73% | 0/12 |
| 60 | 2344 | 624 | `msb,inv,raw` | 74% | 0/12 |
| 68 | 2421 | 528 | `msb,inv,raw` | 73% | 0/11 |
| 88 | 1965 | 512 | `msb,inv,raw` | 73% | 0/11 |
| 58 | 2292 | 496 | `msb,inv,raw` | 75% | 0/13 |
| 70 | 2525 | 448 | `msb,inv,raw` | 73% | 0/12 |
| 50 | 2499 | 432 | `lsb,inv,raw` | 74% | 0/14 |
| 64 | 1604 | 336 | `msb,inv,raw` | 74% | 0/10 |
| 65 | 1844 | 320 | `msb,norm,nrzi_derivative` | 75% | 0/11 |
| 67 | 2295 | 272 | `msb,inv,raw` | 73% | 0/13 |
| 49 | 2033 | 256 | `msb,inv,raw` | 74% | 0/11 |
| 85 | 2238 | 256 | `msb,inv,raw` | 74% | 0/12 |
| 62 | 2419 | 224 | `msb,inv,raw` | 73% | 0/12 |

So the CDD source is not simply packed EFMPlus/channel data. If the DVD
size clue matters, it is more likely pre-modulation scrambled/ECC-ish
record material or a custom format inspired by those hardware blocks.

## Sparse Systematic-Byte Probe

I also tested simple monotonic byte projections of the form
`source[floor(i * numerator / denominator) + phase]`, with identity,
NOT, bit-reversed, and bit-reversed-NOT transforms. These stay at
random-looking match rates.

| record | byte eq | lo nibble | hi nibble | bit eq | best transform |
| --- | --- | --- | --- | --- | --- |
| 87 | 1.2% | 6.9% | 6.1% | 50.4% | `bitrev 649/1008 phase -10` |
| 51 | 1.4% | 5.8% | 7.8% | 51.2% | `bitrev 1163/816 phase -12` |
| 55 | 1.3% | 7.9% | 6.6% | 51.2% | `bitrev_not 2314/896 phase 27` |
| 66 | 1.4% | 6.2% | 8.5% | 51.5% | `bitrev_not 1607/720 phase 61` |
| 60 | 2.2% | 7.1% | 7.9% | 51.5% | `not 781/848 phase -39` |
| 68 | 1.7% | 7.8% | 7.4% | 50.7% | `not 1210/640 phase -60` |
| 88 | 1.4% | 6.5% | 6.9% | 49.3% | `bitrev_not 1964/688 phase 11` |
| 58 | 1.8% | 6.5% | 8.5% | 50.8% | `not 2291/544 phase -41` |
| 70 | 1.8% | 6.5% | 8.7% | 50.3% | `id 841/560 phase 26` |
| 50 | 2.3% | 7.0% | 8.6% | 51.4% | `bitrev_not 2499/496 phase 30` |
| 64 | 2.0% | 10.5% | 7.4% | 51.1% | `bitrev_not 1604/688 phase 18` |
| 65 | 2.6% | 10.9% | 8.3% | 52.3% | `bitrev_not 1845/544 phase -61` |
| 67 | 2.9% | 8.2% | 9.1% | 51.6% | `bitrev_not 1530/656 phase 4` |
| 49 | 2.0% | 6.0% | 9.6% | 51.2% | `bitrev 2033/448 phase 33` |
| 85 | 3.0% | 11.1% | 5.1% | 50.6% | `bitrev 746/768 phase -28` |
| 62 | 3.1% | 12.5% | 5.2% | 53.3% | `bitrev_not 806/464 phase -5` |

## Current Read

- The hard records are not lightly scrambled byte streams.
- They are not already post-modulation EFMPlus/RLL channel bits.
- Their source lengths are suspiciously close to DVD-style
  pre-modulation/ECC frame sizes, especially around 2366 bytes.
- `key5` correlates strongly with source-length class, so it likely
  participates in selecting code rate/redundancy/block layout.
- The next static test worth doing is not another broad XOR scan. It is
  a targeted implementation of DVD-like scrambling/ECC/interleave
  hypotheses, compared against high-coverage records' masked known
  outputs.

Record 87 remains the cleanest first target for generic hard-record
transform work because its known-output export has high coverage and no
slot variants. For the DVD-size clue specifically, records closer to the
2366-byte source length, such as 51, 55, 60, 66, and 68, are the better
cross-checks even though they have more public-slot ambiguity.

