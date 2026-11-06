# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool in progress: stages and endings reached, other screens not. Last build: none yet.
- **Done:**
  - Step 0: dump pinned, pre-commit proven to reject a failing test, guard hook proven (blocked `sed -i`), emulators fetched, smoke boots the original ISO (exit 0), scripted input reaches title menu and new game. Keyboard input on the windowed build not tested: nobody at the keyboard; the window starts and runs the game.
  - Phase 1. Text recon in `docs/re/text.md`: Data.cpk fully unpacked; text sources located (57 event scripts, EBOOT, FCT 3/15, FCT 1/0); encoding Shift-JIS; printer control codes; message references are op 0x46 file offsets; fonts located; EBOOT decrypted.
  - Phase 1. Graphics survey in `docs/re/graphics.md`: every sweep page read (all 9 strip pages at full size, the 66 texture pages at quarter size, with their text regions cropped at full size), every Japanese family found is listed with its files. PTG sprite groups decoded (`tools/ptg.py`, `tests/test_ptg.py`); `tools/sweep.py` now draws sprites whole. Prologue scroll, chapter cards and story recap pages located.
  - Phase 2, part: `tools/debug/warp.py` and `warp_all.py` warp from a cold boot to a stage through the game's own stage table (153 records, covering all 57 scripts), with chapter and stage cards. Endings 0-3 reached with `--req 0x200 --var 0xb=N`. Prep screens reached by mashing; the field by poking mode 14 from prep. Findings and addresses: `docs/re/debug.md`.
- **Next (phase 2), in order, all listed under Open in `docs/re/debug.md`:**
  1. Fix the 1_05_B and 1_05_C warps, which end the emulator (try `warp(card=False)`).
  2. Credits (press circle on the ending CG), endings above N=3.
  3. Game over. Combat and result screens: start from a field reached by poking mode 14. Find the real battle-start control.
  4. Extras (needs its unlock on the title), tutorial, recap pages, title sub-screens (LOAD DATA, CONTINUE, OPTION).
  5. Scene list file with one command that regenerates a shot per entry, then read the shots. So far `work/qa/stages/*.png` have been checked by assertion only (stage index, mode, not flat), plus three stages by eye (3_10_A, 2_01_A, 1_02_A).
- **Known limits of the survey:** PTA grey slices taken to be animation frames (not decoded), opening movie sampled every 15 s only, some rows in `graphics.md` give a page instead of offsets (`work/sweep/index.tsv` has them), pages with no visible text were read at quarter size only, so small text there could be missed. The in-game tour (phases 5 and 8) checks all of this.
- **Open bugs:** none (no build yet).
- **Waiting on the user:** non-blocking: the shipped EBOOT must be a plain ELF; it runs on PPSSPP and CFW, which is the expected audience. Default: ship plain.
