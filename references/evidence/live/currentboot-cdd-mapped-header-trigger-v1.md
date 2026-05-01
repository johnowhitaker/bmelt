# Currentboot CDD Mapped Header Trigger V1

Date: 2026-05-01

Host/drive separation: Linux drive #1 on `jonathan-thinkpad-t480s`, optical
target `/dev/sg0`.

## What Ran

This run tested `currentboot-response-hook-gateway-bulk-cdd-mapped-header-v1`.
It is the next rung after the negative descriptor-trigger result.

The hook keeps the proven bulk gateway reader and reserves the fake gateway
prefix `CDB[7:8] = fc de` as a guarded trigger. On that trigger it mirrors the
resident CDD parser's mapped-header setup:

- sets `xdata[0x8256..0x8257] = c0 00`;
- sets `IRAM[0x30..0x33] = 00 07 ff ff`;
- loads `R4..R7 = 00 00 70 2c`, the LD5M CDD1 header address;
- calls `0x1717`;
- copies `xdata[0xc000..0xc01f]` into the INQUIRY response;
- returns marker `0xd0` at response byte `0x20`.

The actual trigger CDB was:

```text
12 00 00 00 f0 40 00 fc de 00 00 00
```

## Result

The trigger executed and returned the expected marker:

```text
response[0x20]: 0xd0
expected:       0xd0
```

The mapped bytes at response `0x21..0x40` were the LD5M CDD header:

```text
43 44 44 09 10 16 53 0d 90 00 00 7d ec 03 08 10
87 0e 80 00 00 70 00 18 40 00 1b 3f ff 1b 3f ff
```

As fields, this includes the expected LD5M CDD container values:

```text
CDD2 start:       0x0d9000
CDD1 directory:   0x007dec
final boundary:   0x0e8000
descriptor addr:  0x007000
decoded start:    0x184000
decoded end:      0x1b3fff
```

The decoded CDD candidate windows stayed zero:

```text
before 0x184000 len 0x20: all zero
before 0x184060 len 0x20: all zero
before 0x190690 len 0x20: all zero
after  0x184000 len 0x20: all zero
after  0x184060 len 0x20: all zero
after  0x190690 len 0x20: all zero
```

The known live gateway smoke window still worked:

```text
0x070000 len 0x20:
aff39a1acffcbc0401a40000cffcbc0401a50000cffcbc0401a60000cffcbc04
```

After a Pico cold boot, the drive returned to normal `LD5M`.

## Interpretation

This is the first positive currentboot CDD-controller result in this branch of
the work. Calling the real mapped-header helper at `0x1717` is safe in this
context and it really does copy the requested CDD header into the `0xc000`
mapped window.

It is not yet the decoded CDD breakthrough. The high decoded address range
remained zero, so `0x1717` by itself appears to map/copy a source CDD header,
not wake the full controller-side CDD expansion engine.

The next live step should use this as a foothold rather than repeat the same
decoded-address reads. Useful successors:

- call the next resident parser step after a successful `0x1717` header map;
- vary the mapped source address to learn whether `0x1717` is a general
  controller copy primitive;
- capture the `0x4e80..0x4ea0` status/mailbox bytes immediately after the
  `0x1717` call;
- make a compact trigger that maps selected CDD source records into `0xc000`
  and returns them, then compare those mapped bytes against the known encoded
  F0 image.

## Files

```text
references/evidence/live/currentboot-cdd-mapped-header-trigger-v1/
  summary.json
  before-gateway-184000-0020.bin
  before-gateway-184060-0020.bin
  before-gateway-190690-0020.bin
  after-gateway-184000-0020.bin
  after-gateway-184060-0020.bin
  after-gateway-190690-0020.bin
  after-070000-smoke.bin
  after-070000-smoke.json
```
