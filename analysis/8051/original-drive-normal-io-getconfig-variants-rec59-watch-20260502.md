# Normal Work-Window Watch Chunks

## Chunks

| name | sha256 | first bytes |
|---|---|---|
| `rec59-c0` | `20ea2ab16891b5c70526dc35ea5187e6ab4d45b592920d95e255f52d34a09baa` | `8a29e0c4540f30e011908a4ce0c3940e` |
| `rec59-c1` | `99d4493dc4cfdc4cea75d21f27ed90af53b0f067d9238f902e536c1eec033b29` | `f608760112efb6057c057c22908857e0` |
| `rec59-c2` | `b7a129b7d392f0209ca71625dbfb5e4a1609c0ae26b96d7cc940ea0582952c49` | `e054884efeef4ef07e007f08120a65e4` |

## Totals

### getconfig-variants

- captures: `80`
- adjacency: `{'full-adjacent': 43, 'edge-bits:01': 37}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 43, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 37}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x43, `+0x7140` x37 |
| `rec59-c1` | `+0x71c0` x80 |
| `rec59-c2` | `+0x7200` x80 |

## By Stimulus

### getconfig-variants

#### baseline-no-stimulus

- captures: `8`
- adjacency: `{'edge-bits:01': 4, 'full-adjacent': 4}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x4, `+0x7180` x4 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### ctrl-01-current-sf0000

- captures: `8`
- adjacency: `{'full-adjacent': 5, 'edge-bits:01': 3}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 5, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 3}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x5, `+0x7140` x3 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### r4-01-current-sf0000

- captures: `8`
- adjacency: `{'full-adjacent': 6, 'edge-bits:01': 2}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 6, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 2}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x6, `+0x7140` x2 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### r4-fe-current-sf0000

- captures: `8`
- adjacency: `{'full-adjacent': 4, 'edge-bits:01': 4}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x4, `+0x7140` x4 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### r5-01-current-sf0000

- captures: `8`
- adjacency: `{'full-adjacent': 5, 'edge-bits:01': 3}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 5, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 3}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x5, `+0x7140` x3 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### r5-0f-current-sf0000

- captures: `8`
- adjacency: `{'edge-bits:01': 4, 'full-adjacent': 4}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x4, `+0x7180` x4 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### r5-f0-current-sf0000

- captures: `8`
- adjacency: `{'full-adjacent': 4, 'edge-bits:01': 4}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 4}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x4, `+0x7140` x4 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### r6-01-current-sf0000

- captures: `8`
- adjacency: `{'edge-bits:01': 5, 'full-adjacent': 3}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 5, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 3}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x5, `+0x7180` x3 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### std-current-sf0000-len00fc

- captures: `8`
- adjacency: `{'full-adjacent': 6, 'edge-bits:01': 2}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 6, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 2}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x6, `+0x7140` x2 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

#### std-current-sf0020-len00fc

- captures: `8`
- adjacency: `{'edge-bits:01': 6, 'full-adjacent': 2}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 6, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 2}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x6, `+0x7180` x2 |
| `rec59-c1` | `+0x71c0` x8 |
| `rec59-c2` | `+0x7200` x8 |

