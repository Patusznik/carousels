"""Start a carousel project.

usage:  python3 new_carousel.py <project_dir> [--theme lilac] [--handle @you] [--lang en|pl] [--size 4:5|3:4|1:1]
                                [--photos file_or_folder …]
→ <project>/carousel.json (no slides yet) and <project>/photos/ (copies of the photos you pass; from videos the 4 sharpest stills).
Next: import a script (script.py) or add slides one by one (slide.py add …), then render.py.
"""
import os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import save, cfg_path, theme, PHOTO_EXT, VIDEO_EXT, SIZES, die

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

if len(sys.argv) < 2: raise SystemExit(__doc__)
proj = os.path.abspath(os.path.expanduser(sys.argv[1]))
if os.path.exists(cfg_path(proj)) and '--force' not in sys.argv: die(f'{cfg_path(proj)} exists (use --force to start over)')
os.makedirs(os.path.join(proj, 'photos'), exist_ok=True)
th = arg('--theme', 'lilac'); theme(th)
size = arg('--size', '4:5')
if size not in SIZES: die(f'size must be one of {", ".join(SIZES)}')
copied, videos = [], []
if '--photos' in sys.argv:
    for a in sys.argv[sys.argv.index('--photos') + 1:]:
        if a.startswith('--'): break
        a = os.path.expanduser(a)
        files = [os.path.join(a, f) for f in sorted(os.listdir(a))] if os.path.isdir(a) else [a]
        for f in files:
            if f.lower().endswith(VIDEO_EXT) and os.path.isfile(f): videos.append(f); continue
            if f.lower().endswith(PHOTO_EXT) and os.path.isfile(f):
                dst = os.path.join(proj, 'photos', os.path.basename(f))
                if not os.path.exists(dst): shutil.copy2(f, dst)
                copied.append(os.path.basename(f))
cfg = {'theme': th, 'size': size, 'lang': arg('--lang', 'en'), 'handle': arg('--handle', ''), 'slides': []}
save(proj, cfg)
if videos:                                       # videos → their sharpest stills (photos.py runs in the engine venv)
    import subprocess
    for v in videos:
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'photos.py'), proj, '--video', v], check=True)
print(f'carousel {proj}  ({size}, theme {th}, lang {cfg["lang"]})')
print('photos:', ', '.join(copied) if copied else '(none yet — put them in photos/)')
print('next: python3 script.py', proj, 'script.md   or   python3 slide.py', proj, 'add layout=cover photo=… title="…"')
