# Drive 3 Normal-Mode Side-Channel Push

This pass started from the XD13 notes rather than from blind CDD cracking. The
goal was to see whether the XD13 plaintext 8051 islands give us enough
orientation to get a normal-mode host-visible side channel on clean Drive #3,
without relying on currentboot-only hooks.

## Safety Boundary

The useful rule from this pass is: no more casual CDD edits. Even structured
affine edits can move the controller/runtime work surface in ways that are hard
to distinguish from persistent state. Anything beyond read-only captures should
be treated as an explicit approval point.

All captures below used Drive #3 on the Linux host as `/dev/sg0`. The Pico
servo power-cycle was available from Linux as `/dev/ttyACM0`.

## Read-Only XD13 Validation

The XD13 homologs are genuinely useful on LD5M normal mode. Focused captures
showed the expected packet/bridge-looking signatures in the public normal
work-window:

- record55-ish patterns around `+0x6a00..+0x6c40`;
- record58-ish bridge/packet patterns around `+0x7050..+0x7180`;
- record60-ish bridge patterns around `+0x7300..+0x7480`.

The first focused report is:

```text
analysis/8051/drive3-normal-mode-xd13-sidechannel-watch-20260504.md
```

Read-only GET CONFIG field variants, a CDB echo scan, and a broader
error/status command corpus did not expose a response-byte echo or a clean
host-controlled bit. They were still useful because they showed that these
XD13-derived signatures are stable enough to use as watchpoints.

## Record60 Affine Probe

We then tried the prepared structured affine probe:

```text
F0[0x2ae8f] 0x4e -> 0x4c
record60/group15 affine plain 0xc9 -> 0xcb
```

This was not an arbitrary hard-lane byte; it was one of the safer affine-leaf
targets. Still, it proved why caution is warranted.

After the patch attempt, Drive #3 stayed in normal `LD5M`, and the normal
work-window changed locally in the watched record60 cluster:

```text
pre:     4cfa6d151318 @ +0x7380
patched: 4cfa6d151318 @ +0x7300

pre:     28583441dfa8 @ +0x73c0
patched: 28583441dfa8 @ +0x7380

pre:     4037c8574920 @ +0x73ce
patched: 4037c8574920 @ +0x738e
```

That initially looked like a good normal-mode oracle. The matching restore
candidate reported success and Drive #3 still booted as `LD5M`, but the
work-window did not move back to the old layout.

The important cleanup was a full sequential F0 verification after restore. The
zero-based 1 MiB dump matched stock LD5M exactly:

```text
sha256=488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39
```

So the flash image is stock. The apparent record60 effect is not yet a proven
firmware-byte-controlled bit. It is evidence that the public normal work-window
has persistent/runtime phase or tile-scheduling state that can outlive the
obvious firmware-byte experiment.

Reports:

```text
analysis/8051/drive3-record60-affine-pre-patched-restored-watch-20260504.md
analysis/8051/drive3-stock-coldboot-controls-record60-watch-20260504.md
```

## Phase Controls

After the restore and stock full-F0 verification, three stock cold-boot controls
still showed the shifted record60 layout:

```text
4cfa6d151318 @ +0x7300
28583441dfa8 @ +0x7380
9b673c066ae4 @ +0x7480
```

This makes the first pre-patch Drive #3 baseline a different runtime/viewing
state rather than a state we can currently command back into existence.

Two read-only phase tests then tried to turn the visible record58 placement into
a side channel:

- baseline-only repeated 24 times;
- GET CONFIG current repeated 24 times;
- interleaved baseline/GET CONFIG A/B;
- a broader read-only command screen.

Baseline-only was stable in one run, but the interleaved A/B showed the phase
latches and wanders in runs. The broad command screen produced several offset
pairs (`+0x70d0/+0x7140`, `+0x7090/+0x7180`, `+0x7010/+0x7140`,
`+0x7010/+0x7180`) without a reliable per-command mapping. In other words, this
surface is a useful runtime observation surface, but it is not yet a clean
normal-mode I/O bit.

## Current Conclusion

We have not yet reached a slow normal-mode side channel. We do have a better
normal-mode observation surface and a sharper warning:

- XD13 is a good atlas for LD5M normal-mode work-window snippets.
- Record58/60 signatures are stable enough to watch.
- The public work-window is a rotating/tiled/runtime surface, not flat memory.
- Full sequential F0 readback is the source of truth after any restore.
- Structured CDD affine edits still need explicit approval.

## Next Sensible Moves

1. Keep using read-only XD13 watchpoints to map normal-mode command handling.
   Focus on response-producing commands and packet-shadow paths, not broad CDD
   mutations.
2. If we want to test whether the update path alone causes the shifted layout,
   prepare a byte-identical stock replay control, but ask before running it.
   It is lower risk than a mutation but still exercises the live update/write
   machinery.
3. If a physical media disc is still present, remove it before the next clean
   baseline series. Media readiness/spin-up adds avoidable state.
4. Treat any future CDD edit as a three-state experiment: stock/control replay,
   mutation, restore, with cold boots and full zero-based F0 verification after
   restore.

## Byte-Identical Stock Replay Control

After the first side-channel writeup, we ran the safer control: replay the
byte-identical stock image through the helper-bypass path, with no F0 mutation.
The candidate was the record60 restore candidate, whose target image SHA-256 is
the stock LD5M image and whose `diff_summary.modified_byte_count` is zero.

Flow:

1. Pico cold boot.
2. Focused pre-replay normal-mode capture.
3. Byte-identical full-currentboot/helper-bypass replay.
4. Pico cold boot.
5. Focused post-replay normal-mode capture.
6. Full zero-based F0 verification.

The replay completed cleanly:

```text
success=1
final_revision_after_sequence=LD5M
```

The post-replay full F0 dump still matched stock LD5M exactly:

```text
488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39
```

The normal-mode work-window comparison did not show a new stock-replay-induced
layout transition. Pre and post both stayed in the shifted stock phase:

```text
4cfa6d151318 @ +0x7300  (18/18 pre, 18/18 post)
28583441dfa8 @ +0x7380  (18/18 pre, 18/18 post)
9b673c066ae4 @ +0x7480  (18/18 pre, 18/18 post)
```

The record58 watchpoint continued to wander among its known phase positions,
but with similar pre/post distribution:

```text
pre:  20ea2ab16891 @ +0x70d0 x14, +0x7090 x2, +0x7010 x2
post: 20ea2ab16891 @ +0x70d0 x15, +0x7090 x3
```

So the stock replay control rules out the simplest version of "any same-image
update replay causes the record60 phase shift." The phase shift was already
present before this control and survived it unchanged. Current best read:

- the first pre-record60 baseline caught a different public-window/runtime
  phase;
- the record60 edit/update sequence pushed or coincided with a transition into
  the current shifted phase;
- byte-identical replay does not, by itself, reset or further perturb that
  phase.

Report:

```text
analysis/8051/drive3-stock-replay-control-watch-20260504.md
```
