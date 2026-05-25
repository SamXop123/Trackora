# Trackora Developer Recovery & Troubleshooting Guide

Internal recovery and debugging handbook for Trackora development on Fedora GNOME Wayland.

---

# Table of Contents

1. Project Architecture
2. Golden Recovery Sequence
3. GNOME Extension Troubleshooting
4. systemd Service Troubleshooting
5. Tracker Debugging
6. Database Debugging
7. Dashboard/UI Debugging
8. Common Failure Patterns
9. Safe Development Workflow
10. Useful Commands Reference

---

# 1. Project Architecture

Trackora pipeline:

GNOME Extension
↓
current_window.json
↓
Python tracker backend
↓
SQLite database
↓
PyQt dashboard

Main integration points:

- GNOME Shell extension
- systemd user service
- SQLite database
- dashboard frontend

Most failures occur because one of these layers stops updating.

---

# 2. GOLDEN RECOVERY SEQUENCE

If Trackora suddenly stops working:

## Step 1 — Verify extension exists

```bash
ls ~/.local/share/gnome-shell/extensions/
````

Expected:

```text
trackora@trackora.dev
```

---

## Step 2 — Verify extension enabled

```bash
gnome-extensions list
```

Expected:

```text
trackora@trackora.dev
```

If missing:

```bash
gnome-extensions enable trackora@trackora.dev
```

---

## Step 3 — Verify service exists

```bash
ls ~/.config/systemd/user/
```

Expected:

```text
trackora.service
```

---

## Step 4 — Reload systemd

```bash
systemctl --user daemon-reload
```

---

## Step 5 — Restart tracker service

```bash
systemctl --user restart trackora.service
```

---

## Step 6 — Verify service running

```bash
systemctl --user status trackora.service
```

Expected:

```text
active (running)
```

---

## Step 7 — Verify tracker logs

```bash
journalctl --user -u trackora.service -f
```

Expected:

```text
[Trackora] Session started
[Trackora] Session ended
```

---

## Step 8 — Verify app switching

Switch between:

* Chrome
* VS Code
* Terminal

Dashboard should update active app.

---

# 3. GNOME EXTENSION TROUBLESHOOTING

---

## Check GNOME version

```bash
gnome-shell --version
```

Example:

```text
GNOME Shell 50.1
```

---

## Extension compatibility issue

Symptom:

```text
This extension is incompatible with your current version of GNOME
```

Fix:

Edit metadata:

```bash
nano ~/.local/share/gnome-shell/extensions/trackora@trackora.dev/metadata.json
```

Ensure:

```json
{
  "shell-version": ["45", "46", "47", "48", "49", "50"]
}
```

---

## Common metadata.json mistake

Broken:

```json
"shell-version": ["50"]

"session-modes": ["user"]
```

Correct:

```json
"shell-version": ["50"],

"session-modes": ["user"]
```

Missing comma causes:

```text
Failed to parse metadata.json
```

---

## Reload GNOME Shell

Wayland-safe reload:

```bash
killall -3 gnome-shell
```

Then:

* logout
* login again

---

## View GNOME extension logs

```bash
journalctl --user -b | grep -i trackora
```

Useful for:

* metadata errors
* extension crashes
* compatibility issues

---

## Verify extension folder

```bash
ls ~/.local/share/gnome-shell/extensions/trackora@trackora.dev
```

Should contain:

* metadata.json
* extension.js
* stylesheet.css

---

# 4. SYSTEMD SERVICE TROUBLESHOOTING

---

## Service not found

Error:

```text
Failed to restart trackora.service: Unit trackora.service not found
```

Fix:

```bash
mkdir -p ~/.config/systemd/user

cp ~/dev-work/Trackora/systemd/trackora.service ~/.config/systemd/user/
```

---

## Verify service contents

```bash
nano ~/.config/systemd/user/trackora.service
```

IMPORTANT:

```ini
[Service]
WorkingDirectory=/home/samxop123/dev-work/Trackora
Environment=PYTHONPATH=/home/samxop123/dev-work/Trackora
```

Without these:

* service may run wrong package
* singleton protection may fail

---

## Reload systemd

```bash
systemctl --user daemon-reload
```

---

## Enable service

```bash
systemctl --user enable --now trackora.service
```

---

## Restart service

```bash
systemctl --user restart trackora.service
```

---

## Verify service status

```bash
systemctl --user status trackora.service
```

Expected:

```text
active (running)
```

---

## Live service logs

```bash
journalctl --user -u trackora.service -f
```

---

# 5. TRACKER DEBUGGING

---

## Verify singleton protection

Run:

```bash
python3 -m trackora
```

Expected:

```text
Trackora tracker is already running
```

If tracker starts twice:

* singleton failed
* duplicate instances exist

---

## Verify current_window.json updates

Watch live:

```bash
watch cat ~/.local/share/trackora/current_window.json
```

Switch apps.

Expected:

* app name changes
* title changes
* timestamps update

---

## Verify app switching

Tracker should:

* end previous session
* start new session

Logs:

```bash
journalctl --user -u trackora.service -f
```

Expected:

```text
Session ended
Session started
```

---

## Sleep mode bug

Symptom:

* app keeps accumulating time during suspend

Fix:

* restart tracker service
* ensure timeout logic active

```bash
systemctl --user restart trackora.service
```

---

# 6. DATABASE DEBUGGING

---

## Open database

```bash
sqlite3 ~/.local/share/trackora/trackora.db
```

---

## View latest sessions

```sql
select id, app_name, start_time, end_time, duration_seconds
from app_sessions
order by id desc
limit 20;
```

---

## Detect impossible durations

```sql
select *
from app_sessions
where duration_seconds > 86400;
```

---

## Reset database safely

WARNING:
Deletes all tracking history.

```bash
rm ~/.local/share/trackora/trackora.db
```

Then restart service:

```bash
systemctl --user restart trackora.service
```

---

## Verify database recreated

```bash
ls ~/.local/share/trackora/
```

Expected:

```text
trackora.db
```

---

# 7. DASHBOARD/UI DEBUGGING

---

## Dashboard not updating

Usually caused by:

* extension stopped
* service stopped
* stale JSON updates

Check:

```bash
systemctl --user status trackora.service
```

and:

```bash
watch cat ~/.local/share/trackora/current_window.json
```

---

## Active session missing

Usually:

* tracker idle
* extension stopped
* stale session state

Restart:

```bash
systemctl --user restart trackora.service
```

---

## Charts look broken

Usually caused by:

* tiny window size
* responsive layout issues

Test fullscreen first before debugging layout.

---

# 8. COMMON FAILURE PATTERNS

---

## GNOME reset destroyed tracking

Symptoms:

* extension missing
* no active sessions
* dashboard frozen

Fix:

* re-enable extension
* restore metadata compatibility
* restart service

---

## Duplicate tracker instances

Symptoms:

* impossible daily totals
* 24h+ usage
* duplicate sessions

Fix:

* ensure singleton protection working
* verify only one service active

---

## metadata.json parse failure

Symptoms:

```text
Failed to parse metadata.json
```

Usually:

* missing comma
* broken JSON syntax

---

## Dashboard stale state

Symptoms:

* charts frozen
* app not updating

Usually:

* service dead
* JSON stopped updating

---

## Service disappeared after reset

Symptoms:

```text
Unit trackora.service not found
```

Fix:

* recopy service file
* daemon-reload
* enable service again

---

# 9. SAFE DEVELOPMENT WORKFLOW

---

## BEFORE major AI edits

Always:

```bash
git add .

git commit -m "stable checkpoint"
```

---

## NEVER do all at once

Avoid:

* backend rewrite
* UI redesign
* DB changes
* service changes

in one prompt.

---

## Stable development order

1. backend
2. tracking
3. service
4. database
5. UI polish

---

## When to restart GNOME shell

Only when:

* extension changes
* metadata changes
* extension stops loading

---

## When NOT to delete database

Do NOT delete DB for:

* UI bugs
* chart bugs
* extension bugs

Only delete DB for:

* corrupted data
* impossible analytics

---

# 10. USEFUL COMMANDS REFERENCE

---

## Service

```bash
systemctl --user status trackora.service
systemctl --user restart trackora.service
systemctl --user daemon-reload
systemctl --user enable --now trackora.service
journalctl --user -u trackora.service -f
```

---

## GNOME

```bash
gnome-shell --version
gnome-extensions list
gnome-extensions enable trackora@trackora.dev
killall -3 gnome-shell
```

---

## Database

```bash
sqlite3 ~/.local/share/trackora/trackora.db
```

---

## Tracker

```bash
python3 -m trackora
watch cat ~/.local/share/trackora/current_window.json
```

---

## Git Safety

```bash
git add .
git commit -m "checkpoint"
git checkout -b stable-build
```

---

## Final Advice

If Trackora suddenly appears broken:

DO NOT panic.

Usually the issue is:

* GNOME extension state
* missing service
* stale systemd config
* metadata compatibility

NOT total project corruption.

Always debug:

1. extension
2. service
3. JSON updates
4. tracker logs
5. database

in that order.


