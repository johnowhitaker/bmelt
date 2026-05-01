# Normal Read/Status Correlation Pass

Host: `jonathan-thinkpad-t480s`
Drive: `PLDS DVD+-RW DS-8ABSH LD5M`
Evidence:
`references/evidence/live/normal-work-window-readstatus-correlation-20260501`

This was a read-only normal-runtime probe to look for a cleaner command family
than GET CONFIGURATION for the packet-shadow/controller bridge. It ran four
cycles of:

- baseline capture;
- `REQUEST SENSE`;
- `READ TOC/PMA/ATIP` formats `0`, `1`, `2`, and `4`;
- `GET PERFORMANCE` type `0x00`;
- `GET PERFORMANCE` type `0x03`.

The drive remained in normal `LD5M` afterwards. `REQUEST SENSE` and
`GET PERFORMANCE type03` returned GOOD. The no-disc `READ TOC` commands and
`GET PERFORMANCE type00` returned expected CHECK/failed status with no data.

## Main Observations

The strongest recurring stimulus-only chunk was:

```text
0x8b00/+0x8b40/+0x8b80/+0x8bc0
sha256 prefix 707389d4505f
sample        8a34e04404f0908a29e020e042105202
target refs   0x8a49, 0x8a4d
```

It appeared for every failed `READ TOC` format and every failed
`GET PERFORMANCE type00`, but not for the successful `GET PERFORMANCE type03`
or ordinary `REQUEST SENSE`. This looks like an error/status path rather than
the good-response bridge, but it is useful because it consistently exposes the
opcode/selector byte and the length/count-ish byte in one stimulus class.

The same chunk contains a concrete CDB-shadow anchor:

```text
90 8a 49 e0 64 1b 70 27      ; compare CDB[0] with START STOP UNIT
90 8a 4d e0 54 0f ff bf 02   ; compare CDB[4] low nibble with 0x02
```

For START STOP UNIT, CDB byte 4 carries the load/eject/start bits. Low nibble
`0x02` is the eject-style case. That means `0x8a4d` is not merely a generic
count byte; it is CDB byte 4 at least in this path. The better current map is
`0x8a49 = CDB[0]`, `0x8a4a = CDB[1]`, and so on, with later shadow bytes also
serving as controller response/data staging in some handlers.

A second recurring chunk in the same failed-command set touched the controller
gateway:

```text
+0x7140/+0x7180
sha256 prefix 8b2115cd509f
target refs   0x4000, 0x4091, 0x4093, 0x4098
```

This is a different flavor from the clean GET CONFIGURATION bridge, which was
centered around `0x4099` response bytes copied back into `0x8a4e/0x8a53/0x8a54`.
The failed TOC/performance path seems to expose a read-side `0x4098` gateway
surface instead.

`GET PERFORMANCE type03` is still worth keeping in the safe-command set: it
returned GOOD and sometimes exposed the `0x8a4c` FIFO-intake chunk, but it did
not produce a stable bridge signature in only four cycles.

## Interpretation

This pass separates two normal-runtime surfaces:

1. GET CONFIGURATION good-response path:
   `0x4099` traffic copied into `0x8a4e/0x8a53/0x8a54`.
2. Failed read/status path from no-disc TOC/performance requests:
   `0x8a49/0x8a4d` selector/count checks plus a `0x4098` gateway-looking
   snippet.

The failed path is not the fast oracle by itself, but it may be a cleaner way
to map packet-shadow field roles because the same chunk appears for a coherent
set of commands. The next live correlation should vary one of these families
more deliberately rather than sweep broadly: for example, `READ TOC` format,
MSF bit, allocation length, and immediate post-failure `REQUEST SENSE`, while
watching whether the `0x8bxx` and `0x7140/+0x7180` chunks move together.
