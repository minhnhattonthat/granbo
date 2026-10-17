@ vwf.s: variable-width replacement for the message window's draw_glyph(win r0, glyph r1, col r2) at 0x08056058.
@ The game calls it once per glyph with col counting 8 px cells (docs/re/text.md, Message window). We keep a pen in
@ pixels: the next glyph of the same window at col == lastcol+1 goes at pen + width[lastglyph]; any other call
@ (new line, new page, indent, other window) restarts at col*8. The glyph is recoloured by the game's own routine
@ (0x080560A8) into a stack buffer, then its non-background pixels are written into the canvas at 0x03000CC0, whose
@ 8 px columns are 0x40 bytes (top tile, bottom tile: row r of the glyph is at byte r*4 in both).
@ ARM7TDMI: Thumb-1 only. Low-register ops use the flag-setting forms (movs/adds/lsls...), low-to-low moves are
@ `adds rd, rm, #0`; tools/asm.py rejects any 32-bit encoding except bl.
@ Symbols filled in by tools/asm.py: STATE (16 bytes RAM), WIDTHS (512 bytes, advance per glyph code).
    .thumb
vwf_draw:
    push {r4-r7, lr}
    mov r4, r8
    mov r5, r9
    push {r4, r5}
    sub sp, #0x40
    lsls r1, r1, #16
    lsrs r1, r1, #16
    lsls r2, r2, #16
    lsrs r2, r2, #16
    ldr r3, lit_state
    ldr r4, [r3, #0]
    cmp r4, r0
    bne reset
    ldr r4, [r3, #4]
    adds r4, #1
    cmp r4, r2
    bne reset
    ldr r4, [r3, #12]
    ldr r5, lit_widths
    ldrb r4, [r5, r4]
    ldr r5, [r3, #8]
    adds r5, r5, r4
    b store
reset:
    lsls r5, r2, #3
store:
    str r0, [r3, #0]
    str r2, [r3, #4]
    str r5, [r3, #8]
    str r1, [r3, #12]
    adds r6, r0, #0
    adds r7, r5, #0
    ldr r3, lit_fontptr
    ldr r3, [r3]
    lsls r1, r1, #6
    adds r1, r3, r1
    add r2, sp, #0
    ldr r3, lit_recolor
    bl call_r3
    adds r0, r6, #0
    adds r0, #0x2f
    ldrb r0, [r0]
    movs r1, #0xf
    ands r0, r1
    ldr r1, lit_canvas
    mov r9, r1
    movs r1, #0
    mov r8, r1
row_loop:
    mov r1, r8
    add r2, sp, #0
    ldr r2, [r2, r1]
    movs r3, #0
px_loop:
    lsls r5, r3, #2
    adds r4, r2, #0
    lsrs r4, r5
    movs r1, #0xf
    ands r4, r1
    cmp r4, r0
    beq next_px
    adds r5, r7, r3
    lsrs r6, r5, #3
    lsls r6, r6, #6
    add r6, r9
    add r6, r8
    movs r1, #7
    ands r5, r1
    lsls r5, r5, #2
    lsls r4, r5
    movs r1, #0xf
    lsls r1, r5
    ldr r5, [r6]
    bics r5, r1
    orrs r5, r4
    str r5, [r6]
next_px:
    adds r3, #1
    cmp r3, #8
    blt px_loop
    mov r1, r8
    adds r1, #4
    mov r8, r1
    cmp r1, #0x40
    blt row_loop
    add sp, #0x40
    pop {r4, r5}
    mov r8, r4
    mov r9, r5
    pop {r4-r7}
    pop {r0}
    bx r0
call_r3:
    bx r3
    .align 2
lit_state:   .word STATE
lit_widths:  .word WIDTHS
lit_fontptr: .word 0x0829FE04
lit_recolor: .word 0x080560A9
lit_canvas:  .word 0x03000CC0
