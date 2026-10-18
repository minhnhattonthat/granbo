"""names.py: speaker names for batch context and the inline NPC labels the merge fills in (glossary.md)."""
import re

# name slot k ({94xx}: speaker xx-0x96, inline xx < 0x1E); slot 0 = the player's name
SLOTS = ["(player)", "Akari", "Daigoro", "Shizuku", "Kazuki", "Grazie", "Captain", "Baltic", "Aegean", "Bermuda",
         "Granbo", "Chief", "Nurse", "Haruna", "Granbo", "Grunt", "Bermuda", "Old Gen", "Grazio", "Grunt 3", "Grunt 4",
         "Grunt 5", "Grunt 6", "Grunt 7"]

# {94C8}LABEL「 inline speaker labels, JP -> EN (<= 46 px, checked by tests/test_lint.py)
SPEAKERS = {
    "女の子": "Girl", "男の子": "Boy", "おじさん": "Man", "少年セイバー": "Kid Saver", "おじいさん": "Old Man",
    "おばあさん": "Old Lady", "おばさん": "Lady", "元セイバー": "Ex-Saver", "少女セイバー": "Gal Saver",
    "しかいしゃ": "Emcee", "大人セイバー": "Saver", "オーナー": "Owner", "店長": "Manager", "かいさついん": "Gatekeep",
    "かかりいん": "Staff", "ならず者": "Thug", "じいさん": "Gramps", "お姉さん": "Miss", "ヒゲじい": "Beardy",
    "ばあさん町長": "Mayor", "こども": "Kid", "システム": "System", "町長": "Mayor", "おかみ": "Landlady", "老人": "Elder",
    "おっちゃん": "Mister", "ダイゴロウ父": "Dad", "てんいん": "Clerk", "とりまき男": "Groupie", "とりまき女": "Groupie",
    "客の男": "Guest", "コック": "Cook", "おばちゃん": "Auntie", "子ども": "Kid", "けいびいん": "Guard",
    "店長の子ども": "Kid", "？？？？？？": "???", "ダイゴロウ母": "Mom", "元ならず者": "Ex-Thug", "ギャル": "Gal",
    "大人": "Adult", "ばあさん村長": "Chief", "うけつけ": "Desk", "おじちゃん": "Uncle", "セイバー": "Saver",
    "とりまき達": "Groupies", "男の声": "Voice", "チロ": "Chiro", "パイロット": "Pilot", "男の人": "Man",
    "へんそう子分": "Grunt", "子分店長": "Grunt", "お兄さん": "Lad", "女の声": "Voice", "グランボ": "Granbo",
    "大人の声": "Voice",
}
INLINE = re.compile(r"(\{94(?:C[89A-F]|[D-F][0-9A-F])\})([^{「]*)((?:\{[0-9A-F]{4}\})*)「")  # label, codes, 「


def speaker(page_header):
    """Readable speaker for a page header, for translator context."""
    m = INLINE.search(page_header)
    if m:
        return SPEAKERS.get(m.group(2), m.group(2))
    m = re.search(r"\{94([0-9A-F]{2})\}", page_header)
    if m and int(m.group(1), 16) >= 0x96:
        k = int(m.group(1), 16) - 0x96
        return SLOTS[k] if k < len(SLOTS) else f"slot{k}"
    return "-"


def english_header(h):
    """Page header with an inline JP label replaced by its English label."""
    return INLINE.sub(lambda m: m.group(1) + SPEAKERS[m.group(2)] + m.group(3) + "「", h)
