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

| image | stream | dir end | entries | aux len | body start | body len | body len mod 12 | top sliding 12-byte motif | motif count | longest 13-stride run |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|
| LD5M | `0x0702c..0xcec18` | `0x07dec` | 436 | `0x400` | `0x11c0` | `0xc6a2c` | 0 | `b8b820171417141a77b83760` | 73 | 15 |
| AD12 | `0x0702c..0xcfb67` | `0x07dec` | 436 | `0x400` | `0x11c0` | `0xc797b` | 7 | `e8e89fdfdb689fc0b2713f92` | 18 | 0 |
| AHS9 | `0x0702c..0xcfe20` | `0x07dec` | 436 | `0x400` | `0x11c0` | `0xc7c34` | 8 | `f92111f3fb0711f03e4623e2` | 17 | 0 |
| CD12 | `0x0702c..0xced1c` | `0x07dec` | 436 | `0x400` | `0x11c0` | `0xc6b30` | 8 | `c6582018c818c810d1706780` | 83 | 16 |
| CHS7 | `0x0702c..0xcedb4` | `0x07dec` | 436 | `0x400` | `0x11c0` | `0xc6bc8` | 4 | `c07820180c180c0d15706740` | 84 | 15 |
| CHS9 | `0x0702c..0xcee2a` | `0x07dec` | 436 | `0x400` | `0x11c0` | `0xc6c3e` | 2 | `bef82017dc17dc0c3d706740` | 84 | 15 |

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
| LD5M | CDD bodies | `0xd388d` | 4.4070 |
| LD5M | CDD1 body | `0xc6a2c` | 4.1382 |
| LD5M | CDD2 inferred body | `0xce61` | 0.2687 |
| LD5M | directory pointer span | `0xde04` | 0.2891 |
| LD5M | directory final pointer | `0xe620` | 0.2996 |
| LD5M | directory entry388 pointer | `0xd91a` | 0.2827 |
| AD12 | descriptor object | `0xe1000` | 4.6875 |
| AD12 | CDD streams | `0xd5e2a` | 4.4559 |
| AD12 | CDD bodies | `0xd46ca` | 4.4255 |
| AD12 | CDD1 body | `0xc797b` | 4.1582 |
| AD12 | CDD2 inferred body | `0xcd4f` | 0.2673 |
| AD12 | directory pointer span | `0xddf2` | 0.2890 |
| AD12 | directory final pointer | `0xe60f` | 0.2996 |
| AD12 | directory entry388 pointer | `0xd91a` | 0.2827 |
| AHS9 | descriptor object | `0xe1000` | 4.6875 |
| AHS9 | CDD streams | `0xd615e` | 4.4601 |
| AHS9 | CDD bodies | `0xd49fe` | 4.4297 |
| AHS9 | CDD1 body | `0xc7c34` | 4.1617 |
| AHS9 | CDD2 inferred body | `0xcdca` | 0.2680 |
| AHS9 | directory pointer span | `0xddfa` | 0.2890 |
| AHS9 | directory final pointer | `0xe616` | 0.2996 |
| AHS9 | directory entry388 pointer | `0xd91a` | 0.2827 |
| CD12 | descriptor object | `0xe1000` | 4.6875 |
| CD12 | CDD streams | `0xd5002` | 4.4375 |
| CD12 | CDD bodies | `0xd38a2` | 4.4071 |
| CD12 | CDD1 body | `0xc6b30` | 4.1396 |
| CD12 | CDD2 inferred body | `0xcd72` | 0.2675 |
| CD12 | directory pointer span | `0xddf5` | 0.2890 |
| CD12 | directory final pointer | `0xe611` | 0.2996 |
| CD12 | directory entry388 pointer | `0xd91a` | 0.2827 |
| CHS7 | descriptor object | `0xe1000` | 4.6875 |
| CHS7 | CDD streams | `0xd50bc` | 4.4385 |
| CHS7 | CDD bodies | `0xd395c` | 4.4080 |
| CHS7 | CDD1 body | `0xc6bc8` | 4.1403 |
| CHS7 | CDD2 inferred body | `0xcd94` | 0.2677 |
| CHS7 | directory pointer span | `0xddf7` | 0.2890 |
| CHS7 | directory final pointer | `0xe613` | 0.2996 |
| CHS7 | directory entry388 pointer | `0xd91a` | 0.2827 |
| CHS9 | descriptor object | `0xe1000` | 4.6875 |
| CHS9 | CDD streams | `0xd512f` | 4.4390 |
| CHS9 | CDD bodies | `0xd39cf` | 4.4086 |
| CHS9 | CDD1 body | `0xc6c3e` | 4.1409 |
| CHS9 | CDD2 inferred body | `0xcd91` | 0.2677 |
| CHS9 | directory pointer span | `0xddf6` | 0.2890 |
| CHS9 | directory final pointer | `0xe613` | 0.2996 |
| CHS9 | directory entry388 pointer | `0xd91a` | 0.2827 |

## Header Fields

The CDD stream header is mostly 24-bit big-endian fields. The repeated `0x1b3fff` value is inclusive, while the descriptor stores end+1 as `0x1b4000`.

| image | stream2 start | directory end | control quad | aux len | final boundary | descriptor | decoded start | decoded inclusive end |
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

The resulting addresses are monotonic and land in the CDD payload/aux regions. Entry 388 starts at `0xd91a0`, exactly after CDD2's copied directory prefix and before its inferred `0x400` aux window.

| image | first source | entry 388 source | last source | final gap to CDD2 end | monotonic | common entry prefix | count | common short segment |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| LD5M | `0x081c0` | `0xd91a0` | `0xe6204` | `0x1fd` | True | `0d6840031a` | 16 | `0x34` x16 |
| AD12 | `0x081d0` | `0xd91a0` | `0xe60f2` | `0x1fd` | True | `0c60000318` | 18 | `0x30` x18 |
| AHS9 | `0x081c0` | `0xd91a0` | `0xe616d` | `0x1fd` | True | `0c60000318` | 16 | `0x30` x16 |
| CD12 | `0x081c8` | `0xd91a0` | `0xe6114` | `0x1fe` | True | `0d6840031a` | 18 | `0x34` x18 |
| CHS7 | `0x081c4` | `0xd91a0` | `0xe6136` | `0x1fe` | True | `0d6840031a` | 18 | `0x34` x18 |
| CHS9 | `0x081d0` | `0xd91a0` | `0xe6133` | `0x1fe` | True | `0d6840031a` | 18 | `0x34` x18 |

This is the strongest static CDD grammar clue so far. The small repeated-source templates such as `0d6840031a` and `0c60000318` point at short `0x34`/`0x30` byte spans, matching the visible motif islands. That makes the 8-byte records look like a real packed-stream directory rather than encrypted noise.

LD5M source-segment mapping for useful probe offsets:

| offset | source entry | source range | entry bytes |
|---:|---:|---:|---|
| `0x0704f` | none | outside source spans | |
| `0x081ec` | 0 | `0x081c0..0x08d32` | `ef7a96b5bc051c08` |
| `0x27d4f` | 58 | `0x27825..0x28119` | `66228ca200558227` |
| `0xd91a0` | 388 | `0xd91a0..0xd9adb` | `0dabd47774031ad9` |
| `0xd95a0` | 388 | `0xd91a0..0xd9adb` | `0dabd47774031ad9` |
| `0xe7fe0` | none | outside source spans | |

## CDD2 Directory Duplicate

For DS-8ABSH-style images, stream2 bytes `0x20..0x1a0` duplicate stream1 bytes `0xc40..0xdc0`, i.e. CDD1 entries 388..435.

| image | duplicate length | stream2 inferred body start | stream2 body len |
|---|---:|---:|---:|
| LD5M | `0x180` | `0x5a0` | `0xce61` |
| AD12 | `0x180` | `0x5a0` | `0xcd4f` |
| AHS9 | `0x180` | `0x5a0` | `0xcdca` |
| CD12 | `0x180` | `0x5a0` | `0xcd72` |
| CHS7 | `0x180` | `0x5a0` | `0xcd94` |
| CHS9 | `0x180` | `0x5a0` | `0xcd91` |

## Exact Shifted Body Matches: CHS7 vs CHS9

| length | left body rel | right body rel | shift | sample |
|---:|---:|---:|---:|---|
| 53 | `0x13cec` | `0x13cdc` | `-0x10` | `17dae71ce0b4d63409790b0bc8d5c6ae3b70bdcb1cc4722f` |
| 53 | `0xc1be` | `0xc1ae` | `-0x10` | `9831c65b013108503e84cbbc9738e31c648fa1b3ca39c5a1` |
| 52 | `0x25da4` | `0x25d96` | `-0xe` | `0e15719718ee58927eaaab1b9453394a3b951995572616c0` |
| 51 | `0xb70f` | `0xb6ff` | `-0x10` | `ea41ed651fe2ba06e4620cad713908c726f5c7c16eecf80d` |
| 50 | `0x146bc` | `0x146ac` | `-0x10` | `0f127a07a85054fbbe102eac23858bbd60e8d34e3d720fce` |
| 47 | `0x58310` | `0x58350` | `+0x40` | `a8357d41f6310656b637fd3768308d4494c27c348ce10fc9` |
| 46 | `0x5c92e` | `0x5c96e` | `+0x40` | `371cd9bb177b1b072ba4aae601dbf1f434de3eccd67164a8` |
| 46 | `0x2a370` | `0x2a362` | `-0xe` | `8c894741912bf55aa392280fc20d4b352e9c997922ec3808` |

## Exact Shifted Body Matches: AD12 vs CD12

| length | left body rel | right body rel | shift | sample |
|---:|---:|---:|---:|---|

## Exact Shifted Body Matches: AHS9 vs CHS9

| length | left body rel | right body rel | shift | sample |
|---:|---:|---:|---:|---|

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
