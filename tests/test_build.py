import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import find_rel  # noqa: E402
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
    assert build.build(orig, empty, engine_patch=False).finish() == orig


def test_rel_strings_follow_their_base(orig, files):
    """Strings code reaches as base + offset (find_rel) all have entries, and in the marker build base + new offset
    lands on the child's marker text."""
    ents = [e for n, f in files.items() if n.startswith("ptr/") for e in f["entries"]]
    by_at, by_id = {int(e["at"], 16): e for e in ents}, {e["id"]: e for e in ents}
    rels = find_rel.relations(orig, ents)
    assert not [hex(t) for t, *_ in rels if t not in by_at]
    rom = build.build(orig, files, marker=build.MARKER).finish()
    for t, b, kind, site in rels:
        base = struct.unpack_from("<I", rom, int(by_id[b]["ptrs"][0], 16))[0] - build.GBA
        hw = struct.unpack_from("<H", rom, site)[0]
        off = {"adds": hw & 0xFF, "neg": -(hw & 0xFF), "word": struct.unpack_from("<i", rom, site)[0]}[kind]
        want = text.encode_en(build.MARKER(by_at[t]))
        assert rom[base + off:base + off + len(want)] == want, (by_at[t]["id"], b, hex(site))


def test_marker_build_repoints(orig, files):
    """Marker build: every entry readable at its new home through its own pointers/table slots."""
    rom = build.build(orig, files, marker=build.MARKER).finish()
    for name, f in files.items():
        for e in f["entries"]:
            want = text.encode_en(build.MARKER(e))
            if name.startswith("events/"):
                lit = int(f["block_lits"][0], 16)
                b = struct.unpack_from("<I", rom, lit)[0] - build.GBA
                ats = [b + 2 * struct.unpack_from("<H", rom, int(f["table"], 16) + 2 * i)[0] for i in e["idx"]]
            else:
                ats = [struct.unpack_from("<I", rom, int(p, 16))[0] - build.GBA for p in e["ptrs"]]
            for at in ats:
                assert rom[at:at + len(want)] == want, e["id"]
