# Drive 3 Router CD-ROM Read-Only Probe

Date: 2026-05-04

Read-only normal-mode media-present run with the router software CD-ROM.

Highlights:

- `TEST UNIT READY` succeeds.
- READ CAPACITY(10): last LBA `0x8390`, block size `2048`.
- Current profile is CD-ROM `0x0008`.
- READ TOC formats `0`, `1`, and `2` succeed.
- READ(10) of sectors `0..16` succeeds.
- LBA 16 contains an ISO9660 `CD001` primary volume descriptor.
- A 64 KiB public `READ BUFFER id=01 offset=0x070000` snapshot after reading
  LBA 16 contains no targeted hits for the sector payload.
- Drive stayed `LD5M`.

Detailed interpretation:

```text
analysis/8051/drive3-router-cd-readonly-20260504.md
```
