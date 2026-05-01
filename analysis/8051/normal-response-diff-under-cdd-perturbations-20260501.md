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

### contig68

| State | Path | Response files | Stimuli | Stable stimuli |
|---|---|---:|---:|---:|
| `mutated` | `runs/contig68-ownership/mutated-captures` | 12 | 1 | 1 |
| `restored` | `runs/contig68-ownership/restored-captures` | 12 | 1 | 1 |
| `stock` | `runs/contig68-ownership/stock-before` | 8 | 1 | 1 |

| Stimulus | State summary |
|---|---|
| `get-performance-type00` | mutated: 1 variant(s), top `e3b0c44298fc` x12; restored: 1 variant(s), top `e3b0c44298fc` x12; stock: 1 variant(s), top `e3b0c44298fc` x8 |

### contig8

| State | Path | Response files | Stimuli | Stable stimuli |
|---|---|---:|---:|---:|
| `base_cold` | `runs/contig8-rec57-ownership/base-readback-cold-captures` | 12 | 1 | 1 |
| `mutated` | `runs/contig8-rec57-ownership/mutated-captures` | 12 | 1 | 1 |
| `prefix_restored` | `runs/contig8-rec57-ownership/prefix-restored-cold-captures` | 12 | 1 | 1 |
| `restored` | `runs/contig8-rec57-ownership/restored-captures` | 12 | 1 | 1 |
| `restored_cold` | `runs/contig8-rec57-ownership/restored-captures-cold` | 8 | 1 | 1 |

| Stimulus | State summary |
|---|---|
| `get-performance-type00` | base_cold: 1 variant(s), top `e3b0c44298fc` x12; mutated: 1 variant(s), top `e3b0c44298fc` x12; prefix_restored: 1 variant(s), top `e3b0c44298fc` x12; restored: 1 variant(s), top `e3b0c44298fc` x12; restored_cold: 1 variant(s), top `e3b0c44298fc` x8 |

### contig15

| State | Path | Response files | Stimuli | Stable stimuli |
|---|---|---:|---:|---:|
| `mutated` | `runs/contig15-rec70-ownership/mutated-captures` | 12 | 1 | 1 |

| Stimulus | State summary |
|---|---|
| `get-performance-type00` | mutated: 1 variant(s), top `e3b0c44298fc` x12 |

## Interpretation

A positive result here would have been very useful: it would mean we
could use ordinary SCSI responses as a normal-mode code/logic oracle.
The negative result does not reduce the importance of the CDD
perturbations. It just says the existing mutations landed in runtime
work tiles rather than in the specific response path we captured.

The next shortcut is to rank CDD records whose affected tiles sit near
response-handling contigs, then test those as targeted perturbations.
