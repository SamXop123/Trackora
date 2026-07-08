# Changelog

All notable changes to the Trackora project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [1.0.1] - 2026-07-08

### Fixed
- Fixed a critical bug causing a GNOME login loop on Fedora Wayland. Corrected systemd user service dependencies by removing `Wants=graphical-session.target` and updating the install target to `WantedBy=graphical-session.target`.

---

## [1.0.0] - 2026-07-08

This release marks the first stable public launch of the Trackora suite, including the core background services, compositor extensions, and desktop visualization dashboard.

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
