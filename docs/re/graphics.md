# Graphics text

Japanese drawn as tiles, not strings. Fixes live in `tools/gfx.py` (applied by the build) unless noted.

| Screen | Element | Layer / source | State |
|---|---|---|---|
| battle | command label コウゲキ/ワザ/アイテム/ヘンシン/ボウギョ/ニゲル | OBJ tile 0x320 (32x32, pal 12); six raw 4bpp sprites at ROM 0x409B20 + 0x280*n | done: Attack/Move/Item/Morph/Defend/Run (gfx.LABELS) |
| title | グランボ logo (katakana), NEW GAME | to find | todo |
| name entry | kana keyboard grid | to find (draw_cells or tiles?) | todo |
| status, skills, map, menus | element icon 火/水/木/闇 (+ empty) in a circle | 16x16, raw 4bpp: tops 0x572D74 + 0x40*i, bottoms 0x573174 + 0x40*i (block 0x08571974 +0x1400/+0x1800, copier 0x0806A3BC) | done: flame/drop/leaf/crescent pictograms (gfx.ELEMENTS) |
| battle HUD / small font | punctuation ' : ; % & * # missing in the 8x8 font (kanji slots 0x1F0+) | small font 0x08310C58 | todo |
