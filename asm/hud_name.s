@ hud_name.s: battle HUD names, proportional. The HUD routine 0x08014790 copied one 8x8 small-font tile per name
@ byte (6 bytes, 6 tiles); English names need more letters than tiles, and a two-letter code (tools/ligatures.py)
@ showed its kana there. hud_name(r0 = VRAM address of the 6 tiles, r1 = the 6 name bytes) expands each code
@ through PAIRS (2 bytes per code: first, second or 0), draws the letters from FONT (tools/font_small.py, 8x8,
@ advances ADV) into a 192-byte buffer and queues one copy (0x0804D284, flushed at vblank). The buffer is
@ BUF + 192 * (side * 3 + slot): the caller's sb is the side (0-1), r6 its slot + 1, so each HUD name keeps its own
@ buffer until the flush. Pixels past 48 px are dropped. Thumb-1; keeps r4-r11.
@ Entry +2 is name_small (Data Ball grid names, below).
    .thumb
    b hud_name
    b name_small
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

@ name_small: draw_menu_string's small-font path (0x0804B4B0, one 8x8 tile per code via glyph8 0x0804B260) lets a
@ two-letter code squeeze 2 letters into 8 px beside single letters 8 px apart (Data Ball grid, issue #4). At a
@ Granbo name (r6 == the name6 buffer at NAMEBUF: 6 units + 8500) draw the 6 codes proportionally like hud_name
@ into 6 tiles of the game's tile ring buffer [0x02023C40] (recoloured as glyph8 does), queue the copy and write 6
@ map entries. Other strings: glyph8 as before. In: r4 map pointer, r5 tile, r6 unit pointer, sl tile base,
@ r8 map attribute, caller's glyph count at its [sp+4]. Out: r4, r5, r6 advanced (the caller then adds 2 to r6 and
@ 1 to the count); keeps r7-r11.
name_small:
    push {lr}
    ldr r3, lit_namebuf
    ldr r3, [r3]
    cmp r3, r6
    beq ns_name
    lsls r0, r5, #5
    add r0, sl
    ldrh r1, [r6]
    ldr r3, lit_glyph8
    bl call_r3
    mov r0, r8
    orrs r0, r5
    strh r0, [r4]
    adds r5, #1
    lsls r5, r5, #16
    lsrs r5, r5, #16
    adds r4, #2
    pop {r3}
    bx r3
ns_name:
    push {r4-r7}
    lsls r0, r5, #5
    add r0, sl
    push {r0}
    adds r5, r6, #0
    ldr r3, lit_ring
    ldr r7, [r3]
    ldr r4, lit_bg
    movs r3, #0
ns_fill:
    str r4, [r7, r3]
    adds r3, #4
    cmp r3, #192
    blt ns_fill
    movs r6, #0
    movs r4, #0
ns_unit:
    lsls r1, r4, #1
    ldrh r1, [r5, r1]
    ldr r3, lit_pairs
    lsls r1, r1, #1
    adds r3, r3, r1
    ldrb r1, [r3, #0]
    bl glyph
    ldrb r1, [r3, #1]
    cmp r1, #0
    beq ns_next
    bl glyph
ns_next:
    adds r4, #1
    cmp r4, #6
    blt ns_unit
    ldr r3, lit_color
    ldrb r2, [r3]
    movs r3, #15
    ands r2, r3
    beq ns_queue
    movs r3, #0
ns_rc:
    ldrb r0, [r7, r3]
    movs r1, #15
    ands r1, r0
    cmp r1, #1
    bne ns_hi
    adds r0, r0, r2
ns_hi:
    lsrs r1, r0, #4
    cmp r1, #1
    bne ns_st
    lsls r1, r2, #4
    adds r0, r0, r1
ns_st:
    strb r0, [r7, r3]
    adds r3, #1
    cmp r3, #192
    blt ns_rc
ns_queue:
    pop {r0}
    adds r1, r7, #0
    movs r2, #192
    ldr r3, lit_queue
    bl call_r3
    ldr r3, lit_ring
    ldr r0, [r3]
    adds r0, #192
    str r0, [r3]
    pop {r4-r7}
    movs r3, #0
ns_map:
    mov r0, r8
    orrs r0, r5
    strh r0, [r4]
    adds r5, #1
    adds r4, #2
    adds r3, #1
    cmp r3, #6
    blt ns_map
    lsls r5, r5, #16
    lsrs r5, r5, #16
    adds r6, #10
    ldr r0, [sp, #8]
    adds r0, #5
    str r0, [sp, #8]
    pop {r3}
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
lit_namebuf: .word NAMEBUF
lit_glyph8: .word 0x0804B261
lit_ring:  .word 0x02023C40
lit_color: .word 0x020260C5
