# Normal Packet Selector Map

This report condenses the normal-runtime packet-shadow evidence into a
selector/field map. It is based on public `READ BUFFER id=01` work-window
captures, so capture labels show when a code/table chunk was visible, not
a proof that the named command executed that exact branch.

## Summary

- captures scanned: 208
- packet-shadow compare idioms: 32
- packet-shadow/controller edge rows: 12
- `0x8a49` remains the best opcode/selector byte.
- `GET CONFIGURATION` (`0x46`) tags the controller bridge dynamically,
  but a plain `0x8a49 == 0x46` compare has not appeared in the public
  work-window corpus. That means its route may be table-driven, handled
  through an unharvested slice, or dispatched before this compare cluster.

## 0x8a49 Opcode-Like Compares

| value | likely meaning | class | compare forms | count | sample slots |
|---:|---|---|---|---:|---|
| `0x03` | REQUEST SENSE | read/status | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 624 | `+0x6380`, `+0x63c0`, `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`, `+0x9f00`, `+0x9f40` |
| `0x13` | VERIFY(6) / legacy | unknown | `cjne_a_imm->cjne` | 58 | `+0x9e00`, `+0x9e40`, `+0x9e80` |
| `0x1b` | START STOP UNIT | mechanical | `xrl_a_imm->jnz` | 106 | `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0` |
| `0x28` | READ(10) | read/data | `xrl_a_imm->jz`, `mov_r7_xrl_imm->jz`, `cjne_a_imm->cjne` | 1872 | `+0x6100`, `+0x6140`, `+0x6180`, `+0x61c0`, `+0x6b00`, `+0x6b40`, `+0x6b80`, `+0x6bc0` |
| `0x2a` | WRITE(10) | write/data | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 308 | `+0x6240`, `+0x6280`, `+0x62c0`, `+0x7e40`, `+0x7e80`, `+0x7ec0` |
| `0x55` | MODE SELECT(10) | write/config | `cjne_a_imm->cjne` | 161 | `+0x7f40`, `+0x7f80`, `+0x7fc0` |
| `0x6b` | Vendor / blank-like opcode | unknown | `cjne_a_imm->cjne` | 12 | `+0x9ec0` |
| `0x78` | Vendor / DVD command-class opcode | unknown | `cjne_a_imm->cjne` | 4 | `+0x9e00`, `+0x9e40` |
| `0x7c` | unknown/vendor | unknown | `cjne_a_imm->cjne` | 1 | `+0x9ec0` |
| `0xa1` | BLANK / vendor-adjacent | write/media | `cjne_a_imm->cjne` | 2 | `+0x9ec0` |
| `0xa3` | SEND KEY / MMC security | write/control | `cjne_a_imm->cjne` | 83 | `+0x9100`, `+0x9180` |
| `0xa4` | REPORT KEY / MMC security | read/control | `cjne_a_imm->cjne` | 83 | `+0x9100`, `+0x9180` |
| `0xb4` | READ ELEMENT STATUS ATTACHED / vendor | read/status | `cjne_a_imm->cjne` | 129 | `+0x9e40`, `+0x9e80` |
| `0xcf` | Vendor-specific | unknown | `cjne_a_imm->cjne` | 2 | `+0x9e00` |
| `0xe3` | LiteOn/vendor | vendor | `mov_r7_xrl_imm->jz` | 208 | `+0x9740`, `+0x97c0` |
| `0xe6` | LiteOn/vendor | vendor | `mov_r7_cjne_imm->cjne` | 94 | `+0x8800` |
| `0xe7` | LiteOn/vendor | vendor | `cjne_a_imm->cjne` | 208 | `+0x9740`, `+0x97c0` |

## Adjacent Shadow Field Compares

| addr | role sketch | values seen | total compares |
|---:|---|---|---:|
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` x208, `0x01` x208, `0x0e` x94, `0x02` x51 | 561 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` x208, `0x22` x94 | 302 |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x01` x29 | 29 |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0x01` x208, `0xf0` x202, `0xfe` x4 | 414 |
| `0x8a4e` | CDB byte 5 or reused controller/status byte | - | 0 |
| `0x8a4f` | CDB byte 6 / payload field | - | 0 |
| `0x8a50` | CDB byte 7 / payload field | - | 0 |
| `0x8a51` | CDB byte 8 / payload field | - | 0 |
| `0x8a52` | CDB byte 9 / payload field | - | 0 |
| `0x8a53` | CDB byte 10 or reused controller/status byte | `0x01` x194 | 194 |
| `0x8a54` | CDB byte 11 or reused controller/status byte | - | 0 |

## Shadow Byte Edge Sketch

| addr | role sketch | strongest observed edges |
|---:|---|---|
| `0x8a49` | CDB byte 0 / opcode selector | - |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x47b1->0x8a4a` fifo x208 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x47b1->0x8a4b` fifo x208 |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x8a4c->0x4011` ctrl x208; `0x47b1->0x8a4c` fifo x50 |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0x47b1->0x8a4d` fifo x208; `0x8a4d->0x4012` ctrl x208; `0x8a4d->0x47d6` copy x167; `0x8a4d->0x85ff` copy x114 |
| `0x8a4e` | CDB byte 5 or reused controller/status byte | `0x47b1->0x8a4e` fifo x208; `0x8a4e->0x4013` ctrl x208; `0x8a4e->0x4099` ctrl x206; `0x4099->0x8a4e` ctrl x4; `0x8a4e->0x47b1` fifo x2 |
| `0x8a4f` | CDB byte 6 / payload field | `0x47b1->0x8a4f` fifo x208; `0x8a4f->0x47d6` copy x60; `0x8a4f->0x47b1` fifo x2 |
| `0x8a50` | CDB byte 7 / payload field | `0x47b1->0x8a50` fifo x208; `0x8a50->0x85f4` copy x202; `0x8a50->0x47b1` fifo x2 |
| `0x8a51` | CDB byte 8 / payload field | `0x47b1->0x8a51` fifo x208; `0x8a51->0x85f5` copy x202 |
| `0x8a52` | CDB byte 9 / payload field | `0x47b1->0x8a52` fifo x208 |
| `0x8a53` | CDB byte 10 or reused controller/status byte | `0x47b1->0x8a53` fifo x208; `0x8a53->0x4099` ctrl x206; `0x8a53->0x47b1` fifo x60; `0x4099->0x8a53` ctrl x38 |
| `0x8a54` | CDB byte 11 or reused controller/status byte | `0x8a54->0x4099` ctrl x206; `0x8a54->0x40b7` ctrl x99; `0x47b1->0x8a54` fifo x87; `0x8a54->0x47b1` fifo x60; `0x4099->0x8a54` ctrl x38 |

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
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | xrl_a_imm | jz | 832 | `+0x8700`, `+0x9600`, `+0x9780`, `+0x9c40`, `+0x8780`, `+0x87c0`, `+0x8740`, `+0x9c80` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | mov_r7_xrl_imm | jz | 624 | `+0x61c0`, `+0x9600`, `+0x9bc0`, `+0x6180`, `+0x6140`, `+0x6100`, `+0x9b00` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x03` | cjne_a_imm | cjne | 416 | `+0x8700`, `+0x9f00`, `+0x8780`, `+0x87c0`, `+0x9f80`, `+0x8740`, `+0x9f40`, `+0x9fc0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | cjne_a_imm | cjne | 416 | `+0x6b00`, `+0x9900`, `+0x6b80`, `+0x6bc0`, `+0x99c0`, `+0x9940`, `+0x6b40` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/00-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x03` | xrl_a_imm | jz | 208 | `+0x63c0`, `+0x6380` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xe3` | mov_r7_xrl_imm | jz | 208 | `+0x9740`, `+0x97c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xe7` | cjne_a_imm | cjne | 208 | `+0x9740`, `+0x97c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x2a` | cjne_a_imm | cjne | 164 | `+0x7e40`, `+0x7ec0`, `+0x7e80` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x55` | cjne_a_imm | cjne | 161 | `+0x7f40`, `+0x7f80`, `+0x7fc0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x2a` | xrl_a_imm | jz | 144 | `+0x6240`, `+0x6280`, `+0x62c0` | `normal-work-window-stimuli-full-20260501/01-test-unit-ready`, `normal-work-window-stimuli-full-20260501/02-request-sense` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xb4` | cjne_a_imm | cjne | 129 | `+0x9e80`, `+0x9e40` | `normal-work-window-stimuli-focused-20260501/00-cycle00-inquiry-extrainq`, `normal-work-window-stimuli-expanded-20260501/12-mode-sense10-capabilities` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x1b` | xrl_a_imm | jnz | 106 | `+0x8b40`, `+0x8b00`, `+0x8bc0`, `+0x8b80` | `normal-work-window-stimuli-full-20260501/01-test-unit-ready`, `normal-work-window-stimuli-full-20260501/02-request-sense` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xe6` | mov_r7_cjne_imm | cjne | 94 | `+0x8800` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa3` | cjne_a_imm | cjne | 83 | `+0x9180`, `+0x9100` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa4` | cjne_a_imm | cjne | 83 | `+0x9180`, `+0x9100` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x13` | cjne_a_imm | cjne | 58 | `+0x9e00`, `+0x9e80`, `+0x9e40` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x6b` | cjne_a_imm | cjne | 12 | `+0x9ec0` | `normal-work-window-stimuli-focused-20260501/01-cycle00-mode-sense10-all`, `normal-work-window-stimuli-focused-20260501/02-cycle00-get-configuration-current` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x78` | cjne_a_imm | cjne | 4 | `+0x9e00`, `+0x9e40` | `normal-work-window-stimuli-full-20260501/00-baseline-no-stimulus`, `normal-work-window-stimuli-full-20260501/01-test-unit-ready` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa1` | cjne_a_imm | cjne | 2 | `+0x9ec0` | `normal-work-window-stimuli-focused-20260501/05-cycle01-inquiry-extrainq`, `normal-work-window-stimuli-focused-20260501/30-cycle06-inquiry-extrainq` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xcf` | cjne_a_imm | cjne | 2 | `+0x9e00` | `normal-work-window-stimuli-full-20260501/03-inquiry-standard-96`, `normal-work-window-stimuli-full-20260501/04-inquiry-extrainq` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x7c` | cjne_a_imm | cjne | 1 | `+0x9ec0` | `normal-work-window-stimuli-focused-20260501/15-cycle03-inquiry-extrainq` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x01` | cjne_a_imm | cjne | 208 | `+0x6740`, `+0x67c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` | xrl_a_imm | jnz | 208 | `+0x6540`, `+0x6580` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x0e` | cjne_a_imm | cjne | 94 | `+0x8800` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x02` | xrl_a_imm | jz | 51 | `+0x7e00`, `+0x7e40`, `+0x7e80` | `normal-work-window-stimuli-full-20260501/06-get-configuration-current`, `normal-work-window-stimuli-full-20260501/07-get-configuration-all` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` | mov_r7_xrl_imm | jz | 208 | `+0x7240`, `+0x7200` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x22` | cjne_a_imm | cjne | 94 | `+0x8800` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x01` | mov_r7_xrl_imm | jz | 29 | `+0x9540`, `+0x9580`, `+0x9500`, `+0x95c0` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/07-capture-only` |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0x01` | cjne_a_imm | cjne | 208 | `+0x8d40`, `+0x8d00` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0xf0` | cjne_a_imm | cjne | 202 | `+0x6700` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0xfe` | cjne_a_imm | cjne | 4 | `+0x7180`, `+0x7140` | `normal-work-window-stimuli-focused-20260501/03-cycle00-get-configuration-all`, `normal-work-window-stimuli-focused-20260501/27-cycle05-get-configuration-current` |
| `0x8a53` | CDB byte 10 or reused controller/status byte | `0x01` | cjne_a_imm | cjne | 194 | `+0x9040`, `+0x9080` | `normal-work-window-capture-only-20260501/00-capture-only`, `normal-work-window-capture-only-20260501/01-capture-only` |
