"""engine.py: code and font patches for English (docs/re/text.md, docs/fonts.md).

- English glyphs (tools/font_en.py) replace the font's Latin/digit/punctuation glyphs; characters the font lacks
  go into kanji slots 0x1F0+ (unused once the script is English).
- VWF for the message window: draw_glyph at 0x08056058 jumps to asm/vwf.s, which advances by WIDTHS[code].
Codes not drawn by font_en keep their 8 px advance.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import asm  # noqa: E402
import font_en  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FONT = 0x308BF8
CODE_BASE = 0x7F3000  # 0xFF padding after the original data (ends 0x7F207B); inside the original 8 MiB
VWF_STATE = 0x0203F000  # 16 bytes; only boot-time clears touch 0x0203E000-0x0203F5CF (docs/re/text.md)
DRAW_GLYPH = 0x056058
MENU_GLYPH = 0x04B4C8  # 8x16 per-glyph block inside draw_menu_string (0x0804B3AC)
TYPE_GLYPH = 0x04B6C0  # 8x16 per-glyph block inside the typewriter window printer (0x0804B524)
DRAW_CELLS = 0x00F9B0  # draw_cells(dst, tile, str, n, big, centre): menus and lists (docs/re/text.md)

EN_CODES = {" ": 0x000}
EN_CODES.update({str(d): 0x001 + d for d in range(10)})
EN_CODES.update({chr(65 + i): 0x0AC + i for i in range(26)})
EN_CODES.update({chr(97 + i): 0x0C6 + i for i in range(26)})
EN_CODES.update({"!": 0x0E8, "?": 0x0E9, ".": 0x0EC, ",": 0x0E2, "-": 0x0EE, "(": 0x0F5, ")": 0x0F6, "/": 0x0F1,
                 "+": 0x0ED, "=": 0x0F2, "~": 0x0E1, "<": 0x0E4, ">": 0x0E5, '"': 0x0E6,
                 "「": 0x0F7, "'": 0x1F0, ":": 0x1F1, ";": 0x1F2, "%": 0x1F3, "&": 0x1F4, "*": 0x1F5, "#": 0x1F6})
assert len(set(EN_CODES.values())) == len(EN_CODES)
assert set(EN_CODES) <= set(font_en.ART), set(EN_CODES) - set(font_en.ART)


def widths():
    w = bytearray([8] * 512)
    for ch, code in EN_CODES.items():
        w[code] = font_en.advance(ch)
    return bytes(w)


def patch(r):
    """Apply the engine patches to build.Rom r (writes logged through r.put)."""
    for ch, code in EN_CODES.items():
        r.put(FONT + code * 0x40, font_en.glyph_bytes(ch), f"font {ch!r}")
    wt = CODE_BASE + 0x400
    r.put(wt, widths(), "vwf widths")
    code = asm.assemble(ROOT / "asm/vwf.s", 0x08000000 + CODE_BASE, {"STATE": VWF_STATE, "WIDTHS": 0x08000000 + wt})
    assert len(code) <= 0x400
    assert r.orig[CODE_BASE:CODE_BASE + 0x600] == b"\xff" * 0x600
    r.put(CODE_BASE, code, "vwf code")
    assert r.orig[DRAW_GLYPH:DRAW_GLYPH + 8] == bytes.fromhex("10b5031c09041204"), r.orig[DRAW_GLYPH:DRAW_GLYPH + 8].hex()
    hook = bytes.fromhex("004b1847") + struct.pack("<I", 0x08000000 + CODE_BASE + 1)  # ldr r3,[pc]; bx r3; .word
    r.put(DRAW_GLYPH, hook, "vwf hook draw_glyph")
    # fixed-cell strings (menus, lists): 0x0800F9B0 keeps its push; 8x16 mode goes to asm/vwf_cells.s
    cells = CODE_BASE + 0x800
    code = asm.assemble(ROOT / "asm/vwf_cells.s", 0x08000000 + cells, {"WIDTHS": 0x08000000 + wt})
    assert len(code) <= 0x400 and r.orig[cells:cells + 0x400] == b"\xff" * 0x400
    r.put(cells, code, "vwf_cells code")
    assert r.orig[DRAW_CELLS:DRAW_CELLS + 12] == bytes.fromhex("f0b557464e464546e0b484b0")
    hook = bytes.fromhex("014c2047c046") + struct.pack("<I", 0x08000000 + cells + 1)  # ldr r4,[pc,#4]; bx r4; nop
    r.put(DRAW_CELLS + 2, hook, "vwf_cells hook")
    # menu strings: draw_menu_string's 8x16 glyph block (0x0804B4C8-0x0804B4E5) -> asm/vwf_menu.s
    menu = CODE_BASE + 0x1000
    code = asm.assemble(ROOT / "asm/vwf_menu.s", 0x08000000 + menu,
                        {"STATE": VWF_STATE + 0x10, "WIDTHS": 0x08000000 + wt})
    assert len(code) <= 0x800 and r.orig[menu:menu + 0x800] == b"\xff" * 0x800
    r.put(menu, code, "vwf_menu code")
    assert r.orig[MENU_GLYPH:MENU_GLYPH + 30] == bytes.fromhex(
        "680150443188fff7f5fd404628432080211c4031681c424610430880a81c")
    stub = bytes.fromhex("3188281c221c044b00f004f8051c0c1c08e0c0461847c046") \
        + struct.pack("<I", 0x08000000 + menu + 1) + bytes.fromhex("c046")
    # ldrh r1,[r6]; adds r0,r5,#0; adds r2,r4,#0; ldr r3,[pc,#16]; bl +8 (-> bx r3); adds r5,r0,#0;
    # adds r4,r1,#0; b 0x0804B4EC; nop; bx r3; nop; .word vwf_menu|1; nop
    assert len(stub) == 30
    r.put(MENU_GLYPH, stub, "vwf_menu hook")
    # typewriter window (0x0804B524): its 8x16 block keeps slot at [r5] (0x020260CC) and the attribute at [r8]
    assert r.orig[TYPE_GLYPH:TYPE_GLYPH + 44] == bytes.fromhex(
        "2888400150440988fff7f8fc434618882988084320804020001984462a88501c198808436146088002322a80")
    # its own copy of vwf_menu with its own state: it prints a glyph per frame while menus redraw strings between
    # its calls, and a shared state would restart its run at every one of them
    tw = CODE_BASE + 0x1800
    code = asm.assemble(ROOT / "asm/vwf_menu.s", 0x08000000 + tw,
                        {"STATE": VWF_STATE + 0x40, "WIDTHS": 0x08000000 + wt})
    assert len(code) <= 0x800 and r.orig[tw:tw + 0x800] == b"\xff" * 0x800
    r.put(tw, code, "vwf_menu (typewriter) code")
    wrap = CODE_BASE + 0x2000
    code = asm.assemble(ROOT / "asm/tw_wrap.s", 0x08000000 + wrap, {"VWF": 0x08000000 + tw + 1})
    assert len(code) <= 0x40 and r.orig[wrap:wrap + 0x40] == b"\xff" * 0x40
    r.put(wrap, code, "typewriter column sync")
    stub = bytes.fromhex("28880988221c434608b41b889846054b00f006f828800c1c08bc984607e0c0461847c046") \
        + struct.pack("<I", 0x08000000 + wrap + 1) + bytes.fromhex("c046c046")
    # ldrh r0,[r5]; ldrh r1,[r1]; adds r2,r4,#0; mov r3,r8; push {r3}; ldrh r3,[r3]; mov r8,r3; ldr r3,[pc,#20];
    # bl +12 (-> bx r3); strh r0,[r5]; adds r4,r1,#0; pop {r3}; mov r8,r3; b 0x0804B6EE; nop; bx r3; nop; .word; nops
    assert len(stub) == 44
    r.put(TYPE_GLYPH, stub, "vwf_menu typewriter hook")
    # speaker-name copy loops (`cmp r4,#5`: 6 units) pad the name with spaces: inline labels from the message (<= 9
    # glyphs) -> 10 units, RAM name slots (16 bytes: <= 7 glyphs + end) -> 8, so a padding space always separates
    # name and text. fit.first_x computes where the text then starts; fit.NAME_PX gates the name width.
    for site, n in ((0x05661A, 10), (0x056648, 8)):
        assert r.orig[site:site + 2] == bytes.fromhex("052c")
        r.put(site, bytes([n - 1, 0x2C]), f"speaker name {n} units")
