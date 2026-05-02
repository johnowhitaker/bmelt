# Normal Work-Window Contig Hits By Stimulus

Contig: `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin`
Length: `192` bytes / `3` chunks

## Totals

| state | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `stock` | 32 | 0 | `{'3': 32}` | - |
| `old_mutated` | 32 | 15 | `{'3': 32}` | `+0x7180` x15 |
| `current_small` | 28 | 10 | `{'3': 28}` | `+0x7180` x10 |
| `current_focused` | 96 | 50 | `{'3': 96}` | `+0x7180` x50 |

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

### current_small

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 4 | 1 | `{'3': 4}` | `+0x7180` x1 |
| `get-configuration-all` | 4 | 1 | `{'3': 4}` | `+0x7180` x1 |
| `get-configuration-current` | 4 | 3 | `{'3': 4}` | `+0x7180` x3 |
| `get-performance-type00` | 4 | 2 | `{'3': 4}` | `+0x7180` x2 |
| `inquiry-extrainq` | 4 | 1 | `{'3': 4}` | `+0x7180` x1 |
| `inquiry-standard-96` | 4 | 1 | `{'3': 4}` | `+0x7180` x1 |
| `mode-sense10-read-error-recovery` | 4 | 1 | `{'3': 4}` | `+0x7180` x1 |

### current_focused

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 16 | 9 | `{'3': 16}` | `+0x7180` x9 |
| `get-configuration-all` | 16 | 8 | `{'3': 16}` | `+0x7180` x8 |
| `get-configuration-current` | 16 | 9 | `{'3': 16}` | `+0x7180` x9 |
| `inquiry-extrainq` | 16 | 7 | `{'3': 16}` | `+0x7180` x7 |
| `inquiry-standard-96` | 16 | 9 | `{'3': 16}` | `+0x7180` x9 |
| `mode-sense10-read-error-recovery` | 16 | 8 | `{'3': 16}` | `+0x7180` x8 |

## Chunk Offsets

### stock
- chunk 0: `+0x7140` x26, `+0x7180` x6
- chunk 1: `+0x7100` x32
- chunk 2: `+0x72c0` x32

### old_mutated
- chunk 0: `+0x7140` x17, `+0x7180` x15
- chunk 1: `+0x71c0` x32
- chunk 2: `+0x7200` x32

### current_small
- chunk 0: `+0x7140` x18, `+0x7180` x10
- chunk 1: `+0x71c0` x28
- chunk 2: `+0x7200` x28

### current_focused
- chunk 0: `+0x7180` x50, `+0x7140` x46
- chunk 1: `+0x71c0` x96
- chunk 2: `+0x7200` x96

