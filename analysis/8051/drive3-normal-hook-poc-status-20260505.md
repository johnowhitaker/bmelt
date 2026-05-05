# Drive 3 Normal-Mode Hook PoC Status

Date: 2026-05-05

This note records the next step after the pressed-DVD auth work. The goal was
to keep moving toward a normal-mode proof-of-control hook without touching CDD
source bytes or flash unless the hook delivery path was justified.

## Current Result

No custom normal-mode hook was installed in this pass. The blocker is still
delivery, not hook-site imagination:

- we have normal command paths that exchange data with the drive;
- we have plausible normal-runtime code islands and branch bodies;
- we do not yet have a safe way to patch those normal-runtime CDD/body bytes.

So the safe end state for this pass is a sharper hook target map plus one more
negative on an existing, non-flash selector idea.

## REPORT KEY Format-8 Branch Body

The `REPORT KEY` / `SEND KEY` selector island found earlier is still the best
normal command island:

```asm
mov  dptr,#0x8a49
movx a,@dptr
cjne a,#0xa4,not_report_key
mov  dptr,#0x8a53
movx a,@dptr
anl  a,#0x3f
mov  r7,a
cjne r7,#0x08,not_report_key
ljmp 0x6f62
```

The caution from the earlier note still applies: public work-window offsets are
tiles, not a flat code map. But `0x6f62` is now a stronger candidate than it was
then, for three reasons:

- the selector has a literal `LJMP 0x6f62`;
- the currentboot gateway direct-reference scan independently sees `MOV
  DPTR,#0x4782` starting at gateway offset `0x6f62`;
- normal/DVD-auth windows repeatedly expose plausible 8051 code around this
  family of offsets, including writes to `0x4867`, `0x486a`, and `0x486b`.

The useful branch-body signature is:

```text
90 48 67 e0 44 14 f0
```

which is:

```asm
mov  dptr,#0x4867
movx a,@dptr
orl  a,#0x14
movx @dptr,a
```

This appears in live normal/currentboot windows and also in sibling PLDS
plaintext-style images such as `YL32.bin` and `YA12.bin` at approximately
`0x1838f5`. That sibling code is a hardware/status setup routine around
`0x4860..0x486b`, `0x5904..0x5a01`, and related mechanics/status registers.

Practical interpretation: the safe `REPORT KEY format 8` branch is probably a
status/config updater, not a response generator. It is useful because it is a
host-reachable normal branch, but it is not by itself the one-byte response
hook we want.

## Read-Only RPC-State Capture

Run:

```text
references/evidence/live/normal-mailbox-dvd-auth-20260505T040403172305Z/
```

This was a read-only `dvd-auth` pass with `--capture-step-windows` and a 64 KiB
public window. It left Drive #3 in normal `LD5M`.

Key observations:

- `REPORT KEY` AGID, ASF, RPC state, and AGID invalidation all completed.
- The `0x4867 |= 0x14` branch-body signature appeared after AGID/ASF in that
  run and disappeared after the later phase windows.
- The shared controller write-side helper stayed stable at
  `+0xdbc0..+0xdc7f`.
- The direct RPC-state response remained the ordinary stable bytes:
  `0006000064fe0100`.

This is useful as a branch/body correlation run, but it is still work-window
evidence rather than a host-visible hook.

## MODE SELECT Bit As A Selector

The one proven normal writable bit is still:

```text
MODE SENSE/SELECT(10) page 0x08
page byte 0x02
mask 0x04
observed: 0x04 -> 0x00 -> 0x04
```

I tested whether that bit can act as a selector for the safe
`REPORT KEY format 8` path:

```text
references/evidence/live/normal-mode-bit-rpc-observer-20260505T040730344882Z/
```

Sequence:

1. read current/changeable MODE page `0x08`;
2. read `REPORT KEY format 8`;
3. capture a public work-window;
4. flip the volatile bit with `MODE SELECT(10) PF=1 SP=0`;
5. read `REPORT KEY format 8`;
6. capture another public work-window;
7. restore the bit;
8. read `REPORT KEY format 8`;
9. capture a final work-window.

Result:

```text
MODE bit roundtrip:       yes
identity stable:          yes
RPC response before:      0006000064fe0100
RPC response mutated:     0006000064fe0100
RPC response restored:    0006000064fe0100
```

The public work-window hashes changed, and the branch-body tile showed up at
different offsets in different phases. That is normal for this surface and is
not a controlled response bit. The direct host-visible response did not change.

`scripts/probe_liteon_mode_bit_observer.py` now captures this experiment in a
repeatable form.

## Hook Design Still Standing

The best custom hook design is still the conservative `READ BUFFER` response
redirect from `analysis/8051/normal-mode-read-buffer-hook-plan-20260504.md`:

```text
if READ BUFFER id=01 offset=0x070bad:
    substitute response offset 0x07dbc0
else:
    run stock response bridge
```

That design is attractive because it changes existing response-bridge
arguments (`0x4011..0x4013`) rather than inventing a new response path.

The missing piece is how to install it:

- currentboot volatile gateway writes do not carry into normal mode through
  `sg_reset`, USB reauth, or stock recovery;
- visible F0-prefix hooks have not affected normal-mode command handling;
- patching the normal response bridge or `REPORT KEY` branch body likely means
  patching CDD-derived normal runtime code, which is a riskier step and needs a
  chosen source-byte strategy or explicit approval.

## Practical Next Step

Do not count public-window phase shifts as a hook. The next real advance needs
one of these:

1. a safe delivery path into normal CDD-derived runtime code;
2. a standard normal command whose direct response is influenced by a
   host-writable state byte;
3. an explicitly approved, tightly scoped CDD/runtime byte mutation with a
   restore candidate ready.

Until one of those exists, the project has a good hook plan and good normal
command islands, but not a normal-mode custom hook in place.
