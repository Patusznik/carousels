# Installing Carousels

## The quick way (one command)

- **Mac** (Terminal): `curl -fsSL https://cyberspell.tech/carousel-skill/install.sh | bash`
- **Windows** (PowerShell): `irm https://cyberspell.tech/carousel-skill/install.ps1 | iex`

Wait for **READY**, then start Claude Code in your `Carousels` folder and type `/carousels`.

## Without Terminal: let Claude install it

1. Download the skill as a zip and unzip it (double-click on a Mac; right-click → *Extract All* on Windows).
2. Open the Claude desktop app, go to the *Code* tab and choose the unzipped folder.
3. Type: *Run the installer in this folder and tell me when it says READY.*
4. Allow the commands Claude asks to run. It takes a few minutes.
5. When it says READY, open the *Code* tab again, choose the *Carousels* folder in your home folder, and type
   `/carousels`.

## For Claude: running the installer from this folder

The user unzipped this skill and wants it installed. From this folder:

- **Mac:** `bash install.sh`
- **Windows:** `powershell -ExecutionPolicy Bypass -File install.ps1` (from Git Bash or PowerShell)

Run from this folder, the installer uses these files instead of downloading them. It takes several minutes (it
downloads Python packages and about 1.5 GB of models), so give the command a long timeout or run it in the background
and check its output. It ends with `READY` or with the exact step that failed and how to fix it. When it's READY, tell
the user to start Claude Code in `~/Carousels` (restart it if this session should see the new skill) and type
`/carousels`.

## Check or remove it

- Check: `bash ~/.claude/skills/carousels/install.sh --doctor` (Windows: `install.ps1 -Doctor`)
- Remove: `bash ~/.claude/skills/carousels/install.sh --uninstall` (Windows: `install.ps1 -Uninstall`).
  Your `Carousels` folder stays.
