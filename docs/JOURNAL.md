# Project Journal

This is the cleaned-up story of the boastermelt LiteOn/PLDS `DS-8ABSH` work so
far. It is deliberately human-readable: enough technical detail to preserve the
thread, but not a dump of every failed probe.

## Starting Point

The project began with an ordinary-looking slimline optical drive and the
question that makes these devices interesting: if the vendor updater can
rewrite the drive firmware over normal storage commands, can we understand the
protocol well enough to read, modify, and eventually run our own code?

The first foothold was SCSI. Besides normal INQUIRY and storage commands, the
drive accepted vendor-flavored `READ BUFFER` and `WRITE BUFFER` traffic. That
was enough to start treating the drive as a black box with a firmware-update
surface rather than as a completely sealed appliance.

## Reading The Drive

The early read work found the useful public windows:

- standard INQUIRY reported `PLDS DVD+-RW DS-8ABSH`;
- EXTRAINQ exposed LiteOn-specific metadata and key material;
- `READ BUFFER mode=1 id=F0` exposed a 1 MiB firmware window.

The F0 bytes were encrypted, but the pattern was tractable. EXTRAINQ gave the
pieces needed to derive the AES key and IV, and F0 decrypted cleanly when read
in `0x80`-byte reset windows. That gave us the baseline LD5M image.

Once the image was visible, its structure stood out:

- a low resident/prefix region;
- a family marker around `0x6ff8`;
- a descriptor and two large `CDD` streams;
- identity/profile bytes around `0xd8fd0`;
- trailer material around `0xe7fe0`;
- a final erased tail from `0xe8000` onward.

## Learning From The Updaters

The next step was to stop guessing the write sequence and watch the official
updaters. That led to the Wine shim work: fake enough of the Windows SPTI/ASPI
environment that the updater would run offline while logging every command it
wanted to send.

That was one of the big unlocks. The updater traces gave us:

- the banked chunking model;
- the profile-tail helper payloads;
- the use of AES-CBC plus CMAC on transport payloads;
- the split between normal/pre-tail keys and currentboot keys;
- the official-style 544-event currentboot write sequence.

Extracting firmware from installers became its own subproblem. AD12, AHS9,
CHS9, and related sibling images each needed slightly different handling:
some were pulled from updater traces, some from FileDecrypt-style paths, and
some required the `F2K8` postprocess mask. Comparing valid images made the
container layout much clearer, especially the suspicious pre-family word and
the 14-byte trailer seal.

## The First Wrong Theories

A lot of effort went into testing simple explanations:

- maybe the USB bridge was blocking writes;
- maybe direct SATA would behave differently;
- maybe a final commit CDB was missing;
- maybe the last 16-byte pMac/control payload was a checksum;
- maybe the trailer was a CRC, sum, Adler, visible-key CMAC, or HMAC;
- maybe the Coastermelt-style bypass was a visible count byte in the CDD header.

Most of these were useful negatives. Modified images staged and read back
correctly, but final persistence failed. Same-image controls passed. Flipping
the final event payload still passed. Skipping the final event failed later.
The evidence kept pointing away from transport mechanics and toward a
controller-side admission check over the staged container.

## The 0D5C Detour

At one point the project crossed a boundary without knowing the return path.
Both affected drives ended up reporting `0D5C`, a currentboot/recovery-like
personality with CD-only behavior. That looked bad for a while.

Linux changed the situation. With direct `sg_raw` access on
`jonathan-thinkpad-t480s`, we could speak the same SCSI dialect more reliably
than macOS/USB allowed. The LD5M currentboot-key continuation sequence recovered
the drives back to normal `LD5M`. That turned `0D5C` from a dead end into a
known, recoverable state.

That recovery path changed the tone of the project. We could afford sharper
experiments because the common failure mode had a mapped exit.

## The Container Barrier

The cleanest model became:

1. Host chunks and pMac/control commands can stage bytes.
2. The staged bytes can read back correctly.
3. Final event 544 hands off to controller/helper logic.
4. The controller admits only containers it considers valid.

The visible 8051 code showed the final path entering a controller handoff
rather than locally validating a simple host checksum. The helper/status path
around `0x4da4`, `0x48a0`, and `01:8006` looked like a controller-mediated
finalization step.

The trailer at `0xe7fe0..0xe7fed` remains suspicious. It is almost certainly
container-auth material, but not a simple checksum we have reproduced. The
project could still return to that clean route later, but it was not the
fastest way to get code running.

## The Helper Bypass

The breakthrough came from treating the `ef130045` profile-tail payload as a
mutable 8051 helper overlay. It is loaded separately from the F0 image and is
visible at `READ BUFFER 01:018000` in normal mode. Static analysis mapped it as
a flash-profile helper linked at code base `0x3000`.

The crucial patch was tiny:

```text
helper plain 0x02b5: 30 e6 12 -> 02 32 c4
```

That forces the helper's final status branch to jump to its local success path.
With that helper patch in place, selected F0 changes persisted even when the
ordinary modified image would have failed admission.

Live-proven cases included:

- identity/profile byte `0xd8ff4`;
- identity/profile vendor-copy byte `0xd8fd8`;
- a later CDD stream 1 byte at `0x27d4f`;
- low-prefix restores when the helper erase/program start range was patched.

This did not make every byte safe. The low prefix below `0x7000` is special,
CDD directories are risky, canonical erased gaps should stay erased, and
`0xe8000..0xfffff` is outside the programmed object. But it changed the core
question from "can we edit this?" to "what shall we build?"

## Code Execution

The first attempts at host-visible code execution taught two things:

- persistent F0 hooks are not automatically live just because the bytes are in
  flash;
- patching the helper entry is too early and can wedge the drive at the next
  pMac/control boundary.

The successful proof used a later, already-understood helper branch instead.
We hooked the final status branch at code `0x32af`, jumped to payload space at
`0x361a`, ran a finite delay loop, and returned to the normal success path at
`0x32c4`.

The host-visible signal was timing:

```text
baseline event 68: 0.255830s
delay 0x20 event 68: 0.849545s
delay 0x80 event 68: 2.638886s
```

The adjacent event timings stayed flat, and each partial run recovered back to
`LD5M`. That is the first clean proof that our patched helper code runs and can
communicate back to the host, even if only through a crude timing channel for
now.

The next small breakthrough was turning that crude timing channel into a real
bit. Instead of delaying, the payload chooses between the helper's normal
success path and its original error path. Success makes event `68` return
GOOD; the error path makes it return the known recoverable `DID_ERROR`.

That was enough to read XDATA one bit at a time. A tiny payload reads a byte
with `MOVX`, tests one bit, then chooses success or error. The first full byte
read was the helper/controller handoff byte at `0x48a0`:

```text
xdata[0x48a0] = 0xa0
```

This is not fast enough to dump memory wholesale, but it changes the shape of
the next phase. We can now ask the drive small internal questions without
soldering anything: what does this status register contain at the hook point,
does this GPIO bit move when a button changes, does this controller handoff
flag mean what we think it means?

The error-path bit channel then taught us its own limitation. Claude ran an
overnight candidate sweep and hit the first organic zero in the controller
mailbox area: `xdata[0x4704].0 = 0`. The helper reported that zero by jumping
to `DID_ERROR`, and this time auto-recovery did not finish cleanly without a
physical replug. That made `0x4704` interesting, but it also made the channel's
weakness obvious: using a helper error as a data symbol is a blunt instrument.

The fix was to return to the original timing idea, but make it conditional.
The new payload reads a bit, delays only when the bit is one, and always returns
through the helper success path. Because that payload is longer than the old
`Flash Type Error` string slot, it now lives in a larger comment-string slot at
helper plaintext `0x04f6` / code `0x34f0`.

With a fresh calibration, event `68` was about `0.256s` for no delay and
`0.853s` for delay `0x20`. Reading all eight bits of `xdata[0x4704]` through
that safer channel gave:

```text
xdata[0x4704] = 0x00
```

That both confirms Claude's bit-zero observation and gives us a less
punishing way to keep mapping controller registers.

## Where The Clean Repo Starts

The active repo now keeps only the compact operating set:

- the LD5M base image and EXTRAINQ reference;
- the profile-tail helper artifacts;
- currentboot/recovery candidates;
- the minimal Linux dumping/recovery/bypass scripts;
- the current 8051 binary and Ghidra decompile;
- the timing code-execution proof;
- the helper success/error bit-channel proof;
- the helper timing-channel read proof.

The next phase is to use that slow bit channel for targeted internal mapping,
then decide whether a Pico front-panel link is worth adding for faster,
friendlier communication.

## Front-Panel Probing

The Pico side quest is now real enough to be useful. The gutted drive's front
board is wired with blue as ground, green as the normally-high eject button
line on `GP27`, and yellow as the LED-plus line on `GP26`. Pulling GP27 low from
the Pico safely simulates a button press electrically, and GP26 clearly follows
the visible LED during helper/recovery activity.

This immediately exposed a timing problem in the naive LED-register probes:
checking GP26 only after a SCSI command returns can only see latched state. A
candidate register could pulse during helper execution and be restored before
the host sees command completion.

The current probe method fixes that. The helper hook at plain `0x02b5` jumps to
payload space at plain `0x0600`, where the payload either delays or repeatedly
asserts a candidate register value while the Pico samples GP26. This is a
known-good execution window:

```text
plain 0x0600 delay payload: event 68 stretches to about 2.7s
plain 0x0600 looped XDATA hold: event 68 stretches to about 3.1s
```

So far, this stronger method has ruled out the first small LED-control
shortlist: `P1.6`, XDATA `0x4023`, `0x4844`, and `0x90fc`. The earlier
final-tail probes also ruled out the obvious `0x59xx/0x5axx` initialization
registers. The LED is observable, but we have not found the latch yet.

The more promising next step is probably to use GP27 as an input signal and map
which internal bit changes when the eject button line is pulled low. That should
narrow the front-panel GPIO block more efficiently than brute-forcing output
registers.

The first attempt at making that efficient was a parity/syndrome scanner: ask
the helper for parity over whole XDATA ranges, once with the button line
released and once with it low. In the ideal single-bit-change case, a handful of
predicate bits decodes the changing address directly.

That idea is still good, but the first live shakeout taught us not to hold GP27
low through the whole sequence. It physically moved the sled and made the drive
report tray-open/not-ready before reaching the helper. The tool now refuses
button-low runs unless explicitly allowed, and the intended mode is to run setup
with GP27 released, then pull GP27 low only for event 68. Whether even that
short pulse is acceptable is a hardware/mechanism decision, not just a software
one.

The first event-scoped try still attempted to eject, so GP27 is now classified
as a mechanism actuator rather than a useful debug input in the current wiring.
Removing the tray/insert sense band might reduce mechanical risk, but it also
risks preventing the updater sequence from reaching the helper at all. The
better next hardware input is a separate line that does not already mean
"eject" to the drive.

The LED search then became a trace-analysis problem. We added a Pico waveform
analyzer and started comparing the sampled GP26 shape during event 68 and
recovery. Direct 8051 port probes were mostly boring: `P1.0..P1.7` and
`P3.0..P3.5` all produced the same seven-transition LED pattern as the baseline.
`P3.6` was not boring: clearing it wedged the optical LUN and left the LED on.
That is probably the 8051 external-memory write strobe showing through, so
`P3.6` and its neighbors are now off the casual-probe list.

The useful crack came from XDATA. Writing `0x00` to `0x4748` in a held helper
loop completed and recovered. Writing `0xff` to the same address let event 68
return, but then GP26 stayed high for the whole attempted recovery and the USB
side timed out until a physical replug. That is the first strong front-panel LED
path lead: not yet a communication channel, because whole-byte `0xff` is too
destructive, but very likely either the LED latch itself or a nearby
front-panel/control register. Static refs point toward the latter: stock code
writes `0x88`/`0x98` to `0x4748` and treats bit 7 as a kick/wait bit beside
command bytes at `0x474d/0x474e`. The next version of this experiment should be
bit-level and should preserve/restore the original `0x4748` value instead of
hammering all bits high.

That follow-up mostly demoted `0x4748` from "possible LED latch" to "controller
state clue." Reading it through the slow helper bit-channel showed it is already
`0xff` at the event-68 hook. Restored writes, including restored whole-byte
`0xff`, recover normally. So the earlier wedge was not the transient write; it
was leaving that controller byte in the wrong state for the next recovery
transaction.

The neighboring controller cluster was similarly educational. Restored writes
to `0x4726`, `0x479e`, `0x4784`, `0x4788`, `0x4756`, `0x47a7`, and `0x4728`
looked normal. Restored `0x4780=0x00` looked normal too, but restored
`0x4780=0xff` completed event 68 and then left the drive in currentboot with
GP26 high during recovery. The normal recovery script brought it back to LD5M.
That makes `0x4780` a second hazardous controller-path lead, not yet a clean
LED output channel.

## Back To The Updaters

After the slow bit-channel work, we took a static detour back into the Windows
updater dumps to answer a simpler question: does the updater ever hold the CDD
payload in a more useful plaintext form?

The answer is half yes. The unpacked AHS9 updater module does not contain raw
`CDD` streams at rest. It contains an encrypted 1 MiB F0 object plus the data
needed to decrypt it. The FileDecrypt key is built from a 256-byte table after
the `COPYF2K8_SIZE` marker:

```text
key[i] = table[(selector + i * 0x11) & 0xff]
```

For AHS9, selector `0x07` gives:

```text
7ee34f39b34d5c9248473a39ec976508
```

AES-ECB decrypting the object at `0x195dc0` produces an almost-valid F0 image:
the CDD markers, family marker, identity area, and trailer auth are all there.
The remaining difference turned out to be the old `F2K8` postprocess layer, now
modeled exactly. The updater applies a 1 KiB mask window, changing one byte in
each `0x400` block:

```text
rel = mask[i] & 0x3f
delta = sum(NEW_FW1[0:4]) & 0xff if i % 7 in {0, 2} else mask[i]
image[i * 0x400 + rel] ^= delta
```

For `AHS9`, `sum("AHS9") & 0xff` is `0x15`. Applying that rule reproduces the
existing `AHS9-postprocess-plain.bin` byte-for-byte.

That is useful cleanup and future tooling, but it does not expose decoded servo
runtime memory. The Windows updater materializes the sealed F0 container. The
CDD body still looks like something the drive's controller consumes and
expands internally.

## The CDD Shape Gets Clearer

The next static pass pushed on that CDD question without touching the live
drive. The important result is that the obvious decoded allocation is not the
remembered 1.4x relationship. Both the outer descriptor and the CDD stream
headers name controller/logical space `0x184000..0x1b4000`, exactly `0x30000`
bytes. The encoded object from `0x7000..0xe8000` is about 4.69 times that, and
the actual CDD streams/bodies are about 4.4 times that.

So if there is a 1.4x relation hiding somewhere, it is not the top-level
encoded-vs-decoded CDD size. It may be a smaller work buffer or substream, but
the visible CDD descriptor is saying something much chunkier.

The structure is getting less mysterious, though. CDD1 begins with 436
eight-byte directory records, then a low-entropy table/control window. The
header byte that looked like a clean `0x400` table length turned out to be only
a nominal boundary: the first source bytes begin a little earlier, around
stream-relative `0x1194..0x11a4` depending on the image. CDD2 reuses the tail
of the directory: its bytes `0x20..0x1a0` exactly duplicate CDD1 entries
388..435, and its source payload starts immediately at `0x1a0`. The old
`0x5a0` CDD2 body guess was too symmetrical.

Then that pointer-like column turned into a real address field. For each
directory entry:

```text
source_start = (u16le(entry[6:8]) << 4) | (entry[5] >> 4)
```

Those source starts are monotonic and land directly inside the CDD object. CDD1
entry 388 starts at `0xd91a0`, exactly after CDD2's copied directory prefix.
Byte 5 is split: its high nibble is the low nibble of the source address, while
its low nibble groups with bytes 0..4 as a non-source operation key. In the
CHS7/CHS9 pair, 380 of 436 same-index records keep that operation key and all
380 keep the same source-span length; 377 of them differ only in source-address
bits. That is the best evidence so far that the records are real packed-stream
instructions, not opaque metadata.

The common short templates `0d6840031a` and `0c60000318` point at
`0x34`/`0x30` byte spans, matching the visible repeated motif islands. This is
another strong sign that the 8-byte records are a packed-stream directory with
source spans.

Those short templates even have an internal length pattern: for `0d6840031a`,
`0x0d` acts like `N`, `0x68` is `8*N`, `0x1a` is `2*N`, and the source span is
`4*N = 0x34`. The `0c60000318` template follows the same rule with `N=0x0c`.
That looks much more like an opcode/length tuple than random high-entropy
material.

Comparing same-index source spans across close siblings backs that up. CHS7
and CHS9 have directory entries that are usually only one or two bytes apart,
and some same-index source spans share long prefixes, up to 56 bytes in the
current report. The record index is probably a stable semantic unit across
minor firmware revisions.

That is not what a plain encrypted blob looks like. Cheap decode probes agree:
no global XOR/add/sub transform exposed text, no standard zlib payload decoded,
and the repeated motif runs do not look like AES-ECB blocks. The best static
path is now to reverse the directory record grammar and use sibling shifted
matches as anchors, not to brute-force an unknown cipher.

The hybrid path remains attractive too. Once we can hook normal runtime, a few
bytes from `0x184000`, `0x18481c`, and `0x19191a` would tell us whether that
logical range contains raw CDD body material, decoded controller code/data, or
some third representation.

We tried those reads through the existing currentboot helper timing channel.
They all came back `0x00`, with clean recovery after each bit:

```text
controller[0x184000] = 0x00
controller[0x18481c] = 0x00
controller[0x19191a] = 0x00
```

That mostly tells us the currentboot helper hook is the wrong vantage point for
decoded CDD memory. The descriptor can still be right; the decoded/controller
range may simply not be populated or exposed until normal LD5M runtime.
