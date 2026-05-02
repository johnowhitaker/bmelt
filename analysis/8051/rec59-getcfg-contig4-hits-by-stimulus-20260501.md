# Normal Work-Window Contig Hits By Stimulus

Contig: `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin`
Length: `192` bytes / `3` chunks

## Totals

| state | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `stock` | 32 | 0 | `{'3': 32}` | - |
| `mutated` | 32 | 15 | `{'3': 32}` | `+0x7180` x15 |

## By Stimulus

### stock

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 8 | 0 | `{'3': 8}` | - |
| `r5-0f-current-sf0000` | 8 | 0 | `{'3': 8}` | - |
| `r5-f0-current-sf0000` | 8 | 0 | `{'3': 8}` | - |
| `std-current-sf0000-len00fc` | 8 | 0 | `{'3': 8}` | - |

### mutated

| stimulus | captures | full-sequence hits | chunk-count histogram | sequence offsets |
|---|---:|---:|---|---|
| `baseline-no-stimulus` | 8 | 5 | `{'3': 8}` | `+0x7180` x5 |
| `r5-0f-current-sf0000` | 8 | 1 | `{'3': 8}` | `+0x7180` x1 |
| `r5-f0-current-sf0000` | 8 | 4 | `{'3': 8}` | `+0x7180` x4 |
| `std-current-sf0000-len00fc` | 8 | 5 | `{'3': 8}` | `+0x7180` x5 |

## Chunk Offsets

### stock
- chunk 0: `+0x7140` x26, `+0x7180` x6
- chunk 1: `+0x7100` x32
- chunk 2: `+0x72c0` x32

### mutated
- chunk 0: `+0x7140` x17, `+0x7180` x15
- chunk 1: `+0x71c0` x32
- chunk 2: `+0x7200` x32

