            0x00000000      mov a, #0x03
            0x00000002      movx @dptr, a
            0x00000003      inc dptr
            0x00000004      mov a, #0x10
        ┌─< 0x00000006      sjmp 0x003c
        │   0x00000008      mov dptr, #0x8a52                          ; [0x8a52:1]=255
        │   0x0000000b      mov a, #0x03
        │   0x0000000d      movx @dptr, a
        │   0x0000000e      inc dptr
        │   0x0000000f      mov a, #0x1c
        │   0x00000011      movx @dptr, a
        │   0x00000012      mov dptr, #0x8a4d                          ; [0x8a4d:1]=255
        │   0x00000015      clr a
        │   0x00000016      movx @dptr, a
        │   0x00000017      inc dptr
        │   0x00000018      mov a, #0x10
        │   0x0000001a      movx @dptr, a
       ┌──< 0x0000001b      sjmp 0x008f
       ││   0x0000001d      mov dptr, #0x8a52                          ; [0x8a52:1]=255
       ││   0x00000020      mov a, #0x03
       ││   0x00000022      movx @dptr, a
       ││   0x00000023      inc dptr
       ││   0x00000024      mov a, #0x24                               ; '$'
      ┌───< 0x00000026      sjmp 0x0066
      │││   0x00000028      mov dptr, #0x8a52                          ; [0x8a52:1]=255
      │││   0x0000002b      mov a, #0x03
      │││   0x0000002d      movx @dptr, a
      │││   0x0000002e      inc dptr
      │││   0x0000002f      mov a, #0x50                               ; 'P'
     ┌────< 0x00000031      sjmp 0x003c
     ││││   0x00000033      mov dptr, #0x8a52                          ; [0x8a52:1]=255
     ││││   0x00000036      mov a, #0x03
     ││││   0x00000038      movx @dptr, a
     ││││   0x00000039      inc dptr
     ││││   0x0000003a      mov a, #0x5c                               ; '\\'
     └──└─> 0x0000003c      movx @dptr, a
      ││    0x0000003d      mov dptr, #0x8a4d                          ; [0x8a4d:1]=255
      ││┌─< 0x00000040      jnz 0x0052
     ┌────< 0x00000042      jb 0x27.0, 0x0052                          ; [0x27:1]=62
    ┌─────< 0x00000045      jb 0x27.1, 0x005a                          ; [0x27:1]=62
    │││││   0x00000048      mov a, 0x24                                ; [0x24:1]=116
   ┌──────< 0x0000004a      jnz 0x0050
   ││││││   0x0000004c      mov a, 0x23                                ; [0x23:1]=163
   ││││││   0x0000004e      xrl a, #0xc0
  ┌└──────> 0x00000050      jnz 0x005a
  │ │└──└─> 0x00000052      mov dptr, #0x47b1                          ; [0x47b1:1]=255
  │ │ ││    0x00000055      mov a, #0x02
  │ │ ││    0x00000057      movx @dptr, a
