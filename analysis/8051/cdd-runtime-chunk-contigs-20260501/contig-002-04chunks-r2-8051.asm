            0x00000000      clr a
            0x00000001      addc a, @r0
            0x00000002      mov @r0, a
            0x00000003      mov dptr, #0x47d7                          ; [0x47d7:1]=255
            0x00000006      movx a, @dptr
            0x00000007      anl a, #0xfe
            0x00000009      movx @dptr, a
            0x0000000a      mov dptr, #0x8a4f                          ; [0x8a4f:1]=255
            0x0000000d      movx a, @dptr
            0x0000000e      mov dptr, #0x47d6                          ; [0x47d6:1]=255
            0x00000011      movx @dptr, a
            0x00000012      mov dptr, #0x47af                          ; [0x47af:1]=255
            0x00000015      clr a
            0x00000016      movx @dptr, a
            0x00000017      mov dptr, #0x47b1                          ; [0x47b1:1]=255
            0x0000001a      movx @dptr, a
            0x0000001b      movx @dptr, a
            0x0000001c      mov a, @r0
            0x0000001d      movx @dptr, a
            0x0000001e      inc r0
            0x0000001f      mov a, @r0
            0x00000020      movx @dptr, a
            0x00000021      clr a
            0x00000022      movx @dptr, a
            0x00000023      movx @dptr, a
            0x00000024      mov dptr, #0x8a53                          ; [0x8a53:1]=255
            0x00000027      movx a, @dptr
            0x00000028      mov dptr, #0x47b1                          ; [0x47b1:1]=255
            0x0000002b      movx @dptr, a
            0x0000002c      mov dptr, #0x8a54                          ; [0x8a54:1]=255
            0x0000002f      movx a, @dptr
            0x00000030      mov dptr, #0x47b1                          ; [0x47b1:1]=255
            0x00000033      movx @dptr, a
            0x00000034      mov a, #0xfc
            0x00000036      add a, @r0
            0x00000037      mov @r0, a
            0x00000038      dec r0
            0x00000039      mov a, #0xff
            0x0000003b      addc a, @r0
            0x0000003c      mov @r0, a
            0x0000003d      setb c
            0x0000003e      mov dptr, #0x8a90                          ; [0x8a90:1]=255
            0x00000041      mov 0x2c, r5                               ; [0x2c:1]=144
            0x00000043      movx a, @dptr
            0x00000044      inc a
            0x00000045      movx @dptr, a
            0x00000046      mov dptr, #0x89fc                          ; [0x89fc:1]=255
            0x00000049      movx a, @dptr
