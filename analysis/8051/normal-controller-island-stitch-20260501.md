# Normal Controller Island Stitch Report

This report treats the normal work-window as a rotating 0x40-byte tile
surface. Publicly adjacent slots are useful evidence, but they are not
assumed to be one stable code image unless repeated adjacency supports it.

## Summary

- captures scanned: `509`
- chunk size: `0x40`
- selected ranges: `0x7000:0x7240, 0x7480:0x7680, 0xdbc0:0xdcc0`
- unique chunks in selected ranges: `35`
- observed adjacent chunk edges in selected ranges: `92`
- seed component chunks at edge threshold `1`: `16`

## Anchor Patterns

| pattern                      | hits | offsets                                                                                                             | top runs                                                                                                                                                                                                                                                          | chunks                                                                             |
| ---------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `public_bridge_8a4c_to_4011` | 509  | `0x715a` x251, `0x711a` x136, `0x719a` x122                                                                         | `normal-work-window-get-performance-variants-long-20260501` x76, `normal-work-window-get-config-field-variants-r5-long-20260501` x48, `normal-work-window-stimuli-focused-20260501` x40, `normal-work-window-get-performance-variants-20260501` x38               | `20ea2ab16891` x509                                                                |
| `public_bridge_8a4d_to_4012` | 509  | `0x7162` x251, `0x7122` x136, `0x71a2` x122                                                                         | `normal-work-window-get-performance-variants-long-20260501` x76, `normal-work-window-get-config-field-variants-r5-long-20260501` x48, `normal-work-window-stimuli-focused-20260501` x40, `normal-work-window-get-performance-variants-20260501` x38               | `20ea2ab16891` x509                                                                |
| `public_bridge_8a4e_to_4013` | 509  | `0x716a` x251, `0x712a` x136, `0x71aa` x122                                                                         | `normal-work-window-get-performance-variants-long-20260501` x76, `normal-work-window-get-config-field-variants-r5-long-20260501` x48, `normal-work-window-stimuli-focused-20260501` x40, `normal-work-window-get-performance-variants-20260501` x38               | `20ea2ab16891` x509                                                                |
| `controller_addr_4091`       | 572  | `0x7603` x253, `0x7672` x253, `0x70ce` x17, `0x700e` x15, `0x715d` x13, `0x711d` x9, `0x708e` x7, `0x719d` x5       | `normal-work-window-stimuli-focused-20260501` x84, `normal-work-window-readstatus-correlation-20260501` x70, `normal-work-window-get-config-current-long-20260501` x67, `normal-work-window-get-config-variants-20260501` x56                                     | `0c9a360d26b8` x253, `3465e4783c3d` x253, `4037c8574920` x39, `8b2115cd509f` x27   |
| `controller_addr_4095`       | 1783 | `0xdbf6` x509, `0xdc19` x509, `0xdc6c` x509, `0x7646` x256                                                          | `normal-work-window-get-performance-variants-long-20260501` x304, `normal-work-window-get-config-field-variants-r5-long-20260501` x192, `normal-work-window-get-performance-variants-20260501` x152, `normal-work-window-get-config-r5-01-isolated-20260501` x128 | `e2488fa3edce` x509, `cf3469eae7d0` x509, `ebaf1ca1d57c` x509, `580b9228d0b9` x256 |
| `controller_kick_409c`       | 1602 | `0x74e9` x502, `0x7660` x256, `0x7673` x256, `0x7620` x253, `0x7629` x253, `0x70eb` x17, `0x70f4` x17, `0x702b` x15 | `normal-work-window-get-performance-variants-long-20260501` x228, `normal-work-window-get-config-field-variants-r5-long-20260501` x166, `normal-work-window-stimuli-focused-20260501` x128, `normal-work-window-get-performance-variants-20260501` x114           | `580b9228d0b9` x512, `9b673c066ae4` x506, `0c9a360d26b8` x506, `4037c8574920` x78  |
| `getcfg_4099_to_shadow`      | 39   | `0x7143` x21, `0x7103` x12, `0x7183` x6                                                                             | `normal-work-window-get-config-field-variants-r5-long-20260501` x11, `normal-work-window-get-config-field-variants-20260501` x6, `normal-work-window-get-config-r5-f0-isolated-20260501` x6, `normal-work-window-get-config-variants-20260501` x4                 | `8d8c3b0a22a0` x39                                                                 |
| `getcfg_fe_sentinel_branch`  | 39   | `0x7166` x21, `0x7126` x12, `0x71a6` x6                                                                             | `normal-work-window-get-config-field-variants-r5-long-20260501` x11, `normal-work-window-get-config-field-variants-20260501` x6, `normal-work-window-get-config-r5-f0-isolated-20260501` x6, `normal-work-window-get-config-variants-20260501` x4                 | `8d8c3b0a22a0` x39                                                                 |

## GET CONFIG Seed Component

The main seed is the chunk containing the `0x4099 -> 0x8a4e/0x8a53/0x8a54`
burst and the `0x8a4d == 0xfe` branch. Its neighbors form a small
rotating component around the response builder.

| chunk          | obs | offsets                                                  | top DPTR refs                                                                | direct copies                                                          | top next                                                                          |
| -------------- | --- | -------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `7e15398acc97` | 509 | `0x7040` x256, `0x7000` x217, `0x70c0` x26, `0x7080` x10 | `0x8988` x2, `0x893d` x1, `0x47c9` x1, `0x47cb` x1                           | -                                                                      | `5b46d4574b86` x473, `8636ecaed520` x26, `8f8e0add044c` x6, `d92154cb54aa` x3     |
| `8f8e0add044c` | 509 | `0x70c0` x222, `0x7080` x153, `0x7000` x134              | `0x4011` x2, `0x85fd` x1, `0x8a29` x1, `0x8a4c` x1, `0x85fe` x1, `0x85ff` x1 | `0x85fe->0x4011`, `0x85ff->0x4012`                                     | `7e15398acc97` x136, `20ea2ab16891` x136, `d92154cb54aa` x128, `8636ecaed520` x86 |
| `d92154cb54aa` | 440 | `0x70c0` x230, `0x7000` x132, `0x7080` x78               | `0x90d8` x2, `0xd812` x1, `0x90dc` x1, `0xdce0` x1, `0xd8e0` x1              | -                                                                      | `8636ecaed520` x131, `7e15398acc97` x121, `841742a3e15a` x99, `8f8e0add044c` x70  |
| `4037c8574920` | 39  | `0x70c0` x17, `0x7000` x15, `0x7080` x7                  | `0x409c` x2, `0x4000` x1, `0x8ac6` x1, `0x4091` x1, `0x0001` x1, `0x4093` x1 | `0x8ac6->0x4091`                                                       | `7e15398acc97` x15, `8d8c3b0a22a0` x12, `8f8e0add044c` x6, `8636ecaed520` x5      |
| `eec973076bac` | 27  | `0x70c0` x14, `0x7000` x9, `0x7080` x4                   | -                                                                            | -                                                                      | `7e15398acc97` x9, `8b2115cd509f` x9, `8636ecaed520` x5, `8f8e0add044c` x4        |
| `167b6d557116` | 3   | `0x7000` x2, `0x7080` x1                                 | `0x895e` x2, `0x891a` x1                                                     | -                                                                      | `5b46d4574b86` x2, `7e15398acc97` x1                                              |
| `5b46d4574b86` | 509 | `0x7080` x256, `0x7040` x253                             | -                                                                            | -                                                                      | `8f8e0add044c` x289, `d92154cb54aa` x177, `4037c8574920` x19, `eec973076bac` x13  |
| `20ea2ab16891` | 509 | `0x7140` x251, `0x7100` x136, `0x7180` x122              | `0x8a4c` x2, `0x4011` x2, `0x8a4d` x1, `0x4012` x1, `0x8a4e` x1, `0x4013` x1 | `0x8a4c->0x4011`, `0x8a4d->0x4012`, `0x8a4e->0x4013`                   | `841742a3e15a` x232, `99d4493dc4cf` x122, `8636ecaed520` x120, `8d8c3b0a22a0` x20 |
| `8636ecaed520` | 509 | `0x7180` x256, `0x7100` x253                             | `0x8988` x2, `0x8a3a` x1, `0x8a23` x1                                        | -                                                                      | `99d4493dc4cf` x256, `20ea2ab16891` x131, `841742a3e15a` x109, `8d8c3b0a22a0` x7  |
| `841742a3e15a` | 440 | `0x7140` x222, `0x7180` x119, `0x7100` x99               | `0x8627` x1, `0x90dc` x1, `0xdce0` x1, `0x90d8` x1, `0xd8e0` x1              | -                                                                      | `20ea2ab16891` x208, `99d4493dc4cf` x119, `8636ecaed520` x113                     |
| `8d8c3b0a22a0` | 39  | `0x7140` x21, `0x7100` x12, `0x7180` x6                  | `0x4099` x3, `0x8a4e` x1, `0x8a53` x1, `0x8a54` x1, `0x8a4d` x1, `0x8a4b` x1 | `0x4099->0x8a4e`, `0x4099->0x8a53`, `0x4099->0x8a54`                   | `20ea2ab16891` x19, `8636ecaed520` x14, `99d4493dc4cf` x6                         |
| `8b2115cd509f` | 27  | `0x7140` x13, `0x7100` x9, `0x7180` x5                   | `0x4762` x1, `0x4000` x1, `0x89a5` x1, `0x4091` x1, `0x0001` x1, `0x4093` x1 | `0x89a5->0x4091`                                                       | `20ea2ab16891` x13, `8636ecaed520` x9, `99d4493dc4cf` x5                          |
| `957d82183ebf` | 3   | `0x7140` x2, `0x7180` x1                                 | `0x8813` x2, `0x81fd` x1, `0x401b` x1                                        | -                                                                      | `20ea2ab16891` x2, `99d4493dc4cf` x1                                              |
| `99d4493dc4cf` | 509 | `0x71c0` x509                                            | `0x8857` x1, `0x885d` x1, `0x8858` x1, `0x885e` x1, `0x84af` x1, `0x885f` x1 | `0x8857->0x885d`, `0x8858->0x885e`, `0x84af->0x885f`, `0x84b0->0x8860` | `6c1b7a18ce27` x256, `b7a129b7d392` x253                                          |
| `6c1b7a18ce27` | 256 | `0x7200` x256                                            | `0x8a4b` x1, `0x8a53` x1, `0x4014` x1                                        | -                                                                      | -                                                                                 |
| `b7a129b7d392` | 253 | `0x7200` x253                                            | `0x885d` x1, `0x8811` x1, `0x885e` x1, `0x8812` x1, `0x885f` x1, `0x8814` x1 | `0x8811->0x885e`, `0x8812->0x885f`, `0x8814->0x8860`                   | -                                                                                 |

## Seed Chunk Hex

### `8f8e0add044c`

- observations: `509`
- offsets: `0x70c0` x222, `0x7080` x153, `0x7000` x134

```text
3407fee43dfde43cfc9085fd123430908a29e0c4540f30e011908a4ce0c3940e4008904011740ef080089085fee0904011f09085ffe0904012f0908600802e90
```

### `4037c8574920`

- observations: `39`
- offsets: `0x70c0` x17, `0x7000` x15, `0x7080` x7

```text
08eff6904000e020e7f9908ac6e0904091f0a87c0808e6a3f07b00a97c09097a00900001122fb7904093f090409c7440f07424f090409ce020e5f9904099e090
```

### `20ea2ab16891`

- observations: `509`
- offsets: `0x7140` x251, `0x7100` x136, `0x7180` x122

```text
8a29e0c4540f30e011908a4ce0c3940e4008904011740ef08008908a4ce0904011f0908a4de0904012f0908a4ee0904013f0908a50e0ffa3e078a9cff608eff6
```

### `8d8c3b0a22a0`

- observations: `39`
- offsets: `0x7140` x21, `0x7100` x12, `0x7180` x6

```text
8a4df0904099e0908a4ef0904099e0908a53f0904099e0908a54f0a87c08740426f618e436f6908a4de0b4fe028014908a4be0fea3e0ffa3e0fca3e0fdc39fec
```

### `8b2115cd509f`

- observations: `27`
- offsets: `0x7140` x13, `0x7100` x9, `0x7180` x5

```text
36f6904762e030e409e054eff0a87c087601904000e020e7f99089a5e0904091f0a87c0808e6a3f07b00a97c09097a00900001122fb7904093f0904098e0a87c
```

### `99d4493dc4cf`

- observations: `509`
- offsets: `0x71c0` x509

```text
f608760112efb6057c057c22908857e090885df0908858e090885ef09084afe090885ff09084b0e0908860f07b2a7df17f007e0b908859eef0a3eff090893ce0
```

### `b7a129b7d392`

- observations: `253`
- offsets: `0x7200` x253

```text
e054884efeef4ef07e007f08120a65e490885df0908811e090885ef0908812e090885ff0908814e0908860f07b027daa7f007e04120a6b2290898ee04401f090
```

## Interpretation

- The GET CONFIG-specific anchor is confined to one rotating chunk.
- The common `0x8a4c..0x8a4e -> 0x4011..0x4013` chunk is shared by all
  normal captures, so it is public response plumbing rather than a
  GET CONFIG-only oracle.
- The immediately preceding `0x4091/0x4093/0x409c/0x4099` chunk is the
  best concrete controller-read setup to reverse next.
- The adjacency graph is a safer guide than public slot order; the same
  chunk can appear before or after the seed depending on capture phase.

A likely linear path, when the `4037c8574920 -> 8d8c3b0a22a0 ->
20ea2ab16891` adjacency is present, is:

```text
wait for 0x4000.7 clear
xdata[0x8ac6] -> controller[0x4091]
IRAM/local pointer bytes -> controller[0x4092]
LCALL 0x2fb7 with DPTR=0x0001, result -> controller[0x4093]
controller[0x409c] = 0x40, then 0x24
wait for controller[0x409c].5 clear
read controller[0x4099] four times into 0x8a4d,0x8a4e,0x8a53,0x8a54
advance local byte count by four
if 0x8a4d == 0xfe, skip the dynamic length-difference calculation
copy/clamp 0x8a4c..0x8a4e into controller[0x4011..0x4013]
copy 0x8a50..0x8a51 into the IRAM 0xa9/0xaa length/state pair
```

That makes the cleanest current patch idea a response-builder redirect:
either alter the address material before the `0x4091..0x4093/0x409c`
kick, or replace the four bytes after the `0x4099` reads and before the
`0x4011..0x4013` public response setup. It still needs a safe normal-mode
patch foothold before it becomes a live oracle.
