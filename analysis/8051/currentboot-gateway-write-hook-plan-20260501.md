# Currentboot Gateway Write Hook Plan

Date: 2026-05-01

This note records the next volatile patch primitive: a guarded currentboot hook
that can write one byte through the controller gateway and return readback over
the ordinary INQUIRY response.

## Why This Is Useful

The normal runtime public window is not plain currentboot XDATA. The recent
source-localization pass found only 2 exact chunks shared with currentboot
XDATA, but hundreds shared with the currentboot controller/gateway view. That
means the existing guarded XDATA writer probably cannot patch the normal
work-window directly.

The normal snapshots also show response-helper-looking 8051 code in controller
memory. For example, the public normal window always contains this sequence
near `+0xddac`:

```text
90 41 a1 e0 54 18 64 10 ... 90 41 a0 ec f0 ee f0 ... 92 af 22
```

That resembles the visible resident response-byte writer family, but it is not
at the same public-window offset as its logical code address. Likewise, many
normal chunks call `LCALL 0x3d89`, but public offset `+0x3d89` is all zero.
So those calls are probably into a banked/controller code view, not directly
into the visible F0 byte at file offset `0x3d89`.

Practical implication: instead of patching visible F0 command handlers blindly,
try a volatile controller/gateway RAM patch first.

## New Hook Mode

Added builder mode:

```sh
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-cdb-rw-v1 \
  --gateway-cdb-rw \
  --cave-len 0xdd
```

Normal read mode is the proven one-byte gateway reader:

```text
CDB[5] low bits  selector within 64-byte window
CDB[7:9]         24-bit big-endian controller base address
CDB[6]           00
CDB[10]          00
```

Write mode requires both guards:

```text
CDB[6]  = a6
CDB[10] = 5a
CDB[11] = value to write
```

The hook computes the same controller address, writes through
`0x4095..0x4098`, then reads back through `0x4091..0x4098` and returns the
readback byte at response offset `0x20`.

The payload is `0xc0` bytes, so the old `0x80` cave limit is too small. The
LD5M `0x6ee3` FF cave extends to `0x6fc0`, so `--cave-len 0xdd` is the
intended build constraint. It still stops well before `0x6ff0`.

## Host-Side Writer

Added:

```sh
python3 scripts/write_liteon_currentboot_gateway.py \
  --device /dev/sg0 \
  --address 0x018620 \
  --value 0x47
```

`0x018620` is a good first smoke-test address because the currentboot gateway
reader already recovers the helper string `Flash Type Error` there. A write
test can change `F` to `G`, read back, then restore `F`.

## Caution

This is a controller-memory write primitive, not persistent flash programming.
It should be tested first on known scratch/currentboot helper text, then on
normal-overlap pages only if the smoke test proves clean.

The interesting follow-up is not "can we scribble on RAM"; it is whether a
patch to a normal-overlap controller page survives the transition into normal
runtime long enough to affect a safe command response or timing path.
