"""Print the defeat text chains (0x2B1C6C on in the EBOOT), one per line, parts joined by " / ", from script/: each part is one line on the game over screen.

    python -X utf8 tools/debug/defeat_text.py [--en]   JP, or the current English with JP for parts not translated yet
"""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE, START = 0x2B1690, 0x2B1C6C


def chains(code):
    """Each chain as a list of substring indexes: 03 nn = sub, 04 nn nn = sub16, 01 = next line, 00 = end. Stops at the first other byte."""
    pos, parts, out = START, [], []
    while True:
        b = code[pos]
        if b == 0:
            if parts:
                out.append(parts)
            parts = []
            pos += 1
        elif b == 1:
            pos += 1
        elif b == 3:
            parts.append(code[pos + 1])
            pos += 2
        elif b == 4:
            parts.append(code[pos + 1] | code[pos + 2] << 8)
            pos += 3
        else:
            return out


def main():
    code = (ROOT / "work/exe/code.bin").read_bytes()
    ents = {e["id"]: e for p in (ROOT / "script").glob("*.json") for e in json.loads(p.read_text(encoding="utf-8"))}
    en = "--en" in sys.argv

    def text(i):
        e = ents.get("eboot_%06X" % struct.unpack_from("<I", code, TABLE + 4 * i)[0])
        return e and ((en and e.get("en")) or e["jp"]) or f"<{i}>"

    seen = set()
    for chain in chains(code):
        line = " / ".join(text(i) for i in chain)
        if line not in seen:
            print(line)
            seen.add(line)


if __name__ == "__main__":
    main()
