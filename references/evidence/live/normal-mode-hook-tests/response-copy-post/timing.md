# Normal-Mode Command Timing

Date: 2026-04-30T21:24:08.809665+00:00

## Target

```text
host   jonathan-thinkpad-t480s
device /dev/sg0
```

## Summary

| command | good | median | min | max | bytes | return codes |
|---|---:|---:|---:|---:|---:|---|
| `inquiry-standard-96` | true | 0.007003s | 0.004257s | 0.008886s | `96` | `0` |
| `inquiry-extrainq` | true | 0.007816s | 0.007465s | 0.011056s | `176` | `0` |
| `mode-sense10-all` | true | 0.008585s | 0.008067s | 0.010500s | `224` | `0` |
| `get-configuration-current` | true | 0.006887s | 0.005021s | 0.007763s | `60` | `0` |
| `get-configuration-all` | true | 0.010415s | 0.009793s | 0.014245s | `252` | `0` |
| `get-event-status-media` | true | 0.007574s | 0.007250s | 0.009382s | `8` | `0` |
| `mechanism-status` | true | 0.007562s | 0.004690s | 0.010144s | `8` | `0` |
