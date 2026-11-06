# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- references/platform-psp.md: `cpk.py` refuses ITOC-only CPKs (no names, numeric IDs, no TOC), which CRI also ships; this repo wrote a reader with a CRILAYLA decoder in `tools/itoc.py`, worth adopting.
- references/platform-psp.md: EBOOT dump via `DumpFileTypes` works only in the windowed build, PPSSPPHeadless ignores it; and Vulkan's default failed silently (only `FailedGraphicsBackends.txt` as evidence), `GraphicsBackend = 2` fixed it.
- references/emulator-qa.md: psp.py runs write `ppsspp.log`, not the `log.txt` emu.py's help describes.
- references/emulator-qa.md: PPSSPP WebSocket memory breakpoints work from Python: `memory.breakpoint.add` then `cpu.runUntilTime` + `wait("cpu.stepping")`; `cpu.getAllRegs` categories[0].uintValues gives GPRs. See `tools/debug/ppdbg.py`. No skill tool wraps this.
- references/graphics.md: a sweep at 240x136 per cell loses 8-px text strips entirely, and PTX-style slices can share the previous texture's palette (offset 0): noise until handled.
- SKILL.md: a dispatched worker told "no subagents" has no cheap way to read a 100-page sweep; the sheet budget alone forces a hand-back. Worked here: quarter-size overviews (4 pages per image) to classify, then crops of text regions at full size: roughly 60k tokens instead of 180k (estimated from image sizes), at the cost of small text on quarter-size pages being easier to miss.
- references/graphics.md: text that looks cut in half across a sweep may be a packed atlas, not a decoder bug. Here PTX slices lay a sprite's lower half beside its upper half and a PTG cell table reassembles them; a worker misread one such strip as two lines. Check for a cell table in front of the texture before reading strips.
- references/graphics.md: the hook guard also blocks a heredoc that merely holds backslash escapes in a throwaway script, so scratch scripts go through the file-write tool; `| tail` in the same command hides the test exit code from an `echo $?`, redirect to a log instead.
