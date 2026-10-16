"""Prepare every photo the carousel uses: upright, graded in the theme's look, and cut out (you without the background).

usage:  python3 photos.py <project_dir> [--force] [--only NAME,…] [--all]
        python3 photos.py <project_dir> --sheet     quick overview of ALL photos in photos/ (names under each) → work/photos_sheet.jpg
        python3 photos.py <project_dir> --video FILE [--n 4] [--at 1.5,3.2]   best (sharpest) frames of a video → photos/<name>_<s>s.jpg
→ work/photos/<name>/graded.jpg   the photo in the theme grade (long side ≤ 2400 px)
                     alpha.png    person matte (RobustVideoMatting, run on the still a few passes to settle)
                     cutout.png   graded person on transparent background
                     sticker.png  cutout with a white sticker outline + soft shadow
                     meta.json    size, person box, head (x, top, width) — used for smart crops
Cached: a photo is redone only when the source file changes (or --force). render.py runs this automatically.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ensure_venv, project_dir, load, P, MODELS, theme, photo_path, stem, open_photo, die, ffmpeg
ensure_venv()
import numpy as np
from PIL import Image

MAX_SIDE = 2400
PREP_V = 3          # bump when the preparation changes → cached photos are redone


def grade(img, g):
    """Theme grade on float RGB 0..255: warm balance, gentle contrast, faded blacks, softer colour, split tone, vignette."""
    x = img / 255.0
    x = x * np.array(g.get('wb', [1, 1, 1]), np.float32)
    x = 0.5 + (x - 0.5) * g.get('contrast', 1.0)
    lo, hi = g.get('fade', [0.0, 1.0]); x = lo + np.clip(x, 0, 1) * (hi - lo)
    lum = (x @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    x = lum + (x - lum) * g.get('saturation', 1.0)
    x = x + np.array(g.get('shadow_tint', [0, 0, 0]), np.float32) * (1 - lum) + np.array(g.get('highlight_tint', [0, 0, 0]), np.float32) * lum
    v = g.get('vignette', 0)
    if v:
        h, w = x.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        d = np.sqrt(((xx / w - 0.5) * 1.1) ** 2 + ((yy / h - 0.5)) ** 2)
        x = x * (1 - v * np.clip((d - 0.35) / 0.45, 0, 1) ** 1.6)[..., None]
    return np.clip(x * 255, 0, 255)


_model = None
def matte(img):
    """RobustVideoMatting on a still: a few recurrent passes over the same frame let the matte settle."""
    global _model
    import torch
    sys.path.insert(0, os.path.join(MODELS, 'RVM'))
    from model import MattingNetwork
    dev = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
    if _model is None:
        w = os.path.join(MODELS, 'rvm_resnet50.pth')
        if not os.path.exists(w): die('cut-out model missing: run the installer again (it downloads the models)')
        _model = MattingNetwork('resnet50').eval().to(dev)
        _model.load_state_dict(torch.load(w, map_location='cpu'))
    h, wd = img.shape[:2]
    ratio = float(np.clip(640 / max(h, wd), 0.1, 1.0))
    x = torch.from_numpy(img / 255.0).float().permute(2, 0, 1)[None].to(dev)
    rec = [None] * 4
    with torch.no_grad():
        for _ in range(4):
            fgr, pha, *rec = _model(x, *rec, downsample_ratio=ratio)
    return pha[0, 0].clamp(0, 1).cpu().numpy().astype(np.float32), fgr[0].permute(1, 2, 0).clamp(0, 1).cpu().numpy() * 255


def main_person(img):
    """Mask of the main person from the pose model (MediaPipe pose_landmarker_heavy), or None.
    Used to drop other people's hands/shoulders that the matting model also cuts out."""
    p = os.path.join(MODELS, 'pose_landmarker_heavy.task')
    if not os.path.exists(p): return None
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
        o = vision.PoseLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=p), running_mode=vision.RunningMode.IMAGE,
                                         num_poses=1, output_segmentation_masks=True)
        with vision.PoseLandmarker.create_from_options(o) as lm:
            r = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(img.astype(np.uint8))))
        return r.segmentation_masks[0].numpy_view().squeeze().astype(np.float32) if r.segmentation_masks else None
    except Exception as e:
        print('  (pose model skipped:', str(e)[:80] + ')'); return None


def clean(a, pm=None):
    from scipy import ndimage
    core = a > 0.5
    lab, n = ndimage.label(core)
    if n > 1:
        idx = range(1, n + 1); sizes = ndimage.sum(core, lab, idx)
        if pm is not None:                                       # keep pieces that belong to the main person (pose mask)
            cover = ndimage.mean(pm > 0.3, lab, idx)
            keep = [i for i, (s, c) in zip(idx, zip(sizes, cover)) if s == sizes.max() or (c > 0.5 and s > 0.002 * sizes.max())]
        else:
            keep = [i for i, s in zip(idx, sizes) if s > 0.05 * sizes.max()]
        core = np.isin(lab, keep)
    holes = ndimage.binary_fill_holes(core) & ~core               # fill only specks; real gaps (arm akimbo) stay open
    hl, hn = ndimage.label(holes)
    if hn:
        hs = ndimage.sum(holes, hl, range(1, hn + 1))
        holes = np.isin(hl, [i + 1 for i, s in enumerate(hs) if s < 0.0004 * a.size])
    filled = core | holes
    region = ndimage.binary_dilation(filled, iterations=max(4, a.shape[1] // 100))
    return np.maximum(np.where(region, a, 0), ndimage.binary_erosion(filled, iterations=3).astype(np.float32))


def head(a):
    rows = np.where((a > 0.5).sum(1) > max(6, a.shape[1] // 200))[0]
    if not len(rows): return None
    top = int(rows[0]); band = a[top + a.shape[0] // 40: top + a.shape[0] // 9] > 0.5
    xs = [np.where(r)[0] for r in band if r.any()]
    if not xs: return None
    lo, hi = float(np.median([x[0] for x in xs])), float(np.median([x[-1] for x in xs]))
    return {'x': round((lo + hi) / 2, 1), 'top': top, 'w': round(hi - lo, 1)}


def sticker(rgb, a):
    """White outline around the cutout + soft drop shadow, as RGBA."""
    import cv2
    h, w = a.shape
    r = max(6, int(round(min(h, w) * 0.012)))
    hard = (a > 0.35).astype(np.uint8)
    ring = cv2.dilate(hard, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    outline = cv2.GaussianBlur(ring.astype(np.float32), (0, 0), max(1.0, r * 0.12))
    sh = cv2.GaussianBlur(np.roll(outline, (int(r * 1.6), int(r * 0.6)), (0, 1)), (0, 0), r * 1.8) * 0.35
    base_a = np.clip(np.maximum(outline, sh), 0, 1)
    base_rgb = np.where((outline >= sh)[..., None], 255.0, 40.0) * np.ones(3)
    out_a = a + base_a * (1 - a)
    out_rgb = (rgb * a[..., None] + base_rgb * (base_a * (1 - a))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    return np.dstack([np.clip(out_rgb, 0, 255), out_a * 255]).astype(np.uint8)


def prepare(proj, src, th, force=False):
    out = os.path.join(proj, 'work', 'photos', stem(src)); os.makedirs(out, exist_ok=True)
    meta_p = os.path.join(out, 'meta.json')
    mt = os.path.getmtime(src)
    if not force and os.path.exists(meta_p):
        with open(meta_p) as f: m = json.load(f)
        if m.get('src_mtime') == mt and m.get('theme') == th['name'] and m.get('v') == PREP_V and m.get('grade') == th.get('grade'): return m
    im = open_photo(src)
    k = MAX_SIDE / max(im.size)
    if k < 1: im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    raw = np.asarray(im, np.float32)
    g = grade(raw, th.get('grade', {}))
    a, fgr = matte(raw)
    a = clean(a, main_person(raw))
    fg = grade(fgr, th.get('grade', {}))
    core = np.clip((a - 0.92) / 0.08, 0, 1)[..., None]             # true pixels inside, clean foreground colour at the edges
    person = fg * (1 - core) + g * core
    Image.fromarray(g.astype(np.uint8)).save(os.path.join(out, 'graded.jpg'), quality=93)
    im.save(os.path.join(out, 'orig.jpg'), quality=92)                # ungraded, for before / after
    Image.fromarray((a * 255 + 0.5).astype(np.uint8), 'L').save(os.path.join(out, 'alpha.png'))
    Image.fromarray(np.dstack([person, a * 255]).astype(np.uint8), 'RGBA').save(os.path.join(out, 'cutout.png'))
    Image.fromarray(sticker(person, a), 'RGBA').save(os.path.join(out, 'sticker.png'))
    ys, xs = np.where(a > 0.5)
    m = {'v': PREP_V, 'grade': th.get('grade'), 'src': src, 'src_mtime': mt, 'theme': th['name'], 'size': [im.width, im.height], 'head': head(a),
         'person': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
         'coverage': round(float((a > 0.5).mean()), 3)}
    with open(meta_p, 'w') as f: json.dump(m, f, indent=1)
    return m


def used_photos(proj, cfg):
    refs = []
    for s in cfg.get('slides', []):
        for k in ('photo', 'photo2', 'sticker'):
            if s.get(k): refs.append(photo_path(proj, s[k]))
        for e in s.get('ui', []):
            if str(e.get('raw', '')).lower() in ('1', 'true', 'on', 'yes'): continue
            for k in ('photo', 'before', 'sticker', 'avatar', 'icon'):
                if e.get(k): refs.append(photo_path(proj, e[k]))
            for r in str(e.get('photos') or '').split(','):
                if r.strip(): refs.append(photo_path(proj, r.strip()))
    return list(dict.fromkeys(refs))


def all_photos(proj):
    from common import PHOTO_EXT
    d = os.path.join(proj, 'photos')
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(PHOTO_EXT) and not f.startswith('.')] if os.path.isdir(d) else []


def video_frames(proj, path, n=4, at=None):
    """Pull stills out of a video: the sharpest frame in each of n equal parts (or the frames at the given seconds)."""
    import subprocess, cv2
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(path): die(f'no video {path}')
    FF = ffmpeg()
    info = subprocess.run([FF, '-hide_banner', '-i', path], capture_output=True, text=True, errors='replace').stderr
    import re; m = re.search(r'Duration:\s*(\d+):(\d+):([\d.]+)', info)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    if 'arib-std-b67' in info or 'smpte2084' in info:
        print('! HDR video: stills may look washed out (turn HDR video off on the iPhone for footage you want stills from)')
    if not at:
        fps, w = 4, 360
        # ffmpeg applies the rotation itself, so measure the decoded frame size instead of trusting width/height
        one = subprocess.run([FF, '-v', 'error', '-i', path, '-vf', f'scale={w}:-2', '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                             capture_output=True).stdout
        import io; h = Image.open(io.BytesIO(one)).height
        raw = subprocess.run([FF, '-v', 'error', '-i', path, '-vf', f'fps={fps},scale={w}:-2', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                             capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8); frames = fr[: len(fr) // (w * h) * w * h].reshape(-1, h, w)
        if not len(frames): die(f'could not read frames from {path}')
        sharp = [cv2.Laplacian(f[h // 6: h * 5 // 6, w // 6: w * 5 // 6], cv2.CV_32F).var() for f in frames]
        parts = np.array_split(np.arange(len(frames)), max(1, min(n, len(frames))))
        at = [(int(p[np.argmax([sharp[i] for i in p])]) + 0.5) / fps for p in parts if len(p)]
    out = []
    for t in at:
        t = min(float(t), max(0.0, dur - 0.05))
        fn = os.path.join(P(proj, 'photos'), f'{stem(path)}_' + f'{t:.1f}'.replace('.', '-') + 's.jpg')
        subprocess.run([FF, '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', path, '-frames:v', '1', '-q:v', '2', fn], check=True)
        out.append(os.path.basename(fn))
    print(f'{os.path.basename(path)} → ' + ', '.join(out))
    return out


def sheet(proj):
    from PIL import ImageDraw, ImageOps
    fs = all_photos(proj)
    if not fs: die(f'no photos in {proj}/photos')
    tw, th_, cols = 300, 400, 6; rows = (len(fs) + cols - 1) // cols
    S = Image.new('RGB', (cols * (tw + 10) + 10, rows * (th_ + 40) + 10), (24, 18, 15)); dr = ImageDraw.Draw(S)
    for k, f in enumerate(fs):
        im = open_photo(f); im = ImageOps.fit(im, (tw, th_), Image.LANCZOS, centering=(0.5, 0.35))
        x, y = 10 + (k % cols) * (tw + 10), 10 + (k // cols) * (th_ + 40)
        S.paste(im, (x, y)); dr.text((x + 4, y + th_ + 10), stem(f)[:40], fill=(243, 233, 215))
    out = P(proj, 'work', 'photos_sheet.jpg'); S.save(out, quality=86)
    print(f'{len(fs)} photos → {out}')


if __name__ == '__main__':
    proj = project_dir(); cfg = load(proj); th = theme(cfg.get('theme', 'lilac'))
    if '--video' in sys.argv:
        v = sys.argv[sys.argv.index('--video') + 1]
        n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 4
        at = [float(x) for x in sys.argv[sys.argv.index('--at') + 1].split(',')] if '--at' in sys.argv else None
        video_frames(proj, v, n, at); sys.exit(0)
    if '--sheet' in sys.argv: sheet(proj); sys.exit(0)
    only = set(sys.argv[sys.argv.index('--only') + 1].split(',')) if '--only' in sys.argv else None
    srcs = all_photos(proj) if '--all' in sys.argv else (used_photos(proj, cfg) or all_photos(proj))
    for s in srcs:
        if only and stem(s) not in only: continue
        m = prepare(proj, s, th, '--force' in sys.argv)
        h = m.get('head') or {}
        print(f"{stem(s):<28} {m['size'][0]}×{m['size'][1]}  person {m['coverage'] * 100:4.1f}% of frame  head x={h.get('x')} top={h.get('top')}")
    print('next: python3 render.py', proj)
