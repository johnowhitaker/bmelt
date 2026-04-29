# Linux Drive 1 Helper Timing Code-Execution PoC

Date: 2026-04-29

Host: `jonathan-thinkpad-t480s`

Drive: Linux drive #1, `PLDS DVD+-RW DS-8ABSH`, recovered to `LD5M` after each run.

## Summary

We have a host-visible proof that patched helper-overlay code executes at the
bank pMac/control boundary.

The successful proof does not use EXTRAINQ, persistent resident-code hooks, or
GPIO. It patches the mutable `ef130045` profile-tail helper so that the already
proven late status branch at code `0x32af` jumps to a small payload placed over
the `Flash Type Error` string at code `0x361a`. The payload runs a finite 8051
delay loop, then returns to the normal helper success path at `0x32c4`.

The host observes the payload through SCSI command latency. With the same
short replay ending at event `68`, the unmodified helper takes about `0.256s`
for the bank-1 pMac/control boundary. The patched delay loops increase only
that event, while the earlier event `34` pMac and event `35` profile-tail load
remain flat.

## Payloads

Common hook:

```text
helper plain 0x02b5 / code 0x32af:
30 e6 12 -> 02 36 1a
```

Delay `0x20` payload at helper plain `0x0620` / code `0x361a`:

```text
7f 20 7e ff 7d ff dd fe de fa df f6 02 32 c4
```

Delay `0x80` payload:

```text
7f 80 7e ff 7d ff dd fe de fa df f6 02 32 c4
```

The loop is intentionally simple:

```text
mov r7,#N
outer:
  mov r6,#0xff
middle:
  mov r5,#0xff
inner:
  djnz r5,inner
  djnz r6,middle
  djnz r7,outer
ljmp 0x32c4
```

## Timing Results

All three runs used `--end-index 68`, then auto-recovered from the partial
currentboot state back to `LD5M`.

| run | event 34 pMac | event 35 profile-tail | event 68 pMac | post-recovery revision |
|---|---:|---:|---:|---|
| canonical baseline | `0.367726s` | `0.045753s` | `0.255830s` | `LD5M` |
| delay `0x20` | `0.365976s` | `0.045785s` | `0.849545s` | `LD5M` |
| delay `0x80` | `0.369848s` | `0.045820s` | `2.638886s` | `LD5M` |

The scaling is the important point. Event `68` changes with the immediate byte
we put in the helper payload. Adjacent control points do not.

## Evidence Paths

Candidates:

```text
references/firmware/extracted/liteon-full-currentboot-ld5m-base-mutated-all-helper-final-branch-delay-poc-candidate.json
references/firmware/extracted/liteon-profile-tail-helper-final-branch-delay-poc-candidate.md
references/firmware/extracted/liteon-full-currentboot-ld5m-base-mutated-all-helper-final-branch-delay80-poc-candidate.json
references/firmware/extracted/liteon-profile-tail-helper-final-branch-delay80-poc-candidate.md
```

Live results:

```text
references/evidence/live/linux-drive1-codeexec-poc-attempts/baseline-through-event68/persistence-experiment-result.json
references/evidence/live/linux-drive1-codeexec-poc-attempts/final-branch-delay-poc/persistence-experiment-result.json
references/evidence/live/linux-drive1-codeexec-poc-attempts/final-branch-delay80-poc/persistence-experiment-result.json
```

Runner change:

```text
scripts/run_liteon_linux_persistence_experiment.py
```

`run_sg_raw()` now records `elapsed_seconds` for each command.

## Negative Side Result

Before the timing proof, a self-write payload tried:

```text
mov dptr,#0x361a
mov a,#0x58
movx @dptr,a
ljmp 0x32c4
```

The helper-window bytes at public `READ BUFFER 01:018620` did not change after
event `68`; they remained the staged helper payload bytes. That suggests the
public `01:018000` helper window is a controller-exposed copy of the loaded
profile-tail record, not a live alias for `MOVX` writes to the helper code/data
space.

Evidence:

```text
references/evidence/live/linux-drive1-codeexec-poc-attempts/final-branch-selfwrite-poc/persistence-experiment-result.json
```

## Interpretation

This is a real execution foothold in the mutable helper overlay. It proves:

- currentboot profile-tail helper body bytes are not merely visible as data;
- code patched into the helper body can run at a known late helper path;
- the host can receive at least a timing-channel signal from that code;
- the late `0x32af -> payload -> 0x32c4` hook is much safer than the earlier
  helper-entry trampoline, which wedged at event `68`;
- partial runs through event `68` leave the drive in `0D5C`, but the known
  Linux recovery replay restores `LD5M` without physical replug for this class.

It does not yet prove a general data-return channel, nor does it prove that
normal persistent F0 resident-code hooks are live after boot. It is the first
clean host-visible arbitrary helper-code execution proof.

## Good Next Steps

1. Build a more useful helper-side host channel than timing, preferably by
   reusing an existing helper/status routine instead of touching raw controller
   registers early.
2. Try a controlled status-byte payload at the same late hook point, not at
   helper entry.
3. If host-visible status remains opaque, move to the Pico front-panel path:
   use this same late hook to toggle a known-safe LED/front-panel line once the
   GPIO register is mapped.
4. Keep event-68 short runs as the code-exec test harness because they are fast
   and recover cleanly.
