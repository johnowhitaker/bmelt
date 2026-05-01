# Normal Controller Read Primitive Hypothesis

This note captures a promising interpretation of the normal-runtime
`0x4091..0x4099/0x409c` bridge. It may become the way to ask the live
controller for bytes without falling back to the slow currentboot bit channel.

This is not proven yet. The current evidence is static/disassembly from the
normal work-window corpus plus command tagging from the GET CONFIGURATION run.

## The Candidate Path

The relevant public-window corridor is around `+0x75b8..+0x7665`, with a
GET CONFIGURATION-tagged variant around `+0x70c3`.

Common shape:

```text
wait until xdata[0x4000].7 is clear
load controller address/setup bytes into 0x4091..0x4093
write 0x409c = 0x40
write 0x409c = 0x20 or 0x24
poll xdata[0x409c].5 until clear
read data/status through 0x4098 or 0x4099
copy results into the 0x8a packet shadow or local IRAM counters
```

The long GET CONFIGURATION current run tags the `0x24` variant cleanly:

```text
0x8ac6 -> 0x4091
IRAM-derived bytes -> 0x4092/0x4093
0x409c = 0x40
0x409c = 0x24
poll 0x409c.5
read 0x4099
```

The broader normal-window path shows a nearby `0x20` variant:

```text
0x898a or 0x891b -> 0x4091
computed bytes -> 0x4092/0x4093
0x409c = 0x40
0x409c = 0x20
poll 0x409c.5
read 0x4098 / derived 0x40a0+n window
```

## Host-Shadow Inputs

Several pieces of the candidate routine use packet-shadow bytes:

```text
0x8a4d    appears to be a count/length byte; capped at 0x12 and rounded up if odd
0x8a4e    low nibble selects a subpath or response/status slot
0x8a4b..0x8a54 copied from the 0x47b1 FIFO and reused by other command handlers
```

The `0x8a4d` handling is especially concrete:

```text
if xdata[0x8a4d] == 0: jump to an alternate path
if xdata[0x8a4d] >= 0x12: clamp it to 0x12
if xdata[0x8a4d] is odd: increment it
write xdata[0x8a4d] to xdata[0x47d6]
```

That looks like a byte count or transfer unit count, not an arbitrary flag.

When `xdata[0x8a4e] & 0x0f == 0`, the path also adds a base pointer from
`xdata[0x891e..0x891f]` to the working address in IRAM. When the low nibble is
nonzero, the path emits a `0x71` status byte through `0x47b1` and branches
around some of the address setup.

## Why This Matters

We already know the currentboot controller gateway can read controller space,
but the bit/timing channels are painfully slow. This normal-runtime bridge
looks like a stock code path that already does controller reads for ordinary
host commands. If we can learn which host-visible fields feed `0x8a4d`,
`0x8a4e`, and the IRAM address bytes, we may get a faster read oracle without
patching the CDD decoder or instrumenting the controller directly.

The likely model is:

```text
host packet/CDB bytes
  -> 0x47b1 FIFO
  -> xdata[0x8a49..0x8a54] packet shadow
  -> normal handler transforms selected fields
  -> 0x4091..0x4093 setup
  -> 0x409c command/kick
  -> 0x4098/0x4099 data/status
  -> response shadow / 0x47b1 output
```

## Unknowns

- Which public command family owns the `+0x75b8..+0x7665` path?
- Are `0x4091..0x4093` literal controller addresses, banked selectors, or
  command arguments?
- What distinguishes `0x409c=0x20` from `0x409c=0x24`?
- Is `0x4098` a different FIFO from `0x4099`, or is one data and one status?
- Can a legal read-only host command vary the setup address enough to read
  useful decoded/controller memory?

## Suggested Next Experiments

Keep the first pass read-only:

1. Run isolated normal work-window captures for GET CONFIGURATION variants that
   vary starting feature and request length. Check whether `0x8a4d/0x8a4e`
   shadow values or the `0x409c=0x24` path shift predictably.
2. Run isolated captures for safe `READ BUFFER id=01` offset/length variants.
   Avoid `id=02` by default because it previously hung the optical LUN.
3. Add a static correlation pass that groups packet-shadow handler snippets by
   `xdata[0x8a49]` selector comparisons, then tags which selectors reach the
   `0x4091..0x4093` read-side bridge.
4. If a controllable field is found, try a tiny normal-mode read-only oracle
   over a harmless controller address first, then compare with known public
   response bytes before aiming at decoded CDD targets.
