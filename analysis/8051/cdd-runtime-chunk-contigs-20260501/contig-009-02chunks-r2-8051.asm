            0x00000000      subb a, r5
            0x00000001      mov r7, a
            0x00000002      mov a, r6
            0x00000003      subb a, r4
            0x00000004      mov dptr, #0x8988                          ; [0x8988:1]=255
            0x00000007      movx @dptr, a
            0x00000008      inc dptr
            0x00000009      mov a, r7
            0x0000000a      movx @dptr, a
            0x0000000b      mov dptr, #0x8a49                          ; [0x8a49:1]=255
            0x0000000e      movx a, @dptr
        ┌─< 0x0000000f      cjne a, #0x28, 0x003b
        │   0x00000012      clr c
        │   0x00000013      mov dptr, #0x8989                          ; [0x8989:1]=255
        │   0x00000016      movx a, @dptr
        │   0x00000017      subb a, #0x64
        │   0x00000019      mov dptr, #0x8988                          ; [0x8988:1]=255
        │   0x0000001c      movx a, @dptr
        │   0x0000001d      subb a, #0x00
       ┌──< 0x0000001f      jc 0x003b
       ││   0x00000021      clr a
       ││   0x00000022      mov r7, #0x01
       ││   0x00000024      mov r6, a
       ││   0x00000025      mov r5, a
       ││   0x00000026      mov r4, a
       ││   0x00000027      mov r0, #0xa2
       ││   0x00000029      lcall 0x33b2
       ││   0x0000002c      clr c
       ││   0x0000002d      lcall 0x3311
      ┌───< 0x00000030      jnz 0x003b
      │││   0x00000032      mov dptr, #0x8a38                          ; [0x8a38:1]=255
      │││   0x00000035      movx a, @dptr
      │││   0x00000036      orl a, #0x01
      │││   0x00000038      movx @dptr, a
     ┌────< 0x00000039      sjmp 0x0042
     │└└└─> 0x0000003b      mov dptr, #0x8a38                          ; [0x8a38:1]=255
     │      0x0000003e      movx a, @dptr
     │      0x0000003f      anl a, #0x02
     │  ┌─< 0x00000041      cjne r7, #0x37, 0xffd4
        │   0x00000044      mov 0xe0, 0x2e                             ; [0x2e:1]=51
        │   0x00000047      dec a
        │   0x00000048      movx @dptr, a
        │   0x00000049      movx a, @dptr
       ┌──< 0x0000004a      jnz 0x004f
      ┌───< 0x0000004c      ljmp 0xbf47
      │└──> 0x0000004f      mov dptr, #0x55c6                          ; [0x55c6:1]=255
      │ │   0x00000052      movx a, @dptr
      │ │   0x00000053      mov dptr, #0x855d                          ; [0x855d:1]=255
