# Currentboot Mapped-Source Hook On Spare

Date: 2026-05-02

Host/drive separation: spare drive on `jonathan-thinkpad-t480s`, optical target
`/dev/sg0`.

## Summary

This run turned the resident currentboot CDD mapped-source helper at code
`0x1717` into a practical read oracle.

The important workflow correction was:

1. Install a currentboot response hook through the normal full 544-event helper
   bypass sequence.
2. Cold power-cycle the drive/bridge.
3. Send only the profile-tail/event-1 entry step to land in currentboot.
4. Query the hook while currentboot is live.

If the hook is merely admitted and allowed to boot normal `LD5M`, the normal
firmware no longer reaches the currentboot response handler at `0x4fc9`.

## First Negative

Candidate:

```text
currentboot-response-hook-gateway-bulk-cdd-mapped-source-v1
```

The candidate image was admitted and the drive returned as normal `LD5M`, but a
special mapped-source CDB did not hit the hook. Response byte `0x20` was stock
`0x4c` (`"LD5M..."`) instead of marker `0xd5`.

The low-prefix hook/cave were restored afterward with `restore-4fc9-cave`, and a
sequential readback of `F0[0x0000..0x7000]` matched stock.

Files:

```text
install-result.json
restore-result.json
normal-after-install-special-cdb-response.bin
restore-check-f0-000000-007000.dec.bin
```

## Corrected Currentboot Workflow

Using the corrected workflow above, the fixed-header mapper returned the LD5M
CDD header at source address `0x702c`:

```text
43 44 44 09 10 16 53 0d 90 00 00 7d ec 03 08 10
87 0e 80 00 00 70 00 18 40 00 1b 3f ff 1b 3f ff
```

This proved the hook can safely call resident helper `0x1717` while the drive is
kept in currentboot.

Files:

```text
currentboot-v1-samples/
```

## Status64 Diagnostic

The next diagnostic build returned:

- marker `0xd6`;
- `xdata[0xc000..0xc01f]` at response bytes `0x21..0x40`;
- `xdata[0x4e80..0x4ebf]` at response bytes `0x41..0x80`.

The `0xc000` data stayed stale after the first header mapping, but the status
row changed cleanly with the requested source address. In particular,
`xdata[0x4e90..0x4e93]` reported:

```text
0x400000 + requested_address + 0x20
```

Examples:

```text
source 0x00702c -> status 0x40704c
source 0x028119 -> status 0x428139
source 0x0502fa -> status 0x45031a
source 0x184000 -> status 0x584020
```

This proved that arbitrary host-selected address bytes reach the resident
`0x1717` path. The missing piece was the correct output byte inside the mapped
window.

Files:

```text
currentboot-status64-v1-samples/
remote-logs/status64-*.json
```

## Window128 D7 Byte Oracle

The compact 128-byte window build returned marker `0xd7` and
`xdata[0xc000..0xc07f]`. The useful mapped byte is at `xdata[0xc07f]`; the
earlier part of the window remains mostly stale header/zero material.

The reader now has a byte-oracle mode:

```sh
python3 scripts/read_liteon_currentboot_cdd_mapped_source.py \
  --device /dev/sg0 \
  --address 0x28119 \
  --length 0x10 \
  --d7-c07f-byte-oracle \
  --out /tmp/rec59-byte-oracle-16.bin \
  --json-out /tmp/rec59-byte-oracle-16.json
```

The `0x28119` record-59 read matched stock LD5M exactly:

```text
d8 19 20 0a 7a dd 2a ad 9f 56 a3 49 38 51 aa cc
```

Local stock comparison:

```text
F0[0x28119..0x28128] = d819200a7add2aad9f56a3493851aacc
```

So this is now a byte-per-command CDD/source/controller-address oracle, not just
the old timing or one-bit helper channel.

Files:

```text
currentboot-window128-v2-samples/
currentboot-window128-v2-byte-oracle/
remote-logs/window128-v2-*.json
```

## Controller Address Samples

The same byte oracle can read nonzero bytes at controller-space addresses such
as `0x184000`, but the sampled bytes currently look high-entropy rather than
like flat decoded 8051 code:

```text
0x184000:
52 51 12 ff 26 66 3d c0 31 7f d4 94 d8 45 ff 52
2f f9 77 91 76 26 6b d7 b4 eb ed e6 be 24 b5 78
```

Additional 64-byte reads were captured at:

```text
0x184000
0x184060
0x191010
0x198900
0x199030
0x19c020
0x1a0000
0x1a2fe0
```

These are useful controller-address samples, but they should not yet be treated
as decoded CDD runtime code. A record-59 candidate flat decoded address
`0x18b170` also did not resemble the known normal-mode record-59 overlay.

Files:

```text
decoded-oracle-targets-v2/
currentboot-window128-v2-samples/decoded-rec59-candidate-18b170-0130.*
```

## Final Drive State

After the D7 run, the spare was recovered back to normal `LD5M`:

```text
/dev/sg0: PLDS DVD+-RW DS-8ABSH LD5M
```

Recovery log:

```text
remote-logs/window128-v2-recovery-result.json
```

## Practical Interpretation

- `0x1717` is safe enough to call from a currentboot response hook.
- Host-selected 24-bit address bytes reach that mapper.
- `xdata[0xc07f]` gives a reliable one-byte mapped output.
- CDD source bytes can now be read quickly from currentboot without mutating the
  CDD.
- The advertised `0x184000..0x1b3fff` controller range is readable in this
  path, but the bytes do not yet prove a decoded CDD image.

The sensible next use of this primitive is targeted read-only mapping: sample
record source spans, call-target owner records such as 5 and 137, and small
controller windows around the resident mailbox/status state. Do not use these
captures as proof of a flat CDD decoder until a live perturbation ties a specific
source byte to a specific readable decoded/controller byte.
