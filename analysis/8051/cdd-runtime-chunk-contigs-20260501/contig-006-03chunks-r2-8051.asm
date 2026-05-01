            0x00000000      xch a, r3
            0x00000001      movx @dptr, a
            0x00000002      mov dptr, #0x47c9                          ; [0x47c9:1]=255
            0x00000005      mov a, #0x51                               ; 'Q'
            0x00000007      movx @dptr, a
            0x00000008      mov dptr, #0x47a8                          ; [0x47a8:1]=255
            0x0000000b      movx a, @dptr
            0x0000000c      anl a, #0x28
            0x0000000e      mov r7, a
        ┌─< 0x0000000f      cjne r7, #0x28, 0x0020
        │   0x00000012      movx a, @dptr
        │   0x00000013      orl a, #0x10
        │   0x00000015      movx @dptr, a
        │   0x00000016      movx a, @dptr
        │   0x00000017      anl a, #0xef
        │   0x00000019      movx @dptr, a
        │   0x0000001a      mov dptr, #0x8a33                          ; [0x8a33:1]=255
        │   0x0000001d      mov a, #0x01
        │   0x0000001f      movx @dptr, a
        └─> 0x00000020      mov dptr, #0x47c4                          ; [0x47c4:1]=255
            0x00000023      clr a
            0x00000024      movx @dptr, a
            0x00000025      inc dptr
            0x00000026      movx @dptr, a
            0x00000027      mov dptr, #0x47c2                          ; [0x47c2:1]=255
            0x0000002a      mov a, #0x03
            0x0000002c      movx @dptr, a
            0x0000002d      mov dptr, #0x8ad9                          ; [0x8ad9:1]=255
            0x00000030      movx a, @dptr
            0x00000031      xrl a, #0x01
        ┌─< 0x00000033      jz 0x0038
       ┌──< 0x00000035      ljmp 0xb2cb
       │└─> 0x00000038      mov dptr, #0x893d                          ; [0x893d:1]=255
       │    0x0000003b      movx a, @dptr
       │┌─< 0x0000003c      jb 0xe0.0, 0x0042                          ; [0xe0:1]=255 ; 224
      ┌───< 0x0000003f      ljmp 0x25e0
      ││└─> 0x00000042      mov 0xf0, #0x0a                            ; [0xf0:1]=255 ; 10
      ││    0x00000045      div ab
      ││    0x00000046      mov r5, a
      ││    0x00000047      mov r4, #0x00
      ││    0x00000049      mov a, r7
      ││    0x0000004a      mov 0xf0, #0xb0                            ; [0xf0:1]=255 ; 176
      ││    0x0000004d      mul ab
      ││    0x0000004e      add a, r5
      ││    0x0000004f      mov r7, a
      ││    0x00000050      mov a, r4
      ││    0x00000051      addc a, 0xf0                               ; [0xf0:1]=255 ; 240
      ││    0x00000053      xch a, r7
