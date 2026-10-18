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
import font_small  # noqa: E402
import ligatures  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FONT = 0x308BF8
CODE_BASE = 0x7F3000  # 0xFF padding after the original data (ends 0x7F207B); inside the original 8 MiB
VWF_STATE = 0x0203F000  # 16 bytes; only boot-time clears touch 0x0203E000-0x0203F5CF (docs/re/text.md)
NAMEBUF = VWF_STATE + 0x70  # u32: last output buffer of name6 (asm/name6.s), after the two vwf_menu states
NAME6 = 0x04B71C  # name6(src bytes, dst units): a Granbo name's 6 RAM bytes -> 6 units + 8500
HUD_BUF = VWF_STATE + 0x80  # 6 x 192 bytes: battle HUD name tiles (asm/hud_name.s), up to 0x0203F500
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
                 "「": 0x0F7, "'": 0x1F0, ":": 0x1F1, ";": 0x1F2, "%": 0x1F3, "&": 0x1F4, "*": 0x1F5, "#": 0x1F6,
                 " ": 0x1F7})
assert len(set(EN_CODES.values())) == len(EN_CODES)
assert set(EN_CODES) <= set(font_en.ART), set(EN_CODES) - set(font_en.ART)


KB_LETTERS = ["ABCDEabcde ", "FGHIJfghij.", "KLMNOklmno-", "PQRSTpqrst!", "UVWXYuvwxy?", "Z    z    ~"]
KB_SYMBOLS = ["1234567890 ", "!?.,-~()/+=", '<>"        ', "           ", "           ", "           "]


def keyboard(rows):
    """A name-entry page in the かな page's layout: per row 5 keys | 5 keys | 1 key, each key + FF00, an FF00 between
    groups, then the row's command key FF0n and 8200 (8500 after the last row). ' ' is an empty key (code 0)."""
    us = []
    for n, row in enumerate(rows, 1):
        for i, ch in enumerate(row):
            us += [EN_CODES[ch], 0xFF00] + ([0xFF00] if i in (4, 9, 10) else [])
        us += [0xFF00 + n, 0x8200 if n < len(rows) else 0x8500]
    assert all(u < 0x100 or u >= 0xFF00 or u in (0x8200, 0x8500) for u in us)
    return struct.pack(f"<{len(us)}H", *us)


def widths(pairs=None):
    w = bytearray([8] * 512)
    for ch, code in EN_CODES.items():
        w[code] = font_en.advance(ch)
    for p, code in (pairs or {}).items():  # two-letter glyphs (tools/ligatures.py): c draws both halves
        w[code], w[code + 1] = ligatures.pair_px(p), 0
    return bytes(w)


def patch(r, lig=None):
    """Apply the engine patches to build.Rom r (writes logged through r.put). lig: ligatures.plan() result."""
    pairs = (lig or {}).get("pairs", {})
    for ch, code in EN_CODES.items():
        r.put(FONT + code * 0x40, font_en.glyph_bytes(ch), f"font {ch!r}")
    for p, code in pairs.items():
        left, right = ligatures.glyphs(p)
        r.put(FONT + code * 0x40, left + right, f"font pair {p!r}")
    wt = CODE_BASE + 0x400
    r.put(wt, widths(pairs), "vwf widths")
    code = asm.assemble(ROOT / "asm/vwf.s", 0x08000000 + CODE_BASE,
                        {"STATE": VWF_STATE, "WIDTHS": 0x08000000 + wt, "GAP": EN_CODES[" "]})
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
                        {"STATE": VWF_STATE + 0x10, "WIDTHS": 0x08000000 + wt, "FILL": 1, "NAMEBUF": NAMEBUF})
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
                        {"STATE": VWF_STATE + 0x40, "WIDTHS": 0x08000000 + wt, "FILL": 0, "NAMEBUF": NAMEBUF})
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
    # skills list (0x0806BD6C): rows are 2 columns 112 px apart with "E n" drawn at name+64 px, too narrow for the
    # English names. Skip the per-row cost (`beq` on empty slot -> `b`); the description box shows "EN Cost n".
    assert r.orig[0x06BDC2:0x06BDC4] == bytes.fromhex("40d0")
    r.put(0x06BDC2, bytes.fromhex("40e0"), "skills list: no per-row cost")
    # its description box composes name + 12 spaces, cut at unit 14, + "EN Cost n": pad with asm/pad_col.s instead
    pad = CODE_BASE + 0x2040
    code = asm.assemble(ROOT / "asm/pad_col.s", 0x08000000 + pad, {"GAP": EN_CODES[" "]})
    assert len(code) <= 0x40 and r.orig[pad:pad + 0x40] == b"\xff" * 0x40
    r.put(pad, code, "pad_col code")
    assert r.orig[0x06B2F2:0x06B30E] == bytes.fromhex("00241b481c49e0f79efa601c0004040c0b2cf6d9174d85200002a883")
    stub = bytes.fromhex("1c4d281c0e21024b00f001f806e01847c046") + struct.pack("<I", 0x08000000 + pad + 1) \
        + bytes.fromhex("c046c046c046")
    # ldr r5,=0x020036F0 (pool 0x0806B364); adds r0,r5,#0; movs r1,#14; ldr r3,[pc,#8]; bl +2 (-> bx r3);
    # b 0x0806B30E; bx r3; nop; .word pad_col|1; nops
    assert len(stub) == 28
    r.put(0x06B2F2, stub, "skill description: pad_col 14")
    assert r.orig[NAME6:NAME6 + 32] == bytes.fromhex(
        "021c00231078088001320231581c0006030e052bf6d985221202101c08807047")
    code = asm.assemble(ROOT / "asm/name6.s", 0x08000000 + NAME6, {"NAMEBUF": NAMEBUF})
    assert len(code) == 32, len(code)
    r.put(NAME6, code, "name6: record the name buffer")
    # status pages: "Defense" is wider than the 32 px before the AT./DF./SP. icons. Main status (0x0806CBCE..):
    # icons 168 -> 176, values 184 -> 192; the other page using these labels (0x0808AF70..): icons 152 -> 160
    for sites, old, new in (((0x06CCBE, 0x06CD06, 0x06CD42), 0xA8, 0xB0), ((0x06CCD8, 0x06CD1C, 0x06CD58), 0xB8, 0xC0),
                            ((0x08B044, 0x08B08E, 0x08B0D0), 0x98, 0xA0)):
        for site in sites:
            assert r.orig[site:site + 2] == bytes([old, 0x20])  # movs r0, #old
            r.put(site, bytes([new, 0x20]), "status stat column x")
    # player card (0x08072EC0..): "N wins", "N hrs" need more than the 1-2 cells after the number; move the first
    # number and its label left a cell (wins: number 104 -> 88, label 136 -> 120; hours: 112 -> 96, 136 -> 120)
    # save screen (0x08073380..): hours number 120 -> 112, " hrs" 160 -> 152
    for site, old, new in ((0x07301C, 0x68, 0x58), (0x073032, 0x88, 0x78), (0x07309E, 0x70, 0x60),
                           (0x0730B6, 0x88, 0x78), (0x0733D0, 0x78, 0x70), (0x0733E8, 0xA0, 0x98)):
        assert r.orig[site:site + 2] == bytes([old, 0x20])  # movs r0, #old
        r.put(site, bytes([new, 0x20]), "card column x")
    # name-entry keyboard: the かな and カナ pages (layout strings 0x08295C44 / 0x08295D88, read by 0x08091820) become
    # an upper|lower-case page and a digits/symbols page; the ABC page (0x08295ECC) already is Latin. Codes < 256 only:
    # a Granbo's name is 6 bytes.
    for at, rows in ((0x295C44, KB_LETTERS), (0x295D88, KB_SYMBOLS)):
        old, new = r.orig[at:at + 0x144], keyboard(rows)
        ctrl = lambda b: [u if u >= 0x8000 else 0 for u in struct.unpack(f"<{len(b) // 2}H", b)]  # noqa: E731
        assert len(new) == len(old) and ctrl(new) == ctrl(old)  # same keys, separators and commands
        r.put(at, new, "name-entry keyboard page")
    # battle HUD names (0x08014790): proportional compact font instead of one small-font tile per byte
    pt = bytearray(512)
    for c in range(256):
        pt[2 * c] = c
    for p, c in pairs.items():
        pt[2 * c], pt[2 * c + 1] = EN_CODES[p[0]], EN_CODES[p[1]]
    syms = {"BUF": HUD_BUF, "PAIRS": 0x08000000 + r.alloc(bytes(pt), "hud name pairs"),
            "FONT": 0x08000000 + r.alloc(font_small.tiles(EN_CODES), "hud name font"),
            "ADV": 0x08000000 + r.alloc(font_small.advances(EN_CODES), "hud name advances")}
    hud = r.alloc(b"\0" * 0x100, "hud_name code")
    code = asm.assemble(ROOT / "asm/hud_name.s", 0x08000000 + hud, syms)
    assert len(code) <= 0x100
    r.put(hud, code, "hud_name code")
    assert r.orig[0x0147EE:0x014814] == bytes.fromhex(
        "288800194001c023db04c01839190a785201534619688918202238f03cfd0134052cedd91be0")
    stub = bytes.fromhex("28884001c023db04c018391c024b00f001f824e01847") + struct.pack("<I", 0x08000000 + hud + 1) \
        + bytes.fromhex("c046") * 6
    # ldrh r0,[r5]; lsls r0,r0,#5; movs r3,#0xc0; lsls r3,r3,#19; adds r0,r0,r3 (VRAM tile address); adds r1,r7,#0
    # (name); ldr r3,[pc,#8]; bl +2 (-> bx r3); b 0x0801484C; bx r3; .word hud_name|1; nops
    assert len(stub) == 38
    r.put(0x0147EE, stub, "hud name call")
