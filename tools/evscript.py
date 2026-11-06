"""Event scripts (CPK IDs 2149-2205): bytecode walk and message references. usage: evscript.py FILE [--ops]
Header: u32[0] = file size - 0x14, the offset of 5 u32 naming groups of 9 entry points (the first is u32[1..9]). Handlers
are at EBOOT 0x2AEDB8 + op*4 and take (vm, op + 2); returning 1 advances IP by the op's length byte (docs/re/text.md)."""
import collections
import struct
import sys

# ops whose last 4 bytes are a target when they have that many bytes (handlers calling 0xFF778, plus call op 7)
JUMPS = {0x05, 0x07, 0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x1D, 0x1E, 0x90, 0x91, 0xDD, 0xDF, 0xEA, 0xF0, 0xFC}
STOPS = {0x01, 0x03, 0x05, 0x06}  # never fall through
INLINE = 0x74  # 74 len idx <NUL-terminated string>: IP advances past the string (handler 0x108D5C)
TABLES = {0x52: 2, 0x53: 2, 0x08: 4}  # op -> table start: u32 targets indexed by a game variable; never fall through
SWITCH = 0x09  # 09 len var count <count u32>: falls through past the table when var >= count
BRANCH = 0x0A  # 0A len var <u32 true> <u32 false>: never falls through


def header(d):
    return struct.unpack_from("<10I", d)


def entries(d):
    """Every entry point the file declares: the 5 u32 at u32[0] each give the offset of a group of 9 entry u32 (0 = none).
    The first group is usually at 4, the rest of the header."""
    return {x for g in groups(d) for x in struct.unpack_from("<9I", d, g) if 0 < x < len(d)}


def groups(d):
    """Offsets of the entry groups, each 9 u32."""
    return [g for g in struct.unpack_from("<5I", d, header(d)[0]) if g]


def table_targets(d, p, start):
    """Targets of a jump table at p + start. It ends where the lowest forward target so far starts, because the code that
    follows is only reached through it. shortcut: a table with no forward target runs to a value out of range."""
    out, q = [], p + start
    while q + 4 <= len(d):
        forward = [t for t in out if t > p]
        if forward and q >= min(forward):
            break
        t = struct.unpack_from("<I", d, q)[0]
        if not 0 < t < len(d):
            break
        out.append(t)
        q += 4
    return out, q


def walk(d, points=None):
    """Recursive descent from points (default: the file's entries).
    -> (ops {off: (op, raw)}, tables {off: (targets, end)}, inline {string off: (op off, end)})."""
    ops, tables, inline, todo = {}, {}, {}, sorted(entries(d) if points is None else points)
    while todo:
        p = todo.pop()
        while 0 <= p < len(d) - 1 and p not in ops:
            op, ln = d[p], d[p + 1]
            if op == INLINE:
                q = d.index(0, p + 3)
                inline[p + 3] = (p, q + 1)
                ops[p] = (op, d[p:q + 1])
                p = q + 1
                continue
            if op in TABLES:
                targets, end = table_targets(d, p, TABLES[op])
                tables[p] = (targets, end)
                ops[p] = (op, d[p:end])
                todo += targets
                break
            if op == SWITCH:
                end = p + 4 + d[p + 3] * 4
                targets = list(struct.unpack_from(f"<{d[p + 3]}I", d, p + 4))
                tables[p] = (targets, end)
                ops[p] = (op, d[p:end])
                todo += targets
                p = end
                continue
            if op == BRANCH:
                ops[p] = (op, d[p:p + 11])
                todo += struct.unpack_from("<2I", d, p + 3)
                break
            if ln < 2 or p + ln > len(d):
                raise ValueError(f"bad op {op:#x} len {ln} at {p:#x}")
            ops[p] = (op, d[p:p + ln])
            if op in JUMPS and ln >= 6:
                t = struct.unpack_from("<I", d, p + ln - 4)[0]
                if 0 < t < len(d):
                    todo.append(t)
            if op in STOPS:
                break
            p += ln
    return ops, tables, inline


def message_refs(ops):
    """{message offset: [operand offsets]} from 46 07 00 <u32>."""
    out = collections.defaultdict(list)
    for o, (op, raw) in ops.items():
        if op == 0x46 and raw[2] == 0 and len(raw) == 7:
            out[struct.unpack_from("<I", raw, 3)[0]].append(o + 3)
    return dict(out)


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    ops, tables, inline = walk(d)
    print("ops", len(ops), "tables", len(tables), "inline", len(inline), "messages", len(message_refs(ops)))
    if "--ops" in sys.argv:
        c = collections.Counter((v[0], len(v[1])) for v in ops.values())
        print(sorted(c.items(), key=lambda kv: -kv[1])[:60])
