# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool not started (phase 1 done). Last build: none yet.
- **Done:**
  - Step 0: dump pinned, pre-commit proven to reject a failing test, guard hook proven (blocked `sed -i`), emulators fetched, smoke boots the original ISO (exit 0), scripted input reaches title menu and new game. Keyboard input on the windowed build not tested: nobody at the keyboard; the window starts and runs the game.
  - Phase 1. Text recon in `docs/re/text.md`: Data.cpk fully unpacked; text sources located (57 event scripts, EBOOT, FCT 3/15, FCT 1/0); encoding Shift-JIS; printer control codes; message references are op 0x46 file offsets; fonts located; EBOOT decrypted.
  - Phase 1. Graphics survey in `docs/re/graphics.md`: every sweep page read (all 9 strip pages at full size, the 66 texture pages at quarter size, with their text regions cropped at full size), every Japanese family found is listed with its files. PTG sprite groups decoded (`tools/ptg.py`, `tests/test_ptg.py`); `tools/sweep.py` now draws sprites whole. Prologue scroll, chapter cards and story recap pages located.
- **Next (phase 2):** `tools/debug/`: reach any scene, menu or ending from a cold boot, each with a shot, no save and no playthrough. PPSSPP has no Lua: Python over the WebSocket (`tools/debug/ppdbg.py`: `dump`, `find`, `peek`, `mods`, `watch`). Session `work/play/a` shows the new-game route: wait ~1400 frames, 2 x start, wait 6500 (movie), circle x4, wait for prologue ~4800 frames, circle. Scene list to cover: the 57 event scripts (2149-2205), chapter cards, recap pages, game over, tutorial, extras menu, credits.
- **Known limits of the survey:** PTA grey slices taken to be animation frames (not decoded), opening movie sampled every 15 s only, some rows in `graphics.md` give a page instead of offsets (`work/sweep/index.tsv` has them), pages with no visible text were read at quarter size only, so small text there could be missed. The in-game tour (phases 5 and 8) checks all of this.
- **Open bugs:** none (no build yet).
- **Waiting on the user:** non-blocking: the shipped EBOOT must be a plain ELF; it runs on PPSSPP and CFW, which is the expected audience. Default: ship plain.
