# Currentboot CDD Mapped Header Status Trigger V1

Date: 2026-05-01

Host/drive separation: Linux drive #1 on `jonathan-thinkpad-t480s`, optical
target `/dev/sg0`.

## What Ran

This run tested
`currentboot-response-hook-gateway-bulk-cdd-mapped-header-status-v1`, a small
successor to the mapped-header trigger.

The trigger is `CDB[7:8] = fc df`. It calls the same resident helper at
`0x1717`, then copies two windows into the response:

- response `0x21..0x40`: `xdata[0xc000..0xc01f]`;
- response `0x41..0x60`: `xdata[0x4e80..0x4e9f]`.

It returns marker `0xd1` at response byte `0x20`.

## Result

The trigger executed:

```text
CDB:            12 00 00 00 f0 40 00 fc df 00 00 00
response[0x20]: 0xd1
expected:       0xd1
```

The mapped `0xc000` bytes again contained the LD5M CDD header:

```text
43 44 44 09 10 16 53 0d 90 00 00 7d ec 03 08 10
87 0e 80 00 00 70 00 18 40 00 1b 3f ff 1b 3f ff
```

The `0x4e80..0x4e9f` status/mailbox snapshot after the `0x1717` call was:

```text
000000000000000000000000010000000040704c0008001f0000000000000000
```

Expanded by address:

```text
0x4e80..0x4e8b: 00 00 00 00 00 00 00 00 00 00 00 00
0x4e8c..0x4e8f: 01 00 00 00
0x4e90..0x4e97: 00 40 70 4c 00 08 00 1f
0x4e98..0x4e9f: 00 00 00 00 00 00 00 00
```

The decoded CDD candidate windows still stayed zero:

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

This confirms the mapped-header result and gives the first compact live
snapshot of the `0x4e80` controller/status region immediately after `0x1717`.
The nonzero cluster at `0x4e8c` and `0x4e91..0x4e97` is likely part of the
controller-side read/map descriptor.

The result still does not populate decoded CDD memory. The next step should
compare this status snapshot against either:

- a no-call baseline of `0x4e80..0x4e9f` in the same currentboot phase;
- a status snapshot after mapping a different source address;
- a trigger that performs the resident parser step after `0x1717`.

The immediate static question is what the bytes `01` at `0x4e8c` and
`40 70 4c 00 08 00 1f` at `0x4e91..0x4e97` mean in the surrounding
`0x16ef/0x1717/0x17bb` controller command path.

## Files

```text
references/evidence/live/currentboot-cdd-mapped-header-status-trigger-v1/
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
