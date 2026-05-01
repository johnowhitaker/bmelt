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
        ┌─< 0x00000020      02bf37         ljmp 0xbf37
        │   0x00000023      90852e         mov dptr, #0x852e           ; [0x852e:1]=255
        │   0x00000026      e0             movx a, @dptr
        │   0x00000027      14             dec a
        │   0x00000028      f0             movx @dptr, a
        │   0x00000029      e0             movx a, @dptr
       ┌──< 0x0000002a      7003           jnz 0x002f
      ┌───< 0x0000002c      02bf47         ljmp 0xbf47
      │└──> 0x0000002f      9055c6         mov dptr, #0x55c6           ; [0x55c6:1]=255
      │ │   0x00000032      e0             movx a, @dptr
      │ │   0x00000033      90855d         mov dptr, #0x855d           ; [0x855d:1]=255
      │ │   0x00000036      f0             movx @dptr, a
      │ │   0x00000037      e0             movx a, @dptr
      │┌──< 0x00000038      30e761         jnb 0xe0.7, 0x009c          ; [0xe0:1]=254
      │││   0x0000003b      7f5e           mov r7, #0x5e               ; '^'
      │││   0x0000003d      1208d9         lcall 0x08d9
      │││   0x00000040      90855b         mov dptr, #0x855b           ; [0x855b:1]=255
      │││   0x00000043      ef             mov a, r7
      │││   0x00000044      f0             movx @dptr, a
      │││   0x00000045      90830e         mov dptr, #0x830e           ; [0x830e:1]=255
      │││   0x00000048      e0             movx a, @dptr
      │││   0x00000049      fe             mov r6, a
      │││   0x0000004a      ef             mov a, r7
      │││   0x0000004b      d3             setb c
      │││   0x0000004c      9e             subb a, r6
     ┌────< 0x0000004d      4008           jc 0x0057
     ││││   0x0000004f      90855b         mov dptr, #0x855b           ; [0x855b:1]=255
     ││││   0x00000052      e0             movx a, @dptr
     ││││   0x00000053      90830e         mov dptr, #0x830e           ; [0x830e:1]=255
     ││││   0x00000056      f0             movx @dptr, a
     └────> 0x00000057      908320         mov dptr, #0x8320           ; [0x8320:1]=255
      │││   0x0000005a      e0             movx a, @dptr
      │││   0x0000005b      04             inc a
      │││   0x0000005c      f0             movx @dptr, a
      │││   0x0000005d      7f46           mov r7, #0x46               ; 'F'
      │││   0x0000005f      909dff         mov dptr, #0x9dff           ; [0x9dff:1]=255
      │││   0x00000062      ee             mov a, r6
      │││   0x00000063      9c             subb a, r4
      │││   0x00000064      908988         mov dptr, #0x8988           ; [0x8988:1]=255
      │││   0x00000067      f0             movx @dptr, a
      │││   0x00000068      a3             inc dptr
      │││   0x00000069      ef             mov a, r7
      │││   0x0000006a      f0             movx @dptr, a
      │││   0x0000006b      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
      │││   0x0000006e      e0             movx a, @dptr
     ┌────< 0x0000006f      b42829         cjne a, #0x28, 0x009b
     ││││   0x00000072      c3             clr c
     ││││   0x00000073      908989         mov dptr, #0x8989           ; [0x8989:1]=255
     ││││   0x00000076      e0             movx a, @dptr
     ││││   0x00000077      9464           subb a, #0x64
     ││││   0x00000079      908988         mov dptr, #0x8988           ; [0x8988:1]=255
     ││││   0x0000007c      e0             movx a, @dptr
     ││││   0x0000007d      9400           subb a, #0x00
    ┌─────< 0x0000007f      401a           jc 0x009b
    │││││   0x00000081      e4             clr a
    │││││   0x00000082      7f01           mov r7, #0x01
    │││││   0x00000084      fe             mov r6, a
    │││││   0x00000085      fd             mov r5, a
    │││││   0x00000086      fc             mov r4, a
    │││││   0x00000087      78a2           mov r0, #0xa2
    │││││   0x00000089      1233b2         lcall 0x33b2
    │││││   0x0000008c      c3             clr c
    │││││   0x0000008d      123311         lcall 0x3311
   ┌──────< 0x00000090      7009           jnz 0x009b
   ││││││   0x00000092      908a38         mov dptr, #0x8a38           ; [0x8a38:1]=255
   ││││││   0x00000095      e0             movx a, @dptr
   ││││││   0x00000096      4401           orl a, #0x01
   ││││││   0x00000098      f0             movx @dptr, a
  ┌───────< 0x00000099      8007           sjmp 0x00a2
  │└└└────> 0x0000009b      908a38         mov dptr, #0x8a38           ; [0x8a38:1]=255
  │   │ │   0x0000009e      e0             movx a, @dptr
  │   │ │   0x0000009f      54fe           anl a, #0xfe
  │   │ │   0x000000a1      f0             movx @dptr, a
  └───────> 0x000000a2      908ad9         mov dptr, #0x8ad9           ; [0x8ad9:1]=255
      │ │   0x000000a5      e0             movx a, @dptr
      │ │   0x000000a6      6401           xrl a, #0x01
      │┌──< 0x000000a8      705b           jnz 0x0105
      │││   0x000000aa      90893d         mov dptr, #0x893d           ; [0x893d:1]=255
      │││   0x000000ad      e0             movx a, @dptr
     ┌────< 0x000000ae      30e054         jnb 0xe0.0, 0x0105          ; [0xe0:1]=254
     ││││   0x000000b1      7da0           mov r5, #0xa0
     ││││   0x000000b3      7ffa           mov r7, #0xfa
     ││││   0x000000b5      123d89         lcall 0x3d89
     ││││   0x000000b8      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
     ││││   0x000000bb      e0             movx a, @dptr
     ││││   0x000000bc      ff             mov r7, a
     ││││   0x000000bd      a3             inc dptr
     ││││   0x000000be      e0             movx a, @dptr
     ││││   0x000000bf      fd             mov r5, a
     ││││   0x000000c0      123d89         lcall 0x3d89
     ││││   0x000000c3      908a4b         mov dptr, #0x8a4b           ; [0x8a4b:1]=255
     ││││   0x000000c6      e0             movx a, @dptr
     ││││   0x000000c7      ff             mov r7, a
     ││││   0x000000c8      a3             inc dptr
     ││││   0x000000c9      e0             movx a, @dptr
     ││││   0x000000ca      fd             mov r5, a
     ││││   0x000000cb      123d89         lcall 0x3d89
     ││││   0x000000ce      908a4d         mov dptr, #0x8a4d           ; [0x8a4d:1]=255
     ││││   0x000000d1      e0             movx a, @dptr
     ││││   0x000000d2      ff             mov r7, a
     ││││   0x000000d3      a3             inc dptr
     ││││   0x000000d4      e0             movx a, @dptr
     ││││   0x000000d5      fd             mov r5, a
     ││││   0x000000d6      123d89         lcall 0x3d89
     ││││   0x000000d9      908a4f         mov dptr, #0x8a4f           ; [0x8a4f:1]=255
     ││││   0x000000dc      e0             movx a, @dptr
     ││││   0x000000dd      ff             mov r7, a
     ││││   0x000000de      a3             inc dptr
     ││││   0x000000df      e0             movx a, @dptr
     ││││   0x000000e0      fe             mov r6, a
     ││││   0x000000e1      f0             movx @dptr, a
     ││││   0x000000e2      908ad9         mov dptr, #0x8ad9           ; [0x8ad9:1]=255
     ││││   0x000000e5      e0             movx a, @dptr
     ││││   0x000000e6      6401           xrl a, #0x01
    ┌─────< 0x000000e8      705b           jnz 0x0145
    │││││   0x000000ea      90893d         mov dptr, #0x893d           ; [0x893d:1]=255
    │││││   0x000000ed      e0             movx a, @dptr
   ┌──────< 0x000000ee      30e054         jnb 0xe0.0, 0x0145          ; [0xe0:1]=254
   ││││││   0x000000f1      7da0           mov r5, #0xa0
   ││││││   0x000000f3      7ffa           mov r7, #0xfa
   ││││││   0x000000f5      123d89         lcall 0x3d89
   ││││││   0x000000f8      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
   ││││││   0x000000fb      e0             movx a, @dptr
   ││││││   0x000000fc      ff             mov r7, a
   ││││││   0x000000fd      a3             inc dptr
   ││││││   0x000000fe      e0             movx a, @dptr
   ││││││   0x000000ff      fd             mov r5, a
   ││││││   0x00000100      123d89         lcall 0x3d89
   ││││││   0x00000103      908a4b         mov dptr, #0x8a4b           ; [0x8a4b:1]=255
   ││ │ │   0x00000106      e0             movx a, @dptr
   ││ │ │   0x00000107      ff             mov r7, a
   ││ │ │   0x00000108      a3             inc dptr
   ││ │ │   0x00000109      e0             movx a, @dptr
   ││ │ │   0x0000010a      fd             mov r5, a
   ││ │ │   0x0000010b      123d89         lcall 0x3d89
   ││ │ │   0x0000010e      908a4d         mov dptr, #0x8a4d           ; [0x8a4d:1]=255
   ││ │ │   0x00000111      e0             movx a, @dptr
   ││ │ │   0x00000112      ff             mov r7, a
   ││ │ │   0x00000113      a3             inc dptr
   ││ │ │   0x00000114      e0             movx a, @dptr
   ││ │ │   0x00000115      fd             mov r5, a
   ││ │ │   0x00000116      123d89         lcall 0x3d89
   ││ │ │   0x00000119      908a4f         mov dptr, #0x8a4f           ; [0x8a4f:1]=255
   ││ │ │   0x0000011c      e0             movx a, @dptr
   ││ │ │   0x0000011d      ff             mov r7, a
   ││ │ │   0x0000011e      a3             inc dptr
   ││ │ │   0x0000011f      e0             movx a, @dptr
   ││ │ │   0x00000120      fe             mov r6, a
