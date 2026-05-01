# Normal Work-Window Stimulus Analysis

Capture directory: `references/evidence/live/normal-work-window-capture-only-20260501`

## Captures

| index | name | sha256 | diff vs baseline | largest diff run |
|---:|---|---|---:|---:|
| 0 | `00-capture-only` | `d06ea8eaf23fcb87` | 0 | `0x0` |
| 1 | `01-capture-only` | `4797a96f5cb96890` | 561 | `0x80` |
| 2 | `02-capture-only` | `ea9c9094c752dcb2` | 1130 | `0x90` |
| 3 | `03-capture-only` | `166bef5d496c8245` | 1129 | `0x90` |
| 4 | `04-capture-only` | `06bfdaa1afdcb673` | 1130 | `0x90` |
| 5 | `05-capture-only` | `7a7d368177d2473b` | 1134 | `0x90` |
| 6 | `06-capture-only` | `b0b408954e99efb3` | 1129 | `0x90` |
| 7 | `07-capture-only` | `695d5c9b339eea25` | 1070 | `0x90` |
| 8 | `08-capture-only` | `9337b074eb637390` | 1067 | `0x90` |
| 9 | `09-capture-only` | `e190b51102b898eb` | 1130 | `0x90` |
| 10 | `10-capture-only` | `0404ffcc333a884b` | 1130 | `0x90` |
| 11 | `11-capture-only` | `bb3a4205fc91e297` | 1068 | `0x9b` |
| 12 | `12-capture-only` | `3dc679ebb0ba870f` | 1062 | `0x90` |
| 13 | `13-capture-only` | `7d7a7e0d50744d1e` | 1069 | `0x90` |

## Variable Pages

| page | variable bytes |
|---:|---:|
| `+0x6000` | 256 |
| `+0x9500` | 256 |
| `+0x8600` | 191 |
| `+0x6100` | 190 |
| `+0x8700` | 186 |
| `+0x9e00` | 64 |
| `+0x9900` | 63 |
| `+0x9a00` | 63 |

## Variable Runs

- `+0x6000..+0x6100` len `0x100`
- `+0x6140..+0x61d0` len `0x90`
- `+0x61d1..+0x61e9` len `0x18`
- `+0x61ea..+0x6200` len `0x16`
- `+0x8640..+0x8681` len `0x41`
- `+0x8682..+0x8710` len `0x8e`
- `+0x8711..+0x8713` len `0x2`
- `+0x8715..+0x8740` len `0x2b`
- `+0x8780..+0x8793` len `0x13`
- `+0x8794..+0x87ba` len `0x26`
- `+0x87bb..+0x87d3` len `0x18`
- `+0x87d4..+0x8800` len `0x2c`
- `+0x9500..+0x9600` len `0x100`
- `+0x99c0..+0x99c9` len `0x9`
- `+0x99ca..+0x9a00` len `0x36`
- `+0x9a80..+0x9aa5` len `0x25`
- `+0x9aa6..+0x9ac0` len `0x1a`
- `+0x9e80..+0x9ec0` len `0x40`

## Moving Tile Inventory

Chunk size: `0x40`
Informative unique chunks: 704
Chunks seen more than once: 702
Chunks seen at multiple offsets: 20

| index | name | informative chunks | new vs baseline |
|---:|---|---:|---:|
| 0 | `00-capture-only` | 699 | 0 |
| 1 | `01-capture-only` | 699 | 4 |
| 2 | `02-capture-only` | 699 | 5 |
| 3 | `03-capture-only` | 699 | 4 |
| 4 | `04-capture-only` | 699 | 5 |
| 5 | `05-capture-only` | 699 | 3 |
| 6 | `06-capture-only` | 699 | 4 |
| 7 | `07-capture-only` | 699 | 3 |
| 8 | `08-capture-only` | 699 | 4 |
| 9 | `09-capture-only` | 699 | 4 |
| 10 | `10-capture-only` | 699 | 3 |
| 11 | `11-capture-only` | 699 | 2 |
| 12 | `12-capture-only` | 699 | 3 |
| 13 | `13-capture-only` | 699 | 3 |

Top moving chunks:

- `1886905164886340` observed 28 times in 14 captures at `+0xff00`, `+0xff80`; sample `434444091016530d9000007dec030810`
- `19cf1f0ab9c1fac8` observed 14 times in 14 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `e60997ff18e61997fee57c2405f9c3ef`
- `0c705773105c535a` observed 14 times in 14 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `ec38fc908996123430800be490896af0`
- `602f0151f661bc5c` observed 14 times in 14 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `83eef090855ee004f080c5908ca5e0ff`
- `8bf0e900d2ceae35` observed 14 times in 14 captures at `+0x6140`, `+0x61c0`; sample `89fd7408f012f76c2039030260d29089`
- `01d84480073eed3d` observed 14 times in 14 captures at `+0x6140`, `+0x6180`; sample `922e9082dfe030e00e90841fe06005e0`
- `6c4f90652e56f086` observed 14 times in 14 captures at `+0x6180`, `+0x61c0`; sample `47c5e09089c8f09047c4e09089c9f090`
- `f52b132a1a9679b1` observed 14 times in 14 captures at `+0x8640`, `+0x8680`; sample `a2e0b4020e908ebde024fff0908ebce0`
- `e586bd150939defc` observed 14 times in 14 captures at `+0x8640`, `+0x86c0`; sample `07908a23e04402f0e57c2409f57c2220`
- `06ba20adffeda02c` observed 14 times in 14 captures at `+0x8680`, `+0x86c0`; sample `20e00c908a51e07004a3e06002d25122`
- `ec0b96cc1dec61e0` observed 14 times in 14 captures at `+0x8700`, `+0x8780`; sample `02063302063978a976eb08761402711d`
- `d21d30cf6e6b65b0` observed 14 times in 14 captures at `+0x8700`, `+0x87c0`; sample `12f2a022908844eff090825be030e627`
- `ccd665edc6156d36` observed 14 times in 14 captures at `+0x8780`, `+0x87c0`; sample `7be06003025bf3025be5908937e07003`
- `3e8bf4421828f024` observed 14 times in 14 captures at `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0`; sample `e0908c87f07f0412014a7df17faf123d`
- `d441a6b6013cacd4` observed 14 times in 14 captures at `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0`; sample `3ae0c41313540320e003025f2f203e03`
- `2111cafaf69c3db5` observed 14 times in 14 captures at `+0x9540`, `+0x9580`, `+0x95c0`; sample `47b1e0908a4cf09047b1e0908a4df090`
- `d602ae9aefb0b2e2` observed 10 times in 10 captures at `+0x9500`, `+0x9540`, `+0x9580`, `+0x95c0`; sample `908d44e0feef4ed082d083f0904806c0`
- `486eefd5d1b741b6` observed 8 times in 8 captures at `+0x6000`, `+0x6040`, `+0x6080`; sample `8f5f8d60859067904e05e054fef07f05`
- `8abb923850ed71bb` observed 6 times in 6 captures at `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`; sample `809840351207235030908124e030e029`
- `cd1041a057e9566c` observed 4 times in 4 captures at `+0x9500`, `+0x9540`, `+0x9580`; sample `7ff9123d89e4fd7f40123d89e4908a33`
