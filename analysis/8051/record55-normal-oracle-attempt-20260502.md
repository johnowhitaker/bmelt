# Record 55 Normal Oracle Attempt

This note captures the first live attempt to use record 55 as a normal-mode CDD
ownership oracle.

## Stock Baseline

Path:

```text
references/evidence/live/normal-oracle-record55-stock-20260502T022556Z/
```

The spare drive was recovered to normal `LD5M` before capture. The baseline
used read-only normal-mode work-window snapshots after:

- baseline/no stimulus;
- EXTRAINQ;
- MODE SENSE(10) all;
- GET CONFIGURATION current/all;
- GET PERFORMANCE type 00/type 04;
- READ TOC format 0 plus REQUEST SENSE.

The record-55 target was present and stable enough to use as an oracle:

| chunk/contig | hits | main offsets | notes |
|---|---:|---|---|
| `8853b78ca23e` | 48/48 | `+0x6ac0`, `+0x6a00`, `+0x6a80` | record 55, controller/FIFO loop |
| `95caa55b881e` | 45/48 | `+0x6b00`, `+0x6bc0`, `+0x6b40` | record 55, `0x48f4..0x48f6` area |
| `a87d03db223d` | 48/48 | `+0x6b40`, `+0x6bc0`, `+0x6b00`, `+0x6b80` | record 55 status/setup chunk |
| `25956f88a30e` | 48/48 | `+0x6c80`, `+0x6cc0` | record 55/56 packet-shadow chunk |
| `4f29221f2e51` | 32/48 | `+0x6cc0`, `+0x6c00`, `+0x6c80` | record 55/56 boundary chunk |
| contig 16 | 23/48 | mostly `+0x6c80` | record 55/56 |
| contig 21 | 21/48 | mostly `+0x6b00` | record 55-only |

Two rarer candidate chunks, `796c2cf9d837` and `86709485b961`, did not appear
in this stock set.

## Mutation

Candidate:

```text
runs/helper-bypass-candidates/record55-20260502/normal-oracle-rec55-plus400-5d-to-5c/
```

Patch:

```text
F0[0x2627a] 0x5d -> 0x5c
```

This is record 55 source-relative `+0x400`, chosen to mirror the earlier
record-59 `+0x400` ownership probe style.

Result evidence:

```text
references/evidence/live/normal-oracle-record55-5d-to-5c-20260502T022801Z/
```

Observed behavior:

- All arg00 chunk transfers and readback verifies succeeded.
- Final event 544 returned `DID_ERROR` / `rc=99`.
- Immediate identity after the sequence still returned normal `LD5M`.
- A later `sg_inq` hung.
- Pico servo power cuts and SCSI rescans brought back only the bridge's
  Generic SD/MMC LUN; the PLDS optical LUN did not reappear.

The `rc=99` final event is not by itself a failure signature, because the older
record-59 helper-bypass CDD perturbation also ended this way and still produced
normal-mode captures after cold boot. The differentiator is the missing optical
LUN after power cycling.

## Interpretation

Record 55 remains a good read-only target, but `F0[0x2627a]` is not a safe first
hard-lane mutation. It may be boot-critical CDD material, or it may place the
drive/bridge into a state that the servo power cut does not clear.

If the drive physically reappears as an optical LUN, restore stock before any
new live work. A restore candidate is prepared here:

```text
runs/helper-bypass-candidates/record55-restore-20260502/restore-rec55-0x2627a-stock-5d/
```

Next safer directions:

1. Prefer proven-safe record-59-style perturbations only when a restore path is
   immediately available.
2. For record 55, do not mutate another arbitrary hard-lane byte until we know
   whether this one is recoverable by physical replug.
3. If live work resumes on record 55, target a decoded tile/contig only after
   a better source-byte ownership model exists.
4. Use read-only record-55 captures as static evidence for packet/output-path
   mapping; the baseline already confirms its normal runtime visibility.
