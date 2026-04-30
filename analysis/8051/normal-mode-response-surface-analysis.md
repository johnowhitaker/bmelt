# Normal-Mode Response Surface Analysis

Date: 2026-04-30

This is an offline comparison of the normal LD5M read-only command survey
against the known F0 image, the `0x070000` currentboot gateway dump,
and the captured currentboot XDATA dump.

## Summary

The normal drive has several fast host-visible response channels even with
no disc inserted: standard `INQUIRY`, vendor `EXTRAINQ`, `MODE SENSE(10)`,
`GET CONFIGURATION`, `GET EVENT STATUS`, and `MECHANISM STATUS`.
`GET PERFORMANCE` timed out and should not be used as a casual trigger.
`READ BUFFER id=02` is now excluded from the default survey because it hung
the optical LUN once and required a Pico servo power cycle.

The strongest response-source clue is paradoxical: normal `INQUIRY` and
`EXTRAINQ` contain long exact byte strings that also exist in two visible
F0 identity copies, but live edits to those copies did not affect normal
LD5M identity after cold boot. So exact F0 equality here means the normal
runtime uses the same template data, not necessarily that it reads those
specific flash offsets.

A second useful clue is that currentboot XDATA also contains partial
normal-response material: the model string appears at `xdata[0x811e]`,
`GET CONFIGURATION` feature bytes appear near `xdata[0x40a4]`, and a
`MODE SENSE(10)` fragment appears near `xdata[0x4e1b]`. These are not
yet proven normal-runtime sources, but they are better carryover/localizer
targets than another blind visible-F0 hook.

Follow-up live test: `xdata[0x811e] <- 0x58` read back correctly through
the guarded currentboot XDATA hook, but the next currentboot identity
response still returned canonical `DVD+-RW DS-8ABSH`; only the deliberate
hook readback byte changed. So `0x811e` is not the live currentboot
identity source.

## Command Surface

| command | rc | good | elapsed | bytes | sense / note |
|---|---:|---:|---:|---:|---|
| `test-unit-ready` | 2 | false | 0.004632s | 0 | Not Ready |
| `request-sense` | 0 | true | 0.004991s | 20 | SCSI Status: Good; Writing 20 bytes of data to stdout |
| `inquiry-standard-96` | 0 | true | 0.007161s | 96 | SCSI Status: Good; Writing 96 bytes of data to stdout |
| `inquiry-vpd-supported` | 5 | false | 0.012712s | 0 | Illegal Request |
| `inquiry-vpd-serial` | 5 | false | 0.012754s | 0 | Illegal Request |
| `inquiry-vpd-device-id` | 5 | false | 0.013116s | 0 | Illegal Request |
| `inquiry-extrainq` | 0 | true | 0.008629s | 176 | SCSI Status: Good; Writing 176 bytes of data to stdout |
| `mode-sense6-all` | 2 | false | 0.012985s | 0 | Not Ready |
| `mode-sense6-cd-dvd-cap` | 2 | false | 0.013066s | 0 | Not Ready |
| `mode-sense10-all` | 0 | true | 0.009130s | 224 | SCSI Status: Good; Writing 224 bytes of data to stdout |
| `get-configuration-current` | 0 | true | 0.008446s | 60 | SCSI Status: Good; Writing 60 bytes of data to stdout |
| `get-configuration-all` | 0 | true | 0.014008s | 252 | SCSI Status: Good; Writing 252 bytes of data to stdout |
| `get-event-status-media` | 0 | true | 0.010067s | 8 | SCSI Status: Good; Writing 8 bytes of data to stdout |
| `read-toc-format-0` | 2 | false | 0.014071s | 0 | Not Ready |
| `read-disc-information` | 2 | false | 0.010394s | 0 | Not Ready |
| `read-track-information-lba0` | 2 | false | 0.012705s | 0 | Not Ready |
| `mechanism-status` | 0 | true | 0.007455s | 8 | SCSI Status: Good; Writing 8 bytes of data to stdout |
| `read-dvd-structure-format0` | 2 | false | 0.013400s | 0 | Not Ready |
| `get-performance-nominal` | 99 | false | 10.360608s | 0 | >>> transport error: Host_status=0x03 [DID_TIME_OUT]; Driver_status=0x00 [DRIVER_OK] |

## Exact Matches

| command | target | response offset | target offset | len | sample |
|---|---|---:|---:|---:|---|
| `inquiry-standard-96` | F0 | `0x05` | `0xd8fd5` (identity/profile area) | `0x2b` | `000000504c4453202020204456442b2d` `...PLDS    DVD+-RW DS-8ABSHLD5M2016/10/1` |
| `inquiry-standard-96` | F0 | `0x05` | `0x04457` (lower/currentboot identity copy) | `0x1b` | `000000504c4453202020204456442b2d` `...PLDS    DVD+-RW DS-8ABSH` |
| `inquiry-standard-96` | currentboot XDATA | `0x10` | `0x0811e` (currentboot identity/key/model window) | `0x10` | `4456442b2d52572044532d3841425348` `DVD+-RW DS-8ABSH` |
| `inquiry-extrainq` | F0 | `0x6f` | `0x044c1` | `0x31` | `100120b4050000000000005fff01000f` `.. ........_............................` |
| `inquiry-extrainq` | F0 | `0x00` | `0xd8fd0` (identity/profile area) | `0x30` | `05800032ab000000504c445320202020` `...2....PLDS    DVD+-RW DS-8ABSHLD5M2016` |
| `inquiry-extrainq` | F0 | `0x00` | `0x04452` (lower/currentboot identity copy) | `0x20` | `05800032ab000000504c445320202020` `...2....PLDS    DVD+-RW DS-8ABSH` |
| `inquiry-extrainq` | currentboot XDATA | `0x10` | `0x0811e` (currentboot identity/key/model window) | `0x10` | `4456442b2d52572044532d3841425348` `DVD+-RW DS-8ABSH` |
| `inquiry-extrainq` | currentboot XDATA | `0xa0` | `0x08112` (currentboot identity/key/model window) | `0xc` | `314435302d3120204c44354d` `1D50-1  LD5M` |
| `get-configuration-all` | currentboot XDATA | `0x3c` | `0x040a4` | `0xd` | `00010b08000000070100000000` `.............` |

## Foothold Implications

For a host-visible normal-runtime PoC, the best triggers are now:

- `INQUIRY` / `EXTRAINQ`: fastest and richest responses, but the visible F0
  identity copies are known not to be the live normal source.
- `GET CONFIGURATION`: fast, returns structured feature data, and is likely
  handled by the real optical runtime rather than only by the bridge.
- `MODE SENSE(10)`: fast and returns a large response without media.
- `GET EVENT STATUS` and `MECHANISM STATUS`: small but likely close to
  runtime state machines.

The immediate next experiment should not be another visible-F0 prefix hook.
Better candidates are:

1. a currentboot-to-LD5M RAM carryover marker test using the currentboot
   XDATA write hook. Skip `xdata[0x811e]` as a live-template source; it
   is now tested negative. Better remaining markers are `xdata[0x40a4]`
   (GET CONFIG feature-list fragment) and `xdata[0x4e1b]` (MODE SENSE
   fragment), though both are lower-confidence because the matches are
   shorter and more structured;
2. a normal-mode standard-command source-localization pass, patching only
   already-proven restorable template bytes if a new candidate source is
   identified;
3. CDD/decoded-runtime work if we need to hook the actual normal command
   handlers rather than visible fallback/currentboot handlers.

