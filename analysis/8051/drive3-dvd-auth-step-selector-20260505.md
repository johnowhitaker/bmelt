# Normal Packet Selector Map

This report condenses the normal-runtime packet-shadow evidence into a
selector/field map. It is based on public `READ BUFFER id=01` work-window
captures, so capture labels show when a code/table chunk was visible, not
a proof that the named command executed that exact branch.

## Summary

- captures scanned: 7
- packet-shadow compare idioms: 14
- packet-shadow/controller edge rows: 12
- `0x8a49` remains the best opcode/selector byte.
- `GET CONFIGURATION` (`0x46`) tags the controller bridge dynamically,
  but a plain `0x8a49 == 0x46` compare has not appeared in the public
  work-window corpus. That means its route may be table-driven, handled
  through an unharvested slice, or dispatched before this compare cluster.

## 0x8a49 Opcode-Like Compares

| value | likely meaning | class | compare forms | count | sample slots |
|---:|---|---|---|---:|---|
| `0x03` | REQUEST SENSE | read/status | `cjne_a_imm->cjne`, `xrl_a_imm->jz` | 21 | `+0x63c0`, `+0x8780`, `+0x9f40` |
| `0x1b` | START STOP UNIT | mechanical | `cjne_a_imm->cjne`, `xrl_a_imm->jnz` | 11 | `+0x8bc0`, `+0x9ec0` |
| `0x28` | READ(10) | read/data | `mov_r7_xrl_imm->jz`, `xrl_a_imm->jz`, `cjne_a_imm->cjne` | 70 | `+0x6100`, `+0x6140`, `+0x6180`, `+0x61c0`, `+0x6b00`, `+0x6b40`, `+0x6b80`, `+0x6bc0` |
| `0x2a` | WRITE(10) | write/data | `xrl_a_imm->jz` | 4 | `+0x6240` |
| `0xa3` | SEND KEY / MMC security | write/control | `cjne_a_imm->cjne` | 6 | `+0x91c0` |
| `0xa4` | REPORT KEY / MMC security | read/control | `cjne_a_imm->cjne` | 6 | `+0x91c0` |

## Adjacent Shadow Field Compares

| addr | role sketch | values seen | total compares |
|---:|---|---|---:|
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` x7, `0x01` x7 | 14 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` x7 | 7 |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x01` x7 | 7 |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | - | 0 |
| `0x8a4e` | CDB byte 5 or reused controller/status byte | - | 0 |
| `0x8a4f` | CDB byte 6 / payload field | - | 0 |
| `0x8a50` | CDB byte 7 / payload field | - | 0 |
| `0x8a51` | CDB byte 8 / payload field | - | 0 |
| `0x8a52` | CDB byte 9 / payload field | - | 0 |
| `0x8a53` | CDB byte 10 or reused controller/status byte | - | 0 |
| `0x8a54` | CDB byte 11 or reused controller/status byte | - | 0 |

## Shadow Byte Edge Sketch

| addr | role sketch | strongest observed edges |
|---:|---|---|
| `0x8a49` | CDB byte 0 / opcode selector | - |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x47b1->0x8a4a` fifo x7 |
| `0x8a4b` | CDB byte 2 / op-specific field | `0x47b1->0x8a4b` fifo x7 |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x8a4c->0x4011` ctrl x7 |
| `0x8a4d` | CDB byte 4 or reused controller/status byte | `0x47b1->0x8a4d` fifo x7; `0x8a4d->0x4012` ctrl x7 |
| `0x8a4e` | CDB byte 5 or reused controller/status byte | `0x47b1->0x8a4e` fifo x7; `0x8a4e->0x4013` ctrl x7 |
| `0x8a4f` | CDB byte 6 / payload field | `0x47b1->0x8a4f` fifo x7 |
| `0x8a50` | CDB byte 7 / payload field | `0x47b1->0x8a50` fifo x7 |
| `0x8a51` | CDB byte 8 / payload field | `0x47b1->0x8a51` fifo x7 |
| `0x8a52` | CDB byte 9 / payload field | `0x47b1->0x8a52` fifo x7 |
| `0x8a53` | CDB byte 10 or reused controller/status byte | `0x47b1->0x8a53` fifo x7 |
| `0x8a54` | CDB byte 11 or reused controller/status byte | - |

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
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | mov_r7_xrl_imm | jz | 28 | `+0x6100`, `+0x7640`, `+0x96c0`, `+0x9bc0`, `+0x61c0`, `+0x6140`, `+0x6180` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | xrl_a_imm | jz | 28 | `+0x8780`, `+0x96c0`, `+0x9740`, `+0x9c00` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x03` | cjne_a_imm | cjne | 14 | `+0x8780`, `+0x9f40` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x28` | cjne_a_imm | cjne | 14 | `+0x6b80`, `+0x9980`, `+0x6bc0`, `+0x6b00`, `+0x6b40` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x03` | xrl_a_imm | jz | 7 | `+0x63c0` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x1b` | cjne_a_imm | cjne | 7 | `+0x9ec0` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa3` | cjne_a_imm | cjne | 6 | `+0x91c0` | `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf`, `normal-mailbox-dvd-auth-20260505T034456990715Z/06-after-report-key-css-rpc-state` |
| `0x8a49` | CDB byte 0 / opcode selector | `0xa4` | cjne_a_imm | cjne | 6 | `+0x91c0` | `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf`, `normal-mailbox-dvd-auth-20260505T034456990715Z/06-after-report-key-css-rpc-state` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x1b` | xrl_a_imm | jnz | 4 | `+0x8bc0` | `normal-mailbox-dvd-auth-20260505T034456990715Z/08-after-send-key-css-host-challenge`, `normal-mailbox-dvd-auth-20260505T034456990715Z/10-after-report-key-css-key1` |
| `0x8a49` | CDB byte 0 / opcode selector | `0x2a` | xrl_a_imm | jz | 4 | `+0x6240` | `normal-mailbox-dvd-auth-20260505T034456990715Z/08-after-send-key-css-host-challenge`, `normal-mailbox-dvd-auth-20260505T034456990715Z/10-after-report-key-css-key1` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x01` | cjne_a_imm | cjne | 7 | `+0x6700` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf` |
| `0x8a4a` | CDB byte 1 / op-specific field | `0x06` | xrl_a_imm | jnz | 7 | `+0x6540` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf` |
| `0x8a4b` | CDB byte 2 / op-specific field | `0xe2` | mov_r7_xrl_imm | jz | 7 | `+0x7280` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf` |
| `0x8a4c` | CDB byte 3 / controller setup byte | `0x01` | mov_r7_xrl_imm | jz | 7 | `+0x95c0`, `+0x9540`, `+0x9580` | `normal-mailbox-dvd-auth-20260505T034456990715Z/02-after-report-key-css-agid`, `normal-mailbox-dvd-auth-20260505T034456990715Z/04-after-report-key-css-asf` |
