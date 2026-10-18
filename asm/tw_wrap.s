@ tw_wrap.s: calls the typewriter's own copy of vwf_menu and keeps the typewriter's column counter in step.
@ The typewriter (0x0804B524) rebuilds its tilemap pointer every frame from x = [0x020260C0] + [0x020260C2] (the
@ glyph count, +1 after each glyph). Under the VWF a glyph advances the map by 0..n cells, so after the call
@ [0x020260C2] += cells moved - 1; the caller's +1 then lands the next frame's pointer on the cell the pen is in,
@ and vwf_menu sees a continuation. Same arguments and results as vwf_menu (r0 slot, r1 code, r2 map).
@ Thumb-1 only. Symbols: VWF (vwf_menu copy | 1).
    .thumb
tw_wrap:
    push {r4, r5, lr}
    adds r4, r2, #0
    ldr r3, lit_vwf
    bl call_r3
    subs r2, r1, r4
    asrs r2, r2, #1
    subs r2, #1
    ldr r3, lit_x
    ldrb r5, [r3]
    adds r5, r5, r2
    strb r5, [r3]
    pop {r4, r5}
    pop {r3}
    bx r3
call_r3:
    bx r3
    .align 2
lit_vwf: .word VWF
lit_x:   .word 0x020260C2
