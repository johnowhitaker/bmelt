# Linux Drive #1 Servo Cold-Boot Persistence Map

Date: 2026-04-30.

Drive: Linux bench drive #1 on `jonathan-thinkpad-t480s`, active optical LUN
`/dev/sg0`, `PLDS DVD+-RW DS-8ABSH LD5M`.

Primitive: Pico `GP10` servo mechanically cuts the spliced USB `+5V` line for
about one second. Linux `dmesg` showed real USB disconnect/re-enumeration during
these tests, so this is stronger than SCSI reset, USB deauth/reauth, or host
reboot.

## Test 1: Resident INQUIRY Hook After True Power Loss

Candidate:

```text
references/firmware/extracted/resident-hook-candidates/
  resident-hook-inquiry-delay20/
    liteon-full-currentboot-ld5m-helper-bypass-resident-hook-inquiry-delay20-candidate.json
```

The helper-bypass write persisted the patch in F0:

```text
0x4ec6: 90 81 8b -> 02 6e e3
0x6ee3: ff...    -> 7f 20 7e ff 7d ff dd fd de fa df f6 90 81 8b 02 4e c9
diff_count in 0x0000..0x7000: 19
```

Timing control before the power cut:

```text
INQUIRY median 0.005337s, max 0.005638s
```

Timing after servo cold power cycle:

```text
INQUIRY median 0.005362s, max 0.005574s
```

Interpretation: the visible F0 prefix patch persists but is not the live normal
`INQUIRY` handler even after real `+5V` loss. The normal runtime path is either
using another code copy/overlay or the bridge/controller handles this path
without executing the visible F0 prefix function at `0x4ec6`.

The stock restore candidate then returned `0x0000..0x7000` to byte-identical
stock:

```text
diff_count: 0
0x4ec6: 90 81 8b ...
0x6ee3: ff ff ff ...
```

## Test 2: Identity/Profile Timestamp After True Power Loss

Candidate:

```text
references/firmware/extracted/helper-bypass-candidates/
  identity-date-3016-servo/
    liteon-full-currentboot-ld5m-helper-bypass-identity-date-3016-servo-candidate.json
```

Patch:

```text
0xd8ff4: 32 -> 33
text: LD5M2016/10/18 -> LD5M3016/10/18
```

Post-write F0 verification matched the patched target:

```text
post_decrypted_sha256: 51eb32a82aa78614e88e1fddd66c35abc54b545e54d7c8516cc849fd19c49bde
post_matches_expected_target: true
```

After a servo cold power cycle, live EXTRAINQ stayed canonical:

```text
revision:  LD5M
timestamp: 2016/10/18 14:18
```

But a direct F0 dump still showed the patched flash bytes:

```text
F0 0xd8fd0: ... PLDS    DVD+-RW DS-8ABSHLD5M3016/10/18 1CDD ...
F0 0xd8ff4: 0x33
```

Interpretation: the identity/profile copy at `0xd8fd0..0xd8fff` is writable
persistent F0 data, but it is not the normal runtime source for live EXTRAINQ.
The host-visible identity/timestamp is coming from another runtime/controller
source or a canonicalized copy loaded before this F0 region matters.

The restore candidate returned the byte to stock:

```text
0xd8ff4: 0x32
F0 text: LD5M2016/10/18
```

## Operational Note

For verification dumps in this phase, a fresh binary EXTRAINQ capture was more
reliable than feeding the older text reference log to the F0 dumper. If a small
window decrypt produces nonsense or a huge unexpected diff, capture live binary
EXTRAINQ first:

```sh
sg_raw -b --request=176 /dev/sg0 12 00 00 00 F0 40 00 00 00 00 00 00 > live-extrainq.bin
```

Then use `--extrainq live-extrainq.bin` for the relevant dump.

