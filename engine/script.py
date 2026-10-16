"""Turn a carousel script (e.g. from /social-writer) into slides.

usage:  python3 script.py <proj> SCRIPT.md|.txt [--replace]
Understands slides marked "Slide 1:", "Slajd 1 —", "1.", "## 1" or separated by "---".
Per slide: first line → title, the rest → body; lines starting with "- " / "• " → a list slide.
[PHOTO: name] / [ZDJĘCIE: name] inside a slide → that slide shows the photo (cover on slide 1, else split).
[LAYOUT: quote] etc. forces a layout. Slide 1 → cover (cover-sticker if it has no photo), a last slide that asks
to save/share/comment/follow → cta, everything else → text. Fix anything afterwards with slide.py.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import project_dir, load, save, die

HEAD = re.compile(r'^\s*(?:#+\s*)?(?:\*\*)?\s*(?:slide|slajd|karta)?\s*(\d{1,2})\s*(?:\*\*)?\s*[:.)\-—–]\s*(?:\*\*)?\s*', re.I)
TAG = re.compile(r'\[(PHOTO|ZDJ[ĘE]CIE|FOTO|LAYOUT|UKŁAD|STICKER|NAKLEJKA)\s*:\s*([^\]]+)\]', re.I)
CTA = re.compile(r'\b(save|share|send|comment|follow|zapisz|udost[eę]pnij|wy[sś]lij|napisz|skomentuj|obserwuj)\b', re.I)


def split_slides(text):
    text = text.replace('\r', '')
    if re.search(r'^\s*-{3,}\s*$', text, re.M) and not HEAD.search(text):
        return [b.strip() for b in re.split(r'^\s*-{3,}\s*$', text, flags=re.M) if b.strip()]
    blocks, cur = [], None
    for line in text.split('\n'):
        m = HEAD.match(line)
        if m:
            if cur is not None: blocks.append('\n'.join(cur).strip())
            cur = [line[m.end():]]
        elif cur is not None:
            cur.append(line)
    if cur is not None: blocks.append('\n'.join(cur).strip())
    return [b for b in blocks if b] or [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]


def to_slide(block, n, total):
    tags = {k.upper(): v.strip() for k, v in TAG.findall(block)}
    block = TAG.sub('', block).strip()
    lines = [l.rstrip() for l in block.split('\n')]
    while lines and not lines[0].strip(): lines.pop(0)
    title = re.sub(r'^\*\*(.+)\*\*$', r'\1', lines[0].strip()) if lines else ''
    rest = [l for l in lines[1:]]
    items = [re.sub(r'^\s*[-•*]\s+', '', l) for l in rest if re.match(r'^\s*[-•*]\s+', l)]
    body = '\n'.join(l for l in rest if not re.match(r'^\s*[-•*]\s+', l)).strip()
    s = {'title': title}
    photo = next((v for k, v in tags.items() if k in ('PHOTO', 'ZDJĘCIE', 'ZDJECIE', 'FOTO')), None)
    sticker = next((v for k, v in tags.items() if k in ('STICKER', 'NAKLEJKA')), None)
    lay = next((v for k, v in tags.items() if k in ('LAYOUT', 'UKŁAD')), None)
    if items: s['items'] = items
    if body: s['body'] = body
    if lay: s['layout'] = lay.lower()
    elif n == 1: s['layout'] = 'cover' if photo else 'cover-sticker'
    elif n == total and CTA.search(block): s['layout'] = 'cta'
    elif items: s['layout'] = 'list'
    elif photo: s['layout'] = 'split'
    else: s['layout'] = 'text'
    if photo: s['photo'] = photo
    if sticker: s['sticker'] = sticker
    return s


def main():
    proj = project_dir(); cfg = load(proj)
    if len(sys.argv) < 3: die('usage: script.py <proj> SCRIPT.md [--replace]')
    with open(os.path.expanduser(sys.argv[2]), encoding='utf-8') as f: blocks = split_slides(f.read())
    new = [to_slide(b, i + 1, len(blocks)) for i, b in enumerate(blocks)]
    if cfg.get('slides') and '--replace' not in sys.argv:
        die(f'carousel already has {len(cfg["slides"])} slides — use --replace to overwrite them')
    cfg['slides'] = new; save(proj, cfg)
    for i, s in enumerate(new, 1):
        print(f'{i:02d}  {s["layout"]:<14} {s.get("photo", ""):<16} {s["title"][:60]}')
    need = [i for i, s in enumerate(new, 1) if s['layout'] in ('cover', 'photo', 'split', 'cover-sticker') and not s.get('photo')]
    if need: print('! slides', ', '.join(map(str, need)), 'need a photo: slide.py', proj, 'set N photo=NAME')
    print('next: python3 render.py', proj)


if __name__ == '__main__':
    main()
