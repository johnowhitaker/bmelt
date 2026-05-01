# Normal START STOP / Mechanics Path Notes

Date: 2026-05-01

This is an offline note over the normal-runtime work-window captures. It does
not come from a new live drive probe.

The main point is that the recurring `+0x8bxx` work-window snippet gives a
concrete CDB-shadow anchor and a plausible first mechanics-path foothold. It
is not yet enough to command the sled safely, but it names the next hook site
more precisely than the earlier broad `0x4860` cluster notes.

Primary evidence:

```text
references/evidence/live/normal-work-window-readstatus-correlation-20260501/
references/evidence/live/normal-work-window-error-path-pairs-20260501/
analysis/8051/normal-readstatus-correlation-20260501.md
analysis/8051/normal-error-path-pairs-20260501.md
analysis/8051/normal-4860-cluster-20260501.md
analysis/8051/normal-packet-selector-map-readstatus-20260501.md
analysis/8051/normal-packet-selector-map-error-pairs-20260501.md
```

## Capture Caveat

The public `READ BUFFER id=01 offset=0x070000` window behaves like a rotating
normal-runtime work window. A chunk being visible in a snapshot proves that the
bytes are live resident/overlay material, but not that the immediately
preceding host command executed that exact branch.

That caveat matters here: the START STOP-looking code was exposed by no-disc
`READ TOC` and `GET PERFORMANCE type00` failure captures, not by a deliberate
START STOP run. It is still useful because the byte sequence itself is clear.

## CDB Shadow Anchor

The most important snippet begins around work-window `+0x8b00`:

```text
90 8a 34 e0 44 04 f0        ; xdata[0x8a34] |= 0x04
...
90 8a 49 e0 64 1b 70 27     ; if CDB[0] != 0x1b, skip
90 8a 4d e0 54 0f ff bf 02  ; if (CDB[4] & 0x0f) != 0x02, skip
1d
20 43 1a                    ; extra bit/state gate
90 8a 2d e0 ff c4 13 13
54 03 20 e4 ff              ; extra state gate
12 0f 8d                    ; call small helper with R7=0
...
```

`0x1b` is START STOP UNIT. For that command, CDB byte 4 is the
load/eject/start control byte. Low nibble `0x02` is the eject-style case. This
upgrades the packet-shadow map from "probably opcode-ish" to ordinary CDB
order:

```text
0x8a49 = CDB byte 0 / opcode
0x8a4a = CDB byte 1
0x8a4b = CDB byte 2
0x8a4c = CDB byte 3
0x8a4d = CDB byte 4 / START STOP control byte in this path
...
```

Later bytes in the same `0x8a49..0x8a54` region are also reused as controller
data/status shadows in some handlers, but the base packet copy is now anchored.

## Mechanics-Adjacent State Nearby

The same captures also include state transitions that match the separate
`0x4860` cluster note. The public window should not be treated as a perfect
linear disassembly: in a few places it exposes a partial `0x4860` read/OR
without the final store byte. The stronger evidence is the combination of the
START STOP branch above, the `0x480e` gated state path below, and the complete
set/clear idioms that recur elsewhere in the same normal work-window corpus.

The `0x480e` gated path around `+0x8bc0..+0x8c70` includes:

```text
90 48 0e e0 54 03 60 74       ; if (xdata[0x480e] & 0x03) == 0, skip path
90 48 a5 e0 54 ef f0          ; xdata[0x48a5] &= 0xef
90 47 62 e0 54 ef f0          ; xdata[0x4762] &= 0xef
90 48 0e e0 54 03 64 03 70 3d ; require (xdata[0x480e] & 0x03) == 0x03
90 48 60 e0 44 04 ...         ; prepares/branches near 0x4860.2 handling
...
90 59 05 e0 54 fe f0          ; xdata[0x5905] &= 0xfe
90 5a 01 e0 54 fa f0          ; xdata[0x5a01] &= 0xfa
...
90 48 64 e0 54 fe f0          ; xdata[0x4864] &= 0xfe
90 59 05 e0 54 fb f0          ; xdata[0x5905] &= 0xfb
90 48 60 e0 54 fb f0          ; xdata[0x4860] &= 0xfb
```

The complete paired setter appears in the `+0x926c/+0x92ac/+0x92ec` family:

```text
90 48 60 e0 44 04 f0          ; xdata[0x4860] |= 0x04
90 48 64 e0 44 01 f0          ; xdata[0x4864] |= 0x01
```

This is a better mechanics clue than a raw `0x4860` reference by itself:

- `0x480e` gates the path using its low two bits.
- `0x48a5.4` and `0x4762.4` are cleared in the same state-gated path that
  prepares `0x4860.2` handling.
- `0x4860.2` and `0x4864.0` are set as a pair in the `+0x92xx` family.
- `0x4860.2` and `0x4864.0` are later cleared in the cleanup side.
- `0x5905` and `0x5a01` are touched in the same cleanup path, tying this to
  the broader `0x59xx/0x5axx` mechanics/servo register family.

This still does not mean `0x4860.2` is "the eject bit." A safer reading is:
`0x4860.2` and `0x4864.0` are controller-facing state/enable bits used during a
valid mechanics transition.

## Relationship To Earlier Sled/LED Work

The earlier hardware experiments showed real visible effects from this broad
controller/mechanics fabric:

- pulling the Pico-connected button line can trigger eject behavior;
- some helper/register probes caused sled or tray motion;
- the visible LED is likely controller/CDD-owned, not a plain 8051 GPIO latch.

The START STOP snippet fits that model. It is a packet-level route into the
same fabric, while the `0x4860/0x4864/0x5905/0x5a01` cluster looks like the
backend state machine that makes the mechanism do work.

## Practical Next Hooks

Do not start by blindly writing `0x4860`, `0x4864`, `0x5905`, or `0x5a01`.
Those bits are surrounded by state gates and cleanup writes, and earlier
mechanics pokes have already shown that partial sequences can wedge the LUN or
move the mechanism unexpectedly.

The higher-information next hooks are:

1. Hook or instrument the START STOP branch itself, around the
   `0x8a49 == 0x1b` / `(0x8a4d & 0x0f) == 0x02` check. The goal is to confirm
   branch reachability and state values, not to force movement yet.
2. Read a tiny telemetry set around a natural START STOP/eject-style event:
   `0x8a49`, `0x8a4d`, `0x8a2d`, `0x8a34`, `0x480e`, `0x48a5`, `0x4762`,
   `0x4860`, `0x4864`, `0x5905`, and `0x5a01`.
3. If we want a visible movement primitive, prefer replaying or lightly
   modifying a complete command path once the gates are understood. A single
   register write is the riskiest and least diagnostic option.
4. If using the Pico front-panel wiring, pair this with LED/button observation
   and the servo power-cycler so a wedged state is recoverable without waiting
   for a manual unplug.

I added `scripts/capture_liteon_normal_start_stop_path.py` for this. It is
gated: it prints the START STOP CDBs and captures a baseline by default, and
only sends a mechanical command when `--allow-start-stop` is supplied. Example
dry run:

```sh
python3 scripts/capture_liteon_normal_start_stop_path.py \
  --device /dev/sg0 \
  --out-dir references/evidence/live/normal-start-stop-path-YYYYMMDD \
  --variant eject
```

Actual live use should wait until the Pico power-cycler is ready:

```sh
python3 scripts/capture_liteon_normal_start_stop_path.py \
  --device /dev/sg0 \
  --out-dir references/evidence/live/normal-start-stop-path-YYYYMMDD \
  --variant eject \
  --allow-start-stop \
  --sense-after \
  --mechanism-status-after
```

## Current Working Model

The normal-mode route now looks like:

```text
host CDB
  -> normal packet shadow at xdata[0x8a49..]
  -> opcode/control checks, including START STOP eject branch
  -> 0x480e / 0x48a5 / 0x4762 state gates
  -> 0x4860 / 0x4864 controller-facing mechanics state
  -> 0x5905 / 0x5a01 mechanics/servo register family
  -> controller/CDD-owned actuator behavior
```

That is enough to make the next live pass much narrower: confirm the branch and
read the state bytes before trying to command motion.
