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


def patch(r):
    for off, text in LABELS:
        r.put(off, label(r.orig[off:off + 0x200], text), f"battle label {text}")


def _check():
    blank = bytes(0x200)
    assert sprite_bytes(sprite_px(bytes(range(256)) * 2)) == bytes(range(256)) * 2
    assert all(sum(font_small.advance(c) for c in t) - 1 <= 30 for _, t in LABELS)
    assert label(blank, "Run") != blank


_check()
