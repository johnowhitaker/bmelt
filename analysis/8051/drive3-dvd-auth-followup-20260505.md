# Drive 3 Pressed DVD Auth Follow-Up

This follows `analysis/8051/drive3-movie-dvd-auth-20260505.md`.

Drive #3 is still a normal `PLDS DVD+-RW DS-8ABSH LD5M` target after the
additional tests. No firmware, CDD, region-setting, or media-write commands were
used in this follow-up.

## Harness updates

`scripts/normal_mailbox_probe.py dvd-auth` now has two useful fixes:

- run ids include microseconds, so fast repeated nonce runs do not overwrite
  each other;
- `--capture-step-windows` captures the public `READ BUFFER mode=1 id=1`
  work-window after each auth command.

`scripts/analyze_liteon_normal_packet_shadow.py` now accepts both historical
`*.window.bin` files and the mailbox harness' newer `*.work-window.bin` names.

## Nonce behavior

With the correct host-challenge-first sequence, the DVD CSS path behaves like a
real normal-mode host-input path:

| run | host challenge / nonce | key1 response | drive challenge response |
|---|---|---|---|
| `...034336247973Z` | `00010203040506070809` | `000a00001d846fede3000000` | `000e00001a244eedb218675e526f0000` |
| `...034336476593Z` | `10111213141516171819` | `000a000074eb0bcd88000000` | `000e0000cd6e7faa15c3f6cb96f10000` |
| `...034336556664Z` | `535445503157494e3032` | `000a000060b40e6789000000` | `000e0000573b2354a3d21df9b1900000` |
| `...034336637574Z` | `ffeeddccbbaa99887766` | `000a0000dd7def2713000000` | `000e0000ea4876e45930a9362ede0000` |

Repeating the same nonce gives the same key1 but a fresh drive challenge:

| run | host challenge / nonce | key1 response | drive challenge response |
|---|---|---|---|
| `...034352968391Z` | `535445503157494e3033` | `000a00005539c62770000000` | `000e0000114101b99b7b0ccef6d60000` |
| `...034353050854Z` | `535445503157494e3033` | `000a00005539c62770000000` | `000e00005324786402fac6173d1c0000` |
| `...034353132186Z` | `535445503157494e3033` | `000a00005539c62770000000` | `000e0000cfaf24cd8a7ad43653550000` |

Interpretation:

- the host challenge reaches real normal-mode auth logic;
- key1 is deterministic for a fixed host challenge and disc/session state;
- the drive challenge contains session/random material;
- this is useful bidirectional normal-mode I/O, even if it is not arbitrary
  memory I/O.

## Step-window captures

A 16 KiB step-window run interleaved public-window reads after every auth
command. Every step produced the same window hash and no nonce hit:

`263cdc891c2ab58e...`

That proves the interleaved `READ BUFFER` captures do not break the CSS command
sequence, but the narrow window does not expose the nonce.

A 64 KiB step-window run showed changing public-window phase/state across the
auth sequence, still with no exact nonce hit:

| phase | window hash prefix |
|---|---|
| after AGID | `c91d928c2b3e` |
| after ASF | `7a652cb818c7` |
| after RPC state | `7bc2be7543dc` |
| after SEND KEY host challenge | `606472fe8482` |
| after key1 | `e9a67c4091d4` |
| after drive challenge | `6c317fa7ad72` |
| after invalidate AGID | `bf79ab3f8d29` |

The selector analyzer report for this run is saved as:

- `analysis/8051/drive3-dvd-auth-step-selector-20260505.md`
- `analysis/8051/drive3-dvd-auth-step-selector-20260505.json`

## Selector island

The 64 KiB capture exposes a useful normal-runtime selector island at public
window offset `+0x91c2`. Disassembled as 8051, the head is:

```asm
mov  dptr,#0x8a49
movx a,@dptr
cjne a,#0xa4,not_report_key
mov  dptr,#0x8a53
movx a,@dptr
anl  a,#0x3f
mov  r7,a
cjne r7,#0x08,not_report_key
ljmp 0x6f62

not_report_key:
mov  dptr,#0x8a49
movx a,@dptr
cjne a,#0xa3,not_send_key
mov  dptr,#0x8a53
movx a,@dptr
anl  a,#0x3f
mov  r7,a
cjne r7,#0x06,not_send_key
ljmp 0x6f73
```

This is a concrete A3/A4 command-family dispatch, but it is not the host
challenge branch we exercised. It checks:

- `REPORT KEY` (`0xa4`) with low key format `0x08`, which is the read-only RPC
  state path we already use safely;
- `SEND KEY` (`0xa3`) with low key format `0x06`, which is very likely the RPC
  region-setting/write side. Treat that path as hazardous and do not probe it
  casually.

Extracted chunks and r2 disassembly are in:

`analysis/8051/dvd-auth-step-20260505/`

The first AGID window showed a different phase at `+0x91c0`; from the ASF step
onward, the A3/A4 selector island is stable at `+0x91c2`.

Important caveat: the public work-window is a tiled/rotating observation
surface, not a flat 8051 code-address map. The `LJMP 0x6f62` and `LJMP 0x6f73`
targets above are real code targets, but public offsets `+0x6f62` and
`+0x6f73` are not automatically those routines. The `public-offset-6f*.bin`
extracts in this directory are phase/context samples only, not confirmed branch
targets.

## Read-only REPORT KEY format scan

A read-only `REPORT KEY` format scan over `0x01..0x0f`, with AGID `3`, found
only these successful formats:

| key format | result |
|---:|---|
| `0x00` | AGID grant: `00060000000000c0` |
| `0x05` | ASF: `0006000000000000` |
| `0x08` | RPC state: `0006000064fe0100` |
| `0x3f` | AGID invalidation at end, GOOD/no data |

Notable failures:

- formats `0x01` and `0x02` return `Command sequence error` without a prior
  host challenge;
- format `0x04` returns `Copy protection key exchange failure - key not
  established`;
- format `0x06` as `REPORT KEY` is invalid, while the visible selector island's
  `SEND KEY` format `0x06` branch should be treated as a write/config path.

Evidence:

`references/evidence/live/drive3-dvd-report-key-scan-20260505T034858209881Z/`

## Practical read

This thread has produced a real normal-mode host/device exchange, but the auth
nonce and computed values appear to be consumed by CSS/controller internals
rather than being left in the public `0x070000` work-window.

The best next step is not broad CSS fuzzing. The safe next static/live target is
the visible `REPORT KEY format 8` selector path:

1. find the actual `0x6f62` branch body or its public-window tile, then map its
   state effects;
2. correlate those with repeated `REPORT KEY format 8` and ordinary
   command/window captures;
3. only after that, decide whether this read-only branch is a plausible normal
   hook site or simply a status updater.

Do not send `SEND KEY format 6` unless we intentionally want to risk touching
DVD region/RPC state.
