# Normal Work-Window Tile Harvest

The currentboot CDD parser-call experiments were useful negatives: the visible
8051 parser and `0x4a` mailbox can be replayed, but decoded CDD targets under
`0x184000` remain zero in that boot personality. The next useful pivot was to
look again at the normal-runtime public `READ BUFFER mode=1 id=01
offset=0x070000` window.

That window is not a simple static dump. It behaves like a rotating/pageable
work/code window. Repeated captures in normal `LD5M` mode move 64-byte tiles
among a handful of public offsets, especially around:

```text
+0x6000..+0x61ff
+0x8600..+0x87ff
+0x9500..+0x95ff
```

The repeated-read control run is:

```text
references/evidence/live/normal-work-window-capture-only-20260501/
analysis/8051/normal-work-window-capture-only-20260501.md
```

It produced 704 informative unique `0x40` chunks. Every capture still had 699
informative chunks, but only a few chunks were new relative to the first
capture. That means the act of reading the window itself rotates a small
stable working set.

The safe-stimulus run is:

```text
references/evidence/live/normal-work-window-stimuli-full-20260501/
analysis/8051/normal-work-window-stimuli-full-20260501.md
```

It sent only read-only/no-data-out normal commands between captures:
`TEST UNIT READY`, `REQUEST SENSE`, standard `INQUIRY`, EXTRAINQ,
`MODE SENSE(10)`, `GET CONFIGURATION`, `GET EVENT STATUS NOTIFICATION`,
`READ TOC`, `READ DISC INFORMATION`, `READ TRACK INFORMATION`,
`MECHANISM STATUS`, and `READ DVD STRUCTURE`.

Comparison against the capture-only control is:

```text
analysis/8051/normal-work-window-stimuli-vs-capture-only-20260501.md
```

That comparison is the important result:

```text
capture-only unique informative chunks: 704
safe-stimulus unique informative chunks: 752
shared chunks: 704
stimulus-only chunks: 48
capture-only-only chunks: 0
```

So the safe commands did not merely perturb the same ring. The stimulus run
contains the entire capture-only corpus plus 48 additional informative
64-byte tiles. The busiest stimulus-only pages were:

```text
+0x8300  14 observations
+0x7e00  13 observations
+0x8400  12 observations
+0x9000  12 observations
+0x6200  10 observations
+0x6600  10 observations
+0x8b00  10 observations
+0x9f00  10 observations
```

Most sample bytes look like plausible 8051 code or code-adjacent tables:

```text
90 55 c6 e0 44 30 f0 90 82 43 e0 c4 54 0f 30 e0
8a 4d f0 90 8a 4d e0 ff c3 94 12 50 15 7d 00 ef
90 8a 4e e0 fd 7e 04 7f 55 12 02 fd 90 8a cf e0
```

This makes the public normal work window a third extraction path:

1. static CDD decoding;
2. slow currentboot bit/gateway readout;
3. normal-runtime tile harvesting through safe SCSI command stimuli.

The key unknown is whether the moving tiles have recoverable logical addresses.
For now, treat public offsets as page-frame positions rather than stable
addresses. The same chunk can appear at multiple offsets, often within a
four-slot `0x40` ring such as `+0x6000`, `+0x6040`, `+0x6080`, `+0x60c0`.

Reusable tools:

```sh
python3 scripts/capture_liteon_normal_work_window_stimuli.py \
  --device /dev/sg0 \
  --out-dir runs/normal-work-window-stimuli-full-YYYYMMDD

python3 scripts/analyze_liteon_normal_work_window_stimuli.py \
  references/evidence/live/normal-work-window-stimuli-full-YYYYMMDD \
  --out-json analysis/8051/normal-work-window-stimuli-full-YYYYMMDD.json \
  --out-md analysis/8051/normal-work-window-stimuli-full-YYYYMMDD.md

python3 scripts/compare_liteon_normal_work_window_runs.py \
  --reference references/evidence/live/normal-work-window-capture-only-YYYYMMDD \
  --target references/evidence/live/normal-work-window-stimuli-full-YYYYMMDD \
  --out-json analysis/8051/normal-work-window-stimuli-vs-capture-only-YYYYMMDD.json \
  --out-md analysis/8051/normal-work-window-stimuli-vs-capture-only-YYYYMMDD.md
```

Next useful expansion: add command families one at a time, repeat each stimulus
several times, and build a unique-tile corpus tagged by command. The immediate
goal is not to execute anything new; it is to harvest as much already-decoded
normal-runtime 8051 material as possible.

Follow-up focused harvest:

```text
references/evidence/live/normal-work-window-stimuli-focused-20260501/
analysis/8051/normal-work-window-stimuli-focused-20260501.md
analysis/8051/normal-work-window-focused-vs-capture-only-20260501.md
analysis/8051/normal-work-window-focused-vs-full-stimuli-20260501.md
```

This repeated the highest-yield safe stimuli for eight cycles:
EXTRAINQ, `MODE SENSE(10)`, `GET CONFIGURATION` current/all, and
`GET EVENT STATUS NOTIFICATION`. The drive stayed normal `LD5M`.

The focused run produced 751 informative unique chunks. Compared with the
original full-stimulus pass, it shared 736 chunks, added 15 new chunks, and
missed 16 chunks that the full pass had seen. That looks like normal cache
sampling variance plus a small amount of continued corpus growth, not an
unbounded new stream from the same five commands.

Aggregate corpus after the capture-only, full-stimulus, and focused-stimulus
runs:

```text
analysis/8051/normal-work-window-chunk-corpus-20260501.md
analysis/8051/normal-work-window-chunk-corpus-20260501.json
```

Current aggregate:

```text
captures: 68
unique informative 0x40 chunks: 767
capture-only contributed: 704 initial chunks
full-stimulus contributed: 48 new chunks
focused-stimulus contributed: 15 new chunks
```

Second follow-up expanded the safe command surface with read-capacity,
read-format-capacities, additional mode-sense pages, additional event classes,
TOC/DVD-structure variants, and get-performance probes:

```text
references/evidence/live/normal-work-window-stimuli-expanded-20260501/
analysis/8051/normal-work-window-stimuli-expanded-20260501.md
analysis/8051/normal-work-window-expanded-vs-focused-20260501.md
```

The drive again stayed normal `LD5M`. Some of the new commands returned CHECK
CONDITION or ILLEGAL REQUEST, but the follow-up window captures still completed.
The expanded pass contributed 18 more aggregate chunks. Current aggregate:

```text
captures: 94
unique informative 0x40 chunks: 785
capture-only contributed: 704 initial chunks
full-stimulus contributed: 48 new chunks
focused-stimulus contributed: 15 new chunks
expanded-stimulus contributed: 18 new chunks
```

Static exact-match check:

```text
analysis/8051/normal-work-window-chunk-static-matches-20260501.md
analysis/8051/normal-work-window-chunk-static-matches-20260501.json
```

Only 63 of the 785 chunks are exact `0x40`-byte slices of the known 1 MiB LD5M
F0 image, and only 8 are exact slices of the extracted visible 8051 prefix.
That does not prove every unmatched chunk is decoded executable code, because
the public window also contains live tables, profile strings, and work state.
But it strongly argues that the harvest is not just a fancy way of rereading
static flash. A large part of the window is runtime material.

The DPTR-immediate scan is a useful first correlation pass:

```text
analysis/8051/normal-work-window-dptr-refs-20260501.md
analysis/8051/normal-work-window-dptr-refs-20260501.json
```

It simply scans harvested chunks for the 8051 `MOV DPTR,#xxxx` opcode
sequence. This is not a complete disassembler, but it is a good way to find
runtime XDATA/mailbox addresses. The top references include familiar anchors:
`0x47b1`, `0x4000`, `0x4091`, `0x4098`, and `0x825b`. More interestingly,
many high-frequency references are not present as DPTR immediates in the known
F0/visible-8051 references:

```text
0x8a23
0x8a4a..0x8a54
0x8adf
0x88f1
0x8988
0x8353
```

This fits the live normal-window interpretation. The earlier static
`+0x6747` READ BUFFER accept-list analysis implied a normal-runtime packet
shadow around `xdata[0x8a49..]`; the harvested chunks now show lots of runtime
code touching that region. Those references are mostly absent from the visible
F0 prefix, which is exactly what we would expect if normal-mode overlays are
being paged into the public window.

Overlay/frame atlas:

```text
analysis/8051/normal-work-window-overlay-map-20260501.md
analysis/8051/normal-work-window-overlay-map-20260501.json
```

The atlas folds the 94 captures into public `0x40`-byte slots and separates
three cases:

- static exact matches against the known LD5M F0/prefix;
- runtime chunks that move among public slots;
- dense branch/vector-table-like chunks that should not be chased as
  straight-line code until their entry layout is understood.

Current overlay summary:

```text
public slots: 702
unique informative chunks: 785
static-matched chunks: 63
runtime/unmatched chunks: 722
chunks seen at multiple public slots: 159
```

The top actionable code-like chunk is the packet-shadow copy loop observed in
all 94 captures at the `+0x9500..+0x95c0` rotating slots:

```text
47 b1 e0 90 8a 4c f0 90 47 b1 e0 90 8a 4d f0 ...
```

Interpreted one byte in, this is the familiar pattern:

```text
MOV DPTR,#47b1
MOVX A,@DPTR
MOV DPTR,#8a4c
MOVX @DPTR,A
...
```

So the normal runtime is not just exposing random work RAM; it is exposing the
live command/packet ingress plumbing that moves bytes from the `0x47b1`
port/FIFO into the `0x8a4c..` shadow area. Other high-scoring chunks touch
`0x4095..0x4098`, `0x4000`, `0x8adf`, and neighboring `0x8a` addresses,
making the `0x8a49..0x8a54` region the best next static target for understanding
normal-mode command handling.

The `+0xa180..+0xad40` island is also important, but it is mostly dense
dispatch/table material: repeated low `LJMP 0x01xx/0x02xx` entries and
branch-plus-DPTR records. Treat it as a table to decode, not as a normal
linear function body.
