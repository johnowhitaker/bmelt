# Currentboot Gateway 0x070000 Analysis

Date: 2026-04-30

This is an offline analysis of the 64 KiB controller-gateway dump read
from Linux drive #1 while the drive was in currentboot. No live drive
access is performed by this report generator.

## Artifact

```text
path   references/evidence/live/normal-read-buffer-work-window-20260501/id01-070000-010000.bin
base   0x070000
size   0x10000
sha256 c3cd6e6d3e25a55e54d779a0f71965e93315290ab44537df4f0b6393c0e840e7
```

## Main Read

This 64 KiB window is mixed material, not a plain reset-vector firmware
image. The low pages contain compact tables/records and `PBDS` markers,
`0x02ea..0x3fff` is zero, `0x4000..0x5fff` is string/profile/table-heavy,
and `0x6000..0xffff` contains substantial 8051-like code mixed with tables.

The most important new finding is that the tail of this gateway window
contains exact LD5M CDD bytes. In particular, the dump at gateway offset
`0xf000` mirrors F0 bytes starting at `0x704c`, the first post-header
CDD1 directory/table material. This is not decoded servo code; it is the
sealed/encoded CDD container material visible in F0. The same window also
contains the expected duplicate of the CDD2 prefix and repeated CDD headers.

So the gateway is a better live oracle than the earlier zero `0x184000`
guess, but it is not yet the decoded `0x184000..0x1b3fff` runtime payload.

## Normal Overlay READ BUFFER Clue

The normal-mode work/code dump explains why `READ BUFFER id=f2` works even
though the visible F0-prefix handler at `FUN_CODE_385c` does not accept it.
There is an alternate READ BUFFER-like check at dump offset `+0x6747`:

```text
0x6747  mov dptr,#8a4a
0x674a  movx a,@dptr
0x674b  cjne a,#01,...      ; byte looks like READ BUFFER mode
0x674e  inc dptr
0x674f  movx a,@dptr        ; byte looks like buffer ID
0x6751  xrl a,#01
0x6756  xrl a,#02
0x675b  xrl a,#e2
0x6760  xrl a,#f0
0x6765  xrl a,#f2
0x676a  xrl a,#f1
```

So the normal runtime has a CDB shadow around `xdata[0x8a49..]`, distinct from
the F0-prefix/currentboot shadow at `xdata[0x818a..]`, and its handler accepts
`0xf2`. A nearby branch at `+0x6848` dispatches special cases for `f0`, `f1`,
`f2`, and `e2`; that path is a better static target than `FUN_CODE_385c` for
understanding exact-`0x80` `f2` behavior.

The special-ID branch currently reads as:

```text
id f0  -> +0x68aa
id f1  -> +0xa2b1
id f2  -> +0xa2f0  ; appears to trampoline toward code/data around +0xd7b8
id e2  -> +0x6863
other  -> +0xa32a
```

The `+0xa2xx` area is a dense trampoline/table region, so these are not clean
function starts yet. Still, this is the first static anchor for the observed
normal-mode `f2` responder.

## Page Shape

| page | nonzero | non-ff | entropy | note |
|---:|---:|---:|---:|---|
| `0x0000` | 595 | 4096 | 1.3699 | low table/record area |
| `0x1000` | 0 | 4096 | -0.0000 | all zero |
| `0x2000` | 0 | 4096 | -0.0000 | all zero |
| `0x3000` | 0 | 4096 | -0.0000 | all zero |
| `0x4000` | 3967 | 690 | 1.6837 | profile/string/table area |
| `0x5000` | 1316 | 3171 | 1.7817 | profile/string/table area |
| `0x6000` | 4012 | 4031 | 6.6733 | code-like/table mixed |
| `0x7000` | 4041 | 4036 | 6.5669 | code-like/table mixed |
| `0x8000` | 4011 | 4023 | 6.6240 | code-like/table mixed |
| `0x9000` | 4039 | 4012 | 6.6086 | code-like/table mixed |
| `0xa000` | 4059 | 4083 | 5.6282 | code-like/table mixed |
| `0xb000` | 4093 | 4086 | 5.3377 | code-like/table mixed |
| `0xc000` | 4078 | 4064 | 6.2036 | code-like/table mixed |
| `0xd000` | 3731 | 4050 | 6.7902 | code-like/table mixed |
| `0xe000` | 4022 | 4018 | 6.7048 | code-like/table mixed |
| `0xf000` | 3529 | 4087 | 7.2622 | CDD mirror/header tail |

Long zero/ff runs:

```text
00 0x02b0..0x3fff len=0x3d50
ff 0x4519..0x46cc len=0x1b4
ff 0x46d2..0x4885 len=0x1b4
ff 0x488b..0x4a3e len=0x1b4
ff 0x4a44..0x4bf4 len=0x1b1
00 0x5860..0x5c00 len=0x3a1
ff 0x5ccc..0x5e07 len=0x13c
ff 0x5e09..0x5f9f len=0x197
00 0xdebe..0xe000 len=0x143
00 0xfda0..0xfeff len=0x160
```

## CDD Overlap

| item | F0 source | gateway hit(s) | length |
|---|---:|---:|---:|
| CDD1 post-header prefix | `0x0704c` | `0xf000` | `0xda0` |
| CDD2 duplicate prefix | `0xd9020` | `0xfc20` | `0x180` |
| CDD header | `0x0702c` | `0xff00, 0xff80` | `0x20` |

The `0xf000` CDD1 hit runs exactly through F0 `0x704c..0x7deb`.
The `0xfc20` CDD2-prefix hit is contained inside that CDD1 region,
matching the known CDD2-prefix duplicate inside CDD1. The repeated
headers at `0xff00` and `0xff80` look like controller-side CDD work
slots or copied descriptors, not decoded output.

## Exact Overlaps

Nontrivial exact byte matches against known artifacts:

### profile_tail_helper

| len | gateway | other | sample |
|---:|---:|---:|---|
| `0x2d` | `0xd508` | `0x081b` | `d083d082f8e4937012740193700da3a3` |

### ldm58051_resident

| len | gateway | other | sample |
|---:|---:|---:|---|
| `0xcf` | `0xd211` | `0x1c98` | `2275f008758200ef2fffee33fecd33cd` |
| `0x95` | `0xcc03` | `0x19de` | `e9cdf9eafeebffef89f0a4fce5f0ce89` |
| `0x8a` | `0xd028` | `0x1c0f` | `22f8bb010de58229f582e5833af583e8` |
| `0x65` | `0xe8dd` | `0x15de` | `22904e0fe4f022904e107401f022904e` |
| `0x5b` | `0xe755` | `0x1456` | `904e16e0b401047f0180607f00805c90` |
| `0x57` | `0xcde3` | `0x1b40` | `ec334010ef33ffee33feed33fdec33fc` |
| `0x55` | `0xe1ab` | `0x10d1` | `8042904a81e064016007904a89e0b401` |
| `0x53` | `0xd4e2` | `0x1e4d` | `d083d082f8e4937012740193700da3a3` |
| `0x4b` | `0xd2ec` | `0x1d66` | `22c3e49fffe49efee49dfde49cfc22eb` |
| `0x4a` | `0xce3c` | `0x1b99` | `e9d2e7c933e833f892d5edd2e7cd33ec` |
| `0x48` | `0xe97e` | `0x175c` | `904ea0e0ff22904ebae0ff904eb9f022` |
| `0x42` | `0xdb95` | `0x517a` | `e47e019360bca3ff543f30e509541ffe` |

### ld5m_f0

| len | gateway | other | sample |
|---:|---:|---:|---|
| `0xda0` | `0xf000` | `0x00704c` | `ef7a96b5bc051c08ddd2d6b79625d308` |
| `0x180` | `0xfc20` | `0x0d9020` | `0dabd47774031ad990694a4808b2add9` |
| `0xcf` | `0xd211` | `0x001c98` | `2275f008758200ef2fffee33fecd33cd` |
| `0x95` | `0xcc03` | `0x0019de` | `e9cdf9eafeebffef89f0a4fce5f0ce89` |
| `0x8a` | `0xd028` | `0x001c0f` | `22f8bb010de58229f582e5833af583e8` |
| `0x65` | `0xe8dd` | `0x0015de` | `22904e0fe4f022904e107401f022904e` |
| `0x5b` | `0xe755` | `0x001456` | `904e16e0b401047f0180607f00805c90` |
| `0x57` | `0xcde3` | `0x001b40` | `ec334010ef33ffee33feed33fdec33fc` |
| `0x55` | `0xe1ab` | `0x0010d1` | `8042904a81e064016007904a89e0b401` |
| `0x53` | `0xd4e2` | `0x001e4d` | `d083d082f8e4937012740193700da3a3` |
| `0x4b` | `0xd2ec` | `0x001d66` | `22c3e49fffe49efee49dfde49cfc22eb` |
| `0x4a` | `0xce3c` | `0x001b99` | `e9d2e7c933e833f892d5edd2e7cd33ec` |

## Direct Register References

These are linear `MOV DPTR,#imm16` sightings. They are useful waypoints,
not proof of valid function boundaries because the image mixes code and data.

| addr | count | first gateway offsets | label |
|---:|---:|---|---|
| `0x4000` | 25 | `0x67cd, 0x6a04, 0x6a11, 0x6a29, 0x7281, 0x7391` | controller gateway/status |
| `0x4002` | 1 | `0xbbe1` | controller gateway/status |
| `0x4004` | 1 | `0xc961` | controller gateway/status |
| `0x4008` | 1 | `0x9239` | controller gateway/status |
| `0x400e` | 1 | `0x8537` | controller gateway/status |
| `0x4011` | 4 | `0x70e2, 0x70ee, 0x7152, 0x715e` | controller gateway/status |
| `0x4012` | 2 | `0x70f6, 0x7166` | controller gateway/status |
| `0x4013` | 1 | `0x716e` | controller gateway/status |
| `0x4014` | 3 | `0x61fb, 0x726f, 0xa279` | controller gateway/status |
| `0x4016` | 1 | `0xc72d` | controller gateway/status |
| `0x4018` | 1 | `0x9ff5` | controller gateway/status |
| `0x4019` | 1 | `0x6fa3` | controller gateway/status |
| `0x401a` | 1 | `0x72b8` | controller gateway/status |
| `0x401b` | 1 | `0x7d01` | controller gateway/status |
| `0x401e` | 1 | `0xbaa3` | controller gateway/status |
| `0x401f` | 1 | `0x7d17` | controller gateway/status |
| `0x4023` | 3 | `0x6f4f, 0x6f57, 0x7d07` | controller gateway/status |
| `0x4025` | 1 | `0xd9f0` | controller gateway/status |
| `0x4026` | 1 | `0xd9fa` | controller gateway/status |
| `0x402b` | 1 | `0x6056` | controller gateway/status |
| `0x402d` | 1 | `0xd9db` | controller gateway/status |
| `0x403c` | 1 | `0x6062` | controller gateway/status |
| `0x4050` | 1 | `0xc9eb` | controller gateway/status |
| `0x4078` | 1 | `0xbdc7` | controller gateway/status |
| `0x4091` | 4 | `0x7603, 0x7b22, 0x8701, 0xe5f7` | controller gateway/status |
| `0x4093` | 2 | `0x761c, 0x7b3b` | controller gateway/status |
| `0x4095` | 7 | `0x739c, 0x7646, 0x77b0, 0x7c68, 0xdbf6, 0xdc19` | controller gateway/status |
| `0x4096` | 3 | `0xdbfe, 0xdc21, 0xdc74` | controller gateway/status |
| `0x4097` | 5 | `0x73b5, 0x7dc1, 0xdc06, 0xdc29, 0xdc7c` | controller gateway/status |
| `0x4098` | 9 | `0x6a0b, 0x6a18, 0x7288, 0x8714, 0x871f, 0x872c` | controller gateway/status |
| `0x4099` | 6 | `0x7483, 0x748b, 0x7493, 0x749b, 0x7986, 0x7995` | controller gateway/status |
| `0x409a` | 4 | `0x7653, 0x7667, 0xe60a, 0xe66a` | controller gateway/status |
| `0x409c` | 9 | `0x73b9, 0x74a9, 0x7620, 0x7629, 0x7660, 0x7673` | controller gateway/status |
| `0x40a0` | 1 | `0xe629` | controller gateway/status |
| `0x40a1` | 1 | `0xe681` | controller gateway/status |
| `0x40a7` | 1 | `0xe655` | controller gateway/status |
| `0x40b5` | 2 | `0x7dd9, 0x7de6` | controller gateway/status |
| `0x40b6` | 1 | `0x7dcc` | controller gateway/status |
| `0x40b7` | 1 | `0x7dd5` | controller gateway/status |
| `0x40c4` | 1 | `0xa0cf` | controller gateway/status |
| `0x40e2` | 1 | `0xa49b` | controller gateway/status |
| `0x40e3` | 1 | `0xa747` | controller gateway/status |
| `0x40e7` | 1 | `0xb5ab` | controller gateway/status |
| `0x4704` | 1 | `0x8684` | controller/front-panel/status fabric |
| `0x4709` | 1 | `0x822d` | controller/front-panel/status fabric |
| `0x470e` | 4 | `0x8223, 0x855d, 0x8564, 0xda8d` | controller/front-panel/status fabric |
| `0x4712` | 1 | `0x96a5` | controller/front-panel/status fabric |
| `0x471d` | 1 | `0xa74d` | controller/front-panel/status fabric |
| `0x471f` | 1 | `0x9aa3` | controller/front-panel/status fabric |
| `0x472d` | 1 | `0x96b5` | controller/front-panel/status fabric |
| `0x4739` | 1 | `0x9a95` | controller/front-panel/status fabric |
| `0x474c` | 2 | `0x857a, 0x868c` | controller/front-panel/status fabric |
| `0x4762` | 11 | `0x72a2, 0x7313, 0x76a9, 0x8031, 0x81f8, 0x82c9` | controller/front-panel/status fabric |
| `0x4764` | 1 | `0xda65` | controller/front-panel/status fabric |
| `0x4772` | 1 | `0xda6a` | controller/front-panel/status fabric |
| `0x4774` | 1 | `0xda5f` | controller/front-panel/status fabric |
| `0x477f` | 1 | `0x653e` | controller/front-panel/status fabric |
| `0x4782` | 2 | `0x920b, 0xda94` | controller/front-panel/status fabric |
| `0x4789` | 2 | `0x7ebc, 0x96a0` | controller/front-panel/status fabric |
| `0x4794` | 1 | `0x6a3e` | controller/front-panel/status fabric |
| `0x47a6` | 6 | `0x8556, 0x856b, 0x8573, 0xdaa8, 0xdace, 0xdae8` | controller/front-panel/status fabric |
| `0x47a8` | 1 | `0x6648` | controller/front-panel/status fabric |
| `0x47af` | 3 | `0x75eb, 0x8252, 0x9e07` | controller/front-panel/status fabric |
| `0x47b0` | 1 | `0x9464` | controller/front-panel/status fabric |
| `0x47b1` | 39 | `0x6266, 0x6275, 0x6342, 0x636c, 0x637c, 0x6497` | controller/front-panel/status fabric |
| `0x47c0` | 1 | `0x6b85` | controller/front-panel/status fabric |
| `0x47c1` | 1 | `0x6069` | controller/front-panel/status fabric |
| `0x47c2` | 1 | `0x6667` | controller/front-panel/status fabric |
| `0x47c4` | 3 | `0x61c7, 0x61f0, 0x6660` | controller/front-panel/status fabric |
| `0x47c5` | 1 | `0x61eb` | controller/front-panel/status fabric |
| `0x47c9` | 4 | `0x6506, 0x6642, 0x702c, 0x9fd1` | controller/front-panel/status fabric |
| `0x47ca` | 2 | `0x7bd1, 0x9fc2` | controller/front-panel/status fabric |
| `0x47cb` | 3 | `0x6502, 0x7031, 0x9ef6` | controller/front-panel/status fabric |
| `0x47cd` | 2 | `0x6093, 0x7c18` | controller/front-panel/status fabric |
| `0x47cf` | 2 | `0x605b, 0x9fde` | controller/front-panel/status fabric |
| `0x47d0` | 2 | `0x9fc8, 0x9fe8` | controller/front-panel/status fabric |
| `0x47d2` | 2 | `0x6076, 0x61f4` | controller/front-panel/status fabric |
| `0x47d6` | 3 | `0x75e7, 0x824e, 0x9e03` | controller/front-panel/status fabric |
| `0x47d7` | 2 | `0x6206, 0x8243` | controller/front-panel/status fabric |
| `0x47e0` | 1 | `0xa753` | controller/front-panel/status fabric |
| `0x47f3` | 3 | `0x821c, 0x823b, 0x8f03` | controller/front-panel/status fabric |
| `0x47f4` | 1 | `0x8f11` | controller/front-panel/status fabric |
| `0x47ff` | 1 | `0x8f0a` | controller/front-panel/status fabric |
| `0x4805` | 1 | `0xe7fe` | controller/front-panel/status fabric |
| `0x4806` | 5 | `0x928e, 0x9309, 0x932c, 0x933b, 0x954c` | controller/front-panel/status fabric |
| `0x480b` | 3 | `0x9402, 0x9417, 0x9425` | controller/front-panel/status fabric |
| `0x480c` | 5 | `0x9281, 0x92b8, 0x9324, 0x9334, 0x9437` | controller/front-panel/status fabric |
| `0x480e` | 7 | `0x831c, 0x8bda, 0x8bf0, 0x8c7a, 0x91f2, 0x92a6` | controller/front-panel/status fabric |
| `0x4814` | 1 | `0x8005` | controller/front-panel/status fabric |
| `0x4819` | 1 | `0xdb33` | controller/front-panel/status fabric |
| `0x481a` | 1 | `0xa0bc` | controller/front-panel/status fabric |
| `0x4820` | 2 | `0x8d41, 0x9393` | controller/front-panel/status fabric |
| `0x4821` | 1 | `0x9a81` | controller/front-panel/status fabric |
| `0x4823` | 2 | `0x7fca, 0x7fd4` | controller/front-panel/status fabric |
| `0x4825` | 2 | `0x9a86, 0x9a90` | controller/front-panel/status fabric |
| `0x482b` | 2 | `0x6238, 0x81ae` | controller/front-panel/status fabric |
| `0x482d` | 1 | `0x63c4` | controller/front-panel/status fabric |
| `0x4831` | 1 | `0xa0b4` | controller/front-panel/status fabric |
| `0x4834` | 5 | `0x6a59, 0x6a76, 0x6b4d, 0x7d2d, 0x884d` | controller/front-panel/status fabric |
| `0x4835` | 2 | `0x6a69, 0x6b46` | controller/front-panel/status fabric |
| `0x4840` | 5 | `0x7436, 0x84ab, 0x858e, 0x8894, 0x9b32` | controller/front-panel/status fabric |
| `0x4841` | 1 | `0x77f0` | controller/front-panel/status fabric |
| `0x4860` | 4 | `0x750d, 0x8bfa, 0x8c64, 0x92ec` | controller/front-panel/status fabric |
| `0x4862` | 2 | `0x62a3, 0x7522` | controller/front-panel/status fabric |
| `0x4863` | 4 | `0x7528, 0x84a3, 0x8584, 0x889c` | controller/front-panel/status fabric |
| `0x4864` | 4 | `0x7502, 0x777e, 0x8c56, 0x92f3` | controller/front-panel/status fabric |
| `0x4867` | 4 | `0x68fd, 0x9409, 0x941e, 0xa645` | controller/front-panel/status fabric |
| `0x486a` | 1 | `0x7538` | controller/front-panel/status fabric |
| `0x486e` | 1 | `0x8693` | controller/front-panel/status fabric |
| `0x48a5` | 3 | `0x60a1, 0x8be2, 0x91fc` | controller/front-panel/status fabric |
| `0x48b4` | 1 | `0x7fbe` | controller/front-panel/status fabric |
| `0x48c0` | 1 | `0x68eb` | controller/front-panel/status fabric |
| `0x48c1` | 1 | `0x68e6` | controller/front-panel/status fabric |
| `0x48c8` | 3 | `0x6be2, 0x9953, 0x9961` | controller/front-panel/status fabric |
| `0x48e7` | 2 | `0x9943, 0x994a` | controller/front-panel/status fabric |
| `0x48ee` | 2 | `0x8ea7, 0x8eb3` | controller/front-panel/status fabric |
| `0x48ef` | 1 | `0x6bea` | controller/front-panel/status fabric |
| `0x48f1` | 1 | `0x68ef` | controller/front-panel/status fabric |
| `0x48f4` | 1 | `0x6bca` | controller/front-panel/status fabric |
| `0x48f5` | 1 | `0x6bd2` | controller/front-panel/status fabric |
| `0x48f6` | 1 | `0x6bda` | controller/front-panel/status fabric |
| `0x48f8` | 2 | `0x81d9, 0x81e2` | controller/front-panel/status fabric |
| `0x48fc` | 1 | `0x8eba` | controller/front-panel/status fabric |
| `0x5905` | 4 | `0x87f8, 0x8c41, 0x8c5d, 0x9388` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5906` | 3 | `0x848b, 0x8598, 0x8884` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5907` | 1 | `0x68d9` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x590b` | 1 | `0x68f6` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x590d` | 3 | `0x8493, 0x84ba, 0x888c` | servo/mechanics-looking hardware cluster |
| `0x594d` | 1 | `0x9228` | servo/mechanics-looking hardware cluster |
| `0x5962` | 1 | `0x85a6` | servo/mechanics-looking hardware cluster |
| `0x5969` | 2 | `0x833b, 0x85b5` | servo/mechanics-looking hardware cluster |
| `0x596a` | 1 | `0x8483` | servo/mechanics-looking hardware cluster |
| `0x59c6` | 1 | `0x85af` | servo/mechanics-looking hardware cluster |
| `0x59f9` | 1 | `0xbfef` | servo/mechanics-looking hardware cluster |
| `0x5a00` | 2 | `0x849b, 0x85a2` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5a01` | 2 | `0x8c48, 0x9381` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5a0c` | 1 | `0x968a` | servo/mechanics-looking hardware cluster |
| `0x5a10` | 2 | `0x9682, 0x9690` | servo/mechanics-looking hardware cluster |
| `0x5a28` | 1 | `0x908a` | servo/mechanics-looking hardware cluster |
| `0x5a31` | 1 | `0x68c5` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x8000` | 1 | `0xdb1f` | shared command/status buffers |
| `0x8008` | 1 | `0x86e4` | shared command/status buffers |
| `0x800f` | 1 | `0x645d` | shared command/status buffers |
| `0x8016` | 1 | `0x9b03` | shared command/status buffers |
| `0x8017` | 1 | `0x9a33` | shared command/status buffers |
| `0x801c` | 1 | `0xee01` | shared command/status buffers |
| `0x801d` | 1 | `0xee0a` | shared command/status buffers |
| `0x8020` | 1 | `0x9a2e` | shared command/status buffers |
| `0x8042` | 2 | `0x9537, 0x9708` | shared command/status buffers |
| `0x8046` | 1 | `0x65da` | shared command/status buffers |
| `0x8074` | 2 | `0xed9c, 0xede2` | shared command/status buffers |
| `0x8075` | 2 | `0xedae, 0xedf2` | shared command/status buffers |
| `0x807c` | 1 | `0x77ca` | shared command/status buffers |
| `0x8080` | 1 | `0x7f89` | shared command/status buffers |
| `0x80a1` | 1 | `0xecec` | shared command/status buffers |
| `0x80a2` | 1 | `0x9cdb` | shared command/status buffers |
| `0x80a7` | 2 | `0x9cd6, 0xadcb` | shared command/status buffers |
| `0x80b4` | 1 | `0x6c5e` | shared command/status buffers |
| `0x80d8` | 1 | `0xa9ff` | shared command/status buffers |
| `0x80db` | 1 | `0xc6cd` | shared command/status buffers |
| `0x80e0` | 1 | `0xb3b9` | shared command/status buffers |
| `0x80f0` | 1 | `0x7f7f` | shared command/status buffers |
| `0x8102` | 1 | `0x6f3e` | shared command/status buffers |
| `0x810e` | 1 | `0x62fe` | shared command/status buffers |
| `0x811d` | 1 | `0x6614` | shared command/status buffers |
| `0x8120` | 1 | `0xd7ee` | shared command/status buffers |
| `0x8133` | 2 | `0x62f4, 0x8660` | shared command/status buffers |
| `0x814b` | 1 | `0x6d22` | shared command/status buffers |
| `0x8153` | 1 | `0x6eb8` | shared command/status buffers |
| `0x8156` | 1 | `0x6686` | shared command/status buffers |
| `0x8177` | 1 | `0x95dd` | shared command/status buffers |
| `0x8184` | 1 | `0xf766` | shared command/status buffers |
| `0x81a0` | 1 | `0xbda3` | shared command/status buffers |
| `0x81a4` | 1 | `0xb827` | shared command/status buffers |
| `0x81ce` | 1 | `0x8172` | shared command/status buffers |
| `0x81cf` | 1 | `0x816a` | shared command/status buffers |
| `0x81f5` | 5 | `0x6e8e, 0x6e9a, 0x6f00, 0x6f2e, 0x810f` | shared command/status buffers |
| `0x81ff` | 1 | `0x9005` | shared command/status buffers |
| `0x8213` | 1 | `0x7454` | shared command/status buffers |
| `0x8216` | 1 | `0xed6b` | shared command/status buffers |
| `0x8217` | 1 | `0xed74` | shared command/status buffers |
| `0x8224` | 3 | `0x744c, 0x7b89, 0x7ba2` | shared command/status buffers |
| `0x8232` | 1 | `0x6117` | shared command/status buffers |
| `0x8243` | 5 | `0x6e75, 0x9047, 0x9619, 0x971c, 0x9d4c` | shared command/status buffers |
| `0x8249` | 1 | `0x966c` | shared command/status buffers |
| `0x824a` | 1 | `0x6125` | shared command/status buffers |
| `0x824b` | 1 | `0x65f4` | shared command/status buffers |
| `0x824f` | 3 | `0x7f9c, 0x9710, 0x9caf` | shared command/status buffers |
| `0x8250` | 2 | `0xed06, 0xed4c` | shared command/status buffers |
| `0x8251` | 2 | `0xed18, 0xed5c` | shared command/status buffers |
| `0x8259` | 2 | `0x8113, 0x8b4b` | shared command/status buffers |
| `0x825b` | 14 | `0x6c64, 0x79c3, 0x7ca7, 0x7cb3, 0x86d0, 0x87c9` | shared command/status buffers |
| `0x82cd` | 1 | `0x6131` | shared command/status buffers |
| `0x82d8` | 1 | `0xc631` | shared command/status buffers |
| `0x82df` | 2 | `0x603d, 0x6102` | shared command/status buffers |
| `0x82f3` | 1 | `0x65f0` | shared command/status buffers |
| `0x82fa` | 1 | `0x7568` | shared command/status buffers |
| `0x82fc` | 1 | `0xee12` | shared command/status buffers |

## Disassembly Caution

Many apparent calls/jumps target `0x02ea..0x3fff`, which is all zero in
this captured window. That argues against treating the dump as a complete
standalone 8051 code image at base zero. Plausible explanations are missing
bank/common-ROM code, banked address spaces, and false positives from
linear-disassembling data.

- top-80 `LCALL` targets in the zero range: 56
- top-80 `LJMP` targets in the zero range: 14

## Sled / Servo Side Quest

The gateway dump gives a much stronger static foothold for the mechanics
goal. The `0x59xx` and `0x5axx` cluster is touched by several coherent
routines, and exact overlap shows the LD5M resident routine around F0
`0x59f3` is present at gateway offset `0x6059`. That routine clears or
masks `0x5904`, `0x5905`, `0x5906`, `0x592a`, `0x59f0`, `0x59f1`,
`0x5a00`, `0x5a24`, `0x5a31`, and then initializes nearby `0x4860..0x486a`
state. Other gateway routines around `0x642c`, `0x6fe0`, and `0x8278`
manipulate the same cluster.

That lines up with the live observation that blind probes in this area
moved the sled or changed recovery behavior. Practically, this is now a
servo/mechanics command cluster to reverse, not a front-LED latch to poke.
The safer next static step is to map the call graph and state-machine inputs
around these `0x59xx` routines before issuing any live movement tests.

Promising static waypoints:

- gateway `0x6059`: resident/helper init-like hardware setup, exact F0 overlap;
- gateway `0x642c`: masks `0x5904/0x590b`, writes `0x4864=0x36`, loops through data while polling `0x4000.7`;
- gateway `0x6fe0`: enables/disables `0x59a4/0x5907/0x599e/0x592b/0x5997/0x5945` paths;
- gateway `0x8278`: state-gated path that clears `0x5905.6`, then branches into larger mechanics/state routines.

## Practical Consequence

The new artifact narrows the next work. For CDD, it proves the gateway can
show copied encoded CDD work buffers, but not yet decoded controller code at
`0x184000`. For mechanics, it gives a concrete `0x59xx` control cluster to
reverse from real runtime bytes. For LED output, it reinforces that the LED
is probably controller-owned or coupled to controller state, not an easy
8051 GPIO latch.
