# Reviewer brief - Granbo pointer strings (menus, items, moves, Granbo data, battle and system text)

You review part of the English draft of the game's non-dialogue strings. Read `docs/reviewer-brief.md` first: the
same purpose, priorities and "leave alone" rule apply, as do the output files and report format. Then read
`docs/ptr-brief.md` for how these strings work (no re-wrapping, ` / ` line breaks, pixel limits, `padded` form,
groups, naming rules). Work only on the batch in your dispatch; no subagents; edit no file but your two outputs.

## Input: `work/tl/<batch>.tsv`
`id<TAB>group<TAB>form<TAB>limit<TAB>Japanese<TAB>current English`, in ROM order (a move's name, then its
description, then its short battle description; a Granbo's name, then its descriptions).

## Look for, in this order
1. Mistranslation: wrong item/move effect, number, target ("self" vs "team" vs "all foes"), element, stat.
2. Names that differ from `glossary.md` or from the same name elsewhere in your batch (moves, items, Granbo,
   places, ranks). Tiers 1/2/3 and EX; 全X -> Team X; ALL stays ALL.
3. English errors and stray spaces. A leading space is right only for a tail the game prints after a name or
   number (the Japanese starts with a particle like を/が/は and is clearly a sentence ending: "をおあずかりしました"
   -> " deposited."); move or item names never start with one.
4. Battle dialogue (group t1A1568) follows the dialogue voices in `docs/reviewer-brief.md`.
Keep every line within its `limit` (the check measures it) and the same number of ` / ` as the Japanese.

## Output and check
`work/tl/<batch>.out.tsv` (every id, unchanged lines copied exactly) and `work/tl/<batch>.notes.txt` (one line per
changed id), then `python -X utf8 tools/ptrbatches.py check <batch>` until it prints OK.
