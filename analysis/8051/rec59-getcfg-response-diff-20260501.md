# Normal Response Diff Under CDD Perturbations

This is an offline check for a shortcut normal-mode side channel.
Instead of trying to interpret the rotating `READ BUFFER` work-window,
it asks whether any existing CDD perturbation changed an actual
host-visible SCSI response payload.

## Result

No reversible host-visible response payload changes were found in
the existing captures. The CDD edits clearly perturb the normal
work-window, but the captured command responses stayed stable or
the experiment lacked complete stock/mutated/restored states.

## Experiments

### rec59-getcfg

| State | Path | Response files | Stimuli | Stable stimuli |
|---|---|---:|---:|---:|
| `mutated` | `references/evidence/live/rec59-getcfg-response-diff/mutated` | 24 | 3 | 3 |
| `stock` | `references/evidence/live/rec59-getcfg-response-diff/stock` | 24 | 3 | 3 |

| Stimulus | State summary |
|---|---|
| `r5-0f-current-sf0000` | mutated: 1 variant(s), top `3f2298adc6ed` x8; stock: 1 variant(s), top `3f2298adc6ed` x8 |
| `r5-f0-current-sf0000` | mutated: 1 variant(s), top `3f2298adc6ed` x8; stock: 1 variant(s), top `3f2298adc6ed` x8 |
| `std-current-sf0000-len00fc` | mutated: 1 variant(s), top `3f2298adc6ed` x8; stock: 1 variant(s), top `3f2298adc6ed` x8 |

## Interpretation

A positive result here would have been very useful: it would mean we
could use ordinary SCSI responses as a normal-mode code/logic oracle.
The negative result does not reduce the importance of the CDD
perturbations. It just says the existing mutations landed in runtime
work tiles rather than in the specific response path we captured.

The next shortcut is to rank CDD records whose affected tiles sit near
response-handling contigs, then test those as targeted perturbations.
