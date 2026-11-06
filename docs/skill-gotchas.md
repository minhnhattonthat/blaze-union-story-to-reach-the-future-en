# Skill gotchas

One line per gotcha: the reference file it belongs in, then the fact.

- references/platform-psp.md: `cpk.py` refuses ITOC-only CPKs (no names, numeric IDs, no TOC), which CRI also ships; this repo wrote a reader with a CRILAYLA decoder in `tools/itoc.py`, worth adopting.
- references/platform-psp.md: EBOOT dump via `DumpFileTypes` works only in the windowed build, PPSSPPHeadless ignores it; and Vulkan's default failed silently (only `FailedGraphicsBackends.txt` as evidence), `GraphicsBackend = 2` fixed it.
- references/emulator-qa.md: psp.py runs write `ppsspp.log`, not the `log.txt` emu.py's help describes.
- references/emulator-qa.md: PPSSPP WebSocket memory breakpoints work from Python: `memory.breakpoint.add` then `cpu.runUntilTime` + `wait("cpu.stepping")`; `cpu.getAllRegs` categories[0].uintValues gives GPRs. See `tools/debug/ppdbg.py`. No skill tool wraps this.
- references/graphics.md: a sweep at 240x136 per cell loses 8-px text strips entirely, and PTX-style slices can share the previous texture's palette (offset 0): noise until handled.
- SKILL.md: a dispatched worker told "no subagents" has no cheap way to read a 100-page sweep; the sheet budget alone forces a hand-back.
