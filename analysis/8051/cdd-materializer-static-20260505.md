# CDD Materializer Static Pass - 2026-05-05

Scope: static/offline. No live drive commands were sent for this pass.

## Short Version

The visible 8051 still does not contain a byte-level decoder for the hard CDD
bodies. It is a controller setup layer. It stages descriptor fields, maps small
windows, rings mailbox bits, and polls completion/status registers. The actual
materialization of CDD records into the `0x184000..0x1b3fff` controller range
still appears to happen inside the controller side.

The useful correction is that our prior currentboot CDD tests exercised mostly
the shallow/default parser path: map the 32-byte CDD header, package
`0x4a*` fields, and ring the mailbox. That path is real and reproducible, but
it does not wake decoded CDD memory in currentboot. The branch that still looks
closest to a materialization command is the `xdata[0x8196] == 2` path in
`FUN_CODE_002e`, because it drives a larger `0x4e80/84/88/8c` transaction:

```text
0x4e80 = 0x00407000
0x4e84 = 0x0007b000
0x4e88 = 0x00005000
0x4e8c = 0x01
```

That path is not proven to be the ordinary LD5M boot path, but it remains the
best non-mutating controller-oracle candidate.

## What "Materializer" Means Here

There are three layers that are easy to conflate:

1. The encoded CDD source in the F0 image.
2. The visible resident 8051 code that validates headers and programs mailbox
   registers.
3. The hidden controller/ASIC engine that actually expands or interprets hard
   CDD bodies.

The visible resident code is layer 2. It tells us how to ask the controller for
work, but it does not itself transform mode-`0x40`/`0x80` hard bodies into
decoded code bytes.

## Normal Handoff Chain

The ordinary resident sequence is fuller than a naked `FUN_CODE_002e` call:

```text
FUN_CODE_268a
  -> FUN_CODE_48e7
       calls FUN_CODE_111a(selector 0x80)
       parses/stages descriptor state
  -> FUN_CODE_40b2
       reads/verifies trailer magic "LITE" through the controller gateway
       validates descriptor words
       copies descriptor fields into 0x8248..0x8255
       calls FUN_CODE_002e
```

`FUN_CODE_40b2` seeds a 4-byte source read at `0x000e7ffc`, where the F0 image
contains ASCII `LITE`. It then polls `xdata[0x4000].7` and reads bytes from the
`xdata[0x4098]` FIFO, expecting:

```text
4c 49 54 45  ; "LITE"
```

Only after that does it validate:

```text
xdata[0x8229..0x822c] == 0x00007000
xdata[0x822d..0x8230] == 0x00004000
```

Then it copies the descriptor fields used by `FUN_CODE_002e`.

This is important: currentboot tests that directly called `0x1717`, directly
wrote `0x4a*`, or called `FUN_CODE_002e` did not reproduce this full
trailer/gateway prelude.

## `FUN_CODE_002e` Mode Split

`FUN_CODE_002e` gates on `xdata[0x8196]`:

| gate | effect |
|---|---|
| `0x8196 == 0x01` | early/special return before CDD header mapping |
| `0x8196 == 0x02` | descriptor-transfer path through `0x4e80/84/88/8c`, then `0x4e14/15/16` |
| otherwise | default mapped-header path: map `CDD\x09 10 16`, package `0x4a*`, ring mailbox |

The known visible LD5M setup call is `FUN_CODE_111a(0x80)` at `0x4940`. That
call stages:

```text
0x8245..0x8248 = 0x00007000
0x8249..0x824c = 0x00004000
0x824d..0x8250 = 0x00000000
```

The last word makes the staged parser mode byte `0x8196 = 0`, not `2`. So
`0x8196 == 2` should be described as a real alternate/controller path, not as
the proven normal LD5M boot path.

## Default Path

The default path is the one our currentboot tests have mostly exercised. It:

1. Sets `xdata[0x8256..0x8257] = 0xc000`.
2. Uses `FUN_CODE_1717` to map the 32-byte CDD header at F0 `0x0702c` into
   the `0xc000` XDATA window.
3. Verifies the mapped header begins `43 44 44 09 10 16`.
4. Dispatches on aux length derived from header byte `0x10`.
5. For DS-8ABSH, takes the `0x0400` aux/table case and writes
   `xdata[0x4a01] = 3`.
6. Packages header fields into the controller mailbox:

```text
0x4a03 = header[0x06] & 3
0x4a05 = header[0x06] >> 2
0x4a06 = header[0x10] & 0x0f
0x4a20..0x4a22 = header[0x0d..0x0f]
0x8258..0x825b = 00 || header[0x07..0x09]  ; CDD2 pointer
```

Live currentboot triggers proved this path works:

- The mapped-header trigger returned the exact LD5M CDD header in the response.
- The parser-call trigger returned populated `0x4a00..0x4a3f` fields.
- The second-doorbell trigger executed and recovered.

But in all those runs, sampled decoded/controller addresses stayed zero. This
rules out the shallow default path as a currentboot decoded-memory oracle. It
does not rule out a fuller normal handoff or the alternate `0x8196 == 2` path.

## `0x4e` Command Engine

The command wrappers around `0x4e80/84/88/8c` are banked controller-window
transactions. The source word is not a flat address: the wrapper shifts a
selector left by 21 bits and adds it into the first pointer. In practice:

```text
0x0040702c = selector 2 + source 0x0702c
0x00407000 = selector 2 + source 0x07000
```

The default header map uses:

```text
0x4e80 = 0x0040702c
0x4e84 = 0x0007ffff
0x4e88 = 0x00000020
```

The saved status row after that call advanced exactly as expected:

```text
source after = 0x0040704c
extent after = 0x0008001f
status = 0x06
```

So `0x4e84` behaves like a second extent/window operand. It should not be
called a proven second CDD source, but it is address-like enough that its
numeric band matters.

## Untested Materializer Candidate

The `0x8196 == 2` path computes a larger transfer:

```text
0x4e18..0x4e19 = 0x01ec
0x4e1e         = 0x01
0x4a00         = 0x00
0x4e80         = 0x00407000
0x4e84         = 0x0007b000
0x4e88         = 0x00005000
0x4e8c         = 0x01
wait until 0x4ea0 == 0x06
0x4e14..0x4e15 = 0x01ff
0x4e16         = 0x01
```

The front operand covers the start of the CDD object:

```text
0x07000..0x0bfff
```

The second numeric extent is:

```text
0x7b000..0x7ffff
```

In the static F0 layout, that `0x7b000..0x7ffff` band overlaps CDD records
224..233, whose decoded candidate destinations are:

```text
0x19c120..0x19d2e0
```

The front CDD1 table points into several of those records. Existing saved
currentboot decoded-target reads did not sample that companion band, so the
best currentboot negative corpus does not actually test the band most tied to
this alternate transfer.

## What To Test Next, If Live Work Is Approved

The safest useful live plan is still non-mutating:

1. Stay in a recoverable currentboot hook environment.
2. Capture baseline:
   - `xdata[0x4e00..0x4ebf]`
   - `xdata[0x4a00..0x4a30]`
   - gateway reads around `0x070000`, `0x0702c`, and `0x7b000`
   - decoded companion samples listed below.
3. Trigger a guarded `0x8196 == 2` equivalent, or call `FUN_CODE_002e` with
   descriptor state plus `xdata[0x8196] = 2`.
4. Capture the same windows immediately and after a short delay.
5. Cold boot back to stock.

Companion-band decoded sample addresses:

```text
0x19c120
0x19c1b0
0x19c2a0
0x19c660
0x19c760
0x19cb10
0x19cd50
0x19cf30
0x19d128
0x19d210
```

Success would be any stable nonzero decoded-looking output in that band, or a
status transition in `0x4e/0x4a` that differs from the already-tested default
path.

## Risk

This is non-persistent and does not edit the CDD image, but it is not risk-free.
It rings controller command registers that may control an internal transfer
engine. The expected failure mode is a currentboot wedge requiring a power
cycle/recovery. It should not be run on a drive whose recovery path is unknown.

Things this plan should not do:

- no CDD hard-body mutation;
- no F0 writes;
- no profile-tail `arg=0x7f` experiments outside the already-known guarded
  update flow;
- no unbounded waits if `0x4ea0` never reaches `0x06`.

## Current Read

The materializer is better understood as a controller transaction protocol than
as a local decompressor. The next breakthrough is likely one of:

1. a non-mutating replay that gets the controller to expose decoded CDD bytes;
2. a normal-runtime hook that observes the CDD-decoded range after the ordinary
   boot handoff;
3. a true static encoder/decoder breakthrough for hard records.

Given what the static path now says, the highest-value non-mutating experiment
is the guarded mode-2 materializer replay with companion-band sampling. It is
more targeted than another broad CDD decode attempt and less risky than a blind
CDD source mutation.
