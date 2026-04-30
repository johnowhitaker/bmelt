# Currentboot XDATA 0x811e Source Test

Date: 2026-04-30.

Host separation:

- drive host: `jonathan-thinkpad-t480s` via Tailscale IP `100.119.237.135`
- remote repo: `/home/jonathan/boastermelt`
- drive: Linux drive #1
- device during the test: `/dev/sg0`

## Question

The offline normal-response comparison found that currentboot XDATA contains
the model substring also present in normal `INQUIRY`/`EXTRAINQ`:

```text
xdata[0x811e..0x812d] = 44 56 44 2b 2d 52 57 20 44 53 2d 38 41 42 53 48
                       "DVD+-RW DS-8ABSH"
```

This test asked whether that XDATA copy is an actual currentboot response
source, or just a stale/key/metadata copy.

## Procedure

1. Installed the guarded `currentboot-response-hook-xdata-cdb-rw` candidate.
2. Pico servo cold-booted the drive.
3. Entered currentboot with the usual event-1 profile-tail transition.
4. Wrote one byte through the guarded XDATA hook:

```text
xdata[0x811e] <- 0x58  ("X")
readback = 0x58
```

5. Issued another currentboot `INQUIRY`/EXTRAINQ-style command with the hook
   selecting the same XDATA byte, so response byte `0x20` would also show the
   hook readback.

## Result

The hook readback worked:

```text
response[0x20] = 0x58  ("X")
```

But the stock model field remained canonical:

```text
response[0x10..0x1f] = "DVD+-RW DS-8ABSH"
```

So `xdata[0x811e]` is writable/readable through the currentboot hook, but it is
not the live source for the currentboot identity response. The XDATA copy is
probably metadata/key-window state, not the response template itself.

## Cleanup

The first recovery back to `LD5M` did not remove the installed response hook.
That is expected in hindsight: the same-image recovery exits currentboot, but it
does not necessarily force a stock rewrite of the patched bytes.

I then ran the explicit `currentboot-response-hook-restore-4fc9-cave` helper
bypass candidate, cold-booted with the Pico servo, and verified a live-key F0
dump of `0x1000..0x6fff` against stock LD5M:

```text
diffs = 0
0x4fc9 = 12 62 06
0x6ee3.. = ff...
```

## Artifacts

```text
references/evidence/live/xdata-source-localizer/write-811e-X.json
references/evidence/live/xdata-source-localizer/currentboot-inquiry-after-811e-X.bin
references/evidence/live/xdata-source-localizer/post-exp-f0-1000-6fff-livekey.bin
```
