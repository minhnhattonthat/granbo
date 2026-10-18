# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6 (translation) finishing; 5 (engine) open for per-screen fields; 8 (QA) not started.
- **Done:**
  - Recon, extraction, build with relocation, roundtrip/identity/marker tests; debug warp tool (20 scenes,
    `docs/re/debug.md`).
  - Engine: English proportional font; VWF in the message window (`asm/vwf.s`), in draw_menu_string
    (`asm/vwf_menu.s`: lazy cell allocation, columns after a space run snap to the monospace column) and in the
    fixed-cell routine 0x0800F9B0 8x16 mode (`asm/vwf_cells.s`); speaker-name loops widened.
  - Event script: all 54 batches merged (every message with text). Pointer strings: p000-p019 merged
    (`tools/ptrbatches.py`, `docs/ptr-brief.md`); p020-p025 running; p026-p030 to dispatch.
- **Next:**
  - Merge p020-p030. Then screen QA with the warp scenes and fix per screen:
    - skills list: name field ~52 px before the "E 4" cost (drawn by 0x0806A47C into its own tiles; row text
      composed by 0x0804B71C, drawn at x=40): move the cost right or widen the field; many move names are wider.
    - status screen: labels (こうげき/ぼうぎょ/すばやさ -> 32 px before the AT./DF./SP. icons) overrun; evolution EXP
      label garbled.
    - Data Pad help bar ("Granbo commands") still monospace: another draw routine.
    - shop/item lists: check names vs the price/count column; 所持数 label shows as "y".
    - battle message lines: 12 merged lines over the box width (list: run `ptrbatches.issues` over t1A1568).
    - padded choice menus (278 strings): check alignment after the column snap.
    - p002/p005/p006 battle lines were over-trimmed under an older check: restore fuller wording.
  - Graphics: title logo (グランボ), name-entry grid (kana -> letters), battle UI labels (コウゲキ etc.), 8x8 small
    font glyphs for ' : ; % & * # (kanji slots 0x1F0+), anything else the survey finds.
  - Review pass (reviewer agents) on events; whole-project sampled review; polish pass (Minors, term consistency:
    Grazie's identity/voice, "Bata" vs "Hop!" cry, Message Board capitalisation).
  - Release: BPS patch, README, jp_left scan, qa_gate.
- **Open bugs:** see the per-screen list above.
- **Waiting on the user:** nothing.
