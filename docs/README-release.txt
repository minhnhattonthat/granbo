Granbo - English translation patch v{version}
=============================================

{preview}An unofficial fan translation of Granbo (Capcom, 2001, Game Boy Advance) into English.
This archive holds only the patch. No ROM is included or will be provided.

Applying the patch
------------------
Patch file: {patch} (BPS format). Use Floating IPS (flips), beat, or the online Rom Patcher JS.
Apply it to this exact dump of the Japanese cartridge:

  Granbo (Japan)
  Size:   {orig[size]} bytes
  CRC32:  {orig[crc32]}
  MD5:    {orig[md5]}
  SHA-1:  {orig[sha1]}

The patched ROM should have:

  Size:   {built[size]} bytes
  CRC32:  {built[crc32]}
  SHA-1:  {built[sha1]}

The patcher refuses a different dump. Start a new game or load a save made with this patch; savestates from the
Japanese game carry the old text code and will show garbled text.

What is translated
------------------
All story dialogue, menus, items, moves, Granbo data, battle text, help pages, staff credits, the name-entry
keyboard, the title logo, battle command labels and the element icons. The text uses a new variable-width font.

Tested in: MesenCE 2.2.1 (cold boot, headless scripted runs through every map variant and the menus).

Known issues
------------
- Link-cable features (trading, link battles) could not be tested.
- The battle command for transforming reads "Morph" on its small label; menus call it "Transform".

Credits
-------
Translation, font, graphics and engine work: prepared with AI assistance (Claude by Anthropic), directed by the
patch author. Granbo is (c) Capcom. This patch is a non-commercial fan work and is not affiliated with Capcom.
