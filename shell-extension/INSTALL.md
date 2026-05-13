# Trackora GNOME Shell extension — install and test

This extension runs **inside gnome-shell** on Fedora GNOME **Wayland** (and X11). It uses **Mutter / Meta** APIs (`Meta.Display`, `Meta.Window`) that are not available to ordinary desktop processes, which is why a Shell extension is the reliable approach.

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

1. **Watch logs.** Extension output uses `console.log`, which gnome-shell records to the journal. In a terminal:

   ```bash
   journalctl --user -f -o cat | grep --line-buffered Trackora
   ```

   If nothing appears, try without `--user` (depending on how your distro tags gnome-shell):

   ```bash
   journalctl -f -o cat | grep --line-buffered Trackora
   ```

2. **Confirm it is loaded.** Open **Extensions** and ensure Trackora shows as **On** with no error badge. For deeper diagnostics, open Looking Glass (`Alt`+`F2`, run `lg`), open the **Errors** tab, and look for stack traces mentioning `trackora@trackora.dev`.

3. **Exercise focus.** Switch between Firefox, Terminal, Settings, etc. Every **3 seconds** you should see a line like:

   ```text
   [Trackora] [14:02:10] Firefox - Example Page — Mozilla Firefox
   ```

   The bracketed time is local wall clock; the segment after it matches the earlier Trackora CLI format: `Application - Window title`.

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
