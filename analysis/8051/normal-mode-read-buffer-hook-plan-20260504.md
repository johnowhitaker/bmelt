# Normal-Mode READ BUFFER Hook Plan

Date: 2026-05-04

This is the first concrete hook plan after the Drive #3 normal-mailbox pass.
It is a plan only. No live write is implied by this note.

## Goal

Build the smallest normal-mode proof that stock host commands can reach
patched normal runtime code and receive a changed response.

The desired first success is deliberately boring:

```text
READ BUFFER mode=1 id=01 offset=0x070bad
```

returns a different, predictable public-window slice only when the hook is
installed. It does not need to return arbitrary memory yet.

## New selector result

The normal mailbox pass found a clean volatile state bit:

```text
MODE SENSE(10) page 0x08 byte 0x02: current 0x04
MODE SELECT(10) PF=1 SP=0 can change it 0x04 -> 0x00
MODE SELECT(10) can restore it 0x00 -> 0x04
```

This is useful, but its backing XDATA/controller storage is not localized yet.
So it should not be the first hook gate.

For the first hook, use the READ BUFFER CDB itself as the gate. The public
bridge already exposes the relevant CDB offset bytes:

```text
xdata[0x8a4c] = READ BUFFER CDB byte 3 / offset high
xdata[0x8a4d] = READ BUFFER CDB byte 4 / offset mid
xdata[0x8a4e] = READ BUFFER CDB byte 5 / offset low
```

Once a response hook is proven, the page `0x08` bit can become a cleaner
armed/disarmed selector if we later find where the normal runtime stores it.

## Response bridge target

The best host-visible target remains the normal public response bridge chunk,
currently represented by known-output record 59 at record-relative `0x10`.

The first 0x4c bytes disassemble as:

```asm
; record 59 relative 0x10, public chunk 20ea2ab16891...
mov  0x29, r2
movx a, @dptr
swap a
anl  a, #0x0f
jnb  acc.0, use_cdb_offset

mov  dptr, #0x8a4c
movx a, @dptr
clr  c
subb a, #0x0e
jc   use_cdb_offset

mov  dptr, #0x4011
mov  a, #0x0e
movx @dptr, a
sjmp after_4011

use_cdb_offset:
mov  dptr, #0x8a4c
movx a, @dptr
mov  dptr, #0x4011
movx @dptr, a

after_4011:
mov  dptr, #0x8a4d
movx a, @dptr
mov  dptr, #0x4012
movx @dptr, a

mov  dptr, #0x8a4e
movx a, @dptr
mov  dptr, #0x4013
movx @dptr, a

mov  dptr, #0x8a50
movx a, @dptr
mov  r7, a
inc  dptr
movx a, @dptr
mov  r0, #0xa9
xch  a, r7
mov  @r0, a
inc  r0
mov  a, r7
mov  @r0, a
mov  @r0, a
inc  r0
mov  @r0, #0x01
lcall 0xefb6
inc  0x7c
inc  0x7c
ret
```

This bridge is attractive because the hook can be a conditional argument
rewrite rather than a whole new response generator. The stock code already
writes the controller response-address registers `0x4011..0x4013` and kicks
the response path with `LCALL 0xefb6`.

## First hook behavior

Gate:

```text
if xdata[0x8a4c..0x8a4e] == 07 0b ad:
    substitute response offset = 07 db c0
else:
    run stock bridge
```

Expected host-visible effect:

```text
READ BUFFER id=01 offset=0x070bad len=0x80
```

should return the stable bytes from the public `0x07dbc0` window instead of
the stock `0x070bad` bytes.

Why this is safer than a marker payload:

- it only changes the same controller arguments the stock bridge already
  writes;
- it does not invent a response buffer;
- it avoids writing custom marker bytes into unknown normal RAM;
- it gives an unambiguous direct SCSI response diff.

Once that works, the next payload can redirect to a scratch window containing
`NMIO` plus selected state bytes.

## Delivery problem

The hook target is planned, but the delivery primitive is still the open
question.

Known facts:

- The response bridge chunk is stable in normal captures.
- Currentboot `+0x7140` is unrelated, so directly writing that public offset
  from currentboot is not expected to patch the normal bridge.
- The write-side helper at public `+0xdbc0..+0xdc7f` is byte-identical in
  currentboot gateway dumps and normal captures. That makes it the best
  candidate for a currentboot-to-normal carryover test, but it touches
  `0x4095..0x4098` and should not be patched casually.

Therefore the safe execution order is:

1. Baseline normal `READ BUFFER id=01 offset=0x070bad` and `0x07dbc0`.
2. Test currentboot-to-normal carryover using an inert shared marker, not code.
3. If inert marker carryover works, try a behavior-neutral byte in the shared
   `+0xdbc0..+0xdc7f` helper and verify it appears in normal.
4. Only after shared code carryover is proven, use that shared helper as the
   carrier for the `0x070bad -> 0x07dbc0` redirect proof.
5. If carryover fails, stop this route and search for a true normal-mode write
   primitive. Do not fall back to random CDD source mutations.

## Acceptance checks

The hook is considered real only if all of this holds:

- Drive remains `PLDS DVD+-RW DS-8ABSH LD5M`.
- Stock `0x070bad` and `0x07dbc0` responses are captured before patching.
- With hook installed, `0x070bad` matches the chosen redirected window.
- With hook absent or disabled, `0x070bad` returns stock bytes again.
- No sled/eject/media command is involved.
- The result is a direct SCSI response change, not just a public work-window
  phase shift.

## Practical read

This is not yet arbitrary normal-mode I/O. It is the smallest response-route
proof I think is worth attempting:

```text
host CDB bytes -> normal runtime branch -> controller response args -> host-visible bytes
```

If it works, the next hook can replace the fixed redirect with a tiny
`NMIO` response that returns `xdata[0x8a49..0x8a54]`, the MODE SELECT page-bit
state if localized, or selected controller/mailbox bytes.

## Carryover Gate Result

The inert carryover gate was run after this plan was written. It failed safely:

- the currentboot gateway hook installed and Drive #3 recovered to `LD5M`;
- a harmless marker write at controller/public `0x074030` changed `ff -> 5a`
  while currentboot was active;
- `sg_reset` and USB bridge reauthorization both stayed in currentboot;
- stock recovery returned to `LD5M` but wiped the marker back to `ff`;
- the `0x070bad` and `0x07dbc0` READ BUFFER hashes matched stock afterward.

So the response-redirect hook design remains useful, but this delivery route is
not viable. Do not attempt the shared-code hook via volatile currentboot
carryover unless a different, proven currentboot-to-normal transition appears.

Detailed evidence:

```text
analysis/8051/drive3-normal-hook-carryover-20260504.md
references/evidence/live/drive3-normal-hook-carryover-20260504T203335Z/
```
