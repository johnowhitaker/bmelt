# Original Drive Normal-Mode I/O Primitive Checkpoint

This run implemented the next-phase normal-mode I/O plan against the original
drive, now back on Linux as `/dev/sg0`.

## Starting State

The drive still reports normal `LD5M`:

```text
/dev/sg0: PLDS DVD+-RW DS-8ABSH LD5M
```

A focused live-key F0 read confirmed the expected state before any write
attempt:

```text
F0[0x2627a] = 0x5d   record55 byte is stock
F0[0x28519] = 0x60   record59 mutation remains installed
F0[0x2ae8f] = 0x4e   record60 affine candidate is stock
```

Baseline evidence:

```text
references/evidence/live/original-drive-normal-io-baseline-20260502T032421Z/
```

## Read-Only Baseline

The focused-safe baseline used only:

- baseline/no stimulus;
- standard INQUIRY;
- EXTRAINQ;
- GET CONFIGURATION current/all;
- MODE SENSE(10) read-error recovery.

It avoided the unhealthy `GET PERFORMANCE nominal` path. The drive stayed
visible as normal `LD5M`.

Record 59 remains the useful phase oracle. Its three watched chunks are always
visible, but chunk 0 alternates between two slots:

```text
rec59-c0: +0x7140 or +0x7180
rec59-c1: +0x71c0
rec59-c2: +0x7200
```

The full contig sequence appears only when chunk 0 is at `+0x7180`:

```text
20ea2ab16891 -> 99d4493dc4cf -> b7a129b7d392
```

In this 96-capture baseline:

```text
full-adjacent: 50
edge-bits:01: 46
```

Record 60 is much more stable. The watched chunks appeared in every capture at
fixed offsets:

```text
rec60-c0 4cfa6d151318: +0x7300
rec60-c1 28583441dfa8: +0x7380
rec60-c2 9b673c066ae4: +0x7480
```

They do not form a simple contiguous 3-chunk run in the public surface, but the
layout is stable enough to be a good future mutation watch target.

Analysis:

```text
analysis/8051/original-drive-normal-io-baseline-rec59-watch-20260502.md
analysis/8051/original-drive-normal-io-baseline-rec60-watch-20260502.md
analysis/8051/original-drive-normal-io-baseline-contig4-hits-20260502.md
analysis/8051/original-drive-normal-io-baseline-contig18-hits-20260502.md
```

## Update-Entry Viability

The prepared record60 affine patch/restore artifacts were built offline:

```text
patch:   F0[0x2ae8f] 0x4e -> 0x4c
restore: F0[0x2ae8f] 0x4c -> 0x4e
```

But the live run stopped at the viability gate. Sending only events `0..1`
from the patch candidate produced the same blocked update-entry behavior seen
after the record59 mutation:

```text
event=0 phase=live_extrainq_read rc=0
event=1 phase=profile_tail_arg7f rc=99
```

The runner then hung trying to status/recover through the wedged sg command.
I killed the hung process and used the Pico servo power cut. The drive came
back as normal `LD5M`.

Because this was only the entry event, the record60 patch was never sent. A
live-key F0 read after the servo cycle confirmed:

```text
F0[0x2627a] = 0x5d
F0[0x28519] = 0x60
F0[0x2ae8f] = 0x4e
```

Post-viability F0 evidence:

```text
references/evidence/live/original-drive-normal-io-post-viability-f0-livekey-20260502T033149Z/
```

Practical result: the original drive is still useful, but not for ordinary
helper-bypass write attempts while the record59 mutation is present. Treat it
as a mutated-but-alive normal-mode oracle until we have a different restore or
write path.

## GET CONFIG Variant Read-Only Probes

Since live writes stopped, I ran read-only GET CONFIG field variants to see
whether host-controlled fields bias the existing record59 phase oracle or touch
record60's bridge-adjacent chunks.

First pass:

```text
references/evidence/live/original-drive-normal-io-getconfig-variants-20260502T033434Z/
```

Second focused phase-bias pass:

```text
references/evidence/live/original-drive-normal-io-getconfig-phase-bias-20260502T033558Z/
```

All tested GET CONFIG response payloads were byte-stable:

```text
std-current-sf0000-len00fc  24/24 good, one response hash
std-current-sf0020-len00fc  24/24 good, one response hash
r4-01-current-sf0000        24/24 good, one response hash
r6-01-current-sf0000        24/24 good, one response hash
```

Record60 remained fixed in all 120 phase-bias captures:

```text
rec60-c0@+0x7300 rec60-c1@+0x7380 rec60-c2@+0x7480: 120/120
```

Record59 showed small phase-ratio differences, but nothing strong enough to
call a host-controlled bit:

```text
baseline-no-stimulus        full 13/24
std-current-sf0000-len00fc  full 15/24
std-current-sf0020-len00fc  full 14/24
r4-01-current-sf0000        full  9/24
r6-01-current-sf0000        full 13/24
```

That is useful as a classifier but not yet a communication primitive. It looks
like ambient phase/timing plus maybe weak scheduling bias, not a clean command
field to output bit path.

Analysis:

```text
analysis/8051/original-drive-normal-io-getconfig-variants-rec59-watch-20260502.md
analysis/8051/original-drive-normal-io-getconfig-variants-rec60-watch-20260502.md
analysis/8051/original-drive-normal-io-getconfig-phase-bias-rec59-watch-20260502.md
analysis/8051/original-drive-normal-io-getconfig-phase-bias-rec60-watch-20260502.md
```

## New Helper

I added a compact watch-chunk analyzer:

```text
scripts/analyze_liteon_work_window_watch_chunks.py
```

It tracks selected 64-byte chunks by state and stimulus, reports offsets, and
summarizes whether the chunks form adjacent runs. This is now the quick way to
classify record59/record60 phase behavior after future normal-mode captures.

The third record60 watch chunk was also saved as a standalone artifact:

```text
analysis/8051/watch-chunks-20260502/record60-c2-9b673c066ae4.bin
```

## Current Practical State

- Original drive: alive as normal `LD5M`; useful for read-only normal-mode
  oracle work; not clean stock; normal update-entry/helper-bypass path is
  blocked.
- Spare drive: bridge/card-reader only; no PLDS optical LUN; effectively
  unavailable for SCSI-side experiments until deeper recovery exists.
- Incoming fresh drives: best next live mutation targets.

## Next Work

1. On a fresh drive, capture a clean normal baseline and verify stock F0.
2. Re-run the record60 affine probe there, with immediate restore.
3. If record60 gives a reversible tile/edge effect, use the watch-chunk tool to
   test host-command modulation.
4. If normal helper-bypass entry blocks after record59-style mutations again,
   prioritize finding an out-of-band restore/write route before using the last
   good drive for more CDD writes.
5. In parallel, continue static work around records 58/59/60 and the controller
   bridge snippets. The normal-mode I/O primitive is likely in this area, but
   the current original drive can only safely show us read-only phase behavior.
