-- Scene list for tools/debug/warp.lua: name -> { desc, run(W) }. run is a coroutine: W.wait / W.press / W.warp
-- block until their screen condition holds. Map ids and variants: docs/re/debug.md (map table 0x081AC4F4).
local S = {}

S.title = { desc = "title screen, NEW GAME", run = function(W) W.boot_title() end }

S.town = { desc = "first town outdoors (map 1 TOWN, variant 0 W-VIEW), plaza with NPCs", run = function(W)
  W.new_game()
  W.warp(1, 0, 400, 300, 0)
end }

return S
