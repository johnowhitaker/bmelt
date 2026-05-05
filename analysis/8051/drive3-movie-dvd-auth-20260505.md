# Drive 3 Movie DVD Auth Probe

Date: 2026-05-05

Media: pressed movie DVD inserted by hand.

Scope: normal-mode media/auth probing only. No firmware-update commands, no CDD
edits, no flash writes, no media writes, and no tray/eject commands.

Evidence:

```text
references/evidence/live/drive3-movie-dvd-auth-20260505T033701Z/
references/evidence/live/normal-mailbox-dvd-auth-20260505T033713Z/
references/evidence/live/normal-mailbox-dvd-auth-20260505T033935Z/
```

## Media Status

The disc is recognized as DVD-ROM media.

`TEST UNIT READY` succeeds, and REQUEST SENSE reports no current error.

READ CAPACITY(10):

```text
last_lba   = 0x0016732f  # 1,471,279
block_size = 0x00000800  # 2048
```

GET CONFIGURATION current profile:

```text
current_profile = 0x0010  # DVD-ROM
```

READ DVD STRUCTURE format `0` succeeds. The physical-format information starts:

```text
08 02 00 00 01 02 01 00 00 03 00 00 00 19 73 2f
```

The drive stayed normal `LD5M`.

## Report-Only Auth Probe

The first `dvd-auth` run used the older harness order, which requested a drive
challenge before sending a host challenge. This was useful because the drive
answered like a real CSS state machine:

```text
REPORT KEY CSS AGID:       GOOD, response 00060000000000c0, AGID=3
REPORT KEY CSS ASF:        GOOD, response 0006000000000000
REPORT KEY CSS RPC state:  GOOD, response 0006000064fe0100
REPORT KEY drive challenge before host challenge:
    CHECK CONDITION / Illegal Request / Command sequence error
REPORT KEY invalidate AGID:
    GOOD
```

So the pressed DVD unlocks the CSS/MMC authentication path, and the command
sequence is order-sensitive.

## Host-Challenge Auth Probe

The harness was corrected to send the host challenge before asking for the
drive challenge. The standard nonce payload was:

```text
42 4d 49 4f 4e 4f 4e 43 45 01
```

Payload sent through `SEND KEY key format 1`:

```text
00 0e 00 00 42 4d 49 4f 4e 4f 4e 43 45 01 00 00
```

Corrected sequence result:

```text
REPORT KEY CSS AGID:                    GOOD, AGID=3
REPORT KEY CSS ASF:                     GOOD
REPORT KEY CSS RPC state:               GOOD
SEND KEY CSS host challenge:            GOOD
REPORT KEY CSS key1 after host:         GOOD, 000a00007e4bea0202000000
REPORT KEY CSS drive challenge after host:
    GOOD, 000e00007e2f16a7be83358bace60000
REPORT KEY invalidate AGID:             GOOD
identity after:                         LD5M
```

A 16 KiB public `READ BUFFER id=01 offset=0x070000` snapshot after the sequence
had no exact nonce hits. That means the auth path is a real normal-mode
bidirectional command path, but not yet a public-window data leak.

## Harness Fix

`scripts/normal_mailbox_probe.py` now respects the observed CSS order:

1. `REPORT KEY` AGID;
2. optional `SEND KEY` host challenge when `--send-challenge` is set;
3. `REPORT KEY` key1;
4. `REPORT KEY` drive challenge;
5. invalidate AGID.

Without `--send-challenge`, the harness now skips the challenge/key path rather
than deliberately generating a command-sequence error.

## Practical Read

This is the cleanest normal-mode bidirectional host/device path so far:

- host sends 10 nonce bytes through a standard MMC command;
- the drive accepts the data in normal `LD5M` mode;
- the drive returns authentication material afterward;
- the command path is stateful and order-sensitive;
- the drive remains stable.

This does not yet give arbitrary drive-internal reads. The next useful work is
to localize where the nonce and returned key/challenge pass through the normal
runtime: packet shadow, FIFO, controller bridge, or a transient media/auth
buffer. The normal public window did not show the nonce directly, so static
packet-path work or a more targeted runtime hook is still needed.

Recommended next steps:

1. Add `SEND KEY` / `REPORT KEY` to the normal response matrix and work-window
   watch patterns.
2. Compare public-window chunks for AGID-only, host-challenge, key1, and
   invalidate phases.
3. Statically rank normal chunks that test packet opcode `0xa3` / `0xa4` and
   touch `xdata[0x8a49..0x8a54]`, `0x47b1`, or the `0x409x` gateway.
4. Keep the movie DVD as the auth-path test disc.
