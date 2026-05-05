# Normal Runtime Packet Shadow Analysis

This report scans complete normal-runtime work-window captures for target
XDATA references and short MOVX idioms. Unlike the overlay atlas, it scans
across `0x40` chunk boundaries, so packet-copy sequences split between
tiles are still detected.

## Summary

- captures: 4
- target DPTR observations: 933
- unique target chunks: 118
- direct MOVX copy edges: 27
- write idioms touching target addresses: 47
- compare idioms touching target addresses: 16
- FIFO bursts from `0x47b1`: 2
- controller command/FIFO sequence classes: 2

## Target DPTR References

| addr | observations | chunks | sample slots |
|---:|---:|---:|---|
| `0x8a23` | 127 | 33 | `+0x6140`, `+0x6180`, `+0x6300`, `+0x6340`, `+0x6fc0`, `+0x7100`, `+0x7140`, `+0x7300` |
| `0x8a49` | 104 | 26 | `+0x6140`, `+0x61c0`, `+0x6240`, `+0x6300`, `+0x64c0`, `+0x6b00`, `+0x6b40`, `+0x6bc0` |
| `0x4000` | 66 | 13 | `+0x6ac0`, `+0x7140`, `+0x7240`, `+0x8780`, `+0x9180`, `+0x92c0`, `+0x9340`, `+0xd7c0` |
| `0x47b1` | 66 | 14 | `+0x62c0`, `+0x63c0`, `+0x6400`, `+0x6580`, `+0x6780`, `+0x7140`, `+0x7240`, `+0x7380` |
| `0x8adf` | 48 | 12 | `+0x7200`, `+0x7f80`, `+0x8040`, `+0x8200`, `+0x8d40`, `+0x9340`, `+0x9400`, `+0x94c0` |
| `0x8a51` | 34 | 10 | `+0x6f80`, `+0x7140`, `+0x7800`, `+0x81c0`, `+0x8280`, `+0x8640`, `+0x86c0`, `+0x8d00` |
| `0x8a53` | 33 | 8 | `+0x72c0`, `+0x7700`, `+0x8580`, `+0x8f40`, `+0x91c0`, `+0x9500`, `+0x9b80` |
| `0x8a4c` | 32 | 6 | `+0x6800`, `+0x6c40`, `+0x70c0`, `+0x7180`, `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x4098` | 30 | 6 | `+0x6ac0`, `+0x7140`, `+0x7240`, `+0x8780`, `+0x9180`, `+0xdc00` |
| `0x4867` | 27 | 8 | `+0x6700`, `+0x6e00`, `+0x6fc0`, `+0x7000`, `+0x73c0`, `+0x8400`, `+0x85c0`, `+0xa640` |
| `0x8a50` | 26 | 7 | `+0x6780`, `+0x6b00`, `+0x6b40`, `+0x6bc0`, `+0x6f80`, `+0x7180`, `+0x9500`, `+0x9c40` |
| `0x486a` | 24 | 8 | `+0x6700`, `+0x6e00`, `+0x6fc0`, `+0x7000`, `+0x73c0`, `+0x83c0`, `+0x89c0`, `+0x9180` |
| `0x8a4b` | 24 | 6 | `+0x6800`, `+0x72c0`, `+0x7d00`, `+0x9480`, `+0x9a40`, `+0x9a80`, `+0x9ac0`, `+0x9c40` |
| `0x8a4d` | 23 | 9 | `+0x62c0`, `+0x63c0`, `+0x6c40`, `+0x7180`, `+0x8b40`, `+0x9500`, `+0x9a40`, `+0x9a80` |
| `0x8a4e` | 20 | 4 | `+0x6c40`, `+0x7180`, `+0x7c40`, `+0x9500` |
| `0x4863` | 18 | 6 | `+0x7b40`, `+0x83c0`, `+0x8400`, `+0x84c0`, `+0x85c0`, `+0x88c0` |
| `0x8a4a` | 17 | 5 | `+0x64c0`, `+0x6540`, `+0x6780`, `+0x9480`, `+0x9c00` |
| `0x4011` | 16 | 2 | `+0x70c0`, `+0x7180` |
| `0x4861` | 16 | 5 | `+0x7b40`, `+0x83c0`, `+0x8400`, `+0x85c0`, `+0x9180` |
| `0x4862` | 16 | 6 | `+0x62c0`, `+0x7b40`, `+0x83c0`, `+0x8440`, `+0x85c0`, `+0x89c0` |
| `0x8a4f` | 16 | 3 | `+0x6f80`, `+0x9500`, `+0x9a40`, `+0x9a80`, `+0x9ac0` |
| `0x4864` | 13 | 4 | `+0x83c0`, `+0x8440`, `+0x89c0`, `+0x9680` |
| `0x4095` | 12 | 3 | `+0xdbc0`, `+0xdc00`, `+0xdc40` |
| `0x4096` | 12 | 3 | `+0xdbc0`, `+0xdc00`, `+0xdc40` |
| `0x4097` | 12 | 2 | `+0xdc00`, `+0xdc40` |
| `0x8a5b` | 12 | 2 | `+0xdc00`, `+0xdc40` |
| `0x4091` | 9 | 3 | `+0x7140`, `+0x8780`, `+0xe5c0` |
| `0x4012` | 8 | 2 | `+0x70c0`, `+0x7180` |
| `0x409a` | 8 | 2 | `+0xe600`, `+0xe640` |
| `0x409c` | 8 | 2 | `+0xe600`, `+0xe640` |
| `0x8a52` | 8 | 2 | `+0x6f80`, `+0x9500` |
| `0x8a5c` | 8 | 1 | `+0xdc00` |
| `0x8ade` | 8 | 2 | `+0xdbc0`, `+0xdc40` |
| `0x8aeb` | 8 | 2 | `+0xdc00`, `+0xdc40` |
| `0x8aec` | 8 | 2 | `+0xdc00`, `+0xdc40` |
| `0x89a5` | 5 | 2 | `+0x7140`, `+0xdc00` |
| `0x4013` | 4 | 1 | `+0x7180` |
| `0x8a54` | 4 | 1 | `+0x9600` |
| `0x4860` | 2 | 1 | `+0x73c0` |
| `0x4093` | 1 | 1 | `+0x7140` |

## MOVX Copy Edges

| src | dst | kind | count | sample offsets |
|---:|---:|---|---:|---|
| `0x4095` | `0x8ade` | direct | 4 | `+0xdbc0` |
| `0x4096` | `0x8aec` | direct | 4 | `+0xdbc0` |
| `0x4097` | `0x8aeb` | direct | 4 | `+0xdc00` |
| `0x47b1` | `0x8a4a` | direct | 4 | `+0x9480` |
| `0x47b1` | `0x8a4b` | direct | 4 | `+0x9480` |
| `0x47b1` | `0x8a4d` | direct | 4 | `+0x9500` |
| `0x47b1` | `0x8a4e` | direct | 4 | `+0x9500` |
| `0x47b1` | `0x8a4f` | direct | 4 | `+0x9500` |
| `0x47b1` | `0x8a50` | direct | 4 | `+0x9500` |
| `0x47b1` | `0x8a51` | direct | 4 | `+0x9500` |
| `0x47b1` | `0x8a52` | direct | 4 | `+0x9500` |
| `0x47b1` | `0x8a53` | direct | 4 | `+0x9500` |
| `0x85fe` | `0x4011` | direct | 4 | `+0x70c0` |
| `0x85ff` | `0x4012` | direct | 4 | `+0x70c0` |
| `0x89a5` | `0x4095` | direct | 4 | `+0xdc00` |
| `0x8a4c` | `0x4011` | direct | 4 | `+0x7180` |
| `0x8a4d` | `0x4012` | direct | 4 | `+0x7180` |
| `0x8a4e` | `0x4013` | direct | 4 | `+0x7180` |
| `0x8a5b` | `0x4096` | direct | 4 | `+0xdc00` |
| `0x8a5c` | `0x4097` | direct | 4 | `+0xdc00` |
| `0x8ade` | `0x4095` | direct | 4 | `+0xdc40` |
| `0x8aeb` | `0x4097` | direct | 4 | `+0xdc40` |
| `0x8aec` | `0x4096` | direct | 4 | `+0xdc40` |
| `0x4863` | `0x8630` | direct | 3 | `+0x84c0` |
| `0x8630` | `0x4863` | direct | 3 | `+0x88c0` |
| `0x89a5` | `0x4091` | direct | 1 | `+0x7140` |
| `0x8ae4` | `0x47b1` | direct | 1 | `+0x6400` |

## FIFO Bursts From 0x47b1

| dst range | bytes | observations | sample |
|---|---:|---:|---|
| `0x8a4a..0x8a4b` | 2 | 4 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` `+0x94af` |
| `0x8a4d..0x8a53` | 7 | 4 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` `+0x9507` |

## Packet Shadow To Controller Edges

| src | dst | kind | count | sample offsets |
|---:|---:|---|---:|---|
| `0x4095` | `0x8ade` | direct | 4 | `+0xdbc0` |
| `0x4096` | `0x8aec` | direct | 4 | `+0xdbc0` |
| `0x4097` | `0x8aeb` | direct | 4 | `+0xdc00` |
| `0x85fe` | `0x4011` | direct | 4 | `+0x70c0` |
| `0x85ff` | `0x4012` | direct | 4 | `+0x70c0` |
| `0x89a5` | `0x4095` | direct | 4 | `+0xdc00` |
| `0x8a4c` | `0x4011` | direct | 4 | `+0x7180` |
| `0x8a4d` | `0x4012` | direct | 4 | `+0x7180` |
| `0x8a4e` | `0x4013` | direct | 4 | `+0x7180` |
| `0x8a5b` | `0x4096` | direct | 4 | `+0xdc00` |
| `0x8a5c` | `0x4097` | direct | 4 | `+0xdc00` |
| `0x8ade` | `0x4095` | direct | 4 | `+0xdc40` |
| `0x8aeb` | `0x4097` | direct | 4 | `+0xdc40` |
| `0x8aec` | `0x4096` | direct | 4 | `+0xdc40` |
| `0x89a5` | `0x4091` | direct | 1 | `+0x7140` |

## Controller Command/FIFO Sequences

These are heuristic linear-DPTR decodes of short local idioms. They catch
stream writes through `INC DPTR` and repeated writes to a command register
that the direct copy scan cannot name by destination address.

| sequence | observations | sample | local MOVX stream |
|---|---:|---|---|
| controller FIFO writer: setup 4095..4097 then data to 4098 | 8 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` `+0xdc2f` | `read 0x8a5d`; `read 0x8a5e`; `write 0x8a5e`; `read 0x8a5d`; `write 0x8a5d`; `read 0x4095`; `0x8ade<=xdata_0x4095`; `read 0x4096`; `0x8aec<=xdata_0x4096`; `read 0x4097`; `0x8aeb<=xdata_0x4097`; `read 0x4000` |
| restore mirrored controller setup: 8ade/8aec/8aeb -> 4095..4097 | 8 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` `+0xdc7f` | `read 0x8a5b`; `0x4096<=xdata_0x8a5b`; `read 0x8a5c`; `0x4097<=xdata_0x8a5c`; `write 0x4098`; `read 0x4000`; `write 0x4098`; `read 0x8a5c`; `write 0x8a5b`; `write 0x8a5c`; `read 0x4000`; `read 0x8ade` |

## Target Writes

| addr | kind | value | count | sample offsets |
|---:|---|---:|---:|---|
| `0x8a23` | or_mask | `0x02` | 22 | `+0x7140`, `+0x7800`, `+0x81c0`, `+0x8280`, `+0x8600`, `+0x86c0`, `+0x8d00`, `+0x9c00` |
| `0x8a23` | or_mask | `0x40` | 16 | `+0x7f80`, `+0x9280`, `+0xdac0`, `+0xee80` |
| `0x8a23` | or_mask | `0x10` | 12 | `+0x7e80`, `+0x8600`, `+0x8640`, `+0x9400`, `+0x94c0` |
| `0x4011` | write_imm | `0x0e` | 8 | `+0x70c0`, `+0x7180` |
| `0x409a` | write_zero | `0x00` | 8 | `+0xe600`, `+0xe640` |
| `0x8a23` | and_mask | `0xef` | 8 | `+0xeec0`, `+0xef00` |
| `0x4862` | and_mask | `0x3f` | 5 | `+0x83c0`, `+0x89c0` |
| `0x486a` | and_mask | `0xdf` | 5 | `+0x83c0`, `+0x89c0` |
| `0x47b1` | write_zero | `0x00` | 4 | `+0x6580`, `+0x8e00` |
| `0x4861` | or_mask | `0x08` | 4 | `+0x8400` |
| `0x4861` | or_mask | `0x40` | 4 | `+0x8400` |
| `0x4861` | write_imm | `0x40` | 4 | `+0x7b40` |
| `0x4862` | write_imm | `0x73` | 4 | `+0x7b40` |
| `0x4863` | or_mask | `0x1d` | 4 | `+0x8400` |
| `0x4863` | write_imm | `0x1d` | 4 | `+0x7b40` |
| `0x4864` | and_mask | `0xfd` | 4 | `+0x8440` |
| `0x4864` | or_mask | `0x04` | 4 | `+0x89c0` |
| `0x4864` | write_zero | `0x00` | 4 | `+0x9680` |
| `0x4867` | and_mask | `0xeb` | 4 | `+0x6700` |
| `0x4867` | and_mask | `0xfd` | 4 | `+0x8400` |
| `0x4867` | or_mask | `0x08` | 4 | `+0x6e00` |
| `0x4867` | or_mask | `0x10` | 4 | `+0x6e00` |
| `0x486a` | and_mask | `0xfa` | 4 | `+0x6700` |
| `0x486a` | or_mask | `0x05` | 4 | `+0x6e00` |
| `0x8a52` | and_mask | `0xfe` | 4 | `+0x6f80` |
| `0x8a23` | and_mask | `0xbf` | 3 | `+0x8d40` |
| `0x8a23` | and_mask | `0xf7` | 3 | `+0x8940` |
| `0x4860` | write_zero | `0x00` | 2 | `+0x73c0` |
| `0x4861` | write_zero | `0x00` | 2 | `+0x9180` |
| `0x4862` | and_mask | `0xfb` | 2 | `+0x62c0` |
| `0x4867` | or_mask | `0x14` | 2 | `+0x6fc0` |
| `0x4867` | write_imm | `0x61` | 2 | `+0x73c0` |
| `0x486a` | or_mask | `0x2c` | 2 | `+0x6fc0` |
| `0x486a` | write_zero | `0x00` | 2 | `+0x73c0` |
| `0x8adf` | and_mask | `0xf0` | 2 | `+0x9340` |
| `0x47b1` | write_imm | `0x02` | 1 | `+0x6580` |
| `0x47b1` | write_imm | `0x03` | 1 | `+0x62c0` |
| `0x47b1` | write_imm | `0x04` | 1 | `+0x63c0` |
| `0x47b1` | write_imm | `0x06` | 1 | `+0x6580` |
| `0x4861` | and_mask | `0x7f` | 1 | `+0x83c0` |
| `0x4861` | and_mask | `0xf7` | 1 | `+0x85c0` |
| `0x4863` | and_mask | `0xfd` | 1 | `+0x83c0` |
| `0x4864` | and_mask | `0xfb` | 1 | `+0x83c0` |
| `0x4867` | and_mask | `0xe3` | 1 | `+0x7000` |
| `0x4867` | and_mask | `0xf7` | 1 | `+0x7000` |
| `0x4867` | or_mask | `0x02` | 1 | `+0x85c0` |
| `0x486a` | and_mask | `0xf2` | 1 | `+0x7000` |

## Target Compares

| addr | kind | value | branch | count | sample offsets |
|---:|---|---:|---|---:|---|
| `0x8a49` | mov_r7_xrl_imm | `0x28` | jz | 16 | `+0x6140`, `+0x61c0`, `+0x7680`, `+0x9600`, `+0x9b80` |
| `0x8a49` | xrl_a_imm | `0x28` | jz | 15 | `+0x8740`, `+0x87c0`, `+0x9600`, `+0x9780`, `+0x9c40` |
| `0x8a49` | cjne_a_imm | `0x03` | cjne | 8 | `+0x8740`, `+0x87c0`, `+0x9f00`, `+0x9fc0` |
| `0x8a49` | cjne_a_imm | `0x28` | cjne | 8 | `+0x6b00`, `+0x6b40`, `+0x6bc0`, `+0x9980` |
| `0x8a49` | xrl_a_imm | `0x03` | jz | 4 | `+0x6300` |
| `0x8a4a` | cjne_a_imm | `0x01` | cjne | 4 | `+0x6780` |
| `0x8a4a` | xrl_a_imm | `0x06` | jnz | 4 | `+0x6540` |
| `0x8a4b` | mov_r7_xrl_imm | `0xe2` | jz | 4 | `+0x72c0` |
| `0x8a4c` | mov_r7_xrl_imm | `0x01` | jz | 4 | `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x8a49` | cjne_a_imm | `0xa3` | cjne | 3 | `+0x91c0` |
| `0x8a49` | cjne_a_imm | `0xa4` | cjne | 3 | `+0x91c0` |
| `0x8a49` | cjne_a_imm | `0x1b` | cjne | 2 | `+0x9ec0` |
| `0x8a49` | xrl_a_imm | `0x1b` | jnz | 1 | `+0x8b40` |
| `0x8a49` | xrl_a_imm | `0x2a` | jz | 1 | `+0x6240` |
| `0x8a49` | cjne_a_imm | `0xa1` | cjne | 1 | `+0x9ec0` |
| `0x8a49` | cjne_a_imm | `0xe0` | cjne | 1 | `+0x9ec0` |

## High-Value Snippets

| label | capture | offset | bytes |
|---|---|---:|---|
| copy 0x85fe->0x4011 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x70da` | `8a4ce0c3940e4008904011740ef080089085fee0904011f09085ffe0904012f0908600802e90fd123d89908988e0ffa3e0fd123d897f0012050d908988eef0a3` |
| copy 0x85ff->0x4012 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x70e2` | `904011740ef080089085fee0904011f09085ffe0904012f0908600802e90fd123d89908988e0ffa3e0fd123d897f0012050d908988eef0a3eff0908a3ae0547f` |
| copy 0x8a4c->0x4011 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x718a` | `8a4ce0c3940e4008904011740ef08008908a4ce0904011f0908a4de0904012f0908a4ee0904013f0908a50e0ffa3e078a9cff608eff6e04401f0905997e04450` |
| copy 0x8a4d->0x4012 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x7192` | `904011740ef08008908a4ce0904011f0908a4de0904012f0908a4ee0904013f0908a50e0ffa3e078a9cff608eff6e04401f0905997e04450f022ee70089055cd` |
| copy 0x8a4e->0x4013 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x719a` | `908a4ce0904011f0908a4de0904012f0908a4ee0904013f0908a50e0ffa3e078a9cff608eff6e04401f0905997e04450f022ee70089055cde054e7f022eeb401` |
| copy 0x47b1->0x8a4a | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x949f` | `e04480f0229047b0e4f0a3e0908a49f09047b1e0908a4af09047b1e0908a4bf090249089ece004f0e0c3940a401d908a23e04410f0c2789088f1e054fbf09089` |
| copy 0x47b1->0x8a4b | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x94a7` | `e4f0a3e0908a49f09047b1e0908a4af09047b1e0908a4bf090249089ece004f0e0c3940a401d908a23e04410f0c2789088f1e054fbf09089247401f08005e490` |
| copy 0x47b1->0x8a4d | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x94f7` | `940240031202bb908a47b1e0908a4cf09047b1e0908a4df09047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f0` |
| copy 0x47b1->0x8a4e | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x94ff` | `8a47b1e0908a4cf09047b1e0908a4df09047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f0` |
| copy 0x47b1->0x8a4f | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9507` | `9047b1e0908a4df09047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f0907ff9123d89e4fd` |
| copy 0x47b1->0x8a50 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x950f` | `9047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f0907ff9123d89e4fd7f40123d89e4908a` |
| copy 0x47b1->0x8a51 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9517` | `9047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f0907ff9123d89e4fd7f40123d89e4908a33f0d0d092af2290` |
| copy 0x47b1->0x8a52 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x951f` | `9047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f0907ff9123d89e4fd7f40123d89e4908a33f0d0d092af22908a4ce0ff6401601c` |
| copy 0x47b1->0x8a53 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9527` | `9047b1e0908a51f09047b1e0908a52f09047b1e0908a53f0907ff9123d89e4fd7f40123d89e4908a33f0d0d092af22908a4ce0ff6401601cef64026017ef6404` |
| copy 0x4095->0x8ade | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdbe6` | `600e908a5ee024fff0908a5de034fff0904095e0908adef0904096e0908aecf0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f090` |
| copy 0x4096->0x8aec | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdbee` | `f0908a5de034fff0904095e0908adef0904096e0908aecf0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3` |
| copy 0x4097->0x8aeb | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdbf6` | `904095e0908adef0904096e0908aecf0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7` |
| copy 0x89a5->0x4095 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdc05` | `f0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7f9904098edf0908a5ce02402f0908a` |
| copy 0x8a5b->0x4096 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdc0d` | `f0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7f9904098edf0908a5ce02402f0908a5be03400f0e0b440` |
| copy 0x8a5c->0x4097 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdc15` | `9089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7f9904098edf0908a5ce02402f0908a5be03400f0e0b44013a3e0b4000e908a` |
| copy 0x8ade->0x4095 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdc58` | `02f0e4908a5bf0a3f0904000e020e7f9908adee0904095f0908aece0904096f0908aebe0904097f0d0d092af22c0e0c0f0c083c082c0d075d0187b437d587f45` |
| copy 0x8aec->0x4096 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdc60` | `f0904000e020e7f9908adee0904095f0908aece0904096f0908aebe0904097f0d0d092af22c0e0c0f0c083c082c0d075d0187b437d587f45123e1ae4ff120279` |
| copy 0x8aeb->0x4097 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0xdc68` | `908adee0904095f0908aece0904096f0908aebe0904097f0d0d092af22c0e0c0f0c083c082c0d075d0187b437d587f45123e1ae4ff120279908565eff0603ba3` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x61bf` | `2347c5e09089c8f09047c4e09089c9f0908a49e0ff64286013ef64be600eef64a86009ef64d56004efb4b9099047c5e4f09047c4f09047d2e054fef0904014e4` |
| compare 0x8a49 with 0x03 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x631a` | `908920e06404604720470578b5e66008908a49e064036037908a23e0ff1313543f30e008908afea3e02400ffec3efe90881ce02ff090881be03ef090881be0f9` |
| compare 0x8a4a with 0x06 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x6551` | `e00d129865bf01077db17ffb123d8922908a4ae06406705ea3e064677058a3e064787052a3e06489704ca3e0649a7059547006e0543ff08004e044c0f07f1112` |
| compare 0x8a4a with 0x01 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x6777` | `70479088cee0fba3e0e09047b102a4be908a4ae0b40120a3e0ff6401601cef64026017ef64e26012ef64f0600def64f26008ef64f1600302a36b908a50e0fea3` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x6b5f` | `6007d2497f00020513e478a6f612b092908a49e0b42839908a50e07004a3e06401900001122fb7904835f0ef4440904834f0904e02e04408f0d2a9057c057cd0` |
| compare 0x8a4b with 0xe2 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x72b0` | `054000886b379979558d2c4000c14800908a4be0ff64e26004efb4f116908a53e0fea3e0ffc378aa96ee18965005eef608eff678aae630e00606e61870010690` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x7691` | `0720e00302b839c27790809ee04408f0908a49e0ff64286019ef64a86014ef64be600fef64d5600aef64b96005ef6459c07404f09059617408f09059227403f0` |
| compare 0x8a49 with 0x03 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x8740` | `02063302063978a976eb08761402711d908a49e0b4030302a4c2e478b5f678abf678b0f6908a44e0601a908a49e064286012e0644a600de0600ae064466005e4` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x875a` | `e478b5f678abf678b0f6908a44e0601a908a49e064286012e0644a600de0600ae064466005e4e0904091f0a3e55ef0a3e55ff0904000e020e7f9904098e09040` |
| compare 0x8a4c with 0x01 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9546` | `fd7f40123d89e4908a33f0d0d092af22908a4ce0ff6401601cef64026017ef64046012ef6405600d78b5760578ab7624e478b0f6227f0112bb183ae0c4131354` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x95f7` | `908042e0fe1313540147b1e0908a54f0908a49e0ff64286009ef64a86004efb4be07908243e04480f0908a49e064286003029e319089f7e0ffd39402507cef14` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9610` | `ef64a86004efb4be07908243e04480f0908a49e064286003029e319089f7e0ffd39402507cef14602a14602724027060e04402f09058007405f0905950e4f0e0` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x997b` | `807d017e009dffee9c908988f0a3eff0908a49e0b42829c3908989e09464908988e09400401ae47f01fefdfc78a21233b2c31233117009908a38e04401f08007` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9ba2` | `123d897f0012050d908988eef0a3eff0908a49e0ff64286004efb4a80f9030e6617f5f1208d990855ceff0908355e0feefd39e400890855ce0908355f090849b` |
| compare 0x8a49 with 0x28 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9c3e` | `0af08946e0ffa3e090892dcff0a3eff0908a49e06428600302a016908a69e0fca3e0fda3e0fea3e0ff908a4be0f8a3e0f9a3e0faa3e0fbc31233116077908a50` |
| compare 0x8a49 with 0xa1 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9eeb` | `1f20e04c908a37e04408f09047cbe4f0908a49e0b4a10d9047ca7450f09047d0e4f0801fc23f9047c97450f0908a49e0b4030a9047cf7401f0a3f080069047d0` |
| compare 0x8a49 with 0x03 | `normal-mailbox-dvd-auth-20260505T040403172305Z/02-after-report-key-css-agid` | `+0x9f07` | `f09047d0e4f0801fc23f9047c97450f0908a49e0b4030a9047cf7401f0a3f080069047d07401f0908a38e054eff09040187403f0d0d092af221b089089f6e064` |

## Interpretation

- The FIFO intake is visible in two pieces: a prefix sequence clears
  `0x47b0` and reads `0x47b1` into `0x8a49..0x8a4b`, then later bursts
  fill the rest of the shadow through `0x8a54`. Because this public
  window is paged/rotating, individual captures expose slightly different
  slices of that burst.
- `xdata[0x8a49]` is compared against command-like values including
  `0x28`, `0xa8`, and `0xbe` immediately after the FIFO burst. This
  makes it the likely opcode/selector byte for the normal packet shadow.
- The strongest packet-to-controller bridge edges are now explicit:
  shadow bytes feed `0x4011..0x4013`, `0x4091`, `0x4095`, `0x4099`,
  and `0x40b7`, while controller setup bytes are mirrored back into
  `0x8ade/0x8aeb/0x8aec`. That is the next static path to reverse.
- The command/FIFO sequences sharpen that bridge: `0x4091..0x4093`
  feed read-side commands kicked by `0x409c=0x40/0x24`; `0x4095..0x4097`
  feed write-side/FIFO commands; and the GET CONFIG-tagged path writes
  packet-shadow bytes through `0x4099`, then streams command bytes into
  `0x409a..0x409c` before polling `0x409c`.
