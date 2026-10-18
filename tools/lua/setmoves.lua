-- Force the first party Granbo's move slots every frame (QA for move-name widths):
--   emu.py ... --script tools/debug/warp.lua --var "SCENE='menu_skills'" --script tools/lua/setmoves.lua
--   --var "MOVES={218,229,26,416,0}"
-- Moves are indices into the skill table 0x082905B4 (12-byte records); slot i is u16 at 0x02005100 + 0x34 + 4*i.
-- Skills list rows (table 0x08293760): slot 4 top (64,48), 0 (24,64), 1 (136,64), 2 (24,80), 3 (136,80).
L.on_frame(function()
  for i, m in ipairs(MOVES) do
    emu.write16(0x02005100 + 0x34 + 4 * (i - 1), m, emu.memType.gbaMemory)
  end
end)
