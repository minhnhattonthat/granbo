@ item2.s: field item list (0x0806ECE0) names too wide for the 64 px before the x drawn as two lines of the compact
@ font (issue #4). Replaces that list's bl draw_menu_string at 0x0806EDBC, same arguments: r0 x, r1 y, r2 name,
@ r3 tile slot, [sp] map attribute, [sp+4] layer (3 here: tiles at 0x06008000); r5 = the inventory entry (u16 id).
@ TWO[id] (id < COUNT) -> 512 bytes of tiles built by font_small.two_lines (8 for line 1, 8 for line 2) or 0.
@ 0: tail-call draw_menu_string. Else copy them into the game's per-frame staging ring ([0x02023C40]), recolour
@ as glyph16 does (ink 1/2 + ([0x020260C5] & 15); background 3 -> 0 when [0x020260C4] == 1), queue the copy to
@ VRAM slot*32 (0x0804D284) and write the 8x2 tilemap entries into the layer's map shadow (0x02000EE0 + layer*0x800).
@ Entered through a veneer that already did push {r4, r5}.
    .thumb
item2:
    ldrh r4, [r5]
    cmp r4, #COUNT
    bhs i2_plain
    lsls r4, r4, #2
    ldr r5, lit_two
    ldr r4, [r5, r4]
    cmp r4, #0
    bne i2_two
i2_plain:
    ldr r4, lit_dms
    mov ip, r4
    pop {r4, r5}
    bx ip
i2_two:
    push {r6, r7, lr}
    @ stack: r6 r7 lr r4 r5 | attr layer -> attr at [sp+20], layer at [sp+24]
    push {r0, r1, r3}
    ldr r5, lit_ring
    ldr r5, [r5]
    ldr r6, lit_color
    ldrb r6, [r6]
    movs r0, #15
    ands r6, r0
    ldr r7, lit_c4
    ldrb r7, [r7]
    movs r3, #0
i2_copy:
    ldrb r0, [r4, r3]
    movs r1, #15
    ands r1, r0
    lsrs r2, r0, #4
    bl pix
    push {r1}
    adds r1, r2, #0
    bl pix
    lsls r1, r1, #4
    pop {r0}
    orrs r0, r1
    strb r0, [r5, r3]
    adds r3, #1
    lsls r0, r3, #23
    bne i2_copy
    @ queue: r0 = VRAM + slot*32, r1 = ring, r2 = 512
    ldr r0, [sp, #8]
    lsls r0, r0, #5
    ldr r1, lit_vram
    adds r0, r0, r1
    adds r1, r5, #0
    movs r2, #1
    lsls r2, r2, #9
    ldr r3, lit_queue
    bl call_r3
    ldr r3, lit_ring
    ldr r0, [r3]
    movs r1, #1
    lsls r1, r1, #9
    adds r0, r0, r1
    str r0, [r3]
    @ map pointer: 0x02000EE0 + layer*0x800 + (((y>>3)&31)*32 + ((x>>3)&31))*2
    pop {r0, r1, r3}
    asrs r0, r0, #3
    movs r2, #31
    ands r0, r2
    asrs r1, r1, #3
    ands r1, r2
    lsls r1, r1, #5
    adds r0, r0, r1
    lsls r0, r0, #1
    ldr r1, lit_map
    adds r0, r0, r1
    ldr r1, [sp, #24]
    lsls r1, r1, #11
    adds r4, r0, r1
    ldr r5, [sp, #20]
    orrs r5, r3
    movs r2, #0
i2_map:
    strh r5, [r4]
    adds r0, r5, #0
    adds r0, #8
    adds r1, r4, #0
    adds r1, #0x40
    strh r0, [r1]
    adds r5, #1
    adds r4, #2
    adds r2, #1
    cmp r2, #8
    blt i2_map
    pop {r6, r7}
    pop {r3}
    pop {r4, r5}
    bx r3

@ pix(r1 = nibble) -> r1 recoloured; r6 = colour offset, r7 = 1 when the background is transparent. Keeps r0, r2-r7.
pix:
    cmp r1, #3
    bne pix_ink
    cmp r7, #1
    bne pix_out
    movs r1, #0
    bx lr
pix_ink:
    cmp r1, #0
    beq pix_out
    cmp r1, #2
    bhi pix_out
    adds r1, r1, r6
pix_out:
    bx lr

call_r3:
    bx r3

    .align 2
lit_two:   .word TWO
lit_dms:   .word 0x0804B3AD
lit_ring:  .word 0x02023C40
lit_color: .word 0x020260C5
lit_c4:    .word 0x020260C4
lit_queue: .word 0x0804D285
lit_vram:  .word 0x06008000
lit_map:   .word 0x02000EE0
