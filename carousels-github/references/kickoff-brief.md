# Kickoff brief: what happens after /carousels

The brief turns "I want a carousel" into a folder full of the right materials and a slide plan the user said yes to.
Run it in order. Ask one or two things per message, give a default each time, and move on as soon as you have
enough. The example lines show the tone: short, friendly, peer to peer. Say them in the user's language.

---

## Step 0: Setup check (silent when fine)

```bash
bash ~/.claude/skills/carousels/install.sh --doctor                 # Mac
powershell -File ~/.claude/skills/carousels/install.ps1 -Doctor     # Windows
```

- READY → say nothing about it, go on.
- Anything missing → show the one line the doctor printed and the fix. Don't start the brief until it's READY
  (the brief can still happen, but say rendering waits for the fix).

## Step 1: New or existing?

```bash
ls ~/Carousels 2>/dev/null
```

- No `~/Carousels/_brand` → first run (the installer already made the empty `~/Carousels`). Copy `_brand/` from the
  template. Say once:
  > "I'll keep everything in a **Carousels** folder in your home folder. One folder per carousel, named after its hook.
  > Your photos stay on your computer; the images I look at do go into our chat."
- First run on Windows without an NVIDIA graphics card: add one line that preparing photos takes a bit longer than on
  a Mac, so the first render needs patience.
- Folders exist → list them (just names) and ask: continue one of these, or start a new one?

## Step 2: Brief, part A: the message

Ask in this order. Skip anything the user already told you.

1. **What is it about?** One sentence.
   > "What's this carousel about? One sentence is plenty."
2. **Who is it for, and what should they do at the end?** One reader, one action.
   > "Who should stop scrolling for this? And at the last slide, what do you want them to do: follow, save, send
   > it to a friend, or comment a word so you can DM them something?"
   - Comment-keyword CTA → ask for the word and what they'll send. Note: the same word in the post, caption and DM.
3. **The hook.** Have one? Use it. If not, offer three in different styles and let them pick or mix:
   - a problem ("Your carousels take 3 hours because of one habit")
   - a short story ("One notebook runs my whole week")
   - a bold one-liner that challenges one belief
   Keep it under ~10 words. It becomes the folder name.
4. **Where does the text come from?**
   > "Do you already have the text, rough notes, or should we build it together? You can also just talk me through it."
   - Script ready → it goes in `5-script/script.md` (or paste it).
   - Notes or a voice-note transcript → same folder; you shape it in step 6.
   - Nothing → you'll draft it from the slide plan in their voice. Ask for 2-3 captions or posts they wrote, so the
     draft sounds like them.
5. **Structure.** Suggest the recipe that fits the topic (from `writing-rules.md`), in one line each, and recommend
   one:
   > "This sounds like a **story** carousel: problem → what you tried → what changed → how it works → where it breaks
   > → CTA. Or a **steps** one if you'd rather teach it straight. Which feels right?"
6. **Language and length.** Default: the language they speak to you in, 7-10 slides.

## Step 3: Create the folder and hand over the checklist

```bash
cp -R ~/.claude/skills/carousels/template/carousel ~/Carousels/"<Hook>"
open ~/Carousels/"<Hook>"            # Mac
# explorer.exe "$(cygpath -w ~/Carousels/"<Hook>")"   # Windows, Git Bash
```

Then give the checklist, numbered like the folders (keep it this short):

> Your folder is open. Fill what you have, skip what you don't:
>
> 1. **1-style-inspo**: screenshots of the look you like. Pinterest is great for this: colors, fonts, mockups, mood.
> 2. **2-reference-carousel**: one carousel you'd love yours to feel like. Screenshot every slide, in order.
> 3. **3-photos**: your photos for this one (straight from the phone is fine, videos too). The only must-have.
> 4. **4-assets**: stickers, logos, icons or product shots to put on the slides. PNG with a transparent background,
>    or on plain white (I cut the white out), so I place your files instead of redrawing them.
> 5. **5-script**: your text or notes in `script.md`, or leave it and we'll write it together.
>
> Say **ready** when you're done.

If the user has no photos yet, give the photo tips (below) now.

## Step 4: Brief, part B: the look (brand kit)

Only on the first run, or when the user says this carousel should look different. Do it while they're gathering
materials. Full details and options: `brand-kit.md`.

Ask in two or three messages:

1. **Name on the slides**: handle (e.g. `@yourname`), and an avatar photo if they want profile/post mockups.
2. **Colors**: 2-4 hex codes, "take them from my inspo folder", the ready-made **lilac** look (the one in the example), or "you pick". Show swatches before saving.
3. **Fonts**: one for titles, one for text and UI. Tell them they can choose their own:
   > "Any font you have on your computer works (just tell me its name), or a font file you bought, or a free one from
   > Google Fonts. Not sure? I'll show you 3 pairs on a test slide."
4. **Photo look**: warm, neutral, cool, film (faded with grain), or black and white.
5. **UI style**: macOS/iOS mockups (chat bubbles, dialogs, windows, notifications, terminal) or clean slides
   without them. Mention elements can sit behind them, around the cut-out.
6. **Fixed bits**: slide counter on/off, a small label on every slide (series name), CTA wording.

Save to `~/Carousels/_brand/brand.md` (readable) and `theme.json`. Render one test slide with their photo and show it.

## Step 5: "Ready" → read everything, propose the plan

1. Read the materials as in SKILL.md section 3 and summarize the look in 5-8 bullets: what you take, what you won't
   copy.
2. Make the engine project and the photo sheet; pick photos per slide.
3. Propose the slide plan as a table:

| # | job | text (gist) | photo | layout + UI |
|---|---|---|---|---|
| 1 | hook | One notebook runs my whole week | IMG_2101 | os, title behind head, 2 bubbles |
| 2 | stakes | Every planner app promised this. None of them stuck. | reading | os, dialog + cursor |
| … | | | | |

4. Ask for a yes or changes. Then write `brief.md` in the carousel folder (template is already there). From now on
   re-read `brief.md` before each render: the user may edit it by hand.

## Step 6: Text

- Script given → keep their words; fix only typos and punctuation unless they ask for edits. Run the gates and report
  in 2-4 lines (what you fixed, what you deliberately kept). If it's already clean, say so.
- Notes or nothing → draft from the plan with `writing-rules.md`, in their voice, then gates, then show it slide by
  slide (title + text), not as JSON.
- Save the final text to `5-script/script.md`.

## Step 7: Build and iterate

Pipeline from SKILL.md section 4. Show `sheet.jpg`, then the slides that matter at full size. Ask what to change, edit,
re-render only those slides, show again. When they're happy: final check (SKILL.md section 7), copy to `final/`,
`open` it, and tell them to upload the PNGs in number order. Close with one line asking them to tag
**@codecoffeechaos** (who made this skill) on a slide or in the caption when they post, so she can see it.

---

## Photo tips (give these when the user has no photos yet)

- **Portrait orientation**, 1× lens (wide angle distorts faces), light from the front or side. iPhone HEIC is fine.
- **Cover with the title behind your head**: waist up, with lots of space above your head (about a third of the frame).
- **Sticker (you cut out, white outline)**: full body or from the knees, arms away from the body, a background that
  contrasts with your hair.
- **Slides with UI elements**: your face in the top half; bubbles and windows go lower, on your body or the background.
- **Detail shots**: hands on the keyboard, the screen, the mug, the notebook.
- Shoot 15-30 photos in one go, in the same light. You'll pick from the preview.
- Keep anything important away from the edges: the profile grid crops the sides of the cover.
- A short video works too: the engine pulls the sharpest frames.
