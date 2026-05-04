# Normal Response Matrix

This report captures standard read-only normal-mode command responses,
REQUEST SENSE after failures, and the public `READ BUFFER id=01`
work-window. The purpose is to find a host-controlled normal-mode
observation bit without touching CDD/F0 bytes.

## Run

- device: `/dev/sg0`
- timestamp UTC: `2026-05-04T17:22:38.073576+00:00`
- profile: `core`
- cycles: `12`
- shuffled per cycle: `True`
- shuffle seed: `61166`
- sense mode: `on-failure`

## Commands

| name | profile | cdb | request | notes |
|---|---|---|---:|---|
| `baseline-test-unit-ready` | `core` | `00 00 00 00 00 00` | 0 | TEST UNIT READY |
| `inquiry-standard-36` | `core` | `12 00 00 00 24 00` | 36 | standard INQUIRY |
| `modesense-cd-device` | `core` | `5A 00 0D 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x0d |

## Response Stability

| command | response variants | top response | sense variants | window layouts |
|---|---:|---|---|---:|
| `baseline-test-unit-ready` | 1 | `empty` | `00/00/00` x12 | 2 |
| `inquiry-standard-36` | 1 | `0ee0c5976aa0` | - | 2 |
| `modesense-cd-device` | 1 | `6393bfc79af9` | - | 2 |

## Interesting Window Layouts

### baseline-test-unit-ready
- x6: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7050 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x74c0`
- x6: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x74c0`

### inquiry-standard-36
- x7: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x74c0`
- x5: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7050 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x74c0`

### modesense-cd-device
- x7: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x74c0`
- x5: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7050 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x74c0`

## Raw Files

- JSON: `references/evidence/live/drive3-normal-response-matrix-modesense-cddevice-ab-20260504/summary.json`
