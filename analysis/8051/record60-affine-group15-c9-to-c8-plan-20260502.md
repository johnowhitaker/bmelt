# CDD Affine Group Patch Plan

Image: `LD5M`
Group: `15`
Stock plain: `0xc9`
Target plain: `0xc8`
Cells: `15`
Records: `63`
Kinds: `suffix`

Patch args:

```text
--patch 0x2ae8f:4f
```

Restore args:

```text
--patch 0x2ae8f:4e
```

| offset | record | cell | mask | before | after |
|---:|---:|---:|---:|---:|---:|
| `0x2ae8f` | 63 | 15 | `0x87` | `0x4e` | `0x4f` |
