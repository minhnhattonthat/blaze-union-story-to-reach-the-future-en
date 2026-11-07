"""The strings of the defeat table 0x2B4E58 (rows of 4 u32: flags, chain, flags, chain), by use: `news` (+4, one centred line in battle at
0x115804) and `gameover` (+0xC, the game over screen's text at 0x1161D4). Each part is one line on screen.

    python -X utf8 tools/debug/defeat_parts.py        counts, and game over parts over LIMIT
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
TABLE = 0x2B1690  # substring table
ROWS, ROW_END = 0x2B3648, 0x2B4E58
LIMIT = 288


def parts(code, pos):
    """Substring indexes of the chain at pos: 03 nn sub, 04 nn nn sub16, 01 next line, 00 end."""
    out = []
    while pos and code[pos]:
        if code[pos] == 3:
            out.append(code[pos + 1])
            pos += 2
        elif code[pos] == 4:
            out.append(code[pos + 1] | code[pos + 2] << 8)
            pos += 3
        else:
            pos += 1
    return out


def ids(code):
    """(news ids, game over ids): record id of every part in each use, plus the game over chains as lists of ids."""
    name = lambda i: "eboot_%06X" % struct.unpack_from("<I", code, TABLE + 4 * i)[0]
    news, over, chains = set(), set(), set()
    for row in range(ROWS, ROW_END, 16):
        _, a, _, b = struct.unpack_from("<4I", code, row)
        news |= {name(i) for i in parts(code, a)}
        chain = tuple(name(i) for i in parts(code, b))
        over |= set(chain)
        chains.add(chain)
    return news, over, chains


def main():
    import batches
    import fit
    code = (ROOT / "work/exe/code.bin").read_bytes()
    news, over, chains = ids(code)
    ents = batches.index()
    print(f"news {len(news)} parts, game over {len(over)}, both {len(news & over)}, game over chains {len(chains)}")
    wide = sorted((fit.width(ents[i]["en"], 1), i, ents[i]["jp"], ents[i]["en"]) for i in over if i in ents)
    print("game over parts over", LIMIT, sum(w[0] > LIMIT for w in wide), "of", len(wide), "; over 215:", sum(w[0] > 215 for w in wide))
    for w in reversed(wide):
        if w[0] > LIMIT:
            print(w)
    print("news widest", max(fit.width(ents[i]["en"], 1) for i in news if i in ents))


if __name__ == "__main__":
    main()
