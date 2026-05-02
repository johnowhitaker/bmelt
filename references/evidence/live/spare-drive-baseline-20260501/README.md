# Spare Drive Baseline

Date: 2026-05-01.

Host separation:

- Linux host: `jonathan-thinkpad-t480s`
- Active optical LUN: `/dev/sg0`
- Drive state: spare drive switched into the Linux bench setup
- Front-panel wiring: not attached on this spare

Read-only status:

```text
/dev/sg0: vendor='PLDS' model='DVD+-RW DS-8ABSH' rev='LD5M' type='5'
```

Read-only F0 spot window:

```sh
sg_raw --cmdset=1 -b --request 176 --timeout 3 /dev/sg0 \
  12 00 00 00 f0 40 00 00 00 00 00 00 \
  > /tmp/boastermelt-spare-baseline/live-extrainq-176.bin

python3 scripts/dump_liteon_linux_f0_window.py \
  --device /dev/sg0 \
  --extrainq /tmp/boastermelt-spare-baseline/live-extrainq-176.bin \
  --start 0x28000 --size 0x800 --chunk 0x80 \
  --out /tmp/boastermelt-spare-baseline/f0-028000-028800.dec.bin \
  --raw-out /tmp/boastermelt-spare-baseline/f0-028000-028800.raw.bin
```

Result:

```text
f0-028000-028800.dec.bin sha256 ce8695fdf6905c29d40dfef65e9d1a7b01d7e42cb333f01cbfd0b33e2803ef27
F0[0x028119] = 0xd8
F0[0x028519] = 0x68
```

The decrypted `0x28000..0x287ff` window matches the stock LD5M image. In
particular, the old record-59 mutation site is stock on this spare:

```text
F0[0x28519] = 0x68
```

This drive is a usable spare baseline for read-only work and carefully chosen
low-risk live probes. Avoid repeating record 58/59 CDD mutations casually:
that byte neighborhood blocked the update-entry path on the previous Linux
drive.
