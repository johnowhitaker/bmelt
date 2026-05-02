# Normal IO Targets With Affine Evidence

The record-55 `+0x400` hard-lane probe showed that arbitrary CDD source bytes
can be boot-critical even when the decoded-runtime tiles are host-visible. This
note re-ranks the normal IO candidates by a stricter criterion: does the
candidate record's four-record group have a statically decoded affine leaf byte
in LD5M?

This is still not a proof of safety. It is a better live-test heuristic because
the affine cells are a visible, structured CDD layer we can recompute, unlike
the hard-lane bytes.

## Top Normal IO Records

| record | score | record group | LD5M affine group? | note |
|---:|---:|---:|---|---|
| 55 | 1546.5 | 13 | no | strong read-only surface; first hard-lane mutation was hazardous |
| 58 | 1286.8 | 14 | no | GET CONFIG read/bridge target; no LD5M affine leaf in group |
| 66 | 1281.6 | 16 | no | controller/status bridge target; no LD5M affine leaf in group |
| 51 | 1210.2 | 12 | no | high coverage, but LD5M lacks local affine evidence |
| 60 | 1090.3 | 15 | yes, plain `0xc9` | best next safer live candidate |
| 70 | 937.0 | 17 | no | strong but hard-lane only |
| 87 | 880.1 | 21 | no | high coverage but likely packet/handler sensitive |
| 62 | 409.2 | 15 | yes, plain `0xc9` | same affine group as record 60 |

## Recommended Next Safer Probe

Record 60 is not the highest-scoring target, but its four-record group
(`60..63`) has an LD5M affine leaf at record 63/cell 15. The decoded interval
for that group is:

```text
0x18b2a0..0x18b8df
```

That interval covers the same group as record 60's normal work-window chunks,
including:

```text
4cfa6d151318
28583441dfa8
9b673c066ae4
```

The bit-clear affine patch plan is:

```text
stock plain:  0xc9
target plain: 0xcb
patch:        F0[0x2ae8f] 0x4e -> 0x4c
restore:      F0[0x2ae8f] 0x4c -> 0x4e
```

Generated plan:

```text
analysis/8051/record60-affine-group15-c9-to-cb-bitclear-plan-20260502.md
analysis/8051/record60-affine-group15-c9-to-cb-bitclear-plan-20260502.json
```

There is also a one-bit semantic decrement plan (`plain 0xc9 -> 0xc8`), but it
requires raw `0x4e -> 0x4f`, which is less attractive because the on-flash byte
change sets a bit. The bit-clear plan above keeps the flash mutation style
closer to the previous safe probes.

## Live Discipline

Do not run this while the record-55 state is unresolved. First recover or swap
to a drive with a known optical LUN, then restore any lingering record-55
mutation.

If the record-60 affine probe is run later:

1. Capture a stock record-60 baseline.
2. Apply `0x2ae8f:4c` through the helper bypass.
3. Cold boot.
4. Capture the same normal work-window set.
5. Restore `0x2ae8f:4e` before trying any hard-lane mutation.

Expected useful outcomes:

- If the drive boots and record-60 chunks move/reorder, affine cells are safer
  normal IO oracles than arbitrary hard-lane bytes.
- If the drive boots but record-60 chunks are unchanged, the affine byte may be
  metadata/control for the CDD group rather than local decoded tile content.
- If the optical LUN disappears, even affine group-15 mutation is unsafe and
  live CDD perturbation should pause until a stronger restore path exists.
