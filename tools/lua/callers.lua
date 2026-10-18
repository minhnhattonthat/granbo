-- Log distinct callers (LR) of a function: emu.py ... --script tools/lua/callers.lua --var FN=0x08098914 [--var FN2=0x...]
-- One line per distinct (fn, lr) with r0-r3 of the first hit. Thumb LR has bit 0 set; the call is at LR-5.
-- Optional --var R0_LO=0x.. --var R0_HI=0x.. (or R1_LO/R1_HI): only count calls whose r0 (r1) is in that range.
local seen = {}
local function hook(fn)
  L.on_exec(fn, fn, function()
    local s = emu.getState()
    if R0_LO and (s["cpu.r0"] < R0_LO or s["cpu.r0"] > R0_HI) then return end
    if R1_LO and (s["cpu.r1"] < R1_LO or s["cpu.r1"] > R1_HI) then return end
    local lr = s["cpu.r14"]
    local key = fn .. ":" .. lr
    if seen[key] then return end
    seen[key] = true
    L.log(string.format("f%d fn=%08X lr=%08X r0=%08X r1=%08X r2=%08X r3=%08X", L.frame, fn, lr,
      s["cpu.r0"], s["cpu.r1"], s["cpu.r2"], s["cpu.r3"]))
  end)
end
hook(FN)
if FN2 then hook(FN2) end
