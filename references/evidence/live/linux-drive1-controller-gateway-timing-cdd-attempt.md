# Linux Drive 1 Controller-Gateway Timing CDD Attempt

Date: 2026-04-30

Host: `jonathan-thinkpad-t480s`

Drive: Linux drive #1, `PLDS DVD+-RW DS-8ABSH`; active `sg_inq` reported
`LD5M` after every partial run. Linux sysfs still showed stale `0D5C`.

## Goal

Use the existing GOOD/GOOD helper timing channel to read a few bytes through
the 8051/controller gateway:

```text
0x4000.7       busy bit, poll while set
0x4091..0x4093 read-side command/address bytes
0x4098         FIFO data port
```

The immediate question was whether we could sample decoded CDD/controller
memory directly from the currentboot helper hook instead of trying to decode
the CDD stream offline.

## Tooling Change

`scripts/build_liteon_helper_codeexec_candidate.py` now has:

```sh
controller-byte-bit-delay --addr 0xHHMMLL --bit N --payload-offset 0x04f6
```

It sets the controller gateway address, reads one byte from `0x4098`, and uses
the existing timing delay to report one bit. The reader supports this with:

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --space controller \
  --addr 0x184000 \
  --payload-offset 0x04f6
```

A small `--controller-skip N` option can consume a few FIFO bytes after setting
the address. This matters because the resident sometimes treats
`0x4091..0x4093` as a stream selector rather than a flat byte address.

## Calibration

The calibration split stayed clean:

| case | event 68 |
|---|---:|
| constant zero | about `0.256s` |
| constant one | about `0.851s` |
| threshold used | `0.553848s` |

## Reads

All reads used event 68, auto-recovered after each partial run, and ended with
active `LD5M`.

| target | mode | value | interpretation |
|---|---|---:|---|
| `0x184000` | controller direct | `0x00` | first guessed decoded CDD descriptor byte |
| `0x18481c` | controller direct | `0x00` | guessed `0x184000 + CDD directory entry0` |
| `0x000001` | controller direct | `0x00` | proves direct low-byte addressing is not a flat stream offset |
| `0x000000` | controller, skip 1 | `0xce` | non-zero proof that the FIFO-skip controller timing primitive works |
| `0x184000` | controller, skip 1 | `0x00` | guessed CDD descriptor stream still looks zero at this hook |
| `xdata[0x803c]` | direct XDATA | `0x00` | resident gateway base byte is not populated here |
| `xdata[0x803d]` | direct XDATA | `0x00` | same for next base byte |

## Interpretation

The controller-gateway timing read primitive is real: `00:0000` with one FIFO
skip returned a structured non-zero byte (`0xce`) and every bit returned through
the normal helper success path.

The guessed decoded CDD address path did not pan out in this context. Both
`18:4000` and `18:481c` read as zero, and the resident's live gateway-base
bytes at `xdata[0x803c..0x803d]` are zero at the event-68 helper hook. That
suggests the currentboot helper environment does not have the normal decoded
CDD/controller base state populated, or the `0x184000` descriptor address is
not exposed through this gateway until a different runtime phase.

This does not disprove the decoded-CDD-memory idea. It narrows the next attempt:
we probably need a resident/runtime hook after normal LD5M boot, or a more exact
model of the controller stream selector, rather than trying to read decoded CDD
memory from the currentboot profile-tail helper hook.

Ignored raw run summaries remain on the Linux host under:

```text
/home/jonathan/boastermelt/work/linux-runs/
```

