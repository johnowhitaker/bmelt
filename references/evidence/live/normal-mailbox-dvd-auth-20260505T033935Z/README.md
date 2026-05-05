# DVD Auth Host-Challenge Probe

Date: 2026-05-05

This run used the corrected host-challenge-first CSS order.

Result:

- `REPORT KEY` CSS AGID: GOOD, AGID `3`.
- `REPORT KEY` ASF: GOOD.
- `REPORT KEY` RPC state: GOOD.
- `SEND KEY` host challenge: GOOD.
- `REPORT KEY` key1: GOOD, `000a00007e4bea0202000000`.
- `REPORT KEY` drive challenge: GOOD, `000e00007e2f16a7be83358bace60000`.
- AGID invalidation succeeded.
- Drive identity stayed `LD5M`.
- A 16 KiB public `READ BUFFER id=01 offset=0x070000` snapshot had no exact
  nonce hits.

Interpretation: this is a real normal-mode bidirectional MMC path, but not yet
a public-window leak.

Detailed interpretation:

```text
analysis/8051/drive3-movie-dvd-auth-20260505.md
```
