-- Scene list for tools/debug/warp.lua: name -> { desc, run(W) }. run is a coroutine: W.wait / W.press / W.warp
-- block until their screen condition holds. Map ids and variants: docs/re/debug.md (map table 0x081AC4F4).
local S = {}

S.title = { desc = "title screen, NEW GAME", run = function(W) W.boot_title() end }

S.name_entry = { desc = "new game: name-entry keyboard (mode 11)", run = function(W) W.start_game() end }

S.name_confirm = { desc = "new game: 'あなたの名前は『カケル』ですね? はい/いいえ' (dark room, map 1/1)",
  run = function(W)
  W.new_game()
  W.msg_page("name prompt")
end }

S.town ={ desc = "first town outdoors (map 1 TOWN, variant 0 W-VIEW), plaza with NPCs", run = function(W)
  W.new_game()
  W.warp(1, 0, 400, 300, 0)
end }

-- Any map: --var "SCENE='map'" --var MAP=1 --var VAR=0 [--var X=400 --var Y=300 --var DIR=0]
S.map = { desc = "any map/variant from --var MAP/VAR/X/Y/DIR (list: docs/re/debug.md)", run = function(W)
  W.new_game()
  W.warp(assert(MAP, "--var MAP=n"), VAR or 0, X, Y, DIR)  -- X/Y default: the variant's spawn point
end }

return S
