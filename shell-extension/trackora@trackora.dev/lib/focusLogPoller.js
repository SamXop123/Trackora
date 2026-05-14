// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Timer: sample Mutter focus every N seconds and write ``current_window.json``.
 *
 * The Python backend reads that file only; no Wayland probing from Python.
 */
import GLib from 'gi://GLib';

import {readFocusedSnapshot} from './focusReader.js';
import {writeWindowStateFile} from './windowStateWriter.js';

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
        writeWindowStateFile(snap);
    }
}
