# Normal-Mode Hook Tests

Date: 2026-04-30.

Drive: Linux bench drive #1 on `jonathan-thinkpad-t480s`, optical LUN
`/dev/sg0`, normal identity `PLDS DVD+-RW DS-8ABSH LD5M`.

Goal: test whether the fast normal-mode commands found in the read-only survey
execute any of the visible F0/currentboot 8051 command path.

## Baseline

Before installing any new hook, the selected no-disc normal commands were all
fast and stable:

| command | median | max |
|---|---:|---:|
| `INQUIRY` standard | `0.007160s` | `0.010091s` |
| `EXTRAINQ` | `0.007783s` | `0.010037s` |
| `MODE SENSE(10)` | `0.008962s` | `0.012150s` |
| `GET CONFIGURATION current` | `0.008364s` | `0.009163s` |
| `GET CONFIGURATION all` | `0.009959s` | `0.010785s` |
| `GET EVENT STATUS media` | `0.007974s` | `0.008198s` |
| `MECHANISM STATUS` | `0.007750s` | `0.007954s` |

## Test 1: Visible Response-Copy Helper

Candidate: `resident-hook-response-copy-delay20`

Patch:

```text
0x6206: 90 80 3e -> 02 6e e3
0x6ee3: delay 0x20, original 90 80 3e, LJMP 0x6209
```

The patch persisted in F0:

```text
0x6206 live 026ee3...
0x6ee3 live 7f207eff7dffddfedefadff690803e026209...
```

Normal-mode command timings did not move:

| command | median | max |
|---|---:|---:|
| `INQUIRY` standard | `0.007003s` | `0.008886s` |
| `EXTRAINQ` | `0.007816s` | `0.011056s` |
| `MODE SENSE(10)` | `0.008585s` | `0.010500s` |
| `GET CONFIGURATION current` | `0.006887s` | `0.007763s` |
| `GET CONFIGURATION all` | `0.010415s` | `0.014245s` |
| `GET EVENT STATUS media` | `0.007574s` | `0.009382s` |
| `MECHANISM STATUS` | `0.007562s` | `0.010144s` |

Interpretation: normal LD5M responses are not using the visible F0
`FUN_CODE_6206` response-copy helper.

Useful side observation: the next currentboot write run slowed dramatically
while this hook was installed. So `0x6206` is definitely live in currentboot;
it is just not live for ordinary normal-mode command responses.

## Test 2: Visible Packet-Intake Helper

Candidate: `resident-hook-packet-intake-delay20`

Patch:

```text
0x542b: 90 81 79 -> 02 6e e3
0x6ee3: delay 0x20, original 90 81 79, LJMP 0x542e
```

The patch persisted in F0:

```text
0x542b live 026ee3...
0x6206 live 90803e...        # previous response-copy hook restored
0x6ee3 live 7f207eff7dffddfedefadff690817902542e...
```

Normal-mode command timings again did not move:

| command | median | max |
|---|---:|---:|
| `INQUIRY` standard | `0.005213s` | `0.006725s` |
| `EXTRAINQ` | `0.008033s` | `0.009451s` |
| `MODE SENSE(10)` | `0.008723s` | `0.009052s` |
| `GET CONFIGURATION current` | `0.007850s` | `0.008178s` |
| `GET CONFIGURATION all` | `0.010605s` | `0.011677s` |
| `GET EVENT STATUS media` | `0.007529s` | `0.009367s` |
| `MECHANISM STATUS` | `0.007303s` | `0.010437s` |

Interpretation: normal LD5M commands are not entering the visible F0
`FUN_CODE_542b` packet-intake helper either.

## Restore

The stock-restore candidate rewrote:

```text
0x1ea0 -> 20 22 38
0x542b -> 90 81 79
0x6206 -> 90 80 3e
0x6ee3..0x6f62 -> ff...
```

After Pico servo cold boot, a live-key F0 dump of `0x1000..0x6fff` matched
stock LD5M exactly:

```text
diffs = 0
```

Post-restore command timings returned to baseline-scale values, and the drive
is visible as `LD5M`.

## Conclusion

This phase tested the two broadest visible-F0 hooks that should have affected
many commands if the normal LD5M host response path used the visible currentboot
8051 command machinery:

- `0x6206` response-copy helper;
- `0x542b` packet-intake helper.

Both hooks persisted and both were negative for normal-mode SCSI timing. The
fast normal-mode response surfaces are still useful trigger candidates, but the
code path that serves them is likely a different ROM/RAM/controller runtime
path, not the visible F0 prefix/currentboot path we have been patching.

The next useful route is therefore not another blind visible-prefix timing
hook. Better options:

1. localize where normal runtime materializes the `INQUIRY`/`EXTRAINQ`
   templates outside the visible F0 copies;
2. find a hook that survives into the normal runtime after controller/CDD boot;
3. use currentboot/controller gateway work to identify the RAM/overlay region
   that replaces this visible command path.

Artifacts:

```text
references/evidence/live/normal-mode-hook-tests/baseline/timing.md
references/evidence/live/normal-mode-hook-tests/response-copy-post/timing.md
references/evidence/live/normal-mode-hook-tests/packet-intake-post/timing.md
references/evidence/live/normal-mode-hook-tests/stock-restore/timing.md
references/evidence/live/normal-mode-hook-tests/stock-restore/f0-1000-6fff-livekey.bin
```
