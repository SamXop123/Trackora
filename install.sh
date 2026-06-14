#!/usr/bin/env bash

# ==============================================================================
# Trackora Production-Release Installation Script
# ==============================================================================
# Installs Python dependencies, copies application files to user site-packages,
# registers the systemd service, and sets up the GNOME Shell Extension.
#
# Safe, transactional, idempotent, and position-independent.
# ==============================================================================

# ANSI color codes for formatted terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${BLUE}${BOLD}                    Trackora installation & setup                     ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}"

# Exit immediately if a pipeline or command fails
set -o pipefail

# 1. Determine script directory (for absolute paths)
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "[INFO] Running from source directory: ${SRC_DIR}"

# Define target locations
USER_SITE=$(python3 -m site --user-site)
TARGET_PKG_DIR="${USER_SITE}/trackora"
EXT_UUID="trackora@trackora.dev"
TARGET_EXT_DIR="${HOME}/.local/share/gnome-shell/extensions/${EXT_UUID}"
TARGET_SERVICE_FILE="${HOME}/.config/systemd/user/trackora.service"
DATA_DIR="${HOME}/.local/share/trackora"

# ------------------------------------------------------------------------------
# Phase 1: Pre-installation validations
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Phase 1/4] Running Pre-installation Checks ---${NC}"

# A. Verify operating system is Fedora Linux
if [ -f /etc/fedora-release ]; then
    FEDORA_VER=$(cat /etc/fedora-release)
    echo -e "[PASS] Operating System: ${FEDORA_VER}"
else
    echo -e "${RED}[FAIL] Error: Trackora is currently only packaged and optimized for Fedora Linux.${NC}"
    exit 1
fi

# B. Verify GNOME Shell is installed
if command -v gnome-shell &> /dev/null; then
    GNOME_VER=$(gnome-shell --version)
    echo -e "[PASS] Desktop Environment: ${GNOME_VER}"
else
    echo -e "${RED}[FAIL] Error: GNOME Shell not found. Trackora requires the GNOME desktop environment.${NC}"
    exit 1
fi

# C. Verify Python version is 3.8+
if command -v python3 &> /dev/null; then
    python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"
    if [ $? -eq 0 ]; then
        PYTHON_VER=$(python3 --version)
        echo -e "[PASS] Python Version: ${PYTHON_VER}"
    else
        echo -e "${RED}[FAIL] Error: Python 3.8 or higher is required.${NC}"
        exit 1
    fi
else
    echo -e "${RED}[FAIL] Error: Python 3 is not installed.${NC}"
    exit 1
fi

# D. Validate GNOME Extension source files and metadata
EXT_SRC_DIR="${SRC_DIR}/shell-extension/${EXT_UUID}"
if [ ! -d "$EXT_SRC_DIR" ]; then
    echo -e "${RED}[FAIL] Error: Source extension directory not found at: ${EXT_SRC_DIR}${NC}"
    exit 1
fi

if [ ! -f "${EXT_SRC_DIR}/extension.js" ]; then
    echo -e "${RED}[FAIL] Error: extension.js missing from source folder.${NC}"
    exit 1
fi

if [ ! -f "${EXT_SRC_DIR}/metadata.json" ]; then
    echo -e "${RED}[FAIL] Error: metadata.json missing from source folder.${NC}"
    exit 1
fi

# Validate metadata.json syntax and contents using python
python3 -c "
import json, sys
try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = json.load(f)
    if data.get('uuid') != sys.argv[2]:
        print(f'UUID mismatch in metadata.json. Expected: {sys.argv[2]}, Got: ' + str(data.get('uuid')))
        sys.exit(2)
except json.JSONDecodeError as e:
    print(f'JSON parsing error in metadata.json: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Error validating metadata.json: {e}')
    sys.exit(3)
" "${EXT_SRC_DIR}/metadata.json" "$EXT_UUID"

VALIDATE_STATUS=$?
if [ $VALIDATE_STATUS -eq 0 ]; then
    echo -e "[PASS] GNOME Extension Metadata Verified."
elif [ $VALIDATE_STATUS -eq 2 ]; then
    echo -e "${RED}[FAIL] Error: GNOME Extension UUID mismatch.${NC}"
    exit 1
else
    echo -e "${RED}[FAIL] Error: Invalid GNOME Extension metadata.json syntax.${NC}"
    exit 1
fi

# E. Verify required source entrypoint files exist in repository
REQUIRED_SOURCE_FILES=(
    "trackora/gui/app.py"
    "trackora/cli.py"
    "trackora/database/sqlite.py"
    "trackora/tracker/session_tracker.py"
    "trackora/services/tracking_service.py"
    "systemd/trackora.service"
)

for file in "${REQUIRED_SOURCE_FILES[@]}"; do
    if [ ! -f "${SRC_DIR}/${file}" ]; then
        echo -e "${RED}[FAIL] Error: Required source file missing: ${SRC_DIR}/${file}${NC}"
        exit 1
    fi
done
echo -e "[PASS] Codebase entrypoint files validated."

# ------------------------------------------------------------------------------
# Phase 2: Upgrade Detection
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Phase 2/4] Detecting Existing Installations ---${NC}"
UPGRADE_MODE=false

if [ -d "$TARGET_PKG_DIR" ] || [ -d "$TARGET_EXT_DIR" ] || [ -f "$TARGET_SERVICE_FILE" ]; then
    UPGRADE_MODE=true
    echo -e "${YELLOW}[INFO] Existing Trackora installation detected. Upgrading existing system...${NC}"
else
    echo -e "${GREEN}[INFO] No prior installation detected. Performing fresh install.${NC}"
fi

# ------------------------------------------------------------------------------
# Phase 3: Transactional Copy & Safeties (Rollback support)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Phase 3/4] Performing Transactional File Installation ---${NC}"

# Install Python requirements
echo -e "[INFO] Checking Python dependencies..."
python3 -m pip install --user -r "${SRC_DIR}/requirements.txt"
if [ $? -ne 0 ]; then
    echo -e "${RED}[FAIL] Error: Failed to install Python dependencies. Aborting.${NC}"
    exit 1
fi

# Create a temporary directory for backups of active modules in case copy fails
BACKUP_DIR="/tmp/trackora_backup_$$"
mkdir -p "$BACKUP_DIR"

rollback() {
    echo -e "\n${RED}[CRITICAL] Installation failed! Rolling back changes...${NC}"
    if [ -d "${BACKUP_DIR}/trackora_pkg" ]; then
        echo -e "Restoring Python package..."
        rm -rf "$TARGET_PKG_DIR"
        mv "${BACKUP_DIR}/trackora_pkg" "$TARGET_PKG_DIR"
    elif [ "$UPGRADE_MODE" = false ] && [ -d "$TARGET_PKG_DIR" ]; then
        rm -rf "$TARGET_PKG_DIR"
    fi

    if [ -d "${BACKUP_DIR}/trackora_ext" ]; then
        echo -e "Restoring GNOME extension..."
        rm -rf "$TARGET_EXT_DIR"
        mv "${BACKUP_DIR}/trackora_ext" "$TARGET_EXT_DIR"
    elif [ "$UPGRADE_MODE" = false ] && [ -d "$TARGET_EXT_DIR" ]; then
        rm -rf "$TARGET_EXT_DIR"
    fi

    if [ -f "${BACKUP_DIR}/trackora_service" ]; then
        echo -e "Restoring systemd unit..."
        mv "${BACKUP_DIR}/trackora_service" "$TARGET_SERVICE_FILE"
    elif [ "$UPGRADE_MODE" = false ] && [ -f "$TARGET_SERVICE_FILE" ]; then
        rm -f "$TARGET_SERVICE_FILE"
    fi

    rm -rf "$BACKUP_DIR"
    systemctl --user daemon-reload
    echo -e "${GREEN}Rollback complete. System state restored.${NC}"
    exit 1
}

# Trap unexpected exits during installation to trigger rollback
trap rollback ERR INT TERM

# 1. Back up existing package files if upgrading
if [ -d "$TARGET_PKG_DIR" ]; then
    mv "$TARGET_PKG_DIR" "${BACKUP_DIR}/trackora_pkg"
fi
echo -e "[INFO] Copying Python core module to: ${TARGET_PKG_DIR}"
mkdir -p "$USER_SITE"
cp -r "${SRC_DIR}/trackora" "$TARGET_PKG_DIR"
if [ $? -ne 0 ]; then
    rollback
fi

# 2. Back up existing extension files if upgrading
if [ -d "$TARGET_EXT_DIR" ]; then
    mv "$TARGET_EXT_DIR" "${BACKUP_DIR}/trackora_ext"
fi
echo -e "[INFO] Copying GNOME extension to: ${TARGET_EXT_DIR}"
mkdir -p "${HOME}/.local/share/gnome-shell/extensions"
cp -r "$EXT_SRC_DIR" "$TARGET_EXT_DIR"
if [ $? -ne 0 ]; then
    rollback
fi

# 3. Back up systemd unit file if upgrading
if [ -f "$TARGET_SERVICE_FILE" ]; then
    mv "$TARGET_SERVICE_FILE" "${BACKUP_DIR}/trackora_service"
fi
echo -e "[INFO] Copying systemd user service unit to: ${TARGET_SERVICE_FILE}"
mkdir -p "${HOME}/.config/systemd/user"
cp "${SRC_DIR}/systemd/trackora.service" "$TARGET_SERVICE_FILE"
if [ $? -ne 0 ]; then
    rollback
fi

# Remove temporary backup files upon successful copies
rm -rf "$BACKUP_DIR"
trap - ERR INT TERM # Clear rollback trap
echo -e "${GREEN}✔ Files installed successfully.${NC}"

# ------------------------------------------------------------------------------
# Phase 4: Initialization & Registration
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}--- [Phase 4/4] Registering Services & Initializing Data ---${NC}"

# Create data directory safely
mkdir -p "$DATA_DIR"

# Initialize local SQLite database if it doesn't exist (Preserves existing data!)
if [ ! -f "${DATA_DIR}/trackora.db" ]; then
    echo -e "[INFO] Initializing new SQLite tracking database..."
    python3 -c "
    import sys
    sys.path.insert(0, '${USER_SITE}')
    from trackora.database.sqlite import SQLiteSessionStore
    from trackora.utils.paths import default_database_path
    store = SQLiteSessionStore(default_database_path())
    store.initialize()
    store.close()
    "
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✔ Database initialized successfully at ${DATA_DIR}/trackora.db.${NC}"
    else
        echo -e "${RED}[FAIL] Error: Database initialization failed.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}[INFO] Existing database detected. Preserving data history.${NC}"
fi

# Reload systemd user daemon so it registers the service
echo -e "[INFO] Reloading systemd user config..."
systemctl --user daemon-reload

# 1. Automatically enable the GNOME Shell extension
echo -e "[INFO] Enabling GNOME Shell extension..."
if command -v gnome-extensions &> /dev/null; then
    gnome-extensions enable "$EXT_UUID"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✔ GNOME extension enabled.${NC}"
    else
        echo -e "${YELLOW}[WARN] Could not enable extension via CLI. You may need to enable it manually or restart GNOME.${NC}"
    fi
else
    echo -e "${YELLOW}[WARN] gnome-extensions CLI tool not found. You may need to enable it manually.${NC}"
fi

# 2. Automatically start the Trackora systemd user service once during installation
echo -e "[INFO] Starting Trackora background service..."
systemctl --user start trackora.service
if [ $? -eq 0 ]; then
    # Health check
    echo -e "[INFO] Running service health check..."
    sleep 1.5
    if systemctl --user is-active --quiet trackora.service; then
        echo -e "${GREEN}✔ Trackora tracking service is running and healthy.${NC}"
    else
        echo -e "${RED}[FAIL] Error: Trackora tracking service is registered but failed to remain active.${NC}"
        echo -e "${RED}Recent Service Logs:${NC}"
        journalctl --user -u trackora.service -n 10 --no-pager
        exit 1
    fi
else
    echo -e "${RED}[FAIL] Error: Failed to start trackora.service.${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# Completion Message
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD}             Trackora Installation Completed Successfully!            ${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo -e "\n${YELLOW}${BOLD}POST-INSTALLATION INSTRUCTIONS:${NC}"
echo -e "Trackora is now fully installed, enabled, and running in the background."
echo -e "*Note: If tracking is not active, you may need to log out and log back in to reload GNOME Shell.*"
echo -e "\nTo open the Trackora Dashboard GUI, run:"
echo -e "  ${BOLD}python3 -m trackora.gui${NC}\n"
exit 0
