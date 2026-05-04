# Drive 3 Normal Response Matrix

This pass stayed read-only in normal `LD5M` mode. The goal was to see whether
standard host commands already give us a slow normal-mode I/O primitive: either
a response byte, a sense byte, or a public work-window tile position that
changes predictably with host-controlled command fields.

## Tools Added

Two small helpers were added:

```text
scripts/capture_liteon_normal_response_matrix.py
scripts/analyze_liteon_normal_response_matrix_correlations.py
```

The capture script sends standard no-data-out/read/status commands, saves the
direct response, runs REQUEST SENSE after failures, and snapshots the public
normal work-window at `READ BUFFER mode=1 id=01 offset=0x070000`.

The correlation script scans the resulting work-window captures for simple
single-byte equality correlations with CDB fields. This was a check for a
one-byte packet-shadow leak rather than a full CDB-string echo.

## Evidence Captured

```text
references/evidence/live/drive3-normal-response-matrix-core-20260504/
references/evidence/live/drive3-normal-response-matrix-core-repeat-20260504/
references/evidence/live/drive3-normal-response-matrix-core-shuffled-20260504/
references/evidence/live/drive3-normal-response-matrix-modesense-cddevice-ab-20260504/
references/evidence/live/drive3-normal-response-matrix-disc-status-20260504/
```

Offline reduction:

```text
analysis/8051/drive3-normal-response-matrix-correlations-20260504.md
analysis/8051/drive3-normal-response-matrix-correlations-20260504.json
```

Drive #3 remained visible as normal `PLDS DVD+-RW DS-8ABSH LD5M` after every
run.

## What Worked

The direct host responses are very stable. Across repeated and shuffled core
passes, each command returned the same response payload hash every time. That is
good as a baseline: the host side is not randomly corrupting or changing
responses while we probe.

The normal work-window also continues to expose the XD13-derived snippets:

```text
rec58 bridge/control snippet
rec58b controller-register snippet
rec60 GET-CONFIG-adjacent bridge snippet
```

Those are still useful normal-mode watchpoints for later experiments.

## What Did Not Work

No command in the core matrix produced a reliable host-controlled response bit.
The GET CONFIG, MODE SENSE, GET EVENT, INQUIRY/EXTRAINQ, and REQUEST SENSE
responses are stable, but that stability is just the normal SCSI response
surface. It does not expose drive-internal state.

The public work-window is still phasey. In the sorted repeat pass, some commands
looked weakly associated with record58 offsets. After shuffling command order,
those associations mostly collapsed into normal phase drift. A specific weak
lead, `MODE SENSE cd-device`, was tested in a randomized A/B run against
`TEST UNIT READY` and standard INQUIRY. It split the same way as the controls:

```text
rec58-bridge-long:
  baseline-test-unit-ready   +0x7050 x6, +0x7010 x6
  inquiry-standard-36        +0x7010 x7, +0x7050 x5
  modesense-cd-device        +0x7010 x7, +0x7050 x5
```

So that was not a command-controlled bit.

The single-byte correlation scan also did not find a convincing CDB-shadow leak.
The few positive-looking rows are either sequence artifacts, common constants
such as `0x00`/`0xfc`, or weak one-count lifts that do not survive as plausible
I/O candidates.

The disc/status pass was read-only and safe. With no medium present, most disc
commands returned CHECK CONDITION / Not Ready / medium not present in `sg_raw`
stderr; a follow-up REQUEST SENSE reported no sense because the condition had
already been consumed by `sg_raw`'s autosense path. That pass did not reveal a
new work-window or response hook.

## Current Interpretation

This route probably cannot give us a normal-mode I/O primitive by itself. The
standard responses are too well behaved, and the public work-window is a tiled
runtime/code surface rather than a simple RAM window containing the latest CDB.

The useful result is a narrower negative:

- XD13-derived work-window snippets are good observation points.
- Ordinary read/status command fields do not visibly echo into the public
  window as bytes or short strings.
- Work-window tile placement is not reliable enough to use as a side channel
  without a stronger synchronizer or a real code hook.

## Next Better Moves

1. Use static XD13/LD5M homologs to rank CDD records that are closer to actual
   response construction, not just packet parsing. If we choose another live
   mutation, it should be targeted there and explicitly approved.
2. Look for a normal-mode hook path that modifies an existing response payload
   directly. The stock responses are stable enough that even a one-byte response
   hook would be obvious.
3. Revisit hardware I/O only when the front-panel LED/button wiring is
   available again. The public SCSI work-window is not currently a good enough
   timing or phase channel.
4. Keep CDD decode work focused on response/bridge islands. Full CDD decode is
   still valuable, but the near-term goal is a host-visible normal-mode foothold.
