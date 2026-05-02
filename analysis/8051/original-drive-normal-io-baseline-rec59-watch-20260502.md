# Normal Work-Window Watch Chunks

## Chunks

| name | sha256 | first bytes |
|---|---|---|
| `rec59-c0` | `20ea2ab16891b5c70526dc35ea5187e6ab4d45b592920d95e255f52d34a09baa` | `8a29e0c4540f30e011908a4ce0c3940e` |
| `rec59-c1` | `99d4493dc4cfdc4cea75d21f27ed90af53b0f067d9238f902e536c1eec033b29` | `f608760112efb6057c057c22908857e0` |
| `rec59-c2` | `b7a129b7d392f0209ca71625dbfb5e4a1609c0ae26b96d7cc940ea0582952c49` | `e054884efeef4ef07e007f08120a65e4` |

## Totals

### original-baseline

- captures: `96`
- adjacency: `{'full-adjacent': 50, 'edge-bits:01': 46}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 50, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 46}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x50, `+0x7140` x46 |
| `rec59-c1` | `+0x71c0` x96 |
| `rec59-c2` | `+0x7200` x96 |

## By Stimulus

### original-baseline

#### baseline-no-stimulus

- captures: `16`
- adjacency: `{'edge-bits:01': 8, 'full-adjacent': 8}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 8, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 8}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x8, `+0x7180` x8 |
| `rec59-c1` | `+0x71c0` x16 |
| `rec59-c2` | `+0x7200` x16 |

#### get-configuration-all

- captures: `16`
- adjacency: `{'full-adjacent': 9, 'edge-bits:01': 7}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 9, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 7}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x9, `+0x7140` x7 |
| `rec59-c1` | `+0x71c0` x16 |
| `rec59-c2` | `+0x7200` x16 |

#### get-configuration-current

- captures: `16`
- adjacency: `{'edge-bits:01': 9, 'full-adjacent': 7}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 9, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 7}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x9, `+0x7180` x7 |
| `rec59-c1` | `+0x71c0` x16 |
| `rec59-c2` | `+0x7200` x16 |

#### inquiry-extrainq

- captures: `16`
- adjacency: `{'full-adjacent': 9, 'edge-bits:01': 7}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 9, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 7}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x9, `+0x7140` x7 |
| `rec59-c1` | `+0x71c0` x16 |
| `rec59-c2` | `+0x7200` x16 |

#### inquiry-standard-96

- captures: `16`
- adjacency: `{'edge-bits:01': 8, 'full-adjacent': 8}`
- layouts: `{'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 8, 'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 8}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7140` x8, `+0x7180` x8 |
| `rec59-c1` | `+0x71c0` x16 |
| `rec59-c2` | `+0x7200` x16 |

#### mode-sense10-read-error-recovery

- captures: `16`
- adjacency: `{'full-adjacent': 9, 'edge-bits:01': 7}`
- layouts: `{'rec59-c0@+0x7180 rec59-c1@+0x71c0 rec59-c2@+0x7200': 9, 'rec59-c0@+0x7140 rec59-c1@+0x71c0 rec59-c2@+0x7200': 7}`

| chunk | offsets |
|---|---|
| `rec59-c0` | `+0x7180` x9, `+0x7140` x7 |
| `rec59-c1` | `+0x71c0` x16 |
| `rec59-c2` | `+0x7200` x16 |

