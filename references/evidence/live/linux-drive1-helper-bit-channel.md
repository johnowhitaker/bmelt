# Linux Drive 1 Helper Bit-Channel PoC

Date: 2026-04-29

Host: `jonathan-thinkpad-t480s`

Drive: Linux drive #1, `PLDS DVD+-RW DS-8ABSH`, recovered to `LD5M` after
each short run.

## Summary

The timing-only helper-code execution proof is now widened into a no-hardware
one-bit data channel.

The channel still uses the late helper hook:

```text
helper plaintext 0x02b5 / code 0x32af:
30 e6 12 -> 02 36 1a
```

but the payload at helper code `0x361a` chooses between:

```text
0x32c4  normal helper success path  -> event 68 returns GOOD
0x32b2  original helper error path   -> event 68 returns DID_ERROR
```

That means helper code can send one bit to the host by deciding whether event
`68` should complete normally or take the known recoverable helper error path.

## Proof Steps

### Status Pair Probe

First, the helper's existing `0x3740` status-pair routine was tested as a
possible packet-like channel.

Payload control path:

```text
LCALL 0x373c
MOV R5,#status
MOV R7,#0x04
LJMP 0x32cb
```

Results:

| run | event 68 rc | event 68 stderr | recovery |
|---|---:|---|---|
| `status-01-control` | `0` | `SCSI Status: Good` | `LD5M` |
| `status-42-probe` | `0` | `SCSI Status: Good` | `LD5M` |

Changing the nominal status byte to `0x42` was visible in the staged helper
window but did not alter host-visible command status. This path is not an
obvious multi-byte host packet channel.

### Forced Error Path

Patching the late branch directly to the original error path:

```text
0x02b5: 30 e6 12 -> 02 32 b2
```

made event `68` return:

```text
Host_status=0x07 [DID_ERROR]
Driver_status=0x08 [DRIVER_SENSE]
SCSI Status: Good
```

Auto-recovery returned the drive to `LD5M`.

### Payload-Controlled Bit

The payload then made the success/error choice from an actual bit test:

```text
MOV A,#value
JNB ACC.bit,error
LJMP 0x32c4
error:
LJMP 0x32b2
```

Results:

| run | tested value | event 68 rc | meaning |
|---|---:|---:|---|
| `immediate-bit1-success` | `0x01.bit0` | `0` | payload chose success |
| `immediate-bit0-error` | `0x00.bit0` | `99` | payload chose error |

This proves the host-visible bit is controlled by helper code, not merely by a
static patch target.

### MOVC Negative

`MOVC A,@A+DPTR` at code address `0x32af` did not distinguish bit `0` from bit
`1`; both probes returned GOOD. The likely explanation is that `MOVC` is not
seeing the mutable helper overlay at that address, or it is reading an unmapped
/ all-ones code view.

### MOVX XDATA Read

`MOVX A,@DPTR` does work as an internal-state source. The polarity check on
`xdata[0x48a0].6` matched the known helper branch behavior:

| run | condition treated as success | event 68 rc | interpretation |
|---|---|---:|---|
| `movx-48a0-bit6-success-on-zero` | bit 6 clear | `0` | bit 6 is `0` |
| `movx-48a0-bit6-success-on-one` | bit 6 set | `99` | bit 6 is not `1` |

The byte reader then read all bits of `xdata[0x48a0]` at the late event-68 hook:

| bit | value | event 68 rc |
|---:|---:|---:|
| 0 | `0` | `99` |
| 1 | `0` | `99` |
| 2 | `0` | `99` |
| 3 | `0` | `99` |
| 4 | `0` | `99` |
| 5 | `1` | `0` |
| 6 | `0` | `99` |
| 7 | `1` | `0` |

Result:

```text
xdata[0x48a0] = 0xa0
```

That matches the helper success path setting `0x48a0 |= 0xa0` before the final
cleanup sequence.

Additional selected XDATA reads at the same hook point:

| address | value | note |
|---:|---:|---|
| `0x47d2` | `0xff` | controller/finalizer state byte candidate |
| `0x48a0` | `0xa0` | handoff byte; success path has set bits 7 and 5 |
| `0x48a5` | `0xff` | nearby helper cleanup/status byte candidate |
| `0x8221` | `0xff` | finalizer handoff byte candidate |

Compact machine-readable summaries:

```text
references/evidence/live/linux-drive1-helper-xdata-48a0-summary.json
references/evidence/live/linux-drive1-helper-xdata-selected-summary.json
```

## Tools

Reusable builders:

```text
scripts/build_liteon_helper_codeexec_candidate.py
scripts/read_liteon_xdata_bit_channel.py
```

Example byte read:

```bash
python3 scripts/read_liteon_xdata_bit_channel.py \
  --device /dev/sg1 \
  --addr 0x48a0 \
  --out-dir runs/helper-xdata-bit-channel \
  --retry-attempts 2 \
  --between-delay 4
```

The delay is deliberate. After a bit returns through the error path, the
recovery run can leave a short-lived Unit Attention condition. Waiting between
bits keeps the loop stable.

## Interpretation

This is slow, but it is a real no-hardware internal data channel:

- patched helper code can execute at a known safe late hook;
- it can read XDATA with `MOVX`;
- it can return one bit to the host by selecting helper success or helper error;
- the known Linux recovery path restores `LD5M` after each bit.

It is not yet a practical bulk dump channel. It is good enough to map a small
number of important XDATA registers and to validate candidate GPIO/status
registers before moving to Pico wiring.

## Timing-Nibble Side Probe

A follow-up attempt tried to convert one XDATA nibble into a delay count so a
byte could be read in two successful event-68 runs. Constant delay calibration
still behaved as expected, but nibble-derived delays from the `0x48a0` hook did
not decode consistently. That mode was not kept as supported tooling. Use the
GOOD/DID_ERROR bit channel until there is a cleaner multi-bit channel.
