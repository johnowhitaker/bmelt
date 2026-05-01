# Currentboot Gateway Extra Map, 2026-05-01

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- remote work dir: `/home/jonathan/bmelt-live`
- device: `/dev/sg0`
- drive state: entered currentboot with event 1, using the already-installed
  `gateway-cdb-bulk-xdata-write-v2` currentboot response hook

The goal was to test whether the new `selector << 21` mailbox-bank clue gave a
simple alternate view of decoded CDD/runtime memory through the currentboot
controller gateway.

## Result

The useful answer is negative for decoded CDD, positive for currentboot mapping.

Small bulk reads at these addresses were all zero:

```text
0x184000 0x284000 0x384000 0x484000 0x584000
0x191010 0x391010 0x591010
0x198900 0x398900 0x598900
0x1a0000 0x3a0000 0x5a0000
```

So the decoded CDD candidate range is not merely sitting at the same offset in
another simple `+0x100000` or `+0x200000` gateway mirror during currentboot.

A sparse 24-bit scan showed the gateway path used by this hook mirrors every
`0x100000` bytes. In practice, the currentboot hook sees an effective 20-bit
view, not the 2 MiB-banked command-wrapper space:

```text
0x000000, 0x100000, ...  live command/profile-looking window
0x010000, 0x110000, ...  sparse mostly-zero page
0x020000, 0x120000, ...  all ff
0x070000, 0x170000, ...  mixed currentboot work window, known from earlier
everything else          all zero at 64 KiB sampling granularity
```

This does not invalidate the `0x4e80` mailbox bank finding. It says the
response-hook's direct `0x4091..0x4098` gateway read path is a different,
mirrored view in currentboot.

## New Dumps

The new evidence lives in:

```text
references/evidence/live/currentboot-gateway-extra-20260501/
```

Raw dump hashes:

```text
684e62df2fc4188d2e30a8c2df90b7af644f1c2c3822eb38e7e1db1f9b55e463  gateway-000000-007000.bin
9379cda168e7cb98f99971e04b84e75aef5c6768c7949c195e8c74f5c2acdeb7  gateway-018000-001000.bin
5be642575befeae903a1af35134d4a887b17a4790d1f92aa2f15c242adb7ddb0  gateway-06b000-001000.bin
```

`gateway-018000-001000.bin` is the active plain profile-tail helper overlay.
Its first `0xbc0` bytes match
`references/firmware/extracted/liteon-official-profile-tail-ef130045-plain.bin`
byte-for-byte.

`gateway-000000-007000.bin` starts with the current profile-tail command/CDB
surface, then contains an exact encoded-F0 overlap:

```text
gateway[0x002c..0x5554] == LD5M F0[0xe002c..0xe5554]
```

That is inside encoded CDD stream 2, not decoded runtime CDD. It is still useful
because it confirms this low gateway page contains live staging/currentboot
work buffers, not arbitrary noise.

`gateway-06b000-001000.bin` is a low-entropy table/profile-looking area. It
contains repeated drive/part strings such as:

```text
CN0HMN3XPLC0088251M0A00
```

## Practical Takeaway

For live data reads, the currentboot hook is now well mapped:

- use `0x018000` to inspect the active helper overlay;
- use `0x070000..0x07ffff` for the mixed currentboot work/code/profile window;
- use `0x000000..0x006fff` if we need the current low staging buffer, including
  the encoded CDD2 overlap;
- do not expect decoded CDD bytes at `0x184000` in this phase, even with simple
  bank offsets.

The next real decoded-memory read likely needs a normal-runtime hook or a
controlled call into the `0x4e80/84/88/8c` mailbox path, not another passive
currentboot gateway address guess.
