# Text engine

Dump: `rom.sha1` (AIBJ, 8 MiB, SRAM save, data ends 0x7F207B; rest 0xFF).

## Encoding — verified
- Text is u16 little-endian glyph indices, uncompressed in ROM. **verified**: intro line どこかにかくれなきゃ！！！
  logged glyph-by-glyph at the font read (BIOS CpuFastSet from the font, pc 0xC18) and found at 0x27197A.
- Font: ROM 0x308BF8, 512 glyphs of 8x16 px, 4bpp, 0x40 bytes each (top tile then bottom tile), pixel values 1-3.
  Glyph = code. 0 = space, 1-10 digits, then hiragana, katakana, A-Z, a-z, punctuation, ~260 kanji (one 8 px glyph
  each). Order and labels: `tools/gen_tbl.py` -> `tbl/jp.tbl`. **verified** for kana/latin/punct and the kanji
  that appear in decoded text so far (攻撃, 事, 高, 弱, 中, 強); **guess** for rarely used kanji
  (0x132 効, 0x153 像, 0x189 征, 0x1B6 薬, 0x1ED 口, 0x1F7 庫, 0x1F9 殺): confirm from context before relying on them.
- The renderer draws one glyph per 8 px column into a 2-tile-high canvas (dialogue: BG0 tiles 0x40-0x69 at
  VRAM 0x800, map 0x2000 rows 17-18), so lines are at most 30 glyphs on a 240 px screen.

## Control codes — partly guessed
Codes >= 0x8000; high byte = command, low byte = argument (one u16, no extra words seen yet).

| code | meaning | state |
|---|---|---|
| 8500 | end of string | verified (every pointer target ends with it) |
| 8200 | newline | guess (between two description lines) |
| 82xx | newline + indent/xx? (8205 in dialogue) | guess |
| 8300 | page break, wait for button | guess |
| 8400 | final wait | guess |
| 8A01 / 8B00 | open / close message window | guess |
| 86xx | portrait or speaker xx | guess |
| 94xx | 949C/949F speaker name?, 9408 inserts a name variable ("{9408}さん") | guess |
| 80,81,87,88,89,8C,8F,92,93,96,FF xx | unknown | - |

## Pointers — partly verified
- Per-string u32 pointers (`0x08000000|off`), each target preceded by 8500 (previous string's end).
- Tables: 0x2905B4 (1790 entries, skill/item names + descriptions 0x2797F0-0x285BC0), 0x1A1568 (439, battle
  dialogue 0x272D08-0x278C66), 0x1AA48C (names: ウッディーナ ...). More pointer runs: see `tools/` scans.
- Code literal pools also point at text: 0x7F2A8 -> 0x27196A (intro subtitles, fixed-size zero-padded slots).

## Event messages — verified
- Map init code stores the map's message block into RAM 0x020038F0 and its u16 offset table into 0x0201B040;
  message n = block + 2*table[n] (reader 0x08054554). **verified**: table 0x1B5A00 -> block 0x1B5B00, every
  offset lands right after an 8500. `tools/map_blocks.py` finds all 254 block/table pairs; `tools/dump.py` dumps them.
- Table length is not stored; the dump counts entries while offsets land on string starts. 90 tables end exactly
  at their block, the rest at map data. The build copies each old block verbatim before the new messages, so a
  missed index still reads valid Japanese (and shows up in QA) instead of garbage.

## Message window pipeline — verified (hooks on the original ROM, play state after the intro)
- 0x08056468 copies one page (up to {8300} or {8500}) of the message into IWRAM buffer 0x030026B0, expanding
  {94xx} names (xx >= 0x1E: table 0x081AA48C[xx-0x1E]; else RAM 0x02016A90 + 16*xx, the player-set names) and
  {96xx}. **The buffer is 0x110 bytes = 136 units** (next variable 0x030027C0): a page, names expanded, must fit.
- 0x08055C60.. walks the buffer (window struct: +8 read pointer, +0x10 current unit, +0x27/+0x2B/+0x31 state set
  by 89/88/92/93 codes).
- draw_glyph(win r0, glyph r1, col r2) at 0x08056058: src = font + glyph*0x40, dst = canvas 0x03000CC0 + col*0x40;
  CpuFastSet when colour (win+0x2F)==0x33 and (win+0x2B)==0, else the recolouring copy at 0x080560A8.
- Canvas 0x03000CC0, 0x1500 bytes (cleared by CpuFastSet fill at 0x08056038), uploaded whole to VRAM 0x06000800
  (call at 0x08056136). Columns are 2 tiles (top, bottom) = 0x40 bytes; a box line is 28 columns (BG0 map rows
  13-14 use tiles 0x40-0x77 in the field box).
- Other draw paths (fixed-length menu strings: 0x0800F9B0 copies N glyphs straight to VRAM) are separate.

## Text ranges (heuristic scan, to be replaced by the pointer-driven dump)
Main bank ~0x1A9000-0x2A0000 (densest 0x26E28A-0x290532). Smaller hits up to 0x7F16D4 are mostly noise; check each.
