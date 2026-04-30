# Linux Drive 1 Helper Timing XDATA Channel

Date: 2026-04-30

Host: `jonathan-thinkpad-t480s`

Drive: Linux drive #1, `PLDS DVD+-RW DS-8ABSH`, recovered to `LD5M` after each
partial currentboot run.

## Why This Exists

The original helper bit channel returned:

```text
bit 1 -> helper success path -> event 68 GOOD
bit 0 -> helper error path   -> event 68 DID_ERROR
```

That was enough to read selected XDATA bytes, but Claude's overnight sweep hit
`xdata[0x4704].0 = 0` and then recovery did not complete cleanly. The zero bit
itself was not the useful part of the failure; the useful part was realizing
that using `DID_ERROR` as a data symbol is unnecessarily rough.

The new timing channel always returns through the helper success path. It reads
one bit, delays only when the selected value is present, then returns GOOD.
The host reads the bit from event-68 elapsed time.

## Payload Layout

Hook:

```text
helper plain 0x02b5 / code 0x32af:
30 e6 12 -> LJMP payload
```

Payload slot:

```text
helper plain 0x04f6 / code 0x34f0
```

This uses a long comment string in the helper body rather than the shorter
`Flash Type Error` string at `0x0620`. The conditional timing payload is
20 bytes, too large for the old 16-byte string slot without trampling nearby
helper code.

For `MOVX xdata[addr].bit`, delay-on-one:

```text
MOV DPTR,#addr
MOVX A,@DPTR
JNB ACC.bit,success
delay-loop
success:
LJMP 0x32c4
```

## Calibration

Live calibration with `delay-count = 0x20`:

| case | event 68 |
|---|---:|
| constant `0x00.bit0` | `0.255969s` |
| constant `0x01.bit0` | `0.853324s` |
| threshold used | `0.554646s` |

## First Read

Target:

```text
xdata[0x4704] at the event-68 hook
```

Results:

| bit | event 68 | value |
|---:|---:|---:|
| 0 | `0.256199s` | `0` |
| 1 | `0.255101s` | `0` |
| 2 | `0.255080s` | `0` |
| 3 | `0.258092s` | `0` |
| 4 | `0.255870s` | `0` |
| 5 | `0.257465s` | `0` |
| 6 | `0.259269s` | `0` |
| 7 | `0.257542s` | `0` |

So:

```text
xdata[0x4704] = 0x00
```

That confirms Claude's bit-0 finding and shows the whole byte is zero at this
hook point.

## Follow-Up Controller Cluster Read

Using the same calibration threshold, the next four bytes in the nearby
controller/status cluster were:

| address | value | bits |
|---:|---:|---|
| `0x4708` | `0x90` | `10010000` |
| `0x4709` | `0x00` | `00000000` |
| `0x470a` | `0x64` | `01100100` |
| `0x470b` | `0x06` | `00000110` |

All runs recovered to `LD5M`. The timing split stayed clean: short values were
around `0.257s`, delayed values around `0.854s`.

Static cross-reference note:

- `0x4708` has resident bit writes at `0x5cf5`/`0x5d17`/`0x5d24`.
- `0x4709` has resident bit writes at `0x25cb`/`0x25cf`/`0x25d3`/`0x25e5`
  and `0x5e5c`/`0x5e83`.
- `0x470a.5` is read at `0x6458` and written at `0x244a`.
- `0x470b` is written during resident init/servo-controller setup.

These values are much more structured than the all-`0xff` idle reads and are
worth treating as live initialized controller state, not empty bus noise.

## Operational Notes

- The first target attempt hit a transient `Unit Attention` on the first
  profile-tail command after recovery. The timing reader now retries that
  class of failure.
- Each completed partial run auto-recovered to `LD5M`.
- The Linux sysfs `rev` field may stay stale at `0D5C`; active `sg_inq`
  reported `LD5M`.

## Tools

Builder modes:

```sh
python3 scripts/build_liteon_helper_codeexec_candidate.py \
  --name example \
  movx-bit-delay --addr 0x4704 --bit 0 --payload-offset 0x04f6
```

Reader:

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --addr 0x4704 \
  --calibrate \
  --payload-offset 0x04f6
```

Raw copied run summaries are in ignored local `work/linux-runs/`.
