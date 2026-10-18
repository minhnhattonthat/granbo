# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 - release candidate v1.0 built locally (`release/Granbo_EN_v1.0.zip`, patched CRC32 4F834541):
  build, tests, jp_left, visual QA gate (419 sheets: 396 map variants + warp scenes, `work/qa/verdicts/`), smoke
  and BPS re-apply all pass. Not published: that is the user's call.
- **Done:**
  - Recon, extraction, build with relocation, roundtrip/identity/marker tests; debug warp tool (21 scenes,
    `docs/re/debug.md`, `tools/debug/regen_states.py`); map tour of every map variant (`tools/debug/map_tour.py`,
    sheets in `work/qa/tour/`).
  - All text translated and reviewed: 4117 event messages (review pass 1, `tools/review.py split`, 122 fixes) and
    ~3290 pointer strings (review pass 2, `split-ptr`, 240 fixes). Briefs: `docs/reviewer-brief.md`,
    `docs/ptr-reviewer-brief.md`.
  - Engine (`tools/engine.py`, `asm/`): proportional font + VWF in the message window (`vwf.s`; a run-start space
    keeps 8 px for the choice cursor), draw_menu_string (`vwf_menu.s`; name fields drawn to their 6-cell end via
    `asm/name6.s`), the typewriter window, the fixed-cell routine; two-letter glyphs for Granbo names; battle HUD
    names (`asm/hud_name.s`, compact font `tools/font_small.py`); skills list without the per-row cost and an
    uncut description line (`asm/pad_col.s`); column moves on status/card/save; English name-entry keyboard.
  - Base+offset strings (docs/re/text.md): `tools/find_rel.py` traces them (adds/subs/word/neg); the build places
    each group and rewrites the offsets; a test fails if a derived string has no entry.
  - Graphics (`tools/gfx.py`, docs/re/graphics.md): title logo (`tools/gen_title.py` -> `assets/title_en.png`),
    battle command labels, element pictograms, 通信中 -> Linking, small-font punctuation.
  - Title redesign: custom angular GRANBO lettering, silver bevels and indigo extrusion; original 240x160
    indexed palette and 600-tile budget retained. Regeneration is byte-identical; 10 tests, build and cold-boot
    smoke pass; independent visual review and `title_logo_manifest.tsv` QA gate pass (1 sheet).
    Before: `work/qa/title_logo_before/final.png`; after: `work/qa/title_logo/final.png`.
    The local build includes this redesign; the existing v1.0 release archive predates it.
  - Playtest fixes: Yes/No prompt line keeps the JP newline (an {8207} one pushed "No" past the canvas at
    0x03000CC0 into game state 0x03002320: crash at ev1BC98C_012); speaker text starts at x=64 on every line
    (D8: 「 tabs there in vwf.s, fit adds it after RAM-slot names); GAP drawn opaque so the choice cursor erases.
  - Release tooling: `tools/release.py <ver>` (build, tests, jp_left with `docs/jp_known.txt`, qa_gate, smoke, BPS,
    README from `docs/README-release.txt`, zip in release/; never publishes).
  - QA-pass fixes: battle dialogue clears the portrait (`build.clear_portrait`), battle move popup 12 cells in a
    14-wide box, small-font pair glyphs (Data Ball grids), element icon copies, fit width fixes for name codes.
- **Next (after user playtesting):**
  - Unverified screens (no warp scene): the second status page (0x0808AF70, icons moved to x=160), storage /
    Data Ball / shop prompts added by find_rel (ID_PX limits in ptrbatches are their current widths), link-battle
    screens (Record W/L composite with 1-cell W/L, FLAGGED), intro subtitles (s27196A.., new-game opening).
  - Reviewer notes left open: shop prompts keep a double space before {8E03} (menu placement, check on screen);
    some move short descriptions keep JP column spaces; "Team X" for 全X moves that hit all foes (glossary rule);
    `{940E}`/`{940F}` name codes unknown (Bermuda lines ev240336_019, ev2407DE_003, ev2082EE_022).
  - FLAGGED: tournament list titles "X Cup" vs dialogue "X Saver Tournament"; battle label ヘンシン = "Morph".
- **Choices made without the user (pre-approved autonomy, D6) that they may want to revisit:** skills list drops
  the per-row EN cost (shown in the description box); element kanji became pictograms; name-entry pages are
  ABC / 123 / A-Z; the title logo is new "GRANBO" lettering over a reconstructed egg.
- **Waiting on the user:** nothing.
