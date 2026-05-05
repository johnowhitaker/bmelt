# Tomorrow Plan: Crossing The Normal-Mode Delivery Gap

Date: 2026-05-05

## Plain-English Blocker

We can now talk to the drive in several useful ways:

- the updater/currentboot path gives us strong read/write tools;
- the helper bypass lets us persist F0 bytes without solving the 14-byte seal;
- normal `LD5M` mode exposes real command paths like `REPORT KEY`, `MODE
  SELECT`, `READ BUFFER`, `GET CONFIGURATION`, and media reads;
- the public `READ BUFFER id=01 offset=0x070000` window shows slices of normal
  runtime code.

The annoying split is this:

```text
currentboot world: we can patch and instrument it
normal LD5M world: the interesting code is CDD-derived runtime code
```

The normal runtime is not mainly executing the easy first 8051 prefix we can
patch comfortably. It is using controller/CDD materialized code and work
buffers. The public work-window is like seeing a moving reflection of that
runtime, not holding a pointer to memory we can simply overwrite.

So the blocker is not "where could a hook go?" anymore. We have good hook
ideas. The blocker is delivery:

```text
How do we safely get one deliberate byte/code change into the normal runtime
that actually handles host commands?
```

The easy delivery ideas are closed:

- visible F0-prefix hooks did not affect normal command handlers;
- currentboot gateway writes do not survive the available transitions into
  normal mode;
- the volatile `MODE SELECT` bit is writable, but does not change the direct
  `REPORT KEY format 8` response;
- public-window phase shifts are real observations, but not a controlled I/O
  channel.

## Best Bet

The best-looking path is now a tightly scoped CDD-derived normal-runtime edit
using the helper-bypass persistent write method.

The intuition:

```text
normal command -> CDD-derived normal runtime island -> controller response path
```

We cannot directly write the decoded runtime island, but we can persist changes
to the encoded CDD source. Earlier CDD edits proved that some source-byte
changes can perturb normal work-window chunks. The job is to make the next edit
boring, reversible, and close to a host-visible response path.

The safest concrete target family is still the response bridge / packet shadow
area:

- record 58/59: stages response/controller address bytes into `0x4011..0x4013`;
- record 60: nearby controller write/FIFO partner;
- record 55/56: packet/response corridor that is less scarred than record 59.

The first real PoC hook should remain the conservative `READ BUFFER` redirect:

```text
if READ BUFFER id=01 offset=0x070bad:
    substitute response offset 0x07dbc0
else:
    stock behavior
```

Why this hook is still the right shape:

- it changes only response arguments the stock bridge already writes;
- it does not invent a new response buffer;
- success is a direct host-visible SCSI response diff;
- failure can be tested without counting public-window phase noise as success.

The hard part is not writing that hook in abstract 8051. The hard part is
getting any chosen edit into the CDD-owned normal runtime without breaking the
runtime or losing update/recovery entry.

## Main Risk

This plan crosses the CDD mutation boundary. That is riskier than the normal
mailbox probes we just ran.

Known risks:

- A CDD source-byte edit can make the normal runtime behave strangely even
  after the raw F0 bytes are restored. We saw this with the record60 phase
  shift: the flash was byte-stock again, but the public window did not simply
  return to its original layout.
- Record59 is powerful evidence but has already been associated with blocked
  update entry on one drive. Treat it as a high-value area, not the first casual
  target.
- A CDD edit may perturb command handling, so the drive can stop accepting the
  helper-bypass restore path until power-cycled or recovered.
- Because the CDD encoding is not solved, a source-byte edit is not equivalent
  to a clean decoded-code edit. We may get a local perturbation, a phase shift,
  or nothing.
- The public work-window is tiled/phasey, so a visually exciting change can be
  misleading unless a direct response changes or the effect is reversible and
  localized.

Why the risk is still reasonable if we choose to proceed:

- Drive #3 is fresh and baseline-dumped.
- The helper-bypass write/restore path is live-proven on this family.
- We can build explicit restore candidates before running the mutation.
- We can avoid known hazardous paths: no `SEND KEY format 6`, no random CDD
  directory/header edits, no START STOP recovery experiments, no broad fuzzing.
- The target can be a single bit-clear in a known normal-runtime island, not an
  arbitrary multi-byte payload.

## Tomorrow Work Plan

### 1. Lock The Baseline Again

Before any write:

- confirm Drive #3 is normal `LD5M`;
- confirm the movie DVD/media state if it matters, or eject and run no-media if
  we want fewer moving parts;
- capture direct response baselines:
  - `READ BUFFER id=01 offset=0x070bad len=0x80`;
  - `READ BUFFER id=01 offset=0x07dbc0 len=0x80`;
  - `REPORT KEY format 8`;
  - `MODE SENSE page 0x08`;
- capture one focused 64 KiB public work-window;
- spot-read the planned F0 source byte(s).

Success criteria for baseline: all direct responses stable and drive identity
unchanged.

### 2. Pick One Mutation Target Offline

Do not start by patching record59 again.

Preferred target order:

1. **Record55/56 response corridor**: lower known scar risk than record59, still
   close to packet/response output.
2. **Record58 GET CONFIG / response bridge**: very relevant to response
   construction, but adjacent to the scarred record59 area.
3. **Record60 controller write-side partner**: useful but already produced
   confusing phase behavior.

For the first pass, choose one bit-clear source-byte mutation with:

- a known source offset;
- a known stock byte;
- a generated restore candidate;
- a focused watch set;
- no edits in CDD headers, directories, erased gaps, or auth/trailer fields.

The experiment is an ownership/control probe first, not the final redirect
hook. We should only try to install a multi-byte redirect after a one-byte edit
gives a clean, localized, reversible effect.

### 3. Run One Bounded Live Edit

If update entry and helper-bypass still work:

1. run the candidate;
2. cold power-cycle;
3. check identity;
4. capture the same direct responses and public windows;
5. spot-read the changed F0 byte;
6. immediately run the restore candidate;
7. cold power-cycle;
8. verify full or focused F0 restoration;
9. repeat the same direct responses and public windows.

Acceptance checks:

- drive remains `LD5M`;
- changed F0 byte is observed after mutation;
- restored F0 byte is observed after restore;
- any effect is localized to the expected record/watch family;
- direct host responses are checked first, before public-window interpretation.

Stop conditions:

- optical LUN disappears;
- update entry times out repeatedly;
- direct normal commands become broadly unstable;
- the effect is broad/random rather than local;
- restore candidate cannot run.

### 4. If The One-Byte Probe Works

Then move from "ownership" to "hook."

The next hook should not try to dump arbitrary memory. It should do one boring
thing:

```text
READ BUFFER 0x070bad returns the bytes normally returned by 0x07dbc0
```

That proves:

- normal-mode patched code ran;
- host CDB bytes are visible to it;
- stock response machinery can be steered;
- direct SCSI response bytes changed predictably.

Only after that should we expand to an `NMIO` marker or selected XDATA bytes.

### 5. If The Probe Fails Or Looks Too Risky

Fallbacks, in order:

1. continue normal mailbox exploration with direct responses only;
2. add DVD-RW/media-sector buffer-flow probes when sacrificial media is
   available;
3. revisit front-panel/Pico LED/button once we have a normal code path worth
   triggering;
4. return to static CDD work only where it directly improves target selection.

Do not spend tomorrow counting public-window phase changes as progress unless
they tie back to a direct response or a clean reversible record ownership
result.

## Best Current Decision Point

Tomorrow's real question is:

```text
Are we willing to spend one carefully bounded CDD-derived runtime mutation on
Drive #3 to try to break the delivery deadlock?
```

My recommendation: yes, but only one, and only after the target is chosen
offline and the restore candidate is built first.

I would not attempt a large hook payload immediately. I would first run a
single-byte ownership/control probe in record55/56 or record58. If that gives a
localized reversible effect, the READ BUFFER redirect hook becomes the next
reasonable escalation. If it does not, the safer conclusion is that we need a
better source-to-decoded-runtime map before mutating more CDD bytes.
