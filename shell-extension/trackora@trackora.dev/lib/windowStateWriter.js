// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Persist focused-window state for the Python backend.
 *
 * Writes ``$XDG_DATA_HOME/trackora/current_window.json`` (normally
 * ``~/.local/share/trackora/current_window.json``).
 *
 * Uses ``GLib.mkdir_with_parents`` then ``GLib.file_set_contents_full`` with
 * ``CONSISTENT`` so the file is replaced atomically where the platform allows.
 *
 * Important: do not gate on ``mkdir_with_parents``’s return value in GJS — the
 * introspected binding may not expose a reliable boolean, which would skip all
 * writes if treated as strict ``false``.
 */
import GLib from 'gi://GLib';

/**
 * @returns {string} Absolute path to ``current_window.json``.
 */
export function getTrackoraStatePath() {
    const dataDir = GLib.get_user_data_dir();
    return GLib.build_filenamev([dataDir, 'trackora', 'current_window.json']);
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
    const dataDir = GLib.get_user_data_dir();
    const dir = GLib.build_filenamev([dataDir, 'trackora']);
    const path = getTrackoraStatePath();

    try {
        GLib.mkdir_with_parents(dir, 0o700);
    } catch (e) {
        console.warn(`[Trackora] mkdir_with_parents failed: ${dir}: ${e}`);
        return;
    }

    if (!GLib.file_test(dir, GLib.FileTest.IS_DIR)) {
        console.warn(`[Trackora] trackora data directory missing after mkdir: ${dir}`);
        return;
    }

    const dt = GLib.DateTime.new_now_local();
    const ts = dt.format('%Y-%m-%dT%H:%M:%S') ?? '';

    const payload = {
        app: formatAppForJson(snapshot.app),
        title: snapshot.title ?? '',
        timestamp: ts,
    };

    const json = JSON.stringify(payload);

    try {
        GLib.file_set_contents_full(
            path,
            json,
            -1,
            GLib.FileSetContentsFlags.CONSISTENT,
            0o600,
            null
        );
        console.log(
            `[Trackora] wrote current_window.json (${payload.app}) -> ${path}`
        );
    } catch (e) {
        console.warn(`[Trackora] file_set_contents_full failed: ${path}: ${e}`);
    }
}
