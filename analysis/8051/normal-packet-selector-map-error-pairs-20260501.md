# Normal Packet Selector Map

This report condenses the normal-runtime packet-shadow evidence into a
selector/field map. It is based on public `READ BUFFER id=01` work-window
captures, so capture labels show when a code/table chunk was visible, not
a proof that the named command executed that exact branch.

## Summary

- captures scanned: 21
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
| `0x03` | REQUEST SENSE | read/status | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 63 | `+0x63c0`, `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`, `+0x9f80` |
| `0x1b` | START STOP UNIT | mechanical | `xrl_a_imm->jnz` | 17 | `+0x8b00`, `+0x8b80`, `+0x8bc0` |
| `0x28` | READ(10) | read/data | `xrl_a_imm->jz`, `mov_r7_xrl_imm->jz`, `cjne_a_imm->cjne` | 189 | `+0x6100`, `+0x6180`, `+0x6b00`, `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`, `+0x9600` |
| `0x2a` | WRITE(10) | write/data | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 39 | `+0x6240`, `+0x6280`, `+0x7e40` |
| `0x55` | MODE SELECT(10) | write/config | `cjne_a_imm->cjne` | 21 | `+0x7f00`, `+0x7f40`, `+0x7f80`, `+0x7fc0` |
| `0xa3` | SEND KEY / MMC security | write/control | `cjne_a_imm->cjne` | 20 | `+0x9180` |
| `0xa4` | REPORT KEY / MMC security | read/control | `cjne_a_imm->cjne` | 20 | `+0x9180` |
| `0xe0` | unknown/vendor | unknown | `cjne_a_imm->cjne` | 21 | `+0x9ec0` |
| `0xe3` | LiteOn/vendor | vendor | `mov_r7_xrl_imm->jz` | 21 | `+0x9740` |
| `0xe6` | LiteOn/vendor | vendor | `mov_r7_cjne_imm->cjne` | 21 | `+0x8800` |
| `0xe7` | LiteOn/vendor | vendor | `cjne_a_imm->cjne` | 21 | `+0x9740` |

## Adjacent Shadow Field Compares

| addr | role sketch | values seen | total compares |
|---:|---|---|---:|
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` x21, `0x01` x21, `0x0e` x21 | 63 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` x21, `0x22` x21 | 42 |
| `0x8a4c` | controller setup high-ish byte | `0x01` x2 | 2 |
| `0x8a4d` | length/count-ish byte | `0xf0` x21, `0x01` x21 | 42 |
| `0x8a4e` | subselector/status byte; low nibble tested | - | 0 |
| `0x8a4f` | payload/field byte | - | 0 |
| `0x8a50` | payload/field byte | - | 0 |
| `0x8a51` | payload/field byte | - | 0 |
| `0x8a52` | payload/field byte | - | 0 |
| `0x8a53` | controller response/data shadow byte | `0x01` x21 | 21 |
| `0x8a54` | controller response/data shadow byte | - | 0 |

## Shadow Byte Edge Sketch

| addr | role sketch | strongest observed edges |
|---:|---|---|
| `0x8a49` | opcode/selector candidate | - |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x47b1->0x8a4a` fifo x21 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x47b1->0x8a4b` fifo x21 |
| `0x8a4c` | controller setup high-ish byte | `0x8a4c->0x4011` ctrl x21; `0x47b1->0x8a4c` fifo x10 |
| `0x8a4d` | length/count-ish byte | `0x47b1->0x8a4d` fifo x21; `0x8a4d->0x4012` ctrl x21; `0x8a4d->0x47d6` copy x21 |
| `0x8a4e` | subselector/status byte; low nibble tested | `0x47b1->0x8a4e` fifo x21; `0x8a4e->0x4013` ctrl x21; `0x8a4e->0x4099` ctrl x21 |
| `0x8a4f` | payload/field byte | `0x47b1->0x8a4f` fifo x21 |
| `0x8a50` | payload/field byte | `0x47b1->0x8a50` fifo x21; `0x8a50->0x85f4` copy x21 |
| `0x8a51` | payload/field byte | `0x47b1->0x8a51` fifo x21; `0x8a51->0x85f5` copy x21 |
| `0x8a52` | payload/field byte | `0x47b1->0x8a52` fifo x21 |
| `0x8a53` | controller response/data shadow byte | `0x47b1->0x8a53` fifo x21; `0x8a53->0x4099` ctrl x21 |
| `0x8a54` | controller response/data shadow byte | `0x8a54->0x4099` ctrl x21; `0x47b1->0x8a54` fifo x10 |

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
| `0x8a49` | opcode/selector candidate | `0x28` | xrl_a_imm | jz | 84 | `+0x8700`, `+0x9600`, `+0x9780`, `+0x9c40`, `+0x8740`, `+0x8780`, `+0x87c0` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x28` | mov_r7_xrl_imm | jz | 63 | `+0x6100`, `+0x9600`, `+0x9bc0`, `+0x6180` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x03` | cjne_a_imm | cjne | 42 | `+0x8700`, `+0x9f80`, `+0x8740`, `+0x8780`, `+0x87c0` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x28` | cjne_a_imm | cjne | 42 | `+0x6b00`, `+0x9900` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus` |
| `0x8a49` | opcode/selector candidate | `0x03` | xrl_a_imm | jz | 21 | `+0x63c0` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | opcode/selector candidate | `0x2a` | cjne_a_imm | cjne | 21 | `+0x7e40` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | opcode/selector candidate | `0x55` | cjne_a_imm | cjne | 21 | `+0x7fc0`, `+0x7f40`, `+0x7f80`, `+0x7f00` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | opcode/selector candidate | `0xe0` | cjne_a_imm | cjne | 21 | `+0x9ec0` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | opcode/selector candidate | `0xe3` | mov_r7_xrl_imm | jz | 21 | `+0x9740` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | opcode/selector candidate | `0xe6` | mov_r7_cjne_imm | cjne | 21 | `+0x8800` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | opcode/selector candidate | `0xe7` | cjne_a_imm | cjne | 21 | `+0x9740` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | opcode/selector candidate | `0xa3` | cjne_a_imm | cjne | 20 | `+0x9180` | `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command`, `normal-work-window-error-path-pairs-20260501/02-cycle00-read-toc-format-0-after-request-sense` |
| `0x8a49` | opcode/selector candidate | `0xa4` | cjne_a_imm | cjne | 20 | `+0x9180` | `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command`, `normal-work-window-error-path-pairs-20260501/02-cycle00-read-toc-format-0-after-request-sense` |
| `0x8a49` | opcode/selector candidate | `0x2a` | xrl_a_imm | jz | 18 | `+0x6240`, `+0x6280` | `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command`, `normal-work-window-error-path-pairs-20260501/02-cycle00-read-toc-format-0-after-request-sense` |
| `0x8a49` | opcode/selector candidate | `0x1b` | xrl_a_imm | jnz | 17 | `+0x8b80`, `+0x8bc0`, `+0x8b00` | `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command`, `normal-work-window-error-path-pairs-20260501/02-cycle00-read-toc-format-0-after-request-sense` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x01` | cjne_a_imm | cjne | 21 | `+0x6740` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` | xrl_a_imm | jnz | 21 | `+0x6540` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x0e` | cjne_a_imm | cjne | 21 | `+0x8800` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x22` | cjne_a_imm | cjne | 21 | `+0x8800` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` | mov_r7_xrl_imm | jz | 21 | `+0x7240` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a4c` | controller setup high-ish byte | `0x01` | mov_r7_xrl_imm | jz | 2 | `+0x9500`, `+0x9580` | `normal-work-window-error-path-pairs-20260501/03-cycle00-read-toc-format-4-after-command`, `normal-work-window-error-path-pairs-20260501/05-cycle00-get-performance-type00-after-command` |
| `0x8a4d` | length/count-ish byte | `0x01` | cjne_a_imm | cjne | 21 | `+0x8d40` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a4d` | length/count-ish byte | `0xf0` | cjne_a_imm | cjne | 21 | `+0x6700` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a53` | controller response/data shadow byte | `0x01` | cjne_a_imm | cjne | 21 | `+0x9040` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
