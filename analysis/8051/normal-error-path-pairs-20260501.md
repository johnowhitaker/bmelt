# Normal Error-Path Pair Capture

Host: `jonathan-thinkpad-t480s`
Drive: `PLDS DVD+-RW DS-8ABSH LD5M`
Evidence:
`references/evidence/live/normal-work-window-error-path-pairs-20260501`

This run followed the read/status correlation pass with paired captures:

1. send one expected-failing read/status command;
2. capture the normal `READ BUFFER id=01 offset=0x070000` work window;
3. send `REQUEST SENSE`;
4. capture the work window again.

The commands were `READ TOC` formats `0` and `4`, plus
`GET PERFORMANCE type00`. The failures and follow-up sense reads repeated for
three cycles. The drive stayed in normal `LD5M`.

## Result

The pair run did not cleanly split "after failed command" from "after request
sense" into two separate stable snippets. Several recurring stimulus-only
chunks appeared in both phases:

```text
+0x9c00/+0x9c80  refs 0x4000, 0x4098
+0x6f80          refs 0x8a23
+0x9a00/+0x9ac0  refs 0x8a23
```

The older `+0x7140/+0x7180` `0x4098` gateway-looking chunk still appeared, but
only twice and only after `READ TOC format0`. The `+0x8bxx` selector/count
chunk remains visible in the selector-map pass for this run, but it was not as
cleanly stimulus-only as in the broader read/status correlation run.

The `+0x8bxx` chunk is still important statically even when it is not a clean
pair-run discriminator. It checks `0x8a49 == 0x1b` and then checks
`(0x8a4d & 0x0f) == 0x02`, which matches the START STOP UNIT eject/control
field in CDB byte 4. This is the best byte-map anchor so far for the packet
shadow.

## Interpretation

This suggests the no-disc failure path and the follow-up sense path share more
runtime machinery than expected, or that the public work window is rotating
through a longer error/status handler whose phase does not line up tightly with
the host command boundary.

The pair run is still useful as a constraint:

- `REQUEST SENSE` after a failure does not reveal a totally different simple
  fast-oracle surface.
- The error/status surface repeatedly touches `0x4098` as well as the
  `0x8a23` state flag.
- The cleaner `0x8a49/0x8a4d` observation is still the previous read/status
  correlation run, where failed `READ TOC` and `GET PERFORMANCE type00`
  commands were compared against local baselines without immediately draining
  sense after every command.

For the next pass, prefer either a longer one-command-only capture, or a direct
normal-runtime hook around the `0x8bxx`/`0x9cxx` snippets, rather than more
paired host-command snapshots.
