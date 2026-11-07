Blaze Union: Story to Reach the Future - English translation v{version}
Unofficial fan translation of the PSP game (Sting, 2010). All story, menus, items, skills,
battle text, tutorials, books, chapter cards and credits are in English.

WHAT YOU NEED
Your own dump of the Japanese game, as an ISO, matching exactly:
  Name:   Blaze Union - Story to Reach The Future (Japan).iso
  Size:   {base_size} bytes
  CRC32:  {base_crc32}
  MD5:    {base_md5}
  SHA-1:  {base_sha1}
No game data comes with this patch, and no patched images are shared. Please don't ask for them.

HOW TO PATCH
Use xdelta3, or a front end such as xdelta UI or Delta Patcher:
  xdelta3 -d -s "Blaze Union - Story to Reach The Future (Japan).iso" Blaze_Union_EN_v{version}.xdelta blaze_union_en.iso
Result:
  Size:   {patched_size} bytes
  CRC32:  {patched_crc32}
  SHA-1:  {patched_sha1}
The patched ISO is larger than the original (the English event scripts and graphics sit at
the end of the image); that is expected.

HOW TO PLAY
Tested in PPSSPP v1.20.4. The patched EBOOT is a plain ELF, so it runs on PPSSPP and on
custom firmware. Not tested on a real PSP.
Start a new game: this is a text and code patch, so emulator savestates from the Japanese
game won't work. Boot the game cold after patching. Memory card saves were not tested
across the patch.

KNOWN ISSUES
- Most battle events and many lists were read for width and meaning but never seen on screen
  by an automatic run, so a line may still overflow. Reports are welcome.
- Staff and cast names in the credits are read from kanji; only some are confirmed.
- A few long item, card and unit names are shortened to fit. Lines where a sexual remark
  targets a young or young-looking character are rewritten on purpose.
- The title logo's small katakana reading is kept as part of the logo.

REPORT A BUG
https://github.com/minhnhattonthat/blaze-union-story-to-reach-the-future-en/issues
A savestate or a screenshot helps most.

CREDITS
Translation, tools and QA: minhnhattonthat, with extensive AI assistance (Claude by Anthropic).
English font: Source Sans 3 (Adobe, SIL Open Font License 1.1).
Names follow the official English of Yggdra Union where the game's series has one.
Blaze Union is (c) Sting. This project is not affiliated with Sting or Atlus.
