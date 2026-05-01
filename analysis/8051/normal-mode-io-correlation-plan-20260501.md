# Normal-Mode I/O Correlation Plan

Date: 2026-05-01

Scope: planning and offline analysis only. No live drive commands were sent for
this note.

## What Changed

The second reversible CDD affine edit gives us a cleaner target set for normal
mode I/O work.

- Group 105: decoded CDD affine byte `0x84` was changed to `0x85` and `0x8b`,
  then restored. The group-105 report found `62` clean reversible public-window
  chunk offsets.
- Group 99: decoded CDD affine byte `0x0a` was changed to `0x0b`, then
  restored. The group-99 report found `107` clean stock-consistent public-window
  chunk offsets.
- Cross-group overlap: `31` offsets react to both independent CDD leaf edits.

These are not decoded CDD bytes. The normal `READ BUFFER id=01/02
offset=0x070000` surface still rotates whole `0x40`-byte tiles. The useful
advance is that we now have a higher-confidence list of places where normal
runtime state is sensitive to two different CDD leaf edits.

## Best Overlap Targets

The full overlap is in:

```text
analysis/8051/cdd-affine-cross-group-correlation-20260501.md/json
```

The most useful starting offsets are:

```text
0x01c0  low compact controller/status-looking row
0x0280  low compact controller/status-looking row
0x7140  response-bridge-adjacent tile
0x7180  response-bridge-adjacent tile
0x8f40  repeated exact stock/mutation tile participant
0x8fc0  paired with 0x8f40
0x9b00  three-way tile-rotation participant
0x9b40  three-way tile-rotation participant
0x9b80  three-way tile-rotation participant
```

The `0x7140/0x7180` pair remains attractive because it overlaps the earlier
response-bridge story. The `0x9b00/0x9b40/0x9b80` trio is attractive for a
different reason: both CDD edits perturb a compact rotation among the same few
code-looking chunks, which may be easier to recognize after a hook changes one
byte or one phase bit.

## How To Use This

The normal-mode I/O problem is still not "write a byte to public offset X." The
public offset is a viewing slot. A better workflow is:

1. Pick a tiny normal-mode hook that should perturb one bridge/status byte or
   one tile phase, preferably in a region already seen in currentboot and normal
   captures.
2. Cold boot into normal mode.
3. Capture the same `id=01/02 offset=0x070000 length=0x10000` work-window
   repeats.
4. Compare only against the overlap offsets, not the whole noisy window.
5. Promote offsets that respond in the predicted direction and remain stable
   across a restore.

That gives us a practical detector for "our normal-mode hook ran" even before
we have a direct SCSI response channel or LED channel.

## Patch-Site Implications

The response-bridge pair is not the only candidate. The stronger carryover
candidate from the previous normal/currentboot overlap work is still the
controller write helper around normal offsets:

```text
0xdbc0
0xdc00
0xdc40
```

Those chunks appeared in every normal capture and matched the saved currentboot
gateway dump. They touch `0x4095..0x4098`, so they are not casual patch sites,
but they are much more likely than a random public-window row to exist in both
the currentboot staging context and normal runtime.

The next normal-mode proof should therefore be a marker/carryover test, not a
mechanical command:

- alter one harmless-looking byte in a shared normal/currentboot chunk;
- use a full hardware cold boot;
- check whether any cross-group overlap offsets change in a repeatable way;
- restore immediately if the public identity or work-window surface looks odd.

## What This Does Not Solve

This does not decode CDD, and it does not prove a writable normal-mode SCSI
reply path. It narrows the search by giving us a much better observable:

```text
CDD leaf edit -> normal runtime perturbation -> public work-window offset set
```

That observable can be reused while trying normal-mode hooks, LED/button
bridges, or future controller-mailbox experiments.
