# Graphics text

Japanese drawn as tiles, not strings. Fixes live in `tools/gfx.py` (applied by the build) unless noted.

| Screen | Element | Layer / source | State |
|---|---|---|---|
| battle | command label コウゲキ/ワザ/アイテム/ヘンシン/ボウギョ/ニゲル | OBJ tile 0x320 (32x32, pal 12); six raw 4bpp sprites at ROM 0x409B20 + 0x280*n | done: Attack/Move/Item/Morph/Defend/Run (gfx.LABELS) |
| title | グランボ logo (katakana), NEW GAME | to find | todo |
| name entry | kana keyboard grid | to find (draw_cells or tiles?) | todo |
| status, skills, battle HUD | element icon 火 (and 水/木/光/闇) in a circle | to find | todo: decide letters/symbols |
| map | region element icon 木 | to find | todo |
| battle HUD / small font | punctuation ' : ; % & * # missing in the 8x8 font (kanji slots 0x1F0+) | small font 0x08310C58 | todo |
