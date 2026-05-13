// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * GLib timer that samples focused window metadata and prints to the Shell log.
 *
 * console.log / log from extensions is captured by gnome-shell’s logging and
 * shows up in the system journal (see INSTALL.md).
 */
import GLib from 'gi://GLib';

import {readFocusedSnapshot} from './focusReader.js';
import {formatFocusLogLine} from './logFormat.js';

export class FocusLogPoller {
    /**
     * @param {{ intervalSec: number }} opts
     */
    constructor(opts) {
        this._intervalSec = opts.intervalSec;
        /** @type {number|null} */
        this._sourceId = null;
    }

    start() {
        this.stop();
        // Immediate sample so you see output right after enable.
        this._tick();
        this._sourceId = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            this._intervalSec,
            () => {
                this._tick();
                return GLib.SOURCE_CONTINUE;
            }
        );
    }

    stop() {
        if (this._sourceId !== null) {
            GLib.source_remove(this._sourceId);
            this._sourceId = null;
        }
    }

    _tick() {
        const snap = readFocusedSnapshot();
        console.log(`[Trackora] ${formatFocusLogLine(snap)}`);
    }
}
