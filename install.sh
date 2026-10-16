#!/usr/bin/env bash
# Carousels: a free Claude Code skill that turns your photos into Instagram carousels.
# By @codecoffeechaos · https://cyberspell.tech/carousel-skill · GPL-3.0
#
# Install or update (Mac):   curl -fsSL https://cyberspell.tech/carousel-skill/install.sh | bash
# Check:                     bash ~/.claude/skills/carousels/install.sh --doctor
# Uninstall:                 bash ~/.claude/skills/carousels/install.sh --uninstall
#
# Without Terminal: unzip carousels-skill.zip, open the folder in the Claude app's Code tab and ask Claude to run
# this installer. Run from an unzipped folder, it installs that folder's files instead of downloading them.
#
# What it touches: ~/.claude/skills/carousels (the skill) and ~/.carousels (Python, models, browser).
# Your work in ~/Carousels is never touched.
# Stats: at the end it sends one anonymous count (installed, or the step that failed, plus OS) to Umami.
# No personal data. Skip it with CAROUSELS_NO_STATS=1.
set -euo pipefail

BASE="${CAROUSELS_BASE_URL:-https://cyberspell.tech/carousel-skill}"
CH="${CAROUSELS_HOME:-$HOME/.carousels}"
SKILL="${CAROUSELS_SKILL_DIR:-$HOME/.claude/skills/carousels}"
PY="$CH/venv/bin/python"
UMAMI_ID="18fcec8a-1398-4b38-9913-e45ec41863b8"                      # Umami website ID for the anonymous install count; empty = off
SRC="$(cd "$(dirname "${BASH_SOURCE[0]:-/nonexistent}")" 2>/dev/null && pwd || true)"
MODE=download
if [ -n "$SRC" ] && [ -f "$SRC/SKILL.md" ] && [ -d "$SRC/engine" ] && [ "$SRC" != "$SKILL" ]; then MODE=local; fi
STEP=start

RVM_COMMIT=53d74c6826735f01f4406b5ca9075eee27bec094
RVM_SRC="${CAROUSELS_RVM_SRC:-https://github.com/PeterL1n/RobustVideoMatting/archive/$RVM_COMMIT.zip}"
RVM_W=https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50.pth
RVM_SHA=c191a807251164c073dce5fa408e7a816070d539b882b2a3150330a9fec112ce
POSE=https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task

stat() {
  [ -n "$UMAMI_ID" ] && [ -z "${CAROUSELS_NO_STATS:-}" ] || return 0
  curl -s -m 4 -o /dev/null -X POST https://gateway.umami.is/api/send \
    -H 'Content-Type: application/json' -H 'User-Agent: Mozilla/5.0 (Macintosh; carousels-installer)' \
    -d "{\"type\":\"event\",\"payload\":{\"website\":\"$UMAMI_ID\",\"hostname\":\"cyberspell.tech\",\"url\":\"/carousel-skill/install\",\"name\":\"$1\",\"data\":{\"os\":\"$(uname -s | tr A-Z a-z)\",\"arch\":\"$(uname -m)\",\"mode\":\"$MODE\",\"step\":\"$STEP\"}}}" || true
}
say()  { printf '\033[1;35m▸\033[0m %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
fail() { printf '\n\033[31m✗ %s\033[0m\n' "$*"; stat install_failed; exit 1; }

case "${1:-}" in
  --doctor)
    [ -x "$PY" ] || fail "Not installed yet. Run: curl -fsSL $BASE/install.sh | bash"
    exec "$PY" "$SKILL/engine/doctor.py" ;;
  --uninstall)
    say "Removing Carousels"
    for d in "$SKILL" "$CH"; do
      if [ -d "$d" ]; then rm -rf "$d"; ok "deleted $d"; fi
    done
    ok "your carousels in ~/Carousels are untouched"
    exit 0 ;;
esac

echo
say "Installing Carousels (a few minutes; about 1.5 GB on first install)"

# 1. platform
STEP=platform
OS="$(uname -s)"; ARCH="$(uname -m)"
if [ "$OS" = "Darwin" ]; then
  [ "$ARCH" = "arm64" ] && ok "Mac with Apple Silicon" || warn "Intel Mac: not tested, it should work but slower"
elif [ "$OS" = "Linux" ]; then
  warn "Linux: not officially supported, trying anyway"
else
  fail "On Windows, open PowerShell and run:  irm $BASE/install.ps1 | iex"
fi
command -v claude >/dev/null 2>&1 || [ -d "$HOME/.claude" ] || \
  warn "Claude Code not found. Install it too: https://code.claude.com/docs/en/overview"

STEP=uv
# 2. uv (Python manager by Astral, installs Python without touching your system)
if ! command -v uv >/dev/null 2>&1; then
  [ -x "$HOME/.local/bin/uv" ] || { say "Getting uv"; curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null; }
  export PATH="$HOME/.local/bin:$PATH"
fi
command -v uv >/dev/null 2>&1 || fail "Could not install uv. Check your internet connection and run the command again."
ok "uv $(uv --version | awk '{print $2}')"

# 3. Python 3.12 in its own environment
STEP=python
mkdir -p "$CH/models"
if [ ! -x "$PY" ]; then
  say "Setting up Python 3.12"
  uv venv --quiet --python 3.12 "$CH/venv" || fail "Could not set up Python. Run the command again."
fi
ok "Python $("$PY" -c 'import platform; print(platform.python_version())')"

# 4. the skill itself
STEP=skill
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [ "$MODE" = local ]; then
  say "Installing the skill from $SRC"
  "$PY" - "$SRC" "$TMP/skill.zip" <<'PYZIP'
import os, sys, zipfile
src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(out, 'w') as z:
    for d, ds, fs in os.walk(src):
        ds[:] = [x for x in ds if x not in ('__pycache__', '.git', 'carousel-skill', '_build')]
        for f in fs:
            if f.endswith('.pyc') or f in ('.DS_Store', 'carousels-skill.zip'): continue
            p = os.path.join(d, f); z.write(p, os.path.relpath(p, src))
PYZIP
else
say "Downloading the skill"
curl -fsSL "$BASE/carousels-skill.zip" -o "$TMP/skill.zip" || fail "Could not download $BASE/carousels-skill.zip"
if curl -fsSL "$BASE/carousels-skill.zip.sha256" -o "$TMP/skill.sha256" 2>/dev/null; then
  "$PY" - "$TMP/skill.zip" "$TMP/skill.sha256" <<'EOF' || fail "The download is damaged. Run the command again."
import hashlib, sys
want = open(sys.argv[2]).read().split()[0].lower()
got = hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest()
sys.exit(0 if got == want else 1)
EOF
fi
fi
if [ -d "$SKILL" ]; then
  grep -q '^name: carousels' "$SKILL/SKILL.md" 2>/dev/null || fail "$SKILL exists and isn't this skill. Move it away and run again."
  rm -rf "$SKILL"
fi
mkdir -p "$SKILL"
"$PY" -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$TMP/skill.zip" "$SKILL"
chmod +x "$SKILL/install.sh" 2>/dev/null || true
ok "skill in $SKILL"

# 5. Python packages
STEP=packages
say "Installing packages (PyTorch, OpenCV, MediaPipe, Playwright…)"
if [ -n "${CAROUSELS_TORCH_INDEX:-}" ]; then
  uv pip install --quiet --python "$PY" torch torchvision --index-url "$CAROUSELS_TORCH_INDEX"
fi
uv pip install --quiet --python "$PY" -r "$SKILL/engine/requirements.txt" || fail "Package install failed. Run the command again."
ok "packages"

# 6. a browser to render slides
STEP=browser
if [ -d "/Applications/Google Chrome.app" ] || command -v google-chrome >/dev/null 2>&1; then
  ok "renders with your Google Chrome"
else
  say "Getting a browser for rendering (Chromium)"
  PLAYWRIGHT_BROWSERS_PATH="$CH/browsers" "$PY" -m playwright install chromium >/dev/null || fail "Could not download Chromium. Run the command again."
  ok "Chromium"
fi

# 7. models (downloaded from their official sources)
STEP=models
say "Downloading the cut-out and pose models"
W="$CH/models/rvm_resnet50.pth"
sha() { "$PY" -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$1"; }
if [ ! -f "$W" ] || [ "$(sha "$W")" != "$RVM_SHA" ]; then
  curl -fL --progress-bar "$RVM_W" -o "$W.part" || fail "Could not download the cut-out model."
  [ "$(sha "$W.part")" = "$RVM_SHA" ] || { rm -f "$W.part"; fail "Cut-out model checksum mismatch. Run the command again."; }
  mv "$W.part" "$W"
fi
ok "RobustVideoMatting weights"
if [ ! -f "$CH/models/RVM/model/model.py" ]; then
  if [ -d "$RVM_SRC" ]; then cp -R "$RVM_SRC" "$TMP/rvm"; else
    curl -fsSL "$RVM_SRC" -o "$TMP/rvm.zip" || fail "Could not download the cut-out model code."
    "$PY" -c "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$TMP/rvm.zip" "$TMP/rvmx"
    mv "$TMP"/rvmx/RobustVideoMatting-* "$TMP/rvm"
  fi
  rm -rf "$CH/models/RVM"; mkdir -p "$CH/models/RVM"
  cp -R "$TMP/rvm/model" "$CH/models/RVM/model"; cp "$TMP/rvm/LICENSE" "$CH/models/RVM/LICENSE" 2>/dev/null || true
fi
ok "RobustVideoMatting code"
PT="$CH/models/pose_landmarker_heavy.task"
if ! "$PY" -c "import zipfile,sys; sys.exit(0 if zipfile.is_zipfile(sys.argv[1]) else 1)" "$PT" 2>/dev/null; then
  curl -fL --progress-bar "$POSE" -o "$PT.part" || fail "Could not download the pose model."
  mv "$PT.part" "$PT"
fi
ok "MediaPipe pose model"

# 8. your work folder
mkdir -p "$HOME/Carousels"
ok "your carousels will live in ~/Carousels"

# 9. check
STEP=doctor
echo
"$PY" "$SKILL/engine/doctor.py" || fail "Something is still missing (see above). Run the command again; if it keeps failing, DM @codecoffeechaos a screenshot."
STEP=done; stat install_ready
echo
printf '\033[1;35mDone.\033[0m Next: type  \033[1mcd ~/Carousels\033[0m  then  \033[1mclaude\033[0m  and in Claude type  \033[1m/carousels\033[0m\n'
printf '(Or open the Code tab in the Claude app and choose the Carousels folder. Restart Claude Code if it was open.)\n'
printf 'Posting your carousel? Tag @codecoffeechaos so I can see it.\n\n'
