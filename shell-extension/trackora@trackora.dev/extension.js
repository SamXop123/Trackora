import GLib from 'gi://GLib';
import Gio from 'gi://Gio';

let timeout = null;

function writeWindowState() {
    try {
        const window = global.display.get_focus_window();

        if (!window) {
            console.log('[Trackora] No focused window');
            return true;
        }

        const app = window.get_wm_class() || 'Unknown';
        const title = window.get_title() || '';

        console.log(`[Trackora] Detected: ${app} - ${title}`);

        const data = {
            app: app,
            title: title,
            timestamp: new Date().toISOString()
        };

        const dirPath = GLib.build_filenamev([
            GLib.get_home_dir(),
            '.local',
            'share',
            'trackora'
        ]);

        console.log(`[Trackora] Directory path: ${dirPath}`);

        GLib.mkdir_with_parents(dirPath, 0o755);

        const filePath = GLib.build_filenamev([
            dirPath,
            'current_window.json'
        ]);

        console.log(`[Trackora] File path: ${filePath}`);

        const file = Gio.File.new_for_path(filePath);

        const json = JSON.stringify(data, null, 2);

        const encoder = new TextEncoder();
        const contents = encoder.encode(json);

        file.replace_contents(
            contents,
            null,
            false,
            Gio.FileCreateFlags.REPLACE_DESTINATION,
            null
        );

        console.log('[Trackora] JSON file written successfully');

    } catch (e) {
        console.log(`[Trackora] WRITE ERROR: ${e.message}`);
        console.log(`${e.stack}`);
    }

    return true;
}

export default class TrackoraExtension {
    enable() {
        console.log('[Trackora] Extension enabled');

        writeWindowState();

        timeout = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            3,
            writeWindowState
        );
    }

    disable() {
        console.log('[Trackora] Extension disabled');

        if (timeout) {
            GLib.source_remove(timeout);
            timeout = null;
        }
    }
}