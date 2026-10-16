"""Shared helpers for the Carousels engine.

A project is a folder: carousel.json (the slides) + the photos it uses (anywhere; paths are relative to the project)
+ work/ (prepared photos, render stage) + out/ (01.png …, carousels.pdf, sheet.jpg).
Runs in its own environment, made by install.sh / install.ps1: ~/.carousels/venv (torch, opencv, pillow, playwright)
and ~/.carousels/models (RobustVideoMatting code + weights, MediaPipe pose model). CAROUSELS_HOME moves it.
"""
import json, os, platform, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.environ.get('CAROUSELS_HOME') or os.path.join(os.path.expanduser('~'), '.carousels')
VENV = os.path.join(HOME, 'venv')
MODELS = os.path.join(HOME, 'models')
if os.path.isdir(os.path.join(HOME, 'browsers')):             # Chromium the installer downloaded (when there's no Chrome)
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', os.path.join(HOME, 'browsers'))
PHOTO_EXT = ('.jpg', '.jpeg', '.png', '.heic', '.heif', '.webp', '.tif', '.tiff')
VIDEO_EXT = ('.mov', '.mp4', '.m4v')
SIZES = {'4:5': (1080, 1350), '3:4': (1080, 1440), '1:1': (1080, 1080)}


def venv_python():
    return os.path.join(VENV, 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(VENV, 'bin', 'python')


def ensure_venv():
    """Re-exec inside the engine venv when it exists and we're not already in it."""
    py = venv_python()
    if os.path.exists(py) and os.path.realpath(sys.prefix) != os.path.realpath(VENV) and not os.environ.get('CAROUSELS_NO_REEXEC'):
        os.environ['CAROUSELS_NO_REEXEC'] = '1'
        if os.name == 'nt':                       # execv on Windows doesn't replace the process cleanly
            raise SystemExit(subprocess.call([py] + sys.argv))
        os.execv(py, [py] + sys.argv)


def ffmpeg():
    """ffmpeg on PATH, else the copy that ships with the imageio-ffmpeg package (installed into the venv)."""
    exe = shutil.which('ffmpeg')
    if exe: return exe
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        die('ffmpeg not found: run the installer again, or install ffmpeg')


def die(msg):
    raise SystemExit('✗ ' + msg)


def project_dir():
    if len(sys.argv) < 2 or sys.argv[1].startswith('-'):
        die(f'usage: {os.path.basename(sys.argv[0])} <project_dir> …')
    return os.path.abspath(os.path.expanduser(sys.argv[1]))


def cfg_path(proj): return os.path.join(proj, 'carousel.json')


def load(proj):
    p = cfg_path(proj)
    if not os.path.isfile(p): die(f'no carousel.json in {proj} — run new_carousel.py first')
    with open(p, encoding='utf-8') as f: return json.load(f)


def save(proj, cfg):
    tmp = cfg_path(proj) + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(cfg, f, indent=1, ensure_ascii=False)
    os.replace(tmp, cfg_path(proj))


def P(proj, *parts):
    p = os.path.join(proj, *parts)
    os.makedirs(os.path.dirname(p) if os.path.splitext(p)[1] else p, exist_ok=True)
    return p


def theme(name):
    p = os.path.join(HERE, 'themes', f'{name}.json')
    if not os.path.isfile(p):
        die(f'unknown theme "{name}" — available: ' + ', '.join(sorted(f[:-5] for f in os.listdir(os.path.join(HERE, 'themes')))))
    with open(p, encoding='utf-8') as f: return json.load(f)


def canvas(cfg):
    return SIZES.get(cfg.get('size', '4:5'), SIZES['4:5'])


def photo_path(proj, ref):
    """A slide's photo reference → absolute path (relative to the project, or a bare name found in <proj>/photos)."""
    if not ref: return None
    p = os.path.join(proj, os.path.expanduser(ref))
    if os.path.isfile(p): return os.path.abspath(p)
    for d in ('photos', 'assets', '.'):
        for f in os.listdir(os.path.join(proj, d)) if os.path.isdir(os.path.join(proj, d)) else []:
            r = os.path.basename(ref).lower(); fl = f.lower()
            if fl.endswith(PHOTO_EXT) and (fl == r or os.path.splitext(fl)[0] == r or
                                           (r.endswith(PHOTO_EXT) and os.path.splitext(fl)[0] == os.path.splitext(r)[0])):
                return os.path.abspath(os.path.join(proj, d, f))
    die(f'photo "{ref}" not found (looked in {proj} and {proj}/photos)')


def stem(path): return os.path.splitext(os.path.basename(path))[0]


def open_photo(path):
    """Open any photo as an upright RGB PIL image (EXIF orientation applied; HEIC via pillow-heif or macOS sips)."""
    from PIL import Image, ImageOps
    if path.lower().endswith(('.heic', '.heif')):
        try:
            import pillow_heif; pillow_heif.register_heif_opener()
        except ImportError:
            if platform.system() == 'Darwin' and shutil.which('sips'):
                jpg = os.path.join(os.path.dirname(path), '.' + stem(path) + '.jpg')
                if not os.path.exists(jpg):
                    subprocess.run(['sips', '-s', 'format', 'jpeg', path, '--out', jpg], check=True, capture_output=True)
                path = jpg
            else:
                die('HEIC photo: run the installer again (it adds pillow-heif), or export the photo as JPG')
    im = Image.open(path)
    return trim_borders(ImageOps.exif_transpose(im).convert('RGB'))


def trim_borders(im):
    """Cut flat black/white bars (screenshots of photos, letterboxed exports)."""
    import numpy as np
    a = np.asarray(im.convert('L').resize((max(1, im.width // 4), max(1, im.height // 4))), np.float32)
    flat = lambda v: v.std() < 3 and (v.mean() < 14 or v.mean() > 245)
    t, b, l, r = 0, a.shape[0], 0, a.shape[1]
    while t < b - 8 and flat(a[t]): t += 1
    while b > t + 8 and flat(a[b - 1]): b -= 1
    while l < r - 8 and flat(a[t:b, l]): l += 1
    while r > l + 8 and flat(a[t:b, r - 1]): r -= 1
    if (t, b, l, r) == (0, a.shape[0], 0, a.shape[1]) or (b - t) * (r - l) < 0.3 * a.size: return im
    return im.crop((l * 4 + (2 if l else 0), t * 4 + (2 if t else 0), min(im.width, r * 4 - (2 if r < a.shape[1] else 0)),
                    min(im.height, b * 4 - (2 if b < a.shape[0] else 0))))
