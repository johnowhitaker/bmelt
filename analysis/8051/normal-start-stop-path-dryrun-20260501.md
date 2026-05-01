# Normal START STOP Path Dry Run

Host: `jonathan-thinkpad-t480s`
Drive: `PLDS DVD+-RW DS-8ABSH LD5M`
Evidence:
`references/evidence/live/normal-start-stop-path-dryrun-20260501`

This was a tool sanity check for
`scripts/capture_liteon_normal_start_stop_path.py`. It did not send START STOP
UNIT because `--allow-start-stop` was intentionally omitted.

Command shape tested:

```text
planned variant: eject
planned CDB:     1B 00 00 00 02 00
meaning:         START=0 LOEJ=1
allow flag:      false
```

The script captured one normal work-window baseline:

```text
READ BUFFER mode=1 id=01 offset=0x070000 length=0x10000 chunk=0x400
sha256 a5a35e863e849ed2a3a5e19eee2d720e2bd683c3b14971faea7ed900bf19730d
```

Post-run status check remained normal:

```text
/dev/sg0 PLDS DVD+-RW DS-8ABSH LD5M
/dev/sg1 Generic SD/MMC 1.00
```

This verifies the safety gate and baseline capture flow. The next live version
can use the same tool with `--allow-start-stop` once the Pico power-cycler and
front-panel observation are ready.
