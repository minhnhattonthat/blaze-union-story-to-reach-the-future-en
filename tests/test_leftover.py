"""Leftover pixels (D16): gen_gfx.english sweeps pieces of the Japanese a tight box cut off; `ygg` rows copy Yggdra art."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import leftover


def test_stray_and_sweep():
    leftover._selftest()


def test_extras_menu_has_no_debris():
    """2700@9c090 (Extra Contents) left bracket shadows and glyph edges beside its boxes before the sweep."""
    import gen_gfx
    import sprite
    rs = gen_gfx.rows()["2700@9c090"]
    assert leftover.stray(sprite.image("2700@9c090"), gen_gfx.english("2700@9c090", rs), [r[0] for r in rs]) == []


@pytest.mark.skipif(not (ROOT / "rom/Yggdra Union - We'll Never Fight Alone (USA).iso").exists(), reason="no Yggdra ISO")
def test_ygg_card_page_is_yggdra_art():
    import gen_gfx
    import ygg
    import numpy as np
    img = gen_gfx.english("264@0", gen_gfx.rows()["264@0"])
    assert np.array_equal(np.asarray(img), np.asarray(ygg.image("00266@0").convert("RGBA")))
