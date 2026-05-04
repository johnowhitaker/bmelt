# Normal Response Matrix

This report captures standard read-only normal-mode command responses,
REQUEST SENSE after failures, and the public `READ BUFFER id=01`
work-window. The purpose is to find a host-controlled normal-mode
observation bit without touching CDD/F0 bytes.

## Run

- device: `/dev/sg0`
- timestamp UTC: `2026-05-04T17:19:10.428512+00:00`
- profile: `core`
- cycles: `3`
- sense mode: `on-failure`

## Commands

| name | profile | cdb | request | notes |
|---|---|---|---:|---|
| `baseline-test-unit-ready` | `core` | `00 00 00 00 00 00` | 0 | TEST UNIT READY |
| `getcfg-all-0000` | `core` | `46 00 00 00 00 00 00 00 FC 00` | 252 | GET CONFIGURATION rt=0 start_feature=0x0000 |
| `getcfg-current-0000` | `core` | `46 02 00 00 00 00 00 00 FC 00` | 252 | GET CONFIGURATION rt=2 start_feature=0x0000 |
| `getcfg-current-0000-len16` | `core` | `46 02 00 00 00 00 00 00 10 00` | 16 | GET CONFIGURATION rt=2 start_feature=0x0000 |
| `getcfg-current-0000-len64` | `core` | `46 02 00 00 00 00 00 00 40 00` | 64 | GET CONFIGURATION rt=2 start_feature=0x0000 |
| `getcfg-current-0001` | `core` | `46 02 00 01 00 00 00 00 FC 00` | 252 | GET CONFIGURATION rt=2 start_feature=0x0001 |
| `getcfg-current-0010` | `core` | `46 02 00 10 00 00 00 00 FC 00` | 252 | GET CONFIGURATION rt=2 start_feature=0x0010 |
| `getcfg-current-0020` | `core` | `46 02 00 20 00 00 00 00 FC 00` | 252 | GET CONFIGURATION rt=2 start_feature=0x0020 |
| `getcfg-current-0100` | `core` | `46 02 01 00 00 00 00 00 FC 00` | 252 | GET CONFIGURATION rt=2 start_feature=0x0100 |
| `getcfg-one-0000` | `core` | `46 01 00 00 00 00 00 00 FC 00` | 252 | GET CONFIGURATION rt=1 start_feature=0x0000 |
| `getevent-busy` | `core` | `4A 01 00 00 40 00 00 00 FC 00` | 252 | GET EVENT STATUS NOTIFICATION class=0x40 |
| `getevent-external` | `core` | `4A 01 00 00 04 00 00 00 FC 00` | 252 | GET EVENT STATUS NOTIFICATION class=0x04 |
| `getevent-media` | `core` | `4A 01 00 00 10 00 00 00 FC 00` | 252 | GET EVENT STATUS NOTIFICATION class=0x10 |
| `getevent-multihost` | `core` | `4A 01 00 00 20 00 00 00 FC 00` | 252 | GET EVENT STATUS NOTIFICATION class=0x20 |
| `getevent-operational` | `core` | `4A 01 00 00 01 00 00 00 FC 00` | 252 | GET EVENT STATUS NOTIFICATION class=0x01 |
| `getevent-power` | `core` | `4A 01 00 00 02 00 00 00 FC 00` | 252 | GET EVENT STATUS NOTIFICATION class=0x02 |
| `inquiry-extrainq-176` | `core` | `12 00 00 00 B0 40 00 00 00 00 00 00` | 176 | LiteOn EXTRAINQ-sized read |
| `inquiry-extrainq-240` | `core` | `12 00 00 00 F0 40 00 00 00 00 00 00` | 240 | LiteOn EXTRAINQ maximal read |
| `inquiry-standard-36` | `core` | `12 00 00 00 24 00` | 36 | standard INQUIRY |
| `inquiry-standard-96` | `core` | `12 00 00 00 60 00` | 96 | standard INQUIRY |
| `modesense-all` | `core` | `5A 00 3F 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x3f |
| `modesense-caching` | `core` | `5A 00 08 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x08 |
| `modesense-capabilities` | `core` | `5A 00 2A 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x2a |
| `modesense-cd-audio` | `core` | `5A 00 0E 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x0e |
| `modesense-cd-device` | `core` | `5A 00 0D 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x0d |
| `modesense-fault-failure` | `core` | `5A 00 1C 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x1c |
| `modesense-power` | `core` | `5A 00 1A 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x1a |
| `modesense-read-error` | `core` | `5A 00 01 00 00 00 00 00 FC 00` | 252 | MODE SENSE(10) page=0x01 |
| `request-sense` | `core` | `03 00 00 00 FC 00` | 252 | standard sense read |

## Response Stability

| command | response variants | top response | sense variants | window layouts |
|---|---:|---|---|---:|
| `baseline-test-unit-ready` | 1 | `empty` | `00/00/00` x3 | 2 |
| `getcfg-all-0000` | 1 | `ef4fbc3f6980` | - | 2 |
| `getcfg-current-0000` | 1 | `3f2298adc6ed` | - | 2 |
| `getcfg-current-0000-len16` | 1 | `44f1fee3c03d` | - | 1 |
| `getcfg-current-0000-len64` | 1 | `3f2298adc6ed` | - | 2 |
| `getcfg-current-0001` | 1 | `5415d6eda815` | - | 2 |
| `getcfg-current-0010` | 1 | `afeea43d7f88` | - | 3 |
| `getcfg-current-0020` | 1 | `9d095d24d858` | - | 2 |
| `getcfg-current-0100` | 1 | `39bacb767e0e` | - | 2 |
| `getcfg-one-0000` | 1 | `17c42afea436` | - | 3 |
| `getevent-busy` | 1 | `ddd1faf2c467` | - | 3 |
| `getevent-external` | 1 | `d570c65860bc` | - | 3 |
| `getevent-media` | 1 | `b321489fa116` | - | 3 |
| `getevent-multihost` | 1 | `67de05f5172e` | - | 3 |
| `getevent-operational` | 1 | `67de05f5172e` | - | 3 |
| `getevent-power` | 1 | `25b2ea65b069` | - | 3 |
| `inquiry-extrainq-176` | 1 | `077fe3994e56` | - | 2 |
| `inquiry-extrainq-240` | 1 | `077fe3994e56` | - | 2 |
| `inquiry-standard-36` | 1 | `0ee0c5976aa0` | - | 2 |
| `inquiry-standard-96` | 1 | `494fd1594d9d` | - | 2 |
| `modesense-all` | 1 | `17f2e6cb97b5` | - | 2 |
| `modesense-caching` | 1 | `ad6ad737bae6` | - | 2 |
| `modesense-capabilities` | 1 | `387e87799ddb` | - | 2 |
| `modesense-cd-audio` | 1 | `1bbc802cd056` | - | 2 |
| `modesense-cd-device` | 1 | `6393bfc79af9` | - | 2 |
| `modesense-fault-failure` | 1 | `empty` | `00/00/00` x3 | 2 |
| `modesense-power` | 1 | `3ef7fba3fd23` | - | 2 |
| `modesense-read-error` | 1 | `f94cadcc283b` | - | 2 |
| `request-sense` | 1 | `572aa2d495ba` | - | 2 |

## Interesting Window Layouts

### baseline-test-unit-ready
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-all-0000
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-current-0000
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-current-0000-len64
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-current-0001
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x70c0 rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-current-0010
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x7000 rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x7000 rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-current-0020
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x70c0 rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-current-0100
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getcfg-one-0000
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x70c0 rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getevent-busy
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getevent-external
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getevent-media
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getevent-multihost
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getevent-operational
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### getevent-power
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### inquiry-extrainq-176
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### inquiry-extrainq-240
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### inquiry-standard-36
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### inquiry-standard-96
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-all
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-caching
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-capabilities
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-cd-audio
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-cd-device
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7010 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-fault-failure
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-power
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### modesense-read-error
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

### request-sense
- x2: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x70d0 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`
- x1: `rec58-edge-a@- rec58-edge-b@- rec58-edge-c@- rec58-bridge-long@+0x7090 rec58b-ctrl-long@+0x738e rec60-a@- rec60-b@- rec60-c@- rec60-bridge-long@+0x7440`

## Raw Files

- JSON: `references/evidence/live/drive3-normal-response-matrix-core-repeat-20260504/summary.json`
