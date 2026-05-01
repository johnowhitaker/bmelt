# Currentboot Bulk IO Live Notes

Date: 2026-05-01

## Goal

Improve the currentboot service channel from one byte per SCSI command toward
a more ergonomic debug primitive.

## Candidate

Built:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2/currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-gateway-cdb-bulk-xdata-rw-v2-candidate.json
```

This installs a hook at `0x4fc9` into the `0x6ee3` cave.

After the `rw-v2` XDATA-read branch proved unsafe, the write-only candidate was
rebuilt with the same live-proven `CDB[10] == a5` guard and installed as the
preferred service hook:

```text
references/firmware/extracted/currentboot-response-hook-candidates/currentboot-response-hook-gateway-cdb-bulk-xdata-write-v2/currentboot-response-hook-gateway-cdb-bulk-xdata-write-v2/liteon-full-currentboot-ld5m-helper-bypass-currentboot-response-hook-gateway-cdb-bulk-xdata-write-v2-candidate.json
```

## Live Results

Working:

- bulk controller-gateway reads;
- guarded XDATA writes with `CDB[10] = a5`;
- power-cycle recovery to normal `LD5M` after currentboot experiments.

Not working:

- the guarded XDATA-read branch with `CDB[10] = 5a` timed out on the first
  smoke test and left the SCSI path blocked until the stuck process was killed
  and the drive was Pico power-cycled.

## Smoke Evidence

Bulk gateway read from controller address `0x018620` returned:

```text
Flash Type Error
```

followed by the expected helper code bytes in one 64-byte response. The reader
used the normal stale-first-byte compensation in
`scripts/read_liteon_currentboot_gateway_bulk.py`.

Guarded XDATA write:

```text
xdata[0x8000] <- 0x5a
```

returned readback `0x5a` and did not break subsequent bulk gateway reads.

The first write-only build had a stale guard-byte-order assumption and fell
through to the gateway reader. The builder now checks only `xdata[0x8194] ==
0xa5` for write mode, matching the live CDB shadow behavior. The corrected
write-only candidate was installed and smoke-tested successfully.

The XDATA-read attempt:

```text
xdata[0x818a], CDB[10:11] = 5a a5
```

timed out with `DID_TIME_OUT` / `Error 99 occurred, no data received`.

## Practical Conclusion

Use the currentboot service channel as:

```text
bulk gateway read + guarded XDATA write
```

Prefer the corrected write-only `gateway-cdb-bulk-xdata-write-v2` candidate for
routine service work. Do not use the combined `rw-v2` hook's XDATA-read branch
for routine work. For XDATA reads, use the separate proven XDATA bulk hook
candidate or keep using the older timing/bit-channel paths when the environment
requires them.

Also note that the standard canonical recovery sequence restores stock LD5M and
wipes installed currentboot response hooks. Reinstall the desired hook before
entering currentboot, or use the Pico power cycle to return from currentboot
when a full canonical rewrite is not needed.
