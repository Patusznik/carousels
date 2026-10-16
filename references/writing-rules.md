# Writing rules for carousels

Use these when you draft, shape or check slide text. If the user has their own writing skill or voice guide, their
voice wins; these rules still decide the carousel's structure and the gates.

## 1. Sound like them

- Before drafting from scratch, read their script or notes, or ask for 2-3 captions they wrote. Match their sentence
  length, humor, slang and language.
- Second person, peer to peer. Share what worked; offer, don't order. No guru tone.
- "I" is for the hook or one story beat that earns trust. Then turn to the reader.
- Their facts only. No invented numbers, results, quotes or timelines. Missing → ask, or `[placeholder]` and flag it.

## 2. What keeps people swiping

1. **Challenge one belief.** Pick a single thing the reader assumes and question it. One per carousel.
2. **Curiosity before the lesson.** Open a loop first; teach after it's earned.
3. **One idea per slide.** Two ideas on a slide → split it.
4. **Every slide earns the next swipe.** If a slide could go without anyone missing it, cut it.
5. **The three-second test.** People skim. Each slide must land at a glance: title around 8 words max, body around
   25 words max, short lines.
6. **One CTA.** One action at the end. Two asks get neither.

### The beats

- **Slide 1, the hook.** Under ~10 words, readable as a thumbnail. Types: a problem, a short story, a bold one-liner.
- **Slide 2 raises the stakes. It does not answer the hook.** Name what not knowing costs, or widen the gap between
  where they are and the payoff. Answer here and they stop swiping.
- **The middle.** Story (problem → what they tried → what changed), then the value. Open the value with the
  **second-best** point and save the **best** one for the end of the run.
- **A rehook halfway** (around slide 5 of 10): one line that renews curiosity before the best part.
- **Where it breaks.** One honest slide: limits, who it's not for, what goes wrong. It builds trust.
- **CTA.** One action. With a comment keyword, the same word appears in the post, the caption and the DM.

## 3. Structure recipes

Suggest one in the brief. Each is a starting order, not a cage.

| recipe | slide order |
|---|---|
| **Story** | hook → stakes → the problem → what I tried → what changed → how it works (2-3 slides) → rehook → where it breaks → CTA |
| **Steps** | hook → stakes → why the usual way fails → step 1 … step n → the mistake to avoid → CTA |
| **Tips** | hook → stakes → tip (second best) → tips → rehook → tip (best) → CTA |
| **Before / after** | hook (the after) → stakes → before → the turning point → after → how → where it breaks → CTA |
| **Myth vs truth** | hook (the myth) → stakes → why people believe it → what's actually true → what to do instead → CTA |
| **Photo dump** | hook → one photo per beat with one line each → CTA |

If the user hands you a reference carousel or their own template, its structure wins: keep its beats and pacing, swap
in their content.

## 4. Gates: check every draft before you show it

Fix these silently, then report in 2-4 lines what you changed and what you deliberately kept. If the text is already
clean, say so and change nothing.

- **No em dashes** (—), and no en dashes (–) used as dashes. Use a period, comma, colon or a line break.
- **"Not X, it's Y" contrasts:** one per carousel at most, only as the centerpiece. Two reads like a template.
- **No hustle framing:** no grind, no "5am", no shame for not doing enough.
- **No AI filler.** Words that make text sound generated: delve, leverage, unlock, elevate, seamless, robust,
  game-changer, journey, landscape, tapestry, realm, "in today's fast-paced world", "let's dive in", "here's the
  thing", "the best part?". Replace with what you actually mean.
- **No fake suspense:** no "And the result? …", no countdowns, no question-then-answer chains.
- **No vague authority:** "studies show", "experts say" only with a named source the user gave you.
- **No bold first word on every bullet.** Bold one or two words that carry the slide, if any.
- **No filler slides:** each slide passes the "would anyone miss it?" test.

## 5. Text markup the engine understands

- Titles: `|` forces a new line; `*word*` makes the accent italic.
- Body: an empty line starts a paragraph; `**x**` is bold; lines starting with `- ` become a list.
- In `script.md`: `Slide 1:` … or blocks separated by `---`. First line = title, the rest = body.
  Tags inside a slide: `[PHOTO: name]`, `[LAYOUT: quote]`, `[STICKER: name]`.
