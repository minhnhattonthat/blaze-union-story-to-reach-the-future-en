# Blaze Union: Story to Reach the Future (PSP) English translation

Skill: translate-retro-game; `python tools/skill.py` prints its folder. Read its SKILL.md before ROM, text or QA work. `"$(python tools/skill.py)"` works in bash and PowerShell; never paste a `plugins/cache/<hash>` path.

## Commands (run from repo root)
- Unpack: `python -X utf8 tools/iso9660.py x "rom/Blaze Union - Story to Reach The Future (Japan).iso" work/iso` then `python -X utf8 tools/itoc.py x work/iso/PSP_GAME/USRDIR/Data/Data.cpk work/cpk` (~80 s)
- Extract: `python -X utf8 tools/extract.py` -> `script/*.json` (`--force` re-dumps, keeping `en` and `status`)
- Build:  `python -X utf8 tools/build.py` -> `build/blaze_union_en.iso` (checks the dump against `rom.sha1` first; edits plug in at `edits()`)
- Check:  `python -X utf8 tools/check.py` (tests + lint; the pre-commit hook runs this). Hook: `git config core.hooksPath tools/hooks`
- Verify: `python -X utf8 tools/verify_build.py` (after a build: romdiff over the EBOOT's write log, disc and Data.cpk change only what they should)
- Smoke:  `python -X utf8 "$(python tools/skill.py)/scripts/emu.py" build/blaze_union_en.iso --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:   `python -X utf8 tools/debug/warp.py 3_10_A --out work/qa/w --frames 1200 --every 300 --mash circle` (cold boot to any stage; `tools/debug/warp_all.py` does the 151 reachable). `docs/re/debug.md` has the rest. Never ask the user to play to a scene.
- Scenes: `python -X utf8 tools/debug/scenes.py --stages --jobs 6 --iso build/blaze_union_en.iso` (every menu, battle screen, ending, credits and extras from a cold boot; shots in `work/qa/scenes/`, `--states` also saves states; with no `--iso` or `BU_ISO`, it and `warp.py` run the Japanese ISO).
- Release: `python -X utf8 tools/release.py --version 1.0` (every gate, xdelta3 patch, re-apply, zip in `release/`; never publish without the user)
- Clean:  `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)

## Paths
- Original ROM: `rom/Blaze Union - Story to Reach The Future (Japan).iso` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulators: PPSSPPHeadless QA fork `qa-1` (`fetch_emu.py ppsspp-headless`, one per machine in `%LOCALAPPDATA%\translate-retro-game\ppsspp-headless\`) and windowed PPSSPP v1.20.4 in `tools/ppsspp/` (https://github.com/hrydgard/ppsspp/releases/download/v1.20.4/PPSSPP-v1.20.4-Windows-x64.zip; gitignored; needs `GraphicsBackend = 2` in its memstick ppsspp.ini, Vulkan fails here). Savestates: `work/states/`.
- Decrypted EBOOT: `work/exe/EBOOT.dump.bin` (windowed PPSSPP with `DumpFileTypes = 7`; see `docs/re/README.md`).
- Text: `script/` (JSON, per pipeline.md). Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the `.claude/agents/` types (translator, reviewer, visual-qa, playtester), never general-purpose: their short tool list cuts each agent's start-up context from ~43k to ~9k tokens.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Never fetch tcrf.net or its subdomains (datacrystal.tcrf.net has a Blaze Union page: denied by the skill's rule, not read).
- Data.cpk is ITOC-only (numeric IDs, no names): use `tools/itoc.py`; `tools/cpk.py` refuses it.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
