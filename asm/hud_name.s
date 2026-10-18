@ hud_name.s: battle HUD names, proportional. The HUD routine 0x08014790 copied one 8x8 small-font tile per name
@ byte (6 bytes, 6 tiles); English names need more letters than tiles, and a two-letter code (tools/ligatures.py)
@ showed its kana there. hud_name(r0 = VRAM address of the 6 tiles, r1 = the 6 name bytes) expands each code
@ through PAIRS (2 bytes per code: first, second or 0), draws the letters from FONT (tools/font_small.py, 8x8,
@ advances ADV) into a 192-byte buffer and queues one copy (0x0804D284, flushed at vblank). The buffer is
@ BUF + 192 * (side * 3 + slot): the caller's sb is the side (0-1), r6 its slot + 1, so each HUD name keeps its own
@ buffer until the flush. Pixels past 48 px are dropped. Thumb-1; keeps r4-r11.
    .thumb
hud_name:
    push {r4-r7, lr}
    mov r3, r8
    push {r3}
    adds r5, r1, #0
    mov r8, r0
    mov r3, sb
    lsls r4, r3, #1
    adds r4, r4, r3
    adds r4, r4, r6
    subs r4, #1
    movs r3, #192
    muls r4, r3
    ldr r7, lit_buf
    adds r7, r7, r4
    ldr r4, lit_bg
    movs r3, #0
fill:
    str r4, [r7, r3]
    adds r3, #4
    cmp r3, #192
    blt fill
    movs r6, #0
    movs r4, #0
byte_loop:
    ldrb r1, [r5, r4]
    ldr r3, lit_pairs
    lsls r1, r1, #1
    adds r3, r3, r1
    ldrb r1, [r3, #0]
    bl glyph
    ldrb r1, [r3, #1]
    cmp r1, #0
    beq next_byte
    bl glyph
next_byte:
    adds r4, #1
    cmp r4, #6
    blt byte_loop
    mov r0, r8
    adds r1, r7, #0
    movs r2, #192
    ldr r3, lit_queue
    bl call_r3
    pop {r3}
    mov r8, r3
    pop {r4-r7}
    pop {r3}
    bx r3
call_r3:
    bx r3

@ glyph(r1 = code): ink pixels of FONT[code] into the buffer r7 at pen r6; r6 += ADV[code]. Keeps r1-r5, r7.
glyph:
    push {r1-r5, lr}
    ldr r0, lit_font
    lsls r2, r1, #5
    adds r5, r0, r2
    movs r2, #0
g_row:
    lsls r0, r2, #2
    ldr r3, [r5, r0]
    movs r4, #0
g_px:
    movs r0, #15
    ands r0, r3
    lsrs r3, r3, #4
    cmp r0, #3
    beq g_next
    push {r1-r3}
    adds r1, r6, r4
    cmp r1, #48
    bge g_skip
    lsrs r3, r1, #3
    lsls r3, r3, #5
    lsls r2, r2, #2
    adds r3, r3, r2
    movs r2, #7
    ands r2, r1
    lsrs r2, r2, #1
    adds r3, r3, r2
    movs r2, #1
    ands r2, r1
    lsls r2, r2, #2
    ldrb r1, [r7, r3]
    push {r4}
    movs r4, #15
    lsls r4, r2
    bics r1, r4
    lsls r0, r2
    orrs r1, r0
    strb r1, [r7, r3]
    pop {r4}
g_skip:
    pop {r1-r3}
g_next:
    adds r4, #1
    cmp r4, #8
    blt g_px
    adds r2, #1
    cmp r2, #8
    blt g_row
    ldr r0, lit_adv
    ldrb r0, [r0, r1]
    adds r6, r6, r0
    pop {r1-r5, pc}
    .align 2
lit_buf:   .word BUF
lit_bg:    .word 0x33333333
lit_pairs: .word PAIRS
lit_font:  .word FONT
lit_adv:   .word ADV
lit_queue: .word 0x0804D285
