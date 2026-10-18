# Debug tool: cold-boot warps

`tools/debug/warp.lua` boots the ROM cold, plays to a scene from `tools/debug/scenes.lua` by waiting on RAM/screen
conditions, shoots it and stops. No save, no savestate, no manual play.

```
python -X utf8 $SKILL/scripts/emu.py "rom/0291 - Granbo (J)(Lord Moyne).gba" --out work/qa/warp_town \
    --script tools/debug/warp.lua --var "SCENE='town'" --frames 900 --sheet [--state-out work/states/town.mss]
python -X utf8 tools/debug/regen_states.py [ROM] [--only a,b] [--jobs 3]   # every scene -> work/states/<scene>.mss
```

- `--frames` is only a floor: warp.lua raises the timeout to `WARP_TIMEOUT` (8000) and ends the run itself `HOLD`
  (45) frames after the scene is reached (most scenes land at frame 500-930). Exit 2 + "not reached ... waiting for X".
- Extra globals: `GOD=true`, `NOENC=true`, `AFTER='30 right;6 a;60 -'` (route steps after arrival), `HOLD=N`.
- Generic scenes (skipped by regen): `map` (`--var MAP=1 --var VAR=0 [--var X= --var Y=]`), `menu_any`
  (`--var TOP=0..3 --var SUB=0..2`), `program` (`--var PROG=n`).
- scenes.lua is found by walking up from `--out` (Mesen runs scripts from its own directory), so keep `--out`
  inside the repo or pass `--var "SCENES='H:/.../scenes.lua'"`.

## Scenes (all verified 2026-10-18 on the original ROM, contact sheets in `work/qa/warp_<scene>/sheet.png`)

| scene | how it gets there |
|---|---|
| title | Start skips the opening anime; wait boot stage 01 01 03 02, Start, wait 01 01 03 04 (NEW GAME menu) |
| name_entry | title, Start until mode 11, wait name-entry task state 1 (keyboard) |
| name_confirm | Start on the keyboard (default name カケル), wait first field frame (dark room map 1/1), wait page typed |
| house | new game, warp 1/7 at 0,0 (the variant's event places the player), wait first page of its dialogue |
| town | new game, warp 1/0 at (400,300): plaza with NPCs |
| town_talk | town, walk up 40 + right 30 frames, A on the Granbo NPC, wait page typed |
| shop_event | warp 1/5 (SHOP A): shop manager's event (first Granbo hatches), first page |
| shop | warp 3/1 (SHOP B), walk up to the counter, A through the greeting until mode 12/9, wait mode 9 + fade idle: buy list with prices |
| battle | warp 2/1 (cave), encounter meter = 0x100, step up, wait mode 5 + command window OBJ |
| battle_won | battle with GOD, A until mode 8, fade idle: '戦闘に勝った!!!' |
| menu | set flag 3/0x90, B until mode 7 sub 3 |
| menu_skills / menu_status | menu top 0 sub 0 / 2, A on the Granbo picker until menu page 3 |
| menu_items / menu_map / menu_card | menu 1/0 (empty: アイテムがありません), 2/0, 2/2 |
| menu_save / menu_options | menu 3/0 (セーブしますか? はい/いいえ), 3/2 |
| prologue | event program 17 (narration この大地はあれはて over a storm), wait palette fade-in settled |
| ending | warp 1/10 (debug name ENDING): ending event in the town plaza, first page |

Not reached: **staff credits.** Mashing A through the 1/10 ending event (~4000 frames) ends in a map change to
0/0 (FIELD) that stays black; the credits probably need the final story flags (set 3) the warp does not set.
Next step: log flag-set calls (fn 0x08056A38) during a real ending, or trace the 1/10 event script's last commands.
Also: item screens show no items (inventory not located); story battles with dialogue not located (random
battles have no text box); program ids 22/25/27 (and others) show garbage from a cold boot.

## RAM / ROM addresses

| address | meaning | state |
|---|---|---|
| 0x0300265C u32 | top program: 0 boot/logos/title, 1 game (table 0x081A118C) | verified: trace across boot, dispatch at 0x0800058C |
| 0x03000420 4×u8 | boot stage (01 00 xx logo, 01 01 02 anime, 01 01 03 02 title idle, 03 04 NEW GAME menu, 02 start) | verified: trace + title/name scenes |
| 0x03002320 u32 | game mode (table 0x081A1408): 0 init, 1 load request, 2 map load, 3 field, 4 battle intro, 5 battle, 6 map change pending, 7 field menu, 8 battle result, 9 event program, 10 world travel, 11 name entry, 12 fade then mode [+0x14], 13 ?, 14 ? | verified for 1-12 by trace/poke; 13/14 guess |
| 0x03002324 u32 | sub-state of the mode | verified (menu 3 top list, 4 sub list, 6 screen) |
| 0x03002328 u8 | game +8: field-menu page (2 Granbo picker, 3 skill list / status page, 7 use prompt) | verified: ramsearch + menu_skills/status scenes |
| 0x03002340 ptr | game +0x20: current map's encounter table (0 = no random battles) | verified: read by fn 0x080535A4 (disasm) |
| 0x03002350 u8 | game +0x30: battle request (field → mode 4) | verified: poke starts a battle |
| 0x03002351 u8 | game +0x31: map changed / reload request (field → mode 6) | verified: disasm 0x08001D60, set by warp |
| 0x03002352 u8 | game +0x32: field menu allowed | guess: disasm 0x08001E58 |
| 0x03002354/55 u8 | game +0x34 event program request, +0x35 program id (→ mode 12 → 9) | verified: poke, ids 0-39 surveyed |
| 0x03002366 s16 | game +0x46: kind of the last mode-12 transition (5 menu, 2 battle) | guess: disasm |
| 0x03002368 s16 | current map id (map table 0x081AC4F4, 68 × 28 bytes) | verified: map loads change it, warps |
| 0x0300236A s16 | current map variant (index into the map's variant list) | verified: same |
| 0x0300244A s8 | game +0x12A: world-travel request (>0 → mode 10, <0 → mode 13) | verified: poke plays the travel sequence |
| 0x030023F0..F8 s16 | map-change request: dest map, variant, x, y, facing (fn 0x080492C4) | verified: watch + disasm; facing values guess |
| 0x02000010/14 u32 | mode 10 (world travel) phase / step | verified: trace |
| 0x0201B170 | player actor: +0x12 x, +0x16 y (s16 px), +0x83 facing, +0x100 encounter meter | verified: disasm 0x08048A88 + trace |
| 0x0201B270 s16 | encounter meter: battle when > 0xFF after a step; flag 1/8 zeroes it each step | verified: poke 0x100 + step = battle, NOENC (0 each frame) = no battle in 50 steps |
| 0x02005118 u16 | first party Granbo HP (+2 max HP, +4 EN, +6 max EN) | verified: drops in battle; GOD keeps 59/59 |
| 0x0201ACA0 | message window: +0 3 open, +1 1 typing/2 closed, +2 1 page done, +8 text cursor, +0x10 current code | verified: per-frame trace over 3 dialogues |
| 0x020262D0 / D2 u8 | field-menu top cursor (0..3) / sub cursor (0..2) | verified: ramsearch + menu matrix |
| 0x02026398 | name-entry task: +4 state (1 input, 2 accepted, 4 done) | verified: trace, name_entry scene |
| 0x0201B050 u32 | palette fade running (fn 0x08047130 sets it up); 0 idle | verified: disasm + shop/battle_won waits |
| 0x02023A00 / 0x02023600 | base / work palette (work copied to palette RAM only while a fade runs) | verified: warp out of the naming room fixed by copying |
| ROM 0x081AD668 | flag-set table: 8 bytes per set {u32 RAM base, u32 count}; set 3 = 0x0201AD20 story flags | verified: disasm 0x08056A38 |
| flag 3/0x90 | field menu enabled | verified: set → B opens the menu |
| ROM 0x081AC4F4 | map table, 28 B: {type 0/1/3, ?, variants ptr, ?, spawns ptr, ?, debug name ptr} | verified: names, spawns (1/1 = 328,432 as the game uses) |
| variants | 12 B each {u16 flags, u16 BGM?, init fn, debug name}, 0xFF ends | init fn verified (0x080576F0 etc.); BGM guess (read at 0x080688C0) |
| spawns | 32 B per variant, x/y at +4/+6 | verified: warps land walkable |
| OAM tile 0x320 at (0,6) | battle command window (コウゲキ) | verified: OAM dump visible vs hidden |

## Map ids (debug names from the ROM; variants worth knowing)

0 FIELD (TREE 1..DEMO), 1 TOWN (0 W-VIEW outdoors, 1 HOME naming room, 4 B-FRIEND, 5 SHOP A, 6 SALON A,
7 MINKA A player's house, 8/9 EVENT, 10 ENDING, 11 RESTART), 2 CAVE (1F/2F/3F rooms), 3 TOWN (1 SHOP B, 2 SALON B),
4 TOWER, 6 AIRPORT, 7 CAVE, 8 TITLE, 10/12 TOWN, 11 CAVE, 13 TOWER, 16 AIRPORT, 17/22 AIRCRAFT, 18/19 CAVE,
23-27 TOWN, 28-30 CAVE, 33 AIRPORT, 34 SKY, 53 STADIUM, 56 SKYSHARK, 60 SKYSHIP, 61 W_TOWER, 62-67 CAVE;
9/14/15/20/21/42-44/52 NO USE. Full list: decode the table (records end at 0x081ACC64).

## Event programs (mode 9 id at game +0x35), cold-boot survey

2 / 11 intro cutscenes, 4 keyboard-like screen, 5 shop list, 8-10 Granbo data screens, 13 area map, 15 '1回戦で
負けました' (tournament loss), 17 prologue narration, 24 'COMPLETE' picture; 22/25/27 garbage without context;
19/30 white; 31-39 black.

## Gotchas

- Pressing Start on the title while it still animates is fine; new-game setup (mode 11 sub 1) is the name-entry
  keyboard and waits for one more Start (a fixed-count route that stops pressing hangs there).
- A warp straight out of the naming room loads the map black: palette RAM is fed from the work palette only during a
  fade. warp.lua copies the base palette's BG half to work + palette RAM after every warp.
- Random battles are real-time: the command window comes and goes with the gauge, so the battle scene waits for its
  OBJ, not a RAM flag (none found by ramsearch across three turns).
