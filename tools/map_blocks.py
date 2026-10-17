"""map_blocks.py: find every per-map event message block (analysis only).

Map init code does `ldr rA,=0x020038F0; ldr rB,=BLOCK; str rB,[rA]` and the same with 0x0201B040 and the u16 offset
table: message n = BLOCK + 2 * TABLE[n] (reader at 0x08054554, docs/re/text.md). This walks every Thumb literal load
of either RAM address, tracks literal constants through straight-line code to the store, and returns the stores.
    python -X utf8 tools/map_blocks.py   -> prints one line per (literal site, kind, value)
"""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/0291 - Granbo (J)(Lord Moyne).gba"
BLOCK_VAR, TABLE_VAR = 0x020038F0, 0x0201B040
CODE_END = 0x1A0000


def u16(rom, o):
    return struct.unpack_from("<H", rom, o)[0]


def u32(rom, o):
    return struct.unpack_from("<I", rom, o)[0]


def literal_loads(rom, site):
    """Offsets p of Thumb `ldr Rd,[pc,#imm]` that load the word at `site`."""
    for p in range(max(0, site - 1020), site, 2):
        h = u16(rom, p)
        if h >> 11 == 0b01001 and ((p + 4) & ~3) + (h & 0xFF) * 4 == site:
            yield p, (h >> 8) & 7


def stores(rom):
    """[(code offset of str, kind, value, literal offset of value)] for every BLOCK_VAR/TABLE_VAR store."""
    out = []
    for site in range(0, CODE_END, 4):
        var = u32(rom, site)
        if var not in (BLOCK_VAR, TABLE_VAR):
            continue
        for p, ra in literal_loads(rom, site):
            regs, lits = {ra: var}, {}
            q = p + 2
            for _ in range(12):
                h = u16(rom, q)
                if h >> 11 == 0b01001:  # ldr Rd,[pc,#imm]
                    lo = ((q + 4) & ~3) + (h & 0xFF) * 4
                    rd = (h >> 8) & 7
                    regs[rd], lits[rd] = u32(rom, lo), lo
                elif h >> 11 == 0b01100 and (h >> 6) & 31 == 0:  # str Rd,[Rn,#0]
                    rd, rn = h & 7, (h >> 3) & 7
                    if regs.get(rn) == var and rd in lits:
                        out.append((q, "block" if var == BLOCK_VAR else "table", regs[rd] - 0x08000000, lits[rd]))
                        break
                elif h >> 13 == 0b001 or h >> 10 == 0b010000:  # mov/cmp/add/sub imm, ALU: clobbers Rd
                    regs.pop((h >> 8) & 7 if h >> 13 == 0b001 else h & 7, None)
                elif h >> 12 in (0b1101, 0b1110, 0b1111) or h >> 8 == 0b01000111:  # branch, bl, bx
                    break
                q += 2
    return out


if __name__ == "__main__":
    rom = ROM.read_bytes()
    for q, kind, v, lit in stores(rom):
        print(f"{q:#08x} {kind:5s} {v:#08x} lit@{lit:#08x}")
