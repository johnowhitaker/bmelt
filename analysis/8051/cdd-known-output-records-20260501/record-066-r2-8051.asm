            0x00000000      00             nop
            0x00000001      00             nop
            0x00000002      00             nop
            0x00000003      00             nop
            0x00000004      00             nop
            0x00000005      00             nop
            0x00000006      00             nop
            0x00000007      00             nop
            0x00000008      00             nop
            0x00000009      00             nop
            0x0000000a      00             nop
            0x0000000b      00             nop
            0x0000000c      00             nop
            0x0000000d      00             nop
            0x0000000e      00             nop
            0x0000000f      00             nop
            0x00000010      b79040         cjne @r1, #0x90, 0x0053
            0x00000013      97             subb a, @r1
            0x00000014      f0             movx @dptr, a
        ┌─> 0x00000015      904000         mov dptr, #0x4000           ; [0x4000:1]=255
        ╎   0x00000018      e0             movx a, @dptr
        └─< 0x00000019      20e7f9         jb 0xe0.7, 0x0015           ; [0xe0:1]=7
            0x0000001c      9040b6         mov dptr, #0x40b6           ; [0x40b6:1]=255
            0x0000001f      e4             clr a
            0x00000020      f0             movx @dptr, a
            0x00000021      908a54         mov dptr, #0x8a54           ; [0x8a54:1]=255
            0x00000024      e0             movx a, @dptr
            0x00000025      9040b7         mov dptr, #0x40b7           ; [0x40b7:1]=255
            0x00000028      f0             movx @dptr, a
            0x00000029      9040b5         mov dptr, #0x40b5           ; [0x40b5:1]=255
            0x0000002c      7414           mov a, #0x14
            0x0000002e      f0             movx @dptr, a
        ┌─> 0x0000002f      904000         mov dptr, #0x4000           ; [0x4000:1]=255
        ╎   0x00000032      e0             movx a, @dptr
        └─< 0x00000033      20e7f9         jb 0xe0.7, 0x002f           ; [0xe0:1]=7
            0x00000036      9040b5         mov dptr, #0x40b5           ; [0x40b5:1]=255
            0x00000039      7410           mov a, #0x10
            0x0000003b      f0             movx @dptr, a
            0x0000003c      908a54         mov dptr, #0x8a54           ; [0x8a54:1]=255
            0x0000003f      e0             movx a, @dptr
            0x00000040      ff             mov r7, a
            0x00000041      7e00           mov r6, #0x00
            0x00000043      78aa           mov r0, #0xaa
            0x00000045      26             add a, @r0
            0x00000046      f6             mov @r0, a
            0x00000047      18             dec r0
            0x00000048      ee             mov a, r6
            0x00000049      36             addc a, @r0
            0x0000004a      f6             mov @r0, a
            0x0000004b      a87c           mov r0, 0x7c                ; [0x7c:1]=224
            0x0000004d      08             inc r0
            0x0000004e      ef             mov a, r7
            0x0000004f      26             add a, @r0
            0x00000050      8571e5         mov 0xe5, 0x71              ; [0x71:1]=48
            0x00000053      a8f0           mov r0, 0xf0                ; [0xf0:1]=63
            0x00000055      75a890         mov 0xa8, #0x90             ; [0xa8:1]=137
        ┌─< 0x00000058      203e06         jb 0x27.6, 0x0061           ; [0x27:1]=183
       ┌──< 0x0000005b      204f03         jb 0x29.7, 0x0061           ; [0x29:1]=144
      ┌───< 0x0000005e      303f07         jnb 0x27.7, 0x0068          ; [0x27:1]=183
      │└└─> 0x00000061      908a29         mov dptr, #0x8a29           ; [0x8a29:1]=255
      │     0x00000064      e0             movx a, @dptr
      │ ┌─< 0x00000065      30e01b         jnb 0xe0.0, 0x0083          ; [0xe0:1]=7
      └───> 0x00000068      908a34         mov dptr, #0x8a34           ; [0x8a34:1]=255
        │   0x0000006b      e0             movx a, @dptr
        │   0x0000006c      ff             mov r7, a
        │   0x0000006d      13             rrc a
        │   0x0000006e      13             rrc a
        │   0x0000006f      543f           anl a, #0x3f
       ┌──< 0x00000071      30e00c         jnb 0xe0.0, 0x0080          ; [0xe0:1]=7
       ││   0x00000074      7f02           mov r7, #0x02
       ││   0x00000076      12db41         lcall 0xdb41
       ││   0x00000079      908a34         mov dptr, #0x8a34           ; [0x8a34:1]=255
       ││   0x0000007c      e0             movx a, @dptr
       ││   0x0000007d      54fb           anl a, #0xfb
       ││   0x0000007f      f0             movx @dptr, a
       └──> 0x00000080      12061b         lcall 0x061b
        └─> 0x00000083      908571         mov dptr, #0x8571           ; [0x8571:1]=255
            0x00000086      e0             movx a, @dptr
            0x00000087      f5a8           mov 0xa8, a                 ; [0xa8:1]=137
        ┌─< 0x00000089      024e65         ljmp 0x4e65
        │   0x0000008c      904789         mov dptr, #0x4789           ; [0x4789:1]=255
        │   0x0000008f      e0             movx a, @dptr
        │   0x00000090      f6             mov @r0, a
        │   0x00000091      18             dec r0
        │   0x00000092      ee             mov a, r6
        │   0x00000093      36             addc a, @r0
        │   0x00000094      f6             mov @r0, a
        │   0x00000095      908a4a         mov dptr, #0x8a4a           ; [0x8a4a:1]=255
        │   0x00000098      e0             movx a, @dptr
        │   0x00000099      6402           xrl a, #0x02
       ┌──< 0x0000009b      6003           jz 0x00a0
      ┌───< 0x0000009d      0273de         ljmp 0x73de
      │└──> 0x000000a0      90891f         mov dptr, #0x891f           ; [0x891f:1]=255
      │ │   0x000000a3      e0             movx a, @dptr
      │ │   0x000000a4      2434           add a, #0x34
      │ │   0x000000a6      ff             mov r7, a
      │ │   0x000000a7      90891e         mov dptr, #0x891e           ; [0x891e:1]=255
      │ │   0x000000aa      e0             movx a, @dptr
      │ │   0x000000ab      3407           addc a, #0x07
      │ │   0x000000ad      a87c           mov r0, 0x7c                ; [0x7c:1]=224
      │ │   0x000000af      08             inc r0
      │ │   0x000000b0      08             inc r0
      │ │   0x000000b1      f6             mov @r0, a
      │ │   0x000000b2      08             inc r0
      │ │   0x000000b3      ef             mov a, r7
      │ │   0x000000b4      f6             mov @r0, a
      │┌──> 0x000000b5      904000         mov dptr, #0x4000           ; [0x4000:1]=255
      │╎│   0x000000b8      e0             movx a, @dptr
      │└──< 0x000000b9      20e7f9         jb 0xe0.7, 0x00b5           ; [0xe0:1]=7
      │ │   0x000000bc      908ac6         mov dptr, #0x8ac6           ; [0x8ac6:1]=255
      │ │   0x000000bf      e0             movx a, @dptr
      │ │   0x000000c0      904091         mov dptr, #0x4091           ; [0x4091:1]=255
      │ │   0x000000c3      f0             movx @dptr, a
      │ │   0x000000c4      a87c           mov r0, 0x7c                ; [0x7c:1]=224
      │ │   0x000000c6      08             inc r0
      │ │   0x000000c7      08             inc r0
      │ │   0x000000c8      e6             mov a, @r0
      │ │   0x000000c9      a3             inc dptr
      │ │   0x000000ca      f0             movx @dptr, a
      │ │   0x000000cb      7b00           mov r3, #0x00
      │ │   0x000000cd      a97c           mov r1, 0x7c                ; [0x7c:1]=224
      │ │   0x000000cf      09             inc r1
      │ │   0x000000d0      8571e5         mov 0xe5, 0x71              ; [0x71:1]=48
      │ │   0x000000d3      a8f0           mov r0, 0xf0                ; [0xf0:1]=63
      │ │   0x000000d5      75a890         mov 0xa8, #0x90             ; [0xa8:1]=137
      │┌──< 0x000000d8      203e06         jb 0x27.6, 0x00e1           ; [0x27:1]=183
     ┌────< 0x000000db      204f03         jb 0x29.7, 0x00e1           ; [0x29:1]=144
    ┌─────< 0x000000de      303f07         jnb 0x27.7, 0x00e8          ; [0x27:1]=183
    │└─└──> 0x000000e1      908a29         mov dptr, #0x8a29           ; [0x8a29:1]=255
    │ │ │   0x000000e4      e0             movx a, @dptr
    │ │┌──< 0x000000e5      30e01b         jnb 0xe0.0, 0x0103          ; [0xe0:1]=7
    └─────> 0x000000e8      908a34         mov dptr, #0x8a34           ; [0x8a34:1]=255
      │││   0x000000eb      e0             movx a, @dptr
      │││   0x000000ec      ff             mov r7, a
      │││   0x000000ed      13             rrc a
      │││   0x000000ee      13             rrc a
      │││   0x000000ef      543f           anl a, #0x3f
     ┌────< 0x000000f1      30e00c         jnb 0xe0.0, 0x0100          ; [0xe0:1]=7
     ││││   0x000000f4      7f02           mov r7, #0x02
     ││││   0x000000f6      12db41         lcall 0xdb41
     ││││   0x000000f9      908a34         mov dptr, #0x8a34           ; [0x8a34:1]=255
     ││││   0x000000fc      e0             movx a, @dptr
     ││││   0x000000fd      54fb           anl a, #0xfb
     ││││   0x000000ff      f0             movx @dptr, a
     └────> 0x00000100      12061b         lcall 0x061b
      │└──> 0x00000103      908571         mov dptr, #0x8571           ; [0x8571:1]=255
      │ │   0x00000106      e0             movx a, @dptr
      │ │   0x00000107      f5a8           mov 0xa8, a                 ; [0xa8:1]=137
      │ │   0x00000109      024e65         ljmp 0x4e65
      │ │   0x0000010c      904789         mov dptr, #0x4789           ; [0x4789:1]=255
      │ │   0x0000010f      e0             movx a, @dptr
      │ │   0x00000110      f6             mov @r0, a
      │ │   0x00000111      18             dec r0
      │ │   0x00000112      ee             mov a, r6
      │ │   0x00000113      36             addc a, @r0
      │ │   0x00000114      f6             mov @r0, a
      │ │   0x00000115      908a4a         mov dptr, #0x8a4a           ; [0x8a4a:1]=255
      │ │   0x00000118      e0             movx a, @dptr
      │ │   0x00000119      6402           xrl a, #0x02
      │ │   0x0000011b      6003           jz 0x0120
      │ │   0x0000011d      0273de         ljmp 0x73de
      │ │   0x00000120      90891f         mov dptr, #0x891f           ; [0x891f:1]=255
      │ │   0x00000123      e0             movx a, @dptr
      │ │   0x00000124      2434           add a, #0x34
      │ │   0x00000126      ff             mov r7, a
      │ │   0x00000127      90891e         mov dptr, #0x891e           ; [0x891e:1]=255
      │ │   0x0000012a      e0             movx a, @dptr
      │ │   0x0000012b      3407           addc a, #0x07
      │ │   0x0000012d      a87c           mov r0, 0x7c                ; [0x7c:1]=224
      │ │   0x0000012f      08             inc r0
      │ │   0x00000130      08             inc r0
      │ │   0x00000131      f6             mov @r0, a
      │ │   0x00000132      08             inc r0
      │ │   0x00000133      ef             mov a, r7
      │ │   0x00000134      f6             mov @r0, a
      │ │   0x00000135      904000         mov dptr, #0x4000           ; [0x4000:1]=255
      │ │   0x00000138      e0             movx a, @dptr
      │ │   0x00000139      20e7f9         jb 0xe0.7, 0x0135           ; [0xe0:1]=7
      │ │   0x0000013c      908ac6         mov dptr, #0x8ac6           ; [0x8ac6:1]=255
      │ │   0x0000013f      e0             movx a, @dptr
