# Drive 3 Normal Hook Carryover Evidence

Date: 2026-05-04

Purpose: test whether a harmless currentboot gateway marker can survive into
normal `LD5M` mode before attempting any shared-code normal hook.

Summary:

- Stock `READ BUFFER id=01/02` baselines for `0x070bad` and `0x07dbc0` were
  captured before any currentboot entry.
- `gateway-cdb-rw-v2` installed successfully and returned to `LD5M`.
- Event 1 entered the hooked currentboot context.
- Currentboot gateway write changed controller/public `0x074030` from `ff` to
  `5a` and read it back.
- `sg_reset` and USB deauth/reauth both stayed in currentboot identity.
- Stock currentboot recovery returned to `LD5M`.
- After recovery, the marker was gone and the `0x070bad` / `0x07dbc0` hashes
  matched stock.

Conclusion: currentboot volatile carryover is not a viable delivery path for
the planned shared-code normal READ BUFFER hook.

See:

```text
analysis/8051/drive3-normal-hook-carryover-20260504.md
```
