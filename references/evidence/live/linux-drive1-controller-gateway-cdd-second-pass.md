# Linux Drive 1 Controller-Gateway CDD Second Pass

Date: 2026-04-30.

Host: `jonathan-thinkpad-t480s`.

Drive target: `/dev/sg1`, active INQUIRY revision `LD5M`.

No F0 bytes were modified. These were GOOD/GOOD timing-channel helper reads
through the controller gateway path. Each bit run ended with recovery back to
`LD5M`.

## Command Shape

```sh
python3 scripts/read_liteon_xdata_timing_channel.py \
  --device /dev/sg1 \
  --space controller \
  --addr <addr> \
  --payload-offset 0x04f6 \
  --between-delay 3 \
  --retry-attempts 2 \
  --quiet-builder \
  --quiet-runner \
  --out-dir runs/cdd-controller-read-pass
```

The first address used `--calibrate`. The two follow-up addresses reused the
fresh threshold `0.556915`.

## Results

| controller address | value | notes |
|---:|---:|---|
| `0x184000` | `0x00` | descriptor decoded/controller range start |
| `0x18481c` | `0x00` | `0x184000 + LD5M CDD source pointer entry0 low word` |
| `0x19191a` | `0x00` | `0x184000 + LD5M CDD source pointer entry388 low word` |

All observed event-68 timings for data bits were short, about
`0.254..0.263s`, well below the threshold. The run therefore confirms zeros at
these addresses in the currentboot helper context.

## Interpretation

This reinforces the previous controller-gateway result: the timing primitive is
usable, but the normal decoded CDD/controller range does not appear populated or
directly exposed at the event-68 currentboot helper hook.

This does not disprove the `0x184000..0x1b4000` decoded-range interpretation in
the static CDD descriptor. It only says this particular helper/currentboot
context cannot see useful decoded CDD bytes there. A future runtime/resident
hook after normal LD5M boot is still the better live route.
