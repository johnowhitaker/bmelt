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
            0x00000020      e0             movx a, @dptr
            0x00000021      5488           anl a, #0x88
            0x00000023      4e             orl a, r6
            0x00000024      fe             mov r6, a
            0x00000025      ef             mov a, r7
            0x00000026      4e             orl a, r6
            0x00000027      f0             movx @dptr, a
            0x00000028      7e00           mov r6, #0x00
            0x0000002a      7f08           mov r7, #0x08
            0x0000002c      120a65         lcall 0x0a65
            0x0000002f      e4             clr a
            0x00000030      90885d         mov dptr, #0x885d           ; [0x885d:1]=255
            0x00000033      f0             movx @dptr, a
            0x00000034      908811         mov dptr, #0x8811           ; [0x8811:1]=255
            0x00000037      e0             movx a, @dptr
            0x00000038      90885e         mov dptr, #0x885e           ; [0x885e:1]=255
            0x0000003b      f0             movx @dptr, a
            0x0000003c      908812         mov dptr, #0x8812           ; [0x8812:1]=255
            0x0000003f      e0             movx a, @dptr
            0x00000040      90885f         mov dptr, #0x885f           ; [0x885f:1]=255
            0x00000043      f0             movx @dptr, a
            0x00000044      908814         mov dptr, #0x8814           ; [0x8814:1]=255
            0x00000047      e0             movx a, @dptr
            0x00000048      908860         mov dptr, #0x8860           ; [0x8860:1]=255
            0x0000004b      f0             movx @dptr, a
            0x0000004c      7b02           mov r3, #0x02
            0x0000004e      7daa           mov r5, #0xaa
            0x00000050      7f00           mov r7, #0x00
            0x00000052      7e04           mov r6, #0x04
            0x00000054      120a6b         lcall 0x0a6b
            0x00000057      22             ret
            0x00000058      90898e         mov dptr, #0x898e           ; [0x898e:1]=255
            0x0000005b      e0             movx a, @dptr
            0x0000005c      4401           orl a, #0x01
            0x0000005e      f0             movx @dptr, a
            0x0000005f      908a23         mov dptr, #0x8a23           ; [0x8a23:1]=255
            0x00000062      e0             movx a, @dptr
            0x00000063      54bf           anl a, #0xbf
            0x00000065      f0             movx @dptr, a
            0x00000066      908adf         mov dptr, #0x8adf           ; [0x8adf:1]=255
            0x00000069      e0             movx a, @dptr
            0x0000006a      540f           anl a, #0x0f
            0x0000006c      6403           xrl a, #0x03
        ┌─< 0x0000006e      6003           jz 0x0073
       ┌──< 0x00000070      02b59c         ljmp 0xb59c
       │└─> 0x00000073      904762         mov dptr, #0x4762           ; 'bG'
       │                                                               ; [0x4762:1]=255
       │    0x00000076      e0             movx a, @dptr
       │    0x00000077      54ef           anl a, #0xef
       │    0x00000079      f0             movx @dptr, a
       │    0x0000007a      908a17         mov dptr, #0x8a17           ; [0x8a17:1]=255
       │    0x0000007d      e0             movx a, @dptr
       │┌─< 0x0000007e      6015           jz 0x0095
       ││   0x00000080      e4             clr a
       ││   0x00000081      908a13         mov dptr, #0x8a13           ; [0x8a13:1]=255
       ││   0x00000084      f0             movx @dptr, a
       ││   0x00000085      a3             inc dptr
       ││   0x00000086      f0             movx @dptr, a
       ││   0x00000087      9089a2         mov dptr, #0x89a2           ; [0x89a2:1]=255
       ││   0x0000008a      f0             movx @dptr, a
       ││   0x0000008b      9089d0         mov dptr, #0x89d0           ; [0x89d0:1]=255
       ││   0x0000008e      f0             movx @dptr, a
       ││   0x0000008f      a3             inc dptr
       ││   0x00000090      f0             movx @dptr, a
       ││   0x00000091      908a17         mov dptr, #0x8a17           ; [0x8a17:1]=255
       ││   0x00000094      f0             movx @dptr, a
       │└─> 0x00000095      d2a8           setb 0xa8.0                 ; [0xa8:1]=223
       │    0x00000097      d2ad           setb 0xa8.5                 ; [0xa8:1]=223
       │    0x00000099      7f03           mov r7, #0x03
       │    0x0000009b      121425         lcall 0x1425
       │    0x0000009e      c2a8           clr 0xa8.0                  ; [0xa8:1]=223
       │    0x000000a0      8a23           mov 0x23, r2                ; [0x23:1]=78
       │    0x000000a2      e0             movx a, @dptr
       │    0x000000a3      54bf           anl a, #0xbf
       │    0x000000a5      f0             movx @dptr, a
       │    0x000000a6      908adf         mov dptr, #0x8adf           ; [0x8adf:1]=255
       │    0x000000a9      e0             movx a, @dptr
       │    0x000000aa      540f           anl a, #0x0f
       │    0x000000ac      6403           xrl a, #0x03
       │┌─< 0x000000ae      6003           jz 0x00b3
      ┌───< 0x000000b0      02b59c         ljmp 0xb59c
      ││└─> 0x000000b3      904762         mov dptr, #0x4762           ; 'bG'
      ││                                                               ; [0x4762:1]=255
      ││    0x000000b6      e0             movx a, @dptr
      ││    0x000000b7      54ef           anl a, #0xef
      ││    0x000000b9      f0             movx @dptr, a
      ││    0x000000ba      908a17         mov dptr, #0x8a17           ; [0x8a17:1]=255
      ││    0x000000bd      e0             movx a, @dptr
      ││┌─< 0x000000be      6015           jz 0x00d5
      │││   0x000000c0      e4             clr a
      │││   0x000000c1      908a13         mov dptr, #0x8a13           ; [0x8a13:1]=255
      │││   0x000000c4      f0             movx @dptr, a
      │││   0x000000c5      a3             inc dptr
      │││   0x000000c6      f0             movx @dptr, a
      │││   0x000000c7      9089a2         mov dptr, #0x89a2           ; [0x89a2:1]=255
      │││   0x000000ca      f0             movx @dptr, a
      │││   0x000000cb      9089d0         mov dptr, #0x89d0           ; [0x89d0:1]=255
      │││   0x000000ce      f0             movx @dptr, a
      │││   0x000000cf      a3             inc dptr
      │││   0x000000d0      f0             movx @dptr, a
      │││   0x000000d1      908a17         mov dptr, #0x8a17           ; [0x8a17:1]=255
      │││   0x000000d4      f0             movx @dptr, a
      ││└─> 0x000000d5      d2a8           setb 0xa8.0                 ; [0xa8:1]=223
      ││    0x000000d7      d2ad           setb 0xa8.5                 ; [0xa8:1]=223
      ││    0x000000d9      7f03           mov r7, #0x03
      ││    0x000000db      121425         lcall 0x1425
      ││    0x000000de      c2a8           clr 0xa8.0                  ; [0xa8:1]=223
      ││    0x000000e0      fe             mov r6, a
      ││    0x000000e1      ef             mov a, r7
      ││    0x000000e2      78aa           mov r0, #0xaa
      ││    0x000000e4      26             add a, @r0
      ││    0x000000e5      ff             mov r7, a
      ││    0x000000e6      ee             mov a, r6
      ││    0x000000e7      18             dec r0
      ││    0x000000e8      36             addc a, @r0
      ││    0x000000e9      a87c           mov r0, 0x7c                ; [0x7c:1]=23
      ││    0x000000eb      08             inc r0
      ││    0x000000ec      08             inc r0
      ││    0x000000ed      f6             mov @r0, a
      ││    0x000000ee      08             inc r0
      ││    0x000000ef      ef             mov a, r7
      ││    0x000000f0      f6             mov @r0, a
      ││┌─> 0x000000f1      904000         mov dptr, #0x4000           ; [0x4000:1]=255
      ││╎   0x000000f4      e0             movx a, @dptr
      ││└─< 0x000000f5      20e7f9         jb 0xe0.7, 0x00f1           ; [0xe0:1]=254
      ││    0x000000f8      908ac6         mov dptr, #0x8ac6           ; [0x8ac6:1]=255
      ││    0x000000fb      e0             movx a, @dptr
      ││    0x000000fc      904095         mov dptr, #0x4095           ; [0x4095:1]=255
      ││    0x000000ff      f0             movx @dptr, a
      ││    0x00000100      a87c           mov r0, 0x7c                ; [0x7c:1]=23
      ││    0x00000102      08             inc r0
      ││    0x00000103      08             inc r0
      ││    0x00000104      e6             mov a, @r0
      ││    0x00000105      a3             inc dptr
      ││    0x00000106      f0             movx @dptr, a
      ││    0x00000107      7b00           mov r3, #0x00
      ││    0x00000109      a97c           mov r1, 0x7c                ; [0x7c:1]=23
      ││    0x0000010b      09             inc r1
      ││    0x0000010c      09             inc r1
      ││    0x0000010d      7a00           mov r2, #0x00
      ││    0x0000010f      900001         mov dptr, #0x0001           ; [0x1:1]=0
      ││    0x00000112      122fb7         lcall 0x2fb7
      ││    0x00000115      904097         mov dptr, #0x4097           ; [0x4097:1]=255
      ││    0x00000118      f0             movx @dptr, a
      ││    0x00000119      90409c         mov dptr, #0x409c           ; [0x409c:1]=255
      ││    0x0000011c      7440           mov a, #0x40                ; '@'
      ││    0x0000011e      f0             movx @dptr, a
      ││    0x0000011f      900000         mov dptr, #0x0000
      ││    0x00000122      00             nop
      ││    0x00000123      00             nop
