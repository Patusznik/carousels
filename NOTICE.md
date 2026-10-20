# Notice

**Carousels** by @codecoffeechaos (CyberSpell Software) · https://carousels.cyberspell.tech
Copyright (C) 2026 CyberSpell Software (@codecoffeechaos).

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation, version 3 (see `LICENSE`). It comes with no warranty.

## What it uses

| component | license | how it gets here |
|---|---|---|
| RobustVideoMatting (code + `rvm_resnet50` weights), Peter Lin et al. | GPL-3.0 | downloaded from its GitHub repository during install |
| MediaPipe pose landmarker (heavy), Google | Apache-2.0 | downloaded from Google's model storage during install |
| PyTorch, torchvision, NumPy, SciPy | BSD-style | installed with uv from PyPI |
| OpenCV (opencv-python-headless) | Apache-2.0 / MIT | PyPI |
| Pillow | MIT-CMU (HPND) | PyPI |
| pillow-heif | BSD-3-Clause (libheif: LGPL-3.0) | PyPI |
| MediaPipe (Python package) | Apache-2.0 | PyPI |
| Playwright (+ Chromium when Chrome isn't installed) | Apache-2.0 (Chromium: BSD and others) | PyPI + Playwright's download |
| imageio-ffmpeg (bundled ffmpeg) | BSD-2-Clause (ffmpeg: LGPL/GPL) | PyPI |
| uv, Astral | Apache-2.0 / MIT | Astral's official installer |
| Fonts: Anton, Instrument Serif, Inter, JetBrains Mono, Playfair Display, GFS Didot, Jost | SIL Open Font License 1.1 | in `engine/templates/fonts/`, each with its license text |
| Didot, Futura | Apple macOS fonts | **not included**: used from the user's own Mac by name, never copied |

No company logos ship inside the UI elements. Names of apps that appear in the example carousel are the author's own
content, not part of the product.
