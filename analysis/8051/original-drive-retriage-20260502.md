# Original Drive Retriage

Date: 2026-05-02

After the spare drive stopped exposing an optical LUN, the original drive was
swapped back onto the Linux/Initio/Pico setup.

## Bench State

Linux sees the original drive as a normal optical target:

```text
/dev/sg0  PLDS DVD+-RW DS-8ABSH LD5M
/dev/sr0  CD-ROM
/dev/sg1  Generic- SD/MMC bridge LUN
```

The Pico is on the Linux laptop at `/dev/ttyACM0`; `pyserial` is installed
there and `pico/client.py` can control the servo power switch from Linux.

## Flash State

A sequential 1 MiB F0 read from offset zero is the reliable state check. The
original drive differs from stock LD5M in four ranges:

```text
0x04fc9..0x04fcb  12 62 06 -> 02 6e e3
0x06ee3..0x06ef6  currentboot response-hook cave payload
0x06ef8..0x06f78  currentboot response-hook cave payload
0x28519           68 -> 60, record-59 CDD mutation
```

The cave payload matches the old `currentboot-response-hook-gateway-cdb-bulk`
candidate. That hook is useful in currentboot identity handling, but it does
not appear to affect normal LD5M command responses.

Known probe bytes:

```text
F0[0x2627a] = 0x5d   record-55 byte is stock
F0[0x28519] = 0x60   record-59 mutation remains installed
F0[0x2ae8f] = 0x4e   record-60 affine byte is stock
F0[0x27410] = 0x3a   record-57 byte is stock
```

Evidence:

```text
references/evidence/live/original-drive-f0-state-20260502T024733Z/
```

## Normal-Mode Read-Only Captures

First capture:

```text
references/evidence/live/original-drive-normal-readonly-hook-rec59-20260502T025333Z/
```

This captured baseline, INQUIRY, EXTRAINQ, GET CONFIGURATION,
GET PERFORMANCE type 00, and MODE SENSE read-error windows. The follow-up
read-only surface probe finished, but `GET PERFORMANCE nominal` took 4.3s with
`rc=99`, and a later status check wedged the bridge until a Pico servo power
cycle. Avoid that nominal GET PERFORMANCE probe on this drive state.

Second focused capture:

```text
references/evidence/live/original-drive-rec59-focused-safe-20260502T025736Z/
```

This excluded the slow GET PERFORMANCE path and completed cleanly. The drive
stayed visible as normal `LD5M`.

## Record-59 Contig Result

The current original-drive captures match the known record-59-mutated behavior.
For contig 4:

```text
analysis/8051/cdd-runtime-chunk-contigs-20260501/contig-004-03chunks.bin
```

The focused run saw the full 3-chunk sequence at public offset `+0x7180` in
50/96 captures:

```text
stock reference:        0/32 full-sequence hits
old record-59 mutated: 15/32 full-sequence hits
current original:      50/96 full-sequence hits
```

All component chunks are visible in all states. The mutation changes the public
tile placement/adjacency, not the chunk bytes themselves.

Record 59 is a hard/high-redundancy record, not one of the affine leaf records:

```text
CDD1 source range: 0x28119..0x28ab7
source length:     0x99e
operation key:     30 ca 94 93 0e 05
mode bits:         0x80
decoded span:      0x130
patched byte:      source +0x400, F0[0x28519]
```

The source/decoded alignment is unusually tidy: record 59's candidate decoded
span begins at public `+0x7170`, and the affected contig appears at `+0x7180`.
That puts the observed 192-byte contig at `+0x10..+0xcf` inside the candidate
decoded span. The byte we changed is therefore probably schedule/control
material for this hard record rather than direct instruction data.

Detailed report:

```text
analysis/8051/original-drive-rec59-focused-contig4-hits-20260502.md
analysis/8051/original-drive-rec59-focused-contig4-hits-20260502.json
```

## Host Responses

Overlapping normal host responses still match the stock record-55 baseline:

```text
INQUIRY EXTRAINQ            unchanged
GET CONFIGURATION current   unchanged
GET CONFIGURATION all       unchanged
```

So the installed `0x4fc9 -> 0x6ee3` hook is inert for these normal LD5M
commands. It is still a currentboot response hook, not a normal-mode response
channel.

## Working Guidance

This drive is usable for read-only normal-mode work and for studying the
already-installed record-59 effect. It is not a clean target for new
helper-bypass write experiments. Any future live-write use should explicitly
start from this mutated state, or first restore:

```text
0x04fc9..0x04fcb -> 12 62 06
0x06ee3..0x06f78 -> ff
0x28519          -> 68
```

Given the spare-drive record-55 failure, do not run the prepared record-60
affine probe on this original unless we consciously accept stacking another
mutation on top of record 59 and the response-hook cave.
