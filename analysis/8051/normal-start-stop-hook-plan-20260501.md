# Normal START STOP Hook Plan

Date: 2026-05-01

This note is the follow-up to the live START STOP variant matrix. It is not a
new drive probe. The goal is to turn the confirmed eject/mechanics trigger into
a practical next hook plan without assuming that the visible F0 prefix is the
normal command handler.

## What The Eject Test Proved

The static work-window branch:

```text
0x8bxx:
90 8a 49 e0 64 1b 70 27      ; CDB[0] == 0x1b, START STOP UNIT
90 8a 4d e0 54 0f ff bf 02   ; (CDB[4] & 0x0f) == 0x02
```

is tied to real mechanism behavior. Sending `1B 00 00 00 02 00` made the sled
do the eject dance. The three other low-nibble variants were boring:

- `0x00` stop: quick CHECK / Not Ready, no public-window timeout;
- `0x01` start: quick CHECK / Not Ready, no public-window timeout;
- `0x03` load: quick CHECK / Illegal Request, no public-window timeout.

Only `0x02` produced visible movement and a multi-second DID_TIME_OUT. That is
strong evidence that the branch is specifically the eject-style START STOP
case, not generic packet handling noise.

## What The Eject Test Also Warned Us About

The public `READ BUFFER id=01 offset=0x070000` work-window path is not a good
immediate reply channel during the eject transition. In repeated runs, the
first one or two post-command work-window reads timed out while the mechanism
was busy, then later reads recovered and the drive stayed normal `LD5M`.

So a useful hook should not depend on "send START STOP eject, immediately ask
for the answer." A better shape is:

1. trigger a known command path;
2. store a few bytes of state somewhere stable;
3. return normally or suppress/shorten the mechanism path;
4. read the stored bytes later through a boring command path.

That is especially important if we use this route for telemetry around
`0x480e`, `0x4860`, `0x4864`, `0x5905`, or `0x5a01`.

## Patchability Is The Main Open Question

The work-window bytes are live normal-runtime/overlay material, but they are
mostly not exact bytes from the visible F0 prefix. The earlier persistent F0
resident-hook attempts proved this the hard way: hooks at visible F0
`0x4ec6`/`0x5c72` wrote and verified in flash, but normal INQUIRY and REQUEST
SENSE timing stayed stock after cold boot.

There is another small alignment warning in the START STOP snippet itself. The
work-window path calls `LCALL 0x0f8d`; in the visible 8051 prefix, the nearby
bytes disassemble as:

```text
0x0f8a  7f 04        MOV R7,#0x04
0x0f8c  12 57 f4     LCALL 0x57f4
0x0f8f  22           RET
0x0f90  90 81 8e     MOV DPTR,#0x818e
```

That does not look like a clean call target in the visible prefix. It is
consistent with the broader model: the public work-window exposes a normal
runtime overlay or controller-loaded image, while the persisted F0 prefix is
not necessarily the code being executed for ordinary commands.

## Practical Hook Shapes

### 1. First Hook: Branch-Local Telemetry, No Movement Change

If we find a patchable copy of the `+0x8bxx` branch, the first payload should be
small and non-commanding:

```text
if CDB[0] == 0x1b and (CDB[4] & 0x0f) == 0x02:
    copy a tiny state set into scratch XDATA
    run original code
```

Candidate bytes:

```text
0x8a49  CDB opcode shadow
0x8a4d  CDB byte 4 / START STOP control
0x8a2d  nearby state gate used in the branch
0x8a34  branch-local flag byte
0x480e  low-two-bit mechanics state gate
0x48a5  bit4 cleared in mechanics path
0x4762  bit4 cleared in mechanics path
0x4860  controller-facing state/enable cluster
0x4864  paired state/ack cluster
0x5905  servo/mechanics family
0x5a01  servo/mechanics family
```

The readback should happen later through a known stable response path, not
during the busy eject window.

### 2. Safer Second Hook: Eject-Path Suppression

Once the branch is confirmed patchable, the next hook can short-circuit after
capturing state:

```text
if CDB[0] == 0x1b and (CDB[4] & 0x0f) == 0x02:
    capture state
    return CHECK/GOOD through an existing nearby error path
else:
    original code
```

The point is not to defeat eject permanently. The point is to make START STOP
usable as a repeatable host trigger without moving the sled every run.

This should wait until the return path is understood. Returning from the wrong
place can leave the packet engine busy, which is worse than just letting eject
finish.

### 3. Host-Visible Readback Hook

The currentboot response-hook builder already knows how to write bytes into a
SCSI response buffer and can bulk-copy XDATA or gateway bytes using CDB-supplied
addresses. That code is useful as a payload library, but the hook site is
currentboot-specific. For normal runtime we still need a live patchable response
path.

Good normal candidates are boring status/read commands that do not move the
mechanism:

- REQUEST SENSE;
- GET CONFIGURATION current;
- a no-disc READ TOC failure path, if it can be made deterministic;
- the GET PERFORMANCE type03 path, which returned normally in the correlation
  runs.

Do not reuse the currentboot hook addresses blindly in normal mode. The
persistent F0 negative says those visible addresses are not enough.

## Recommended Next Work

The next work should be static/localization first, not another mechanical poke:

1. localize the `+0x8bxx` and `+0x92xx` work-window chunks to a source image or
   runtime overlay, if possible;
2. find a normal command response path that is both live and patchable;
3. adapt the currentboot response payload routines to that normal hook site;
4. only then use START STOP eject as a telemetry trigger again.

If the normal overlay source turns out to be decoded CDD/controller material,
the persistent-F0 route is probably the wrong patching surface. In that case
the better path is a currentboot/helper-installed RAM patch or a hardware
front-panel channel, not more visible-prefix hooks.

## Current Decision

For now:

- treat START STOP `0x02` as a confirmed trigger;
- treat immediate post-eject `READ BUFFER` as unreliable because the drive is
  legitimately busy;
- do not blindly write the `0x4860/0x4864/0x5905/0x5a01` registers;
- do not spend another run on a visible-F0 standard-command hook without first
  proving that the target bytes are executed in normal mode.

The narrowest good next success is a non-mechanical normal-mode oracle: a small
patchable response hook that returns XDATA bytes after the drive is fully
booted. Once that exists, START STOP, LED/button state, and decoded-controller
windows all become much cheaper to map.
