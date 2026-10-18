-- Log every distinct (lr, string) passed to a string routine: emu.py ... --script tools/lua/strcalls.lua
--   --var FN=0x0804B3AC [--var REG='"r2"'] [--var N=16]
-- One line per distinct (lr, string units): frame, lr, x (r0), y (r1), pointer and up to N u16 units in hex.
local seen, reg, n = {}, REG or "r2", N or 16
L.on_exec(FN, FN, function()
  local s = emu.getState()
  local p = s["cpu." .. reg]
  local t = {}
  for i = 0, n - 1 do
    local v = emu.read16(p + 2 * i, emu.memType.gbaMemory)
    t[#t + 1] = string.format("%04X", v)
    if v == 0x8500 then break end
  end
  local key = s["cpu.r14"] .. table.concat(t)
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d lr=%08X x=%d y=%d p=%08X %s", L.frame, s["cpu.r14"], s["cpu.r0"], s["cpu.r1"], p,
    table.concat(t, " ")))
end)
