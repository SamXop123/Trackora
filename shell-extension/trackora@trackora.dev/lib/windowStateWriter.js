// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Persist focused-window state for the Python backend.
 *
 * Writes ``$XDG_DATA_HOME/trackora/current_window.json`` (normally
 * ``~/.local/share/trackora/current_window.json``). Atomic replace via Gio.
 */
import GLib from 'gi://GLib';
import Gio from 'gi://Gio';

/**
 * @returns {string}
 */
export function getTrackoraStatePath() {
    return GLib.build_filenamev([GLib.get_user_data_dir(), 'trackora', 'current_window.json']);
}

/**
 * @param {string} raw
 * @returns {string}
 */
function formatAppForJson(raw) {
    const s = (raw ?? '').trim();
    if (!s || s === 'Unknown')
        return 'Unknown';
    return s
        .split(/[\s_-]+/)
        .filter(Boolean)
        .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
        .join(' ');
}

/**
 * @param {{ app: string; title: string }} snapshot
 */
export function writeWindowStateFile(snapshot) {
    const dir = GLib.build_filenamev([GLib.get_user_data_dir(), 'trackora']);
    if (!GLib.mkdir_with_parents(dir, 0o700)) {
        console.warn(`[Trackora] mkdir_with_parents failed: ${dir}`);
        return;
    }

    const dt = GLib.DateTime.new_now_local();
    const ts = dt.format('%Y-%m-%dT%H:%M:%S') ?? '';

    const payload = {
        app: formatAppForJson(snapshot.app),
        title: snapshot.title ?? '',
        timestamp: ts,
    };

    const path = getTrackoraStatePath();
    const file = Gio.File.new_for_path(path);
    const json = JSON.stringify(payload);

    try {
        const bytes = new TextEncoder().encode(json);
        file.replace_contents(
            bytes,
            null,
            false,
            Gio.FileCreateFlags.REPLACE_DESTINATION,
            null
        );
    } catch (e) {
        console.warn(`[Trackora] write ${path} failed: ${e}`);
    }
}
