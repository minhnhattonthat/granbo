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


def patch(r):
    for t, data in title_tiles().items():
        at = TITLE_TILES + t * 64
        if r.orig[at:at + 64] != data:
            r.put(at, data, f"title tile {t:#x}")
    for off, text in LABELS:
        r.put(off, label(r.orig[off:off + 0x200], text), f"battle label {text}")
    for i, art in enumerate(ELEMENTS):
        top, bottom = element_icon(r.orig, art)
        r.put(ELEM_TOP + 0x40 * i, top, f"element icon {i}")
        r.put(ELEM_BOTTOM + 0x40 * i, bottom, f"element icon {i}")


# Element icons: 16x16 white circles with the element's kanji (火 水 木 闇; icon 4 is the empty circle), 2 tiles
# per half: top halves at ELEM_TOP + 0x40*i, bottoms at ELEM_BOTTOM + 0x40*i (graphics block 0x08571974 + 0x1400 /
# 0x1800, copied by 0x0806A3BC). Redrawn as pictograms (flame, drop, leaf, crescent) in the kanji's ink index 2 on
# the empty circle, so they need no reading.
ELEM_TOP, ELEM_BOTTOM = 0x572D74, 0x573174
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
