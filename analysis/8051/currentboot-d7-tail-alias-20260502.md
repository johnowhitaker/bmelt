# Currentboot D7 Tail Alias Notes

Date: 2026-05-02

## What Changed

The `0xd7` currentboot response hook gave us a better read-only oracle, but it
also corrected an earlier interpretation. The nonzero data at addresses such as
`0x184000` is not decoded CDD runtime code in this currentboot phase. It matches
stock LD5M F0 under a simple modulo-1MiB interpretation:

```text
0x184000 -> F0 0x84000
0x18b170 -> F0 0x8b170
0x191010 -> F0 0x91010
```

So `0x184000..0x1b3fff` may still be the descriptor's decoded controller range
in normal runtime, but this particular currentboot `0x1717` call is not exposing
that decoded image.

## The Useful Surprise

The same oracle exposes non-F0 material in the nominally erased F0 tail:

```text
stock F0 0xe8000..0xfffff = ff...
D7 read 0xe8000..0xfffff = currentboot/profile/work-window material
```

The transition is exact. A read beginning at `0xe7fe0` matches the LD5M trailer
through `0xe7fff`, then diverges immediately at `0xe8000`.

Dense captures now preserved:

```text
references/evidence/live/currentboot-byte-oracle-targeted-20260502T0150Z/
  hidden_tail_0e8000_2000.bin
  hidden_tail_0f0000_8000.bin
  hidden_tail_0f8000_8000.bin
```

## Tail Layout From Current Reads

```text
0xe8000..0xe9fff  data, starts like the old currentboot gateway 0x070000 page
0xea000..0xebfff  sampled as 00
0xec000..0xeffff  sampled as ff
0xf0000..0xfdfff  repeated profile/key-parameter pages
0xfe000..0xfffff  ff
```

The `0xf0000..0xfdfff` area contains live per-drive strings:

```text
PLDS CORPORATION
0HCS6F443-03+08182272090282469221322105320529A U2SU35BH23I4
CN0HMN3XPLC0088251B6A00
PCBASU35BH23I4
KEYPARA
CDROM
LSCDRW / HSCDRW / USCDRW / DVD* profile labels
DBUG
```

The same structural strings appeared in the older `0x070000` gateway dump from
Linux drive #1, but with different per-drive identity material. That makes this
look like a real currentboot/profile work surface rather than static firmware
bytes.

## Full-Window Hook Result

The raw `window128_*.bin` tests explain why this hook is still slow. A full
`0xd7` response mostly returns a fixed/stale CDD-header buffer. The selected
mapped byte lands at response byte `0xa0`, which corresponds to
`xdata[0xc07f]`. Examples:

```text
address 0x00702c: window[0x7f] == byte_oracle[0x00]
address 0x0e8000: window[0x7f] == byte_oracle[0x00]
address 0x184000: window[0x7f] == byte_oracle[0x00]
```

This rules out treating the current `0xd7` hook as a 128-byte bulk reader. A
bulk version would need a new injected loop that advances the requested source
address internally and copies the selected `0xc07f` byte repeatedly into the
response.

## Practical Takeaway

Do not spend the next RE cycle building that faster hook unless we need a large
currentboot dump. The current one-byte oracle is enough for targeted map
questions. The higher-value thread is now:

1. Understand what currentboot exposes through the erased-tail alias.
2. Compare this alias with the older `0x070000` gateway/work-window dumps.
3. Use the tail/profile map to infer how `0x1717` chooses source spaces.
4. Return to a normal-runtime oracle for actual decoded CDD overlays.
