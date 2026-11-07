# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `fonts/SourceSans3-Semibold.ttf` | https://github.com/adobe-fonts/source-sans (release branch, TTF/) | SIL OFL 1.1, `fonts/SourceSans-LICENSE.md` | yes, as rendered glyphs | All English text on fonts 1, 2, 3 (`tools/vwf.py`) | Rendered at 16, 15, 20 px with a 1 px black outline into the game's own palette |
| `fonts/SourceSans3-Bold.ttf`, `fonts/SourceSans3-Black.ttf` | https://github.com/adobe-fonts/source-sans (release branch, TTF/) | SIL OFL 1.1, `fonts/SourceSans-LICENSE.md` | yes, as rendered pixels | Sprite redraws (`tools/gen_gfx.py`, `data/gfx.tsv`) | Rendered, recoloured from the Japanese lettering, quantized to each sprite's palette |
