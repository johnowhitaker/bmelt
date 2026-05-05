# DVD Auth Report-Only Probe

Date: 2026-05-05

This was the first `scripts/normal_mailbox_probe.py dvd-auth` run with the
pressed movie DVD inserted.

Result:

- `REPORT KEY` CSS AGID: GOOD, AGID `3`.
- `REPORT KEY` ASF: GOOD.
- `REPORT KEY` RPC state: GOOD.
- The older harness then requested the drive challenge before sending a host
  challenge, and the drive returned `Illegal Request / Command sequence error`.
- AGID invalidation succeeded.
- Drive identity stayed `LD5M`.

Interpretation: the DVD unlocks the CSS authentication path, but the
challenge/key commands are sequence-sensitive. The harness was corrected after
this run.
