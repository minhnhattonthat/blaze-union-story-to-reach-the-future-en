"""Paste crops of sweep pages and whole images into one sheet, to read just the text-bearing parts.
usage: cropsheet.py OUT.png ITEM... where ITEM is PATH or PATH:x0,y0,x1,y1 (a Windows drive colon is fine)"""
import re
import sys

from PIL import Image

WIDTH = 1440
out = sys.argv[1]
parts = []
for item in sys.argv[2:]:
    m = re.fullmatch(r"(.+):(\d+),(\d+),(\d+),(\d+)", item)
    img = Image.open(m[1] if m else item).convert("RGBA")
    img = Image.alpha_composite(Image.new("RGBA", img.size, (0, 0, 0, 255)), img).convert("RGB")  # hide transparent pixels
    parts.append(img.crop(tuple(int(m[i]) for i in range(2, 6))) if m else img)
x = y = row = 0
placed = []
for c in parts:
    if x + c.width > WIDTH:
        x, y, row = 0, y + row + 4, 0
    placed.append((c, x, y))
    x += c.width + 4
    row = max(row, c.height)
sheet = Image.new("RGB", (WIDTH, y + row), (0, 0, 0))
for c, px, py in placed:
    sheet.paste(c, (px, py))
sheet.save(out)
print(sheet.size)
