            0x00000000      9435           subb a, #0x35
            0x00000002      ee             mov a, r6
            0x00000003      9400           subb a, #0x00
        ┌─< 0x00000005      4014           jc 0x001b
        │   0x00000007      9089f7         mov dptr, #0x89f7           ; [0x89f7:1]=255
        │   0x0000000a      e0             movx a, @dptr
        │   0x0000000b      04             inc a
        │   0x0000000c      f0             movx @dptr, a
        │   0x0000000d      90893a         mov dptr, #0x893a           ; [0x893a:1]=255
        │   0x00000010      e0             movx a, @dptr
        │   0x00000011      2f             add a, r7
        │   0x00000012      f0             movx @dptr, a
        │   0x00000013      908939         mov dptr, #0x8939           ; [0x8939:1]=255
        │   0x00000016      e0             movx a, @dptr
        │   0x00000017      3e             addc a, r6
        │   0x00000018      f0             movx @dptr, a
       ┌──< 0x00000019      8005           sjmp 0x0020
       │└─> 0x0000001b      e4             clr a
       │    0x0000001c      9089f7         mov dptr, #0x89f7           ; [0x89f7:1]=255
       │    0x0000001f      f0             movx @dptr, a
       └──> 0x00000020      9089f7         mov dptr, #0x89f7           ; [0x89f7:1]=255
            0x00000023      e0             movx a, @dptr
        ┌─< 0x00000024      b4030a         cjne a, #0x03, 0x0031
        │   0x00000027      908939         mov dptr, #0x8939           ; [0x8939:1]=255
        │   0x0000002a      7401           mov a, #0x01
        │   0x0000002c      f0             movx @dptr, a
        │   0x0000002d      a3             inc dptr
        │   0x0000002e      74f4           mov a, #0xf4
        │   0x00000030      f0             movx @dptr, a
        └─> 0x00000031      7f00           mov r7, #0x00
            0x00000033      12050d         lcall 0x050d
            0x00000036      908988         mov dptr, #0x8988           ; [0x8988:1]=255
            0x00000039      e0             movx a, @dptr
            0x0000003a      fc             mov r4, a
            0x0000003b      a3             inc dptr
            0x0000003c      e0             movx a, @dptr
            0x0000003d      fd             mov r5, a
            0x0000003e      c3             clr c
            0x0000003f      ef             mov a, r7
            0x00000040      9435           subb a, #0x35
            0x00000042      ee             mov a, r6
            0x00000043      9400           subb a, #0x00
        ┌─< 0x00000045      4014           jc 0x005b
        │   0x00000047      9089f7         mov dptr, #0x89f7           ; [0x89f7:1]=255
        │   0x0000004a      e0             movx a, @dptr
        │   0x0000004b      04             inc a
        │   0x0000004c      f0             movx @dptr, a
        │   0x0000004d      90893a         mov dptr, #0x893a           ; [0x893a:1]=255
        │   0x00000050      e0             movx a, @dptr
        │   0x00000051      2f             add a, r7
        │   0x00000052      f0             movx @dptr, a
        │   0x00000053      908939         mov dptr, #0x8939           ; [0x8939:1]=255
       ╎│   0x00000056      e0             movx a, @dptr
       ╎│   0x00000057      3e             addc a, r6
       ╎│   0x00000058      f0             movx @dptr, a
      ┌───< 0x00000059      8005           sjmp 0x0060
      │╎└─> 0x0000005b      e4             clr a
      │╎    0x0000005c      9089f7         mov dptr, #0x89f7           ; [0x89f7:1]=255
      │╎    0x0000005f      f0             movx @dptr, a
      └───> 0x00000060      9089f7         mov dptr, #0x89f7           ; [0x89f7:1]=255
       ╎    0x00000063      e0             movx a, @dptr
       ╎┌─< 0x00000064      b4030a         cjne a, #0x03, 0x0071
       ╎│   0x00000067      908939         mov dptr, #0x8939           ; [0x8939:1]=255
       ╎│   0x0000006a      7401           mov a, #0x01
       ╎│   0x0000006c      f0             movx @dptr, a
       ╎│   0x0000006d      a3             inc dptr
       ╎│   0x0000006e      74f4           mov a, #0xf4
       ╎│   0x00000070      f0             movx @dptr, a
       ╎└─> 0x00000071      7f00           mov r7, #0x00
       ╎    0x00000073      12050d         lcall 0x050d
       ╎    0x00000076      908988         mov dptr, #0x8988           ; [0x8988:1]=255
       ╎    0x00000079      e0             movx a, @dptr
       ╎    0x0000007a      fc             mov r4, a
       ╎    0x0000007b      a3             inc dptr
       ╎    0x0000007c      e0             movx a, @dptr
       ╎    0x0000007d      fd             mov r5, a
       ╎    0x0000007e      c3             clr c
       ╎    0x0000007f      ef             mov a, r7
       ╎    0x00000080      9d             subb a, r5
       ╎    0x00000081      ff             mov r7, a
       ╎    0x00000082      ee             mov a, r6
       ╎    0x00000083      9c             subb a, r4
       ╎    0x00000084      908988         mov dptr, #0x8988           ; [0x8988:1]=255
       ╎    0x00000087      f0             movx @dptr, a
       ╎    0x00000088      a3             inc dptr
       ╎    0x00000089      ef             mov a, r7
       ╎    0x0000008a      f0             movx @dptr, a
       ╎    0x0000008b      908a49         mov dptr, #0x8a49           ; [0x8a49:1]=255
       ╎    0x0000008e      e0             movx a, @dptr
       ╎┌─< 0x0000008f      b42829         cjne a, #0x28, 0x00bb
       ╎│   0x00000092      c3             clr c
       ╎│   0x00000093      908989         mov dptr, #0x8989           ; [0x8989:1]=255
       ╎│   0x00000096      e0             movx a, @dptr
       ╎│   0x00000097      9464           subb a, #0x64
       ╎│   0x00000099      908988         mov dptr, #0x8988           ; [0x8988:1]=255
       ╎│   0x0000009c      e0             movx a, @dptr
       ╎│   0x0000009d      9400           subb a, #0x00
      ┌───< 0x0000009f      401a           jc 0x00bb
      │╎│   0x000000a1      e4             clr a
      │╎│   0x000000a2      7f01           mov r7, #0x01
      │╎│   0x000000a4      fe             mov r6, a
      │╎│   0x000000a5      fd             mov r5, a
      │╎│   0x000000a6      fc             mov r4, a
      │╎│   0x000000a7      78a2           mov r0, #0xa2
      │╎│   0x000000a9      1233b2         lcall 0x33b2
      │╎│   0x000000ac      c3             clr c
      │╎│   0x000000ad      123311         lcall 0x3311
     ┌────< 0x000000b0      7009           jnz 0x00bb
     ││╎│   0x000000b2      908a38         mov dptr, #0x8a38           ; [0x8a38:1]=255
     ││╎│   0x000000b5      e0             movx a, @dptr
     ││╎│   0x000000b6      4401           orl a, #0x01
     ││╎│   0x000000b8      f0             movx @dptr, a
    ┌─────< 0x000000b9      8007           sjmp 0x00c2
    │└└─└─> 0x000000bb      908a38         mov dptr, #0x8a38           ; [0x8a38:1]=255
    │  ╎    0x000000be      e0             movx a, @dptr
    │  ╎    0x000000bf      5402           anl a, #0x02
    │  └──< 0x000000c1      bf3790         cjne r7, #0x37, 0x0054
            0x000000c4      852ee0         mov 0xe0, 0x2e              ; [0x2e:1]=116
            0x000000c7      14             dec a
            0x000000c8      f0             movx @dptr, a
            0x000000c9      e0             movx a, @dptr
        ┌─< 0x000000ca      7003           jnz 0x00cf
       ┌──< 0x000000cc      02bf47         ljmp 0xbf47
       │└─> 0x000000cf      9055c6         mov dptr, #0x55c6           ; [0x55c6:1]=255
       │    0x000000d2      e0             movx a, @dptr
       │    0x000000d3      90855d         mov dptr, #0x855d           ; [0x855d:1]=255
       │    0x000000d6      f0             movx @dptr, a
       │    0x000000d7      e0             movx a, @dptr
       │┌─< 0x000000d8      30e761         jnb 0xe0.7, 0x013c          ; [0xe0:1]=255 ; 224
       ││   0x000000db      7f5e           mov r7, #0x5e               ; '^'
       ││   0x000000dd      1208d9         lcall 0x08d9
       ││   0x000000e0      ff             mov r7, a
       ││   0x000000e1      ff             mov r7, a
       ││   0x000000e2      ff             mov r7, a
       ││   0x000000e3      ff             mov r7, a
       ││   0x000000e4      ff             mov r7, a
       ││   0x000000e5      ff             mov r7, a
       ││   0x000000e6      ff             mov r7, a
       ││   0x000000e7      ff             mov r7, a
       ││   0x000000e8      ff             mov r7, a
       ││   0x000000e9      ff             mov r7, a
       ││   0x000000ea      ff             mov r7, a
       ││   0x000000eb      ff             mov r7, a
       ││   0x000000ec      ff             mov r7, a
       ││   0x000000ed      ff             mov r7, a
       ││   0x000000ee      ff             mov r7, a
       ││   0x000000ef      ff             mov r7, a
       ││   0x000000f0      ff             mov r7, a
       ││   0x000000f1      ff             mov r7, a
       ││   0x000000f2      ff             mov r7, a
       ││   0x000000f3      ff             mov r7, a
       ││   0x000000f4      ff             mov r7, a
       ││   0x000000f5      ff             mov r7, a
       ││   0x000000f6      ff             mov r7, a
       ││   0x000000f7      ff             mov r7, a
       ││   0x000000f8      ff             mov r7, a
       ││   0x000000f9      ff             mov r7, a
       ││   0x000000fa      ff             mov r7, a
       ││   0x000000fb      ff             mov r7, a
       ││   0x000000fc      ff             mov r7, a
       ││   0x000000fd      ff             mov r7, a
       ││   0x000000fe      ff             mov r7, a
       ││   0x000000ff      ff             mov r7, a
       ││   0x00000100      ff             mov r7, a
       ││   0x00000101      ff             mov r7, a
       ││   0x00000102      ff             mov r7, a
       ││   0x00000103      ff             mov r7, a
       ││   0x00000104      ff             mov r7, a
       ││   0x00000105      ff             mov r7, a
       ││   0x00000106      ff             mov r7, a
       ││   0x00000107      ff             mov r7, a
       ││   0x00000108      ff             mov r7, a
       ││   0x00000109      ff             mov r7, a
       ││   0x0000010a      ff             mov r7, a
       ││   0x0000010b      ff             mov r7, a
       ││   0x0000010c      ff             mov r7, a
       ││   0x0000010d      ff             mov r7, a
       ││   0x0000010e      ff             mov r7, a
       ││   0x0000010f      ff             mov r7, a
       ││   0x00000110      ff             mov r7, a
