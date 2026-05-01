# CDD Affine Group 105 Live Diff

This report compares normal-mode `READ BUFFER id=01/02 offset=0x070000`
captures after reversible edits to CDD stream 2 affine group 105. The
known stock semantic byte is `0x84`; the two live edits rewrote all 12
observed affine lead cells so the group decodes as `0x85` and `0x8b`.

The work-window is a rotating tile surface, so the useful rows are those
that are stable inside each state and return to the same value after the
stock restore.

## Summary

Chunk size: `0x40`
Common stable offsets across all four states: 997
Clean reversible offsets: 62
Noisy mutation-sensitive offsets: 61

| state | captures | stable offsets | path |
|---|---:|---:|---|
| `stock_before` | 8 | 1006 | `runs/cdd-affine-g105-restore-live/repeats-restored` |
| `mut_85` | 8 | 1002 | `runs/cdd-affine-g105-live/repeats-mutated` |
| `mut_8b` | 8 | 1015 | `runs/cdd-affine-g105-8b-live/repeats-mutated` |
| `stock_after` | 8 | 1007 | `runs/cdd-affine-g105-restore-after-8b-live/repeats-restored` |

## Interpretation

- The CDD affine edit is persistable and reversible: stock F0 verification
  returned to byte-identical LD5M after the restore.
- The normal work-window does react, but much of the reaction is tile-phase
  movement rather than a direct decoded-byte oracle.
- The clean rows below are the strongest live evidence that this CDD leaf
  participates in normal runtime state, but they should be treated as
  public-window effects, not as a direct decoded CDD dump.

## Clean Reversible Offsets

| offset | mut85 diffs | mut8b diffs | stock head | mut85 head | mut8b head |
|---:|---:|---:|---|---|---|
| `0x01c0` | 0 | 1 | `aff1760700d70000aff115082d05aff1` | `aff1760700d70000aff115082d05aff1` | `aff1760700d70000aff115082d05aff1` |
| `0x0280` | 3 | 41 | `006baff1760700d700c8aff115082d05` | `0071aff1760700d700c8aff115082d05` | `15082d05aff1510c006baff1760700d7` |
| `0x6140` | 0 | 61 | `fef01205afd2411205b5c24112038190` | `fef01205afd2411205b5c24112038190` | `47c5e09089c8f09047c4e09089c9f090` |
| `0x6480` | 63 | 62 | `18ef2430ffe43402fe1202f19042b5ef` | `d378aae6940418e694004020e49089a4` | `6ee054f8301f054402f080034403f012` |
| `0x65c0` | 63 | 63 | `700c9047cbf09047c97450f0805278b5` | `0214f090851fe004f0908523e004f090` | `0214f090851fe004f0908523e004f090` |
| `0x6ac0` | 63 | 63 | `98e54cf0904000e020e7f9904098e54d` | `943fa87c402cee1313543fffe4f608ef` | `fc08e6f5828c83eff0905503e030e1f9` |
| `0x6b00` | 0 | 64 | `c7e0b4a1069047c07404f010490302c3` | `c7e0b4a1069047c07404f010490302c3` | `007e02120b079085efe09048f4f09085` |
| `0x6b40` | 58 | 64 | `007e02120b079085efe09048f4f09085` | `b1e04402f022908db1e04404f022908d` | `c7e0b4a1069047c07404f010490302c3` |
| `0x6bc0` | 58 | 0 | `b1e04402f022908db1e04404f022908d` | `007e02120b079085efe09048f4f09085` | `b1e04402f022908db1e04404f022908d` |
| `0x6d80` | 0 | 64 | `10af01c3c0d0157c157ca87cecf608ed` | `10af01c3c0d0157c157ca87cecf608ed` | `d0157ca87ceff6157c157c90825be020` |
| `0x6ec0` | 0 | 64 | `a3e0f9a3e0faa3e02fffea3efeed39fd` | `a3e0f9a3e0faa3e02fffea3efeed39fd` | `e01a90837de07014a87ce6ff7b00a97c` |
| `0x7000` | 0 | 64 | `3407fee43dfde43cfc9085fd12343090` | `3407fee43dfde43cfc9085fd12343090` | `6401704b90893de030e0447f0012050d` |
| `0x7080` | 62 | 62 | `6401704b90893de030e0447f0012050d` | `cbefcbd0e0ffd0e0fed0e0fdd0e0fcc3` | `cbefcbd0e0ffd0e0fed0e0fdd0e0fcc3` |
| `0x7140` | 63 | 0 | `8a29e0c4540f30e011908a4ce0c3940e` | `3311700302a55c908627e0fca3e0fda3` | `8a29e0c4540f30e011908a4ce0c3940e` |
| `0x7180` | 63 | 0 | `3311700302a55c908627e0fca3e0fda3` | `8a29e0c4540f30e011908a4ce0c3940e` | `3311700302a55c908627e0fca3e0fda3` |
| `0x7440` | 0 | 64 | `80034402f09087bce09057cbf022d310` | `80034402f09087bce09057cbf022d310` | `f0905498e05411f09087aee0908224f0` |
| `0x7580` | 0 | 62 | `503fa87c0808e6fe08e6ffe4fcfd908a` | `503fa87c0808e6fe08e6ffe4fcfd908a` | `a3e060030276b4908a4ff0a87ce6fe08` |
| `0x7640` | 0 | 64 | `3090891ce0fea3e0a87c08080826f618` | `3090891ce0fea3e0a87c08080826f618` | `1ce03403f543904095eff0a3e543f0a3` |
| `0x77c0` | 0 | 63 | `e020e7f9904098e0a87cf6904000e020` | `e020e7f9904098e0a87cf6904000e020` | `7405f0905495e04444f090807ce0ff90` |
| `0x7800` | 62 | 0 | `301c55908e3ae0604fef6403704a908e` | `e04404f07f0212036912dbb1400c9089` | `301c55908e3ae0604fef6403704a908e` |
| `0x78c0` | 62 | 0 | `e04404f07f0212036912dbb1400c9089` | `301c55908e3ae0604fef6403704a908e` | `e04404f07f0212036912dbb1400c9089` |
| `0x7900` | 0 | 62 | `00500302c6f67e1d7f381203c3cceecc` | `00500302c6f67e1d7f381203c3cceecc` | `9085f4e0ff6012908970e0feefc39e50` |
| `0x7a00` | 0 | 64 | `8a4fe0bf01054410f0800354eff0908a` | `8a4fe0bf01054410f0800354eff0908a` | `7f101202f79089a47402f0908938e0ff` |
| `0x7e40` | 0 | 64 | `8571e5a8f075a890203e06204f03303f` | `8571e5a8f075a890203e06204f03303f` | `5d7401f0a37470f07b0c7df37f007e08` |
| `0x80c0` | 0 | 61 | `e02fffea3efeed39fdec38fc90895e12` | `e02fffea3efeed39fdec38fc90895e12` | `7f501204e322d310af01c3c0d0e4fffe` |
| `0x8100` | 0 | 64 | `e0ff90549af0905480eff0905495e054` | `e0ff90549af0905480eff0905495e054` | `78b3e61846601508e6540f700f06e618` |
| `0x8240` | 0 | 63 | `e436f69047d7e054fef0908a4fe09047` | `e436f69047d7e054fef0908a4fe09047` | `7e01ef70b27f5080ae904762e9f09049` |
| `0x82c0` | 0 | 63 | `7e01ef70b27f5080ae904762e9f09049` | `7e01ef70b27f5080ae904762e9f09049` | `e436f69047d7e054fef0908a4fe09047` |
| `0x8300` | 0 | 64 | `596ac39089d1e094b89089d0e0940b50` | `596ac39089d1e094b89089d0e0940b50` | `e478b0f622e490855ff090855e04f060` |
| `0x8340` | 0 | 63 | `51e09408908a50e094005006e4f608f6` | `51e09408908a50e094005006e4f608f6` | `596ac39089d1e094b89089d0e0940b50` |
| `0x8380` | 0 | 64 | `e478b0f622e490855ff090855e04f060` | `e478b0f622e490855ff090855e04f060` | `12014a9085f1e0fea3e0ffee4f24ff22` |
| `0x83c0` | 0 | 63 | `12014a9085f1e0fea3e0ffee4f24ff22` | `12014a9085f1e0fea3e0ffee4f24ff22` | `51e09408908a50e094005006e4f608f6` |
| `0x8400` | 0 | 61 | `862cf090596ae090862df0905906e090` | `862cf090596ae090862df0905906e090` | `8a4df0908a4de0ffc3941250157d00ef` |
| `0x8440` | 0 | 61 | `8a4df0908a4de0ffc3941250157d00ef` | `8a4df0908a4de0ffc3941250157d00ef` | `b43c13908a14e004f07006908a13e004` |
| `0x8480` | 0 | 63 | `cdeae57c2404f57cd0d092af22303e03` | `cdeae57c2404f57cd0d092af22303e03` | `862cf090596ae090862df0905906e090` |
| `0x84c0` | 0 | 64 | `b43c13908a14e004f07006908a13e004` | `b43c13908a14e004f07006908a13e004` | `cdeae57c2404f57cd0d092af22303e03` |
| `0x8500` | 0 | 63 | `30e054df904863f0908631e054fd9048` | `30e054df904863f0908631e054fd9048` | `e0c3943c500ae004f0e4908974f0a3f0` |
| `0x8580` | 0 | 61 | `7ccff0a3eff008e6ff08e6a3cff0a3ef` | `7ccff0a3eff008e6ff08e6a3cff0a3ef` | `30e054df904863f0908631e054fd9048` |
| `0x85c0` | 0 | 59 | `e0c3943c500ae004f0e4908974f0a3f0` | `e0c3943c500ae004f0e4908974f0a3f0` | `7ccff0a3eff008e6ff08e6a3cff0a3ef` |
| `0x8c40` | 64 | 0 | `f0905905e054fef0905a01e054faf07e` | `8a34e0ff131313541f30e003025bf390` | `f0905905e054fef0905a01e054faf07e` |
| `0x8d00` | 0 | 62 | `3400f0e0fea3e0ff12cdeee57c2405f5` | `3400f0e0fea3e0ff12cdeee57c2405f5` | `7be06003025bf3025bf0908920e06077` |
| `0x8d80` | 0 | 64 | `7be06003025bf3025bf0908920e06077` | `7be06003025bf3025bf0908920e06077` | `ef600f78b5760678ab7628e478b0f602` |
| `0x8dc0` | 0 | 63 | `ef600f78b5760678ab7628e478b0f602` | `ef600f78b5760678ab7628e478b0f602` | `3400f0e0fea3e0ff12cdeee57c2405f5` |
| `0x8f40` | 0 | 63 | `894bf0a3f0802c202f0790412fe030e7` | `894bf0a3f0802c202f0790412fe030e7` | `fccdefcd7e007fab12efc07c017dfc7e` |
| `0x8f80` | 0 | 60 | `a02290825be030e61aef7f20b4010812` | `a02290825be030e61aef7f20b4010812` | `894bf0a3f0802c202f0790412fe030e7` |
| `0x8fc0` | 0 | 62 | `fccdefcd7e007fab12efc07c017dfc7e` | `fccdefcd7e007fab12efc07c017dfc7e` | `a02290825be030e61aef7f20b4010812` |
| `0x9000` | 0 | 64 | `071d3048139081ffe0ffc413540730e0` | `071d3048139081ffe0ffc413540730e0` | `b57c007ded7f221208b5905a287488f0` |
| `0x9040` | 0 | 63 | `7fce1208bb7c007d007e007fcf1208bb` | `7fce1208bb7c007d007e007fcf1208bb` | `9055c6e04430f0908243e0c4540f30e0` |
| `0x9080` | 0 | 59 | `9055c6e04430f0908243e0c4540f30e0` | `9055c6e04430f0908243e0c4540f30e0` | `071d3048139081ffe0ffc413540730e0` |
| `0x90c0` | 0 | 64 | `b57c007ded7f221208b5905a287488f0` | `b57c007ded7f221208b5905a287488f0` | `7fce1208bb7c007d007e007fcf1208bb` |
| `0x9300` | 64 | 0 | `08e6540c700302dd61904806e0549ff0` | `5a017418f02290549fe0332290848ee0` | `08e6540c700302dd61904806e0549ff0` |
| `0x9380` | 62 | 62 | `71905a01e04405f0905905e04401f0e0` | `08e6540c700302dd61904806e0549ff0` | `5a017418f02290549fe0332290848ee0` |
| `0x9840` | 0 | 64 | `90869de04480f090869de0fea3e0ff22` | `90869de04480f090869de0fea3e0ff22` | `04f8e6fe08e6ffe4fcfdfb7a80f9f8d3` |
| `0x98c0` | 0 | 62 | `9435ee940040149089f7e004f090893a` | `9435ee940040149089f7e004f090893a` | `90869de04480f090869de0fea3e0ff22` |
| `0x9980` | 63 | 61 | `02bf3790852ee014f0e0700302bf4790` | `9dffee9c908988f0a3eff0908a49e0b4` | `b403079048e7740ff0229048e7740ff0` |
| `0x9b00` | 61 | 61 | `30e6617f5f1208d990855ceff0908355` | `a9e6a3f008e6a3f0d251e57c2406f57c` | `a9e6a3f008e6a3f0d251e57c2406f57c` |
| `0x9b40` | 63 | 61 | `a9e6a3f008e6a3f0d251e57c2406f57c` | `ee9084908016e490849af090825be054` | `30e6617f5f1208d990855ceff0908355` |
| `0x9b80` | 64 | 0 | `ee9084908016e490849af090825be054` | `30e6617f5f1208d990855ceff0908355` | `ee9084908016e490849af090825be054` |
| `0x9c40` | 0 | 60 | `8946e0ffa3e090892dcff0a3eff0908a` | `8946e0ffa3e090892dcff0a3eff0908a` | `c3123d8990855ce0fd7f02123d899083` |
| `0x9cc0` | 0 | 64 | `c3123d8990855ce0fd7f02123d899083` | `c3123d8990855ce0fd7f02123d899083` | `7e167fe512b9637d447e167fe612b963` |
| `0x9d80` | 0 | 64 | `908a51e0ff7009908a50e070030293ca` | `908a51e0ff7009908a50e070030293ca` | `030260483048030260489089fde06003` |
| `0x9dc0` | 0 | 64 | `030260483048030260489089fde06003` | `030260483048030260489089fde06003` | `908a51e0ff7009908a50e070030293ca` |

## Low-Window Detail

The low window contains compact controller-looking records. These are useful
for pattern matching, but not deterministic enough to stand alone as a
semantic oracle because some bytes drift between stock cold boots.

### `0x0180`
- `stock_before` `15082d05f7f2cd35000bf99a1002fccf` sha `8a752e9b44dd`
- `mut_85` `15082d05f7f2cd35000bf99a1002fccf` sha `a295465712ca`
- `mut_8b` `15082d05f7f2cd35000bf99a1002fccf` sha `2fdaa861309d`
- `stock_after` `15082d05f7f2cd35000bf99a1002fccf` sha `5cdffddd0e81`
- `mut_85` first diffs: `+0x2e:8b->84^0f`
- `mut_8b` first diffs: `+0x2e:8b->9a^11`

### `0x01c0`
- `stock_before` `aff1760700d70000aff115082d05aff1` sha `a757e9b414af`
- `mut_85` `aff1760700d70000aff115082d05aff1` sha `a757e9b414af`
- `mut_8b` `aff1760700d70000aff115082d05aff1` sha `9319100b9fa3`
- `stock_after` `aff1760700d70000aff115082d05aff1` sha `a757e9b414af`
- `mut_85` first diffs: `none`
- `mut_8b` first diffs: `+0x13:93->8c^1f`

### `0x0200`
- `stock_before` `60932312aff151016bf7193eaff15200` sha `df9d2c1fe24c`
- `mut_85` `609923cdaff1510171f71a35aff15200` sha `bc9d16c83916`
- `mut_8b` `609322d5aff151016bf71969aff15200` sha `3d36707e1c28`
- `stock_after` `60992384aff151016bf719dbaff15200` sha `be5fd98777f5`
- `mut_85` first diffs: `+0x01:93->99^0a` `+0x03:12->cd^df` `+0x08:6b->71^1a` `+0x0a:19->1a^03` `+0x0b:3e->35^0b`
- `mut_8b` first diffs: `+0x02:23->22^01` `+0x03:12->d5^c7` `+0x0b:3e->69^57` `+0x35:f8->e4^1c`

### `0x0240`
- `stock_before` `aff00302010000000000aff20803aff0` sha `2454c089c84f`
- `mut_85` `aff00302010000000000aff20803aff0` sha `74b43542a681`
- `mut_8b` `aff00302010000000000aff20803aff0` sha `2eb32dedf768`
- `stock_after` `aff00302010000000000aff20803aff0` sha `c7dc41d1175c`
- `mut_85` first diffs: `+0x1b:6b->71^1a` `+0x1c:19->1a^03` `+0x1d:3e->35^0b` `+0x22:6b->71^1a` `+0x24:19->1a^03` `+0x25:3e->35^0b`
- `mut_8b` first diffs: `+0x1d:3e->69^57` `+0x23:f8->f9^01` `+0x25:3e->69^57` `+0x2a:f7->af^58` `+0x2b:f2->f1^03` `+0x2c:dd->76^ab` `+0x2d:00->03^03` `+0x2e:af->20^8f`

### `0x0280`
- `stock_before` `006baff1760700d700c8aff115082d05` sha `6927be1bc371`
- `mut_85` `0071aff1760700d700c8aff115082d05` sha `ed4842169842`
- `mut_8b` `15082d05aff1510c006baff1760700d7` sha `48cea53ed762`
- `stock_after` `006baff1760700d700c8aff115082d05` sha `6927be1bc371`
- `mut_85` first diffs: `+0x01:6b->71^1a` `+0x15:6b->71^1a` `+0x1b:6b->71^1a`
- `mut_8b` first diffs: `+0x00:00->15^15` `+0x01:6b->08^63` `+0x02:af->2d^82` `+0x03:f1->05^f4` `+0x04:76->af^d9` `+0x05:07->f1^f6` `+0x06:00->51^51` `+0x07:d7->0c^db`

## Next Use

Use this as a candidate generator, not a final decode. Good next tests are:

- mutate a second lane-0 group and look for overlapping public-window
  signatures;
- use the clean reversible offsets as trigger/correlation targets while
  developing a normal-mode I/O loop;
- avoid treating the low-window bytes as stable values unless stock-before
  and stock-after agree in the same run.
