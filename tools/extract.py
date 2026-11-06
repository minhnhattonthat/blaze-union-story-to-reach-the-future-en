"""Dump every Japanese string to script/*.json: 57 event scripts, FCT 3/15 children, the EBOOT, FCT 1/0.
usage: extract.py [--force]  writes only missing files unless --force; --force keeps `en` and `status` by id."""
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evscript
import fct
import textscan
from tbl import Table

ROOT = Path(__file__).resolve().parents[1]
CPK = ROOT / "work/cpk"
ELF = ROOT / "work/exe/EBOOT.dump.bin"
OUT = ROOT / "script"
EVENTS = range(2149, 2206)
RODATA, DATA_END = 0x1B1420, 0x2BFBDF  # .rodata and .data vaddrs, from the ELF section headers
BLOCK = 0x10000  # one eboot_*.json per this much of the address space


def table():
    """Printer bytes (docs/re/text.md) as a Table: 00 ends a string and is never decoded."""
    lines = ["01={n}", "02={voice:3}", "03={sub:1}", "04={sub16:2}", "20=\\s"]
    lines += [f"{c:02X}={chr(c)}" for c in range(0x21, 0x7F)]
    for c in range(0xA1, 0xE0):  # half-width kana
        lines.append(f"{c:02X}={bytes([c]).decode('cp932')}")
    for hi in [*range(0x81, 0xA0), *range(0xE0, 0xFD)]:
        for lo in [*range(0x40, 0x7F), *range(0x80, 0xFD)]:
            b = bytes([hi, lo])
            try:
                s = b.decode("cp932")
            except UnicodeDecodeError:
                continue
            if s.encode("cp932") == b:  # NEC/IBM duplicates stay [XX][XX] and still roundtrip
                lines.append(f"{b.hex().upper()}={s}")
    return Table(lines)


TBL = table()


def string_end(d, p, end=None):
    """End of the printer string at p, past its NUL; None if the bytes aren't printer text."""
    end = len(d) if end is None else end
    while p < end:
        c = d[p]
        if c == 0:
            return p + 1
        if c == 1:
            p += 1
        elif c == 2:
            p += 4
        elif c == 3:
            p += 2
        elif c == 4:
            p += 3
        elif c < 0x20 or c == 0x7F or c >= 0xFD or c == 0x80 or c == 0xA0:
            return None
        elif c < 0x7F or 0xA1 <= c <= 0xDF:
            p += 1
        elif p + 1 < end and (d[p + 1] >= 0x40 and d[p + 1] != 0x7F and d[p + 1] <= 0xFC):
            p += 2
        else:
            return None
    return None


def has_jp(raw):
    """Any double-byte Shift-JIS character outside a control code's arguments?"""
    p, n = 0, len(raw)
    while p < n:
        c = raw[p]
        if c == 2:
            p += 4
        elif c == 3:
            p += 2
        elif c == 4:
            p += 3
        elif 0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC:
            return True
        elif 0xA1 <= c <= 0xDF:
            return True
        else:
            p += 1
    return False


def plain(raw):
    """Text with its control codes removed: for judging whether it reads as Japanese."""
    return TBL.decode(raw, length=len(raw))[0]


def entry(src, d, p, end, kind, slots):
    """One JSON record; `end` is past the NUL, `bytes` counts it."""
    raw = d[p:end - 1]
    return {"id": f"{src}_{p:05X}", "ptr": p, "bytes": end - p, "kind": kind, "slots": slots,
            "jp": TBL.decode(raw, length=len(raw))[0], "en": "", "status": ""}


def script_entries(d):
    """Entry points of a VM file, event script or FCT 3/15 child. -> (entries, offsets of bytes that are tables), or None.
    Event scripts have the tail table of groups, child 8 a u32[0] offset of a zero-ended list, the rest a list at 0."""
    w = struct.unpack_from("<I", d)[0]
    if not 0 < w < len(d):
        return None
    if w == len(d) - 0x14 and len(d) > 0x28:
        groups = evscript.groups(d)
        spans = [(0, 0x28), (w, w + 20), *((g, g + 36) for g in groups)]
        return evscript.entries(d), spans
    if w % 4:
        return None
    if w > 0x1000 and struct.unpack_from("<I", d, 4)[0] == 0x90909090:  # child 8: list at w
        n = 0
        while struct.unpack_from("<I", d, w + n * 4)[0]:
            n += 1
        return set(struct.unpack_from(f"<{n}I", d, w)), [(0, 4), (w, w + (n + 1) * 4)]
    return {x for x in struct.unpack_from(f"<{w // 4}I", d) if 0 < x < len(d)}, [(0, w)]


def reads_jp(raw):
    """An unreferenced run in a script's gap is text only if it reads as text; dead bytecode can decode too."""
    if raw[:1] == b"\x02":  # a leading voice cue is normal for a line
        raw = raw[4:]
    return has_jp(raw) and looks_text(raw, True)


def scan_script(src, d):
    """Walk the bytecode, then read every gap. -> (entries, stats, other spans). A gap's bytes are strings, padding, dead
    code (op-shaped bytes the walk can't reach, read for their message references) or data."""
    start = script_entries(d)
    if start is None:  # bare strings, children 6 and 7
        ents, p = [], 0
        while p < len(d):
            e = string_end(d, p)
            if e is None:
                raise ValueError(f"{src}: bad bare string at {p:#x}")
            if e - p > 1:
                ents.append(entry(src, d, p, e, "bare", []))
            p = e
        return ents, {"str": len(d)}, []
    points, spans = start
    ops, tables, inline = evscript.walk(d, points)
    mask = bytearray(len(d))
    for a, b in spans:
        mask[a:b] = b"\1" * (b - a)
    for o, (_, raw) in ops.items():
        mask[o:o + len(raw)] = b"\1" * len(raw)
    for s, (_, q) in inline.items():
        mask[s:q] = b"\0" * (q - s)  # inline strings count as strings, not code
    refs = evscript.message_refs(ops)

    gaps, p = [], 0
    while p < len(d):
        if mask[p]:
            p += 1
            continue
        q = p
        while q < len(d) and not mask[q]:
            q += 1
        gaps.append((p, q))
        p = q

    # first pass: dead code, for references the walk can't see
    strings, dead, other = {}, [], []
    for a, b in gaps:
        g = a
        while g < b:
            e = string_end(d, g, b)
            if g in inline:
                g = inline[g][1]
            elif e and (g in refs or reads_jp(d[g:e - 1])):
                strings[g] = e
                g = e
            elif d[g] in (0, 0x90):
                g += 1
            else:
                h = g  # linear ops up to the next thing that reads as a string
                while h + 1 < b and d[h + 1] >= 2 and h + d[h + 1] <= b and d[h] != evscript.INLINE:
                    ops_end = h + d[h + 1]
                    dead.append((h, d[h:ops_end]))
                    h = ops_end
                    e2 = string_end(d, h, b)
                    if e2 and reads_jp(d[h:e2 - 1]):
                        break
                if h == g:  # not op-shaped: data, to the next printable string
                    h = g + 1
                    while h < b and not (string_end(d, h, b) and reads_jp(d[h:string_end(d, h, b) - 1]) and d[h - 1] in (0, 0x90)):
                        h += 1
                    other.append((g, h))
                g = h
    for o, raw in dead:
        if raw[0] == 0x46 and raw[2] == 0 and len(raw) == 7:
            refs.setdefault(struct.unpack_from("<I", raw, 3)[0], []).append(o + 3)

    for r in refs:  # a reference can start partway through a longer message: it gets its own record
        if r not in strings:
            strings[r] = string_end(d, r)
            if not strings[r] or mask[r]:
                raise ValueError(f"{src}: reference to no string: {r:#x}")
    ents = [entry(src, d, s, e, "msg" if s in refs else "unref", refs.get(s, [])) for s, e in sorted(strings.items())]
    ents += [entry(src, d, s, q, "inline", [o]) for s, (o, q) in sorted(inline.items())]
    ents.sort(key=lambda r: r["ptr"])
    stats = {"str": sum(e["bytes"] for e in ents), "code": sum(len(r) for _, r in ops.values()),
             "dead": sum(len(r) for _, r in dead), "other": sum(b - a for a, b in other)}
    return ents, stats, other


def relocations(elf):
    """Every pointer in the ELF's .rel.* sections. -> [(target vaddr, slot)], slot = {"word": v} or {"hi": v, "lo": v}.
    Segment 0 only: strings live there and its vaddr = code.bin offset."""
    shoff, shnum = struct.unpack_from("<I", elf, 32)[0], struct.unpack_from("<H", elf, 48)[0]
    img = elf[0x74:]
    out = []
    for i in range(shnum):
        s = struct.unpack_from("<10I", elf, shoff + i * 40)
        if s[1] != 0x700000A0:
            continue
        rels = struct.iter_unpack("<II", elf[s[4]:s[4] + s[5]])
        hi = None
        for off, info in rels:
            typ, ofsbase, addrbase = info & 0xFF, info >> 8 & 0xFF, info >> 16 & 0xFF
            if ofsbase or addrbase:
                continue
            word = struct.unpack_from("<I", img, off)[0] if off + 4 <= len(img) else 0
            if typ == 2:
                out.append((word, {"word": off}))
            elif typ == 5:
                hi = (off, word & 0xFFFF)
            elif typ == 6 and hi:
                lo = word & 0xFFFF
                out.append((((hi[1] << 16) + (lo - 0x10000 if lo & 0x8000 else lo)) & 0xFFFFFFFF, {"hi": hi[0], "lo": off}))
    return out


def looks_text(raw, slots):
    """Does a pointer target read as a string rather than bytes that happen to decode? Garbage shows half-width kana,
    stray codes or rare kanji; real names can be kanji-only (盾), so kana isn't required."""
    s = plain(raw)
    if textscan.real(s):
        return True
    if not slots or re.search(r"\{(voice|sub|sub16)|\[[0-9A-F]{2}\]|[｡-ﾟ]", s):
        return False
    s = s.replace("{n}", "")
    if "%" in s and any(ord(c) >= 0x7F for c in s):  # format strings such as %s隊
        return True
    if not all(ord(c) < 0x7F or c.encode("cp932", "ignore") for c in s):  # private-use glyphs
        return False
    wide = [c for c in s if ord(c) >= 0x7F]
    rare = [c for c in wide if c.encode("cp932")[:2] >= b"\x98\x73"]  # JIS level 2 kanji
    return len(wide) >= 2 and not (rare and len(wide) < len(s)) or (len(wide) == 1 and not rare and len(s) == 1)


def scan_eboot(elf):
    """Pointer targets in .rodata/.data, then any Japanese sentence no pointer reaches. kind data = decodes but isn't text."""
    img = elf[0x74:0x74 + DATA_END + 1]
    targets = {}
    for t, slot in relocations(elf):
        if RODATA <= t <= DATA_END:
            targets.setdefault(t, []).append(slot)
    ents, claimed = [], bytearray(len(img))
    for p in sorted(targets):
        e = string_end(img, p)
        if not e or not has_jp(img[p:e - 1]) or claimed[p]:
            continue
        kind = "msg" if looks_text(img[p:e - 1], targets[p]) else "data"
        ents.append(entry("eboot", img, p, e, kind, targets[p]))
        if kind == "msg":
            claimed[p:e] = b"\1" * (e - p)
    for off, s in textscan.scan(img[RODATA:])[0]:
        p = RODATA + off
        if claimed[p]:
            continue
        while p > RODATA and img[p - 1] != 0:  # back up over a leading control code or ASCII
            p -= 1
        e = string_end(img, p)
        kind = "unref"
        if not e:  # CRI middleware and debug printf: ASCII newlines and such, which the game's printer can't draw
            e, kind = img.index(0, p) + 1, "debug"
        if not claimed[p]:
            ents.append(entry("eboot", img, p, e, kind, []))
            claimed[p:e] = b"\1" * (e - p)
    ents.sort(key=lambda r: r["ptr"])
    return ents


def scan_names(src, d):
    """FCT 1/0: effect names inside binary data. Sentences only, kind data: they aren't drawn as far as anyone has seen."""
    ents = []
    for p, _ in textscan.scan(d)[0]:
        e = string_end(d, p)
        if e:
            ents.append(entry(src, d, p, e, "data", []))
    return ents


def uncovered(d, ents):
    """Japanese sentences in d (textscan's filter) that no text record covers: text the extractor missed."""
    claimed = bytearray(len(d))
    for r in ents:
        if r["kind"] != "data":
            claimed[r["ptr"]:r["ptr"] + r["bytes"]] = b"\1" * r["bytes"]
    return [(p, s) for p, s in textscan.scan(d)[0] if not claimed[p]]


def children(path, *route):
    """Bytes of a nested FCT child."""
    d = Path(path).read_bytes()
    for i in route:
        off, size = fct.children(d)[i]
        d = d[off:off + size]
    return d


def sources():
    """-> {name: (bytes, kind)}: every file that holds text, by the name its JSON takes."""
    out = {f"event_{i}": ((CPK / f"{i:05d}.bin").read_bytes(), "script") for i in EVENTS}
    for i in range(len(fct.children(children(CPK / "00003.bin", 15)))):
        out[f"fct3_15_{i:03d}"] = (children(CPK / "00003.bin", 15, i), "script")
    out["fct1_0"] = (children(CPK / "00001.bin", 0), "names")
    out["eboot"] = (ELF.read_bytes(), "eboot")
    return out


def extract():
    """-> ({json name: entries}, {name: (stats, other spans)})"""
    files, info = {}, {}
    for name, (d, kind) in sources().items():
        if kind == "script":
            files[name], stats, other = scan_script(name, d)
            info[name] = (stats, other)
        elif kind == "names":
            files[name] = scan_names(name, d)
        else:
            for r in scan_eboot(d):
                files.setdefault(f"eboot_{r['ptr'] // BLOCK:02X}", []).append(r)
    return files, info


def save(files, force=False):
    """Dump never clobbers English: existing files are left alone, and --force keeps en and status by id."""
    OUT.mkdir(exist_ok=True)
    wrote = 0
    for name, ents in files.items():
        path = OUT / f"{name}.json"
        if path.exists():
            if not force:
                continue
            old = {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8"))}
            for r in ents:
                if r["id"] in old:
                    r["en"], r["status"] = old[r["id"]]["en"], old[r["id"]]["status"]
        path.write_text(json.dumps(ents, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        wrote += 1
    return wrote


if __name__ == "__main__":
    files, info = extract()
    print("wrote", save(files, "--force" in sys.argv), "of", len(files), "files;",
          sum(map(len, files.values())), "strings")
