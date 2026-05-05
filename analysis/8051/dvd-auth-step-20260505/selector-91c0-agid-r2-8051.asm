            0x00000000      e0             movx a, @dptr
            0x00000001      547f           anl a, #0x7f
            0x00000003      f0             movx @dptr, a
            0x00000004      22             ret
            0x00000005      90881f         mov dptr, #0x881f           ; [0x881f:1]=255
            0x00000008      ee             mov a, r6
            0x00000009      f0             movx @dptr, a
            0x0000000a      a3             inc dptr
            0x0000000b      ef             mov a, r7
            0x0000000c      f0             movx @dptr, a
            0x0000000d      78a4           mov r0, #0xa4
            0x0000000f      7c8d           mov r4, #0x8d
            0x00000011      7d01           mov r5, #0x01
        ╎   0x00000013      7b01           mov r3, #0x01
        ╎   0x00000015      7a88           mov r2, #0x88
        ╎   0x00000017      791f           mov r1, #0x1f
        ╎   0x00000019      7e00           mov r6, #0x00
        ╎   0x0000001b      7f02           mov r7, #0x02
        ╎   0x0000001d      122f56         lcall 0x2f56
        ╎   0x00000020      7b01           mov r3, #0x01
        ╎   0x00000022      7a8d           mov r2, #0x8d
        ╎   0x00000024      79a4           mov r1, #0xa4
        ╎   0x00000026      22             ret
        ╎   0x00000027      d3             setb c
       ┌──< 0x00000028      10af01         jbc 0xa8.7, 0x002c          ; [0xa8:1]=144
       │╎   0x0000002b      c3             clr c
       └──> 0x0000002c      c0d0           push 0xd0                   ; [0xd0:1]=2
        ╎   0x0000002e      904737         mov dptr, #0x4737           ; '7G'
        ╎                                                              ; [0x4737:1]=255
        ╎   0x00000031      e0             movx a, @dptr
        ╎   0x00000032      540f           anl a, #0x0f
        ╎   0x00000034      f54e           mov 0x4e, a                 ; [0x4e:1]=211
        ╎   0x00000036      a3             inc dptr
        ╎   0x00000037      e0             movx a, @dptr
        ╎   0x00000038      f54f           mov 0x4f, a                 ; [0x4f:1]=34
        ╎   0x0000003a      ae4e           mov r6, 0x4e                ; [0x4e:1]=211
        ╎   0x0000003c      12c810         lcall 0xc810
        ╎   0x0000003f      8ee0           mov 0xe0, r6                ; [0xe0:1]=125
        ╎   0x00000041      5410           anl a, #0x10
        ╎   0x00000043      c4             swap a
        ╎   0x00000044      540f           anl a, #0x0f
        ╎   0x00000046      ff             mov r7, a
        ╎   0x00000047      22             ret
        ╎   0x00000048      121527         lcall 0x1527
       ┌──< 0x0000004b      202a02         jb 0x25.2, 0x0050           ; [0x25:1]=164
       │╎   0x0000004e      d3             setb c
       │╎   0x0000004f      22             ret
       └──> 0x00000050      c3             clr c
        ╎   0x00000051      22             ret
        ╎   0x00000052      121527         lcall 0x1527
       ┌──< 0x00000055      202a02         jb 0x25.2, 0x005a           ; [0x25:1]=164
       │╎   0x00000058      c3             clr c
       │╎   0x00000059      22             ret
       └──> 0x0000005a      d3             setb c
        ╎   0x0000005b      22             ret
        ╎   0x0000005c      7f0c           mov r7, #0x0c
        ╎   0x0000005e      12f33a         lcall 0xf33a
        ╎   0x00000061      ef             mov a, r7
        ╎   0x00000062      54f0           anl a, #0xf0
        ╎   0x00000064      ff             mov r7, a
        ╎   0x00000065      22             ret
        ╎   0x00000066      7f0e           mov r7, #0x0e
        ╎   0x00000068      12f33a         lcall 0xf33a
        ╎   0x0000006b      ef             mov a, r7
        ╎   0x0000006c      54c0           anl a, #0xc0
        ╎   0x0000006e      ff             mov r7, a
        ╎   0x0000006f      22             ret
        ╎   0x00000070      9055fd         mov dptr, #0x55fd           ; [0x55fd:1]=255
        ╎   0x00000073      740b           mov a, #0x0b
        ╎   0x00000075      f0             movx @dptr, a
       ┌──< 0x00000076      02eee4         ljmp 0xeee4
       │╎   0x00000079      904000         mov dptr, #0x4000           ; [0x4000:1]=255
       │╎   0x0000007c      e4             clr a
       │╎   0x0000007d      93             movc a, @a+dptr
       │╎   0x0000007e      f544           mov 0x44, a                 ; [0x44:1]=84
       │╎   0x00000080      14             dec a
      ┌───< 0x00000081      4002           jc 0x0085
      ││╎   0x00000083      7d14           mov r5, #0x14
      └───> 0x00000085      ed             mov a, r5
       │╎   0x00000086      d3             setb c
       │╎   0x00000087      940a           subb a, #0x0a
       │╎   0x00000089      905800         mov dptr, #0x5800           ; [0x5800:1]=255
       │╎   0x0000008c      e0             movx a, @dptr
       │╎   0x0000008d      54f1           anl a, #0xf1
       │╎   0x0000008f      4404           orl a, #0x04
       │╎   0x00000091      f0             movx @dptr, a
       │╎   0x00000092      7e10           mov r6, #0x10
      ┌───< 0x00000094      306f10         jnb 0x2d.7, 0x00a7          ; [0x2d:1]=208
      ││╎   0x00000097      ed             mov a, r5
      ││╎   0x00000098      d3             setb c
      ││╎   0x00000099      9401           subb a, #0x01
     ┌────< 0x0000009b      500a           jnc 0x00a7
     │││╎   0x0000009d      905950         mov dptr, #0x5950           ; 'PY'
     │││╎                                                              ; [0x5950:1]=255
     │││╎   0x000000a0      e0             movx a, @dptr
     │││╎   0x000000a1      54f8           anl a, #0xf8
     │││╎   0x000000a3      4402           orl a, #0x02
    ┌─────< 0x000000a5      800f           sjmp 0x00b6
    │└└───> 0x000000a7      ed             mov a, r5
    │  │╎   0x000000a8      904a05         mov dptr, #0x4a05           ; [0x4a05:1]=255
    │  │╎   0x000000ab      93             movc a, @a+dptr
    │  │╎   0x000000ac      ff             mov r7, a
    │  │╎   0x000000ad      905950         mov dptr, #0x5950           ; 'PY'
    │  │╎                                                              ; [0x5950:1]=255
    │  │╎   0x000000b0      e0             movx a, @dptr
    │  │╎   0x000000b1      54f8           anl a, #0xf8
    │  │╎   0x000000b3      fd             mov r5, a
    │  │╎   0x000000b4      ef             mov a, r7
    │  │╎   0x000000b5      4d             orl a, r5
    └─────> 0x000000b6      f0             movx @dptr, a
       │╎   0x000000b7      e0             movx a, @dptr
       │╎   0x000000b8      54cf           anl a, #0xcf
       │╎   0x000000ba      4e             orl a, r6
       │╎   0x000000bb      f0             movx @dptr, a
       │╎   0x000000bc      22             ret
       │╎   0x000000bd      ef             mov a, r7
       │╎   0x000000be      d3             setb c
       │╎   0x000000bf      9456           subb a, #0x56
       │╎   0x000000c1      7872           mov r0, #0x72               ; 'r'
       │╎   0x000000c3      7c00           mov r4, #0x00
       │╎   0x000000c5      7d00           mov r5, #0x00
       │╎   0x000000c7      7b01           mov r3, #0x01
       │╎   0x000000c9      7a86           mov r2, #0x86
       │╎   0x000000cb      7977           mov r1, #0x77               ; 'w'
       │╎   0x000000cd      7e00           mov r6, #0x00
       │╎   0x000000cf      7f02           mov r7, #0x02
       │╎   0x000000d1      122f56         lcall 0x2f56
       │╎   0x000000d4      757401         mov 0x74, #0x01             ; [0x74:1]=11
       │╎   0x000000d7      7ffb           mov r7, #0xfb
       │╎   0x000000d9      120eb5         lcall 0x0eb5
       │╎   0x000000dc      7877           mov r0, #0x77               ; 'w'
       │╎   0x000000de      7c86           mov r4, #0x86
       │╎   0x000000e0      7d01           mov r5, #0x01
       │╎   0x000000e2      7e00           mov r6, #0x00
       │╎   0x000000e4      7f02           mov r7, #0x02
       │╎   0x000000e6      122f56         lcall 0x2f56
       │╎   0x000000e9      7b01           mov r3, #0x01
       │╎   0x000000eb      7a86           mov r2, #0x86
       │╎   0x000000ed      7977           mov r1, #0x77               ; 'w'
       │╎   0x000000ef      120bbb         lcall 0x0bbb
       │╎   0x000000f2      9057e4         mov dptr, #0x57e4           ; [0x57e4:1]=255
       │╎   0x000000f5      747f           mov a, #0x7f                ; '\x7f'
       │╎   0x000000f7      f0             movx @dptr, a
       │╎   0x000000f8      905788         mov dptr, #0x5788           ; [0x5788:1]=255
       │╎   0x000000fb      7452           mov a, #0x52                ; 'R'
       │╎   0x000000fd      f0             movx @dptr, a
       │╎   0x000000fe      90577e         mov dptr, #0x577e           ; '~W'
       │╎                                                              ; [0x577e:1]=255
       │└─< 0x00000101      0112           ajmp 0x0012
       │    0x00000103      f7             mov @r1, a
       │    0x00000104      8a80           mov 0x80, r2                ; [0x80:1]=20
       │    0x00000106      18             dec r0
       │    0x00000107      e56f           mov a, 0x6f                 ; [0x6f:1]=34
       │┌─< 0x00000109      b40313         cjne a, #0x03, 0x011f
       ││   0x0000010c      78b2           mov r0, #0xb2
       ││   0x0000010e      7605           mov @r0, #0x05
       ││   0x00000110      08             inc r0
       ││   0x00000111      76dc           mov @r0, #0xdc
       ││   0x00000113      908a23         mov dptr, #0x8a23           ; [0x8a23:1]=255
       ││   0x00000116      e0             movx a, @dptr
       ││   0x00000117      4440           orl a, #0x40
       ││   0x00000119      f0             movx @dptr, a
       ││   0x0000011a      e4             clr a
       ││   0x0000011b      9089f7         mov dptr, #0x89f7           ; [0x89f7:1]=255
       ││   0x0000011e      f0             movx @dptr, a
       │└─> 0x0000011f      e56f           mov a, 0x6f                 ; [0x6f:1]=34
       │    0x00000121      6402           xrl a, #0x02
       │┌─< 0x00000123      701f           jnz 0x0144
       ││   0x00000125      78a1           mov r0, #0xa1
       ││   0x00000127      e6             mov a, @r0
      ┌───< 0x00000128      601a           jz 0x0144
      │││   0x0000012a      908133         mov dptr, #0x8133           ; [0x8133:1]=255
      │││   0x0000012d      e0             movx a, @dptr
      │││   0x0000012e      c3             clr c
      │││   0x0000012f      13             rrc a
     ┌────< 0x00000130      20e011         jb 0xe0.0, 0x0144           ; [0xe0:1]=125
    ┌─────< 0x00000133      301c02         jnb 0x23.4, 0x0138          ; [0x23:1]=141
   ┌──────< 0x00000136      8003           sjmp 0x013b
  ┌─└─────> 0x00000138      301f04         jnb 0x23.7, 0x013f          ; [0x23:1]=141
  │└──────> 0x0000013b      7f02           mov r7, #0x02
  │ ┌─────< 0x0000013d      8002           sjmp 0x0141
  └───────> 0x0000013f      7f71           mov r7, #0x71               ; 'q'
    └─────> 0x00000141      905a01         mov dptr, #0x5a01           ; [0x5a01:1]=255
     └└─└─> 0x00000144      e0             movx a, @dptr
       │    0x00000145      4405           orl a, #0x05
       │    0x00000147      f0             movx @dptr, a
       │    0x00000148      905905         mov dptr, #0x5905           ; [0x5905:1]=255
       │    0x0000014b      e0             movx a, @dptr
       │    0x0000014c      4401           orl a, #0x01
       │    0x0000014e      f0             movx @dptr, a
       │    0x0000014f      e0             movx a, @dptr
       │    0x00000150      4404           orl a, #0x04
       │    0x00000152      f0             movx @dptr, a
       │    0x00000153      904820         mov dptr, #0x4820           ; ' H'
       │                                                               ; [0x4820:1]=255
       │    0x00000156      7404           mov a, #0x04
       │    0x00000158      f0             movx @dptr, a
       │    0x00000159      d0d0           pop 0xd0                    ; [0xd0:1]=2
       │    0x0000015b      92af           mov 0xa8.7, c               ; [0xa8:1]=144
       │    0x0000015d      22             ret
       │    0x0000015e      d3             setb c
       │┌─< 0x0000015f      10af01         jbc 0xa8.7, 0x0163          ; [0xa8:1]=144
       ││   0x00000162      c3             clr c
       │└─> 0x00000163      c0d0           push 0xd0                   ; [0xd0:1]=2
       │    0x00000165      908aed         mov dptr, #0x8aed           ; [0x8aed:1]=255
       │    0x00000168      e0             movx a, @dptr
       │┌─< 0x00000169      30e265         jnb 0xe0.2, 0x01d1          ; [0xe0:1]=125
       ││   0x0000016c      908a33         mov dptr, #0x8a33           ; [0x8a33:1]=255
       ││   0x0000016f      e0             movx a, @dptr
       ││   0x00000170      6401           xrl a, #0x01
      ┌───< 0x00000172      705d           jnz 0x01d1
     ┌────< 0x00000174      203e5a         jb 0x27.6, 0x01d1           ; [0x27:1]=211
    ┌─────< 0x00000177      204f57         jb 0x29.7, 0x01d1           ; [0x29:1]=175
   ┌──────< 0x0000017a      203f54         jb 0x27.7, 0x01d1           ; [0x27:1]=211
   ││││││   0x0000017d      9089ff         mov dptr, #0x89ff           ; [0x89ff:1]=255
   ││││││   0x00000180      0a             inc r2
   ││││││   0x00000181      12ca84         lcall 0xca84
   ││││││   0x00000184      9089dc         mov dptr, #0x89dc           ; [0x89dc:1]=255
   ││││││   0x00000187      743c           mov a, #0x3c                ; '<'
   ││││││   0x00000189      f0             movx @dptr, a
   ││││││   0x0000018a      9089fc         mov dptr, #0x89fc           ; [0x89fc:1]=255
   ││││││   0x0000018d      74fa           mov a, #0xfa
   ││││││   0x0000018f      f0             movx @dptr, a
   ││││││   0x00000190      e4             clr a
   ││││││   0x00000191      ff             mov r7, a
   ││││││   0x00000192      fe             mov r6, a
   ││││││   0x00000193      12f78a         lcall 0xf78a
   ││││││   0x00000196      908a17         mov dptr, #0x8a17           ; [0x8a17:1]=255
   ││││││   0x00000199      7401           mov a, #0x01
   ││││││   0x0000019b      f0             movx @dptr, a
   ││││││   0x0000019c      7d01           mov r5, #0x01
   ││││││   0x0000019e      7f04           mov r7, #0x04
   ││││││   0x000001a0      12f0e5         lcall 0xf0e5
   ││││││   0x000001a3      908a1a         mov dptr, #0x8a1a           ; [0x8a1a:1]=255
   ││││││   0x000001a6      7401           mov a, #0x01
   ││││││   0x000001a8      f0             movx @dptr, a
   ││││││   0x000001a9      908adf         mov dptr, #0x8adf           ; [0x8adf:1]=255
   ││││││   0x000001ac      e0             movx a, @dptr
   ││││││   0x000001ad      54f0           anl a, #0xf0
   ││││││   0x000001af      f0             movx @dptr, a
   ││││││   0x000001b0      456f           orl a, 0x6f                 ; [0x6f:1]=34
   ││││││   0x000001b2      f0             movx @dptr, a
   ││││││   0x000001b3      e56f           mov a, 0x6f                 ; [0x6f:1]=34
   ││││││   0x000001b5      c3             clr c
   ││││││   0x000001b6      9403           subb a, #0x03
  ┌───────< 0x000001b8      5007           jnc 0x01c1
  │││││││   0x000001ba      908a23         mov dptr, #0x8a23           ; [0x8a23:1]=255
  │││││││   0x000001bd      e0             movx a, @dptr
  │││││││   0x000001be      54bf           anl a, #0xbf
  │││││││   0x000001c0      f57c           mov 0x7c, a                 ; [0x7c:1]=228
   ││││││   0x000001c2      f8             mov r0, a
   ││││││   0x000001c3      123424         lcall 0x3424
   ││││││   0x000001c6      78a2           mov r0, #0xa2
   ││││││   0x000001c8      123396         lcall 0x3396
   ││││││   0x000001cb      120519         lcall 0x0519
   ││││││   0x000001ce      9088ea         mov dptr, #0x88ea           ; [0x88ea:1]=255
   └└└└─└─> 0x000001d1      e0             movx a, @dptr
       │    0x000001d2      c3             clr c
       │    0x000001d3      94ff           subb a, #0xff
       │┌─< 0x000001d5      5003           jnc 0x01da
       ││   0x000001d7      e0             movx a, @dptr
       ││   0x000001d8      04             inc a
       ││   0x000001d9      f0             movx @dptr, a
       │└─> 0x000001da      7f01           mov r7, #0x01
       │┌─< 0x000001dc      8002           sjmp 0x01e0
       ││   0x000001de      7f00           mov r7, #0x00
       │└─> 0x000001e0      e57c           mov a, 0x7c                 ; [0x7c:1]=228
       │    0x000001e2      2407           add a, #0x07
       │    0x000001e4      f57c           mov 0x7c, a                 ; [0x7c:1]=228
       │    0x000001e6      d0d0           pop 0xd0                    ; [0xd0:1]=2
       │    0x000001e8      92af           mov 0xa8.7, c               ; [0xa8:1]=144
       │    0x000001ea      22             ret
       │    0x000001eb      c253           clr 0x2a.3                  ; [0x2a:1]=1
       │    0x000001ed      908a38         mov dptr, #0x8a38           ; [0x8a38:1]=255
       │    0x000001f0      e0             movx a, @dptr
       │    0x000001f1      54ef           anl a, #0xef
       │    0x000001f3      f0             movx @dptr, a
       │    0x000001f4      120507         lcall 0x0507
       │┌─< 0x000001f7      303e2a         jnb 0x27.6, 0x0224          ; [0x27:1]=211
       ││   0x000001fa      120345         lcall 0x0345
       ││   0x000001fd      c24f           clr 0x29.7                  ; [0x29:1]=175
       ││   0x000001ff      90             truncated
