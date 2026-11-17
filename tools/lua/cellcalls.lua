-- Log every distinct call to the fixed-cell string routine draw_cells (0x0800F9B0, asm/vwf_cells.s):
--   emu.py ... --script tools/lua/cellcalls.lua
-- One line per distinct (lr, big, string): frame, lr, dst (r0), tile (r1), n (r3), big ([sp]), centre ([sp+4]), units.
local seen = {}
L.on_exec(0x0800F9B0, 0x0800F9B0, function()
  local s = emu.getState()
  local M = emu.memType.gbaMemory
  local p, sp = s["cpu.r2"], s["cpu.r13"]
  local t = {}
  for i = 0, 15 do
    local v = emu.read16(p + 2 * i, M)
    t[#t + 1] = string.format("%04X", v)
    if v == 0x8500 then break end
  end
  local big, ctr = emu.read32(sp, M), emu.read32(sp + 4, M)
  local key = s["cpu.r14"] .. big .. table.concat(t)
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d lr=%08X dst=%08X tile=%d n=%d big=%d ctr=%d %s", L.frame, s["cpu.r14"], s["cpu.r0"],
    s["cpu.r1"], s["cpu.r3"], big, ctr, table.concat(t, " ")))
end)
