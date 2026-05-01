# Normal Controller Island Patchability Notes

This is a short follow-up to
`analysis/8051/normal-controller-island-stitch-20260501.md`.

The stitch report made the GET CONFIG response path much clearer, but the
patchability result is mixed.

## Exact-Pattern Localization

I searched the main static artifacts for three exact chunks:

```text
4037c8574920  GET CONFIG-specific read setup
8d8c3b0a22a0  GET CONFIG-specific 0x4099 -> shadow burst / 0xfe branch
20ea2ab16891  public 0x8a4c..0x8a4e -> 0x4011..0x4013 response bridge
```

Results:

```text
pattern             F0/8051/static refs  currentboot gateway  normal id01/id02 baseline
------------------  -------------------  -------------------  ------------------------
4037 setup          no                   no                   no
8d8c seed           no                   no                   no
20ea bridge         no                   no                   yes, +0x7140 in id01/id02
```

The two GET CONFIG-specific chunks only appear in work-window captures taken
after GET CONFIG-like stimuli. They are not present in the baseline normal
`READ BUFFER id01/id02 offset=0x070000` reference dumps.

The public bridge chunk is present in both baseline normal references:

```text
normal id01 +0x7140:
8a29 e0 c4 54 0f 30 e0 11 90 8a 4c e0 c3 94 0e ...

normal id02 +0x7140:
same chunk
```

The currentboot gateway at the same public offset is unrelated code:

```text
currentboot gateway +0x7140:
e0 44 01 f0 90 59 97 e0 44 50 f0 22 ee 70 08 ...
```

## Practical Read

The GET CONFIG-specific setup is probably a transient overlay/page loaded or
rotated into the public work-window only when that command family runs. It is a
good reverse-engineering target, but not an obvious static flash patch target.

The stable public bridge is a better normal-runtime landmark:

```text
read xdata[0x8a29], derive a small mode/length nibble
clamp xdata[0x8a4c] to max 0x0e before writing controller[0x4011]
copy xdata[0x8a4d] to controller[0x4012]
copy xdata[0x8a4e] to controller[0x4013]
copy xdata[0x8a50..0x8a51] into IRAM 0xa9/0xaa
```

That bridge is probably not GET CONFIG-only. It is public response plumbing
that many command paths share.

## Patch Implications

There are three plausible paths, in descending order of cleanliness:

1. Find a safe normal-mode RAM/controller-memory write primitive and patch the
   stable `20ea2ab16891` bridge at `+0x7140`. That could redirect a boring
   response path without depending on the transient GET CONFIG setup.
2. Trigger GET CONFIG, then patch the transient seed after it has rotated into
   the work-window. This needs a live write primitive into that controller
   window while normal mode is running, which we do not have yet.
3. Use the currentboot/helper path to write controller gateway memory and test
   whether any part survives the transition back to normal. The exact
   currentboot `+0x7140` contents differ from normal, so this is a state-
   carryover experiment, not a direct static patch.

The first route is the most attractive if we can make normal-mode patching
work. The second route is more precise but currently lacks the required write
primitive. The third is experimentally cheap now that servo power-cycling
exists, but less likely because the currentboot and normal gateway pages are
different at this offset.

## Next Experiment Ideas

For offline work:

- stitch and disassemble the stable public bridge neighborhood around
  normal `id01/id02 +0x7100..0x7200`;
- compare that neighborhood against all work-window captures to identify the
  minimal stable response-builder patch site;
- look for a command path whose public response already uses the stable bridge
  and returns enough data to make a small redirect useful.

For live work:

- avoid more sled/eject paths for now;
- if testing state carryover, write a harmless one-byte marker into a
  currentboot gateway page that has a known normal counterpart, recover to
  normal without a cold power cut, and read the normal window immediately;
- if the marker carries over, try the stable `+0x7140` bridge page; if it does
  not, focus on a true normal-mode write primitive instead.
