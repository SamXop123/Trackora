# Trackora systemd user service setup

Trackora is designed to run as a **systemd user service** on Fedora GNOME. This
lets it start automatically when the user logs in, restart after failures, and
write logs into the user journal.

## Files

- Service unit in this repo:

  ```text
  systemd/trackora.service
  ```

- Recommended final RPM install location:

  ```text
  /usr/lib/systemd/user/trackora.service
  ```

Systemd will then expose it automatically to every user session.

## What the service runs

The service executes:

```bash
python3 -m trackora
```

In the unit file this is expressed as:

```ini
ExecStart=/usr/bin/python3 -m trackora
```

This works best once Trackora is installed as a normal Python package by your
RPM so that `python3 -m trackora` resolves from anywhere.

## Fedora user-service behavior

- Starts on user login
- Runs in the background without a terminal
- Restarts if the tracker process crashes
- Logs go to `journalctl --user`

## Local development setup

If you are testing from the repo before RPM packaging, first make sure Python
can import `trackora` from your checkout. The simplest dev-friendly option is:

```bash
cd /home/samxop123/dev-work/Trackora
python3 -m trackora
```

For a user service during development, copy the unit into your user systemd
directory and edit `ExecStart` if needed for your environment.

Create the user service directory:

```bash
mkdir -p ~/.config/systemd/user
```

Copy the unit:

```bash
cp systemd/trackora.service ~/.config/systemd/user/trackora.service
```

If Trackora is **not yet installed system-wide or as a Python package**, update
the copied unit to use your checkout. A safe development variant is:

```ini
WorkingDirectory=/home/your-user/path/to/Trackora
Environment=PYTHONPATH=/home/your-user/path/to/Trackora
ExecStart=/usr/bin/python3 -m trackora
```

After editing, reload the user manager:

```bash
systemctl --user daemon-reload
```

## Production / RPM behavior

For the final Fedora RPM, install:

- the Python package into the normal Python site-packages path
- the user service unit into:

  ```text
  /usr/lib/systemd/user/trackora.service
  ```

Then the user only needs systemd user commands to enable/start it.

## Commands

Enable auto-start on login:

```bash
systemctl --user enable trackora.service
```

Enable and start immediately:

```bash
systemctl --user enable --now trackora.service
```

Start:

```bash
systemctl --user start trackora.service
```

Stop:

```bash
systemctl --user stop trackora.service
```

Restart:

```bash
systemctl --user restart trackora.service
```

Check status:

```bash
systemctl --user status trackora.service
```

Inspect recent logs:

```bash
journalctl --user -u trackora.service
```

Follow logs live:

```bash
journalctl --user -u trackora.service -f
```

Disable auto-start:

```bash
systemctl --user disable trackora.service
```

Disable and stop immediately:

```bash
systemctl --user disable --now trackora.service
```

## Recommended project structure

This repo now benefits from keeping service-related assets separate:

```text
systemd/
├── trackora.service
└── INSTALL.md
```

This keeps runtime Python code separate from deployment and startup integration.
