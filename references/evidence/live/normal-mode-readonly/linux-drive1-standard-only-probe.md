# Normal-Mode Read-Only SCSI Surface Probe

Date: 2026-04-30T21:09:40.908753+00:00

This probe sends only no-data-out status/inquiry/read-style CDBs. It is
intended to catalog host-visible normal LD5M response channels, not to
exercise updater or mechanics commands.

## Target

```text
host   jonathan-thinkpad-t480s
device /dev/sg0
```

## Results

| name | group | rc | good | elapsed | bytes | first bytes / ascii |
|---|---:|---:|---:|---:|---|
| `test-unit-ready` | `standard` | 2 | false | 0.004632s | 0 | `` `` |
| `request-sense` | `standard` | 0 | true | 0.004991s | 20 | `700000000000000a000000000000000000000000` `p...................` |
| `inquiry-standard-96` | `standard` | 0 | true | 0.007161s | 96 | `058000325b000000504c4453202020204456442b2d525720` `...2[...PLDS    DVD+-RW DS-8ABSHLD5M2016...` |
| `inquiry-vpd-supported` | `standard` | 5 | false | 0.012712s | 0 | `` `` |
| `inquiry-vpd-serial` | `standard` | 5 | false | 0.012754s | 0 | `` `` |
| `inquiry-vpd-device-id` | `standard` | 5 | false | 0.013116s | 0 | `` `` |
| `inquiry-extrainq` | `standard` | 0 | true | 0.008629s | 176 | `05800032ab000000504c4453202020204456442b2d525720` `...2....PLDS    DVD+-RW DS-8ABSHLD5M2016...` |
| `mode-sense6-all` | `standard` | 2 | false | 0.012985s | 0 | `` `` |
| `mode-sense6-cd-dvd-cap` | `standard` | 2 | false | 0.013066s | 0 | `` `` |
| `mode-sense10-all` | `standard` | 0 | true | 0.009130s | 224 | `00de700000000000010a0080000000000000000005324005` `..p..................2@....................` |
| `get-configuration-current` | `standard` | 0 | true | 0.008446s | 60 | `000000380000000000000330002b0000001b0000001a0000` `...8.......0.+.............................` |
| `get-configuration-all` | `standard` | 0 | true | 0.014008s | 252 | `000001540000000000000330002b0000001b0000001a0000` `...T.......0.+.............................` |
| `get-event-status-media` | `standard` | 0 | true | 0.010067s | 8 | `0006045e00000000` `...^....` |
| `read-toc-format-0` | `standard` | 2 | false | 0.014071s | 0 | `` `` |
| `read-disc-information` | `standard` | 2 | false | 0.010394s | 0 | `` `` |
| `read-track-information-lba0` | `standard` | 2 | false | 0.012705s | 0 | `` `` |
| `mechanism-status` | `standard` | 0 | true | 0.007455s | 8 | `0000000000000000` `........` |
| `read-dvd-structure-format0` | `standard` | 2 | false | 0.013400s | 0 | `` `` |
| `get-performance-nominal` | `standard` | 99 | false | 10.360608s | 0 | `` `` |

## Notes

- Nonzero `returncode` here usually means CHECK CONDITION/illegal request/no media,
  not necessarily a transport failure.
- If a future persistent hook needs a host-visible normal-mode trigger, prefer
  commands that return data quickly and consistently in this report.
- `GET PERFORMANCE` is not in that preferred set: it returned through
  `sg_raw` as `DID_TIME_OUT` after about ten seconds.
- `READ BUFFER` probes are opt-in because normal-mode `id=02` has hung the
  optical LUN once and required a Pico servo power cycle.
