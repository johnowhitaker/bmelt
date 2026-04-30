# Normal-Mode Command Timing

Date: 2026-04-30T21:35:10.534578+00:00

## Target

```text
host   jonathan-thinkpad-t480s
device /dev/sg0
```

## Summary

| command | good | median | min | max | bytes | return codes |
|---|---:|---:|---:|---:|---:|---|
| `inquiry-standard-96` | true | 0.004221s | 0.004186s | 0.004531s | `96` | `0` |
| `inquiry-extrainq` | true | 0.006053s | 0.004932s | 0.007597s | `176` | `0` |
| `mode-sense10-all` | true | 0.009213s | 0.008899s | 0.011472s | `224` | `0` |
| `get-configuration-current` | true | 0.008039s | 0.007857s | 0.010437s | `60` | `0` |
| `get-configuration-all` | true | 0.009947s | 0.009883s | 0.011385s | `252` | `0` |
| `get-event-status-media` | true | 0.007645s | 0.007595s | 0.009010s | `8` | `0` |
| `mechanism-status` | true | 0.007247s | 0.006930s | 0.007350s | `8` | `0` |
