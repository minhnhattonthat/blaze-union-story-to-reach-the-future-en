"""fits.py [PREFIX]: which data/gfx.tsv sprites fail to repack, and why."""
import sys
sys.path.insert(0, "tools")
import gen_gfx, gfx, sprite

pre = sys.argv[1] if len(sys.argv) > 1 else ""
bad = 0
for label, items in gen_gfx.rows().items():
    if not label.startswith(pre):
        continue
    try:
        img, s = gen_gfx.fitted(label, items)
        if s < 1:
            print(label, "scale", s)
    except Exception as e:
        bad += 1
        print(label, e)
print("failed", bad)
