# Normal READ BUFFER Work Window, 2026-05-01

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- device: `/dev/sg0`
- state: normal `LD5M`, after Pico cold boot

## Summary

Normal-mode `READ BUFFER mode=1` has a useful public read surface. Buffer IDs
`0x01` and `0x02` expose a controller/work window at offsets around
`0x070000`, without entering currentboot and without using the currentboot
response hook.

This is not the decoded CDD payload. The decoded CDD candidates are still zero:

```text
id 01/02 offset 0x184000 = all 00
id 01/02 offset 0x184060 = all 00
id 01/02 offset 0x191010 = all 00
id 01/02 offset 0x198900 = all 00
id 01/02 offset 0x199030 = all 00
id 01/02 offset 0x19c020 = all 00
id 01/02 offset 0x19c800 = all 00
id 01/02 offset 0x1a0000 = all 00
id 01/02 offset 0x1a2fe0 = all 00
```

At those same high offsets, IDs `0xe2`, `0xf0`, and `0xf1` returned CHECK
CONDITION rather than data.

## First-MiB Sparse Map

Sampling 64 bytes every `0x1000` showed that IDs `0x01` and `0x02` have the
same broad shape:

```text
0x000000            small header, starts ff 54 54 45 ("TTE")
0x001000..0x06afff mostly/all zero in sparse samples
0x06b000            low-entropy table/profile-looking data
0x070000            compact table/control data
0x074000..0x07ffff mixed profile strings, tables, and 8051-like code
elsewhere           all zero in the first 1 MiB sparse scan
```

The `0x075000` page contains the familiar profile/media strings:

```text
KEYPARA
CDROM
LSCDRW
HSCDRW
USCDRW
DVD5
DVD9
DVD+R
DVD-R
DVD+RW
DVD-RW
DVD+R9
DVD-R9
DVDRAM
```

## Full Dumps

Evidence directory:

```text
references/evidence/live/normal-read-buffer-work-window-20260501/
```

Full-window hashes:

```text
f3b4000fdcd66e812bdd6e5774215818d6deff904926c8610655261854ca5c8d  id01-000000-007000.bin
47a3217dd7396636bc70cd2ed20ed0f49e6c8d837f355501435f17f8acf17eb4  id01-06b000-001000.bin
c3cd6e6d3e25a55e54d779a0f71965e93315290ab44537df4f0b6393c0e840e7  id01-070000-010000.bin
f3b4000fdcd66e812bdd6e5774215818d6deff904926c8610655261854ca5c8d  id02-000000-007000.bin
47a3217dd7396636bc70cd2ed20ed0f49e6c8d837f355501435f17f8acf17eb4  id02-06b000-001000.bin
3c78f44b80e972eafcdd92be7bc41596ca18481516af1e7525f85792ee379ebd  id02-070000-010000.bin
```

`id01` and `id02` are identical for the small `0x000000` and `0x06b000` dumps.
For the full `0x070000` window, they differ in only a few hundred positions,
concentrated in pages `+0x6000` and `+0x9000`.

Repeated full-window reads are not byte-stable. The changing bytes are again
concentrated in `+0x6000`, `+0x8000`, and `+0x9000`. So this window is a live
runtime/work view, not just a static flash mirror.

## Comparison With Currentboot Gateway

The normal `READ BUFFER id=01` dump shares a large stable middle with the older
currentboot gateway dump:

```text
same run +0x0000..+0x01ad
same run +0x02ea..+0x5fff
same run +0xa000..+0xffff
```

The main differences are:

- the low control records before `+0x02ea`;
- code-like/runtime pages `+0x6000..+0x9fff`;
- live-changing subranges inside `+0x6000`, `+0x8000`, and `+0x9000`.

This makes the normal READ BUFFER window valuable for runtime observation even
though it still does not expose decoded CDD.

## 24-Bit Sparse Map

A later sparse scan sampled 64 bytes at every `0x010000` boundary across the
full 24-bit READ BUFFER offset space. IDs `0x01` and `0x02` both collapse to
three shapes:

```text
0x?00000  small header, starts ff 54 54 45 ("TTE")
0x?70000  the same 0x070000 work-window header sample
else      all zero in this sparse scan
```

So the public normal-mode reader mirrors at 1 MiB granularity for these IDs.
That matches the currentboot gateway result: high addresses like `0x184000` do
not reach an independent decoded-CDD mapping through this path. They fold onto
zero-looking slots in the same 20-bit window.

Evidence:

```text
references/evidence/live/normal-read-buffer-work-window-20260501/id01-id02-24bit-sparse-summary.txt
```

## Buffer ID And Mode Scan

An all-ID scan at `0x070000` found only IDs `0x01` and `0x02`. A broader
selected-offset scan found these READ BUFFER mode-1 responders:

```text
id 0x00  offset 0x000000 only, 64-byte Initio bridge descriptor
id 0x01  public 20-bit LiteOn work window
id 0x02  same public 20-bit LiteOn work window
id 0xe2  offset 0x000000, aliases id01/id02 work-window +0x4000
id 0xf1  offset 0x000000, aliases id01/id02 work-window +0x5000
```

The `0xe2` and `0xf1` aliases are useful names, but not new memory surfaces:

```text
READ BUFFER id=e2 offset=0 len=0x1000 == id01 offset=0x074000 len=0x1000
READ BUFFER id=f1 offset=0 len=0x0b60 == id01 offset=0x075000 len=0x0b60
```

`id=f1` is the `KEYPARA`/media-profile table. `id=e2` begins with the compact
`LT...` record and `PLDS CORPORATION` string from the work window.

An exhaustive scan of READ BUFFER modes `0x00..0x1f` at offset zero found the
same thing: only mode `0x01` produced any data. Every other mode rejected every
ID in that 64-byte probe.

Allocation length matters. A later offset-zero length sweep found that
`id=0xf0` and `id=0xf2` respond to exact `0x80`-byte reads. Those IDs are
tracked separately:

```text
analysis/8051/normal-read-buffer-f0-f2-exact80-20260501.md
```

Evidence:

```text
references/evidence/live/normal-read-buffer-id-scan-20260501/
references/evidence/live/normal-read-buffer-extra-buffers-20260501/
references/evidence/live/normal-read-buffer-mode-scan-20260501/
references/evidence/live/normal-read-buffer-mode-scan-all-20260501/
```

## Static Clues

The normal window has front-panel/mechanics references that differ from the
currentboot dump. Notable direct `MOV DPTR,#addr` sightings:

```text
0x4814  count 1  at gateway offset +0x8005
0x47d2  count 2  at +0x6076, +0x61f4
0x5905  count 4  at +0x87f8, +0x8c41, +0x8c5d, +0x9388
0x5906  count 3  at +0x848b, +0x8598, +0x8884
0x5907  count 1  at +0x68d9
0x590b  count 1  at +0x68f6
0x5a00  count 2  at +0x849b, +0x85a2
0x5a31  count 1  at +0x68c5
```

The `0x4814` reference is especially relevant because the Pico button work
already showed `xdata[0x4814].4` tracks the eject button in currentboot. The
normal window now gives us normal-mode code bytes that read the same status
byte.

## Tooling

Use the chunked reader instead of one-off shell loops:

```sh
python3 scripts/read_liteon_read_buffer_bulk.py \
  --device /dev/sg0 \
  --id 0x01 \
  --offset 0x070000 \
  --length 0x10000 \
  --out runs/normal-read-buffer/id01-070000-010000.bin \
  --json-out runs/normal-read-buffer/id01-070000-010000.json \
  --quiet
```

Practical next uses:

- monitor this window before/after safe normal-mode SCSI commands;
- compare normal runtime pages against currentboot and sibling images;
- use the `0x4814` and `0x59xx` references to guide front-panel/mechanics
  static analysis without blind register writes.
