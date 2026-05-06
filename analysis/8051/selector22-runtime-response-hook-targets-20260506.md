# Selector22 Runtime Response-Hook Targets - 2026-05-06

This is an offline static note. No drive commands are implied.

## Why This Runtime Image Matters

The currentboot CDD `0x111a` selector work gave us one unusually useful
artifact:

```text
analysis/8051/drive3-selector22-runtime-image-0000-3fff-20260506.bin
```

It is a stitched 16 KiB 8051-looking runtime image. The best current page
mapping from the phase-code analysis is `full-reverse`:

```text
public/controller 0x079000 -> logical 0x0000
public/controller 0x078000 -> logical 0x1000
public/controller 0x077000 -> logical 0x2000
public/controller 0x076000 -> logical 0x3000
public/controller 0x075000 -> logical 0x4000
public/controller 0x074000 -> logical 0x5000
public/controller 0x073000 -> logical 0x6000
```

That makes this image a concrete target list for a future post-materializer
runtime writer. It does not yet prove we can patch these bytes live.

## Useful Addresses

| Logical | Public/controller | Meaning |
|---:|---:|---|
| `0x1406` | `0x078406` | packet/read-buffer-like handler that gates on `xdata[0x8a4c] == 0x01` and checks `0x8a51..0x8a54` length/state |
| `0x17eb` | `0x0787eb` | READ/READ-like handler that accepts packet opcodes `0x28` and `0xa8` |
| `0x2cd6` | `0x077cd6` | 42-byte zero/NOP cave, currently best small runtime hook body location |
| `0x33cf` | `0x0763cf` | mechanics/state reset helper, clears `0x4860..0x4864`, writes `0x4867 = 0x61`, clears `0x486a..0x486b` |
| `0x3661` | `0x076661` | broader packet dispatcher checking `0x28`, `0xa8`, `0xbe`, `0xd5`, `0xb9` |

The most attractive future code-exec proof is therefore a two-region runtime
patch:

```text
write hook body at public 0x077cd6
write LCALL 0x2cd6 at public 0x078406 or another confirmed hot entry
```

This is why `scripts/build_liteon_post_materializer_multi_blob_writer_candidate.py`
now exists: a hook body plus trampoline must be written in the same boot, after
the normal runtime has materialized.

## 0x1406 Handler Shape

Disassembly around logical `0x1406`:

```asm
1406  mov  dptr,#0x8a4c
1409  movx a,@dptr
140a  xrl  a,#0x01
140c  jz   0x1411
140e  ljmp 0xbead

1411  mov  dptr,#0x8a51
1414  movx a,@dptr      ; r4 = xdata[0x8a51]
1415  mov  r4,a
1416  inc  dptr
1417  movx a,@dptr      ; r5 = xdata[0x8a52]
1418  mov  r5,a
1419  inc  dptr
141a  movx a,@dptr      ; r6 = xdata[0x8a53]
141b  mov  r6,a
141c  inc  dptr
141d  movx a,@dptr      ; r7 = xdata[0x8a54]
141e  mov  r7,a
141f  mov  a,r4
1420  orl  a,r5
1421  orl  a,r6
1422  orl  a,r7
1423  jnz  0x1428
1425  ljmp 0xbee3

1428  mov  dptr,#0x8a4d ; copy 0x8a4d..0x8a50 into r4..r7
...
1436  mov  dptr,#0x8d15
1439  lcall 0x3430
...
1441  xdata[0x85e6] = xdata[0x8a4d]
1449  xdata[0x85e7] = xdata[0x8a4e]
1451  r7 = xdata[0x8a4a]
1456  r4..r3 = xdata[0x85e4..0x85e7]
1469  lcall 0x04fb
```

This is not the same as the already-known public bridge-clamp chunk at
`0x0771xx`, and it should not be treated as a proven READ BUFFER response hook
yet. The important point is narrower: it is 8051 runtime code that reads the
same packet shadow neighborhood and has a nearby zero cave.

## Cave Candidate

Logical `0x2cd6..0x2cff` is all zero bytes:

```asm
2ccf  lcall 0x1119
2cd2  ret
2cd3  clr  0x2e.0
2cd5  ret
2cd6  nop
...
2cff  nop
2d00  dec r2
2d01  mov a,r7
```

As a first proof, the cave body can be intentionally boring, for example:

```asm
2cd6  clr a
2cd7  mov psw,a
2cd9  ret
```

and the entry at `0x1406` can be replaced with:

```asm
1406  lcall 0x2cd6
```

That particular smoke patch would probably change behavior too much to run as
a first live experiment. It is mainly a toolchain dry-run target for the
multi-blob writer. A real response hook should preserve the stock gate unless
the host supplies a magic selector.

## Execution Order

Do not start with this hook. The safer ladder remains:

1. prove the post-materializer resident hook can patch materialized normal RAM
   by changing the READ BUFFER clamp from `0x0e` to `0x07`;
2. if that passes and restores, try `0x18` as a decoded-band oracle;
3. only then use the multi-blob writer to install a tiny runtime cave body plus
   trampoline.

The reason for this order is simple: the bridge-clamp proof changes one known
byte in already-observed bridge code. The selector22 response hook changes
control flow in materialized runtime code. It has much higher upside, but it is
a second-stage patch.
