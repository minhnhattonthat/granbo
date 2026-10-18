"""find_rel.py: code sites that reach strings as base pointer + offset (analysis only, writes nothing).

Code often loads one string pointer and adds fixed offsets for its neighbours (`adds r2, #0xa`, a literal word
0x2030 added to the base, `movs r2, #0x34` then negated and added). Those neighbours have no pointer of their own,
so the pointer scan never extracted them, and relocating the base breaks them (docs/re/text.md). From every
literal-pool load of an extracted string (a code pointer, < 0x100000), this follows the base forward through
straight-line Thumb code (moves, adds, hi-register adds, negation; calls clobber r0-r3; branches ignored) and
prints each derived pointer that lands on a string start, as a ready "rel" item: [base id, kind, site].
Approximate: check unusual hits by disassembly (scripts/disasm.py).
    python -X utf8 tools/find_rel.py [--window 0x400] [--missing]   (--missing: only targets no entry covers)
"""
import argparse
import glob
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/0291 - Granbo (J)(Lord Moyne).gba"
GBA = 0x08000000


def literal_loads(rom, pool):
    """Thumb `ldr rX, [pc, #imm]` instructions that load the word at pool (searched up to 1 KiB back)."""
    out = []
    for a in range(max(0, pool - 0x400), pool, 2):
        hw = struct.unpack_from("<H", rom, a)[0]
        if hw >> 11 == 0b01001 and ((a + 4) & ~3) + (hw & 0xFF) * 4 == pool:
            out.append(a)
    return out


def trace(rom, start, end):
    """Follow the register loaded at start. Yields (offset, kind, site) for each pointer derived from it.
    Register values: ("B", off) = base + off, ("K", value, site, kind) = a constant and where it came from."""
    hw = struct.unpack_from("<H", rom, start)[0]
    work, seen = [(start + 2, {(hw >> 8) & 7: ("B", 0)})], set()
    while work:
        a, regs = work.pop()
        yield from _path(rom, a, end, dict(regs), work, seen)


def _path(rom, a, end, regs, work, seen):
    """One path of trace(): conditional branches queue their target, `b` jumps, function ends stop."""
    while a < end and a not in seen:
        seen.add(a)
        hw = struct.unpack_from("<H", rom, a)[0]
        op5, rd, rs = hw >> 11, hw & 7, (hw >> 3) & 7
        if op5 == 0b11110:  # bl pair
            for r in range(4):
                regs.pop(r, None)
            a += 4
            continue
        if hw >> 8 in (0xBD,) or hw == 0x4770:  # pop {.., pc}, bx lr: function end
            break
        if hw >> 12 == 0b1101 and (hw >> 8) & 15 < 14:  # conditional branch
            work.append((a + 4 + ((hw & 0xFF) ^ 0x80) * 2 - 0x100, dict(regs)))
        elif op5 == 0b11100:  # b
            a = a + 4 + ((hw & 0x7FF) ^ 0x400) * 2 - 0x800
            continue
        if op5 == 0b00011:  # add/sub register or imm3
            if hw & 0x0600 == 0x0400 and (hw >> 6) & 7 == 0 and rs in regs:  # adds rd, rs, #0
                regs[rd] = regs[rs]
            else:
                regs.pop(rd, None)
        elif op5 == 0b00100:  # movs rd, #imm8
            regs[(hw >> 8) & 7] = ("K", hw & 0xFF, a, "neg")
        elif op5 == 0b00110:  # adds rd, #imm8
            r = (hw >> 8) & 7
            v = regs.get(r)
            if v and v[0] == "B" and v[1] == 0:
                yield hw & 0xFF, "adds", a
                regs[r] = ("B", hw & 0xFF)
            else:
                regs.pop(r, None)
        elif op5 in (0b00000, 0b00001, 0b00010, 0b00111, 0b01011, 0b01101, 0b01111, 0b10001, 0b10011, 0b10100,
                     0b10101):
            regs.pop((hw >> 8) & 7 if op5 >= 0b00111 and op5 not in (0b01011, 0b01101, 0b01111, 0b10001)
                     else rd, None)
        elif hw >> 10 == 0b010000:  # ALU
            alu = (hw >> 6) & 15
            if alu == 9 and rs in regs and regs[rs][0] == "K":  # rsbs rd, rs, #0
                k = regs[rs]
                regs[rd] = ("K", -k[1], k[2], "neg")
            elif alu not in (8, 10, 11):
                regs.pop(rd, None)
        elif hw >> 10 == 0b010001:  # hi-register add / mov
            op, d, m = (hw >> 8) & 3, (hw & 7) | ((hw >> 4) & 8), (hw >> 3) & 15
            if op == 2:
                if m in regs:
                    regs[d] = regs[m]
                else:
                    regs.pop(d, None)
            elif op == 0:
                x, y = regs.get(d), regs.get(m)
                if x and y and {x[0], y[0]} == {"B", "K"}:
                    b, k = (x, y) if x[0] == "B" else (y, x)
                    if b[1] == 0:
                        yield k[1], k[3], k[2]
                    regs[d] = ("B", b[1] + k[1])
                else:
                    regs.pop(d, None)
        elif op5 == 0b01001:  # ldr rd, [pc, #imm]
            pool = ((a + 4) & ~3) + (hw & 0xFF) * 4
            regs[(hw >> 8) & 7] = ("K", struct.unpack_from("<i", rom, pool)[0], pool, "word")
        elif hw >> 12 == 0b0101 and (hw >> 9) & 7 not in (0, 1, 2):  # register-offset loads
            regs.pop(rd, None)
        elif hw >> 12 in (0b0110, 0b0111, 0b1000) and hw & 0x0800:  # immediate-offset loads
            regs.pop(rd, None)
        elif hw >> 12 == 0b1001 and hw & 0x0800 or hw >> 12 == 0b1010:  # ldr sp-rel, add rd, pc/sp
            regs.pop((hw >> 8) & 7, None)
        elif hw >> 9 == 0b1011110 or hw >> 11 == 0b11001:  # pop, ldmia
            for r in range(8):
                if hw >> r & 1:
                    regs.pop(r, None)
        a += 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=lambda x: int(x, 0), default=0x400, help="code bytes followed after a load")
    ap.add_argument("--missing", action="store_true")
    a = ap.parse_args()
    rom = ROM.read_bytes()
    ents = [e for f in sorted(glob.glob(str(ROOT / "script/ptr/*.json")))
            for e in json.loads(Path(f).read_text(encoding="utf-8"))["entries"]]
    by_at = {int(e["at"], 16): e for e in ents}
    known = {(r[0], r[1], int(r[2], 16)) for e in ents for r in e.get("rel", [])}
    for e in ents:
        at = int(e["at"], 16)
        for p in (int(x, 16) for x in e["ptrs"] if int(x, 16) < 0x100000):
            for ld in literal_loads(rom, p):
                for off, kind, site in trace(rom, ld, ld + a.window):
                    t = at + off
                    if not (0 < t < len(rom)) or struct.unpack_from("<H", rom, t - 2)[0] != text.END:
                        continue
                    child = by_at.get(t)
                    if a.missing and child:
                        continue
                    s, _ = text.decode(rom, t)
                    done = "done" if child and (e["id"], kind, site) in known else ""
                    print(f'{t:#x} {child["id"] if child else "-":8} {s[:20]!r:24} ["{e["id"]}", "{kind}", '
                          f'"{site:#08x}"] {done}')


if __name__ == "__main__":
    main()
