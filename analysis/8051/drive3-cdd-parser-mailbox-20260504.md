# Drive 3 CDD Parser/Mailbox Replay

Date: 2026-05-04

Host/drive:

- Linux host: `jonathan-thinkpad-t480s`
- Device: `/dev/sg0`
- Drive: Drive #3, fresh `PLDS DVD+-RW DS-8ABSH LD5M`

## Scope

This pass intentionally did not modify the CDD streams, CDD auth/trailer
material, or any record59/60-style CDD source bytes. The only firmware changes
were temporary currentboot response-hook installs in the low resident prefix:

- `0x4fc9`: hook branch
- `0x6ee3`: erased-code-cave payload

The final restore returned the full 1 MiB F0 image to the stock LD5M SHA-256:

```text
488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39
```

## Operational Note

Drive #3 appears to have media inserted. After Pico power cycles, the drive
sometimes needed a longer settle delay before accepting the event-1 profile
tail. Early attempts failed with:

```text
Not Ready / Logical unit is in process of becoming ready
```

Waiting around 25 to 30 seconds after the power cycle made event 1 succeed.
The tray was ejected after stock verification so the media can be removed.

## Parser-Call Trigger

Installed candidate:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-bulk-cdd-parser-call-v1/
```

Important detail: the hook is a currentboot hook, not a normal LD5M INQUIRY
hook. Triggering it in normal mode returned ordinary EXTRAINQ/date material.
The correct flow is:

1. install hook through helper-bypass;
2. Pico cold power-cycle;
3. wait for the drive to settle;
4. send event 1/profile-tail to enter currentboot;
5. trigger with `CDB[7:9] = fc e1 00`.

Currentboot trigger result:

```text
response[0x20] = d3
```

Returned `xdata[0x4a00..0x4a3f]`:

```text
4a00: 01 03 00 03 00 14 07 00 00 00 00 00 00 20 00 13
4a10: 00 00 00 00 01 ea 00 00 01 00 00 00 00 00 00 00
4a20: 03 08 10 00 03 fe 00 00 00 00 00 01 00 0f 00 00
4a30: 00 07 0f 00 00 00 00 00 00 00 00 00 00 00 00 00
```

Gateway reads before and after the trigger stayed all zero at:

```text
0x184000
0x184060
0x190690
```

Evidence:

```text
references/evidence/live/drive3-cdd-parser-call-20260504/
```

## Second-Doorbell Trigger

Installed candidate:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-bulk-cdd-parser-second-doorbell-v1/
```

This repeats parser setup, mirrors `0x4a24/25` into `0x4a28/29`, rings
`0x4a00`, calls `0x1667`, and returns marker `0xd4`.

Currentboot trigger result:

```text
response[0x20] = d4
```

Gateway reads before and after the trigger stayed all zero at:

```text
0x184000
0x184060
0x190690
```

Evidence:

```text
references/evidence/live/drive3-cdd-parser-second-doorbell-20260504/
```

## Interpretation

Drive #3 reproduces the earlier CDD parser/mailbox findings on clean hardware:

- the currentboot response hook can call the resident CDD parser setup;
- the visible 8051 side populates the expected `0x4a` mailbox package;
- the second-doorbell sequence executes without wedging;
- neither path materializes the decoded CDD target range in currentboot.

This strengthens the prior conclusion: currentboot is good for observing the
visible parser/mailbox mechanics, but the decoded CDD/runtime material probably
requires normal runtime controller state or a deeper controller transition than
`0x002e` plus the `0x4a` doorbells.
