# Materialized Bridge-Clamp Live-Test Analysis

Run directory: `references/evidence/live/freshdrive4-bridgeclamp-clamp07-proof-20260507`

## Assessment

- NO HIGH-OFFSET EFFECT: 0x0f0000 did not show a patched-vs-baseline hash change.
- CAUTION: ordinary 0x070000 also changed; this may be phase/noise or a broad behavioral effect.
- BASELINE SLOT CHECK: 0x077000 contains 6 stock clamp-pattern hit(s).

## Offsets

### `0x070000`

- patched differs from baseline: `True`
- restored matches baseline: `False`
- baseline: 3 captures, stable=`True`, hashes=`715a7880369c1781`
- patched: 3 captures, stable=`True`, hashes=`6424d3698a926c99`
- restored: 3 captures, stable=`True`, hashes=`123c961f61654f2d`

### `0x074000`

- patched differs from baseline: `False`
- restored matches baseline: `True`
- baseline: 3 captures, stable=`True`, hashes=`18469f79007353f5`
- patched: 3 captures, stable=`True`, hashes=`18469f79007353f5`
- restored: 3 captures, stable=`True`, hashes=`18469f79007353f5`

### `0x077000`

- patched differs from baseline: `True`
- restored matches baseline: `False`
- baseline: 3 captures, stable=`True`, hashes=`4ad09694db12bbd3`
  clamp hits: stock=`6`, patched07=`0`, patched18=`0`
- patched: 3 captures, stable=`True`, hashes=`1831e39315e08f29`
  clamp hits: stock=`6`, patched07=`0`, patched18=`0`
- restored: 3 captures, stable=`True`, hashes=`1831e39315e08f29`
  clamp hits: stock=`6`, patched07=`0`, patched18=`0`

### `0x0f0000`

- patched differs from baseline: `False`
- restored matches baseline: `True`
- baseline: 3 captures, stable=`True`, hashes=`076a27c79e5ace2a`
- patched: 3 captures, stable=`True`, hashes=`076a27c79e5ace2a`
- restored: 3 captures, stable=`True`, hashes=`076a27c79e5ace2a`
