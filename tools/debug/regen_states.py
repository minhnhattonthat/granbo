"""Warp to every scene in tools/debug/scenes.lua from a cold boot and save work/states/<scene>.mss.

    python -X utf8 tools/debug/regen_states.py [ROM] [--only town,battle] [--jobs 3]

ROM defaults to the original dump (rom/*.gba). Each scene's shots and contact sheet land in work/qa/warp_<scene>/.
Scenes marked `manual = true` (they need --var arguments) are skipped. Exit 1 if any scene failed.
Run from the repo root. Regenerate after any code, font or graphics change: states keep the old VRAM and code.
"""
import argparse
import glob
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

SKILL = os.environ.get("SKILL", "C:/Users/Nathan/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game")
EMU = os.path.join(SKILL, "scripts", "emu.py")
HERE = os.path.dirname(os.path.abspath(__file__))


def scene_names(path):
    names = []
    for line in open(path, encoding="utf-8"):
        m = re.match(r"S\.(\w+)\s*=\s*\{", line)
        if m and "manual = true" not in line:
            names.append(m.group(1))
    return names


def run(rom, scene):
    out = f"work/qa/warp_{scene}"
    cmd = [sys.executable, "-X", "utf8", EMU, rom, "--out", out, "--script", os.path.join(HERE, "warp.lua"),
           "--var", f"SCENE='{scene}'", "--frames", "900", "--sheet", "--state-out", f"work/states/{scene}.mss"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = os.path.join(out, "log.txt")
    reached = os.path.exists(log) and "reached at frame" in open(log, encoding="utf-8").read()
    ok = p.returncode == 0 and reached and os.path.exists(f"work/states/{scene}.mss")
    lines = (p.stdout + p.stderr).strip().splitlines()
    return scene, ok, f"{out}/sheet.png" if ok else " | ".join(lines[-2:])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?")
    ap.add_argument("--only", help="comma-separated scene names")
    ap.add_argument("--jobs", type=int, default=3)
    a = ap.parse_args()
    rom = a.rom or (sorted(glob.glob("rom/*.gba")) or [None])[0]
    if not rom:
        sys.exit("no ROM given and none in rom/")
    names = scene_names(os.path.join(HERE, "scenes.lua"))
    assert names, "no scenes parsed from scenes.lua"
    if a.only:
        want = a.only.split(",")
        unknown = set(want) - set(names)
        if unknown:
            sys.exit(f"unknown scene(s): {', '.join(sorted(unknown))}")
        names = want
    os.makedirs("work/states", exist_ok=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        results = list(ex.map(lambda n: run(rom, n), names))
    for scene, ok, info in results:
        print(f"{'ok  ' if ok else 'FAIL'} {scene:14} {info}")
    sys.exit(0 if all(ok for _, ok, _ in results) else 1)


if __name__ == "__main__":
    main()
