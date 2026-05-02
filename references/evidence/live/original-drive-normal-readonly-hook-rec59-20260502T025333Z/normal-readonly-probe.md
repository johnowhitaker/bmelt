# Normal-Mode Read-Only SCSI Surface Probe

Date: 2026-05-02T02:53:49.906794+00:00

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
| `test-unit-ready` | `standard` | 2 | false | 0.010521s | 0 | `` `` |
| `request-sense` | `standard` | 0 | true | 0.005142s | 20 | `700000000000000a000000000000000000000000` `p...................` |
| `inquiry-standard-96` | `standard` | 0 | true | 0.007596s | 96 | `058000325b000000504c4453202020204456442b2d525720` `...2[...PLDS    DVD+-RW DS-8ABSHLD5M2016...` |
| `inquiry-vpd-supported` | `standard` | 5 | false | 0.008120s | 0 | `` `` |
| `inquiry-vpd-serial` | `standard` | 5 | false | 0.012502s | 0 | `` `` |
| `inquiry-vpd-device-id` | `standard` | 5 | false | 0.012373s | 0 | `` `` |
| `inquiry-extrainq` | `standard` | 0 | true | 0.008220s | 176 | `05800032ab000000504c4453202020204456442b2d525720` `...2....PLDS    DVD+-RW DS-8ABSHLD5M2016...` |
| `mode-sense6-all` | `standard` | 2 | false | 0.013009s | 0 | `` `` |
| `mode-sense6-cd-dvd-cap` | `standard` | 2 | false | 0.013558s | 0 | `` `` |
| `mode-sense10-all` | `standard` | 0 | true | 0.006019s | 224 | `00de700000000000010a0080000000000000000005324005` `..p..................2@....................` |
| `get-configuration-current` | `standard` | 0 | true | 0.008520s | 60 | `000000380000000000000330002b0000001b0000001a0000` `...8.......0.+.............................` |
| `get-configuration-all` | `standard` | 0 | true | 0.010914s | 252 | `000001540000000000000330002b0000001b0000001a0000` `...T.......0.+.............................` |
| `get-event-status-media` | `standard` | 0 | true | 0.007996s | 8 | `0006045e00000000` `...^....` |
| `read-toc-format-0` | `standard` | 2 | false | 0.013437s | 0 | `` `` |
| `read-disc-information` | `standard` | 2 | false | 0.013471s | 0 | `` `` |
| `read-track-information-lba0` | `standard` | 2 | false | 0.016836s | 0 | `` `` |
| `mechanism-status` | `standard` | 0 | true | 0.011220s | 8 | `0000000000000000` `........` |
| `read-dvd-structure-format0` | `standard` | 2 | false | 0.014030s | 0 | `` `` |
| `get-performance-nominal` | `standard` | 99 | false | 4.325405s | 0 | `` `` |

## Notes

- Nonzero `returncode` here usually means CHECK CONDITION/illegal request/no media,
  not necessarily a transport failure.
- If a future persistent hook needs a host-visible normal-mode trigger, prefer
  commands that return data quickly and consistently in this report.
- `READ BUFFER` probes are opt-in because normal-mode `id=02` has hung the
  optical LUN once and required a Pico servo power cycle.
