# CDD Patchability Blocker

Scope: static/offline. No drive commands were sent.

## Key Result

The normal-mode READ BUFFER bridge gives us a much smaller concrete target than a full custom hook: a one-byte decoded patch in the bridge clamp could probably turn stock READ BUFFER mode-1 requests into a decoded/controller-range read primitive. The useful byte is visible in the decoded record59 code, but we still do not know how to encode that decoded byte change into the hard CDD source body.

So the blocker is now sharper: not "write arbitrary code into normal mode", but "make one specific decoded byte in a mode-0x80 CDD record change predictably."

## Target Records

| rec | source | source len | decoded abs | span | mode | op key | key repeats | known slots | unique chunks | variants |
|---:|---|---:|---|---:|---:|---|---:|---:|---:|---|
| 55 | `0x25e7a..0x26783` | `0x909` | `0x18a940..0x18acc0` | `0x380` | `0x40` | `a742d3782e04` | 1 | 12 | 6 | 0x1c0, 0x200, 0x240, 0x280, 0x2c0, 0x300, 0x340 |
| 58 | `0x27825..0x28119` | `0x8f4` | `0x18af50..0x18b170` | `0x220` | `0x80` | `66228ca20005` | 1 | 8 | 4 | 0x0b0, 0x130, 0x170, 0x1b0, 0x1f0 |
| 59 | `0x28119..0x28ab7` | `0x99e` | `0x18b170..0x18b2a0` | `0x130` | `0x80` | `30ca94930e05` | 1 | 3 | 3 | 0x010 |
| 60 | `0x28ab7..0x293df` | `0x928` | `0x18b2a0..0x18b5f0` | `0x350` | `0x40` | `950a90757805` | 1 | 10 | 6 | 0x2e0, 0x320 |
| 66 | `0x2bc14..0x2c57f` | `0x96b` | `0x18bdb0..0x18c080` | `0x2d0` | `0x80` | `4e8210adb204` | 1 | 11 | 6 | 0x050, 0x0d0, 0x190, 0x1d0, 0x210 |
| 84 | `0x35f9b..0x36831` | `0x896` | `0x18d4e0..0x18d580` | `0xa0` | `0x80` | `3b0a538aa203` | 1 | 2 | 1 | - |
| 85 | `0x36831..0x370ef` | `0x8be` | `0x18d580..0x18d880` | `0x300` | `0x40` | `5f925170d804` | 1 | 4 | 2 | - |
| 87 | `0x379fc..0x38197` | `0x79b` | `0x18d960..0x18dd50` | `0x3f0` | `0x40` | `0af2177f2e01` | 1 | 14 | 5 | - |

`key repeats` is global across the six DS-8ABSH sibling images in the record map. The hook-relevant hard records have no repeated operation key; there is no same-key crib for them in that set.

## Smallest Useful Patch

The bridge-adjacent code contains this clamp, shown here as bytes:

```text
90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 0e f0
MOV DPTR,#8a4c ; MOVX A,@DPTR ; CLR C ; SUBB A,#0e ; JC pass
MOV DPTR,#4011 ; MOV A,#0e ; MOVX @DPTR,A
```

Stock behavior copies READ BUFFER CDB offset byte 3 into controller register `0x4011`, except values `>= 0x0e` are clamped down to `0x0e`. A decoded patch of the second immediate `0x0e -> 0x18` would make requests with high byte `>= 0x0e` point at `0x18xxxx`. That is exactly where the CDD decoded/controller range begins (`0x184000..0x1b3fff`).

| rec | chunk rel | threshold imm | clamp-output imm | clamp-output decoded abs |
|---:|---:|---:|---:|---:|
| 58 | `0x1b0` | `0x1bf` | `0x1c6` | `0x18b116` |
| 58 | `0x1f0` | `0x1ff` | `0x206` | `0x18b156` |
| 59 | `0x010` | `0x01f` | `0x026` | `0x18b196` |

The record59 hit is the cleanest target. It is in the same record whose source mutation previously affected the normal work-window phase. But that previous source mutation did not give a decoded-byte mapping.

## Why This Still Is Not Patch Control

- The decoded byte we want is known: record59 decoded-relative `0x026`, value `0x0e`, wanted `0x18`.
- Record59 source is a mode-`0x80` hard body, F0 `0x28119..0x28ab7`, operation key `30ca94930e05`; that key is unique in the current six-image sibling map.
- Known output tells us what some decoded bytes are, but not which source bits produce them. The known-output exports also contain repeated public tiles, so duplicated chunks must not be treated as independent flat plaintext.
- The live record59 edit at F0 `0x28519` is strong ownership evidence but weak encoder evidence: it changed scheduling/visibility, not a specific decoded byte.
- XD13 is a semantic plaintext analogue. It helps label routines and register roles, but it uses a different CDD presentation and does not encode DS-8ABSH hard-body bytes.

## Repeated Known Chunks

Repeated decoded-looking 64-byte chunks are useful for semantics but dangerous as encoder cribs. They often reflect public work-window tiling or repeated routines rather than separate source-to-output examples.

| chunk | placements |
|---|---|
| `20ea2ab16891` | rec58+0x1b0, rec58+0x1f0, rec59+0x010 |
| `2111cafaf69c` | rec84+0x020, rec84+0x060, rec85+0x000, rec85+0x040 |
| `b7a129b7d392` | rec59+0x090, rec60+0x020 |

## Source Reuse Check

For target records that expose the same decoded-looking 64-byte tile, the hard-body source records do not contain comparable repeated source blocks. That argues against a local bytewise presentation where the same plaintext chunk is simply copied or lightly masked in source order.

| record pair | source lens | longest exact source overlap | offsets | example |
|---|---|---:|---|---|
| rec58 / rec59 | `0x8f4` / `0x99e` | 6 bytes | `0x501` / `0x2e0` | `c0cb2009c5fb` |
| rec59 / rec60 | `0x99e` / `0x928` | 5 bytes | `0x586` / `0x4f7` | `162499df2a` |
| rec58 / rec60 | `0x8f4` / `0x928` | 9 bytes | `0x17` / `0x340` | `c2d64402c4933be54c` |
| rec84 / rec85 | `0x896` / `0x8be` | 5 bytes | `0x77f` / `0x27` | `3a4ffacede` |

## Practical Next Static Work

1. Focus any future encoder attack on this one decoded-byte target first, not arbitrary code injection.
2. Build or find a non-mutating materialization oracle for record59, then use it to learn source-bit influence on decoded-relative `0x026`.
3. Continue static work around the `0x4e` materializer and mode-2 companion window, because the visible 8051 tells us how to ask the controller to materialize windows even though it does not decode hard bodies itself.
4. Treat CDD source mutations as a later, targeted experiment only after we can observe the exact decoded byte they affect.
