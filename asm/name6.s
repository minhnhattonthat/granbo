@ name6.s: replaces 0x0804B71C name6(r0 src bytes, r1 dst units) in place (32 bytes): the same 6 units + 8500,
@ and it stores dst at NAMEBUF so vwf_menu's name_fill knows where a Granbo name ends. Thumb-1, r0-r3 only.
    .thumb
name6:
    ldr r3, lit_namebuf
    str r1, [r3]
    movs r3, #6
copy:
    ldrb r2, [r0]
    strh r2, [r1]
    adds r0, #1
    adds r1, #2
    subs r3, #1
    bne copy
    movs r2, #0x85
    lsls r2, r2, #8
    strh r2, [r1]
    bx lr
    .align 2
lit_namebuf: .word NAMEBUF
