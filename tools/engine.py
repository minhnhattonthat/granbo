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
