# Normal Work-Window Contig Hits By Stimulus

Contig: `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin`
Length: `192` bytes / `3` chunks

## Totals

| state | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `stock` | 32 | 0 | `{'3': 32}` | - |
| `old_mutated` | 32 | 15 | `{'3': 32}` | `+0x7180` x15 |
| `current96` | 96 | 50 | `{'3': 96}` | `+0x7180` x50 |
| `current288` | 288 | 134 | `{'3': 288}` | `+0x7180` x134 |

## By Stimulus

### stock

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 8 | 0 | `{'3': 8}` | - |
| `r5-0f-current-sf0000` | 8 | 0 | `{'3': 8}` | - |
| `r5-f0-current-sf0000` | 8 | 0 | `{'3': 8}` | - |
| `std-current-sf0000-len00fc` | 8 | 0 | `{'3': 8}` | - |

### old_mutated

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 8 | 5 | `{'3': 8}` | `+0x7180` x5 |
| `r5-0f-current-sf0000` | 8 | 1 | `{'3': 8}` | `+0x7180` x1 |
| `r5-f0-current-sf0000` | 8 | 4 | `{'3': 8}` | `+0x7180` x4 |
| `std-current-sf0000-len00fc` | 8 | 5 | `{'3': 8}` | `+0x7180` x5 |

### current96

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 16 | 9 | `{'3': 16}` | `+0x7180` x9 |
| `get-configuration-all` | 16 | 8 | `{'3': 16}` | `+0x7180` x8 |
| `get-configuration-current` | 16 | 9 | `{'3': 16}` | `+0x7180` x9 |
| `inquiry-extrainq` | 16 | 7 | `{'3': 16}` | `+0x7180` x7 |
| `inquiry-standard-96` | 16 | 9 | `{'3': 16}` | `+0x7180` x9 |
| `mode-sense10-read-error-recovery` | 16 | 8 | `{'3': 16}` | `+0x7180` x8 |

### current288

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 48 | 21 | `{'3': 48}` | `+0x7180` x21 |
| `get-configuration-all` | 48 | 21 | `{'3': 48}` | `+0x7180` x21 |
| `get-configuration-current` | 48 | 25 | `{'3': 48}` | `+0x7180` x25 |
| `inquiry-extrainq` | 48 | 25 | `{'3': 48}` | `+0x7180` x25 |
| `inquiry-standard-96` | 48 | 21 | `{'3': 48}` | `+0x7180` x21 |
| `mode-sense10-read-error-recovery` | 48 | 21 | `{'3': 48}` | `+0x7180` x21 |

## Chunk Offsets

### stock
- chunk 0: `+0x7140` x26, `+0x7180` x6
- chunk 1: `+0x7100` x32
- chunk 2: `+0x72c0` x32

### old_mutated
- chunk 0: `+0x7140` x17, `+0x7180` x15
- chunk 1: `+0x71c0` x32
- chunk 2: `+0x7200` x32

### current96
- chunk 0: `+0x7180` x50, `+0x7140` x46
- chunk 1: `+0x71c0` x96
- chunk 2: `+0x7200` x96

### current288
- chunk 0: `+0x7140` x154, `+0x7180` x134
- chunk 1: `+0x71c0` x288
- chunk 2: `+0x7200` x288

