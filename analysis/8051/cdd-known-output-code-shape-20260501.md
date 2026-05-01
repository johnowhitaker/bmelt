# CDD Known-Output Code Shape

Date: 2026-05-01

The normal work-window harvest has become more useful than a slow byte oracle.
By pairing host-visible `0x40`-byte tiles with CDD record buckets, then looking
at which tiles repeat next to each other, we can assemble partial per-record
known-output images. These are not complete decoded CDD records, but many of
them disassemble cleanly as 8051.

## New Artifacts

- `analysis/8051/cdd-tile-adjacency-with-readonly-harvests-20260501.md/json`
  records tile adjacency across 669 normal work-window captures.
- `analysis/8051/cdd-known-output-records-20260501.md` summarizes exported
  per-record known-output kits.
- `analysis/8051/cdd-known-output-records-20260501/record-XXX-encoded-source.bin`
  is the encoded source span from LD5M F0.
- `analysis/8051/cdd-known-output-records-20260501/record-XXX-known-output.bin`
  is the public-slot consensus decoded-looking output.
- `analysis/8051/cdd-known-output-records-20260501/record-XXX-known-mask.bin`
  marks known bytes with `0xff`.
- `analysis/8051/cdd-known-output-records-20260501/record-XXX-slots.json`
  records slot variants and examples.
- `analysis/8051/cdd-known-output-records-20260501/record-XXX-r2-8051.asm`
  is a radare2 8051 disassembly snippet for the strongest records.

## The Practical Surprise

The strongest per-record exports are large enough to be useful:

| record | mode | op key | source | decoded span | known output |
|---:|---:|---|---:|---:|---:|
| 87 | `0x40` | `0af2177f2e01` | 1947 | 1008 | 896 bytes, 89% |
| 51 | `0x80` | `a98252b3a002` | 2326 | 816 | 800 bytes, 98% |
| 55 | `0x40` | `a742d3782e04` | 2313 | 896 | 768 bytes, 86% |
| 66 | `0x80` | `4e8210adb204` | 2411 | 720 | 704 bytes, 98% |
| 60 | `0x40` | `950a90757805` | 2344 | 848 | 624 bytes, 74% |
| 68 | `0x80` | `0fe212a8d404` | 2421 | 640 | 528 bytes, 82% |
| 58 | `0x80` | `66228ca20005` | 2292 | 544 | 496 bytes, 91% |
| 70 | `0x80` | `098ad4a36805` | 2525 | 560 | 448 bytes, 80% |

Several of these consensus outputs are contiguous known ranges with very little
unknown material. Record 87 has a clean `0x20..0x3a0` known range. Record 51 is
known from `0x10` to the end. Record 66 is known from `0x10` to the end.

## 8051 Shape

These known-output bins disassemble as plausible 8051, not random decoded
bytes. Examples:

- Record 87 starts its known range with `02 bf 37` (`LJMP 0xbf37`) and then
  touches packet/status XDATA such as `0x852e`, `0x855d`, `0x830e`, `0x8988`,
  and `0x8a49`.
- Record 51 repeatedly writes the `0x47b1` packet/FIFO port and uses packet
  shadow addresses around `0x8a4d`, `0x89a4`, `0x8ae4`, and `0x89ca`. This
  looks like response generation or packet-side plumbing.
- Record 55 combines packet shadows with controller gateway reads from
  `0x4000` and `0x4098`.
- Record 66 uses controller setup/status addresses including `0x4097`,
  `0x4000`, `0x40b5`, `0x40b6`, `0x40b7`, and packet shadow `0x8a54`.
- Record 70 contains repeated controller read-gateway sequences through
  `0x4091`, `0x4000`, and `0x4098`.

This answers one earlier uncertainty: at least part of the CDD decoded material
is 8051-side code or 8051-executable overlay material. The CDD streams may
still contain controller/servo payloads too, but they are not opaque
non-8051-only blobs.

## Adjacency Result

The tile-adjacency pass scanned 669 captured windows:

- adjacent known-chunk observations: `11146`
- same-record slot observations: `8850`
- unique raw edges: `114`
- unique same-record slot edges: `95`

The strongest local neighborhoods are records 68, 66, 70, 60, 64, 59, 55, and
58. This gives us compact record-level targets for CDD grammar work. Instead of
trying to decode the whole CDD stream at once, we can now ask:

1. Given one encoded source record and a mostly known decoded output record,
   what operation does this record mode/key perform?
2. Do records sharing mode `0x40` or `0x80` obey the same transform once known
   output positions are masked?
3. Are the slot variants real branches/dynamic overlays, or artifacts of public
   work-window rotation?

## Current Interpretation

The CDD body still does not look like a simple XOR, NOT, bit-reverse, or
constant-byte transform. But the normal-mode work-window has given us a more
direct attack surface: mostly decoded 8051 overlays paired with their encoded
record sources.

The most promising next static task is a per-record grammar attack against
records 87, 51, 66, 58, and 70. Record 87 is especially attractive because it
has high coverage and no slot variants in the current export. Records 51, 66,
58, and 70 are attractive because they touch packet/controller machinery that
matters for host-visible I/O.

## Caution

The known-output binaries are public-slot consensus artifacts. They are strong
evidence for local decoded neighborhoods, but they should not be treated as a
flat decoded CDD image. Public offsets rotate. Exact placement still needs a
better address/phase model or a live oracle check.
