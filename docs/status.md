# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (Step 0 done). Last build: none yet.
- **Done:**
  - Step 0: dump pinned, pre-commit proven to reject a failing test, guard hook proven (blocked `sed -i`), emulators fetched, smoke boots the original ISO (exit 0), scripted input reaches title menu and new game. Keyboard input on the windowed build not tested: nobody at the keyboard; the window starts and runs the game.
  - Recon in `docs/re/text.md`: Data.cpk fully unpacked; text sources located (57 event scripts, EBOOT, FCT 3/15, FCT 1/0); encoding Shift-JIS; printer control codes; message references are op 0x46 file offsets; fonts located; EBOOT decrypted.
  - Sweep tool done, sheets are rebuildable: `tools/sweep.py`.
- **Next (finish phase 1):**
  1. Rebuild `work/` if missing (commands in AGENTS.md; EBOOT dump steps in `docs/re/README.md`), run `tools/sweep.py`.
  2. Read all 102 sweep pages in `work/sweep/` in chunks and fill the survey table in `docs/re/graphics.md`. Render the skipped palette-less slices in grey and check the PNGs inside FCT 3 (`3/010-012`) plus ICON0/PIC1.
  3. Then phase 1 meets its done-when; set Phase to 2 (debug tool). `tools/debug/ppdbg.py` and session `work/play/a` show the new-game route: wait ~1400 frames, 2 x start, wait 6500 (movie), circle x4, wait for prologue ~4800 frames, circle.
- **Open bugs:** none (no build yet).
- **Waiting on the user:** non-blocking: the shipped EBOOT must be a plain ELF; it runs on PPSSPP and CFW, which is the expected audience. Default: ship plain.
