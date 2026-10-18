-- Granbo (GBA) cold-boot warp. Boots the original or a built ROM, plays to the scene named by SCENE (see
-- tools/debug/scenes.lua), shoots it and stops. RAM addresses and how they were found: docs/re/debug.md.
--   python -X utf8 $SKILL/scripts/emu.py ROM --out work/qa/warp_town --script tools/debug/warp.lua \
--          --var "SCENE='town'" --frames 900 --sheet [--state-out work/states/town.mss]
-- Globals (--var): SCENE (required), GOD=true (party HP kept full), NOENC=true (no random battles),
--   HOLD=N frames to stay on the scene before the final shot (default 45), SCENES='path' (default
--   tools/debug/scenes.lua, relative to the repo root emu.py runs from).
-- The run ends HOLD frames after the scene is reached (final.png, f<frame>.png, --state-out). --frames is only a
-- timeout here: it is raised to WARP_TIMEOUT (default 8000) because a cold boot alone needs ~900 frames. Exit 2
-- with "scene not reached" when the scene's wait condition never comes true.
local M = emu.memType.gbaMemory
local SCENE_NAME = assert(SCENE, "set --var \"SCENE='name'\"")
-- Mesen runs scripts from its own directory: find scenes.lua by walking up from --out (work/... in the repo).
local function find_scenes()
  local dir = OUT:gsub("\\", "/")
  while dir do
    local p = dir .. "tools/debug/scenes.lua"
    local f = io.open(p)
    if f then f:close(); return p end
    dir = dir:match("^(.*/)[^/]+/$")
  end
  error("tools/debug/scenes.lua not found above --out; pass --var \"SCENES='H:/path/scenes.lua'\"", 0)
end
local scenes = dofile(SCENES or find_scenes())
local scene = scenes[SCENE_NAME]
if not scene then
  local names = {}
  for k in pairs(scenes) do names[#names + 1] = k end
  table.sort(names)
  error("unknown SCENE '" .. SCENE_NAME .. "'; known: " .. table.concat(names, " "), 0)
end

local W = { M = M }
function W.r8(a) return emu.read(a, M) end
function W.r16(a) return emu.read16(a, M) end
function W.r32(a) return emu.read32(a, M) end
function W.w8(a, v) emu.write(a, v, M) end
function W.w16(a, v) emu.write16(a, v, M) end
function W.w32(a, v) emu.write32(a, v, M) end

-- RAM map (docs/re/debug.md)
local A = {
  top = 0x0300265C,      -- u32 top-level program: 0 boot/logos/title, 1 game
  boot = 0x03000420,     -- 4 x u8 boot/title stage (01 01 04 xx = title menu waiting for Start)
  mode = 0x03002320,     -- u32 game mode (1 load request, 2 map load, 3 field, 6 map change pending, 9 demo...)
  sub = 0x03002324,      -- u32 sub-state of mode
  map = 0x03002368,      -- s16 current map id (index into map table 0x081AC4F4)
  var = 0x0300236A,      -- s16 current map variant (index into the map's variant list)
  dmap = 0x030023F0,     -- s16 destination map / variant / x / y / facing (map-change request, fn 0x080492C4)
  dvar = 0x030023F2, dx = 0x030023F4, dy = 0x030023F6, ddir = 0x030023F8,
  px = 0x0201B182, py = 0x0201B186,  -- s16 player pixel position (actor 0x0201B170, +0x12/+0x16)
  msg = 0x0201ACA0,      -- message window: u8 +0 3 = open, +1 1 typing / 2 closed, +2 1 = page done (waits for A),
                         -- +4 script ptr, +8 text cursor
  menu_top = 0x020262D0, menu_sub = 0x020262D2,  -- u8 field-menu cursors
  enc = 0x0201B270,      -- s16 encounter meter (player actor +0x100): battle when > 0xFF after a step
  namekb = 0x02026398,   -- name-entry keyboard task (+4 u8 state: 1 input, 2 accepted, 4 done; +0x1C 0x0826E5B8)
}
W.A = A

function W.mode() return W.r32(A.mode) end
-- boot stage bytes b0 b1 b2 b3: 01 00 xx Capcom logo, 01 01 02 opening anime (~900 frames), 01 01 03 00..02
-- title logo in, 03 02 title idle ("press start"), 03 03..04 NEW GAME menu opening / shown, 01 01 04 xx menu
-- confirmed, 02 start game (top -> 1). Idle 03 02 times out to the attract demo (01 01 05, 01 02 xx).
local function stage(b1, b2, b3)
  return W.r32(A.top) == 0 and W.r8(A.boot) == 1 and W.r8(A.boot + 1) == b1 and W.r8(A.boot + 2) == b2
    and (not b3 or W.r8(A.boot + 3) == b3)
end
function W.title_ready() return stage(1, 3, 4) end
function W.in_field() return W.r32(A.top) == 1 and W.r32(A.mode) == 3 end
-- Game flag sets (fn 0x08056A38 set / 0x08056A74 test): set n's bit array base is the u32 at ROM 0x081AD668 + 8n.
-- Set 3 (0x0201AD20) holds the story flags; flag 3/0x90 enables the field menu.
function W.flag_addr(set, i) return W.r32(0x081AD668 + 8 * set) + (i >> 5) * 4, 1 << (i & 31) end
function W.flag(set, i)
  local a, bit = W.flag_addr(set, i)
  return W.r32(a) & bit ~= 0
end
function W.set_flag(set, i, on)
  local a, bit = W.flag_addr(set, i)
  W.w32(a, on == false and (W.r32(a) & ~bit) or (W.r32(a) | bit))
end
function W.msg_open() return W.r8(A.msg) == 3 end
-- +2 is also 1 for a few frames while a window opens, so wait for a glyph being typed (+0x10, the current text
-- code, below 0x8000) before waiting for +2 == 1. Call it before the page is typed (right after the action).
function W.msg_typing() return W.msg_open() and W.r8(A.msg + 2) == 0 and W.r16(A.msg + 0x10) < 0x8000 end
function W.msg_page(what)
  W.wait(W.msg_typing, (what or "message") .. " typing")
  W.wait(function() return W.msg_open() and W.r8(A.msg + 2) == 1 end, (what or "message") .. " page typed")
end

-- Coroutine helpers: a scene's run(W) is a coroutine resumed once per frame.
local waiting = "start"
function W.frames(n) for _ = 1, n do coroutine.yield() end end
function W.wait(cond, what)
  waiting = what or "condition"
  while not cond() do coroutine.yield() end
end
-- Press and release: hold `n` frames (default 6), then `gap` idle frames (default 10).
function W.press(btn, n, gap)
  L.press(btn, n or 6)
  L.press("-", gap or 10)
  W.frames((n or 6) + (gap or 10))
end
-- Press `btn` every `every` frames until cond() is true.
function W.mash_until(cond, btn, what, every)
  waiting = what or "condition"
  while not cond() do W.press(btn or "a", 6, (every or 20) - 6) end
end

-- New game from a cold boot, up to the first field frame (the dark naming room, map 1 variant 1).
-- Start skips the opening anime, opens the NEW GAME menu and confirms it. Mode 11 is the name-entry keyboard
-- (its task at 0x02026398: +4 state, 1 = taking input); Start there accepts the default name カケル.
function W.boot_title()
  W.wait(function() return stage(1, 2) end, "opening anime")
  W.mash_until(function() return stage(1, 3) end, "start", "title", 20)
  W.wait(function() return stage(1, 3, 2) end, "title idle")
  W.press("start")
  W.wait(W.title_ready, "NEW GAME menu")
end
function W.name_entry_ready() return W.r32(A.mode) == 11 and W.r32(A.sub) == 1 and W.r8(A.namekb + 4) == 1 end
function W.start_game()
  W.boot_title()
  W.mash_until(function() return W.r32(A.top) == 1 and W.r32(A.mode) == 11 end, "start", "game start", 30)
  W.wait(W.name_entry_ready, "name entry keyboard")
end
function W.new_game()
  W.start_game()
  W.mash_until(function() return W.r32(A.mode) ~= 11 end, "start", "name accepted", 30)
  W.wait(W.in_field, "first field frame")
end
-- Load map/variant with the player at pixel (x, y) facing dir (0 down? see debug.md), skipping the fade: the same
-- fields the game's map-change request (0x080492C4) fills, then straight to mode 1 (load) as mode 6 does.
-- Map table 0x081AC4F4: 28-byte records {type, ?, variants, ?, spawns, ?, debug name}; spawns = 32 bytes per
-- variant, x/y at +4/+6 (map 1/1 gives 328,432: where the game itself puts the player).
function W.spawn(map, var)
  local rec = W.r32(0x081AC4F4 + 28 * map + 16) + 32 * var
  return W.r16(rec + 4), W.r16(rec + 6)
end
function W.warp(map, var, x, y, dir)
  if not x then x, y = W.spawn(map, var) end
  W.wait(W.in_field, "field before warp")
  W.w16(A.dmap, map); W.w16(A.dvar, var); W.w16(A.dx, x or 0); W.w16(A.dy, y or 0); W.w16(A.ddir, dir or 0)
  W.w16(A.map, map); W.w16(A.var, var)
  W.w8(A.mode + 0x31, 1)  -- "map changed" flag the request sets (full reload in mode 2)
  W.w32(A.mode, 1); W.w32(A.sub, 0)
  W.frames(2)
  W.wait(W.in_field, "map " .. map .. "/" .. var .. " loaded")
  W.show_palette()
end

-- Field menu (mode 7): B opens it once story flag 3/0x90 is set. Top cursor 0x020262D0 (0 Granbo, 1 items,
-- 2 info, 3 system), sub cursor 0x020262D2 (0..2, left/right). Mode 7 sub 3 = top list idle, 4 = sub list,
-- 6 = the chosen screen.
function W.menu_open()
  W.set_flag(3, 0x90)
  W.wait(W.in_field, "field before menu")
  W.mash_until(function() return W.r32(A.mode) == 7 and W.r32(A.sub) == 3 end, "b", "menu", 40)
end
function W.menu_pick(top, sub)
  W.menu_open()
  while W.r8(A.menu_top) ~= top do W.press("down", 6, 24) end
  W.press("a")
  W.wait(function() return W.r32(A.sub) == 4 end, "sub list")
  if sub then
    while W.r8(A.menu_sub) < sub do W.press("right", 6, 24) end
    W.press("a")
    W.wait(function() return W.r32(A.sub) == 6 end, "menu screen")
  end
end

-- Battle: a step with the encounter meter (player actor +0x100) above 0xFF starts a random battle on maps that
-- have an encounter table (game +0x20). Mode 4 = battle intro, mode 5 = battle. The command window is OBJ tile
-- 0x320 at (0, 6) while the player's gauge is full.
function W.battle_menu()
  for i = 0, 127 do
    local a0 = emu.read16(i * 8, emu.memType.gbaSpriteRam)
    local a2 = emu.read16(i * 8 + 4, emu.memType.gbaSpriteRam)
    if a0 & 0x300 ~= 0x200 and a0 & 0xFF == 6 and a2 & 0x3FF == 0x320 then return true end
  end
  return false
end
function W.encounter(dir)
  W.wait(W.in_field, "field before encounter")
  W.w16(A.enc, 0x100)
  W.wait(function()
    if W.r32(A.mode) ~= 3 then return true end
    L.press(dir or "up", 1)
    return false
  end, "battle start")
  W.wait(function() return W.r32(A.mode) == 5 and W.battle_menu() end, "battle command window")
end
-- Palette RAM is copied from a work palette (0x02023600) only while a fade runs; fades compute the work copy
-- from the base palette (0x02023A00). A warp out of a faded-out scene (the naming room) loads the base but
-- runs no fade, so the background stays black: copy base -> work -> palette RAM for the BG half (the OBJ half of
-- the base is black there while OBJ palette RAM is already right).
function W.show_palette()
  for i = 0, 0x1FC, 4 do
    local v = W.r32(0x02023A00 + i)
    W.w32(0x02023600 + i, v)
    emu.write32(i, v, emu.memType.gbaPaletteRam)
  end
end

-- AFTER='30 right;6 a;60 -' (route syntax) is played once the scene is reached, before HOLD: poke at a scene.
local co = coroutine.create(function()
  scene.run(W)
  L.log(string.format("scene %s at frame %d", SCENE_NAME, L.frame))
  for n, spec in (AFTER or ""):gmatch("(%d+)%s+([^;%s]+)") do
    L.press(spec, tonumber(n))
    W.frames(tonumber(n))
  end
end)
local reached, every = nil, (SHOT_EVERY or 0) > 0 and 0 or 60
FRAMES = math.max(FRAMES or 0, WARP_TIMEOUT or 8000)
L.on_frame(function(f)
  if every > 0 and f % every == 0 and W.r8(A.boot) ~= 0 then L.shot(string.format("f%06d.png", f)) end
  if not reached then
    local ok, e = coroutine.resume(co)
    if not ok then error(e, 0) end
    if coroutine.status(co) == "dead" then
      reached = f
      L.log(string.format("scene %s reached at frame %d", SCENE_NAME, f))
    elseif f >= FRAMES - 1 then
      L.fail(string.format("scene %s not reached by frame %d: waiting for %s", SCENE_NAME, f, waiting))
    end
  elseif f == reached + (HOLD or 45) then
    L.shot(string.format("f%06d.png", f))
    L.shot("final.png")
    L.log("final frame " .. f)
    if STATE_OUT then L.save_state(STATE_OUT, function() L.finish(0) end) else L.finish(0) end
  end
end)

-- Opt-in cheats, applied every frame once in the game.
if GOD or NOENC then
  L.on_frame(function()
    if W.r32(A.top) ~= 1 then return end
    if GOD and scenes.god then scenes.god(W) end
    if NOENC and scenes.noenc then scenes.noenc(W) end
  end)
end
