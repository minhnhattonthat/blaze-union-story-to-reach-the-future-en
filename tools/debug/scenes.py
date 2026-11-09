"""The scene list: reach every non-stage screen from a cold boot, each in its own emulator, with a shot to prove it.
usage: scenes.py [NAME..] [--out work/qa/scenes] [--jobs 6] [--iso ISO] [--states] [--stages] [--list]
Each scene is a list of steps; it passes when it ends in one of its modes and the final shot is not flat. Shots:
OUT/<name>.png; --states also writes work/states/<name>.ppst; --stages then runs warp_all.py for the 151 story stages.
Exit 1 if any scene fails. Addresses and how each path was found: docs/re/debug.md."""
import argparse
import shutil
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import warp

psp, ROOT = warp.psp, warp.ROOT
SEG1 = warp.SEG1
TITLE_MENU = SEG1 + 0x80668 + 0x82  # the title's menu item ids; poke 4 for extras (the real unlock is a cleared game)
CARD_LIMIT = SEG1 + 0x86F10 + 0xC  # cards to pick before circle starts the sortie
GAME_OVER_ID = SEG1 + 0x88540  # u16 index of the defeat text; 0 has no text and ends the emulator (only warps leave it 0)
SYS_PTR = warp.BASE + 0x271728  # system save: unlock bitfields in its first 0x50 bytes
CREDIT_STATE = SEG1 + 0x842A0 + 0xCF  # switch at 0x12CBD4


# Steps: (function, *args), run in order against one emulator.
def wait(run, n):
    while n > 0:  # one long run_to outlasts the debugger's 30 s socket timeout
        run.run_to(run.frame() + min(n, 1500))
        n -= 1500


def press(run, *keys, gap=40):
    for k in keys:
        run.press({k})
        wait(run, 6)
        run.press(set())
        wait(run, gap)


def until(run, modes, mash="circle", limit=12000):
    """Mash until the mode is in MODES (a tuple), then let go."""
    end = run.frame() + limit
    i = 0
    while warp.u32(run, warp.MODE) not in modes:
        assert run.frame() < end, f"mode {warp.u32(run, warp.MODE)} after {limit} frames, wanted {modes}"
        i += 1
        run.press({mash} if mash and i % 4 == 0 else set())
        wait(run, 10)
    run.press(set())


def stage(run, name, card=True):
    warp.warp(run, warp.stages().index(name), card=card)


def poke(run, addr, data):
    warp.poke(run, addr, data)


def var(run, n, v):
    warp.poke(run, warp.u32(run, warp.SAVE_PTR) + 0x20 + n, bytes([v]))


def mode(run, m):
    warp.poke(run, warp.MODE, struct.pack("<I", m))


def req(run, flags):
    warp.poke(run, warp.REQ, struct.pack("<I", warp.u32(run, warp.REQ) | flags))
    mode(run, 0)


def unlock(run):
    warp.poke(run, warp.u32(run, SYS_PTR), b"\xff" * 0x50)


def boost(run):
    """The battle boost option (0x5CA4): set when the credits end."""
    warp.poke(run, warp.u32(run, SYS_PTR) + 0xA4, b"\x01")


def pick_card(run, confirm=True):
    """Walk the list pressing circle until one card is taken (count at +0xD reaches the poked limit at +0xC): the owned cards
    sit at varying slots, blank slots ignore circle. With the limit met, circle then starts the sortie, on a card slot only."""
    warp.poke(run, CARD_LIMIT, b"\x01")
    for _ in range(16):
        press(run, "circle", gap=50)
        if run.ws.mem(CARD_LIMIT + 1, 1)[0]:
            break
        press(run, "down", gap=50)
    else:
        raise AssertionError("no card picked")
    wait(run, 60)
    if confirm:
        press(run, "circle")


COLD = [(warp.boot,)]


def title_route(run):
    """Logos, movie, then the title menu: frames from the boot route in docs/re/debug.md."""
    wait(run, 1400)
    press(run, "start", gap=300)
    press(run, "start", gap=300)
    wait(run, 6500)
    press(run, "start", gap=240)


TITLE = [(title_route,)]
PREP = COLD + [(stage, "1_02_A"), (until, (19, 20)), (wait, 180)]
CARDS = PREP + [(press, "circle"), (until, (23,), None, 600), (wait, 120)]
SORTIE = CARDS + [(pick_card,), (until, (24, 7), None, 900)]
FIELD = SORTIE + [(until, (15,), "circle", 6000), (wait, 120)]
MOVED = FIELD + [(press, "circle"), (press, "up", "right", "right", "right"), (press, "circle"), (wait, 120)]
UNION = MOVED + [(press, "square"), (wait, 120)]
READY = UNION + [(press, "circle"), (wait, 120)]
READY2 = READY + [(press, "circle"), (wait, 120)]
COMBAT = READY2 + [(press, "circle"), (until, (31,), None, 600)]
AFTER = COMBAT + [(until, (15,), "circle", 6000), (wait, 120)]
MENU = FIELD + [(press, "ltrigger"), (wait, 60)]
EXTRAS = TITLE + [(poke, TITLE_MENU, b"\x04"), (unlock,), (press, "circle"), (until, (4,), None, 300), (wait, 240)]
END = COLD + [(req, 0x200)]


def menu_item(n):
    return MENU + [(press, *["down"] * n), (press, "circle"), (wait, 120)]


def extra_item(*keys):
    return EXTRAS + [(press, *keys), (press, "circle"), (wait, 300)]


# name: (steps, allowed final modes). Stages are warp_all.py's job. Titles of 1_02_A's battle stand for the battle screens.
SCENES = {
    "boot_logos": (COLD + [(wait, 240)], (2,)),
    "boot_movie": (COLD + [(wait, 1400), (press, "start", ), (wait, 600)], (2,)),
    "title": (TITLE, (2,)),
    "title_load": (TITLE + [(press, "down"), (press, "circle"), (wait, 120)], (2,)),
    "title_continue": (TITLE + [(press, "down", "down"), (press, "circle"), (wait, 120)], (2,)),
    "title_option": (TITLE + [(press, "down", "down", "down"), (press, "circle"), (wait, 120)], (2,)),
    "title_option_full": (TITLE + [(boost,), (press, "down", "down", "down"), (press, "circle"), (wait, 120)], (2,)),
    "new_game": (TITLE + [(press, "circle"), (wait, 600)], (2, 5, 6, 7)),
    # with battle boost unlocked GAME START asks the difficulty first (4@5e190, issue #2)
    "new_game_difficulty": (TITLE + [(boost,), (press, "circle"), (wait, 240)], (2,)),
    "new_game_scroll": (TITLE + [(press, "circle"), (wait, 1800)], (2, 5, 6, 7)),
    "chapter_card": (COLD + [(stage, "2_01_A"), (wait, 420)], (5,)),
    "stage_card": (COLD + [(stage, "1_02_A"), (until, (6,), None, 600), (wait, 90)], (6,)),
    "event": (COLD + [(stage, "1_02_A"), (until, (7,), "circle", 2000), (wait, 300)], (7,)),
    "prep_charselect": (PREP, (19, 20)),
    "prep_status": (PREP + [(press, "triangle"), (wait, 120)], (21, 26)),
    "prep_equip": (PREP + [(press, "left"), (wait, 120)], (21,)),
    "prep_heal": (PREP + [(press, "right"), (wait, 120)], (20, 22)),
    "prep_wincond": (PREP + [(press, "ltrigger"), (wait, 120)], (18,)),
    "prep_map": (PREP + [(press, "rtrigger"), (wait, 120)], (16,)),
    "prep_location": (PREP + [(press, "rtrigger"), (wait, 120), (press, "triangle"), (wait, 120)], (16,)),
    "prep_deploy": (PREP + [(press, "square"), (wait, 120)], (16,)),
    "card_select": (CARDS, (23,)),
    "card_data": (CARDS + [(press, "down", "down", "down", "triangle"), (wait, 120)], (25,)),
    "card_sort": (CARDS + [(press, "select"), (wait, 60)], (23,)),
    "sortie_ok": (CARDS + [(pick_card, False), (wait, 30)], (24,)),
    "tutorial_intro": (SORTIE + [(until, (7,), None, 600), (wait, 700)], (7,)),
    "tutorial_map": (SORTIE + [(until, (7,), None, 600), (press, *["circle"] * 8)], (7,)),
    "field": (FIELD, (15,)),
    "field_status": (FIELD + [(press, "circle"), (press, "triangle"), (wait, 90)], (15,)),
    "field_moved": (MOVED, (15,)),
    "union": (UNION, (15,)),
    "battle_ready": (READY, (15, 30)),
    "combat_fight": (COMBAT + [(wait, 120)], (31,)),
    "combat_tip": (COMBAT + [(wait, 600)], (31,)),
    "combat_win": (COMBAT + [(wait, 1500), (press, "circle"), (wait, 300)], (31, 32)),
    "combat_result": (COMBAT + [(until, (32,), "circle", 6000), (wait, 60)], (32,)),
    "combat_exp": (AFTER, (15,)),
    "menu": (MENU, (15, 16)),
    **{f"menu_{n}": (menu_item(i), (15, 16, 18, 28)) for i, n in enumerate(
        ("endturn", "bigmap", "units", "cards", "weapons", "terrain", "objects", "tutorial", "rules", "suspend"))},
    "enemy_phase": (MENU + [(press, "circle"), (press, "circle"), (wait, 180)], (7,)),
    "turn_two": (MENU + [(press, "circle"), (press, "circle"), (until, (28, 29), "circle", 9000), (wait, 60)], (28, 29)),
    "victory": (FIELD + [(var, 0xA, 4), (mode, 7), (until, (34,), None, 300), (wait, 120)], (34,)),
    "victory_loot": (FIELD + [(var, 0xA, 4), (mode, 7), (until, (34,), None, 300), (wait, 240), (press, "circle"), (wait, 200)], (34,)),
    "victory_cards": (FIELD + [(var, 0xA, 4), (mode, 7), (until, (34,), None, 300), (wait, 240), (press, "circle", "circle"), (wait, 200)], (34,)),
    "game_over": (FIELD + [(var, 0xA, 2), (poke, GAME_OVER_ID, b"\x01\x00"), (mode, 7), (until, (11,), None, 300), (wait, 1200)], (11,)),
    "save_prompt": (FIELD + [(var, 0xA, 5), (mode, 7), (until, (35,), None, 300), (wait, 180)], (35,)),
    "save_dialog": (FIELD + [(var, 0xA, 5), (mode, 7), (until, (35,), None, 300), (wait, 180), (press, "circle"), (wait, 200)], (35,)),
    # 0-3 full endings (table 0x2B6480), 4-22 bonus scenes (table 0x2B64C0, 19 records of 12 bytes): 0x11F434
    **{f"ending_{n}": (COLD + [(var, 0xB, n), (req, 0x200), (wait, 4700)], (36,)) for n in range(23)},
    "credits_start": (COLD + [(var, 0xB, 0), (req, 0x200), (wait, 5000), (press, "circle"), (wait, 1200)], (36, 38)),
    "credits_cast": (COLD + [(var, 0xB, 0), (req, 0x200), (wait, 5000), (press, "circle"), (wait, 3000)], (38,)),
    "credits_staff": (COLD + [(var, 0xB, 0), (req, 0x200), (wait, 5000), (press, "circle"), (wait, 9000)], (38,)),
    # credit state 0x1E waits on 0x10E730 (the music stream), which never ends in headless: step past it
    "after_credits": (COLD + [(var, 0xB, 0), (req, 0x200), (wait, 5000), (press, "circle"), (wait, 9000), (poke, CREDIT_STATE, b"\x1f"), (wait, 600)], (38, 2)),
    "extras": (EXTRAS, (4,)),
    "extras_illust": (extra_item(), (4,)),
    "extras_sound": (extra_item("down"), (4,)),
    "extras_chronicle": (extra_item("right", "right"), (4,)),
    "extras_cards": (extra_item("up"), (4,)),
    "extras_fifth": (extra_item("right", "right", "right"), (4,)),
    # a few pages deep: item and card text have their own wrap, and only these books show every entry
    **{f"extras_item_{n}": (extra_item("right", "right", "right") + [(press, *["right"] * (n % 9), *["down"] * n), (wait, 90)], (4,))
       for n in (5, 13, 22, 31, 47, 64)},
    **{f"extras_card_{n}": (extra_item("up") + [(press, *["down"] * n), (wait, 90)], (4,)) for n in (12, 40, 77)},
    **{f"recap_{c}": (COLD + [(stage, f"{c}_01_A"), (wait, 420), (press, *["circle"] * 20), (wait, 120)], (5, 6, 7)) for c in range(2, 9)},
    "resume_prompt": (menu_item(9) + [(press, "circle"), (wait, 600), (press, "start"), (wait, 200), (press, "circle"), (wait, 240)], (2, 7, 15)),
    "tutorial_page": (menu_item(7) + [(press, "circle"), (wait, 240)], (7,)),
    "field_info": (FIELD + [(press, "cross"), (wait, 60)], (15,)),
    "field_threat": (FIELD + [(press, "triangle"), (wait, 60)], (15,)),
}


def run_scene(name, a):
    steps, modes = SCENES[name]
    out = Path(a.out) / "_run" / name
    shutil.rmtree(out, ignore_errors=True)
    run = psp.Run(psp.find_emu(None), a.iso, str(out))
    try:
        for fn, *args in steps:
            fn(run, *args)
        m = warp.u32(run, warp.MODE)
        path = run.shot("final.png")
        shutil.copy(path, Path(a.out) / f"{name}.png")
        if a.states:
            run.save_state(str(ROOT / "work/states" / f"{name}.ppst"))
        assert m in modes, f"mode {m}, wanted {modes}"
        assert not psp.blank(path), "flat shot"
    finally:
        run.close()
    shutil.rmtree(out, ignore_errors=True)


def one(name, a):
    cmd = [sys.executable, "-X", "utf8", __file__, "--child", name, "--out", a.out, "--iso", a.iso] + (["--states"] if a.states else [])
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1500)
    err = (r.stdout + r.stderr).strip().splitlines()
    return name, "" if r.returncode == 0 else (err[-1] if err else "failed")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--out", default=str(ROOT / "work/qa/scenes"))
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--iso", default=warp.ISO)
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--stages", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--child")
    a = ap.parse_args()
    if a.list:
        print("\n".join(SCENES))
        return
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.child:
        run_scene(a.child, a)
        return
    with ThreadPoolExecutor(a.jobs) as ex:
        res = list(ex.map(lambda n: one(n, a), a.names or list(SCENES)))
    bad = [r for r in res if r[1]]
    for n, e in bad:
        print("FAIL", n, e[:200])
    print(f"{len(res) - len(bad)}/{len(res)} scenes ok")
    code = 1 if bad else 0
    if a.stages:
        code |= subprocess.call([sys.executable, "-X", "utf8", str(Path(__file__).with_name("warp_all.py")), "--iso", a.iso])
    sys.exit(code)


if __name__ == "__main__":
    main()
