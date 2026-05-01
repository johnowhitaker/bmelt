# Normal Runtime 0x4860 Cluster Notes

This note pulls together the `0x4860..0x486a` references that surfaced while
mapping the normal packet/controller bridge. The conclusion is deliberately
conservative: this cluster looks hardware-control or mechanics-adjacent, but
it is not yet a confirmed LED, button, sled, focus, or laser register set.

Primary evidence lives in:

```text
analysis/8051/normal-packet-shadow-analysis-20260501.md
analysis/8051/normal-packet-shadow-analysis-20260501.json
```

## Observed References

The expanded packet-shadow target list finds these cluster addresses in normal
work-window captures:

```text
0x4860  376 observations, 4 unique chunks
0x4864  376 observations, 4 unique chunks
0x4867  376 observations, 3 unique chunks
0x4863  352 observations, 4 unique chunks
0x4862  159 observations, 2 unique chunks
0x486a   94 observations, 1 unique chunk
```

The recurring writes are more informative than the raw counts:

```text
0x4860 = 0x00               at +0x7500
0x4860 |= 0x04              at +0x9200/+0x9240/+0x9280/+0x92c0
0x4860 &= 0xfb              at +0x8c40

0x4862 = 0xff               at +0x7500
0x4862 &= 0xfb              at +0x6240/+0x6280

0x4863 = 0x2f               at +0x7500
0x4863 <-> xdata[0x8630]    at +0x8480/+0x8880

0x4864 &= 0xfe              at +0x8c40 and in the +0x7500 setup path
0x4864 |= 0x01              at +0x9200/+0x9240/+0x9280/+0x92c0

0x4867 |= 0x80              at +0x9400/+0x9440/+0x9480/+0x94c0
0x4867 &= 0x7f              at +0x9400/+0x9440/+0x9480/+0x94c0

0x486a |= 0xf0              at +0x7500
```

## Notable Snippets

### Packet-shadow command tail at `+0x7502`

Immediately after the `0x4099/0x409a/0x409b/0x409c=0x14` packet-shadow command
sequence, the normal runtime initializes this cluster:

```text
0x4864 bit0 clear if set
0x4860 = 0x00
0x4861 = 0x60
0x4862 = 0xcf or 0xff depending on IRAM flags
0x4863 = 0x2f
0x4864 = 0xbe then 0xbf
0x4865 = 0xef
0x486a |= 0xf0
```

That is too structured to be random scratch state. It looks like a command
block or hardware register bank being primed after a controller transaction.

### Paired enable/disable around `0x4860.2` and `0x4864.0`

Two separate paths treat `0x4860.2` and `0x4864.0` like paired enable bits:

```text
+0x8bxx:  xdata[0x480e] gates a nearby state path and prepares 0x4860.2 handling
+0x8c56:  clear 0x4864.0, clear 0x4860.2, then call short delay helpers
+0x926c:  set 0x4860.2 and set 0x4864.0 in a broader 0x480e/0x480c/0x41b0 path
```

The original rough note called the `+0x8bxx` path a direct set, but the raw
public window only shows a partial `90 48 60 e0 44 04 ...` island there, not
the full `... f0` store. The complete paired set is the `+0x92xx` family. The
mechanics interpretation still holds, but the exact local control flow should
be treated cautiously.

The surrounding code references `0x480e`, `0x480c`, `0x4806`, `0x48a5`,
`0x4762`, `0x5905`, and `0x5a01`, plus short delay-like calls. That pattern
fits hardware gating or an internal controller handshake better than a simple
software variable.

### `0x4867.7` toggled with `0x480b`

The `+0x9400` family toggles `0x4867.7` while also manipulating `0x480b.4`:

```text
0x480b &= 0xef
0x4867 |= 0x80
...
if not already active:
    0x4867 &= 0x7f
    0x480b &= 0xef
    0x480b |= 0x10
    delay/poll
```

This looks like a latched hardware/status transition. It is worth revisiting
when we are mapping visible mechanics, but it is not yet safe to call it a
specific actuator.

## Working Interpretation

The `0x4860..0x486a` cluster is probably a small hardware-control bank or
mailbox used by the normal runtime while issuing controller/mechanics work. The
strongest current candidates are:

- `0x4860.2`: enable/start bit paired with `0x4864.0`;
- `0x4864.0`: companion enable/ack bit;
- `0x4867.7`: latched transition/status bit tied to `0x480b.4`;
- `0x4863`: command/value byte mirrored through `xdata[0x8630]`;
- `0x4862`: command/value byte whose bit2 is cleared in another path.

Do not treat these as raw GPIO. They may be controller-facing bits that cause
mechanics or servo work only in a valid surrounding state.

## Suggested Next Tests

1. Use read-only normal captures with command families that naturally exercise
   mechanics/state transitions, then check whether the `0x4860` cluster chunks
   are tagged more strongly than baseline.
2. If doing live helper experiments, read `0x4860`, `0x4864`, `0x4867`,
   `0x480b`, `0x480c`, and `0x480e` before/after visible events before writing
   any of these bits.
3. If we later have reliable LED/button exfiltration in normal mode, these
   addresses are good low-volume telemetry targets: single bytes here may say
   more than arbitrary decoded CDD bytes.
