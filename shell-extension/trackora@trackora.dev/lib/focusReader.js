// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Reads the currently focused Meta.Window from the global Shell/Mutter display.
 *
 * On Wayland, unfocused clients cannot enumerate other apps’ windows; inside the
 * Shell extension we run with the same privileges as gnome-shell and use the
 * same objects Shell uses for Alt+Tab and the top bar.
 */

/**
 * @typedef {{ app: string; title: string }} FocusSnapshot
 */

/**
 * @returns {FocusSnapshot}
 */
export function readFocusedSnapshot() {
    const display = global.display;
    // GJS exposes GObject properties with dashes as underscore names.
    const win =
        display.focus_window ?? display.get_focus_window?.() ?? null;

    if (!win)
        return {app: 'Unknown', title: ''};

    const title = win.get_title() ?? '';

    // Prefer WM_CLASS “instance” (first field of WM_CLASS), e.g. “firefox”.
    let app = win.get_wm_class_instance?.() ?? '';
    if (!app) {
        const wmClass = win.get_wm_class?.() ?? '';
        app = wmClass.split('\0')[0] ?? '';
    }

    // GTK4 apps sometimes expose a stable application id.
    const gtkAppId = win.get_gtk_application_id?.() ?? '';
    if (!app && gtkAppId)
        app = gtkAppId;

    return {
        app: app || 'Unknown',
        title,
    };
}
