// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Human-readable log line: [HH:MM:SS] Application - Window title
 */
import GLib from 'gi://GLib';

/**
 * @param {{ app: string; title: string }} snapshot
 * @returns {string}
 */
export function formatFocusLogLine(snapshot) {
    const dt = GLib.DateTime.new_now_local();
    const ts = dt.format('%H:%M:%S') ?? '--:--:--';
    const app = snapshot.app?.trim() || 'Unknown';
    const title = snapshot.title?.trim() ?? '';
    return `[${ts}] ${app} - ${title}`;
}
