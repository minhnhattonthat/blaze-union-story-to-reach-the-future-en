"""gen_gfx's clears and vertical text on synthetic images (no game data needed)."""
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import gen_gfx


def test_mirror_takes_the_other_side():
    img = Image.new("RGBA", (20, 4), (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (3, 4), (9, 8, 7, 255)), (17, 0))  # art on the right edge
    gen_gfx.draw(img, (0, 0, 5, 4), "mirror", "")
    assert img.getpixel((0, 1)) == (9, 8, 7, 255) and img.getpixel((3, 1))[3] == 0


def test_inpaint_keeps_art_outside_letters():
    img = Image.new("RGBA", (12, 12), (200, 0, 0, 255))
    img.paste(Image.new("RGBA", (2, 2), (255, 255, 255, 255)), (5, 5))  # a white letter on red art
    gen_gfx.inpaint(img, (0, 0, 12, 12))
    assert all(abs(c - r) < 2 for c, r in zip(img.getpixel((5, 5)), (200, 0, 0, 255)))


def test_vertical_text_reads_down_and_hangs_from_the_top():
    img = Image.new("RGBA", (30, 180), (0, 0, 0, 0))
    gen_gfx.draw(img, (0, 0, 30, 180), "vbanner", "Short")
    bb = img.getbbox()
    assert bb[1] == 0 and bb[3] - bb[1] > bb[2] - bb[0]  # taller than wide, starts at the top
