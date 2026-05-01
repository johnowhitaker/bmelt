# Normal READ BUFFER High-Mode Scan And GET PERFORMANCE Harvest

This checkpoint followed the GET CONFIG bridge correction. If the strongest
normal bridge edge is just the public READ BUFFER offset path, the obvious
next question is whether byte 1 of the READ BUFFER CDB has hidden high-bit
selectors that expose another window.

## READ BUFFER High Modes

Tool:

```text
scripts/scan_liteon_read_buffer_modes.py
```

Evidence:

```text
references/evidence/live/normal-read-buffer-mode-byte-scan-20260501/
```

The scanner sends raw READ BUFFER CDBs and treats byte 1 as an unconstrained
8-bit value instead of the ordinary low 5-bit SCSI mode field. It remains
read-only and uses no data-out payload.

The smoke scan checked representative high byte values:

```text
0x20, 0x40, 0x60, 0x80, 0xa0, 0xc0, 0xe0, 0xff
```

for IDs:

```text
0x01, 0x02, 0xe2, 0xf0, 0xf1, 0xf2
```

at offset `0x000000`, length `0x80`. All 48 requests returned `rc=5` with no
data. The broader scan covered every mode byte `0x20..0xff` against the same
IDs, again at offset `0x000000`, length `0x80`. All 1344 requests returned
the same `rc=5` no-data shape. There were no timeouts and no partial data
windows.

Practical result: high READ BUFFER mode bits are not an easy selector path.
The drive rejects them before exposing even the public windows.

## GET PERFORMANCE Tile Harvest

Tool:

```text
scripts/capture_liteon_normal_get_performance_variants.py
```

Evidence:

```text
references/evidence/live/normal-work-window-get-performance-variants-20260501/
references/evidence/live/normal-work-window-get-performance-variants-long-20260501/
analysis/8051/normal-work-window-get-performance-variants-20260501.md
analysis/8051/normal-work-window-get-performance-variants-long-20260501.md
```

This helper sends read-only MMC GET PERFORMANCE variants, saves any response,
then captures the normal public work window with:

```text
READ BUFFER mode=1 id=01 offset=0x070000 length=0x10000
```

Most GET PERFORMANCE variants return the expected CHECK/no-data response. The
useful part is not the host response; it is that the command perturbs which
normal-runtime overlay tiles are visible in the follow-up work-window capture.

The first two-cycle pass produced 38 captures and added 77 chunks to the
combined normal work-window corpus. The four-cycle longer pass produced 76
captures but added no new corpus chunks, so this command family appears
saturated for the current capture method.

Updated corpus:

```text
analysis/8051/normal-work-window-chunk-corpus-20260501.md
analysis/8051/normal-work-window-overlay-map-20260501.md
analysis/8051/normal-work-window-dptr-refs-20260501.md
```

Current counts:

```text
runs:                       6
captures:                   208
unique informative chunks:  862
static-matched chunks:      63
runtime/unmatched chunks:   799
chunks seen at >1 slot:     262
```

The first GET PERFORMANCE pass was therefore a good one-time tile harvest, but
looping it further is not a good use of live cycles.

## Important Interpretation Caution

The strongest recurring GET PERFORMANCE-only chunk appears at
`+0x8b00/+0x8b40/+0x8b80/+0x8bc0` and references `0x8a49` and `0x8a4d`. A
linear disassembly of the surrounding bytes shows checks equivalent to:

```text
xdata[0x8a49] == 0x1b
(xdata[0x8a4d] & 0x0f) == 0x02
```

That is the already-confirmed START STOP eject branch, not a new GET
PERFORMANCE semantic path. GET PERFORMANCE is causing this normal overlay
tile to become visible in the sampled public window, but that does not mean
the GET PERFORMANCE CDB executes the eject path.

## Current Read

Two easy selector ideas are now closed:

1. GET CONFIG reserved bytes do not steer a hidden normal bridge.
2. READ BUFFER high mode-byte values do not expose a hidden selector.

The normal public window is still valuable because it exposes a large and
mostly runtime-only code/data corpus. But the next useful live work should not
be more blind looping of the same two commands. Better next targets are:

- offline stitching of the harvested `0x8a49..0x8a54` packet-shadow code;
- another safe command family that naturally exercises different normal
  command handlers;
- a normal-mode patchability route, so the known public READ BUFFER machinery
  can be redirected rather than merely sampled.
