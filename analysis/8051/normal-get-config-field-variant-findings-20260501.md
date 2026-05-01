# Normal GET CONFIG Field-Variant Findings

Date: 2026-05-01

This pass tested whether the normal-mode GET CONFIGURATION path gives us a
controllable read-side controller bridge. The target was the bridge-like
work-window corridor that writes `0x4091..0x4093`, kicks `0x409c`, and reads
`0x4099`. Earlier packet-shadow work made CDB bytes 4 and 5 interesting because
they line up with `xdata[0x8a4d]` and `xdata[0x8a4e]`.

Important correction after this run:

```text
analysis/8051/normal-read-buffer-capture-bridge-correction-20260501.md
```

The recurring `0x8a4c..0x8a4e -> 0x4011..0x4013` bridge is most cleanly
explained as the follow-up `READ BUFFER` capture command's own 24-bit offset
path, not as a hidden GET CONFIG address field. The GET CONFIG variants are
still useful safe stimuli, but the bridge snippets in `*.window.bin` must be
interpreted through the `READ BUFFER id=01 offset=0x070000` command used to
capture the window.

Live evidence:

```text
references/evidence/live/normal-work-window-get-config-field-variants-20260501/
references/evidence/live/normal-work-window-get-config-field-variants-r5-long-20260501/
references/evidence/live/normal-work-window-get-config-r5-01-isolated-20260501/
references/evidence/live/normal-work-window-get-config-r5-f0-isolated-20260501/

analysis/8051/normal-work-window-get-config-field-variants-20260501.md/json
analysis/8051/normal-work-window-get-config-field-variants-r5-long-20260501.md/json
analysis/8051/normal-work-window-get-config-r5-isolated-20260501.md/json
```

All runs were host read/no-data-out. The drive stayed normal `LD5M`.

## What Was Varied

The normal GET CONFIGURATION CDB is:

```text
46 RT SF_hi SF_lo 00 00 00 AL_hi AL_lo 00
```

The new capture helper varies the reserved bytes that should map onto the
packet shadow as:

```text
CDB[4] -> xdata[0x8a4d]
CDB[5] -> xdata[0x8a4e]
CDB[6] -> xdata[0x8a4f]
```

The first run tested ordinary current/all-style variants plus:

```text
CDB[4] = 01 / fe
CDB[5] = 01 / 0f / f0
CDB[6] = 01
CDB[9] = 01
```

The follow-up runs isolated `CDB[5]=01` and `CDB[5]=f0` for 16 alternating
baseline/stimulus cycles each.

## Result

Every variant returned GOOD. The host-visible GET CONFIG response was unchanged
for the reserved-field variants:

```text
standard current sf=0000: 60 bytes
CDB[4] variants:          60 bytes, same response hash
CDB[5] variants:          60 bytes, same response hash
CDB[6] variant:           60 bytes, same response hash
CDB[9] variant:           60 bytes, same response hash
```

So these fields are tolerated, but they are not a direct host-visible read
oracle through the normal GET CONFIG response.

The familiar bridge chunks did recur:

```text
read-side kick:
  refs 0x4000, 0x4091, 0x4093, 0x4099
  sample 08eff6904000e020e7f9908ac6e09040...

4099 burst:
  refs 0x4099, 0x8a4b, 0x8a4d, 0x8a4e, 0x8a53, 0x8a54
  sample 8a4df0904099e0908a4ef0904099e090...
```

The mixed-order run initially made `CDB[5]` look special, but the longer
single-variant runs make the safer interpretation narrower: GET CONFIG in
general tags these bridge chunks, and public-window rotation/capture phase is a
large confounder. `CDB[5]=f0` exposed the bridge chunks 6/16 times, while
plain GET CONFIG current exposed them 3/16 times in the earlier long run. That
is not enough to call address/control steering.

`CDB[5]=01` did expose one extra recurring packet-shadow chunk:

```text
offsets: +0x9500/+0x9540/+0x9580/+0x95c0
refs:    0x8a4c
sample:  7ff9123d89e4fd7f40123d89e4908a33...
```

But that chunk is already known from the broader read/status corpus, including
GET PERFORMANCE and READ TOC captures. Treat it as another packet-shadow
slice, not proof that reserved GET CONFIG byte 5 controls a new path.

## Practical Meaning

This line of attack is still useful for harvesting normal work-window slices,
but it did not become the fast normal runtime oracle we wanted.

The current read is:

- GET CONFIGURATION is a safe, repeatable, non-mechanical stimulus around the
  public work-window reader.
- Reserved CDB bytes 4, 5, 6, and 9 are tolerated by this drive.
- Those bytes do not alter the ordinary GET CONFIG response.
- Public-window chunk presence is too phase-sensitive to infer control from
  mixed-order captures, and the recurring bridge snippets likely belong to the
  follow-up READ BUFFER capture path itself.
- If a normal bridge oracle exists here, it probably needs either a deeper
  patch/hook around the bridge path or a field family that the stock handler
  actually copies into the controller address registers and then exposes in the
  host response.

## Next Use

Do not spend more time on random GET CONFIG reserved-byte values unless the
question is specifically "can this field move a known work-window chunk?".

Better next targets:

1. Keep using plain GET CONFIG/current as a boring bridge-tagging stimulus.
2. Look for another read-only command family where CDB bytes that feed
   `0x8a4d/0x8a4e/0x8a53/0x8a54` are semantically meaningful and reflected in
   the response.
3. Keep the START STOP/eject path separate; it is a real mechanics trigger and
   should only be used after we have a later stable readback hook.
4. Focus static work on how the bridge result is copied into response/FIFO
   state rather than on more GET CONFIG reserved-field fuzzing.
