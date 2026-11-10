"""Put text into the game files: script/*.json records -> {Data.cpk id: bytes}, EBOOT. `text(record, file name)` gives the string
to insert, None to leave the record as it is. Used by the marker build and the translated build."""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import cardsel
import elfpatch
import extract
import fct
import vwf

ROOT = extract.ROOT
SCRIPT = ROOT / "script"
SEG_VADDR = 0x363000  # past segment 1's bss, 0x362F1C
ALIGN_PACK = 16


def records(name):
    return json.loads((SCRIPT / f"{name}.json").read_text(encoding="utf-8"))


def encode(s, r):
    """Bytes of the string, with its NUL."""
    b = extract.TBL.encode(s) + b"\0"
    if r["kind"] in ("inline", "bare") and len(b) > r["bytes"]:
        raise ValueError(f"{r['id']}: {len(b)} bytes, slot holds {r['bytes']}: {s!r}")
    return b


def pack_script(d, recs, text, name):
    """In place when it fits and nothing overlaps it, else after the end of the file. Inline strings keep their exact size
    (IP moves past the NUL) and so do bare ones (reached by unknown means, docs/re/text.md)."""
    out = bytearray(d)
    spans = sorted((r["ptr"], r["ptr"] + r["bytes"]) for r in recs)
    overlap = set()
    for (a, b), (c, _) in zip(spans, spans[1:]):
        if c < b:
            overlap |= {a, c}
    tail = bytearray()
    done = 0
    for r in recs:
        s = text(r, name)
        if s is None:
            continue
        b = encode(s, r)
        done += 1
        if r["kind"] in ("inline", "bare"):
            out[r["ptr"]:r["ptr"] + r["bytes"]] = b[:-1] + b" " * (r["bytes"] - len(b)) + b"\0"
            continue
        for slot in r["slots"]:
            assert struct.unpack_from("<I", d, slot)[0] == r["ptr"], (name, r["id"], slot)
        if len(b) <= r["bytes"] and r["ptr"] not in overlap:
            out[r["ptr"]:r["ptr"] + len(b)] = b
            continue
        if not r["slots"]:  # no pointer to move: too long is refused (the lint says so first, fit.problems); overlapping, its bytes belong to the other record
            if len(b) > r["bytes"]:
                raise ValueError(f"{r['id']}: {len(b)} bytes, unreferenced and holds {r['bytes']}: {s!r}")
            continue
        at = len(d) + len(tail)
        tail += b
        for slot in r["slots"]:
            struct.pack_into("<I", out, slot, at)
    return bytes(out) + bytes(tail), done


LOSE_TEXT, ICONS, MISSIONS = 0x2B8758, 0x2B87C4, 0x2B8810  # pointers, 19 records (10 win, 9 lose), 8-byte records
ICON_WIN = 10


def goal_icons(eb, recs, text):
    """The goal panel (0x12F124) draws an icon over one glyph slot of a row: record mission, slot, row, icon. The string has ■
    there, and the slot is its index in that row, so it has to follow the English."""
    by_ptr = {r["ptr"]: r for r in recs}
    for at in range(ICONS, MISSIONS, 4):
        mission, slot, row, _ = eb.word(at).to_bytes(4, "little")
        win, lose = eb.word(MISSIONS + mission * 8), eb.word(MISSIONS + mission * 8 + 4).to_bytes(4, "little")[:3]
        ptrs = [win] if (at - ICONS) // 4 < ICON_WIN else [eb.word(LOSE_TEXT + i * 4) for i in lose if i != 0xFF]
        jp, en = [], []
        for r in (by_ptr[p] for p in ptrs):
            one = text(r, "eboot")
            jp += r["jp"].split("{n}")
            en += one.split("{n}")
            assert len(jp) == len(en), f"{r['id']}: English rows must match the Japanese, the row is in the record"
        assert jp[row].rindex("■") == slot, (hex(at), jp[row])
        eb.put(at + 1, bytes([en[row].rindex("■")]))


def pack_eboot(eb, recs, text):
    """Move strings to the new segment and repoint them. A lui shared with another target can't move: those strings stay."""
    if not hasattr(text, "fit"):  # the marker has no icons to place
        goal_icons(eb, recs, text)
    hi_targets = {}
    for t, s in extract.relocations(bytes(eb.elf)):
        if "hi" in s:
            hi_targets.setdefault(s["hi"], set()).add(t)
    done = 0
    wrapped = {}  # string address -> where its line breaks go: vwf.WRAPS
    for table, end, brk, n, font, px in vwf.WRAPS:
        for i in range((end - table) // 4):
            wrapped.setdefault(eb.word(table + i * 4), []).append((brk + i * n, n, font, px))
    widths = vwf.widths()
    for r in recs:
        s = text(r, "eboot")
        if s is None:
            continue
        if r["ptr"] in wrapped:
            for at, n, font, px in wrapped[r["ptr"]]:
                eb.put(at, vwf.breaks(s, n, font, px, widths[font]))
        b = encode(s, r)
        done += 1
        shared = any(len(hi_targets[x["hi"]]) > 1 for x in r["slots"] if "hi" in x)
        if not r["slots"] or shared:
            if len(b) > r["bytes"] and hasattr(text, "fit"):
                b = encode(text.fit(r), r)
            if len(b) > r["bytes"]:
                raise ValueError(f"{r['id']}: stays in place (no slot or shared lui), {len(b)} > {r['bytes']}: {s!r}")
            eb.put(r["ptr"], b)
            continue
        at = eb.append(b)
        for x in r["slots"]:
            if "word" in x:
                assert eb.word(x["word"]) == r["ptr"], r["id"]
                eb.put(x["word"], struct.pack("<I", at))
            else:
                hi, lo = eb.word(x["hi"]), eb.word(x["lo"])
                was = ((hi & 0xFFFF) << 16) + ((lo & 0xFFFF) - 0x10000 if lo & 0x8000 else lo & 0xFFFF)
                assert was & 0xFFFFFFFF == r["ptr"], r["id"]
                eb.put(x["hi"], struct.pack("<I", hi & 0xFFFF0000 | (at + 0x8000) >> 16))
                eb.put(x["lo"], struct.pack("<I", lo & 0xFFFF0000 | at & 0xFFFF))
    return done


def pack_fct(d, repl):
    """FCT with children replaced, others byte for byte; children stay 16-aligned as in the original."""
    kids = fct.children(d)
    first = kids[0][0]
    out = bytearray(d[:first])
    table = struct.unpack_from("<I", d, 8)[0]
    for i, (o, s) in enumerate(kids):
        out += bytes(-len(out) % ALIGN_PACK)
        c = repl.get(i, d[o:o + s])
        struct.pack_into("<II", out, table + i * 8, len(out), len(c))
        out += c
    tail = d[kids[-1][0] + kids[-1][1]:]
    return bytes(out) + (tail if len(tail) < ALIGN_PACK else b"")


def child(path, *route):
    return extract.children(path, *route)


def build(text, base=None):
    """-> ({Data.cpk id: bytes}, EBOOT bytes). Every call starts from the dump's bytes in work/, or from base[3] for
    FCT 3 (its sprites already edited by gen_gfx)."""
    cpk = extract.CPK
    repl = {}
    count = 0
    for i in extract.EVENTS:
        name = f"event_{i}"
        repl[i], n = pack_script((cpk / f"{i:05d}.bin").read_bytes(), records(name), text, name)
        count += n

    d3 = (base or {}).get(3) or (cpk / "00003.bin").read_bytes()
    k3 = fct.children(d3)
    d15 = d3[k3[15][0]:k3[15][0] + k3[15][1]]
    new15 = {}
    for i, (o, s) in enumerate(fct.children(d15)):
        name = f"fct3_15_{i:03d}"
        new15[i], n = pack_script(d15[o:o + s], records(name), text, name)
        count += n
    d1 = d3[k3[1][0]:k3[1][0] + k3[1][1]]
    k1 = fct.children(d1)
    pages, info = vwf.fonts(lambda c: d1[k1[c][0]:k1[c][0] + k1[c][1]])
    repl[3] = pack_fct(d3, {15: pack_fct(d15, new15), 1: pack_fct(d1, pages)})
    assert len(repl[3]) - vwf.FCT3_SIZE <= vwf.ARENA_GROW, f"FCT 3 is {len(repl[3]):#x}: raise vwf.ARENA_GROW"  # arena 0 keeps its original slack

    eb = elfpatch.Eboot(extract.ELF.read_bytes(), SEG_VADDR)
    vwf.install(eb, info)
    cardsel.install(eb)
    recs = [r for f in sorted(SCRIPT.glob("eboot_*.json")) for r in json.loads(f.read_text(encoding="utf-8"))]
    count += pack_eboot(eb, recs, text)
    log = ROOT / "build/writes.txt"
    log.parent.mkdir(exist_ok=True)
    log.write_text("".join(f"{v:X} {o.hex()} {n.hex()}\n" for v, o, n in eb.writes), newline="\n")
    return repl, eb.serialize(), count
