import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import text  # noqa: E402

pytestmark = pytest.mark.skipif(not build.ROM.is_file(), reason="needs the original ROM in rom/")


@pytest.fixture(scope="module")
def orig():
    return build.ROM.read_bytes()


@pytest.fixture(scope="module")
def files():
    return build.load_script()


def test_roundtrip_every_entry(orig, files):
    """encode(jp) is byte-identical to the ROM at every entry (phase 4)."""
    bad = []
    for name, f in files.items():
        for e in f["entries"]:
            if name.startswith("events/"):
                b, t = int(f["block"], 16), int(f["table"], 16)
                at = b + 2 * struct.unpack_from("<H", orig, t + 2 * e["idx"][0])[0]
            else:
                at = int(e["at"], 16)
            enc = text.encode(e["jp"])
            if orig[at:at + len(enc)] != enc:
                bad.append(e["id"])
    assert not bad, bad[:20]


def test_identity_build(orig):
    """No translations -> the build is the original ROM (phase 3)."""
    empty = {n: {**f, "entries": [{**e, "en": ""} for e in f["entries"]]} for n, f in build.load_script().items()}
    assert build.build(orig, empty).finish() == orig


def test_marker_build_repoints(orig, files):
    """Marker build: every entry readable at its new home through its own pointers/table slots."""
    rom = build.build(orig, files, marker=build.MARKER).finish()
    for name, f in files.items():
        for e in f["entries"]:
            if name.startswith("events/"):
                lit = int(f["block_lits"][0], 16)
                b = struct.unpack_from("<I", rom, lit)[0] - build.GBA
                at = b + 2 * struct.unpack_from("<H", rom, int(f["table"], 16) + 2 * e["idx"][0])[0]
                assert text.decode(rom, at)[0] == build.MARKER(e), e["id"]
            else:
                for p in e["ptrs"]:
                    at = struct.unpack_from("<I", rom, int(p, 16))[0] - build.GBA
                    assert text.decode(rom, at)[0] == build.MARKER(e), e["id"]
