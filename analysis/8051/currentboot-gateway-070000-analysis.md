# Currentboot Gateway 0x070000 Analysis

Date: 2026-04-30

This is an offline analysis of the 64 KiB controller-gateway dump read
from Linux drive #1 while the drive was in currentboot. No live drive
access is performed by this report generator.

## Artifact

```text
path   /Users/johno/projects/boastermelt/references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin
base   0x070000
size   0x10000
sha256 5f517adeab1647dbedf7b93f8be097b1641164fd49e87776364b9e134b9cbc0b
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

## Page Shape

| page | nonzero | non-ff | entropy | note |
|---:|---:|---:|---:|---|
| `0x0000` | 645 | 4096 | 1.4561 | low table/record area |
| `0x1000` | 0 | 4096 | -0.0000 | all zero |
| `0x2000` | 0 | 4096 | -0.0000 | all zero |
| `0x3000` | 0 | 4096 | -0.0000 | all zero |
| `0x4000` | 3967 | 690 | 1.6837 | profile/string/table area |
| `0x5000` | 1316 | 3171 | 1.7817 | profile/string/table area |
| `0x6000` | 3989 | 4042 | 6.6662 | code-like/table mixed |
| `0x7000` | 3990 | 4048 | 6.6578 | code-like/table mixed |
| `0x8000` | 4001 | 4039 | 6.6977 | code-like/table mixed |
| `0x9000` | 3892 | 4040 | 6.8288 | code-like/table mixed |
| `0xa000` | 4059 | 4083 | 5.6282 | code-like/table mixed |
| `0xb000` | 4093 | 4086 | 5.3377 | code-like/table mixed |
| `0xc000` | 4078 | 4064 | 6.2036 | code-like/table mixed |
| `0xd000` | 3731 | 4050 | 6.7902 | code-like/table mixed |
| `0xe000` | 4022 | 4018 | 6.7048 | code-like/table mixed |
| `0xf000` | 3529 | 4087 | 7.2622 | CDD mirror/header tail |

Long zero/ff runs:

```text
00 0x02ea..0x3fff len=0x3d16
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
| `0x27` | `0x6059` | `0x0631` | `905904e4f0a3f09059c0e054fe4404f0` |
| `0x25` | `0x651b` | `0x0631` | `905904e4f0a3f09059c0e054fe4404f0` |

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
| `0x4000` | 38 | `0x63af, 0x6490, 0x672b, 0x6843, 0x6851, 0x6ef6` | controller gateway/status |
| `0x4001` | 1 | `0x6288` | controller gateway/status |
| `0x4002` | 2 | `0x6280, 0xbbe1` | controller gateway/status |
| `0x4004` | 1 | `0xc961` | controller gateway/status |
| `0x4008` | 1 | `0x92b9` | controller gateway/status |
| `0x400a` | 2 | `0x9621, 0x962b` | controller gateway/status |
| `0x4014` | 1 | `0xa279` | controller gateway/status |
| `0x4016` | 1 | `0xc72d` | controller gateway/status |
| `0x4019` | 1 | `0x9667` | controller gateway/status |
| `0x401a` | 3 | `0x75cd, 0x75da, 0x9325` | controller gateway/status |
| `0x401d` | 1 | `0x7c34` | controller gateway/status |
| `0x401e` | 1 | `0xbaa3` | controller gateway/status |
| `0x4021` | 1 | `0x7c26` | controller gateway/status |
| `0x4025` | 1 | `0xd9f0` | controller gateway/status |
| `0x4026` | 1 | `0xd9fa` | controller gateway/status |
| `0x4028` | 1 | `0x8fb0` | controller gateway/status |
| `0x402d` | 1 | `0xd9db` | controller gateway/status |
| `0x4037` | 1 | `0x9e1b` | controller gateway/status |
| `0x4050` | 1 | `0xc9eb` | controller gateway/status |
| `0x4078` | 1 | `0xbdc7` | controller gateway/status |
| `0x4091` | 3 | `0x6732, 0x8155, 0xe5f7` | controller gateway/status |
| `0x4092` | 2 | `0x801e, 0x814d` | controller gateway/status |
| `0x4093` | 2 | `0x8016, 0x8145` | controller gateway/status |
| `0x4095` | 12 | `0x6858, 0x6efd, 0x7117, 0x7a36, 0x7ca9, 0x7e9c` | controller gateway/status |
| `0x4096` | 3 | `0xdbfe, 0xdc21, 0xdc74` | controller gateway/status |
| `0x4097` | 3 | `0xdc06, 0xdc29, 0xdc7c` | controller gateway/status |
| `0x4098` | 24 | `0x6395, 0x63b6, 0x673d, 0x70d3, 0x70da, 0x7304` | controller gateway/status |
| `0x409a` | 2 | `0xe60a, 0xe66a` | controller gateway/status |
| `0x409c` | 2 | `0xe616, 0xe676` | controller gateway/status |
| `0x40a0` | 1 | `0xe629` | controller gateway/status |
| `0x40a1` | 1 | `0xe681` | controller gateway/status |
| `0x40a7` | 1 | `0xe655` | controller gateway/status |
| `0x40b5` | 1 | `0x903e` | controller gateway/status |
| `0x40c4` | 1 | `0xa0cf` | controller gateway/status |
| `0x40d4` | 1 | `0x9e14` | controller gateway/status |
| `0x40d8` | 1 | `0x85d1` | controller gateway/status |
| `0x40d9` | 1 | `0x85d9` | controller gateway/status |
| `0x40e2` | 1 | `0xa49b` | controller gateway/status |
| `0x40e3` | 1 | `0xa747` | controller gateway/status |
| `0x40e7` | 1 | `0xb5ab` | controller gateway/status |
| `0x40ea` | 1 | `0x85de` | controller gateway/status |
| `0x4709` | 1 | `0x822d` | controller/front-panel/status fabric |
| `0x470e` | 4 | `0x8223, 0x855d, 0x8564, 0xda8d` | controller/front-panel/status fabric |
| `0x471d` | 1 | `0xa74d` | controller/front-panel/status fabric |
| `0x4737` | 1 | `0x916e` | controller/front-panel/status fabric |
| `0x474c` | 1 | `0x857a` | controller/front-panel/status fabric |
| `0x4755` | 1 | `0x9d04` | controller/front-panel/status fabric |
| `0x4762` | 4 | `0x91e8, 0xa0c2, 0xda5a, 0xefc2` | controller/front-panel/status fabric |
| `0x4764` | 1 | `0xda65` | controller/front-panel/status fabric |
| `0x4772` | 1 | `0xda6a` | controller/front-panel/status fabric |
| `0x4774` | 1 | `0xda5f` | controller/front-panel/status fabric |
| `0x4782` | 3 | `0x6f62, 0x928b, 0xda94` | controller/front-panel/status fabric |
| `0x47a6` | 6 | `0x8556, 0x856b, 0x8573, 0xdaa8, 0xdace, 0xdae8` | controller/front-panel/status fabric |
| `0x47cd` | 2 | `0x75e4, 0x7c58` | controller/front-panel/status fabric |
| `0x47d1` | 2 | `0x6c20, 0x81e0` | controller/front-panel/status fabric |
| `0x47d5` | 1 | `0x6c28` | controller/front-panel/status fabric |
| `0x47e0` | 1 | `0xa753` | controller/front-panel/status fabric |
| `0x47f3` | 2 | `0x821c, 0x823b` | controller/front-panel/status fabric |
| `0x4800` | 1 | `0x983d` | controller/front-panel/status fabric |
| `0x4805` | 1 | `0xe7fe` | controller/front-panel/status fabric |
| `0x4806` | 1 | `0x950c` | controller/front-panel/status fabric |
| `0x4819` | 1 | `0xdb33` | controller/front-panel/status fabric |
| `0x481a` | 1 | `0xa0bc` | controller/front-panel/status fabric |
| `0x4823` | 2 | `0x9f44, 0x9f4e` | controller/front-panel/status fabric |
| `0x482b` | 1 | `0x7956` | controller/front-panel/status fabric |
| `0x4831` | 1 | `0xa0b4` | controller/front-panel/status fabric |
| `0x4834` | 1 | `0x9f64` | controller/front-panel/status fabric |
| `0x4840` | 1 | `0x9bb2` | controller/front-panel/status fabric |
| `0x4851` | 1 | `0x8f29` | controller/front-panel/status fabric |
| `0x4860` | 2 | `0x6167, 0x73cf` | controller/front-panel/status fabric |
| `0x4861` | 7 | `0x8312, 0x84da, 0x84e8, 0x852b, 0x8620, 0x87e8` | controller/front-panel/status fabric |
| `0x4862` | 4 | `0x8327, 0x8479, 0x8539, 0x89d5` | controller/front-panel/status fabric |
| `0x4863` | 4 | `0x6456, 0x8319, 0x84f6, 0x8614` | controller/front-panel/status fabric |
| `0x4864` | 6 | `0x6357, 0x6450, 0x832e, 0x8441, 0x87fd, 0x89dc` | controller/front-panel/status fabric |
| `0x4867` | 13 | `0x6176, 0x643a, 0x67b5, 0x6fd8, 0x705a, 0x706d` | controller/front-panel/status fabric |
| `0x486a` | 10 | `0x617c, 0x645d, 0x67ae, 0x6fc4, 0x7061, 0x73e4` | controller/front-panel/status fabric |
| `0x486b` | 4 | `0x6fd1, 0x8472, 0x87c7, 0x89f4` | controller/front-panel/status fabric |
| `0x486e` | 1 | `0x6513` | controller/front-panel/status fabric |
| `0x4876` | 6 | `0x60b6, 0x6244, 0x64b7, 0x66d2, 0x6879, 0x6a92` | controller/front-panel/status fabric |
| `0x487a` | 1 | `0x8fa9` | controller/front-panel/status fabric |
| `0x4880` | 1 | `0x9660` | controller/front-panel/status fabric |
| `0x48a0` | 1 | `0x8985` | controller/front-panel/status fabric |
| `0x48a5` | 4 | `0x75f2, 0x7696, 0x9300, 0x930e` | controller/front-panel/status fabric |
| `0x48ac` | 23 | `0x6100, 0x6105, 0x610c, 0x6121, 0x624e, 0x6254` | controller/front-panel/status fabric |
| `0x48ad` | 7 | `0x60b1, 0x64b1, 0x66cc, 0x6873, 0x6a8c, 0x8778` | controller/front-panel/status fabric |
| `0x48af` | 1 | `0x9e22` | controller/front-panel/status fabric |
| `0x48b7` | 1 | `0x877e` | controller/front-panel/status fabric |
| `0x48d0` | 6 | `0x7543, 0x7567, 0x9923, 0x9931, 0x993d, 0x9d92` | controller/front-panel/status fabric |
| `0x48d9` | 2 | `0x8f22, 0x8f35` | controller/front-panel/status fabric |
| `0x48e9` | 4 | `0x754a, 0x756e, 0x9938, 0x9d99` | controller/front-panel/status fabric |
| `0x48eb` | 1 | `0x60cc` | controller/front-panel/status fabric |
| `0x48ee` | 2 | `0x88a3, 0x88ab` | controller/front-panel/status fabric |
| `0x48f0` | 2 | `0x613e, 0x777e` | controller/front-panel/status fabric |
| `0x48f4` | 1 | `0x780a` | controller/front-panel/status fabric |
| `0x48f5` | 1 | `0x7812` | controller/front-panel/status fabric |
| `0x48f8` | 1 | `0x7fc6` | controller/front-panel/status fabric |
| `0x5900` | 1 | `0x7219` | servo/mechanics-looking hardware cluster |
| `0x5901` | 1 | `0x7d6e` | servo/mechanics-looking hardware cluster |
| `0x5904` | 7 | `0x6059, 0x642c, 0x651b, 0x6fe0, 0x8304, 0x846b` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5905` | 7 | `0x6223, 0x622c, 0x636d, 0x71f0, 0x8278, 0x845f` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5906` | 5 | `0x6069, 0x652b, 0x8516, 0x89c0, 0x89ea` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5907` | 1 | `0x6ff7` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x590b` | 1 | `0x6433` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5922` | 1 | `0x76cb` | servo/mechanics-looking hardware cluster |
| `0x592a` | 4 | `0x6070, 0x6532, 0x7535, 0x7c1c` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x592b` | 1 | `0x7045` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5940` | 5 | `0x6b67, 0x6b76, 0x6c0b, 0x71d8, 0x7bb0` | servo/mechanics-looking hardware cluster |
| `0x5945` | 1 | `0x7053` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5946` | 1 | `0x6b4c` | servo/mechanics-looking hardware cluster |
| `0x594a` | 1 | `0x6b5e` | servo/mechanics-looking hardware cluster |
| `0x594b` | 6 | `0x6b7a, 0x6c0f, 0x6c1b, 0x70a6, 0x7bb4, 0x7c00` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x594d` | 1 | `0x92a8` | servo/mechanics-looking hardware cluster |
| `0x594f` | 1 | `0x99e9` | servo/mechanics-looking hardware cluster |
| `0x5954` | 2 | `0x6159, 0x851d` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5960` | 1 | `0x7ced` | servo/mechanics-looking hardware cluster |
| `0x5961` | 1 | `0x76c5` | servo/mechanics-looking hardware cluster |
| `0x5962` | 1 | `0x7ce0` | servo/mechanics-looking hardware cluster |
| `0x596c` | 1 | `0x7cdc` | servo/mechanics-looking hardware cluster |
| `0x5991` | 1 | `0x7252` | servo/mechanics-looking hardware cluster |
| `0x5997` | 2 | `0x704c, 0x7144` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x599a` | 1 | `0x8baf` | servo/mechanics-looking hardware cluster |
| `0x599e` | 2 | `0x6ffe, 0x7631` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x599f` | 4 | `0x6366, 0x720a, 0x77d5, 0x77e4` | servo/mechanics-looking hardware cluster |
| `0x59a4` | 2 | `0x6ff0, 0x707d` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x59c0` | 2 | `0x6060, 0x6522` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x59e0` | 2 | `0x9851, 0x9862` | servo/mechanics-looking hardware cluster |
| `0x59f0` | 3 | `0x6077, 0x6539, 0x830b` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x59f9` | 1 | `0xbfef` | servo/mechanics-looking hardware cluster |
| `0x5a00` | 2 | `0x6021, 0x6141` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5a10` | 4 | `0x84d3, 0x8524, 0x860d, 0x87d2` | servo/mechanics-looking hardware cluster |
| `0x5a24` | 4 | `0x614b, 0x8320, 0x8458, 0x89ce` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5a28` | 1 | `0x904a` | servo/mechanics-looking hardware cluster |
| `0x5a2c` | 1 | `0x6034` | servo/mechanics-looking hardware cluster |
| `0x5a31` | 2 | `0x6152, 0x67a5` | servo/mechanics-looking hardware cluster; servo/mechanics shortlist |
| `0x5a44` | 1 | `0x75bc` | servo/mechanics-looking hardware cluster |
| `0x8000` | 1 | `0xdb1f` | shared command/status buffers |
| `0x8002` | 1 | `0x74b9` | shared command/status buffers |
| `0x8016` | 1 | `0x9b83` | shared command/status buffers |
| `0x8017` | 1 | `0x9a73` | shared command/status buffers |
| `0x801c` | 1 | `0xee01` | shared command/status buffers |
| `0x801d` | 1 | `0xee0a` | shared command/status buffers |
| `0x8020` | 1 | `0x9a6e` | shared command/status buffers |
| `0x8046` | 1 | `0x65da` | shared command/status buffers |
| `0x805d` | 1 | `0x7788` | shared command/status buffers |
| `0x8074` | 2 | `0xed9c, 0xede2` | shared command/status buffers |
| `0x8075` | 2 | `0xedae, 0xedf2` | shared command/status buffers |
| `0x807b` | 1 | `0x8abd` | shared command/status buffers |
| `0x809e` | 1 | `0x765a` | shared command/status buffers |
| `0x80a1` | 1 | `0xecec` | shared command/status buffers |
| `0x80a7` | 1 | `0xadcb` | shared command/status buffers |
| `0x80a9` | 1 | `0x8aad` | shared command/status buffers |
| `0x80b4` | 1 | `0x9bee` | shared command/status buffers |
| `0x80bb` | 1 | `0x80bd` | shared command/status buffers |
| `0x80d8` | 1 | `0xa9ff` | shared command/status buffers |
| `0x80db` | 1 | `0xc6cd` | shared command/status buffers |
| `0x80e0` | 1 | `0xb3b9` | shared command/status buffers |
| `0x8120` | 1 | `0xd7ee` | shared command/status buffers |
| `0x8133` | 8 | `0x764a, 0x779c, 0x7b85, 0x7d74, 0x864d, 0x88cf` | shared command/status buffers |
| `0x814b` | 1 | `0x98b1` | shared command/status buffers |
| `0x814e` | 1 | `0x73c4` | shared command/status buffers |
| `0x8153` | 3 | `0x7f21, 0x7f3c, 0x8083` | shared command/status buffers |
| `0x8156` | 1 | `0x6606` | shared command/status buffers |
| `0x8177` | 1 | `0x955d` | shared command/status buffers |
| `0x8183` | 2 | `0x6a79, 0x7bc6` | shared command/status buffers |
| `0x8184` | 1 | `0xf766` | shared command/status buffers |
| `0x81a0` | 1 | `0xbda3` | shared command/status buffers |
| `0x81a4` | 1 | `0xb827` | shared command/status buffers |
| `0x81e4` | 1 | `0x7c18` | shared command/status buffers |
| `0x81f5` | 1 | `0x810f` | shared command/status buffers |
| `0x81fd` | 1 | `0x8f02` | shared command/status buffers |
| `0x81ff` | 1 | `0x9085` | shared command/status buffers |
| `0x8216` | 1 | `0xed6b` | shared command/status buffers |
| `0x8217` | 1 | `0xed74` | shared command/status buffers |
| `0x8219` | 1 | `0x8046` | shared command/status buffers |
| `0x821a` | 1 | `0x804e` | shared command/status buffers |
| `0x8224` | 2 | `0x7ad0, 0x8b9d` | shared command/status buffers |
| `0x8243` | 1 | `0x9cd4` | shared command/status buffers |
| `0x8249` | 1 | `0x96ec` | shared command/status buffers |
| `0x824b` | 1 | `0x65f4` | shared command/status buffers |
| `0x824f` | 1 | `0x9caf` | shared command/status buffers |
| `0x8250` | 2 | `0xed06, 0xed4c` | shared command/status buffers |
| `0x8251` | 2 | `0xed18, 0xed5c` | shared command/status buffers |
| `0x8259` | 1 | `0x8113` | shared command/status buffers |
| `0x825b` | 22 | `0x61aa, 0x6af7, 0x6ce2, 0x6d4b, 0x6e70, 0x836e` | shared command/status buffers |
| `0x827b` | 1 | `0x8d3e` | shared command/status buffers |
| `0x82c9` | 1 | `0x9fa6` | shared command/status buffers |
| `0x82d8` | 1 | `0xc631` | shared command/status buffers |
| `0x82e4` | 1 | `0x8aa8` | shared command/status buffers |
| `0x82f3` | 1 | `0x65f0` | shared command/status buffers |
| `0x82fc` | 1 | `0xee12` | shared command/status buffers |
| `0x82fe` | 1 | `0x8a91` | shared command/status buffers |

## Disassembly Caution

Many apparent calls/jumps target `0x02ea..0x3fff`, which is all zero in
this captured window. That argues against treating the dump as a complete
standalone 8051 code image at base zero. Plausible explanations are missing
bank/common-ROM code, banked address spaces, and false positives from
linear-disassembling data.

- top-80 `LCALL` targets in the zero range: 48
- top-80 `LJMP` targets in the zero range: 20

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

