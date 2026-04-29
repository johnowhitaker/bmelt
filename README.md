# boastermelt

Clean working repo for the LiteOn/PLDS `DS-8ABSH` firmware project.

The old 10GB+ working tree was intentionally collapsed. Historical bulk logs,
temporary Wine prefixes, packaged handoff zips, and the old git history were
removed from the active repo; a small amount of retired source/notes is under
`old/`, which is ignored. The user has external backups of the full pre-clean
tree.

## Current State

We can:

- talk to a drive from Linux with `sg_raw`;
- dump and decrypt `READ BUFFER id=F0`;
- recover the known `0D5C` currentboot state back to `LD5M`;
- build helper-bypass candidates that persist selected F0 byte changes;
- execute patched 8051 helper-overlay code and observe a host timing signal.

The current code-exec foothold is documented in
`references/evidence/live/linux-drive1-codeexec-timing-poc.md`.

## Read First

- `docs/AI_FIELD_GUIDE.md`: compact technical handoff for future agents.
- `docs/JOURNAL.md`: human-readable story of the project so far.
- `docs/helper-bypass-write-method.md`: practical helper-bypass write method.
- `handoff/NEXT_SESSION_HANDOFF.md`: latest operational handoff.

## Useful Commands

Check the repo:

```sh
make check
```

On the Linux host, discover the drive:

```sh
ssh root@jonathan-thinkpad-t480s 'cd /home/jonathan/boastermelt && python3 scripts/liteon_linux_status.py'
```

Dump a full decrypted F0 image:

```sh
ssh root@jonathan-thinkpad-t480s 'cd /home/jonathan/boastermelt && mkdir -p runs/f0 && python3 scripts/dump_liteon_linux_f0_window.py --device /dev/sg1 --extrainq references/evidence/ld5m-extrainq-reference.log --start 0 --size 0x100000 --chunk 0x80 --out runs/f0/f0-decrypted.bin --raw-out runs/f0/f0-raw.bin'
```

Recover from known `0D5C` currentboot:

```sh
ssh root@jonathan-thinkpad-t480s 'cd /home/jonathan/boastermelt && python3 scripts/recover_liteon_currentboot_linux.py --device /dev/sg1'
```

Build a helper-bypass candidate:

```sh
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name example-d8ff4 \
  --patch 0xd8ff4:33 \
  --include-pre-tail
```

Run a candidate on Linux:

```sh
ssh root@jonathan-thinkpad-t480s 'cd /home/jonathan/boastermelt && python3 scripts/run_liteon_linux_persistence_experiment.py --candidate references/firmware/extracted/helper-bypass-candidates/example-d8ff4/liteon-full-currentboot-ld5m-helper-bypass-example-d8ff4-candidate.json --device /dev/sg1 --skip-pre-f0 --end-index 544 --f0-size 0xe0000 --capture-finalizer-status-after-event 1 --capture-finalizer-status --recover-on-currentboot'
```

## Layout

- `analysis/8051/`: current 8051 binary and Ghidra decompile.
- `docs/`: curated docs only.
- `handoff/`: short handoff for the next session.
- `references/`: minimal known-good artifacts and current PoC evidence.
- `scripts/`: minimal tooling for Linux access, candidate building, and recovery.
- `old/`: ignored retired pre-clean misc files.
