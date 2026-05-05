# Drive 3 DVD SEEK/READ Motion-Control Findings

Date: 2026-05-05

Scope: stock normal-mode commands on Drive #3 with a movie DVD inserted. No
firmware writes, no CDD mutations, and no raw actuator/register writes were
sent in this pass.

## Why This Pass Happened

The user saw a dramatic stock `SEEK(10)` sweep: spindle spun up, laser was on,
and the sled moved quickly between positions. That confirms we already have a
high-level, safe motion surface through standard MMC commands. The question for
this pass was whether the normal public work-window would also expose a cleaner
low-level branch we could map toward manual sled/focus/spindle control.

The new evidence is:

```text
references/evidence/live/drive3-dvd-read10-lba-control-corpus-20260505T231732Z/
references/evidence/live/drive3-dvd-seek10-lba-control-corpus-20260505T232203Z/
analysis/8051/drive3-dvd-read10-lba-control-dptr-20260505.md
analysis/8051/drive3-dvd-seek10-lba-control-dptr-20260505.md
```

## What The Stock Commands Showed

The `READ(10)` corpus used:

```text
TUR
READ CAPACITY(10)
READ(10) LBA 0x10
READ(10) LBA 0x40000
READ(10) LBA 0x80000
READ(10) LBA 0x120000
READ(10) LBA 0x166000
READ(10) LBA 0x10
```

The `SEEK(10)` corpus used the same LBA ladder. The first `SEEK(10) LBA 0x10`
took about `0.63 s`; later seeks returned in only a few milliseconds. So this
run proves the command path is accepted, but not that every requested LBA caused
a fresh physical sled move. Treat it as a control-path corpus, not a precise
positioning calibration.

Both corpora caused large public work-window phase changes after the media
commands. Relative to the baseline snapshot:

```text
READ(10) post-command snapshots: ~216..246 changed 0x40-byte slots
SEEK(10) post-command snapshots: ~228..260 changed 0x40-byte slots
```

That means stock media commands put the normal runtime into a richer scheduler
state, but the public `READ BUFFER id=01` window is still a rotating tile
surface. It is not a flat trace of "the branch just executed".

## What Did Not Show Up

I looked for a simple direct `SEEK(10)` opcode branch:

```asm
mov  dptr,#0x8a49
movx a,@dptr
xrl  a,#0x2b
```

and the comparable `CJNE #0x2b` shape. It did not appear in the exposed tiles.
The same scan did find the already-known direct branches for:

```text
0x1b  START STOP UNIT
0x28  READ(10)
0x2a  WRITE(10)-ish path
```

Several seek-only chunks use add-chain dispatch rather than `xrl`, but the
decoded comparisons are not `0x2b`. For example:

```asm
mov  dptr,#0x8a49
movx a,@dptr
add  a,#0xab
jz   branch_for_opcode_0x55
add  a,#0x98
jz   branch_for_opcode_0xbd
add  a,#0x63
jz   branch_for_opcode_0x5a
```

Other visible command checks in the seek-only region include `0x2a`, `0x35`,
`0xac`, `0xa3`, and `0xa4`, but not a clean exposed `0x2b` branch. The current
interpretation is that one of these is true:

- `SEEK(10)` is translated into a more generic media/scheduler path before the
  visible tiles we are seeing;
- the `0x2b` branch exists but was not in the rotating public window during
  these captures;
- the first visible movement was mostly spin/focus/setup, with the later LBA
  seek decisions handled deeper in controller/CDD code.

## Useful Low-Level Islands We Did See

The same normal-runtime families keep surfacing across `READ(10)`, `SEEK(10)`,
latched-no-disc focus retries, and START STOP eject traces:

```text
0x8a49..0x8a54   packet/CDB shadow
0x47b1           packet FIFO / command-response port
0x4000/0x409x    controller bridge and FIFO
0x4860..0x486a   controller-facing mechanics state/config
0x5904/5905/...  servo/mechanics register cluster
0x5a00/5a01/...  companion servo/mechanics cluster
```

The most actionable mechanics-adjacent snippets remain these:

### 1. Mechanics reset/config block

Observed in media command corpora:

```asm
lcall 0xbff8
mov  dptr,#0x4860
clr  a
movx @dptr,a
inc  dptr
movx @dptr,a
...
mov  dptr,#0x4867
mov  a,#0x61
movx @dptr,a
mov  dptr,#0x486a
clr  a
movx @dptr,a
inc  dptr
movx @dptr,a
ret
```

This looks like normal mechanics/controller state setup, not a motion command
by itself. Currentboot replaying this kind of block did not produce confirmed
motion, which supports that interpretation.

### 2. Record70-style controller/status helper

Known-output record 70 starts with:

```asm
lcall 0xf2a0
ret
mov  dptr,#0x8844
movx @dptr,r7
mov  dptr,#0x825b
movx a,@dptr
jnb  acc.6,done
...
mov  r7,#0x0b
lcall 0xf33a
...
lcall 0xf2a0
```

Later nearby code reads/writes the controller FIFO and mirrors controller state
into the `0x486x/0x590x` families. This is still a high-value static target.

### 3. Servo/start-ish block

The most "start an action" looking snippet is:

```asm
mov  dptr,#0x5a01
movx a,@dptr
orl  a,#0x05
movx @dptr,a
mov  dptr,#0x5905
movx a,@dptr
orl  a,#0x01
movx @dptr,a
movx a,@dptr
orl  a,#0x04
movx @dptr,a
mov  dptr,#0x4820
mov  a,#0x04
movx @dptr,a
ret
```

This is more interesting than the cleanup-only record74 path because it sets
bits rather than clearing them. But as a raw-poke target it is still incomplete:
it appears as the tail of a function, and the entry conditions around
`0x8aed`, `0x8a33`, and several IRAM flags are visible immediately afterward.
It should be understood as part of a normal scheduler routine before replaying
it blindly.

### 4. START STOP / tray-state path

The stock eject/front-panel path is still the best mapped mechanical state
machine route:

```text
host or Pico button/eject event
  -> CDB shadow at 0x8a49..0x8a4d
  -> 0x480e / 0x48a5 / 0x4762 state gates
  -> 0x4860 / 0x4864 state pair
  -> 0x5905 / 0x5a01 cleanup and transition
```

The GP28 tray simulator makes this route safer to experiment with because we
can present "closed" and "open" states without relying on the physical tray.

## Practical Assessment

We now have two different kinds of control:

1. **Safe high-level motion control:** stock MMC commands can spin, focus/read,
   seek, and enter tray/eject state paths. This is useful immediately for demos
   and for collecting natural traces.
2. **Incomplete low-level control:** the visible low-level registers and state
   bytes are mapped better, but raw writes to `0x486x`, `0x590x`, or `0x5a0x`
   are still not enough by themselves. Normal motion is coordinated by a
   scheduler/controller path that the currentboot helper context does not fully
   reproduce.

So the next sensible low-level path is not "try another isolated register
poke." It is:

```text
use stock commands to identify complete normal sequences
  -> map the scheduler/mailbox step before the 0x486x/0x590x writes
  -> replay or instrument a complete sequence, preferably in normal context
```

## Recommended Next Steps

1. Use the existing stock commands as controlled stimuli:
   - `SEEK(10)` for coarse sled positioning;
   - `READ(10)`/latched-no-disc `READ(10)` for focus/search behavior;
   - START STOP / GP27 / GP28 for tray-state transitions.
2. Keep building the normal mechanics map around:
   - record70 controller helper;
   - record73/74 mechanics transition/cleanup;
   - the `0x5a01/0x5905/0x4820` set-bit routine.
3. Avoid CDD mutations and broad raw register writes for now.
4. If moving back to live experiments, prefer one of:
   - a standard-command trace that forces visible motion and captures the
     delayed work-window state;
   - a currentboot non-mutating materializer harvest aimed at source ranges for
     records 54/70/73/74;
   - a very small normal-mode hook only after a complete scheduler sequence is
     identified.

The headline is that physical control is no longer abstract: stock commands
move real hardware. The remaining reverse-engineering problem is to find the
normal scheduler/controller mailbox layer that turns packet-level commands into
the `0x486x/0x590x/0x5a0x` register choreography.
