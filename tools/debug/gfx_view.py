"""One sheet of sprites by exact label, on grey with a 10/50 px ruler, to read them and write data/gfx.tsv rows.
usage: gfx_view.py OUT.png LABEL[:x,y,w,h].. [--zoom Z] [--built] (--built: the English sprite as the build draws it)"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gen_gfx
import sprite

GREY, TICK = (92, 92, 108, 255), (255, 255, 0, 255)


def main():
    args = sys.argv[1:]
    zoom = 2
    if "--zoom" in args:
        i = args.index("--zoom")
        zoom = float(args[i + 1])
        del args[i:i + 2]
    built = "--built" in args
    if built:
        args.remove("--built")
    out, shots = args[0], []
    rows = gen_gfx.rows() if built else {}
    for spec in args[1:]:
        lab, _, crop = spec.partition(":")
        img = gen_gfx.fitted(lab, rows[lab])[0] if built and lab in rows else sprite.image(lab)
        ox, oy = 0, 0
        if crop:
            ox, oy, w, h = map(int, crop.split(","))
            img = img.crop((ox, oy, ox + w, oy + h))
        shots.append((spec, img.resize((int(img.width * zoom), int(img.height * zoom)), Image.NEAREST), ox, oy))
    width = max(s[1].width for s in shots) + 40
    sheet = Image.new("RGBA", (width, sum(s[1].height + 30 for s in shots)), GREY)
    d = ImageDraw.Draw(sheet)
    y = 0
    for spec, im, ox, oy in shots:
        d.text((2, y + 1), spec, fill=TICK)
        y += 16
        sheet.alpha_composite(im, (34, y + 10))
        for v in range(ox + (-ox % 10), ox + int(im.width / zoom), 10):  # x ruler
            x = 34 + int((v - ox) * zoom)
            d.line((x, y + 6, x, y + 9), fill=TICK)
            if v % 50 == 0:
                d.text((x + 1, y - 4), str(v), fill=TICK)
        for v in range(oy + (-oy % 10), oy + int(im.height / zoom), 10):  # y ruler
            t = y + 10 + int((v - oy) * zoom)
            d.line((29, t, 33, t), fill=TICK)
            if v % 50 == 0:
                d.text((2, t - 5), str(v), fill=TICK)
        y += im.height + 14
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
