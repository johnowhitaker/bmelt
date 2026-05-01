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
            0x00000070      12014a         lcall 0x014a
            0x00000073      9085f1         mov dptr, #0x85f1           ; [0x85f1:1]=255
            0x00000076      e0             movx a, @dptr
            0x00000077      fe             mov r6, a
            0x00000078      a3             inc dptr
            0x00000079      e0             movx a, @dptr
            0x0000007a      ff             mov r7, a
            0x0000007b      ee             mov a, r6
            0x0000007c      4f             orl a, r7
            0x0000007d      24ff           add a, #0xff
            0x0000007f      22             ret
            0x00000080      e4             clr a
            0x00000081      908638         mov dptr, #0x8638           ; [0x8638:1]=255
            0x00000084      f0             movx @dptr, a
            0x00000085      a3             inc dptr
            0x00000086      e5a8           mov a, 0xa8                 ; [0xa8:1]=134
            0x00000088      f0             movx @dptr, a
            0x00000089      75a890         mov 0xa8, #0x90             ; [0xa8:1]=134
            0x0000008c      90480e         mov dptr, #0x480e           ; '\x0eH'
                                                                       ; [0x480e:1]=255
            0x0000008f      e0             movx a, @dptr
            0x00000090      5403           anl a, #0x03
        ┌─< 0x00000092      7003           jnz 0x0097
        │   0x00000094      d3             setb c
       ┌──< 0x00000095      8001           sjmp 0x0098
       │└─> 0x00000097      c3             clr c
       └┌─< 0x00000098      4009           jc 0x00a3
        │   0x0000009a      1202bb         lcall 0x02bb
        │   0x0000009d      908638         mov dptr, #0x8638           ; [0x8638:1]=255
        │   0x000000a0      7401           mov a, #0x01
        │   0x000000a2      f0             movx @dptr, a
        └─> 0x000000a3      9055e0         mov dptr, #0x55e0           ; [0x55e0:1]=255
            0x000000a6      e0             movx a, @dptr
            0x000000a7      90862e         mov dptr, #0x862e           ; [0x862e:1]=255
            0x000000aa      f0             movx @dptr, a
            0x000000ab      905969         mov dptr, #0x5969           ; 'iY'
                                                                       ; [0x5969:1]=255
            0x000000ae      e0             movx a, @dptr
            0x000000af      90596a         mov dptr, #0x596a           ; 'jY'
                                                                       ; [0x596a:1]=255
            0x000000b2      c3             clr c
            0x000000b3      9089d1         mov dptr, #0x89d1           ; [0x89d1:1]=255
            0x000000b6      e0             movx a, @dptr
            0x000000b7      94b8           subb a, #0xb8
            0x000000b9      9089d0         mov dptr, #0x89d0           ; [0x89d0:1]=255
            0x000000bc      e0             movx a, @dptr
            0x000000bd      940b           subb a, #0x0b
        ┌─< 0x000000bf      500c           jnc 0x00cd
        │   0x000000c1      a3             inc dptr
        │   0x000000c2      e0             movx a, @dptr
        │   0x000000c3      04             inc a
        │   0x000000c4      f0             movx @dptr, a
       ┌──< 0x000000c5      7006           jnz 0x00cd
       ││   0x000000c7      9089d0         mov dptr, #0x89d0           ; [0x89d0:1]=255
       ││   0x000000ca      e0             movx a, @dptr
       ││   0x000000cb      04             inc a
       ││   0x000000cc      f0             movx @dptr, a
       └└─> 0x000000cd      9089d0         mov dptr, #0x89d0           ; [0x89d0:1]=255
            0x000000d0      e0             movx a, @dptr
        ┌─< 0x000000d1      b40b18         cjne a, #0x0b, 0x00ec
        │   0x000000d4      a3             inc dptr
        │   0x000000d5      e0             movx a, @dptr
       ┌──< 0x000000d6      b4b813         cjne a, #0xb8, 0x00ec
       ││   0x000000d9      9089a2         mov dptr, #0x89a2           ; [0x89a2:1]=255
       ││   0x000000dc      e0             movx a, @dptr
       ││   0x000000dd      c3             clr c
       ││   0x000000de      943c           subb a, #0x3c
      ┌───< 0x000000e0      500a           jnc 0x00ec
      │││   0x000000e2      e0             movx a, @dptr
      │││   0x000000e3      04             inc a
      │││   0x000000e4      f0             movx @dptr, a
