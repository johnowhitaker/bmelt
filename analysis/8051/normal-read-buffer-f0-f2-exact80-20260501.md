# Normal READ BUFFER F0/F2 Exact-0x80 Reads, 2026-05-01

Host separation:

- drive host: `jonathan-thinkpad-t480s`
- device: `/dev/sg0`
- state: normal `LD5M`

## Summary

The all-ID scan missed two important responders because allocation length
matters. In normal mode, `READ BUFFER mode=1` IDs `0xf0` and `0xf2` accept
exact `0x80`-byte reads. Shorter or larger single requests can reject, even
though a sequence of exact `0x80` chunks works.

This does not expose decoded CDD directly, but it clarifies two read surfaces:

```text
id=f0  encrypted F0 readback, stateful with EXTRAINQ timing
id=f2  encoded container slice around CDD2/profile/trailer material
```

The drive remained normal `LD5M` after the sweeps.

## F0 Timing

`id=f0` is the known encrypted F0 readback path, but the ciphertext depends on
the command state. A 1 MiB dump taken before a fresh live EXTRAINQ was stable,
but did not decrypt with the current EXTRAINQ key:

```text
bfd89088679ea61ec5ae8430cd12c4b006866efdd198692a0ccb93b506414495  idf0-000000-100000.bin
```

After issuing live EXTRAINQ:

```text
077fe3994e5692c807360ab0b16d043b1a7a7e2da4f4bf83724eee1432fe99be  live-extrainq-176.bin
57d4722e8e319ddc25c647b5d43616e4d4f830e14885486b70204a94eeed05be  idf0-000000-001000-after-extrainq.bin
1f9392329b426ed368680d2cb67f77d40bc245465e3a83ad07b3f5f6d55a7bee  idf0-000000-001000-after-extrainq-decrypted-livekey.bin
```

The post-EXTRAINQ raw F0 prefix decrypts with the live EXTRAINQ IV/key, using
AES-CBC reset every `0x80` bytes, and matches the stock LD5M F0 prefix exactly.

Practical rule: for persistent-write verification, read EXTRAINQ immediately
before F0 readback and read in exact `0x80` chunks.

## F2 Layout

`id=f2` also requires exact `0x80`-byte chunks. It is not decoded CDD. It exposes
encoded container material:

```text
251137803ea5f0fc4ab74077b16be77912d93a303b38989fedc604acedf36731  idf2-000000-000080.bin
8548457f7e9a92c7060426f7e77b05c84947531c0c20e078dbfa212ab4277ea0  idf2-000000-030000.bin
```

Useful anchors:

```text
f2 +0x00000 == F0 +0xd9000  CDD2 header/prefix
f2 +0x0ffd0 == F0 +0xd8fd0  identity/profile area
f2 +0x1efe0 contains trailer auth14 and DU8A6S/LITE markers
```

The full `0x30000` dump is a rebased/container view with two non-erased CDD2
spans and several erased/pad regions:

```text
f2 0x00000..0x07000  == F0 0xd9000..0xe0000  CDD2 header and first body span
f2 0x07000..0x10000  == F0 0xd0000..0xd9000  erased gap, then profile at +0xffd0
f2 0x10000..0x17000  == all ff                  final erased-region view
f2 0x17000..0x1d401  == F0 0xe0000..0xe6401  CDD2 tail span
f2 0x1d401..0x1f000  == F0 0xe6401..0xe8000  gap plus trailer/marker
f2 0x1f000..0x30000  == all ff                  final erased-region view
```

Sparse `f2` reads at high candidate decoded-CDD offsets such as `0x184000`
returned all `ff` for the exact `0x80` request. This is another encoded-object
view, not the runtime decoded `0x184000..0x1b3fff` range.

One useful static wrinkle: the visible F0-prefix READ BUFFER handler at
`FUN_CODE_385c` / code `0x385c` explicitly accepts only buffer IDs
`0x01`, `0x02`, `0xe2`, `0xf0`, and `0xf1`. It has no `0xf2` comparison in the
F0-prefix binary. A live read-only check still showed
`READ BUFFER mode=1 id=f2` works, including with a 12-byte ATAPI-style CDB:

```text
3c 01 f2 00 00 00 00 00 80 00 00 00
251137803ea5f0fc4ab74077b16be77912d93a303b38989fedc604acedf36731
```

The normal-mode `id01:0x070000` work/code dump resolves this: it contains an
alternate READ BUFFER-like accept list at dump offset `+0x6747` with the
sequence `01, 02, e2, f0, f2, f1`. That makes `f2` a normal-runtime overlay
surface, not evidence that `FUN_CODE_385c` has a hidden decoded-CDD branch.

A later read-only high-ID exact-`0x80` scan confirmed that this family is small
at offset zero:

```text
mode=1 length=0x80 ids=0xe0..0xff
responders: e2, f0, f1, f2
all other high IDs: CHECK CONDITION / no data
post-scan status: normal LD5M
```

The matching exact-size mode sweep for just `e2/f0/f1/f2` also stayed narrow:

```text
modes scanned: 0x00..0x1f
length:        0x80
responding mode: 0x01 only
post-scan status: normal LD5M
```

Evidence:

```text
references/evidence/live/normal-read-buffer-exact80-scan-20260430/
references/evidence/live/normal-read-buffer-mode-exact80-scan-20260430/
```

## Evidence

```text
references/evidence/live/normal-read-buffer-length-scan-20260501/
references/evidence/live/normal-read-buffer-f0-f2-map-20260501/
references/evidence/live/normal-read-buffer-f0-f2-full-20260501/
```

## Next Uses

- Use `id=f0` only with exact `0x80` chunks and fresh EXTRAINQ when verifying
  persistent flash state.
- Use `id=f2` as a direct live encoded-container view if we need to compare the
  controller's admitted/staged CDD2/profile/trailer material against an offline
  candidate.
- Do not treat pre-EXTRAINQ encrypted F0 ciphertext as decoded CDD or as a raw
  firmware image.
