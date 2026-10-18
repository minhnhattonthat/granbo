@ vwf.s: variable-width replacement for the message window's draw_glyph(win r0, glyph r1, col r2) at 0x08056058.
@ The game calls it once per glyph with col counting 8 px cells (docs/re/text.md, Message window). We keep a pen in
@ pixels: the next glyph of the same window at col == lastcol+1 goes at pen + width[lastglyph]; any other call
@ (new line, new page, indent, other window) restarts at col*8. The glyph is recoloured by the game's own routine
@ (0x080560A8) into a stack buffer, then its non-background pixels are written into the canvas at 0x03000CC0, whose
@ 8 px columns are 0x40 bytes (top tile, bottom tile: row r of the glyph is at byte r*4 in both).
@ Wide glyphs (width > 8, the two-letter glyphs Granbo names use to fit their 6-byte RAM field): the right half is
@ the next code's glyph, drawn 8 px further.
@ ARM7TDMI: Thumb-1 only. Low-register ops use the flag-setting forms (movs/adds/lsls...), low-to-low moves are
@ `adds rd, rm, #0`; tools/asm.py rejects any 32-bit encoding except bl.
@ Symbols filled in by tools/asm.py: STATE (16 bytes RAM), WIDTHS (512 bytes, advance per glyph code), GAP.
    .thumb
vwf_draw:
    push {r4-r7, lr}
    mov r4, r8
    mov r5, r9
    mov r6, sl
    push {r4, r5, r6}
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
@ a space that starts a run keeps its 8 px cell: choice lists (s26E2DE "...{8F01}Yes") draw the cursor's cell as a
@ space right before the word, and a 3 px space put "Yes" under the cursor. GAP is blank with an 8 px advance.
    cmp r1, #0
    bne store
    ldr r1, lit_gap
store:
    str r0, [r3, #0]
    str r2, [r3, #4]
    str r5, [r3, #8]
    str r1, [r3, #12]
    adds r6, r0, #0
    adds r7, r5, #0
    movs r4, #0
    mov sl, r4
half_loop:
    ldr r3, lit_state
    ldr r1, [r3, #12]
    add r1, sl
    ldr r3, lit_fontptr
    ldr r3, [r3]
    lsls r1, r1, #6
    adds r1, r3, r1
    add r2, sp, #0
    adds r0, r6, #0
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
    mov r1, sl
    lsls r1, r1, #3
    adds r5, r5, r1
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
    ldr r3, lit_state
    ldr r6, [r3, #0]
    mov r1, sl
    cmp r1, #0
    bne halves_done
    ldr r1, [r3, #12]
    ldr r2, lit_widths
    ldrb r1, [r2, r1]
    cmp r1, #8
    ble halves_done
    movs r1, #1
    mov sl, r1
    b half_loop
halves_done:
@ The game wraps a line by glyph count (window byte +0x2A, the column the caller increments after this call).
@ For the message loop's two call sites, set it to the cell the pen ends in, so wrapping follows pixels.
    ldr r3, lit_state
    ldr r1, [r3, #12]
    ldr r2, lit_widths
    ldrb r1, [r2, r1]
    adds r1, r7, r1
    adds r1, #7
    lsrs r1, r1, #3
    subs r1, #1
    ldr r2, [sp, #0x5c]
    ldr r0, lit_ret1
    cmp r2, r0
    beq sync
    ldr r0, lit_ret2
    cmp r2, r0
    bne done
sync:
    str r1, [r3, #4]
    ldr r0, [r3, #0]
    adds r0, #0x2a
    strb r1, [r0]
done:
    add sp, #0x40
    pop {r4, r5, r6}
    mov r8, r4
    mov r9, r5
    mov sl, r6
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
lit_ret1:    .word 0x08055BF9
lit_ret2:    .word 0x08055C27
lit_gap:     .word GAP
