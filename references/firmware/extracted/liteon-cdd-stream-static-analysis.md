# LiteOn CDD Stream Static Analysis

Offline-only checkpoint. No drive commands were sent.

## Inputs

The sibling comparison set is local in ignored scratch space at
`work/cdd-siblings/`:

- `AD12-1.bin`
- `AHS9-postprocess-plain.bin`
- `CD12-postprocess-plain.bin`
- `CHS7-postprocess-plain.bin`
- `CHS9-postprocess-plain.bin`
- `XD13-postprocess-plain.bin`

The reusable analyzer is `scripts/analyze_liteon_cdd_streams.py`.

## Main Findings

The LD5M `0x11c0` CDD1 body start now has a concrete explanation. For all
DS-8ABSH-style images, CDD1 is:

| region | stream-relative range | notes |
|---|---:|---|
| CDD header | `0x0000..0x001f` | starts with `43 44 44 09 10 16`; contains absolute directory end `0x7dec` |
| directory | `0x0020..0x0dbf` | 436 records, 8 bytes each |
| aux/table window | `0x0dc0..0x11bf` | 0x400 bytes; low entropy, mostly 16-bit-looking values |
| CDD1 body | `0x11c0..stream_end` | high entropy body with recurring motifs |

CDD2 reuses the tail of CDD1's directory:

- CDD2 bytes `0x20..0x1a0` match CDD1 bytes `0xc40..0xdc0`.
- That is CDD1 entries 388..435, 48 entries total.
- With the same 0x400 aux/table window rule, CDD2's inferred body starts at
  stream-relative `0x5a0`.

The final two bytes of every 8-byte CDD1 directory entry form a
little-endian, monotonically increasing value. For LD5M:

- entry 0: `0x081c`
- entry 388: `0xd91a`
- entry 435: `0xe620`

The same entry 388 value appears across all DS-8ABSH samples. This looks much
more like a real offset/index column than random encrypted record material.

CHS7 and CHS9 make the directory structure especially visible. They have only
three byte-identical full entries, but column-wise they are overwhelmingly
similar:

| column | identical entries, CHS7 vs CHS9 |
|---:|---:|
| 0 | 402 / 436 |
| 1 | 406 / 436 |
| 2 | 401 / 436 |
| 3 | 416 / 436 |
| 4 | 403 / 436 |
| 5 | 92 / 436 |
| 6 | 63 / 436 |
| 7 | 434 / 436 |

That is another strike against "the directory is encrypted." It is structured
metadata, with columns 5 and 6 carrying the most version-specific movement.

## Motifs

The repeated LD5M motif remains real:

`b8 b8 20 17 14 17 14 1a 77 b8 37 60`

It occurs 73 times in CDD1 and 26 times in CDD2. Other siblings have
image-specific motifs with the same general "template plus one changing byte"
behavior. Examples:

| image | top CDD1 sliding 12-byte motif | count |
|---|---|---:|
| LD5M | `b8b820171417141a77b83760` | 73 |
| CD12 | `c6582018c818c810d1706780` | 83 |
| CHS7 | `c07820180c180c0d15706740` | 84 |
| CHS9 | `bef82017dc17dc0c3d706740` | 84 |

The "13th byte" in the long runs is probably not a parity byte over the
preceding 12-byte motif. The strongest counterexample is that matched sibling
runs often have the same varying byte sequence while the repeated 12-byte
motif differs by image. That is more consistent with an instruction/data
template where one field varies than with a checksum over the motif bytes.

The original "CDD1 body is exactly 67801 * 12 bytes" observation is true for
LD5M, but it is not universal. The sibling CDD1 body lengths after `0x11c0`
are not all divisible by 12, so 12-byte units are not a global stream grammar.
The motifs are sliding byte patterns, not reliably aligned 12-byte records.

## What This Says About "Decrypting" CDD

This does not look like one uniformly encrypted blob:

- the CDD header is plain and directly parsed by the 8051;
- the directory has at least one clear monotonic offset/index column;
- the 0x400 window has low entropy and 16-bit-table structure;
- the body has repeated sliding templates and long 13-stride runs.

It also does not look like plain ARM/8051 code. The body entropy is very high,
there are no useful strings, and the 8051 loader appears to configure the
controller-side CDD machinery rather than decode the body locally.

Working model: CDD is a controller-specific packed/program/data format. The
8051 validates the header, prepares XDATA `0x4a00`/`0x4a10`/`0x4a20` state, and
hands ranges to the controller. The actual transformation into the runtime
controller address space is probably controller-side.

## Immediate Next Static Leads

1. Continue parsing the 8-byte directory format. The final little-endian word
   is the first firm field; the first six bytes likely contain flags, lengths,
   or encoded source/destination metadata.

2. Use CHS7 vs CHS9 shifted exact runs as alignment anchors. They share exact
   body runs up to 53 bytes with shifts like `-0x10` and `+0x40`, which is
   useful for distinguishing code/data movement from per-image encoding.

3. When live work resumes, take a tiny decoded-memory sample through the
   controller gateway at the descriptor address `0x184000`, plus offsets
   implied by the directory column such as `0x18481c` and `0x19191a`. A few
   dozen decoded bytes would tell us whether the runtime image resembles the
   aux table, body bytes, or a third representation.

4. If the Pico/LED channel becomes reliable, prioritize reading decoded CDD
   memory over continuing blind XDATA register sweeps. The static CDD format
   now gives much better target addresses for those reads.
