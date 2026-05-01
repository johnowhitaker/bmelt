# Currentboot CDD Parser Second-Doorbell Trigger v1

Date: 2026-05-01

Host/drive: `jonathan-thinkpad-t480s` `/dev/sg0`, PLDS DS-8ABSH LD5M.

Candidate: `currentboot-response-hook-gateway-bulk-cdd-parser-second-doorbell-v1`.

Trigger: currentboot INQUIRY hook with `CDB[7:9] = fc e2 00`.

## What The Hook Does

- Seeds the same `FUN_CODE_002e` descriptor prestate as the parser-call trigger.
- Calls resident CDD parser setup at `0x002e`.
- Clears `xdata[0x4a00]`.
- Mirrors `xdata[0x4a24] -> xdata[0x4a28]` and
  `xdata[0x4a25] -> xdata[0x4a29]`.
- Writes `xdata[0x4a00] = 1`.
- Calls `0x1667`.
- Returns marker `0xd4` at response byte `0x20`.
- Keeps the normal bulk controller-gateway reader available for post-trigger samples.

This mirrors the visible side effects of the later resident helper at `0x08d0`,
but performs them directly so the hook does not depend on the decompiler's
unclear 8051 calling convention for `FUN_CODE_08d0`.

## Result

The hook installed successfully through the helper-bypass flow. Post-F0 SHA-256
matched the target, and a Pico cold power-cycle returned the drive to normal
LD5M before the trigger run.

The live trigger returned the expected marker:

```text
response[0x20] = d4
```

Immediate and delayed gateway reads from decoded CDD candidates stayed all zero:

```text
0x184000
0x184060
0x190690
0x191010
0x198900
0x1a0000
```

## Interpretation

The `0x4a24/25 -> 0x4a28/29` mirror plus `0x4a00` doorbell is not sufficient to
make the decoded CDD runtime range appear in currentboot. Together with the
parser-call result, this suggests the visible mailbox path can be replayed in
currentboot, but the active CDD expansion/runtime engine is either absent,
uninitialized, or mapped somewhere else in this boot personality.

Evidence files are in:

```text
references/evidence/live/currentboot-cdd-parser-second-doorbell-trigger-v1/
```
