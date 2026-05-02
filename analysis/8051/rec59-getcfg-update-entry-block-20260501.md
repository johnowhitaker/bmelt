# Record 59 GET CONFIG Follow-Up And Update-Entry Block

## Target

- CDD stream: CDD1
- Candidate record: `59`
- Record source range: `0x28119..0x28ab7`
- Record operation key: `30ca94930e05`
- Candidate decoded/public span: `+0x7170..+0x729f`
- F0 patch: `0x28519: 68 -> 60`
- Patch relative to record source: `+0x400`
- Runtime contig: `analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin`

This repeats the earlier record-59 perturbation, but captures focused
`GET CONFIGURATION` variants instead of only `GET PERFORMANCE type 00`.
The source/runtime alignment is unusually clean: the contig's full-sequence
hits appear at public offset `+0x7180`, which is only `+0x10` into record 59's
candidate decoded span. The patched source byte is exactly `+0x400` into the
encoded record.

The known-output export lines up exactly with that interpretation:

```text
record-059-known-output.bin length = 0x130
known mask range                 = +0x10..+0xcf
known bytes in that range        = contig-004-03chunks.bin byte-for-byte
```

So record 59 currently gives a compact known pair:

```text
encoded source:  0x28119..0x28ab6, with live patch at +0x400
decoded surface: +0x7170..+0x729f, with known contig at +0x10..+0xcf
```

## Persistence

The mutation run stopped at final selector-15 with a host transport error:

```text
3B 05 01 00 00 00 00 00 10 80 0F 00
Host_status=0x07 [DID_ERROR]
SCSI Status: Good
```

Despite that, a live-key sequential F0 read of `0x000000..0x030000` showed:

```text
F0[0x28519] = 0x60
```

So the final host error can still accompany a persistent flash change.

## GET CONFIG Responses

The ordinary host-visible response payloads did not change:

```text
std-current-sf0000-len00fc  stock == mutated
r5-0f-current-sf0000        stock == mutated
r5-f0-current-sf0000        stock == mutated
```

See:

```text
analysis/8051/rec59-getcfg-response-diff-20260501.md
```

## Work-Window Effect

The public work-window did change. In this corpus, all component chunks remained
visible in both states, but full contig adjacency flipped:

| state | captures | full contig-4 hits |
|---|---:|---:|
| stock | 32 | 0 |
| mutated | 32 | 15 |

All full mutated hits appeared at public offset `+0x7180`.

This differs from the earlier `GET PERFORMANCE` corpus, where the same mutation
removed full-sequence hits. The safe interpretation is that record 59 controls
tile ordering/placement in the normal decoded-runtime surface, not a stable flat
decoded byte span.

One important detail: the component chunks stayed byte-identical and visible.
The mutation changed their public placement/adjacency, not the chunk bytes
themselves. That makes `0x28519` look more like schedule/interleaver/control
material for the decoded tile neighborhood than direct encoded payload for one
instruction byte.

See:

```text
analysis/8051/rec59-getcfg-contig4-hits-by-stimulus-20260501.md
analysis/8051/rec59-getcfg-work-window-diff-20260501.md
```

## Restore Problem

After reinstalling this mutation, the normal firmware-update entry path stopped
working on Linux drive #1. These probes all timed out or returned host transport
errors while the drive still reported normal `LD5M` after cold boot:

- normal LD5M event-1 pre-tail;
- currentboot-key tail;
- direct event-2 `arg=00` chunk staging without a tail;
- failed pre-tail followed by direct event-2 chunk staging.

A second live-key sequential F0 read still showed:

```text
F0[0x28519] = 0x60
```

So record 59 should no longer be treated as a clean reversible live oracle on
the current Linux drive. It is a very useful static clue, because it appears to
touch the normal update/response bridge neighborhood, but it is a bad target for
more casual mutations unless a fresh drive or out-of-band flash restore is
available.
