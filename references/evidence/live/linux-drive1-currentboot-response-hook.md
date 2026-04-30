# Linux Drive 1 Currentboot Response Hook

Date: 2026-04-30

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- remote repo: `/home/jonathan/boastermelt`
- device during these runs: `/dev/sg0`
- drive: Linux drive #1

## Summary

The currentboot INQUIRY/EXTRAINQ path reaches visible 8051 code. Hooking the
final response-copy call at code `0x4fc9` lets a small resident payload write a
chosen byte into the INQUIRY response before the stock `0x6206` response copy.

This converts the earlier timing/error readout into a host-visible byte channel:

- constant test: currentboot revision became `XD5C`;
- XDATA fixed-window test: `xdata[0x818a..0x8195]` exposed the active CDB bytes;
- controller-gateway test: controller address `0x018620` returned
  `Flash Type Error`;
- XDATA CDB-address test: arbitrary 16-bit XDATA reads now work through INQUIRY.

This still requires the drive to enter the currentboot identity handler. In
practice, after installing a new persistent F0 hook, use the Pico servo cold
power-cycle and then run event 1/profile-tail to enter currentboot.

## Hook Site

The hook is in `FUN_CODE_4ec6`, the visible currentboot INQUIRY/EXTRAINQ
handler. The final response-copy sequence is:

```text
0x4fc5  7f20      MOV R7,#0x20
0x4fc7  7e02      MOV R6,#0x02
0x4fc9  126206    LCALL 0x6206
0x4fcc  22        RET
```

The hook patches `0x4fc9` to `LJMP 0x6ee3`, writes response byte `0x20`, calls
the original `0x6206`, then jumps back to `0x4fcc`.

Builder:

```text
scripts/build_liteon_currentboot_response_hook_candidate.py
```

Readers:

```text
scripts/read_liteon_currentboot_gateway.py
scripts/read_liteon_currentboot_xdata.py
```

## Constant Response PoC

Candidate:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-revision-x-constant/currentboot-response-hook-revision-x-constant/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-revision-x-constant-candidate.json
```

Payload wrote constant byte `0x58` (`X`) to response offset `0x20`.

After servo cold boot and event 1, currentboot identity reported revision
`XD5C`. This is the first clean host-visible proof that our resident 8051 code
can alter data returned over normal SCSI.

## XDATA CDB Window

Candidate:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-xdata-818a-window/currentboot-response-hook-xdata-818a-window/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-xdata-818a-window-candidate.json
```

The hook read `xdata[0x818a + (CDB[5] & 0x3f)]`.

Readback:

```text
xdata[0x818a..0x81c9]:
12000000b045b4000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
```

Interpretation:

- `0x818a = 0x12`, the INQUIRY opcode;
- `0x818e = 0xb0`, the handler's clamped allocation length;
- `0x818f` follows the host's CDB byte 5;
- CDB bytes 7..11 also survive to the hook, which gives us parameter bytes.

## Controller-Gateway CDB Address

Candidate:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-cdb-byte-v3/currentboot-response-hook-gateway-cdb-byte-v3/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-gateway-cdb-byte-v3-candidate.json
```

Addressing:

```text
CDB[5] low six bits = byte offset inside a 64-byte window
CDB[7:9]            = 24-bit big-endian controller base address
response[0x20]      = selected byte
```

Version 1 and 2 returned stale `0x05` bytes. Version 3 fixed this by mimicking
the resident's controller-read quirk: after writing `0x4091..0x4093`, perform a
throwaway `0x4098` read, wait on `0x4000.7`, then read `0x4098` again.

Known-good read:

```sh
python3 scripts/read_liteon_currentboot_gateway.py \
  --device /dev/sg0 \
  --address 0x018620 \
  --length 32
```

Output:

```text
466c6173682054797065204572726f7200905904e4f0a3f09059c0e054fe4404
Flash Type Error..Y......Y..T.D.
```

The guessed decoded CDD base is still zero in this currentboot/helper phase:

```text
controller[0x184000..0x1841ff] = all 00
```

That agrees with the older timing-channel attempts. It does not disprove the
descriptor's `0x184000..0x1b4000` logical range; it says this currentboot phase
does not expose populated decoded CDD bytes there.

## XDATA CDB Address

Candidate:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-xdata-cdb-byte/currentboot-response-hook-xdata-cdb-byte/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-xdata-cdb-byte-candidate.json
```

Addressing:

```text
CDB[5] low six bits = byte offset inside a 64-byte window
CDB[7:8]            = 16-bit big-endian XDATA base address
response[0x20]      = selected byte
```

Known-good reads:

```text
xdata[0x818a..] = 12 00 00 00 b0 4f b4 81 80 ...
xdata[0x4704..] = 00 50 00 04 90 00 64 06 78 ...
```

The `0x4704` read confirms Claude's bit-channel finding (`xdata[0x4704].0 = 0`)
without jumping into the helper `DID_ERROR` path.

## Button Differential

With the XDATA hook installed and GP27 controlled by the Pico:

```text
released GP27: ~2.8-2.9 V, digital high
pulled-low GP27: ~0 V, digital low
```

Reading `xdata[0x4800..0x48ff]` with the button released vs held low produced
stable changes:

```text
0x4814: d9 -> c9  xor 10
0x48f7: 87 -> 07  xor 80
```

`0x4814.4` is the cleanest front eject button-sense candidate so far. A few
neighboring `0x488x` bytes also move, but less cleanly across repeats.

## Practical Consequence

The old bit/timing channels were useful proof but slow and awkward: a single
bit could cost a full helper run and a recovery cycle, sometimes seconds per
bit. The currentboot response hook reads one byte per ordinary INQUIRY CDB and
returns through the normal handler. The bandwidth is still not bulk-dump fast,
but it is fast enough to map pages of XDATA or controller memory without
wedging the drive on every zero bit.

The main remaining gap is phase/context. This hook sees currentboot-helper
state, not necessarily normal LD5M runtime state. The decoded CDD range is
still blank here, and normal-runtime host-visible hooks are still unresolved.
