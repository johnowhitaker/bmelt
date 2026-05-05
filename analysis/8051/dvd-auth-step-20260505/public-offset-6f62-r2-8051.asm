            0x00000022      8944           mov 0x44, r1                ; [0x44:1]=144
            0x00000024      e581           mov a, 0x81                 ; [0x81:1]=42
            0x00000026      f0             movx @dptr, a
            0x00000027      904a01         mov dptr, #0x4a01           ; [0x4a01:1]=255
            0x0000002a      e0             movx a, @dptr
        ┌─< 0x0000002b      601b           jz 0x0048
        │   0x0000002d      14             dec a
       ┌──< 0x0000002e      600f           jz 0x003f
       ││   0x00000030      14             dec a
      ┌───< 0x00000031      6003           jz 0x0036
      │││   0x00000033      14             dec a
     ┌────< 0x00000034      801b           sjmp 0x0051
     │└───> 0x00000036      78a7           mov r0, #0xa7
     │ ││   0x00000038      7600           mov @r0, #0x00
     │ ││   0x0000003a      08             inc r0
     │ ││   0x0000003b      7680           mov @r0, #0x80
     │┌───< 0x0000003d      8019           sjmp 0x0058
     ││└──> 0x0000003f      7803           mov r0, #0x03
     ││┌──< 0x00000041      30180a         jnb 0x23.0, 0x004e          ; [0x23:1]=68
     ││││   0x00000044      90486a         mov dptr, #0x486a           ; 'jH'
     ││││                                                              ; [0x486a:1]=255
     ││││   0x00000047      e0             movx a, @dptr
     │││└─> 0x00000048      442c           orl a, #0x2c
     │││    0x0000004a      f0             movx @dptr, a
     │││    0x0000004b      a3             inc dptr
     │││┌─< 0x0000004c      8006           sjmp 0x0054
    ┌──└──> 0x0000004e      301c07         jnb 0x23.4, 0x0058          ; [0x23:1]=68
    │└────> 0x00000051      90486b         mov dptr, #0x486b           ; 'kH'
    │ │ │                                                              ; [0x486b:1]=255
    │ │ └─> 0x00000054      e0             movx a, @dptr
    │ │     0x00000055      4409           orl a, #0x09
    │ │     0x00000057      f0             movx @dptr, a
    └─└───> 0x00000058      904867         mov dptr, #0x4867           ; 'gH'
                                                                       ; [0x4867:1]=255
            0x0000005b      e0             movx a, @dptr
            0x0000005c      4414           orl a, #0x14
            0x0000005e      f0             movx @dptr, a
            0x0000005f      22             ret
            0x00000060      905904         mov dptr, #0x5904           ; [0x5904:1]=255
            0x00000063      e0             movx a, @dptr
            0x00000064      54f3           anl a, #0xf3
            0x00000066      f0             movx @dptr, a
            0x00000067      ee             mov a, r6
        ┌─< 0x00000068      704b           jnz 0x00b5
        │   0x0000006a      12fbe0         lcall 0xfbe0
        │   0x0000006d      ef             mov a, r7
       ┌──< 0x0000006e      6074           jz 0x00e4
       ││   0x00000070      9059a4         mov dptr, #0x59a4           ; [0x59a4:1]=255
       ││   0x00000073      e0             movx a, @dptr
       ││   0x00000074      54fe           anl a, #0xfe
       ││   0x00000076      f0             movx @dptr, a
       ││   0x00000077      905907         mov dptr, #0x5907           ; [0x5907:1]=255
       ││   0x0000007a      e0             movx a, @dptr
       ││   0x0000007b      547f           anl a, #0x7f
       ││   0x0000007d      f0             movx @dptr, a
       ││   0x0000007e      905964         mov dptr, #0x5964           ; 'dY'
       ││                                                              ; [0x5964:1]=255
       ││   0x00000081      2a             add a, r2
      ┌───< 0x00000082      600e           jz 0x0092
      │││   0x00000084      e0             movx a, @dptr
      │││   0x00000085      64aa           xrl a, #0xaa
     ┌────< 0x00000087      6009           jz 0x0092
     ││││   0x00000089      e0             movx a, @dptr
     ││││   0x0000008a      6428           xrl a, #0x28
    ┌─────< 0x0000008c      6004           jz 0x0092
    │││││   0x0000008e      e0             movx a, @dptr
   ┌──────< 0x0000008f      b4a809         cjne a, #0xa8, 0x009b
   │└└└───> 0x00000092      908a33         mov dptr, #0x8a33           ; [0x8a33:1]=255
   │   ││   0x00000095      e0             movx a, @dptr
   │  ┌───< 0x00000096      6003           jz 0x009b
   │  │││   0x00000098      12070b         lcall 0x070b
   └─┌└───> 0x0000009b      301f1e         jnb 0x23.7, 0x00bc          ; [0x23:1]=68
     │┌───< 0x0000009e      100a02         jbc 0x21.2, 0x00a3          ; [0x21:1]=144
    ┌─────< 0x000000a1      8019           sjmp 0x00bc
    ││└───> 0x000000a3      904019         mov dptr, #0x4019           ; '\x19@'
    ││ ││                                                              ; [0x4019:1]=255
    ││ ││   0x000000a6      e0             movx a, @dptr
    ││ ││   0x000000a7      54ef           anl a, #0xef
    ││ ││   0x000000a9      f0             movx @dptr, a
    ││ ││   0x000000aa      78b5           mov r0, #0xb5
    ││ ││   0x000000ac      e6             mov a, @r0
    ││┌───< 0x000000ad      700d           jnz 0x00bc
    │││││   0x000000af      d209           setb 0x21.1                 ; [0x21:1]=144
    │││││   0x000000b1      904220         mov dptr, #0x4220           ; ' B'
    │││││                                                              ; [0x4220:1]=255
    │││││   0x000000b4      7404           mov a, #0x04
    ││││    0x000000b6      f0             movx @dptr, a
    ││││    0x000000b7      e4             clr a
    ││││    0x000000b8      908fc9         mov dptr, #0x8fc9           ; [0x8fc9:1]=255
    ││││    0x000000bb      f0             movx @dptr, a
    └└└───> 0x000000bc      908ad9         mov dptr, #0x8ad9           ; [0x8ad9:1]=255
       │    0x000000bf      e0             movx a, @dptr
       │    0x000000c0      6401           xrl a, #0x01
       │┌─< 0x000000c2      704b           jnz 0x010f
       ││   0x000000c4      90893d         mov dptr, #0x893d           ; [0x893d:1]=255
       ││   0x000000c7      e0             movx a, @dptr
      ┌───< 0x000000c8      30e044         jnb 0xe0.0, 0x010f          ; [0xe0:1]=136
      │││   0x000000cb      7f00           mov r7, #0x00
      │││   0x000000cd      12050d         lcall 0x050d
      │││   0x000000d0      908988         mov dptr, #0x8988           ; [0x8988:1]=255
      │││   0x000000d3      e0             movx a, @dptr
      │││   0x000000d4      fc             mov r4, a
      │││   0x000000d5      a3             inc dptr
      │││   0x000000d6      e0             movx a, @dptr
      │││   0x000000d7      fd             mov r5, a
      │││   0x000000d8      c3             clr c
      │││   0x000000d9      ef             mov a, r7
      │││   0x000000da      9d             subb a, r5
      │││   0x000000db      ff             mov r7, a
      │││   0x000000dc      ee             mov a, r6
      │││   0x000000dd      9c             subb a, r4
      │││   0x000000de      908988         mov dptr, #0x8988           ; [0x8988:1]=255
      │││   0x000000e1      f0             movx @dptr, a
      │││   0x000000e2      a3             inc dptr
      │││   0x000000e3      ef             mov a, r7
      │└──> 0x000000e4      f0             movx @dptr, a
      │ │   0x000000e5      7da0           mov r5, #0xa0
      │ │   0x000000e7      7ffb           mov r7, #0xfb
      │ │   0x000000e9      123d89         lcall 0x3d89
      │ │   0x000000ec      9047c9         mov dptr, #0x47c9           ; [0x47c9:1]=255
      │ │   0x000000ef      e0             movx a, @dptr
      │ │   0x000000f0      ff             mov r7, a
      │ │   0x000000f1      9047cb         mov dptr, #0x47cb           ; [0x47cb:1]=255
      │ │   0x000000f4      e0             movx a, @dptr
      │ │   0x000000f5      fd             mov r5, a
      │ │   0x000000f6      123d89         lcall 0x3d89
      │ │   0x000000f9      78ab           mov r0, #0xab
      │ │   0x000000fb      e6             mov a, @r0
      │ │   0x000000fc      ff             mov r7, a
      │ │   0x000000fd      78b0           mov r0, #0xb0
      │ │   0x000000ff      e6             mov a, @r0
      │ │   0x00000100      0b             inc r3
      │ │   0x00000101      e0             movx a, @dptr
