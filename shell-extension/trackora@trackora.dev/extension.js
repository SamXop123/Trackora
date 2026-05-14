// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Trackora GNOME Shell extension entry.
 *
 * Runs in-process with Mutter: reads the focused ``Meta.Window``, then writes
 * ``$XDG_DATA_HOME/trackora/current_window.json`` using GLib/Gio only (no Node
 * ``fs`` / ``Buffer`` APIs).
 */
import ByteArray from 'gi://ByteArray';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

import {readFocusedSnapshot} from './lib/focusReader.js';

const INTERVAL_SEC = 3;

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
 * @returns {string} ``~/.local/share/trackora`` when ``XDG_DATA_HOME`` is unset.
 */
function getTrackoraDir() {
    return GLib.build_filenamev([GLib.get_user_data_dir(), 'trackora']);
}

/**
 * @returns {string} Full path to ``current_window.json``.
 */
function getTrackoraJsonPath() {
    return GLib.build_filenamev([GLib.get_user_data_dir(), 'trackora', 'current_window.json']);
}

/**
 * Create ``trackora`` under the user data dir and write JSON via ``replace_contents``.
 */
function writeCurrentWindowJson() {
    const dir = getTrackoraDir();
    const path = getTrackoraJsonPath();

    try {
        GLib.mkdir_with_parents(dir, 0o700);
    } catch (e) {
        console.warn(`[Trackora] mkdir_with_parents failed (${dir}): ${e}`);
        return;
    }

    if (!GLib.file_test(dir, GLib.FileTest.IS_DIR)) {
        console.warn(`[Trackora] directory missing after mkdir: ${dir}`);
        return;
    }

    const snap = readFocusedSnapshot();
    const dt = GLib.DateTime.new_now_local();
    const ts = dt.format('%Y-%m-%dT%H:%M:%S') ?? '';

    const payload = {
        app: formatAppForJson(snap.app),
        title: snap.title ?? '',
        timestamp: ts,
    };
    const json = JSON.stringify(payload);

    const file = Gio.File.new_for_path(path);

    try {
        // GByteArray-backed buffer — correct type for replace_contents in GJS.
        const contents = ByteArray.fromString(json);
        file.replace_contents(
            contents,
            null,
            false,
            Gio.FileCreateFlags.REPLACE_DESTINATION,
            null
        );
        console.log(
            `[Trackora] OK replace_contents ${path} (${payload.app}, ${payload.title.length} title chars)`
        );
    } catch (e) {
        console.warn(`[Trackora] replace_contents failed (${path}): ${e}`);
    }
}

export default class TrackoraExtension extends Extension {
    enable() {
        this._timeoutId = null;
        writeCurrentWindowJson();
        this._timeoutId = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            INTERVAL_SEC,
            () => {
                writeCurrentWindowJson();
                return GLib.SOURCE_CONTINUE;
            }
        );
    }

    disable() {
        if (this._timeoutId !== null) {
            GLib.source_remove(this._timeoutId);
            this._timeoutId = null;
        }
    }
}
