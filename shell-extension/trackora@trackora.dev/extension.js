// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Trackora GNOME Shell extension entry.
 *
 * Shell runs this code in-process with Mutter, so we read Meta.Display’s
 * focused window and write ``current_window.json`` under the user data directory
 * for the Python backend. Normal desktop apps cannot do this on Wayland.
 */
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

import {FocusLogPoller} from './lib/focusLogPoller.js';

const INTERVAL_SEC = 3;

export default class TrackoraExtension extends Extension {
    enable() {
        this._poller = new FocusLogPoller({intervalSec: INTERVAL_SEC});
        this._poller.start();
    }

    disable() {
        this._poller?.stop();
        this._poller = null;
    }
}
