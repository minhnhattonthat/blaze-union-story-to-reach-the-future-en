"""Script records whose Japanese holds a card name and whose English spells it unlike the card art (2642 sprites, D2).
Prints lines for tools/tlfix.py (bNNN:n<TAB>English) with the art's spelling. usage: card_names.py > fixes.tsv"""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = {
    "ラウーガー": ("Rauger", "Rauher"),
    "ヴァイス": ("Vice", "Vise"),
    "リヴェリオン": ("Rebellion", "Revellion"),
    "マントラップ": ("Man Trap", "Mantrap"),
    "サンダーボルト": ("Thunderbolt", "Thunder Bolt"),
    "サンドストーム": ("Sandstorm", "Sand Storm"),
    "ロックフォール": ("Rockfall", "Rock Fall"),
}
lines = {}  # English -> [batch:n], from the batches' output
for f in glob.glob(str(ROOT / "work/tl/b*.out.tsv")):
    b = Path(f).name.split(".")[0]
    for row in open(f, encoding="utf-8"):
        n, _, en = row.rstrip("\n").partition("\t")
        lines.setdefault(en, []).append(f"{b}:{n}")
for f in sorted(glob.glob(str(ROOT / "script/*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    for r in d if isinstance(d, list) else d.get("records", []):
        en = new = r.get("en", "")
        for jp, (a, b) in ART.items():
            if jp in r.get("jp", ""):
                new = new.replace(a, b)
        if en != new:
            for at in lines.pop(en, []):
                print(at, new, sep="\t")
