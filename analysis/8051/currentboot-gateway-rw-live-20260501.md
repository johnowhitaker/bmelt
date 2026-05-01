# Currentboot Gateway Read/Write Live Result

Date: 2026-05-01

Evidence:

```text
references/evidence/live/currentboot-gateway-rw-20260501/
```

## Result

`gateway-cdb-rw-v2` is a live-proven volatile controller-gateway write
primitive in the hooked currentboot handler.

The failed v1 attempt was still useful: it installed and read correctly, but
its write branch did not fire. V1 required both `CDB[6] == 0xa6` and
`CDB[10] == 0x5a`; readback stayed unchanged. That matches the older
observation that CDB byte 6 is not a reliable parameter byte in this handler.

V2 keeps the write guard in the preserved parameter window:

```text
CDB[5] low six bits  selector within 64-byte gateway window
CDB[7:9]             24-bit big-endian controller base address
CDB[10]              0x5a means write
CDB[11]              byte value to write
response[0x20]       readback byte
```

## Smoke Test

The currentboot helper string at controller `0x018620` initially read:

```text
Flash Type Error
```

Writing `0x47` at `0x018620` returned readback `0x47`, and a follow-up gateway
read showed:

```text
Glash Type Error
```

Writing `0x46` restored:

```text
Flash Type Error
```

The multi-byte writer then repeated the same proof by writing/restoring the
five-byte `Flash` prefix.

## Carryover Probe

I used a harmless padding byte before the normal/currentboot-shared
`PLDS CORPORATION` string as a marker:

```text
controller[0x074030] ff -> 5a
```

The write succeeded and read back in currentboot.

A bare `PLDSVUC` lock command did not exit currentboot. It returned CHECK with
Not Ready / Medium not present, and the hooked identity remained `;D5C`.

After restoring the byte, I repeated the marker write and then ran the known
full currentboot recovery sequence. Recovery returned to normal LD5M, but
normal `READ BUFFER id=01 offset=0x074030` showed the original bytes:

```text
ff ff ... ff 50 4c 44 53 20 43 4f 52 ...
```

So this primitive does not give trivial currentboot-to-normal page carryover
through the known recovery path.

## Practical Meaning

This is still a useful primitive:

- currentboot controller/helper RAM patches can now be tested without
  rebuilding and reinstalling a whole helper-bypass candidate;
- helper-overlay behavior can be altered after event 1 and before later pMac
  boundaries;
- currentboot mailbox and parser experiments can write structured state in one
  run instead of baking every trial into flash.

It is not, by itself, a normal-runtime patch mechanism. The next normal-runtime
path still needs either a gentler currentboot-to-normal transition that keeps a
patched controller page alive, or a separate normal-mode write/patch foothold.
