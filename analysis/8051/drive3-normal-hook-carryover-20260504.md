# Drive 3 Normal Hook Carryover Test

Date: 2026-05-04

This is the live result for the inert carryover gate in
`analysis/8051/normal-mode-read-buffer-hook-plan-20260504.md`.

## Question

Can a currentboot gateway write to a shared-looking controller/public page
survive a transition back into normal `LD5M` mode?

This was the safety gate before attempting any normal shared-code hook. If a
harmless marker byte could not carry over, then a behavior-changing shared-code
patch would not be justified through this route.

## Evidence

Live evidence is under:

```text
references/evidence/live/drive3-normal-hook-carryover-20260504T203335Z/
```

## Baseline

Drive #3 started as normal `LD5M`:

```text
Product revision level: LD5M
```

The planned magic/redirect windows were captured before any currentboot entry:

```text
READ BUFFER id=01 offset=0x070bad sha256=38723a2e5e8a17aa7950dc008209944e898f69a7bd10a23c839d341e935fd5ca
READ BUFFER id=01 offset=0x07dbc0 sha256=deba3a77d7dd53153ad4b4e54af7b4dfcdc2d4965855b42031f3d7385f1c6e98
READ BUFFER id=02 offset=0x070bad sha256=38723a2e5e8a17aa7950dc008209944e898f69a7bd10a23c839d341e935fd5ca
READ BUFFER id=02 offset=0x07dbc0 sha256=deba3a77d7dd53153ad4b4e54af7b4dfcdc2d4965855b42031f3d7385f1c6e98
```

This confirmed that a future `0x070bad -> 0x07dbc0` redirect would be directly
observable in the host response.

## Setup

The already-proven `gateway-cdb-rw-v2` currentboot response hook was installed
with the helper-bypass write sequence:

```text
success=true
final_revision_after_sequence=LD5M
```

After a Pico servo power cycle, event 1 entered the hooked currentboot state:

```text
final_revision_after_sequence=;D5C
```

That is expected for the hooked currentboot response-handler context.

## Marker Write

The inert marker target was a padding byte in the shared-looking string area:

```text
controller/public address: 0x074030
before: ff
write:  5a
after:  5a
```

The surrounding readback before the transition was:

```text
3f 4c 07 bc 06 20 06 9a 13 16 27 29 0e 5a 18 81
5a ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
50 4c 44 53 20 43 4f 52 50 4f 52 41 54 49 4f 4e
```

So the currentboot gateway write primitive worked exactly as intended.

## Soft Exit Attempts

Two soft transitions were tried:

```text
sg_reset --device /dev/sg0
USB deauthorize/reauthorize of the bridge device
```

Both left the optical LUN in currentboot identity:

```text
Product revision level: ;D5C
```

So these are not usable currentboot-to-normal exits on this bench setup.

## Recovery Result

Stock currentboot recovery was then run:

```text
success=1
final_revision=LD5M
```

After recovery, the drive was back to normal `LD5M`, but the marker byte was
gone:

```text
00000000: 3f 4c 07 bc 06 20 06 9a 13 16 27 29 0e 5a 18 81
00000010: ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
00000020: 50 4c 44 53 20 43 4f 52 50 4f 52 41 54 49 4f 4e
00000030: ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff ff
```

The post-recovery `0x070bad` and `0x07dbc0` hashes matched stock:

```text
0x070bad sha256=38723a2e5e8a17aa7950dc008209944e898f69a7bd10a23c839d341e935fd5ca
0x07dbc0 sha256=deba3a77d7dd53153ad4b4e54af7b4dfcdc2d4965855b42031f3d7385f1c6e98
```

## Conclusion

The currentboot gateway write can edit the marker while currentboot is active,
but the available transitions do not carry that edit into normal mode:

- `sg_reset` stays in currentboot.
- USB bridge reauthorization stays in currentboot.
- stock recovery returns to `LD5M` but reloads/wipes the marker.

Therefore the planned shared-code normal hook was not attempted. The
`0x070bad -> 0x07dbc0` hook remains a sensible hook design if we later find a
real normal-mode delivery primitive, but the currentboot volatile carryover
route is closed for now.

## Practical Next Step

Resume with normal-mode mailbox/write surfaces rather than currentboot
carryover:

- standard echo-buffer `WRITE BUFFER 0x0a` / `READ BUFFER 0x0a`;
- volatile `MODE SELECT` page changes already proven for page `0x08`;
- `SEND KEY` / `REPORT KEY` DVD-auth nonce paths;
- media-backed read/write buffers if we decide to involve sacrificial media.

The stop condition did its job: no shared normal code was patched through an
unproven transition.
