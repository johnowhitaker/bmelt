# DVD Auth Harness With CD-ROM Inserted

Date: 2026-05-04

Reran `scripts/normal_mailbox_probe.py dvd-auth` while the router CD-ROM was
inserted.

Result:

- `REPORT KEY` CSS AGID: `Illegal Request / Cannot read medium - incompatible format`.
- `REPORT KEY` CSS ASF: same.
- `REPORT KEY` RPC state: GOOD, 8-byte response.
- No AGID was granted.
- No nonce was sent or observed.
- Drive identity stayed `LD5M`.

Interpretation: CD media changes the failure from "medium not present" to
"incompatible format", but it does not exercise the DVD CSS challenge path. Use
a pressed DVD for the real `REPORT KEY` / `SEND KEY` mailbox test.
