# Normal Packet Selector Map

This report condenses the normal-runtime packet-shadow evidence into a
selector/field map. It is based on public `READ BUFFER id=01` work-window
captures, so capture labels show when a code/table chunk was visible, not
a proof that the named command executed that exact branch.

## Summary

- captures scanned: 32
- packet-shadow compare idioms: 24
- packet-shadow/controller edge rows: 12
- `0x8a49` remains the best opcode/selector byte.
- `GET CONFIGURATION` (`0x46`) tags the controller bridge dynamically,
  but a plain `0x8a49 == 0x46` compare has not appeared in the public
  work-window corpus. That means its route may be table-driven, handled
  through an unharvested slice, or dispatched before this compare cluster.

## 0x8a49 Opcode-Like Compares

| value | likely meaning | class | compare forms | count | sample slots |
|---:|---|---|---|---:|---|
| `0x03` | REQUEST SENSE | read/status | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 96 | `+0x63c0`, `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`, `+0x9f80` |
| `0x13` | VERIFY(6) / legacy | unknown | `cjne_a_imm->cjne` | 32 | `+0x9e40` |
| `0x1b` | START STOP UNIT | mechanical | `xrl_a_imm->jnz` | 20 | `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0` |
| `0x28` | READ(10) | read/data | `xrl_a_imm->jz`, `mov_r7_xrl_imm->jz`, `cjne_a_imm->cjne` | 288 | `+0x6100`, `+0x6180`, `+0x61c0`, `+0x6b00`, `+0x6b40`, `+0x6b80`, `+0x8700`, `+0x8740` |
| `0x2a` | WRITE(10) | write/data | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 62 | `+0x6280`, `+0x7ec0` |
| `0x55` | MODE SELECT(10) | write/config | `cjne_a_imm->cjne` | 29 | `+0x7f40`, `+0x7f80`, `+0x7fc0` |
| `0xa3` | SEND KEY / MMC security | write/control | `cjne_a_imm->cjne` | 30 | `+0x9180` |
| `0xa4` | REPORT KEY / MMC security | read/control | `cjne_a_imm->cjne` | 30 | `+0x9180` |
| `0xe3` | LiteOn/vendor | vendor | `mov_r7_xrl_imm->jz` | 32 | `+0x9740` |
| `0xe6` | LiteOn/vendor | vendor | `mov_r7_cjne_imm->cjne` | 32 | `+0x8800` |
| `0xe7` | LiteOn/vendor | vendor | `cjne_a_imm->cjne` | 32 | `+0x9740` |

## Adjacent Shadow Field Compares

| addr | role sketch | values seen | total compares |
|---:|---|---|---:|
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` x32, `0x01` x32, `0x0e` x32 | 96 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` x32, `0x22` x32 | 64 |
| `0x8a4c` | controller setup high-ish byte | `0x01` x6 | 6 |
| `0x8a4d` | length/count-ish byte | `0xf0` x32, `0x01` x32 | 64 |
| `0x8a4e` | subselector/status byte; low nibble tested | - | 0 |
| `0x8a4f` | payload/field byte | - | 0 |
| `0x8a50` | payload/field byte | - | 0 |
| `0x8a51` | payload/field byte | - | 0 |
| `0x8a52` | payload/field byte | - | 0 |
| `0x8a53` | controller response/data shadow byte | `0x01` x32 | 32 |
| `0x8a54` | controller response/data shadow byte | - | 0 |

## Shadow Byte Edge Sketch

| addr | role sketch | strongest observed edges |
|---:|---|---|
| `0x8a49` | opcode/selector candidate | - |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x47b1->0x8a4a` fifo x32 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x47b1->0x8a4b` fifo x32 |
| `0x8a4c` | controller setup high-ish byte | `0x8a4c->0x4011` ctrl x32; `0x47b1->0x8a4c` fifo x12 |
| `0x8a4d` | length/count-ish byte | `0x47b1->0x8a4d` fifo x32; `0x8a4d->0x4012` ctrl x32; `0x8a4d->0x47d6` copy x32 |
| `0x8a4e` | subselector/status byte; low nibble tested | `0x47b1->0x8a4e` fifo x32; `0x8a4e->0x4013` ctrl x32; `0x8a4e->0x4099` ctrl x32 |
| `0x8a4f` | payload/field byte | `0x47b1->0x8a4f` fifo x32; `0x8a4f->0x47d6` copy x7 |
| `0x8a50` | payload/field byte | `0x47b1->0x8a50` fifo x32; `0x8a50->0x85f4` copy x32 |
| `0x8a51` | payload/field byte | `0x47b1->0x8a51` fifo x32; `0x8a51->0x85f5` copy x32 |
| `0x8a52` | payload/field byte | `0x47b1->0x8a52` fifo x32 |
| `0x8a53` | controller response/data shadow byte | `0x47b1->0x8a53` fifo x32; `0x8a53->0x4099` ctrl x32; `0x8a53->0x47b1` fifo x7 |
| `0x8a54` | controller response/data shadow byte | `0x8a54->0x4099` ctrl x32; `0x47b1->0x8a54` fifo x17; `0x8a54->0x40b7` ctrl x7; `0x8a54->0x47b1` fifo x7 |

## Practical Read

- `0x8a49` is a real command-like selector, but it is not the whole story.
  The visible compare cluster includes ordinary read/write opcodes, MMC
  security-style opcodes, and LiteOn/vendor values. The GET CONFIG path
  that currently looks most useful does not show up as a simple `0x46`
  compare here.
- `0x8a4d` and `0x8a4e` are still the best field-control suspects for a
  future fast oracle. They are checked locally and also bridge into
  `0x4012/0x4013` or `0x4099` paths.
- The safest live-probe candidates remain read/status commands that already
  completed cleanly: `INQUIRY`, `REQUEST SENSE`, `MODE SENSE(10)`,
  `GET CONFIGURATION`, `GET EVENT STATUS`, `READ TOC`, and DVD-structure
  reads. `START STOP`, write/data opcodes, and vendor/security opcodes may
  be informative, but should be separated from benign read-only mapping.
- A useful next live experiment is not a wider random command sweep. It is a
  focused correlation run that captures the work window after controlled
  field variations for one command family, then asks whether the bridge
  snippets move with `0x8a4d/0x8a4e`-like length/subselector fields.

## Raw Compare Rows

| addr | role | value | kind | branch | count | sample slots | sample captures |
|---:|---|---:|---|---|---:|---|---|
| `0x8a49` | opcode/selector candidate | `0x28` | xrl_a_imm | jz | 128 | `+0x8780`, `+0x9600`, `+0x9780`, `+0x9c40`, `+0x8740`, `+0x8700`, `+0x87c0` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x28` | mov_r7_xrl_imm | jz | 96 | `+0x6180`, `+0x9600`, `+0x9bc0`, `+0x61c0`, `+0x6100` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x03` | cjne_a_imm | cjne | 64 | `+0x8780`, `+0x9f80`, `+0x8740`, `+0x8700`, `+0x87c0` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x28` | cjne_a_imm | cjne | 64 | `+0x6b80`, `+0x9900`, `+0x6b00`, `+0x6b40` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x03` | xrl_a_imm | jz | 32 | `+0x63c0` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a49` | opcode/selector candidate | `0x13` | cjne_a_imm | cjne | 32 | `+0x9e40` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a49` | opcode/selector candidate | `0x2a` | cjne_a_imm | cjne | 32 | `+0x7ec0` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a49` | opcode/selector candidate | `0xe3` | mov_r7_xrl_imm | jz | 32 | `+0x9740` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a49` | opcode/selector candidate | `0xe6` | mov_r7_cjne_imm | cjne | 32 | `+0x8800` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a49` | opcode/selector candidate | `0xe7` | cjne_a_imm | cjne | 32 | `+0x9740` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a49` | opcode/selector candidate | `0x2a` | xrl_a_imm | jz | 30 | `+0x6280` | `normal-work-window-readstatus-correlation-20260501/02-cycle00-read-toc-format-0`, `normal-work-window-readstatus-correlation-20260501/03-cycle00-read-toc-format-1` |
| `0x8a49` | opcode/selector candidate | `0xa3` | cjne_a_imm | cjne | 30 | `+0x9180` | `normal-work-window-readstatus-correlation-20260501/02-cycle00-read-toc-format-0`, `normal-work-window-readstatus-correlation-20260501/03-cycle00-read-toc-format-1` |
| `0x8a49` | opcode/selector candidate | `0xa4` | cjne_a_imm | cjne | 30 | `+0x9180` | `normal-work-window-readstatus-correlation-20260501/02-cycle00-read-toc-format-0`, `normal-work-window-readstatus-correlation-20260501/03-cycle00-read-toc-format-1` |
| `0x8a49` | opcode/selector candidate | `0x55` | cjne_a_imm | cjne | 29 | `+0x7fc0`, `+0x7f80`, `+0x7f40` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a49` | opcode/selector candidate | `0x1b` | xrl_a_imm | jnz | 20 | `+0x8b00`, `+0x8b80`, `+0x8b40`, `+0x8bc0` | `normal-work-window-readstatus-correlation-20260501/02-cycle00-read-toc-format-0`, `normal-work-window-readstatus-correlation-20260501/03-cycle00-read-toc-format-1` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x01` | cjne_a_imm | cjne | 32 | `+0x6740` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` | xrl_a_imm | jnz | 32 | `+0x6540` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x0e` | cjne_a_imm | cjne | 32 | `+0x8800` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x22` | cjne_a_imm | cjne | 32 | `+0x8800` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` | mov_r7_xrl_imm | jz | 32 | `+0x7240` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a4c` | controller setup high-ish byte | `0x01` | mov_r7_xrl_imm | jz | 6 | `+0x9580`, `+0x9540`, `+0x95c0` | `normal-work-window-readstatus-correlation-20260501/07-cycle00-get-performance-type03`, `normal-work-window-readstatus-correlation-20260501/15-cycle01-get-performance-type03` |
| `0x8a4d` | length/count-ish byte | `0x01` | cjne_a_imm | cjne | 32 | `+0x8d40` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a4d` | length/count-ish byte | `0xf0` | cjne_a_imm | cjne | 32 | `+0x6700` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
| `0x8a53` | controller response/data shadow byte | `0x01` | cjne_a_imm | cjne | 32 | `+0x9040` | `normal-work-window-readstatus-correlation-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-readstatus-correlation-20260501/01-cycle00-request-sense` |
