# Normal READ BUFFER E2 Alias, 2026-05-01

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- device: `/dev/sg0`
- state before and after probe: normal `LD5M`

## Summary

`READ BUFFER mode=1 id=e2` is not a decoded CDD/runtime-memory leak. It is a
narrow public alias for the first two pages of the normal `id=01` work window:

```text
id=e2 offset 0x0000 == id=01 offset 0x074000
id=e2 offset 0x1000 == id=01 offset 0x075000
id=e2 offset 0x2000 and above at page starts: CHECK CONDITION
```

The old `ide2-000000-001000.bin` artifact matches
`id01-070000-010000.bin[0x4000..0x4fff]` byte-for-byte. A new read-only
`0x80`-byte check at `e2 +0x1000` matches
`id01-070000-010000.bin[0x5000..0x507f]` byte-for-byte.

That means `id=e2` exposes the profile/string/table region at controller/work
addresses `0x074000..0x075fff`, then stops. It does not reach the code-heavy
`0x076000..0x07ffff` part of the work window, and it does not reach the
candidate decoded CDD range.

## Evidence

Existing exact match:

```text
b1bc188cf3b2730df52da0beafc580f2a02b1f9689a490ed3d888d700dee42f1
references/evidence/live/normal-read-buffer-extra-buffers-20260501/ide2-000000-001000.bin
```

New exact-`0x80` read at `e2 +0x1000`:

```text
1b448780ca7218253f31b3d32178c5fbb937a30543e9c85597069b5a73ccdf03
references/evidence/live/normal-read-buffer-e2-alias-20260501/ide2-001000-000080.bin
```

The page-start scan used one exact `0x80` read per page start:

```text
references/evidence/live/normal-read-buffer-e2-alias-20260501/e2-page-starts-len80-summary.txt
references/evidence/live/normal-read-buffer-e2-alias-20260501/e2-page-starts-len80.jsonl
```

Result:

```text
offset 0x0000  GOOD, interesting, equals id01 +0x4000
offset 0x1000  GOOD, interesting, equals id01 +0x5000
offset 0x2000  CHECK CONDITION / no data
offset 0x3000  CHECK CONDITION / no data
...
offset 0xb000  CHECK CONDITION / no data
```

The optical LUN stayed normal `LD5M` after the scan.

## Static Anchor

The normal overlay's special READ BUFFER branch has a direct `id=e2` path at
dump offset `+0x6863`, unlike the `f1`/`f2` paths that jump into the dense
`+0xa2xx` island:

```text
+0x6848  read xdata[0x8a4b]       ; READ BUFFER id byte
+0x684c  add #0x10                ; f0 -> +0x68aa
+0x6853  ljmp +0xa2b1             ; f1
+0x6859  ljmp +0xa2f0             ; f2
+0x685c  add #0x10                ; e2 -> +0x6863
+0x6863  read xdata[0x8a4c]
+0x6867  reject if nonzero
+0x6869  read xdata[0x8a4d..0x8a4e]
+0x6873  set r2 = 0x20
+0x6878  lcall 0x32fb
```

The live behavior fits that static shape: `e2` only accepts low offsets and
does not use the wider `id=01` 24-bit address surface.

## Practical Takeaway

For future public read-only work:

- Use `id=01 offset 0x070000` for the full `0x070000..0x07ffff` work window.
- Use `id=e2` only as a sanity alias for `0x074000..0x075fff`.
- Do not spend CDD-decoder effort on `e2`; it is profile/table material already
  visible through `id=01`.
