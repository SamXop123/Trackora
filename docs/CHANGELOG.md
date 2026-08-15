# Changelog

All notable changes to the Trackora project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-08-15

This release introduces a major performance engine overhaul, non-blocking asynchronous icon loading, native Windows Per-Monitor High-DPI scaling, and refined Windows application tracking.

### Performance & Engine Overhaul
- **$O(N)$ Floating-Point Analytics Engine**:
  - Replaced nested ISO date string parsing with single-pass floating-point epoch math, speeding up 30-day and 90-day Reports queries from 5 seconds to **~3 ms** (over 900x faster).
  - Added SQLite database indexes on session timestamps and app names to stop full-table scans.
  - Added smart in-memory query caching with database modification checks for instantaneous range filter switching.
- **Asynchronous Icon Extraction (`QThreadPool`)**:
  - Moved Windows shell `.exe` icon extraction to background worker threads so Application cards render in **0 ms** with no UI thread freeze.
  - Indexed Windows Start Menu shortcuts in memory to eliminate repeated directory scans.
- **Instantaneous Tab Navigation**:
  - Made sidebar tab switches and navigation instantaneous with deferred data reloads.

### Display & Windows High-DPI Polish
- **Per-Monitor v2 High-DPI Awareness**:
  - Configured native Windows Per-Monitor High-DPI awareness (`DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2`) and pass-through scaling policy.
  - Enabled sub-pixel font anti-aliasing and full hinting, eliminating blurry or pixelated text on 16:10 / 1920x1200+ laptop displays.

### Windows Tracking & Exclusions
- **Refined Process Name Normalization**:
  - Improved executable matching for Windows background processes and Trackora Python GUI instances.
  - Pre-compiled exclusion tokens in memory to eliminate repeated filesystem kernel `stat()` calls in hot paths.

---

## [2.1.0] - 2026-08-02

This minor release brings Timeline pagination, high-performance icon caching, system tray fixes for Windows, desktop tracking enhancements across Linux & Windows, and general Quality of Life (QoL) improvements.

### Added & Improved
- **Timeline Pagination & UX Polish**:
  - Pagination controls for Timeline entries with optimized database queries.
  - Smooth timeline scrolling fixes and responsive layouts.
- **Icon Caching Engine**:
  - Dynamic application icon caching to reduce I/O overhead and instantly load application icons across dashboard pages.
- **Windows System Tray & Focus Fixes**:
  - Enhanced tray menu interactions and active window focus handling.
- **Desktop Tracking & Platform QoLs**:
  - Refined desktop tracking accuracy for Linux (GNOME Wayland) and Windows 10/11.

---

## [2.0.0] - 2026-07-28

This major release introduces full native support for Microsoft Windows (10/11), bringing Trackora's premium screen time and productivity tracking to Windows alongside Linux GNOME Wayland.

### Added (Windows Native Support)
- **Native Win32 Tracking Engine (`windows/tracker.py`)**:
  - Direct Win32 API window focus tracking using `GetForegroundWindow`, `GetWindowThreadProcessId`, and process executable path resolution.
  - Smart Windows Lock Screen & Sleep filtering (ignores `LockApp.exe` so lock screen / sleep mode is recorded as idle time).
- **Windows System Tray Integration (`trackora/gui/dashboard_window.py`)**:
  - System tray icon with custom dark-themed context menu ("Open Dashboard", "Quit Trackora") and hover tooltip.
  - Window close `(X)` minimizes silently to the system tray so background tracking continues uninterrupted.
  - Native `SetForegroundWindow` taskbar focus retention keeping the Windows tray overflow panel open while interacting with options.
- **Single-Instance Protection (`trackora-gui.lock`)**:
  - Advisory lock file preventing multiple GUI windows from opening simultaneously; automatically restores existing dashboard window if launched twice.
- **Auto-Track on Startup Toggle**:
  - Windows Registry autostart management (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) with customizable toggle in the Settings tab.
- **High-Resolution App Icon Extraction (`trackora/gui/utils.py`)**:
  - Fuzzy case-insensitive process path resolution and recursive UWP PNG asset extractor for Windows Store apps (WhatsApp, Photos, etc.).
- **Standalone Windows Installer Packaging**:
  - Automated compilation pipeline (`build-windows.ps1` and `build-installer.iss`) building a standalone, zero-dependency `TrackoraSetup.exe`.

---

## [1.0.1] - 2026-07-08

### Fixed
- Fixed a critical bug causing a GNOME login loop on Fedora Wayland. Corrected systemd user service dependencies by removing `Wants=graphical-session.target` and updating the install target to `WantedBy=graphical-session.target`.

---

## [1.0.0] - 2026-07-07

This release marks the first stable public launch of the Trackora suite, including the core background services, compositor extensions, and desktop visualization dashboard.

---

## [1.0.0-rc1] - 2026-06-29

Trackora is now ready for the v1.0.0 Release Candidate 1 (RC1) release. This release focuses on final release polish, robust Fedora RPM packaging, and standard installation pipelines.

### Packaging
- Native Fedora RPM package (`trackora-1.0.0-rc1.rpm`) for simple system-wide installation.
- Clean desktop launcher (`trackora.desktop`) registered in `/usr/share/applications/`.
- Full GNOME application menu integration with high-quality icons and system categorization.
- Standardized AppStream metadata (`trackora.metainfo.xml`) supporting software centers.
- Modern Python packaging with `pyproject.toml` and CLI entry points (`trackora-gui`, `trackora-daemon`).
- Improved system-wide asset management and resolution helpers.

### Installation
- Simplified installation via native Fedora software managers.
- Legacy installation script (`install.sh`) retained for manual or custom environment setups.
- RPM installation recommended as the primary distribution method.

### Improvements
- Packaging and dependencies fixes: PySide6 and PyQtGraph dependencies mapped to native Fedora packages.
- Desktop integration fixes: Wayland window class and name matched with `StartupWMClass` to display correctly in GNOME dock.
- Runtime dependency fixes: automated PySide6 extension activation and daemon service initialization.
- Resource path improvements: flexible asset resolution from system, local git repository, or wheel bundle.
- General stability and error handling improvements.

---

### Added
- **Core Tracking Engine**:
  - Headless tracking service daemon (`python3 -m trackora`) using a robust state machine to track window switches, heartbeats, and idle ticks.
  - Multi-instance prevention utilizing standard advisory kernel file locking (`fcntl.flock`).
  - Stale session recovery automatically repairing unclosed records on system startup.
- **GNOME Shell Extension**:
  - Compositor window manager integration querying active application class names and window titles securely on Wayland.
  - Asynchronous, atomic JSON state writes to avoid IPC read collisions.
- **SQLite Database Store**:
  - Standardized local database schema storing structured user sessions.
  - Filtered partial unique index ensuring a single active session in the database.
- **systemd Integration**:
  - Dedicated systemd user service configurations ensuring background tracking starts automatically on user login.
- **Desktop Dashboard (PySide6)**:
  - **Dashboard Page**: Today's time stats, top applications, and weekly activity bar graphs.
  - **Timeline Page**: Chronological list of user activity.
  - **Applications Page**: Ranked list of app focus durations, session totals, and percentages.
  - **Insights Page**: Switch tracking, context switches per hour, and focus analytics.
  - **Reports Page**: Custom calendar selector with SVG icons and historical range summaries.
  - **Settings & Diagnostics Page**: Real-time service status, database controls, data export tools, and path indicators.
- **Premium UI Components**:
  - Animated `_FilterBtn` and `_ActionCard` using linear color interpolation for state transitions.
  - Custom custom-painted `_Switch` button toggles replacing standard Qt checkboxes.
  - Graphics effects with transient page-fade animations inside the main stacked layout.

---

## [0.1.0] - Initial Development Sandbox

- Prototype implementation of SQLite database tracking.
- Draft GNOME Shell extension tracking `Meta.Window` focus.
- Draft PyQt interface displaying raw session logs.
