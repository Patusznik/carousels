"""Checks that everything the Carousels engine needs is in place. Prints READY, or each missing piece and how to fix it.

usage:  <venv python> doctor.py [--quick]      (--quick skips the browser launch)
"""
import importlib, os, platform, sys, zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HOME, MODELS, VENV  # noqa: E402

FIX = 'run the installer again'
problems, notes = [], []


def need(mod, pip_name=None):
    try:
        return importlib.import_module(mod)
    except Exception as e:
        problems.append(f'Python package "{pip_name or mod}" missing or broken ({str(e)[:60]}) → {FIX}')


def main():
    print(f'Carousels doctor · {platform.system()} {platform.machine()} · Python {platform.python_version()}')
    if os.path.realpath(sys.prefix) != os.path.realpath(VENV):
        notes.append(f'not running inside {VENV} (fine for a check, the engine switches to it by itself)')

    for mod, pipn in [('numpy', None), ('scipy', None), ('PIL', 'pillow'), ('pillow_heif', 'pillow-heif'),
                      ('cv2', 'opencv-python-headless'), ('torchvision', None), ('mediapipe', None),
                      ('imageio_ffmpeg', 'imageio-ffmpeg'), ('playwright.sync_api', 'playwright')]:
        need(mod, pipn)
    torch = need('torch')
    if torch:
        dev = 'mps (Apple GPU)' if torch.backends.mps.is_available() else ('cuda (NVIDIA GPU)' if torch.cuda.is_available() else 'cpu')
        notes.append(f'cut-out runs on: {dev}' + ('  (slower; fine, just give the first render a minute)' if dev == 'cpu' else ''))

    w = os.path.join(MODELS, 'rvm_resnet50.pth')
    if not os.path.isfile(w) or os.path.getsize(w) < 100_000_000:
        problems.append(f'cut-out model missing ({w}) → {FIX}')
    if not os.path.isfile(os.path.join(MODELS, 'RVM', 'model', 'model.py')):
        problems.append(f'cut-out model code missing ({MODELS}/RVM/model) → {FIX}')
    pose = os.path.join(MODELS, 'pose_landmarker_heavy.task')
    if not (os.path.isfile(pose) and zipfile.is_zipfile(pose)):
        problems.append(f'pose model missing ({pose}) → {FIX}')

    if not problems and torch:
        try:
            sys.path.insert(0, os.path.join(MODELS, 'RVM'))
            from model import MattingNetwork
            m = MattingNetwork('resnet50').eval()
            m.load_state_dict(torch.load(w, map_location='cpu'))
        except Exception as e:
            problems.append(f'cut-out model does not load ({str(e)[:80]}) → {FIX}')

    try:
        import imageio_ffmpeg, shutil
        ff = shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()
        if not ff or not os.path.exists(ff): raise RuntimeError('no binary')
    except Exception:
        problems.append(f'ffmpeg missing (needed for videos only) → {FIX}')

    if '--quick' not in sys.argv and not any('playwright' in p for p in problems):
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                try:
                    b = p.chromium.launch(channel='chrome'); which = 'Google Chrome'
                except Exception:
                    b = p.chromium.launch(); which = 'Chromium'
                pg = b.new_page(); pg.set_content('<p id=x>ok</p>'); ok = pg.inner_text('#x') == 'ok'; b.close()
            if not ok: raise RuntimeError('page did not render')
            notes.append(f'slides render with: {which}')
        except Exception as e:
            problems.append(f'no browser for rendering ({str(e).splitlines()[0][:80]}) → {FIX}')

    for n in notes: print('  · ' + n)
    if problems:
        print('\n✗ NOT READY')
        for p in problems: print('  ✗ ' + p)
        sys.exit(1)
    print(f'\n✓ READY   (tools and models in {HOME})')


if __name__ == '__main__':
    main()
