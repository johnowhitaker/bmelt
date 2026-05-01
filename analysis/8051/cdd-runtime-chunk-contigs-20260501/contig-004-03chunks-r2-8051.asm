            0x00000000      mov 0x29, r2                               ; [0x29:1]=240
            0x00000002      movx a, @dptr
            0x00000003      swap a
            0x00000004      anl a, #0x0f
        ┌─< 0x00000006      jnb 0xe0.0, 0x001a                         ; [0xe0:1]=255 ; 224
        │   0x00000009      mov dptr, #0x8a4c                          ; [0x8a4c:1]=255
        │   0x0000000c      movx a, @dptr
        │   0x0000000d      clr c
        │   0x0000000e      subb a, #0x0e
       ┌──< 0x00000010      jc 0x001a
       ││   0x00000012      mov dptr, #0x4011                          ; '\x11@'
       ││                                                              ; [0x4011:1]=255
       ││   0x00000015      mov a, #0x0e
       ││   0x00000017      movx @dptr, a
      ┌───< 0x00000018      sjmp 0x0022
      │└└─> 0x0000001a      mov dptr, #0x8a4c                          ; [0x8a4c:1]=255
      │     0x0000001d      movx a, @dptr
      │     0x0000001e      mov dptr, #0x4011                          ; '\x11@'
      │                                                                ; [0x4011:1]=255
      │     0x00000021      movx @dptr, a
      └───> 0x00000022      mov dptr, #0x8a4d                          ; [0x8a4d:1]=255
            0x00000025      movx a, @dptr
            0x00000026      mov dptr, #0x4012                          ; '\x12@'
                                                                       ; [0x4012:1]=255
            0x00000029      movx @dptr, a
            0x0000002a      mov dptr, #0x8a4e                          ; [0x8a4e:1]=255
            0x0000002d      movx a, @dptr
            0x0000002e      mov dptr, #0x4013                          ; '\x13@'
                                                                       ; [0x4013:1]=255
            0x00000031      movx @dptr, a
            0x00000032      mov dptr, #0x8a50                          ; [0x8a50:1]=255
            0x00000035      movx a, @dptr
            0x00000036      mov r7, a
            0x00000037      inc dptr
            0x00000038      movx a, @dptr
            0x00000039      mov r0, #0xa9
            0x0000003b      xch a, r7
            0x0000003c      mov @r0, a
            0x0000003d      inc r0
            0x0000003e      mov a, r7
            0x0000003f      mov @r0, a
            0x00000040      mov @r0, a
            0x00000041      inc r0
            0x00000042      mov @r0, #0x01
            0x00000044      lcall 0xefb6
            0x00000047      inc 0x7c                                   ; [0x7c:1]=144
            0x00000049      inc 0x7c                                   ; [0x7c:1]=144
            0x0000004b      ret
            0x0000004c      mov dptr, #0x8857                          ; [0x8857:1]=255
            0x0000004f      movx a, @dptr
            0x00000050      mov dptr, #0x885d                          ; [0x885d:1]=255
            0x00000053      movx @dptr, a
