"""Speaker of each event message: the last op EB before it names a unit, `eb 0b side expr part 00 01 pose <u16 name id> slot`.
The id indexes the name table in the EBOOT (TABLE). Context for translators and reviewers only; nothing is built from it.

    python -X utf8 tools/speakers.py          writes data/speakers.tsv: id, speaker
"""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import evscript

TABLE, STRIDE = 0x2ADE7C, 12  # ガーロット's slot, id 0; 3 words a row (0x53 = ？？？, 0x55 = 赤毛の幼い子ども, as the scenes read)


def names():
    """{name id: jp} from the slots of the EBOOT's records."""
    out = {}
    for p in sorted((ROOT / "script").glob("eboot_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            for s in r["slots"]:
                if "word" in s and TABLE <= s["word"] < TABLE + STRIDE * 500 and (s["word"] - TABLE) % STRIDE == 0:
                    out[(s["word"] - TABLE) // STRIDE] = r["jp"]
    return out


def tags(d):
    """{message offset: name id}, in op order, for one script file."""
    ops, _, _ = evscript.walk(d)
    cur, out = None, {}
    for o in sorted(ops):
        op, raw = ops[o]
        if op == 0xEB and len(raw) == 11:
            cur = struct.unpack_from("<H", raw, 8)[0]
        elif op == 0x46 and raw[2] == 0 and len(raw) == 7:
            out.setdefault(struct.unpack_from("<I", raw, 3)[0], cur)
    return out


def main():
    table = names()
    rows, missing = [], 0
    import extract
    for p in sorted((ROOT / "script").glob("event_*.json")) + sorted((ROOT / "script").glob("fct3_15_*.json")):
        if p.stem.startswith("event_"):
            d = (ROOT / f"work/cpk/{int(p.stem[6:]):05d}.bin").read_bytes()
        else:
            d = extract.children(extract.CPK / "00003.bin", 15, int(p.stem[8:]))
        try:
            t = tags(d)
        except (ValueError, struct.error, IndexError):  # children 006, 007 are bare strings, no VM
            t = {}
        for r in json.loads(p.read_text(encoding="utf-8")):
            sid = t.get(r["ptr"])
            who = table.get(sid, "") if sid is not None else ""
            missing += not who
            rows.append(f"{r['id']}\t{who}\n")
    (ROOT / "data/speakers.tsv").write_text("".join(rows), encoding="utf-8", newline="\n")
    print(len(rows), "rows,", missing, "without a speaker;", len(table), "names")


if __name__ == "__main__":
    main()
