# Currentboot CDD Mapped Header Status64 Trigger V1

Date: 2026-05-01

Host/drive separation: Linux drive #1 on `jonathan-thinkpad-t480s`, optical
target `/dev/sg0`.

## What Ran

This run tested
`currentboot-response-hook-gateway-bulk-cdd-mapped-header-status64-v1`.

The trigger is `CDB[7:8] = fc e0`. It calls the resident mapped-header helper
at `0x1717`, then copies:

- response `0x21..0x40`: `xdata[0xc000..0xc01f]`;
- response `0x41..0x80`: `xdata[0x4e80..0x4ebf]`.

It returns marker `0xd2` at response byte `0x20`.

## Result

The trigger executed:

```text
CDB:            12 00 00 00 f0 40 00 fc e0 00 00 00
response[0x20]: 0xd2
expected:       0xd2
```

The mapped `0xc000` bytes again contained the LD5M CDD header:

```text
43 44 44 09 10 16 53 0d 90 00 00 7d ec 03 08 10
87 0e 80 00 00 70 00 18 40 00 1b 3f ff 1b 3f ff
```

The `0x4e80..0x4ebf` snapshot after the `0x1717` call was:

```text
0x4e80: 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00
0x4e90: 00 40 70 4c 00 08 00 1f 00 00 00 00 00 00 00 00
0x4ea0: 06 00 00 00 9a d1 bb 4b 00 00 18 00 00 00 00 00
0x4eb0: 00 08 00 0f 00 00 00 00 07 00 00 00 00 00 00 00
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

This confirms the `0x1717` transaction all the way through the resident
completion status. `xdata[0x4ea0]` is `0x06`, exactly the value the resident
polls for after issuing the `0x4e8c` command.

The `0x4e90` row also matches the static model of the transaction. The command
maps source `0x0040702c` for `0x20` bytes into a destination ending at
`0x0008001f`:

```text
source end-ish:      00 40 70 4c
destination end-ish: 00 08 00 1f
```

That is `0x0040702c + 0x20 = 0x0040704c` and
`0x0007ffff + 0x20 = 0x0008001f`, matching the helper setup.

So the mapped-header operation is understood better now:

1. `0x17bb` issues a banked controller transfer.
2. `0x4ea0` reports done with `0x06`.
3. `0x16ef` points the local window at the mapped data.
4. `xdata[0xc000]` exposes the requested CDD source header.

This still does not wake the decoded CDD range at `0x184000`. The next live
question is probably no longer "does `0x1717` work?" It does. The next question
is which later parser/controller step consumes this mapped header and starts
the CDD engine, or whether that step only exists in normal runtime.

## Files

```text
references/evidence/live/currentboot-cdd-mapped-header-status64-trigger-v1/
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
