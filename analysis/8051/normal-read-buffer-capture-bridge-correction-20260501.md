# Normal READ BUFFER Capture Bridge Correction

Date: 2026-05-01

This is a correction to how the normal `0x4091..0x4099` bridge snippets should
be interpreted in the stimulus-capture corpus.

The earlier phrasing "GET CONFIG tags the bridge" is operationally true, but
it is easy to overread. Every normal work-window stimulus run has this shape:

```text
optional stimulus command
READ BUFFER mode=1 id=01 offset=0x070000 length=...
```

So the code chunks exposed in `*.window.bin` are often dominated by the
follow-up `READ BUFFER` capture command, not necessarily by the immediately
preceding stimulus. The stimulus can still perturb state or timing, which is
why stimulus-only chunks appear, but the bridge code itself must be interpreted
through the capture command too.

## Why This Matters

The strongest bridge edge is:

```text
xdata[0x8a4c] -> xdata[0x4011]
xdata[0x8a4d] -> xdata[0x4012]
xdata[0x8a4e] -> xdata[0x4013]
```

For a 10-byte SCSI READ BUFFER CDB:

```text
byte 0   3c
byte 1   mode
byte 2   buffer id
byte 3   buffer offset high
byte 4   buffer offset mid
byte 5   buffer offset low
byte 6   allocation length high
byte 7   allocation length mid
byte 8   allocation length low
byte 9   control
```

So this edge lines up exactly with the READ BUFFER 24-bit offset field:

```text
CDB[3] -> 0x4011
CDB[4] -> 0x4012
CDB[5] -> 0x4013
```

That is a much better explanation than treating those three bytes as a
GET CONFIG-specific hidden address field. It also explains why changing
reserved GET CONFIG byte 5 did not change the host-visible response: the most
obvious controllable address-like bridge was already the later READ BUFFER
capture offset, which we control directly.

## Practical Reinterpretation

The normal runtime already gives us a stock public read oracle:

```text
READ BUFFER mode=1 id=01/02 offset=<24-bit public offset>
```

We have mapped that oracle:

```text
0x000000            small header/TTE-ish region
0x06b000            profile/table data
0x070000..0x07ffff  mixed live work/code/profile window
0x?70000 mirrors    1 MiB-period mirrors of the same public window
elsewhere           mostly zero or rejected for the useful ids
```

That stock oracle is valuable but constrained. It does not reach decoded CDD
runtime memory at `0x184000..0x1b3fff`; those offsets fold to zero through
IDs `0x01/0x02`.

The `GET CONFIG` runs are still useful as safe timing/state perturbations, but
they should not be used as proof that GET CONFIG has an independent
controller-memory read address. The bridge snippets are more likely the normal
READ BUFFER handler and its public offset path.

## Updated Model

```text
host command
  -> normal packet shadow at xdata[0x8a49..0x8a54]
  -> for READ BUFFER: CDB[3..5] copied to controller registers 0x4011..0x4013
  -> public READ BUFFER id/mode selects a constrained controller/work window
  -> host receives public window bytes
```

For a future fast oracle, the problem is no longer "can we discover the GET
CONFIG hidden address fields?". The better questions are:

1. Is there another legal READ BUFFER mode/id/length corner that selects a
   different controller address space?
2. Is there a normal command whose stock response exposes the `0x4098/0x4099`
   bridge result with less public-window masking?
3. Can we patch the normal READ BUFFER handler or its selector table so the
   already-working public oracle points at decoded CDD memory?

The third option still has the same blocker as before: the normal READ BUFFER
handler lives in normal runtime/controller overlay material, not in the visible
F0 prefix we can already persistently patch.
