"""Edit the slides (this is what dictation maps to).

usage:  python3 slide.py <proj> show                          all slides: layout, photo, title, text
        python3 slide.py <proj> add [--at N] key=value …      new slide (at the end, or as slide N)
        python3 slide.py <proj> set N key=value …             change slide N (value - removes the key)
        python3 slide.py <proj> rm N  ·  mv N M  ·  dup N     remove / move / duplicate
        python3 slide.py <proj> photos                        photos in the project (name, size, person found?)

keys:   layout   cover · cover-sticker · photo · split · text · list · quote · cta
        title    "LINE ONE|*accent line*"   (| = new line, *x* = serif italic accent)
        body     text (blank line = new paragraph, *x* accent, **x** bold)
        kicker   small mono label top-left          items  "point one|point two|…" (list)
        quote, by (quote)    photo NAME (cover/photo/split/cover-sticker)    sticker NAME (small cut-out on text/cta)
        focus X,Y (0–1 point of the photo to centre on)   zoom 1.3   head_y 0.25 (where her head top sits, 0–1)
        title_size PX (max title size)   counter off   actions save,share,comment (cta)   labels.save="…" (cta line text)
        overlap 0–3 (cover: how deep your head goes behind the title, default 1)
        bg_blur PX (blur the background behind you; cover does it on its own when the background is busy, 0 = off)
        set all key=value … changes every slide (e.g. set all kicker="SERIES NAME")

layout os (macOS / iOS look): photo=NAME (or none → desktop wallpaper), title (title_pos behind|top|bottom), body,
        menubar on, select_person "label" (editor selection box around you), bg plain, clock "Thu 9:41"
        python3 slide.py <proj> ui N add type=… key=value …   UI element on slide N   (ui N list · ui N set K k=v · ui N rm K · ui N clear)
        types: bubble text side=in|out time · input text select send · dialog title text buttons="No|Yes" primary glyph icon
               notif app title text time icon · pill label sub glyph=heart|call|moon · window title_bar + kicker title body
               | lines="$ cmd|output" | photo | before+photo | photos=a,b,c names folder pick · folder label tag sticker
               profile name avatar bio stats follow · post photo name avatar text · sticker photo · sticky text · cursor · spark · counter
        every element: at=top|upper|center|lower|bottom[-left|-right] or at=X,Y (%), w=PX, rot=DEG, layer=behind (between photo and you)
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import project_dir, load, save, photo_path, stem, die, PHOTO_EXT

LAYOUTS = ('cover', 'cover-sticker', 'photo', 'split', 'text', 'list', 'quote', 'cta', 'os')
NUM = {'zoom', 'head_y', 'title_size', 'overlap', 'bg_blur', 'title_h', 'w', 'h', 'rot', 'primary', 'pick', 'ratio'}
BOOL = {'menubar', 'send'}


def parse_kv(args):
    d = {}
    for a in args:
        if '=' not in a: die(f'expected key=value, got "{a}"')
        k, v = a.split('=', 1); k = k.strip()
        if '.' in k:                                         # nested, e.g. labels.save="Zapisz"
            top, sub = k.split('.', 1); d.setdefault(top, {})[sub] = None if v == '-' else v; continue
        if v == '-': d[k] = None; continue
        if k == 'focus': v = [float(x) for x in v.split(',')]
        elif k == 'items': v = [x.strip() for x in v.split('|') if x.strip()]
        elif k == 'actions': v = [x.strip() for x in v.split(',') if x.strip()]
        elif k in NUM: v = float(v)
        elif k == 'counter' or k in BOOL: v = v.lower() not in ('off', 'no', 'false', '0')
        if k == 'layout' and v not in LAYOUTS: die(f'unknown layout "{v}" — {", ".join(LAYOUTS)}')
        d[k] = v
    return d


def apply(s, kv):
    for k, v in kv.items():
        if v is None: s.pop(k, None)
        elif isinstance(v, dict):
            m = {**s.get(k, {}), **v}; m = {a: b for a, b in m.items() if b is not None}
            (s.__setitem__(k, m) if m else s.pop(k, None))
        else: s[k] = v
    return s


def show(proj, cfg):
    S = cfg.get('slides', [])
    if not S: print('(no slides)'); return
    for i, s in enumerate(S, 1):
        ph = s.get('photo') or s.get('sticker') or ''
        txt = (s.get('title') or s.get('quote') or '').replace('|', ' / ')
        extra = s.get('body') or ' · '.join(s.get('items', []))
        print(f'{i:02d}  {s.get("layout", "text"):<14} {ph[:22]:<22} {txt[:46]:<46} {extra[:50].replace(chr(10), " ")}')
    print(f'\n{len(S)} slides · {cfg.get("size")} · theme {cfg.get("theme")} · {cfg.get("lang")}' + (' · ! max 20 on Instagram' if len(S) > 20 else ''))


def main():
    proj = project_dir(); cfg = load(proj); S = cfg.setdefault('slides', [])
    if len(sys.argv) < 3: show(proj, cfg); return
    cmd, rest = sys.argv[2], sys.argv[3:]
    idx = lambda x: (int(x) - 1) if 1 <= int(x) <= len(S) else die(f'there is no slide {x} (1–{len(S)})')
    if cmd == 'show': show(proj, cfg); return
    if cmd == 'photos':
        d = os.path.join(proj, 'photos')
        for f in sorted(x for x in os.listdir(d) if not x.startswith('.')) if os.path.isdir(d) else []:
            if not f.lower().endswith(PHOTO_EXT): continue
            mp = os.path.join(proj, 'work', 'photos', stem(f), 'meta.json')
            info = ''
            if os.path.exists(mp):
                m = json.load(open(mp)); info = f"{m['size'][0]}×{m['size'][1]}  person {m['coverage'] * 100:.0f}%" + ('' if m.get('head') else '  (no head found)')
            print(f'{stem(f):<28} {info or "(not prepared yet)"}')
        return
    if cmd == 'add':
        at = len(S)
        if rest[:1] == ['--at']: at = int(rest[1]) - 1; rest = rest[2:]
        s = apply({'layout': 'text'}, parse_kv(rest))
        for k in ('photo', 'sticker'):
            if s.get(k): photo_path(proj, s[k])
        S.insert(max(0, min(at, len(S))), s)
    elif cmd == 'set':
        if not rest: die('set N key=value …')
        kv = parse_kv(rest[1:])
        for s in (S if rest[0] == 'all' else [S[idx(rest[0])]]):
            apply(s, json.loads(json.dumps(kv)))
            for k in ('photo', 'sticker'):
                if s.get(k): photo_path(proj, s[k])
    elif cmd == 'ui':
        if not rest: die('ui N add|set|rm|list|clear …')
        s = S[idx(rest[0])]; U = s.setdefault('ui', []); sub = rest[1] if len(rest) > 1 else 'list'; args = rest[2:]
        k = lambda x: (int(x) - 1) if 1 <= int(x) <= len(U) else die(f'slide {rest[0]} has no ui element {x} (1–{len(U)})')
        if sub == 'add':
            e = apply({}, parse_kv(args))
            if 'type' not in e: die('ui add needs type=…')
            U.append(e)
        elif sub == 'set': apply(U[k(args[0])], parse_kv(args[1:]))
        elif sub == 'rm': U.pop(k(args[0]))
        elif sub == 'clear': U.clear()
        elif sub != 'list': die(f'unknown ui command "{sub}" — add, set, rm, list, clear')
        for j, e in enumerate(U, 1):
            print(f'  ui {j}: ' + ' '.join(f'{a}={json.dumps(b, ensure_ascii=False) if not isinstance(b, str) or " " in b else b}' for a, b in e.items()))
        if sub == 'list': return
    elif cmd == 'rm': S.pop(idx(rest[0]))
    elif cmd == 'dup': i = idx(rest[0]); S.insert(i + 1, json.loads(json.dumps(S[i])))
    elif cmd == 'mv':
        i = idx(rest[0]); j = int(rest[1]) - 1; s = S.pop(i); S.insert(max(0, min(j, len(S))), s)
    else: die(f'unknown command "{cmd}" — show, add, set, rm, mv, dup, photos')
    save(proj, cfg); show(proj, cfg)
    print('saved → carousel.json · next: python3 render.py', proj, '[--only N]')


if __name__ == '__main__':
    main()
