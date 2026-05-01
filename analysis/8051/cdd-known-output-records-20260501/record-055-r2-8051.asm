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
            0x00000010      00             nop
            0x00000011      00             nop
            0x00000012      00             nop
            0x00000013      00             nop
            0x00000014      00             nop
            0x00000015      00             nop
            0x00000016      00             nop
            0x00000017      00             nop
            0x00000018      00             nop
            0x00000019      00             nop
            0x0000001a      00             nop
            0x0000001b      00             nop
            0x0000001c      00             nop
            0x0000001d      00             nop
            0x0000001e      00             nop
            0x0000001f      00             nop
            0x00000020      00             nop
            0x00000021      00             nop
            0x00000022      00             nop
            0x00000023      00             nop
            0x00000024      00             nop
            0x00000025      00             nop
            0x00000026      00             nop
            0x00000027      00             nop
            0x00000028      00             nop
            0x00000029      00             nop
            0x0000002a      00             nop
            0x0000002b      00             nop
            0x0000002c      00             nop
            0x0000002d      00             nop
            0x0000002e      00             nop
            0x0000002f      00             nop
            0x00000030      00             nop
            0x00000031      00             nop
            0x00000032      00             nop
            0x00000033      00             nop
            0x00000034      00             nop
            0x00000035      00             nop
            0x00000036      00             nop
            0x00000037      00             nop
            0x00000038      00             nop
            0x00000039      00             nop
            0x0000003a      00             nop
            0x0000003b      00             nop
            0x0000003c      00             nop
            0x0000003d      00             nop
            0x0000003e      00             nop
            0x0000003f      00             nop
            0x00000040      00             nop
            0x00000041      00             nop
            0x00000042      00             nop
            0x00000043      00             nop
            0x00000044      00             nop
            0x00000045      00             nop
            0x00000046      00             nop
            0x00000047      00             nop
            0x00000048      00             nop
            0x00000049      00             nop
            0x0000004a      00             nop
            0x0000004b      00             nop
            0x0000004c      00             nop
            0x0000004d      00             nop
            0x0000004e      00             nop
            0x0000004f      00             nop
            0x00000050      00             nop
            0x00000051      00             nop
            0x00000052      00             nop
            0x00000053      00             nop
            0x00000054      00             nop
            0x00000055      00             nop
            0x00000056      00             nop
            0x00000057      00             nop
            0x00000058      00             nop
            0x00000059      00             nop
            0x0000005a      00             nop
            0x0000005b      00             nop
            0x0000005c      00             nop
            0x0000005d      00             nop
            0x0000005e      00             nop
            0x0000005f      00             nop
            0x00000060      00             nop
            0x00000061      00             nop
            0x00000062      00             nop
            0x00000063      00             nop
            0x00000064      00             nop
            0x00000065      00             nop
            0x00000066      00             nop
            0x00000067      00             nop
            0x00000068      00             nop
            0x00000069      00             nop
            0x0000006a      00             nop
            0x0000006b      00             nop
            0x0000006c      00             nop
            0x0000006d      00             nop
            0x0000006e      00             nop
            0x0000006f      00             nop
            0x00000070      00             nop
            0x00000071      00             nop
            0x00000072      00             nop
            0x00000073      00             nop
            0x00000074      00             nop
            0x00000075      00             nop
            0x00000076      00             nop
            0x00000077      00             nop
            0x00000078      00             nop
            0x00000079      00             nop
            0x0000007a      00             nop
            0x0000007b      00             nop
            0x0000007c      00             nop
            0x0000007d      00             nop
            0x0000007e      00             nop
            0x0000007f      00             nop
            0x00000080      908a4d         mov dptr, #0x8a4d           ; [0x8a4d:1]=255
            0x00000083      e0             movx a, @dptr
            0x00000084      fe             mov r6, a
            0x00000085      a3             inc dptr
            0x00000086      e0             movx a, @dptr
            0x00000087      ff             mov r7, a
            0x00000088      908a53         mov dptr, #0x8a53           ; [0x8a53:1]=255
            0x0000008b      ee             mov a, r6
            0x0000008c      f0             movx @dptr, a
            0x0000008d      a3             inc dptr
            0x0000008e      ef             mov a, r7
            0x0000008f      f0             movx @dptr, a
            0x00000090      c3             clr c
            0x00000091      e4             clr a
            0x00000092      9f             subb a, r7
            0x00000093      f0             movx @dptr, a
            0x00000094      7420           mov a, #0x20
            0x00000096      9e             subb a, r6
            0x00000097      908a53         mov dptr, #0x8a53           ; [0x8a53:1]=255
            0x0000009a      f0             movx @dptr, a
            0x0000009b      908a4e         mov dptr, #0x8a4e           ; [0x8a4e:1]=255
            0x0000009e      e0             movx a, @dptr
            0x0000009f      2400           add a, #0x00
            0x000000a1      f0             movx @dptr, a
            0x000000a2      908a4d         mov dptr, #0x8a4d           ; [0x8a4d:1]=255
            0x000000a5      e0             movx a, @dptr
            0x000000a6      3440           addc a, #0x40
        ┌─< 0x000000a8      807a           sjmp 0x0124
        │   0x000000aa      908a4f         mov dptr, #0x8a4f           ; [0x8a4f:1]=255
        │   0x000000ad      e0             movx a, @dptr
       ┌──< 0x000000ae      7014           jnz 0x00c4
       ││   0x000000b0      a3             inc dptr
       ││   0x000000b1      e0             movx a, @dptr
      ┌───< 0x000000b2      7004           jnz 0x00b8
      │││   0x000000b4      a3             inc dptr
      │││   0x000000b5      e0             movx a, @dptr
      │││   0x000000b6      6480           xrl a, #0x80
     ┌└───> 0x000000b8      700a           jnz 0x00c4
     │ ││   0x000000ba      908a4c         mov dptr, #0x8a4c           ; [0x8a4c:1]=255
     │ ││   0x000000bd      e0             movx a, @dptr
     │ ││   0x000000be      fd             mov r5, a
     │ ││   0x000000bf      c3             clr c
     │ ││   0x000000c0      98             subb a, r0
     │ ││   0x000000c1      e54c           mov a, 0x4c                 ; [0x4c:1]=0
     │ ││   0x000000c3      f0             movx @dptr, a
     └┌└──> 0x000000c4      904000         mov dptr, #0x4000           ; [0x4000:1]=255
      ╎ │   0x000000c7      e0             movx a, @dptr
      └───< 0x000000c8      20e7f9         jb 0xe0.7, 0x00c4           ; [0xe0:1]=229
        │   0x000000cb      904098         mov dptr, #0x4098           ; [0x4098:1]=255
        │   0x000000ce      e54d           mov a, 0x4d                 ; [0x4d:1]=0
        │   0x000000d0      f0             movx @dptr, a
        │   0x000000d1      904000         mov dptr, #0x4000           ; [0x4000:1]=255
