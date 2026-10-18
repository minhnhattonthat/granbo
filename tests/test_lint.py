import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402
import fit  # noqa: E402
import lint  # noqa: E402


def test_every_translation_passes_lint():
    bad = []
    for name, f in build.load_script().items():
        kind = "event" if name.startswith("events/") else "ptr"
        for e in f["entries"]:
            for msg in lint.issues(e, kind):
                bad.append(f"{e['id']}: {msg}")
    assert not bad, f"{len(bad)} lint errors:\n" + "\n".join(bad[:40])


def test_fit_wraps_and_paginates():
    jp = "{8002}{8620}{94A7}「あ」{8300}{8620}{94A7}「い{8207}う」{8400}{8100}"
    en = "{8002}{8620}{94A7}Short.{8300}{8620}{94A7}" + "word " * 60 + "end.{8400}{8100}"
    f = fit.fit(en, jp)
    assert not fit.problems(f)
    assert f.count("{8300}") >= 2 and f.endswith("{8400}{8100}")
    assert all(p.startswith("{8620}{94A7}") for p in f.split("{8300}")[1:])


def test_fit_prompt_line_keeps_jp_newline():
    # an indented prompt line overran the canvas and crashed the game (ev1BC98C_012)
    jp = "{8001}{94C8}店長「では{8207}セツメイしておこうかの？」{9200}\n{8D00}{8100}"
    en = "{8001}{94C8}Manager「Now then... shall I explain about Granbo first?{9200}{8D00}{8100}"
    assert fit.fit(en, jp).endswith("{9200}\n{8D00}{8100}")
    # the JP's empty line before the prompt is kept, so Yes/No stays on line 3 (ev1BC98C_018)
    jp = "{8001}{94C8}店長「わかったかの？」{9200}{8207}\n{8D00}{8100}"
    en = "{8001}{94C8}Manager「Got all that?{9200}{8D00}{8100}"
    assert fit.fit(en, jp).endswith("{9200}{8207}\n{8D00}{8100}")


def test_lint_catches_code_mismatch():
    e = {"id": "x", "jp": "{8002}{94A7}「あ」{8400}{8100}", "en": "{8002}Hi{8400}{8100}"}
    assert any("control codes" in m for m in lint.issues(e, "event"))
