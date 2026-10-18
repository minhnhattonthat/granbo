"""release.py: build, gate and package the English patch (never uploads anything; publishing is the user's call).

    python -X utf8 tools/release.py 1.0 [--allow-open-qa]

Steps, each fatal on failure:
1. check the dump (rom.sha1) and build build/granbo_en.gba;
2. tests (tools/check.py); leftover-Japanese scan (jp_left.py, docs/jp_known.txt lists the checked noise);
3. visual QA gate (qa_gate.py check work/qa/manifest.tsv work/qa/verdicts); --allow-open-qa skips it for a test
   package only and marks the README as a preview;
4. smoke boot of the build (emu.py --smoke);
5. BPS patch (bps.py make re-applies it and compares) -> release/Granbo_EN_v<ver>.bps, README.txt with the hashes,
   release/Granbo_EN_v<ver>.zip holding the patch and README only.
"""
import argparse
import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_rom  # noqa: E402
from debug.regen_states import SKILL  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "rom/0291 - Granbo (J)(Lord Moyne).gba"
BUILT = ROOT / "build/granbo_en.gba"
SCRIPTS = Path(SKILL) / "scripts"


def step(name, cmd):
    print(f"== {name}")
    p = subprocess.run([sys.executable, "-X", "utf8", *map(str, cmd)], cwd=ROOT)
    if p.returncode:
        sys.exit(f"{name} failed (exit {p.returncode}): not released")


def hashes(path):
    data = path.read_bytes()
    return {"size": len(data), "crc32": f"{zlib.crc32(data):08X}", "md5": hashlib.md5(data).hexdigest(),
            "sha1": hashlib.sha1(data).hexdigest()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("version")
    ap.add_argument("--allow-open-qa", action="store_true", help="skip the visual QA gate (preview package)")
    a = ap.parse_args()
    check_rom.check()
    step("build", [ROOT / "tools/build.py"])
    step("tests", [ROOT / "tools/check.py"])
    step("leftover Japanese", [SCRIPTS / "jp_left.py", BUILT, "--orig", ORIG, "--tbl", ROOT / "tbl/jp.tbl", "--le16",
                               "--gba-ptrs", "--min", "3", "--known", ROOT / "docs/jp_known.txt"])
    if not a.allow_open_qa:
        step("visual QA gate", [SCRIPTS / "qa_gate.py", "check", ROOT / "work/qa/manifest.tsv",
                                ROOT / "work/qa/verdicts"])
    step("smoke boot", [SCRIPTS / "emu.py", BUILT, "--out", ROOT / "work/qa/release_smoke", "--route",
                        ROOT / "tools/routes/boot.txt", "--smoke"])
    out = ROOT / "release"
    out.mkdir(exist_ok=True)
    stem = f"Granbo_EN_v{a.version}"
    bps = out / f"{stem}.bps"
    step("patch", [SCRIPTS / "bps.py", "make", ORIG, BUILT, bps])
    o, b = hashes(ORIG), hashes(BUILT)
    readme = (ROOT / "docs/README-release.txt").read_text(encoding="utf-8").format(
        version=a.version, patch=bps.name, orig=o, built=b,
        preview="PREVIEW BUILD: visual QA not complete.\n\n" if a.allow_open_qa else "")
    (out / "README.txt").write_text(readme, encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(out / f"{stem}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(bps, bps.name)
        z.write(out / "README.txt", "README.txt")
    print(f"release/{stem}.zip: {bps.name} + README.txt (patched CRC32 {b['crc32']}). Not published.")


if __name__ == "__main__":
    main()
