import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "rom/0291 - Granbo (J)(Lord Moyne).gba"
sys.path.insert(0, str(ROOT / "tools"))

needs_rom = pytest.mark.skipif(not ROM.is_file(), reason="needs the original ROM in rom/")


@needs_rom
def test_rom_hash():
    import check_rom
    check_rom.check()


def test_table_has_every_glyph():
    import gen_tbl
    assert len(gen_tbl.lines()) == 1 + 512 + len(gen_tbl.CTRL)
    assert (ROOT / "tbl/jp.tbl").read_text(encoding="utf-8").splitlines() == gen_tbl.lines()


@needs_rom
def test_intro_line_decodes():
    import gen_tbl
    rom = ROM.read_bytes()
    codes = struct.unpack_from("<10H", rom, 0x27197A)
    assert "".join(gen_tbl.GLYPHS[c] for c in codes) == "どこかにかくれなきゃ"
