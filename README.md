# Blaze Union: Story to Reach the Future English translation

Unofficial English fan translation of **Blaze Union: Story to Reach the Future** (PSP, Sting, 2010): the source text and tools
that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue and story, all routes and endings | Translated |
| Menus, items, skills, cards, battle text, system messages | Translated |
| Title screen, chapter cards, banners, tutorial slides, graphics with text | Translated (the logo's small katakana reading stays, as part of the logo) |
| Name entry | None in the game |
| Voices, credits | Voices stay Japanese; credits are translated, staff names romanised |

Known issues: see [Issues](../../issues). Base dump: `Blaze Union - Story to Reach The Future (Japan).iso`, 582,221,824 bytes,
CRC32 8F901A9F, MD5 6a759f27b03f1133d6cd2c0818f954fa, SHA-1 de0e837fb23e4db73afa3fcaf84e71ac8030fac8.

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.claude/agents/` | Subagent types (translator, reviewer, visual QA, playtester) with only the tools each needs. |

## Build your own patched ISO

Needs Python 3.12+, PPSSPP (any recent version), xdelta3 for the release step, and your own dumps of two games:

- Blaze Union (Japan): the game being patched.
- Yggdra Union - We'll Never Fight Alone (USA): same engine; some sprites are copied from its official English.

`tools/check_rom.py` checks all three files below against `rom.sha1`, and the build refuses to run until they match.

The patched EBOOT is built from the game's decrypted EBOOT, which PPSSPP writes out for you:

1. Close PPSSPP. In its `PSP/SYSTEM/ppsspp.ini` (Windows: the `memstick` folder beside the exe, or
   Documents\PPSSPP; Linux: `~/.config/ppsspp`), add `DumpFileTypes = 7` under `[General]`.
2. Boot the Japanese ISO and wait for the title screen, then quit.
3. Copy `PSP/SYSTEM/DUMP/ULJM05503_EBOOT.BIN` to `work/exe/EBOOT.dump.bin` in this repo
   (3,545,728 bytes, SHA-1 8788cf63723f84e8b067bbb9c5f0ab33650602d4). Remove the `DumpFileTypes` line again.

```sh
git clone https://github.com/minhnhattonthat/blaze-union-story-to-reach-the-future-en
cd blaze-union-story-to-reach-the-future-en
# copy your dumps to:
#   rom/Blaze Union - Story to Reach The Future (Japan).iso
#     (582,221,824 bytes, SHA-1 de0e837fb23e4db73afa3fcaf84e71ac8030fac8)
#   rom/Yggdra Union - We'll Never Fight Alone (USA).iso   (SHA-1 c982fec7fa6309d20e8bc5170db1acf49df72e95)
#   work/exe/EBOOT.dump.bin                                 (from PPSSPP, steps above)
python -X utf8 tools/check_rom.py                      # "rom ok" when all three match
python -X utf8 tools/iso9660.py x "rom/Blaze Union - Story to Reach The Future (Japan).iso" work/iso
python -X utf8 tools/itoc.py x work/iso/PSP_GAME/USRDIR/Data/Data.cpk work/cpk
python -X utf8 tools/build.py                          # -> build/blaze_union_en.iso
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` is Sting's and is included only so
the translation can be checked against it. Blaze Union is (c) Sting; this project is not affiliated with them.
Do not share patched ISOs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
