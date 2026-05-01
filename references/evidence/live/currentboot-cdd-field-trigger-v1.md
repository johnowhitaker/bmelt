# Currentboot CDD Field Trigger V1

Date: 2026-05-01

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- remote repo during run: `/home/jonathan/bmelt-live`
- device during the run: `/dev/sg0`
- drive: Linux drive #1

## Summary

This run tested a special currentboot response hook:
`currentboot-response-hook-gateway-cdb-bulk-cdd-field-replay-v1`.

The hook keeps the proven controller-gateway bulk reader for ordinary CDB
addresses. A fake preserved address, CDB bytes `7..9 = fc dd 00`, does not read
the gateway. Instead it writes the static LD5M field-only CDD mailbox package:

```text
xdata[0x4a00] = 00
xdata[0x4a01] = 03
xdata[0x4a02] = 00
xdata[0x4a03] = 03
xdata[0x4a05] = 14
xdata[0x4a06] = 07
xdata[0x4a20] = 03
xdata[0x4a21] = 08
xdata[0x4a22] = 10
xdata[0x8258..0x825b] = 00 0d 90 00
xdata[0x4a00] = 01
```

The trigger returned `0xcd` at response byte `0x20`, so the special hook path
executed.

## Result

The decoded CDD candidate gateway windows stayed all zero:

| sample | before | after |
|---|---|---|
| `controller[0x184000..0x1840ff]` | all `00` | all `00` |
| `controller[0x184060..0x18415f]` | all `00` | all `00` |
| `controller[0x190690..0x19078f]` | all `00` | all `00` |

A post-run smoke read of `controller[0x070000..0x0700ff]` was nonzero, proving
the gateway reader was still alive:

```text
af f3 9a 1a cf fc bc 04 01 a4 00 0c ff cb c0 40 ...
```

## Interpretation

This is a stronger negative than the earlier one-byte doorbell test. The hook
definitely wrote the full header-derived `0x4a` field package and rang
`0x4a00`, but currentboot still did not expose decoded CDD memory at the
advertised decoded range or the affine-derived oracle target.

The next currentboot-side replay step would have to include more of the
resident parser prestate, especially the descriptor-derived `0x8244..0x8255`
window and possibly the `0x4e80/84/88/8c` mapped-header command. The latter is
the higher-risk controller command path, not just passive mailbox staging.

Raw artifacts:

```text
references/evidence/live/currentboot-cdd-field-trigger-v1/
```
