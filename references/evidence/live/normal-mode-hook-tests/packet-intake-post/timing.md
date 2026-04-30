# Normal-Mode Command Timing

Date: 2026-04-30T21:32:51.703390+00:00

## Target

```text
host   jonathan-thinkpad-t480s
device /dev/sg0
```

## Summary

| command | good | median | min | max | bytes | return codes |
|---|---:|---:|---:|---:|---:|---|
| `inquiry-standard-96` | true | 0.005213s | 0.004671s | 0.006725s | `96` | `0` |
| `inquiry-extrainq` | true | 0.008033s | 0.007719s | 0.009451s | `176` | `0` |
| `mode-sense10-all` | true | 0.008723s | 0.008113s | 0.009052s | `224` | `0` |
| `get-configuration-current` | true | 0.007850s | 0.005519s | 0.008178s | `60` | `0` |
| `get-configuration-all` | true | 0.010605s | 0.010138s | 0.011677s | `252` | `0` |
| `get-event-status-media` | true | 0.007529s | 0.007213s | 0.009367s | `8` | `0` |
| `mechanism-status` | true | 0.007303s | 0.007246s | 0.010437s | `8` | `0` |
