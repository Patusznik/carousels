# Brand kit: making the look the user's own

The brand kit lives in `~/Carousels/_brand/` and is shared by every carousel. Build it on the first run (kickoff
brief, step 4). Every choice has a default: if the user says "you pick", choose from their inspo folder.

## 1. Name and avatar

- Handle shown on slides: `@name`. Display name for profile and post mockups.
- Avatar: a square-ish photo in `_brand/avatar.png` (optional).

## 2. Colors

Get 2-4 colors, then fill all theme roles from them.

- From hex codes the user gives.
- From `1-style-inspo`: read the images, pick a background, a text color and 1-2 accents. Show swatches as a test
  slide before saving.
- Check contrast: body text on its background must read at phone size. Text on photos uses `ink_on_photo`.
- Avoid a terracotta + cream combination with a sparkle glyph: it reads as another brand.

Roles (all required): `cream` light background · `cream2` second light layer · `paper` · `espresso` text and dark
background · `espresso2` secondary text · `terracotta` accent · `terracotta2` light accent on photos and dark slides ·
`plum` second accent · `ink_on_photo` · `surface` windows and cards · `on_accent` text on the accent · `sticky` · `ok`.

## 3. Fonts: the user can choose their own

Two choices: a **title** font (`display`, plus `accent` for italic words) and a **text/UI** font (`body`, `label`).
`mono` stays a monospace for terminal windows. Offer these routes:

1. **A font installed on their computer** (Mac system fonts like Didot, Futura, Avenir; Windows fonts like Segoe UI,
   Georgia, Bahnschrift; fonts they activated or bought). Use it by name through `local()`, never copy the file anywhere:
   ```json
   {"family": "Title", "local": ["Didot", "Didot-Regular"], "file": "gfs-didot-latin-400-normal.woff2", "weight": 400}
   ```
   `file` is an optional free fallback in case the font is missing. Find exact names:
   Mac: `system_profiler SPFontsDataType | grep -i "full name: didot"`. Windows: the PowerShell font list in SKILL.md.
   Didot and Futura exist only on Macs: on Windows they fall back to the free files.
2. **A font file they own a license for** → they drop it in `_brand/fonts/`. Copy it to the engine's
   `templates/fonts/` for rendering; it never leaves their computer. Remind them their license decides where they may use it.
3. **A free Google Font (SIL Open Font License).** Download it from npm, never from random font sites:
   ```bash
   cd "$(mktemp -d)" && npm pack @fontsource/<font-name> && tar xzf *.tgz
   cp package/files/*-latin-400-normal.woff2 package/files/*-latin-ext-400-normal.woff2 ~/Carousels/_brand/fonts/
   ```
   Keep the license text (`package/LICENSE`) next to the files.
4. **Built in, free (OFL):** Anton, Instrument Serif, Inter, JetBrains Mono, Playfair Display, GFS Didot, Jost.

Not sure? Render one test slide with three pairs and let them pick, e.g. Playfair Display + Inter (classic),
Anton + Inter (loud), Instrument Serif + Jost (soft editorial).

## 4. Photo look

Starting points for `grade`; tune by eye on a test slide with their photo.

| look | wb [R,G,B] | contrast | fade [black, white] | saturation | grain |
|---|---|---|---|---|---|
| warm | [1.03, 1.0, 0.96] | 1.05 | [0.03, 0.98] | 0.95 | 0.05 |
| neutral | [1.0, 1.0, 1.0] | 1.03 | [0.02, 0.99] | 1.0 | 0 |
| cool | [0.97, 1.0, 1.04] | 1.05 | [0.03, 0.98] | 0.9 | 0.05 |
| film | [1.02, 1.0, 0.97] | 0.98 | [0.07, 0.95] | 0.85 | 0.12 |
| black and white | [1.0, 1.0, 1.0] | 1.1 | [0.04, 0.97] | 0 | 0.08 |

Add a light `vignette` (0.05-0.12) for a softer edge. After changing the grade: `photos.py "$P" --force`.

## 5. UI style

- **Mockups on**: the `os` layout on most slides; ask which elements they like (bubbles, dialogs, windows, terminal,
  notifications, a Finder-style file window, profile card). Elements can stand behind the person (`layer=behind`).
- **Clean**: `cover`, `photo`, `split`, `text`, `list`, `quote`, `cta` only.
- Set `"auto"` in the theme to the layouts the script import should prefer.

## 6. Fixed bits

- Slide counter on or off (`counter=off`).
- A small label on every slide (`kicker`), e.g. a series name.
- CTA wording: `strings` in `carousel.json` overrides the default lines (`swipe`, `save`, `share`, `comment`,
  `cta_title`). Default text in English is generic; write theirs.

## 7. Save it

- `_brand/brand.md`: the choices in plain words (handle, hex codes, fonts, photo look, UI style, fixed bits), so the
  user can read and edit it.
- `_brand/theme.json`: a full engine theme. Start from the `lilac` preset in `engine/themes/` (the light purple
  look from the @codecoffeechaos example: Didot + Futura, lavender desktop), then replace colors, fonts,
  `font_faces`, `grade`, `grain`, `auto`. Name it `brand-<handle>`.
- Show one finished test slide with their photo before the first real render.
