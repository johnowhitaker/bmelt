# Boastermelt Next Session Handoff

Date: 2026-04-30.

This is the clean-slate handoff after the repo spring cleaning. The old
generated logs, Wine prefixes, packaged bundles, and git history were removed
from the active tree. The compact operating set is now in this repo.

## Read First

1. `docs/AI_FIELD_GUIDE.md`
2. `docs/JOURNAL.md`
3. `docs/helper-bypass-write-method.md`
4. `references/evidence/live/linux-drive1-codeexec-timing-poc.md`
5. `references/evidence/live/linux-drive1-helper-bit-channel.md`
6. `references/evidence/live/linux-drive1-helper-xdata-timing-channel.md`
7. `scripts/run_liteon_linux_persistence_experiment.py`
8. `scripts/build_liteon_helper_bypass_candidate.py`
9. `scripts/build_liteon_helper_codeexec_candidate.py`
10. `scripts/read_liteon_xdata_bit_channel.py`
11. `scripts/read_liteon_xdata_timing_channel.py`
12. `scripts/recover_liteon_currentboot_linux.py`
13. `scripts/recover_liteon_blank_currentboot_linux.py`
14. `scripts/dump_liteon_linux_f0_window.py`
15. `references/evidence/live/normal-mode-readonly/linux-drive1-standard-only-probe.md`
16. `analysis/8051/normal-mode-response-surface-analysis.md`

## Hardware State

- Linux host: `jonathan-thinkpad-t480s`
- Remote repo: `/home/jonathan/boastermelt`
- SSH as `root` works.
- Rediscover the sg device before live work; the optical LUN moves between
  `/dev/sg0` and `/dev/sg1`.
- After cleanup, sysfs still showed `/dev/sg1` rev `0D5C`, but `sg_inq`
  reported `LD5M`; trust the active SCSI INQUIRY over stale sysfs text.
- Current live state after the blank-currentboot recovery: Linux drive #1 is
  visible as the optical PLDS LUN and cold-boots as `LD5M`.

```text
PLDS / DVD+-RW DS-8ABSH / LD5M
```

Current caveat: this used to carry the deliberate
`currentboot-response-hook-gateway-cdb-bulk` patch, but the later normal-mode
hook test phase restored the visible prefix/cave area. The post-restore
live-key F0 dump of `0x1000..0x6fff` matched stock LD5M with zero diffs.

```text
0x4fc9..0x4fcb = 12 62 06
0x6ee3..       = ff...
```

Reinstall a currentboot response hook before using the bulk gateway/XDATA
readout scripts that depend on `0x4fc9 -> 0x6ee3`.

Rediscover:

```sh
python3 scripts/liteon_linux_status.py
```

Power-cycle the bench drive/bridge from the Mac and wait for the Linux optical
LUN:

```sh
python3 scripts/pico_power_cycle_linux_drive.py
```

For a longer raw servo cut without waiting for `LD5M`:

```sh
python3 pico/client.py --port /dev/cu.usbmodem2101 --timeout 35 "TOGGLE SERVO 30000"
```

## Current Capabilities

Live-proven:

- dump/decrypt F0 through Linux `READ BUFFER id=F0`;
- recover known `0D5C` currentboot back to `LD5M`;
- recover the newer blank-currentboot dialect back to `LD5M`;
- persist selected F0 bytes with the helper-status bypass;
- execute patched helper-overlay code and observe host-visible timing;
- read selected XDATA bits through event-68 GOOD vs DID_ERROR;
- read selected XDATA bits through a safer GOOD/GOOD timing channel.

Still unsolved:

- the real `0xe7fe0` container seal/auth algorithm;
- a fast/general host data-return channel from helper code;
- stable normal-mode persistent F0 resident hooks.

## Normal-Mode Read-Only Surface

A standard-only normal LD5M survey ran on Linux drive #1 with no data-out or
mechanics commands. Fast host-visible channels with no disc inserted:

```text
INQUIRY standard       96 bytes, ~7 ms
EXTRAINQ              176 bytes, ~9 ms
MODE SENSE(10)        224 bytes, ~9 ms
GET CONFIGURATION     60/252 bytes, ~8-14 ms
GET EVENT STATUS      8 bytes, ~10 ms
MECHANISM STATUS      8 bytes, ~8 ms
```

Avoid using these as casual probes:

- normal-mode `READ BUFFER id=02`: hung the optical LUN once and needed a Pico
  servo power-cycle;
- `GET PERFORMANCE`: returned `DID_TIME_OUT` after about ten seconds.

Scripts/artifacts:

```text
scripts/probe_liteon_normal_mode_readonly.py
scripts/analyze_liteon_normal_mode_responses.py
references/evidence/live/normal-mode-readonly/linux-drive1-standard-only-probe.json
references/evidence/live/normal-mode-readonly/linux-drive1-standard-only-probe.md
analysis/8051/normal-mode-response-surface-analysis.md
```

The exact-match analysis shows normal `INQUIRY`/`EXTRAINQ` data overlaps both
visible F0 identity copies (`0x04452` and `0xd8fd0`). Do not overread that:
live edits to the visible F0 identity/profile copy persisted across a true
cold boot but did not alter normal EXTRAINQ. This is a source-localization clue,
not a solved resident hook.

Currentboot XDATA `0x811e` has the same shape: it contains the model string and
is writable/readable through the guarded XDATA hook, but changing it to `X` did
not alter the next currentboot identity model field. It only changed the
deliberate hook readback byte. Treat it as metadata, not the live source.

Follow-up timing hooks tested the broad visible command path directly:

```text
0x6206 response-copy helper -> persisted, no normal-mode timing effect
0x542b packet-intake helper -> persisted, no normal-mode timing effect
```

The `0x6206` hook did slow the next currentboot update run, proving the hook was
real and live in currentboot. The negative is specific to normal LD5M command
handling. After the tests, stock restore rewrote `0x1ea0`, `0x542b`, `0x6206`,
and `0x6ee3..`, and a live-key F0 dump of `0x1000..0x6fff` had zero diffs
against stock.

Evidence:

```text
references/evidence/live/normal-mode-hook-tests/normal-mode-hook-tests-summary.md
references/evidence/live/xdata-source-localizer/currentboot-xdata-811e-source-test.md
```

Blank-currentboot details:

- standard INQUIRY and EXTRAINQ keep PLDS/model but return blank/garbage
  revision and no normal `EXTRAINQ` marker;
- known `0D5C` recovery profile tail rejects with `Parameter value invalid`;
- normal event-1 pre-tail also rejects;
- `arg=00` chunks still stage and read back;
- the profile-tail key is still recoverable from malformed EXTRAINQ bytes
  `0x9c..0xab`, and must be regenerated dynamically at bank boundaries.

Recovery:

```sh
python3 scripts/recover_liteon_blank_currentboot_linux.py --device /dev/sg0
```

Evidence:

```text
references/evidence/live/linux-drive1-blank-currentboot-after-led-probe.md
```

Important 2026-04-30 update: true servo-driven `+5V` power loss did not make
the persisted F0 `INQUIRY` hook at `0x4ec6` live. Direct F0 readback showed the
patch, dmesg showed real disconnect/re-enumeration, but command timing stayed
baseline. A patched identity/profile timestamp at `0xd8ff4` also persisted in
F0 across cold boot while live EXTRAINQ stayed canonical. See:

```text
references/evidence/live/linux-drive1-servo-coldboot-persistence-map.md
```

Follow-up: patching the lower `0D5C2011` identity record at `0x4476` to `3011`
did affect currentboot EXTRAINQ after power loss and event 1. The restore write
and restore-verification run both completed: currentboot EXTRAINQ returned to
`2011/04/28`, then auto-recovery returned to `LD5M`.

## Practical Write Method

The helper-bypass write method patches the mutable `ef130045` profile-tail
helper body. The essential status bypass is:

```text
helper plain 0x02b5 / code 0x32af:
30 e6 12 -> 02 32 c4
```

Build example:

```sh
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name example-d8ff4 \
  --patch 0xd8ff4:33 \
  --include-pre-tail
```

For sectors below `0x7000`, add `--auto-helper-range` only when deliberately
touching that lower range.

Run shape:

```sh
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/helper-bypass-candidates/example-d8ff4/liteon-full-currentboot-ld5m-helper-bypass-example-d8ff4-candidate.json \
  --device /dev/sg1 \
  --skip-pre-f0 \
  --end-index 544 \
  --f0-size 0xe0000 \
  --capture-finalizer-status-after-event 1 \
  --capture-finalizer-status \
  --recover-on-currentboot
```

## Code-Execution Foothold

The current proof hooks the late helper status branch:

```text
helper plain 0x02b5 / code 0x32af:
30 e6 12 -> 02 36 1a
```

Payloads at helper code `0x361a` run a finite delay and `LJMP 0x32c4`.

Observed event-68 timings:

```text
baseline:   0.255830s
delay 0x20: 0.849545s
delay 0x80: 2.638886s
```

Event `34` and event `35` stayed flat, and auto-recovery restored `LD5M`.

Evidence:

```text
references/evidence/live/linux-drive1-codeexec-timing-poc.md
```

## XDATA Bit Channel

The same late hook can now return one bit without timing. Payload code chooses:

```text
LJMP 0x32c4  -> event 68 GOOD
LJMP 0x32b2  -> event 68 DID_ERROR, then auto-recovery restores LD5M
```

`MOVX A,@DPTR` can feed that decision. The first byte read was:

```text
xdata[0x48a0] at event 68 = 0xa0
```

Follow-up selected reads:

```text
xdata[0x47d2] = 0xff
xdata[0x48a5] = 0xff
xdata[0x8221] = 0xff
```

Evidence:

```text
references/evidence/live/linux-drive1-helper-bit-channel.md
references/evidence/live/linux-drive1-helper-xdata-48a0-summary.json
references/evidence/live/linux-drive1-helper-xdata-selected-summary.json
```

Read another byte:

```sh
python3 scripts/read_liteon_xdata_bit_channel.py \
  --device /dev/sg1 \
  --addr 0x48a0 \
  --out-dir runs/helper-xdata-bit-channel \
  --retry-attempts 2 \
  --between-delay 4
```

This is intentionally slow. It is suitable for selected registers, not bulk
memory dumps.

## XDATA Timing Channel

The GOOD/DID_ERROR channel is no longer the preferred first choice for unknown
controller registers. Claude's overnight sweep hit `xdata[0x4704].0 = 0` and
then recovery wedged until physical replug. The safer channel always returns
GOOD and encodes the bit in event-68 latency.

Use payload offset `0x04f6` for conditional timing payloads; the old
`0x0620` `Flash Type Error` string slot is too short for the 20-byte predicate.

Live calibration:

```text
no delay: 0.255969s
delay 0x20: 0.853324s
threshold: 0.554646s
```

Confirmed:

```text
xdata[0x4704] at event 68 = 0x00
xdata[0x4708] at event 68 = 0x90
xdata[0x4709] at event 68 = 0x00
xdata[0x470a] at event 68 = 0x64
xdata[0x470b] at event 68 = 0x06
```

Read shape:

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --addr 0x4704 \
  --calibrate \
  --payload-offset 0x04f6 \
  --between-delay 3
```

Evidence:

```text
references/evidence/live/linux-drive1-helper-xdata-timing-channel.md
```

## Good Next Step

The live drive is back in a known state: `LD5M`, with the currentboot gateway
bulk response hook still installed. Decide deliberately whether to keep that
hook for currentboot reads or restore stock bytes with the
`currentboot-response-hook-restore-4fc9-cave` candidate before more LED probes.

For the normal-runtime foothold, do not spend the next live run on another
blind visible-F0 prefix hook. That class now includes the command-specific
`0x4ec6`/`0x5c72` hooks and the broader `0x6206`/`0x542b` hooks. Better next
tests:

1. a currentboot-to-LD5M state-carryover marker test, if the right XDATA/write
   response hook is installed or can be safely reinstalled;
2. static/source localization for the fast normal-mode response channels above;
3. decoded-runtime/CDD work if the real normal handlers live outside the
   visible F0 prefix.

Latest gateway map: the originally guessed decoded CDD window
`controller[0x184000..0x1b4000]` is still all zero in currentboot, but a sparse
gateway sweep found a much more useful live region at
`controller[0x070000..0x07ffff]`, mirrored at `0x170000..0x17ffff`. The first
full dump is tracked:

```text
references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin
sha256 5f517adeab1647dbedf7b93f8be097b1641164fd49e87776364b9e134b9cbc0b
```

Offline analysis is in:

```text
analysis/8051/currentboot-gateway-070000-analysis.md
analysis/8051/currentboot-gateway-070000-analysis.json
analysis/8051/servo-mechanics-static-notes.md
```

Important nuance: the `0x070000` dump is mixed currentboot controller/work
memory, not the decoded CDD image. Its tail contains exact sealed CDD bytes:
gateway `+0xf000` mirrors F0 `0x704c..0x7deb`, gateway `+0xfc20` mirrors the
known CDD2 duplicate prefix at F0 `0xd9020`, and `+0xff00/+0xff80` repeat the
CDD header. It also contains profile/calibration strings and 8051-like code
fragments, including exact overlaps with the resident/helper code.

For the sled/focus/laser side quest, focus statically on the `0x59xx`/`0x5axx`
cluster before any live mechanics poke. The LD5M routine at F0 `0x59f3` appears
at gateway offset `0x6059`; related gateway routines around `0x642c`, `0x6fe0`,
and `0x8278` manipulate the same cluster. This is likely a servo/mechanics
command area, not an LED latch.

Reinstall the bulk currentboot response hook if fast currentboot reads are
needed, then use it alongside the timing XDATA channel to map a short list of
high-value registers before adding hardware. Use the older GOOD/DID_ERROR
channel only when the value is already known not to drive a messy recovery path.

- nearby handoff/status bytes around `0x48a0`;
- controller/finalizer state bytes already seen statically, such as `0x47d2`
  and `0x8221`;
- candidate GPIO/front-panel registers before wiring the Pico into an active
  feedback loop.

If this becomes too slow or cannot see the needed state, use the Pico
front-panel wiring for a faster LED/button channel. Avoid helper-entry
trampolines; those wedged at event `68`.

## Check

```sh
make check
```

At cleanup time, `make check` passed.

## Latest Normal-Mode Mechanics State

START STOP UNIT eject is now confirmed as a real normal-runtime mechanics
trigger. See:

```text
analysis/8051/normal-start-stop-mechanics-path-20260501.md
analysis/8051/normal-start-stop-eject-live-20260501.md
analysis/8051/normal-start-stop-variant-matrix-20260501.md
analysis/8051/normal-start-stop-hook-plan-20260501.md
```

The live matrix is clean: only `1B 00 00 00 02 00` caused visible motion and
temporary `READ BUFFER id=01` timeouts. The `0x00`, `0x01`, and `0x03` variants
returned quick CHECK status with no work-window trouble.

Important next-step constraint: do not build a hook that depends on an
immediate SCSI read during eject. The drive is legitimately busy for several
seconds. Better plan: capture state into scratch, let/suppress the mechanism
path, then expose the stored bytes through a later stable command.

Also do not assume the `+0x8bxx` work-window offset is patchable in the visible
F0 prefix. Prior F0 resident hooks persisted but did not alter normal command
timing, and the START STOP snippet itself does not line up cleanly with visible
prefix disassembly. First find a live, patchable normal response path.

Latest offline localization:

```text
analysis/8051/normal-work-window-reference-localization-20260501.md
analysis/8051/normal-currentboot-work-window-overlap-20260501.md
analysis/8051/normal-work-window-extended-reference-matches-20260501.md/json
```

High-level result: the normal work-window barely matches visible F0
(`63/908` chunks), the visible 8051 prefix (`8/908`), or currentboot XDATA
(`2/908`), and not the helper at all. It does substantially overlap the
currentboot gateway `0x070000` dump (`510/908` chunks). Normal `id01/id02`
snapshots match 693 chunks each and are near-aliases. The START STOP `+0x8bxx`
branch is still not localized to a known patchable image. Shared
currentboot/normal pages are strongest at `+0xa000..+0xde80`,
`+0xe000..+0xfd80`, and `+0x4000..+0x4500`; use those as the first candidates
if testing any currentboot-to-normal controller-memory patch carryover. The
guarded currentboot XDATA writer is probably not enough by itself.

## Currentboot Gateway Write Primitive

New files:

```text
analysis/8051/currentboot-gateway-write-hook-plan-20260501.md
analysis/8051/currentboot-gateway-rw-live-20260501.md
scripts/write_liteon_currentboot_gateway.py
scripts/write_liteon_currentboot_gateway_blob.py
```

`scripts/build_liteon_currentboot_response_hook_candidate.py` now has
`--gateway-cdb-rw`. It is a one-byte controller gateway reader by default. If
host `CDB[10]` is `5a`, it writes `CDB[11]` through `0x4095..0x4098`, reads the
same controller address back through `0x4091..0x4098`, and returns the readback
byte at response offset `0x20`.

Use the v2 artifact name. v1 also checked `CDB[6] == a6`; it installed cleanly
and the read side returned `Flash Type Error` from `0x018620`, but the write
branch did not fire. Treat that as another confirmation that CDB byte 6 is not
a safe parameter byte in this handler.

Build with the larger proven FF cave:

```sh
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name gateway-cdb-rw-v2 \
  --gateway-cdb-rw \
  --cave-len 0xdd
```

The dry-run payload is `0xc0` bytes, so the old `0x80` cave default is too
small. The `0x6ee3` cave is all-FF through `0x6fbf`, so `0xdd` bytes is still
below `0x6ff0`.

Live smoke test passed:

```sh
# read first to confirm "Flash Type Error"
python3 scripts/read_liteon_currentboot_gateway.py --device /dev/sg0 \
  --address 0x018620 --length 0x10

# write F -> G, read back, then restore G -> F
python3 scripts/write_liteon_currentboot_gateway.py --device /dev/sg0 \
  --address 0x018620 --value 0x47
python3 scripts/write_liteon_currentboot_gateway.py --device /dev/sg0 \
  --address 0x018620 --value 0x46
```

The v2 write changed `Flash Type Error` to `Glash Type Error` and restored it.
The blob writer repeated the same proof for the five-byte prefix. A harmless
marker at controller `0x074030` also wrote/read in currentboot, but did not
survive either bare `PLDSVUC` or the known full recovery path into normal mode.
So this is a currentboot volatile controller-memory write primitive, not a
trivial normal-runtime patch primitive. The Linux persistence runner can now
inject these writes mid-sequence with `--gateway-patch-after-event` and
`--gateway-patch-after-phase`; the event-1 smoke test patched `Flash` to
`Glash` immediately after profile-tail entry and read it back successfully.

## Latest GET CONFIG Normal-Bridge Probe

New helper:

```text
scripts/capture_liteon_normal_get_config_field_variants.py
```

It varies reserved GET CONFIGURATION CDB bytes while capturing
`READ BUFFER id=01 offset=0x070000` work-window snapshots. Evidence:

```text
references/evidence/live/normal-work-window-get-config-field-variants-20260501/
references/evidence/live/normal-work-window-get-config-field-variants-r5-long-20260501/
references/evidence/live/normal-work-window-get-config-r5-01-isolated-20260501/
references/evidence/live/normal-work-window-get-config-r5-f0-isolated-20260501/

analysis/8051/normal-get-config-field-variant-findings-20260501.md
analysis/8051/normal-work-window-get-config-field-variants-20260501.md/json
analysis/8051/normal-work-window-get-config-field-variants-r5-long-20260501.md/json
analysis/8051/normal-work-window-get-config-r5-isolated-20260501.md/json
```

Result: all reserved-field variants returned GOOD and the drive stayed normal
`LD5M`. Host-visible GET CONFIG responses did not change. The familiar
`0x4091/0x4093/0x4099` bridge chunks recur, but the longer isolated runs do not
prove that CDB byte 5 steers the bridge; public-window rotation is still a big
confounder. Treat this as a useful negative: GET CONFIG is safe for tagging the
normal bridge, but reserved GET CONFIG bytes are not the fast normal runtime
read oracle by themselves.

Follow-up correction:

```text
analysis/8051/normal-read-buffer-capture-bridge-correction-20260501.md
```

The strongest `0x8a4c..0x8a4e -> 0x4011..0x4013` bridge edge now looks like
the follow-up `READ BUFFER` capture command's own 24-bit offset path. In a
READ BUFFER CDB, bytes 3..5 are the buffer offset, exactly matching those
shadow bytes. So do not treat the GET CONFIG field run as evidence for a hidden
GET CONFIG address register. The stock normal READ BUFFER oracle is real and
controlled, but it is the already-mapped public work-window/mirror surface; it
does not reach decoded CDD memory.

## Latest READ BUFFER And GET PERFORMANCE Findings

New helper:

```text
scripts/scan_liteon_read_buffer_modes.py
```

Evidence and summary:

```text
references/evidence/live/normal-read-buffer-mode-byte-scan-20260501/
analysis/8051/normal-read-buffer-high-mode-and-get-performance-harvest-20260501.md
```

This scans READ BUFFER CDB byte 1 as an unrestricted 8-bit value. A smoke pass
over representative high values and a full pass over `0x20..0xff` against IDs
`0x01`, `0x02`, `0xe2`, `0xf0`, `0xf1`, and `0xf2` found no hidden selector.
All 1344 full-pass requests returned `rc=5` with no data, no partial responses,
and no timeouts. So the easy "high mode bit means different window" idea is
closed for now.

New helper:

```text
scripts/capture_liteon_normal_get_performance_variants.py
```

Evidence and reports:

```text
references/evidence/live/normal-work-window-get-performance-variants-20260501/
references/evidence/live/normal-work-window-get-performance-variants-long-20260501/
analysis/8051/normal-work-window-get-performance-variants-20260501.md
analysis/8051/normal-work-window-get-performance-variants-long-20260501.md
```

This sends read-only GET PERFORMANCE variants, then captures the public normal
work window with `READ BUFFER mode=1 id=01 offset=0x070000 length=0x10000`.
The first pass added 77 new chunks to the normal runtime corpus. The longer
repeat added zero new chunks, so this command family is likely saturated for
the current capture method.

Updated combined reports:

```text
analysis/8051/normal-work-window-chunk-corpus-20260501.md
analysis/8051/normal-work-window-overlay-map-20260501.md
analysis/8051/normal-work-window-dptr-refs-20260501.md
```

Current corpus shape:

```text
6 runs
208 captures
862 unique informative chunks
63 static-matched chunks
799 runtime/unmatched chunks
262 chunks seen at multiple public slots
```

Caution: the strongest GET PERFORMANCE-only recurring tile at `+0x8bxx`
references `0x8a49` and `0x8a4d`, but its checks match the known START STOP
eject branch (`0x8a49 == 0x1b`, `(0x8a4d & 0x0f) == 0x02`). Treat this as an
overlay tile surfaced by the capture sequence, not as GET PERFORMANCE command
semantics.

Recommended next directions:

- Offline stitch the harvested `0x8a49..0x8a54` packet-shadow/runtime chunks.
- Try another harmless command family for tile harvesting instead of looping
  GET PERFORMANCE again.
- Continue normal-mode patchability work so the public READ BUFFER machinery
  can be redirected rather than merely sampled.

## Latest Packet-Shadow Offline Stitching

New all-runs reports:

```text
analysis/8051/normal-packet-shadow-all-runs-findings-20260501.md
analysis/8051/normal-packet-shadow-all-runs-20260501.md/json
analysis/8051/normal-packet-selector-map-all-runs-20260501.md/json
```

Also generated six-directory corpus-specific reports:

```text
analysis/8051/normal-packet-shadow-full-corpus-20260501.md/json
analysis/8051/normal-packet-selector-map-full-corpus-20260501.md/json
```

The all-runs scan covers 19 normal work-window dirs and 509 captures. It
confirms:

```text
0x47b1 -> 0x8a4a..0x8a54 packet/FIFO intake
0x8a49 is still the opcode-like selector
0x8a4d/0x8a4e/0x8a53/0x8a54 are reused later as controller/status scratch
```

GET CONFIG now has a cleaner local shape:

```text
0x4099 -> 0x8a4d/0x8a4e/0x8a53/0x8a54
0x8a4d == 0xfe
0x8a4c/0x8a4d/0x8a4e -> 0x4011/0x4012/0x4013
```

The `0x4099 -> shadow` burst plus `0x8a4d == 0xfe` appears 39 times and only
in GET CONFIG-oriented dirs. The generic `0x8a4c..0x8a4e -> 0x4011..0x4013`
bridge appears everywhere and should be treated as public READ BUFFER response
plumbing.

Practical interpretation: GET CONFIG likely has a controller-backed feature
list/response builder with an internal `0xfe` sentinel. It is a better
normal-runtime island to reverse, but it is still not an arbitrary memory
oracle by itself.

Static islands worth stitching next:

```text
+0x70c0/+0x7100/+0x7140/+0x7180   read-side / 4011..4013 / 4099 path
+0x7480/+0x74c0                   4099 burst command
+0x7600/+0x7640                   4091..4093 setup and 409c kicks
+0xdbc0/+0xdc00/+0xdc40           4095..4097 save/restore/FIFO writer
```
