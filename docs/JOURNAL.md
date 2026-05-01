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

The next live test made that split sharper. Instead of patching individual
command handlers again, we patched two broad visible helpers: the response-copy
routine at `0x6206` and the packet-intake routine at `0x542b`. If the normal
commands were quietly using the visible currentboot command path, one of those
hooks should have made several commands slow down.

Both hooks persisted. Neither changed normal LD5M timing. But the `0x6206`
hook did slow the next currentboot write run, which is exactly the kind of
negative result that tells a clean story: the visible path is real and live in
currentboot, while ordinary normal-mode responses are coming from somewhere
else.

Afterward we restored the low-prefix hooks and cave to stock and verified
`0x1000..0x6fff` byte-for-byte. The drive is back in normal `LD5M`.

A later source-localization test narrowed this further. The currentboot XDATA
dump contains the normal-looking model string at `xdata[0x811e]`, which made it
a tempting candidate response source. With the guarded XDATA write hook
installed, I changed that byte from `D` to `X` and read it back successfully.
The following currentboot identity response still used the canonical
`DVD+-RW DS-8ABSH` string; only the hook's explicit readback byte changed. That
means `0x811e` is real writable state, but not the live identity template.

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
total, but the candidate decoded span is `0x30`: four 12-byte units. A peer
static pass caught an important correction here. The first byte is not just
throwaway parity, and our first "m byte" model was still one level too shallow.
The real mask table is:

```text
cell: 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f
mask: 00 19 32 2b 64 7d 56 4f c8 d1 fa e3 ac b5 9e 87
```

That table is carry-less multiplication by `0x19` over the 4-bit cell index.
For a short record, the cell is:

```text
cell = 4 * (record_index & 3) + unit_index
plain_group_byte = raw_cell_byte ^ mask[cell]
```

This turns adjacent short records into observations of one group byte rather
than independent row-local values. For example, record 423's raw first bytes
`28 31 1a 03` use cells 12..15 and all decode to `0x84`.

Then Pro's bigger observation held up: the same canonical unit tail appears as
suffix cells inside longer records. That means some long records are partly
decodable too. In CHS9, record 108 ends with three canonical-tail units whose
first bytes decode as cells 1..3, and records 109..111 supply cells 4..15; all
15 observations agree on group 27 = `0xe4`. This is the first real static
decode of bytes out of long CDD records, even though it is still only a thin
suffix-cell layer.

The suffix layer has structure but is not fully solved. Across six sibling
images, there are 115 suffix records: 49 with one trailing unit, 37 with two,
and 29 with three. All have `op_key[5] == 0`; excluding the noisy CDD1/CDD2
boundary group, `op_key[4]` remains the doubled unit size, and every two- or
three-unit suffix uses the same `0x30` decoded-span field as the short records.
That is enough to keep decoding literal tail evidence, but not enough to claim
the op key alone predicts suffix length.

There is also a useful caution here. The affine byte is definitely real
structure, but we should not over-name it yet. It might be a semantic group
byte, a parity/control byte, or one visible lane of a broader controller
codeword. The short-record span still says `0x30` bytes, so one good runtime
oracle for a known short record would tell us whether the canonical tail is
actual decoded output, scaffold, or something stranger.

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

A parallel raw-disassembly check helped clean up the static footing too. The
quick Ghidra C export is useful, but it is not the thing to trust for exact
XDATA flow. Looking directly at `analysis/8051/ldm58051.bin`, the CDD parser
really does package header fields into `xdata[0x4a00..0x4a29]` and issues
controller command/status work through `xdata[0x4e80/0x4e84/0x4e88/0x4e8c]`
while polling `xdata[0x4ea0]`. That supports the model that the visible 8051
sets up a mailbox and waits; the actual CDD body expansion still seems to live
on the controller side.

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

The recovered F0 image was not byte-identical to the original stock LD5M
baseline at first, but it was not random damage. It matched the deliberate
`currentboot-response-hook-gateway-cdb-bulk` candidate: a jump at `0x4fc9` into
the `0x6ee3` code cave, where the currentboot response hook lived. That was a
useful temporary state, and it let us keep mapping currentboot memory. A later
normal-mode hook phase restored `0x4fc9`, `0x6206`, `0x542b`, and the `0x6ee3`
cave; the post-restore F0 dump over `0x1000..0x6fff` matched stock LD5M with
zero diffs.

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

## A Combined Hook And A Doorbell Negative

The latest currentboot hook folds two tools into one. Instead of installing one
F0 image to read the controller gateway and another to write XDATA, the v2 hook
does both. Ordinary parameterized INQUIRY commands bulk-read 128 bytes from the
controller gateway. If the same host command carries guard bytes `a5 5a`, the
hook writes one chosen byte into XDATA and returns the readback byte. Internally
currentboot stores those two guard bytes reversed in its CDB shadow, which is
why some low-level notes describe the observed shadow as `5a a5`.

That sounds like a small convenience, but it changes the shape of experiments:
we can now set a currentboot control byte, immediately read the controller-side
effect, and then restore the byte without reflashing a different helper. The
first version tried to use CDB byte `6` as part of the guard; live testing
showed that byte is not reliable in this handler. Bytes `7..11` are the useful
parameter window.

The first target was the CDD mailbox. Static 8051 analysis says the resident
CDD parser writes header/control fields into `xdata[0x4a00..0x4a29]`, with
`0x4a00` looking like a controller doorbell. The v2 hook successfully wrote
`xdata[0x4a00] = 1` and read it back. Then it sampled the decoded CDD base and
the better affine-derived oracle targets: group 27 at `0x190690`, group 78 at
`0x1a63a0`, and group 99 at `0x1aeb80`.

Everything in the decoded range stayed zero. The known live `0x070000` gateway
window stayed nonzero and unchanged, so this was not a broken reader. The
single doorbell byte is just not enough. Either the controller needs a fuller
CDD command sequence, the currentboot phase is missing state that normal boot
sets up, or the actual body expansion lives behind a different hidden
transition.

This is a good negative. It rules out a tempting "poke the obvious mailbox bit"
shortcut and leaves the next decoded-CDD route clearer: find a later runtime
hook, model the complete CDD parser/controller handoff, or keep digging into
the static record grammar until we can predict a more exact control sequence.

On the static side, that grammar got sharper too. The affine-unit decoder now
handles full rows, prefix runs, and suffix runs of the canonical unit tail. The
old conflict around group 96 disappeared once record 387 was treated as a
prefix run; it decodes cleanly to `0xd8`. All confident affine observations so
far land in one lane of a 12-record macro schedule, with 624 cell observations
and zero conflicts. That still is not a full CDD decompressor, but it is real
structure and a better map for future oracle reads.

## Lane 0 Is Special

The next static pass asked whether we were just being too conservative about
that affine leaf. Maybe lanes 1 and 2 had the same repeated-tail unit grammar,
but with a different unit size or a different prefix/suffix placement. I wrote
a broader lane-schedule scan for that: for every source record, try unit sizes
from 4 to 40 bytes, look at prefix and suffix edge runs of two to four units,
and ask whether the unit lead bytes satisfy the same 16-cell affine masks.

The answer was cleanly negative in a useful way. The scan found 718
edge-affine hits, all in macro lane 0:

```text
hits by macro lane: {0: 718}
hits by unit size:  {12: 231, 13: 487}
lane 1/2 hits:      0
```

The repeated-tail grammar really is a lane-0 surface. Lanes 1 and 2 are not
hiding the same trick at their record edges. They likely carry their useful
content in the high-entropy body, or use a different controller-side codeword
grammar entirely.

The close-sibling comparison is still encouraging. CHS7 and CHS9 keep the same
operation key and source length for most records in all three lanes. In those
same-operation records, about 72% of source bytes are identical, and the bytes
that change are dominated by one-bit XOR deltas like `0x80`, `0x01`, `0x02`,
and `0x40`. The changes are spatially local too: about 60% of contiguous diff
runs are a single byte, about 88% are one or two bytes, and about 98% are four
bytes or fewer in every lane. That is a very poor fit for encryption
avalanche. It looks more like a deterministic, localized codeword stream where
version changes perturb nearby coded bytes.

So the CDD picture has narrowed again: lane 0 exposes a real affine leaf layer,
while lanes 1 and 2 are the harder packed/ECC-like body. The next static work
should classify those lane 1/2 operation-key fields and diff locality, not keep
searching for more copies of the lane-0 motif.

## Operation Keys Are Real Selectors

The follow-up operation-key pass made that last sentence more concrete. The
six-byte key derived from each directory entry is not just decorative metadata:
across the six sibling images, all 2,135 unique operation keys map to exactly
one encoded source length. So the controller likely has a real per-key packet
grammar, even though the directory also stores source starts.

There were useful negatives too. Letting the lane-schedule scanner choose any
carry-less affine multiplier did not uncover a hidden lane-1 or lane-2 version
of the repeated-tail grammar. The only complete affine rows are still lane 0,
still multiplier `0x19`, and still 12- or 13-byte units.

The operation key also does not expose source length as a simple bitfield. A
linear GF(2) probe found only the parity relation:

```text
source_len.bit0 = key[0].0 ^ key[1].3 ^ key[2].6 ^ key[4].1
```

Bits 1 through 11 of the encoded source length are not affine functions of the
raw key bits. And while `key[4] / 2` is exactly the unit-size hint for the
lane-0 affine records, it fails badly as a universal unit size in the hard
lanes.

That keeps the static CDD story in a narrower place: lane 0 gives us a proven
affine leaf, but the dense lanes are using a proprietary packet/codeword grammar
that is not just a disguised copy of the easy motif. The next likely unlock is
either a runtime oracle for one decoded record, or a deeper classification of
the hard-lane operation keys.

## The Mailbox Has Banks

One more resident-code pass tightened the controller-mailbox picture. The
visible 8051 command wrapper around `0x4e80/0x4e84/0x4e88/0x4e8c` had already
looked like a generic "write three pointers and ring a doorbell" path. Raw
disassembly showed the selector is more specific than that.

The helper at `0x1daf` shifts a 32-bit value left by `r0` bits. The mailbox
wrappers call it with `r0 = 0x15`, after loading a selector value into `r7`.
So selector values `0`, `1`, and `2` become offsets `0x000000`, `0x200000`,
and `0x400000`. The wrapper validates pointer ranges against a 2 MiB local
window, adds this bank offset to the first pointer, writes the command
descriptor, and sets `xdata[0x4e8c] = 1`.

That turns a vague mailbox into a more concrete banked controller-memory
surface. It does not decode CDD by itself, but it gives us better words for the
next runtime-oracle attempts: the advertised decoded CDD range
`0x184000..0x1b3fff` sits inside bank 0, and the same command family may expose
other banked views of the controller once we can call it in the right phase.

## Currentboot Gateway Is Only 20-Bit Here

The obvious live follow-up was to try those bank ideas through the currentboot
response hook's direct controller-gateway reader. The hook was still installed:
after sending only event 1, `controller[0x018620]` again returned `Flash Type
Error`, so no rewrite was needed.

The banked reads were cleanly negative for decoded CDD. `0x184000` stayed zero,
and so did `0x284000`, `0x384000`, `0x484000`, `0x584000`, plus the better CDD
oracle targets around `0x191010`, `0x198900`, and `0x1a0000` with the same bank
offsets. A broader 24-bit sparse scan explained why: this direct gateway path
mirrors every `0x100000` bytes in currentboot. It is not the same 2 MiB-banked
view used by the `0x4e80` command wrapper.

The scan still found useful live surfaces. A finer first-MiB pass showed:

```text
0x000000..0x006fff  high-entropy/live staging buffer
0x018000            active plain profile-tail helper overlay
0x06b000            low-entropy profile/serial-looking table
0x070000..0x07ffff  known mixed currentboot work/code/profile window
```

The new `0x018000` dump matches the official plain `ef130045` helper overlay
byte-for-byte. The new `0x000000` dump has an exact encoded-F0 overlap:

```text
gateway[0x002c..0x5554] == LD5M F0[0xe002c..0xe5554]
```

That range is encoded CDD stream 2, so this is not the decoded payload we want.
But it sharpens the map: currentboot already exposes the active helper and some
staging buffers quickly through SCSI, while decoded CDD likely requires either
a normal-runtime hook or a deliberate `0x4e80/84/88/8c` mailbox interaction.

## Normal READ BUFFER Opens The Same Window

The next surprise was that the `0x070000` work window is not currentboot-only.
In normal `LD5M`, plain public `READ BUFFER mode=1` with buffer IDs `0x01` and
`0x02` exposes the same class of controller/work memory directly. No currentboot
hook, no helper, no bit channel.

The first decoded-CDD hope was still negative: `id=01` and `id=02` return all
zeroes at `0x184000`, `0x184060`, `0x191010`, `0x198900`, `0x199030`,
`0x19c020`, `0x19c800`, `0x1a0000`, and `0x1a2fe0`. IDs `0xe2`, `0xf0`, and
`0xf1` just reject those high offsets.

But a sparse first-MiB scan found a normal-mode map:

```text
0x000000            small header, starts ff 54 54 45
0x06b000            low-entropy profile/serial table
0x070000..0x07ffff  mixed work/profile/code window
```

A full 24-bit sparse pass then showed that this public normal reader has the
same practical address-width limit as the currentboot gateway path: IDs `0x01`
and `0x02` mirror at 1 MiB granularity. The only 64 KiB slots with non-zero
64-byte samples were `0x?00000` and `0x?70000`; all the decoded-CDD candidate
addresses fold into zero-looking slots through this route.

An all-ID sweep tightened that map. At `0x070000`, only IDs `0x01` and `0x02`
respond. At offset zero, `id=0x00` returns a 64-byte Initio bridge descriptor,
while `id=0xe2` and `id=0xf1` expose named slices of the same `0x070000` work
window. `id=e2` is exactly work-window `+0x4000`; `id=f1` is exactly
work-window `+0x5000`, the `KEYPARA` media-profile table. An exhaustive
offset-zero scan of READ BUFFER modes `0x00..0x1f` found no other responders,
so the useful public variant remains mode `0x01`.

Then the length sweep caught a subtle but important miss: some handlers only
answer exact request sizes. `READ BUFFER id=f0` and `id=f2` both answer exact
`0x80`-byte requests. `id=f0` is the encrypted F0 readback path, but the raw
ciphertext is stateful: a stable pre-EXTRAINQ dump did not decrypt with the
current key, while a read taken immediately after live EXTRAINQ decrypted
cleanly to stock LD5M using the EXTRAINQ-derived AES-CBC key with `0x80` resets.
`id=f2` exposes encoded container material, starting with CDD2 and later showing
the identity/profile and trailer marker areas. It is useful, but still not the
decoded CDD runtime image.

The full normal `0x070000` dump has the familiar `KEYPARA`, media-profile
strings, `PLDS CORPORATION`, serial-looking material, and 8051-like code. It is
not byte-stable: repeated reads change bytes mostly in pages `+0x6000`,
`+0x8000`, and `+0x9000`. It also differs from the older currentboot dump in
exactly the places that look runtime-like, while retaining large identical
runs.

That gives us a better live-read primitive than we had at the start of the day.
It still does not give decoded CDD, but it gives normal-mode controller state
quickly enough to monitor experiments. It also brings the front-panel lead back
into normal mode: the dump has code at `+0x8005` reading `xdata[0x4814]`, the
same byte whose bit 4 tracked the eject button in the Pico/currentboot tests.

One more wrinkle matters for the next static pass. The visible F0-prefix
`READ BUFFER` handler accepts `01`, `02`, `e2`, `f0`, and `f1`, but not `f2`.
Live `f2` reads still work, even with a 12-byte ATAPI-style CDB. The answer was
in the normal work/code dump: around `+0x6747` there is a separate READ
BUFFER-like accept list that explicitly includes `f2`, with command bytes
apparently shadowed around `xdata[0x8a49..]`. That is annoying, but useful: it
tells us not to hunt for a decoded CDD branch in the wrong visible handler.

The next pass tightened that conclusion rather than opening a new public door.
An exact-`0x80` scan across high vendor IDs `e0..ff` found only the already
known responders: `e2`, `f0`, `f1`, and `f2`. The drive remained in normal
`LD5M`, so this is a safe read-only check we can repeat, but it does not reveal
another decoded-memory buffer. A second exact-size sweep over READ BUFFER modes
`0x00..0x1f`, limited to those four IDs, also found only mode `0x01`.

The static picture of the normal work window also got more honest. The
`0x070000` window is partly live work RAM: comparing six captures shows stable
code/table pages mixed with moving state regions. The useful `f2` accept list
at `+0x6747` is stable, and so is the packet copy path that reads from the
`0x47b1` FIFO into `xdata[0x8a49..0x8a4b]`. But the dense `+0xa2xx` dispatch
area is alignment-sensitive, and some branches land in the middle of the
obvious six-byte `MOV DPTR; LJMP` records. So the lesson is to trust the
accept-list and CDB-shadow evidence, but not to over-explain the downstream
branch targets from one linear disassembly.

One small public-buffer mystery closed cleanly after that. `id=e2` was not a
new decoder or a second controller image; it was a narrow alias into the same
normal work window. `e2:0` is `id01:0x074000`, and `e2:0x1000` is
`id01:0x075000`. Page-start reads from `e2:0x2000` upward reject. `id=f1` is
the same pattern from the second page: `f1:0` is `id01:0x075000`, but only for
`0x0b60` bytes. So `e2` and `f1` reach only the profile/table pages we already
know how to read, not the decoded CDD or the code-heavy tail of the work
window.

One more read-only `f2` wrinkle got checked before closing this path. Because
the drive accepts a 12-byte ATAPI-looking `READ BUFFER` CDB, we tried using the
two trailing bytes as possible hidden selectors. Values like `0001`, `5aa5`,
`a55a`, and `ffff` all returned the exact same 128-byte CDD2-header page as the
plain `0000` CDB, and the drive stayed in normal `LD5M`. That makes the public
`f2` surface less mysterious: it is an encoded-container view, not a selectable
decoded-memory portal hiding in the unused CDB tail.

The standard READ BUFFER control byte got the same treatment immediately after.
Changing `CDB[9]` to `01`, `02`, `5a`, `a5`, or `ff` also produced the same
`f2` page. So the easy selector-hunting on this public command is now pretty
well exhausted.

That pushed us back to the CDD mailbox path, but with a better question. The
old live test had written just `xdata[0x4a00] = 1`, hoping the obvious
doorbell might be enough. A raw 8051 pass showed why that was too hopeful. The
resident parser first pulls the early outer-descriptor fields into
`xdata[0x8244..0x8255]`: for LD5M those are `0x7000`, `0x4000`, `0x80000`,
`0x5000`, and mode word `0x4000`. From those it derives small controller
status/config bytes like `0x4e0d=0x40`, `0x4e1a=0x14`, and `0x4e1c=1`.

More importantly, the parser does not appear to read the CDD header straight
from flash. It adds the descriptor length to get `0x702c`, sets
`xdata[0x8256..0x8257] = 0xc000`, and runs the banked `0x4e80/84/88/8c`
command path before checking for `CDD\\x09 10 16` at `xdata[0xc000]`. That
makes `0xc000` look like a mapped XDATA window. Only after that does it package
the header-derived `0x4a01/03/05/06/20/21/22` fields and ring `0x4a00`.

So the failed one-byte doorbell test is not the end of this route. It just
rules out the most cartoonishly simple shortcut. The next live version, if we
choose to try it, is a field-only replay: write the derived `0x4a` package and
`xdata[0x8258..0x825b]`, ring `0x4a00`, then watch `0x4a24..0x4a29`, `0x4ea0`,
and the decoded CDD target addresses. A generated static plan now records the
exact values for that ladder of experiments.

I then made the live tooling less brittle before taking that shot. The newest
combined hook keeps the normal gateway-bulk read path, keeps guarded XDATA
writes on host CDB bytes `a5 5a`, and adds a guarded XDATA read path on host
CDB bytes `5a a5`. That means the field replay can now read back the `0x4a`
and `0x4e` status windows without installing a different hook. A runner script
wraps the whole attempt into one artifact: baseline samples, ordered writes,
after-samples, and a doorbell restore.

The first read/write version was too clever: it keyed the read and write modes
off a two-byte magic and the XDATA-read smoke test timed out, probably because
the command shadow did not preserve that pair the way the hook expected. The
replacement is deliberately simpler. Gateway mode only happens when both bytes
are zero; `CDB[10]=0xa5` means XDATA write; `CDB[10]=0x5a` means XDATA read;
other nonzero selector values return `0xee` instead of accidentally turning
into a controller-gateway read at some unlucky address.

That still was not enough: the smoke test showed the combined currentboot path
does not reliably carry CDB bytes `10` and `11` at all. So the next hook avoids
that end of the CDB entirely. It keeps the proven `CDB[7:9]` gateway-address
path, and reserves the fake address `0xfcdd00` as a trigger that writes the CDD
field package inside the hook itself. It is less general, but it uses only
bytes already proven to reach the hook.

That special trigger did execute: it returned the planned `0xcd` marker. But
the result was still negative. The decoded target windows at `0x184000`,
`0x184060`, and affine group 27 at `0x190690` were all zero before and after,
while the known live `0x070000` gateway window remained nonzero. So the field
package plus `0x4a00` doorbell is not sufficient in currentboot. The missing
state is now more likely in the descriptor prestate, the `0xc000` mapped-header
setup, or the higher-risk `0x4e8c` controller command path.

The next rung is ready but, at this point in the notes, not yet live-proven.
It is a deliberately compact "descriptor prestate plus field package" trigger.
The hook gives up the fast bulk gateway reader and falls back to one-byte
gateway reads, because the `0x6ee3` cave only has `0xdd` bytes. That buys room
to preload the nonzero descriptor-derived bytes around `xdata[0x8246]`,
`0x824a`, `0x824d`, `0x8252`, `0x8254`, status/config bytes at `0x4e0d`,
`0x4e1a`, and `0x4e1c`, direct bytes `0x60=1` and `0x61=ff`, then the same
`0x4a` CDD field package. The fake gateway address trigger is still
`CDB[7:8] = fc dd`, and the planned response marker is `0xce`.

The dry run matters because this path is tight: the payload is 215 bytes in a
221-byte cave. The runner now has a sample-length cap, so the first live shot
can read only a few dozen bytes around each decoded target instead of spending
minutes on byte-at-a-time 256-byte windows. If this still leaves the decoded
targets zero, the likely missing ingredient is no longer passive descriptor
prestate; it is either the real mapped-header setup through the
`0x4e80/84/88/8c` path or a later normal-runtime phase where the controller CDD
engine is actually awake.

That live shot found a tooling limit before it found a CDD answer. The one-byte
gateway version installed, but its first high-address baseline read timed out
before the trigger ran. A Pico cold boot recovered the drive. Rather than chase
that reader, I made a tighter bulk-reader variant: it keeps the proven fast
gateway path, drops the derived `0x4e` and direct-byte prestate, and fits by
writing only the descriptor-derived `0x824x/0x825x` bytes plus the same CDD
field package. It returned a new `0xcf` marker when triggered with the fake
`fc dd` gateway prefix.

That descriptor-trigger result was cleanly negative. The trigger executed, the
known `0x070000` gateway window still read correctly, but decoded CDD targets
`0x184000`, `0x184060`, and `0x190690` stayed all zero before and after. So the
missing currentboot ingredient is not just passive descriptor prestate. The
remaining live mailbox route probably has to exercise the real
`0x4e80/84/88/8c` mapped-header path, include more internal parser state in a
different hook shape, or move the readout into normal runtime after the CDD
engine has already been brought up.

The mapped-header shot was a real step forward. I added a new compact trigger
on fake gateway prefix `fc de` that mirrors the resident parser's setup for
`0x1717`: target `xdata[0xc000]`, source `0x0000702c`, and a 32-byte copy. It
returned a new `0xd0` marker and the response payload contained the actual
LD5M CDD header:

```text
43 44 44 09 10 16 53 0d 90 00 00 7d ec 03 08 10
87 0e 80 00 00 70 00 18 40 00 1b 3f ff 1b 3f ff
```

That proves the currentboot hook can call the real mapped-header helper and
read back the `0xc000` mapped window without wedging the drive. The decoded
target windows at `0x184000`, `0x184060`, and `0x190690` still stayed zero,
so `0x1717` alone looks like a source-header mapping/copy primitive rather
than the full CDD expansion. Still, the difference matters: we now have a live
way to exercise and observe one piece of the controller-side CDD path, instead
of only guessing from static structure.

I immediately widened that foothold by making a status-return variant on fake
gateway prefix `fc df`. It does the same `0x1717` mapped-header call, then
copies both `xdata[0xc000..0xc01f]` and `xdata[0x4e80..0x4e9f]` into the
host response. The CDD header came back again, and the status window after the
call was:

```text
000000000000000000000000010000000040704c0008001f0000000000000000
```

In address form, that means `0x4e8c = 01` and a compact nonzero cluster at
`0x4e91..0x4e97 = 40 70 4c 00 08 00 1f`. The decoded targets were still zero,
but now the question is sharper. We are no longer just asking "what wakes the
CDD engine?" We have a working currentboot call into the mapped-header path
and a small status/control snapshot to line up against the resident code around
`0x16ef`, `0x1717`, and `0x17bb`.

One wider status capture made that line-up much clearer. The `fc e0` trigger
returns `xdata[0x4e80..0x4ebf]` after the same `0x1717` call, and the important
bytes are:

```text
0x4e90: 00 40 70 4c 00 08 00 1f
0x4ea0: 06 00 00 00 9a d1 bb 4b 00 00 18 00 00 00 00 00
0x4eb0: 00 08 00 0f 00 00 00 00 07 00 00 00 00 00 00 00
```

The `0x4ea0 = 06` byte is exactly what the resident loop waits for. The
`0x4e90` row also fits the static model: `0x0040702c + 0x20 = 0x0040704c` and
`0x0007ffff + 0x20 = 0x0008001f`. So `0x1717` is no longer mysterious in the
same way. It issues a banked source-to-window transfer, waits for completion,
then `0x16ef` makes the `0xc000` window point at the result. The decoded CDD
range staying zero means the remaining missing step is downstream from this
header-map operation.

The next rung was to stop reimplementing individual fields and call the
resident parser setup itself. I added a compact `fc e1` trigger that seeds the
descriptor state expected by `FUN_CODE_002e`, calls `0x002e` with descriptor
base `0x7000`, then returns `xdata[0x4a00..0x4a3f]` in the INQUIRY response.
This also installed cleanly and returned marker `0xd3`. More importantly, the
mailbox came back populated:

```text
0x4a00: 01 03 00 03 00 14 07 00 00 00 00 00 00 20 00 13
0x4a10: 00 00 00 00 01 ea 00 00 01 00 00 00 00 00 00 00
0x4a20: 03 08 10 00 03 fe 00 00 00 00 00 01 00 0f 00 00
0x4a30: 00 07 0f 00 00 00 00 00 00 00 00 00 00 00 00 00
```

So the visible parser path is callable from currentboot, and it does build a
richer mailbox package than the earlier hand-written replay did. But decoded
CDD reads at `0x184000`, `0x184060`, `0x190690`, and several Pro-suggested
table targets were still all zero immediately after the trigger and again
after a delay.

That mailbox snapshot suggested one more obvious test. The later resident path
around `0x08d0` copies `0x4a24/25` into `0x4a28/29`, writes `0x4a00 = 1`, and
calls `0x1667`. I added an `fc e2` trigger that calls `0x002e`, then performs
that second-doorbell sequence directly. It returned marker `0xd4` and left the
drive recoverable, but decoded CDD targets still stayed zero even after a
delay. That closes a nice small loop: in currentboot we can call the mapped
header helper, observe its completion status, call the visible CDD parser, and
manually ring the later mailbox doorbell, but none of those paths materialize
the decoded controller range. The likely explanation is that the CDD expansion
engine is not actually active in currentboot; it is a normal-runtime facility,
or it needs additional controller state that this boot personality never
establishes.

That negative result pointed back at normal runtime. One surprise hiding in
plain sight is that normal `LD5M` exposes the same public
`READ BUFFER mode=1 id=01 offset=0x070000` work window without entering
currentboot. Earlier we had treated it mostly as a mixed table/code dump, with
some live bytes. A more deliberate stimulus pass showed it is livelier than
that: it behaves like a small rotating/pageable cache of 64-byte work/code
tiles.

I added a capture script that stays in read-only/no-data-out territory and
records that `0x070000` window after safe normal SCSI/MMC commands: ordinary
inquiry, EXTRAINQ, mode sense, get configuration, event status, TOC/disc/track
information, mechanism status, and DVD structure reads. A capture-only control
run then repeated the same `id=01` window dump fourteen times with no
intervening stimulus.

The comparison was clean. Repeated reads alone produced 704 informative unique
`0x40` chunks and showed the expected small rotation around pages like
`+0x6000`, `+0x8600`, and `+0x9500`. The safe-stimulus run produced 752
informative chunks. Every chunk from the capture-only control was present, plus
48 more chunks that only appeared after normal command stimuli. That means the
commands are not merely shuffling the same ring; they can pull additional
already-decoded runtime material into the public work window.

This gives the project a third readout route. We still have the static CDD
decoder work, and we still have the slow currentboot gateway/bit-channel path.
Now we also have a normal-runtime tile-harvesting path that may expose decoded
8051 overlays without asking the controller CDD format to give up all its
secrets at once. Public offsets are probably page-frame positions rather than
stable logical addresses, since the same chunk can appear in multiple slots,
but the corpus is real and reproducible. The immediate next step is to expand
the stimulus set carefully, repeat each command family enough times to build a
larger unique-tile corpus, and start correlating harvested chunks with the
known static disassembly.

The first expansion run was encouraging but also sobering in the right way. I
repeated the highest-yield safe stimuli for eight cycles: EXTRAINQ, mode sense,
get configuration, and event status. The drive stayed normal. The focused run
produced 751 informative chunks, 15 of which were new relative to the earlier
full-stimulus pass. Taken together, the capture-only, full-stimulus, and
focused-stimulus runs give 68 captures and 767 unique informative 64-byte
chunks. So this is a real harvest path, but it probably saturates by command
family. More progress will come from broader stimulus coverage and better
correlation/disassembly, not just looping the same few commands forever.

The broader one-cycle expansion was worth doing. I added more safe information
commands: read capacity, format capacities, individual mode-sense pages, more
event-status classes, TOC/DVD-structure variants, and get-performance. Several
of these quite reasonably came back as CHECK CONDITION or ILLEGAL REQUEST with
no disc, but the drive stayed in normal `LD5M`, and the follow-up window
captures completed. This added another 18 aggregate chunks. The normal-window
corpus now stands at 94 captures and 785 unique informative `0x40` chunks.

The first static correlation makes the result feel less like a bookkeeping
trick. Exact 64-byte matching against the known 1 MiB LD5M F0 image finds only
63 matching chunks, and exact matching against the extracted visible 8051 prefix
finds only 8. The rest is not automatically "decoded servo firmware"; the
public window also includes profile tables, strings, and live work state. But
the important bit is that most of this corpus is not simply present verbatim in
the static F0 image. Normal runtime is exposing material we did not otherwise
have byte-for-byte.

One quick disassembly-adjacent pass made that more concrete. I scanned the
harvested chunks for the 8051 `MOV DPTR,#xxxx` opcode pattern. It immediately
found the expected old friends: `0x47b1`, `0x4000`, `0x4091`, `0x4098`, and
`0x825b`. But it also found high-frequency references that are not present as
DPTR immediates in the known F0/visible-8051 references, especially the
`0x8a23` and `0x8a4a..0x8a54` cluster. That lines up with the earlier
normal-window static read: the live normal READ BUFFER handler seems to use a
packet/CDB shadow around `xdata[0x8a49..]`. Now we have runtime chunks touching
that shadow directly.

The latest cleanup pass turned those captures into an overlay map instead of a
bag of bytes. Across 94 normal-runtime snapshots, the public work window has
702 informative `0x40`-byte slots, 785 unique informative chunks, and 159
chunks that show up at more than one public offset. Only 63 chunks match the
known LD5M F0 image exactly. The rest is runtime-only material, live tables, or
state.

The most satisfying result is a little command-ingress loop hiding in plain
sight. One harvested chunk repeatedly copies from `xdata[0x47b1]` into
`xdata[0x8a4c..0x8a50]`. That fits the earlier suspicion that `0x47b1` is the
packet/FIFO port and that the `0x8a49..` area is the normal-runtime command
shadow. In practical terms, the public normal-mode window is now giving us
already-decoded live code and tables that the static F0 image did not expose
verbatim.

There is also a large dispatch-looking island around public offsets
`+0xa180..+0xad40`. The first naive scan ranked it as "code-like", but the
overlay analyzer now labels the dense `LJMP`/branch-plus-DPTR patterns as table
material. That matters for tomorrow: the obvious next target is not to
linear-disassemble the whole island, but to decode its table entries and
connect them to the packet-shadow chunks around `0x8a4c`.

The next pass did exactly that: instead of looking at chunks as isolated
tiles, it scanned whole captured windows for short `MOVX` copy idioms. That
fixed a subtle alignment issue and turned the packet-shadow story into a
proper path.

The shape now looks like this. The drive reads bytes from the `0x47b1`
port/FIFO into a normal-runtime shadow around `xdata[0x8a49..0x8a54]`.
`0x8a49` is treated like the selector/opcode byte and is compared against a
long list of command-like values. `0x8a23` is a busy state/flag byte that gets
masked and ORed in many handlers. Then parts of the shadow are copied into
controller-facing registers: `0x8a4c..0x8a4e` feed `0x4011..0x4013`,
`0x8ac6` feeds `0x4091/0x4095`, `0x8a4e/0x8a53/0x8a54` feed `0x4099`, and
the `0x4095..0x4097` setup bytes are mirrored back into `0x8ade/0x8aeb/0x8aec`.

That is a real bridge from "host sent a packet" to "controller register
traffic happened." It does not yet give us a hook, but it narrows where a hook
should live. We are no longer searching the whole normal runtime; we are
looking at the packet ingress/shadow/controller handoff corridor.

I also ran four small read-only command-specific captures on the Linux drive:
EXTRAINQ, GET CONFIGURATION current, MODE SENSE all, and GET EVENT STATUS
media, each alternating with local baseline captures. The drive stayed normal
`LD5M`. These short runs were mostly dominated by ordinary window rotation,
but GET CONFIGURATION current gave the clearest recurring stimulus-only chunks
with target references, particularly around the `0x4099` controller bridge.
That makes it the best candidate for a longer dedicated capture if we want to
tag this path more precisely.

The morning follow-up decoded the big branch-looking island more carefully.
The first pass had only marked `+0xa180..` as suspicious; widening the parser
showed it is a much cleaner structure than that. Starting one byte before the
chunk boundary, at `+0xa17f`, there are 1,762 regular entries before ordinary
bytes resume at `+0xcaab`.

The first 32 entries are tiny selector stubs: "load A with selector 0..31, then
jump to `0x0162`." The remaining 1,730 entries are "load DPTR with a 16-bit
parameter, then jump into one of a small set of low `0x01xx/0x02xx` helpers."
Those low targets line up with plausible helper code in the static 8051 prefix,
but the public work-window bytes at the same low offsets are different, so this
is not a simple flat dump of active code memory. The best current description
is a banked or threaded runtime artifact.

That is useful in a very practical way. Instead of trying to disassemble the
island linearly, we now have an entry grammar. The next questions are much
smaller: what indexes the first 32 selector entries, what the 16-bit parameters
mean, and whether those indices connect to the `0x8a49` command shadow or to
the CDD record/lane schedule. It is another case where the opaque blob has
turned into a shaped machine part.

After that I let the normal drive run a longer, still read-only,
GET CONFIGURATION current capture: sixteen baseline snapshots alternating with
sixteen command snapshots. It did not add any new unique chunks to the big
normal-window corpus, which is useful in itself because it says this command
mostly samples a known slice of runtime. But it tagged that slice very cleanly.
Only two recurring stimulus-only chunks survived the local baseline comparison,
and both sit exactly in the controller bridge path we care about.

One chunk waits on the controller busy bit at `0x4000`, writes setup bytes into
`0x4091..0x4093`, kicks `0x409c`, and reads from `0x4099`. The companion chunk
stores successive `0x4099` reads into the `0x8a` packet shadow, including
`0x8a4e`, `0x8a53`, and `0x8a54`. That turns "the normal runtime probably has
a command shadow" into something more concrete: we have a tagged, repeatable
path where a normal host command becomes controller register traffic and then
controller response bytes are copied back into the shadow.

The last static pass made that bridge less hand-wavy. I broadened the
packet-shadow analyzer so it no longer only sees direct `MOV DPTR; MOVX`
copies. It now follows short local DPTR/A streams well enough to catch the
`INC DPTR` writes and repeated command-register writes that were obvious by
eye but missing from the table.

That gives the normal-mode controller path a compact shape. There is a
read-side setup family that loads `0x4091..0x4093` and kicks `0x409c`; a
write/FIFO setup family that loads `0x4095..0x4097`; a data/FIFO port at
`0x4099`; a FIFO writer through `0x4098`; and a packet-shadow command sequence
that pushes bytes through `0x4099`, then writes `0x409a=0`, `0x409b=1`, and
`0x409c=0x14` before polling.

This is not yet the LED or sled map, but it is the kind of small protocol
sketch we need. The host packet path is no longer just "somewhere in normal
runtime": `0x47b1` feeds `0x8a49..0x8a54`, and that shadow feeds the
controller register families above. A nearby `0x4860..0x486a` cluster keeps
showing up around the same path, which makes it a good candidate for future
mechanics/servo exploration once we are ready to poke more deliberately.

I pulled that `0x4860` cluster into its own note before moving on. The short
version: it looks real. `0x4860.2` and `0x4864.0` are set and cleared as a
pair in multiple paths, `0x4867.7` toggles with a nearby `0x480b` status bit,
and `0x4863` is mirrored through `0x8630`. The cautious read is
"hardware-control/mailbox cluster", not "LED pin" or "sled motor" yet. But it
is exactly the sort of small register island we wanted to identify before
doing more visible-mechanics experiments.

There may also be a bigger prize hiding in the same neighborhood. The normal
runtime has a stock-looking controller read path: wait on `0x4000`, load
`0x4091..0x4093`, kick `0x409c`, poll it, then read back through `0x4098` or
`0x4099`. GET CONFIGURATION current cleanly tags one version of that path, and
the surrounding handler uses packet-shadow bytes like `0x8a4d` and `0x8a4e`
as count/selector fields. If those bytes are controllable through a legal host
command, this could become the fast normal-mode oracle we wanted: a way to ask
the live controller for bytes without waiting seconds per bit.

I tried the first cautious version of that test live: a read-only sweep over
GET CONFIGURATION variants, changing request type, starting feature, and
allocation length, with work-window snapshots after each command. The drive
stayed in normal `LD5M`, and the host responses varied exactly as the command
fields changed. The bridge chunks still showed up, but they did not sort
cleanly by start-feature or allocation in only two cycles. So this is not the
fast oracle yet. It is a useful constraint: GET CONFIG definitely tags the
bridge, but we still need either more cycles on fewer variants or a more direct
way to observe the packet-shadow fields.

The follow-up was a cleanup pass on that evidence, not another live poke. I
split out a selector-map report for the normal packet shadow. The short version
is that `0x8a49` really does look like an opcode byte: the visible code compares
it with `REQUEST SENSE`, `READ(10)`, `WRITE(10)`, `MODE SELECT(10)`, key/report
key style values, and several LiteOn/vendor opcodes. The neighboring bytes now
have a more practical sketch too: `0x8a4d` is length/count-ish, while
`0x8a4e`, `0x8a53`, and `0x8a54` participate in controller FIFO/status traffic
through `0x4099`.

The interesting negative is still GET CONFIGURATION. It is the command that
most clearly lights up the controller bridge in the live captures, but the
public work-window corpus does not show a plain `0x8a49 == 0x46` compare. That
probably means GET CONFIG reaches the bridge through a table-driven route, an
unharvested code slice, or an earlier dispatch stage. Either way, the next live
experiment should be narrower than "try more random commands": vary fields in
one read/status command family and watch whether the `0x8a4d/0x8a4e` field
roles move in lockstep with the bridge snippets.

I ran that narrower experiment next, still in normal mode and still read-only.
This time the command family was "things that ask ordinary optical-drive
questions": `REQUEST SENSE`, several `READ TOC` formats, and two
`GET PERFORMANCE` types. The drive stayed in normal `LD5M`.

The useful result was a split between successful and failed status paths.
`REQUEST SENSE` and `GET PERFORMANCE type03` returned normally. The no-disc
`READ TOC` variants and `GET PERFORMANCE type00` returned failed/check status,
and those failures consistently exposed a recurring work-window chunk around
`+0x8b00`. That chunk references `0x8a49` and `0x8a4d`, exactly the
opcode/selector and count-ish bytes we care about. A companion chunk around
`+0x7140/+0x7180` touches the controller gateway through `0x4098`, not the
`0x4099` bridge seen in the GET CONFIG good-response path.

Looking at that `+0x8b00` chunk more closely produced a better byte map. It is
not just "some status code." It explicitly checks `0x8a49 == 0x1b`, the START
STOP UNIT opcode, then checks `(0x8a4d & 0x0f) == 0x02`, which is the
load/eject/start control nibble in CDB byte 4. So the packet shadow is now much
less vague: `0x8a49` is CDB byte 0, `0x8a4a` is byte 1, and `0x8a4d` is byte 4.
Some later bytes are also reused in controller response paths, but the base
shadow mapping is ordinary CDB order.

So the normal runtime now has two visible surfaces to pull on. GET CONFIG gives
a clean successful-response route through `0x4099` and the later shadow bytes.
Failed TOC/performance requests give a status/error route through `0x8a49`,
`0x8a4d`, and a `0x4098`-looking gateway. That is not yet an oracle, but it is
another shaped edge of the same machine.

I tried to sharpen that edge by pairing each failing command with an immediate
`REQUEST SENSE`: fail, capture; sense, capture. This was less clean than I had
hoped. The pair run did not neatly separate "after the failure" from "after
sense"; the recurring chunks showed up across both phases, with strong touches
on `0x4098` and `0x8a23`. That is still useful. It tells us the public work
window is sampling a longer shared error/status path rather than a tidy
command-bounded handler. More host-command snapshots may have diminishing
returns here; the better next step is probably a narrow one-command capture or
a hook around the `0x8bxx`/`0x9cxx` snippets.

I did that pass offline first, and the `+0x8bxx` clue got a little more useful.
The START STOP check is close to the `0x4860` cluster we had already marked as
mechanics-adjacent. The nearby code gates on `0x480e`, clears bits in
`0x48a5` and `0x4762`, and prepares `0x4860.2` handling. A complete paired
setter for `0x4860.2` and `0x4864.0` appears in a separate `+0x92xx` family,
while the cleanup side clears `0x4864.0`, `0x5905`, `0x5a01`, and `0x4860.2`
again. That makes a much more concrete story than "maybe `0x4860` does
something": the path now looks like host CDB, packet shadow, START STOP/eject
control check, state gates, then a controller-facing mechanics register family.

That still does not make `0x4860.2` an eject button or a sled bit. It is more
likely one piece of a valid controller transaction. The next good live pass is
not a blind write into those registers; it is telemetry around the branch:
confirm when the START STOP path is reached, read the handful of state bytes
around it, and only then think about replaying or modifying a whole mechanics
sequence. I wrote this up in
`analysis/8051/normal-start-stop-mechanics-path-20260501.md`.

I also sanity-checked the new capture tool on the Linux host in dry-run mode.
It planned the eject-style START STOP CDB, `1B 00 00 00 02 00`, but because
`--allow-start-stop` was not present it did not send it. It only captured the
normal work-window baseline and then checked that `/dev/sg0` was still normal
`LD5M`. So the tool is ready for the real test without having already moved
anything.

Then I ran the real one. The command was still just ordinary START STOP UNIT,
not updater traffic: `1B 00 00 00 02 00`, the exact eject-style low-nibble
case from the static branch. The drive visibly did the eject dance. That is a
very satisfying anchor: the CDB shadow check we found is not a curiosity in an
error path, it is on a real route to mechanism movement.

The capture side taught us something too. The immediate post-command
`READ BUFFER` work-window capture timed out while the mechanism was doing its
thing, and `sg_raw` returned after about five seconds with no response payload.
But a delayed follow-up succeeded, `MECHANISM STATUS` returned eight zero
bytes, and `/dev/sg0` still identified as normal `LD5M`. So this was not a
currentboot-style loss; it was a busy transition window. I hardened the capture
tool so future mechanical runs keep their summaries even when the first
post-command window times out.

I repeated the same eject command with the hardened tool and longer delays.
The first two post-command work-window reads still timed out, then later
windows succeeded. REQUEST SENSE came back clean, MECHANISM STATUS before and
after was eight zero bytes, and the optical LUN stayed normal. So the practical
rule is now: START STOP can leave the public work-window path unavailable for
several seconds after visible motion, but it recovers by itself.

To make sure this was really the low-nibble `0x02` case and not generic START
STOP weirdness, I ran the other three variants. They were boring in exactly the
right way. `stop` and `start` returned quick CHECK/Not Ready because there is
no medium. `load` returned quick CHECK/Illegal Request. All their post-command
work-window captures succeeded. Only `eject` caused visible movement and the
multi-second busy timeout. That lines up beautifully with the branch we found:
opcode `0x1b`, then `(CDB[4] & 0x0f) == 0x02`.

The hook plan after that is deliberately less dramatic than the sled movement.
START STOP eject is now a real trigger, but it is a terrible moment to expect a
clean host reply: the drive is busy doing the mechanical thing we asked it to
do. The better hook shape is capture first, answer later. If we can patch the
branch, it should copy a handful of state bytes such as `0x480e`, `0x4860`,
`0x4864`, `0x5905`, and `0x5a01` into scratch XDATA, then either let the stock
path run or eventually short-circuit it through a known return path. A later
boring command can expose the stored bytes.

The catch is still where to patch. The live work-window code looks like normal
runtime overlay material, and our earlier persistent visible-F0 hooks did not
affect normal INQUIRY or REQUEST SENSE timing after cold boot. Even a small
detail in the START STOP chunk reinforces that: its `LCALL 0x0f8d` does not
line up cleanly with the visible 8051 prefix disassembly. So the next real
breakthrough is not another blind F0 hook. It is finding a normal-mode response
path that is both live and patchable, or proving that the overlay has to be
patched through a different route.

I pushed that source question a little harder offline. Comparing the normal
work-window chunks against everything we have was clarifying: only a tiny slice
matches the visible F0 prefix, none matches the helper, and almost none matches
currentboot XDATA. But a surprisingly large part matches the currentboot
`0x070000` gateway dump. Normal `id01` and `id02` reads are also near-aliases
for the public work-window. The high half of that window has long exact runs
shared between normal and currentboot, especially `+0xa000..+0xde80` and
`+0xe000..+0xfd80`.

That is good news and bad news. Good: the normal window is not pure fog; it is a
shared controller/work-memory image we can compare across modes. Bad: the exact
START STOP `+0x8bxx` branch still does not localize to F0, the helper, or an
obvious currentboot gateway chunk. The nearby mechanics cluster around
`+0x92xx/+0x93xx/+0x95xx` does have a few small shifted currentboot overlaps,
so it may give us cross-mode landmarks even if it is not a direct patch map.

One tempting lead needed a correction before it turned into another blind
hook. A lot of normal-window chunks contain `LCALL 0x3d89`, and at first glance
that looked like a shared visible-F0 routine. But the callers load byte pairs
into registers before calling it, while visible F0 `0x3d89` is the tail of a
CMAC-ish controller write helper and does not fit those arguments. Public
offset `+0x3d89` in the normal window is also all zero. The better read is that
we are seeing banked/controller code snippets, not a simple linear 8051 code
image.

That pushed the next idea sideways: if the normal window is mostly
controller/gateway memory, make the currentboot hook write that memory
directly. I added a guarded `gateway-cdb-rw` hook mode. In ordinary use it is
the same one-byte controller-gateway reader we already trust. The first version
required `CDB[6] == 0xa6` and `CDB[10] == 0x5a`, then wrote `CDB[11]` through
`0x4095..0x4098`, read the same address back, and returned the byte at response
offset `0x20`.

That v1 hook half-worked in exactly the useful way: it installed cleanly, and
the read path returned `Flash Type Error` from controller `0x018620`, but the
write branch did not fire. The command returned GOOD and readback stayed
`0x46`. That lines up with the older warning that CDB byte 6 is not preserved
reliably in this handler. I rebuilt the hook as v2 so the guard lives only in
the proven parameter window: `CDB[10] == 0x5a`, with the write value in
`CDB[11]`. The smoke test remains reversible and currentboot-local: change
`Flash...` to `Glash...`, read it back, then restore it.

V2 worked. The smoke test changed the helper string from `Flash Type Error` to
`Glash Type Error`, then restored it. I also used a padding byte before the
`PLDS CORPORATION` string at controller `0x074030` as a harmless carryover
marker. A bare `PLDSVUC` lock did not exit currentboot; it returned CHECK/Not
Ready and stayed in the hooked `;D5C` view. The full recovery path returned to
LD5M, but the marker was gone in normal `READ BUFFER`, so this is a strong
currentboot volatile write primitive, not yet a trivial way to patch normal
controller memory across recovery.

I also added the missing workflow glue: the Linux persistence runner can now
apply gateway patches after a specific event or after every event with a given
phase. The smoke test used
`--gateway-patch-after-event 1:0x018620:476c617368`, which means “after event
1, write `Glash` at the helper-string address.” The runner logged the patch,
and the next read showed `Glash Type Error`. That gives us a faster way to try
helper-overlay changes at the exact point they matter, without regenerating a
new profile-tail candidate for every tiny experiment.

After the sled/eject excitement, I deliberately shifted back to boring
normal-mode read-only commands. The best candidate for a quiet fast oracle was
GET CONFIGURATION, because the work-window captures keep showing a controller
bridge near `0x4091..0x4099` when that command runs. The tempting theory was:
maybe the reserved GET CONFIG CDB bytes that land in the packet shadow at
`0x8a4d` and `0x8a4e` can steer the bridge.

That was worth testing because it was low drama: no data-out payloads, no
WRITE BUFFER, no START STOP, no mechanics. I added a small capture helper and
ran variants with nonzero CDB bytes 4, 5, 6, and 9. The drive accepted all of
them and stayed normal `LD5M`, but the host-visible GET CONFIG response did
not change. Longer isolated runs for CDB byte 5 (`0x01` and `0xf0`) showed the
same bridge chunks as plain GET CONFIG, but not a clean controllable address
field. The useful conclusion is negative: GET CONFIG is safe and good for
tagging the normal bridge, but these reserved bytes are not the fast read
oracle by themselves.

That still helps. It keeps the normal-mode plan honest. The bridge is real, but
we probably need either a different command family whose CDB fields naturally
feed the bridge, or a live patch/hook around the bridge path before it becomes
an arbitrary controller-memory readout.

There was also a useful self-correction hiding in that result. The recurring
`0x8a4c..0x8a4e -> 0x4011..0x4013` bridge looks less like a secret GET CONFIG
address path and more like the follow-up `READ BUFFER` capture command itself:
in a normal READ BUFFER CDB, bytes 3, 4, and 5 are exactly the 24-bit buffer
offset. That means the normal bridge we kept seeing is probably the public
work-window reader we already control. It is a good oracle, but a constrained
one: it reaches the `0x070000` work window and its mirrors, not decoded CDD
memory. The next question is therefore sharper: can we find another legal
READ BUFFER selector, or patch that normal READ BUFFER overlay, so the same
machinery points somewhere more interesting?

I took the legal-selector question seriously before moving on. A new scanner
sent raw READ BUFFER CDBs where byte 1 was treated as a full 8-bit value, not
just the ordinary low 5-bit SCSI mode. The smoke pass tried representative
high values, then the full pass covered every value from `0x20` through
`0xff` against IDs `0x01`, `0x02`, `0xe2`, `0xf0`, `0xf1`, and `0xf2`. Every
one of the 1344 full-pass reads returned the same hard `rc=5` no-data shape.
No timeouts, no partial buffers, no weird high-bit window. So that easy door is
closed: high READ BUFFER mode bits do not appear to be a hidden normal-runtime
selector.

The next quiet command family was GET PERFORMANCE. This was not aimed at
mechanics or writes; it was just a way to perturb the normal command path and
then capture the public work window again. That worked as a tile harvester.
The first GET PERFORMANCE variant pass added 77 new normal-runtime chunks to
the corpus, bringing the combined capture set to 208 work-window snapshots and
862 unique informative chunks. The longer four-cycle repeat added zero more,
which is useful in its own way: GET PERFORMANCE is a good one-time pass, but
not a bottomless source of new tiles.

One tempting chunk from that run needed careful handling. GET PERFORMANCE made
a strong recurring `+0x8bxx` tile visible, and it references the packet shadow
at `0x8a49` and `0x8a4d`. But the branch checks are exactly the START STOP
eject signature we already confirmed live: command opcode `0x1b`, low nibble
`0x02`. In other words, the GET PERFORMANCE run surfaced the eject overlay
tile; it did not turn GET PERFORMANCE into an eject command. That distinction
matters because these public windows show rotating overlay memory, not
necessarily the currently executing command handler.

That leaves us with a cleaner normal-mode picture. The stock READ BUFFER
oracle is real but fenced into the public work-window surface. GET CONFIG and
GET PERFORMANCE are safe ways to tag and harvest pieces of the normal runtime,
but neither gives direct decoded CDD memory. The next realistic paths are now:
stitch the harvested packet-shadow code offline, find a different harmless
command family that exercises new handlers, or solve normal-mode patchability
so we can redirect the already-known READ BUFFER machinery instead of merely
watching it rotate past.

I then reran the packet-shadow analysis across every saved normal work-window
directory, not just the latest six-run corpus. That broadened the sample to
509 captures and made one thing clearer: the packet shadow is real, but the
later bytes are reused. `0x8a49` is still the opcode-like selector, with
compares against ordinary SCSI/MMC commands and LiteOn vendor-looking values.
But bytes like `0x8a4d`, `0x8a4e`, `0x8a53`, and `0x8a54` are not permanently
just CDB bytes. Some paths refill them from controller response FIFO state.

That matters for GET CONFIG. Across the all-runs scan, a GET CONFIG-specific
slice shows `0x4099` feeding `0x8a4d/0x8a4e/0x8a53/0x8a54`, followed by a
branch on `0x8a4d == 0xfe`. This pattern only appears in GET CONFIG-oriented
capture directories. The generic `0x8a4c..0x8a4e -> 0x4011..0x4013` bridge, by
contrast, appears everywhere and belongs to the public READ BUFFER response
plumbing. So the better read is that GET CONFIG has a small controller-backed
feature-list builder with an internal `0xfe` sentinel, not an exposed arbitrary
read primitive.

This is still progress. The response-builder path gives us a more concrete
normal-runtime island to reverse: `+0x70c0/+0x7100/+0x7140/+0x7180` for the
read-side and `0x4011..0x4013` setup, `+0x7480/+0x74c0` for the `0x4099`
burst, `+0x7600/+0x7640` for `0x4091..0x4093` setup, and
`+0xdbc0/+0xdc00/+0xdc40` for the write/FIFO save-restore path. The next
breakthrough probably requires either normal-mode patchability around one of
these islands or a command family whose stock response builder exposes richer
controller bytes without requiring a patch.

The next pass treated those islands less like a flat memory dump and more like
what they seem to be: rotating tiles. I added a stitcher that tracks
`0x40`-byte chunks and their observed neighbors instead of pretending that two
adjacent public slots are always adjacent code. That made the GET CONFIG path
much cleaner. The best observed chain is:

```text
4037c8574920 -> 8d8c3b0a22a0 -> 20ea2ab16891
```

In plain language, that chain waits for the controller to be ready, writes a
three-byte-ish selector/address through `0x4091..0x4093`, kicks the controller
with `0x409c=0x40` then `0x24`, waits for `0x409c.5` to clear, reads four
bytes from `0x4099` into `0x8a4d`, `0x8a4e`, `0x8a53`, and `0x8a54`, checks
whether the first byte is the special `0xfe` sentinel, and then drops into the
common public response builder that writes `0x8a4c..0x8a4e` into
`0x4011..0x4013`.

The patchability result was less magical but useful. The GET CONFIG-specific
setup and seed chunks are not in the visible F0 image, not in the saved
currentboot gateway dump, and not even in the baseline normal id01/id02
work-window references. They only show up when the right stimulus has made
that overlay tile visible. The common response bridge chunk is different: it
is stable in baseline normal id01/id02 at `+0x7140`, though currentboot
`+0x7140` contains unrelated code.

So the "where do we hook?" answer is narrower. The transient GET CONFIG chunk
is an excellent map of the local mechanism, but not an obvious static flash
patch target. The stable bridge is a better normal-runtime landmark. To turn
this into a host-visible oracle, we likely need either a real normal-mode
RAM/controller-memory write primitive or a proven currentboot-to-normal
state-carryover trick. Writing a visible F0 offset is still the wrong default
for this path.

After the sled/eject surprise, I kept the next pass offline. The question was:
are the normal-mode work-window bytes a clean decoded CDD image, or are they a
rotating overlay surface? I added a classifier for every saved normal
`0x070000` work-window tile. Across 509 captures it found 888 unique
`0x40`-byte chunks. About half of them match visible artifacts somewhere
else, but 387 do not match F0, the visible 8051 prefix, the helper overlay, or
the saved currentboot gateway dump.

That is exciting and humbling in equal measure. The stable public response
bridge and the GET CONFIG `0x4099` seed are hidden normal-runtime code, not
visible F0 bytes. But the same chunks move among public slots: the bridge tile
appears at `+0x7100`, `+0x7140`, and `+0x7180`. If those offsets were trusted
as decoded CDD addresses, the same code would land in different CDD records,
which is nonsense. So this is probably decoded/controller or overlay material,
but the public `READ BUFFER` offset is a tile viewport, not the true internal
address.

The practical result is a cleaner rule of engagement. Normal work-window
tiles are now a useful hidden-runtime corpus for static study. They are not a
linear dump to patch by offset. The response bridge remains the best
host-visible hook target, but only after we learn a real normal-mode write
primitive or a reliable way to carry a currentboot edit into the normal
runtime.

One extra sanity check closed off a tempting shortcut. I tried normalizing all
captures by the stable bridge tile, as if the whole 64 KiB public window were
just shifted by one local phase. That made the corpus less stable, not more
stable: raw public offsets have 746 positions stable at 95% or better, while
bridge-aligned offsets have only 244. So the bridge has a real local phase,
but it is not a universal scroll key for the window. The normal work-window is
more like a set of independently rotating or overlaid code tiles than one
global ring buffer.

There was also a nicer patchability clue hiding on the write side. The normal
chunks at `+0xdbc0`, `+0xdc00`, and `+0xdc40` save controller command
registers, write through the `0x4095..0x4098` command/FIFO path, and restore
the old state. Those exact chunks are present in every normal capture and also
match the saved currentboot gateway dump. That makes them a much more
interesting future state-carryover test than the response bridge: unlike
`+0x7140`, this region is visibly shared between currentboot and normal. It is
not a safe thing to poke casually, because it is a real controller command
helper, but it is the first clean-looking overlap region where a reversible
currentboot gateway marker might tell us whether normal runtime patching is
possible without a true normal-mode write primitive.

The next CDD push knocked down one attractive checksum story. The 14-byte
trailer field looked like it might split into a two-byte Coastermelt-style
additive checksum plus a 12-byte checksum over the CDD unit structure. I added
a focused offline probe for exactly that. It tried every contiguous two-byte
slice of `0xe7fe0..0xe7fed` against low-16 sums, one's-complement sums, and
two's-complement sums over the obvious firmware/container/CDD regions. It then
tried the remaining 12 bytes as column-wise sums, XORs, CRC32-low bytes, and
Adler-low bytes over obvious 12-byte and 13-byte CDD unit streams. Across
LD5M, AD12, AHS9, CD12, CHS7, and CHS9, there were no exact matches and no
near misses worth explaining. So the easy split is out.

I also tried to use the normal hidden-runtime chunks as known output for the
CDD hard modes. Stable hidden chunks do line up, under the naive public-offset
mapping, with CDD mode `0x40`/`0x80` records. That is at least aesthetically
consistent: the hard-looking normal runtime material points at the hard CDD
record classes. But the cheap source/output tests were negative. The decoded
64-byte chunks do not appear directly in their candidate CDD source spans, and
even fixed-XOR four-byte seed checks are basically empty. This is useful
negative evidence: if these are decoded CDD outputs, they are not coming from a
simple byte copy, fixed XOR, or obvious unpacking. The CDD problem remains a
real decoder/codeword problem, not a disguised CRC table.

The next live CDD push was more interesting. We picked one of the
well-understood affine leaf cells in CDD stream 2: group 105, whose stock
decoded lane-0 byte is `0x84`. Rather than flipping one random encoded byte,
we rewrote all 12 observed affine lead cells consistently, first so the group
decoded as `0x85`, then again so it decoded as `0x8b`. Both edits were
admitted through the helper-bypass path, survived a hardware power-cycle, and
the drive still cold-booted as normal `LD5M`. Restoring the 12 lead cells gave
byte-identical F0 again. That is a big practical step: at least this class of
CDD leaf bytes is mutable without solving the trailer seal.

It did not magically become a CDD decoder. Normal `READ BUFFER id=01/02
offset=0x070000` captures changed after the CDD edits, but the changes look
mostly like tile/phase movement in the public work-window, not a direct
"decoded byte appears here" oracle. The cleanest report is
`analysis/8051/cdd-affine-g105-live-diff-20260501.md`: across stock,
`0x84->0x85`, `0x84->0x8b`, and restored stock states, there are 62 stable
reversible public-window offsets. That is enough to say this CDD leaf affects
normal runtime state. It is not enough to read arbitrary decoded CDD memory.

One operational trap also became clearer. After finalizer/currentboot work,
plain F0 READ BUFFER dumps can decrypt as nonsense until a live EXTRAINQ has
been sent. The key material is not changing; the live EXTRAINQ appears to
prime or reset the readback transform/state. I added `--prime-extrainq` to
`scripts/dump_liteon_linux_f0_window.py` so future post-mutation F0
verification can explicitly perform that handshake before reading F0.

The follow-up did the obvious "why not both" move: mutate another clean CDD
affine leaf and compare it to the first one. Group 99 is also in CDD stream 2,
with stock decoded lane-0 byte `0x0a`. We rewrote all 12 observed affine lead
cells so it decoded as `0x0b`, cold-booted the drive, and verified the exact
12 flash bytes had changed. Then we staged a stock restore, cold-booted again,
and verified the page was byte-for-byte back to LD5M. This second CDD leaf is
therefore not a one-off curiosity: the helper bypass can make repeatable,
structured CDD affine edits and cleanly undo them.

The normal-mode captures from group 99 were more useful than the raw tile
chaos suggests. `analysis/8051/cdd-affine-g99-live-diff-20260501.md` found
107 clean stock-consistent public-window offsets. Intersecting those with the
group-105 result gives 31 offsets that react to two independent decoded CDD
leaf edits. The overlap includes the old response-bridge pair
`+0x7140/+0x7180`, some compact low-window rows like `+0x01c0/+0x0280`, and
several code-looking tile rotations. This still is not a decoded CDD oracle,
but it is now a practical detector set for future normal-mode hooks: if a
normal-mode marker or response tweak runs, compare these overlap offsets first
instead of staring at the whole unstable 64 KiB window.

I also made the tooling a little less bespoke. `plan_liteon_cdd_affine_group_patch.py`
turns a decoded affine group and target byte into the exact F0 patch/restore
arguments needed for the helper-bypass renderer. `analyze_liteon_cdd_affine_experiment.py`
does the per-state stable-tile comparison for new CDD edits, and
`compare_liteon_cdd_affine_live_reports.py` intersects two such reports. One
small operational fix landed too: EXTRAINQ priming can succeed through this
Linux path without printing the normal `SCSI Status: Good` string, so the F0
dump helper no longer treats that successful prime as a hard failure.

I then tried a third affine point in a different part of the CDD: group 27,
an early CDD1 full-row leaf whose stock decoded byte is `0xe4`. Changing all
12 observed lead cells to decode as `0xe5` still booted as normal `LD5M`, and
the stock restore sequence also completed cleanly. This one exposed a new
readback caveat: CDD1 F0 spot reads around `0x43800` can decrypt correctly for
some single aligned `0x80` reads and badly for adjacent/multi-chunk reads, so
CDD1 F0 verification is less pleasant than the late CDD2 pages. The important
behavioral result survived that nuisance: group 27 produced 78 clean
normal-window offsets.

With three independent affine edits in hand, the overlap picture got sharper.
Group 27 and group 99 overlap at 64 clean offsets; group 27 and group 105 at
24; group 99 and group 105 at 31. The triple overlap is 21 offsets, including
`+0x01c0`, `+0x0280`, `+0x8f40`, `+0x8fc0`, `+0x9d80`, and `+0x9dc0`. The old
response-bridge pair `+0x7140/+0x7180` is still useful, but it is specific to
the two late CDD2 edits and did not show up in the group-27 clean set. That is
actually helpful: we now have a general detector set and a more specific
response-bridge probe for future normal-mode hook work.

Before pushing more risky live experiments, I rebuilt the external AI handoff
bundle as `fw_static_re_bundle_20260501.zip`. The new bundle is much smaller
than the old project dump and starts with a `START_HERE.md` that explains the
current CDD problem, the valid sibling images, the affine leaf decoder, the
three live affine edits, and the normal-mode detector offsets. It also includes
the 8051 decompile, CDD record maps, trailer/auth negatives, and Claude's
short-op plaintext artifacts. The point is to give other models a clean static
surface while we continue live work locally.

The next creative pivot was to stop treating normal `READ BUFFER id=01
offset=0x070000` only as a flaky detector and start treating it as a passive
decoded-runtime sampler. I ran two read-only harvests on the Linux drive while
it was normal `LD5M`: 40 baseline capture-only windows, then 8 cycles of safe
standard commands such as INQUIRY, EXTRAINQ, MODE SENSE, GET CONFIGURATION,
GET EVENT STATUS, and MECHANISM STATUS. No firmware writes or helper payloads
were sent, and the drive still reported normal `LD5M` afterward.

That worked well enough to become a real avenue. The normal work-window corpus
grew from 509 captures / 888 unique chunks to 669 captures / 902 unique
chunks. More importantly, I made `analyze_liteon_cdd_known_plaintext_pairs.py`,
which pairs encoded CDD record spans with decoded-looking 64-byte normal
runtime chunks. With the new harvests, it gives 247 candidate known-output
pairs across 35 CDD records. Simple direct, bitwise-NOT, bit-reversed, and
constant-XOR checks are still negative, so this is not a trivial byte transform.
But records such as 51, 55, 58, 60, 66, 68, 70, and 87 now have enough
decoded-looking tile evidence to be useful static targets.

This gives us a third path around the CDD wall. We still have the pure static
sibling-image work, and we still have the slow currentboot/controller oracle,
but now we also have a no-write normal-mode sampler for hidden decoded runtime
tiles. It does not provide a flat decoded CDD dump: the public window rotates,
and the bridge at `+0x7140/+0x7180/+0x7100` is only a local island anchor, not
a global scroll key. Still, it gives us real decoded-looking code chunks that
can be bucketed back to candidate CDD records. The next useful static job is
to build per-record chunk adjacency graphs and infer record grammars from
known encoded-source / decoded-tile pairs.
