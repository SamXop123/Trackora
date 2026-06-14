# Changelog

All notable changes to the Trackora project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - Upcoming / In Progress

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
