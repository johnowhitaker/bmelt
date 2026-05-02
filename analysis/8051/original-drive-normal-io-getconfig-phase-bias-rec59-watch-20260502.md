# Normal Work-Window Watch Chunks

## Chunks

| name | sha256 | first bytes |
|---|---|---|
| `rec59-c0` | `20ea2ab16891b5c70526dc35ea5187e6ab4d45b592920d95e255f52d34a09baa` | `8a29e0c4540f30e011908a4ce0c3940e` |
| `rec59-c1` | `99d4493dc4cfdc4cea75d21f27ed90af53b0f067d9238f902e536c1eec033b29` | `f608760112efb6057c057c22908857e0` |
| `rec59-c2` | `b7a129b7d392f0209ca71625dbfb5e4a1609c0ae26b96d7cc940ea0582952c49` | `e054884efeef4ef07e007f08120a65e4` |

## Totals

### phase-bias

- captures: `120`
- adjacency: `{'full-adjacent': 64, 'edge-bits:01': 56}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 64, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 56}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x64, `+0x7140` x56 |
| `rec59-c1` | `+0x71c0` x120 |
| `rec59-c2` | `+0x7200` x120 |

## By Stimulus

### phase-bias

#### baseline-no-stimulus

- captures: `24`
- adjacency: `{'full-adjacent': 13, 'edge-bits:01': 11}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 13, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 11}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x13, `+0x7140` x11 |
| `rec59-c1` | `+0x71c0` x24 |
| `rec59-c2` | `+0x7200` x24 |

#### r4-01-current-sf0000

- captures: `24`
- adjacency: `{'edge-bits:01': 15, 'full-adjacent': 9}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 15, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 9}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x15, `+0x7180` x9 |
| `rec59-c1` | `+0x71c0` x24 |
| `rec59-c2` | `+0x7200` x24 |

#### r6-01-current-sf0000

- captures: `24`
- adjacency: `{'full-adjacent': 13, 'edge-bits:01': 11}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 13, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 11}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x13, `+0x7140` x11 |
| `rec59-c1` | `+0x71c0` x24 |
| `rec59-c2` | `+0x7200` x24 |

#### std-current-sf0000-len00fc

- captures: `24`
- adjacency: `{'full-adjacent': 15, 'edge-bits:01': 9}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 15, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 9}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x15, `+0x7140` x9 |
| `rec59-c1` | `+0x71c0` x24 |
| `rec59-c2` | `+0x7200` x24 |

#### std-current-sf0020-len00fc

- captures: `24`
- adjacency: `{'full-adjacent': 14, 'edge-bits:01': 10}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 14, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 10}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x14, `+0x7140` x10 |
| `rec59-c1` | `+0x71c0` x24 |
| `rec59-c2` | `+0x7200` x24 |

