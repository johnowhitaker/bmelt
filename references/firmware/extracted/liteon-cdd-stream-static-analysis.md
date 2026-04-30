# LiteOn CDD Stream Static Analysis

Offline only. No drive commands were sent.

## Images

| image | sha256 | CDD starts | family | trailer auth14 |
|---|---:|---:|---|---|
| LD5M | `488f49c7f5d8` | `0x0702c`, `0xd9000` | `U8A60D5C` | `4979c08a77386c1658483bf233fe` |
| AD12 | `17c8b50717b1` | `0x0702c`, `0xd9000` | `S8AB0D16` | `fe3ed5cbc2002a6eb5ae0dfb5d4a` |
| AHS9 | `e556dbed1132` | `0x0702c`, `0xd9000` | `S8AB0HS6` | `5084d8596db47bd5da64d01ad053` |
| CD12 | `c1848cb515c8` | `0x0702c`, `0xd9000` | `S8AB0D16` | `445c5e968b5f1fb80016fa3fdfc5` |
| CHS7 | `017b0f9c769e` | `0x0702c`, `0xd9000` | `S8AB0HS6` | `f817e214ed8b13729811dfb4c2f6` |
| CHS9 | `6f2552a0a4b9` | `0x0702c`, `0xd9000` | `S8AB0HS6` | `8061c6bb6c5f698b66425bb17dd7` |
| XD13 | `ebfb4902d401` | `0x08000` | `\xa8\x00"\x00\x00\x00\x00\x00` | `ffffffffffffffffffffffffffff` |

## CDD1 Grammar

| image | stream | dir end | entries | nominal 12-byte body | first source | nominal body len | nominal body len mod 12 | top sliding 12-byte motif | motif count | longest 13-stride run |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| LD5M | `0x0702c..0xcec18` | `0x07dec` | 436 | `0x11c0` | `0x1194` | `0xc6a2c` | 0 | `b8b820171417141a77b83760` | 73 | 15 |
| AD12 | `0x0702c..0xcfb67` | `0x07dec` | 436 | `0x11c0` | `0x11a4` | `0xc797b` | 7 | `e8e89fdfdb689fc0b2713f92` | 18 | 0 |
| AHS9 | `0x0702c..0xcfe20` | `0x07dec` | 436 | `0x11c0` | `0x1194` | `0xc7c34` | 8 | `f92111f3fb0711f03e4623e2` | 17 | 0 |
| CD12 | `0x0702c..0xced1c` | `0x07dec` | 436 | `0x11c0` | `0x119c` | `0xc6b30` | 8 | `c6582018c818c810d1706780` | 83 | 16 |
| CHS7 | `0x0702c..0xcedb4` | `0x07dec` | 436 | `0x11c0` | `0x1198` | `0xc6bc8` | 4 | `c07820180c180c0d15706740` | 84 | 15 |
| CHS9 | `0x0702c..0xcee2a` | `0x07dec` | 436 | `0x11c0` | `0x11a4` | `0xc6c3e` | 2 | `bef82017dc17dc0c3d706740` | 84 | 15 |

## Descriptor Logical Range And Size Ratios

The DS-8ABSH descriptor and CDD headers both point at controller/logical range `0x184000..0x1b4000`, length `0x30000`. That is the only decoded/runtime allocation that is currently explicit in the F0 image.

| image | descriptor | decoded range | CDD1 end | CDD2 end | final boundary |
|---|---:|---:|---:|---:|---:|
| LD5M | `0x07000..0x0702c` | `0x184000..0x1b4000` | `0xcec18` | `0xe6401` | `0xe8000` |
| AD12 | `0x07000..0x0702c` | `0x184000..0x1b4000` | `0xcfb67` | `0xe62ef` | `0xe8000` |
| AHS9 | `0x07000..0x0702c` | `0x184000..0x1b4000` | `0xcfe20` | `0xe636a` | `0xe8000` |
| CD12 | `0x07000..0x0702c` | `0x184000..0x1b4000` | `0xced1c` | `0xe6312` | `0xe8000` |
| CHS7 | `0x07000..0x0702c` | `0x184000..0x1b4000` | `0xcedb4` | `0xe6334` | `0xe8000` |
| CHS9 | `0x07000..0x0702c` | `0x184000..0x1b4000` | `0xcee2a` | `0xe6331` | `0xe8000` |

Relative to that explicit `0x30000` decoded range, the obvious encoded sizes are much larger than 1.4x. If the remembered ~1.4 factor is real, it is probably a smaller internal work allocation rather than the descriptor-level decoded CDD range.

| image | encoded measure | size | ratio to `0x30000` decoded range |
|---|---|---:|---:|
| LD5M | descriptor object | `0xe1000` | 4.6875 |
| LD5M | CDD streams | `0xd4fed` | 4.4374 |
| LD5M | CDD bodies | `0xd3cb9` | 4.4124 |
| LD5M | CDD1 source body | `0xc6a58` | 4.1385 |
| LD5M | CDD2 source body | `0xd261` | 0.2739 |
| LD5M | directory pointer span | `0xde04` | 0.2891 |
| LD5M | directory final pointer | `0xe620` | 0.2996 |
| LD5M | directory entry388 pointer | `0xd91a` | 0.2827 |
| AD12 | descriptor object | `0xe1000` | 4.6875 |
| AD12 | CDD streams | `0xd5e2a` | 4.4559 |
| AD12 | CDD bodies | `0xd4ae6` | 4.4309 |
| AD12 | CDD1 source body | `0xc7997` | 4.1583 |
| AD12 | CDD2 source body | `0xd14f` | 0.2725 |
| AD12 | directory pointer span | `0xddf2` | 0.2890 |
| AD12 | directory final pointer | `0xe60f` | 0.2996 |
| AD12 | directory entry388 pointer | `0xd91a` | 0.2827 |
| AHS9 | descriptor object | `0xe1000` | 4.6875 |
| AHS9 | CDD streams | `0xd615e` | 4.4601 |
| AHS9 | CDD bodies | `0xd4e2a` | 4.4351 |
| AHS9 | CDD1 source body | `0xc7c60` | 4.1619 |
| AHS9 | CDD2 source body | `0xd1ca` | 0.2732 |
| AHS9 | directory pointer span | `0xddfa` | 0.2890 |
| AHS9 | directory final pointer | `0xe616` | 0.2996 |
| AHS9 | directory entry388 pointer | `0xd91a` | 0.2827 |
| CD12 | descriptor object | `0xe1000` | 4.6875 |
| CD12 | CDD streams | `0xd5002` | 4.4375 |
| CD12 | CDD bodies | `0xd3cc6` | 4.4125 |
| CD12 | CDD1 source body | `0xc6b54` | 4.1398 |
| CD12 | CDD2 source body | `0xd172` | 0.2727 |
| CD12 | directory pointer span | `0xddf5` | 0.2890 |
| CD12 | directory final pointer | `0xe611` | 0.2996 |
| CD12 | directory entry388 pointer | `0xd91a` | 0.2827 |
| CHS7 | descriptor object | `0xe1000` | 4.6875 |
| CHS7 | CDD streams | `0xd50bc` | 4.4385 |
| CHS7 | CDD bodies | `0xd3d84` | 4.4134 |
| CHS7 | CDD1 source body | `0xc6bf0` | 4.1405 |
| CHS7 | CDD2 source body | `0xd194` | 0.2729 |
| CHS7 | directory pointer span | `0xddf7` | 0.2890 |
| CHS7 | directory final pointer | `0xe613` | 0.2996 |
| CHS7 | directory entry388 pointer | `0xd91a` | 0.2827 |
| CHS9 | descriptor object | `0xe1000` | 4.6875 |
| CHS9 | CDD streams | `0xd512f` | 4.4390 |
| CHS9 | CDD bodies | `0xd3deb` | 4.4140 |
| CHS9 | CDD1 source body | `0xc6c5a` | 4.1411 |
| CHS9 | CDD2 source body | `0xd191` | 0.2729 |
| CHS9 | directory pointer span | `0xddf6` | 0.2890 |
| CHS9 | directory final pointer | `0xe613` | 0.2996 |
| CHS9 | directory entry388 pointer | `0xd91a` | 0.2827 |

## Header Fields

The CDD stream header is mostly 24-bit big-endian fields. The repeated `0x1b3fff` value is inclusive, while the descriptor stores end+1 as `0x1b4000`. The `nominal table guess` column is the old interpretation of header byte `+0x10`; the directory source field below shows the real payload boundary is slightly earlier in CDD1 and much earlier in CDD2.

| image | stream2 start | directory end | control quad | nominal table guess | final boundary | descriptor | decoded start | decoded inclusive end |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LD5M | `0xd9000` | `0x07dec` | `0x03081087` | `0x400` | `0xe8000` | `0x07000` | `0x184000` | `0x1b3fff` |
| AD12 | `0xd9000` | `0x07dec` | `0x03101087` | `0x400` | `0xe8000` | `0x07000` | `0x184000` | `0x1b3fff` |
| AHS9 | `0xd9000` | `0x07dec` | `0x03080f87` | `0x400` | `0xe8000` | `0x07000` | `0x184000` | `0x1b3fff` |
| CD12 | `0xd9000` | `0x07dec` | `0x030c0f87` | `0x400` | `0xe8000` | `0x07000` | `0x184000` | `0x1b3fff` |
| CHS7 | `0xd9000` | `0x07dec` | `0x030a0f87` | `0x400` | `0xe8000` | `0x07000` | `0x184000` | `0x1b3fff` |
| CHS9 | `0xd9000` | `0x07dec` | `0x03100f87` | `0x400` | `0xe8000` | `0x07000` | `0x184000` | `0x1b3fff` |

## Directory Pointer Column

The final two bytes of each 8-byte CDD1 directory entry form a little-endian monotonically increasing value.

| image | first | entry 388 | last | monotonic | common diffs |
|---|---:|---:|---:|---:|---|
| LD5M | `0x081c` | `0xd91a` | `0xe620` | True | `0x93` x15, `0x96` x13, `0x8b` x10, `0x86` x10, `0x90` x10 |
| AD12 | `0x081d` | `0xd91a` | `0xe60f` | True | `0x3` x18, `0x93` x13, `0x9d` x12, `0x9b` x12, `0x88` x11 |
| AHS9 | `0x081c` | `0xd91a` | `0xe616` | True | `0x3` x16, `0x92` x14, `0x90` x12, `0x93` x11, `0x9b` x10 |
| CD12 | `0x081c` | `0xd91a` | `0xe611` | True | `0x3` x13, `0x9c` x11, `0x9f` x10, `0x8c` x10, `0x96` x10 |
| CHS7 | `0x081c` | `0xd91a` | `0xe613` | True | `0x92` x17, `0x3` x12, `0x9c` x11, `0x99` x11, `0x93` x11 |
| CHS9 | `0x081d` | `0xd91a` | `0xe613` | True | `0x92` x15, `0x3` x13, `0x88` x11, `0x93` x11, `0x9d` x10 |

## Directory Source Address Field

The directory pointer column now has a direct file-address interpretation:

```text
source_start = (u16le(entry[6:8]) << 4) | (entry[5] >> 4)
```

The resulting addresses are monotonic and land in the CDD payload regions. Entry 388 starts at `0xd91a0`, exactly after CDD2's copied directory prefix. This corrects the earlier CDD2 symmetry guess: despite the copied header byte that looks like a `0x400` table length, CDD2 appears to start source payload immediately after the copied entries.

| image | first source | entry 388 source | last source | final gap to CDD2 end | monotonic | common entry prefix | count | common short segment |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| LD5M | `0x081c0` | `0xd91a0` | `0xe6204` | `0x1fd` | True | `0d6840031a` | 16 | `0x34` x16 |
| AD12 | `0x081d0` | `0xd91a0` | `0xe60f2` | `0x1fd` | True | `0c60000318` | 18 | `0x30` x18 |
| AHS9 | `0x081c0` | `0xd91a0` | `0xe616d` | `0x1fd` | True | `0c60000318` | 16 | `0x30` x16 |
| CD12 | `0x081c8` | `0xd91a0` | `0xe6114` | `0x1fe` | True | `0d6840031a` | 18 | `0x34` x18 |
| CHS7 | `0x081c4` | `0xd91a0` | `0xe6136` | `0x1fe` | True | `0d6840031a` | 18 | `0x34` x18 |
| CHS9 | `0x081d0` | `0xd91a0` | `0xe6133` | `0x1fe` | True | `0d6840031a` | 18 | `0x34` x18 |

This is the strongest static CDD grammar clue so far. The small repeated-source templates such as `0d6840031a` and `0c60000318` point at short `0x34`/`0x30` byte spans, matching the visible motif islands. For these templates, byte 0 behaves like `N`, byte 1 is `8*N`, byte 4 is `2*N`, and the source span is `4*N`. That looks like an opcode/length tuple for a repeated packed-stream construct. The broader record format is still unresolved, but the records are no longer plausibly encrypted noise.

## Directory/Table Boundary

The source-address field gives a more precise payload boundary than the copied header bytes. CDD1 has a low-entropy table/control window after the directory, but its first source segment begins before the old nominal `directory + 0x400` boundary. CDD2 is different: after the copied header and copied entries, source payload begins immediately with no separate `0x400` table-like window.

| image | CDD1 directory end rel | CDD1 first source rel | CDD1 table/control len | nominal overlap | CDD1 table entropy | CDD1 table common u16 | CDD2 copied entries end | CDD2 first source rel |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| LD5M | `0xdc0` | `0x1194` | `0x3d4` | `0x2c` | 6.038 | `0x0d01` x16, `0x1503` x4, `0x1490` x4 | `0x1a0` | `0x1a0` |
| AD12 | `0xdc0` | `0x11a4` | `0x3e4` | `0x1c` | 6.052 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4 | `0x1a0` | `0x1a0` |
| AHS9 | `0xdc0` | `0x1194` | `0x3d4` | `0x2c` | 6.051 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4 | `0x1a0` | `0x1a0` |
| CD12 | `0xdc0` | `0x119c` | `0x3dc` | `0x24` | 6.051 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4 | `0x1a0` | `0x1a0` |
| CHS7 | `0xdc0` | `0x1198` | `0x3d8` | `0x28` | 6.059 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4 | `0x1a0` | `0x1a0` |
| CHS9 | `0xdc0` | `0x11a4` | `0x3e4` | `0x1c` | 6.053 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4 | `0x1a0` | `0x1a0` |

## CDD1 Table As Decoded Paragraph Offsets

Interpreting the CDD1 table/control window as little-endian 16-bit words gives another strong structural clue: every word, shifted left by four, lands inside the explicit decoded range length `0x30000`. This makes the table look like decoded-space paragraph address/control material rather than arbitrary aux bytes.

| image | table words | shifted offset range | low/mid/high bands | most common words |
|---|---:|---:|---|---|
| LD5M | 490 | `0x00060..0x1efe0` | low 355, mid 35, high 100 | `0x0d01` x16, `0x1503` x4, `0x1490` x4, `0x1502` x4, `0x1880` x2 |
| AD12 | 498 | `0x00060..0x1f080` | low 365, mid 37, high 96 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4, `0x1490` x4, `0x1502` x4 |
| AHS9 | 490 | `0x00060..0x1f060` | low 353, mid 41, high 96 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4, `0x1490` x4, `0x1502` x4 |
| CD12 | 494 | `0x00060..0x1f000` | low 359, mid 39, high 96 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4, `0x1490` x4, `0x1502` x4 |
| CHS7 | 492 | `0x00060..0x1f080` | low 356, mid 40, high 96 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4, `0x1490` x4, `0x1502` x4 |
| CHS9 | 498 | `0x00060..0x1f0e0` | low 365, mid 37, high 96 | `0x0d01` x16, `0x14e0` x4, `0x1503` x4, `0x1490` x4, `0x1502` x4 |

Splitting that table at word index 128 exposes two different-looking regions. The front `0x100` bytes carry the high/mid paragraph targets and the repeated `0x0d01`/`0x14e0`/`0x1503`/`0x1490`/`0x1502` runs, and those front words target later candidate decoded records. The remaining words are mostly low decoded offsets with no adjacent repeats, and they target the early decoded records. That makes the front look more like a vector/entrypoint/control table, while the tail looks more like a secondary offset list.

| image | front 128 words | front target records | remaining words | tail target records | long repeated runs in front table |
|---|---|---:|---|---:|---|
| LD5M | low 0, mid 28, high 100 | 118..281 | low 355, mid 7, high 0 | 0..98 | `0x0d01` x16 @16 -> rec 118+`0xf0`, `0x1503` x4 @52 -> rec 189+`0x90`, `0x1490` x4 @72 -> rec 186+`0x240`, `0x1502` x4 @124 -> rec 189+`0x80` |
| AD12 | low 0, mid 32, high 96 | 102..272 | low 365, mid 5, high 0 | 0..86 | `0x0d01` x16 @16 -> rec 102+`0xe0`, `0x14e0` x4 @4 -> rec 176+`0x50`, `0x1503` x4 @40 -> rec 178+`0x20`, `0x1490` x4 @80 -> rec 172+`0x10`, `0x1502` x4 @112 -> rec 178+`0x10` |
| AHS9 | low 0, mid 32, high 96 | 102..272 | low 353, mid 9, high 0 | 0..86 | `0x0d01` x16 @16 -> rec 102+`0x2c0`, `0x14e0` x4 @8 -> rec 180+`0x240`, `0x1503` x4 @40 -> rec 181+`0xc0`, `0x1490` x4 @80 -> rec 177+`0x60`, `0x1502` x4 @112 -> rec 181+`0xb0` |
| CD12 | low 0, mid 32, high 96 | 112..272 | low 359, mid 7, high 0 | 0..91 | `0x0d01` x16 @16 -> rec 112+`0x90`, `0x14e0` x4 @4 -> rec 181+`0x220`, `0x1503` x4 @40 -> rec 183+`0x0`, `0x1490` x4 @80 -> rec 180+`0xd0`, `0x1502` x4 @112 -> rec 182+`0x170` |
| CHS7 | low 0, mid 32, high 96 | 106..275 | low 356, mid 8, high 0 | 0..93 | `0x0d01` x16 @16 -> rec 106+`0x240`, `0x14e0` x4 @4 -> rec 182+`0x10`, `0x1503` x4 @40 -> rec 183+`0xb0`, `0x1490` x4 @80 -> rec 180+`0x190`, `0x1502` x4 @112 -> rec 183+`0xa0` |
| CHS9 | low 0, mid 32, high 96 | 105..276 | low 365, mid 5, high 0 | 0..93 | `0x0d01` x16 @16 -> rec 105+`0x130`, `0x14e0` x4 @4 -> rec 181+`0x2c0`, `0x1503` x4 @40 -> rec 183+`0x90`, `0x1490` x4 @80 -> rec 180+`0x170`, `0x1502` x4 @112 -> rec 183+`0x80` |

LD5M decoded/controller oracle shortlist for future runtime reads:

| decoded offset | controller address | reason | table index | target record+rel | source range | operation key |
|---:|---:|---|---:|---:|---:|---|
| `0x00000` | `0x184000` | decoded base / record 0 |  | 0+`0x0` | `0x081c0..0x08d32` | `ef7a96b5bc05` |
| `0x00060` | `0x184060` | minimum CDD1 table target | 471 | 0+`0x60` | `0x081c0..0x08d32` | `ef7a96b5bc05` |
| `0x0d010` | `0x191010` | `0x0d01` x16 repeated front-table target | 16 | 118+`0xf0` | `0x4670e..0x47065` | `03ba94a26604` |
| `0x14900` | `0x198900` | `0x1490` x4 front-table target | 72 | 186+`0x240` | `0x68949..0x692d7` | `cfe2537e9404` |
| `0x15030` | `0x199030` | `0x1503` x4 front-table target | 52 | 189+`0x90` | `0x6a15c..0x6a86c` | `7fd1d274c802` |
| `0x18020` | `0x19c020` | `0x1802` x2 front-table target | 50 | 222+`0x280` | `0x7a001..0x7a7ad` | `01eace6f1e04` |
| `0x18800` | `0x19c800` | `0x1880` x2 front-table target | 46 | 228+`0x120` | `0x7d029..0x7d962` | `8442127b0205` |
| `0x1c000` | `0x1a0000` | high front-table target | 112 | 258+`0x330` | `0x8e17c..0x8e92b` | `be01107a1204` |
| `0x1efe0` | `0x1a2fe0` | near-highest LD5M table target | 122 | 281+`0x340` | `0x9908b..0x999c3` | `fc11147e8405` |

Close sibling tables also line up by position. CHS7 and CHS9 have 189 identical same-index table words, including long equal runs, so this table is versioned data with stable structure.

| pair | table words | same-position equal | most common word deltas |
|---|---:|---:|---|
| CHS7 vs CHS9 | 492/498 | 189 | `+0x0` x189, `+0x2` x17, `+0x4` x10, `+0x6` x9, `-0x2` x7, `+0xa` x3 |
| AD12 vs CD12 | 498/494 | 82 | `+0x0` x82, `+0x8` x7, `+0x2` x7, `+0x6` x6, `+0x4` x5, `+0xa` x5 |
| LD5M vs CHS9 | 490/498 | 49 | `+0x0` x49, `-0x4` x6, `+0x2` x6, `+0xa` x5, `-0x6` x4, `+0x6` x4 |

Once the candidate decoded span field is applied, the table lines up even more tightly: every shifted table word falls inside one of the candidate decoded record intervals.

| image | table words in candidate intervals | misses | top target records | common in-record offsets |
|---|---:|---:|---|---|
| LD5M | 490/490 | 0 | `5` x62, `1` x51, `0` x40, `4` x28, `7` x28, `6` x23 | `0xf0` x26, `0x80` x17, `0x40` x16, `0x10` x15, `0x20` x15, `0x0` x15 |
| AD12 | 498/498 | 0 | `6` x55, `1` x49, `0` x40, `7` x37, `5` x31, `40` x19 | `0xe0` x29, `0x10` x20, `0x70` x18, `0x20` x17, `0xc0` x16, `0x80` x15 |
| AHS9 | 490/490 | 0 | `1` x50, `7` x47, `0` x41, `5` x37, `4` x21, `9` x19 | `0x2c0` x21, `0x40` x17, `0x60` x17, `0x20` x17, `0x90` x17, `0x70` x17 |
| CD12 | 494/494 | 0 | `1` x51, `7` x47, `0` x42, `5` x37, `6` x31, `4` x20 | `0x90` x29, `0xb0` x17, `0x10` x17, `0x50` x16, `0x0` x16, `0xd0` x16 |
| CHS7 | 492/492 | 0 | `1` x48, `0` x44, `6` x41, `5` x34, `7` x23, `8` x21 | `0x240` x21, `0x60` x20, `0xc0` x17, `0xb0` x17, `0xa0` x17, `0x30` x15 |
| CHS9 | 498/498 | 0 | `1` x49, `0` x43, `6` x41, `5` x34, `7` x24, `8` x21 | `0x130` x25, `0x50` x18, `0x170` x17, `0x10` x17, `0x90` x17, `0xb0` x17 |

LD5M source-segment mapping for useful probe offsets:

| offset | source entry | source range | candidate decoded start/span | entry bytes |
|---:|---:|---:|---:|---|
| `0x0704f` | none | outside source spans | | |
| `0x081ec` | 0 | `0x081c0..0x08d32` | `0x00000`/`0x350` | `ef7a96b5bc051c08` |
| `0x27d4f` | 58 | `0x27825..0x28119` | `0x06f50`/`0x220` | `66228ca200558227` |
| `0xd91a0` | 388 | `0xd91a0..0xd9adb` | `0x295a0`/`0x370` | `0dabd47774031ad9` |
| `0xd95a0` | 388 | `0xd91a0..0xd9adb` | `0x295a0`/`0x370` | `0dabd47774031ad9` |
| `0xe7fe0` | none | outside source spans | | |

## CDD2 Directory Duplicate

For DS-8ABSH-style images, stream2 bytes `0x20..0x1a0` duplicate stream1 bytes `0xc40..0xdc0`, i.e. CDD1 entries 388..435. Stream2 source payload starts at `0x1a0`, immediately after those copied entries.

| image | duplicate length | stream2 source body start | stream2 source body len |
|---|---:|---:|---:|
| LD5M | `0x180` | `0x1a0` | `0xd261` |
| AD12 | `0x180` | `0x1a0` | `0xd14f` |
| AHS9 | `0x180` | `0x1a0` | `0xd1ca` |
| CD12 | `0x180` | `0x1a0` | `0xd172` |
| CHS7 | `0x180` | `0x1a0` | `0xd194` |
| CHS9 | `0x180` | `0x1a0` | `0xd191` |

## Exact Shifted Body Matches: CHS7 vs CHS9

| length | left body rel | right body rel | shift | sample |
|---:|---:|---:|---:|---|
| 53 | `0x13d14` | `0x13cf8` | `-0x1c` | `17dae71ce0b4d63409790b0bc8d5c6ae3b70bdcb1cc4722f` |
| 53 | `0xc1e6` | `0xc1ca` | `-0x1c` | `9831c65b013108503e84cbbc9738e31c648fa1b3ca39c5a1` |
| 52 | `0x25dcc` | `0x25db2` | `-0x1a` | `0e15719718ee58927eaaab1b9453394a3b951995572616c0` |
| 51 | `0xb737` | `0xb71b` | `-0x1c` | `ea41ed651fe2ba06e4620cad713908c726f5c7c16eecf80d` |
| 50 | `0x146e4` | `0x146c8` | `-0x1c` | `0f127a07a85054fbbe102eac23858bbd60e8d34e3d720fce` |
| 47 | `0x58338` | `0x5836c` | `+0x34` | `a8357d41f6310656b637fd3768308d4494c27c348ce10fc9` |
| 46 | `0x5c956` | `0x5c98a` | `+0x34` | `371cd9bb177b1b072ba4aae601dbf1f434de3eccd67164a8` |
| 46 | `0x2a398` | `0x2a37e` | `-0x1a` | `8c894741912bf55aa392280fc20d4b352e9c997922ec3808` |

## Exact Shifted Body Matches: AD12 vs CD12

| length | left body rel | right body rel | shift | sample |
|---:|---:|---:|---:|---|

## Exact Shifted Body Matches: AHS9 vs CHS9

| length | left body rel | right body rel | shift | sample |
|---:|---:|---:|---:|---|

## Same-Index Source Segment Matches: CHS7 vs CHS9

CHS7 and CHS9 are close siblings. Their directory entries are mostly one or two bytes apart, and the source-address model lets us compare the same directory index as a semantic unit rather than searching the whole body blindly.

| entry | common prefix | left source | right source | lengths | entry byte diff | entries |
|---:|---:|---:|---:|---:|---:|---|
| 406 | 56 | `0xddb65` | `0xddb64` | `0x507`/`0x507` | 1 | `6d11cb4d0252b6dd` / `6d11cb4d0242b6dd` |
| 232 | 32 | `0x80214` | `0x80252` | `0x8af`/`0x8af` | 2 | `b012517dd0432180` / `b012517dd0232580` |
| 408 | 25 | `0xde681` | `0xde680` | `0x534`/`0x534` | 1 | `0b414657081468de` / `0b414657080468de` |
| 52 | 22 | `0x23a52` | `0x23a44` | `0x890`/`0x890` | 2 | `5f5a108edc23a523` / `5f5a108edc43a423` |
| 366 | 22 | `0xc3880` | `0xc38be` | `0x829`/`0x829` | 2 | `0c1294758a0388c3` / `0c1294758ae38bc3` |
| 124 | 21 | `0x49265` | `0x492a2` | `0x47d`/`0x47e` | 3 | `a6694453fa512649` / `a6698453fa212a49` |
| 199 | 17 | `0x6ea5d` | `0x6ea9c` | `0x74c`/`0x74c` | 2 | `5b420c63bad3a56e` / `5b420c63bac3a96e` |
| 316 | 15 | `0xac567` | `0xac5a2` | `0xa1e`/`0xa1e` | 2 | `dab2d2990e7556ac` / `dab2d2990e255aac` |

## Operation Fields Versus Source Fields

The source-address formula splits byte 5: the high nibble is the source low nibble, while the low nibble stays with the non-source record fields. Treating `entry[0:5] + (entry[5] & 0x0f)` as an operation key makes the close-sibling comparison much cleaner.

| pair | exact same entry | same operation key | same-op equal source length | source-only changes | common source deltas |
|---|---:|---:|---:|---:|---|
| CHS7 vs CHS9 | 3 | 380 | 380 | 377 | `-0x3b` x74, `-0x3e` x56, `-0x40` x52, `+0xe` x39, `-0x3f` x33, `+0x10` x30 |
| AD12 vs CD12 | 0 | 7 | 7 | 7 | `-0x13` x2, `-0x19` x2, `-0x21` x2, `+0xf48` x1 |
| AHS9 vs CHS9 | 0 | 2 | 2 | 2 | `+0xc` x1, `+0x3a` x1 |

For CHS7 vs CHS9, 380 of 436 records keep the same operation key; all 380 also keep the same source-segment length, and 377 differ only in the source-address bits. That is strong evidence that the directory entry is not opaque: `entry[0:5]` plus byte5 low nibble likely describes the packed operation/output contract, while byte5 high nibble and bytes 6-7 are the source-address field.

Example CHS7/CHS9 source-only differences:

| entry | source delta | lengths | entries |
|---:|---:|---:|---|
| 14 | `+0xe` | `0x94d`/`0x94d` | `753a11b3ca03f610` / `753a11b3ca23f510` |
| 15 | `+0xe` | `0x34`/`0x34` | `0d6840031ad08a11` / `0d6840031af08911` |
| 16 | `+0xe` | `0x726`/`0x726` | `26b20c698c138e11` / `26b20c698c338d11` |
| 17 | `+0xe` | `0x530`/`0x530` | `e279c73ae8720012` / `e279c73ae892ff11` |
| 18 | `+0xe` | `0x6a0`/`0x6a0` | `5e810d5f2c745312` / `5e810d5f2c945212` |
| 20 | `+0x10` | `0x734`/`0x734` | `cb01d083b4e25c13` / `cb01d083b4e25b13` |

## Operation Key Source-Length Invariant

Across these DS-8ABSH samples, `2135` unique operation keys appear. None map to more than one source-span length (`0` inconsistent keys). That makes the operation key a deterministic source-length descriptor, even though the full field grammar is not solved.

| operation key | count | source length | indices | images |
|---|---:|---:|---|---|
| `0d6840031a00` | 70 | `0x34` x70 | 15, 51, 109, 110, 111, 206, 207, 279, 312, 313, ... | CD12, CHS7, CHS9, LD5M |
| `0c6000031800` | 34 | `0x30` x34 | 109, 110, 111, 279, 312, 313, 314, 315, 327, 337, ... | AD12, AHS9 |
| `5f884219a000` | 4 | `0x165` x4 | 401 | AD12, AHS9, CHS7, CHS9 |
| `72014b6a0204` | 3 | `0x67c` x3 | 357 | CD12, CHS7, CHS9 |
| `6629cb56de02` | 3 | `0x595` x3 | 434 | AHS9, CHS7, CHS9 |
| `86784e616203` | 3 | `0x58b` x3 | 137 | CD12, CHS7, CHS9 |
| `fc4188493802` | 3 | `0x546` x3 | 404 | CD12, CHS7, CHS9 |
| `50b14d3de001` | 3 | `0x4eb` x3 | 392 | CD12, CHS7, CHS9 |
| `559841137c00` | 3 | `0x113` x3 | 425 | AD12, AHS9, CD12 |
| `e002dbb69e05` | 2 | `0xbea` x2 | 76 | CHS7, CHS9 |
| `cf6a57b5b205` | 2 | `0xb6a` x2 | 294 | CHS7, CHS9 |
| `232317c51404` | 2 | `0xb25` x2 | 3 | CHS7, CHS9 |

A partial length field also falls out of the operation key:

```text
length_base = u16le(operation_key[2:4]) >> 4
```

This equals the source-span length for `106` records. For the rest it is a length-ish base with a structured residual, so bytes 2..3 are probably part of the length coding rather than the complete source-length field.

| residual (`source_len - length_base`) | count |
|---:|---:|
| `+0x0` | 106 |
| `+0x6` | 13 |
| `+0xad` | 12 |
| `+0x15` | 10 |
| `-0xc9` | 10 |
| `+0x1a` | 9 |
| `-0x67` | 9 |
| `-0x5a` | 9 |
| `-0x71` | 9 |
| `-0x89` | 9 |
| `+0x1d` | 8 |
| `-0x4` | 8 |

## Candidate Decoded Span Field

A second length-like field appears in operation-key byte 3. The candidate decoded/output span is:

```text
decoded_span = (operation_key[3] & 0x3f) << 4
```

This is not a full CDD decoder, but it is the first field that lands near the explicit `0x30000` decoded/controller range instead of the much larger encoded source length.

| image | candidate decoded span | delta from `0x30000` | CDD1 entries | CDD2 entries | encoded source / candidate decoded |
|---|---:|---:|---:|---:|---:|
| LD5M | `0x2e3b0` | `-0x1c50` | `0x295a0` | `0x04e10` | 4.581x |
| AD12 | `0x2fc20` | `-0x3e0` | `0x2aac0` | `0x05160` | 4.453x |
| AHS9 | `0x30720` | `+0x720` | `0x2b530` | `0x051f0` | 4.394x |
| CD12 | `0x2fe50` | `-0x1b0` | `0x2acc0` | `0x05190` | 4.422x |
| CHS7 | `0x30350` | `+0x350` | `0x2b1d0` | `0x05180` | 4.394x |
| CHS9 | `0x2ffd0` | `-0x30` | `0x2ae50` | `0x05180` | 4.415x |

The close siblings keep this field aligned in long same-operation runs. For CHS7 vs CHS9, cumulative decoded offsets have piecewise constant deltas across same-operation records, which is what we would expect from a versioned decoded address stream.

| pair | longest same-op decoded-offset runs |
|---|---|
| CHS7 vs CHS9 | `252..325` len 74 delta `+0x10`, `136..187` len 52 delta `+0x20`, `51..84` len 34 delta `-0x20`, `20..49` len 30 delta `-0x20`, `348..375` len 28 delta `+0x10`, `413..435` len 23 delta `-0x380` |
| AD12 vs CD12 | `430..431` len 2 delta `+0x230`, `424..425` len 2 delta `+0x230`, `417..417` len 1 delta `+0x220`, `415..415` len 1 delta `+0x210`, `384..384` len 1 delta `+0x240` |

This field also lands on the two visible short-operation islands. `0d6840031a00` consumes four 13-byte source units (`0x34` bytes total), while `0c6000031800` consumes four 12-byte source units (`0x30` bytes total); both claim candidate decoded span `0x30`. The first byte of each unit is not discardable padding: across every known short record it is one cell of a 16-cell affine group code.

The high two bits of the same operation-key byte look like mode flags. They split the stream into different redundancy classes rather than changing the decoded-span unit.

| mode bits (`operation_key[3] & 0xc0`) | records | encoded source | decoded span candidate | encoded / decoded | zero-span records | common byte5 flags |
|---:|---:|---:|---:|---:|---:|---|
| `0x00` | 272 | `0x26e80` | `0x13ad0` | 1.977x | 0 | `0x0` x211, `0x1` x32, `0x2` x24, `0x3` x2, `0x4` x2, `0x5` x1 |
| `0x40` | 812 | `0x160cdc` | `0x73810` | 3.054x | 13 | `0x4` x255, `0x3` x225, `0x2` x191, `0x5` x61, `0x1` x50, `0x0` x27 |
| `0x80` | 1510 | `0x361d94` | `0x96c50` | 5.743x | 21 | `0x4` x737, `0x5` x463, `0x3` x177, `0x2` x79, `0x0` x22, `0x1` x22 |
| `0xc0` | 22 | `0xf50e` | `0x930` | 26.673x | 3 | `0x6` x10, `0x4` x5, `0x5` x4, `0x3` x3 |

## Short Operation Source Units

The two high-frequency short operations expose a small regular source format. In both cases byte 0 of the operation key is the source unit length, byte 1 is `8 * unit_len`, byte 4 is `2 * unit_len`, and each record source span is `4 * unit_len`.

The byte-0 sequence now has a stronger interpretation: `104/104` short records decode under `mask[cell] = carryless_mul8(0x19, cell)`, with `cell = 4 * (record_index & 3) + unit_index`. Across shared groups, `10/10` groups keep a single decoded byte across the sibling set.

This corrects the earlier parity-only and row-local `m` interpretations. The profile-specific unit tails still look like scaffolding or controller coding material, but byte 0 is a coded observation of a group byte.

| operation key | image | records | unit len | source span | decoded span candidate | units | constant unit tail | first-byte samples |
|---|---|---:|---:|---:|---:|---:|---|---|
| `0d6840031a00` | CD12 | 18 | `0xd` | `0x34` | `0x30` | 72 | `c6582018c818c810d1706780` | `0x7e` x2, `0x67` x2, `0x4c` x2, `0x55` x2, `0x80` x1, `0x99` x1, `0xb2` x1, `0xab` x1 |
| `0d6840031a00` | CHS7 | 18 | `0xd` | `0x34` | `0x30` | 72 | `c07820180c180c0d15706740` | `0x7e` x2, `0x67` x2, `0x4c` x2, `0x55` x2, `0xb7` x1, `0xae` x1, `0x85` x1, `0x9c` x1 |
| `0d6840031a00` | CHS9 | 18 | `0xd` | `0x34` | `0x30` | 72 | `bef82017dc17dc0c3d706740` | `0x7e` x2, `0x67` x2, `0x4c` x2, `0x55` x2, `0xb7` x1, `0xae` x1, `0x85` x1, `0x9c` x1 |
| `0d6840031a00` | LD5M | 16 | `0xd` | `0x34` | `0x30` | 64 | `b8b820171417141a77b83760` | `0x94` x2, `0x8d` x2, `0xa6` x2, `0xbf` x2, `0x80` x1, `0x99` x1, `0xb2` x1, `0xab` x1 |
| `0c6000031800` | AD12 | 18 | `0xc` | `0x30` | `0x30` | 72 | `cf6b016b016b00c8d60680` | `0x94` x2, `0x8d` x2, `0xa6` x2, `0xbf` x2, `0x80` x1, `0x99` x1, `0xb2` x1, `0xab` x1 |
| `0c6000031800` | AHS9 | 16 | `0xc` | `0x30` | `0x30` | 64 | `d33ac13ac13ac0c9560668` | `0x80` x1, `0x99` x1, `0xb2` x1, `0xab` x1, `0x2c` x1, `0x35` x1, `0x1e` x1, `0x07` x1 |

Representative short-record decoded group bytes:

| image | record count | `group:plain` values |
|---|---:|---|
| LD5M | 16 | `27:0xe4`, `51:0xbe`, `69:0x38`, `78:0x17`, `81:0x15`, `99:0x0a`, `105:0x84` |
| AD12 | 18 | `27:0xe4`, `69:0x38`, `78:0x17`, `81:0x15`, `84:0x52`, `99:0x0a`, `105:0x84` |
| AHS9 | 16 | `27:0xe4`, `78:0x17`, `81:0x15`, `84:0x52`, `99:0x0a`, `105:0x84` |
| CD12 | 18 | `3:0xd2`, `27:0xe4`, `78:0x17`, `81:0x15`, `84:0x52`, `99:0x0a`, `105:0x84` |
| CHS7 | 18 | `3:0xd2`, `12:0x1b`, `27:0xe4`, `78:0x17`, `81:0x15`, `84:0x52`, `99:0x0a`, `105:0x84` |
| CHS9 | 18 | `3:0xd2`, `12:0x1b`, `27:0xe4`, `78:0x17`, `81:0x15`, `84:0x52`, `99:0x0a`, `105:0x84` |

Shared-group examples:

| group | plain | cells | raw byte sequence | images |
|---:|---:|---|---|---|
| 105 | `0x84` | `4,5,6,7` | `e0 f9 d2 cb` | AD12, AHS9, CD12, CHS7, CHS9, LD5M |
| 99 | `0x0a` | `4,5,6,7` | `6e 77 5c 45` | AD12, AHS9, CD12, CHS7, CHS9, LD5M |
| 81 | `0x15` | `12,13,14,15` | `b9 a0 8b 92` | AD12, AHS9, CD12, CHS7, CHS9, LD5M |
| 78 | `0x17` | `4,5,6,7` | `73 6a 41 58` | AD12, AHS9, CD12, CHS7, CHS9, LD5M |
| 27 | `0xe4` | `4,5,6,7` | `80 99 b2 ab` | AD12, AHS9, CD12, CHS7, CHS9, LD5M |
| 84 | `0x52` | `4,5,6,7` | `36 2f 04 1d` | AD12, AHS9, CD12, CHS7, CHS9 |

Longer records also carry matching canonical unit tails as suffix cells. See `liteon-cdd-affine-unit-analysis.md` for the multi-image suffix-cell decode.

## Simple Decode/Compression Probes

These are sanity probes, not proof that no transform exists. They rule out the cheap cases: a global one-byte XOR/add/sub mask, obvious text-bearing transform, and standard compression headers at useful rates.

Best printable score over the first `0x20000` bytes of LD5M CDD1 body:

| transform | best key | printable fraction |
|---|---:|---:|
| xor | `0x80` | 0.4039 |
| add | `0x80` | 0.4039 |
| sub | `0x80` | 0.4039 |

Common compression magic counts across the full LD5M CDD1 body:

| magic | count |
|---|---:|
| zlib 78 01 | 5 |
| zlib 78 5e | 5 |
| zlib 78 9c | 10 |
| zlib 78 da | 120 |
| gzip | 21 |
| bzip2 | 0 |
| xz | 0 |

Zlib decompression successes from those LD5M CDD1 body magic-looking offsets: `0`.

The body also contains sliding/13-stride motif runs and cross-sibling exact matches that are not aligned like AES-ECB blocks. That makes generic block-cipher brute force a poor fit: the useful attack surface is probably the CDD record grammar, not a blind key search.

## Interpretation

This still does not give us a decoded controller firmware image. It does narrow the static picture:

- The updater materializes a sealed F0 container, not decoded CDD runtime bytes.
- The visible descriptor/header decoded range is `0x30000`, but the encoded CDD object is roughly 4.4x larger; the remembered ~1.4 factor is not present at this level.
- The directory and aux table are plainly structured, so treating CDD as one encrypted blob is probably the wrong mental model.
- A blind brute-force decrypt is not realistic without a known algorithm/key/plaintext target. The more promising static route is to reverse the 8-byte directory records, then use sibling shifted matches as anchors.

Best next hybrid test, once live work resumes: sample a few normal-boot decoded/controller bytes around `0x184000`, `0x18481c`, and `0x19191a`. If those bytes resemble CDD directory/body material we get a mapping; if they are a third representation, static decode probably needs that runtime oracle.
