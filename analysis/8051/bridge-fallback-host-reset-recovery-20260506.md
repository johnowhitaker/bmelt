# Bridge Fallback Host-Reset Recovery - 2026-05-06

Read-only / host-reset diagnostic. No firmware-update WRITE BUFFER paths were
sent.

## Starting State

Linux exposes the Initio bridge as a direct-access disk, not as the PLDS optical
LUN:

```text
/dev/sg0  /dev/sda  Generic   External          1.14
/dev/sg1  /dev/sdb  Generic-  SD/MMC            1.00
```

USB topology:

```text
Bus 001 Device 009: ID 13fd:0840 Initio Corporation INIC-1618L SATA
/:  Bus 01.Port 1: Dev 9, If 0, Class=Mass Storage, Driver=usb-storage, 480M
```

The bridge still reaches the attached ATAPI device through SAT identify:

```text
firmware: LD5M
model:    PLDS DVD+/-RW DS-8ABSH
serial:   HMN3XPLC0088251BRA00
```

So this is not a dead USB bridge and probably not dead PLDS silicon. It is a
bad bridge-facing enumeration/personality state: the host gets a bogus
direct-access disk LUN, while SAT identify can still see the optical drive
underneath.

## Attempts

All of these returned to the same `Generic External 1.14` state:

```sh
# USB deauthorize / reauthorize
echo 0 > /sys/bus/usb/devices/1-1/authorized
sleep 3
echo 1 > /sys/bus/usb/devices/1-1/authorized

# usb-storage interface unbind / bind
echo -n 1-1:1.0 > /sys/bus/usb/drivers/usb-storage/unbind
sleep 2
echo -n 1-1:1.0 > /sys/bus/usb/drivers/usb-storage/bind

# USBDEVFS_RESET on /dev/bus/usb/001/009

# SCSI device reset
sg_reset --device /dev/sg0
```

Earlier attempts already covered Pico power cycles, SAT software reset,
COMRESET-style ATA pass-through, cautious ATAPI PACKET probes, and a Linux host
reboot. Those also returned to bridge fallback.

## Practical Result

Do not send helper-bypass, currentboot, or normal-mode hook write paths while
the host sees this state. The guard should remain:

```text
sg_inq must report PLDS DS-8ABSH
```

The next useful live step requires one of:

- physical drive/bridge replug or replacement that enumerates as PLDS again;
- a different bridge/direct-SATA path;
- a new recovery insight specifically for the Initio fallback state.

Once the PLDS optical LUN returns, the next queued experiment is:

```sh
python3 scripts/run_liteon_bridge_oracle_ladder.py \
  --device /dev/sg0 \
  --pico-port /dev/ttyACM0 \
  --execute
```
