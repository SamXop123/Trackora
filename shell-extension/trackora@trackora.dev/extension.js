// SPDX-License-Identifier: GPL-2.0-or-later
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

import {readFocusedSnapshot} from './lib/focusReader.js';

const INTERVAL_SEC = 3;

function getStateDir() {
    return GLib.build_filenamev([GLib.get_user_data_dir(), 'trackora']);
}

function getStateFilePath() {
    return GLib.build_filenamev([getStateDir(), 'current_window.json']);
}

function ensureStateDir() {
    const dir = getStateDir();
    const result = GLib.mkdir_with_parents(dir, 0o700);

    if (result === 0) {
        console.log(`[Trackora] state directory ready: ${dir}`);
        return true;
    }

    console.log(`[Trackora] failed to create state directory: ${dir} (code=${result})`);
    return false;
}

function writeWindowState(snapshot) {
    if (!ensureStateDir())
        return;

    const timestamp =
        GLib.DateTime.new_now_local()?.format('%Y-%m-%dT%H:%M:%S') ?? '';

    const payload = {
        app: snapshot.app ?? 'Unknown',
        title: snapshot.title ?? '',
        timestamp,
    };

    const path = getStateFilePath();
    const file = Gio.File.new_for_path(path);
    const contents = JSON.stringify(payload, null, 2);

    try {
        const bytes = new TextEncoder().encode(contents);
        file.replace_contents(
            bytes,
            null,
            false,
            Gio.FileCreateFlags.REPLACE_DESTINATION,
            null
        );
        console.log(`[Trackora] wrote state file successfully: ${path}`);
    } catch (e) {
        console.log(`[Trackora] failed to write state file: ${path} :: ${e}`);
    }
}

export default class TrackoraExtension extends Extension {
    enable() {
        this._sourceId = null;

        const tick = () => {
            const snapshot = readFocusedSnapshot();
            writeWindowState(snapshot);
            return GLib.SOURCE_CONTINUE;
        };

        tick();
        this._sourceId = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            INTERVAL_SEC,
            tick
        );
    }

    disable() {
        if (this._sourceId !== null) {
            GLib.source_remove(this._sourceId);
            this._sourceId = null;
        }
    }
}
