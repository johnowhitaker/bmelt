# Drive 3 Router CD-ROM Read-Only Probe

Date: 2026-05-04

Media: router software CD-ROM inserted by hand.

Scope: read-only normal-mode media-present probes. No firmware-update events,
no `MODE SELECT`, no media writes, no tray/eject commands, and no CDD edits.

Evidence:

```text
references/evidence/live/drive3-router-cd-readonly-corrected-20260504T205514Z/
references/evidence/live/normal-mailbox-dvd-auth-20260504T205538Z/
```

## Result

The disc is recognized as readable CD-ROM media.

`TEST UNIT READY` succeeds, and REQUEST SENSE reports no current error:

```text
70 00 00 ... 00 00
```

READ CAPACITY(10):

```text
last_lba = 0x00008390  # 33680
block_size = 0x00000800  # 2048
total_bytes = 68,978,688
```

GET CONFIGURATION current profile reports CD-ROM profile `0x0008` as current:

```text
00 00 00 38 00 00 00 08 ...
```

READ TOC works for formats `0`, `1`, and `2`. Format `4` returns the expected
`Illegal Request / Invalid field in CDB` for this media/drive state.

READ DISC INFORMATION succeeds. READ TRACK INFORMATION by LBA 0 with the CDB
used here returns `Illegal Request / Invalid field in CDB`; this should be
treated as a command-shape issue, not a media failure.

The drive stayed `LD5M` after all probes.

## Sector Read

Reading the first 17 sectors with READ(10) succeeded:

```text
sha256=20547fcfeb05e10b7f3d58b7b74c6cddee179f421fe3ed3a784e5b9067b30af2
```

Sector 16 is a normal ISO9660 primary volume descriptor:

```text
01 43 44 30 30 31 01 00 57 49 4e 33 32 ...
   C  D  0  0  1       W  I  N  3  2
```

Visible strings include:

```text
CD001
WIN32
CD503A3
ULTRAISO V8.6 CD & DVD CREATOR, (C) 2006 EZB SYSTEMS, INC.
ULTRAISO
8.6.1.1982
```

A direct one-sector READ(10) of LBA 16 also succeeded:

```text
sha256=571834e35a96d628b6e03820b66a92cade3f768175dcd684b95effd55a786561
```

## Public Window Search

After reading LBA 16, a `READ BUFFER mode=1 id=01 offset=0x070000 length=0x10000`
snapshot was captured:

```text
sha256=398b0bc8026b9c87e8af23b1ef3020eb092d8a9111a1eb7b96fd291559174629
```

No exact or targeted fragment hits were found for the LBA 16 payload, including
`CD001`, `WIN32`, `CD503A3`, or `ULTRAISO`.

Conclusion: the public normal work-window does not simply expose the last
READ(10) user-sector buffer at the sampled offset/range. The CD is useful for
media-present command-path experiments, but it is not an immediate host-data
mailbox through this window.

## REPORT KEY With CD Media

The normal DVD-auth harness was rerun with the CD inserted:

```text
references/evidence/live/normal-mailbox-dvd-auth-20260504T205538Z/
```

Result:

```text
REPORT KEY CSS AGID: Illegal Request / Cannot read medium - incompatible format
REPORT KEY CSS ASF:  Illegal Request / Cannot read medium - incompatible format
REPORT KEY RPC:      GOOD, 8-byte response
AGID:                none
nonce hit:           false
identity stable:     true
```

This differs from the no-media result in the expected way: the command now
reaches a media-aware incompatibility check rather than `Medium not present`.
It does not unlock the CSS challenge path. A pressed DVD is still needed for
the real `REPORT KEY` / `SEND KEY` nonce experiment.

## Practical Read

What the router CD gives us now:

- a safe media-present baseline;
- real CD-ROM read/status paths;
- useful READ TOC / READ CAPACITY / READ(10) command traffic;
- a non-sensitive disc we can use for read-only packet/selector studies.

What it does not give us:

- DVD CSS `REPORT KEY` / `SEND KEY` authentication;
- a visible public-window copy of recently read sector payload;
- a writeable media path.

Recommended next steps:

1. Keep the router CD for read-only media-present command-path mapping.
2. Order a cheap pressed DVD for the CSS/DVD-auth mailbox path.
3. Order DVD+RW or DVD-RW media for later sacrificial sector-write/buffer-flow
   experiments.
4. In parallel, continue static/localization work around the volatile
   `MODE SELECT` page `0x08` bit and normal response construction paths.
