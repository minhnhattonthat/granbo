# Translator brief - Granbo menus, items, moves and system text (pointer strings)

You translate one batch of the game's non-dialogue strings: menu labels, item and move names and descriptions,
Granbo data, place names, Saver ranks, help pages, battle messages and the staff credits. Same game, tone and
glossary as the dialogue (read `docs/translator-brief.md` §Style once for the voice and naming rules).
Do all translation yourself; no subagents. Work only on the batch in your dispatch.

## Read first
1. `glossary.md` - binding names: Granbo species list, move tier rules (弱/中/強 -> 1/2/3, 様 -> EX, 全X -> Team X,
   ALL stays ALL), items, places, ranks. These strings are the names the dialogue already uses: match them exactly.
2. `work/tl/<batch>.terms.txt` - the glossary rows that occur in this batch.
3. When a name is not in the glossary, search the merged English for it first:
   `grep -h -o '"en": "[^"]*WORD[^"]*' script/events/*.json | head` (or grep the `jp` field for the Japanese).

## Input: `work/tl/<batch>.tsv`
`id<TAB>group<TAB>form<TAB>limit<TAB>Japanese`, in ROM order (neighbours are usually related: a move's name, then its
description, then its short battle description; a Granbo's name, then its two descriptions).
- ` / ` in the Japanese is a line break. Keep exactly the same number of lines; this text is NOT re-wrapped.
- `limit` is the maximum pixel width of each line (`120/96px` = line 1 at most 120 px, line 2 at most 96 px). The
  English font averages ~5.5 px a letter (i, l, ' are 2 px; m, w are 6-8 px; space 3 px). The check measures it.
- `form` = `text` or `padded`. `padded`: the Japanese lines up columns with runs of spaces (menus with choices, two
  short descriptions on one line). Keep every control code and keep the runs of spaces between the parts (you may
  shorten or lengthen a run so the parts still line up roughly); no width check is made on these.
- `group` = the source table (t290574 = items/moves/Granbo data, t1A1568 = battle dialogue, code = menus and system
  messages, t294A08 = help pages, r290000 = Data Pad commands and staff credits, t1AA48C = place names,
  t2946A8 = ranks and tournaments).

## Output: `work/tl/<batch>.out.tsv` (your file-write tool, not a shell heredoc)
`id<TAB>English`, every input id exactly once, in order. Plain ASCII. Write ` / ` where the Japanese has one.

## Rules
- Copy every `{XXXX}` code exactly, same count, sensible position. `{8300}` (new box) and `{82xx}` (new line) count
  as codes here: keep them where they are.
- Names (items, moves, Granbo, places) are title case and short: they sit in menu fields. Prefer the established
  form even when a longer one reads better. Tiers: 弱/中/強 on moves -> 1/2/3 ("Virus Claw 2"); 小/中/大 on items
  and on HP回復 moves -> S/M/L for items ("HP Capsule S"), 1/2/3 for moves ("HP Heal 2", as the dialogue uses).
- Descriptions: plain, short sentences; no ending period on one-line menu descriptions unless the JP has 。.
- Staff credits: romanise Japanese names in Western order, given name first, Hepburn without macrons
  ("まつした くにおみ" -> "Kuniomi Matsushita"); job titles in English.
- Debug/dummy strings (ダミー, ワーク, 未使用, test labels): translate literally and short.

## Validate
`python -X utf8 tools/ptrbatches.py check <batch>` until it prints OK.

## Report (reply with only this)
File written and entry count; then `NEW TERM: jp -> en`, `UNSURE: id - note`, `LONG: id - note` (a line you could
not fit without losing meaning: keep the meaning and report it).
