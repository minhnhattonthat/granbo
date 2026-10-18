-- Scene list for tools/debug/warp.lua: name -> { desc, run(W) }. run is a coroutine: W.wait / W.press / W.warp
-- block until their screen condition holds. Map ids and variants: docs/re/debug.md (map table 0x081AC4F4).
-- tools/debug/regen_states.py runs every scene here except those with `manual = true`.
local S = {}

S.title = { desc = "title screen, NEW GAME menu", run = function(W) W.boot_title() end }

S.name_entry = { desc = "new game: name-entry keyboard (mode 11)", run = function(W) W.start_game() end }

S.name_confirm = { desc = "new game: 'あなたの名前は『カケル』ですね? はい/いいえ' (dark room, map 1/1)",
  run = function(W)
  W.new_game()
  W.msg_page("name prompt")
end }

S.house = { desc = "player's house after the intro (map 1/7 MINKA A): opening event, first dialogue page",
  run = function(W)
  W.new_game()
  W.warp(1, 7, 0, 0, 0)  -- 0,0: the variant's event places the player, as the game's own warp does
  W.msg_page("house dialogue")
end }

S.town = { desc = "first town outdoors (map 1 TOWN, variant 0 W-VIEW), plaza with NPCs", run = function(W)
  W.new_game()
  W.warp(1, 0, 400, 300, 0)
end }

S.town_talk = { desc = "town plaza, talking to the Granbo NPC (dialogue box)", run = function(W)
  W.new_game()
  W.warp(1, 0, 400, 300, 0)
  W.press("up", 40, 2)
  W.press("right", 30, 2)
  W.press("a")
  W.msg_page("NPC dialogue")
end }

S.lab = { desc = "map 1/5 (debug name SHOP A): professor's lab event, first dialogue page", run = function(W)
  W.new_game()
  W.warp(1, 5)
  W.msg_page("lab dialogue")
end }

S.battle = { desc = "random battle in cave map 2/1 (2 ホッパー): battle screen with the command window",
  run = function(W)
  W.new_game()
  W.warp(2, 1)
  W.encounter("up")
end }

-- Field menu: top 0 Granbo (skills...), 1 items, 2 info (map...), 3 system (save...); sub 0..2 per top.
S.menu = { desc = "field menu, top list (B in the field)", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_open()
end }
S.menu_skills = { desc = "menu > Granbo > ワザ > ピヨリカ: skill list with description", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(0, 0)
  W.mash_until(function() return W.r8(0x020260CA) == 1 end, "a", "skill list", 40)
end }
S.menu_status = { desc = "menu > Granbo > 強さ > ピヨリカ: Granbo status page", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(0, 2)
  W.mash_until(function() return W.r8(0x02026044) == 1 end, "a", "status page", 40)
end }
S.menu_card = { desc = "menu > ジョウホウ > player card (name, ID, rank, record, play time)", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(2, 2)
end }
S.menu_options = { desc = "menu > システム > options (sound, music, text speed)", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(3, 2)
end }
S.menu_items = { desc = "menu > アイテム > first item screen", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(1, 0)
end }
S.menu_map = { desc = "menu > ジョウホウ > マップ (area map)", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(2, 0)
end }
S.menu_save = { desc = "menu > システム > セーブ (save confirm)", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(3, 0)
end }

S.ending = { desc = "ending event in the town plaza (map 1/10, debug name ENDING), first dialogue page",
  run = function(W)
  W.new_game()
  W.warp(1, 10, 0, 0, 0)
  W.msg_page("ending dialogue")
end }

-- Any map: --var "SCENE='map'" --var MAP=1 --var VAR=0 [--var X=400 --var Y=300 --var DIR=0]
S.map = { manual = true, desc = "any map/variant from --var MAP/VAR/X/Y/DIR (list: docs/re/debug.md)",
  run = function(W)
  W.new_game()
  W.warp(assert(MAP, "--var MAP=n"), VAR or 0, X, Y, DIR)  -- X/Y default: the variant's spawn point
end }
-- Any menu screen: --var "SCENE='menu_any'" --var TOP=2 --var SUB=1
S.menu_any = { manual = true, desc = "field menu screen from --var TOP/SUB", run = function(W)
  W.new_game(); W.warp(1, 0, 400, 300, 0); W.menu_pick(TOP or 0, SUB)
end }

-- Opt-in cheats (warp.lua calls these every frame in game when --var GOD=true / NOENC=true)
function S.noenc(W) W.w16(W.A.enc, 0) end
function S.god(W) W.w16(W.A.hp, W.r16(W.A.hp + 2)) end  -- first party Granbo only (others' slots unknown)

return S
