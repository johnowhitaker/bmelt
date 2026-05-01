# CDD DVD-Reuse Hypothesis Probes

Date: 2026-05-01

Offline only. No drive commands were sent.

This is a targeted follow-up to the hard-record size clue. ECMA-267
DVD recording frames are 2366 bytes, arranged as 13 rows of 182
bytes, with 10 PI Reed-Solomon parity bytes per row. The CDD hard
records often sit near that size, so this report tests the literal
DVD-frame interpretation before treating it as only a loose hardware
reuse clue.

Reference: <https://ecma-international.org/publications-and-standards/standards/Ecma-267/>

## DVD LFSR / Direct Known-Output Matches

For each known-output record, I tried raw source bytes, every possible
2366-byte frame window when present, simple row parity-column drops,
and the 16 ECMA DVD scrambler preset values. The score below is the
longest exact known-output byte sequence found in any transformed
candidate. Values at 4 bytes are random-level evidence; useful hits
would need to be much longer.

| record | source | known | distance to 2366 | best exact run | best candidate |
| --- | --- | --- | --- | --- | --- |
| 50 | 2499 | 432 | +133 | 0 | `none >= 4 bytes` |
| 51 | 2326 | 800 | -40 | 0 | `none >= 4 bytes` |
| 55 | 2313 | 768 | -53 | 0 | `none >= 4 bytes` |
| 58 | 2292 | 496 | -74 | 0 | `none >= 4 bytes` |
| 60 | 2344 | 624 | -22 | 0 | `none >= 4 bytes` |
| 62 | 2419 | 224 | +53 | 0 | `none >= 4 bytes` |
| 66 | 2411 | 704 | +45 | 0 | `none >= 4 bytes` |
| 67 | 2295 | 272 | -71 | 0 | `none >= 4 bytes` |
| 68 | 2421 | 528 | +55 | 4 | `frame+0x21:drop-pi-12x172 / dvd-lfsr-seed-0x0040` |
| 70 | 2525 | 448 | +159 | 4 | `frame+0x90:drop-pi-12x172 / dvd-lfsr-seed-0x5400` |
| 73 | 2355 | 192 | -11 | 0 | `none >= 4 bytes` |
| 86 | 2317 | 224 | -49 | 0 | `none >= 4 bytes` |
| 87 | 1947 | 896 | -419 | 0 | `none >= 4 bytes` |

## DVD PI Row-Parity Check

If a 2366-byte CDD source window were literally a DVD recording frame,
its 13 rows should satisfy the DVD PI RS(182,172) parity check. I tested
raw, byte-inverted, row-byte-reversed, and whole-frame-reversed windows.

| record | source | best valid PI rows | window | variant |
| --- | --- | --- | --- | --- |
| 50 | 2499 | 0 | 0x0 | `raw` |
| 51 | 2326 | 0 | n/a | `source-shorter-than-2366` |
| 55 | 2313 | 0 | n/a | `source-shorter-than-2366` |
| 58 | 2292 | 0 | n/a | `source-shorter-than-2366` |
| 60 | 2344 | 0 | n/a | `source-shorter-than-2366` |
| 62 | 2419 | 0 | 0x0 | `raw` |
| 66 | 2411 | 0 | 0x0 | `raw` |
| 67 | 2295 | 0 | n/a | `source-shorter-than-2366` |
| 68 | 2421 | 0 | 0x0 | `raw` |
| 70 | 2525 | 0 | 0x0 | `raw` |
| 73 | 2355 | 0 | n/a | `source-shorter-than-2366` |
| 86 | 2317 | 0 | n/a | `source-shorter-than-2366` |
| 87 | 1947 | 0 | n/a | `source-shorter-than-2366` |

## Current Read

- The source-length clue is real, but these records are not literal
  ECMA-267 DVD recording frames.
- DVD LFSR descrambling plus simple frame/row extraction does not reveal
  the known decoded 8051 bytes directly.
- No tested 2366-byte source window satisfies even one DVD PI row-parity
  check, so the standard DVD inner-code layout is not present verbatim.
- The better working model is now narrower: CDD may reuse DVD-like
  dimensions, scheduling, or controller ECC datapaths, but the hard
  record format is a custom controller codeword layer.

