# Normal Response Matrix

This report captures standard read-only normal-mode command responses,
REQUEST SENSE after failures, and the public `READ BUFFER id=01`
work-window. The purpose is to find a host-controlled normal-mode
observation bit without touching CDD/F0 bytes.

## Run

- device: `/dev/sg0`
- timestamp UTC: `2026-05-04T17:26:16.735751+00:00`
- profile: `disc`
- cycles: `1`
- shuffled per cycle: `False`
- shuffle seed: `49374`
- sense mode: `on-failure`

## Commands

| name | profile | cdb | request | notes |
|---|---|---|---:|---|
| `mechanism-status` | `disc` | `BD 00 00 00 00 00 00 00 00 FC 00 00` | 252 |  |
| `read-disc-information` | `disc` | `51 00 00 00 00 00 00 00 FC 00` | 252 |  |
| `read-format-capacities` | `disc` | `23 00 00 00 00 00 00 00 FC 00` | 252 |  |
| `read-track-information-lba0` | `disc` | `52 01 00 00 00 00 00 00 FC 00` | 252 |  |
| `readdvdstruct-format-0` | `disc` | `AD 00 00 00 00 00 00 00 00 FC 00 00` | 252 | READ DVD STRUCTURE format=0x00 |
| `readdvdstruct-format-1` | `disc` | `AD 00 00 00 00 00 00 01 00 FC 00 00` | 252 | READ DVD STRUCTURE format=0x01 |
| `readdvdstruct-format-2` | `disc` | `AD 00 00 00 00 00 00 02 00 FC 00 00` | 252 | READ DVD STRUCTURE format=0x02 |
| `readdvdstruct-format-ff` | `disc` | `AD 00 00 00 00 00 00 FF 00 FC 00 00` | 252 | READ DVD STRUCTURE format=0xff |
| `readtoc-format-0` | `disc` | `43 00 00 00 00 00 00 00 FC 00` | 252 | READ TOC/PMA/ATIP format=0x00 |
| `readtoc-format-1` | `disc` | `43 00 01 00 00 00 00 00 FC 00` | 252 | READ TOC/PMA/ATIP format=0x01 |
| `readtoc-format-2` | `disc` | `43 00 02 00 00 00 00 00 FC 00` | 252 | READ TOC/PMA/ATIP format=0x02 |
| `readtoc-format-4` | `disc` | `43 00 04 00 00 00 00 00 FC 00` | 252 | READ TOC/PMA/ATIP format=0x04 |

## Response Stability

| command | response variants | top response | sense variants | window layouts |
|---|---:|---|---|---:|
| `mechanism-status` | 1 | `af5570f5a181` | - | 1 |
| `read-disc-information` | 1 | `empty` | `00/00/00` x1 | 1 |
| `read-format-capacities` | 1 | `ef5fea7e6e14` | - | 1 |
| `read-track-information-lba0` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readdvdstruct-format-0` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readdvdstruct-format-1` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readdvdstruct-format-2` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readdvdstruct-format-ff` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readtoc-format-0` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readtoc-format-1` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readtoc-format-2` | 1 | `empty` | `00/00/00` x1 | 1 |
| `readtoc-format-4` | 1 | `empty` | `00/00/00` x1 | 1 |

## Interesting Window Layouts

## Raw Files

- JSON: `references/evidence/live/drive3-normal-response-matrix-disc-status-20260504/summary.json`
