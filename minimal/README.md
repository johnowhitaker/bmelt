# Boastermelt Minimal Walkthrough

This is the short version of the LiteOn/PLDS `DS-8ABSH` firmware adventure:
enough to plug in a drive, dump its firmware, understand the key trick, and try
small experiments without reading the whole project archive first.

It is written for the current repo layout. The actual tools still live in
`scripts/` and the reference material still lives under `references/`; this
directory is the map, not a second copy of the repo.

## The Shape Of The Story

These drives speak normal SCSI/MMC commands, plus a handful of vendor-flavored
commands used by the official updater. The first win was realizing that Linux
`sg_raw` can talk to those commands directly, without fighting macOS or a USB
storage stack that hides too much.

The second win was `EXTRAINQ`. It looks like a weird extended inquiry response,
but it contains the AES material needed to decrypt the drive's `READ BUFFER id
F0` firmware window. With that, a "blank black box" became a 1 MiB firmware
image we could diff, patch, and disassemble.

The big wall is still the CDD/container seal. The drive can stage modified F0
bytes and read them back, but the finalizer rejects arbitrary changed firmware
unless the image still satisfies a controller-side validation rule. We have not
cracked that rule.

The trick that *did* work was sneakier: keep the staged F0 container valid, but
mutate the updater's temporary flash helper overlay. That helper runs during
the update path and performs the flash programming. By patching the helper
rather than forging the unknown seal, we got controlled persistent writes and
then currentboot code execution.

## Hardware And Linux Setup

Use Linux with SCSI generic access. Direct SATA is ideal; a bridge can work if
it passes `sg_raw` commands cleanly.

Install the basics:

```sh
sudo apt-get update
sudo apt-get install -y sg3-utils python3 python3-pip
python3 -m pip install --user cryptography
```

If you are using the Pico servo power-cycle setup from this project, the Linux
side usually sees it as `/dev/ttyACM0`. It is convenient, but the firmware
walkthrough below only needs the optical drive.

All commands below assume you are at the repo root on the Linux machine:

```sh
cd /home/jonathan/boastermelt
```

Adjust that path for your own clone.

## 1. See The Drive

First find the SCSI generic node:

```sh
sg_map -i
python3 scripts/liteon_linux_status.py
```

A healthy target looks like this:

```text
/dev/sg0  /dev/sr0  PLDS      DVD+-RW DS-8ABSH  LD5M
```

Set a shell variable so the rest of the commands are copy-pasteable:

```sh
export DRIVE=/dev/sg0
```

Then check standard inquiry:

```sh
sg_inq "$DRIVE"
```

Expected identity:

```text
PLDS DVD+-RW DS-8ABSH LD5M
```

If the revision is `0D5C`, the drive is in currentboot/recovery personality.
That state is often recoverable on Linux, but it is not the normal starting
point.

## 2. Read EXTRAINQ

The useful extended inquiry CDB is:

```text
12 00 00 00 f0 40 00 00 00 00 00 00
```

The allocation byte says `0xf0`, but this drive normally returns `0xb0` bytes.
Ask `sg_raw` for `176`, not `240`, so the short-but-good transfer is accepted:

```sh
mkdir -p runs/minimal

sg_raw --cmdset=1 -b --request 176 --timeout 3 \
  "$DRIVE" 12 00 00 00 f0 40 00 00 00 00 00 00 \
  > runs/minimal/extrainq.bin
```

Parse it:

```sh
python3 scripts/parse_liteon_extrainq.py runs/minimal/extrainq.bin
```

The important fields are:

```text
InitVec=...
SecKey=...
marker='EXTRAINQ'
primary_selector_value=...
```

That IV/key pair is the door into the encrypted F0 firmware window.

## 3. Dump And Decrypt Firmware

F0 readback is encrypted. The reliable path is:

1. read or prime EXTRAINQ;
2. read `READ BUFFER mode=1 id=F0` in exact `0x80` chunks;
3. AES-CBC decrypt with the EXTRAINQ IV/key, resetting the CBC stream every
   `0x80` bytes.

The repo tool does this for you:

```sh
python3 scripts/dump_liteon_linux_f0_window.py \
  --device "$DRIVE" \
  --extrainq runs/minimal/extrainq.bin \
  --prime-extrainq \
  --prime-extrainq-out runs/minimal/extrainq-live.bin \
  --start 0 \
  --size 0x100000 \
  --chunk 0x80 \
  --out runs/minimal/f0-decrypted.bin \
  --raw-out runs/minimal/f0-raw-encrypted.bin
```

For a stock LD5M drive, compare against the checked-in reference:

```sh
sha256sum runs/minimal/f0-decrypted.bin \
  references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin
```

The decrypted 1 MiB image has the useful high-level layout:

```text
0x00000..0x06fff   visible 8051/currentboot-ish code and tables
0x07000..0x0702b   descriptor
0x0702c..0xcec17   CDD stream 1, encoded controller payload
0xcec18..0xd8fcf   erased gap, still validation-covered
0xd8fd0..0xd8fff   identity/profile area
0xd9000..0xe6400   CDD stream 2, encoded controller payload
0xe6401..0xe7fdf   erased gap, still validation-covered
0xe7fe0..0xe7fed   14-byte auth/seal-looking field
0xe7ff5..0xe7fff   DU8A6S / LITE marker
0xe8000..0xfffff   final erased tail, apparently outside the admitted object
```

## 4. Persistent Writes With The Helper Bypass

Naively editing F0 does not work: the drive stages the bytes, but the finalizer
rejects the modified container.

The helper bypass avoids that finalizer decision. The rough idea is:

1. build a normal full-currentboot update candidate;
2. keep the staged F0 image LD5M-shaped;
3. patch the temporary profile-tail flash helper overlay;
4. let the helper's normal flash erase/program path write the target bytes.

The essential helper patch is:

```text
helper plaintext 0x02b5: 30 e6 12 -> 02 32 c4
```

The builder applies that helper patch automatically.

### A Safe-ish Persistent Byte Demo

This changes one byte in the identity/profile area:

```sh
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name minimal-date-byte-3016 \
  --patch 0xd8ff4:33 \
  --include-pre-tail
```

Run it on Linux:

```sh
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/helper-bypass-candidates/minimal-date-byte-3016/liteon-full-currentboot-ld5m-helper-bypass-minimal-date-byte-3016-candidate.json \
  --device "$DRIVE" \
  --skip-pre-f0 \
  --end-index 544 \
  --f0-size 0xe0000 \
  --capture-finalizer-status-after-event 1 \
  --capture-finalizer-status \
  --recover-on-currentboot
```

Then power-cycle and dump F0 again. The byte should persist in flash:

```sh
python3 scripts/dump_liteon_linux_f0_window.py \
  --device "$DRIVE" \
  --extrainq runs/minimal/extrainq.bin \
  --prime-extrainq \
  --start 0 \
  --size 0x100000 \
  --chunk 0x80 \
  --out runs/minimal/f0-after-date-byte.bin

xxd -g1 -s 0xd8ff0 -l 0x20 runs/minimal/f0-after-date-byte.bin
```

Restore candidate:

```sh
python3 scripts/build_liteon_helper_bypass_candidate.py \
  --name minimal-date-byte-2016-restore \
  --patch 0xd8ff4:32 \
  --include-pre-tail
```

Run it with the same `run_liteon_linux_persistence_experiment.py` command,
changing only the `--candidate` path.

This is not exciting as a user-visible change; normal EXTRAINQ still reports
canonical identity text. It is exciting because it proves persistent flash
editing without solving the 14-byte seal.

## 5. Helper Code Execution: A Timing Tweak

The flash helper is not only patchable; it executes. The first clean proof was
almost comically primitive: insert a delay loop and watch one updater event get
slower.

Build a currentboot helper candidate that delays the late helper path:

```sh
python3 scripts/build_liteon_helper_codeexec_candidate.py \
  --name minimal-delay20 \
  delay-only \
  --payload-offset 0x0620 \
  --delay-count 0x20
```

Run only through the interesting helper event:

```sh
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/helper-codeexec-candidates/minimal-delay20/liteon-full-currentboot-ld5m-helper-codeexec-minimal-delay20-candidate.json \
  --device "$DRIVE" \
  --skip-pre-f0 \
  --skip-post-f0 \
  --end-index 68 \
  --recover-on-currentboot
```

In the original proof, event 68 moved from roughly `0.25s` to roughly `0.85s`.
That timing bump is the drive saying: "yes, your helper overlay code ran."

The payload shape is just 8051 delay-loop code:

```asm
mov r7,#N
outer:
  mov r6,#0xff
middle:
  mov r5,#0xff
inner:
  djnz r5,inner
  djnz r6,middle
  djnz r7,outer
ljmp 0x32c4      ; return to normal helper success path
```

That timing channel later became a painfully slow bit reader for selected
XDATA/controller bytes. It was useful, but slow enough that the next hook was
much more satisfying.

## 6. Currentboot Identity Response Hook

Currentboot has an identity handler for INQUIRY/EXTRAINQ. We found a tiny hook
point:

```text
0x4fc9: 12 62 06   ; LCALL stock response copy
```

Patch it to:

```text
0x4fc9: 02 6e e3   ; LJMP into an FF cave
```

The cave payload writes bytes into the response staging buffer, calls the
original response-copy routine, and returns. This is the point where the project
stopped being "watch a timing delay" and started being "ask the drive for
bytes."

Build a simple controller-gateway bulk reader:

```sh
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name minimal-gateway-bulk \
  --gateway-cdb-bulk
```

That creates a helper-bypass candidate here:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-minimal-gateway-bulk/currentboot-response-hook-minimal-gateway-bulk/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-minimal-gateway-bulk-candidate.json
```

Install it:

```sh
python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-minimal-gateway-bulk/currentboot-response-hook-minimal-gateway-bulk/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-minimal-gateway-bulk-candidate.json \
  --device "$DRIVE" \
  --skip-pre-f0 \
  --skip-post-f0 \
  --end-index 544 \
  --f0-size 0xe0000 \
  --recover-on-currentboot
```

Cold-cycle, then enter currentboot by replaying only event 1 from the stock
base candidate:

```sh
# If the Pico servo is attached to the Linux host:
python3 pico/client.py --port /dev/ttyACM0 --timeout 8 "TOGGLE SERVO 3000"
sleep 8

python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/liteon-full-currentboot-ld5m-base-candidate.json \
  --device "$DRIVE" \
  --skip-pre-f0 \
  --skip-post-f0 \
  --end-index 1 \
  --out-dir runs/minimal/event1-currentboot-no-recover
```

Now read through the installed hook. This example asks the controller gateway
for bytes at `0x018620`:

```sh
python3 scripts/read_liteon_currentboot_gateway_bulk.py \
  --device "$DRIVE" \
  --address 0x018620 \
  --length 64 \
  --out runs/minimal/gateway-018620.bin \
  --json-out runs/minimal/gateway-018620.json

xxd -g1 runs/minimal/gateway-018620.bin
```

The known settled output includes:

```text
Flash Type Error
```

That is a small string, but it was a large moment: the host sent a custom-ish
INQUIRY CDB, our patched currentboot handler ran, the 8051 read controller
gateway memory, and the bytes came back in the SCSI response.

To return the low currentboot hook area to stock, build and run a restore
candidate:

```sh
python3 scripts/build_liteon_currentboot_response_hook_candidate.py \
  --name minimal-gateway-bulk-restore \
  --restore

python3 scripts/run_liteon_linux_persistence_experiment.py \
  --candidate references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-minimal-gateway-bulk-restore/currentboot-response-hook-minimal-gateway-bulk-restore/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-minimal-gateway-bulk-restore-candidate.json \
  --device "$DRIVE" \
  --skip-pre-f0 \
  --skip-post-f0 \
  --end-index 544 \
  --f0-size 0xe0000 \
  --recover-on-currentboot
```

## 7. Recovery Notes

If a run leaves the drive in the `0D5C` currentboot personality, Linux recovery
is usually:

```sh
python3 scripts/recover_liteon_currentboot_linux.py \
  --device "$DRIVE"
```

The generic runner can also recover automatically when a candidate ends in
currentboot:

```sh
--recover-on-currentboot
```

The standard recovery path rewrites stock LD5M and wipes installed currentboot
response hooks. Reinstall a hook before using hook-dependent readout tools.

Use fresh `sg_map -i` / `liteon_linux_status.py` checks after every recovery or
power cycle. The Linux device node can move.

## 8. The CDD Blocker In One Page

The remaining lock is not the SCSI transport. The official update packet
sequence is well-modeled. Chunks stage and read back. The final selector-15
event triggers a controller-side finalizer. Byte-identical LD5M passes;
arbitrary F0 edits inside `0x00000..0xe7fff` fail.

Visible suspicious fields:

```text
0x06ff0..0x06ff3     pre-family word
0xe7fe0..0xe7fed     14-byte trailer seal/auth field
```

We tested the obvious checksum/hash/CMAC ideas and did not find a way to
recompute the trailer. We also found no Coastermelt-style "set signature table
length to zero" bypass in the visible headers.

The CDD streams are the deeper mystery. They are not plain code. They look like
structured, controller-consumed encoded payloads:

```text
CDD1 starts at 0x0702c
CDD2 starts at 0xd9000
decoded/controller target range appears to be 0x184000..0x1b3fff
```

We decoded some directory structure and a small affine lane, and live captures
showed fragments of normal-runtime 8051-looking code after materialization.
But we still do not have a full static encoder/decoder. Without that, targeted
normal-mode code patches remain hard: we can persist F0 bytes, but we cannot
yet reliably say "change this normal-mode instruction and re-encode the CDD."

That is why the current practical powers are:

- dump/decrypt firmware;
- persist selected bytes with the helper bypass;
- run helper/currentboot code;
- read selected currentboot/controller state through response hooks;
- observe pieces of the normal runtime;

and the current missing power is:

- complete normal-mode code control.

## Good Next Tinkering Targets

If you want to play without diving into the full evidence tree, start here:

```sh
python3 scripts/liteon_linux_status.py
python3 scripts/parse_liteon_extrainq.py --help
python3 scripts/dump_liteon_linux_f0_window.py --help
python3 scripts/build_liteon_helper_bypass_candidate.py --help
python3 scripts/build_liteon_helper_codeexec_candidate.py --help
python3 scripts/build_liteon_currentboot_response_hook_candidate.py --help
python3 scripts/read_liteon_currentboot_gateway_bulk.py --help
```

The most pleasant small experiment is still the delay hook: it is visible in a
single run, it does not require decoding CDD, and it gives a feel for the whole
workflow. The most powerful currentboot experiment is the gateway bulk response
hook. The hard research frontier is still CDD materialization and normal-mode
I/O.
