# Record 59 Static Neighborhood

This note ties the record-59 live perturbation back to the decoded CDD runtime bytes. It is static analysis only.

## Focus Records

| record | source | len | decoded | span | mode | op key | known ranges | rel +0x400 |
|---:|---:|---:|---:|---:|---:|---|---|---:|
| 57 | `0x27075` | `0x7b0` | `+0x6e20` | `0x130` | `0x40` | `3512d253d403` | +0x60..+0x12f | `0xc2` |
| 58 | `0x27825` | `0x8f4` | `+0x6f50` | `0x220` | `0x80` | `66228ca20005` | +0x30..+0x21f | `0xd3` |
| 59 | `0x28119` | `0x99e` | `+0x7170` | `0x130` | `0x80` | `30ca94930e05` | +0x10..+0xcf | `0x68` |
| 60 | `0x28ab7` | `0x928` | `+0x72a0` | `0x350` | `0x40` | `950a90757805` | +0x20..+0x11f, +0x1e0..+0x34f | `0xf2` |
| 66 | `0x2bc14` | `0x96b` | `+0x7db0` | `0x2d0` | `0x80` | `4e8210adb204` | +0x10..+0x2cf | `0xe4` |
| 70 | `0x2e0cd` | `0x9dd` | `+0x8700` | `0x230` | `0x80` | `098ad4a36805` | +0x0..+0x1bf | `0x58` |
| 84 | `0x35f9b` | `0x896` | `+0x94e0` | `0xa0` | `0x80` | `3b0a538aa203` | +0x20..+0x9f | `0xfd` |
| 85 | `0x36831` | `0x8be` | `+0x9580` | `0x300` | `0x40` | `5f925170d804` | +0x0..+0x7f, +0x280..+0x2ff | `0x1d` |

## Record 59 Decoded Shape

The known output for record 59 is exactly one 192-byte contig at `+0x10..+0xcf`. The first function is a controller-command bridge:

- reads `xdata[0x8a29]`, swaps/masks the high nibble, and branches on bit 0;
- copies or clamps CDB shadow byte `xdata[0x8a4c]` into `xdata[0x4011]`;
- copies `xdata[0x8a4d]` and `xdata[0x8a4e]` into `xdata[0x4012]` and `xdata[0x4013]`;
- copies `xdata[0x8a50..0x8a51]` into IRAM scratch around `0xa9..0xaa`;
- sets an IRAM flag byte to `0x01`, calls `0xefb6`, advances `0x7c` twice, then returns.

The second visible function copies `0x8857/0x8858/0x84af/0x84b0` into `0x885d..0x8860`, writes command-like pairs through `0x8859/0x885a` and `0x893c`, then calls `0x0a65` and `0x0a6b`.

## Record 59 Call Targets

| target | count | owner record | owner decoded span | op key |
|---:|---:|---:|---:|---|
| `0xefb6` | 1 | 137 | `+0xee50..+0xf08f` | `87804e645c03` |
| `0x0a65` | 1 | 5 | `+0x9b0..+0xd8f` | `4e3ad47ecc04` |
| `0x0a6b` | 1 | 5 | `+0x9b0..+0xd8f` | `4e3ad47ecc04` |

This is a useful correction: the `0xefb6`, `0x0a65`, and `0x0a6b` targets are not useful resident-prefix disassembly targets. They are inside other CDD decoded records.

## Interesting DPTR Immediates

| dptr | count | note |
|---:|---:|---|
| `0x8a4c` | 2 | CDB shadow byte 0 |
| `0x4011` | 2 | controller CDB/arg byte 0 |
| `0x885d` | 2 | response/setup destination byte 0 |
| `0x885e` | 2 | response/setup destination byte 1 |
| `0x885f` | 2 | response/setup destination byte 2 |
| `0x8860` | 2 | response/setup destination byte 3 |
| `0x8a4d` | 1 | CDB shadow byte 1 |
| `0x4012` | 1 | controller CDB/arg byte 1 |
| `0x8a4e` | 1 | CDB shadow byte 2 |
| `0x4013` | 1 | controller CDB/arg byte 2 |
| `0x8a50` | 1 | CDB shadow byte 4/transfer high |
| `0x8857` | 1 | response/setup source byte 0 |
| `0x8858` | 1 | response/setup source byte 1 |
| `0x8859` | 1 | response/setup length/command high |
| `0x893c` | 1 | response/setup control byte |

## Practical Read

- Record 59 is now best treated as an update/response bridge control neighborhood, not a payload string or simple response buffer.
- The live `0x28519: 0x68 -> 0x60` byte is record-relative `+0x400`. Saved captures showed chunk placement changes without byte changes, so it probably modified a CDD schedule/interleaver/control cell for this bridge neighborhood.
- Because this same mutation blocked update entry on the previous drive, avoid record 58/59 writes on the spare unless the experiment explicitly needs that risk.
- Safer static follow-up: target the call owners, especially record 137 around `0xefb6`, for read-only work-window harvests or source/known-output recovery. That may reveal the bridge submit routine without perturbing record 59 again.

