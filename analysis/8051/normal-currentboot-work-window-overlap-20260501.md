# Normal vs Currentboot Work-Window Overlap

Date: 2026-05-01

This note compares three 64 KiB controller/work-window dumps directly:

```text
normal id01:
  references/evidence/live/normal-read-buffer-work-window-20260501/id01-070000-010000.bin

normal id02:
  references/evidence/live/normal-read-buffer-work-window-20260501/id02-070000-010000.bin

currentboot gateway:
  references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin
```

The comparison uses exact informative `0x40`-byte chunks.

## Summary

```text
normal id01 informative chunks:       700 total / 699 unique
normal id02 informative chunks:       700 total / 699 unique
currentboot gateway informative:      701 total / 700 unique

id01 vs id02 exact chunk pairs:       701
id01 vs currentboot exact pairs:      476

id01 vs id02 same-offset pairs:       693
id01 vs currentboot same-offset pairs:452
```

So normal `id01` and `id02` are not byte-identical files, but they are mostly
the same memory image. Currentboot gateway `0x070000` is also substantially the
same image, but less so.

A separate scratch comparison against the full currentboot XDATA dump found
only 2 exact chunks in common with the normal work-window corpus. That matters:
the shared surface here is the controller/gateway window, not ordinary XDATA
already covered by the currentboot guarded XDATA write hook.

## Same-Offset Runs

The strongest normal-id01/currentboot exact runs are:

```text
normal +0xa000..+0xde80 == currentboot +0xa000..+0xde80   251 chunks
normal +0xe000..+0xfd80 == currentboot +0xe000..+0xfd80   119 chunks
normal +0x4000..+0x4500 == currentboot +0x4000..+0x4500    21 chunks
normal +0x0000..+0x0140 == currentboot +0x0000..+0x0140     6 chunks
normal +0x5100..+0x51c0 == currentboot +0x5100..+0x51c0     4 chunks
```

This makes the high half of the public `0x070000` window look more like stable
controller/work memory than a normal-only transient overlay.

The strongest normal-id01/id02 exact runs are broader:

```text
normal id01 +0x9600..+0xde80 == id02 +0x9600..+0xde80   291 chunks
normal id01 +0x60c0..+0x94c0 == id02 +0x60c0..+0x94c0   209 chunks
normal id01 +0xe000..+0xfd80 == id02 +0xe000..+0xfd80   119 chunks
normal id01 +0x4000..+0x4500 == id02 +0x4000..+0x4500    21 chunks
normal id01 +0x0000..+0x0280 == id02 +0x0000..+0x0280    11 chunks
```

Normal `id01` and `id02` are therefore close enough to treat as aliases for
many localization tasks, but not as identical byte-for-byte dumps.

## What This Means For START STOP

The START STOP/eject branch lives around normal `+0x8bxx`. That region is
stable between normal `id01` and `id02`, but it is not part of the large
same-offset currentboot overlap. In the extended reference pass, the most
interesting `+0x8bxx` chunks either matched only normal `id01/id02` or did not
match any current reference.

That keeps the patching conclusion unchanged:

- the branch is live and normal-mode relevant;
- it is not visible F0 prefix;
- it is not the helper overlay;
- it is not present as an obvious exact chunk in the currentboot gateway dump;
- it should not be patched by guessing a flash offset.

## What This Means For Mechanics/Servo Work

The `+0x92xx/+0x93xx/+0x95xx` cluster has a mixed result. It is not part of a
large currentboot-identical run, but several individual chunks match the
currentboot gateway with small shifts:

```text
normal +0x9200 -> currentboot +0x9280
normal +0x9300/+0x9340/+0x9380/+0x93c0 -> currentboot +0x9340
normal +0x9500/+0x9540/+0x9580/+0x95c0 -> currentboot +0x9500/+0x9540
```

That is not a patch map, but it is a useful clue: the mechanics/packet-copy
cluster appears to share code/data fragments with currentboot controller memory
even when the exact START STOP branch does not.

## Working Interpretation

The `0x070000` public window is a shared controller/work-memory region with
several classes of content:

1. stable tables/profile data shared across normal and currentboot;
2. stable normal command/packet machinery shared between `id01` and `id02`;
3. mode-specific or stimulus-specific code/data that does not appear in our
   currentboot dump;
4. moving pages whose public slot can shift by small multiples of `0x40`.

The normal START STOP branch is in class 2 or 3. The high tables are class 1.
The mechanics/packet-copy cluster straddles class 2 and small shifted class 4.

## Next Use

For a normal-mode response hook, prefer chunks that are stable in normal id01
and id02 and near a boring command response, not the eject branch itself.

For currentboot-to-normal patch carryover experiments, the best candidates are
the currentboot/normal shared pages, especially the long exact runs at
`+0xa000..+0xde80` and `+0xe000..+0xfd80`. The START STOP branch itself is not
yet in that category.
