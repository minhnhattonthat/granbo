@ vwf_menu.s: proportional 8x16 text for draw_menu_string (0x0804B3AC: menus, lists, shops, status screens).
@ The original block at 0x0804B4C8 draws one glyph per cell: glyph16(sl + slot*32, code) recolours and queues two
@ tiles, then writes tilemap entries attr|slot at map and attr|slot+1 at map+0x40; slot += 2, map += 2.
@ The hook there calls vwf_menu(r0 slot, r1 code, r2 map) -> r0 new slot, r1 new map and resumes at 0x0804B4EC.
@ vwf_menu keeps a pen inside the current cell. A call whose slot/map equal what the previous call returned
@ continues the same run of text; anything else (new string, newline, other window) starts a new run at slot/map.
@ Cells are allocated lazily when a pixel lands in them or the pen passes them: a 0x40-byte buffer from the game's
@ per-frame staging allocator (pointer at 0x02023C40), filled with the background, queued to VRAM with the game's
@ copy queue (0x0804D284, flushed at vblank), plus the two tilemap entries. Pixels are then written into the
@ buffer, which is fine until the vblank flush. Colours as glyph16: ink 1/2 + ([0x020260C5] & 15) when that byte
@ is non-zero; background 3, or 0 (transparent) when [0x020260C4] == 1.
@ Columns: menus pad with spaces to line things up (a name, spaces, then a cost or count; choices). Under the VWF a
@ space is 3 px, so a glyph that follows 2+ spaces snaps to the column it had in the original monospace layout
@ (8 px x its index in the run), when that is right of the pen. Text before the gap must fit its old cells.
@ Frames: the typewriter window (0x0804B524) prints one glyph per frame, and the staging buffers die at each vblank.
@ When a run continues on a later frame (frame counter 0x03002654), the cell buffers are dropped; a cell that
@ already exists is reallocated by copying its 0x40 bytes back from VRAM instead of filling it with the background.
@ Uses sl (VRAM base) and r8 (tilemap attribute) of the caller read-only. Thumb-1 only. Symbols: STATE (48 bytes
@ RAM: slot, map, buf0, buf1, pen, ret slot, ret map, run start slot, glyph index, space run, frame, flags
@ (bit 0: current cell is in VRAM, bit 1: next cell is)), WIDTHS.
    .thumb
vwf_menu:
    push {r4-r7, lr}
    ldr r7, lit_state
    ldr r3, [r7, #20]
    cmp r0, r3
    bne newrun
    ldr r3, [r7, #24]
    cmp r2, r3
    beq cont
newrun:
    str r0, [r7, #0]
    str r2, [r7, #4]
    movs r3, #0
    str r3, [r7, #8]
    str r3, [r7, #12]
    str r3, [r7, #16]
    str r0, [r7, #28]
    str r3, [r7, #32]
    str r3, [r7, #36]
    str r3, [r7, #44]
    b stamp
cont:
    ldr r3, lit_frame
    ldr r3, [r3]
    ldr r4, [r7, #40]
    cmp r3, r4
    beq blit
    movs r4, #0
    ldr r5, [r7, #8]
    cmp r5, #0
    beq no_cur
    movs r4, #1
no_cur:
    ldr r5, [r7, #12]
    cmp r5, #0
    beq no_next
    adds r4, #2
no_next:
    ldr r5, [r7, #44]
    orrs r4, r5
    str r4, [r7, #44]
    movs r5, #0
    str r5, [r7, #8]
    str r5, [r7, #12]
stamp:
    ldr r3, lit_frame
    ldr r3, [r3]
    str r3, [r7, #40]
blit:
    cmp r1, #0
    bne notspace
    ldr r3, [r7, #36]
    adds r3, #1
    str r3, [r7, #36]
    b counted
notspace:
    ldr r3, [r7, #36]
    cmp r3, #2
    blt nosnap
    push {r1}
    ldr r0, [r7, #32]
    lsls r0, r0, #3
    ldr r2, [r7, #0]
    ldr r3, [r7, #28]
    subs r2, r2, r3
    lsls r2, r2, #2
    ldr r3, [r7, #16]
    adds r2, r2, r3
    subs r0, r0, r2
    ble snap_done
    adds r0, r0, r3
    bl move_pen
snap_done:
    pop {r1}
nosnap:
    movs r3, #0
    str r3, [r7, #36]
counted:
    ldr r3, [r7, #32]
    adds r3, #1
    str r3, [r7, #32]
    push {r1}
    ldr r3, lit_fontptr
    ldr r3, [r3]
    lsls r4, r1, #6
    adds r6, r3, r4
    movs r5, #0
row:
    ldr r4, [r6, r5]
    movs r3, #0
px:
    lsls r0, r3, #2
    adds r1, r4, #0
    lsrs r1, r0
    movs r0, #0xf
    ands r1, r0
    cmp r1, #3
    beq nextpx
    cmp r1, #0
    beq nextpx
    ldr r0, lit_c5
    ldrb r0, [r0]
    cmp r0, #0
    beq nocol
    lsls r0, r0, #28
    lsrs r0, r0, #28
    adds r1, r1, r0
nocol:
    push {r1, r3, r4}
    ldr r0, [r7, #16]
    adds r0, r0, r3
    push {r0}
    lsrs r0, r0, #3
    bl ensure
    pop {r2}
    lsls r2, r2, #29
    lsrs r2, r2, #27
    adds r0, r0, r5
    pop {r1}
    lsls r1, r2
    movs r3, #0xf
    lsls r3, r2
    ldr r2, [r0]
    bics r2, r3
    orrs r2, r1
    str r2, [r0]
    pop {r3, r4}
nextpx:
    adds r3, #1
    cmp r3, #8
    blt px
    adds r5, #4
    cmp r5, #0x40
    blt row
    pop {r1}
    ldr r3, lit_widths
    ldrb r3, [r3, r1]
    ldr r0, [r7, #16]
    adds r0, r0, r3
    bl move_pen
retvals:
    ldr r0, [r7, #0]
    adds r0, #2
    str r0, [r7, #20]
    ldr r1, [r7, #4]
    adds r1, #2
    str r1, [r7, #24]
    pop {r4-r7}
    pop {r3}
    bx r3

@ move_pen(r0 = new pen, from the current cell's left edge): walks into later cells, making sure every cell the pen
@ passes (and the one it stops inside) exists, so the tilemap has entries for blank cells too. Keeps r1-r7.
move_pen:
    push {r1-r6, lr}
mp_loop:
    cmp r0, #8
    blt mp_done
    push {r0}
    movs r0, #0
    bl ensure
    ldr r1, [r7, #0]
    adds r1, #2
    str r1, [r7, #0]
    ldr r1, [r7, #4]
    adds r1, #2
    str r1, [r7, #4]
    ldr r1, [r7, #12]
    str r1, [r7, #8]
    movs r1, #0
    str r1, [r7, #12]
    ldr r1, [r7, #44]
    lsrs r1, r1, #1
    str r1, [r7, #44]
    pop {r0}
    subs r0, #8
    b mp_loop
mp_done:
    str r0, [r7, #16]
    cmp r0, #0
    beq mp_ret
    movs r0, #0
    bl ensure
mp_ret:
    pop {r1-r6, pc}

@ ensure(r0 = 0: current cell, 1: next cell) -> r0 = its buffer, allocating it on first use. Keeps r1-r7.
ensure:
    push {r1-r6, lr}
    cmp r0, #0
    bne ens_next
    ldr r0, [r7, #8]
    cmp r0, #0
    bne ens_ret
    ldr r1, [r7, #0]
    ldr r2, [r7, #4]
    ldr r3, [r7, #44]
    movs r4, #1
    ands r3, r4
    ldr r5, [r7, #44]
    movs r6, #1
    bics r5, r6
    str r5, [r7, #44]
    bl alloc
    str r0, [r7, #8]
    b ens_ret
ens_next:
    ldr r0, [r7, #12]
    cmp r0, #0
    bne ens_ret
    ldr r1, [r7, #0]
    adds r1, #2
    ldr r2, [r7, #4]
    adds r2, #2
    ldr r3, [r7, #44]
    lsrs r3, r3, #1
    movs r4, #1
    ands r3, r4
    ldr r5, [r7, #44]
    movs r6, #2
    bics r5, r6
    str r5, [r7, #44]
    bl alloc
    str r0, [r7, #12]
ens_ret:
    pop {r1-r6, pc}

@ alloc(r1 slot, r2 map, r3 = 1: reload the cell from VRAM, 0: fill with the background) -> r0 buffer: staging
@ buffer queued to sl + slot*32, tilemap entries attr|slot at map and attr|slot+1 at map+0x40. Keeps r1-r7.
alloc:
    push {r1-r6, lr}
    adds r6, r3, #0
    ldr r3, lit_stage
    ldr r0, [r3]
    adds r4, r0, #0
    adds r4, #0x40
    str r4, [r3]
    cmp r6, #0
    beq bgfill
    lsls r5, r1, #5
    mov r4, sl
    adds r5, r5, r4
    movs r3, #0
copy_loop:
    ldr r4, [r5, r3]
    str r4, [r0, r3]
    adds r3, #4
    cmp r3, #0x40
    blt copy_loop
    b filled
bgfill:
    ldr r3, lit_c4
    ldrb r3, [r3]
    movs r4, #0
    cmp r3, #1
    beq fill
    ldr r4, lit_bg
fill:
    movs r3, #0
fill_loop:
    str r4, [r0, r3]
    adds r3, #4
    cmp r3, #0x40
    blt fill_loop
filled:
    mov r3, r8
    orrs r3, r1
    strh r3, [r2]
    mov r3, r8
    adds r4, r1, #1
    orrs r3, r4
    adds r5, r2, #0
    adds r5, #0x40
    strh r3, [r5]
    push {r0}
    lsls r3, r1, #5
    mov r4, sl
    adds r3, r3, r4
    adds r1, r0, #0
    adds r0, r3, #0
    movs r2, #0x40
    ldr r3, lit_queue
    bl call_r3
    pop {r0}
    pop {r1-r6, pc}
call_r3:
    bx r3
    .align 2
lit_state:   .word STATE
lit_fontptr: .word 0x0829FE04
lit_widths:  .word WIDTHS
lit_c5:      .word 0x020260C5
lit_c4:      .word 0x020260C4
lit_stage:   .word 0x02023C40
lit_bg:      .word 0x33333333
lit_queue:   .word 0x0804D285
lit_frame:   .word 0x03002654
