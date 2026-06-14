# Contributing to Trackora

Thank you for your interest in contributing to Trackora! We welcome contributions from developers of all skill levels, whether you are fixing a small bug, improving the documentation, or proposing a major feature.

This guide outlines our contribution workflow, coding standards, and community guidelines to ensure a smooth, collaborative process.

---

## 1. Ground Rules & Code of Conduct

*   **Respectful Communication**: Please maintain a supportive and respectful tone in all issues, pull requests, and discussions.
*   **Privacy-First Mindset**: Trackora is built to protect user privacy. We will reject any feature requests or PRs that introduce remote tracking, telemetry, cloud requirements, or compromise the local-first nature of the tool.
*   **Quality over Speed**: We prefer clean, readable, typed, and well-tested code over rapid feature churn.

---

## 2. How to Contribute

### Reporting Bugs
If you find a bug, please check the [existing issues](https://github.com/SamXop123/Trackora/issues) first to see if it has already been reported. If not, open a new issue containing:
1.  **Clear Description**: A concise title and summary of the issue.
2.  **Reproduction Steps**: Step-by-step instructions to reproduce the behavior.
3.  **System Info**: GNOME Shell version (`gnome-shell --version`), Wayland/X11 status, and Python version.
4.  **Logs**: Relevant terminal output or journalctl logs (`journalctl --user -u trackora.service`).

### Suggesting Features
We love new ideas! To propose a feature:
1.  Open an issue or start a [GitHub Discussion](https://github.com/SamXop123/Trackora/discussions).
2.  Explain *why* the feature is useful and how it aligns with the local-first, friction-free philosophy of Trackora.
3.  Wait for maintainer feedback before starting to write code. This ensures your implementation details align with the project's roadmap.

### Submitting Pull Requests
1.  **Fork and Clone**: Fork the repository and clone it locally.
2.  **Create a Branch**: Create a feature branch off of `main` (e.g., `git checkout -b feat/my-new-feature` or `git checkout -b fix/issue-123`).
3.  **Follow the Development Guide**: Read [DEVELOPMENT.md](DEVELOPMENT.md) for detailed onboarding guidelines, architectural breakdown, and environment setup.
4.  **Commit Messages**: Keep commit messages concise and descriptive. We encourage the use of conventional prefixes (e.g., `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `chore:`).
5.  **Submit PR**: Open a pull request against our `main` branch. Provide a detailed summary of what was changed and why.

---

## 3. Code Quality & Formatting Checklist

To keep the codebase maintainable and type-safe, make sure your code adheres to these standards:
*   **Run type checks & lints**: Always import `from __future__ import annotations` in Python modules, and annotate parameter and return types.
*   **No dead code/unused imports**: Remove any imports that are no longer used.
*   **Style consistency**: Match the existing coding patterns (e.g., camelCase for JavaScript, snake_case for Python, and custom Qt drawing mechanisms for the frontend).
*   **No heavy stylesheets**: Do not use massive stylesheet overrides on PySide6 widgets; implement `paintEvent` transitions with `QVariantAnimation` for dynamic visual components.

---

## 4. Getting Help

If you have questions about the codebase or need help during implementation, feel free to:
*   Post in the discussions forum.
*   Ask directly inside your open draft Pull Request.
*   DM on discord: `dot_notsam`

