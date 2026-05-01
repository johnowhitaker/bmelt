            0x00000000      mov r6, a
            0x00000001      inc r0
            0x00000002      mov a, @r0
            0x00000003      mov r7, a
            0x00000004      mov dptr, #0x891f                          ; [0x891f:1]=255
            0x00000007      movx a, @dptr
            0x00000008      add a, r7
            0x00000009      mov r7, a
            0x0000000a      mov dptr, #0x891e                          ; [0x891e:1]=255
            0x0000000d      movx a, @dptr
            0x0000000e      addc a, r6
            0x0000000f      mov r0, 0x7c                               ; [0x7c:1]=163
            0x00000011      inc r0
            0x00000012      inc r0
            0x00000013      mov @r0, a
            0x00000014      inc r0
            0x00000015      mov a, r7
            0x00000016      mov @r0, a
        ┌─> 0x00000017      mov dptr, #0x4000                          ; [0x4000:1]=255
        ╎   0x0000001a      movx a, @dptr
        └─< 0x0000001b      jb 0xe0.7, 0x0017                          ; [0xe0:1]=255 ; 224
            0x0000001e      mov dptr, #0x8ac6                          ; [0x8ac6:1]=255
            0x00000021      movx a, @dptr
            0x00000022      mov dptr, #0x4091                          ; [0x4091:1]=255
            0x00000025      movx @dptr, a
            0x00000026      mov r0, 0x7c                               ; [0x7c:1]=163
            0x00000028      inc r0
            0x00000029      inc r0
            0x0000002a      mov a, @r0
            0x0000002b      inc dptr
            0x0000002c      movx @dptr, a
            0x0000002d      mov r3, #0x00
            0x0000002f      mov r1, 0x7c                               ; [0x7c:1]=163
            0x00000031      inc r1
            0x00000032      inc r1
            0x00000033      mov r2, #0x00
            0x00000035      mov dptr, #0x0001                          ; [0x1:1]=8
            0x00000038      lcall 0x2fb7
            0x0000003b      mov dptr, #0x4093                          ; [0x4093:1]=255
            0x0000003e      movx @dptr, a
            0x0000003f      mov dptr, #0xf012                          ; [0xf012:1]=255
            0x00000042      dec a
            0x00000043      addc a, @r1
            0x00000044      mov dptr, #0x8aed                          ; [0x8aed:1]=255
            0x00000047      movx a, @dptr
        ┌─< 0x00000048      jnb 0xe0.2, 0x0070                         ; [0xe0:1]=255 ; 224
        │   0x0000004b      mov dptr, #0x89dd                          ; [0x89dd:1]=255
        │   0x0000004e      movx a, @dptr
