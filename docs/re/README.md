# Reverse-engineering notes

One file per subsystem. **verified** names the test or breakpoint; **guess** says why, and must be promoted before code
depends on it. Addresses are for the dump in `rom.sha1`.

| File | Covers | State |
|---|---|---|
| `text.md` | Image layout, text inventory, encoding, control codes, script bytecode and message references, EBOOT strings, fonts, free space | Mostly verified; open items listed at its end |
| `graphics.md` | PTX and PTG formats, sweep tool, graphics-text survey | Formats verified; static survey complete; PTA not decoded |
| `cardsel.md` | Card Select panel: how the original picks its effect and condition strips, our font-printer hooks | Seen in game: Steal, Shield Barrier, empty slot |
| `debug.md` | Stage table, top-level modes, request flags, story variables, what the warp tool reaches and what it doesn't | Stage warps and endings verified; open items listed in it |

## Getting the decrypted EBOOT

`EBOOT.BIN` is encrypted (`~PSP`, internal name `YggdraUnion`). PPSSPPHeadless does not honour `DumpFileTypes`; the
windowed build does:

1. Write `tools/ppsspp/memstick/PSP/SYSTEM/ppsspp.ini` with `[General] DumpFileTypes = 7` and
   `[Graphics] GraphicsBackend = 2` (Vulkan fails on this machine and the game never starts).
2. Run `tools/ppsspp/PPSSPPWindows64.exe <iso>` for ~40 s, then close it. Set `DumpFileTypes = 0` again.
3. Result: `memstick/PSP/SYSTEM/DUMP/ULJM05503_EBOOT.BIN`. Copy to `work/exe/EBOOT.dump.bin`.
   `work/exe/code.bin` = bytes 116..116+2882720 of it (`tail -c +117 | head -c 2882720`), so file offset = vaddr.
4. It is a relocatable PRX ELF (type 0xFFA0). RAM address = 0x08804000 + vaddr (**verified**: breakpoint pc 0x088A2A6C
   lands on the `lbu` at vaddr 0x9EA6C).

Debugger helper: `tools/debug/ppdbg.py` (`dump`, `find`, `peek`, `mods`, `watch`).
