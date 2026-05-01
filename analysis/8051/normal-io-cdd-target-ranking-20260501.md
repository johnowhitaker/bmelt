# Normal I/O CDD Target Ranking

This is a prioritization pass for the next live perturbation. It ranks
normal-runtime work-window chunks and their candidate CDD records by how
closely they touch packet-shadow, controller-register, and response-bridge
patterns.

The score is heuristic. It is meant to choose better live targets, not to
prove ownership by itself.

## Top Runtime Chunks

| rank | score | chunk | observations | CDD candidates | reasons |
|---:|---:|---|---:|---|---|
| 1 | 149.0 | `20ea2ab16891` | 669 | r58@0x7140, r59@0x7180, r58@0x7100 | seen 669x; controller_status refs x4; packet_shadow refs x5; copies 0x8a4c->0x4011, 0x8a4d->0x4012, 0x8a4e->0x4013 |
| 2 | 143.0 | `2111cafaf69c` | 669 | r85@0x9580, r84@0x9540, r84@0x9500, r85@0x95c0 | seen 669x; front_panel_or_status refs x7; packet_shadow refs x8; copies 0x47b1->0x8a4d, 0x47b1->0x8a4e, 0x47b1->0x8a4f |
| 3 | 124.5 | `8d8c3b0a22a0` | 44 | r58@0x7140, r58@0x7100, r59@0x7180 | seen 44x; controller_status refs x3; packet_shadow refs x5; copies 0x4099->0x8a4e, 0x4099->0x8a53, 0x4099->0x8a54 |
| 4 | 121.0 | `9b673c066ae4` | 666 | r60@0x74c0, r60@0x7480 | seen 666x; controller_status refs x5; packet_shadow refs x4; copies 0x8a4e->0x4099, 0x8a53->0x4099, 0x8a54->0x4099 |
| 5 | 102.0 | `efcb6299a750` | 336 | r66@0x7f80, r66@0x7f40, r66@0x7fc0 | seen 336x; controller_status refs x5; packet_shadow refs x3; copies 0x4099->0x8a53, 0x4099->0x8a54 |
| 6 | 98.8 | `5a65b8a71db9` | 218 | r80@0x91c0, r80@0x9180 | seen 218x; controller_status refs x4; packet_shadow refs x4; copies 0x401e->0x8784, 0x4022->0x8784, 0x4023->0x8785 |
| 7 | 92.0 | `8f8e0add044c` | 669 | r58@0x70c0, r58@0x7080, r58@0x7000 | seen 669x; controller_status refs x3; packet_shadow refs x6; copies 0x85fe->0x4011, 0x85ff->0x4012 |
| 8 | 92.0 | `04a2d67cbfff` | 428 | r66@0x7dc0 | seen 428x; controller_status refs x7; packet_shadow refs x2; copies 0x8a54->0x40b7 |
| 9 | 90.0 | `add3eb18b8cc` | 400 | r67@0x8240 | seen 400x; front_panel_or_status refs x6; packet_shadow refs x3; copies 0x8a4f->0x47d6, 0x8a53->0x47b1, 0x8a54->0x47b1 |
| 10 | 88.0 | `c5c0741f5daa` | 644 | r68@0x8480, r68@0x84c0, r68@0x8400 | seen 644x; front_panel_or_status refs x2; packet_shadow refs x7; profile_string_area refs x4 |
| 11 | 88.0 | `0c705773105c` | 669 | r49@0x6080, r49@0x60c0, r49@0x6000, r49@0x6040 | seen 669x; controller_status refs x2; front_panel_or_status refs x3; packet_shadow refs x4 |
| 12 | 88.0 | `144315176c64` | 669 | r83@0x9480, r83@0x94c0, r81@0x9400 | seen 669x; front_panel_or_status refs x3; packet_shadow refs x6; copies 0x47b1->0x8a4a, 0x47b1->0x8a4b |
| 13 | 84.3 | `ee30d1b5daca` | 162 | r57@0x6ec0 | seen 162x; controller_status refs x3; packet_shadow refs x5; copies 0x8961->0x4097, 0x8960->0x4096 |
| 14 | 84.0 | `6c4f90652e56` | 669 | r50@0x6180, r50@0x61c0, r50@0x6100, r50@0x6140 | seen 669x; controller_status refs x1; front_panel_or_status refs x4; packet_shadow refs x3 |
| 15 | 82.8 | `5a92e83e04a8` | 54 | r68@0x8580, r69@0x85c0 | seen 54x; front_panel_or_status refs x5; packet_shadow refs x3; copies 0x8a4e->0x47b1, 0x8a4f->0x47b1, 0x8a50->0x47b1 |
| 16 | 82.0 | `95caa55b881e` | 597 | r55@0x6b80, r55@0x6b00, r55@0x6bc0, r55@0x6b40 | seen 597x; front_panel_or_status refs x5; packet_shadow refs x7; copies 0x85ef->0x48f4, 0x85f0->0x48f5, 0x85f1->0x48f6 |
| 17 | 80.3 | `796c2cf9d837` | 19 | r55@0x6b00, r55@0x6b40, r55@0x6b80, r55@0x6bc0 | seen 19x; front_panel_or_status refs x3; packet_shadow refs x4; copies 0x8a4e->0x47b1, 0x8a54->0x47b1 |
| 18 | 78.0 | `3465e4783c3d` | 413 | r62@0x7640 | seen 413x; controller_status refs x5; packet_shadow refs x2; copies 0x891b->0x4091 |
| 19 | 76.0 | `70e7ea0193bb` | 669 | r70@0x8880, r70@0x8800 | seen 669x; front_panel_or_status refs x2; packet_shadow refs x7; profile_string_area refs x2 |
| 20 | 76.0 | `b69f366c92b6` | 667 | r64@0x7b00, r64@0x7b80 | seen 667x; controller_status refs x3; packet_shadow refs x3; copies 0x8ac6->0x4091 |

## Top Candidate CDD Records

| rank | score | record | chunks | pair count | operation keys | reasons |
|---:|---:|---:|---|---:|---|---|
| 1 | 1546.5 | 55 | `8853b78ca23e` x669, `a87d03db223d` x669, `95caa55b881e` x597 | 31 | `a742d3782e04` x62 | appears in GET PERFORMANCE runs; appears in GET CONFIG runs; CDD candidates 55; packet_shadow refs x7 |
| 2 | 1286.8 | 58 | `8f8e0add044c` x669, `7e15398acc97` x669, `20ea2ab16891` x450 | 18 | `66228ca20005` x36 | appears in GET CONFIG runs; seen 669x; packet_shadow refs x5; appears in GET PERFORMANCE runs |
| 3 | 1281.6 | 66 | `404045e0e63c` x669, `9aa0a39b4424` x669, `bd4b736c6b8d` x509 | 16 | `4e8210adb204` x32 | appears in GET CONFIG runs; packet_shadow refs x4; seen 669x; appears in GET PERFORMANCE runs |
| 4 | 1210.2 | 51 | `fe95f1ed098a` x669, `0f031dd8ed37` x652, `056348c5dbbf` x634 | 20 | `a98252b3a002` x40 | appears in GET CONFIG runs; appears in GET PERFORMANCE runs; packet_shadow refs x6; dptr 0x47b1 |
| 5 | 1090.3 | 60 | `4cfa6d151318` x669, `6d249b0b8b59` x669, `28583441dfa8` x668 | 13 | `950a90757805` x26 | appears in GET CONFIG runs; seen 669x; appears in GET PERFORMANCE runs; CDD candidates 60 |
| 6 | 937.0 | 70 | `fb00deab088b` x669, `70e7ea0193bb` x669, `23c16a978aa0` x669 | 15 | `098ad4a36805` x30 | appears in GET CONFIG runs; CDD candidates 70; seen 669x; appears in GET PERFORMANCE runs |
| 7 | 880.1 | 87 | `183ec6fd07c7` x669, `c2560553eb14` x669, `ba3aab1d5fd2` x445 | 14 | `0af2177f2e01` x28 | appears in GET CONFIG runs; CDD candidates 87; seen 669x; appears in GET PERFORMANCE runs |
| 8 | 816.9 | 68 | `85545872cc2b` x669, `ad2faf50bc31` x669, `17a7e3a30d12` x669 | 11 | `0fe212a8d404` x22 | appears in GET CONFIG runs; front_panel_or_status refs x2; profile_string_area refs x4; packet_shadow refs x7 |
| 9 | 680.0 | 88 | `7fabb1c7616c` x669, `03044422ea30` x338, `eda48f3e289c` x9 | 9 | `37424f6bc203` x18 | CDD candidates 88; seen 669x; controller_status refs x1; front_panel_or_status refs x5 |
| 10 | 655.2 | 50 | `6c4f90652e56` x669, `2598f9591a20` x644 | 7 | `6092d29f2405` x14 | seen 669x; controller_status refs x1; front_panel_or_status refs x4; packet_shadow refs x3 |
| 11 | 530.4 | 64 | `c24221ec1018` x669, `24ebe8bb67f5` x668, `b69f366c92b6` x667 | 7 | `93390e6b7c02` x14 | appears in GET CONFIG runs; controller_status refs x3; packet_shadow refs x1; appears in GET PERFORMANCE runs |
| 12 | 459.4 | 49 | `0c705773105c` x669, `ac6243637e2d` x5 | 7 | `428a889c5804` x14 | appears in GET CONFIG runs; seen 669x; controller_status refs x2; front_panel_or_status refs x3 |
| 13 | 424.1 | 85 | `2111cafaf69c` x329, `306eb529b363` x78 | 4 | `5f925170d804` x8 | seen 669x; appears in GET CONFIG runs; front_panel_or_status refs x7; packet_shadow refs x8 |
| 14 | 409.2 | 62 | `25333cae3674` x668, `3465e4783c3d` x413, `580b9228d0b9` x256 | 5 | `9fd2119d4c04` x10 | appears in GET CONFIG runs; seen 668x; appears in GET PERFORMANCE runs; controller_status refs x5 |
| 15 | 394.8 | 59 | `99d4493dc4cf` x669, `b7a129b7d392` x413, `20ea2ab16891` x219 | 5 | `30ca94930e05` x10 | seen 669x; controller_status refs x4; packet_shadow refs x5; appears in GET CONFIG runs |
| 16 | 377.2 | 80 | `5a65b8a71db9` x218, `1fc002817f62` x99 | 4 | `1f4acc5b4c04` x8 | appears in GET CONFIG runs; seen 218x; controller_status refs x4; packet_shadow refs x4 |
| 17 | 372.1 | 57 | `cfe0a1406283` x669, `5fb5a8bf8f9a` x490, `ee30d1b5daca` x162 | 6 | `3512d253d403` x12 | appears in GET CONFIG runs; seen 669x; appears in GET PERFORMANCE runs; packet_shadow refs x5 |
| 18 | 358.9 | 86 | `0b045c0906d5` x617, `306eb529b363` x591, `71a589c84051` x287 | 6 | `a3520f8e9004` x12 | seen 669x; appears in GET CONFIG runs; appears in GET PERFORMANCE runs; packet_shadow refs x7 |
| 19 | 358.8 | 67 | `037cda80b040` x669, `0803afdb9f57` x427, `add3eb18b8cc` x400 | 5 | `b0f2d169c404` x10 | appears in GET CONFIG runs; seen 669x; appears in GET PERFORMANCE runs; packet_shadow refs x7 |
| 20 | 343.2 | 84 | `2111cafaf69c` x340 | 2 | `3b0a538aa203` x4 | seen 669x; front_panel_or_status refs x7; packet_shadow refs x8; copies 0x47b1->0x8a4d, 0x47b1->0x8a4e, 0x47b1->0x8a4f |

## Top Contigs

| rank | score | contig | records | chunks | reasons |
|---:|---:|---:|---|---|---|
| 1 | 395.4 | 16 | common 55,56 / union 55,56 | `25956f88a30e`, `4f29221f2e51` | seen 669x; packet_shadow refs x6; seen 409x; packet_shadow refs x7 |
| 2 | 379.3 | 3 | common 51 / union 51,52 | `0a8cd35adb0f`, `056348c5dbbf`, `39ab42ddd82a` | seen 52x; packet_shadow refs x6; seen 634x; front_panel_or_status refs x4 |
| 3 | 373.0 | 21 | common 55 / union 55 | `95caa55b881e`, `a87d03db223d` | seen 597x; front_panel_or_status refs x5; seen 669x; front_panel_or_status refs x2 |
| 4 | 361.2 | 17 | common 66 / union 66 | `404045e0e63c`, `efcb6299a750` | seen 669x; front_panel_or_status refs x2; seen 336x; controller_status refs x5 |
| 5 | 350.0 | 20 | common 58 / union 58 | `7e15398acc97`, `8f8e0add044c` | seen 669x; front_panel_or_status refs x2; controller_status refs x3; has common CDD record owner |
| 6 | 344.2 | 4 | common 59 / union 58,59,60 | `20ea2ab16891`, `99d4493dc4cf`, `b7a129b7d392` | seen 669x; controller_status refs x4; packet_shadow refs x10; packet_shadow refs x8 |
| 7 | 331.2 | 22 | common 66 / union 66 | `9aa0a39b4424`, `fe343ef73975` | seen 669x; front_panel_or_status refs x1; seen 383x; controller_status refs x2 |
| 8 | 308.9 | 9 | common 86,87 / union 86,87 | `0b045c0906d5`, `71a589c84051` | seen 669x; packet_shadow refs x6; packet_shadow refs x7; has common CDD record owner |
| 9 | 303.4 | 0 | common  / union 68,69 | `85545872cc2b`, `c5c0741f5daa`, `17a7e3a30d12`, `7106a72e56d9`, `5a0c5fbcd38c` | seen 669x; packet_shadow refs x8; seen 644x; front_panel_or_status refs x2 |
| 10 | 297.6 | 18 | common 60 / union 60 | `4cfa6d151318`, `28583441dfa8` | seen 669x; front_panel_or_status refs x1; seen 668x; controller_status refs x4 |
| 11 | 280.5 | 15 | common 70 / union 70 | `23c16a978aa0`, `70e7ea0193bb` | seen 669x; front_panel_or_status refs x1; front_panel_or_status refs x2; has common CDD record owner |
| 12 | 273.5 | 23 | common 70 / union 70 | `d21d30cf6e6b`, `fb00deab088b` | seen 669x; packet_shadow refs x4; controller_status refs x8; has common CDD record owner |
| 13 | 270.0 | 14 | common 87 / union 87 | `183ec6fd07c7`, `ba3aab1d5fd2` | seen 669x; packet_shadow refs x6; seen 445x; controller_status refs x6 |
| 14 | 264.0 | 1 | common  / union 62,63,64 | `25333cae3674`, `204291444868`, `2b9a017b9d81`, `c24221ec1018` | seen 668x; controller_status refs x2; seen 548x; controller_status refs x4 |
| 15 | 255.2 | 8 | common 57 / union 57,58 | `cfe0a1406283`, `ee30d1b5daca`, `5fb5a8bf8f9a` | seen 669x; packet_shadow refs x7; seen 162x; controller_status refs x3 |
| 16 | 252.0 | 2 | common  / union 67,68 | `add3eb18b8cc`, `037cda80b040`, `0803afdb9f57`, `ad2faf50bc31` | seen 400x; front_panel_or_status refs x6; seen 669x; packet_shadow refs x7 |
| 17 | 237.3 | 24 | common 88 / union 88 | `eda48f3e289c`, `7fabb1c7616c` | seen 9x; front_panel_or_status refs x2; seen 669x; controller_status refs x1 |
| 18 | 220.4 | 11 | common 62 / union 61,62 | `0c9a360d26b8`, `3465e4783c3d` | seen 668x; controller_status refs x4; seen 413x; controller_status refs x5 |
| 19 | 206.0 | 5 | common  / union 50,51 | `2598f9591a20`, `0f031dd8ed37`, `fe95f1ed098a` | seen 644x; front_panel_or_status refs x2; seen 652x; front_panel_or_status refs x3 |
| 20 | 191.0 | 7 | common  / union 64,65 | `b69f366c92b6`, `7a8cbb7773e7`, `9e474876a043` | seen 667x; controller_status refs x3; seen 669x; front_panel_or_status refs x1 |

## Practical Read

- Records `58` and `59` remain the highest-value bridge records because
  they own chunks with direct `0x8a4c..0x8a4e -> 0x4011..0x4013` and
  `0x4099 -> 0x8a4e/0x8a53/0x8a54` patterns.
- Record `59` already has a strong reversible ownership result from the
  contig-4 live test, so it is the best known perturbation detector.
- Records `84/85` are packet-intake candidates around the `0x47b1 ->
  0x8a4c..0x8a53` CDB shadow copy. They are attractive if the next goal
  is to disturb command parsing rather than response setup.
- The clever shortcut to test next is currentboot-to-normal carryover:
  plant markers in these packet/bridge XDATA locations through the
  currentboot write hook, recover to normal without a hard power cut,
  then capture the same ranked work-window offsets.
