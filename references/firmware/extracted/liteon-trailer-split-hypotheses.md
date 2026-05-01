# LiteOn Trailer Split Hypothesis Probe

Offline only. No drive commands were sent.

This specifically tests whether the 14-byte trailer field can be split into a 2-byte Coastermelt-style additive checksum plus a 12-byte checksum over CDD 12-byte units.

## Inputs

| image | family | preword | auth14 |
| --- | --- | --- | --- |
| `LD5M` | `U8A60D5C` | `e2781a96` | `4979c08a77386c1658483bf233fe` |
| `AD12` | `S8AB0D16` | `244d39b4` | `fe3ed5cbc2002a6eb5ae0dfb5d4a` |
| `AHS9` | `S8AB0HS6` | `c1e2ab08` | `5084d8596db47bd5da64d01ad053` |
| `CD12` | `S8AB0D16` | `9cec113c` | `445c5e968b5f1fb80016fa3fdfc5` |
| `CHS7` | `S8AB0HS6` | `cc7c7447` | `f817e214ed8b13729811dfb4c2f6` |
| `CHS9` | `S8AB0HS6` | `cc7c7447` | `8061c6bb6c5f698b66425bb17dd7` |

## Result

- exact 2-byte additive matches across all images: `0`
- exact 12-byte CDD unit checksum matches across all images: `0`

## Near Misses

Near misses are included only to catch obvious one-image extraction or family anomalies. None should be treated as evidence unless the matching image set is meaningful.

- additive near misses: `0` retained
- unit-checksum near misses: `0` retained

## Interpretation

This probe is negative for the proposed split. It does not rule out a bespoke controller-side codeword, a keyed MAC, or a split field with a nontrivial algorithm. It does rule out the easy form: one contiguous 2-byte additive checksum plus a direct column-wise 12-byte checksum over the obvious CDD unit streams.
