"""Map tour for visual QA: warp to every map variant from a cold boot and A-mash through whatever runs there.

    python -X utf8 tools/debug/map_tour.py [ROM] [--jobs 4] [--only 1/7,2/1] [--mash 60]

ROM defaults to build/granbo_en.gba. Variants come from the map table (ROM 0x081AC4F4, docs/re/debug.md); unused
maps are skipped. Each run: the `map` scene at the variant's spawn, then --mash rounds of "6 a; 24 -" (pages through
dialogue, talks to whoever stands in front), a shot every 45 frames, and a contact sheet of the frames that changed:
work/qa/tour/map_MM_VV.png (the tour dir that tools' qa_gate.py init reads). Exit 1 lists variants that were not
reached (some need story flags; their sheets still show what loaded).
"""
import argparse
import os
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regen_states import EMU, HERE, SKILL  # noqa: E402

UNUSED = {9, 14, 15, 20, 21, 42, 43, 44, 52}  # "NO USE" debug names
SHEET = os.path.join(SKILL, "scripts", "sheet.py")


def variants(rom):
    out = []
    for m in range(68):
        vp = struct.unpack_from("<I", rom, 0x1AC4F4 + m * 28 + 8)[0]
        if m in UNUSED or not 0x08000000 <= vp < 0x08800000:
            continue
        o, v = vp - 0x08000000, 0
        while rom[o + 12 * v] != 0xFF and 0x08000000 <= struct.unpack_from("<I", rom, o + 12 * v + 4)[0] < 0x08800000:
            out.append((m, v))
            v += 1
    return out


def run(rom, m, v, mash):
    out = f"work/qa/maps/{m:02d}_{v:02d}"
    shutil.rmtree(out, ignore_errors=True)
    after = ";".join(["6 a;24 -"] * mash)
    cmd = [sys.executable, "-X", "utf8", EMU, rom, "--out", out, "--script", os.path.join(HERE, "warp.lua"),
           "--var", "SCENE='map'", "--var", f"MAP={m}", "--var", f"VAR={v}", "--var", f"AFTER='{after}'",
           "--var", "HOLD=60", "--var", "WARP_TIMEOUT=3000", "--var", "NOENC=true", "--frames", "900",
           "--shot-every", "45"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = os.path.join(out, "log.txt")
    reached = os.path.exists(log) and "reached at frame" in open(log, encoding="utf-8").read()
    os.makedirs("work/qa/tour", exist_ok=True)
    start = 0
    if reached:
        start = int(open(log, encoding="utf-8").read().split("scene map at frame")[1].split()[0])  # arrival
    s = subprocess.run([sys.executable, "-X", "utf8", SHEET, out, "--changed", "0.02", "--from", str(start), "--div",
                        "1", "--cols", "3", "--max", "24", "--out", f"work/qa/tour/map_{m:02d}_{v:02d}.png"],
                       capture_output=True, text=True)
    return m, v, reached and p.returncode == 0, s.returncode == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", default="build/granbo_en.gba")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", help="comma-separated map/variant pairs, e.g. 1/7,2/1")
    ap.add_argument("--mash", type=int, default=60, help="A presses after arrival (30 frames each)")
    a = ap.parse_args()
    rom = open(a.rom, "rb").read()
    todo = variants(rom)
    if a.only:
        todo = [tuple(map(int, p.split("/"))) for p in a.only.split(",")]
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda mv: run(a.rom, *mv, a.mash), todo))
    bad = [f"{m}/{v}" for m, v, ok, _ in res if not ok]
    print(f"{len(res) - len(bad)}/{len(res)} reached; sheets in work/qa/tour/")
    if bad:
        print("not reached:", " ".join(bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
