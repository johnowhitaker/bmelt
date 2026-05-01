        ┌─< 0x00000000      cjne a, #0x3c, 0x0016
        │   0x00000003      mov dptr, #0x8a14                          ; [0x8a14:1]=255
        │   0x00000006      movx a, @dptr
        │   0x00000007      inc a
        │   0x00000008      movx @dptr, a
       ┌──< 0x00000009      jnz 0x0011
       ││   0x0000000b      mov dptr, #0x8a13                          ; [0x8a13:1]=255
       ││   0x0000000e      movx a, @dptr
       ││   0x0000000f      inc a
       ││   0x00000010      movx @dptr, a
       └──> 0x00000011      clr a
        │   0x00000012      mov dptr, #0x89a2                          ; [0x89a2:1]=255
        │   0x00000015      movx @dptr, a
        └─> 0x00000016      clr c
            0x00000017      mov dptr, #0x8975                          ; [0x8975:1]=255
            0x0000001a      movx a, @dptr
            0x0000001b      subb a, #0xb8
            0x0000001d      mov dptr, #0x8974                          ; [0x8974:1]=255
            0x00000020      movx a, @dptr
            0x00000021      subb a, #0x0b
        ┌─< 0x00000023      jnc 0x0031
        │   0x00000025      inc dptr
        │   0x00000026      movx a, @dptr
        │   0x00000027      inc a
        │   0x00000028      movx @dptr, a
       ┌──< 0x00000029      jnz 0x0031
       ││   0x0000002b      mov dptr, #0x8974                          ; [0x8974:1]=255
       ││   0x0000002e      movx a, @dptr
       ││   0x0000002f      inc a
       ││   0x00000030      movx @dptr, a
       └└─> 0x00000031      mov dptr, #0x8974                          ; [0x8974:1]=255
            0x00000034      movx a, @dptr
        ┌─< 0x00000035      cjne a, #0x0b, 0x0050
        │   0x00000038      inc dptr
        │   0x00000039      movx a, @dptr
       ┌──< 0x0000003a      cjne a, #0xb8, 0x0050
       ││   0x0000003d      mov dptr, #0x894a                          ; [0x894a:1]=255
       ││   0x00000040      mov 0x2c, @r0                              ; [0x2c:1]=137
       ││   0x00000042      movx @dptr, a
       ││   0x00000043      mov dptr, #0x596a                          ; 'jY'
       ││                                                              ; [0x596a:1]=255
       ││   0x00000046      movx a, @dptr
       ││   0x00000047      mov dptr, #0x862d                          ; [0x862d:1]=255
       ││   0x0000004a      movx @dptr, a
       ││   0x0000004b      mov dptr, #0x5906                          ; [0x5906:1]=255
       ││   0x0000004e      movx a, @dptr
       ││   0x0000004f      mov dptr, #0x8633                          ; [0x8633:1]=255
            0x00000052      movx @dptr, a
            0x00000053      mov dptr, #0x590d                          ; '\rY'
                                                                       ; [0x590d:1]=255
