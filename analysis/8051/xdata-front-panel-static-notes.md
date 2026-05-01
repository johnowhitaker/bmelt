# Front-Panel XDATA Static Notes

Date: 2026-04-30

These notes summarize the static pass over the Ghidra 8051 C export after the
Pico front-panel experiments. The working assumption is now that the LED is not
a simple 8051 SFR or XDATA latch. The visible 8051 code mostly talks to a
controller/status fabric, and the physical LED may be owned by the controller
code behind the CDD streams.

Generated cross-reference files:

```sh
python3 scripts/analyze_liteon_xdata_register_refs.py \
  --xdata-dump references/evidence/live/linux-drive1-currentboot-xdata-0000-ffff-bulk-v2.bin \
  --md-out analysis/8051/xdata-register-crossref.md \
  --json-out analysis/8051/xdata-register-crossref.json
```

## Main Findings

### `0x4748` Is A Controller Transaction Kick, Not A Clean LED Latch

The earlier live probes made `xdata[0x4748]` look interesting because some
values left GP26 high and sometimes wedged the optical LUN. The static map makes
that less mysterious:

- `FUN_CODE_47b0` writes command bytes into `0x474d/0x474e`, updates related
  selector/config bytes such as `0x4726` and `0x479e`, clears `0x4748.7`, calls
  `FUN_CODE_60c4`, and then sometimes sets `0x4748.7`.
- `FUN_CODE_4c7f` writes whole-byte `0x4748 = 0x88` or `0x98`, then calls the
  same wait path.
- `FUN_CODE_5a68` also sets `0x4748.7` while emitting status/debug bytes.

That fits a controller command/start/ack register. It explains why wild writes
near `0x4748` can affect LED timing or recovery without making `0x4748` the LED
driver.

### `0x4780` Is Part Of The Same Init/Controller Cluster

`xdata[0x4780]` has only one visible direct operation: `FUN_CODE_4a1b` ORs in
bit 7 during a broader controller/hardware initialization sequence. The nearby
code configures many `0x47xx` registers, so the live `0x4780=0xff` hazard should
be treated as a controller-path clue, not as an output candidate.

### `0x4814` Really Is Front-Panel-Adjacent Status

Live Pico differential:

```text
GP27 released: xdata[0x4814] = d9
GP27 low:      xdata[0x4814] = c9
```

So `0x4814.4` tracks the eject button line. Static code only polls the sign bit:

```c
DAT_EXTMEM_4822 = param_1 >> 1;
DAT_EXTMEM_4821 = 0xc0;
do {
} while (-1 < DAT_EXTMEM_4814);
```

The likely interpretation is that `0x4814` is a packed status byte from the
controller/front-panel block. Bit 4 is the button sense we observed. Bit 7 is an
ack/ready bit for the `0x4821/0x4822` handshake.

The normal hidden-runtime tile scan later gave a cleaner normal-mode
corroboration. Chunk `5f416d4189c9` appears in every saved normal work-window
capture, does not match F0/currentboot/helper bytes, and contains:

```text
90 48 14 e0 54 10 c4 54 0f 24 ff b3 92 2c
e0 54 04 13 13 54 3f 24 ff 92 2a
```

In 8051 terms, this reads `xdata[0x4814]`, extracts bit 4 into an internal bit
flag near `0x2c`, then extracts bit 2 into another bit flag near `0x2a`. That
fits the Pico result exactly: `0x4814.4` is not merely a currentboot artifact;
normal runtime code actively samples it as front-panel/status input.

### `0x482b/0x482c/0x482d` Look Like A Small Query/Timer Port

Several helpers write a command to `0x482b` and immediately read a 16-bit result
from `0x482c/0x482d`. Examples include `FUN_CODE_6048`, `FUN_CODE_60c4`,
`FUN_CODE_60ff`, `FUN_CODE_640a`, and `FUN_CODE_6428`.

This may become useful as a *read/query* path into controller status, but it is
still a controller interface. Do not randomly write new `0x482b` command values
until the stock command vocabulary is better mapped.

### `0x483f` Is A Sparse 0/1 Latch Worth Keeping On The Shortlist

`xdata[0x483f]` has only one visible writer:

```c
if (_7_0 != 0) {
  DAT_EXTMEM_483f = 1;
} else {
  DAT_EXTMEM_483f = 0;
}
```

That does not prove it is LED-related. The call sites are tied to transfer/setup
paths, and the currentboot dump has `0x483f = 0x01`. But compared with the broad
controller command registers, it is a cleaner future held-window candidate if we
decide to run another Pico-sampled LED probe.

### `0x486x` And `0x59xx/0x5axx` Still Look Like Init/Config

The cross-reference map reinforces the existing live negatives. `0x4860..0x486b`
and the `0x59xx/0x5axx` helper-init shortlist are written as initialization
clusters and do not look like front-panel output latches.

Later normal-runtime work-window analysis sharpened this rather than overturning
it:

```text
analysis/8051/normal-4860-cluster-20260501.md
```

The `0x4860` cluster now looks more hardware-control/mailbox-like than inert
configuration. In particular, `0x4860.2`, `0x4864.0`, and `0x4867.7` are
actively toggled by normal-mode code. That makes the cluster interesting for
future mechanics/servo work, but it still argues against using it as the
primary LED exfiltration path.

## Existing Pico Trace Review

Existing GP26 traces also fit the controller-path interpretation. Most
event-68 traces keep the same qualitative blink shape: a fixed transition count
with shifted timing. The anomaly scores in `runs/pico-led-analysis` are often
dominated by event duration changes, not by a new stable held LED level.

The strongest exception remains `0x4780=0xff`: event 68 shortens, the transition
count drops, recovery fails, and GP26 stays high during the failed recovery
window. That is consistent with disturbing a controller state path. It is not a
useful output primitive.

`0x4748` restored one-bit OR probes also alter event-68 timing, but recovery
returns to the normal multi-transition pattern. That makes `0x4748` useful for
understanding the currentboot controller transaction, while still being the
wrong place to look for a byte-rate LED channel.

## Practical Consequence

The LED path probably needs one of these:

1. a mapped controller command that asks the controller/CDD side to blink or set
   the front-panel LED;
2. a later normal-runtime hook, where the decoded CDD/controller state is live
   and natural LED transitions can be correlated against XDATA/controller
   traffic;
3. a cleaner hardware channel that does not depend on the built-in LED path.

The next static target should be the command vocabulary around `0x474d/0x474e`
and `0x482b`, not more blind LED latch probing.

Later normal-runtime chunk classification lives in:

```text
analysis/8051/normal-hidden-runtime-chunks-20260501.md
analysis/8051/normal-hidden-runtime-chunks-20260501.json
```
