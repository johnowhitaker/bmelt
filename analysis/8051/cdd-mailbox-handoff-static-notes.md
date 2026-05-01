# CDD Mailbox Handoff Static Notes

Date: 2026-04-30

Scope: static only. This note cross-checks the Ghidra C export against raw
8051 disassembly from `analysis/8051/ldm58051.bin`. Treat the decompiled C as
an orientation aid, not as ground truth: the export has duplicate XDATA
declarations and can obscure pointer arithmetic around `MOVX`.

## Better References

For CDD/controller work, use this priority order:

1. raw `analysis/8051/ldm58051.bin` disassembled as 8051 at base 0;
2. focused scripts and notes derived from raw bytes;
3. Ghidra/r2 graph views for navigation;
4. `analysis/8051/ldm58051_c.c` only for quick search terms and rough control
   flow.

Useful command shape:

```sh
r2 -q -a 8051 -b 8 -m 0x0 -e scr.color=false \
  -e asm.bytes=true -e asm.lines=false \
  -c 'pD 0x160 @ 0x79b' analysis/8051/ldm58051.bin
```

## CDD Parser / Mailbox Setup

`FUN_CODE_002e` is still the best visible 8051 CDD parser and handoff path.
Raw disassembly confirms the important Ghidra-derived mailbox writes:

- `0x0034`: checks and clears `xdata[0x4a00]` if already set.
- `0x03d2`: writes `xdata[0x4a00] = 1`, then writes `xdata[0x4a01]`
  from IRAM `0x67`, and clears `xdata[0x4a02]`.
- `0x03f0..0x0410`: reads CDD header byte `+0x06` and writes:
  - `xdata[0x4a03] = header[0x06] & 0x03`;
  - `xdata[0x4a05] = header[0x06] >> 2`;
  - `xdata[0x4a06] = header[0x10] & 0x0f`.
- `0x0419..0x044f`: reads CDD header bytes `+0x0d..+0x0f` and writes
  them into `xdata[0x4a20..0x4a22]`.

That strongly supports the current model: visible 8051 code validates and
packages CDD header fields for a controller-side engine; it does not contain a
complete CDD body decoder.

## Secondary `0x4a10` Window

The path around `0x079b..0x085e` uses another mailbox/status window:

- `0x079b`: writes `xdata[0x4a10] = 1`.
- `0x07a1`: clears `xdata[0x4a12..0x4a13]`.
- `0x07bd..0x07ec`: copies bytes from the CDD/header pointer into
  `xdata[0x4a17]` and `xdata[0x4a16]`, then writes `xdata[0x4a11] = 1`.
- `0x0804..0x0852`: compares subsequent source bytes against
  `xdata[0x4a19]` and `xdata[0x4a18]`; mismatch returns carry clear.
- `0x085e`: clears `xdata[0x4a10]` after the loop.

This looks like a controller-mediated byte/window check rather than a local
software decompressor.

## Final `0x4a00` Doorbell Path

The later path around `0x08c8..0x08f0` reads `xdata[0x4a26..0x4a27]`.
If those two bytes are nonzero:

- `0x08d2`: clears `xdata[0x4a00]`;
- `0x08d7..0x08e5`: copies `xdata[0x4a24..0x4a25]` into
  `xdata[0x4a28..0x4a29]`;
- `0x08e6..0x08eb`: writes `xdata[0x4a00] = 1`;
- `0x08ec`: calls `0x1667`.

So `0x4a00` is a real doorbell/state byte, not just a passive mirror.

## `0x4e` Command / Status Doorbell

The `0x4e` block gives a second controller command surface:

- `0x175c`: returns `xdata[0x4ea0]` in `r7`; this is the cheap status poll.
- `0x1872`, `0x1880`, `0x188e`, `0x1894`: writes three 32-bit values into
  `xdata[0x4e80]`, `0x4e84`, `0x4e88`, then sets `xdata[0x4e8c] = 1`.
- `0x1923`, `0x1929`, `0x193b`, `0x1941`: similar command issue path, but
  zeroes `xdata[0x4e84]` before setting `0x4e8c`.
- `0x1962`: writes a 16-bit value to `xdata[0x4e14..0x4e15]`, then sets
  `xdata[0x4e16] = 1`.

Raw `LCALL` search gives these current callers:

```text
0x17ae: 0x0663, 0x1273
0x17b3: 0x01d9
0x17bb: 0x06e9, 0x078c, 0x08af, 0x1251, 0x173f
0x189c: 0x1294, 0x12b5, 0x12d6, 0x61cd
0x175c: 0x01dc, 0x0666, 0x06ec, 0x078f, 0x08b2, 0x14b0, 0x14b5, 0x14c3,
        0x1742, 0x184a, 0x18fb
```

The cluster at `0x1238..0x12d9` looks like a dispatcher over several
controller command forms. It loads 32-bit fields from IRAM pointer blocks
around `0x5d`, `0x61`, and `0x65`, then chooses `0x17bb`, `0x17ae`, or
`0x189c` with selector values `r7 = 0/1/2`. This is a better next target than
blind Ghidra search if we want to name the `0x4e80/84/88/8c` descriptor fields.

Follow-up raw disassembly clarifies the selector: `0x1daf` is a 32-bit
left-shift helper, and both `0x17bb` and `0x189c` call it with `r0 = 0x15`
after loading the selector into `r7`. So the selector contributes
`selector << 21`, i.e. a `0x200000`-byte bank offset, before the command writes
`xdata[0x4e80]`.

The two wrappers are therefore best described as banked controller-memory
command issuers:

```text
0x17bb:
  validate three local ranges against a 0x200000-byte window
  xdata[0x4e80] = pointer_a + (selector << 21)
  xdata[0x4e84] = pointer_b
  xdata[0x4e88] = pointer_c
  xdata[0x4e8c] = 1

0x189c:
  validate two local ranges against a 0x200000-byte window
  xdata[0x4e80] = pointer_a + (selector << 21)
  xdata[0x4e84] = 0
  xdata[0x4e88] = pointer_b
  xdata[0x4e8c] = 1
```

That makes the earlier `r7 = 0/1/2` values look like controller address-bank
selectors, not small command opcodes. It also explains why caller code spends
so much effort comparing pointer windows before setting `0x4e8c`: the command
surface appears to reject or protect transfers that would cross a 2 MiB bank
window. This may matter for future decoded-CDD work because the advertised
`0x184000..0x1b3fff` range sits inside bank 0, while adjacent controller
address banks may expose different currentboot/runtime views.

These paths are consistent with the field guide's current model: the visible
8051 side stages command descriptors and polls status, while the hidden
controller/CDD side owns the actual decode/servo details.

## Immediate Static Follow-Ups

- Trace callers of `0x17ae`, `0x17bb`, and `0x189c` to classify the three
  `0x4e80/84/88/8c` command forms.
- Cross-reference writes to `0x4a24..0x4a29` and reads from `0x4a26..0x4a27`;
  these may describe controller-returned CDD result windows.
- Keep any future Ghidra claim about `0x4a`/`0x4e` guarded until the exact
  raw `MOVX` path has been checked.
