"""bisect_entries.py: find the translated entry that breaks a warp scene (binary search over one script file).

    python -X utf8 tools/bisect_entries.py ptr/code.json battle
Builds the ROM with only part of FILE's translations (everything else keeps its English), runs the warp, and
narrows down to the entries whose English makes the scene fail (emu.py exit != 0). Prints the culprit ids.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/Nathan/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game")


def run(files, scene, tag):
    out = ROOT / f"build/bisect_{tag}.gba"
    out.write_bytes(build.build(build.ROM.read_bytes(), files).finish())
    r = subprocess.run([sys.executable, "-X", "utf8", str(SKILL / "scripts/emu.py"), str(out), "--out",
                        str(ROOT / f"work/qa/bisect_{tag}"), "--script", str(ROOT / "tools/debug/warp.lua"),
                        "--var", f"SCENE='{scene}'", "--frames", "900"], capture_output=True, text=True)
    return r.returncode == 0


def main(fname, scene):
    files = build.load_script()
    ids = [e["id"] for e in files[fname]["entries"] if e.get("en")]

    def with_only(keep):
        f = dict(files)
        f[fname] = {**files[fname], "entries": [{**e, "en": e.get("en", "") if e["id"] in keep else ""}
                                                for e in files[fname]["entries"]]}
        return f

    cand = ids
    while len(cand) > 1:
        half = cand[:len(cand) // 2]
        ok = run(with_only(set(half)), scene, "a")
        cand = half if not ok else cand[len(cand) // 2:]
        print(f"{len(cand)} candidates left", flush=True)
    print("culprit:", cand)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
