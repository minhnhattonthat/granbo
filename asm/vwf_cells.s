@ vwf_cells.s: proportional text for the fixed-cell string routine at 0x0800F9B0.
@ draw_cells(dst r0, tile r1, str r2, n r3, [sp] big, [sp+4] centre) writes n cells of a u16 string (8500-ended)
@ to VRAM at dst + tile*32. big != 0: 8x16 font, a cell = 2 tiles (0x40 bytes, top then bottom); big == 0: 8x8
@ small font, a cell = 1 tile. The hook at 0x0800F9B0 keeps its `push {r4-r7,lr}` and jumps here.
@ big == 0 -> replay the overwritten instructions and return to the original code at 0x0800F9BC.
@ big != 0 -> clear the n cells with glyph 0's background, measure the string with WIDTHS, centre it in pixels if
@ asked, then OR each glyph's non-background pixels in at the pen. Control codes (>= 512) draw nothing.
@ Thumb-1 only (ARM7TDMI); tools/asm.py rejects 32-bit encodings except bl. Symbols: WIDTHS.
    .thumb
vwf_cells:
    ldr r4, [sp, #20]
    lsls r4, r4, #24
    bne big
    mov r7, sl
    mov r6, sb
    mov r5, r8
    push {r5, r6, r7}
    sub sp, #0x10
    ldr r4, lit_back
    bx r4
big:
    mov r4, r8
    mov r5, r9
    mov r6, sl
    mov r7, fp
    push {r4-r7}
    lsls r1, r1, #16
    lsrs r1, r1, #11
    adds r0, r0, r1
    mov r8, r0
    mov r9, r3
    mov sl, r2
    ldr r4, lit_fontptr
    ldr r4, [r4]
    ldr r4, [r4]
    mov fp, r4
    lsls r5, r3, #6
    movs r6, #0
clear:
    cmp r6, r5
    bhs measure
    str r4, [r0, r6]
    adds r6, #4
    b clear
measure:
    movs r5, #0
    movs r3, #0
    mov r6, sl
    ldr r7, lit_widths
    movs r1, #0x85
    lsls r1, r1, #8
m_loop:
    ldrh r4, [r6]
    cmp r4, r1
    beq m_done
    adds r3, #1
    lsrs r0, r4, #9
    bne m_next
    ldrb r0, [r7, r4]
    adds r5, r5, r0
m_next:
    adds r6, #2
    b m_loop
m_done:
@ the original returns the unit count before 8500, capped at n; lr is free (saved by the hook's push)
    cmp r3, r9
    bls count_ok
    mov r3, r9
count_ok:
    mov lr, r3
    movs r6, #0
    ldr r4, [sp, #40]
    lsls r4, r4, #24
    beq draw
    mov r4, r9
    lsls r4, r4, #3
    subs r4, r4, r5
    ble draw
    lsrs r6, r4, #1
draw:
    mov r2, sl
    ldrh r4, [r2]
    adds r2, #2
    mov sl, r2
    movs r1, #0x85
    lsls r1, r1, #8
    cmp r4, r1
    beq done
    lsrs r0, r4, #9
    bne draw
    mov r0, r9
    lsls r0, r0, #3
    cmp r6, r0
    bhs done
    ldr r0, lit_fontptr
    ldr r0, [r0]
    lsls r1, r4, #6
    adds r0, r0, r1
    push {r4}
    bl blit_rows
    pop {r4}
    ldr r7, lit_widths
    ldrb r0, [r7, r4]
    cmp r0, #8
    ble adv
@ wide glyph: the right half is the next code's glyph, 8 px further
    push {r4}
    adds r6, #8
    ldr r0, lit_fontptr
    ldr r0, [r0]
    adds r1, r4, #1
    lsls r1, r1, #6
    adds r0, r0, r1
    bl blit_rows
    subs r6, #8
    pop {r4}
    ldr r7, lit_widths
    ldrb r0, [r7, r4]
adv:
    adds r6, r6, r0
    b draw

@ blit_rows(r0 = glyph src, r6 = pen): the glyph's non-background pixels into the cells, clipped to n cells.
blit_rows:
    push {r4-r7, lr}
    movs r1, #0
row_loop:
    ldr r2, [r0, r1]
    movs r3, #0
px_loop:
    lsls r5, r3, #2
    adds r4, r2, #0
    lsrs r4, r5
    movs r7, #0xf
    ands r4, r7
    mov r7, fp
    lsls r7, r7, #28
    lsrs r7, r7, #28
    cmp r4, r7
    beq next_px
    adds r5, r6, r3
    mov r7, r9
    lsls r7, r7, #3
    cmp r5, r7
    bhs next_px
    lsrs r7, r5, #3
    lsls r7, r7, #6
    add r7, r8
    adds r7, r7, r1
    lsls r5, r5, #29
    lsrs r5, r5, #27
    lsls r4, r5
    mov ip, r4
    movs r4, #0xf
    lsls r4, r5
    ldr r5, [r7]
    bics r5, r4
    mov r4, ip
    orrs r5, r4
    str r5, [r7]
next_px:
    adds r3, #1
    cmp r3, #8
    blt px_loop
    adds r1, #4
    cmp r1, #0x40
    blt row_loop
    pop {r4-r7, pc}
done:
    mov r0, lr
    pop {r4-r7}
    mov r8, r4
    mov r9, r5
    mov sl, r6
    mov fp, r7
    pop {r4-r7}
    pop {r3}
    bx r3
    .align 2
lit_back:    .word 0x0800F9BD
lit_fontptr: .word 0x0829FE04
lit_widths:  .word WIDTHS
