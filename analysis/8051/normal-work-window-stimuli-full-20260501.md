# Normal Work-Window Stimulus Analysis

Capture directory: `references/evidence/live/normal-work-window-stimuli-full-20260501`

## Captures

| index | name | sha256 | diff vs baseline | largest diff run |
|---:|---|---|---:|---:|
| 0 | `00-baseline-no-stimulus` | `6f7b0943fc985c24` | 0 | `0x0` |
| 1 | `01-test-unit-ready` | `2f4fbef2e2881bd9` | 2186 | `0xbe` |
| 2 | `02-request-sense` | `bc3733efe18a8845` | 2124 | `0xbe` |
| 3 | `03-inquiry-standard-96` | `a7e5feaa8805ad5d` | 2182 | `0xbe` |
| 4 | `04-inquiry-extrainq` | `1b01d8d62091d272` | 3696 | `0xbe` |
| 5 | `05-mode-sense10-all` | `0ba9c8061fda6b5d` | 4891 | `0xad` |
| 6 | `06-get-configuration-current` | `915c028c1fac8490` | 5017 | `0xc0` |
| 7 | `07-get-configuration-all` | `3c9ac61ba470f060` | 5204 | `0xd0` |
| 8 | `08-get-event-status-media` | `981b08099f21efef` | 5323 | `0xc0` |
| 9 | `09-read-toc-format-0` | `8e266cf6673ce9c4` | 5136 | `0xc0` |
| 10 | `10-read-disc-information` | `9a13077eebceb4a1` | 4940 | `0xc0` |
| 11 | `11-read-track-information-lba0` | `97d20dc7ec812439` | 5318 | `0xc0` |
| 12 | `12-mechanism-status` | `dab89d32c1938bdc` | 5386 | `0xc0` |
| 13 | `13-read-dvd-structure-format0` | `364b1f39d1f67999` | 5075 | `0xc0` |

## Variable Pages

| page | variable bytes |
|---:|---:|
| `+0x6000` | 256 |
| `+0x6100` | 256 |
| `+0x8600` | 256 |
| `+0x8700` | 256 |
| `+0x9500` | 256 |
| `+0x6b00` | 254 |
| `+0x6f00` | 254 |
| `+0x9f00` | 254 |
| `+0x9800` | 253 |
| `+0x6600` | 192 |
| `+0x7400` | 192 |
| `+0x7f00` | 192 |
| `+0x8b00` | 192 |
| `+0x9300` | 192 |
| `+0x9a00` | 192 |
| `+0x6400` | 191 |
| `+0x9400` | 190 |
| `+0x7e00` | 189 |
| `+0x6a00` | 188 |
| `+0x8100` | 188 |
| `+0x6500` | 128 |
| `+0x8500` | 128 |
| `+0x9900` | 128 |
| `+0x9e00` | 128 |
| `+0x7100` | 127 |
| `+0x8300` | 127 |
| `+0x7500` | 126 |
| `+0x7000` | 125 |
| `+0x9200` | 124 |
| `+0x9d00` | 124 |
| `+0x6200` | 64 |
| `+0x6c00` | 64 |

## Variable Runs

- `+0x02b2..+0x02b5` len `0x3`
- `+0x02b7..+0x02b8` len `0x1`
- `+0x6000..+0x6200` len `0x200`
- `+0x6240..+0x6280` len `0x40`
- `+0x6300..+0x632b` len `0x2b`
- `+0x632c..+0x6340` len `0x14`
- `+0x6440..+0x64d5` len `0x95`
- `+0x64d6..+0x6540` len `0x6a`
- `+0x65c0..+0x6600` len `0x40`
- `+0x6640..+0x6700` len `0xc0`
- `+0x69c0..+0x69f3` len `0x33`
- `+0x69f4..+0x6a01` len `0xd`
- `+0x6a03..+0x6a1f` len `0x1c`
- `+0x6a20..+0x6a76` len `0x56`
- `+0x6a77..+0x6a80` len `0x9`
- `+0x6ac0..+0x6b46` len `0x86`
- `+0x6b47..+0x6bc6` len `0x7f`
- `+0x6bc7..+0x6c00` len `0x39`
- `+0x6c40..+0x6c80` len `0x40`
- `+0x6ec0..+0x6f43` len `0x83`
- `+0x6f44..+0x6f52` len `0xe`
- `+0x6f53..+0x7000` len `0xad`
- `+0x7080..+0x708b` len `0xb`
- `+0x708c..+0x70a2` len `0x16`
- `+0x70a3..+0x70ac` len `0x9`
- `+0x70ad..+0x7100` len `0x53`
- `+0x7140..+0x716e` len `0x2e`
- `+0x716f..+0x71c0` len `0x51`
- `+0x7280..+0x72bd` len `0x3d`
- `+0x72be..+0x72c0` len `0x2`
- `+0x7440..+0x7500` len `0xc0`
- `+0x7580..+0x7593` len `0x13`
- `+0x7594..+0x75ab` len `0x17`
- `+0x75ac..+0x7600` len `0x54`
- `+0x7e00..+0x7e1a` len `0x1a`
- `+0x7e1b..+0x7e43` len `0x28`
- `+0x7e44..+0x7e4f` len `0xb`
- `+0x7e50..+0x7e80` len `0x30`
- `+0x7ec0..+0x7f00` len `0x40`
- `+0x7f40..+0x8000` len `0xc0`
- `+0x8080..+0x80c0` len `0x40`
- `+0x8100..+0x8138` len `0x38`
- `+0x8139..+0x814e` len `0x15`
- `+0x814f..+0x8180` len `0x31`
- `+0x81c0..+0x81e9` len `0x29`
- `+0x81eb..+0x8200` len `0x15`
- `+0x8240..+0x8264` len `0x24`
- `+0x8266..+0x8267` len `0x1`
- `+0x8268..+0x826c` len `0x4`
- `+0x826e..+0x8273` len `0x5`
- `+0x8274..+0x8280` len `0xc`
- `+0x8300..+0x8340` len `0x40`
- `+0x8380..+0x8398` len `0x18`
- `+0x8399..+0x83c0` len `0x27`
- `+0x8400..+0x8440` len `0x40`
- `+0x8580..+0x8800` len `0x280`
- `+0x8b00..+0x8b80` len `0x80`
- `+0x8bc0..+0x8c00` len `0x40`
- `+0x8cc0..+0x8ccc` len `0xc`
- `+0x8ccd..+0x8d00` len `0x33`
- `+0x9040..+0x9079` len `0x39`
- `+0x907a..+0x9080` len `0x6`
- `+0x9180..+0x91c0` len `0x40`
- `+0x9200..+0x9207` len `0x7`
- `+0x9208..+0x9222` len `0x1a`
- `+0x9223..+0x9247` len `0x24`
- `+0x9248..+0x9262` len `0x1a`
- `+0x9263..+0x9280` len `0x1d`
- `+0x9300..+0x9380` len `0x80`
- `+0x93c0..+0x946b` len `0xab`
- `+0x946c..+0x9486` len `0x1a`
- `+0x9487..+0x94c0` len `0x39`
- `+0x9500..+0x9600` len `0x100`
- `+0x9800..+0x9813` len `0x13`
- `+0x9814..+0x9816` len `0x2`
- `+0x9817..+0x986d` len `0x56`
- `+0x986e..+0x9900` len `0x92`
- `+0x9940..+0x9980` len `0x40`
- `+0x99c0..+0x9a80` len `0xc0`
- `+0x9ac0..+0x9b00` len `0x40`

## Moving Tile Inventory

Chunk size: `0x40`
Informative unique chunks: 752
Chunks seen more than once: 740
Chunks seen at multiple offsets: 89

| index | name | informative chunks | new vs baseline |
|---:|---|---:|---:|
| 0 | `00-baseline-no-stimulus` | 699 | 0 |
| 1 | `01-test-unit-ready` | 699 | 8 |
| 2 | `02-request-sense` | 699 | 5 |
| 3 | `03-inquiry-standard-96` | 699 | 8 |
| 4 | `04-inquiry-extrainq` | 699 | 17 |
| 5 | `05-mode-sense10-all` | 699 | 23 |
| 6 | `06-get-configuration-current` | 699 | 26 |
| 7 | `07-get-configuration-all` | 699 | 28 |
| 8 | `08-get-event-status-media` | 699 | 24 |
| 9 | `09-read-toc-format-0` | 699 | 17 |
| 10 | `10-read-disc-information` | 699 | 18 |
| 11 | `11-read-track-information-lba0` | 699 | 18 |
| 12 | `12-mechanism-status` | 699 | 20 |
| 13 | `13-read-dvd-structure-format0` | 699 | 23 |

Top moving chunks:

- `1886905164886340` observed 28 times in 14 captures at `+0xff00`, `+0xff80`; sample `434444091016530d9000007dec030810`
- `602f0151f661bc5c` observed 14 times in 14 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `83eef090855ee004f080c5908ca5e0ff`
- `19cf1f0ab9c1fac8` observed 14 times in 14 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `e60997ff18e61997fee57c2405f9c3ef`
- `0c705773105c535a` observed 14 times in 14 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `ec38fc908996123430800be490896af0`
- `01d84480073eed3d` observed 14 times in 14 captures at `+0x6100`, `+0x6140`, `+0x6180`, `+0x61c0`; sample `922e9082dfe030e00e90841fe06005e0`
- `0c7ad71c6007f9e4` observed 14 times in 14 captures at `+0x6100`, `+0x6180`; sample `fef01205afd2411205b5c24112038190`
- `8bf0e900d2ceae35` observed 14 times in 14 captures at `+0x6140`, `+0x6180`, `+0x61c0`; sample `89fd7408f012f76c2039030260d29089`
- `6c4f90652e56f086` observed 14 times in 14 captures at `+0x6140`, `+0x6180`, `+0x61c0`; sample `47c5e09089c8f09047c4e09089c9f090`
- `2eed30eee3d0d93c` observed 14 times in 14 captures at `+0x6440`, `+0x64c0`; sample `6ee054f8301f054402f080034403f012`
- `9e7ab96c98381b97` observed 14 times in 14 captures at `+0x6640`, `+0x66c0`; sample `8029e57c2404f8e6c394184007e57c24`
- `6037190cb4bc9fd9` observed 14 times in 14 captures at `+0x6a00`, `+0x6a40`; sample `fc08e6f5828c83eff0905503e030e1f9`
- `f349733d2f3c5817` observed 14 times in 14 captures at `+0x6a00`, `+0x6ac0`; sample `0808e624f8602724fe602c24fa603824`
- `2958d3bbf5db423b` observed 14 times in 14 captures at `+0x6a40`, `+0x6ac0`; sample `943fa87c402cee1313543fffe4f608ef`
- `d71c07c7fcd6f06d` observed 14 times in 14 captures at `+0x6b00`, `+0x6b80`; sample `c7e0b4a1069047c07404f010490302c3`
- `a87d03db223d165c` observed 14 times in 14 captures at `+0x6b40`, `+0x6bc0`; sample `900001122fb7904835f0ef4440904834`
- `4f7ce11fed12844c` observed 14 times in 14 captures at `+0x6b40`, `+0x6b80`, `+0x6bc0`; sample `b1e04402f022908db1e04404f022908d`
- `7bcf95762bd048e4` observed 14 times in 14 captures at `+0x6f00`, `+0x6fc0`; sample `642a600ee064aa6009e064286004e0b4`
- `a41108260d665003` observed 14 times in 14 captures at `+0x6f40`, `+0x6f80`; sample `ff36f68020a87ce8c0e07e047f241230`
- `5fb5a8bf8f9adbbb` observed 14 times in 14 captures at `+0x6f80`, `+0x6fc0`; sample `9081f5e0ff908672e0fe6f6015908c84`
- `8f8e0add044ccff6` observed 14 times in 14 captures at `+0x7080`, `+0x70c0`; sample `3407fee43dfde43cfc9085fd12343090`
- `20ea2ab16891b5c7` observed 14 times in 14 captures at `+0x7140`, `+0x7180`; sample `8a29e0c4540f30e011908a4ce0c3940e`
- `404045e0e63cf82b` observed 14 times in 14 captures at `+0x7f40`, `+0x7f80`, `+0x7fc0`; sample `b404077d007f041205439048237480f0`
- `22c3f9325ca88af0` observed 14 times in 14 captures at `+0x8100`, `+0x81c0`; sample `78b3e61846601508e6540f700f06e618`
- `305ea7ee70e08354` observed 14 times in 14 captures at `+0x8100`, `+0x8140`; sample `70fa904a1de070fa904a40e0fca3e078`
- `0ee20a0462ac5d2d` observed 14 times in 14 captures at `+0x8140`, `+0x81c0`; sample `0ee0fca3e0fd7f5b1208b5908672e090`
- `06ba20adffeda02c` observed 14 times in 14 captures at `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`; sample `20e00c908a51e07004a3e06002d25122`
- `f52b132a1a9679b1` observed 14 times in 14 captures at `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`; sample `a2e0b4020e908ebde024fff0908ebce0`
- `e586bd150939defc` observed 14 times in 14 captures at `+0x8600`, `+0x8640`, `+0x8680`, `+0x86c0`; sample `07908a23e04402f0e57c2409f57c2220`
- `60a76d91539c247b` observed 14 times in 14 captures at `+0x8600`, `+0x8640`, `+0x86c0`; sample `e04408f09047047408f0e4f090474ce5`
- `ccd665edc6156d36` observed 14 times in 14 captures at `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`; sample `7be06003025bf3025be5908937e07003`
- `d21d30cf6e6b65b0` observed 14 times in 14 captures at `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`; sample `12f2a022908844eff090825be030e627`
- `fb00deab088bdb7e` observed 14 times in 14 captures at `+0x8700`, `+0x8740`, `+0x8780`, `+0x87c0`; sample `e0904091f0a3e55ef0a3e55ff0904000`
