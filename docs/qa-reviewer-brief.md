# Visual QA brief - Granbo English build

You judge contact sheets (PNG grids of emulator screenshots) of the English build. Read-only: change no file except
your verdict file. No subagents.

## For each sheet in your list
Read it (zoom in on text with an image crop if it is small). Look only for these problems:
- Japanese still visible (kana, kanji) anywhere: text boxes, menus, signs drawn as graphics, labels.
- Text running past a box or frame edge, clipped letters, two texts drawn over each other.
- Garbage: wrong glyphs, stray tiles or blocks, letters from another string, kana inside English words.
- Broken layout: a line break in the middle of a word, an empty box where text should be, misaligned columns.
- English that is plainly broken on screen (a word cut off, a name code shown raw like {9400}).
Normal, not issues: a page caught mid-typing (partial line), black or fading frames, field screens without text,
the same page twice, a speaker name in colour before the text, dialogue lines after the first starting further
right (they start at the text column beside the portrait).

## Output
Write `work/qa/verdicts/<your chunk name>.tsv` with your file-write tool, one line per sheet in your list:
`id<TAB>ok|issue<TAB>note` - for an issue, say which frame (row/column in the grid) and what is wrong, quoting the
visible text. Reply with only: sheets judged, number of issues, and one line per issue.
