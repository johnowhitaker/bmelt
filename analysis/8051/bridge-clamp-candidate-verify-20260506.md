# Bridge-Clamp Candidate Verification

candidate: `post-materializer-runtime-bridge-clamp07`
restore: `post-materializer-runtime-bridge-clamp07-restore`
all ok: `True`

| check | ok | detail |
|---|---:|---|
| `base_hook_stock` | `True` |  |
| `base_cave_ff` | `True` |  |
| `candidate_hook_patch` | `True` |  |
| `candidate_cave_not_ff` | `True` |  |
| `restore_image_equals_base` | `True` | restore_sha256='488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39', base_sha256='488f49c7f5d8141186db6ca006a33cccefcc391b537d2a903f4ebaa7ea8f2e39' |
| `candidate_only_expected_offsets_changed` | `True` | changed_count=211, expected_count=211, unexpected=[], missing=[] |
| `candidate_helper_low_sector_patches_present` | `True` | helper_patches=['0x169:752204', '0x2b5:0232c4', '0x345:752440'] |
| `restore_helper_low_sector_patches_present` | `True` | helper_patches=['0x169:752204', '0x2b5:0232c4', '0x345:752440'] |
| `candidate_gateway_writes_match_plan` | `True` | writes=[{'address': '0x077156', 'value': '0x07'}, {'address': '0x077196', 'value': '0x07'}, {'address': '0x0770e6', 'value': '0x07'}, {'address': '0x077026', 'value': '0x07'}, {'address': '0x0770a6', 'value': '0x07'}, {'address': '0x077066', 'value': '0x07'}] |
| `final_candidate_diff_count_matches_image` | `True` | final_modified_byte_count=211, image_changed_count=211 |
| `final_candidate_event_count` | `True` | event_count=546 |
| `restore_final_candidate_diff_count_zero` | `True` | restore_modified_byte_count=0 |
