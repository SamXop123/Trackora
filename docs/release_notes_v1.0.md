# Trackora v1.0.0 Stable Release Notes
### The Privacy-First Attention Observer for Linux GNOME Wayland

Trackora v1.0.0 marks the first stable production release of the local-first activity and screen time tracker. Engineered natively for modern Linux desktops, Trackora bridges the visibility gap between hours worked and attention spent. 

By utilizing low-level GNOME Shell compositor hooks, Trackora operates entirely offline with zero cloud telemetry, giving professionals, developers, and creators absolute ownership over their session data.

---

## 🏛️ Comprehensive Architecture & Subsystem Deep-Dive

Trackora is architected as an asynchronous, decoupled multi-layered system designed to minimize CPU overhead while ensuring thread-safe data persistence.

```
                  [ GNOME Shell / Mutter Compositor ]
                                  │
                                  ▼ (Query Focus Window Metadata)
                   [ GNOME Shell Extension ]
                                  │
                                  ▼ (Atomic GLib Writes: REPLACE_DESTINATION)
                    [ transient_state.json ]
                                  │
                                  ▼ (File Watcher Polling)
                 [ Background Tracking Engine (Daemon) ]
                                  │
                                  ▼ (SQL Transactions: Write-Ahead Logging)
                        [ SQLite Database ]
                                  │
                                  ▼ (SQL Queries on Demand)
                    [ PySide6 Desktop GUI Dashboard ]
```

### 1. The GNOME Shell Extension Observer
Traditional Wayland security models isolate standard user-space processes from accessing window manager variables, rendering traditional screen-trackers obsolete or forcing them to run under legacy XWayland compatibility layers. 
*   **Compositor Integration**: Trackora’s GNOME Shell extension runs directly in-process with the Mutter display compositor. 
*   **API Hooks**: It utilizes `global.display.get_focus_window()` to query the active `MetaWindow` object every 3 seconds.
*   **Metadata Extraction**: Extracts the focused window's application identifier (`wm_class`), document path, or browser tab title.
*   **Non-Blocking IPC**: To prevent compositor frame drops, the extension writes state data asynchronously to a local configuration directory using GLib atomic write flags (`g_file_replace_contents` with `REPLACE_DESTINATION`), bypassing file locks and context switches.

### 2. The Background Tracking Engine (Daemon)
The Python tracking daemon runs as a sandboxed systemd user service (`trackora.service`), separating data tracking from the main graphical dashboard.
*   **Session Aggregation**: Listens to changes in the active window configuration, merging contiguous chunks of focus time on the same application.
*   **AFK & Idle Filter**: Integrates idle observers. If no mouse movement or keyboard event is detected within a configurable threshold (default: 5 minutes), the daemon pauses the current session timer, retroactively deducting the idle period to ensure metrics reflect actual focus.
*   **Resource Throttling**: Operates near-zero footprint, consuming less than 15MB of RAM and <0.5% CPU under continuous load.

### 3. SQLite Storage Engine
Data is stored locally in `~/.local/share/trackora/history.db`.
*   **Write-Ahead Logging (WAL)**: Enabled to allow concurrent read queries from the PySide6 client GUI while the daemon writes session frames.
*   **Index Optimization**: Applies custom relational indices (`idx_app_sessions_time`) across timestamps, optimizing data retrieval speeds to under 5ms even for databases spanning multiple years.
*   **Database recovery**: Automatic startup routines verify database integrity. If a sudden power loss occurs, stale open sessions (sessions where `end_time` is null) are closed gracefully at the last verified heartbeat timestamp, preventing telemetry drift.

### 4. PySide6 Analytics Client
A desktop dashboard built with custom HSL dark-themed Qt widgets.
*   **Timeline View**: A chronological timeline mapping exactly how your day unfolded—aggregating switches, showcasing focus cycles, and filtering short anomalies.
*   **Insights Engine**: Algorithms process raw SQL intervals to determine productivity metrics, context switching rates, and peak focus windows.
*   **Diagnostics Portal**: Full configuration access showing service daemon health, database connection handles, and log files.

---

## 🚀 New & Refined in the v1.0.0 Stable Release

Compared to the initial Release Candidates (RCs), v1.0.0 introduces structural optimizations:

*   **Atomic Write Resilience**: Resolved edge-case file corruption bugs occurring during sudden system shutdowns by introducing double-buffered JSON atomic swaps.
*   **Mutter API Version Compatibility**: Added full metadata support for GNOME Shell 45 through GNOME Shell 47.
*   **Enhanced Idle Calculations**: AFK calculations now account for video playback states (e.g., if a browser tab is active and full-screen media is playing, the idle timer remains active).
*   **Stable RPM Packaging**: A completely overhauled spec file integrating automated package linting (`desktop-file-validate` and `appstream-util validation`).

---

## 🔒 Security Audit & Privacy Guarantees

Trackora was designed with the core belief that your workspace metadata is private.
*   **No Network Permissions**: The `AndroidManifest` equivalent (systemd service definitions and package configurations) does not declare internet sockets.
*   **No Cloud Integrations**: We do not offer or support cloud storage, third-party auth, or off-site synchronization.
*   **Plain SQL Databases**: Your data belongs to you. It is stored in a clean SQLite schema that can be copied, inspected, or deleted using standard databases clients (e.g., `sqlite3`).

---

## 📦 Detailed Installation Guide

### Fedora Linux (DNF Native RPM)
The pre-built RPM contains systemd units, GNOME desktop wrappers, icons, and local-path python configurations.
```bash
# 1. Download the native RPM
wget https://github.com/SamXop123/Trackora/releases/download/v1.0.0/trackora-v1.rpm

# 2. Install using DNF package manager
sudo dnf install ./trackora-v1.rpm

# 3. Reload GNOME Shell (or log out and back in) to activate the shell extension
```

### Build & Install From Source
To compile and package manually for other distributions:
```bash
# 1. Clone repo
git clone https://github.com/SamXop123/Trackora.git
cd Trackora

# 2. Grant execution permissions
chmod +x install.sh

# 3. Run install script (creates systemd user configurations and installs python packages)
./install.sh
```

---

## ⚙️ Service Command Reference

Manage the background daemon manually via standard systemd controls:

```bash
# Check daemon status
systemctl --user status trackora

# Start/Stop service
systemctl --user start trackora
systemctl --user stop trackora

# View background logs
journalctl --user -u trackora -n 50 -f
```

---

## 🗺️ Roadmap to v2.0
Work has officially begun on the next major iteration:
*   **Native Windows Support**: Porting the core background tracking engine to Windows, utilizing Win32 hook threads to capture application parameters while maintaining strict local database privacy guarantees.
