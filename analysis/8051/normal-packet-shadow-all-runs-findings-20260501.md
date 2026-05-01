# Normal Packet Shadow All-Runs Findings

This pass reran the packet-shadow analyzers over every saved normal
work-window capture directory, not just the six-directory corpus used for the
latest tile-harvest checkpoint.

Inputs:

```text
references/evidence/live/normal-work-window-*/
```

Outputs:

```text
analysis/8051/normal-packet-shadow-all-runs-20260501.md/json
analysis/8051/normal-packet-selector-map-all-runs-20260501.md/json
analysis/8051/normal-packet-shadow-full-corpus-20260501.md/json
analysis/8051/normal-packet-selector-map-full-corpus-20260501.md/json
```

The all-runs scan covers 19 directories and 509 work-window captures. It sees:

```text
target DPTR observations:       177029
unique target chunks:           191
direct MOVX copy edges:         59
target compare idioms:          35
FIFO bursts from 0x47b1:        6
controller sequence classes:    6
```

## Packet Shadow Is Real, But The Bytes Are Reused

The FIFO intake pattern is now very strong:

```text
0x47b1 -> 0x8a4a..0x8a4b
0x47b1 -> 0x8a4c..0x8a54
0x47b1 -> 0x8a4d..0x8a54
```

The opcode-like compare cluster around `0x8a49` also remains strong. The
all-runs selector map sees compares against values such as:

```text
0x03 REQUEST SENSE
0x1b START STOP UNIT
0x28 READ(10)
0x2a WRITE(10)
0x55 MODE SELECT(10)
0xa3 SEND KEY
0xa4 REPORT KEY
0xe3/0xe6/0xe7 LiteOn/vendor-like commands
```

So `0x8a49` is still the best normal packet opcode/selector byte.

The important correction is for the later shadow bytes. `0x8a4d`, `0x8a4e`,
`0x8a53`, and `0x8a54` are not permanently just CDB bytes. They often start as
packet-shadow bytes, but later paths reuse them as controller response/status
or response-builder scratch. The selector analyzer now labels them that way.

## GET CONFIG-Specific Slice

The all-runs scan exposed one sharper GET CONFIG pattern:

```text
0x4099 -> 0x8a4d/0x8a4e/0x8a53/0x8a54
0x8a4d == 0xfe
0x8a4c/0x8a4d/0x8a4e -> 0x4011/0x4012/0x4013
0x8a50/0x8a51 -> IRAM 0xa9/0xaa style length/state pair
```

The byte pattern:

```text
90 40 99 e0 90 8a 4e f0
90 40 99 e0 90 8a 53 f0
90 40 99 e0 90 8a 54 f0
...
90 8a 4d e0 b4 fe 02 80 14
```

appears 39 times across saved captures, and only in GET CONFIG-oriented
directories:

```text
normal-work-window-get-config-current-long-20260501
normal-work-window-get-config-field-variants-20260501
normal-work-window-get-config-field-variants-r5-long-20260501
normal-work-window-get-config-r5-01-isolated-20260501
normal-work-window-get-config-r5-f0-isolated-20260501
normal-work-window-get-config-variants-20260501
normal-work-window-isolated-get-config-current-20260501
normal-work-window-stimuli-focused-20260501
```

The generic `0x8a4c..0x8a4e -> 0x4011..0x4013` clamp/copy pattern appears in
all work-window captures, because it belongs to the public READ BUFFER response
path. The `0x4099 -> shadow` burst plus the `0x8a4d == 0xfe` sentinel is the
more specific GET CONFIG clue.

## Current Interpretation

GET CONFIG is not a hidden arbitrary-memory oracle. The reserved CDB-byte
experiments already showed that tolerated junk fields do not change the host
response. The better interpretation is that GET CONFIG runs a small
controller-backed response builder:

1. It asks the controller for response/list material through `0x4099/0x409c`.
2. It stores returned bytes into reused shadow/scratch bytes.
3. It recognizes `0xfe` as a sentinel or special length/control marker.
4. It feeds `0x4011..0x4013` and local length state to build the host-visible
   feature list.

That makes GET CONFIG useful for mapping the normal response machinery, but not
sufficient by itself for decoded CDD reads.

## Next Static Targets

The most useful static work from here is to stitch these islands:

```text
+0x70c0 / +0x7100 / +0x7140 / +0x7180   read-side / 4011..4013 / 4099 path
+0x7480 / +0x74c0                       4099 burst command
+0x7600 / +0x7640                       4091..4093 setup and 409c kicks
+0xdbc0 / +0xdc00 / +0xdc40             4095..4097 save/restore/FIFO writer
```

The most useful live work, when we return to it, is not more random GET CONFIG
reserved-byte fuzzing. Better candidates are:

- normal-mode patchability around this response builder;
- controlled GET CONFIG start-feature/request-type/length tests only when a
  specific branch hypothesis needs checking;
- another harmless command family whose stock handler naturally exposes more
  controller-backed response bytes.
