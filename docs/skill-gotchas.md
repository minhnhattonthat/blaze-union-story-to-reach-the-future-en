# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- references/platform-psp.md: `cpk.py` refuses ITOC-only CPKs (no names, numeric IDs, no TOC), which CRI also ships; this repo wrote a reader with a CRILAYLA decoder in `tools/itoc.py`, worth adopting.
- references/platform-psp.md: EBOOT dump via `DumpFileTypes` works only in the windowed build, PPSSPPHeadless ignores it; and Vulkan's default failed silently (only `FailedGraphicsBackends.txt` as evidence), `GraphicsBackend = 2` fixed it.
- references/emulator-qa.md: psp.py runs write `ppsspp.log`, not the `log.txt` emu.py's help describes.
- references/emulator-qa.md: PPSSPP WebSocket memory breakpoints work from Python: `memory.breakpoint.add` then `cpu.runUntilTime` + `wait("cpu.stepping")`; `cpu.getAllRegs` categories[0].uintValues gives GPRs. See `tools/debug/ppdbg.py`. No skill tool wraps this.
- references/graphics.md: a sweep at 240x136 per cell loses 8-px text strips entirely, and PTX-style slices can share the previous texture's palette (offset 0): noise until handled.
- SKILL.md: a dispatched worker told "no subagents" has no cheap way to read a 100-page sweep; the sheet budget alone forces a hand-back. Worked here: quarter-size overviews (4 pages per image) to classify, then crops of text regions at full size: roughly 60k tokens instead of 180k (estimated from image sizes), at the cost of small text on quarter-size pages being easier to miss.
- scripts/psp.py: `WS.recv` hands a WebSocket close frame (opcode 8) to `json.loads`, so an emulator that dies shows as `UnicodeDecodeError ... byte 0xe9` (status 1001 = `03 E9`), which reads like a text bug. It should raise a clear "emulator closed the connection".
- references/platform-psp.md: PRX `lui` values can be segment-relative: here values below 0x0A are relative to segment 1 (vaddr 0x2BFCA0), so RAM = load base + segment base + value. A plain `base + value` read returned a plausible wrong word and cost a failed warp.
- references/emulator-qa.md: `play.py SESSION --rom ROM --state S` takes no presses on the creating call; create the session first, then press. Copying a state into a hand-made session folder cold-boots instead.
- references/emulator-qa.md: look for a game's table of stages early: here a 153-record table with script and card ids plus names like `1_02_A`, found from a save-description string, and a leftover start path in the re-init mode, gave warps with no story flags.
- references/graphics.md: text that looks cut in half across a sweep may be a packed atlas, not a decoder bug. Here PTX slices lay a sprite's lower half beside its upper half and a PTG cell table reassembles them; a worker misread one such strip as two lines. Check for a cell table in front of the texture before reading strips.
- references/graphics.md: the hook guard also blocks a heredoc that merely holds backslash escapes in a throwaway script, so scratch scripts go through the file-write tool; `| tail` in the same command hides the test exit code from an `echo $?`, redirect to a log instead.
