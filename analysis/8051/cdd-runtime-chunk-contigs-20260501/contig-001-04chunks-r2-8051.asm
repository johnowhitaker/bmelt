            0x00000000      xrl a, #0xfe
        ┌─< 0x00000002      jnz 0x0007
       ┌──< 0x00000004      ljmp 0x767b
       │└─> 0x00000007      mov dptr, #0x891f                          ; [0x891f:1]=255
       │    0x0000000a      movx a, @dptr
       │    0x0000000b      add a, #0x38
       │    0x0000000d      mov r7, a
       │    0x0000000e      mov dptr, #0x891e                          ; [0x891e:1]=255
       │    0x00000011      movx a, @dptr
       │    0x00000012      addc a, #0x07
       │    0x00000014      mov r6, a
       │    0x00000015      mov a, r7
       │    0x00000016      mov r0, #0xaa
       │    0x00000018      add a, @r0
       │    0x00000019      mov r7, a
       │    0x0000001a      mov a, r6
       │    0x0000001b      dec r0
       │    0x0000001c      addc a, @r0
       │    0x0000001d      mov r0, 0x7c                               ; [0x7c:1]=36
       │    0x0000001f      inc r0
       │    0x00000020      inc r0
       │    0x00000021      mov @r0, a
       │    0x00000022      inc r0
       │    0x00000023      mov a, r7
       │    0x00000024      mov @r0, a
       │┌─> 0x00000025      mov dptr, #0x4000                          ; [0x4000:1]=255
       │╎   0x00000028      movx a, @dptr
       │└─< 0x00000029      jb 0xe0.7, 0x0025                          ; [0xe0:1]=144
       │    0x0000002c      mov dptr, #0x8ac6                          ; [0x8ac6:1]=255
       │    0x0000002f      movx a, @dptr
       │    0x00000030      mov dptr, #0x4095                          ; [0x4095:1]=255
       │    0x00000033      movx @dptr, a
       │    0x00000034      mov r0, 0x7c                               ; [0x7c:1]=36
       │    0x00000036      inc r0
       │    0x00000037      inc r0
       │    0x00000038      mov a, @r0
       │    0x00000039      inc dptr
       │    0x0000003a      movx @dptr, a
       │    0x0000003b      mov r3, #0x00
       │    0x0000003d      mov r1, 0x7c                               ; [0x7c:1]=36
       │    0x0000003f      inc r1
       │    0x00000040      inc r1
       │    0x00000041      mov r2, #0x00
       │    0x00000043      mov dptr, #0x0001                          ; [0x1:1]=254
       │    0x00000046      lcall 0x2fb7
       │    0x00000049      mov dptr, #0x4097                          ; [0x4097:1]=255
       │    0x0000004c      movx @dptr, a
       │    0x0000004d      mov dptr, #0x409c                          ; [0x409c:1]=255
