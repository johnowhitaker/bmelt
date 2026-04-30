# Linux Drive 1 Pre-Tail Event-1 Codeexec Probe

Date: 2026-04-30

Goal: test whether the known late helper hook at helper plaintext `0x02b5`
/ code `0x32af` can run from the normal/pre-tail profile-tail payload at event
`1`, before the drive enters the currentboot update sequence.

This was the first attempt at a post-recovery-oracle route that might expose
normal-runtime/controller memory without waiting for event `68`.

## Tooling

`scripts/build_liteon_helper_codeexec_candidate.py` now accepts:

```sh
--tail-scope currentboot  # old behavior: mutate all currentboot-key tails
--tail-scope pretail      # mutate only event-1 normal/pre-tail helper payload
```

`scripts/read_liteon_xdata_timing_channel.py` forwards that scope and switches
its target event from `68` to `1` when using `--tail-scope pretail`.

## Live Results

Calibration candidates were built with constant predicates, then run through
event `1` only:

```text
immediate constant 0, event 1: GOOD, ~0.199447s
immediate constant 1, event 1: GOOD, ~0.198619s
```

There was no timing split. A direct force-error payload also returned GOOD at
event `1`.

Interpretation: event `1` accepts mutated pre-tail payload bytes and still
transitions the drive into currentboot, but the known late helper branch at
`0x32af` is not reached in that event. The event-68 hook remains real; it is
just too late for the pre-tail-normal-runtime shortcut.

## Drive State

The event-1 experiments left the drive in `0D5C` currentboot until the known
Linux recovery sequence was run manually. Recovery completed and active
INQUIRY returned to `LD5M`.

## Consequence

This specific option-1 route is a negative. A different pre-tail hook point may
exist, but the more promising next route is a resident LD5M command hook that
can be triggered after normal boot.
