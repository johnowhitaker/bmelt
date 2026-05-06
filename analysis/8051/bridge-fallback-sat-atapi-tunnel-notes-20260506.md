# Bridge Fallback SAT/ATAPI Tunnel Notes - 2026-05-06

No firmware-update commands were sent for this note.

## Question

When the Initio bridge exposes only:

```text
Generic External 1.14
```

but `sg_sat_identify -p /dev/sg0` can still identify the attached PLDS ATAPI
drive, can we tunnel arbitrary MMC/ATAPI packet commands through SAT and keep
working without the optical LUN?

## Local Evidence

Verbose `sg_sat_identify -p -vvvv /dev/sg0` shows the bridge accepting an ATA
PASS-THROUGH(16) command for ATA command `0xa1`:

```text
85 08 0e 00 00 00 01 00 00 00 00 00 00 00 a1 00
```

That is not an ATAPI packet command such as SCSI INQUIRY or READ BUFFER. It is
the ATA `IDENTIFY PACKET DEVICE` command, transferred as a normal PIO data-in
ATA command through the SAT layer. This is enough to prove that the PLDS drive
is alive below the bridge, but it does not prove that the bridge can forward
arbitrary 12-byte MMC packets.

## Why General Packet Tunneling Looks Unlikely

T10 draft `04-262r2` briefly listed protocol `8` as "Packet" in the proposed
ATA command pass-through protocol table. Later draft `04-262r8a` removed that
packet-protocol reference and explicitly narrowed the proposal away from ATAPI.
The modern SAT-style protocol table used by sg3_utils treats protocol `8` as
device diagnostic, not packet.

That matches the bench behavior:

- `IDENTIFY PACKET DEVICE` works because it is ATA command `0xa1`.
- Attempts at a general ATAPI PACKET/TUR-style path did not yield a usable
  read-only INQUIRY path.
- Host-side USB/SCSI resets do not change the bridge personality.

## Practical Conclusion

The `Generic External` fallback is useful for diagnostics only:

```text
SAT identify -> confirms LD5M PLDS below the bridge
```

It is not currently a trustworthy route for normal READ BUFFER, helper-bypass,
or the bridge-oracle ladder. Keep the hard live-write gate:

```text
sg_inq must report PLDS DS-8ABSH
```

The next productive live step still requires a PLDS optical LUN via physical
replug/swap, alternate bridge, or direct SATA.

References checked while writing this note:

- T10 `04-262r2`, ATA Command Pass-Through draft, protocol table still listing
  packet.
- T10 `04-262r8a`, later ATA Command Pass-Through draft, revision history
  noting removal of packet-protocol support and ATAPI scope.
