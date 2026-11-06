# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 3. Identity build next: unpack then repack with no edits. Debug tool finished. Last build: none yet.
- **Done:**
  - Step 0: dump pinned, pre-commit proven to reject a failing test, guard hook proven (blocked `sed -i`), emulators fetched, smoke boots the original ISO (exit 0), scripted input reaches title menu and new game. Keyboard input on the windowed build not tested: nobody at the keyboard; the window starts and runs the game.
  - Phase 1. Text recon in `docs/re/text.md`: Data.cpk fully unpacked; text sources located (57 event scripts, EBOOT, FCT 3/15, FCT 1/0); encoding Shift-JIS; printer control codes; message references are op 0x46 file offsets; fonts located; EBOOT decrypted.
  - Phase 1. Graphics survey in `docs/re/graphics.md`: every sweep page read (all 9 strip pages at full size, the 66 texture pages at quarter size, with their text regions cropped at full size), every Japanese family found is listed with its files. PTG sprite groups decoded (`tools/ptg.py`, `tests/test_ptg.py`); `tools/sweep.py` now draws sprites whole. Prologue scroll, chapter cards and story recap pages located.
  - Phase 2. `tools/debug/scenes.py --stages --jobs 6` reaches its whole list from a cold boot, each with a shot: 99 scenes (title and option, prologue, chapter recaps, prep, cards, field, Main Menu items, union, combat, result, victory, game over, save, resume, tutorial, 23 endings, credits and post-credits notice, 5 extras books) and 151 stage warps (`warp_all.py`). Last full run 99/99 and 151/151; shots read on contact sheets, stages at thumbnail size. Findings: `docs/re/debug.md`.
- **Next (phase 3):** build tool: repack `work/cpk` to Data.cpk, then the ISO, byte-identical to the original, as a test. Formats: `tools/itoc.py`, `tools/iso9660.py`. Then fill the Build line in `AGENTS.md`.
- **Debug tool limits, all in `docs/re/debug.md`:** 1_05_B and 1_05_C can't be reached by any play route (empty script entry slots, the game's own data). Credits stall on the last page in headless, on what reads as the music wait, so `after_credits` pokes past it; not checked on the windowed build. Save lists not shot with data present. Not yet in the list: the reward prompt, later stages' mission banners, skills and cards beyond 1_02_A's; `textcover.py` in phase 8 adds what's missing.
- **Known limits of the survey:** PTA grey slices taken to be animation frames (not decoded), opening movie sampled every 15 s only, some rows in `graphics.md` give a page instead of offsets (`work/sweep/index.tsv` has them), pages with no visible text were read at quarter size only, so small text there could be missed. The in-game tour (phases 5 and 8) checks all of this.
- **Open bugs:** none (no build yet).
- **Waiting on the user:** non-blocking: the shipped EBOOT must be a plain ELF; it runs on PPSSPP and CFW, which is the expected audience. Default: ship plain.
