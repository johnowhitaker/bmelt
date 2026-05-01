# CDD Affine Triple Correlation

Date: 2026-05-01

Inputs:

```text
analysis/8051/cdd-affine-g27-live-diff-20260501.json
analysis/8051/cdd-affine-g99-live-diff-20260501.json
analysis/8051/cdd-affine-g105-live-diff-20260501.json
```

## Summary

Three independent CDD affine leaf edits now have normal-mode work-window
captures:

| group | stream | stock -> mutated | clean offsets | note |
|---:|---|---|---:|---|
| 27 | CDD1 | `0xe4 -> 0xe5` | 78 | early CDD1 leaf; CDD1 F0 readback has chunk-boundary decrypt quirks |
| 99 | CDD2 | `0x0a -> 0x0b` | 107 | late CDD2 leaf |
| 105 | CDD2 | `0x84 -> 0x85/0x8b` | 62 | late CDD2 leaf, two mutations |

Pairwise overlaps:

```text
g27 ∩ g99   = 64
g27 ∩ g105  = 24
g99 ∩ g105  = 31
```

Triple overlap:

```text
g27 ∩ g99 ∩ g105 = 21
```

The 21 triple-overlap public offsets are:

```text
0x01c0
0x0280
0x6140
0x6480
0x65c0
0x6b00
0x7000
0x7080
0x78c0
0x7e40
0x80c0
0x8100
0x8d00
0x8f40
0x8fc0
0x9080
0x90c0
0x9300
0x9380
0x9d80
0x9dc0
```

## Interpretation

The triple-overlap rows are better normal-mode hook detectors than the earlier
one-off rows: three different decoded affine leaves, including one in CDD1 and
two in CDD2, perturb those public work-window offsets.

The response-bridge pair `0x7140/0x7180` is still interesting, but it is not in
the triple overlap. It reacts to both late CDD2 edits (`g99` and `g105`) and
does not react to the early CDD1 edit (`g27`) under the same clean-offset rule.
That makes it more specific than the low/tile-overlap rows, not more universal.

The strongest general detector set for future normal-mode marker/carryover
tests is therefore:

```text
0x01c0
0x0280
0x8f40
0x8fc0
0x9d80
0x9dc0
```

Those offsets are not decoded CDD addresses. They are public viewing slots that
consistently react when CDD affine leaves are perturbed. Use them as
before/after correlation targets while developing a normal-mode I/O loop.

## Readback Caution

The group-27 CDD1 mutation exposed a readback wrinkle: post-coldboot F0 dumps
around `0x43800..0x43a00` can decrypt correctly for some aligned single
`0x80` reads and incorrectly for adjacent/multi-chunk reads. The runner's
staging readbacks verified the sent chunks, the drive booted as `LD5M`, and the
restore sequence completed successfully, but CDD1 F0 spot verification is less
clean than the CDD2 group-99/group-105 pages.

For CDD1 spot checks, prefer multiple single aligned reads and avoid treating
one bad multi-chunk decrypt as proof that flash contents are zeroed.
