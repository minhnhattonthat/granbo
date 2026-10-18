-- Force the first party Granbo's 6 name bytes every frame (QA for name widths in HUDs and menus):
--   emu.py ... --script tools/debug/warp.lua --var "SCENE='battle'" --script tools/lua/setname.lua
--   --var "NAME={101,103,105,218,45,211}"
-- Codes as the build encodes a species name (tools/ligatures.py pairs, engine.EN_CODES); name at 0x02005100 + 8.
L.on_frame(function()
  if emu.read32(0x03002320, emu.memType.gbaMemory) ~= 3 then return end  -- field only: earlier, the record isn't set up
  for i, c in ipairs(NAME) do
    emu.write(0x02005100 + 7 + i, c, emu.memType.gbaMemory)
  end
end)
