# Helper-Bypass Write Method

Status: live-proven on Linux drive #1 for LD5M same-family currentboot flow.

This is the current practical route for persistent modified F0 bytes without
recomputing the unknown `0xe7fe0` container seal.

## Core Idea

The controller admits only byte-valid/sealed F0 containers at finalization. The
working bypass does not forge that seal. Instead it:

1. stages an LD5M-shaped F0 image through the already-modeled full-currentboot
   update flow;
2. patches the profile-tail helper overlay so its final-status path reports
   success;
3. lets the helper's normal flash erase/program code write the staged bytes;
4. verifies persistence with delayed `READ BUFFER id=F0`.

The essential helper patch is:

```text
plain 0x02b5: 30 e6 12 -> 02 32 c4
```

That patch is applied to every currentboot-key profile-tail payload and,
when `--include-pre-tail` is used, to event 1 with the separate LD5M pre-tail
key.

## Build A Candidate

For normal sectors at or above `0x7000`:

```bash
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name example-patch \
  --patch 0xd8ff4:33 \
  --include-pre-tail
```

For lower-prefix sectors below `0x7000`, add automatic erase/program range
patches:

```bash
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name example-prefix-patch \
  --patch 0x445a:40 \
  --auto-helper-range \
  --include-pre-tail
```

`--auto-helper-range` intentionally chooses erase+rewrite from the lowest
touched `0x1000` sector. Use it only when that sector is a deliberate target.
Sectors `0x00..0x03` remain a higher-risk escalation.

## Plan A Patch

Before building, classify bit transitions and helper range needs:

```bash
python3 scripts/plan_liteon_bitclear_patch.py \
  --patch 0xd8ff4:33 \
  --out-json work/plans/liteon-bitclear-patch-plan-example.json \
  --out-md work/plans/liteon-bitclear-patch-plan-example.md
```

If restoring a known live scar, model that current byte:

```bash
python3 scripts/plan_liteon_bitclear_patch.py \
  --current-patch 0x445a:40 \
  --patch 0x445a:50 \
  --out-json work/plans/liteon-bitclear-patch-plan-restore.json \
  --out-md work/plans/liteon-bitclear-patch-plan-restore.md
```

## Run On Linux

Copy the candidate directory to the Linux host, then run:

```bash
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/helper-bypass-candidates/example-patch/liteon-full-currentboot-ld5m-helper-bypass-example-patch-candidate.json \
  --device /dev/sg0 \
  --skip-pre-f0 \
  --end-index 544 \
  --f0-size 0xe0000 \
  --capture-finalizer-status-after-event 1 \
  --capture-finalizer-status \
  --recover-on-currentboot
```

Rediscover the drive before each run. After host reboots or USB/SATA resets it
may move between `/dev/sg0` and `/dev/sg1`.

## Verify Or Dump Manually

The Linux read-only dumper is:

```bash
python3 scripts/dump_liteon_linux_f0_window.py \
  --device /dev/sg0 \
  --extrainq references/evidence/ld5m-extrainq-reference.log \
  --start 0 \
  --size 0x100000 \
  --chunk 0x80 \
  --out runs/current-f0/f0-decrypted.bin \
  --raw-out runs/current-f0/f0-raw.bin
```

The drive accepts `READ BUFFER F0` reliably at `0x80`-byte chunks.

## Live-Proven Cases

- Helper final-status bypass made modified F0 bytes persist.
- Identity/profile byte `0xd8ff4: 32 -> 33` persisted via the generic builder.
- The same byte restored to `32` via the generic builder.
- After a true Pico-servo `+5V` power cycle, direct F0 readback still showed
  the `0xd8ff4` edit, while live EXTRAINQ stayed canonical. This confirms flash
  persistence but also confirms this identity/profile copy is not the live
  EXTRAINQ source.
- Identity/profile vendor-copy byte `0xd8fd8: 50 -> 40` persisted and restored;
  normal INQUIRY still reported `PLDS`, so that copy is not the normal-mode live
  identity source.
- Lower-prefix sector 6 was erased/reprogrammed to restore `0x6f80`.
- Lower-prefix sector 4 was erased/reprogrammed to restore `0x445a`.
- Full 1 MiB F0 after the generic proof/restore matched stock LD5M exactly.
- Full 1 MiB F0 after the later vendor-copy proof/restore also matched stock
  LD5M exactly.

The clean repo keeps only compact current evidence. The full proof/restore logs
are in the external pre-clean backup; the current runnable artifacts are:

```text
references/firmware/extracted/liteon-full-currentboot-ld5m-base-candidate.json
references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-currentboot.json
references/firmware/extracted/liteon-profile-tail-ef130045-ld5m-official-pretail.json
references/evidence/live/linux-drive1-codeexec-timing-poc.md
```

## Boundaries

This method bypasses final admission status; it does not make arbitrary
structural edits safe.

Avoid casual edits in:

- CDD stream record directories, especially stream1 `0x704c..0x7dec`;
- CDD headers and descriptor boundary fields;
- erased gaps unless deliberately testing layout rules;
- sectors `0x00..0x03` until there is a specific reason and recovery plan.

For normal non-CDD bytes in helper-covered sectors, the workflow is now close to
generic: plan the patch, build a helper-bypass candidate, run on Linux, verify
with delayed F0 readback, and keep a restore candidate nearby.
