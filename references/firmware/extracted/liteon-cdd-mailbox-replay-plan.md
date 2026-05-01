# LiteOn CDD Mailbox Replay Plan

Scope: static only. This file is generated from a dumped 1 MiB F0 image and does not command a drive.

Image: `/Users/johno/projects/boastermelt/references/firmware/extracted/ld5m-f0-window-0x00000-0x100000.bin`

## Descriptor Fields Used By Resident Code

The CDD outer descriptor starts immediately before CDD1. The visible 8051 code at `0x12e0..0x13a0` and `0x4180..0x41de` uses the early descriptor fields before calling `FUN_CODE_002e`.

| field | value | resident use |
|---|---:|---|
| descriptor start | `0x07000` | length-prefixed descriptor |
| length | `0x002c` | added to parser base to locate CDD header |
| parser base | `0x00007000` | copied to `xdata[0x8244..0x8247]` |
| parser window | `0x00004000` | copied to `xdata[0x8248..0x824b]`; becomes `0x4e0d=0x40` |
| parser source size | `0x00080000` | copied to `xdata[0x824c..0x824f]`; gives `0x60..0x61=0x01ff` |
| parser target size | `0x00005000` | copied to `xdata[0x8250..0x8253]`; becomes `0x4e1a=0x14` |
| parser mode word | `0x4000` | copied to `xdata[0x8254..0x8255]`; gives `0x4e1c=0x01` |
| decoded start | `0x00184000` | advertised controller decoded range |
| decoded end exclusive | `0x001b4000` | advertised controller decoded range |

## CDD Header Package

CDD1 starts at `0x0702c`. After adding the descriptor length, the parser expects the header at `0x0000702c`.

| field | value | mailbox/register effect |
|---|---:|---|
| header byte `0x06` | `0x53` | `0x4a03=0x03`, `0x4a05=0x14` |
| CDD2 start | `0x0d9000` | `xdata[0x8258..0x825b]=0x000d9000` |
| controller params | `030810` | `xdata[0x4a20..0x4a22]` |
| aux length | `0x0400` | `0x4a01=3` |
| low param | `0x07` | `0x4a06=0x07` |
| decoded range | `0x184000..0x1b3fff` | expected decoded/controller object |

## Why The Doorbell-Only Test Was Too Small

The earlier live test wrote only `xdata[0x4a00]=1`. The resident parser does not do that in isolation. Before or around that doorbell it:

- validates descriptor fields and preloads `xdata[0x8244..0x8255]`;
- derives `0x4e0d`, `0x4e1a`, `0x4e1c`, and the `0x60..0x61` count from descriptor sizes;
- configures an XDATA mapped window at `0xc000` using the `0x4e80/0x4e84/0x4e88/0x4e8c` command path;
- verifies `CDD\x09 10 16` through that mapped window;
- then writes the `0x4a01/03/05/06/20/21/22` field package and rings `0x4a00`.

So `0x4a00=1` remains a useful negative for a trivial shortcut, but it does not prove the CDD engine cannot be started from currentboot.

## Candidate Replay Levels

### field-only CDD mailbox

Set only the header-derived 0x4a fields, then ring 0x4a00. This is the smallest useful successor to the failed single-byte doorbell test.

Expected if sufficient: decoded/controller memory near 0x184000 becomes nonzero or 0x4a24..0x4a29 updates.

Risk: low-to-medium; no 0x4e8c command issue, but it does ring the CDD mailbox.

Static writes/fields:

```json
{
  "0x4a00": 1,
  "0x4a01": 3,
  "0x4a02": 0,
  "0x4a03": 3,
  "0x4a05": 20,
  "0x4a06": 7,
  "0x4a20": 3,
  "0x4a21": 8,
  "0x4a22": 16,
  "0x8258..0x825b": 888832
}
```

### descriptor prestate plus field mailbox

Preload 0x8244..0x825b and the early 0x4e status fields to mirror the resident parser, then ring the 0x4a mailbox.

Expected if sufficient: same as above, plus 0x4e status fields should match resident assumptions.

Risk: medium; still avoids direct 0x4e8c transfer commands.

Static writes/fields:

```json
{
  "0x4a00": 1,
  "0x4a01": 3,
  "0x4a02": 0,
  "0x4a03": 3,
  "0x4a05": 20,
  "0x4a06": 7,
  "0x4a20": 3,
  "0x4a21": 8,
  "0x4a22": 16,
  "0x4e0d": 64,
  "0x4e1a": 20,
  "0x4e1c": 1,
  "0x60..0x61": 511,
  "0x8244..0x8247": 28672,
  "0x8248..0x824b": 16384,
  "0x824c..0x824f": 524288,
  "0x8250..0x8253": 20480,
  "0x8254..0x8255": 16384,
  "0x8258..0x825b": 888832
}
```

### mapped-header command path

Exercise the 0x4e80/84/88/8c path that normal code uses before it trusts xdata[0xc000] as a CDD header.

Expected if sufficient: xdata[0xc000..0xc01f] aliases or contains the CDD header, enabling the rest of the parser path.

Risk: high; this crosses into controller-memory command issuance, not just passive mailbox fields.

Static writes/fields:

```json
{
  "doorbell": "xdata[0x4e8c] = 1, then poll xdata[0x4ea0] == 0x06",
  "note": "0xc000 is not an F0 address. It is a mapped XDATA window; FUN_CODE_1717/FUN_CODE_16ef appear to configure that window before the parser reads CDD\\x09 from xdata[0xc000].",
  "purpose": "map/read the 0x20-byte CDD header into XDATA window 0xc000",
  "resident_range": "0x01ed..0x0252 then FUN_CODE_1717",
  "selector": 2,
  "xdata_0x4e80": 4223020,
  "xdata_0x4e84": 524032,
  "xdata_0x4e88": 32,
  "xdata_0x8244_after_descriptor_len": 28716,
  "xdata_0x8256..0x8257": 49152
}
```

## Practical Next Step

If we do this live, the next useful experiment is the first replay level: write the header-derived `0x4a` fields plus `xdata[0x8258..0x825b]`, then set `0x4a00=1`, then sample `0x4a24..0x4a29`, `0x4a26..0x4a27`, `0x4ea0`, and the decoded CDD addresses. That adds the missing field package without yet issuing the higher-risk `0x4e8c` mapped-header command.

Ordered byte writes for that field-only attempt:

| address | value | note |
|---:|---:|---|
| `0x4a00` | `0x00` | clear CDD mailbox doorbell before staging fields |
| `0x4a01` | `0x03` | aux length code from header[0x10] high nibble |
| `0x4a02` | `0x00` | resident clears this byte before field package |
| `0x4a03` | `0x03` | header[0x06] low two bits |
| `0x4a05` | `0x14` | header[0x06] upper six bits |
| `0x4a06` | `0x07` | header[0x10] low nibble |
| `0x4a20` | `0x03` | header[0x0d] controller parameter |
| `0x4a21` | `0x08` | header[0x0e] controller parameter |
| `0x4a22` | `0x10` | header[0x0f] controller parameter |
| `0x8258` | `0x00` | CDD2 absolute start from header[0x07..0x09] |
| `0x8259` | `0x0d` | CDD2 absolute start from header[0x07..0x09] byte +1 |
| `0x825a` | `0x90` | CDD2 absolute start from header[0x07..0x09] byte +2 |
| `0x825b` | `0x00` | CDD2 absolute start from header[0x07..0x09] byte +3 |
| `0x4a00` | `0x01` | ring CDD mailbox after staging fields |

Suggested samples afterward:

| kind | address | length | why |
|---|---:|---:|---|
| xdata | `0x4a00` | `0x30` | CDD mailbox/result window, including 0x4a24..0x4a29 |
| xdata | `0x4e00` | `0x30` | nearby 0x4e status fields and 0x4e14/16/18/1a/1c/1e |
| xdata | `0x4ea0` | `0x1` | cheap controller command status byte |
| gateway | `0x184000` | `0x100` | advertised decoded CDD base |
| gateway | `0x184060` | `0x100` | first table-derived decoded target neighborhood |
| gateway | `0x190690` | `0x100` | known affine group 27 oracle target from prior work |

