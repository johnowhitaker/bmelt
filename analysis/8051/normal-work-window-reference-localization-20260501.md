# Normal Work-Window Reference Localization

Date: 2026-05-01

This is an offline follow-up to the START STOP/eject hook plan. It asks a
simple source question: do the normal work-window chunks match any artifact we
already know how to patch or dump?

Input corpus:

```text
references/evidence/live/normal-work-window-capture-only-20260501
references/evidence/live/normal-work-window-stimuli-full-20260501
references/evidence/live/normal-work-window-stimuli-focused-20260501
references/evidence/live/normal-work-window-readstatus-correlation-20260501
references/evidence/live/normal-work-window-error-path-pairs-20260501
references/evidence/live/normal-start-stop-eject-delayed-20260501
```

Reference comparison output:

```text
analysis/8051/normal-work-window-extended-reference-matches-20260501.md
analysis/8051/normal-work-window-extended-reference-matches-20260501.json
```

## High-Level Result

With `0x40`-byte informative chunks:

```text
unique normal work-window chunks: 908

reference                      exact chunk matches
-----------------------------  -------------------
LD5M F0 image                  63
visible 8051 prefix             8
profile-tail helper             0
currentboot gateway 0x070000   510
normal READ BUFFER id01        693
normal READ BUFFER id02        693
```

This changes the model in a useful way:

- the work-window is definitely not just visible F0 prefix code;
- it is also not the profile-tail helper overlay;
- a large fraction overlaps the currentboot `controller[0x070000..0x07ffff]`
  gateway dump;
- normal `READ BUFFER id01` and `id02` at offset `0x070000` are effectively
  equivalent references for this window.

The currentboot gateway overlap is the interesting part. It says the normal
work-window and currentboot gateway dump share a large controller/work-memory
image. That does not make it patchable, but it does mean the normal overlay is
not completely unreachable or mode-private.

## START STOP Branch Localization

The `+0x8bxx` region remains awkward. Its common chunks mostly match the normal
`id01/id02` reference window at neighboring `+0x8bxx` positions, but not F0,
not the helper, and not the currentboot gateway dump:

```text
public slot  common refs
-----------  ------------------------------------------------------------
+0x8b00      normal-id01/id02 @ +0x8b00, +0x8b40, +0x8b80; some NOREF
+0x8b40      normal-id01/id02 @ +0x8b40, +0x8bc0; some NOREF
+0x8b80      normal-id01/id02 @ +0x8b00, +0x8b40, +0x8bc0; some NOREF
+0x8bc0      normal-id01/id02 @ +0x8b00, +0x8b40, +0x8bc0; some NOREF
```

Two recurring `+0x8bxx` chunks are especially important because they do not
match any reference in this pass:

```text
sha eef7607e3343... sample e04410f078b5760678ab76288054204d...
sha 707389d4505f... sample 8a34e04404f0908a29e020e042105202...
```

The second chunk is the local flag/setup chunk that includes `0x8a34` and sits
near the START STOP branch. Its NOREF status reinforces the caution from the
hook plan: do not assume this can be patched by writing visible F0 bytes.

## Mechanics Cluster Localization

The broader mechanics-adjacent pages are a little more encouraging. Some of
the `+0x92xx/+0x93xx/+0x95xx` chunks match the currentboot gateway dump:

```text
normal chunk sample                       currentboot-gateway match
----------------------------------------  -------------------------
0604700602f85612f2b922904782e030...      +0x9280
5a017418f02290549fe0332290848ee0...      +0x9340
908d44e0feef4ed082d083f0904806c0...      +0x9500
3ae0c41313540320e003025f2f203e03...      +0x9540
```

These are not enough to patch the branch, but they are useful landmarks. The
same controller/work-memory image seen in currentboot contains chunks around
the normal mechanics and packet-copy clusters. That gives a static correlation
surface for future analysis:

```text
normal work-window pages  +0x92xx/+0x93xx/+0x95xx
currentboot gateway pages +0x9280/+0x9340/+0x9500/+0x9540
```

## Interpretation

The normal-runtime code/data we are seeing is a mixed controller work-memory
view. Some pages are stable enough to match a normal `READ BUFFER` snapshot,
some are shared with the currentboot gateway dump, and a minority are
stimulus-specific or not present in any known reference.

That leads to two practical conclusions:

1. A visible-F0 persistent hook is still the wrong default for normal command
   paths. The exact branch we want is not localized to F0 or the helper.
2. The currentboot gateway dump is now more valuable than before. It shares
   enough with normal runtime that cross-mode localization may identify stable
   routines, mailboxes, or RAM patch points.

## Next Static Work

The next static pass should compare the normal `id01/id02` canonical window and
the currentboot gateway dump directly, not only chunk-by-chunk against the live
corpus. Useful questions:

- Which normal pages have exact currentboot gateway counterparts?
- Are the currentboot-matching pages code-like, table-like, or mailbox state?
- Do the matched `+0x92xx/+0x93xx/+0x95xx` chunks form one coherent routine
  when disassembled from the currentboot gateway offsets?
- Can any shared chunk be modified through a currentboot/helper RAM write and
  survive long enough to affect normal mode?

For live work, this does not change the immediate rule: avoid more mechanical
START STOP runs until there is a host-visible readback hook or a plausible RAM
patch point.
