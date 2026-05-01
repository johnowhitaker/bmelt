# Currentboot CDD Descriptor Trigger V1

Date: 2026-05-01

Host/drive separation: Linux drive #1 on `jonathan-thinkpad-t480s`, optical
target `/dev/sg0`.

## What Ran

This run tested `currentboot-response-hook-gateway-bulk-cdd-descriptor-replay-v1`.
It was a follow-up to the field-only trigger and the failed one-byte prestage
hook.

The first compact prestage hook tried to pair descriptor/status prestate with a
one-byte gateway reader. It installed successfully, but the first high-address
baseline read timed out before the trigger ran. A Pico cold boot recovered the
drive to normal `LD5M`.

The descriptor trigger keeps the proven bulk gateway reader instead. To fit in
the `0x6ee3` cave, it writes only:

- nonzero outer-descriptor-derived fields at `xdata[0x8246]`, `0x824a`,
  `0x824d`, `0x8252`, and `0x8254`;
- the LD5M CDD field package at `xdata[0x4a01/03/05/06/20/21/22]`;
- the CDD2 start field at `xdata[0x8258..0x825b]`;
- the final `xdata[0x4a00] = 1` doorbell.

The fake gateway prefix `CDB[7:8] = fc dd` triggers the replay and returns
`0xcf` at response byte `0x20`.

## Result

The trigger executed:

```text
CDB: 12 00 00 00 f0 40 00 fc dd 02 00 00
response[0x20]: 0xcf
expected:       0xcf
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

This rules out a second tempting shortcut: passively preloading the visible
descriptor-derived fields plus the CDD field package is still not enough to
populate the advertised decoded CDD range in currentboot.

The missing piece is probably one of:

- the `0xc000` mapped-header setup done by the `0x4e80/84/88/8c` controller
  command path;
- additional derived status/direct state omitted from this compact bulk hook;
- a later normal-runtime phase where the controller CDD engine is active.

The bulk hook itself is still healthy; the zero result is about controller/CDD
state, not a dead gateway reader.

## Files

```text
references/evidence/live/currentboot-cdd-descriptor-trigger-v1/
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
