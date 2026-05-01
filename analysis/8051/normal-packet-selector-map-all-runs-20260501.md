# Normal Packet Selector Map

This report condenses the normal-runtime packet-shadow evidence into a
selector/field map. It is based on public `READ BUFFER id=01` work-window
captures, so capture labels show when a code/table chunk was visible, not
a proof that the named command executed that exact branch.

## Summary

- captures scanned: 509
- packet-shadow compare idioms: 35
- packet-shadow/controller edge rows: 12
- `0x8a49` remains the best opcode/selector byte.
- `GET CONFIGURATION` (`0x46`) tags the controller bridge dynamically,
  but a plain `0x8a49 == 0x46` compare has not appeared in the public
  work-window corpus. That means its route may be table-driven, handled
  through an unharvested slice, or dispatched before this compare cluster.

## 0x8a49 Opcode-Like Compares

| value | likely meaning | class | compare forms | count | sample slots |
|---:|---|---|---|---:|---|
| `0x03` | REQUEST SENSE | read/status | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 1527 | `+0x6380`, `+0x63c0`, `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`, `+0x9f00`, `+0x9f40` |
| `0x13` | VERIFY(6) / legacy | unknown | `cjne_a_imm->cjne` | 164 | `+0x9e00`, `+0x9e40`, `+0x9e80` |
| `0x1b` | START STOP UNIT | mechanical | `xrl_a_imm->jnz` | 143 | `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0` |
| `0x28` | READ(10) | read/data | `xrl_a_imm->jz`, `mov_r7_xrl_imm->jz`, `cjne_a_imm->cjne` | 4573 | `+0x6100`, `+0x6140`, `+0x6180`, `+0x61c0`, `+0x6b00`, `+0x6b40`, `+0x6b80`, `+0x6bc0` |
| `0x2a` | WRITE(10) | write/data | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 622 | `+0x6240`, `+0x6280`, `+0x62c0`, `+0x7e00`, `+0x7e40`, `+0x7e80`, `+0x7ec0` |
| `0x55` | MODE SELECT(10) | write/config | `cjne_a_imm->cjne` | 424 | `+0x7f00`, `+0x7f40`, `+0x7f80`, `+0x7fc0` |
| `0x6b` | Vendor / blank-like opcode | unknown | `cjne_a_imm->cjne` | 98 | `+0x9ec0` |
| `0x78` | Vendor / DVD command-class opcode | unknown | `cjne_a_imm->cjne` | 22 | `+0x9e00`, `+0x9e40` |
| `0x7c` | unknown/vendor | unknown | `cjne_a_imm->cjne` | 1 | `+0x9ec0` |
| `0xa1` | BLANK / vendor-adjacent | write/media | `cjne_a_imm->cjne` | 2 | `+0x9ec0` |
| `0xa3` | SEND KEY / MMC security | write/control | `cjne_a_imm->cjne` | 133 | `+0x9100`, `+0x9180` |
| `0xa4` | REPORT KEY / MMC security | read/control | `cjne_a_imm->cjne` | 133 | `+0x9100`, `+0x9180` |
| `0xb4` | READ ELEMENT STATUS ATTACHED / vendor | read/status | `cjne_a_imm->cjne` | 146 | `+0x9e40`, `+0x9e80` |
| `0xcf` | Vendor-specific | unknown | `cjne_a_imm->cjne` | 27 | `+0x9e00`, `+0x9e40` |
| `0xe0` | unknown/vendor | unknown | `cjne_a_imm->cjne` | 23 | `+0x9ec0` |
| `0xe3` | LiteOn/vendor | vendor | `mov_r7_xrl_imm->jz` | 509 | `+0x9740`, `+0x97c0` |
| `0xe6` | LiteOn/vendor | vendor | `mov_r7_cjne_imm->cjne` | 253 | `+0x8800` |
| `0xe7` | LiteOn/vendor | vendor | `cjne_a_imm->cjne` | 509 | `+0x9740`, `+0x97c0` |
| `0xf0` | unknown/vendor | unknown | `cjne_a_imm->cjne` | 2 | `+0x9e00`, `+0x9e40` |
| `0xfc` | unknown/vendor | unknown | `cjne_a_imm->cjne` | 24 | `+0x9ec0` |

## Adjacent Shadow Field Compares

| addr | role sketch | values seen | total compares |
|---:|---|---|---:|
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` x509, `0x01` x509, `0x02` x281, `0x0e` x253 | 1552 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` x509, `0x22` x253 | 762 |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x01` x85 | 85 |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0x01` x509, `0xf0` x361, `0xfe` x39 | 909 |
| `0x8a4e` | CDB byte 5 or reused controller/status byte | - | 0 |
| `0x8a4f` | CDB byte 6 / payload field | - | 0 |
| `0x8a50` | CDB byte 7 / payload field | - | 0 |
| `0x8a51` | CDB byte 8 / payload field | - | 0 |
| `0x8a52` | CDB byte 9 / payload field | - | 0 |
| `0x8a53` | CDB byte 10 or reused controller/status byte | `0x01` x353 | 353 |
| `0x8a54` | CDB byte 11 or reused controller/status byte | - | 0 |

## Shadow Byte Edge Sketch

| addr | role sketch | strongest observed edges |
|---:|---|---|
| `0x8a49` | CDB byte 0 / opcode selector | - |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x47b1->0x8a4a` fifo x509 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x47b1->0x8a4b` fifo x509 |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x8a4c->0x4011` ctrl x509; `0x47b1->0x8a4c` fifo x136 |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0x47b1->0x8a4d` fifo x509; `0x8a4d->0x4012` ctrl x509; `0x8a4d->0x47d6` copy x433; `0x8a4d->0x85ff` copy x114; `0x4099->0x8a4d` ctrl x12 |
| `0x8a4e` | CDB byte 5 or reused controller/status byte | `0x47b1->0x8a4e` fifo x509; `0x8a4e->0x4013` ctrl x509; `0x8a4e->0x4099` ctrl x506; `0x4099->0x8a4e` ctrl x39; `0x8a4e->0x47b1` fifo x2 |
| `0x8a4f` | CDB byte 6 / payload field | `0x47b1->0x8a4f` fifo x509; `0x8a4f->0x47d6` copy x277; `0x8a4f->0x47b1` fifo x2 |
| `0x8a50` | CDB byte 7 / payload field | `0x47b1->0x8a50` fifo x509; `0x8a50->0x85f4` copy x361; `0x8a50->0x47b1` fifo x2 |
| `0x8a51` | CDB byte 8 / payload field | `0x47b1->0x8a51` fifo x509; `0x8a51->0x85f5` copy x361 |
| `0x8a52` | CDB byte 9 / payload field | `0x47b1->0x8a52` fifo x509 |
| `0x8a53` | CDB byte 10 or reused controller/status byte | `0x47b1->0x8a53` fifo x509; `0x8a53->0x4099` ctrl x506; `0x4099->0x8a53` ctrl x303; `0x8a53->0x47b1` fifo x277 |
| `0x8a54` | CDB byte 11 or reused controller/status byte | `0x8a54->0x4099` ctrl x506; `0x4099->0x8a54` ctrl x303; `0x8a54->0x47b1` fifo x277; `0x8a54->0x40b7` ctrl x268; `0x47b1->0x8a54` fifo x225 |

## Practical Read

- `0x8a49` is a real command-like selector, but it is not the whole story.
  The visible compare cluster includes ordinary read/write opcodes, MMC
  security-style opcodes, and LiteOn/vendor values. The GET CONFIG path
  that currently looks most useful does not show up as a simple `0x46`
  compare here.
- The `+0x8bxx` START STOP snippet gives a strong byte-map anchor:
  it checks `0x8a49 == 0x1b` and `(0x8a4d & 0x0f) == 0x02`, matching
  CDB byte 4's load/eject/start control bits. So `0x8a49..` should
  now be read as a packet/CDB shadow, with later bytes sometimes reused
  as controller response/data shadows.
- `0x8a4d` and `0x8a4e` are still the best field-control suspects for a
  future fast oracle. `0x8a4d` is confirmed as CDB byte 4 in at least
  the START STOP path, and both bytes bridge into `0x4012/0x4013` or
  `0x4099` paths.
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
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | xrl_a_imm | jz | 2028 | `+0x8700`, `+0x9600`, `+0x9780`, `+0x9c40`, `+0x8780`, `+0x8740`, `+0x87c0`, `+0x9c80` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | mov_r7_xrl_imm | jz | 1527 | `+0x61c0`, `+0x9600`, `+0x9bc0`, `+0x6180`, `+0x6100`, `+0x6140`, `+0x9b00` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x03` | cjne_a_imm | cjne | 1018 | `+0x8700`, `+0x9f00`, `+0x8780`, `+0x9f80`, `+0x8740`, `+0x87c0`, `+0x9f40`, `+0x9fc0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | cjne_a_imm | cjne | 1018 | `+0x6b00`, `+0x9900`, `+0x6b80`, `+0x6bc0`, `+0x6b40`, `+0x9940`, `+0x99c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x03` | xrl_a_imm | jz | 509 | `+0x63c0`, `+0x6380` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xe3` | mov_r7_xrl_imm | jz | 509 | `+0x9740`, `+0x97c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xe7` | cjne_a_imm | cjne | 509 | `+0x9740`, `+0x97c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x2a` | cjne_a_imm | cjne | 430 | `+0x7e40`, `+0x7ec0`, `+0x7e80`, `+0x7e00` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x55` | cjne_a_imm | cjne | 424 | `+0x7f40`, `+0x7fc0`, `+0x7f80`, `+0x7f00` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xe6` | mov_r7_cjne_imm | cjne | 253 | `+0x8800` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x2a` | xrl_a_imm | jz | 192 | `+0x6240`, `+0x6280`, `+0x62c0` | `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command`, `normal-work-window-error-path-pairs-20260501/02-cycle00-read-toc-format-0-after-request-sense` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x13` | cjne_a_imm | cjne | 164 | `+0x9e00`, `+0x9e80`, `+0x9e40` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xb4` | cjne_a_imm | cjne | 146 | `+0x9e40`, `+0x9e80` | `normal-work-window-get-config-r5-f0-isolated-20260501/27-cycle13-r5-f0-current-sf0000`, `normal-work-window-get-config-r5-f0-isolated-20260501/28-cycle14-baseline-no-stimulus` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x1b` | xrl_a_imm | jnz | 143 | `+0x8b80`, `+0x8bc0`, `+0x8b00`, `+0x8b40` | `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command`, `normal-work-window-error-path-pairs-20260501/02-cycle00-read-toc-format-0-after-request-sense` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa3` | cjne_a_imm | cjne | 133 | `+0x9180`, `+0x9100` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa4` | cjne_a_imm | cjne | 133 | `+0x9180`, `+0x9100` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x6b` | cjne_a_imm | cjne | 98 | `+0x9ec0` | `normal-work-window-get-config-field-variants-r5-long-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-get-config-field-variants-r5-long-20260501/01-cycle00-std-current-sf0000-len00fc` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xcf` | cjne_a_imm | cjne | 27 | `+0x9e00`, `+0x9e40` | `normal-work-window-get-config-field-variants-20260501/01-cycle00-std-current-sf0000-len00fc`, `normal-work-window-get-config-field-variants-20260501/02-cycle00-std-current-sf0020-len00fc` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xfc` | cjne_a_imm | cjne | 24 | `+0x9ec0` | `normal-work-window-get-config-variants-20260501/01-cycle00-get-config-current-sf0000-len0010`, `normal-work-window-get-config-variants-20260501/02-cycle00-get-config-current-sf0000-len0040` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xe0` | cjne_a_imm | cjne | 23 | `+0x9ec0` | `normal-work-window-error-path-pairs-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-error-path-pairs-20260501/01-cycle00-read-toc-format-0-after-command` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x78` | cjne_a_imm | cjne | 22 | `+0x9e00`, `+0x9e40` | `normal-work-window-get-config-field-variants-20260501/00-cycle00-baseline-no-stimulus`, `normal-work-window-get-config-field-variants-20260501/12-cycle01-std-current-sf0020-len00fc` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa1` | cjne_a_imm | cjne | 2 | `+0x9ec0` | `normal-work-window-stimuli-focused-20260501/05-cycle01-inquiry-extrainq`, `normal-work-window-stimuli-focused-20260501/30-cycle06-inquiry-extrainq` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xf0` | cjne_a_imm | cjne | 2 | `+0x9e00`, `+0x9e40` | `normal-work-window-get-config-field-variants-20260501/11-cycle01-std-current-sf0000-len00fc`, `normal-work-window-isolated-extrainq-20260501/08-cycle04-baseline-no-stimulus` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x7c` | cjne_a_imm | cjne | 1 | `+0x9ec0` | `normal-work-window-stimuli-focused-20260501/15-cycle03-inquiry-extrainq` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x01` | cjne_a_imm | cjne | 509 | `+0x6740`, `+0x67c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` | xrl_a_imm | jnz | 509 | `+0x6540`, `+0x6580` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x02` | xrl_a_imm | jz | 281 | `+0x7e40`, `+0x7ec0`, `+0x7e80`, `+0x7e00` | `normal-work-window-get-config-current-long-20260501/01-cycle00-get-configuration-current`, `normal-work-window-get-config-current-long-20260501/02-cycle01-baseline-no-stimulus` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x0e` | cjne_a_imm | cjne | 253 | `+0x8800` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` | mov_r7_xrl_imm | jz | 509 | `+0x7240`, `+0x7200` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x22` | cjne_a_imm | cjne | 253 | `+0x8800` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x01` | mov_r7_xrl_imm | jz | 85 | `+0x9540`, `+0x9580`, `+0x9500`, `+0x95c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/07-capture-only` |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0x01` | cjne_a_imm | cjne | 509 | `+0x8d40`, `+0x8d00` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0xf0` | cjne_a_imm | cjne | 361 | `+0x6700` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0xfe` | cjne_a_imm | cjne | 39 | `+0x7180`, `+0x7140`, `+0x7100` | `normal-work-window-get-config-current-long-20260501/05-cycle02-get-configuration-current`, `normal-work-window-get-config-current-long-20260501/21-cycle10-get-configuration-current` |
| `0x8a53` | CDB byte 10 or reused controller/status byte | `0x01` | cjne_a_imm | cjne | 353 | `+0x9040`, `+0x9080` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
