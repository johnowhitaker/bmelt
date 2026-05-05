# CDD Materializer Mode-2 Live Probe - 2026-05-05

Scope: Drive #3, Linux direct-SCSI path. This was a bounded currentboot-only
probe. It did not mutate CDD/F0 bytes. The drive was recovered to normal
`LD5M` afterward.

## Result

The guarded `xdata[0x8196] = 2` parser/materializer call executed and returned
stable status, but it did not populate the decoded/controller target range
`0x184000..0x1b3fff` in currentboot.

It did, however, produce a concrete controller-visible side effect:

```text
gateway 0x07b000..0x07ffff  ->  F0 0x007000..0x00bfff
```

After the trigger, reads from controller gateway `0x07b000` returned the stock
LD5M outer descriptor and CDD1 header byte-for-byte:

```text
0x07b000: 00 2c 00 00 70 00 00 00 40 00 00 08 00 00 00 00
0x07b010: 50 00 40 00 00 18 40 00 00 18 40 00 00 1b 40 00
...
0x07b02c: 43 44 44 09 10 16 ...
```

The same mapping held at later sampled offsets:

```text
gateway 0x07b400 == F0 0x007400
gateway 0x07b800 == F0 0x007800
gateway 0x07c000 == F0 0x008000
gateway 0x07d000 == F0 0x009000
gateway 0x07ff00 == F0 0x00bf00
gateway 0x080000 == zero
```

So the `0x8196 == 2` path appears to open or copy a 0x5000-byte CDD source
window into the public/controller gateway surface, bounded at `0x080000`. It
does not, by itself, expand hard CDD records into the decoded destination
range.

## Live Sequence

The hook candidate was built with:

```sh
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-cdb-bulk-cdd-parser-mode2-status64 \
  --gateway-cdb-bulk-with-cdd-parser-mode2-status64 \
  --cave-len 0xdd
```

The full helper-bypass candidate installed successfully on Drive #3 and the
drive returned to `LD5M`.

After a Pico cold cycle, event 1 entered the hooked currentboot state. The
ordinary gateway fallback was verified by reading `0x018620`, which returned:

```text
Flash Type Error
```

The mode-2 trigger CDB was:

```text
12 00 00 00 f0 40 00 fc e4 00 00 00
```

The trigger returned marker `0xd8` at response byte `0x20`, proving the special
hook path ran. It copied `xdata[0x4e80..0x4ebf]` into the response:

```text
xdata[0x4e80..0x4e8f] 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00
xdata[0x4e90..0x4e9f] 00 40 c0 00 00 08 00 00 00 00 00 00 00 00 00 00
xdata[0x4ea0..0x4eaf] 06 00 00 00 0f 60 31 64 00 00 18 00 00 00 00 00
xdata[0x4eb0..0x4ebf] 00 08 00 0f 00 00 00 00 07 00 00 00 00 00 00 00
```

The repeated trigger response was byte-for-byte identical.

## Negative Checks

These sampled decoded/controller addresses stayed all zero before and after the
mode-2 trigger:

```text
0x184000
0x184060
0x190690
0x19c120
0x19c1b0
0x19c2a0
0x19c660
0x19c760
0x19cb10
0x19cd50
0x19cf30
0x19d128
0x19d210
```

This is a useful negative: the alternate `0x8196 == 2` path is a real
controller transfer, but not a complete currentboot decoded-memory oracle.

## Evidence

```text
references/evidence/live/drive3-currentboot-cdd-mode2-materializer-install-20260505/
references/evidence/live/drive3-currentboot-cdd-mode2-materializer-trigger-20260505/
```

Key files:

```text
mode2-trigger-summary.json
mode2-trigger-summary-repeat.json
pre-mode2/
post-mode2/
post-mode2-expanded/
recovery-after-mode2/
```

## Interpretation

The static read of the `0x8196 == 2` path was mostly right about the transfer
shape:

```text
front operand: 0x00407000
window/extent: 0x0007b000
length:        0x00005000
```

The live result suggests this is a mapped-source transfer: it exposes the
front of the CDD object into a controller/public gateway window. That is useful
for understanding the mailbox, but it does not eliminate the CDD hard-body
encoding problem.

Practical consequence: do not spend more live cycles asking this exact mode-2
trigger to produce decoded `0x184000` bytes. The next materializer work should
focus on either:

- the fuller normal boot prelude around the `LITE` trailer check and
  `FUN_CODE_40b2`; or
- identifying the later controller command that consumes the exposed/mapped
  CDD source window and performs hard-body expansion.
