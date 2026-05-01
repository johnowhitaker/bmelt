# Currentboot CDD Mailbox Doorbell V2

Date: 2026-05-01

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- remote repo: `/home/jonathan/boastermelt`
- device during the run: `/dev/sg0`
- drive: Linux drive #1

## Summary

This run used the combined currentboot response hook
`currentboot-response-hook-gateway-cdb-bulk-xdata-write-v2`.
It must be built with `--cave-len 0xdd`; the payload is larger than the older
`0x80`-byte currentboot hook cave budget.

The hook keeps the bulk controller-gateway reader, but adds a guarded XDATA
write mode. If host CDB bytes `10..11` are `a5 5a`, the hook writes CDB byte
`9` to:

```text
xdata[(CDB[7:8] as big-endian) + (CDB[5] & 0x3f)]
```

and returns the readback byte at response offset `0x20`. Otherwise it behaves
as the bulk gateway reader:

```text
controller[(CDB[7:9] as big-endian) + (CDB[5] & 0x3f)]
```

The first combined version used an additional guard byte in CDB byte `6`. That
was a bad assumption: byte `6` is not reliably preserved through this
currentboot INQUIRY path. The live-proven v2 guard uses only CDB bytes
`10..11`. The currentboot CDB shadow stores those two guard bytes reversed at
`xdata[0x8194..0x8195]`.

## Live Checks

After installing the v2 candidate and cold-booting into currentboot with event
1:

- the bulk controller-gateway path still returned `Flash Type Error` at
  `controller[0x018620..]`;
- guarded XDATA write/readback worked at `xdata[0x8000]`;
- `xdata[0x4a00] <- 0x01` returned readback `0x01`;
- restoring `xdata[0x4a00] <- 0x00` returned readback `0x00`.

The CDD-controller doorbell test was a negative. Writing `xdata[0x4a00]=1` by
itself did not populate the candidate decoded CDD range in currentboot:

| sample | address | result |
|---|---:|---|
| baseline decoded base | `0x184000..0x1840ff` | all `00` |
| baseline affine group 27 | `0x190690..0x19078f` | all `00` |
| baseline live smoke | `0x070000..0x0700ff` | nonzero live window |
| after `xdata[0x4a00]=1` | `0x184000..0x1840ff` | all `00` |
| after `xdata[0x4a00]=1` | `0x184060..0x18415f` | all `00` |
| after `xdata[0x4a00]=1` | `0x190690..0x19078f` | all `00` |
| after `xdata[0x4a00]=1` | `0x1a63a0..0x1a645f` | all `00` |
| after `xdata[0x4a00]=1` | `0x1aeb80..0x1aec7f` | all `00` |
| after `xdata[0x4a00]=1` | `0x070000..0x0700ff` | unchanged nonzero live window |

The drive was recovered immediately afterward and standard INQUIRY returned
`PLDS DVD+-RW DS-8ABSH LD5M`.

## Interpretation

`xdata[0x4a00]` is live-writable from the currentboot response hook, but the
single doorbell byte is not enough to make the controller expose decoded CDD
memory in the currentboot phase. That narrows the decoded-CDD route: the next
attempt needs a fuller CDD parser/controller command sequence, a later normal
runtime hook, or a better understanding of the hidden controller phase state.

Raw artifacts:

```text
references/evidence/live/currentboot-cdd-mailbox-doorbell-v2-20260501/
```
