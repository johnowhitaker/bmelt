# Original Drive Record-59 Expanded Read-Only Capture

Date: 2026-05-02

This is a read-only follow-up on the original drive, which currently still has
the persistent record-59 CDD byte mutation:

```text
F0[0x28519] = 0x60   stock LD5M is 0x68
```

No helper-bypass writes, profile-tail entry, START STOP, or nominal
GET PERFORMANCE commands were sent in this run.

## Live Run

Capture directory:

```text
references/evidence/live/original-drive-rec59-focused-safe-20260502T030437Z/
```

Stimuli:

```text
baseline-no-stimulus
inquiry-standard-96
inquiry-extrainq
get-configuration-current
get-configuration-all
mode-sense10-read-error-recovery
```

The capture ran for 48 cycles, producing 288 work-window snapshots. Post-run
status still reported the optical LUN as:

```text
PLDS DVD+-RW DS-8ABSH LD5M
```

So this focused read-only set remains safe on the currently installed original
drive state.

## Contig 4 Result

The watched decoded-runtime contig is:

```text
analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin
```

It consists of three 64-byte chunks:

```text
20ea2ab16891 -> 99d4493dc4cf -> b7a129b7d392
```

The expanded run confirmed the earlier result:

| state | captures | full contig hits | hit offset |
|---|---:|---:|---|
| stock reference | 32 | 0 | - |
| old record-59 mutated | 32 | 15 | `+0x7180` |
| current original, 96 snapshots | 96 | 50 | `+0x7180` |
| current original, 288 snapshots | 288 | 134 | `+0x7180` |

The component chunks were visible in every capture. The mutation mainly changes
their adjacency/placement:

```text
stock:
  chunk0 at +0x7140/+0x7180
  chunk1 at +0x7100
  chunk2 at +0x72c0
  no full contig sequence

record-59 mutated:
  chunk0 at +0x7140 or +0x7180
  chunk1 fixed at +0x71c0
  chunk2 fixed at +0x7200
  full sequence appears when chunk0 is at +0x7180
```

In the 288-snapshot run, chunk0 was at `+0x7180` in 134 captures and `+0x7140`
in 154 captures. That explains the full-contig hit rate without requiring any
change to the three chunk byte strings themselves.

## Interpretation

The persistent `0x28519: 0x68 -> 0x60` edit does not look like a direct edit of
an instruction byte in the decoded output. It behaves like a schedule,
interleaver, or tile-placement control byte for the public work-window surface.

That is still valuable: it proves a single hard-lane CDD source byte can alter
normal-mode decoded-runtime presentation in a repeatable way. But it also means
record-59 is not a clean flat source-to-output decode oracle.

There is an important alternate framing: this may be a correctable CDD-codeword
error rather than an intentional schedule-byte edit. The public decoded chunks
we can recognize stay byte-identical, but their tile phase changes. A quick
stock-versus-mutated unique-chunk comparison found no near one-byte decoded
variants:

```text
stock unique chunks:     721
mutated unique chunks:   716
only-mutated chunks:      37
only-stock chunks:        42
nearest only-mutated to only-stock chunk: 35/64 bytes different
chunks within 8 byte differences: 0
```

So the visible effect is not "one decoded byte changed." It is more consistent
with "the controller still materialized the same decoded payload tiles, but the
decode/status/timing path changed." If CDD is an ECC-like controller codeword
format, this is exactly the kind of side effect a corrected source-byte error
could produce.

The expanded run gives us a stable mutated-state baseline for future read-only
work. It also reinforces that the public window is a rotating surface, not a
simple memory dump. Any future CDD known-output extraction should use chunk
identity and adjacency, not only absolute public offsets.

## New Offline Tool

Added:

```text
scripts/analyze_liteon_work_window_state_delta.py
```

It compares normal work-window states at the 64-byte chunk and adjacent-edge
level, then annotates chunks with candidate CDD records from the known-output
corpus.

The most useful generated reports from this pass are:

```text
analysis/8051/original-drive-rec59-expanded-contig4-hits-20260502.md
analysis/8051/original-drive-rec59-expanded-state-delta-20260502.md
analysis/8051/rec59-getcfg-stock-vs-mutated-state-delta-20260502.md
```

The `current96` versus `current288` state delta is mostly a phase/stability
audit of the same mutated drive, not a mutation comparison. The stock-versus-old
mutated delta is the better record-59 mutation comparison, but it used a
different GET CONFIG-focused stimulus set than the new read-only run.

## Practical Takeaway

- The original drive is still usable for read-only normal-mode work.
- The focused-safe stimulus set is currently the preferred normal-mode capture
  set for this drive.
- The record-59 mutation is persistent and meaningful, but it should not be
  stacked with more live mutations on this drive.
- The next live writes should wait for a clean/recoverable optical LUN.
- For now, the profitable path is static analysis plus read-only public-window
  harvesting from the original drive.
