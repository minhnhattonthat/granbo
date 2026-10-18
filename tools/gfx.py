"""gfx.py: text drawn as graphics (docs/re/graphics.md), redrawn in English by the build.

Battle command labels: six 32x32 sprites (16 tiles, 4bpp, 1D) uncompressed in ROM, one per command, shown at the
top left of the battle screen (OAM tile 0x320). The label strip is rows 4-11, columns 0-29 (background index 1,
text index 0xD); its text is redrawn with tools/font_small.py, centred.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font_small  # noqa: E402

# ヘンシン is "Transform" everywhere else; the 30 px strip fits "Morph" (glossary, flagged)
LABELS = [(0x409B20, "Attack"), (0x409DA0, "Move"), (0x40A020, "Item"), (0x40A2A0, "Morph"), (0x40A520, "Defend"),
          (0x40A7A0, "Run")]


def sprite_px(data, w=4, h=4):
    """4bpp 1D sprite bytes -> rows of palette indices."""
    px = [[0] * (8 * w) for _ in range(8 * h)]
    for t in range(w * h):
        for y in range(8):
            for x in range(8):
                px[t // w * 8 + y][t % w * 8 + x] = data[t * 32 + y * 4 + x // 2] >> (4 * (x & 1)) & 15
    return px


def sprite_bytes(px, w=4, h=4):
    out = bytearray()
    for t in range(w * h):
        for y in range(8):
            row = px[t // w * 8 + y][t % w * 8:t % w * 8 + 8]
            out += bytes(row[x] | row[x + 1] << 4 for x in range(0, 8, 2))
    return bytes(out)


def draw(px, text, x, y, ink):
    for ch in text:
        for dy, r in enumerate(font_small.ART[ch]):
            for dx, c in enumerate(r):
                if c == "#":
                    px[y + dy][x + dx] = ink
        x += font_small.advance(ch)


def label(data, text):
    px = sprite_px(data)
    for y in range(4, 12):
        px[y][:30] = [1] * 30
    w = sum(font_small.advance(c) for c in text) - 1
    draw(px, text, (30 - w) // 2, 5, 0xD)
    return sprite_bytes(px)


SMALL_FONT = 0x310C58
EN_CODES_HIGH = {"'": 0x1F0, ":": 0x1F1, ";": 0x1F2, "%": 0x1F3, "&": 0x1F4, "*": 0x1F5, "#": 0x1F6}  # = engine.EN_CODES
TITLE_TILES = 0x31E878  # title screen: 8bpp tiles, map = row * 32 + col (tools/gen_title.py makes the PNG)
TITLE_PNG = Path(__file__).resolve().parents[1] / "assets/title_en.png"


def title_tiles():
    """{tile index: 64 bytes} for the 30x20 visible tiles of assets/title_en.png (palette indices as stored)."""
    from PIL import Image  # only the build needs Pillow here
    im = Image.open(TITLE_PNG)
    assert im.mode == "P" and im.size == (240, 160)
    px = im.load()
    return {r * 32 + c: bytes(px[c * 8 + x, r * 8 + y] for y in range(8) for x in range(8))
            for r in range(20) for c in range(30)}


def pair_tile(pair):
    """A two-letter code (tools/ligatures.py) as one 8x8 small-font cell: both compact letters, centred, with the
    1 px gap dropped for the few pairs (Ma, Mo, Me, Wa, om, mo) that would be 9 px."""
    w0, w1 = font_small.width(pair[0]), font_small.width(pair[1])
    gap = 1 if w0 + 1 + w1 <= 8 else 0
    px = [[3] * 8 for _ in range(8)]
    x = (8 - (w0 + gap + w1)) // 2
    for ch, dx in ((pair[0], x), (pair[1], x + w0 + gap)):
        for y, row in enumerate(font_small.ART[ch]):
            for i, c in enumerate(row):
                if c == "#":
                    px[font_small.TOP + y][dx + i] = 1
    return bytes(px[y][x] | px[y][x + 1] << 4 for y in range(8) for x in range(0, 8, 2))


def patch(r, pairs=None):
    for t, data in title_tiles().items():
        at = TITLE_TILES + t * 64
        if r.orig[at:at + 64] != data:
            r.put(at, data, f"title tile {t:#x}")
    for off, text in LABELS:
        r.put(off, label(r.orig[off:off + 0x200], text), f"battle label {text}")
    top, bottom = linking(r.orig)
    r.put(LINKING_TOP, top, "linking label")
    r.put(LINKING_BOTTOM, bottom, "linking label")
    # the game's 8x8 small font (0x08310C58, 512 glyphs, 256+ blank): punctuation the English font put at 0x1F0+
    import engine  # noqa: E402 (engine imports the assembler; gfx is otherwise standalone)
    # Granbo names in 8x8 mode (draw_menu_string's small glyphs: Data Ball grids, status) take one cell per code:
    # two-letter codes get both letters in their cell, and the Latin letters become the same compact design
    for ch, code in engine.EN_CODES.items():
        if ch.isalpha() and ch.isascii():
            r.put(SMALL_FONT + code * 32, font_small.tile(ch), f"small font {ch!r}")
    for p, code in (pairs or {}).items():
        r.put(SMALL_FONT + code * 32, pair_tile(p), f"small font pair {p!r}")
    for ch, code in EN_CODES_HIGH.items():
        assert engine.EN_CODES[ch] == code, ch
        at = SMALL_FONT + code * 32
        assert r.orig[at:at + 32] == b"\x33" * 32, hex(code)
        r.put(at, font_small.tile(ch), f"small font {ch!r}")
    for i, art in enumerate(ELEMENTS):
        top, bottom = element_icon(r.orig, art)
        for t, b in ELEM_COPIES:
            assert r.orig[t + 0x40 * i:t + 0x40 * i + 0x40] == r.orig[ELEM_TOP + 0x40 * i:ELEM_TOP + 0x40 * i + 0x40]
            r.put(t + 0x40 * i, top, f"element icon {i}")
            r.put(b + 0x40 * i, bottom, f"element icon {i}")
        at = ELEM_TILES4 + 0xA0 * i  # the Data Ball grids' copy: one icon = 4 tiles (top-left, top-right, bottom...)
        assert r.orig[at:at + 0x40] == r.orig[ELEM_TOP + 0x40 * i:ELEM_TOP + 0x40 * i + 0x40]
        r.put(at, top + bottom, f"element icon {i} (grid copy)")


# Element icons: 16x16 white circles with the element's kanji (火 水 木 闇; icon 4 is the empty circle), 2 tiles
# per half: top halves at ELEM_TOP + 0x40*i, bottoms at ELEM_BOTTOM + 0x40*i (graphics block 0x08571974 + 0x1400 /
# 0x1800, copied by 0x0806A3BC). Redrawn as pictograms (flame, drop, leaf, crescent) in the kanji's ink index 2 on
# the empty circle, so they need no reading.
ELEM_TOP, ELEM_BOTTOM = 0x572D74, 0x573174
ELEM_COPIES = [(ELEM_TOP, ELEM_BOTTOM), (0x57DE14, 0x57E214)]  # two graphics blocks hold the same sheet
ELEM_TILES4 = 0x77D3C8  # a third copy, 4 consecutive tiles per icon, 0xA0 apart
ELEMENTS = [
    ["....2.....", "...22.....", "...222.2..", "..2222.22.", "..22222222", ".222272222", ".222777222",
     ".227777722", "..2277722.", "...22222.."],
    ["....22....", "....22....", "...2222...", "...2222...", "..222222..", ".27222222.", ".27222222.",
     ".22722222.", "..222222..", "...2222..."],
    [".......222", ".....22222", "....222272", "...2222722", "..22227222", "..22272222", ".22272222.",
     ".2272222..", "..72222...", ".2........"],
    ["...2222...", "..222.....", ".222......", ".22.......", ".22.......", ".22.......", ".222......",
     "..222.....", "...2222...", ".........."],
]


LINKING_TOP, LINKING_BOTTOM = ELEM_TOP + 0x200 + 10 * 32, ELEM_TOP + 0x600 + 10 * 32  # 通信中: 3 tiles each


def linking(rom):
    """The link-cable 通信中 label (24x16, white 7 on 1) as "Linking": (top 3 tiles, bottom 3 tiles)."""
    px = [[1] * 24 for _ in range(16)]
    draw(px, "Linking", 0, 4, 7)
    top, bottom = sprite_bytes(px[:8], 3, 1), sprite_bytes(px[8:], 3, 1)
    return top, bottom


def element_icon(rom, art):
    """(top 0x40 bytes, bottom 0x40 bytes) of the empty circle (icon 4) with art stamped at (3, 3)."""
    px = sprite_px(rom[ELEM_TOP + 0x100:ELEM_TOP + 0x140] + rom[ELEM_BOTTOM + 0x100:ELEM_BOTTOM + 0x140], 2, 2)
    for y, row in enumerate(art):
        for x, c in enumerate(row):
            if c != ".":
                px[3 + y][3 + x] = int(c)
    data = sprite_bytes(px, 2, 2)
    return data[:0x40], data[0x40:]


def _check():
    blank = bytes(0x200)
    assert sprite_bytes(sprite_px(bytes(range(256)) * 2)) == bytes(range(256)) * 2
    assert all(sum(font_small.advance(c) for c in t) - 1 <= 30 for _, t in LABELS)
    assert label(blank, "Run") != blank


_check()
