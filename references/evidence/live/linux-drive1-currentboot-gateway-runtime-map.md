# Linux Drive 1 Currentboot Gateway Runtime Map

Date: 2026-04-30

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- remote repo during run: `/home/jonathan/boastermelt`
- device: `/dev/sg0`
- drive: Linux drive #1
- hook installed in flash: `currentboot-response-hook-gateway-cdb-bulk`

## Summary

The currentboot gateway-bulk hook can read more than the helper overlay. The
initial decoded-CDD guess, controller `0x184000..0x1b4000`, is still all zero in
this phase, but a sparse sweep found a live mirrored 64 KiB region at:

```text
0x070000..0x07ffff
0x170000..0x17ffff
```

The first full dump of `0x070000..0x07ffff` is now preserved as:

```text
path   references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin
size   65536
sha256 5f517adeab1647dbedf7b93f8be097b1641164fd49e87776364b9e134b9cbc0b
```

This region is not a byte-for-byte slice of any static firmware image in the
current clean workspace. It contains live per-drive/profile strings and large
areas that disassemble plausibly as 8051 code, including direct references to
the same controller and hardware registers we have been probing.

## Run Details

The drive was entered into currentboot with event 1, then sampled with
`scripts/read_liteon_currentboot_gateway_bulk.py`.

Known-good sanity read:

```text
controller[0x018620..] = "Flash Type Error"
```

Targeted reads:

```text
controller[0x000000..0x000fff]  currentboot identity/trailer-like page
controller[0x004000..0x004fff]  all 00
controller[0x018000..0x018fff]  helper/profile overlay
controller[0x018600..0x018fff]  helper strings/code, includes "Flash Type Error"
controller[0x184000..0x1b3fff]  all 00
controller[0x1a0000..0x1a3fff]  all 00
```

Sparse 0x100-byte reads every 0x4000 from `0x000000..0x1fffff` found only
these nontrivial windows:

```text
0x000000
0x018000
0x070000
0x074000
0x078000
0x07c000
0x100000
0x118000
0x170000
0x174000
0x178000
0x17c000
```

The `0x170000` pages matched the corresponding `0x070000` pages sampled:

```text
0x070000 == 0x170000
0x074000 == 0x174000
0x078000 == 0x178000
0x07c000 == 0x17c000
```

## Strings

Notable strings in the `0x070000` dump:

```text
0x00086  PBDS
0x04040  PLDS CORPORATION
0x042c0  0HCS6F487+10-05202305100308508201293097293483A U2SU35GH7I65
0x043b0  CN0HMN3XPLC0088251M0A00
0x043e0  TST2
0x043f0  TST1
0x04400  PCBASU35GH7I65
0x05000  KEYPARA
0x05010  CDROM
0x050b0  LSCDRW
0x05100  HSCDRW
0x05150  USCDRW
0x051a0  US+CDRW
0x051f0  DVD5
0x05240  DVD9
0x052b0  DVD+R
0x05320  DVD-R
0x05390  DVD+RW
0x05400  DVD-RW
0x05470  DVD+R9
0x05510  DVD-R9
0x055b0  DVDRAM
0x05640  LS-DISK
0x05690  LF-DISK
0x056e0  DISK-IDF
0x0789d  DW8A6S
0x09e2c  DW8A6S
```

The serial/calibration-looking strings are live-drive specific; exact 32-byte
anchors from this region were not found in `references/`, `work/`, or
`analysis/` static files.

## Register Cross-References From This Dump

Treat these as static observations on the decoded/runtime image, not as proof
that casually writing these registers is safe.

```text
0x4000 count=38  controller busy/status waits
0x4091 count=3   gateway read-side address setup
0x4095 count=12  gateway write/command-side setup
0x4098 count=24  gateway FIFO
0x4709 count=1
0x470e count=4
0x47a6 count=6
0x47f3 count=2
0x48a0 count=1
0x4861 count=7
0x4862 count=4
0x4863 count=4
0x4864 count=6
0x4867 count=13
0x486a count=10
0x486b count=4
0x4990 count=1
0x4e0f count=2
0x4e10 count=3
0x4e1c count=2
0x4e1d count=5
0x5904 count=7
0x5905 count=7
0x5906 count=5
0x5907 count=1
0x592a count=4
0x5954 count=2
0x59a4 count=2
0x59c0 count=2
0x59f0 count=3
0x5a10 count=4
0x5a24 count=4
```

The `0x59xx` cluster appears in several substantial hardware-initialization
paths. That matches the live behavior: pokes near this cluster can move the
sled or alter recovery state, so it is not a simple front LED latch.

## Disassembly Clues

Radare2 with `-a 8051 -b 8` disassembles many parts of the `0x070000` dump
coherently. One example around offset `0x6395` is a standard controller FIFO
read loop:

```text
0x6395  mov dptr, #0x4098
0x6398  movx a, @dptr
...
0x63af  mov dptr, #0x4000
0x63b2  movx a, @dptr
0x63b3  jb 0xe0.7, 0x63af
0x63b6  mov dptr, #0x4098
0x63b9  movx a, @dptr
```

Several routines around `0x6059`, `0x642c`, `0x651b`, `0x6fe0`, `0x846b`, and
`0x89c7` manipulate `0x5904` and neighboring `0x59xx` registers. The region
around `0x8217`/`0x8556` references `0x470e`, `0x4709`, `0x47a6`, and `0x47f3`,
which makes the earlier hazardous-controller-path findings more grounded.

The `0x482b` register has a clean-looking helper at `0x7956`:

```text
0x7953  mov a, r7
0x7954  orl a, #0x01
0x7956  mov dptr, #0x482b
0x7959  movx @dptr, a
0x795a  inc dptr
0x795b  movx a, @dptr  ; copied to iram[0x48]
0x795e  inc dptr
0x795f  movx a, @dptr  ; copied to iram[0x49]
```

That looks more like a small controller command/status helper than a GPIO
write. `xdata[0x4814]`, the front-button sense candidate from the currentboot
XDATA differential, does not appear as a direct `MOV DPTR,#0x4814` reference in
this `0x070000` image; it may be updated indirectly or by hardware/controller
side effects rather than read by a simple direct-DPTR path here.

## Practical Consequence

The decoded CDD descriptor target `0x184000` is not the only useful gateway
address. In the currentboot phase, `0x070000`/`0x170000` is the better live
oracle. It may be a decoded controller/runtime/profile image, and it gives us a
new static target for:

- mapping controller-side register use without single-bit helper probes;
- understanding why LED/front-panel writes were not simple GPIO latches;
- looking for safer normal-runtime hook sites or command handlers;
- comparing currentboot and later-runtime controller memory if we get a hook
  that survives normal LD5M boot.

The drive was recovered after this run with
`scripts/recover_liteon_currentboot_linux.py --force`; final standard INQUIRY
reported revision `LD5M`.
