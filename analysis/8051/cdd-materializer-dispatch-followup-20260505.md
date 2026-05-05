# CDD Materializer Dispatch Follow-Up - 2026-05-05

Scope: static/offline, plus tooling preparation. No live drive commands were
sent for this pass.

## Short Version

The current best model is now sharper:

- `FUN_CODE_002e` is still a visible 8051 controller setup routine, not the
  hard CDD decoder.
- The live mode-2 trigger showed that one alternate branch maps/copies encoded
  CDD source bytes into a gateway-visible `0x07b000..0x07ffff` window.
- The next likely consumer is not another simple `0x002e` call. It is a later
  dispatch/status path around `FUN_CODE_111a`, `FUN_CODE_141e`, and
  `FUN_CODE_40b2`, plus controller-owned state selected by `xdata[0x4819].0`.

The main new static correction is that Ghidra hides important inline dispatch
tables. `FUN_CODE_111a` is a selector dispatcher. The known normal setup call
uses selector `0x80`; the `0x4819` alternate branch uses selector `0x02`.
Those are different cases, not the same "mode 2" mechanism.

## Inline Dispatch Tables

The helper at `0x1e4d` pops the caller return address and treats the bytes
after the call as a jump table. Entries are:

```text
target_hi target_lo selector
```

and the table ends with:

```text
00 00 default_hi default_lo
```

That means raw disassembly at the call site looks like nonsense instructions
unless it is treated as data.

### `FUN_CODE_1009`

`FUN_CODE_1009` calls the same inline dispatcher at `0x1009`. Its table maps
small selectors to controller/status helpers:

```text
00 -> 0x1057   clear 0x4e08
01 -> 0x105f   call 0x167d(0)
02 -> 0x1063   call 0x167d(1)
03 -> 0x106b   call 0x15df
04 -> 0x1071   call 0x15e5
05 -> 0x1077   call 0x15ec
06 -> 0x107d   call 0x15f2
07 -> 0x1083   call 0x15fc
08 -> 0x1089   call 0x1615
09 -> 0x108f   call 0x1634
0a -> 0x1095   set 0x4e16 = 1
0b -> 0x109a   clear 0x4e16
0c -> 0x10a1   set 0x4e17 = 1
0d -> 0x10a6   clear 0x4e17
0e -> 0x10ad   call 0x164d
0f -> 0x10b2   call 0x1654
10 -> 0x10b7   clear/set 0x4e2c path
11 -> 0x10c7   clear 0x4e2c
20 -> 0x10ce   call 0x165a
ff -> 0x10d3   status/default path
default -> 0x1115
```

This makes the `0x4e14..0x4e2c` cluster look like a small command/status
state machine, not passive scratch RAM.

### `FUN_CODE_111a`

`FUN_CODE_111a` starts by copying three 32-bit staged fields:

```text
xdata[0x8245..0x8248] -> IRAM[0x5d..0x60]
xdata[0x8249..0x824c] -> IRAM[0x61..0x64]
xdata[0x824d..0x8250] -> IRAM[0x65..0x68]
```

Then it dispatches on the caller selector:

```text
00 -> 0x1183
01 -> 0x11cb
02 -> 0x11f2
20 -> 0x1228
21 -> 0x1257
22 -> 0x1278
23 -> 0x1299
24 -> 0x12ba
80 -> 0x12e0
default -> 0x140e
```

The selector matters:

- `FUN_CODE_48e7` calls `FUN_CODE_111a(0x80)`. This is the visible normal
  descriptor/setup case.
- The alternate `xdata[0x4819].0` branch in `FUN_CODE_40b2` calls
  `FUN_CODE_111a(0x02)`. This is a later status/continuation case.

So the branch at `xdata[0x8196] == 2` inside `FUN_CODE_002e` and the
`FUN_CODE_111a(0x02)` continuation are easy to confuse, but they are different
things.

## Selector `0x80`: Descriptor Setup Case

The `FUN_CODE_111a(0x80)` case begins at `0x12e0`. It:

1. Adjusts hardware/control bits around `0x40fd` and `0x480e`.
2. Calls `FUN_CODE_1009(0x20)`.
3. Reads `xdata[0x4e0f]`.
4. Uses the staged pointer in `IRAM[0x5f..0x60]` as a code-pointer table.
5. Copies several descriptor/state fields into:

```text
0x8227..0x8228
0x8229..0x822c
0x822d..0x8230
0x8231..0x8234
0x8235..0x8238
0x8239..0x823a
```

6. Writes `xdata[0x8196]` from `IRAM[0x68]`.
7. If `0x4e0f == 0`, writes `0x4e0c` and `0x4e0d` from derived staged
   values.
8. Sets the `0x4e1b/0x4e1d/0x4e1e` status flags according to
   `xdata[0x8196]`.

The flag write is exact:

```text
0x8196 == 1: 0x4e1b=0, 0x4e1d=0, 0x4e1e=1
0x8196 == 2: 0x4e1b=1, 0x4e1d=0, 0x4e1e=1
otherwise:   0x4e1b=1, 0x4e1d=1, 0x4e1e=0
```

`FUN_CODE_141e(0)` then reads `0x4e1b == 1`, so `0x4e1b` is a real predicate
used by the later branch in `FUN_CODE_40b2`.

## `xdata[0x4819].0`

Direct visible references to `0x4819` are only:

```text
0x40b2  FUN_CODE_40b2 tests bit 0
0x5118  FUN_CODE_50ca tests bit 0 during boot/init
```

No direct visible 8051 writer was found. That makes `0x4819.0` look like a
hardware/controller personality bit.

Its effects are broad enough that it should not be flipped casually:

- in `FUN_CODE_50ca`, it chooses a different stack pointer/init personality;
- in `FUN_CODE_40b2`, it skips the `LITE` trailer check and the ordinary
  `FUN_CODE_002e` descriptor path, then uses the `FUN_CODE_111a(0x02)`
  continuation if `0x4e1b` says the setup is ready.

In practical terms: `0x4819.0` may distinguish a controller/currentboot-ish
runtime from full normal LD5M, or a later boot phase from the initial
descriptor pass. It is useful as a clue, not as an immediate live knob.

## What The Mode-2 Live Result Means Now

The previous live run of the guarded `xdata[0x8196] = 2` parser path returned:

```text
0x4e90..0x4e93 = 00 40 c0 00
0x4e94..0x4e97 = 00 08 00 00
0x4ea0         = 06
```

Those look like post-transfer echoes:

```text
front/source advanced: 0x00407000 -> 0x0040c000
window advanced:       0x0007b000 -> 0x00080000
status:                0x06
```

The mapped gateway window proved the same thing from the other side:

```text
gateway 0x07b000..0x07ffff == F0 0x007000..0x00bfff
```

So the best current reading is:

```text
mode-2 parser path = expose/copy encoded CDD source window
unknown later path = consume/materialize that source into runtime overlays
```

## Tooling Added

The response-hook builder now has a selectable XDATA-window variant for the
same mode-2 call:

```sh
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name mode2-xdata-4e00 \
  --gateway-cdb-bulk-with-cdd-parser-mode2-xdata-window \
  --mode2-xdata-address 0x4e00 \
  --mode2-xdata-len 0x40 \
  --cave-len 0xdd
```

The new selected-window trigger is:

```text
CDB[7:8] = fc e5
```

and normal/fallback commands still read the controller gateway. The special
trigger returns:

```text
response[0x20] = marker, default 0xd9
response[0x21..] = selected XDATA window after the mode-2 call
```

Dry-run builds for `0x4e00` and `0x8240` both fit exactly in the current
`0xdd` cave. This has not been run on a drive yet.

Useful first windows if we run it later:

```text
0x4e00..0x4e3f   command/status flags before the 0x4e80 status row
0x4a00..0x4a3f   mailbox fields
0x8240..0x827f   descriptor staging/state
0x8190..0x81af   packet/CDB shadow plus 0x8196
```

## Main-Loop Controller Service

The next visible service point after the boot/materializer setup is the
`0x48a0` branch in the main path around `0x27e9`:

```text
if 0x48a0.7 is clear:
    skip controller-service work
if 0x48a0.4 is set:
    clear bit 4
    read 12 FIFO bytes from controller address 00:0000 into xdata[0x818a..0x8195]
    read 32 FIFO bytes into xdata[0x810e..0x812d]
if 0x48a0.6 is set:
    call 0x4b4f, then write 0x47c9 = 0x51
if 0x48a0.5 is set:
    call 0x4b4f, then write 0x47c9 = 0x50
finally:
    clear 0x48a0.7
```

This is important because `0x4da4` and the finalizer path also set
`0x48a0.7`. Visible 8051 code appears to service controller-selected work bits
rather than deciding the CDD/finalization result by itself.

The receiver at `0x4b4f` is a structured controller exchange, not a byte
decompressor. It:

1. Issues a controller command through `0x4095..0x4098`.
2. Requires magic bytes `5a a5 46 4c`.
3. Updates `xdata[0x47d2]` and the high bits of `xdata[0x8221]`.
4. Uses state at `xdata[0x803c..0x803e]` to issue two follow-up controller
   transactions at runtime-base offsets `+0x009f` and `+0x00d1`, echoing one
   byte back through the FIFO each time.

That makes `0x48a0` and `0x4b4f` good status-observation targets, but still
not the missing hard CDD decoder. They are more likely the place where the
controller tells the 8051 side "I have work/status for you" after another
hidden engine has acted.

## Follow-Up: `0x40b2`, `0x51bc`, And The Packet Return Path

A second static pass traced the immediate handoff around:

```text
0x268a -> 0x48e7 -> 0x51bc -> 0x40b2 -> 0x27e9 service branch
```

The useful correction is that `FUN_CODE_51bc` does not look like the CDD
materializer either. It is more like a controller FIFO/config upload helper:

```text
0x51bc:
  load/prep 0x803b and 0x810e via 0x1e1c
  if xdata[0x48a0].7 is clear:
      toggle 0x4968 / 0x4960 / 0x4961
      write 0x40c0 = dc, 0x40d3 = 20, 0x40c3 = 80 then 00, 0x40c2 = 02
  clear 0x4990..0x4994 status-ish bytes
  call 0x6012 with code table 0x439e, length 0x20
  write a long code table beginning at 0x4452 to controller FIFO 0x4098
```

That points to controller configuration or a canned command upload, not a
record-by-record decompressor.

The branch from `FUN_CODE_40b2` at `0x41e3` is now clearer:

```text
restore xdata[0x4023] from xdata[0x80b0]
FUN_CODE_1009(5)
FUN_CODE_141e(0)           ; selector 0 reads the 0x4e1b predicate
if 0x4e1b != 1:
    FUN_CODE_1009(1)
else:
    copy 0x8229..0x822c -> 0x8245..0x8248
    refresh/fill 0x8249..0x824c and 0x824d..0x8250
    FUN_CODE_111a(0x02)
```

So the `0x4e1b` flag set by `FUN_CODE_111a(0x80)` decides whether the later
continuation `FUN_CODE_111a(0x02)` is even attempted.

The most promising observation point is still the `0x48a0.4` controller-service
branch at `0x27fa`, because it copies controller-supplied bytes into ordinary
XDATA:

```text
if xdata[0x48a0].4:
    clear xdata[0x48a0].4
    read controller address 00:0000
    discard/record one leading FIFO byte into IRAM[0x29]
    copy 12 FIFO bytes -> xdata[0x818a..0x8195]
    copy 32 FIFO bytes -> xdata[0x810e..0x812d]
```

After that packet copy, the code updates packet/status fields:

```text
if xdata[0x47c1].0:
    xdata[0x80e9] = 0x0b
    xdata[0x47d2] |= 0x01
else:
    xdata[0x80e9] = xdata[0x47c5]
    xdata[0x80ea] = xdata[0x47c4]
    xdata[0x47d2] &= 0xfe
clear 0x4014..0x4017
```

Bits `0x48a0.6` and `0x48a0.5` are separate status-receiver paths through
`0x4b4f`; after that call they set `0x47c9` to `0x51` or `0x50`, set
`0x47cb = 0x54`, clear `0x47c4/0x47c5`, and write `0x47d0 = 0x10`.

Practical next implication: a low-risk currentboot observation hook should
capture `0x818a..0x8195`, `0x810e..0x812d`, `0x47c1..0x47d2`, and
`0x48a0/0x4e1b` around mode-2/parser continuation attempts. Those windows are
more likely to contain controller-returned state than arbitrary decoded CDD
addresses.

## Next Read

If we continue static-only, the next best target is the branch after
`FUN_CODE_40b2` in normal boot:

```text
0x268a -> 0x48e7 -> 0x40b2 -> 0x51bc / main-loop controller service
```

especially the handoff between `0x4e1b`, `0x48a0`, and the `0x4098` FIFO copy
into `0x818a..0x8195` / `0x810e..0x812d`. That is the visible place where the
controller appears to send work back to the 8051 side.
