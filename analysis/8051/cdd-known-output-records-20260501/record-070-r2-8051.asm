            0x00000000      12f2a0         lcall 0xf2a0
            0x00000003      22             ret
            0x00000004      908844         mov dptr, #0x8844           ; [0x8844:1]=255
            0x00000007      ef             mov a, r7
            0x00000008      f0             movx @dptr, a
            0x00000009      90825b         mov dptr, #0x825b           ; [0x825b:1]=255
            0x0000000c      e0             movx a, @dptr
        ┌─< 0x0000000d      30e627         jnb 0xe0.6, 0x0037          ; [0xe0:1]=65
        │   0x00000010      908844         mov dptr, #0x8844           ; [0x8844:1]=255
        │   0x00000013      e0             movx a, @dptr
       ┌──< 0x00000014      b4010c         cjne a, #0x01, 0x0023
       ││   0x00000017      7f0b           mov r7, #0x0b
       ││   0x00000019      12f33a         lcall 0xf33a
       ││   0x0000001c      ef             mov a, r7
       ││   0x0000001d      543e           anl a, #0x3e
       ││   0x0000001f      4441           orl a, #0x41
      ┌───< 0x00000021      800e           sjmp 0x0031
      │└──> 0x00000023      908844         mov dptr, #0x8844           ; [0x8844:1]=255
      │ │   0x00000026      e0             movx a, @dptr
      │┌──< 0x00000027      700e           jnz 0x0037
      │││   0x00000029      7f0b           mov r7, #0x0b
      │││   0x0000002b      12f33a         lcall 0xf33a
      │││   0x0000002e      ef             mov a, r7
      │││   0x0000002f      54fe           anl a, #0xfe
      └───> 0x00000031      fd             mov r5, a
       ││   0x00000032      7f0b           mov r7, #0x0b
       ││   0x00000034      12f2a0         lcall 0xf2a0
       └└─> 0x00000037      22             ret
            0x00000038      905905         mov dptr, #0x5905           ; [0x5905:1]=255
            0x0000003b      e0             movx a, @dptr
        ┌─< 0x0000003c      30e517         jnb 0xe0.5, 0x0056          ; [0xe0:1]=65
        │   0x0000003f      e0             movx a, @dptr
        │   0x00000040      12f2a0         lcall 0xf2a0
        │   0x00000043      22             ret
        │   0x00000044      908844         mov dptr, #0x8844           ; [0x8844:1]=255
        │   0x00000047      ef             mov a, r7
        │   0x00000048      f0             movx @dptr, a
        │   0x00000049      90825b         mov dptr, #0x825b           ; [0x825b:1]=255
        │   0x0000004c      e0             movx a, @dptr
       ┌──< 0x0000004d      30e627         jnb 0xe0.6, 0x0077          ; [0xe0:1]=65
       ││   0x00000050      908844         mov dptr, #0x8844           ; [0x8844:1]=255
       ││   0x00000053      e0             movx a, @dptr
      ┌───< 0x00000054      b4010c         cjne a, #0x01, 0x0063
      ││    0x00000057      7f0b           mov r7, #0x0b
      ││    0x00000059      12f33a         lcall 0xf33a
      ││    0x0000005c      ef             mov a, r7
      ││    0x0000005d      543e           anl a, #0x3e
      ││    0x0000005f      4441           orl a, #0x41
      ││┌─< 0x00000061      800e           sjmp 0x0071
      └───> 0x00000063      908844         mov dptr, #0x8844           ; [0x8844:1]=255
       ││   0x00000066      e0             movx a, @dptr
      ┌───< 0x00000067      700e           jnz 0x0077
      │││   0x00000069      7f0b           mov r7, #0x0b
      │││   0x0000006b      12f33a         lcall 0xf33a
      │││   0x0000006e      ef             mov a, r7
      │││   0x0000006f      54fe           anl a, #0xfe
      ││└─> 0x00000071      fd             mov r5, a
      ││    0x00000072      7f0b           mov r7, #0x0b
      ││    0x00000074      12f2a0         lcall 0xf2a0
      └└──> 0x00000077      22             ret
            0x00000078      905905         mov dptr, #0x5905           ; [0x5905:1]=255
            0x0000007b      e0             movx a, @dptr
        ┌─< 0x0000007c      30e517         jnb 0xe0.5, 0x0096          ; [0xe0:1]=65
        │   0x0000007f      e0             movx a, @dptr
        │   0x00000080      e0             movx a, @dptr
        │   0x00000081      904091         mov dptr, #0x4091           ; [0x4091:1]=255
        │   0x00000084      f0             movx @dptr, a
        │   0x00000085      a3             inc dptr
        │   0x00000086      e55e           mov a, 0x5e                 ; [0x5e:1]=62
        │   0x00000088      f0             movx @dptr, a
        │   0x00000089      a3             inc dptr
        │   0x0000008a      e55f           mov a, 0x5f                 ; [0x5f:1]=68
        │   0x0000008c      f0             movx @dptr, a
       ┌──> 0x0000008d      904000         mov dptr, #0x4000           ; [0x4000:1]=255
       ╎│   0x00000090      e0             movx a, @dptr
       └──< 0x00000091      20e7f9         jb 0xe0.7, 0x008d           ; [0xe0:1]=65
        │   0x00000094      904098         mov dptr, #0x4098           ; [0x4098:1]=255
            0x00000097      e0             movx a, @dptr
        ┌─> 0x00000098      904000         mov dptr, #0x4000           ; [0x4000:1]=255
        ╎   0x0000009b      e0             movx a, @dptr
        └─< 0x0000009c      20e7f9         jb 0xe0.7, 0x0098           ; [0xe0:1]=65
            0x0000009f      904098         mov dptr, #0x4098           ; [0x4098:1]=255
            0x000000a2      e0             movx a, @dptr
            0x000000a3      f55f           mov 0x5f, a                 ; [0x5f:1]=68
        ┌─> 0x000000a5      904000         mov dptr, #0x4000           ; [0x4000:1]=255
        ╎   0x000000a8      e0             movx a, @dptr
        └─< 0x000000a9      20e7f9         jb 0xe0.7, 0x00a5           ; [0xe0:1]=65
            0x000000ac      904098         mov dptr, #0x4098           ; [0x4098:1]=255
            0x000000af      e55f           mov a, 0x5f                 ; [0x5f:1]=68
            0x000000b1      f0             movx @dptr, a
        ┌─> 0x000000b2      904000         mov dptr, #0x4000           ; [0x4000:1]=255
        ╎   0x000000b5      e0             movx a, @dptr
        └─< 0x000000b6      20e7f9         jb 0xe0.7, 0x00b2           ; [0xe0:1]=65
            0x000000b9      d0d0           pop 0xd0                    ; [0xd0:1]=144
            0x000000bb      92af           mov 0xa8.7, c               ; [0xa8:1]=224
            0x000000bd      22             ret
            0x000000be      c24f           clr 0x29.7                  ; [0x29:1]=127
            0x000000c0      12f2a0         lcall 0xf2a0
            0x000000c3      22             ret
            0x000000c4      908844         mov dptr, #0x8844           ; [0x8844:1]=255
            0x000000c7      ef             mov a, r7
            0x000000c8      f0             movx @dptr, a
            0x000000c9      90825b         mov dptr, #0x825b           ; [0x825b:1]=255
            0x000000cc      e0             movx a, @dptr
        ┌─< 0x000000cd      30e627         jnb 0xe0.6, 0x00f7          ; [0xe0:1]=65
        │   0x000000d0      908844         mov dptr, #0x8844           ; [0x8844:1]=255
        │   0x000000d3      e0             movx a, @dptr
       ┌──< 0x000000d4      b4010c         cjne a, #0x01, 0x00e3
       ││   0x000000d7      7f0b           mov r7, #0x0b
       ││   0x000000d9      12f33a         lcall 0xf33a
       ││   0x000000dc      ef             mov a, r7
       ││   0x000000dd      543e           anl a, #0x3e
       ││   0x000000df      4441           orl a, #0x41
      ┌───< 0x000000e1      800e           sjmp 0x00f1
      │└──> 0x000000e3      908844         mov dptr, #0x8844           ; [0x8844:1]=255
      │ │   0x000000e6      e0             movx a, @dptr
      │┌──< 0x000000e7      700e           jnz 0x00f7
      │││   0x000000e9      7f0b           mov r7, #0x0b
      │││   0x000000eb      12f33a         lcall 0xf33a
      │││   0x000000ee      ef             mov a, r7
      │││   0x000000ef      54fe           anl a, #0xfe
      └───> 0x000000f1      fd             mov r5, a
       ││   0x000000f2      7f0b           mov r7, #0x0b
       ││   0x000000f4      12f2a0         lcall 0xf2a0
       └└─> 0x000000f7      22             ret
            0x000000f8      905905         mov dptr, #0x5905           ; [0x5905:1]=255
            0x000000fb      e0             movx a, @dptr
        ┌─< 0x000000fc      30e517         jnb 0xe0.5, 0x0116          ; [0xe0:1]=65
        │   0x000000ff      e0             movx a, @dptr
        │   0x00000100      908633         mov dptr, #0x8633           ; [0x8633:1]=255
        │   0x00000103      e0             movx a, @dptr
        │   0x00000104      905906         mov dptr, #0x5906           ; [0x5906:1]=255
        │   0x00000107      f0             movx @dptr, a
        │   0x00000108      90862f         mov dptr, #0x862f           ; [0x862f:1]=255
        │   0x0000010b      e0             movx a, @dptr
        │   0x0000010c      90590d         mov dptr, #0x590d           ; '\rY'
        │                                                              ; [0x590d:1]=255
        │   0x0000010f      f0             movx @dptr, a
        │   0x00000110      908631         mov dptr, #0x8631           ; [0x8631:1]=255
        │   0x00000113      e0             movx a, @dptr
        │   0x00000114      904840         mov dptr, #0x4840           ; '@H'
        │                                                              ; [0x4840:1]=255
            0x00000117      f0             movx @dptr, a
            0x00000118      908630         mov dptr, #0x8630           ; [0x8630:1]=255
            0x0000011b      e0             movx a, @dptr
            0x0000011c      904863         mov dptr, #0x4863           ; 'cH'
                                                                       ; [0x4863:1]=255
            0x0000011f      f0             movx @dptr, a
            0x00000120      908638         mov dptr, #0x8638           ; [0x8638:1]=255
            0x00000123      e0             movx a, @dptr
            0x00000124      6005           jz 0x012b
            0x00000126      7f03           mov r7, #0x03
            0x00000128      1227b7         lcall 0x27b7
            0x0000012b      908639         mov dptr, #0x8639           ; [0x8639:1]=255
            0x0000012e      e0             movx a, @dptr
            0x0000012f      f5a8           mov 0xa8, a                 ; [0xa8:1]=224
            0x00000131      908636         mov dptr, #0x8636           ; [0x8636:1]=255
            0x00000134      e0             movx a, @dptr
            0x00000135      fe             mov r6, a
            0x00000136      a3             inc dptr
            0x00000137      e0             movx a, @dptr
            0x00000138      7806           mov r0, #0x06
            0x0000013a      ce             xch a, r6
            0x0000013b      c3             clr c
            0x0000013c      13             rrc a
            0x0000013d      ce             xch a, r6
            0x0000013e      13             rrc a
            0x0000013f      d8c2           djnz r0, 0x0103
            0x00000141      51c2           acall 0x02c2
            0x00000143      49             orl a, r1
            0x00000144      908a37         mov dptr, #0x8a37           ; [0x8a37:1]=255
            0x00000147      e0             movx a, @dptr
            0x00000148      54f7           anl a, #0xf7
            0x0000014a      f0             movx @dptr, a
            0x0000014b      d23e           setb 0x27.6                 ; [0x27:1]=112
            0x0000014d      904834         mov dptr, #0x4834           ; '4H'
                                                                       ; [0x4834:1]=255
            0x00000150      74bf           mov a, #0xbf
            0x00000152      f0             movx @dptr, a
            0x00000153      e4             clr a
            0x00000154      908a18         mov dptr, #0x8a18           ; [0x8a18:1]=255
            0x00000157      f0             movx @dptr, a
            0x00000158      a3             inc dptr
            0x00000159      f0             movx @dptr, a
