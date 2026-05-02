# Currentboot D7 Byte-Oracle Targeted Reads

Date: 2026-05-02

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- remote repo during run: `/home/jonathan/boastermelt`
- device: `/dev/sg0`
- drive: spare Linux drive
- live state during capture: currentboot with the `0xd7` mapped-source response hook installed

## Summary

This run used the currentboot `0xd7` response hook and
`scripts/read_liteon_currentboot_cdd_mapped_source.py --d7-c07f-byte-oracle`.
The hook calls resident helper `0x1717` with a host-selected 24-bit source
address, returns marker `0xd7`, and exposes the reliable selected byte at
`xdata[0xc07f]`. The reader advances one byte at a time.

The main correction from this run is that reads near the descriptor's decoded
range are not decoded CDD in this currentboot path:

```text
0x100000 -> stock F0[0x00000]
0x180000 -> stock F0[0x80000]
0x184000 -> stock F0[0x84000]
0x18b170 -> stock F0[0x8b170]
0x191010 -> stock F0[0x91010]
0x1b3f00 -> stock F0[0xb3f00]
```

So the earlier nonzero `0x184000` lead is best explained as modulo-1MiB F0
aliasing, not decoded controller firmware.

The new useful lead is the erased F0 tail. Stock LD5M has `0xff` from
`0xe8000..0xfffff`, but the D7 oracle exposes live currentboot/profile material
there:

```text
0xe8000..0xe9fff  currentboot work/gateway-like window; starts like old gateway 0x070000
0xea000..0xebfff  sampled as all 00
0xec000..0xeffff  sampled as all ff
0xf0000..0xfdfff  repeated profile/key-parameter pages with live per-drive strings
0xfe000..0xfffff  all ff in the dense tail read
```

This looks like the currentboot source mapper treats the valid F0 object
boundary at `0xe8000` as the end of sealed firmware, and the nominal erased
tail becomes a view onto currentboot runtime/profile pages.

## Captures

All large per-command JSON files were discarded after generating
`capture-summary.json`; the binary captures are the evidence.

Key dense captures:

```text
hidden_tail_0e8000_2000.bin  0x0e8000..0x0e9fff
hidden_tail_0f0000_8000.bin  0x0f0000..0x0f7fff
hidden_tail_0f8000_8000.bin  0x0f8000..0x0fffff
```

Key control captures:

```text
f0_000000_0100.bin           ordinary F0 source control
cdd_header_00702c_0200.bin   ordinary CDD source control
rec59_028119_0400.bin        record 59 source control
rec137_0502fa_0400.bin       record 137 source control
ctrl_184000_0400.bin         proves currentboot 0x184000 aliases F0 0x84000
trailer_0e7fe0_0040.bin      shows exact transition at 0xe8000
```

The `window128_*.bin` captures preserve full raw `0xd7` windows from a few
addresses. They show why the current hook is still a one-byte oracle: most of
the returned 128-byte window is a fixed/stale CDD-header buffer, while the
selected byte appears at response byte `0xa0`, corresponding to
`xdata[0xc07f]`.

## Strings

The profile/key pages contain live strings that are not present in the sealed
stock F0 image, for example:

```text
PLDS CORPORATION
0HCS6F443-03+08182272090282469221322105320529A U2SU35BH23I4
CN0HMN3XPLC0088251B6A00
PCBASU35BH23I4
KEYPARA
CDROM
LSCDRW
HSCDRW
USCDRW
DVD5 / DVD9 / DVD+R / DVD-R / DVD+RW / DVD-RW / DVD+R9 / DVD-R9 / DVDRAM
DBUG
```

This differs from the older Linux drive #1 gateway dump, which had different
per-drive strings such as `...U2SU35GH7I65`. That is expected because this run
used the spare drive.

## Interpretation

The D7 byte oracle remains valuable for targeted reads, but the current hook is
not a bulk decoded-CDD reader. A future speedup would need a new hook that loops
inside the drive, calls `0x1717` for sequential addresses, and places those
selected bytes into the host response. That is an engineering improvement, not
the current highest-value reverse-engineering step.

The next useful analysis target is the hidden tail alias itself:

- compare `0xe8000..0xe9fff` with the old `0x070000` currentboot gateway dump;
- map which live/profile pages repeat at `0xf0000..0xfdfff`;
- check whether the `0xe8000` work-window bytes are enough to infer more about
  `0x1717` source mapping or currentboot profile layout;
- avoid calling `0x184000` a decoded CDD image until a normal-runtime oracle or
  a stronger mailbox state proves it.
