# Normal-Mode Command Timing

Date: 2026-04-30T21:23:25.396137+00:00

## Target

```text
host   jonathan-thinkpad-t480s
device /dev/sg0
```

## Summary

| command | good | median | min | max | bytes | return codes |
|---|---:|---:|---:|---:|---:|---|
| `inquiry-standard-96` | true | 0.007160s | 0.004265s | 0.010091s | `96` | `0` |
| `inquiry-extrainq` | true | 0.007783s | 0.006482s | 0.010037s | `176` | `0` |
| `mode-sense10-all` | true | 0.008962s | 0.008540s | 0.012150s | `224` | `0` |
| `get-configuration-current` | true | 0.008364s | 0.008270s | 0.009163s | `60` | `0` |
| `get-configuration-all` | true | 0.009959s | 0.007832s | 0.010785s | `252` | `0` |
| `get-event-status-media` | true | 0.007974s | 0.007648s | 0.008198s | `8` | `0` |
| `mechanism-status` | true | 0.007750s | 0.007569s | 0.007954s | `8` | `0` |
