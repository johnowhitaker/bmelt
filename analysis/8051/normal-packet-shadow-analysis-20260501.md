# Normal Runtime Packet Shadow Analysis

This report scans complete normal-runtime work-window captures for target
XDATA references and short MOVX idioms. Unlike the overlay atlas, it scans
across `0x40` chunk boundaries, so packet-copy sequences split between
tiles are still detected.

## Summary

- captures: 94
- target DPTR observations: 34186
- unique target chunks: 181
- direct MOVX copy edges: 57
- write idioms touching target addresses: 46
- compare idioms touching target addresses: 32
- FIFO bursts from `0x47b1`: 6
- controller command/FIFO sequence classes: 6

## Target DPTR References

| addr | observations | chunks | sample slots |
|---:|---:|---:|---|
| `0x47b1` | 3278 | 24 | `+0x6240`, `+0x6280`, `+0x6300`, `+0x6380`, `+0x6440`, `+0x6480`, `+0x64c0`, `+0x6500` |
| `0x4000` | 2993 | 31 | `+0x67c0`, `+0x6a00`, `+0x6a40`, `+0x6a80`, `+0x6ac0`, `+0x6c40`, `+0x6c80`, `+0x6ec0` |
| `0x8a49` | 2876 | 28 | `+0x6100`, `+0x6140`, `+0x6180`, `+0x61c0`, `+0x6240`, `+0x6280`, `+0x63c0`, `+0x6400` |
| `0x8a23` | 2704 | 29 | `+0x6100`, `+0x6140`, `+0x6180`, `+0x6300`, `+0x6380`, `+0x63c0`, `+0x6440`, `+0x6480` |
| `0x8a4d` | 2152 | 27 | `+0x6240`, `+0x6280`, `+0x6300`, `+0x6380`, `+0x6440`, `+0x6480`, `+0x6500`, `+0x6640` |
| `0x8adf` | 1222 | 13 | `+0x7300`, `+0x7680`, `+0x7b80`, `+0x7f40`, `+0x7f80`, `+0x7fc0`, `+0x8000`, `+0x8280` |
| `0x8a4e` | 1202 | 18 | `+0x6ac0`, `+0x6c40`, `+0x6c80`, `+0x7140`, `+0x7180`, `+0x7480`, `+0x74c0`, `+0x7580` |
| `0x4098` | 1100 | 10 | `+0x6a00`, `+0x6a40`, `+0x6a80`, `+0x6ac0`, `+0x7180`, `+0x7280`, `+0x72c0`, `+0x7640` |
| `0x8a4c` | 1050 | 10 | `+0x6840`, `+0x6c40`, `+0x6c80`, `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7140`, `+0x7180` |
| `0x8a50` | 1031 | 14 | `+0x6300`, `+0x6380`, `+0x6500`, `+0x65c0`, `+0x6700`, `+0x6740`, `+0x6900`, `+0x69c0` |
| `0x8a53` | 1000 | 15 | `+0x6440`, `+0x6480`, `+0x6c40`, `+0x7140`, `+0x7180`, `+0x7240`, `+0x7280`, `+0x7480` |
| `0x8a54` | 991 | 11 | `+0x6280`, `+0x6780`, `+0x6900`, `+0x69c0`, `+0x7140`, `+0x7180`, `+0x7280`, `+0x7480` |
| `0x8a4b` | 967 | 15 | `+0x6300`, `+0x6380`, `+0x6640`, `+0x6680`, `+0x66c0`, `+0x6840`, `+0x7140`, `+0x7180` |
| `0x8a4f` | 902 | 11 | `+0x6440`, `+0x6480`, `+0x7580`, `+0x75c0`, `+0x7900`, `+0x7980`, `+0x7a00`, `+0x7a80` |
| `0x4099` | 828 | 6 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7140`, `+0x7180`, `+0x7480`, `+0x74c0`, `+0x7800` |
| `0x409c` | 826 | 9 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7380`, `+0x7480`, `+0x74c0`, `+0x7600`, `+0x7800` |
| `0x8a4a` | 790 | 11 | `+0x6400`, `+0x6440`, `+0x6480`, `+0x6500`, `+0x6540`, `+0x65c0`, `+0x6740`, `+0x7280` |
| `0x8a51` | 755 | 12 | `+0x6300`, `+0x6380`, `+0x6700`, `+0x6ec0`, `+0x7f40`, `+0x7f80`, `+0x7fc0`, `+0x8300` |
| `0x4091` | 646 | 10 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7180`, `+0x7600`, `+0x7640`, `+0x7b00`, `+0x7e00` |
| `0x4097` | 572 | 6 | `+0x6ec0`, `+0x7380`, `+0x7800`, `+0x7dc0`, `+0xdc00`, `+0xdc40` |
| `0x4095` | 564 | 6 | `+0x7380`, `+0x7780`, `+0x7c40`, `+0xdbc0`, `+0xdc00`, `+0xdc40` |
| `0x4093` | 440 | 9 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7180`, `+0x7580`, `+0x75c0`, `+0x7600`, `+0x7640` |
| `0x4011` | 380 | 3 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7140`, `+0x7180`, `+0x99c0` |
| `0x4860` | 376 | 4 | `+0x7500`, `+0x8b80`, `+0x8bc0`, `+0x8c40`, `+0x9200`, `+0x9240`, `+0x9280`, `+0x92c0` |
| `0x4864` | 376 | 4 | `+0x7500`, `+0x7740`, `+0x8c40`, `+0x9200`, `+0x9240`, `+0x9280`, `+0x92c0` |
| `0x4867` | 376 | 3 | `+0x68c0`, `+0x9400`, `+0x9440`, `+0x9480`, `+0x94c0`, `+0xa640` |
| `0x4863` | 352 | 4 | `+0x7500`, `+0x8480`, `+0x8580`, `+0x85c0`, `+0x8880` |
| `0x8a52` | 331 | 6 | `+0x6440`, `+0x6480`, `+0x6500`, `+0x6640`, `+0x6680`, `+0x66c0`, `+0x8300`, `+0x8cc0` |
| `0x4096` | 291 | 4 | `+0x6ec0`, `+0xdbc0`, `+0xdc00`, `+0xdc40` |
| `0x8a5b` | 282 | 2 | `+0xdc00`, `+0xdc40` |
| `0x4012` | 228 | 3 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7140`, `+0x7180`, `+0x9a00`, `+0x9a40`, `+0x9a80` |
| `0x4092` | 213 | 4 | `+0x7580`, `+0x75c0`, `+0x7640`, `+0x8080`, `+0x85c0` |
| `0x409a` | 188 | 2 | `+0xe600`, `+0xe640` |
| `0x8a5c` | 188 | 1 | `+0xdc00` |
| `0x8ade` | 188 | 2 | `+0xdbc0`, `+0xdc40` |
| `0x8aeb` | 188 | 2 | `+0xdc00`, `+0xdc40` |
| `0x8aec` | 188 | 2 | `+0xdc00`, `+0xdc40` |
| `0x40b5` | 186 | 1 | `+0x7dc0` |
| `0x891b` | 172 | 2 | `+0x7640`, `+0x9900`, `+0x9940`, `+0x99c0` |
| `0x4862` | 159 | 2 | `+0x6240`, `+0x6280`, `+0x7500` |
| `0x4013` | 134 | 2 | `+0x7140`, `+0x7180`, `+0x9a00`, `+0x9a40`, `+0x9a80`, `+0x9ac0` |
| `0x89a5` | 95 | 2 | `+0x7180`, `+0xdc00` |
| `0x486a` | 94 | 1 | `+0x7500` |
| `0x40b6` | 93 | 1 | `+0x7dc0` |
| `0x40b7` | 93 | 1 | `+0x7dc0` |
| `0x8960` | 63 | 3 | `+0x6ec0`, `+0x7580`, `+0x75c0`, `+0x8080` |
| `0x8961` | 63 | 3 | `+0x6ec0`, `+0x7580`, `+0x75c0`, `+0x8080` |

## MOVX Copy Edges

| src | dst | kind | count | sample offsets |
|---:|---:|---|---:|---|
| `0x8ac6` | `0x4095` | direct | 282 | `+0x7380`, `+0x7780`, `+0x7c40` |
| `0x8ac6` | `0x4091` | direct | 212 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x75c0`, `+0x7b00`, `+0x7e00`, `+0x7e40` |
| `0x4095` | `0x8ade` | direct | 94 | `+0xdbc0` |
| `0x4096` | `0x8aec` | direct | 94 | `+0xdbc0` |
| `0x4097` | `0x8aeb` | direct | 94 | `+0xdc00` |
| `0x47b1` | `0x8a4a` | direct | 94 | `+0x9400`, `+0x9480`, `+0x94c0` |
| `0x47b1` | `0x8a4b` | direct | 94 | `+0x9400`, `+0x9480`, `+0x94c0` |
| `0x47b1` | `0x8a4d` | direct | 94 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x47b1` | `0x8a4e` | direct | 94 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x47b1` | `0x8a4f` | direct | 94 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x47b1` | `0x8a50` | direct | 94 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x47b1` | `0x8a51` | direct | 94 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x47b1` | `0x8a52` | direct | 94 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x47b1` | `0x8a53` | direct | 94 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x4863` | `0x8630` | direct | 94 | `+0x8480` |
| `0x85fe` | `0x4011` | direct | 94 | `+0x7000`, `+0x7080`, `+0x70c0` |
| `0x85ff` | `0x4012` | direct | 94 | `+0x7000`, `+0x7080`, `+0x70c0` |
| `0x8630` | `0x4863` | direct | 94 | `+0x8880` |
| `0x891b` | `0x4091` | direct | 94 | `+0x7640` |
| `0x89a5` | `0x4095` | direct | 94 | `+0xdc00` |
| `0x8a4c` | `0x4011` | direct | 94 | `+0x7140`, `+0x7180` |
| `0x8a4d` | `0x4012` | direct | 94 | `+0x7140`, `+0x7180` |
| `0x8a4e` | `0x4013` | direct | 94 | `+0x7140`, `+0x7180` |
| `0x8a50` | `0x85f4` | direct | 94 | `+0x6700` |
| `0x8a51` | `0x85f5` | direct | 94 | `+0x6700` |
| `0x8a5b` | `0x4096` | direct | 94 | `+0xdc00` |
| `0x8a5c` | `0x4097` | direct | 94 | `+0xdc00` |
| `0x8ade` | `0x4095` | direct | 94 | `+0xdc40` |
| `0x8aeb` | `0x4097` | direct | 94 | `+0xdc40` |
| `0x8aec` | `0x4096` | direct | 94 | `+0xdc40` |
| `0x8e2d` | `0x47b1` | direct | 94 | `+0x78c0` |
| `0x8e2f` | `0x47b1` | direct | 94 | `+0x7940` |
| `0x8e30` | `0x47b1` | direct | 94 | `+0x7940` |
| `0x8a54` | `0x40b7` | direct | 93 | `+0x7dc0` |
| `0x8a4e` | `0x4099` | direct | 92 | `+0x7480`, `+0x74c0` |
| `0x8a53` | `0x4099` | direct | 92 | `+0x7480`, `+0x74c0` |
| `0x8a54` | `0x4099` | direct | 92 | `+0x7480`, `+0x74c0` |
| `0x8ae4` | `0x47b1` | direct | 70 | `+0x6440`, `+0x6480`, `+0x64c0` |
| `0x8960` | `0x4092` | direct | 54 | `+0x7580`, `+0x75c0`, `+0x8080` |
| `0x8961` | `0x4093` | direct | 54 | `+0x7580`, `+0x75c0`, `+0x8080` |
| `0x8a4f` | `0x47d6` | direct | 54 | `+0x8240` |
| `0x8a53` | `0x47b1` | direct | 54 | `+0x8240` |
| `0x8a54` | `0x47b1` | direct | 54 | `+0x8240` |
| `0x8a4d` | `0x47d6` | direct | 53 | `+0x7580`, `+0x75c0` |
| `0x4099` | `0x8a53` | direct | 38 | `+0x7140`, `+0x7180`, `+0x7f40`, `+0x7f80` |
| `0x4099` | `0x8a54` | direct | 38 | `+0x7140`, `+0x7180`, `+0x7f40`, `+0x7f80` |
| `0x47b1` | `0x8a54` | direct | 33 | `+0x95c0` |
| `0x47b1` | `0x8a4c` | direct | 30 | `+0x94c0`, `+0x9500`, `+0x9540`, `+0x9580` |
| `0x8960` | `0x4096` | direct | 9 | `+0x6ec0` |
| `0x8961` | `0x4097` | direct | 9 | `+0x6ec0` |
| `0x891b` | `0x40fe` | direct | 5 | `+0x99c0` |
| `0x4099` | `0x8a4e` | direct | 4 | `+0x7140`, `+0x7180` |
| `0x891b` | `0x4011` | direct | 4 | `+0x99c0` |
| `0x8a4e` | `0x47b1` | direct | 2 | `+0x8580` |
| `0x8a4f` | `0x47b1` | direct | 2 | `+0x8580` |
| `0x8a50` | `0x47b1` | direct | 2 | `+0x8580` |
| `0x89a5` | `0x4091` | direct | 1 | `+0x7180` |

## FIFO Bursts From 0x47b1

| dst range | bytes | observations | sample |
|---|---:|---:|---|
| `0x8a4a..0x8a4b` | 2 | 84 | `normal-work-window-capture-only-20260501/00-capture-only` `+0x94ef` |
| `0x8a4d..0x8a53` | 7 | 53 | `normal-work-window-capture-only-20260501/04-capture-only` `+0x9587` |
| `0x8a4c..0x8a53` | 8 | 18 | `normal-work-window-capture-only-20260501/01-capture-only` `+0x953f` |
| `0x8a4d..0x8a54` | 8 | 11 | `normal-work-window-capture-only-20260501/00-capture-only` `+0x95c7` |
| `0x8a4a..0x8a53` | 10 | 10 | `normal-work-window-stimuli-full-20260501/06-get-configuration-current` `+0x94ef` |
| `0x8a4c..0x8a54` | 9 | 2 | `normal-work-window-capture-only-20260501/13-capture-only` `+0x95bf` |

## Packet Shadow To Controller Edges

| src | dst | kind | count | sample offsets |
|---:|---:|---|---:|---|
| `0x8ac6` | `0x4095` | direct | 282 | `+0x7380`, `+0x7780`, `+0x7c40` |
| `0x8ac6` | `0x4091` | direct | 212 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x75c0`, `+0x7b00`, `+0x7e00`, `+0x7e40` |
| `0x4095` | `0x8ade` | direct | 94 | `+0xdbc0` |
| `0x4096` | `0x8aec` | direct | 94 | `+0xdbc0` |
| `0x4097` | `0x8aeb` | direct | 94 | `+0xdc00` |
| `0x85fe` | `0x4011` | direct | 94 | `+0x7000`, `+0x7080`, `+0x70c0` |
| `0x85ff` | `0x4012` | direct | 94 | `+0x7000`, `+0x7080`, `+0x70c0` |
| `0x891b` | `0x4091` | direct | 94 | `+0x7640` |
| `0x89a5` | `0x4095` | direct | 94 | `+0xdc00` |
| `0x8a4c` | `0x4011` | direct | 94 | `+0x7140`, `+0x7180` |
| `0x8a4d` | `0x4012` | direct | 94 | `+0x7140`, `+0x7180` |
| `0x8a4e` | `0x4013` | direct | 94 | `+0x7140`, `+0x7180` |
| `0x8a5b` | `0x4096` | direct | 94 | `+0xdc00` |
| `0x8a5c` | `0x4097` | direct | 94 | `+0xdc00` |
| `0x8ade` | `0x4095` | direct | 94 | `+0xdc40` |
| `0x8aeb` | `0x4097` | direct | 94 | `+0xdc40` |
| `0x8aec` | `0x4096` | direct | 94 | `+0xdc40` |
| `0x8a54` | `0x40b7` | direct | 93 | `+0x7dc0` |
| `0x8a4e` | `0x4099` | direct | 92 | `+0x7480`, `+0x74c0` |
| `0x8a53` | `0x4099` | direct | 92 | `+0x7480`, `+0x74c0` |
| `0x8a54` | `0x4099` | direct | 92 | `+0x7480`, `+0x74c0` |
| `0x8960` | `0x4092` | direct | 54 | `+0x7580`, `+0x75c0`, `+0x8080` |
| `0x8961` | `0x4093` | direct | 54 | `+0x7580`, `+0x75c0`, `+0x8080` |
| `0x4099` | `0x8a53` | direct | 38 | `+0x7140`, `+0x7180`, `+0x7f40`, `+0x7f80` |
| `0x4099` | `0x8a54` | direct | 38 | `+0x7140`, `+0x7180`, `+0x7f40`, `+0x7f80` |
| `0x8960` | `0x4096` | direct | 9 | `+0x6ec0` |
| `0x8961` | `0x4097` | direct | 9 | `+0x6ec0` |
| `0x4099` | `0x8a4e` | direct | 4 | `+0x7140`, `+0x7180` |
| `0x891b` | `0x4011` | direct | 4 | `+0x99c0` |
| `0x89a5` | `0x4091` | direct | 1 | `+0x7180` |

## Controller Command/FIFO Sequences

These are heuristic linear-DPTR decodes of short local idioms. They catch
stream writes through `INC DPTR` and repeated writes to a command register
that the direct copy scan cannot name by destination address.

| sequence | observations | sample | local MOVX stream |
|---|---:|---|---|
| controller FIFO writer: setup 4095..4097 then data to 4098 | 188 | `normal-work-window-capture-only-20260501/00-capture-only` `+0xdc2f` | `read 0x8a5d`; `read 0x8a5e`; `write 0x8a5e`; `read 0x8a5d`; `write 0x8a5d`; `read 0x4095`; `0x8ade<=xdata_0x4095`; `read 0x4096`; `0x8aec<=xdata_0x4096`; `read 0x4097`; `0x8aeb<=xdata_0x4097`; `read 0x4000` |
| restore mirrored controller setup: 8ade/8aec/8aeb -> 4095..4097 | 188 | `normal-work-window-capture-only-20260501/00-capture-only` `+0xdc7f` | `read 0x8a5b`; `0x4096<=xdata_0x8a5b`; `read 0x8a5c`; `0x4097<=xdata_0x8a5c`; `write 0x4098`; `read 0x4000`; `write 0x4098`; `read 0x8a5c`; `write 0x8a5b`; `write 0x8a5c`; `read 0x4000`; `read 0x8ade` |
| packet-shadow command: 4099 burst, 409a=0, 409b=1, 409c=0x14 | 186 | `normal-work-window-capture-only-20260501/00-capture-only` `+0x74e8` | `write 0x4099`; `read 0x8a4e`; `0x4099<=xdata_0x8a4e`; `read 0x8a53`; `0x4099<=xdata_0x8a53`; `read 0x8a54`; `0x4099<=xdata_0x8a54`; `0x409a=0x00`; `0x409b=0x01`; `0x409c=0x14`; `read 0x409c`; `read 0x8a4d` |
| read-side setup: 4091..4093 then 409c=0x40 | 98 | `normal-work-window-capture-only-20260501/00-capture-only` `+0x7625` | `read 0x8a4d`; `read 0x8a4d`; `read 0x8a4d`; `read 0x8a4d`; `0x4091<=xdata_0x898a`; `write 0x4092`; `write 0x4093`; `0x409c=0x40`; `0x409c=0x20`; `read 0x409c`; `read 0x8a4e` |
| write-side setup: 4095..4097 then 409c=0x40 | 94 | `normal-work-window-capture-only-20260501/00-capture-only` `+0x73be` | `read 0x4000`; `read 0x8ac6`; `0x4095<=xdata_0x8ac6`; `write 0x4096`; `write 0x4097`; `0x409c=0x40` |
| read-side kick: 409c=0x40 then 0x24 | 4 | `normal-work-window-stimuli-focused-20260501/03-cycle00-get-configuration-all` `+0x70f3` | `read 0x4000`; `read 0x8ac6`; `0x4091<=xdata_0x8ac6`; `write 0x4092`; `write 0x4093`; `0x409c=0x40`; `0x409c=0x24`; `read 0x409c`; `read 0x4099` |

## Target Writes

| addr | kind | value | count | sample offsets |
|---:|---|---:|---:|---|
| `0x8a23` | or_mask | `0x02` | 405 | `+0x6500`, `+0x65c0`, `+0x6780`, `+0x7840`, `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0` |
| `0x409c` | write_imm | `0x40` | 320 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7380`, `+0x7600`, `+0x7800`, `+0x7f40`, `+0x7f80` |
| `0x8a23` | or_mask | `0x40` | 282 | `+0x7f40`, `+0x7f80`, `+0x7fc0`, `+0xdac0`, `+0xee80` |
| `0x47b1` | write_zero | `0x00` | 272 | `+0x6500`, `+0x65c0`, `+0x7700`, `+0x7940`, `+0x8580` |
| `0x8a23` | and_mask | `0xf7` | 226 | `+0x6440`, `+0x6480`, `+0x8900`, `+0x8a40` |
| `0x4011` | write_imm | `0x0e` | 188 | `+0x7000`, `+0x7080`, `+0x70c0`, `+0x7140`, `+0x7180` |
| `0x409a` | write_zero | `0x00` | 188 | `+0xe600`, `+0xe640` |
| `0x8a23` | and_mask | `0xef` | 188 | `+0xeec0`, `+0xef00` |
| `0x8a23` | or_mask | `0x10` | 187 | `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`, `+0x9400`, `+0x9440`, `+0x9480`, `+0x94c0` |
| `0x4000` | or_mask | `0xf0` | 94 | `+0x7640` |
| `0x47b1` | write_imm | `0x0a` | 94 | `+0x7940` |
| `0x47b1` | write_imm | `0x70` | 94 | `+0x7700` |
| `0x47b1` | write_imm | `0xf1` | 94 | `+0x7700` |
| `0x4860` | and_mask | `0xfb` | 94 | `+0x8c40` |
| `0x4860` | or_mask | `0x04` | 94 | `+0x9200`, `+0x9240`, `+0x9280`, `+0x92c0` |
| `0x4860` | write_zero | `0x00` | 94 | `+0x7500` |
| `0x4862` | write_imm | `0xff` | 94 | `+0x7500` |
| `0x4863` | write_imm | `0x2f` | 94 | `+0x7500` |
| `0x4864` | and_mask | `0xfe` | 94 | `+0x8c40` |
| `0x4864` | or_mask | `0x01` | 94 | `+0x9200`, `+0x9240`, `+0x9280`, `+0x92c0` |
| `0x4867` | and_mask | `0x7f` | 94 | `+0x9400`, `+0x9440`, `+0x9480`, `+0x94c0` |
| `0x4867` | or_mask | `0x80` | 94 | `+0x9400`, `+0x9440`, `+0x9480`, `+0x94c0` |
| `0x486a` | or_mask | `0xf0` | 94 | `+0x7500` |
| `0x8a54` | write_imm | `0x41` | 94 | `+0x6780` |
| `0x8a54` | write_imm | `0x70` | 94 | `+0x6780` |
| `0x8a54` | write_imm | `0x71` | 94 | `+0x6780` |
| `0x40b5` | write_imm | `0x10` | 93 | `+0x7dc0` |
| `0x40b5` | write_imm | `0x14` | 93 | `+0x7dc0` |
| `0x40b6` | write_zero | `0x00` | 93 | `+0x7dc0` |
| `0x47b1` | write_imm | `0x04` | 90 | `+0x6300`, `+0x6380` |
| `0x47b1` | write_imm | `0x03` | 89 | `+0x6240`, `+0x6280` |
| `0x47b1` | write_imm | `0x02` | 82 | `+0x6500`, `+0x65c0` |
| `0x47b1` | write_imm | `0x06` | 82 | `+0x6500`, `+0x65c0` |
| `0x8a4d` | write_zero | `0x00` | 75 | `+0x6440`, `+0x6480`, `+0x6500`, `+0x6640`, `+0x6680`, `+0x66c0` |
| `0x8a52` | write_imm | `0x02` | 74 | `+0x6440`, `+0x6480`, `+0x6640`, `+0x6680`, `+0x66c0` |
| `0x4862` | and_mask | `0xfb` | 65 | `+0x6240`, `+0x6280` |
| `0x8a52` | write_imm | `0x03` | 64 | `+0x6500`, `+0x6640`, `+0x6680`, `+0x66c0` |
| `0x4091` | write_imm | `0x08` | 60 | `+0x9b00`, `+0x9b40` |
| `0x47b1` | write_imm | `0x71` | 53 | `+0x7580`, `+0x75c0` |
| `0x47b1` | write_imm | `0x80` | 51 | `+0x7e00`, `+0x7ec0` |
| `0x4093` | or_mask | `0x08` | 25 | `+0x85c0` |
| `0x4098` | write_zero | `0x00` | 16 | `+0x9c00`, `+0x9cc0` |
| `0x47b1` | write_imm | `0x01` | 9 | `+0x9f80` |
| `0x8a23` | or_mask | `0x01` | 5 | `+0x93c0` |
| `0x47b1` | write_imm | `0x10` | 2 | `+0x8580` |
| `0x8a4f` | or_mask | `0x01` | 2 | `+0x6440`, `+0x6480` |

## Target Compares

| addr | kind | value | branch | count | sample offsets |
|---:|---|---:|---|---:|---|
| `0x8a49` | xrl_a_imm | `0x28` | jz | 376 | `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`, `+0x9600`, `+0x9780`, `+0x9c40` |
| `0x8a49` | mov_r7_xrl_imm | `0x28` | jz | 282 | `+0x6100`, `+0x6140`, `+0x6180`, `+0x61c0`, `+0x9600`, `+0x9bc0` |
| `0x8a49` | cjne_a_imm | `0x03` | cjne | 188 | `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`, `+0x9f00`, `+0x9f40`, `+0x9f80`, `+0x9fc0` |
| `0x8a49` | cjne_a_imm | `0x28` | cjne | 188 | `+0x6b00`, `+0x6b40`, `+0x6b80`, `+0x6bc0`, `+0x9900`, `+0x9940`, `+0x99c0` |
| `0x8a49` | xrl_a_imm | `0x03` | jz | 94 | `+0x63c0` |
| `0x8a49` | mov_r7_xrl_imm | `0xe3` | jz | 94 | `+0x9740` |
| `0x8a49` | mov_r7_cjne_imm | `0xe6` | cjne | 94 | `+0x8800` |
| `0x8a49` | cjne_a_imm | `0xe7` | cjne | 94 | `+0x9740` |
| `0x8a4a` | cjne_a_imm | `0x01` | cjne | 94 | `+0x6740` |
| `0x8a4a` | xrl_a_imm | `0x06` | jnz | 94 | `+0x6540` |
| `0x8a4a` | cjne_a_imm | `0x0e` | cjne | 94 | `+0x8800` |
| `0x8a4b` | cjne_a_imm | `0x22` | cjne | 94 | `+0x8800` |
| `0x8a4b` | mov_r7_xrl_imm | `0xe2` | jz | 94 | `+0x7240` |
| `0x8a4d` | cjne_a_imm | `0x01` | cjne | 94 | `+0x8d40` |
| `0x8a4d` | cjne_a_imm | `0xf0` | cjne | 94 | `+0x6700` |
| `0x8a53` | cjne_a_imm | `0x01` | cjne | 82 | `+0x9040` |
| `0x8a49` | cjne_a_imm | `0x13` | cjne | 58 | `+0x9e00`, `+0x9e40`, `+0x9e80` |
| `0x8a49` | cjne_a_imm | `0x2a` | cjne | 51 | `+0x7e40`, `+0x7ec0` |
| `0x8a49` | cjne_a_imm | `0x55` | cjne | 49 | `+0x7f40`, `+0x7f80`, `+0x7fc0` |
| `0x8a49` | cjne_a_imm | `0xa3` | cjne | 46 | `+0x9180` |
| `0x8a49` | cjne_a_imm | `0xa4` | cjne | 46 | `+0x9180` |
| `0x8a4a` | xrl_a_imm | `0x02` | jz | 46 | `+0x7e00`, `+0x7e40` |
| `0x8a49` | xrl_a_imm | `0x2a` | jz | 34 | `+0x6240`, `+0x6280` |
| `0x8a49` | xrl_a_imm | `0x1b` | jnz | 18 | `+0x8b00`, `+0x8b40`, `+0x8b80`, `+0x8bc0` |
| `0x8a49` | cjne_a_imm | `0xb4` | cjne | 15 | `+0x9e80` |
| `0x8a4c` | mov_r7_xrl_imm | `0x01` | jz | 15 | `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0` |
| `0x8a49` | cjne_a_imm | `0x6b` | cjne | 12 | `+0x9ec0` |
| `0x8a49` | cjne_a_imm | `0x78` | cjne | 4 | `+0x9e00`, `+0x9e40` |
| `0x8a4d` | cjne_a_imm | `0xfe` | cjne | 4 | `+0x7140`, `+0x7180` |
| `0x8a49` | cjne_a_imm | `0xa1` | cjne | 2 | `+0x9ec0` |
| `0x8a49` | cjne_a_imm | `0xcf` | cjne | 2 | `+0x9e00` |
| `0x8a49` | cjne_a_imm | `0x7c` | cjne | 1 | `+0x9ec0` |

## High-Value Snippets

| label | capture | offset | bytes |
|---|---|---:|---|
| copy 0x85fe->0x4011 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x709a` | `8a4ce0c3940e4008904011740ef080089085fee0904011f09085ffe0904012f0908600802e90cbefcbd0e0ffd0e0fed0e0fdd0e0fcc3ef9bffee9afeed99fdec` |
| copy 0x85ff->0x4012 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x70a2` | `904011740ef080089085fee0904011f09085ffe0904012f0908600802e90cbefcbd0e0ffd0e0fed0e0fdd0e0fcc3ef9bffee9afeed99fdec98fc9090d8123430` |
| copy 0x8a4c->0x4011 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x718a` | `8a4ce0c3940e4008904011740ef08008908a4ce0904011f0908a4de0904012f0908a4ee0904013f0908a50e0ffa3e078a9cff608eff6f608760112efb6057c05` |
| copy 0x8a4d->0x4012 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x7192` | `904011740ef08008908a4ce0904011f0908a4de0904012f0908a4ee0904013f0908a50e0ffa3e078a9cff608eff6f608760112efb6057c057c22908857e09088` |
| copy 0x8a4e->0x4013 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x719a` | `908a4ce0904011f0908a4de0904012f0908a4ee0904013f0908a50e0ffa3e078a9cff608eff6f608760112efb6057c057c22908857e090885df0908858e09088` |
| copy 0x8ac6->0x4095 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x7388` | `36a87c0808f608eff6904000e020e7f9908ac6e0904095f0a87c0808e6a3f07b00a97c09097a00900001122fb7904097f090409c7440f090512278b5e6600302` |
| copy 0x8a4e->0x4099 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x74b7` | `fb7a80f9f8d31232fb8a4de0904099f0908a4ee0904099f0908a53e0904099f0908a54e0904099f0a3e4f0a304f0a37414f090409ce020e4f978aa740426f618` |
| copy 0x8a53->0x4099 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x74bf` | `fb8a4de0904099f0908a4ee0904099f0908a53e0904099f0908a54e0904099f0a3e4f0a304f0a37414f090409ce020e4f978aa740426f618e436f6908a4de070` |
| copy 0x8a54->0x4099 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x74c7` | `908a4ee0904099f0908a53e0904099f0908a54e0904099f0a3e4f0a304f0a37414f090409ce020e4f978aa740426f618e436f6908a4de070027cf0904864e030` |
| copy 0x891b->0x4091 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x765e` | `122fb7904093f0a87c0808e6904092f090891be0904091f0904098e0a87cf6904000e044f0f0c2af204f0e203f0b203e087f0312ec6212e806d2af02b6f3908a` |
| copy 0x8ac6->0x4095 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x779c` | `36a87c0808f608eff6904000e020e7f9908ac6e0904095f0a87c0808e6a3f07b00a97c09e020e7f9904098e0a87cf6904000e020e7f9904098e07b00a97c7a00` |
| copy 0x8ac6->0x4091 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x7b0e` | `3ea87c0808f608eff6904000e020e7f9908ac6e0904091f0a87c0808e6a3f07b00a97c09097a00900001122fb7904093f0901234247e027fc01203dbd3908a4d` |
| copy 0x8ac6->0x4095 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x7c54` | `ef78aa26ffee1836a87c0808f608eff6908ac6e0904095f0a87c0808e6a3f07b00a97c09097a00900001122f02120885ef54ef4410fd7f0212088b7e017fcf12` |
| copy 0x8a54->0x40b7 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x7dc1` | `904097f0904000e020e7f99040b6e4f0908a54e09040b7f09040b57414f0904000e020e7f99040b57410f0908a54e0ff7e0078aa26f618ee36f6a87c08ef2612` |
| copy 0x47b1->0x8a4a | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x94df` | `e04480f0229047b0e4f0a3e0908a49f09047b1e0908a4af09047b1e0908a4bf090e0908c87f07f0412014a7df17faf123d897d037f76123d8990825be0fd7f20` |
| copy 0x47b1->0x8a4b | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x94e7` | `e4f0a3e0908a49f09047b1e0908a4af09047b1e0908a4bf090e0908c87f07f0412014a7df17faf123d897d037f76123d8990825be0fd7f20123d89908490e0ff` |
| copy 0x47b1->0x8a4d | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95b7` | `a3eff030482b90892d47b1e0908a4cf09047b1e0908a4df09047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f0` |
| copy 0x47b1->0x8a4e | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95bf` | `2d47b1e0908a4cf09047b1e0908a4df09047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f0` |
| copy 0x47b1->0x8a4f | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95c7` | `9047b1e0908a4df09047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f09047b1e0908a54f0` |
| copy 0x47b1->0x8a50 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95cf` | `9047b1e0908a4ef09047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f09047b1e0908a54f0908a49e0ff642860` |
| copy 0x47b1->0x8a51 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95d7` | `9047b1e0908a4ff09047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f09047b1e0908a54f0908a49e0ff64286009ef64a86004efb4` |
| copy 0x47b1->0x8a52 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95df` | `9047b1e0908a50f09047b1e0908a51f09047b1e0908a52f09047b1e0908a53f09047b1e0908a54f0908a49e0ff64286009ef64a86004efb4be07908243e04480` |
| copy 0x47b1->0x8a53 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95e7` | `9047b1e0908a51f09047b1e0908a52f09047b1e0908a53f09047b1e0908a54f0908a49e0ff64286009ef64a86004efb4be07908243e04480f0908a49e0642860` |
| copy 0x47b1->0x8a54 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x95ef` | `9047b1e0908a52f09047b1e0908a53f09047b1e0908a54f0908a49e0ff64286009ef64a86004efb4be07908243e04480f0908a49e064286003029e319089f7e0` |
| copy 0x4095->0x8ade | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdbe6` | `600e908a5ee024fff0908a5de034fff0904095e0908adef0904096e0908aecf0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f090` |
| copy 0x4096->0x8aec | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdbee` | `f0908a5de034fff0904095e0908adef0904096e0908aecf0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3` |
| copy 0x4097->0x8aeb | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdbf6` | `904095e0908adef0904096e0908aecf0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7` |
| copy 0x89a5->0x4095 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdc05` | `f0904097e0908aebf0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7f9904098edf0908a5ce02402f0908a` |
| copy 0x8a5b->0x4096 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdc0d` | `f0904000e020e7f99089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7f9904098edf0908a5ce02402f0908a5be03400f0e0b440` |
| copy 0x8a5c->0x4097 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdc15` | `9089a5e0904095f0908a5be0904096f0908a5ce0904097f0a3eff0904000e020e7f9904098edf0908a5ce02402f0908a5be03400f0e0b44013a3e0b4000e908a` |
| copy 0x8ade->0x4095 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdc58` | `02f0e4908a5bf0a3f0904000e020e7f9908adee0904095f0908aece0904096f0908aebe0904097f0d0d092af22c0e0c0f0c083c082c0d075d0187b437d587f45` |
| copy 0x8aec->0x4096 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdc60` | `f0904000e020e7f9908adee0904095f0908aece0904096f0908aebe0904097f0d0d092af22c0e0c0f0c083c082c0d075d0187b437d587f45123e1ae4ff120279` |
| copy 0x8aeb->0x4097 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0xdc68` | `908adee0904095f0908aece0904096f0908aebe0904097f0d0d092af22c0e0c0f0c083c082c0d075d0187b437d587f45123e1ae4ff120279908565eff0603ba3` |
| compare 0x8a49 with 0x28 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x61bf` | `2347c5e09089c8f09047c4e09089c9f0908a49e0ff64286013ef64be600eef64a86009ef64d56004efb4b9099047c5e4f09047c4f09047d2e054fef0904014e4` |
| compare 0x8a49 with 0x03 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x63da` | `908920e06404604720470578b5e66008908a49e064036037908a23e0ff1313543f30e008908a49e07002802390892ce0ffc413540720e01aefc41313540330e0` |
| compare 0x8a4a with 0x06 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x6551` | `e00d129865bf01077db17ffb123d8922908a4ae06406705ea3e064677058a3e064787052a3e06489704ca3e0649a700214f090851fe004f0908523e004f09085` |
| compare 0x8a4d with 0xf0 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x670f` | `ffec35f0cf2401cf3400fed0d092af22908a4de0b4f0089085f47401f08070908a50e09085f4f0908a51e09085f5f09085e09047b102a4be908a4ae0b40120a3` |
| compare 0x8a4a with 0x01 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x6737` | `8a51e09085f5f09085e09047b102a4be908a4ae0b40120a3e0ff6401601cef64026017ef64e26012ef64f0600def64f26008ef64f1600302a36b908a50e0fea3` |
| compare 0x8a49 with 0x28 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x6b1f` | `6007d2497f00020513e478a6f612b092908a49e0b42839908a50e07004a3e06401b1e04402f022908db1e04404f022908db1e04408f022908db1e04410f022d3` |
| compare 0x8a4b with 0xe2 | `normal-work-window-capture-only-20260501/00-capture-only` | `+0x7230` | `7f007e04120a6b2290898ee04401f090908a4be0ff64e26004efb4f116908a53e0fea3e0ffc378aa96ee18965005eef608eff678aae630e00606e61870010690` |

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
