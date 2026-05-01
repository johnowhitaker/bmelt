# CDD Contig 8 / Record 57 Readback Resolution

This note resolves the apparent restore failure from the record-57 contig
ownership experiment.

## Original Observation

The live perturbation target was CDD1 record 57:

```text
F0 offset 0x27410: 0x3a -> 0x32
```

The public normal-mode work-window effect was sharp:

- stock captures: full 3-tile contig present in `24/24` windows;
- mutated captures: full sequence absent in `24/24` windows;
- component tiles 0 and 2 stayed visible, while the middle tile disappeared.

Several restore attempts left the middle tile absent, which originally looked
like a possible flash restore failure.

## What Was Checked

The standalone F0 spot reader was first tested at `0x27400` with and without
`sg_raw --cmdset=1`. Both raw reads were identical, and neither decrypted to the
known LD5M CDD1 bytes. The conclusion is that spot reads inside CDD1 are not a
valid restore oracle.

A sequential normal-mode F0 dump from offset `0` is valid. After a same-image
base replay:

```text
runs/contig8-rec57-ownership/direct-f0-read-after-base/
```

the CDD byte was already restored:

```text
F0[0x27410] = 0x3a
```

That dump still showed a lingering low-prefix currentboot response hook:

```text
0x4fc9..0x4fcb = 02 6e e3   (hook)
0x6ee3..       = hook payload
```

Running the existing `restore-4fc9-cave` candidate restored those prefix bytes.
A direct sequential dump of the first `0x8000` bytes then matched stock exactly,
including `0x4fc9`, `0x6ee3`, `0x6206`, `0x542b`, and `0x1ea0`.

Finally, a full 1 MiB sequential F0 dump matched the LD5M baseline byte-for-byte:

```text
baseline sha256: 488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39
readback sha256: 488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39
cmp: 0
```

The full readback is saved at:

```text
runs/contig8-rec57-ownership/prefix-restored-full-f0-read/
```

## Result

Record 57's source byte was restored. The complete F0 image is stock.

The middle public tile still did not return after a hardware cold boot and
normal work-window capture. That means the lingering missing tile is not caused
by an un-restored byte in F0. It is more likely one of:

- public work-window instability;
- a controller/runtime/cache state not reset by ordinary cold boot;
- a state dependency in the stimulus/capture path;
- a non-F0 persistent state, if such a state exists.

## Practical Lesson

Record 57 remains a useful warning, but it should not be treated as a clean
reversible CDD ownership proof.

The stronger live oracle remains record 59 / contig 4, where the sequence
disappeared under mutation and returned after restore. Future CDD ownership
tests should keep using the full before/mutate/restore pattern, and should add
a sequential F0 readback when a restore result looks odd.

