# Normal Controller Write-Side Overlap

Date: 2026-05-01

This note follows the normal hidden-runtime chunk classifier and focuses on
the controller write-side island around public offsets `+0xdbc0..+0xdc7f`.
Unlike the GET CONFIG-specific read-side seed, this island is both normal-mode
stable and byte-identical in the saved currentboot gateway dump.

## Key Finding

Three controller write-side chunks are present in every saved normal
work-window capture and also appear exactly in
`linux-drive1-currentboot-gateway-070000-10000.bin`:

| chunk | normal public offset | normal observations | exact reference | role |
|---|---:|---:|---|---|
| `e2488fa3edce` | `+0xdbc0` | 509 | currentboot gateway | save current `0x4095..0x4097` state into `0x8ade/0x8aec/0x8aeb` |
| `cf3469eae7d0` | `+0xdc00` | 509 | currentboot gateway | write setup bytes into `0x4095..0x4097`, then write data through `0x4098` |
| `ebaf1ca1d57c` | `+0xdc40` | 509 | currentboot gateway | restore saved `0x4095..0x4097` state |

This is the strongest current static evidence for a code island that might be
reachable from both currentboot and normal runtime.

## Local Shape

The `+0xdbc0` chunk saves controller command registers:

```text
0x4095 -> 0x8ade
0x4096 -> 0x8aec
0x4097 -> 0x8aeb
```

The `+0xdc00` chunk then writes a new controller command setup:

```text
0x89a5 -> 0x4095
0x8a5b -> 0x4096
0x8a5c -> 0x4097
0x4098 <- register/data byte
```

The `+0xdc40` chunk restores the saved state:

```text
0x8ade -> 0x4095
0x8aec -> 0x4096
0x8aeb -> 0x4097
```

So this looks like a stock "temporarily borrow the controller command port,
do a FIFO/data transaction, then restore the previous command address" helper.

## Why This Matters

The response bridge chunk `20ea2ab16891` is stable in normal mode, but
currentboot `+0x7140` is unrelated. That made it a poor direct
currentboot-to-normal patch target.

The write-side island is different. These bytes already match between the
currentboot gateway dump and normal captures. If volatile gateway writes can
ever survive a soft transition into normal mode, this island is a better test
site than the response bridge.

This does **not** mean the island is safe to patch casually. It touches
`0x4095..0x4098`, the controller command/FIFO path, so a bad edit can wedge the
LUN. The useful point is narrower: for a future state-carryover experiment,
patching a reversible one-byte no-op or branch-neutral byte in this exact
overlap region is more defensible than patching a page that is unrelated
between currentboot and normal.

## Practical Next Step

Do not run this automatically. When live work resumes, the clean test would be:

1. Enter currentboot and install the gateway write hook.
2. Patch one harmless byte in `controller[0x07dbc0..0x07dc7f]` that can be
   read back immediately and does not change behavior.
3. Recover to normal without a cold power cut if possible.
4. Read the normal work-window and check whether the exact write-side chunk
   changed.

If that marker carries over, this becomes the first plausible normal-mode
runtime patch primitive. If it does not, then currentboot gateway writes are
probably reset/reloaded before normal mode, and we need a true normal-mode
write path instead.
