# LiteOn Profile-Tail Helper Mutation Candidate

Offline dry-run artifact. No drive commands were sent.

## Purpose

Test whether the `ef130045` profile-tail helper overlay is independently mutable once the F0 image is kept byte-identical to the passing same-image control.

The candidate changes every currentboot-key profile-tail payload. The staged F0 chunks and all bank pMac/control payloads remain those of the same-image LD5M control.

Selected target scope: `all_currentboot_tails` (15 events: `35, 69, 103, 137, 171, 205, 239, 273, 307, 341, 375, 409, 443, 477, 511`).

## Mutation

- first plain profile-tail offset: `0x2b5`.
- first helper body offset: `0x2af`.
- patch `0x2b5` body `0x2af`: `30e612` -> `02361a`.
- patch `0x620` body `0x61a`: `466c6173682054797065204572726f` -> `7f807eff7dffddfedefadff60232c4`.
- expected host READ BUFFER id=01 offset if admitted: `0x182b5`.

## Outputs

- candidate: `references/firmware/extracted/liteon-full-currentboot-ld5m-base-mutated-all-helper-final-branch-delay80-poc-candidate.json`
- mutated plaintext tail: `references/firmware/extracted/profile-tail-mutation-candidates/helper-final-branch-delay80-poc/ef130045-mutated-string-plain.bin`
- mutated currentboot payload: `references/firmware/extracted/profile-tail-mutation-candidates/helper-final-branch-delay80-poc/ef130045-mutated-string-currentboot-payload.bin`

## Expected Live Interpretations

- If first mutated event 35 fails immediately, the profile-tail payload/plaintext is checked before finalizer admission.
- If the mutated tail events succeed but event 544 rejects, the finalizer admission covers or depends on the helper overlay bytes.
- If event 544 passes and READ BUFFER id=01 around host offset 0x0182b5 shows the changed byte, the helper overlay is mutable independently of the F0 container.
- If event 544 passes but the helper window is canonical, the controller re-exposes its own helper copy rather than the staged mutated payload.

## Suggested Probe Shape

- Run only after explicitly choosing drive #1 as the live sacrificial/recoverable target.
- Capture the first mutated event (`35`) return code, event-544 return code, final revision, and READ BUFFER id `01` around `0x0182b5`.
- Auto-recover with the known Linux recovery path if the run enters `0D5C`.

One suitable Linux runner shape is:

```bash
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/liteon-full-currentboot-ld5m-base-mutated-all-helper-final-branch-delay80-poc-candidate.json \
  --device /dev/sg1 \
  --skip-pre-f0 --skip-post-f0 \
  --end-index 544 \
  --capture-finalizer-status-after-event 35 \
  --capture-finalizer-status \
  --recover-on-currentboot
```
