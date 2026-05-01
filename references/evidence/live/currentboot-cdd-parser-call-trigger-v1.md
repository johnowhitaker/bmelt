# Currentboot CDD Parser-Call Trigger v1

Date: 2026-05-01

Host/drive: `jonathan-thinkpad-t480s` `/dev/sg0`, PLDS DS-8ABSH LD5M.

Candidate: `currentboot-response-hook-gateway-bulk-cdd-parser-call-v1`.

Trigger: currentboot INQUIRY hook with `CDB[7:9] = fc e1 00`.

## What The Hook Does

- Seeds the descriptor prestate used by `FUN_CODE_002e`.
- Calls resident CDD parser setup at `0x002e` with descriptor base `0x00007000`.
- Copies `xdata[0x4a00..0x4a3f]` into response bytes `0x21..0x60`.
- Returns marker `0xd3` at response byte `0x20`.
- Keeps the normal bulk controller-gateway reader available for post-trigger samples.

## Result

The hook installed successfully through the helper-bypass flow. Post-F0 SHA-256
matched the target, and a Pico cold power-cycle returned the drive to normal
LD5M before the trigger run.

The live trigger returned the expected marker:

```text
response[0x20] = d3
```

The returned mailbox snapshot was:

```text
0x4a00: 01 03 00 03 00 14 07 00 00 00 00 00 00 20 00 13
0x4a10: 00 00 00 00 01 ea 00 00 01 00 00 00 00 00 00 00
0x4a20: 03 08 10 00 03 fe 00 00 00 00 00 01 00 0f 00 00
0x4a30: 00 07 0f 00 00 00 00 00 00 00 00 00 00 00 00 00
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

This proves `FUN_CODE_002e` can be called from the currentboot response hook
without wedging, and it does populate the visible `0x4a` CDD mailbox. It does
not, by itself, make the decoded CDD runtime range visible in currentboot.

Evidence files are in:

```text
references/evidence/live/currentboot-cdd-parser-call-trigger-v1/
```
