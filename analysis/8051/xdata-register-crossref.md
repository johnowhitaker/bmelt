# LiteOn 8051 XDATA Register Cross-Reference

Generated from the Ghidra C export. This is a heuristic map for triage,
not a complete proof of register semantics.

- source: `analysis/8051/ldm58051_c.c`
- currentboot values: `references/evidence/live/linux-drive1-currentboot-xdata-0000-ffff-bulk-v2.bin`

## High-Value Addresses

| address | summary | likely role | notable refs |
|---|---|---|---|
| `0x4023` | 4 refs; write, read; 3 funcs; cur=0x00; consts=0x00 | mixed/unknown | FUN_CODE_268a:3114 read; FUN_CODE_268a:3115 write; FUN_CODE_40b2:4693 write; FUN_CODE_50ca:5557 write |
| `0x4700` | 10 refs; read-modify-write, test, wait/test; 6 funcs; cur=0x0b; masks=&1,|2 | controller-path/status candidate | FUN_CODE_268a:3125 test; FUN_CODE_268a:3151 test; FUN_CODE_465e:4951 wait/test; FUN_CODE_50ca:5558 test; +6 more |
| `0x4703` | 1 refs; read-modify-write; 1 funcs; cur=0xd0; masks=&0xcf,|0x10 | mostly-written config/state | FUN_CODE_4a1b:5180 read-modify-write |
| `0x4704` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xf7 | controller-path/status candidate | FUN_CODE_4230:4722 read-modify-write |
| `0x4748` | 8 refs; write, read-modify-write, read; 4 funcs; cur=0x98; consts=0x88,0x98; masks=&0x7f,|0x80 | controller-path/status candidate | FUN_CODE_47b0:5071 read-modify-write; FUN_CODE_47b0:5074 read-modify-write; FUN_CODE_47b0:5075 read; FUN_CODE_4c7f:5279 write; +4 more |
| `0x4773` | 4 refs; write, read-modify-write; 4 funcs; cur=0x6d; consts=0x6d; masks=&0xdf,|0x20,|0x40 | controller-path/status candidate | FUN_CODE_48e7:5129 write; FUN_CODE_4a1b:5164 read-modify-write; FUN_CODE_587c:6098 read-modify-write; FUN_CODE_6087:6859 read-modify-write |
| `0x4774` | 7 refs; read, test, wait/test; 3 funcs; cur=0x00; masks=&1 | controller-path/status candidate | FUN_CODE_268a:3236 read; FUN_CODE_268a:3251 read; FUN_CODE_268a:3252 test; FUN_CODE_2a9c:3436 read; +3 more |
| `0x4780` | 1 refs; read-modify-write; 1 funcs; cur=0x74; masks=|0x80 | controller-path/status candidate | FUN_CODE_4a1b:5187 read-modify-write |
| `0x4814` | 1 refs; wait/test; 1 funcs; cur=0xd9 | front-button/status byte candidate | FUN_CODE_63cb:7246 wait/test |
| `0x4815` | 1 refs; read-modify-write; 1 funcs; cur=0x21; masks=&0xcf,|0x20 | mostly-written config/state | FUN_CODE_48e7:5126 read-modify-write |
| `0x4819` | 2 refs; test; 2 funcs; cur=0x00; masks=&1 | mostly-read status | FUN_CODE_40b2:4616 test; FUN_CODE_50ca:5580 test |
| `0x4821` | 1 refs; write; 1 funcs; cur=0xc0; consts=0xc0 | mostly-written config/state | FUN_CODE_63cb:7244 write |
| `0x4822` | 1 refs; write; 1 funcs; cur=0x01 | mostly-written config/state | FUN_CODE_63cb:7243 write |
| `0x482b` | 13 refs; write; 7 funcs; cur=0x00; consts=0x01,0x05; masks=|1 | small handshake/status port | FUN_CODE_4230:4729 write; FUN_CODE_4230:4734 write; FUN_CODE_4230:4744 write; FUN_CODE_4230:4749 write; +9 more |
| `0x482c` | 16 refs; read; 7 funcs; cur=0x10 | small handshake/status port | FUN_CODE_4230:4730 read; FUN_CODE_4230:4735 read; FUN_CODE_4230:4745 read; FUN_CODE_4230:4750 read; +12 more |
| `0x482d` | 16 refs; read; 7 funcs; cur=0x48 | small handshake/status port | FUN_CODE_4230:4731 read; FUN_CODE_4230:4736 read; FUN_CODE_4230:4746 read; FUN_CODE_4230:4751 read; +12 more |
| `0x4844` | 3 refs; read-modify-write, read, test; 1 funcs; cur=0x64; masks=&0xfe,&1 | mixed/unknown | FUN_CODE_50ca:5557 read; FUN_CODE_50ca:5558 test; FUN_CODE_50ca:5559 read-modify-write |
| `0x4862` | 9 refs; write, read-modify-write; 6 funcs; cur=0x04; consts=0x00,0x30; masks=&0x7f,&0xfb,|4 | hardware init/config cluster | FUN_CODE_268a:3116 read-modify-write; FUN_CODE_3f2c:4523 read-modify-write; FUN_CODE_3f2c:4604 read-modify-write; FUN_CODE_48e7:5118 write; +5 more |
| `0x4863` | 3 refs; write, read-modify-write; 2 funcs; cur=0x00; consts=0x00,0x1c; masks=&0xdf | hardware init/config cluster | FUN_CODE_48e7:5087 read-modify-write; FUN_CODE_48e7:5119 write; FUN_CODE_59f3:6249 write |
| `0x48a0` | 14 refs; read-modify-write, read, test; 5 funcs; cur=0x00; masks=&0x7f,&0xef,&1,|0x80 | mixed/unknown | FUN_CODE_268a:3125 test; FUN_CODE_268a:3130 read; FUN_CODE_268a:3135 test; FUN_CODE_268a:3151 test; +10 more |
| `0x48d0` | 1 refs; read-modify-write; 1 funcs; cur=0x0a; masks=|2 | mostly-written config/state | FUN_CODE_5d97:6482 read-modify-write |
| `0x48d1` | 1 refs; read-modify-write; 1 funcs; cur=0x90; masks=&0xf,|0x90 | mostly-written config/state | FUN_CODE_5d97:6483 read-modify-write |
| `0x48d5` | 4 refs; read, test; 3 funcs; cur=0x03 | mostly-read status | FUN_CODE_0909:913 read; FUN_CODE_47b0:5028 test; FUN_CODE_47b0:5040 test; FUN_CODE_4a1b:5169 test |
| `0x8221` | 4 refs; write, read-modify-write, read; 3 funcs; cur=0x01; consts=0x81; masks=|1 | mixed/unknown | FUN_CODE_48e7:5148 read-modify-write; FUN_CODE_4da4:5398 read; FUN_CODE_4da4:5401 read; FUN_CODE_6493:7351 write |

## Dense Address Summary

| address | summary | likely role |
|---|---|---|
| `0x4000` | 85 refs; wait/test; 24 funcs; cur=0x00 | controller gateway/FIFO |
| `0x400d` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4011` | 6 refs; write; 3 funcs; cur=0x06; consts=0x01 | mostly-written config/state |
| `0x4012` | 8 refs; write, read; 3 funcs; cur=0xae; consts=0x00 | mixed/unknown |
| `0x4013` | 3 refs; write; 3 funcs; cur=0xd0 | mostly-written config/state |
| `0x4014` | 7 refs; write; 7 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4015` | 7 refs; write; 7 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4016` | 7 refs; write; 7 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4017` | 7 refs; write; 7 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4018` | 2 refs; write; 2 funcs; cur=0x02; consts=0x01,0x03 | mostly-written config/state |
| `0x401a` | 1 refs; write; 1 funcs; cur=0x01; consts=0x01 | mostly-written config/state |
| `0x4023` | 4 refs; write, read; 3 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x402a` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4091` | 20 refs; write; 14 funcs; cur=0x06; consts=0x00,0x01,0x06 | controller gateway/FIFO |
| `0x4092` | 21 refs; write; 15 funcs; cur=0xae; consts=0x00,0x80,0xc9 | controller gateway/FIFO |
| `0x4093` | 20 refs; write; 15 funcs; cur=0x94; consts=0x00,0x06,0x54 | controller gateway/FIFO |
| `0x4095` | 12 refs; write; 10 funcs; cur=0x06; consts=0x01,0x06,0x0b | controller gateway/FIFO |
| `0x4096` | 13 refs; write, read; 9 funcs; cur=0xae; consts=0x00,0x07,0xc9 | controller gateway/FIFO |
| `0x4097` | 10 refs; write; 9 funcs; cur=0x57; consts=0x00,0x20,0x38,0x54 | controller gateway/FIFO |
| `0x4098` | 36 refs; write, read, test; 22 funcs; cur=0x00; masks=^0x45,^0x49,^0x4c,^0x54 | controller gateway/FIFO |
| `0x40b5` | 2 refs; write; 1 funcs; cur=0x10; consts=0x14 | mostly-written config/state |
| `0x40b6` | 2 refs; write; 1 funcs; cur=0x00; consts=0x10 | mostly-written config/state |
| `0x40b7` | 2 refs; write; 1 funcs; cur=0x08; consts=0x00 | mostly-written config/state |
| `0x40b8` | 2 refs; read-modify-write; 2 funcs; cur=0x00; masks=&0xfe,|1 | mostly-written config/state |
| `0x40b9` | 1 refs; write; 1 funcs; cur=0x00 | mostly-written config/state |
| `0x40ba` | 1 refs; write; 1 funcs; cur=0x00 | mostly-written config/state |
| `0x40c0` | 1 refs; write; 1 funcs; cur=0xdc; consts=0xdc | mostly-written config/state |
| `0x40c2` | 1 refs; write; 1 funcs; cur=0x02; consts=0x02 | mostly-written config/state |
| `0x40c3` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x40d3` | 1 refs; write; 1 funcs; cur=0x20; consts=0x20 | mostly-written config/state |
| `0x40d4` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xf9 | mostly-written config/state |
| `0x40ea` | 1 refs; write; 1 funcs; cur=0x01; consts=0x01 | mostly-written config/state |
| `0x40eb` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4700` | 10 refs; read-modify-write, test, wait/test; 6 funcs; cur=0x0b; masks=&1,|2 | controller-path/status candidate |
| `0x4703` | 1 refs; read-modify-write; 1 funcs; cur=0xd0; masks=&0xcf,|0x10 | mostly-written config/state |
| `0x4704` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xf7 | controller-path/status candidate |
| `0x4709` | 2 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xfd,&0xfe,|1,|2 | mostly-written config/state |
| `0x470a` | 1 refs; test; 1 funcs; cur=0x64; masks=&1 | mostly-read status |
| `0x470b` | 1 refs; read-modify-write; 1 funcs; cur=0x06; masks=&0x7f | mostly-written config/state |
| `0x470c` | 8 refs; read; 2 funcs; cur=0x78; masks=&0xe,&0xf,&0xf0 | mixed/unknown |
| `0x470e` | 4 refs; test, wait/test; 3 funcs; cur=0xde; masks=&1 | mostly-read status |
| `0x470f` | 7 refs; read-modify-write, read, test; 2 funcs; cur=0x74; masks=&0xc,&0xe,&0xf0,&0xf3,|4 | mixed/unknown |
| `0x4710` | 3 refs; read-modify-write, read; 1 funcs; cur=0x84; masks=&0xe | mixed/unknown |
| `0x4712` | 9 refs; read, test, wait/test; 3 funcs; cur=0x0b | mostly-read status |
| `0x4717` | 1 refs; read-modify-write; 1 funcs; cur=0xf6; masks=|6 | mostly-written config/state |
| `0x471f` | 3 refs; write, read; 2 funcs; cur=0x0f | mixed/unknown |
| `0x4720` | 3 refs; write, read; 2 funcs; cur=0x0f | mixed/unknown |
| `0x4721` | 3 refs; write, read; 2 funcs; cur=0x1f | mixed/unknown |
| `0x4723` | 1 refs; write; 1 funcs; cur=0x0a; consts=0x0a | mostly-written config/state |
| `0x4724` | 1 refs; read-modify-write; 1 funcs; cur=0xb4; masks=&0x6f,|0x90 | mostly-written config/state |
| `0x4725` | 1 refs; read-modify-write; 1 funcs; cur=0x08; masks=&0xfc | mostly-written config/state |
| `0x4726` | 12 refs; write, read-modify-write, read; 3 funcs; cur=0x52; masks=&0x7f,&0xfc,|1,|2,|3 | mixed/unknown |
| `0x4727` | 2 refs; read-modify-write; 2 funcs; cur=0x1c; masks=|4,|8 | mostly-written config/state |
| `0x4728` | 1 refs; read-modify-write; 1 funcs; cur=0x1c; masks=|0xc | mostly-written config/state |
| `0x472a` | 4 refs; read-modify-write, test; 2 funcs; cur=0xc8; masks=&0x3f,&0xc0 | mixed/unknown |
| `0x472c` | 8 refs; read, test; 2 funcs; cur=0x8e; masks=&0x3f | mostly-read status |
| `0x472d` | 1 refs; test; 1 funcs; cur=0x90; masks=&1 | mostly-read status |
| `0x472e` | 8 refs; read, test; 2 funcs; cur=0x8d; masks=&0x3f | mostly-read status |
| `0x4730` | 1 refs; read-modify-write; 1 funcs; cur=0x01; masks=|1 | mostly-written config/state |
| `0x4733` | 1 refs; read-modify-write; 1 funcs; cur=0x2a; masks=&0xf,|0x20 | mostly-written config/state |
| `0x4735` | 2 refs; read-modify-write, test; 2 funcs; cur=0x84; masks=&0x43,&0xbc | mixed/unknown |
| `0x4744` | 2 refs; write; 1 funcs; cur=0x34; consts=0x00,0x34 | mostly-written config/state |
| `0x4748` | 8 refs; write, read-modify-write, read; 4 funcs; cur=0x98; consts=0x88,0x98; masks=&0x7f,|0x80 | controller-path/status candidate |
| `0x474d` | 11 refs; write, read, test; 2 funcs; cur=0xc5; consts=0x05,0x15,0x45 | mixed/unknown |
| `0x474e` | 7 refs; write; 1 funcs; cur=0x94; consts=0x30,0x50,0x90,0xa0,0xc0 | mostly-written config/state |
| `0x4756` | 1 refs; read-modify-write; 1 funcs; cur=0x20; masks=&0x9f,|0x20 | mostly-written config/state |
| `0x4761` | 1 refs; read-modify-write; 1 funcs; cur=0x16; masks=|0x16 | mostly-written config/state |
| `0x4762` | 2 refs; write, read-modify-write; 1 funcs; cur=0x00; consts=0x00; masks=&0xef | mostly-written config/state |
| `0x4763` | 1 refs; write; 1 funcs; cur=0x1f; consts=0x1f | mostly-written config/state |
| `0x4764` | 6 refs; read, test; 1 funcs; cur=0x00; masks=&1,&6 | mostly-read status |
| `0x4766` | 1 refs; read-modify-write; 1 funcs; cur=0x0c; masks=|0xc | mostly-written config/state |
| `0x4770` | 3 refs; read-modify-write; 2 funcs; cur=0x23; masks=&0xfd,|2,|8 | mostly-written config/state |
| `0x4771` | 1 refs; write; 1 funcs; cur=0x4e; consts=0x4e | mostly-written config/state |
| `0x4772` | 3 refs; read, test; 1 funcs; cur=0x00; masks=&0xf,&1 | mostly-read status |
| `0x4773` | 4 refs; write, read-modify-write; 4 funcs; cur=0x6d; consts=0x6d; masks=&0xdf,|0x20,|0x40 | controller-path/status candidate |
| `0x4774` | 7 refs; read, test, wait/test; 3 funcs; cur=0x00; masks=&1 | controller-path/status candidate |
| `0x4780` | 1 refs; read-modify-write; 1 funcs; cur=0x74; masks=|0x80 | controller-path/status candidate |
| `0x4781` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4782` | 10 refs; write, read-modify-write, test; 3 funcs; cur=0x01; masks=&0x7f,&1,&6 | mixed/unknown |
| `0x4784` | 5 refs; read-modify-write, test; 5 funcs; cur=0x80; masks=&1,|0x40,|0x80 | mixed/unknown |
| `0x4788` | 1 refs; read-modify-write; 1 funcs; cur=0x09; masks=|1 | mostly-written config/state |
| `0x478c` | 1 refs; read-modify-write; 1 funcs; cur=0x81; masks=|1 | mostly-written config/state |
| `0x478f` | 3 refs; test; 3 funcs; cur=0x00; masks=&1 | mostly-read status |
| `0x4796` | 2 refs; write, test; 2 funcs; cur=0x08 | mixed/unknown |
| `0x4797` | 3 refs; write, read, test; 2 funcs; cur=0x08; masks=&0xe | mixed/unknown |
| `0x4799` | 1 refs; read-modify-write; 1 funcs; cur=0x01; masks=|1 | mostly-written config/state |
| `0x479e` | 5 refs; write, read-modify-write; 2 funcs; cur=0x02; consts=0x00; masks=&0x10,&0x7f,&0xaf,|0x10,|0x87,|0xa8 | mostly-written config/state |
| `0x47a0` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x47a1` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x47a2` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x47a3` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x47a6` | 10 refs; write; 3 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x47a7` | 1 refs; read-modify-write; 1 funcs; cur=0x81; masks=&0xfd,|0x81 | mostly-written config/state |
| `0x47a8` | 1 refs; read-modify-write; 1 funcs; cur=0x60; masks=|0x80 | mostly-written config/state |
| `0x47a9` | 1 refs; write; 1 funcs; cur=0x1f; consts=0x1f | mostly-written config/state |
| `0x47aa` | 4 refs; read-modify-write, read, test; 1 funcs; cur=0x00; masks=&0xf,&0xf0,&1 | mixed/unknown |
| `0x47af` | 2 refs; write; 2 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x47b0` | 3 refs; write; 3 funcs; cur=0x06; consts=0x00 | packet FIFO/window |
| `0x47b1` | 15 refs; write, read; 3 funcs; cur=0x00; consts=0x00,0x45 | packet FIFO/window |
| `0x47b9` | 3 refs; read-modify-write; 3 funcs; cur=0x01; masks=&0xef | mostly-written config/state |
| `0x47c0` | 7 refs; write, test; 3 funcs; cur=0x80; consts=0x04,0x08; masks=&0x30 | mixed/unknown |
| `0x47c1` | 4 refs; read, test; 4 funcs; cur=0x01; masks=&1 | mostly-read status |
| `0x47c2` | 5 refs; write, read; 2 funcs; cur=0x01; consts=0x01,0x03 | mixed/unknown |
| `0x47c3` | 2 refs; write; 1 funcs; cur=0x00; consts=0x00,0x01 | mostly-written config/state |
| `0x47c4` | 10 refs; write, read; 6 funcs; cur=0xff; consts=0x00 | mixed/unknown |
| `0x47c5` | 10 refs; write, read; 6 funcs; cur=0xff; consts=0x00 | mixed/unknown |
| `0x47c6` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x47c7` | 6 refs; read, test; 3 funcs; cur=0xa0 | mostly-read status |
| `0x47c8` | 2 refs; wait/test; 2 funcs; cur=0x00; masks=&1 | mostly-read status |
| `0x47c9` | 13 refs; write, read-modify-write; 6 funcs; cur=0x50; consts=0x50,0x51; masks=&0xef | mostly-written config/state |
| `0x47ca` | 1 refs; write; 1 funcs; cur=0xd0; consts=0x50 | mostly-written config/state |
| `0x47cb` | 18 refs; write, read; 5 funcs; cur=0x00; consts=0x00,0x04,0x40,0x54 | mixed/unknown |
| `0x47cc` | 1 refs; write; 1 funcs; cur=0xb4; consts=0xb4 | mostly-written config/state |
| `0x47cd` | 8 refs; read-modify-write; 7 funcs; cur=0x13; masks=&0xcf,&0xf7,|0x10,|1 | mostly-written config/state |
| `0x47ce` | 1 refs; write; 1 funcs; cur=0x9c; consts=0x9c | mostly-written config/state |
| `0x47cf` | 1 refs; write; 1 funcs; cur=0x01; consts=0x01 | mostly-written config/state |
| `0x47d0` | 14 refs; write; 7 funcs; cur=0x00; consts=0x00,0x01,0x08,0x10 | mostly-written config/state |
| `0x47d1` | 4 refs; write; 4 funcs; cur=0x00; consts=0x02,0x04,0x10 | mostly-written config/state |
| `0x47d2` | 12 refs; write, read-modify-write; 7 funcs; cur=0x01; consts=0x01; masks=&0xfe,|1 | mostly-written config/state |
| `0x47d5` | 4 refs; wait/test; 2 funcs; cur=0xf0; masks=&1 | mostly-read status |
| `0x47d6` | 2 refs; write; 2 funcs; cur=0x00; consts=0x04 | mostly-written config/state |
| `0x47d7` | 3 refs; read-modify-write; 3 funcs; cur=0x09; masks=&0xfe | mostly-written config/state |
| `0x47f0` | 2 refs; write; 2 funcs; cur=0x08 | mostly-written config/state |
| `0x47f2` | 2 refs; write; 2 funcs; cur=0x08 | mostly-written config/state |
| `0x47f3` | 5 refs; read-modify-write; 4 funcs; cur=0x83; masks=&0x7f,|0x80 | mostly-written config/state |
| `0x47f4` | 2 refs; read-modify-write; 2 funcs; cur=0x84; masks=&0xf7,|0xc | mostly-written config/state |
| `0x47f9` | 2 refs; write, read; 2 funcs; cur=0x01 | mixed/unknown |
| `0x47fa` | 2 refs; write, read; 2 funcs; cur=0x86 | mixed/unknown |
| `0x47fb` | 2 refs; write; 1 funcs; cur=0x00 | mostly-written config/state |
| `0x47fc` | 2 refs; write; 1 funcs; cur=0x1f | mostly-written config/state |
| `0x47fd` | 2 refs; write; 1 funcs; cur=0x00 | mostly-written config/state |
| `0x47fe` | 1 refs; write; 1 funcs; cur=0x2f | mostly-written config/state |
| `0x47ff` | 2 refs; read-modify-write, test; 2 funcs; cur=0x74; masks=&1,|0x20 | mixed/unknown |
| `0x4800` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0x7f | mostly-written config/state |
| `0x4801` | 1 refs; write; 1 funcs; cur=0x05; consts=0x05 | mostly-written config/state |
| `0x4802` | 2 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0x7f,|0x80 | mostly-written config/state |
| `0x4804` | 1 refs; write; 1 funcs; cur=0x08; consts=0x08 | mostly-written config/state |
| `0x4806` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4807` | 1 refs; write; 1 funcs; cur=0x01; consts=0x01 | mostly-written config/state |
| `0x4814` | 1 refs; wait/test; 1 funcs; cur=0xd9 | front-button/status byte candidate |
| `0x4815` | 1 refs; read-modify-write; 1 funcs; cur=0x21; masks=&0xcf,|0x20 | mostly-written config/state |
| `0x4819` | 2 refs; test; 2 funcs; cur=0x00; masks=&1 | mostly-read status |
| `0x4821` | 1 refs; write; 1 funcs; cur=0xc0; consts=0xc0 | mostly-written config/state |
| `0x4822` | 1 refs; write; 1 funcs; cur=0x01 | mostly-written config/state |
| `0x482b` | 13 refs; write; 7 funcs; cur=0x00; consts=0x01,0x05; masks=|1 | small handshake/status port |
| `0x482c` | 16 refs; read; 7 funcs; cur=0x10 | small handshake/status port |
| `0x482d` | 16 refs; read; 7 funcs; cur=0x48 | small handshake/status port |
| `0x483f` | 2 refs; write; 1 funcs; cur=0x01; consts=0x00,0x01 | mostly-written config/state |
| `0x4840` | 3 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4842` | 3 refs; read-modify-write; 3 funcs; cur=0xc2; masks=|0x80 | mostly-written config/state |
| `0x4844` | 3 refs; read-modify-write, read, test; 1 funcs; cur=0x64; masks=&0xfe,&1 | mixed/unknown |
| `0x4860` | 2 refs; write; 2 funcs; cur=0x00; consts=0x00 | hardware init/config cluster |
| `0x4861` | 2 refs; write; 2 funcs; cur=0x00; consts=0x00 | hardware init/config cluster |
| `0x4862` | 9 refs; write, read-modify-write; 6 funcs; cur=0x04; consts=0x00,0x30; masks=&0x7f,&0xfb,|4 | hardware init/config cluster |
| `0x4863` | 3 refs; write, read-modify-write; 2 funcs; cur=0x00; consts=0x00,0x1c; masks=&0xdf | hardware init/config cluster |
| `0x4864` | 2 refs; write; 2 funcs; cur=0x00; consts=0x00,0x10 | hardware init/config cluster |
| `0x4865` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | hardware init/config cluster |
| `0x4867` | 1 refs; write; 1 funcs; cur=0x61; consts=0x61 | hardware init/config cluster |
| `0x486a` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | hardware init/config cluster |
| `0x486b` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | hardware init/config cluster |
| `0x4876` | 2 refs; write; 2 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4877` | 2 refs; write; 2 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x4878` | 2 refs; write; 2 funcs; cur=0x03; consts=0x01 | mostly-written config/state |
| `0x487c` | 1 refs; read-modify-write; 1 funcs; cur=0x10; masks=|0x10 | mostly-written config/state |
| `0x48a0` | 14 refs; read-modify-write, read, test; 5 funcs; cur=0x00; masks=&0x7f,&0xef,&1,|0x80 | mixed/unknown |
| `0x48a4` | 1 refs; wait/test; 1 funcs; cur=0x20; masks=&1 | mostly-read status |
| `0x48a5` | 2 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xe7,|0x18 | mostly-written config/state |
| `0x48ac` | 2 refs; write; 2 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x48ad` | 2 refs; write; 2 funcs; cur=0x01; consts=0x01 | mostly-written config/state |
| `0x48af` | 1 refs; read-modify-write; 1 funcs; cur=0x11; masks=&0xcc,|0x11 | mostly-written config/state |
| `0x48d0` | 1 refs; read-modify-write; 1 funcs; cur=0x0a; masks=|2 | mostly-written config/state |
| `0x48d1` | 1 refs; read-modify-write; 1 funcs; cur=0x90; masks=&0xf,|0x90 | mostly-written config/state |
| `0x48d5` | 4 refs; read, test; 3 funcs; cur=0x03 | mostly-read status |
| `0x48ee` | 1 refs; read-modify-write; 1 funcs; cur=0x10; masks=&0xfd | mostly-written config/state |
| `0x48fc` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xf0 | mostly-written config/state |
| `0x5904` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | helper-init hardware cluster |
| `0x5905` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | helper-init hardware cluster |
| `0x5906` | 1 refs; read-modify-write; 1 funcs; cur=0x10; masks=&0x1c | helper-init hardware cluster |
| `0x592a` | 1 refs; read-modify-write; 1 funcs; cur=0x33; masks=&0xf7 | helper-init hardware cluster |
| `0x5954` | 1 refs; read-modify-write; 1 funcs; cur=0x07; masks=&0x3f | helper-init hardware cluster |
| `0x59c0` | 1 refs; read-modify-write; 1 funcs; cur=0x04; masks=&0xfe,|4 | helper-init hardware cluster |
| `0x59f0` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | helper-init hardware cluster |
| `0x59f1` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0x3f | helper-init hardware cluster |
| `0x5a00` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xf8 | helper-init hardware cluster |
| `0x5a01` | 1 refs; write; 1 funcs; cur=0x18; consts=0x18 | helper-init hardware cluster |
| `0x5a24` | 1 refs; read-modify-write; 1 funcs; cur=0x30; masks=&0x30 | helper-init hardware cluster |
| `0x5a31` | 1 refs; read-modify-write; 1 funcs; cur=0x00; masks=&0xfd | helper-init hardware cluster |
| `0x810e` | 5 refs; write, read; 5 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x810f` | 5 refs; write, read; 5 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x8110` | 5 refs; write, read; 5 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x8111` | 5 refs; write, read; 5 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x8164` | 32 refs; read-modify-write, read, test; 15 funcs; cur=0x00; masks=&0xfb,&0xfc,&0xfd,&0xfe,&1,|1,|2,|4 | mixed/unknown |
| `0x816a` | 5 refs; read-modify-write, test; 1 funcs; cur=0x10; masks=&0xef,&1,|0x10 | mixed/unknown |
| `0x8179` | 9 refs; read-modify-write; 8 funcs; cur=0x00; masks=&0xef | mostly-written config/state |
| `0x817b` | 5 refs; read-modify-write, test; 4 funcs; cur=0x00; masks=&0xef,&1,|0x10 | mixed/unknown |
| `0x818a` | 22 refs; write, read, test; 5 funcs; cur=0x12 | CDB/packet shadow |
| `0x818b` | 7 refs; write, read, test; 6 funcs; cur=0x00; masks=&1 | CDB/packet shadow |
| `0x818c` | 9 refs; write, read, test; 4 funcs; cur=0x00; masks=&1 | CDB/packet shadow |
| `0x818d` | 19 refs; write, read, test; 4 funcs; cur=0x00; consts=0x00,0x01,0x02 | CDB/packet shadow |
| `0x818e` | 28 refs; write, read, test; 6 funcs; cur=0xb0; consts=0x00,0x12,0x80,0xb0; masks=&0xf0,&3 | CDB/packet shadow |
| `0x818f` | 13 refs; write, read, test; 4 funcs; cur=0x40; consts=0x00; masks=&0xc0 | CDB/packet shadow |
| `0x8190` | 7 refs; write, read-modify-write, read, test; 3 funcs; cur=0x10; masks=&0xef,&0xf7,|0x10,|8 | CDB/packet shadow |
| `0x8191` | 17 refs; write, read, test; 3 funcs; cur=0x81 | CDB/packet shadow |
| `0x8192` | 14 refs; write, read, test; 3 funcs; cur=0x80; masks=&1,^0x80 | CDB/packet shadow |
| `0x8193` | 8 refs; write, read, test; 2 funcs; cur=0x00; masks=&1 | CDB/packet shadow |
| `0x8194` | 9 refs; write, read; 3 funcs; cur=0x00 | CDB/packet shadow |
| `0x8195` | 5 refs; write, read; 2 funcs; cur=0x00 | CDB/packet shadow |
| `0x8196` | 2 refs; test; 1 funcs; cur=0x00 | mostly-read status |
| `0x819f` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x81a0` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x81b3` | 2 refs; write, test; 1 funcs; cur=0x00 | mixed/unknown |
| `0x81b4` | 1 refs; write; 1 funcs; cur=0x00 | mostly-written config/state |
| `0x8221` | 4 refs; write, read-modify-write, read; 3 funcs; cur=0x01; consts=0x81; masks=|1 | mixed/unknown |
| `0x8227` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8228` | 2 refs; read; 1 funcs; cur=0x2c | mixed/unknown |
| `0x8229` | 3 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x822a` | 3 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x822b` | 3 refs; read; 1 funcs; cur=0x70 | mixed/unknown |
| `0x822c` | 3 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x822d` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x822e` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x822f` | 2 refs; read; 1 funcs; cur=0x40 | mixed/unknown |
| `0x8230` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8231` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8232` | 1 refs; read; 1 funcs; cur=0x08 | mixed/unknown |
| `0x8233` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8234` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8235` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8236` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8237` | 1 refs; read; 1 funcs; cur=0x50 | mixed/unknown |
| `0x8238` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8239` | 1 refs; read; 1 funcs; cur=0x40 | mixed/unknown |
| `0x823a` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8240` | 17 refs; read-modify-write, test; 3 funcs; cur=0x01; masks=&0x7f,&0xf3,&1,|0x20,|0x40,|1,|2,|4,|8 | mixed/unknown |
| `0x8243` | 8 refs; read-modify-write, test; 1 funcs; cur=0x00; masks=&0x41,&0xbe,&0xdf,&0xfe,|0x40,|1 | mixed/unknown |
| `0x8244` | 28 refs; write, read-modify-write, read, test, wait/test; 5 funcs; cur=0x00; consts=0x00,0x10; masks=&1,&7 | mixed/unknown |
| `0x8245` | 26 refs; write, read-modify-write, read, test; 6 funcs; cur=0x01; consts=0x00,0x01; masks=&0x30,&0xc0,&7 | mixed/unknown |
| `0x8246` | 14 refs; write, read, test; 5 funcs; cur=0x80; consts=0x80 | mixed/unknown |
| `0x8247` | 16 refs; write, read, test; 5 funcs; cur=0x00; consts=0x00; masks=&7 | mixed/unknown |
| `0x8248` | 3 refs; write, read; 3 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x8249` | 3 refs; write, read; 3 funcs; cur=0x00; consts=0x01 | mixed/unknown |
| `0x824a` | 3 refs; write, read; 3 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x824b` | 4 refs; write, read; 3 funcs; cur=0x00; consts=0x00,0x30 | mixed/unknown |
| `0x824c` | 17 refs; write, read-modify-write, read, test, wait/test; 5 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x824d` | 15 refs; write, read; 5 funcs; cur=0x01; consts=0x10 | mixed/unknown |
| `0x824e` | 14 refs; read-modify-write, read; 5 funcs; cur=0x80; masks=&0xfc | mixed/unknown |
| `0x824f` | 15 refs; write, read; 5 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x8250` | 11 refs; write, read; 7 funcs; cur=0x00; consts=0x00 | mixed/unknown |
| `0x8251` | 11 refs; write, read; 6 funcs; cur=0xbc; consts=0x08 | mixed/unknown |
| `0x8252` | 7 refs; write, read-modify-write, read; 3 funcs; cur=0x33; masks=&0xfc | mixed/unknown |
| `0x8253` | 10 refs; write, read; 4 funcs; cur=0x38; consts=0x00 | mixed/unknown |
| `0x8254` | 15 refs; write, read-modify-write, read, test, wait/test; 5 funcs; cur=0x00; consts=0x00; masks=&0xfc | mixed/unknown |
| `0x8255` | 16 refs; write, read-modify-write, read, test; 6 funcs; cur=0xbc; consts=0x00 | mixed/unknown |
| `0x8256` | 32 refs; write, read-modify-write, read, test, wait/test; 5 funcs; cur=0x10; consts=0x00,0x10,0xee | mixed/unknown |
| `0x8257` | 25 refs; write, read-modify-write, read, test; 5 funcs; cur=0x10; consts=0x00; masks=&0xf0 | mixed/unknown |
| `0x8258` | 7 refs; write, read; 2 funcs; cur=0x00 | mixed/unknown |
| `0x8259` | 5 refs; write, read; 2 funcs; cur=0x00 | mixed/unknown |
| `0x825a` | 5 refs; write, read, test; 2 funcs; cur=0x0b; masks=&7 | mixed/unknown |
| `0x825b` | 1 refs; read; 1 funcs; cur=0xc0 | mixed/unknown |
| `0x825c` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x825d` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x825e` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x825f` | 2 refs; read; 1 funcs; cur=0xbc | mixed/unknown |
| `0x8260` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8261` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8262` | 2 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8263` | 2 refs; read; 1 funcs; cur=0xbb | mixed/unknown |
| `0x8264` | 17 refs; write, read-modify-write, read, wait/test; 1 funcs; cur=0x10; consts=0x00,0x10 | mixed/unknown |
| `0x8274` | 1 refs; read-modify-write; 1 funcs; cur=0xe7; masks=^0x87 | mostly-written config/state |
| `0x8275` | 2 refs; write, read; 1 funcs; cur=0x01 | mixed/unknown |
| `0x8276` | 2 refs; write, read; 1 funcs; cur=0xd2 | mixed/unknown |
| `0x8277` | 8 refs; write, read-modify-write, read, test; 2 funcs; cur=0x00; consts=0x00; masks=&7 | mixed/unknown |
| `0x8278` | 3 refs; write; 2 funcs; cur=0x00; consts=0x00,0x01 | mostly-written config/state |
| `0x8279` | 5 refs; read, test; 1 funcs; cur=0x00; masks=&0x7f,&0xf | mostly-read status |
| `0x827a` | 8 refs; write, read, test; 1 funcs; cur=0x00 | mixed/unknown |
| `0x827b` | 3 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8281` | 20 refs; write, read; 5 funcs; cur=0x00; consts=0x01,0x08,0x10,0x83 | mixed/unknown |
| `0x8282` | 17 refs; write; 4 funcs; cur=0x00; consts=0x43,0x49,0x4f,0x50,0x52,0x53,0x56 | mostly-written config/state |
| `0x8283` | 18 refs; write; 4 funcs; cur=0x00; consts=0x00,0x45,0x48,0x4b,0x4d,0x4e,0x52,0x53 | mostly-written config/state |
| `0x8284` | 21 refs; write, read-modify-write; 4 funcs; cur=0x00; consts=0x00,0x21,0x30,0x31,0x42,0x43,0x44,0x53,0x54; masks=|0x80 | mostly-written config/state |
| `0x8285` | 6 refs; write, read-modify-write, read; 1 funcs; cur=0x00; consts=0x44; masks=|0x80 | mixed/unknown |
| `0x8289` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x828d` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x8291` | 1 refs; read; 1 funcs; cur=0x00 | mixed/unknown |
| `0x82a5` | 13 refs; write, read, test; 2 funcs; cur=0xff; consts=0x02,0x03,0x04,0x05,0x07,0xff; masks=&7 | mixed/unknown |
| `0x82a6` | 4 refs; write; 2 funcs; cur=0x00; consts=0x00,0x02,0x11 | mostly-written config/state |
| `0x82a7` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x82ac` | 1 refs; write; 1 funcs; cur=0x00; consts=0x00 | mostly-written config/state |
| `0x82af` | 7 refs; write, read-modify-write, test; 2 funcs; cur=0x02; consts=0x00; masks=&1,|0x10,|1,|2,|4,|8 | mixed/unknown |

## Function Clusters

### `FUN_CODE_002e`

`0x40d4`, `0x8196`, `0x8227`, `0x8228`, `0x8244`, `0x8245`, `0x8246`, `0x8247`, `0x8248`, `0x8249`, `0x824a`, `0x824b`, `0x824c`, `0x824d`, `0x824e`, `0x824f`, `0x8250`, `0x8251`, `0x8252`, `0x8253`, `0x8254`, `0x8255`, `0x8256`, `0x8257`

- `699` `read-modify-write` `0x40d4`: `DAT_EXTMEM_40d4 = DAT_EXTMEM_40d4 & 0xf9;`
- `731` `test` `0x8196`: `if (DAT_EXTMEM_8196 != '\x01') {`
- `732` `test` `0x8196`: `if (DAT_EXTMEM_8196 == '\x02') {`
- `789` `read` `0x8227`: `bVar7 = DAT_EXTMEM_8227 - ((CARRY1(DAT_EXTMEM_8247,DAT_EXTMEM_8228) << 7) >> 7);`
- `789` `read` `0x8228`: `bVar7 = DAT_EXTMEM_8227 - ((CARRY1(DAT_EXTMEM_8247,DAT_EXTMEM_8228) << 7) >> 7);`
- `792` `read` `0x8228`: `DAT_EXTMEM_8246 + bVar7,DAT_EXTMEM_8247 + DAT_EXTMEM_8228);`
- `761` `read` `0x8244`: `DAT_INTMEM_37 = DAT_EXTMEM_8244;`
- `762` `read` `0x8244`: `uVar3 = DAT_EXTMEM_8244;`
- `790` `read` `0x8244`: `FUN_CODE_1df7(0x8244,DAT_EXTMEM_8244,`
- `798` `read` `0x8244`: `FUN_CODE_1717(DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `760` `read` `0x8245`: `DAT_INTMEM_38 = DAT_EXTMEM_8245;`
- `763` `read` `0x8245`: `cVar15 = DAT_EXTMEM_8245;`
- `791` `read` `0x8245`: `DAT_EXTMEM_8245 - ((CARRY1(DAT_EXTMEM_8246,bVar7) << 7) >> 7),`
- `798` `read` `0x8245`: `FUN_CODE_1717(DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `759` `read` `0x8246`: `DAT_INTMEM_39 = DAT_EXTMEM_8246;`
- `764` `read` `0x8246`: `bVar7 = DAT_EXTMEM_8246;`
- `791` `read` `0x8246`: `DAT_EXTMEM_8245 - ((CARRY1(DAT_EXTMEM_8246,bVar7) << 7) >> 7),`
- `792` `read` `0x8246`: `DAT_EXTMEM_8246 + bVar7,DAT_EXTMEM_8247 + DAT_EXTMEM_8228);`
- `798` `read` `0x8246`: `FUN_CODE_1717(DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `758` `read` `0x8247`: `DAT_INTMEM_3a = DAT_EXTMEM_8247;`
- `789` `read` `0x8247`: `bVar7 = DAT_EXTMEM_8227 - ((CARRY1(DAT_EXTMEM_8247,DAT_EXTMEM_8228) << 7) >> 7);`
- `792` `read` `0x8247`: `DAT_EXTMEM_8246 + bVar7,DAT_EXTMEM_8247 + DAT_EXTMEM_8228);`
- `798` `read` `0x8247`: `FUN_CODE_1717(DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `720` `read` `0x8248`: `FUN_CODE_1d9c(8,DAT_EXTMEM_8248,DAT_EXTMEM_8249,DAT_EXTMEM_824a);`
- ... 83 more refs

### `FUN_CODE_0909`

`0x48d5`, `0x8244`, `0x8245`, `0x8246`, `0x8247`, `0x8254`, `0x8255`, `0x8256`, `0x8257`, `0x8258`, `0x8259`, `0x825a`, `0x8281`, `0x8282`, `0x8283`, `0x8284`, `0x82a7`, `0x82ac`

- `913` `read` `0x48d5`: `DAT_EXTMEM_8246 = DAT_EXTMEM_48d5 < '\0';`
- `914` `write` `0x8244`: `DAT_EXTMEM_8244 = DAT_EXTMEM_5296 & 1;`
- `918` `test` `0x8244`: `if (((bool)DAT_EXTMEM_8246) || (DAT_EXTMEM_8244 == 0)) {`
- `925` `read` `0x8244`: `DAT_EXTMEM_8283 = DAT_EXTMEM_8244;`
- `912` `write` `0x8245`: `DAT_EXTMEM_8245 = 0;`
- `913` `write` `0x8246`: `DAT_EXTMEM_8246 = DAT_EXTMEM_48d5 < '\0';`
- `918` `test` `0x8246`: `if (((bool)DAT_EXTMEM_8246) || (DAT_EXTMEM_8244 == 0)) {`
- `924` `read` `0x8246`: `DAT_EXTMEM_8282 = DAT_EXTMEM_8246;`
- `915` `write` `0x8247`: `DAT_EXTMEM_8247 = DAT_EXTMEM_5296 >> 1 & 7;`
- `926` `read` `0x8247`: `DAT_EXTMEM_8284 = DAT_EXTMEM_8247;`
- `962` `test` `0x8247`: `if ((DAT_EXTMEM_8247 == (DAT_EXTMEM_825a & 7)) || (DAT_EXTMEM_8247 == 0)) {`
- `975` `test` `0x8247`: `if ((DAT_EXTMEM_8247 != (DAT_EXTMEM_825a & 7)) &&`
- `976` `read` `0x8247`: `(bVar10 = DAT_EXTMEM_8247, DAT_EXTMEM_8247 != 0)) {`
- `1009` `read` `0x8247`: `DAT_EXTMEM_8283 = DAT_EXTMEM_8247;`
- `964` `read` `0x8254`: `bVar10 = FUN_CODE_1d8b(DAT_EXTMEM_8254,DAT_EXTMEM_8255,DAT_EXTMEM_8256,DAT_EXTMEM_8257,0,2,0,0`
- `968` `read` `0x8254`: `bVar10 = FUN_CODE_1d8b(DAT_EXTMEM_8257,DAT_EXTMEM_8254,0,1,0xa0,0);`
- `964` `read` `0x8255`: `bVar10 = FUN_CODE_1d8b(DAT_EXTMEM_8254,DAT_EXTMEM_8255,DAT_EXTMEM_8256,DAT_EXTMEM_8257,0,2,0,0`
- `994` `read` `0x8255`: `DAT_EXTMEM_8282 = DAT_EXTMEM_8255;`
- `964` `read` `0x8256`: `bVar10 = FUN_CODE_1d8b(DAT_EXTMEM_8254,DAT_EXTMEM_8255,DAT_EXTMEM_8256,DAT_EXTMEM_8257,0,2,0,0`
- `995` `read` `0x8256`: `DAT_EXTMEM_8283 = DAT_EXTMEM_8256;`
- `964` `read` `0x8257`: `bVar10 = FUN_CODE_1d8b(DAT_EXTMEM_8254,DAT_EXTMEM_8255,DAT_EXTMEM_8256,DAT_EXTMEM_8257,0,2,0,0`
- `968` `read` `0x8257`: `bVar10 = FUN_CODE_1d8b(DAT_EXTMEM_8257,DAT_EXTMEM_8254,0,1,0xa0,0);`
- `996` `read` `0x8257`: `DAT_EXTMEM_8284 = DAT_EXTMEM_8257;`
- `945` `write` `0x8258`: `DAT_EXTMEM_8258 = DAT_EXTMEM_529b;`
- ... 46 more refs

### `FUN_CODE_0f90`

`0x47d1`, `0x8164`, `0x818b`, `0x818e`

- `1043` `write` `0x47d1`: `DAT_EXTMEM_47d1 = 4;`
- `1047` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 2;`
- `1025` `test` `0x818b`: `if ((DAT_EXTMEM_818b & 1) != 0) {`
- `1022` `read` `0x818e`: `DAT_INTMEM_2b = DAT_EXTMEM_818e & 0xf0;`
- `1030` `test` `0x818e`: `if ((DAT_EXTMEM_818e & 3) == 2) {`
- `1035` `write` `0x818e`: `else if ((DAT_EXTMEM_818e & 3) == 1) {`

### `FUN_CODE_111a`

`0x8245`, `0x8246`, `0x8247`, `0x8248`, `0x8249`, `0x824a`, `0x824b`, `0x824c`, `0x824d`, `0x824e`, `0x824f`, `0x8250`

- `1263` `read` `0x8245`: `FUN_CODE_1deb(0x5d,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247,DAT_EXTMEM_8248);`
- `1263` `read` `0x8246`: `FUN_CODE_1deb(0x5d,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247,DAT_EXTMEM_8248);`
- `1263` `read` `0x8247`: `FUN_CODE_1deb(0x5d,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247,DAT_EXTMEM_8248);`
- `1263` `read` `0x8248`: `FUN_CODE_1deb(0x5d,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247,DAT_EXTMEM_8248);`
- `1264` `read` `0x8249`: `FUN_CODE_1deb(0x61,DAT_EXTMEM_8249,DAT_EXTMEM_824a,DAT_EXTMEM_824b,DAT_EXTMEM_824c);`
- `1264` `read` `0x824a`: `FUN_CODE_1deb(0x61,DAT_EXTMEM_8249,DAT_EXTMEM_824a,DAT_EXTMEM_824b,DAT_EXTMEM_824c);`
- `1264` `read` `0x824b`: `FUN_CODE_1deb(0x61,DAT_EXTMEM_8249,DAT_EXTMEM_824a,DAT_EXTMEM_824b,DAT_EXTMEM_824c);`
- `1264` `read` `0x824c`: `FUN_CODE_1deb(0x61,DAT_EXTMEM_8249,DAT_EXTMEM_824a,DAT_EXTMEM_824b,DAT_EXTMEM_824c);`
- `1268` `read` `0x824d`: `FUN_CODE_1deb(0x65,DAT_EXTMEM_824d,DAT_EXTMEM_824e);`
- `1268` `read` `0x824e`: `FUN_CODE_1deb(0x65,DAT_EXTMEM_824d,DAT_EXTMEM_824e);`
- `1266` `read` `0x824f`: `bVar2 = DAT_EXTMEM_824f;`
- `1267` `read` `0x8250`: `cVar3 = DAT_EXTMEM_8250;`

### `FUN_CODE_1ea0`

`0x47af`, `0x47b1`, `0x47cd`, `0x47d6`, `0x8164`, `0x818a`

- `2922` `write` `0x47af`: `DAT_EXTMEM_47af = 0;`
- `2925` `write` `0x47b1`: `DAT_EXTMEM_47b1 = uVar1;`
- `2927` `write` `0x47b1`: `DAT_EXTMEM_47b1 = 0x45;`
- `2951` `read-modify-write` `0x47cd`: `DAT_EXTMEM_47cd = DAT_EXTMEM_47cd | 1;`
- `2921` `write` `0x47d6`: `DAT_EXTMEM_47d6 = 4;`
- `2865` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 2;`
- `2885` `test` `0x8164`: `if ((DAT_EXTMEM_8164 >> 2 & 1) != 0) {`
- `2889` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 & 0xfb;`
- `2856` `read` `0x818a`: `FUN_CODE_6141(DAT_EXTMEM_818a,0);`
- `2858` `test` `0x818a`: `if (DAT_EXTMEM_818a == -0x11) {`
- `2862` `test` `0x818a`: `if (DAT_EXTMEM_818a != -0x5f) {`
- `2879` `test` `0x818a`: `if ((((DAT_EXTMEM_818a != '\x12') && (DAT_EXTMEM_818a != -0xf)) && (DAT_EXTMEM_818a != -0xc)) &&`
- `2880` `write` `0x818a`: `(DAT_EXTMEM_818a != 'J')) {`
- `2881` `test` `0x818a`: `if (DAT_EXTMEM_818a == '\x03') {`
- `2892` `test` `0x818a`: `if (((((DAT_EXTMEM_818a != '\x1b') && (DAT_EXTMEM_818a != 'U')) &&`
- `2893` `read` `0x818a`: `((DAT_EXTMEM_818a != -0x45 && ((DAT_EXTMEM_818a != -0x43 && (DAT_EXTMEM_818a != 'Z'))))))`
- `2894` `read` `0x818a`: `&& (DAT_EXTMEM_818a != '<')) && ((DAT_EXTMEM_818a != ';' && (DAT_EXTMEM_818a != '\x1e')))) {`
- `2904` `test` `0x818a`: `if (DAT_EXTMEM_818a != '\0') {`
- `2905` `test` `0x818a`: `if (DAT_EXTMEM_818a == '\x12') {`
- `2909` `test` `0x818a`: `if (DAT_EXTMEM_818a == '\x1b') {`
- `2913` `test` `0x818a`: `if (DAT_EXTMEM_818a == ';') {`
- `2917` `test` `0x818a`: `if (DAT_EXTMEM_818a == -0x21) {`
- `2931` `test` `0x818a`: `if (DAT_EXTMEM_818a == -0xf) {`
- `2935` `test` `0x818a`: `if (DAT_EXTMEM_818a == '<') {`

### `FUN_CODE_2000`

`0x47cd`, `0x48a4`, `0x48a5`, `0x8164`

- `2967` `read-modify-write` `0x47cd`: `DAT_EXTMEM_47cd = DAT_EXTMEM_47cd | 1;`
- `2970` `wait/test` `0x48a4`: `} while ((DAT_EXTMEM_48a4 >> 5 & 1) == 1);`
- `2971` `read-modify-write` `0x48a5`: `DAT_EXTMEM_48a5 = DAT_EXTMEM_48a5 | 0x18;`
- `3011` `read-modify-write` `0x48a5`: `DAT_EXTMEM_48a5 = DAT_EXTMEM_48a5 & 0xe7;`
- `3008` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 2;`

### `FUN_CODE_2133`

`0x4876`, `0x4877`, `0x4878`, `0x48ac`, `0x48ad`

- `3035` `write` `0x4876`: `DAT_EXTMEM_4876 = 0;`
- `3036` `write` `0x4877`: `DAT_EXTMEM_4877 = 0;`
- `3037` `write` `0x4878`: `DAT_EXTMEM_4878 = param_2;`
- `3040` `write` `0x48ac`: `DAT_EXTMEM_48ac = 0;`
- `3034` `write` `0x48ad`: `DAT_EXTMEM_48ad = param_3;`

### `FUN_CODE_2172`

`0x4876`, `0x4877`, `0x4878`, `0x48ac`, `0x48ad`

- `3071` `write` `0x4876`: `DAT_EXTMEM_4876 = 0;`
- `3072` `write` `0x4877`: `DAT_EXTMEM_4877 = 0;`
- `3073` `write` `0x4878`: `DAT_EXTMEM_4878 = 1;`
- `3075` `write` `0x48ac`: `DAT_EXTMEM_48ac = 0;`
- `3070` `write` `0x48ad`: `DAT_EXTMEM_48ad = 1;`

### `FUN_CODE_268a`

`0x4000`, `0x4014`, `0x4015`, `0x4016`, `0x4017`, `0x4023`, `0x4091`, `0x4092`, `0x4093`, `0x4098`, `0x4700`, `0x4774`, `0x4782`, `0x478f`, `0x47a6`, `0x47b0`, `0x47b9`, `0x47c0`, `0x47c1`, `0x47c4`, `0x47c5`, `0x47c7`, `0x47c8`, `0x47c9`, `0x47cb`, `0x47cd`, `0x47d0`, `0x47d2`, `0x47d7`, `0x4842`, `0x4862`, `0x487c`, `0x48a0`, `0x8164`, `0x8240`

- `3171` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3176` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3182` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3190` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3203` `write` `0x4014`: `DAT_EXTMEM_4014 = 0;`
- `3204` `write` `0x4015`: `DAT_EXTMEM_4015 = 0;`
- `3205` `write` `0x4016`: `DAT_EXTMEM_4016 = 0;`
- `3206` `write` `0x4017`: `DAT_EXTMEM_4017 = 0;`
- `3114` `read` `0x4023`: `DAT_EXTMEM_80b0 = DAT_EXTMEM_4023;`
- `3115` `write` `0x4023`: `DAT_EXTMEM_4023 = 0;`
- `3172` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `3173` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `3174` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `3180` `read` `0x4098`: `DAT_EXTMEM_4098;`
- `3188` `read` `0x4098`: `DAT_EXTMEM_4098;`
- `3125` `test` `0x4700`: `if ((-1 < (char)DAT_EXTMEM_48a0) && ((DAT_EXTMEM_4700 & 1) != 1)) {`
- `3151` `test` `0x4700`: `if ((-1 < (char)DAT_EXTMEM_48a0) && ((DAT_EXTMEM_4700 & 1) != 1)) {`
- `3236` `read` `0x4774`: `DAT_INTMEM_29 = DAT_EXTMEM_4774;`
- `3251` `read` `0x4774`: `DAT_INTMEM_28 = DAT_EXTMEM_4774;`
- `3252` `test` `0x4774`: `if ((DAT_EXTMEM_4774 & 1) != 0) {`
- `3229` `test` `0x4782`: `if (((DAT_EXTMEM_4782 & 1) != 0) && ((char)DAT_EXTMEM_4782 < '\0')) {`
- `3235` `read-modify-write` `0x4782`: `DAT_EXTMEM_4782 = DAT_EXTMEM_4782 & 0x7f;`
- `3232` `test` `0x478f`: `if ((DAT_EXTMEM_478f & 1) != 0) {`
- `3230` `write` `0x47a6`: `DAT_EXTMEM_47a6 = 0;`
- ... 58 more refs

### `FUN_CODE_2a9c`

`0x4000`, `0x4011`, `0x4012`, `0x4014`, `0x4015`, `0x4016`, `0x4017`, `0x4091`, `0x4092`, `0x4093`, `0x4098`, `0x4774`, `0x4782`, `0x478f`, `0x47a6`, `0x47b0`, `0x47b9`, `0x47c0`, `0x47c1`, `0x47c4`, `0x47c5`, `0x47c7`, `0x47c8`, `0x47c9`, `0x47cb`, `0x47cd`, `0x47d0`, `0x47d2`, `0x47d7`, `0x4842`, `0x48a0`, `0x810e`, `0x810f`, `0x8110`, `0x8111`, `0x8164`, `0x816a`, `0x817b`, `0x818b`, `0x818c`, `0x818d`, `0x818e`, `0x818f`, `0x8191`, `0x8192`, `0x8193`, `0x8194`, `0x819f`, `0x81a0`, `0x8240`, `0x8244`, `0x8245`, `0x8246`, `0x8247`, `0x8248`, `0x8249`, `0x824a`, `0x824b`, `0x8250`, `0x8251`

- `3389` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3394` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3400` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3408` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3579` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3584` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3590` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3371` `write` `0x4011`: `DAT_EXTMEM_4011 = 1;`
- `3640` `write` `0x4011`: `DAT_EXTMEM_4011 = DAT_EXTMEM_818d;`
- `3372` `write` `0x4012`: `DAT_EXTMEM_4012 = 0;`
- `3641` `write` `0x4012`: `DAT_EXTMEM_4012 = DAT_EXTMEM_818e;`
- `3421` `write` `0x4014`: `DAT_EXTMEM_4014 = 0;`
- `3422` `write` `0x4015`: `DAT_EXTMEM_4015 = 0;`
- `3423` `write` `0x4016`: `DAT_EXTMEM_4016 = 0;`
- `3424` `write` `0x4017`: `DAT_EXTMEM_4017 = 0;`
- `3390` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `3580` `write` `0x4091`: `DAT_EXTMEM_4091 = 1;`
- `3391` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `3581` `write` `0x4092`: `DAT_EXTMEM_4092 = 0x80;`
- `3392` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `3582` `write` `0x4093`: `DAT_EXTMEM_4093 = 6;`
- `3398` `read` `0x4098`: `DAT_EXTMEM_4098;`
- `3406` `read` `0x4098`: `DAT_EXTMEM_4098;`
- `3591` `read` `0x4098`: `*(undefined1 *)CONCAT11(DAT_INTMEM_4d,DAT_INTMEM_4e) = DAT_EXTMEM_4098;`
- ... 125 more refs

### `FUN_CODE_3021`

`0x8244`, `0x8245`, `0x8277`, `0x8278`, `0x8279`, `0x827a`, `0x827b`, `0x8281`, `0x8282`, `0x8283`, `0x8284`, `0x8285`, `0x8289`, `0x828d`, `0x8291`, `0x82a5`, `0x82a6`

- `3835` `write` `0x8244`: `DAT_EXTMEM_8244 = 0;`
- `3838` `write` `0x8244`: `CONCAT11(-0x7e - (((0x7d < DAT_EXTMEM_8244) << 7) >> 7),DAT_EXTMEM_8244 + 0x82) =`
- `3840` `read` `0x8244`: `CONCAT11((byte)DAT_EXTMEM_827a | CARRY1(DAT_EXTMEM_827b,DAT_EXTMEM_8244),`
- `3841` `read` `0x8244`: `DAT_EXTMEM_827b + DAT_EXTMEM_8244);`
- `3842` `read-modify-write` `0x8244`: `DAT_EXTMEM_8244 = DAT_EXTMEM_8244 + 1;`
- `3843` `wait/test` `0x8244`: `} while (DAT_EXTMEM_8244 != 0x10);`
- `3844` `write` `0x8244`: `DAT_EXTMEM_8244 = 0x10;`
- `3856` `write` `0x8244`: `DAT_EXTMEM_8244 = 0;`
- `3859` `write` `0x8244`: `CONCAT11(-0x7e - (((0x7d < DAT_EXTMEM_8244) << 7) >> 7),DAT_EXTMEM_8244 + 0x82) =`
- `3861` `read` `0x8244`: `CONCAT11(CARRY1((byte)DAT_EXTMEM_827a,DAT_EXTMEM_8244) + 'Y',`
- `3862` `read` `0x8244`: `DAT_EXTMEM_827a + DAT_EXTMEM_8244);`
- `3863` `read-modify-write` `0x8244`: `DAT_EXTMEM_8244 = DAT_EXTMEM_8244 + 1;`
- `3864` `wait/test` `0x8244`: `} while (DAT_EXTMEM_8244 != 0x10);`
- `3917` `read` `0x8244`: `for (DAT_EXTMEM_8244 = DAT_EXTMEM_82a5; (DAT_EXTMEM_8244 < DAT_EXTMEM_8277) << 7 < '\0';`
- `3918` `read-modify-write` `0x8244`: `DAT_EXTMEM_8244 = DAT_EXTMEM_8244 + 1) {`
- `3919` `read` `0x8244`: `bVar2 = DAT_EXTMEM_8244 - DAT_EXTMEM_82a5 & 7;`
- `3922` `read` `0x8244`: `CONCAT11(-0x7e - (((0x86 < DAT_EXTMEM_8244) << 7) >> 7),DAT_EXTMEM_8244 + 0x79);`
- `3879` `test` `0x8245`: `if (((DAT_EXTMEM_8245 == 0) || (DAT_EXTMEM_8245 == 0x80)) ||`
- `3880` `read` `0x8245`: `((DAT_EXTMEM_8245 == 4 || (DAT_EXTMEM_8245 == 0x84)))) {`
- `3881` `read` `0x8245`: `DAT_EXTMEM_8283 = DAT_EXTMEM_8245;`
- `3886` `test` `0x8245`: `if (DAT_EXTMEM_8245 == 0) {`
- `3887` `read` `0x8245`: `DAT_EXTMEM_8284 = DAT_EXTMEM_8245;`
- `3889` `write` `0x8245`: `else if (DAT_EXTMEM_8245 == 8) {`
- `3890` `read` `0x8245`: `DAT_EXTMEM_8284 = DAT_EXTMEM_8245;`
- ... 70 more refs

### `FUN_CODE_3643`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4095`, `0x4096`, `0x4097`, `0x4098`

- `3994` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4020` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4062` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `3995` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `3996` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_INTMEM_2c;`
- `3997` `write` `0x4093`: `DAT_EXTMEM_4093 = DAT_INTMEM_2d;`
- `3998` `write` `0x4095`: `DAT_EXTMEM_4095 = DAT_EXTMEM_803c;`
- `4021` `write` `0x4095`: `DAT_EXTMEM_4095 = DAT_EXTMEM_803c;`
- `3999` `write` `0x4096`: `DAT_EXTMEM_4096 = 7;`
- `4022` `write` `0x4096`: `DAT_EXTMEM_4096 = 7;`
- `4000` `write` `0x4097`: `DAT_EXTMEM_4097 = 0x38;`
- `4023` `write` `0x4097`: `DAT_EXTMEM_4097 = 0x38;`
- `4056` `write` `0x4098`: `DAT_EXTMEM_4098 =`

### `FUN_CODE_385c`

`0x4011`, `0x4012`, `0x4013`, `0x4014`, `0x4015`, `0x4016`, `0x4017`, `0x8164`, `0x818b`, `0x818c`, `0x818d`, `0x818e`, `0x818f`, `0x8190`, `0x8191`, `0x8192`, `0x8194`, `0x8195`, `0x8250`, `0x8251`

- `4155` `write` `0x4011`: `DAT_EXTMEM_4011 = '\x02';`
- `4159` `write` `0x4011`: `DAT_EXTMEM_4011 = DAT_EXTMEM_818d;`
- `4172` `write` `0x4011`: `DAT_EXTMEM_4011 = DAT_EXTMEM_80c6;`
- `4148` `write` `0x4012`: `DAT_EXTMEM_4012 = DAT_EXTMEM_818e + 0x50;`
- `4156` `write` `0x4012`: `DAT_EXTMEM_4012 = 0;`
- `4160` `write` `0x4012`: `DAT_EXTMEM_4012 = DAT_EXTMEM_818e;`
- `4170` `write` `0x4012`: `DAT_EXTMEM_4012 = DAT_EXTMEM_818e + 0x40;`
- `4173` `read` `0x4012`: `DAT_EXTMEM_818e = DAT_EXTMEM_4012;`
- `4190` `write` `0x4013`: `DAT_EXTMEM_4013 = DAT_EXTMEM_818f;`
- `4189` `write` `0x4014`: `DAT_EXTMEM_4014 = 0;`
- `4188` `write` `0x4015`: `DAT_EXTMEM_4015 = 0;`
- `4187` `write` `0x4016`: `DAT_EXTMEM_4016 = DAT_INTMEM_4d;`
- `4186` `write` `0x4017`: `DAT_EXTMEM_4017 = DAT_INTMEM_4e;`
- `4111` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 2;`
- `4107` `test` `0x818b`: `if ((DAT_EXTMEM_818b != '\x01') ||`
- `4108` `read` `0x818c`: `((((DAT_EXTMEM_818c != '\x01' && (DAT_EXTMEM_818c != '\x02')) && (DAT_EXTMEM_818c != -0x1e)) &&`
- `4109` `read` `0x818c`: `((DAT_EXTMEM_818c != -0x10 && (DAT_EXTMEM_818c != -0xf)))))) {`
- `4122` `test` `0x818c`: `if (DAT_EXTMEM_818c == -0x10) {`
- `4143` `test` `0x818c`: `if (DAT_EXTMEM_818c == -0xf) {`
- `4151` `test` `0x818c`: `if (DAT_EXTMEM_818c != -0x1e) {`
- `4177` `test` `0x818c`: `if (((DAT_EXTMEM_818c == -0x1e) || (DAT_EXTMEM_818c == -0xf)) &&`
- `4129` `read` `0x818d`: `FUN_CODE_3643(1,DAT_EXTMEM_818e,DAT_EXTMEM_818f,DAT_EXTMEM_818d);`
- `4144` `test` `0x818d`: `if ((DAT_EXTMEM_818d != '\0') ||`
- `4159` `read` `0x818d`: `DAT_EXTMEM_4011 = DAT_EXTMEM_818d;`
- ... 41 more refs

### `FUN_CODE_3a35`

`0x47c1`, `0x47c2`, `0x47c4`, `0x47c5`, `0x47c9`, `0x47cb`, `0x47d0`, `0x47d2`, `0x8164`, `0x8179`

- `4206` `read` `0x47c1`: `*BANK1_R1 = DAT_EXTMEM_47c1;`
- `4209` `read` `0x47c2`: `*BANK1_R1 = DAT_EXTMEM_47c2;`
- `4267` `read` `0x47c2`: `*BANK1_R1 = DAT_EXTMEM_47c2;`
- `4287` `read` `0x47c2`: `*BANK1_R1 = DAT_EXTMEM_47c2;`
- `4314` `write` `0x47c4`: `DAT_EXTMEM_47c4 = 0;`
- `4315` `write` `0x47c5`: `DAT_EXTMEM_47c5 = 0;`
- `4305` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x50;`
- `4311` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x51;`
- `4306` `write` `0x47cb`: `DAT_EXTMEM_47cb = 0;`
- `4312` `write` `0x47cb`: `DAT_EXTMEM_47cb = 4;`
- `4318` `write` `0x47d0`: `DAT_EXTMEM_47d0 = 0x10;`
- `4217` `write` `0x47d2`: `DAT_EXTMEM_47d2 = 1;`
- `4221` `write` `0x47d2`: `DAT_EXTMEM_47d2 = 1;`
- `4237` `write` `0x47d2`: `DAT_EXTMEM_47d2 = 1;`
- `4213` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 2;`
- `4304` `test` `0x8164`: `if ((DAT_EXTMEM_8164 >> 1 & 1) == 0) {`
- `4309` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 & 0xfd;`
- `4319` `read-modify-write` `0x8179`: `DAT_EXTMEM_8179 = DAT_EXTMEM_8179 & 0xef;`

### `FUN_CODE_3bfd`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`, `0x8255`, `0x8256`, `0x8257`, `0x8258`, `0x8259`, `0x825a`, `0x825b`, `0x825c`, `0x825d`, `0x825e`, `0x825f`, `0x8260`, `0x8261`, `0x8262`, `0x8263`, `0x8264`, `0x8274`, `0x8275`, `0x8276`

- `4361` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4381` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4394` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4362` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_8255;`
- `4363` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_EXTMEM_8256;`
- `4364` `write` `0x4093`: `DAT_EXTMEM_4093 = DAT_EXTMEM_8257;`
- `4365` `read` `0x4098`: `FUN_CODE_1e1c(0x8260,DAT_EXTMEM_4098);`
- `4382` `read` `0x4098`: `DAT_EXTMEM_42b4 = DAT_EXTMEM_4098;`
- `4396` `read` `0x4098`: `DAT_EXTMEM_4098 ^`
- `4362` `read` `0x8255`: `DAT_EXTMEM_4091 = DAT_EXTMEM_8255;`
- `4363` `read` `0x8256`: `DAT_EXTMEM_4092 = DAT_EXTMEM_8256;`
- `4364` `read` `0x8257`: `DAT_EXTMEM_4093 = DAT_EXTMEM_8257;`
- `4357` `read` `0x8258`: `FUN_CODE_1cd5(0,0,0,0x10,DAT_EXTMEM_8258,DAT_EXTMEM_8259,`
- `4357` `read` `0x8259`: `FUN_CODE_1cd5(0,0,0,0x10,DAT_EXTMEM_8258,DAT_EXTMEM_8259,`
- `4358` `read` `0x825a`: `DAT_EXTMEM_825a - (((0xf0 < DAT_EXTMEM_825b) << 7) >> 7),DAT_EXTMEM_825b + 0xf);`
- `4358` `read` `0x825b`: `DAT_EXTMEM_825a - (((0xf0 < DAT_EXTMEM_825b) << 7) >> 7),DAT_EXTMEM_825b + 0xf);`
- `4375` `read` `0x825c`: `DAT_EXTMEM_825c + (-1 - ((CARRY1(DAT_EXTMEM_825d,bVar2) << 7) >> 7)),`
- `4375` `read` `0x825d`: `DAT_EXTMEM_825c + (-1 - ((CARRY1(DAT_EXTMEM_825d,bVar2) << 7) >> 7)),`
- `4376` `read` `0x825d`: `DAT_EXTMEM_825d + bVar2,DAT_EXTMEM_825e + bVar1,DAT_EXTMEM_825f + -1);`
- `4372` `read` `0x825e`: `bVar2 = 0xff - ((CARRY1(DAT_EXTMEM_825e,bVar1) << 7) >> 7);`
- `4376` `read` `0x825e`: `DAT_EXTMEM_825d + bVar2,DAT_EXTMEM_825e + bVar1,DAT_EXTMEM_825f + -1);`
- `4371` `read` `0x825f`: `bVar1 = 0xff - (((DAT_EXTMEM_825f != '\0') << 7) >> 7);`
- `4376` `read` `0x825f`: `DAT_EXTMEM_825d + bVar2,DAT_EXTMEM_825e + bVar1,DAT_EXTMEM_825f + -1);`
- `4374` `read` `0x8260`: `FUN_CODE_1d8b(DAT_EXTMEM_8260,DAT_EXTMEM_8261,DAT_EXTMEM_8262,DAT_EXTMEM_8263,`
- ... 29 more refs

### `FUN_CODE_3da3`

`0x47c0`, `0x47c2`, `0x47c3`, `0x47c4`, `0x47c5`, `0x47c9`, `0x47cb`, `0x47d0`, `0x8164`, `0x8179`, `0x817b`, `0x818a`

- `4422` `write` `0x47c0`: `DAT_EXTMEM_47c0 = 8;`
- `4445` `write` `0x47c2`: `DAT_EXTMEM_47c2 = 1;`
- `4498` `write` `0x47c2`: `DAT_EXTMEM_47c2 = 3;`
- `4435` `write` `0x47c3`: `DAT_EXTMEM_47c3 = 0;`
- `4441` `write` `0x47c3`: `DAT_EXTMEM_47c3 = 1;`
- `4446` `write` `0x47c4`: `DAT_EXTMEM_47c4 = DAT_INTMEM_4e;`
- `4496` `write` `0x47c4`: `DAT_EXTMEM_47c4 = 0;`
- `4447` `write` `0x47c5`: `DAT_EXTMEM_47c5 = DAT_INTMEM_4d;`
- `4497` `write` `0x47c5`: `DAT_EXTMEM_47c5 = 0;`
- `4433` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x50;`
- `4438` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x51;`
- `4479` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x50;`
- `4491` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x51;`
- `4494` `read-modify-write` `0x47c9`: `DAT_EXTMEM_47c9 = DAT_EXTMEM_47c9 & 0xef;`
- `4434` `write` `0x47cb`: `DAT_EXTMEM_47cb = '\0';`
- `4439` `write` `0x47cb`: `DAT_EXTMEM_47cb = '\x04';`
- `4478` `write` `0x47cb`: `DAT_EXTMEM_47cb = DAT_INTMEM_59;`
- `4483` `write` `0x47cb`: `DAT_EXTMEM_47cb = DAT_INTMEM_59 * '\x10' + '\x04';`
- `4486` `write` `0x47cb`: `DAT_EXTMEM_47cb = DAT_INTMEM_59 * '\x10' + '\b';`
- `4489` `write` `0x47cb`: `DAT_EXTMEM_47cb = DAT_INTMEM_59 << 4;`
- `4500` `write` `0x47d0`: `DAT_EXTMEM_47d0 = 0x10;`
- `4424` `read` `0x8164`: `bVar1 = (DAT_EXTMEM_8164 >> 1 & 1) == 0;`
- `4426` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 & 0xfd;`
- `4428` `read` `0x8164`: `bVar2 = (DAT_EXTMEM_8164 & 1) == 0;`
- ... 10 more refs

### `FUN_CODE_3f2c`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4095`, `0x4096`, `0x4097`, `0x4098`, `0x4862`, `0x810e`, `0x810f`, `0x8110`, `0x8111`, `0x824d`, `0x824e`, `0x824f`, `0x8250`, `0x8251`, `0x8252`, `0x8253`, `0x8254`, `0x8255`, `0x8256`

- `4553` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4566` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4584` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4595` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4555` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_803c;`
- `4560` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_824d;`
- `4557` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_EXTMEM_4096;`
- `4561` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_EXTMEM_824e;`
- `4564` `write` `0x4093`: `DAT_EXTMEM_4093 = *puVar3;`
- `4568` `write` `0x4095`: `DAT_EXTMEM_4095 = DAT_EXTMEM_803c;`
- `4572` `write` `0x4095`: `DAT_EXTMEM_4095 = DAT_EXTMEM_824d;`
- `4547` `write` `0x4096`: `DAT_EXTMEM_4096 =`
- `4550` `read` `0x4096`: `DAT_EXTMEM_8252 = DAT_EXTMEM_4096;`
- `4557` `read` `0x4096`: `DAT_EXTMEM_4092 = DAT_EXTMEM_4096;`
- `4573` `write` `0x4096`: `DAT_EXTMEM_4096 = DAT_EXTMEM_824e;`
- `4576` `write` `0x4097`: `DAT_EXTMEM_4097 = *puVar3;`
- `4585` `read` `0x4098`: `DAT_EXTMEM_42b4 = DAT_EXTMEM_4098;`
- `4593` `write` `0x4098`: `DAT_EXTMEM_4098 = DAT_EXTMEM_42b5;`
- `4523` `read-modify-write` `0x4862`: `DAT_EXTMEM_4862 = DAT_EXTMEM_4862 & 0xfb;`
- `4604` `read-modify-write` `0x4862`: `DAT_EXTMEM_4862 = DAT_EXTMEM_4862 | 4;`
- `4532` `read` `0x810e`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `4532` `read` `0x810f`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `4532` `read` `0x8110`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `4532` `read` `0x8111`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- ... 36 more refs

### `FUN_CODE_40b2`

`0x4000`, `0x4023`, `0x4091`, `0x4092`, `0x4093`, `0x4098`, `0x4819`, `0x8229`, `0x822a`, `0x822b`, `0x822c`, `0x822d`, `0x822e`, `0x822f`, `0x8230`, `0x8231`, `0x8232`, `0x8233`, `0x8234`, `0x8235`, `0x8236`, `0x8237`, `0x8238`, `0x8239`, `0x823a`, `0x8254`, `0x8255`

- `4632` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4637` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4640` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4648` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4656` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4664` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `4693` `write` `0x4023`: `DAT_EXTMEM_4023 = DAT_EXTMEM_80b0;`
- `4633` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `4642` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `4650` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `4658` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `4666` `write` `0x4091`: `DAT_EXTMEM_4091 = 0;`
- `4634` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `4643` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `4651` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `4659` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `4667` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `4635` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `4644` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `4652` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `4660` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `4668` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `4638` `read` `0x4098`: `DAT_INTMEM_2b = DAT_EXTMEM_4098;`
- `4641` `test` `0x4098`: `if ((DAT_EXTMEM_4098 ^ 0x4c) != 0) {`
- ... 40 more refs

### `FUN_CODE_4230`

`0x4704`, `0x472a`, `0x472c`, `0x472e`, `0x47f0`, `0x47f2`, `0x482b`, `0x482c`, `0x482d`

- `4722` `read-modify-write` `0x4704`: `DAT_EXTMEM_4704 = DAT_EXTMEM_4704 & 0xf7;`
- `4727` `test` `0x472a`: `if ((DAT_EXTMEM_472a & 0xc0) != 0) {`
- `4772` `read-modify-write` `0x472a`: `DAT_EXTMEM_472a = DAT_EXTMEM_472a & 0x3f;`
- `4743` `test` `0x472c`: `if (-1 < (char)DAT_EXTMEM_472c) {`
- `4748` `test` `0x472c`: `if ((char)DAT_EXTMEM_472c < '\0') goto LAB_CODE_4348;`
- `4759` `test` `0x472c`: `if ((-1 < (char)DAT_EXTMEM_472e) || (-1 < (char)DAT_EXTMEM_472c)) {`
- `4765` `read` `0x472c`: `BANK1_R1['\x02'] = DAT_EXTMEM_472c & 0x3f;`
- `4728` `test` `0x472e`: `if (-1 < (char)DAT_EXTMEM_472e) {`
- `4733` `test` `0x472e`: `if ((char)DAT_EXTMEM_472e < '\0') goto LAB_CODE_42d0;`
- `4759` `test` `0x472e`: `if ((-1 < (char)DAT_EXTMEM_472e) || (-1 < (char)DAT_EXTMEM_472c)) {`
- `4764` `read` `0x472e`: `BANK1_R1['\x01'] = DAT_EXTMEM_472e & 0x3f;`
- `4770` `write` `0x47f0`: `DAT_EXTMEM_47f0 = BANK1_R1['\x02'];`
- `4767` `write` `0x47f2`: `DAT_EXTMEM_47f2 = BANK1_R1['\x01'];`
- `4729` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4734` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4744` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4749` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4730` `read` `0x482c`: `BANK1_R1['\x03'] = DAT_EXTMEM_482c;`
- `4735` `read` `0x482c`: `BANK1_R1['\x05'] = DAT_EXTMEM_482c;`
- `4745` `read` `0x482c`: `BANK1_R1['\x03'] = DAT_EXTMEM_482c;`
- `4750` `read` `0x482c`: `BANK1_R1['\x05'] = DAT_EXTMEM_482c;`
- `4731` `read` `0x482d`: `FUN_CODE_1c10(DAT_EXTMEM_482d,1,BANK1_R1 + '\x03',0,0);`
- `4736` `read` `0x482d`: `FUN_CODE_1c10(DAT_EXTMEM_482d,1,BANK1_R1 + '\x05',0,0);`
- `4746` `read` `0x482d`: `FUN_CODE_1c10(DAT_EXTMEM_482d,1,BANK1_R1 + '\x03',0,0);`
- ... 1 more refs

### `FUN_CODE_423b`

`0x472a`, `0x472c`, `0x472e`, `0x47f0`, `0x47f2`, `0x482b`, `0x482c`, `0x482d`

- `4788` `test` `0x472a`: `if ((DAT_EXTMEM_472a & 0xc0) != 0) {`
- `4833` `read-modify-write` `0x472a`: `DAT_EXTMEM_472a = DAT_EXTMEM_472a & 0x3f;`
- `4804` `test` `0x472c`: `if (-1 < (char)DAT_EXTMEM_472c) {`
- `4809` `test` `0x472c`: `if ((char)DAT_EXTMEM_472c < '\0') goto LAB_CODE_4348;`
- `4820` `test` `0x472c`: `if ((-1 < (char)DAT_EXTMEM_472e) || (-1 < (char)DAT_EXTMEM_472c)) {`
- `4826` `read` `0x472c`: `BANK1_R1['\x02'] = DAT_EXTMEM_472c & 0x3f;`
- `4789` `test` `0x472e`: `if (-1 < (char)DAT_EXTMEM_472e) {`
- `4794` `test` `0x472e`: `if ((char)DAT_EXTMEM_472e < '\0') goto LAB_CODE_42d0;`
- `4820` `test` `0x472e`: `if ((-1 < (char)DAT_EXTMEM_472e) || (-1 < (char)DAT_EXTMEM_472c)) {`
- `4825` `read` `0x472e`: `BANK1_R1['\x01'] = DAT_EXTMEM_472e & 0x3f;`
- `4831` `write` `0x47f0`: `DAT_EXTMEM_47f0 = BANK1_R1['\x02'];`
- `4828` `write` `0x47f2`: `DAT_EXTMEM_47f2 = BANK1_R1['\x01'];`
- `4790` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4795` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4805` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4810` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `4791` `read` `0x482c`: `BANK1_R1['\x03'] = DAT_EXTMEM_482c;`
- `4796` `read` `0x482c`: `BANK1_R1['\x05'] = DAT_EXTMEM_482c;`
- `4806` `read` `0x482c`: `BANK1_R1['\x03'] = DAT_EXTMEM_482c;`
- `4811` `read` `0x482c`: `BANK1_R1['\x05'] = DAT_EXTMEM_482c;`
- `4792` `read` `0x482d`: `FUN_CODE_1c10(DAT_EXTMEM_482d,1,BANK1_R1 + '\x03',0,0);`
- `4797` `read` `0x482d`: `FUN_CODE_1c10(DAT_EXTMEM_482d,1,BANK1_R1 + '\x05',0,0);`
- `4807` `read` `0x482d`: `FUN_CODE_1c10(DAT_EXTMEM_482d,1,BANK1_R1 + '\x03',0,0);`
- `4812` `read` `0x482d`: `FUN_CODE_1c10(DAT_EXTMEM_482d,1,BANK1_R1 + '\x05',0,0);`

### `FUN_CODE_4502`

`0x470e`, `0x4764`, `0x4770`, `0x4772`, `0x4781`, `0x4782`, `0x478f`, `0x47a0`, `0x47a1`, `0x47a2`, `0x47a3`, `0x47a6`, `0x47aa`, `0x47cd`, `0x47d0`, `0x4842`, `0x8179`, `0x81b3`, `0x81b4`, `0x8240`, `0x8243`

- `4854` `wait/test` `0x470e`: `} while ((DAT_EXTMEM_470e >> 3 & 1) == 0);`
- `4856` `read` `0x4764`: `DAT_INTMEM_2c = DAT_EXTMEM_4764;`
- `4858` `test` `0x4764`: `if ((DAT_EXTMEM_4764 >> 1 & 1) == 0) {`
- `4859` `test` `0x4764`: `if ((DAT_EXTMEM_4764 & 1) == 0) goto LAB_CODE_457b;`
- `4871` `test` `0x4764`: `if (((DAT_EXTMEM_4782 & 6) == 0) && ((DAT_EXTMEM_4764 >> 3 & 1) != 1)) {`
- `4875` `test` `0x4764`: `if ((DAT_EXTMEM_4764 >> 3 & 1) != 0) {`
- `4881` `test` `0x4764`: `if ((DAT_EXTMEM_4764 >> 2 & 1) != 0) {`
- `4910` `read-modify-write` `0x4770`: `DAT_EXTMEM_4770 = DAT_EXTMEM_4770 | 8;`
- `4920` `read-modify-write` `0x4770`: `DAT_EXTMEM_4770 = DAT_EXTMEM_4770 & 0xfd;`
- `4857` `read` `0x4772`: `DAT_INTMEM_2e = DAT_EXTMEM_4772;`
- `4886` `test` `0x4772`: `if ((DAT_EXTMEM_4772 >> 3 & 1) != 0) {`
- `4888` `test` `0x4772`: `if (((DAT_EXTMEM_4772 >> 4 & 1) == 1) || ((DAT_EXTMEM_47aa & 0xf) != 0)) {`
- `4894` `write` `0x4781`: `DAT_EXTMEM_4781 = 0;`
- `4860` `test` `0x4782`: `if ((DAT_EXTMEM_4782 >> 1 & 1) != 0) {`
- `4866` `write` `0x4782`: `else if ((DAT_EXTMEM_4782 >> 2 & 1) != 0) {`
- `4871` `test` `0x4782`: `if (((DAT_EXTMEM_4782 & 6) == 0) && ((DAT_EXTMEM_4764 >> 3 & 1) != 1)) {`
- `4883` `read-modify-write` `0x4782`: `DAT_EXTMEM_4782 = DAT_EXTMEM_4782 & 0x7f;`
- `4907` `test` `0x4782`: `if ((DAT_EXTMEM_4782 & 1) != 0) {`
- `4917` `read-modify-write` `0x4782`: `DAT_EXTMEM_4782 = DAT_EXTMEM_4782 & 0x7f;`
- `4909` `test` `0x478f`: `if ((DAT_EXTMEM_478f & 1) != 0) {`
- `4890` `write` `0x47a0`: `DAT_EXTMEM_47a0 = 0;`
- `4891` `write` `0x47a1`: `DAT_EXTMEM_47a1 = 0;`
- `4892` `write` `0x47a2`: `DAT_EXTMEM_47a2 = 0;`
- `4893` `write` `0x47a3`: `DAT_EXTMEM_47a3 = 0;`
- ... 22 more refs

### `FUN_CODE_465e`

`0x4700`, `0x470c`, `0x470f`, `0x4710`, `0x4712`, `0x4735`, `0x4796`, `0x4797`, `0x8281`, `0x8282`, `0x8283`, `0x8284`

- `4951` `wait/test` `0x4700`: `} while ((DAT_EXTMEM_4700 >> 1 & 1) == 1);`
- `4941` `read` `0x470c`: `DAT_INTMEM_2e = DAT_EXTMEM_470c >> 4;`
- `4942` `read` `0x470c`: `DAT_INTMEM_2f = DAT_EXTMEM_470c & 0xf;`
- `4944` `read` `0x470c`: `FUN_CODE_536e(DAT_EXTMEM_470c);`
- `4945` `read` `0x470c`: `DAT_EXTMEM_470f = DAT_EXTMEM_470f & 0xe | DAT_EXTMEM_470c & 0xf0;`
- `4991` `read` `0x470c`: `DAT_EXTMEM_470f = DAT_EXTMEM_470f & 0xe | DAT_EXTMEM_470c & 0xf0;`
- `5000` `read` `0x470c`: `DAT_EXTMEM_8282 = DAT_EXTMEM_470c;`
- `4940` `test` `0x470f`: `if ((DAT_EXTMEM_470f & 0xc) == 0) {`
- `4943` `read-modify-write` `0x470f`: `DAT_EXTMEM_470f = DAT_EXTMEM_470f & 0xf3 | 4;`
- `4945` `read-modify-write` `0x470f`: `DAT_EXTMEM_470f = DAT_EXTMEM_470f & 0xe | DAT_EXTMEM_470c & 0xf0;`
- `4991` `read-modify-write` `0x470f`: `DAT_EXTMEM_470f = DAT_EXTMEM_470f & 0xe | DAT_EXTMEM_470c & 0xf0;`
- `5001` `read` `0x470f`: `DAT_EXTMEM_8283 = DAT_EXTMEM_470f;`
- `4946` `read-modify-write` `0x4710`: `DAT_EXTMEM_4710 = DAT_EXTMEM_4710 & 0xe | DAT_INTMEM_2f << 4;`
- `4992` `read-modify-write` `0x4710`: `DAT_EXTMEM_4710 = DAT_EXTMEM_4710 & 0xe | DAT_EXTMEM_4797 << 4;`
- `5002` `read` `0x4710`: `DAT_EXTMEM_8284 = DAT_EXTMEM_4710;`
- `4952` `read` `0x4712`: `cVar3 = DAT_EXTMEM_4712;`
- `4953` `test` `0x4712`: `if (DAT_EXTMEM_4712 == '\0') {`
- `4958` `wait/test` `0x4712`: `while (cVar3 = DAT_EXTMEM_4712, DAT_EXTMEM_4712 == '\0') {`
- `4965` `read` `0x4712`: `DAT_EXTMEM_8282 = DAT_EXTMEM_4712;`
- `4966` `read` `0x4712`: `DAT_EXTMEM_8283 = DAT_EXTMEM_4712;`
- `4967` `read` `0x4712`: `DAT_EXTMEM_8284 = DAT_EXTMEM_4712;`
- `4982` `test` `0x4735`: `if ((DAT_EXTMEM_4735 & 0x43) != 0) {`
- `4985` `test` `0x4796`: `if (DAT_EXTMEM_4796 == '\0') {`
- `4988` `test` `0x4797`: `if (DAT_EXTMEM_4797 == '\0') {`
- ... 22 more refs

### `FUN_CODE_47b0`

`0x4726`, `0x4748`, `0x474d`, `0x474e`, `0x479e`, `0x48d5`

- `5022` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc | 1;`
- `5029` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc;`
- `5032` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc | 3;`
- `5041` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc;`
- `5044` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc | 3;`
- `5050` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc | 1;`
- `5055` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc | 2;`
- `5060` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc | 1;`
- `5065` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0xfc | 2;`
- `5071` `read-modify-write` `0x4748`: `DAT_EXTMEM_4748 = DAT_EXTMEM_4748 & 0x7f;`
- `5074` `read-modify-write` `0x4748`: `DAT_EXTMEM_4748 = DAT_EXTMEM_4748 | 0x80;`
- `5075` `read` `0x4748`: `bVar1 = DAT_EXTMEM_4748;`
- `5014` `read` `0x474d`: `bVar1 = DAT_EXTMEM_474d;`
- `5015` `test` `0x474d`: `if ((char)DAT_EXTMEM_474d < '\0') {`
- `5020` `write` `0x474d`: `DAT_EXTMEM_474d = 0x45;`
- `5026` `write` `0x474d`: `DAT_EXTMEM_474d = 0x45;`
- `5046` `write` `0x474d`: `DAT_EXTMEM_474d = 0x45;`
- `5051` `write` `0x474d`: `DAT_EXTMEM_474d = 0x45;`
- `5056` `write` `0x474d`: `DAT_EXTMEM_474d = 0x45;`
- `5061` `write` `0x474d`: `DAT_EXTMEM_474d = 0x15;`
- `5066` `write` `0x474d`: `DAT_EXTMEM_474d = 5;`
- `5021` `write` `0x474e`: `DAT_EXTMEM_474e = 0x90;`
- `5027` `write` `0x474e`: `DAT_EXTMEM_474e = 0x90;`
- `5047` `write` `0x474e`: `DAT_EXTMEM_474e = 0xc0;`
- ... 10 more refs

### `FUN_CODE_48e7`

`0x400d`, `0x401a`, `0x402a`, `0x40ea`, `0x40eb`, `0x4762`, `0x4773`, `0x47cc`, `0x47ce`, `0x47d2`, `0x4801`, `0x4802`, `0x4804`, `0x4806`, `0x4807`, `0x4815`, `0x4840`, `0x4860`, `0x4861`, `0x4862`, `0x4863`, `0x4864`, `0x48a0`, `0x48af`, `0x8221`

- `5133` `write` `0x400d`: `DAT_EXTMEM_400d = 0;`
- `5136` `write` `0x401a`: `DAT_EXTMEM_401a = 1;`
- `5134` `write` `0x402a`: `DAT_EXTMEM_402a = 0;`
- `5137` `write` `0x40ea`: `DAT_EXTMEM_40ea = 1;`
- `5138` `write` `0x40eb`: `DAT_EXTMEM_40eb = 0;`
- `5092` `read-modify-write` `0x4762`: `DAT_EXTMEM_4762 = DAT_EXTMEM_4762 & 0xef;`
- `5135` `write` `0x4762`: `DAT_EXTMEM_4762 = 0;`
- `5129` `write` `0x4773`: `DAT_EXTMEM_4773 = 0x6d;`
- `5130` `write` `0x47cc`: `DAT_EXTMEM_47cc = 0xb4;`
- `5131` `write` `0x47ce`: `DAT_EXTMEM_47ce = 0x9c;`
- `5132` `write` `0x47d2`: `DAT_EXTMEM_47d2 = 1;`
- `5089` `write` `0x4801`: `DAT_EXTMEM_4801 = 5;`
- `5091` `read-modify-write` `0x4802`: `DAT_EXTMEM_4802 = DAT_EXTMEM_4802 | 0x80;`
- `5109` `read-modify-write` `0x4802`: `DAT_EXTMEM_4802 = DAT_EXTMEM_4802 & 0x7f;`
- `5110` `write` `0x4804`: `DAT_EXTMEM_4804 = 8;`
- `5111` `write` `0x4806`: `DAT_EXTMEM_4806 = 0;`
- `5113` `write` `0x4807`: `DAT_EXTMEM_4807 = 1;`
- `5126` `read-modify-write` `0x4815`: `DAT_EXTMEM_4815 = DAT_EXTMEM_4815 & 0xcf | 0x20;`
- `5094` `write` `0x4840`: `DAT_EXTMEM_4840 = 0;`
- `5121` `write` `0x4840`: `DAT_EXTMEM_4840 = 0;`
- `5123` `write` `0x4840`: `DAT_EXTMEM_4840 = 0;`
- `5116` `write` `0x4860`: `DAT_EXTMEM_4860 = 0;`
- `5117` `write` `0x4861`: `DAT_EXTMEM_4861 = 0;`
- `5118` `write` `0x4862`: `DAT_EXTMEM_4862 = 0x30;`
- ... 6 more refs

### `FUN_CODE_4a1b`

`0x4703`, `0x470b`, `0x470e`, `0x4717`, `0x4723`, `0x4724`, `0x4726`, `0x4727`, `0x4728`, `0x4730`, `0x4733`, `0x4756`, `0x4761`, `0x4763`, `0x4766`, `0x4770`, `0x4771`, `0x4773`, `0x4780`, `0x4784`, `0x4788`, `0x478c`, `0x4799`, `0x47a7`, `0x47a9`, `0x47b9`, `0x47f3`, `0x48d5`

- `5180` `read-modify-write` `0x4703`: `DAT_EXTMEM_4703 = DAT_EXTMEM_4703 & 0xcf | 0x10;`
- `5159` `read-modify-write` `0x470b`: `DAT_EXTMEM_470b = DAT_EXTMEM_470b & 0x7f;`
- `5168` `test` `0x470e`: `if (DAT_EXTMEM_470e < '\0') {`
- `5166` `read-modify-write` `0x4717`: `DAT_EXTMEM_4717 = DAT_EXTMEM_4717 | 6;`
- `5160` `write` `0x4723`: `DAT_EXTMEM_4723 = 10;`
- `5191` `read-modify-write` `0x4724`: `DAT_EXTMEM_4724 = DAT_EXTMEM_4724 & 0x6f | 0x90;`
- `5192` `read-modify-write` `0x4726`: `DAT_EXTMEM_4726 = DAT_EXTMEM_4726 & 0x7f;`
- `5161` `read-modify-write` `0x4727`: `DAT_EXTMEM_4727 = DAT_EXTMEM_4727 | 4;`
- `5188` `read-modify-write` `0x4728`: `DAT_EXTMEM_4728 = DAT_EXTMEM_4728 | 0xc;`
- `5190` `read-modify-write` `0x4730`: `DAT_EXTMEM_4730 = DAT_EXTMEM_4730 | 1;`
- `5174` `read-modify-write` `0x4733`: `DAT_EXTMEM_4733 = DAT_EXTMEM_4733 & 0xf | 0x20;`
- `5183` `read-modify-write` `0x4756`: `DAT_EXTMEM_4756 = DAT_EXTMEM_4756 & 0x9f | 0x20;`
- `5167` `read-modify-write` `0x4761`: `DAT_EXTMEM_4761 = DAT_EXTMEM_4761 | 0x16;`
- `5162` `write` `0x4763`: `DAT_EXTMEM_4763 = 0x1f;`
- `5195` `read-modify-write` `0x4766`: `DAT_EXTMEM_4766 = DAT_EXTMEM_4766 | 0xc;`
- `5165` `read-modify-write` `0x4770`: `DAT_EXTMEM_4770 = DAT_EXTMEM_4770 | 2;`
- `5163` `write` `0x4771`: `DAT_EXTMEM_4771 = 0x4e;`
- `5164` `read-modify-write` `0x4773`: `DAT_EXTMEM_4773 = DAT_EXTMEM_4773 | 0x40;`
- `5187` `read-modify-write` `0x4780`: `DAT_EXTMEM_4780 = DAT_EXTMEM_4780 | 0x80;`
- `5181` `read-modify-write` `0x4784`: `DAT_EXTMEM_4784 = DAT_EXTMEM_4784 | 0x80;`
- `5182` `read-modify-write` `0x4788`: `DAT_EXTMEM_4788 = DAT_EXTMEM_4788 | 1;`
- `5189` `read-modify-write` `0x478c`: `DAT_EXTMEM_478c = DAT_EXTMEM_478c | 1;`
- `5194` `read-modify-write` `0x4799`: `DAT_EXTMEM_4799 = DAT_EXTMEM_4799 | 1;`
- `5184` `read-modify-write` `0x47a7`: `DAT_EXTMEM_47a7 = DAT_EXTMEM_47a7 & 0xfd | 0x81;`
- ... 4 more refs

### `FUN_CODE_4b4f`

`0x4000`, `0x4092`, `0x4093`, `0x4095`, `0x4098`

- `5237` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5242` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5244` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5247` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5239` `write` `0x4092`: `DAT_EXTMEM_4092 = 0;`
- `5240` `write` `0x4093`: `DAT_EXTMEM_4093 = 0;`
- `5238` `write` `0x4095`: `DAT_EXTMEM_4095 = 0xb;`
- `5245` `test` `0x4098`: `if (DAT_EXTMEM_4098 == 'Z') {`

### `FUN_CODE_4c7f`

`0x4727`, `0x4744`, `0x4748`, `0x479e`

- `5342` `read-modify-write` `0x4727`: `DAT_EXTMEM_4727 = DAT_EXTMEM_4727 | 8;`
- `5330` `write` `0x4744`: `DAT_EXTMEM_4744 = 0;`
- `5341` `write` `0x4744`: `DAT_EXTMEM_4744 = 0x34;`
- `5279` `write` `0x4748`: `DAT_EXTMEM_4748 = 0x88;`
- `5324` `write` `0x4748`: `DAT_EXTMEM_4748 = 0x88;`
- `5335` `write` `0x4748`: `DAT_EXTMEM_4748 = 0x98;`
- `5306` `read-modify-write` `0x479e`: `DAT_EXTMEM_479e = DAT_EXTMEM_479e & 0xaf | 0xa8;`

### `FUN_CODE_4da4`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4095`, `0x4096`, `0x4097`, `0x4098`, `0x48a0`, `0x8221`

- `5362` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5367` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5369` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5371` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5373` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5375` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5377` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5379` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5381` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5383` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5385` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5387` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5390` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5395` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5397` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5400` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5403` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5391` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_803c;`
- `5392` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_INTMEM_2e;`
- `5393` `write` `0x4093`: `DAT_EXTMEM_4093 = DAT_EXTMEM_803e - 0x2f;`
- `5363` `write` `0x4095`: `DAT_EXTMEM_4095 = 0xb;`
- `5364` `write` `0x4096`: `DAT_EXTMEM_4096 = 0;`
- `5365` `write` `0x4097`: `DAT_EXTMEM_4097 = 0;`
- `5401` `write` `0x4098`: `DAT_EXTMEM_4098 = DAT_EXTMEM_8221;`
- ... 3 more refs

### `FUN_CODE_4ec6`

`0x8164`, `0x818b`, `0x818c`, `0x818d`, `0x818e`, `0x818f`, `0x8190`

- `5469` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 2;`
- `5419` `test` `0x818b`: `if (((DAT_EXTMEM_818b & 1) != 1) && (DAT_EXTMEM_818c == '\0')) {`
- `5419` `test` `0x818c`: `if (((DAT_EXTMEM_818b & 1) != 1) && (DAT_EXTMEM_818c == '\0')) {`
- `5420` `test` `0x818d`: `if ((DAT_EXTMEM_818d != 0) || (DAT_EXTMEM_818e != 0)) {`
- `5422` `read` `0x818d`: `(cVar3 = ((DAT_EXTMEM_818e < 0x6a) << 7) >> 7, (byte)-cVar3 <= DAT_EXTMEM_818d)) {`
- `5424` `read` `0x818d`: `uVar4 = FUN_CODE_5f3d(DAT_EXTMEM_818d + cVar3,0x1d,0x38);`
- `5446` `test` `0x818d`: `if ((byte)-(((DAT_EXTMEM_818e < 0xb1) << 7) >> 7) <= DAT_EXTMEM_818d) {`
- `5447` `write` `0x818d`: `DAT_EXTMEM_818d = 0;`
- `5459` `read` `0x818d`: `bVar5 = DAT_EXTMEM_818d - bVar2;`
- `5460` `test` `0x818d`: `if (DAT_EXTMEM_818d < bVar2) {`
- `5461` `read` `0x818d`: `DAT_INTMEM_4d = DAT_EXTMEM_818d;`
- `5420` `test` `0x818e`: `if ((DAT_EXTMEM_818d != 0) || (DAT_EXTMEM_818e != 0)) {`
- `5422` `read` `0x818e`: `(cVar3 = ((DAT_EXTMEM_818e < 0x6a) << 7) >> 7, (byte)-cVar3 <= DAT_EXTMEM_818d)) {`
- `5446` `test` `0x818e`: `if ((byte)-(((DAT_EXTMEM_818e < 0xb1) << 7) >> 7) <= DAT_EXTMEM_818d) {`
- `5448` `write` `0x818e`: `DAT_EXTMEM_818e = 0xb0;`
- `5450` `read` `0x818e`: `FUN_CODE_6012(DAT_EXTMEM_818e + 0x96,2,0x89);`
- `5458` `read` `0x818e`: `bVar2 = DAT_INTMEM_4d - (((DAT_EXTMEM_818e < DAT_INTMEM_4e) << 7) >> 7);`
- `5462` `read` `0x818e`: `DAT_INTMEM_4e = DAT_EXTMEM_818e;`
- `5463` `read` `0x818e`: `bVar5 = DAT_EXTMEM_818e;`
- `5421` `test` `0x818f`: `if (((DAT_EXTMEM_818f & 0xc0) == 0x40) &&`
- `5432` `write` `0x8190`: `DAT_EXTMEM_8190 = bVar2 & 0xf7;`
- `5435` `write` `0x8190`: `DAT_EXTMEM_8190 = bVar2 | 8;`
- `5440` `read-modify-write` `0x8190`: `DAT_EXTMEM_8190 = DAT_EXTMEM_8190 | 0x10;`
- `5443` `read-modify-write` `0x8190`: `DAT_EXTMEM_8190 = DAT_EXTMEM_8190 & 0xef;`
- ... 1 more refs

### `FUN_CODE_50ca`

`0x4023`, `0x4700`, `0x4819`, `0x4844`

- `5557` `write` `0x4023`: `DAT_EXTMEM_4023 = DAT_EXTMEM_4844;`
- `5558` `test` `0x4700`: `if (((DAT_EXTMEM_4700 & 1) == 0) && ((DAT_EXTMEM_4844 & 1) != 0)) {`
- `5561` `read-modify-write` `0x4700`: `DAT_EXTMEM_4700 = DAT_EXTMEM_4700 | 2;`
- `5580` `test` `0x4819`: `if ((DAT_EXTMEM_4819 & 1) != 0) {`
- `5557` `read` `0x4844`: `DAT_EXTMEM_4023 = DAT_EXTMEM_4844;`
- `5558` `test` `0x4844`: `if (((DAT_EXTMEM_4700 & 1) == 0) && ((DAT_EXTMEM_4844 & 1) != 0)) {`
- `5559` `read-modify-write` `0x4844`: `DAT_EXTMEM_4844 = DAT_EXTMEM_4844 & 0xfe;`

### `FUN_CODE_51bc`

`0x4000`, `0x4098`, `0x40c0`, `0x40c2`, `0x40c3`, `0x40d3`, `0x48a0`

- `5698` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5703` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5708` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5712` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5716` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5717` `write` `0x4098`: `DAT_EXTMEM_4098 = (&DAT_CODE_4452)[bVar2];`
- `5684` `write` `0x40c0`: `DAT_EXTMEM_40c0 = 0xdc;`
- `5687` `write` `0x40c2`: `DAT_EXTMEM_40c2 = 2;`
- `5686` `write` `0x40c3`: `DAT_EXTMEM_40c3 = 0;`
- `5685` `write` `0x40d3`: `DAT_EXTMEM_40d3 = 0x20;`
- `5679` `test` `0x48a0`: `if (-1 < DAT_EXTMEM_48a0) {`

### `FUN_CODE_52a1`

`0x4000`, `0x4095`, `0x4096`, `0x4097`, `0x4098`

- `5742` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5757` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `5743` `write` `0x4095`: `DAT_EXTMEM_4095 = 6;`
- `5744` `write` `0x4096`: `DAT_EXTMEM_4096 = 0xc9;`
- `5745` `write` `0x4097`: `DAT_EXTMEM_4097 = 0x54;`
- `5755` `write` `0x4098`: `DAT_EXTMEM_4098 = *(undefined1 *)CONCAT11(cVar5 + -0x80,cVar6);`

### `FUN_CODE_536e`

`0x4700`, `0x4712`, `0x471f`, `0x4720`, `0x4721`, `0x4726`, `0x4748`, `0x4784`, `0x82af`

- `5809` `read-modify-write` `0x4700`: `DAT_EXTMEM_4700 = DAT_EXTMEM_4700 | 2;`
- `5819` `wait/test` `0x4700`: `while (bVar1 = param_1, (DAT_EXTMEM_4700 >> 1 & 1) != 0) {`
- `5836` `test` `0x4712`: `if (5 < DAT_EXTMEM_4712) break;`
- `5838` `read` `0x4712`: `FUN_CODE_6428(DAT_EXTMEM_4712 - 6);`
- `5800` `read` `0x471f`: `DAT_INTMEM_30 = DAT_EXTMEM_471f;`
- `5840` `write` `0x471f`: `DAT_EXTMEM_471f = DAT_INTMEM_30;`
- `5801` `read` `0x4720`: `DAT_INTMEM_31 = DAT_EXTMEM_4720;`
- `5841` `write` `0x4720`: `DAT_EXTMEM_4720 = DAT_INTMEM_31;`
- `5802` `read` `0x4721`: `DAT_INTMEM_32 = DAT_EXTMEM_4721;`
- `5842` `write` `0x4721`: `DAT_EXTMEM_4721 = DAT_INTMEM_32;`
- `5803` `read` `0x4726`: `DAT_INTMEM_33 = DAT_EXTMEM_4726;`
- `5843` `write` `0x4726`: `DAT_EXTMEM_4726 = DAT_INTMEM_33;`
- `5808` `read-modify-write` `0x4748`: `DAT_EXTMEM_4748 = DAT_EXTMEM_4748 | 0x80;`
- `5806` `read-modify-write` `0x4784`: `DAT_EXTMEM_4784 = DAT_EXTMEM_4784 | 0x40;`
- `5810` `test` `0x82af`: `if ((DAT_EXTMEM_82af >> 4 & 1) == 0) {`

### `FUN_CODE_542b`

`0x4014`, `0x4015`, `0x4016`, `0x4017`, `0x47b0`, `0x47b1`, `0x47c1`, `0x47c4`, `0x47c5`, `0x47d2`, `0x47d7`, `0x8164`, `0x8179`, `0x818a`, `0x818b`, `0x818c`, `0x818d`, `0x818e`, `0x818f`, `0x8190`, `0x8191`, `0x8192`, `0x8193`, `0x8194`, `0x8195`

- `5883` `write` `0x4014`: `DAT_EXTMEM_4014 = 0;`
- `5884` `write` `0x4015`: `DAT_EXTMEM_4015 = 0;`
- `5885` `write` `0x4016`: `DAT_EXTMEM_4016 = 0;`
- `5886` `write` `0x4017`: `DAT_EXTMEM_4017 = 0;`
- `5861` `write` `0x47b0`: `DAT_EXTMEM_47b0 = 0;`
- `5862` `read` `0x47b1`: `DAT_EXTMEM_818a = DAT_EXTMEM_47b1;`
- `5863` `read` `0x47b1`: `DAT_EXTMEM_818b = DAT_EXTMEM_47b1;`
- `5864` `read` `0x47b1`: `DAT_EXTMEM_818c = DAT_EXTMEM_47b1;`
- `5865` `read` `0x47b1`: `DAT_EXTMEM_818d = DAT_EXTMEM_47b1;`
- `5866` `read` `0x47b1`: `DAT_EXTMEM_818e = DAT_EXTMEM_47b1;`
- `5867` `read` `0x47b1`: `DAT_EXTMEM_818f = DAT_EXTMEM_47b1;`
- `5868` `read` `0x47b1`: `DAT_EXTMEM_8190 = DAT_EXTMEM_47b1;`
- `5869` `read` `0x47b1`: `DAT_EXTMEM_8191 = DAT_EXTMEM_47b1;`
- `5870` `read` `0x47b1`: `DAT_EXTMEM_8192 = DAT_EXTMEM_47b1;`
- `5871` `read` `0x47b1`: `DAT_EXTMEM_8193 = DAT_EXTMEM_47b1;`
- `5872` `read` `0x47b1`: `DAT_EXTMEM_8194 = DAT_EXTMEM_47b1;`
- `5873` `read` `0x47b1`: `DAT_EXTMEM_8195 = DAT_EXTMEM_47b1;`
- `5874` `test` `0x47c1`: `if ((DAT_EXTMEM_47c1 & 1) == 0) {`
- `5876` `read` `0x47c4`: `DAT_EXTMEM_80ea = DAT_EXTMEM_47c4;`
- `5875` `read` `0x47c5`: `DAT_EXTMEM_80e9 = DAT_EXTMEM_47c5;`
- `5877` `read-modify-write` `0x47d2`: `DAT_EXTMEM_47d2 = DAT_EXTMEM_47d2 & 0xfe;`
- `5881` `read-modify-write` `0x47d2`: `DAT_EXTMEM_47d2 = DAT_EXTMEM_47d2 | 1;`
- `5887` `read-modify-write` `0x47d7`: `DAT_EXTMEM_47d7 = DAT_EXTMEM_47d7 & 0xfe;`
- `5858` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 1;`
- ... 13 more refs

### `FUN_CODE_54e7`

`0x824c`, `0x824d`, `0x824e`, `0x824f`, `0x8250`, `0x8251`, `0x8253`, `0x8254`, `0x8255`, `0x8256`

- `5901` `write` `0x824c`: `DAT_EXTMEM_824c = '\0';`
- `5920` `read` `0x824c`: `FUN_CODE_5f3d((DAT_EXTMEM_824c + ('\a' - (((199 < DAT_EXTMEM_824d) << 7) >> 7))) -`
- `5902` `write` `0x824d`: `DAT_EXTMEM_824d = 0x10;`
- `5919` `read` `0x824d`: `cVar2 = DAT_EXTMEM_8256 + DAT_EXTMEM_824d + 0x38;`
- `5920` `read` `0x824d`: `FUN_CODE_5f3d((DAT_EXTMEM_824c + ('\a' - (((199 < DAT_EXTMEM_824d) << 7) >> 7))) -`
- `5921` `read` `0x824d`: `((CARRY1(DAT_EXTMEM_8256,DAT_EXTMEM_824d + 0x38) << 7) >> 7));`
- `5916` `read` `0x824e`: `FUN_CODE_1df7(0x8252,DAT_EXTMEM_824e,DAT_EXTMEM_824f,`
- `5916` `read` `0x824f`: `FUN_CODE_1df7(0x8252,DAT_EXTMEM_824e,DAT_EXTMEM_824f,`
- `5917` `read` `0x8250`: `DAT_EXTMEM_8250 - ((CARRY1(DAT_EXTMEM_8251,DAT_EXTMEM_8256) << 7) >> 7),`
- `5917` `read` `0x8251`: `DAT_EXTMEM_8250 - ((CARRY1(DAT_EXTMEM_8251,DAT_EXTMEM_8256) << 7) >> 7),`
- `5918` `read` `0x8251`: `DAT_EXTMEM_8251 + DAT_EXTMEM_8256);`
- `5922` `read` `0x8253`: `cVar1 = DAT_EXTMEM_8253;`
- `5923` `read` `0x8254`: `FUN_CODE_6239(DAT_EXTMEM_8254,DAT_EXTMEM_8255);`
- `5923` `read` `0x8255`: `FUN_CODE_6239(DAT_EXTMEM_8254,DAT_EXTMEM_8255);`
- `5903` `write` `0x8256`: `DAT_EXTMEM_8256 = 0;`
- `5905` `test` `0x8256`: `if (0xf < DAT_EXTMEM_8256) {`
- `5907` `test` `0x8256`: `if (DAT_EXTMEM_8256 == 0xee) {`
- `5917` `read` `0x8256`: `DAT_EXTMEM_8250 - ((CARRY1(DAT_EXTMEM_8251,DAT_EXTMEM_8256) << 7) >> 7),`
- `5918` `read` `0x8256`: `DAT_EXTMEM_8251 + DAT_EXTMEM_8256);`
- `5919` `read` `0x8256`: `cVar2 = DAT_EXTMEM_8256 + DAT_EXTMEM_824d + 0x38;`
- `5921` `read` `0x8256`: `((CARRY1(DAT_EXTMEM_8256,DAT_EXTMEM_824d + 0x38) << 7) >> 7));`
- `5925` `write` `0x8256`: `DAT_EXTMEM_8256 = 0xee;`
- `5928` `read-modify-write` `0x8256`: `DAT_EXTMEM_8256 = DAT_EXTMEM_8256 + 1;`

### `FUN_CODE_558c`

`0x4862`, `0x810e`, `0x810f`, `0x8110`, `0x8111`, `0x817b`, `0x824c`

- `5941` `read-modify-write` `0x4862`: `DAT_EXTMEM_4862 = DAT_EXTMEM_4862 & 0xfb;`
- `5969` `read-modify-write` `0x4862`: `DAT_EXTMEM_4862 = DAT_EXTMEM_4862 | 4;`
- `5944` `read` `0x810e`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `5944` `read` `0x810f`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `5944` `read` `0x8110`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `5944` `read` `0x8111`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `5940` `read-modify-write` `0x817b`: `DAT_EXTMEM_817b = DAT_EXTMEM_817b & 0xef;`
- `5946` `write` `0x824c`: `DAT_EXTMEM_824c = 0;`
- `5948` `test` `0x824c`: `if (0xf < DAT_EXTMEM_824c) break;`
- `5949` `read` `0x824c`: `bVar1 = DAT_EXTMEM_824c;`
- `5950` `read` `0x824c`: `FUN_CODE_5f35(DAT_EXTMEM_824c - 0x10);`
- `5951` `read-modify-write` `0x824c`: `DAT_EXTMEM_824c = DAT_EXTMEM_824c + 1;`
- `5958` `write` `0x824c`: `DAT_EXTMEM_824c = '\0';`
- `5961` `read-modify-write` `0x824c`: `DAT_EXTMEM_824c = DAT_EXTMEM_824c + '\x01';`
- `5962` `wait/test` `0x824c`: `} while (DAT_EXTMEM_824c != '\x10');`
- `5966` `read` `0x824c`: `for (DAT_EXTMEM_824c = 0; DAT_EXTMEM_824c < 0x10; DAT_EXTMEM_824c = DAT_EXTMEM_824c + 1) {`

### `FUN_CODE_5630`

`0x47fb`, `0x47fc`, `0x47fd`, `0x47fe`, `0x47ff`

- `6005` `write` `0x47fb`: `DAT_EXTMEM_47fb = *BANK1_R1;`
- `6012` `write` `0x47fb`: `DAT_EXTMEM_47fb = BANK1_R1['\x02'];`
- `6007` `write` `0x47fc`: `DAT_EXTMEM_47fc = FUN_CODE_1be3(1,BANK1_R1,0,0);`
- `6013` `write` `0x47fc`: `DAT_EXTMEM_47fc = FUN_CODE_1be3(1,BANK1_R1 + '\x02',0,0);`
- `6008` `write` `0x47fd`: `DAT_EXTMEM_47fd = BANK1_R1['\x02'];`
- `6014` `write` `0x47fd`: `DAT_EXTMEM_47fd = *BANK1_R1;`
- `6017` `write` `0x47fe`: `DAT_EXTMEM_47fe = FUN_CODE_1be3(1,puVar2);`
- `6004` `test` `0x47ff`: `if ((DAT_EXTMEM_47ff >> 5 & 1) == 0) {`

### `FUN_CODE_576a`

`0x4862`, `0x810e`, `0x810f`, `0x8110`, `0x8111`, `0x8244`, `0x8245`, `0x8246`, `0x8247`, `0x824c`, `0x824d`, `0x824e`, `0x824f`, `0x8250`, `0x8251`, `0x8252`, `0x8253`

- `6031` `read-modify-write` `0x4862`: `DAT_EXTMEM_4862 = DAT_EXTMEM_4862 & 0xfb;`
- `6049` `read-modify-write` `0x4862`: `DAT_EXTMEM_4862 = DAT_EXTMEM_4862 | 4;`
- `6035` `read` `0x810e`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0);`
- `6035` `read` `0x810f`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0);`
- `6035` `read` `0x8110`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0);`
- `6035` `read` `0x8111`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0);`
- `6030` `read` `0x8244`: `FUN_CODE_1df7(0x824c,DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `6030` `read` `0x8245`: `FUN_CODE_1df7(0x824c,DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `6030` `read` `0x8246`: `FUN_CODE_1df7(0x824c,DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `6030` `read` `0x8247`: `FUN_CODE_1df7(0x824c,DAT_EXTMEM_8244,DAT_EXTMEM_8245,DAT_EXTMEM_8246,DAT_EXTMEM_8247);`
- `6048` `read` `0x824c`: `FUN_CODE_3bfd(DAT_EXTMEM_824c,DAT_EXTMEM_824d,DAT_EXTMEM_824e,DAT_EXTMEM_824f);`
- `6048` `read` `0x824d`: `FUN_CODE_3bfd(DAT_EXTMEM_824c,DAT_EXTMEM_824d,DAT_EXTMEM_824e,DAT_EXTMEM_824f);`
- `6048` `read` `0x824e`: `FUN_CODE_3bfd(DAT_EXTMEM_824c,DAT_EXTMEM_824d,DAT_EXTMEM_824e,DAT_EXTMEM_824f);`
- `6048` `read` `0x824f`: `FUN_CODE_3bfd(DAT_EXTMEM_824c,DAT_EXTMEM_824d,DAT_EXTMEM_824e,DAT_EXTMEM_824f);`
- `6047` `read` `0x8250`: `FUN_CODE_1df7(0x8258,DAT_EXTMEM_8250,DAT_EXTMEM_8251,DAT_EXTMEM_8252,DAT_EXTMEM_8253);`
- `6047` `read` `0x8251`: `FUN_CODE_1df7(0x8258,DAT_EXTMEM_8250,DAT_EXTMEM_8251,DAT_EXTMEM_8252,DAT_EXTMEM_8253);`
- `6047` `read` `0x8252`: `FUN_CODE_1df7(0x8258,DAT_EXTMEM_8250,DAT_EXTMEM_8251,DAT_EXTMEM_8252,DAT_EXTMEM_8253);`
- `6047` `read` `0x8253`: `FUN_CODE_1df7(0x8258,DAT_EXTMEM_8250,DAT_EXTMEM_8251,DAT_EXTMEM_8252,DAT_EXTMEM_8253);`

### `FUN_CODE_587c`

`0x4014`, `0x4015`, `0x4016`, `0x4017`, `0x4773`, `0x47c7`, `0x47d0`, `0x47d2`, `0x8164`, `0x8179`, `0x818a`

- `6122` `write` `0x4014`: `DAT_EXTMEM_4014 = 0;`
- `6123` `write` `0x4015`: `DAT_EXTMEM_4015 = 0;`
- `6124` `write` `0x4016`: `DAT_EXTMEM_4016 = 0;`
- `6125` `write` `0x4017`: `DAT_EXTMEM_4017 = 0;`
- `6098` `read-modify-write` `0x4773`: `DAT_EXTMEM_4773 = DAT_EXTMEM_4773 | 0x20;`
- `6092` `read` `0x47c7`: `DAT_INTMEM_2b = DAT_EXTMEM_47c7;`
- `6094` `test` `0x47c7`: `if (DAT_EXTMEM_47c7 == '\b') {`
- `6117` `test` `0x47c7`: `if (DAT_EXTMEM_47c7 != -0x70) {`
- `6119` `read` `0x47c7`: `DAT_EXTMEM_818a = DAT_EXTMEM_47c7;`
- `6131` `write` `0x47d0`: `DAT_EXTMEM_47d0 = 8;`
- `6097` `read-modify-write` `0x47d2`: `DAT_EXTMEM_47d2 = DAT_EXTMEM_47d2 & 0xfe;`
- `6100` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 4;`
- `6114` `read-modify-write` `0x8164`: `DAT_EXTMEM_8164 = DAT_EXTMEM_8164 | 1;`
- `6093` `read-modify-write` `0x8179`: `DAT_EXTMEM_8179 = DAT_EXTMEM_8179 & 0xef;`
- `6132` `read-modify-write` `0x8179`: `DAT_EXTMEM_8179 = DAT_EXTMEM_8179 & 0xef;`
- `6119` `write` `0x818a`: `DAT_EXTMEM_818a = DAT_EXTMEM_47c7;`

### `FUN_CODE_59f3`

`0x4860`, `0x4861`, `0x4862`, `0x4863`, `0x4864`, `0x4865`, `0x4867`, `0x486a`, `0x486b`, `0x48ee`, `0x48fc`, `0x5904`, `0x5905`, `0x5906`, `0x592a`, `0x5954`, `0x59c0`, `0x59f0`, `0x59f1`, `0x5a00`, `0x5a01`, `0x5a24`, `0x5a31`

- `6246` `write` `0x4860`: `DAT_EXTMEM_4860 = 0;`
- `6247` `write` `0x4861`: `DAT_EXTMEM_4861 = 0;`
- `6248` `write` `0x4862`: `DAT_EXTMEM_4862 = 0;`
- `6249` `write` `0x4863`: `DAT_EXTMEM_4863 = 0;`
- `6250` `write` `0x4864`: `DAT_EXTMEM_4864 = 0;`
- `6251` `write` `0x4865`: `DAT_EXTMEM_4865 = 0;`
- `6252` `write` `0x4867`: `DAT_EXTMEM_4867 = 0x61;`
- `6253` `write` `0x486a`: `DAT_EXTMEM_486a = 0;`
- `6254` `write` `0x486b`: `DAT_EXTMEM_486b = 0;`
- `6255` `read-modify-write` `0x48ee`: `DAT_EXTMEM_48ee = DAT_EXTMEM_48ee & 0xfd;`
- `6256` `read-modify-write` `0x48fc`: `DAT_EXTMEM_48fc = DAT_EXTMEM_48fc & 0xf0;`
- `6234` `write` `0x5904`: `DAT_EXTMEM_5904 = 0;`
- `6235` `write` `0x5905`: `DAT_EXTMEM_5905 = 0;`
- `6237` `read-modify-write` `0x5906`: `DAT_EXTMEM_5906 = DAT_EXTMEM_5906 & 0x1c;`
- `6238` `read-modify-write` `0x592a`: `DAT_EXTMEM_592a = DAT_EXTMEM_592a & 0xf7;`
- `6245` `read-modify-write` `0x5954`: `DAT_EXTMEM_5954 = DAT_EXTMEM_5954 & 0x3f;`
- `6236` `read-modify-write` `0x59c0`: `DAT_EXTMEM_59c0 = DAT_EXTMEM_59c0 & 0xfe | 4;`
- `6239` `write` `0x59f0`: `DAT_EXTMEM_59f0 = 0;`
- `6240` `read-modify-write` `0x59f1`: `DAT_EXTMEM_59f1 = DAT_EXTMEM_59f1 & 0x3f;`
- `6241` `read-modify-write` `0x5a00`: `DAT_EXTMEM_5a00 = DAT_EXTMEM_5a00 & 0xf8;`
- `6242` `write` `0x5a01`: `DAT_EXTMEM_5a01 = 0x18;`
- `6243` `read-modify-write` `0x5a24`: `DAT_EXTMEM_5a24 = DAT_EXTMEM_5a24 & 0x30;`
- `6244` `read-modify-write` `0x5a31`: `DAT_EXTMEM_5a31 = DAT_EXTMEM_5a31 & 0xfd;`

### `FUN_CODE_5a68`

`0x4700`, `0x470c`, `0x470f`, `0x4735`, `0x4748`, `0x4796`, `0x4797`, `0x8281`, `0x8282`, `0x8283`, `0x8284`

- `6271` `read-modify-write` `0x4700`: `DAT_EXTMEM_4700 = DAT_EXTMEM_4700 | 2;`
- `6266` `read` `0x470c`: `DAT_INTMEM_2b = DAT_EXTMEM_470c >> 4;`
- `6267` `read` `0x470c`: `DAT_INTMEM_2c = DAT_EXTMEM_470c & 0xf;`
- `6269` `read-modify-write` `0x470f`: `DAT_EXTMEM_470f = DAT_EXTMEM_470f & 0xf3 | 4;`
- `6280` `read` `0x470f`: `DAT_EXTMEM_8282 = DAT_EXTMEM_470f;`
- `6268` `read-modify-write` `0x4735`: `DAT_EXTMEM_4735 = DAT_EXTMEM_4735 & 0xbc;`
- `6270` `read-modify-write` `0x4748`: `DAT_EXTMEM_4748 = DAT_EXTMEM_4748 | 0x80;`
- `6276` `write` `0x4796`: `DAT_EXTMEM_4796 = DAT_INTMEM_2b;`
- `6277` `write` `0x4797`: `DAT_EXTMEM_4797 = DAT_INTMEM_2c;`
- `6272` `write` `0x8281`: `DAT_EXTMEM_8281 = 0x83;`
- `6279` `write` `0x8281`: `DAT_EXTMEM_8281 = 0x83;`
- `6273` `write` `0x8282`: `DAT_EXTMEM_8282 = 0x49;`
- `6280` `write` `0x8282`: `DAT_EXTMEM_8282 = DAT_EXTMEM_470f;`
- `6274` `write` `0x8283`: `DAT_EXTMEM_8283 = 0x4d;`
- `6281` `write` `0x8283`: `DAT_EXTMEM_8283 = DAT_INTMEM_2b;`
- `6275` `write` `0x8284`: `DAT_EXTMEM_8284 = 0x42;`
- `6282` `write` `0x8284`: `DAT_EXTMEM_8284 = DAT_INTMEM_2c;`

### `FUN_CODE_5ad6`

`0x4000`, `0x4095`, `0x4096`, `0x4097`, `0x4098`

- `6306` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6323` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6307` `write` `0x4095`: `DAT_EXTMEM_4095 = FUN_CODE_1be3(1,BANK1_R1,0,0);`
- `6308` `write` `0x4096`: `DAT_EXTMEM_4096 = FUN_CODE_1be3(2);`
- `6309` `write` `0x4097`: `DAT_EXTMEM_4097 = FUN_CODE_1be3(3);`
- `6321` `write` `0x4098`: `DAT_EXTMEM_4098 = *(undefined1 *)(BANK1_R1 + '\x04');`

### `FUN_CODE_5c0e`

`0x4000`, `0x40b5`, `0x40b6`, `0x40b7`

- `6419` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6426` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6417` `write` `0x40b5`: `DAT_EXTMEM_40b5 = 0x14;`
- `6424` `write` `0x40b5`: `DAT_EXTMEM_40b5 = 0x14;`
- `6415` `write` `0x40b6`: `DAT_EXTMEM_40b6 = 0x10;`
- `6422` `write` `0x40b6`: `DAT_EXTMEM_40b6 = DAT_INTMEM_36;`
- `6416` `write` `0x40b7`: `DAT_EXTMEM_40b7 = 0;`
- `6423` `write` `0x40b7`: `DAT_EXTMEM_40b7 = DAT_INTMEM_37;`

### `FUN_CODE_5c72`

`0x47af`, `0x47b1`, `0x47d6`, `0x818e`

- `6442` `write` `0x47af`: `DAT_EXTMEM_47af = 0;`
- `6443` `write` `0x47b1`: `DAT_EXTMEM_47b1 = 0;`
- `6441` `write` `0x47d6`: `DAT_EXTMEM_47d6 = DAT_EXTMEM_818e;`
- `6437` `test` `0x818e`: `if (DAT_EXTMEM_818e != 0) {`
- `6438` `test` `0x818e`: `if (0x12 < DAT_EXTMEM_818e) {`
- `6439` `write` `0x818e`: `DAT_EXTMEM_818e = 0x12;`
- `6441` `read` `0x818e`: `DAT_EXTMEM_47d6 = DAT_EXTMEM_818e;`

### `FUN_CODE_5d36`

`0x810e`, `0x810f`, `0x8110`, `0x8111`, `0x8257`

- `6460` `read` `0x810e`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `6460` `read` `0x810f`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `6460` `read` `0x8110`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `6460` `read` `0x8111`: `cVar2 = FUN_CODE_1d8b(DAT_EXTMEM_810e,DAT_EXTMEM_810f,DAT_EXTMEM_8110,DAT_EXTMEM_8111,0,0,0,0);`
- `6462` `read` `0x8257`: `for (DAT_EXTMEM_8257 = 0; DAT_EXTMEM_8257 < 0x10; DAT_EXTMEM_8257 = DAT_EXTMEM_8257 + 1) {`
- `6463` `read` `0x8257`: `bVar1 = DAT_EXTMEM_8257;`
- `6469` `read` `0x8257`: `for (DAT_EXTMEM_8257 = 0; DAT_EXTMEM_8257 < 0x10; DAT_EXTMEM_8257 = DAT_EXTMEM_8257 + 1) {`
- `6471` `read` `0x8257`: `*(byte *)CONCAT11(-0x7f - (((0xe1 < DAT_EXTMEM_8257) << 7) >> 7),DAT_EXTMEM_8257 + 0x1e);`
- `6474` `read` `0x8257`: `return DAT_EXTMEM_8257 - 0x10;`

### `FUN_CODE_5ded`

`0x4784`, `0x47cd`, `0x47d1`, `0x47d5`

- `6514` `read-modify-write` `0x4784`: `DAT_EXTMEM_4784 = DAT_EXTMEM_4784 | 0x40;`
- `6503` `read-modify-write` `0x47cd`: `DAT_EXTMEM_47cd = DAT_EXTMEM_47cd & 0xf7;`
- `6504` `write` `0x47d1`: `DAT_EXTMEM_47d1 = 2;`
- `6509` `wait/test` `0x47d5`: `while ((DAT_EXTMEM_47d5 >> 1 & 1) != 0) {`
- `6516` `wait/test` `0x47d5`: `} while ((DAT_EXTMEM_47d5 >> 1 & 1) != 0);`

### `FUN_CODE_5df4`

`0x4784`, `0x47d1`, `0x47d5`

- `6540` `read-modify-write` `0x4784`: `DAT_EXTMEM_4784 = DAT_EXTMEM_4784 | 0x40;`
- `6530` `write` `0x47d1`: `DAT_EXTMEM_47d1 = 2;`
- `6535` `wait/test` `0x47d5`: `while ((DAT_EXTMEM_47d5 >> 1 & 1) != 0) {`
- `6542` `wait/test` `0x47d5`: `} while ((DAT_EXTMEM_47d5 >> 1 & 1) != 0);`

### `FUN_CODE_5e40`

`0x4700`, `0x4709`, `0x470e`, `0x47f3`

- `6560` `read-modify-write` `0x4700`: `DAT_EXTMEM_4700 = DAT_EXTMEM_4700 | 2;`
- `6569` `read-modify-write` `0x4700`: `DAT_EXTMEM_4700 = DAT_EXTMEM_4700 | 2;`
- `6559` `read-modify-write` `0x4709`: `DAT_EXTMEM_4709 = DAT_EXTMEM_4709 & 0xfd | 1;`
- `6568` `read-modify-write` `0x4709`: `DAT_EXTMEM_4709 = DAT_EXTMEM_4709 & 0xfe | 2;`
- `6556` `test` `0x470e`: `if (-1 < DAT_EXTMEM_470e) {`
- `6565` `test` `0x470e`: `if (DAT_EXTMEM_470e < '\0') {`
- `6555` `read-modify-write` `0x47f3`: `DAT_EXTMEM_47f3 = DAT_EXTMEM_47f3 & 0x7f;`
- `6564` `read-modify-write` `0x47f3`: `DAT_EXTMEM_47f3 = DAT_EXTMEM_47f3 | 0x80;`

### `FUN_CODE_5e93`

`0x4018`, `0x47c9`, `0x47ca`, `0x47cb`, `0x47cf`, `0x47d0`, `0x8179`, `0x818a`

- `6602` `write` `0x4018`: `DAT_EXTMEM_4018 = 3;`
- `6592` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x50;`
- `6587` `write` `0x47ca`: `DAT_EXTMEM_47ca = 0x50;`
- `6585` `write` `0x47cb`: `DAT_EXTMEM_47cb = 0;`
- `6594` `write` `0x47cf`: `DAT_EXTMEM_47cf = 1;`
- `6588` `write` `0x47d0`: `DAT_EXTMEM_47d0 = 0;`
- `6595` `write` `0x47d0`: `DAT_EXTMEM_47d0 = 1;`
- `6598` `write` `0x47d0`: `DAT_EXTMEM_47d0 = 1;`
- `6601` `read-modify-write` `0x8179`: `DAT_EXTMEM_8179 = DAT_EXTMEM_8179 & 0xef;`
- `6586` `test` `0x818a`: `if (DAT_EXTMEM_818a == -0x5f) {`
- `6593` `test` `0x818a`: `if (DAT_EXTMEM_818a == '\x03') {`

### `FUN_CODE_5ee4`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`

- `6621` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6626` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6631` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6622` `write` `0x4091`: `DAT_EXTMEM_4091 = 6;`
- `6623` `write` `0x4092`: `DAT_EXTMEM_4092 = 0xc9;`
- `6624` `write` `0x4093`: `DAT_EXTMEM_4093 = 0x54;`
- `6632` `read` `0x4098`: `*(undefined1 *)CONCAT11(cVar2 + -0x80,cVar3) = DAT_EXTMEM_4098;`

### `FUN_CODE_5f35`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`

- `6648` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6658` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6656` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_803c;`
- `6655` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_INTMEM_2e;`
- `6654` `write` `0x4093`: `DAT_EXTMEM_4093 = DAT_INTMEM_2f;`
- `6659` `read` `0x4098`: `return DAT_EXTMEM_4098;`

### `FUN_CODE_5f36`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`

- `6668` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6678` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6676` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_803c;`
- `6675` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_INTMEM_2e;`
- `6674` `write` `0x4093`: `DAT_EXTMEM_4093 = DAT_INTMEM_2f;`
- `6679` `read` `0x4098`: `return DAT_EXTMEM_4098;`

### `FUN_CODE_5f38`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`

- `6690` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6698` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6696` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_803c;`
- `6695` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_INTMEM_2e;`
- `6694` `write` `0x4093`: `DAT_EXTMEM_4093 = DAT_EXTMEM_803e + param_1;`
- `6699` `read` `0x4098`: `return DAT_EXTMEM_4098;`

### `FUN_CODE_5f3d`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`

- `6708` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6715` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6713` `write` `0x4091`: `DAT_EXTMEM_4091 = DAT_EXTMEM_803c;`
- `6712` `write` `0x4092`: `DAT_EXTMEM_4092 = DAT_INTMEM_2e;`
- `6711` `write` `0x4093`: `DAT_EXTMEM_4093 = DAT_EXTMEM_803e + param_2;`
- `6716` `read` `0x4098`: `return DAT_EXTMEM_4098;`

### `FUN_CODE_5fc5`

`0x82af`

- `6751` `write` `0x82af`: `DAT_EXTMEM_82af = 0;`
- `6755` `read-modify-write` `0x82af`: `DAT_EXTMEM_82af = DAT_EXTMEM_82af | 2;`
- `6759` `read-modify-write` `0x82af`: `DAT_EXTMEM_82af = DAT_EXTMEM_82af | 4;`
- `6764` `read-modify-write` `0x82af`: `DAT_EXTMEM_82af = DAT_EXTMEM_82af | 0x10;`
- `6767` `read-modify-write` `0x82af`: `DAT_EXTMEM_82af = DAT_EXTMEM_82af | 1;`
- `6772` `read-modify-write` `0x82af`: `DAT_EXTMEM_82af = DAT_EXTMEM_82af | 8;`

### `FUN_CODE_6008`

`0x4000`, `0x4095`, `0x4096`, `0x4097`, `0x4098`

- `6787` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6793` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6790` `write` `0x4095`: `DAT_EXTMEM_4095 = DAT_EXTMEM_803c;`
- `6789` `write` `0x4096`: `DAT_EXTMEM_4096 = DAT_INTMEM_2e;`
- `6788` `write` `0x4097`: `DAT_EXTMEM_4097 = DAT_EXTMEM_803e + param_1;`
- `6791` `write` `0x4098`: `DAT_EXTMEM_4098 = DAT_EXTMEM_42b5;`

### `FUN_CODE_6012`

`0x4000`, `0x4095`, `0x4096`, `0x4097`, `0x4098`

- `6805` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6811` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `6808` `write` `0x4095`: `DAT_EXTMEM_4095 = DAT_EXTMEM_803c;`
- `6807` `write` `0x4096`: `DAT_EXTMEM_4096 = DAT_INTMEM_2e;`
- `6806` `write` `0x4097`: `DAT_EXTMEM_4097 = DAT_EXTMEM_803e + param_3;`
- `6809` `write` `0x4098`: `DAT_EXTMEM_4098 = param_1;`

### `FUN_CODE_6048`

`0x482b`, `0x482c`, `0x482d`

- `6838` `write` `0x482b`: `DAT_EXTMEM_482b = 1;`
- `6828` `read` `0x482c`: `DAT_INTMEM_2b = DAT_EXTMEM_482c;`
- `6833` `read` `0x482c`: `DAT_INTMEM_2d = DAT_EXTMEM_482c;`
- `6829` `read` `0x482d`: `DAT_INTMEM_2c = DAT_EXTMEM_482d;`
- `6834` `read` `0x482d`: `DAT_INTMEM_2e = DAT_EXTMEM_482d;`

### `FUN_CODE_6087`

`0x4013`, `0x4014`, `0x4015`, `0x4016`, `0x4017`, `0x4018`, `0x4773`, `0x4774`, `0x47c9`, `0x8179`

- `6848` `write` `0x4013`: `DAT_EXTMEM_4013 = param_1;`
- `6849` `write` `0x4014`: `DAT_EXTMEM_4014 = 0;`
- `6850` `write` `0x4015`: `DAT_EXTMEM_4015 = 0;`
- `6851` `write` `0x4016`: `DAT_EXTMEM_4016 = DAT_INTMEM_4d;`
- `6852` `write` `0x4017`: `DAT_EXTMEM_4017 = DAT_INTMEM_4e;`
- `6856` `write` `0x4018`: `DAT_EXTMEM_4018 = 1;`
- `6859` `read-modify-write` `0x4773`: `DAT_EXTMEM_4773 = DAT_EXTMEM_4773 & 0xdf | 0x20;`
- `6858` `wait/test` `0x4774`: `} while ((DAT_EXTMEM_4774 >> 5 & 1) == 0);`
- `6853` `write` `0x47c9`: `DAT_EXTMEM_47c9 = 0x50;`
- `6855` `read-modify-write` `0x8179`: `DAT_EXTMEM_8179 = DAT_EXTMEM_8179 & 0xef;`

### `FUN_CODE_60c4`

`0x474d`, `0x482b`, `0x482c`, `0x482d`

- `6874` `test` `0x474d`: `if (DAT_EXTMEM_474d < '\0') break;`
- `6878` `read` `0x474d`: `return DAT_EXTMEM_474d;`
- `6873` `write` `0x482b`: `DAT_EXTMEM_482b = 5;`
- `6870` `read` `0x482c`: `DAT_INTMEM_39 = DAT_EXTMEM_482c;`
- `6875` `read` `0x482c`: `DAT_INTMEM_3b = DAT_EXTMEM_482c;`
- `6871` `read` `0x482d`: `DAT_INTMEM_3a = DAT_EXTMEM_482d;`
- `6876` `read` `0x482d`: `DAT_INTMEM_3c = DAT_EXTMEM_482d;`

### `FUN_CODE_60ff`

`0x482b`, `0x482c`, `0x482d`

- `6896` `write` `0x482b`: `DAT_EXTMEM_482b = param_3 | 1;`
- `6893` `read` `0x482c`: `DAT_INTMEM_2b = DAT_EXTMEM_482c;`
- `6897` `read` `0x482c`: `DAT_INTMEM_2d = DAT_EXTMEM_482c;`
- `6894` `read` `0x482d`: `DAT_INTMEM_2c = DAT_EXTMEM_482d;`
- `6898` `read` `0x482d`: `DAT_INTMEM_2e = DAT_EXTMEM_482d;`

### `FUN_CODE_6206`

`0x4011`, `0x4012`, `0x4013`, `0x4014`, `0x4015`, `0x4016`, `0x4017`

- `7048` `write` `0x4011`: `DAT_EXTMEM_4011 = DAT_EXTMEM_803c;`
- `7049` `write` `0x4012`: `DAT_EXTMEM_4012 = DAT_INTMEM_2b;`
- `7050` `write` `0x4013`: `DAT_EXTMEM_4013 = DAT_EXTMEM_803e + param_2;`
- `7051` `write` `0x4014`: `DAT_EXTMEM_4014 = 0;`
- `7052` `write` `0x4015`: `DAT_EXTMEM_4015 = 0;`
- `7053` `write` `0x4016`: `DAT_EXTMEM_4016 = DAT_INTMEM_4d;`
- `7054` `write` `0x4017`: `DAT_EXTMEM_4017 = DAT_INTMEM_4e;`

### `FUN_CODE_6235`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`

- `7067` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7072` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7068` `write` `0x4091`: `DAT_EXTMEM_4091 = 1;`
- `7069` `write` `0x4092`: `DAT_EXTMEM_4092 = 0x80;`
- `7070` `write` `0x4093`: `DAT_EXTMEM_4093 = param_1;`
- `7073` `read` `0x4098`: `return DAT_EXTMEM_4098;`

### `FUN_CODE_6239`

`0x4000`, `0x4091`, `0x4092`, `0x4093`, `0x4098`

- `7084` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7089` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7085` `write` `0x4091`: `DAT_EXTMEM_4091 = param_3;`
- `7086` `write` `0x4092`: `DAT_EXTMEM_4092 = param_1;`
- `7087` `write` `0x4093`: `DAT_EXTMEM_4093 = param_2;`
- `7090` `read` `0x4098`: `return DAT_EXTMEM_4098;`

### `FUN_CODE_628f`

`0x4725`, `0x47f3`, `0x47f4`, `0x47ff`

- `7121` `read-modify-write` `0x4725`: `DAT_EXTMEM_4725 = DAT_EXTMEM_4725 & 0xfc;`
- `7122` `read-modify-write` `0x47f3`: `DAT_EXTMEM_47f3 = DAT_EXTMEM_47f3 & 0x7f;`
- `7124` `read-modify-write` `0x47f4`: `DAT_EXTMEM_47f4 = DAT_EXTMEM_47f4 | 0xc;`
- `7123` `read-modify-write` `0x47ff`: `DAT_EXTMEM_47ff = DAT_EXTMEM_47ff | 0x20;`

### `FUN_CODE_62e5`

`0x4000`, `0x4095`, `0x4096`, `0x4097`, `0x4098`

- `7136` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7142` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7137` `write` `0x4095`: `DAT_EXTMEM_4095 = 1;`
- `7138` `write` `0x4096`: `DAT_EXTMEM_4096 = 0;`
- `7139` `write` `0x4097`: `DAT_EXTMEM_4097 = 0x20;`
- `7140` `write` `0x4098`: `DAT_EXTMEM_4098 = param_1;`

### `FUN_CODE_62eb`

`0x4000`, `0x4095`, `0x4096`, `0x4097`, `0x4098`

- `7154` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7160` `wait/test` `0x4000`: `} while (DAT_EXTMEM_4000 < '\0');`
- `7155` `write` `0x4095`: `DAT_EXTMEM_4095 = param_4;`
- `7156` `write` `0x4096`: `DAT_EXTMEM_4096 = param_2;`
- `7157` `write` `0x4097`: `DAT_EXTMEM_4097 = param_3;`
- `7158` `write` `0x4098`: `DAT_EXTMEM_4098 = param_1;`

### `FUN_CODE_6336`

`0x8257`

- `7187` `write` `0x8257`: `DAT_EXTMEM_8257 = 0;`
- `7189` `test` `0x8257`: `if (0xf < DAT_EXTMEM_8257) break;`
- `7192` `read` `0x8257`: `CONCAT11(-0x7f - (((0xf1 < DAT_EXTMEM_8257) << 7) >> 7),DAT_EXTMEM_8257 + 0xe);`
- `7193` `read-modify-write` `0x8257`: `DAT_EXTMEM_8257 = DAT_EXTMEM_8257 + 1;`
- `7195` `read` `0x8257`: `return DAT_EXTMEM_8257 - 0x10;`

### `FUN_CODE_6383`

`0x8277`, `0x8278`, `0x82a5`, `0x82a6`

- `7220` `write` `0x8277`: `DAT_EXTMEM_8277 = 0;`
- `7222` `write` `0x8278`: `DAT_EXTMEM_8278 = 0;`
- `7221` `write` `0x82a5`: `DAT_EXTMEM_82a5 = 0xff;`
- `7223` `write` `0x82a6`: `DAT_EXTMEM_82a6 = 0;`

### `FUN_CODE_63cb`

`0x4814`, `0x4821`, `0x4822`

- `7246` `wait/test` `0x4814`: `} while (-1 < DAT_EXTMEM_4814);`
- `7244` `write` `0x4821`: `DAT_EXTMEM_4821 = 0xc0;`
- `7243` `write` `0x4822`: `DAT_EXTMEM_4822 = param_1 >> 1;`
