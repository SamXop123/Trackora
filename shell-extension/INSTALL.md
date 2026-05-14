# Trackora GNOME Shell extension — install and test

This extension runs **inside gnome-shell** on Fedora GNOME **Wayland** (and X11). It uses **Mutter / Meta** APIs (`Meta.Display`, `Meta.Window`) that are not available to ordinary desktop processes.

## Shared state file (Python backend)

Every **3 seconds** (and once on enable), the extension writes:

**`$XDG_DATA_HOME/trackora/current_window.json`**

On a typical user session that is:

**`~/.local/share/trackora/current_window.json`**

Example contents:

```json
{
  "app": "Firefox",
  "title": "YouTube",
  "timestamp": "2026-05-13T19:30:00"
}
```

The **Python** package does not detect focus itself; run `python3 -m trackora` from the Trackora repo to **read this file** on the same interval and print lines to stdout. Install the extension first and enable it, or the backend will only report that no valid state file exists.

## Requirements

- Fedora Workstation with **GNOME Shell** (Wayland session is typical).
- GNOME Shell **45+** (extension uses the GNOME 45+ ESM extension template). If `gnome-shell --version` is older than 45, this tree will not load; adjust `shell-version` in `metadata.json` only if you maintain a fork for older shells.

## Install (user extension)

1. Copy the UUID folder to your user extensions directory (the folder name **must** match `uuid` in `metadata.json`):

   ```bash
   EXT_UUID=trackora@trackora.dev
   SRC="/path/to/Trackora/shell-extension/${EXT_UUID}"
   DEST="${HOME}/.local/share/gnome-shell/extensions/${EXT_UUID}"
   mkdir -p "${DEST}"
   cp -r "${SRC}"/* "${DEST}/"
   ```

2. **Log out and log back in** (or restart GNOME Shell). On **Wayland**, restarting the shell is easiest via a full session restart; `Alt`+`F2`, `r`, `Enter` only works reliably on legacy X11 sessions.

3. Enable the extension:

   ```bash
   gnome-extensions enable trackora@trackora.dev
   ```

   Or use **Extensions** (gnome-extensions-app): turn **Trackora** on.

## Test

1. **Verify the JSON file** (after a few seconds with the extension enabled):

   ```bash
   cat ~/.local/share/trackora/current_window.json
   ```

   Switch focus between apps; after each 3s tick the file should update.

2. **Run the Python backend** (from the Trackora git root):

   ```bash
   python3 -m trackora
   ```

   You should see lines like `[19:30:00] Firefox - YouTube`. If the file is missing or invalid, the process prints a short message to **stderr** and keeps polling.

3. **Optional: journal.** On write errors the extension uses `console.warn`, which may appear in the journal:

   ```bash
   journalctl --user -f -o cat | grep --line-buffered Trackora
   ```

4. **Confirm it is loaded.** Open **Extensions** and ensure Trackora shows as **On** with no error badge. For deeper diagnostics, open Looking Glass (`Alt`+`F2`, run `lg`), open the **Errors** tab, and look for stack traces mentioning `trackora@trackora.dev`.

## Disable / remove

```bash
gnome-extensions disable trackora@trackora.dev
rm -rf "${HOME}/.local/share/gnome-shell/extensions/trackora@trackora.dev"
```

Then log out and in again (or restart the session) if the shell keeps a stale reference.

## Optional: pack as a zip

```bash
cd shell-extension
zip -r trackora@trackora.dev.zip trackora@trackora.dev
gnome-extensions install --force trackora@trackora.dev.zip
```

Use `--force` when upgrading an existing copy.
