# Installing Carousels

## The quick way (one command)

- **Mac** (Terminal): `curl -fsSL https://carousels.cyberspell.tech/install.sh | bash`
- **Windows** (PowerShell): `irm https://carousels.cyberspell.tech/install.ps1 | iex`

Wait for **READY**, then start Claude Code in your `Carousels` folder and type `/carousels`.

## Try it in a test folder first

Everything (the skill, Python, packages, models, your carousels) goes into one folder, nothing is installed outside it,
and the skill only exists when you start Claude Code in that folder.

- **Mac:** `curl -fsSL https://carousels.cyberspell.tech/install.sh | CAROUSELS_SANDBOX=~/carousels-test bash`
- **Windows (PowerShell):** `$env:CAROUSELS_SANDBOX="$HOME\carousels-test"; irm https://carousels.cyberspell.tech/install.ps1 | iex`

Then `cd ~/carousels-test`, start `claude` and type `/carousels`. To remove it, delete the `carousels-test` folder.
Test installs don't send the anonymous install count.

## Without Terminal: let Claude install it

1. Download the skill as a zip and unzip it (double-click on a Mac; right-click → *Extract All* on Windows).
2. Open the Claude desktop app, go to the *Code* tab and choose the unzipped folder.
3. Type: *Run the installer in this folder and tell me when it says READY.*
4. Allow the commands Claude asks to run. It takes a few minutes.
5. When it says READY, start a new session in the *Code* tab and choose the *Carousels* folder in your home folder
   (the installer made it).
6. Type `/carousels`. The brief starts.

## For Claude: running the installer from this folder

The user unzipped this skill and wants it installed. From this folder:

- **Mac:** `bash install.sh`
- **Windows:** `powershell -ExecutionPolicy Bypass -File install.ps1` (from Git Bash or PowerShell)

Run from this folder, the installer uses these files instead of downloading them. It takes several minutes (it
downloads Python packages, a browser if Chrome is missing, and the models: 2 to 6 GB in all), so give the command a long timeout or run it in the background
and check its output. It ends with `READY` or with the exact step that failed and how to fix it. When it's READY, tell
the user to start Claude Code in `~/Carousels` (restart it if this session should see the new skill) and type
`/carousels`.

## Check or remove it

- Check: `bash ~/.claude/skills/carousels/install.sh --doctor` (Windows: `install.ps1 -Doctor`)
- Remove: `bash ~/.claude/skills/carousels/install.sh --uninstall` (Windows: `install.ps1 -Uninstall`).
  Your `Carousels` folder stays.
