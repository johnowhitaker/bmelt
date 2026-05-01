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
            0x00000030      9081f5         mov dptr, #0x81f5           ; [0x81f5:1]=255
            0x00000033      e0             movx a, @dptr
            0x00000034      ff             mov r7, a
            0x00000035      908672         mov dptr, #0x8672           ; [0x8672:1]=255
            0x00000038      e0             movx a, @dptr
            0x00000039      fe             mov r6, a
            0x0000003a      6f             xrl a, r7
        ┌─< 0x0000003b      6015           jz 0x0052
        │   0x0000003d      908c84         mov dptr, #0x8c84           ; [0x8c84:1]=255
        │   0x00000040      7483           mov a, #0x83
        │   0x00000042      f0             movx @dptr, a
        │   0x00000043      a3             inc dptr
        │   0x00000044      74c3           mov a, #0xc3
        │   0x00000046      f0             movx @dptr, a
        │   0x00000047      e4             clr a
        │   0x00000048      a3             inc dptr
        │   0x00000049      f0             movx @dptr, a
        │   0x0000004a      a3             inc dptr
        │   0x0000004b      ee             mov a, r6
        │   0x0000004c      f0             movx @dptr, a
        │   0x0000004d      7f04           mov r7, #0x04
        │   0x0000004f      12014a         lcall 0x014a
        └─> 0x00000052      908672         mov dptr, #0x8672           ; [0x8672:1]=255
            0x00000055      e0             movx a, @dptr
            0x00000056      c3             clr c
            0x00000057      9403           subb a, #0x03
        ┌─< 0x00000059      4003           jc 0x005e
        │   0x0000005b      7403           mov a, #0x03
        │   0x0000005d      f0             movx @dptr, a
        └─> 0x0000005e      9081f5         mov dptr, #0x81f5           ; [0x81f5:1]=255
            0x00000061      e0             movx a, @dptr
            0x00000062      ff             mov r7, a
            0x00000063      908672         mov dptr, #0x8672           ; [0x8672:1]=255
            0x00000066      e0             movx a, @dptr
            0x00000067      fe             mov r6, a
            0x00000068      6f             xrl a, r7
        ┌─< 0x00000069      7003           jnz 0x006e
       ┌──< 0x0000006b      02b85d         ljmp 0xb85d
       │└─> 0x0000006e      908190         mov dptr, #0x8190           ; [0x8190:1]=255
      ┌───< 0x00000071      81f5           ajmp 0x04f5
      ││╎   0x00000073      e0             movx a, @dptr
      ││╎   0x00000074      ff             mov r7, a
      ││╎   0x00000075      908672         mov dptr, #0x8672           ; [0x8672:1]=255
      ││╎   0x00000078      e0             movx a, @dptr
      ││╎   0x00000079      fe             mov r6, a
      ││╎   0x0000007a      6f             xrl a, r7
     ┌────< 0x0000007b      6015           jz 0x0092
     │││╎   0x0000007d      908c84         mov dptr, #0x8c84           ; [0x8c84:1]=255
     │││╎   0x00000080      7483           mov a, #0x83
     │││╎   0x00000082      f0             movx @dptr, a
     │││╎   0x00000083      a3             inc dptr
     │││╎   0x00000084      74c3           mov a, #0xc3
     │││╎   0x00000086      f0             movx @dptr, a
     │││╎   0x00000087      e4             clr a
     │││╎   0x00000088      a3             inc dptr
     │││╎   0x00000089      f0             movx @dptr, a
     │││╎   0x0000008a      a3             inc dptr
     │││╎   0x0000008b      ee             mov a, r6
     │││╎   0x0000008c      f0             movx @dptr, a
     │││╎   0x0000008d      7f04           mov r7, #0x04
     │││╎   0x0000008f      12014a         lcall 0x014a
     └────> 0x00000092      908672         mov dptr, #0x8672           ; [0x8672:1]=255
      ││╎   0x00000095      e0             movx a, @dptr
      ││╎   0x00000096      c3             clr c
      ││╎   0x00000097      9403           subb a, #0x03
     ┌────< 0x00000099      4003           jc 0x009e
     │││╎   0x0000009b      7403           mov a, #0x03
     │││╎   0x0000009d      f0             movx @dptr, a
     └────> 0x0000009e      9081f5         mov dptr, #0x81f5           ; [0x81f5:1]=255
      ││╎   0x000000a1      e0             movx a, @dptr
      ││╎   0x000000a2      ff             mov r7, a
      ││╎   0x000000a3      908672         mov dptr, #0x8672           ; [0x8672:1]=255
      ││╎   0x000000a6      e0             movx a, @dptr
      ││╎   0x000000a7      fe             mov r6, a
      ││╎   0x000000a8      6f             xrl a, r7
     ┌────< 0x000000a9      7003           jnz 0x00ae
    ┌─────< 0x000000ab      02b85d         ljmp 0xb85d
    │└────> 0x000000ae      908164         mov dptr, #0x8164           ; [0x8164:1]=255
    │ ││└─< 0x000000b1      0170           ajmp 0x0070
    │ ││    0x000000b3      4b             orl a, r3
    │ ││    0x000000b4      90893d         mov dptr, #0x893d           ; [0x893d:1]=255
    │ ││    0x000000b7      e0             movx a, @dptr
    │ ││┌─< 0x000000b8      30e044         jnb 0xe0.0, 0x00ff          ; [0xe0:1]=255
    │ │││   0x000000bb      7f00           mov r7, #0x00
    │ │││   0x000000bd      12050d         lcall 0x050d
    │ │││   0x000000c0      908988         mov dptr, #0x8988           ; [0x8988:1]=255
    │ │││   0x000000c3      e0             movx a, @dptr
    │ │││   0x000000c4      fc             mov r4, a
    │ │││   0x000000c5      a3             inc dptr
    │ │││   0x000000c6      e0             movx a, @dptr
    │ │││   0x000000c7      fd             mov r5, a
    │ │││   0x000000c8      c3             clr c
    │ │││   0x000000c9      ef             mov a, r7
    │ │││   0x000000ca      9d             subb a, r5
    │ │││   0x000000cb      ff             mov r7, a
    │ │││   0x000000cc      ee             mov a, r6
    │ │││   0x000000cd      9c             subb a, r4
    │ │││   0x000000ce      908988         mov dptr, #0x8988           ; [0x8988:1]=255
    │ │││   0x000000d1      f0             movx @dptr, a
    │ │││   0x000000d2      a3             inc dptr
    │ │││   0x000000d3      ef             mov a, r7
    │ │││   0x000000d4      f0             movx @dptr, a
    │ │││   0x000000d5      7da0           mov r5, #0xa0
    │ │││   0x000000d7      7ffb           mov r7, #0xfb
    │ │││   0x000000d9      123d89         lcall 0x3d89
    │ │││   0x000000dc      9047c9         mov dptr, #0x47c9           ; [0x47c9:1]=255
    │ │││   0x000000df      e0             movx a, @dptr
    │ │││   0x000000e0      ff             mov r7, a
    │ │││   0x000000e1      9047cb         mov dptr, #0x47cb           ; [0x47cb:1]=255
    │ │││   0x000000e4      e0             movx a, @dptr
    │ │││   0x000000e5      fd             mov r5, a
    │ │││   0x000000e6      123d89         lcall 0x3d89
    │ │││   0x000000e9      78ab           mov r0, #0xab
    │ │││   0x000000eb      e6             mov a, @r0
    │ │││   0x000000ec      ff             mov r7, a
    │ │││   0x000000ed      78b0           mov r0, #0xb0
    │ │││   0x000000ef      e6             mov a, @r0
    │ │││   0x000000f0      6401           xrl a, #0x01
    │┌────< 0x000000f2      704b           jnz 0x013f
    │││││   0x000000f4      90893d         mov dptr, #0x893d           ; [0x893d:1]=255
    │││││   0x000000f7      e0             movx a, @dptr
   ┌──────< 0x000000f8      30e044         jnb 0xe0.0, 0x013f          ; [0xe0:1]=255
   ││││││   0x000000fb      7f00           mov r7, #0x00
   ││││││   0x000000fd      12050d         lcall 0x050d
   │││││    0x00000100      908988         mov dptr, #0x8988           ; [0x8988:1]=255
   │││││    0x00000103      e0             movx a, @dptr
   │││││    0x00000104      fc             mov r4, a
   │││││    0x00000105      a3             inc dptr
   │││││    0x00000106      e0             movx a, @dptr
   │││││    0x00000107      fd             mov r5, a
   │││││    0x00000108      c3             clr c
   │││││    0x00000109      ef             mov a, r7
