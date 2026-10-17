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
-- Start skips the opening anime, opens the NEW GAME menu, confirms it. New-game setup (mode 11 sub 1) then
-- waits for one more press (o4 of the sound object 0x02026398 goes 1 -> 2 on it), so keep pressing until mode 1.
function W.boot_title()
  W.wait(function() return stage(1, 2) end, "opening anime")
  W.mash_until(function() return stage(1, 3) end, "start", "title", 20)
  W.wait(function() return stage(1, 3, 2) end, "title idle")
  W.press("start")
  W.wait(W.title_ready, "NEW GAME menu")
end
function W.new_game()
  W.boot_title()
  W.mash_until(function() return W.r32(A.top) == 1 and W.r32(A.mode) ~= 11 and W.r32(A.mode) ~= 0 end,
    "start", "new-game setup", 30)
  W.wait(W.in_field, "first field frame")
end
-- Load map/variant with the player at pixel (x, y) facing dir (0 down? see debug.md), skipping the fade: the same
-- fields the game's map-change request (0x080492C4) fills, then straight to mode 1 (load) as mode 6 does.
function W.warp(map, var, x, y, dir)
  W.wait(W.in_field, "field before warp")
  W.w16(A.dmap, map); W.w16(A.dvar, var); W.w16(A.dx, x or 0); W.w16(A.dy, y or 0); W.w16(A.ddir, dir or 0)
  W.w16(A.map, map); W.w16(A.var, var)
  W.w8(A.mode + 0x31, 1)  -- "map changed" flag the request sets
  W.w32(A.mode, 1); W.w32(A.sub, 0)
  W.frames(2)
  W.wait(W.in_field, "map " .. map .. "/" .. var .. " loaded")
end

local co = coroutine.create(function() scene.run(W) end)
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
