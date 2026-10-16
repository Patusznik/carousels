# Carousels: a free Claude Code skill that turns your photos into Instagram carousels.
# By @codecoffeechaos - https://cyberspell.tech/carousel-skill - GPL-3.0
#
# Install or update (Windows PowerShell):  irm https://cyberspell.tech/carousel-skill/install.ps1 | iex
# Check:      powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\carousels\install.ps1" -Doctor
# Uninstall:  powershell -ExecutionPolicy Bypass -File "$HOME\.claude\skills\carousels\install.ps1" -Uninstall
#
# Without Terminal: unzip carousels-skill.zip, open the folder in the Claude app's Code tab and ask Claude to run
# this installer. Run from an unzipped folder, it installs that folder's files instead of downloading them.
# Stats: at the end it sends one anonymous count (installed, or the step that failed, plus OS) to Umami.
# No personal data. Skip it with CAROUSELS_NO_STATS=1.
#
# What it touches: %USERPROFILE%\.claude\skills\carousels (the skill) and %USERPROFILE%\.carousels (Python, models,
# browser). Your work in %USERPROFILE%\Carousels is never touched.
param([switch]$Doctor, [switch]$Uninstall)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Base  = if ($env:CAROUSELS_BASE_URL) { $env:CAROUSELS_BASE_URL } else { 'https://cyberspell.tech/carousel-skill' }
$CH    = if ($env:CAROUSELS_HOME) { $env:CAROUSELS_HOME } else { Join-Path $HOME '.carousels' }
$Skill = Join-Path $HOME '.claude\skills\carousels'
$Py    = Join-Path $CH 'venv\Scripts\python.exe'
$UmamiId = '18fcec8a-1398-4b38-9913-e45ec41863b8'                    # Umami website ID for the anonymous install count; empty = off
$Src = $PSScriptRoot
$Mode = 'download'
if ($Src -and (Test-Path (Join-Path $Src 'SKILL.md')) -and (Test-Path (Join-Path $Src 'engine')) -and ((Resolve-Path $Src).Path -ne $Skill)) { $Mode = 'local' }
$script:Step = 'start'

$RvmCommit = '53d74c6826735f01f4406b5ca9075eee27bec094'
$RvmSrc  = "https://github.com/PeterL1n/RobustVideoMatting/archive/$RvmCommit.zip"
$RvmW    = 'https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_resnet50.pth'
$RvmSha  = 'C191A807251164C073DCE5FA408E7A816070D539B882B2A3150330A9FEC112CE'
$Pose    = 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task'

function Say($m)  { Write-Host "> $m" -ForegroundColor Magenta }
function Ok($m)   { Write-Host "  OK $m" -ForegroundColor Green }
function Warn($m) { Write-Host "  !  $m" -ForegroundColor Yellow }
function Stat($name) {
  if (-not $UmamiId -or $env:CAROUSELS_NO_STATS) { return }
  try {
    $body = @{ type = 'event'; payload = @{ website = $UmamiId; hostname = 'cyberspell.tech'; url = '/carousel-skill/install'; name = $name;
      data = @{ os = 'windows'; arch = $env:PROCESSOR_ARCHITECTURE; mode = $Mode; step = $script:Step } } } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Method Post -Uri 'https://gateway.umami.is/api/send' -Body $body -ContentType 'application/json' `
      -UserAgent 'Mozilla/5.0 (Windows NT 10.0; carousels-installer)' -TimeoutSec 4 | Out-Null
  } catch { }
}
function Fail($m) { Write-Host "`nX $m" -ForegroundColor Red; Stat 'install_failed'; throw $m }
function Get($url, $out) { Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing }

if ($Doctor) {
  if (-not (Test-Path $Py)) { Fail "Not installed yet. Run:  irm $Base/install.ps1 | iex" }
  & $Py (Join-Path $Skill 'engine\doctor.py'); exit $LASTEXITCODE
}
if ($Uninstall) {
  Say 'Removing Carousels'
  foreach ($d in @($Skill, $CH)) { if (Test-Path $d) { Remove-Item -Recurse -Force $d; Ok "deleted $d" } }
  Ok 'your carousels in Carousels are untouched'; return
}

Write-Host ''
Say 'Installing Carousels (a few minutes; about 2 GB on first install)'

# 1. platform
$script:Step = 'platform'
if (-not [Environment]::Is64BitOperatingSystem) { Fail 'Carousels needs 64-bit Windows.' }
if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { Warn 'Windows on ARM: not tested' } else { Ok 'Windows 64-bit' }
if (-not (Get-Command claude -ErrorAction SilentlyContinue) -and -not (Test-Path (Join-Path $HOME '.claude'))) {
  Warn 'Claude Code not found. Install it too: https://code.claude.com/docs/en/overview'
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Warn 'Git for Windows not found. Recommended for Claude Code: https://git-scm.com/downloads/win'
}

# 2. uv (Python manager by Astral)
$script:Step = 'uv'
$env:Path = "$HOME\.local\bin;$env:Path"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Say 'Getting uv'
  powershell -ExecutionPolicy ByPass -NoProfile -c "irm https://astral.sh/uv/install.ps1 | iex" | Out-Null
  $env:Path = "$HOME\.local\bin;$env:Path"
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { Fail 'Could not install uv. Check your internet connection and run the command again.' }
Ok "uv $((uv --version).Split(' ')[1])"

# 3. Python 3.12 in its own environment
$script:Step = 'python'
New-Item -ItemType Directory -Force -Path (Join-Path $CH 'models') | Out-Null
if (-not (Test-Path $Py)) {
  Say 'Setting up Python 3.12'
  uv venv --quiet --python 3.12 (Join-Path $CH 'venv'); if ($LASTEXITCODE) { Fail 'Could not set up Python. Run the command again.' }
}
Ok "Python $(& $Py -c 'import platform; print(platform.python_version())')"

# 4. the skill itself
$script:Step = 'skill'
$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("carousels-" + [guid]::NewGuid())
New-Item -ItemType Directory -Force -Path $Tmp | Out-Null
try {
  if ($Mode -eq 'local') {
    Say "Installing the skill from $Src"
    $stage = Join-Path $Tmp 'stage'; New-Item -ItemType Directory -Force -Path $stage | Out-Null
    Get-ChildItem -Force $Src | Where-Object { $_.Name -notin @('carousel-skill','_build','.git','__pycache__','carousels-skill.zip','.DS_Store') } |
      ForEach-Object { Copy-Item -Recurse -Force $_.FullName (Join-Path $stage $_.Name) }
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath (Join-Path $Tmp 'skill.zip') -Force
  } else {
    Say 'Downloading the skill'
    Get "$Base/carousels-skill.zip" (Join-Path $Tmp 'skill.zip')
    $want = $null
    try {
      Get "$Base/carousels-skill.zip.sha256" (Join-Path $Tmp 'skill.sha256')
      $want = ((Get-Content (Join-Path $Tmp 'skill.sha256') -Raw).Trim() -split '\s+')[0].ToUpper()
    } catch { }
    if ($want -and (Get-FileHash (Join-Path $Tmp 'skill.zip') -Algorithm SHA256).Hash -ne $want) { Fail 'The download is damaged. Run the command again.' }
  }
  if (Test-Path $Skill) {
    if (-not (Select-String -Path (Join-Path $Skill 'SKILL.md') -Pattern '^name: carousels' -Quiet -ErrorAction SilentlyContinue)) {
      Fail "$Skill exists and isn't this skill. Move it away and run again."
    }
    Remove-Item -Recurse -Force $Skill
  }
  New-Item -ItemType Directory -Force -Path $Skill | Out-Null
  Expand-Archive -Path (Join-Path $Tmp 'skill.zip') -DestinationPath $Skill -Force
  Ok "skill in $Skill"

  $script:Step = 'packages'
  # 5. Python packages (PyTorch with NVIDIA support when there's an NVIDIA card)
  Say 'Installing packages (PyTorch, OpenCV, MediaPipe, Playwright...)'
  if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    uv pip install --quiet --python $Py torch torchvision --index-url https://download.pytorch.org/whl/cu124
    if ($LASTEXITCODE) { Warn 'NVIDIA build of PyTorch failed, using the regular one' } else { Ok 'PyTorch with NVIDIA support' }
  }
  uv pip install --quiet --python $Py -r (Join-Path $Skill 'engine\requirements.txt')
  if ($LASTEXITCODE) { Fail 'Package install failed. Run the command again.' }
  Ok 'packages'

  $script:Step = 'browser'
  # 6. a browser to render slides
  $chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe", "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
              "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { $_ -and (Test-Path $_) }
  if ($chrome) { Ok 'renders with your Google Chrome' } else {
    Say 'Getting a browser for rendering (Chromium)'
    $env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $CH 'browsers'
    & $Py -m playwright install chromium | Out-Null
    if ($LASTEXITCODE) { Fail 'Could not download Chromium. Run the command again.' }
    Remove-Item Env:PLAYWRIGHT_BROWSERS_PATH; Ok 'Chromium'
  }

  $script:Step = 'models'
  # 7. models (downloaded from their official sources)
  Say 'Downloading the cut-out and pose models'
  $W = Join-Path $CH 'models\rvm_resnet50.pth'
  if (-not (Test-Path $W) -or (Get-FileHash $W -Algorithm SHA256).Hash -ne $RvmSha) {
    Get $RvmW "$W.part"
    if ((Get-FileHash "$W.part" -Algorithm SHA256).Hash -ne $RvmSha) { Remove-Item "$W.part"; Fail 'Cut-out model checksum mismatch. Run the command again.' }
    Move-Item -Force "$W.part" $W
  }
  Ok 'RobustVideoMatting weights'
  $RvmDir = Join-Path $CH 'models\RVM'
  if (-not (Test-Path (Join-Path $RvmDir 'model\model.py'))) {
    Get $RvmSrc (Join-Path $Tmp 'rvm.zip')
    Expand-Archive -Path (Join-Path $Tmp 'rvm.zip') -DestinationPath (Join-Path $Tmp 'rvmx') -Force
    $src = Get-ChildItem (Join-Path $Tmp 'rvmx') -Directory | Select-Object -First 1
    if (Test-Path $RvmDir) { Remove-Item -Recurse -Force $RvmDir }
    New-Item -ItemType Directory -Force -Path $RvmDir | Out-Null
    Copy-Item -Recurse (Join-Path $src.FullName 'model') (Join-Path $RvmDir 'model')
    Copy-Item (Join-Path $src.FullName 'LICENSE') (Join-Path $RvmDir 'LICENSE') -ErrorAction SilentlyContinue
  }
  Ok 'RobustVideoMatting code'
  $PT = Join-Path $CH 'models\pose_landmarker_heavy.task'
  & $Py -c "import zipfile,sys; sys.exit(0 if zipfile.is_zipfile(sys.argv[1]) else 1)" $PT 2>$null
  if ($LASTEXITCODE) { Get $Pose "$PT.part"; Move-Item -Force "$PT.part" $PT }
  Ok 'MediaPipe pose model'
} finally {
  Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
}

# 8. your work folder
New-Item -ItemType Directory -Force -Path (Join-Path $HOME 'Carousels') | Out-Null
Ok 'your carousels will live in Carousels in your home folder'

# 9. check
$script:Step = 'doctor'
Write-Host ''
& $Py (Join-Path $Skill 'engine\doctor.py')
if ($LASTEXITCODE) { Fail 'Something is still missing (see above). Run the command again; if it keeps failing, DM @codecoffeechaos a screenshot.' }
$script:Step = 'done'; Stat 'install_ready'
Write-Host ''
Write-Host 'Done. Next: type  cd ~/Carousels  then  claude  and in Claude type  /carousels' -ForegroundColor Magenta
Write-Host '(Or open the Code tab in the Claude app and choose the Carousels folder. Restart Claude Code if it was open.)'
Write-Host 'Posting your carousel? Tag @codecoffeechaos so I can see it.'
Write-Host ''
