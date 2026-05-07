# Bridge Clamp To Materialization Oracle Plan - 2026-05-06

Offline/static note only; no drive commands were sent.

## What The Clamp Code Does

The recurring normal READ BUFFER bridge-clamp sequence disassembles as:

```text
mov dptr, #0x8a29
movx a, @dptr
swap a
anl a, #0x0f
jnb acc.0, copy_fallback

mov dptr, #0x8a4c
movx a, @dptr
clr c
subb a, #0x0e
jc copy_fallback

mov dptr, #0x4011
mov a, #0x0e
movx @dptr, a
sjmp after_high

copy_fallback:
mov dptr, #0x85fe
movx a, @dptr
mov dptr, #0x4011
movx @dptr, a

after_high:
mov dptr, #0x85ff
movx a, @dptr
mov dptr, #0x4012
movx @dptr, a
...
```

The `0x8a4c` byte is the high byte of the host READ BUFFER public offset
shadow. When the flag path is active, high bytes at or above `0x0e` are capped
to `0x0e` before being written to controller register `0x4011`. The next bytes
flow through `0x4012` and likely `0x4013`.

## Why The `0x07` Candidate Is First

Changing the clamp immediate `0x0e -> 0x07` should make a high-offset host
READ BUFFER request fold to a visibly different public window. This is not the
final oracle; it is the safer proof that:

- the resident post-materializer hook ran;
- its gateway writes reached decoded normal runtime RAM;
- the patched runtime code affected a host-visible READ BUFFER response;
- stock restore can undo the effect.

The fixed six-slot candidate and the new dynamic baseline-derived candidate
both use `0x07` by default.

## Why `0x18` Was The First Interesting Next Step

The decoded CDD materialization range starts around `0x184000`. If changing
the clamp immediate to `0x18` works without triggering another accept-list or
range check, a host command like:

```text
READ BUFFER mode=1 id=01 offset=0x184000
```

may cause the same normal bridge path to write `0x18 0x40 0x00` into the
controller descriptor instead of clamping the high byte to `0x0e`. That would
turn the stock READ BUFFER path into a real decoded-materialization oracle.

This is not guaranteed. There may be another selector, ID, or range clamp
after `0x4011..0x4013`. But `0x18` is the natural second test only after the
`0x07` proof and restore have succeeded.

There is now one important correction: patching the clamp output immediate to
`0x18` aliases every high byte `>= 0x0e` to `0x18`. That is fine for an
address like `0x184000`, but a request for `0x191010` would be driven as
`0x181010`, not `0x191010`.

The better decoded-band oracle variant is probably to patch the comparison
threshold immediate instead:

```text
90 8a 4c e0 c3 94 0e 40 08 90 40 11 74 0e f0
                  ^^
                  change this threshold byte to 0x1c
```

With `SUBB A,#0x1c`, high bytes `0x18..0x1b` should take the normal
copy-fallback path and reach `0x4011` unchanged. That covers the full stated
decoded CDD range `0x184000..0x1b3fff` without forcing everything to
`0x18xxxx`. This is still a runtime code patch and should only be attempted
after the `0x07` proof proves that post-materializer writes land and restore.

## Recommended Live Order

1. Run the guarded wrapper with the dynamic `0x07` candidate:

   ```sh
   python3 scripts/run_liteon_materialized_bridge_clamp_live_test.py \
     --device /dev/sg0 \
     --pico-port /dev/ttyACM0 \
     --build-dynamic-candidate-from-baseline \
     --dynamic-patch-value 0x07 \
     --execute
   ```

2. Analyze with `scripts/analyze_liteon_materialized_bridge_clamp_live_test.py`.
   Continue only if the high-offset response changes under patch and restores
   to baseline.

3. Repeat with a decoded-oracle patch, ideally using the same preflight
   discipline and immediate restore. The older clamp-output variant is:

   ```sh
   python3 scripts/run_liteon_materialized_bridge_clamp_live_test.py \
     --device /dev/sg0 \
     --pico-port /dev/ttyACM0 \
     --build-dynamic-candidate-from-baseline \
     --dynamic-patch-value 0x18 \
     --include-decoded-oracle-offsets \
     --execute
   ```

   The newer threshold variant is probably the better CDD-band test:

   ```sh
   python3 scripts/run_liteon_materialized_bridge_clamp_live_test.py \
     --device /dev/sg0 \
     --pico-port /dev/ttyACM0 \
     --build-dynamic-candidate-from-baseline \
     --dynamic-patch-kind threshold-immediate \
     --dynamic-patch-value 0x1c \
     --include-decoded-oracle-offsets \
     --execute
   ```

4. If the decoded-oracle patch changes high-offset responses, add focused
   probes for
   `0x180000`, `0x184000`, `0x190000`, and known CDD table target addresses
   such as `0x191010`, `0x198900`, and `0x1a0000`.

   The wrapper/probe now has that first focused set built in through
   `--include-decoded-oracle-offsets`, currently:

   ```text
   0x180000, 0x184000, 0x191010, 0x198900, 0x199030,
   0x19c020, 0x19c800, 0x1a0000, 0x1a2fe0
   ```

## Risk

This remains a code-bearing runtime patch. The patch is narrow and reversible
at the F0/helper level, but a bad decoded-runtime write could wedge the normal
READ BUFFER path until a restore/cold cycle or, in the worst case, until the
drive is recovered through the known currentboot path. Do not run it while the
Linux host sees only the `Generic External` bridge fallback.
