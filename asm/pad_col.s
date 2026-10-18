@ pad_col.s: pad a composed string to a column without cutting it (replaces "append 12 spaces, end at unit 14").
@ pad_col(r0 buf, r1 col): a string of n units with n + 2 <= col gets spaces up to unit col, so the next text
@ snaps to its original column under vwf_menu (2+ spaces); a longer one gets one GAP glyph (blank, fixed advance)
@ instead, so nothing snaps and nothing is cut. Ends the string with 8500. Thumb-1.
@ Symbols: GAP (glyph code).
    .thumb
pad_col:
    push {r4}
    movs r2, #0
    ldr r3, lit_end
scan:
    ldrh r4, [r0]
    cmp r4, r3
    beq found
    adds r0, #2
    adds r2, #1
    b scan
found:
    adds r4, r2, #2
    cmp r4, r1
    bhi long
    movs r4, #0
pad:
    cmp r2, r1
    bhs done
    strh r4, [r0]
    adds r0, #2
    adds r2, #1
    b pad
long:
    ldr r4, lit_gap
    strh r4, [r0]
    adds r0, #2
done:
    strh r3, [r0]
    pop {r4}
    bx lr
    .align 2
lit_end: .word 0x8500
lit_gap: .word GAP
