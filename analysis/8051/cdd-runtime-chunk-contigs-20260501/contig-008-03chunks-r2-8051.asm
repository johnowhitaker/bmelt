            0x00000000      movx @dptr, a
            0x00000001      movx a, @dptr
            0x00000002      anl a, #0xfb
            0x00000004      movx @dptr, a
            0x00000005      lcall 0x97dd
            0x00000008      ret
            0x00000009      mov dptr, #0x8672                          ; [0x8672:1]=255
            0x0000000c      mov a, r7
            0x0000000d      movx @dptr, a
            0x0000000e      mov dptr, #0x81f5                          ; [0x81f5:1]=255
            0x00000011      movx a, @dptr
            0x00000012      xrl a, r7
        ┌─< 0x00000013      jz 0x0031
        │   0x00000015      mov dptr, #0x8672                          ; [0x8672:1]=255
        │   0x00000018      movx a, @dptr
        │   0x00000019      mov r3, a
        │   0x0000001a      mov dptr, #0x81f5                          ; [0x81f5:1]=255
        │   0x0000001d      movx a, @dptr
        │   0x0000001e      mov dptr, #0x885d                          ; [0x885d:1]=255
        │   0x00000021      movx @dptr, a
        │   0x00000022      mov c, 0x2f.0                              ; [0x2f:1]=11
        │   0x00000024      clr a
        │   0x00000025      rlc a
        │   0x00000026      inc dptr
        │   0x00000027      movx @dptr, a
        │   0x00000028      mov r5, #0x0e
        │   0x0000002a      mov r7, #0x00
        │   0x0000002c      mov r6, #0x01
        │   0x0000002e      lcall 0x0b07
        └─> 0x00000031      mov dptr, #0x8946                          ; [0x8946:1]=255
            0x00000034      movx a, @dptr
            0x00000035      mov r7, a
            0x00000036      inc dptr
            0x00000037      movx a, @dptr
            0x00000038      mov dptr, #0x8153                          ; [0x8153:1]=255
            0x0000003b      xch a, r7
            0x0000003c      movx @dptr, a
            0x0000003d      inc dptr
            0x0000003e      mov a, r7
            0x0000003f      movx @dptr, a
            0x00000040      inc dptr
            0x00000041      movx a, @dptr
            0x00000042      mov r1, a
            0x00000043      inc dptr
            0x00000044      movx a, @dptr
            0x00000045      mov r2, a
            0x00000046      inc dptr
            0x00000047      movx a, @dptr
