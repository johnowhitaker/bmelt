# Drive 3 Mechanics Snippet Inventory

Date: 2026-05-05

Scope: offline scan over recent normal-mode work-window captures from DVD
`READ(10)`, DVD `SEEK(10)`, latched-no-disc focus/seek, and simulated
START STOP/front-panel runs. No new live commands were sent for this inventory.

## Purpose

The DPTR count reports are useful, but noisy. This note keeps the smaller set
of repeated snippets that actually touch the mechanics/servo-looking register
families:

```text
0x480e / 0x48a5 / 0x4762     mechanics state gates
0x4860..0x486a               controller-facing mechanics state/config
0x5904/5905/5907/590b/...    servo/mechanics cluster
0x59f0/59f1                  servo setup pair
0x5a00/5a01/5a24/5a31        companion servo/mechanics cluster
0x4820                       action/state latch used by one set-bit routine
```

The key lesson remains: visible motion comes from coordinated normal-runtime
sequences, not from one obvious "sled bit".

## Repeated Snippet Families

### Mechanics reset/config block

Observed in DVD read/seek and latched media captures.

```asm
lcall 0xbff8
mov  dptr,#0x4860
clr  a
movx @dptr,a
inc  dptr
movx @dptr,a
inc  dptr
movx @dptr,a
inc  dptr
movx @dptr,a
inc  dptr
movx @dptr,a
inc  dptr
movx @dptr,a
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

Representative chunk hash: `97fa3fec06c5`.

Interpretation: this is likely a normal mechanics/controller state initializer
or reset. It is not sufficient by itself; earlier currentboot replay of this
kind of state setup did not produce confirmed motion.

### Record70 controller/status helper

Known-output record 70 and several normal-window snippets repeatedly show:

```asm
mov  dptr,#0x8844
movx @dptr,r7
mov  dptr,#0x825b
movx a,@dptr
jnb  acc.6,done

if r7 == 1:
    r7 = 0x0b
    lcall 0xf33a
    r5 = (r7 & 0x3e) | 0x41
    r7 = 0x0b
    lcall 0xf2a0

if r7 == 0:
    r7 = 0x0b
    lcall 0xf33a
    r5 = r7 & 0xfe
    r7 = 0x0b
    lcall 0xf2a0
```

Representative chunk hash: `d21d30cf6e6b`.

Nearby code reads/writes controller FIFO registers and mirrors controller
state:

```text
0x4091/0x4098 bridge reads
0x8633 -> 0x5906
0x862f -> 0x590d
0x8631 -> 0x4840
0x8630 -> 0x4863
```

Interpretation: this is probably a controller/status helper, not a direct
actuator command. It is still one of the best static targets because it bridges
the generic controller FIFO into the mechanics register family.

### Record73/74 transition cleanup

Known-output records 73/74 and START STOP/focus captures expose a complete
gated transition/cleanup path:

```asm
mov  dptr,#0x480e
movx a,@dptr
anl  a,#0x03
jz   cleanup_only

mov  dptr,#0x48a5
movx a,@dptr
anl  a,#0xef
movx @dptr,a

mov  dptr,#0x4762
movx a,@dptr
anl  a,#0xef
movx @dptr,a

if (xdata[0x480e] & 3) == 3:
    xdata[0x4860] |= 0x04
    xdata[0x5905] &= 0xfe
    xdata[0x5a01] &= 0xfa
    delay_or_poll(0x0064)
    xdata[0x4864] &= 0xfe
    xdata[0x5905] &= 0xfb
    xdata[0x4860] &= 0xfb
    delay_or_poll(0x0064)
    transition_helper(1)

followup_helper()
xdata[0x480e] &= 0xfc
```

Representative chunks: `536f157a8567`, `4a6f7bda07c9`.

Interpretation: this explains a lot of the START STOP/front-panel tray-state
behavior, but it mostly clears/cleans up state. It is a bounded stock path, but
not the first place to force new motion.

### Servo setup block

Seen in record 54 and latched-no-disc focus captures:

```asm
mov  dptr,#0x59f0
mov  a,#0xde
movx @dptr,a
inc  dptr
mov  a,#0xc0
movx @dptr,a
mov  dptr,#0x5a00
orl  xdata[0x5a00],#0x07
orl  xdata[0x5a31],#0x02
orl  xdata[0x5954],#0xc0
anl  xdata[0x5962],#0x9f
orl  xdata[0x4861],#0x80
orl  xdata[0x4863],#0x02
orl  xdata[0x4867],#0x02
orl  xdata[0x57be],#0x60
```

Representative chunk: `121190698133` in the latched-no-disc focus corpus.

Interpretation: this is the clearest setup recipe for a servo/focus path. It
contains profile-specific constants, so treat it as a natural-sequence clue,
not a safe generic poke.

### Set-bit action-looking routine

Seen in DVD read/seek and focus runs:

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

Representative chunk hash: `20c555853ab2`.

This is the most tempting direct-control candidate because it sets bits rather
than clearing them. But the bytes immediately after it show that this lives in
a larger scheduler routine with gates:

```asm
push psw
mov  dptr,#0x8aed
movx a,@dptr
jnb  acc.2,skip
mov  dptr,#0x8a33
movx a,@dptr
xrl  a,#0x01
jnz  skip
jb   <iram flag>,skip
...
```

Interpretation: this is probably an action latch or start condition used by
the normal scheduler. It should be instrumented or reached through the stock
path before we try to replay it from currentboot. Replaying only the four
stores may miss the controller state that makes them meaningful.

## Currentboot Materializer Follow-Up

I tried two safe, non-mutating selector-22 harvests after removing media:

```text
references/evidence/live/drive3-currentboot-cdd-111a-harvest-sel22-mechanics-sources-nomedia-20260505/
references/evidence/live/drive3-currentboot-cdd-111a-harvest-sel22-oldhit-sources-nomedia-20260505/
```

Both returned cleanly and Drive #3 stayed `LD5M`.

Results:

- the five mechanics source starts (`record54`, `record70`, `record73`,
  `record74`, `record86`) produced no exact known-runtime chunk hits;
- the old hit-producing source addresses (`0x007000`, `0x009000`, `0x00e000`)
  also produced no exact known-runtime chunk hits in this phase;
- the mechanics-source gateway page was source-insensitive at
  `gateway[0x070000]`.

So selector 22 remains real, but the old exact-hit phase is not a reliable
source-addressed decoder. Treat it as state-sensitive controller surface, not a
dependable way to ask for "record 74 decoded bytes".

## Practical Next Target

The best next low-level target is not an isolated raw register. It is the
normal scheduler path that reaches the set-bit routine:

```text
scheduler gates around 0x8aed / 0x8a33 / IRAM flags
  -> 0x5a01 |= 0x05
  -> 0x5905 |= 0x01
  -> 0x5905 |= 0x04
  -> 0x4820 = 0x04
```

If we can identify the host command or controller status that satisfies those
gates, we get a natural low-level action trigger. If we cannot, this routine is
still the best candidate for a tiny normal-mode hook once the CDD/editing
problem is solved.

For live work, prefer stock-command stimuli and observation:

```text
DVD/latched-media SEEK(10)     coarse sled/positioning path
latched-no-disc READ(10)       focus/search retry path
GP27/GP28 START STOP path      tray/mechanics-state path
```

Keep raw currentboot pokes as a later tool for complete observed sequences, not
for single-bit guesses.
