# Normal-Mode Code Execution / CDD Oracle Status - 2026-05-06

This is a status/audit note, not a live experiment. No drive commands are
implied by this document.

## Objective

Push toward:

1. normal-mode code execution, meaning a stock LD5M boot reaches code we
   changed or code/state we can alter after the normal CDD materializer runs;
2. a proper CDD materialization oracle, meaning a host-visible path to read
   decoded/materialized CDD/controller runtime bytes without needing to solve
   the on-flash CDD encoding first.

## Current Best Route

The best current route is the post-materializer bridge-clamp ladder:

```text
resident 8051 prefix hook at 0x422c
    -> after 0x40b2/materializer return, write controller/public bytes
    -> patch materialized normal READ BUFFER bridge clamp in RAM
    -> observe changed host READ BUFFER responses
```

This route deliberately avoids mutating CDD source bytes. It uses the visible
resident prefix as a small post-materializer writer into decoded/runtime RAM.

## Why This Is Plausible

The normal READ BUFFER bridge contains a recurring clamp sequence:

```text
90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 0e f0
```

The important byte is the `MOV A,#0x0e` immediate before writing controller
register `0x4011`. It caps high public READ BUFFER offsets.

Two planned patch values:

- `0x07`: proof patch. If high-offset reads fold differently and restore, we
  have evidence that a resident hook patched materialized normal runtime code.
- `0x18`: oracle patch. If `0x07` works, `0x18` may let READ BUFFER request
  decoded/controller addresses around `0x184000`.

## Prepared Toolchain

### Watcher / Gate

```sh
python3 scripts/watch_liteon_plds_preflight.py \
  --interval-s 10 \
  --execute-preflight \
  --pico-port /dev/ttyACM0
```

The watcher scans `/dev/sg[0-9]+` for `sg_inq` output containing
`PLDS DS-8ABSH`. When a PLDS LUN appears, it prints the exact guarded ladder
command for that device and Pico port. It does not run the write ladder itself.

### Guarded Ladder

When the drive is visible as PLDS:

```sh
python3 scripts/run_liteon_bridge_oracle_ladder.py \
  --device /dev/sg0 \
  --pico-port /dev/ttyACM0 \
  --execute
```

The ladder:

1. runs dynamic `0x07` first;
2. analyzes that high offset `0x0f0000` changed and restored;
3. refuses `0x18` unless the `0x07` proof passes, unless explicitly forced;
4. runs dynamic `0x18` with decoded-oracle offsets only after that proof.

The lower-level live wrapper also refuses a direct fixed-candidate install
under `--execute` unless `--allow-fixed-candidate` is passed deliberately.
This keeps the normal path on baseline-derived dynamic candidates, where the
run patches only clamp slots actually visible in that run.

The dynamic baseline-derived path now defaults to six writes
(`--dynamic-max-writes 6`). An offline scan of saved normal work-window
captures found eight rotating bridge-clamp copies total, but the six common
slots are the historical fixed-builder set:

```text
0x077156, 0x077196, 0x0770e6, 0x077026, 0x0770a6, 0x077066
```

The two rare slots, `0x077116` and `0x0771d6`, remain useful diagnostics. A
run-local dynamic candidate can still target them if they are the slots visible
in that baseline. See
`analysis/8051/materialized-bridge-clamp-slots-20260506.md`.

### Candidate Verification

Before a live install, the live wrapper now runs:

```sh
python3 scripts/verify_liteon_bridge_clamp_candidate.py ...
```

The verifier checks fixed and dynamic candidates:

- resident hook changed only at `0x422c`;
- cave bytes are parsed gateway-write blocks ending in `CLR A; MOV PSW,A; RET`;
- dynamic candidates preserve DPTR around those gateway writes, so the hook
  returns with stock `A=0`/`PSW=0` while avoiding an extra DPTR side effect;
- dynamic candidate writes exactly the selected baseline-visible clamp
  addresses;
- patch value is the intended `0x07` or `0x18`;
- restore image is byte-identical to the LD5M base;
- helper low-sector erase/program patches are present.

### Analyzer

```sh
python3 scripts/analyze_liteon_materialized_bridge_clamp_live_test.py <run-dir>
```

It distinguishes:

- stock clamp pattern value `0x0e`;
- proof patch value `0x07`;
- oracle patch value `0x18`;
- high-offset response changes and restore;
- decoded-band offset changes and restore.
- READ BUFFER command failures, timeouts, short/no-byte responses, and stderr
  snippets from the probe JSON summaries.

### Second-Stage Blob Writer

```sh
python3 scripts/build_liteon_post_materializer_blob_writer_candidate.py \
  --address 0x077156 \
  --hex "74 07 f0" \
  --name post-materializer-blob-smoke-077156-3b \
  --dry-run
```

This is not part of the first live proof. It exists for the next phase if the
`0x07` bridge-clamp ladder proves that the `0x422c` post-materializer hook can
write materialized normal runtime RAM and restore cleanly.

The builder emits a cave routine at `0x6ee3` that:

- saves DPTR and bank-0 `R0/R1/R7`;
- sets a 24-bit controller/public destination through `0x4095..0x4097`;
- streams an embedded code-table through `0x4098`;
- restores the saved state and returns with the stock `CLR A; MOV PSW,A; RET`
  epilogue shape.

A dry-run smoke build for a three-byte blob at `0x077156` produced an 87-byte
cave payload, leaving room for roughly 137 bytes of contiguous patch data. The
remaining unproven assumption is write-side FIFO auto-increment across
successive `0x4098` writes, so this is second-stage tooling, not something to
run before the smaller bridge-clamp proof succeeds.

### Second-Stage Multi-Blob Writer

```sh
python3 scripts/build_liteon_post_materializer_multi_blob_writer_candidate.py \
  --runtime-patch 0x077cd6:e4f5d022 \
  --runtime-patch 0x078406:122cd6 \
  --name post-materializer-multi-blob-smoke-selector22-ret \
  --dry-run
```

This exists for the first real normal-runtime response hook after the bridge
proof. A response hook normally needs at least two writes in the same boot:

- a small hook body in a materialized runtime cave;
- an entry-point trampoline or conditional branch to that hook body.

The dry-run above targets the selector-22 runtime image only as a toolchain
smoke test:

- cave body at public/controller `0x077cd6`, logical `0x2cd6`;
- trampoline at public/controller `0x078406`, logical `0x1406`;
- generated cave payload/table length: 141 bytes, leaving 80 bytes.

See `analysis/8051/selector22-runtime-response-hook-targets-20260506.md` for
why those addresses are interesting and for the important caveat: selector22 is
not byte-identical to the normal public bridge-clamp page. The normal
bridge-clamp ladder should still use baseline-derived normal work-window slots,
not selector22 logical addresses. This multi-blob selector22 target is not a
first live step and should not be run before the smaller `0x07` clamp proof
succeeds and restores.

## Offline Smoke Test

The bridge-clamp ladder is still blocked on live PLDS visibility, but the
offline pieces were sanity-tested with synthetic `/tmp` captures on
2026-05-06:

1. a fake baseline `0x077000` capture containing the six common stock clamp
   sequences was fed to `build_liteon_dynamic_bridge_clamp_candidate.py`;
2. the builder selected all six observed immediate addresses and generated a
   dynamic `0x18` candidate under `/tmp`;
3. `verify_liteon_bridge_clamp_candidate.py` accepted that candidate against
   the normal restore candidate and confirmed that the dynamic cave preserves
   DPTR;
4. synthetic baseline/patched/restored captures were analyzed, and
   `analyze_liteon_materialized_bridge_clamp_live_test.py` reported:
   - high-offset `0x0f0000` changed and restored;
   - the `0x077000` clamp pattern changed from stock `0x0e` to patched `0x18`;
   - decoded-band `0x184000` changed and restored;
   - a synthetic rejected decoded-band offset was reported as a command
     failure rather than silently disappearing because no `.bin` was written.
5. `build_liteon_post_materializer_multi_blob_writer_candidate.py` built the
   selector22 cave+trampoline smoke target in a temporary directory. The audit
   checks the actual helper-bypass artifacts: two runtime patches, 141-byte
   payload, 80 bytes of remaining cave room, hook bytes changed only at
   `0x422c`, cave bytes changed only for the parsed payload length, low-sector
   helper patches present, and restore image byte-identical to base.

This does not prove the live hook will land, but it verifies the planned
builder/verifier/analyzer loop for the exact success shape expected from the
future `0x18` materialization-oracle run, and it keeps the second-stage
multi-blob response-hook tooling under the same readiness umbrella.

## Current Live Blocker

The Linux bench currently sees:

```text
/dev/sg0  /dev/sda  Generic   External          1.14
/dev/sg1  /dev/sdb  Generic-  SD/MMC            1.00
```

`watch_liteon_plds_preflight.py --once` reports no PLDS devices.

SAT identify can still see the attached ATAPI device below the bridge:

```text
LD5M / PLDS DVD+/-RW DS-8ABSH
```

but that works through ATA `IDENTIFY PACKET DEVICE` (`0xa1`) via ATA
PASS-THROUGH. It is not a usable arbitrary MMC packet tunnel. Do not run helper
bypass, recovery, or bridge-oracle write paths while the host sees only
`Generic External`.

## Completion Audit

| Success criterion | Current evidence | Status |
|---|---|---|
| Visible PLDS optical/currentboot LUN | Current `sg_map` shows only Generic bridge fallback | blocked |
| Normal-mode code execution proof | `0x07` bridge-clamp ladder is prepared, but not run live | not achieved |
| Proper CDD materialization oracle | `0x18` decoded-band ladder step is prepared, but gated behind `0x07` proof | not achieved |
| Restore path ready | Fixed restore candidate verifies byte-identical to base; live wrapper restores after patch | prepared |
| Candidate safety checks | Fixed and synthetic dynamic candidates pass offline verifier | prepared |
| Direct evidence of decoded-band reads | none yet | missing |

## Next Physical/Live Step

Recover or replace the bridge/drive state until `sg_inq /dev/sgX` reports
`PLDS DS-8ABSH`. Then run the watcher or directly run the guarded ladder above.

If the ladder succeeds:

1. archive baseline/patched/restored evidence;
2. inspect `0x077000` for patched clamp hits;
3. inspect `0x0f0000` for the `0x07` proof;
4. inspect decoded-band offsets (`0x184000`, `0x191010`, etc.) for `0x18`
   oracle evidence;
5. only then expand into a real normal-mode response hook.

If the ladder fails before `0x18`, do not force CDD mutations. Analyze whether
the failure was:

- no visible clamp slot in baseline;
- candidate install rejected;
- patched runtime slot not observed;
- high-offset response unchanged;
- restore mismatch.
