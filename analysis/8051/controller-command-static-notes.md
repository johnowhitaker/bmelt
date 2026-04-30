# Controller Command Static Notes

Date: 2026-04-30

This is the first-pass map of the visible 8051 controller command vocabulary
that seems relevant to front-panel/LED work. It is derived from
`analysis/8051/ldm58051_c.c` plus the generated XDATA cross-reference report.

## `0x4748/0x474d/0x474e`: Command Start And Opcode Bytes

The strongest pattern is `FUN_CODE_47b0`. It gates on `0x474d` being negative,
sets command bytes, adjusts selector/config registers, clears `0x4748.7`, waits
through `FUN_CODE_60c4`, then sometimes sets `0x4748.7` again.

Observed command pairs from visible code:

| caller condition | `0x474d` | `0x474e` | nearby setup |
|---|---:|---:|---|
| `param_2=1`, `param_1=2` | `0x45` | `0x90` | `0x4726=(..&fc)|1`, `0x479e=0` |
| `param_2=1`, `param_1=3` | `0x45` | `0x90` | `0x4726=(..&fc)` or `(..&fc)|3`, `0x479e|=0x10` |
| after `param_2=1` setup | | | `0x479e=(0x479e&0x10)|0x87` |
| `param_2=0`, `param_1=3` | `0x45` | `0xc0` | `0x4726=(..&fc)` or `(..&fc)|3` |
| `param_2=0`, `param_1=2` | `0x45` | `0xa0` | `0x4726=(..&fc)|1` |
| `param_2=0`, `param_1=1` | `0x45` | `0x90` | `0x4726=(..&fc)|2` |
| `param_2=0`, `param_1=5` | `0x15` | `0x50` | `0x4726=(..&fc)|1` |
| `param_2=0`, `param_1=4` | `0x05` | `0x30` | `0x4726=(..&fc)|2` |
| after `param_2=0` setup | | | `0x479e &= 0x7f` |

`FUN_CODE_4c7f` wraps this with whole-byte writes to `0x4748`:

- `0x4748 = 0x88` for one path;
- `0x4748 = 0x98` for the other path;
- both paths call `FUN_CODE_60c4`.

`FUN_CODE_60c4` is the wait helper:

```c
DAT_INTMEM_39 = DAT_EXTMEM_482c;
DAT_INTMEM_3a = DAT_EXTMEM_482d;
while (true) {
  DAT_EXTMEM_482b = 5;
  if (DAT_EXTMEM_474d < 0) break;
  DAT_INTMEM_3b = DAT_EXTMEM_482c;
  DAT_INTMEM_3c = DAT_EXTMEM_482d;
}
return DAT_EXTMEM_474d;
```

Interpretation: `0x474d/0x474e` look like opcode/status bytes, `0x4726` and
`0x479e` look like mode/config around that command, `0x4748.7` is a transaction
start/ack bit, and `0x482b=5` polls for completion/status. This is exactly the
shape that made `0x4748` hazardous during LED probes.

## `0x482b/0x482c/0x482d`: Small Poll/Query Port

Stock writers to `0x482b` use only these shapes in the visible code:

| function | write | follow-up |
|---|---|---|
| `FUN_CODE_4230` / `FUN_CODE_423b` | `0x482b = 1` | read `0x482c/0x482d` repeatedly while checking `0x472c/0x472e` |
| `FUN_CODE_6048` | `0x482b = 1` | after waiting on `0x55ce.1` |
| `FUN_CODE_60c4` | `0x482b = 5` | poll until `0x474d` becomes negative |
| `FUN_CODE_60ff` | `0x482b = param_3 | 1` | read `0x482c/0x482d` in a timed loop |
| `FUN_CODE_640a` / `FUN_CODE_6428` | `0x482b = param_1 | 1` | read `0x482c/0x482d` once |

The command values we can name from visible call sites are therefore `1`, `3`
via `param_3=2`, and `5`. This is not enough to invent new commands, but it is
enough to avoid blind writes and to recognize stock poll loops.

## `0x4814`: Status Byte Sharing Button And Handshake Bits

`FUN_CODE_63cb` writes:

```c
DAT_EXTMEM_4822 = param_1 >> 1;
DAT_EXTMEM_4821 = 0xc0;
do {
} while (-1 < DAT_EXTMEM_4814);
```

The live Pico result shows `0x4814.4` is the eject-button sense. This means the
same status byte also carries a bit-7 controller handshake. If we later use the
button line as input, the safer mental model is "read a packed front-panel
status byte" rather than "poll a raw GPIO register".

## `0x483f`: Clean-Looking But Unexplained Latch

`FUN_CODE_64f3` is the only direct visible writer:

```c
if (_7_0 != 0) {
  DAT_EXTMEM_483f = 1;
} else {
  DAT_EXTMEM_483f = 0;
}
```

Call sites are setup/transfer-related, not obviously front-panel-related. Still,
unlike `0x4748`, it is a narrow 0/1 latch rather than a command fabric register.
If another live LED probe is justified, `0x483f` is a better candidate than
continuing to perturb `0x4748` or `0x4780`.
