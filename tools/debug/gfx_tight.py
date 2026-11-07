"""tight.py LABEL x0,y0,x1,y1 ..: tight ink box (x,y,w,h) inside each rough rect."""
import sys
sys.path.insert(0, "tools")
import sprite

lab = sys.argv[1]
img = sprite.image(lab)
for r in sys.argv[2:]:
    x0, y0, x1, y1 = map(int, r.split(","))
    bb = img.crop((x0, y0, x1, y1)).split()[3].point(lambda v: 255 if v > 0 else 0).getbbox()
    if bb:
        print(f"{x0 + bb[0]},{y0 + bb[1]},{bb[2] - bb[0]},{bb[3] - bb[1]}")
    else:
        print("empty", r)
