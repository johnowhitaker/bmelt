            0x00000000      47             orl a, @r1
            0x00000001      c5e0           xch a, 0xe0                 ; [0xe0:1]=96
            0x00000003      9089c8         mov dptr, #0x89c8           ; [0x89c8:1]=255
            0x00000006      f0             movx @dptr, a
            0x00000007      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
            0x0000000a      e0             movx a, @dptr
            0x0000000b      9089c9         mov dptr, #0x89c9           ; [0x89c9:1]=255
            0x0000000e      f0             movx @dptr, a
            0x0000000f      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
            0x00000012      e0             movx a, @dptr
            0x00000013      ff             mov r7, a
            0x00000014      6428           xrl a, #0x28
        ┌─< 0x00000016      6013           jz 0x002b
        │   0x00000018      ef             mov a, r7
        │   0x00000019      64be           xrl a, #0xbe
       ┌──< 0x0000001b      600e           jz 0x002b
       ││   0x0000001d      ef             mov a, r7
       ││   0x0000001e      64a8           xrl a, #0xa8
      ┌───< 0x00000020      6009           jz 0x002b
      │││   0x00000022      ef             mov a, r7
      │││   0x00000023      64d5           xrl a, #0xd5
     ┌────< 0x00000025      6004           jz 0x002b
     ││││   0x00000027      ef             mov a, r7
    ┌─────< 0x00000028      b4b909         cjne a, #0xb9, 0x0034
    │└└└└─> 0x0000002b      9047c5         mov dptr, #0x47c5           ; [0x47c5:1]=255
    │       0x0000002e      e4             clr a
    │       0x0000002f      f0             movx @dptr, a
    │       0x00000030      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
    │       0x00000033      f0             movx @dptr, a
    └─────> 0x00000034      9047d2         mov dptr, #0x47d2           ; [0x47d2:1]=255
            0x00000037      e0             movx a, @dptr
            0x00000038      54fe           anl a, #0xfe
            0x0000003a      f0             movx @dptr, a
            0x0000003b      904014         mov dptr, #0x4014           ; '\x14@'
                                                                       ; [0x4014:1]=255
            0x0000003e      e4             clr a
            0x0000003f      f0             movx @dptr, a
            0x00000040      47             orl a, @r1
            0x00000041      c5e0           xch a, 0xe0                 ; [0xe0:1]=96
            0x00000043      9089c8         mov dptr, #0x89c8           ; [0x89c8:1]=255
            0x00000046      f0             movx @dptr, a
            0x00000047      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
            0x0000004a      e0             movx a, @dptr
            0x0000004b      9089c9         mov dptr, #0x89c9           ; [0x89c9:1]=255
            0x0000004e      f0             movx @dptr, a
            0x0000004f      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
            0x00000052      e0             movx a, @dptr
            0x00000053      ff             mov r7, a
            0x00000054      6428           xrl a, #0x28
        ┌─< 0x00000056      6013           jz 0x006b
        │   0x00000058      ef             mov a, r7
        │   0x00000059      64be           xrl a, #0xbe
       ┌──< 0x0000005b      600e           jz 0x006b
       ││   0x0000005d      ef             mov a, r7
       ││   0x0000005e      64a8           xrl a, #0xa8
      ┌───< 0x00000060      6009           jz 0x006b
      │││   0x00000062      ef             mov a, r7
      │││   0x00000063      64d5           xrl a, #0xd5
     ┌────< 0x00000065      6004           jz 0x006b
     ││││   0x00000067      ef             mov a, r7
    ┌─────< 0x00000068      b4b909         cjne a, #0xb9, 0x0074
    │└└└└─> 0x0000006b      9047c5         mov dptr, #0x47c5           ; [0x47c5:1]=255
    │       0x0000006e      e4             clr a
    │       0x0000006f      f0             movx @dptr, a
    │       0x00000070      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
    │       0x00000073      f0             movx @dptr, a
    └─────> 0x00000074      9047d2         mov dptr, #0x47d2           ; [0x47d2:1]=255
            0x00000077      e0             movx a, @dptr
            0x00000078      54fe           anl a, #0xfe
            0x0000007a      f0             movx @dptr, a
            0x0000007b      904014         mov dptr, #0x4014           ; '\x14@'
                                                                       ; [0x4014:1]=255
            0x0000007e      e4             clr a
            0x0000007f      f0             movx @dptr, a
            0x00000080      47             orl a, @r1
            0x00000081      c5e0           xch a, 0xe0                 ; [0xe0:1]=96
            0x00000083      9089c8         mov dptr, #0x89c8           ; [0x89c8:1]=255
            0x00000086      f0             movx @dptr, a
            0x00000087      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
            0x0000008a      e0             movx a, @dptr
            0x0000008b      9089c9         mov dptr, #0x89c9           ; [0x89c9:1]=255
            0x0000008e      f0             movx @dptr, a
            0x0000008f      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
            0x00000092      e0             movx a, @dptr
            0x00000093      ff             mov r7, a
            0x00000094      6428           xrl a, #0x28
        ┌─< 0x00000096      6013           jz 0x00ab
        │   0x00000098      ef             mov a, r7
        │   0x00000099      64be           xrl a, #0xbe
       ┌──< 0x0000009b      600e           jz 0x00ab
       ││   0x0000009d      ef             mov a, r7
       ││   0x0000009e      64a8           xrl a, #0xa8
      ┌───< 0x000000a0      6009           jz 0x00ab
      │││   0x000000a2      ef             mov a, r7
      │││   0x000000a3      64d5           xrl a, #0xd5
     ┌────< 0x000000a5      6004           jz 0x00ab
     ││││   0x000000a7      ef             mov a, r7
    ┌─────< 0x000000a8      b4b909         cjne a, #0xb9, 0x00b4
    │└└└└─> 0x000000ab      9047c5         mov dptr, #0x47c5           ; [0x47c5:1]=255
    │       0x000000ae      e4             clr a
    │       0x000000af      f0             movx @dptr, a
    │       0x000000b0      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
    │       0x000000b3      f0             movx @dptr, a
    └─────> 0x000000b4      9047d2         mov dptr, #0x47d2           ; [0x47d2:1]=255
            0x000000b7      e0             movx a, @dptr
            0x000000b8      54fe           anl a, #0xfe
            0x000000ba      f0             movx @dptr, a
            0x000000bb      904014         mov dptr, #0x4014           ; '\x14@'
                                                                       ; [0x4014:1]=255
            0x000000be      e4             clr a
            0x000000bf      f0             movx @dptr, a
            0x000000c0      47             orl a, @r1
            0x000000c1      c5e0           xch a, 0xe0                 ; [0xe0:1]=96
            0x000000c3      9089c8         mov dptr, #0x89c8           ; [0x89c8:1]=255
            0x000000c6      f0             movx @dptr, a
            0x000000c7      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
            0x000000ca      e0             movx a, @dptr
            0x000000cb      9089c9         mov dptr, #0x89c9           ; [0x89c9:1]=255
            0x000000ce      f0             movx @dptr, a
            0x000000cf      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
            0x000000d2      e0             movx a, @dptr
            0x000000d3      ff             mov r7, a
            0x000000d4      6428           xrl a, #0x28
        ┌─< 0x000000d6      6013           jz 0x00eb
        │   0x000000d8      ef             mov a, r7
        │   0x000000d9      64be           xrl a, #0xbe
       ┌──< 0x000000db      600e           jz 0x00eb
       ││   0x000000dd      ef             mov a, r7
       ││   0x000000de      64a8           xrl a, #0xa8
      ┌───< 0x000000e0      6009           jz 0x00eb
      │││   0x000000e2      ef             mov a, r7
      │││   0x000000e3      64d5           xrl a, #0xd5
     ┌────< 0x000000e5      6004           jz 0x00eb
     ││││   0x000000e7      ef             mov a, r7
    ┌─────< 0x000000e8      b4b909         cjne a, #0xb9, 0x00f4
    │└└└└─> 0x000000eb      9047c5         mov dptr, #0x47c5           ; [0x47c5:1]=255
    │       0x000000ee      e4             clr a
    │       0x000000ef      f0             movx @dptr, a
    │       0x000000f0      9047c4         mov dptr, #0x47c4           ; [0x47c4:1]=255
    │       0x000000f3      f0             movx @dptr, a
    └─────> 0x000000f4      9047d2         mov dptr, #0x47d2           ; [0x47d2:1]=255
            0x000000f7      e0             movx a, @dptr
            0x000000f8      54fe           anl a, #0xfe
            0x000000fa      f0             movx @dptr, a
            0x000000fb      904014         mov dptr, #0x4014           ; '\x14@'
                                                                       ; [0x4014:1]=255
            0x000000fe      e4             clr a
            0x000000ff      f0             movx @dptr, a
            0x00000100      00             nop
            0x00000101      00             nop
            0x00000102      00             nop
            0x00000103      00             nop
            0x00000104      00             nop
            0x00000105      00             nop
            0x00000106      00             nop
            0x00000107      00             nop
            0x00000108      00             nop
            0x00000109      00             nop
            0x0000010a      00             nop
            0x0000010b      00             nop
            0x0000010c      00             nop
            0x0000010d      00             nop
            0x0000010e      00             nop
            0x0000010f      00             nop
            0x00000110      00             nop
            0x00000111      00             nop
            0x00000112      00             nop
            0x00000113      00             nop
            0x00000114      00             nop
            0x00000115      00             nop
            0x00000116      00             nop
            0x00000117      00             nop
            0x00000118      00             nop
            0x00000119      00             nop
            0x0000011a      00             nop
            0x0000011b      00             nop
            0x0000011c      00             nop
            0x0000011d      00             nop
            0x0000011e      00             nop
            0x0000011f      00             nop
            0x00000120      00             nop
            0x00000121      00             nop
            0x00000122      00             nop
            0x00000123      00             nop
