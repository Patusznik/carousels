---
name: carousels
description: Turns your own photos into Instagram carousels (1080×1350 PNGs in order + a PDF) on a Mac or Windows PC, with optional macOS/iOS-style UI mockups (chat bubbles, dialogs, windows, notifications) that can sit in front of you or behind your cut-out. On /carousels it runs a short brief, sets up a folder for the carousel (style inspo, reference carousel, photos, assets, script), helps you structure and write the slides, then renders them and edits them as you talk. Use when someone wants to make, plan, write or fix an Instagram carousel from their photos, or shows a carousel whose look they want.
---

# Carousels: your photos → Instagram slides

Everything runs locally on the user's computer: a Mac with Apple Silicon (recommended) or a Windows 10/11 PC.
The engine prepares photos (color grade, person cut-out), lays out slides in headless Chrome and renders PNG + PDF.

```bash
S=~/.claude/skills/carousels          # this skill
E=$S/engine                           # the engine scripts
PY=~/.carousels/venv/bin/python       # the skill's own Python (Windows: ~/.carousels/venv/Scripts/python.exe)
C=~/Carousels                         # the user's main folder: one subfolder per carousel + _brand/
```

Run every engine script as `"$PY" $E/<script>.py …`. If `$PY` doesn't exist, the skill isn't installed: give the user
the install command from section 1.

**Custom or test installs:** if `$E/paths.json` exists, it wins: `home` replaces `~/.carousels` (so
`PY=<home>/venv/bin/python`) and `work` replaces `~/Carousels` (so `C=<work>`). A test install made with
`CAROUSELS_SANDBOX` keeps the skill in `<sandbox>/.claude/skills/carousels`, so `S` is the folder this SKILL.md is in.

### Mac or Windows

Commands in this file are written for the Mac. On Windows, translate them:

| | Mac | Windows |
|---|---|---|
| main folder | `~/Carousels` | `C:\Users\<name>\Carousels` (`~/Carousels` in Git Bash) |
| Python | `~/.carousels/venv/bin/python` | `~/.carousels/venv/Scripts/python.exe` |
| open a folder or image | `open "<path>"` | `explorer.exe "<path>"` (Git Bash) / `start "" "<path>"` |
| setup check | `bash $S/install.sh --doctor` | `powershell -ExecutionPolicy Bypass -File $S/install.ps1 -Doctor` |
| installed fonts | `system_profiler SPFontsDataType \| grep -i "full name: <font>"` | `powershell -NoProfile -c "Add-Type -AssemblyName System.Drawing; (New-Object System.Drawing.Text.InstalledFontCollection).Families \| % Name"` |
| file manager | Finder | File Explorer |

- Claude Code on Windows runs commands in Git Bash when Git for Windows is installed, otherwise in PowerShell.
  Check which one you're in and write commands for it.
- On a PC without an NVIDIA graphics card the cut-out runs on the processor: preparing photos takes longer. Say so
  once before the first render, so a slow first run doesn't look like a hang.
- Didot and Futura exist only on Macs. On Windows those themes fall back to free stand-ins (GFS Didot, Jost); offer
  the user a font they have instead.
- iPhone photos (HEIC) open on both systems; videos need ffmpeg (the installer adds it).

## 0. Ground rules

- **Talk in the user's language.** Folder names, file names and the files you create stay in English.
- **One or two questions at a time.** Never a wall of questions. Offer a default every time ("or say *you pick*").
- **Show pictures, never JSON.** After every change, look at the preview yourself (`Read` the image) and tell the user
  to look too (open it for them: `open` on a Mac, `explorer.exe` on Windows). Commands and paths go in code blocks only when the user needs to run them.
- **Nothing covers the face.** Bubbles, windows and text go on the body, legs or background. A title placed *behind* the
  head on purpose is the only exception. Check every slide with UI on it at full size.
- **Their words, their facts.** Never invent results, numbers, quotes or experiences. Missing fact → ask, or leave a
  visible `[placeholder]` and say so.
- **Legal sources only.** Fonts: installed on their computer (used by name), files they own, or OFL fonts. Assets: only what
  the user has the rights to. Never download from Instagram, TikTok or Pinterest yourself: the user saves screenshots.
- **Privacy, said once on first run:** photos are processed on their computer, but any image you look at (previews,
  inspo, photos) is sent into this conversation with Claude.
- **The look must be theirs.** Take the *system* from references (grid, type scale, rhythm, photo treatment), never
  someone else's logo, brand mark or signature graphic.

## 1. When the skill is invoked

Follow `references/kickoff-brief.md` step by step. In short:

1. Setup check (`bash $S/install.sh --doctor` on a Mac, `install.ps1 -Doctor` on Windows → READY, or exactly
   what's missing). Not installed or broken → the user runs the installer again in Terminal / PowerShell:
   Mac `curl -fsSL https://carousels.cyberspell.tech/install.sh | bash`,
   Windows `irm https://carousels.cyberspell.tech/install.ps1 | iex`.
2. Existing carousels? (`ls $C`) → continue one, or start a new one.
3. **Brief, part A (the message):** topic, reader, one CTA, hook, where the text comes from, structure recipe.
4. Create `$C/<Hook>/` from `$S/template/carousel/`, open it in Finder or File Explorer, tell the user what goes in each folder.
5. **Brief, part B (the look):** first run only (or "change the look for this one"): brand kit
   (`references/brand-kit.md`): handle, avatar, colors, fonts, photo look, UI style.
6. User says *ready* → read all materials (section 3), propose the slide plan, write `brief.md`, get a yes.
7. Write or polish the slide text (`references/writing-rules.md`), run the gates, show it.
8. Build, render, show `sheet.jpg`, edit by dictation, final check, copy to `final/`.

Shortcuts: user already has photos and a script → do steps 1, 2, 4, then 6. "Cheat sheet" / "what can I say" →
show `CHEATSHEET.md`. Invoked on a phone or in a chat without their computer: run the brief and write the script here,
and say the rendering happens in Claude Code on their Mac or PC.

## 2. The folder system

```
~/Carousels/
  _brand/                      shared by every carousel (made once, in the brand kit step)
    brand.md                   handle, colors, fonts, photo look, fixed labels: human-readable
    theme.json                 the same as an engine theme
    avatar.png                 for profile / post elements (optional)
    fonts/                     font files the user owns (optional)
  <Hook of the carousel>/      one folder per carousel, named after its hook
    1-style-inspo/             Pinterest saves: colors, fonts, UI mockups, the mood they like
    2-reference-carousel/      the one carousel they want theirs to feel like, every slide in order
    3-photos/                  their photos (HEIC/JPG/PNG) and short videos
    4-assets/                  SVG or transparent PNG: logos, icons, stickers, app screenshots to place as-is
    5-script/script.md         their text, notes or a rough brain dump
    brief.md                   written by Claude in the brief, read before every render
    final/                     finished slides: 01.png, 02.png… + carousel.pdf + sheet.jpg
    .build/                    engine project (hidden; never send the user here)
```

- Folder name from the hook: keep words and spaces; drop `/ : . ? * " < > |` and emoji; max ~60 characters.
  (A dot in a folder name confuses the engine.) Example: `One notebook runs my whole week`.
- Only `3-photos/` is required. Empty inspo / reference / assets / script folders are fine: say what you'll do instead
  (brand kit look, your own structure, no assets, write the script together).
- Create a new carousel: `cp -R "$S/template/carousel" "$C/<Hook>"`, then open it in Finder / File Explorer.
- First run (no `$C/_brand` yet): `mkdir -p "$C" && cp -R "$S/template/brand" "$C/_brand"`.
- Claude Code is usually started inside `~/Carousels`, so paths under it are local; the engine and the skill live
  outside it, so the user gets permission prompts for those commands. Tell them once that allowing them is expected.

## 3. Reading the materials

Do this when the user says *ready*. Look at every image with `Read` (PDFs with `pages`). Large folders: contact sheet
first, then the ones that matter.

- **1-style-inspo** → the mood: palette (give 3-5 hex values), type (serif / sans, caps, italics, weight),
  photo treatment (warm, faded, grain, black and white, cut-outs, collage), UI elements they keep saving.
- **2-reference-carousel** → the system: grid and margins, where the title sits, type scale, how photos are used,
  repeated elements (counter, arrows, handle, numbers), slide rhythm (what follows what), hook style, CTA style.
  Screen recordings: extract frames (`ffmpeg -i in.mov -vf fps=2 frames/%03d.jpg`) and read the frames.
- Tell the user in 5-8 bullets: what you'll take, and what you won't copy (logos, brand marks, signature graphics).
- **3-photos** → `"$PY" $E/photos.py "$P" --sheet` after the project exists (section 4), then `Read`
  `$P/work/photos_sheet.jpg`. Note which photos fit a cover (room above the head), stickers (full body, clean edges),
  UI slides (face in the top half).
- **4-assets** → list them with what each one is. They get placed as they are: never redraw, recolor or "improve"
  an asset, and never draw a logo you weren't given. If something they need is missing (an app icon, a logo), ask
  for the file. SVG: convert it to a PNG at least 1200 px wide first (the engine reads PNG/JPG).
- **5-script** → read it. Script, rough notes or empty: see `references/writing-rules.md`.

## 4. Pipeline

```bash
D="$C/<Hook>"; P="$D/.build"
"$PY" $E/new_carousel.py "$P" --theme <brand theme, or lilac> --handle @handle --lang en --photos "$D/3-photos"
"$PY" $E/photos.py "$P" --sheet         # all photos with names → $P/work/photos_sheet.jpg
"$PY" $E/script.py "$P" "$D/5-script/script.md"   # script → slides (or slide.py add … when dictating)
"$PY" $E/slide.py "$P" show             # list of slides
"$PY" $E/render.py "$P"                 # → $P/out/01.png…, PDF, sheet.jpg
"$PY" $E/render.py "$P" --only 3,4      # re-render only what changed
```

- Assets: `mkdir -p "$P/assets" && cp "$D/4-assets/"*.{png,jpg,jpeg,webp} "$P/assets/" 2>/dev/null` (again whenever
  the user adds some).
- Photos added to `3-photos/` later: copy the new ones into `$P/photos/` (videos: `photos.py "$P" --video <file>`).
- Before `script.py`, strip the template's instructions and examples from `script.md` if the user left them in.
- First render prepares each photo (grade + cut-out, a few seconds each, cached after that).
- Look at `sheet.jpg` before showing anything (slides there are as small as in the feed), then every slide with a
  cover title or UI at full size.
- Done: `cp "$P"/out/[0-9]*.png "$P"/out/sheet.jpg "$D/final/"` and copy the PDF as `final/carousel.pdf`.
  Then open `final/` for them. Upload the PNGs to Instagram in number order.
- Hand-off line, once per carousel: ask them to tag **@codecoffeechaos** (who made this skill) on a slide or in the
  caption when they post it. One friendly sentence, never a condition, never repeated.

### Layouts

| layout | what it is | needs |
|---|---|---|
| `cover` | full-bleed photo, big title **behind the head**, subtitle at the bottom | `photo`, `title` (2 lines with `\|`) |
| `cover-sticker` | plain background, title, the person as a cut-out sticker on an accent shape | `photo` with the full figure |
| `photo` | full-bleed photo, title and text at the bottom on a shade | `photo` |
| `split` | photo on top (56%), title and text below | `photo` |
| `text` | text only, big slide number behind; optional small sticker | `title`/`body`, optional `sticker` |
| `list` | title + numbered points | `items` |
| `quote` | dark slide, quote in serif italics | `quote` (or `title`), optional `by` |
| `cta` | accent slide: title, save / share / comment, optional sticker | nothing (default text), optional `title`, `body`, `sticker` |
| `os` | photo (or a desktop wallpaper) + macOS/iOS UI elements, in front of or behind the person | see below |

Rules: slide 1 is a cover (`cover`, `cover-sticker` or `os` with a title); the last slide carries the CTA; mix photo
and text slides (max 2 text-only slides in a row); max 20 slides, 7-10 works well.

### The `os` layout (the flagship look)

- Slide keys: `photo`, `title` (with a photo it sits behind the head by default; `title_pos=top|bottom|behind`), `body`,
  `menubar=on`, `select_person="you.png"` (editor-style selection box around the person), `overlap` (how deep the head
  goes into the title), `title_size`, `zoom`, `bg_blur`.
- Elements: `slide.py "$P" ui N add type=… at=… [w= rot= layer=behind]`, `ui N set K k=v`, `ui N rm K`, `ui N list`,
  `ui N clear`.
- Types: `bubble` (text, side=in|out, time) · `input` (text, select, send) · `dialog` (title, text, buttons="A|B",
  primary, glyph, icon; `buttons=none` for none) · `notif` (app, title, text, glyph, icon) · `pill` (label, sub, glyph) ·
  `window` (title_bar + kicker/title/body · `lines="$ cmd|> said|✓ done"` terminal · `rows="App (status)|…"` list with
  `button` and `pick` · `photo=` preview · `before=` + `photo=` before/after · `photos=a,b,c` Finder) ·
  `folder` (label, tag, sticker) · `profile` (name, avatar, bio, stats, follow) · `post` (photo, name, avatar, text) ·
  `sticker` (photo) · `sticky` (text) · `cursor` (without `at` it aims at the main button) · `counter` ·
  `image` (a file from `$P/assets/`: `src=NAME w=400 at=… rot=… [outline=on] [shadow=off] [cross=on] [key=none]`).
- `image`: a JPG or PNG on a white background gets the white cut out automatically (`key=none` keeps it);
  `outline=on` adds a white sticker edge; `cross=on` crosses it out with a big red X. Several images with small `rot`
  values read as a sticker collage.
- `at`: `top|upper|center|lower|bottom` + `-left|-right`, or `X,Y` in %, or `L,Y` / `R,Y` / `C,Y` (against the
  left / right edge / centered, at height Y %).
- `layer=behind` puts an element between the photo and the cut-out person: it shows around them, not over them.
- Glyphs: film, warn, comment, photo, bookmark, heart, call, moon, check… No sparkle-in-a-circle in the accent color.
- No real company logos inside UI elements unless the user put that logo in `4-assets` and has the right to use it.

## 5. Dictation → commands

```bash
"$PY" $E/slide.py "$P" add [--at N] layout=… title="…" …   # new slide
"$PY" $E/slide.py "$P" set N key=value …                   # change ("-" removes a key); N = all → every slide
"$PY" $E/slide.py "$P" rm N · mv N M · dup N · photos       # remove / move / duplicate / list photos
```

Keys: `layout`, `title` (`|` = new line, `*word*` = accent italic), `body` (empty line = paragraph, `**x**` = bold),
`kicker` (small label top left), `items="a|b|c"`, `quote`, `by`, `photo=NAME` (file name without extension),
`sticker=NAME`, `focus=X,Y` (point of the photo at the center, 0-1), `zoom=1.3`, `head_y=0.25` (where the top of the
head lands, 0-1), `title_size=PX`, `overlap=0-3`, `counter=off`, `actions=save,share,comment`, `labels.save="…"`.

Typical phrases: `CHEATSHEET.md`. After each batch of edits: `render.py "$P" --only <changed>` and show the result.
Copy shell quoting carefully: titles with apostrophes go in double quotes.

## 6. The look: brand kit and theme

Full guide: `references/brand-kit.md`. The theme is `$C/_brand/theme.json`; before each render copy it to
`$E/themes/<name>.json` (and any font files from `$C/_brand/fonts/` to `$E/templates/fonts/`), because the engine reads
themes from its own folder. The copy in `_brand/` is the master: a skill update must never wipe it.

- `colors` are roles: `cream` (light background), `cream2` (second light layer), `paper`, `espresso` (text and dark
  background), `espresso2` (secondary text), `terracotta` (accent), `terracotta2` (light accent on photos and dark
  slides), `plum` (second accent), `ink_on_photo` (text on photos), `surface` (windows and cards), `on_accent`,
  `sticky`, `ok`. A theme needs all of them.
- `fonts`: `display` (titles), `accent` (italic words), `body`, `label` (UI), `mono` (terminal).
- `grade`: photo look (`wb`, `contrast`, `fade`, `saturation`, `shadow_tint`, `highlight_tint`, `vignette`).
  After a change: `photos.py "$P" --force`, then render.
- `grain`: 0 = none. Per-theme CSS overrides: `<name>.css` next to the JSON.
- One carousel looks different from the brand: put a theme in `$D/.build/` and set `"theme"` in `carousel.json`.

## 7. Check before you hand it over

- No text or UI on the face. The cover title reads at thumbnail size (check `sheet.jpg`).
- The head overlaps the cover title without eating a word (else `overlap=0` or a shorter line).
- Counters add up, the last slide has the single CTA, special characters render (ą, ü, é…).
- Cut-outs: no holes at hair or hands, no background left (look at covers and stickers full size).
- Assets look exactly like the files in `4-assets` (no blur from upscaling a small PNG: ask for a bigger file or SVG).
- Text passed the gates in `references/writing-rules.md`.

## 8. When something goes wrong

- **"no head found" / bad crop** → `focus=X,Y` (e.g. `0.5,0.3`) or `head_y`, maybe `zoom`.
- **Holes or background in the cut-out** → a photo with more contrast between hair and wall; or `layout=photo`.
- **HEIC won't open** → ask the user to export that photo as JPG (on iPhone: share it to Files as "Most Compatible").
- **Photo prep feels stuck on Windows** → it's running on the processor; check the progress output before calling it
  a hang. Fewer or smaller photos help.
- **Theme change not visible on photos** → `photos.py "$P" --force`.
- **Title too long** → the engine shrinks it to a minimum; if it still overflows or gets tiny, shorten it or split
  it with `|`.
- **A font falls back to something else** → the name in `local()` doesn't match the installed font: check the exact
  name (font lookup in the Mac or Windows table at the top).
