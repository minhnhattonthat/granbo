# Graphics text

Japanese drawn as tiles, not strings. Fixes live in `tools/gfx.py` (applied by the build) unless noted.

| Screen | Element | Layer / source | State |
|---|---|---|---|
| battle | command label コウゲキ/ワザ/アイテム/ヘンシン/ボウギョ/ニゲル | OBJ tile 0x320 (32x32, pal 12); six raw 4bpp sprites at ROM 0x409B20 + 0x280*n | done: Attack/Move/Item/Morph/Defend/Run (gfx.LABELS) |
| title | グランボ logo (katakana), NEW GAME | to find | todo |
| name entry | kana keyboard grid | text, not tiles: layout strings 0x08295C44 (かな) / 0x08295D88 (カナ) / 0x08295ECC (ABC), drawn by 0x08091820 | done: ABC (upper|lower) and 123 pages (engine.keyboard), buttons ABC/123/A-Z |
| link cable | 通信中 label (white, 3 kanji 16x16) | block 0x08571974 + 0x1000.., tiles near the element icons (0x572D74 + 0x200/0x600 + 10*32) | todo: "Linking" (unverified screen) |
| status, skills, map, menus | element icon 火/水/木/闇 (+ empty) in a circle | 16x16, raw 4bpp: tops 0x572D74 + 0x40*i, bottoms 0x573174 + 0x40*i (block 0x08571974 +0x1400/+0x1800, copier 0x0806A3BC) | done: flame/drop/leaf/crescent pictograms (gfx.ELEMENTS) |
| battle HUD / small font | punctuation ' : ; % & * # missing in the 8x8 font (kanji slots 0x1F0+) | small font 0x08310C58 | todo |
