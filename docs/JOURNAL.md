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

## Normal Runtime Reality Check

The Pico servo power switch turned out to be more than a convenience. It let us
ask a question that software resets could not answer: if a persistent F0 patch
is really in flash, does a true cold boot make normal firmware execute it?

For the visible F0 prefix handlers we tried, the answer was no. The patched
bytes survived a real `+5V` power cut and the drive re-enumerated cleanly, but
normal `INQUIRY` and EXTRAINQ timing and contents stayed canonical. That means
those visible routines are real code, and they matter in currentboot, but they
are not the normal LD5M command handlers we need for an easy resident backdoor.

We then surveyed the normal command surface without sending updater or
mechanics commands. The drive has several quick, no-disc response channels:
ordinary INQUIRY, EXTRAINQ, MODE SENSE(10), GET CONFIGURATION, GET EVENT
STATUS, and MECHANISM STATUS. `GET PERFORMANCE` timed out, and normal-mode
`READ BUFFER id=02` once hung the optical LUN until the Pico servo power-cycle
recovered it.

The survey gave a useful but subtle clue. Normal INQUIRY and EXTRAINQ contain
byte strings that also exist in the visible F0 identity copies, yet editing one
of those F0 copies did not alter normal EXTRAINQ. So the normal runtime uses
the same template data, or a copied form of it, but probably not those visible
flash offsets directly. This narrows the next problem: find where normal LD5M
materializes those templates, or find a state path that survives from
currentboot into normal runtime.

## The Response Hook Opens Up

The front-panel work also made the old readout pain impossible to ignore. The
first helper code-execution proof was clever but expensive: event `68` took
about a quarter second normally, about `0.85s` with a small delay, and multiple
seconds with larger delay loops. Turning that into a bit channel worked, but it
was still a one-bit-at-a-time conversation where a zero could mean deliberately
walking into the helper error path and then recovering the drive. It proved the
point, but it was not a pleasant way to map memory.

The next blocker was that normal `LD5M` runtime did not seem to use the visible
handler bytes we were patching. A persistent F0 hook could be written and
verified in flash, but EXTRAINQ still looked stock. The crack came from
currentboot instead. After installing a resident hook and doing a real hardware
cold boot with the Pico servo power switch, the drive would enter the visible
currentboot INQUIRY/EXTRAINQ handler after the event-1 profile-tail command.
Software resets and host rescans were not the same thing here; the full
power-cycle made the newly written resident bytes take effect.

The useful hook point is tiny: in the currentboot identity handler, patch the
final `LCALL 0x6206` response-copy call at code `0x4fc9`. The payload writes one
byte into the response staging area, calls the original copy routine, and
returns. The first proof wrote a literal `X` into response byte `0x20`, so the
drive identified itself as `XD5C` instead of `0D5C`. That was the moment the
readout changed from "watch how long a command takes" to "put a byte in the
SCSI response."

That byte channel quickly grew into two useful readers:

- a controller-gateway reader, where CDB bytes choose a 24-bit controller
  address and INQUIRY returns the selected byte;
- an XDATA reader, where CDB bytes choose a 16-bit 8051 XDATA address and
  INQUIRY returns the selected byte.

The controller-gateway reader needed one subtle fix. The first versions always
returned a stale `0x05`. The resident code hinted at the missing ritual: after
setting `0x4091..0x4093`, do a throwaway `0x4098` read, wait for `0x4000.7` to
clear, then read `0x4098` again. With that in place, reading controller address
`0x018620` returned the expected string:

```text
Flash Type Error
```

That is the same region we had only seen through READ BUFFER status windows
before, now available through a parameterized currentboot INQUIRY request.

The decoded CDD mystery did not immediately fall over. Reading the advertised
descriptor range around controller `0x184000` still returns zeros in this
currentboot-helper phase. So the descriptor's `0x184000..0x1b4000` range may be
real but unpopulated here, or it may require a different controller mode or
normal runtime context. Either way, the new reader made that negative result
cheap and firm instead of an all-evening timing-channel ordeal.

The XDATA reader paid off immediately. It confirmed Claude's hazardous
`xdata[0x4704].0 = 0` observation without using the `DID_ERROR` path at all,
then turned the Pico button line into a simple differential scan. With GP27
released versus pulled low, `xdata[0x4814]` consistently changed:

```text
released: d9
low:      c9
change:   bit 4 cleared
```

`xdata[0x48f7].7` also follows the button, but `0x4814.4` is the cleanest front
eject button-sense candidate so far.

This is a major practical shift. We still do not have a normal-runtime debugger,
and we still have not found the LED output latch or a decoded CDD dump. But we
can now ask the currentboot firmware byte-sized questions directly through SCSI
instead of staging a whole firmware image and timing a branch for every bit.
That should make the next round of mapping much faster, and it gives us a much
better bridge between static guesses and live hardware behavior.

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

The servo power switch then gave us a cleaner way to ask what persistent flash
changes do after a real cold boot. The answer was surprisingly strict. An
`INQUIRY` hook visibly persisted in F0, but after a true `+5V` cut Linux still
saw normal 5 ms `INQUIRY` timing. A timestamp byte in the identity/profile area
also persisted across the same cold boot, but live EXTRAINQ continued to report
the stock `2016/10/18` timestamp while direct F0 readback showed our temporary
`3016/10/18` edit. So the helper-bypass writer is genuinely changing flash, but
some normal host-visible state is coming from a different runtime/controller
source rather than these obvious F0 copies.

Then we tried the matching low-prefix currentboot identity record. This one did
matter. Changing the lower `0D5C2011/04/28` string to `0D5C3011/04/28`, cutting
power, and entering currentboot made EXTRAINQ report the patched `3011` date.
That gives us a sharper mental model: normal LD5M identity is not coming from
the high profile copy, but the currentboot personality really does consume the
lower prefix record.

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

The operation key also seems to determine the source span. Across the six
DS-8ABSH samples in the repo, 2,135 unique operation keys appear and none maps
to more than one source length. One obvious partial length field is:

```text
length_base = u16le(operation_key[2:4]) >> 4
```

That is exact for 106 records and close for many more, so bytes 2 and 3 are
probably part of the length coding even if they are not the whole formula.

The short records expose a more tangible source-unit shape. For the `0x0d`
operation, the source is four 13-byte units. For the `0x0c` operation, it is
four 12-byte units. The first byte of each unit behaves like payload: for many
shared record indices the same four first bytes appear in all six images. The
rest of the unit is a constant image/profile-specific tail. That makes these
look less like compressed ordinary code and more like a controller-specific
codeword or packed-record representation.

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

The latest static pass found two more record-level clues. First, the CDD1
post-directory table/control window behaves like decoded address material: if
you read it as little-endian 16-bit words and shift each word left four bits,
every value lands inside the explicit `0x30000` decoded range. CHS7 and CHS9
share 189 same-position words in that table, so it is versioned structure, not
random aux data.

Second, operation-key byte 3 now looks like a decoded span field:

```text
decoded_span = (operation_key[3] & 0x3f) << 4
```

That field sums to almost exactly the descriptor's decoded size across the
sibling images. CHS9 lands at `0x2ffd0`, only `0x30` short of `0x30000`; CD12
is `0x2fe50`, AD12 `0x2fc20`, CHS7 `0x30350`, and AHS9 `0x30720`. LD5M is the
looser outlier at `0x2e3b0`, but still in the same neighborhood.

Then the two clues clicked together. If we lay the CDD records out in order
using that decoded-span candidate, every shifted word from the CDD1 table lands
inside one of the candidate decoded record intervals, for every DS-8ABSH sample
we have. That is a strong validation that the table and the operation-key span
field are talking about the same decoded address space.

One more split made the table more useful. Its first 128 words behave
differently from the rest: they carry all of the high/mid decoded paragraph
targets and stable repeated runs like `0x0d01` repeated 16 times at table
indices 16..31. The tail after that is mostly low decoded offsets and has no
adjacent repeats. The front points into later candidate decoded records, while
the tail points into the early decoded records. I do not want to over-name it
yet, but the front now looks vector/entrypoint/control-table-like, while the
tail looks like a different offset list.

That gives us a more principled runtime-read shortlist too. If we sample decoded
controller space again, addresses like `0x191010` (the `0x0d01` x16 target) or
`0x198900`/`0x199030` (x4 front-table targets) are better probes than random
offsets.

I turned that into a JSON record map alongside the markdown report. It is not a
decoded firmware image, but it is a practical skeleton: each record now has a
source file range, operation key, mode bits, candidate decoded range, and any
CDD1 table entries that target inside it.

This also explains the visible 13-byte motif runs. The common
`0d6840031a00` operation consumes four 13-byte source units, `0x34` bytes
total, but the candidate decoded span is `0x30`: four 12-byte units. That
extra byte per unit now looks like parity, check, or control material rather
than decoded payload. The related `0c6000031800` operation consumes four
12-byte units and also spans `0x30` decoded bytes.

The high two bits of that same byte look like mode flags. They split the record
set into different redundancy classes: roughly 2x encoded/decoded for mode
`0x00`, 3x for `0x40`, 5.7x for `0x80`, and a rare high-ratio `0xc0` mode
that looks more control-like. That is another hint that this is a packed
controller grammar with checks/codewords, not a single encrypted blob.

The CDD object is looking less like encryption and more like a
controller-specific packed/codeword stream: directory records point to encoded
source spans, operation keys describe how much decoded material is produced,
and the table window likely carries decoded-space addresses or control
targets. We still do not have a decoder, but the problem has narrowed from
"what cipher is this?" to "what is this record grammar?"

## Pre-Tail Shortcut Attempt

The decoded CDD question pushed us back toward runtime visibility. The current
helper hook can read the controller gateway, but those decoded-address probes
returned zero at event `68`, which is still inside currentboot. The obvious
shortcut was to move the same hook earlier: mutate only the normal/pre-tail
event-1 helper payload and see whether it runs before the drive enters
currentboot.

That was a clean negative. Event `1` accepts mutated pre-tail payload bytes and
still transitions the drive into `0D5C`, but constant timing payloads at the
known late-helper hook did not split, and a force-error payload still returned
GOOD. In plain terms: the bytes are accepted there, but the branch we know how
to hijack is not executed there.

That closes the easy version of the pre-tail route. The next route is a real
resident LD5M command hook: patch a live normal-mode SCSI handler, trigger it
from the host after recovery, and use that as the vantage point for decoded CDD
or controller memory.

We tried the most direct version of that too. The helper-bypass writer patched
two normal-looking resident handlers in the visible F0 prefix:

```text
0x5c72  REQUEST SENSE handler
0x4ec6  INQUIRY handler
0x6ee3  FF code cave for a small timing stub
```

Both hooks persisted. Delayed F0 readback showed the `LJMP 0x6ee3` patch and
the delay stub in flash. But neither host command slowed down, even after SCSI
reset, USB bridge deauth/reauth, and a full reboot of the Linux host. After
that negative result, we restored the patched range and verified
`0x0000..0x7000` matched stock LD5M byte-for-byte.

That is a useful boundary. We can write the visible F0 prefix, but at least
these obvious standard-command handlers are not the live normal-mode execution
path. The "resident hook" route probably needs a RAM/overlay hook, or we need
to move to a hardware-visible runtime signal path instead of waiting for a
host-visible SCSI command response.

## From One Bit To Whole Pages

The next breakthrough was less glamorous than "decrypt the CDD" but much more
practical: we stopped trying to make the helper report data by deliberately
failing. The old bit channel worked, but it was painful. To learn one bit, we
had to build a helper payload, run part of the currentboot update sequence, see
whether the drive took the success or error path, and often run recovery. A
single byte could take many seconds and a full 64 KiB XDATA sweep was more of
an overnight experiment than a normal debugging move.

The Pico servo power switch mattered here. A Linux host reboot or USB reset is
not the same thing as a drive cold boot; some of our resident F0 changes only
became meaningful after the drive actually lost `+5V`. The little servo pressing
a microswitch in the spliced USB power line gave us a repeatable hardware cold
boot without waiting for a human replug. That made it practical to install a
resident hook, cut power, enter currentboot again, and see which copy of the
firmware was really being executed.

The key hook is in the currentboot INQUIRY/EXTRAINQ response path. We patched
the final response-copy call at `0x4fc9` to jump into the `0x6ee3` FF cave,
write data into the response, call the original `0x6206`, and return. First it
just wrote one constant byte: currentboot revision `0D5C` became `XD5C`, which
was the first clean host-visible proof that our code was running and talking
back over ordinary SCSI.

Then that became an addressable byte reader. The hook reads CDB parameter bytes
left in `xdata[0x818a..]`, uses them as an address, and returns one XDATA byte
or one controller-gateway byte in response byte `0x20`. That immediately
confirmed earlier slow-channel clues like `xdata[0x4704].0 = 0`, and it found
the front-panel button sense candidate without sled-moving experiments:

```text
GP27 released: xdata[0x4814] = d9
GP27 low:      xdata[0x4814] = c9
```

There was one more blocker before this became really useful. My first bulk
reader copied bytes directly into XDATA, but the host response buffer is not
plain XDATA. The stock code writes response bytes through the controller path
at `0x4095..0x4098`, with `FUN_CODE_6012` as the byte writer and `FUN_CODE_6206`
as the final copy/kick. Once the bulk hook used that same `0x6012` helper for
each byte, it worked: one INQUIRY CDB can now return 128 XDATA bytes.

That changes the pace of the project. A full 64 KiB currentboot XDATA dump now
takes seconds rather than thousands of tiny proof runs. The first dump has:

```text
file   references/evidence/live/linux-drive1-currentboot-xdata-0000-ffff-bulk-v2.bin
size   65536
sha256 6862a4c5ddceab9fa6b9e490ff3b14bd4447fe039f0ad2e3556b0d3761fb5d82
```

This still does not magically expose the decoded CDD: the controller
`0x184000` range remains zero in this currentboot phase. But it gives us a real
instrument for mapping the 8051's live state, finding hardware latches, checking
which status bytes move, and designing the next hook from evidence rather than
single-bit guesses. It is the first point where poking around inside the drive
starts to feel like debugging instead of divination.

We added the same idea for the controller gateway too. That path has a small
pipeline quirk: the first returned byte is stale, so the host-side reader asks
for one byte before the desired range and drops it. With that compensated, bulk
gateway reads recover known helper text like `Flash Type Error` at `0x018620`.
They also confirm the awkward negative result at useful scale:
`controller[0x184000..0x184fff]` is still all zero in currentboot. So the
gateway-bulk tool is real, but the decoded CDD likely needs a later runtime
phase, not just a faster read of the same early phase.

## The LED Is Probably Not A Simple Latch

With the bulk reader working, the obvious next dream was a fast hardware-visible
channel: make the drive blink the front LED under our control and let the Pico
read bytes quickly. The front board wiring is simple enough from the outside:
one line sees the LED, one line can pull the eject button low, and the Pico can
sample both.

The button side mapped cleanly. Pulling the eject line low changes
`xdata[0x4814]` from `d9` to `c9`, so bit 4 is a real front-panel button sense.
The LED side was not so kind. Direct 8051 GPIO-style probes were negative, and
some XDATA probes near `0x4748` and `0x4780` affected recovery state without
behaving like a controllable output.

The static pass made that result less disappointing. `0x4748` sits inside a
controller transaction path with command bytes at `0x474d/0x474e`; stock code
clears and sets bit 7 as part of asking the controller to do work. `0x4780`
belongs to the same broad hardware-initialization fabric. So those registers
are clues to the controller interface, not LED latches.

The better interpretation is that the visible 8051 sees a front-panel/status
byte and can talk to the controller, but the raw LED behavior is probably owned
by the controller/CDD side. That leaves three plausible routes: map the
controller command vocabulary around `0x474d/0x474e` and `0x482b`, find a later
runtime hook where natural LED transitions can be correlated against live
state, or use a different hardware channel entirely. The new cross-reference
report gives us a ranked map instead of a list of superstition-driven poke
targets.

## A New Blank-Currentboot Failure Class

The next LED probe found a useful hazard boundary. A delay-only helper payload
at the event-68 hook did exactly what it was supposed to do from the host's
point of view: event `68` returned GOOD, and the Pico saw the LED/front-panel
line rise during the helper window. But the drive did not settle into ordinary
`0D5C` currentboot afterward. Its identity kept the PLDS model string while the
revision and EXTRAINQ tail went mostly zero.

That matters because this is not the old, solved `0D5C` state. The known
recovery script starts by sending the currentboot profile tail before bank 0;
blank-currentboot rejects that tail with `Parameter value invalid`. It also
rejects the normal event-1 pre-tail. On the other hand, it still accepts
ordinary `arg=00` chunk staging and readback. We staged bank-2 chunks
successfully, but the matching bank pMac rejected, so the control/finalize side
is out of sync even though the data staging side is alive.

The new Pico servo command helped rule out easy explanations. A Linux host
reboot, an 8-second servo cold boot, and finally an explicit Pico `ALLZ` plus a
30-second servo power cut all came back to the same blank revision. A non-write
exit pass through TEST UNIT READY, REQUEST SENSE, START STOP variants,
`PLDSVUC` lock/unlock, `DF 0D/11`, and `sg_reset` also left it blank.

So the practical lesson is simple: event-68 helper probes can leave a state
that is neither normal LD5M nor the known recoverable `0D5C`. A full manual
unplug of both the Pico and the drive did not clear it either, which made it
feel uncomfortably persistent for a while.

The recovery turned out not to be a reset at all; it was a third protocol
dialect. The blank EXTRAINQ response had lost the normal `EXTRAINQ` marker, but
it still carried a usable slot-5 AES key at bytes `0x9c..0xab`, with the
familiar `"LD50"` tail. A profile-tail payload rebuilt under that key returned
GOOD. After that, bank 0 staged and crossed its pMac boundary. The next tail
failed, which exposed the pattern: the key bytes change after bank boundaries,
so the tail has to be rebuilt from the current malformed EXTRAINQ before each
bank.

Bank 2 was the decisive test because it is the AES-selected bank. Rebuilding
bank-2 chunks and the pMac under the active slot-5 key worked; after that, the
remaining banks could use plain LD5M chunks while carrying the bank-2 pMac
through every boundary. I wrapped that into
`recover_liteon_blank_currentboot_linux.py`, resumed from bank 3, and the drive
completed through bank 15 and final `PLDSVUC`. A Pico servo cold boot came back
as normal `LD5M`.

The recovered F0 image is not byte-identical to the original stock LD5M
baseline, but it is not random damage. It matches the deliberate
`currentboot-response-hook-gateway-cdb-bulk` candidate: a jump at `0x4fc9` into
the `0x6ee3` code cave, where the currentboot response hook lives. So the state
of the project after this recovery is better than before the wedge: we have the
blank-currentboot exit path, and the useful currentboot bulk-read hook is still
installed.

## The Gateway Map Has A Better Target Than 0x184000

After recovering from blank-currentboot, I used the still-installed
gateway-bulk hook for a broader controller-memory map. The original hope was
still the descriptor's decoded CDD range around `0x184000`, but a larger bulk
read settled that: in this currentboot phase, `0x184000..0x1b3fff` is just
zero. Not stale, not one weird page; the whole sampled CDD window is blank.

The useful result was elsewhere. A sparse sweep over `0x000000..0x1fffff`
showed live windows at `0x070000`, `0x074000`, `0x078000`, and `0x07c000`, with
matching mirrors at `0x170000`, `0x174000`, `0x178000`, and `0x17c000`. Dumping
the full 64 KiB starting at `0x070000` produced a new artifact:

```text
file   references/evidence/live/linux-drive1-currentboot-gateway-070000-10000.bin
size   65536
sha256 5f517adeab1647dbedf7b93f8be097b1641164fd49e87776364b9e134b9cbc0b
```

This blob is not a plain static slice from the firmware files we have in the
clean repo. It has live profile and calibration-looking text:
`PLDS CORPORATION`, `KEYPARA`, `CDROM`, the media profile names, and a
drive-specific-looking serial string. More importantly, big parts of it
disassemble cleanly as 8051. It references the controller FIFO registers
`0x4000` and `0x4098`, the event/status area around `0x47xx`, and the same
`0x59xx` hardware cluster that made the sled twitch during LED experiments.

That gives the LED story a much better shape. We probably were not missing a
simple output latch. The code that touches `0x5904`, `0x5905`, `0x5906`, and
neighbors is real controller/runtime code, and it sits among broader
hardware-initialization routines. Random writes there are exactly the kind of
thing that would move mechanics instead of blinking a nice debug LED. The next
LED/front-panel work should therefore be guided by this gateway/runtime map,
not by brute-force bit pokes.

I recovered the drive immediately after the map run with the standard
currentboot recovery script; standard INQUIRY was back to `LD5M`.

The deeper offline pass sharpened that story. The `0x070000` dump is not the
decoded CDD image we were hoping for. Its tail is a copied CDD work area:
gateway offset `0xf000` exactly matches F0 `0x704c..0x7deb`, the first CDD1
post-header directory/table bytes; `0xfc20` exactly matches the duplicated CDD2
prefix from F0 `0xd9020`; and `0xff00`/`0xff80` repeat the CDD header. That is
still useful, just in a different way. We now know this gateway can show the
controller's currentboot work buffers, but the decoded `0x184000..0x1b3fff`
runtime payload is not present in this phase.

I added a repeatable analyzer for this artifact:
`scripts/analyze_liteon_gateway_runtime.py`, plus a short
`analysis/8051/servo-mechanics-static-notes.md` side note. The report also
found exact overlaps with the resident 8051 and profile-tail helper, including
the hardware setup routine at F0 `0x59f3` reappearing at gateway offset
`0x6059`. That makes the sled side quest much more concrete. The cluster around
`0x5904`, `0x5905`, `0x5906`, `0x592a`, `0x59f0`, `0x5a00`, `0x5a24`, and
`0x5a31` is now the main static target for movement/focus/laser control. The
next move there should be reverse-engineering the state machine around those
routines, not poking them live one bit at a time.
