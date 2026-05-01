# Servo / Mechanics Static Notes

Date: 2026-04-30

These notes are offline only. They collect the static clues that look relevant
to sled/focus/laser control after the `0x070000` currentboot gateway artifact
made the `0x59xx` hardware cluster more concrete.

## Current Model

The visible front LED is probably not a direct 8051 GPIO latch. The registers
that affected LED timing or recovery state (`0x4748`, `0x4780`, and nearby
paths) sit in controller command/status fabric. The same broad fabric touches
the `0x59xx` and `0x5axx` register cluster that caused real sled movement
during earlier live probes.

The better model is:

```text
8051-visible code/status layer
  -> 0x47xx / 0x48xx controller command fabric
  -> 0x59xx / 0x5axx mechanics/servo register cluster
  -> controller/CDD-owned actuator behavior
```

That makes `0x59xx` interesting for the end goal, but not safe to poke blindly.

## Strong Static Anchors

### Normal Runtime Corroboration

The later normal-runtime tile harvest independently pulled the same
`0x4860..0x486a` cluster out of the public `READ BUFFER id=01 offset=0x070000`
work window:

```text
analysis/8051/normal-4860-cluster-20260501.md
```

That matters because it links the currentboot/gateway mechanics hints to code
that is live in ordinary `LD5M` mode. Normal runtime paths set and clear
`0x4860.2` and `0x4864.0` as a pair, toggle `0x4867.7` together with
`0x480b.4`, mirror `0x4863` through `xdata[0x8630]`, and initialize
`0x4860..0x486a` immediately after a packet/controller command sequence. This
strengthens the "hardware-control/mailbox cluster" interpretation. It still
does not make these safe raw GPIO or actuator bits.

### `FUN_CODE_59f3` / gateway `0x6059`

The LD5M resident function at F0 `0x59f3` appears exactly in the gateway dump at
offset `0x6059`. It is an initialization/reset-like sequence for the mechanics
cluster:

```c
DAT_EXTMEM_5904 = 0;
DAT_EXTMEM_5905 = 0;
DAT_EXTMEM_59c0 = DAT_EXTMEM_59c0 & 0xfe | 4;
DAT_EXTMEM_5906 = DAT_EXTMEM_5906 & 0x1c;
DAT_EXTMEM_592a = DAT_EXTMEM_592a & 0xf7;
DAT_EXTMEM_59f0 = 0;
DAT_EXTMEM_59f1 = DAT_EXTMEM_59f1 & 0x3f;
DAT_EXTMEM_5a00 = DAT_EXTMEM_5a00 & 0xf8;
DAT_EXTMEM_5a01 = 0x18;
DAT_EXTMEM_5a24 = DAT_EXTMEM_5a24 & 0x30;
DAT_EXTMEM_5a31 = DAT_EXTMEM_5a31 & 0xfd;
DAT_EXTMEM_5954 = DAT_EXTMEM_5954 & 0x3f;
DAT_EXTMEM_4860..4865 = 0;
DAT_EXTMEM_4867 = 0x61;
DAT_EXTMEM_486a..486b = 0;
```

This is probably not "move sled now"; it looks like "put the mechanics block
into a known baseline mode." It is still useful because it names the central
registers.

### `FUN_CODE_48e7`

`FUN_CODE_48e7` is a broader initialization path. It reads `0x48a0.7`, calls the
`0x4814` handshake/status wait through `FUN_CODE_63cb(1)`, initializes
`0x4860..0x4864`, configures many `0x47xx` bytes, sets `0x8221.0`, then calls
`FUN_CODE_630e()` and `FUN_CODE_6383()`.

This ties the `0x486x` block to the larger controller setup flow. It also means
the front button/status byte and mechanics setup are not independent subsystems.

### `FUN_CODE_5a68`

When `param_1 != 0`, this path:

- splits `0x470c` into two nibbles;
- masks/configures `0x4735` and `0x470f`;
- sets `0x4748.7` and `0x4700.1`;
- emits two short 4-byte status/debug records through `0x8281..0x8284` and
  `FUN_CODE_57f4()`;
- calls `FUN_CODE_0909()`.

This reinforces that `0x4748` is a transaction kick/ack bit, not a clean LED
latch. It may be useful for understanding how mechanics commands announce or
log state transitions.

## Gateway-Only Mechanics Routines

The gateway dump has coherent 8051-looking routines not fully explained by the
resident decompile. The most relevant waypoints are:

| gateway offset | clue |
|---:|---|
| `0x642c` | masks `0x5904/0x590b`, writes `0x4864 = 0x36`, sets bits in `0x4863`, clears `0x486a.6`, then loops while polling `0x4000.7` |
| `0x6fe0` | masks `0x5904`, then conditionally changes `0x59a4`, `0x5907`, `0x599e`, `0x592b`, `0x5997`, `0x5945`, and `0x4867/0x486a/0x486b` |
| `0x8278` | state-gated path that clears `0x5905.6`, branches through larger state routines, and later touches `0x5904`/`0x59f0` |

These look more like real mechanics state-machine paths than simple setup.
They should be mapped before any attempt to command movement from helper code.

## Practical Sled-Movement Theory

The fastest route to a deliberate movement primitive is probably not a raw
single-register write. A raw write risks landing halfway through a command
sequence, which is exactly how earlier probes moved the sled unexpectedly or
wedged the LUN.

Better candidate routes:

1. **Trace natural eject behavior.** GP27 is the real front eject line. When it
   is pulled low, sled/tray behavior happens naturally. A later safe experiment
   can capture XDATA/gateway snapshots immediately before and after a brief
   GP27 pulse and diff the `0x47xx`, `0x48xx`, `0x59xx`, and `0x5axx` clusters.
2. **Call a high-level routine, not a register.** Once the gateway function
   boundaries are better mapped, a helper payload can call a short existing
   routine with controlled arguments, then return through the normal event path.
   `FUN_CODE_59f3` is likely only initialization; the more interesting call
   candidates are the gateway routines around `0x642c`, `0x6fe0`, and `0x8278`.
3. **Use a reversible "setup-only" probe first.** Before moving anything, run a
   helper payload that calls or emulates the known `FUN_CODE_59f3` baseline
   setup and exits. If that is harmless and recoverable, it gives a safer
   substrate for one-step movement experiments.

The end-goal version is a small resident/helper command shim: host sends a
command byte, the shim calls an existing controller routine or writes a known
complete register sequence, and the drive reports success through the response
hook or a Pico-visible line.

## Do Not Do Yet

- Do not brute-force `0x59xx` writes live.
- Do not use the eject button line as a casual input channel; it actuates the
  mechanism.
- Do not assume a front LED blink means we found an LED latch. The LED appears
  coupled to controller state and natural drive activity.
