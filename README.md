<div align="center">

<br />

<img src="https://raw.githubusercontent.com/SamXop123/Trackora/main/assets/trackora-logo.svg" alt="Trackora" width="80" />

<br />

# Trackora

### Beautiful screen time & activity tracking for Linux.

*You work hard. Do you know where the time actually goes?*

<br />

[![License: MIT](https://img.shields.io/badge/License-MIT-5c6bc0.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux-informational?style=flat-square&color=5c6bc0)](https://github.com/SamXop123/Trackora)
[![GNOME](https://img.shields.io/badge/GNOME-Extension-informational?style=flat-square&color=4db6ac)](https://extensions.gnome.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square&color=66bb6a)](DEVELOPMENT.md)
[![Stars](https://img.shields.io/github/stars/SamXop123/Trackora?style=flat-square&color=ffa726)](https://github.com/SamXop123/Trackora/stargazers)

<br />

[**Get Started**](#installation) · [**Features**](#features) · [**Screenshots**](#screenshots) · [**Roadmap**](#roadmap) · [**Contribute**](#contributing)

<br />

---

</div>

<br />

## The problem nobody talks about

You open your laptop at 9am with a clear plan.

By noon, you're not sure what happened.

You *feel* like you coded, answered emails, did research. But the day has this strange quality of slipping away — sessions blur together, "quick breaks" expand silently, and the question *"what did I actually do today?"* has no clean answer.

This isn't a discipline problem. It's a **visibility problem.**

Most productivity tools make you do work to track your work. They want timers, check-ins, rituals, and habits you have to build. They assume you'll remember to start and stop things. You won't. Nobody does.

**Trackora takes a different approach.**

Install it. Use your computer exactly as you always have. Trackora watches quietly in the background and builds a precise, beautiful picture of your day — every app, every session, every pattern — without you doing anything at all.

Then, whenever you're curious: *open it, and know.*

<br />

---

<br />

## Features

<br />

**`📊` Dashboard** &nbsp;—&nbsp; *Your day at a glance*

The moment you open Trackora, you see today. Not a list of raw data — a composed, readable overview of where your time went. Current app, total screen time, live timeline, weekly rhythm, and your top applications, all in one view.

<br />

**`🕒` Timeline** &nbsp;—&nbsp; *Every session, in order*

Scroll back through your day chronologically. See exactly when you opened what, how long you stayed, and when you switched. Group by application to see fragmented usage consolidated. Navigate hours of data instantly.

<br />

**`📱` Applications** &nbsp;—&nbsp; *The honest usage rankings*

A ranked view of every application you used, sorted by time. See usage duration, session counts, and active time per app. No estimates — exact numbers, pulled straight from your activity history.

<br />

**`💡` Insights** &nbsp;—&nbsp; *Patterns you wouldn't have noticed*

When do you do your best work? Which apps fragment your focus? How often do you switch contexts in an hour? Trackora surfaces the patterns buried in your daily data — peak activity hours, focus metrics, app-switching analytics, and category breakdowns.

<br />

**`📈` Reports** &nbsp;—&nbsp; *Any period, any time*

Zoom out. Compare today to yesterday. Review the last 7 or 30 days. Define a custom date range. Export your data whenever you want. It's your time — you should be able to look at all of it.

<br />

**`⚙️` Settings & Diagnostics** &nbsp;—&nbsp; *Full transparency into the tracker itself*

See tracking status, extension health, database info, and backup tools. Manage or delete your data at any time. Trackora never hides what it's doing.

<br />

---

<br />

## Screenshots

<br />

> 📸 &nbsp;Screenshots arriving with v1.0 — [watch the repo](https://github.com/SamXop123/Trackora/subscription) to be notified.

<br />

| Dashboard | Timeline |
|:---------:|:--------:|
| *Today's full picture, always up to date* | *Your day, session by session* |

<br />

| Insights | Reports |
|:--------:|:-------:|
| *Patterns in your focus and habits* | *Historical analysis, any range* |

<br />

---

<br />

## How it works

Trackora is three components working together. You only ever interact with one of them.

```
┌─────────────────────────────────┐
│        GNOME Extension          │  ← Watches active windows silently
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│    Background Tracking Service  │  ← Runs independently, always on
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│         SQLite Database         │  ← Stored locally on your machine
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       Trackora Dashboard        │  ← Open when you want to know
└─────────────────────────────────┘
```

The tracking service runs **independently** of the dashboard. Close the Trackora window, shut down the dashboard, go about your day — your activity is still being recorded. When you open Trackora again, your full history is waiting for you.

<br />

---

<br />

## Installation

<br />

### Fedora *(coming with v1.0)*

```bash
# Package installation instructions arriving with the v1.0 release.
# Watch this repository to be notified.
```

<br />

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/SamXop123/Trackora.git

# Enter the project directory
cd Trackora

# Run Trackora
python3 -m trackora
```

> **Requirements:** Python 3.8+, GNOME desktop, SQLite (bundled with Python)

<br />

---

<br />

## Privacy

Trackora is **local-first by design.** Your activity data belongs to you — it never leaves your machine.

Trackora does **not**:

- ☁️ Upload your data anywhere
- 🔐 Require an account or login
- 💳 Require a subscription
- 📡 Send telemetry or analytics to external servers

Everything is stored in a local SQLite database on your own filesystem. You can inspect it, export it, back it up, or delete it at any time from within the app.

<br />

---

<br />

## Roadmap

<br />

**v1.0** &nbsp;`in progress`
- [x] Dashboard
- [x] Timeline
- [x] Applications
- [x] Insights
- [x] Reports
- [x] Settings & Diagnostics

<br />

**v1.1** &nbsp;`planned`
- [ ] Goals & daily targets
- [ ] Productivity scoring
- [ ] Extended analytics
- [ ] Additional export formats

<br />

---

<br />

## Contributing

Trackora is actively developed and welcomes contributions of all kinds.

- 🐛 **Found a bug?** [Open an issue](https://github.com/SamXop123/Trackora/issues)
- 💡 **Have an idea?** [Start a discussion](https://github.com/SamXop123/Trackora/discussions)
- 🔧 **Want to build?** Read [DEVELOPMENT.md](DEVELOPMENT.md) for architecture, setup, and contributor docs, then open a pull request

If Trackora helped you understand your time a little better, **a star means a lot.** It helps other Linux users find the project.

<br />

---

<br />

<div align="center">

Built for Linux users who want to understand their time.

<br />

*Stop guessing. Start knowing.*

</div>