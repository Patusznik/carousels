"""Render the carousel: prepare photos → crop each slide's photo around you → lay out the slides in headless Chrome
→ out/01.png … (exact Instagram size), out/carousels.pdf, out/sheet.jpg (all slides at a glance).

usage:  python3 render.py <project_dir> [--only 1,3] [--no-pdf]
Takes seconds per slide. Look at out/sheet.jpg (or single slides) before you call it done.
"""
import json, os, shutil, socket, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ensure_venv, project_dir, load, P, HERE, theme, canvas, photo_path, stem, die
ensure_venv()
import numpy as np
from PIL import Image, ImageDraw
from photos import prepare

STRINGS = {
    'en': {'swipe': 'swipe', 'save': 'Save it for later', 'share': 'Send it to a friend', 'comment': 'Tell me in the comments',
           'cta_title': 'SAVE|*this one*'},
    'pl': {'swipe': 'przesuń', 'save': 'Zapisz na później', 'share': 'Wyślij znajomemu', 'comment': 'Napisz w komentarzu',
           'cta_title': 'ZAPISZ|*to sobie*'},
}
# photo box per layout (w, h as fractions of the slide or px), where her head top should sit in it, which asset
BOX = {
    'cover':         dict(w=1.0, h=1.0, head=0.27, need=('ph', 'cut')),
    'cover-sticker': dict(w=660, h=900, head=0.10, need=('stk',)),
    'photo':         dict(w=1.0, h=1.0, head=0.20, need=('ph',)),
    'split':         dict(w=1.0, h=0.56, head=0.16, need=('ph',)),
    'text':          dict(w=380, h=500, head=0.08, need=('stk',), key='sticker'),
    'cta':           dict(w=430, h=570, head=0.08, need=('stk',), key='sticker'),
}
LAYOUTS = ('cover', 'cover-sticker', 'photo', 'split', 'text', 'list', 'quote', 'cta', 'os')


def crop_rect(meta, bw, bh, head_y, focus=None, zoom=1.0):
    W0, H0 = meta['size']; a = bw / bh
    cw = min(W0, H0 * a); ch = cw / a
    zoom = max(1.0, float(zoom or 1.0)); cw, ch = cw / zoom, ch / zoom
    h = meta.get('head')
    if focus:
        x0, y0 = focus[0] * W0 - cw / 2, focus[1] * H0 - ch / 2
    elif h:
        x0, y0 = h['x'] - cw / 2, h['top'] - head_y * ch
    else:
        x0, y0 = (W0 - cw) / 2, (H0 - ch) / 2
    x0 = min(max(0, x0), W0 - cw); y0 = min(max(0, y0), H0 - ch)
    return (x0, y0, x0 + cw, y0 + ch)


def crop_person(meta, bw, bh, zoom=1.0):
    """Sticker crop: tight around the person (they fill ~86 % of the width, head near the top). Outside the photo
    the sticker is transparent, so the crop may run past the edges, except where the person is cut by the frame."""
    W0, H0 = meta['size']; a = bw / bh
    x0, y0, x1, y1 = meta['person']; h = meta.get('head') or {}
    cw = (x1 - x0) / 0.86 / max(0.5, float(zoom or 1.0)); ch = cw / a
    if ch < (y1 - y0) * 0.55: ch = (y1 - y0) * 0.55; cw = ch * a       # very wide poses: keep enough height
    cx = 0.5 * (x0 + x1) * 0.6 + h.get('x', 0.5 * (x0 + x1)) * 0.4
    top = h.get('top', y0) - 0.06 * ch
    if y1 >= H0 - 3: top = min(top, H0 - ch)                          # body runs off the bottom: keep that edge at the slide edge
    left = cx - cw / 2
    if x0 <= 3: left = max(left, 0) if cw <= W0 else left
    if x1 >= W0 - 3 and cw <= W0: left = min(left, W0 - cw)
    return (left, top, left + cw, top + ch)


def busyness(im, box):
    """How hard it is to read text on this part of a photo: 0 calm/dark … 1 busy/bright (edges + brightness)."""
    from PIL import ImageFilter
    g = im.convert('L').crop(box); g = g.resize((270, max(1, round(270 * g.height / g.width))))
    lum = np.asarray(g, np.float32).mean() / 255
    edge = np.asarray(g.filter(ImageFilter.FIND_EDGES), np.float32).mean() / 255
    busy, bright = np.clip((edge - 0.04) / 0.08, 0, 1), np.clip((lum - 0.4) / 0.3, 0, 1)
    return float(busy), float(np.clip(0.6 * busy + 0.4 * bright, 0, 1))


def blur_behind(ph, cut, px, head_px=None):
    """Blur the background only where the title sits (above her head), fading out before the head: her pixels stay
    sharp, and cut-out mistakes lower down (hair ends, sleeves, hands) never sit next to blur, so nothing looks torn."""
    from PIL import ImageFilter
    p = np.asarray(ph, np.float32); a = np.asarray(cut.split()[-1], np.float32)[..., None] / 255
    h = p.shape[0]; end = (head_px if head_px else 0.42 * h) - 0.01 * h; fade = 0.10 * h
    band = np.clip((end - np.arange(h, dtype=np.float32)) / fade, 0, 1)[:, None, None]
    w = 1 - a
    bl = lambda x: np.asarray(Image.fromarray(np.clip(x, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(px)), np.float32)
    num = np.dstack([bl(p[..., c] * w[..., 0]) for c in range(3)]); den = bl(w[..., 0] * 255)[..., None] / 255
    bg = num / np.maximum(den, 1e-3)
    m = (1 - a) * band                                             # where the blurred background shows
    return Image.fromarray(np.clip(p * (1 - m) + bg * m, 0, 255).astype(np.uint8))


def behind_zoom(meta, bw, bh, H, title_bottom=0.18):
    """Zoom needed so the photo can slide far enough up for the head to tuck under a title at the top
    (without the photo's bottom edge coming into the slide)."""
    W0, H0 = meta['size']; h = meta.get('head')
    if not h: return 1.0
    a = bw / bh; cw = min(W0, H0 * a); k0 = bw / cw
    room = k0 * (H0 - h['top'])                     # px of photo below the head top at zoom 1
    if room <= 0: return 1.0
    return float(min(1.6, max(1.0, (H * (1 - title_bottom)) / room * 1.04)))


def avatar_rect(meta, side_k=2.3):
    W0, H0 = meta['size']; h = meta.get('head')
    if not h: s = min(W0, H0); return ((W0 - s) / 2, (H0 - s) / 2, (W0 + s) / 2, (H0 + s) / 2)
    s = min(W0, H0, h['w'] * side_k); cx, cy = h['x'], h['top'] + h['w'] * 0.8
    x0 = min(max(0, cx - s / 2), W0 - s); y0 = min(max(0, cy - s / 2), H0 - s)
    return (x0, y0, x0 + s, y0 + s)


class Assets:
    """Crops photos for one slide into work/stage/a and hands back their URLs."""
    def __init__(self, proj, th, n, adir):
        self.proj, self.th, self.n, self.adir, self.meta = proj, th, n, adir, {}

    def m(self, ref):
        src = photo_path(self.proj, ref)
        if src not in self.meta: self.meta[src] = (src, prepare(self.proj, src, self.th))
        return self.meta[src]

    def get(self, tag, ref, kind, bw, bh, head=0.15, focus=None, zoom=1.0, how='rect', raw=False):
        bw, bh = round(bw), round(bh)
        if raw:                                                   # screenshots, slides: no grade, no cut-out
            from common import open_photo
            src = photo_path(self.proj, ref); im = open_photo(src)
            meta = {'size': list(im.size)}
            r = crop_rect(meta, bw, bh, head, focus, zoom)
            if how == 'top': r = (r[0], 0, r[2], r[3] - r[1])
            im = im.crop(tuple(round(v) for v in r)).resize((bw, bh), Image.LANCZOS)
        else:
            src, meta = self.m(ref)
            if how == 'person' and meta.get('person'): r = crop_person(meta, bw, bh, zoom)
            elif how == 'avatar': r = avatar_rect(meta)
            else:
                r = crop_rect(meta, bw, bh, head, focus, zoom)
                if how == 'top' and not meta.get('head'): r = (r[0], 0, r[2], r[3] - r[1])
            f = {'ph': 'graded.jpg', 'cut': 'cutout.png', 'stk': 'sticker.png', 'orig': 'orig.jpg'}[kind]
            im = Image.open(os.path.join(self.proj, 'work', 'photos', stem(src), f)).crop(tuple(round(v) for v in r)).resize((bw, bh), Image.LANCZOS)
        fn = f's{self.n:02d}_{tag}.' + ('png' if kind in ('cut', 'stk') else 'jpg')
        (im.save(os.path.join(self.adir, fn)) if kind in ('cut', 'stk') else im.convert('RGB').save(os.path.join(self.adir, fn), quality=93))
        return f'a/{fn}?v={int(time.time() * 1000)}'


def key_white(rgb):
    """Alpha for a cut-out on a white background (stock PNG saved as JPG): white connected to the border goes."""
    from scipy import ndimage
    a = np.asarray(rgb, np.float32)
    white = (a.min(-1) > 232) & ((a.max(-1) - a.min(-1)) < 22)
    lab, _ = ndimage.label(white)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])); edge = edge[edge > 0]
    bg = np.isin(lab, edge)
    alpha = (~bg).astype(np.float32)
    alpha = ndimage.gaussian_filter(ndimage.binary_erosion(alpha > 0.5, iterations=1).astype(np.float32), 0.8)
    return alpha


def image_asset(proj, e, adir, tag):
    """A PNG/JPG asset (object, product, sticker) for the UI layer: optional white-background removal and sticker outline."""
    from photos import sticker
    src = photo_path(proj, e['src'])
    im = Image.open(src); im.load()
    rgba = im.convert('RGBA'); rgb = np.asarray(rgba, np.float32)[..., :3]
    a = np.asarray(rgba, np.float32)[..., 3] / 255
    if str(e.get('key', '')).lower() == 'white' or (im.mode != 'RGBA' and e.get('key') != 'none'):
        a = np.minimum(a, key_white(rgb))
    ys, xs = np.where(a > 0.05)                                   # trim empty margins so w= means the object's width
    if len(xs): rgb, a = rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1], a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    w = float(e.get('w') or 400); k = min(2.0, (w * 1.5) / rgb.shape[1])
    if str(e.get('outline', '')).lower() in ('1', 'on', 'true', 'yes'):
        pad = int(max(rgb.shape[:2]) * 0.04)
        rgb = np.pad(rgb, ((pad, pad), (pad, pad), (0, 0))); a = np.pad(a, pad)
        out = Image.fromarray(sticker(rgb, a), 'RGBA')
    else:
        out = Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), 'RGBA')
    out = out.resize((max(1, round(out.width * k)), max(1, round(out.height * k))), Image.LANCZOS)
    if str(e.get('cross', '')).lower() in ('1', 'on', 'true', 'yes'):     # crossed out in red (a big X)
        from PIL import ImageDraw
        dr = ImageDraw.Draw(out); W_, H_ = out.size; m = 0.12; lw = max(6, round(min(W_, H_) * 0.075))
        for (x1, y1, x2, y2) in ((m * W_, m * H_, (1 - m) * W_, (1 - m) * H_), ((1 - m) * W_, m * H_, m * W_, (1 - m) * H_)):
            for col, wd in (((255, 255, 255, 235), lw + max(4, lw // 2)), ((229, 72, 77, 255), lw)):
                dr.line((x1, y1, x2, y2), fill=col, width=wd)
                for (cx, cy) in ((x1, y1), (x2, y2)): dr.ellipse((cx - wd / 2, cy - wd / 2, cx + wd / 2, cy + wd / 2), fill=col)
    fn = f'{tag}.png'; out.save(os.path.join(adir, fn))
    return f'a/{fn}?v={int(time.time() * 1000)}'


def os_slide(proj, th, s, d, n, W, H, adir):
    """Assets for the "os" layout: background photo (+ cut-out when something sits behind you) and every UI element's pictures."""
    A = Assets(proj, th, n, adir); ui = s.get('ui', []); d['ui_assets'] = {}
    if s.get('photo'):
        src, m = A.m(s['photo'])
        behind = any(e.get('layer') == 'behind' for e in ui) or s.get('select_person')
        tp = s.get('title_pos') or ('behind' if s.get('title') and m.get('head') else 'top')
        d['title_pos'] = tp
        bw, bh = W, H
        z = s.get('zoom') or (behind_zoom(m, bw, bh, H) if tp == 'behind' and s.get('head_y') is None else 1.0)
        r = crop_rect(m, bw, bh, s.get('head_y', 0.27 if tp == 'behind' else 0.2), s.get('focus'), z)
        if tp == 'behind' and s.get('head_y') is None and m.get('head'):
            W0, H0 = m['size']; k = bw / (r[2] - r[0]); win = min(H0, (r[3] - r[1]) * 1.8)
            y0 = min(max(0, m['head']['top'] - 0.30 * win), H0 - win); r = (r[0], y0, r[2], y0 + win)
            bh = round(win * k); d['head_px'] = round((m['head']['top'] - y0) * k)
        need = ('ph', 'cut') if (behind or tp == 'behind') else ('ph',)
        ims = {k: Image.open(os.path.join(proj, 'work', 'photos', stem(src), {'ph': 'graded.jpg', 'cut': 'cutout.png'}[k]))
                  .crop(tuple(round(v) for v in r)).resize((bw, bh), Image.LANCZOS) for k in need}
        busy, d['shade'] = busyness(ims['ph'], (0, 0, bw, max(40, d.get('head_px') or round(0.42 * bh))))
        blur = s.get('bg_blur', round(6 * busy) if tp == 'behind' else 0)
        if blur and 'cut' in ims: ims['ph'] = blur_behind(ims['ph'], ims['cut'], blur, d.get('head_px'))
        for k, im in ims.items():
            fn = f's{n:02d}_{k}.' + ('jpg' if k == 'ph' else 'png')
            (im.convert('RGB').save(os.path.join(adir, fn), quality=94) if k == 'ph' else im.save(os.path.join(adir, fn)))
            d['assets'][k] = f'a/{fn}?v={int(time.time() * 1000)}'
        d['box'] = {'w': bw, 'h': bh}
        if 'cut' in ims:
            a = np.asarray(ims['cut'].split()[-1]); ys, xs = np.where(a > 128)
            if len(xs): pad = 18; d['person_box'] = [int(xs.min()) - pad, int(ys.min()) - pad, int(xs.max() - xs.min()) + 2 * pad, int(min(ys.max(), H + 40) - ys.min()) + 2 * pad]
    for k, e in enumerate(ui):
        t = e.get('type'); w = float(e.get('w') or 0); out = {}
        raw = str(e.get('raw', '')).lower() in ('1', 'true', 'on', 'yes')
        if t == 'window' and (e.get('photo') or e.get('before') or e.get('photos')):
            w = w or 880
            if e.get('photos'):
                refs = [x.strip() for x in str(e['photos']).split(',') if x.strip()]
                def thumb(j, r_):
                    if e.get('icons'):                               # Finder icon view: whole file on a white tile
                        try:
                            src = photo_path(proj, r_); im = Image.open(src).convert('RGBA')
                            if im.getextrema()[3][0] == 255 or src.lower().endswith(('.jpg', '.jpeg')):
                                a_ = key_white(np.asarray(im, np.float32)[..., :3]); im.putalpha(Image.fromarray((a_ * 255).astype(np.uint8)))
                            tile = Image.new('RGBA', (240, 240), (255, 255, 255, 255)); im.thumbnail((200, 200), Image.LANCZOS)
                            tile.alpha_composite(im, ((240 - im.width) // 2, (240 - im.height) // 2))
                            fn = f's{n:02d}_u{k}_t{j}.png'; tile.save(os.path.join(adir, fn)); return f'a/{fn}?v={int(time.time() * 1000)}'
                        except SystemExit: return ''
                    try: return A.get(f'u{k}_t{j}', r_, 'ph', 240, 240, 0.12, raw=raw)
                    except SystemExit: print(f'! slide {n}: {r_} not there yet (rendered slides show up after the next render)'); return ''
                out['thumbs'] = [thumb(j, r_) for j, r_ in enumerate(refs)]
            else:
                h_ = float(e.get('h') or round(w * 0.64)); out['h'] = round(h_)
                if e.get('before'):
                    out['before'] = A.get(f'u{k}_b', e['before'], 'orig', w / 2, h_, 0.14, e.get('focus'), e.get('zoom', 1.0), raw=raw)
                    out['ph'] = A.get(f'u{k}_a', e.get('photo') or e['before'], 'ph', w / 2, h_, 0.14, e.get('focus'), e.get('zoom', 1.0), raw=raw)
                else:
                    try: out['ph'] = A.get(f'u{k}_p', e['photo'], 'ph', w, h_, 0.14, e.get('focus'), e.get('zoom', 1.0), 'top', raw=raw)
                    except SystemExit: print(f"! slide {n}: {e['photo']} not there yet (shows up after the next render)"); out['ph'] = ''
        elif t == 'post' and e.get('photo'):
            w = w or 800; h_ = float(e.get('h') or w); out['h'] = round(h_)
            out['ph'] = A.get(f'u{k}_p', e['photo'], 'ph', w, h_, 0.14, e.get('focus'), e.get('zoom', 1.0), raw=raw)
            if e.get('avatar'): out['avatar'] = A.get(f'u{k}_av', e['avatar'], 'ph', 132, 132, how='avatar')
        elif t == 'sticker' and e.get('photo'):
            w = w or 440; out['stk'] = A.get(f'u{k}_s', e['photo'], 'stk', w, w * float(e.get('ratio', 1.3)), how='person', zoom=e.get('zoom', 1.0))
        elif t == 'folder' and e.get('sticker'):
            w = w or 320; out['stk'] = A.get(f'u{k}_s', e['sticker'], 'stk', w * 0.92, w * 1.15, how='person', zoom=e.get('zoom', 1.0))
        if t == 'image' and e.get('src'): out['img'] = image_asset(proj, e, adir, f's{n:02d}_u{k}_img')
        if t == 'profile' and e.get('avatar'): out['avatar'] = A.get(f'u{k}_av', e['avatar'], 'ph', 300, 300, how='avatar')
        if t in ('notif', 'dialog') and e.get('icon'): out['icon'] = A.get(f'u{k}_ic', e['icon'], 'ph', 240, 240, how='avatar')
        d['ui_assets'][k] = out


def grain_png(path, n=512, seed=7):
    if os.path.exists(path): return
    rng = np.random.default_rng(seed)
    g = np.clip(128 + rng.normal(0, 46, (n, n)), 0, 255).astype(np.uint8)
    Image.fromarray(g, 'L').convert('RGB').save(path)


def main():
    proj = project_dir(); cfg = load(proj)
    th = theme(cfg.get('theme', 'lilac')); W, H = canvas(cfg)
    slides = cfg.get('slides', [])
    if not slides: die('no slides in carousel.json — add some (slide.py add …) or import a script (script.py)')
    if len(slides) > 20: print('! Instagram allows max 20 slides per carousel')
    only = {int(x) for x in sys.argv[sys.argv.index('--only') + 1].split(',')} if '--only' in sys.argv else None
    st = P(proj, 'work', 'stage')
    for name in os.listdir(os.path.join(HERE, 'templates')):
        s, d = os.path.join(HERE, 'templates', name), os.path.join(st, name)
        (shutil.copytree(s, d, dirs_exist_ok=True) if os.path.isdir(s) else shutil.copy2(s, d))
    grain_png(os.path.join(st, 'grain.png'))
    tcss = os.path.join(HERE, 'themes', cfg.get('theme', 'lilac') + '.css')         # per-theme layout overrides
    with open(os.path.join(st, 'theme.css'), 'w', encoding='utf-8') as f: f.write(open(tcss, encoding='utf-8').read() if os.path.isfile(tcss) else '')
    adir = P(proj, 'work', 'stage', 'a')
    out_slides = []
    for i, s in enumerate(slides):
        n = i + 1; lay = s.get('layout', 'text')
        if lay not in LAYOUTS: die(f'slide {n}: unknown layout "{lay}" — {", ".join(LAYOUTS)}')
        d = {**s, 'n': n, 'total': len(slides), 'layout': lay, 'assets': {}, 'box': None}
        if lay == 'os':
            if only is None or n in only: os_slide(proj, th, s, d, n, W, H, adir)
            out_slides.append(d); continue
        spec = BOX.get(lay)
        ref = s.get(spec.get('key', 'photo')) if spec else None
        if spec and spec.get('key') is None and not ref and lay in ('cover', 'cover-sticker', 'photo', 'split'):
            die(f'slide {n} ({lay}) needs a photo')
        if spec and ref and (only is None or n in only):
            src = photo_path(proj, ref); m = prepare(proj, src, th)
            bw = round(spec['w'] * W) if spec['w'] <= 1 else spec['w']; bh = round(spec['h'] * H) if spec['h'] <= 1 else spec['h']
            if spec['need'] == ('stk',) and m.get('person') and not s.get('focus') and s.get('head_y') is None:
                r = crop_person(m, bw, bh, s.get('zoom', 1.0))
            else:
                z = s.get('zoom') or (behind_zoom(m, bw, bh, H) if lay == 'cover' and s.get('head_y') is None else 1.0)
                r = crop_rect(m, bw, bh, s.get('head_y', spec['head']), s.get('focus'), z)
            slide_ = None
            if lay == 'cover' and s.get('head_y') is None and m.get('head'):
                # tall strip at the cover's width: the page slides it so her head tucks under the LAST title line
                W0, H0 = m['size']; k = bw / (r[2] - r[0])
                win = min(H0, (r[3] - r[1]) * 1.8)
                y0 = min(max(0, m['head']['top'] - 0.30 * win), H0 - win)
                r = (r[0], y0, r[2], y0 + win)
                bh = round(win * k); slide_ = round((m['head']['top'] - y0) * k)
            pd = os.path.join(proj, 'work', 'photos', stem(src))
            files = {'ph': 'graded.jpg', 'cut': 'cutout.png', 'stk': 'sticker.png'}
            ims = {k: Image.open(os.path.join(pd, files[k])).crop(tuple(round(v) for v in r)).resize((bw, bh), Image.LANCZOS) for k in spec['need']}
            if lay in ('cover', 'photo'):
                # text area: above her head on the cover, the bottom third on photo slides
                tb = (0, 0, bw, max(40, slide_ or round(0.42 * bh))) if lay == 'cover' else (0, round(bh * 0.6), bw, bh)
                busy, d['shade'] = busyness(ims['ph'], tb)
                blur = s.get('bg_blur', round(7 * busy) if lay == 'cover' else 0)
                if blur and 'cut' in ims: ims['ph'] = blur_behind(ims['ph'], ims['cut'], blur, slide_)
                elif blur: ims['ph'] = ims['ph'].filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(blur))
            for k, im in ims.items():
                fn = f's{n:02d}_{k}.' + ('jpg' if k == 'ph' else 'png')
                (im.convert('RGB').save(os.path.join(adir, fn), quality=94) if k == 'ph' else im.save(os.path.join(adir, fn)))
                d['assets'][k] = f'a/{fn}?v={int(time.time() * 1000)}'
            d['box'] = {'w': bw, 'h': bh}
            if slide_ is not None: d['head_px'] = slide_
        out_slides.append(d)
    data = {'W': W, 'H': H, 'theme': th, 'handle': cfg.get('handle', ''), 'strings': {**STRINGS.get(cfg.get('lang', 'en'), STRINGS['en']), **cfg.get('strings', {})},
            'slides': out_slides}
    with open(P(proj, 'work', 'stage', 'data', 'slides.json'), 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False)

    sock = socket.socket(); sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]; sock.close()
    SRV = ('import http.server, socketserver, sys\n'
           'class S(socketserver.ThreadingMixIn, socketserver.TCPServer): allow_reuse_address = True; daemon_threads = True\n'
           'class Q(http.server.SimpleHTTPRequestHandler):\n    def log_message(self, *a): pass\n'
           'S(("127.0.0.1", int(sys.argv[1])), Q).serve_forever()')
    srv = subprocess.Popen([sys.executable, '-c', SRV, str(port)], cwd=st, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.6)
    out = P(proj, 'out')
    done = []
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            try: b = p.chromium.launch(channel='chrome')
            except Exception: b = p.chromium.launch()
            pg = b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
            logs = []; pg.on('pageerror', lambda e: logs.append(str(e)))
            pg.goto(f'http://127.0.0.1:{port}/index.html')
            pg.wait_for_function('window.ready === true', timeout=30000)
            for i in range(len(slides)):
                if only and i + 1 not in only: continue
                pg.evaluate(f'window.renderSlide({i})')
                fn = os.path.join(out, f'{i + 1:02d}.png')
                pg.locator('#slide').screenshot(path=fn)
                done.append(fn)
            b.close()
            for l in logs[:5]: print('page error:', l)
    finally:
        srv.terminate()
    allp = [os.path.join(out, f'{i + 1:02d}.png') for i in range(len(slides)) if os.path.exists(os.path.join(out, f'{i + 1:02d}.png'))]
    if '--no-pdf' not in sys.argv and allp:
        ims = [Image.open(x).convert('RGB') for x in allp]
        ims[0].save(os.path.join(out, 'carousels.pdf'), save_all=True, append_images=ims[1:], resolution=144)
    if allp:                                                   # contact sheet: 5 per row, numbered
        tw, thh = 324, round(324 * H / W); cols = min(5, len(allp)); rows = (len(allp) + cols - 1) // cols
        S = Image.new('RGB', (cols * (tw + 12) + 12, rows * (thh + 46) + 12), (24, 18, 15))
        for k, x in enumerate(allp):
            im = Image.open(x).convert('RGB').resize((tw, thh), Image.LANCZOS)
            cx, cy = 12 + (k % cols) * (tw + 12), 12 + (k // cols) * (thh + 46)
            S.paste(im, (cx, cy)); ImageDraw.Draw(S).text((cx + 4, cy + thh + 10), f'{k + 1:02d}  {slides[k].get("layout")}', fill=(243, 233, 215))
        S.save(os.path.join(out, 'sheet.jpg'), quality=88)
    print(f'✓ {len(done)} slide(s) → {out}/NN.png ({W}×{H})' + ('' if '--no-pdf' in sys.argv else ', carousels.pdf') + ', sheet.jpg')


if __name__ == '__main__':
    main()
