#!/usr/bin/env bash

# ==============================================================================
# Trackora Uninstallation Script
# ==============================================================================
# Safely deactivates systemd services, removes installed extensions,
# deletes Python site-packages, and handles user data preservation.
#
# Safe, idempotent, and position-independent.
# ==============================================================================

# ANSI color codes for formatted terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${RED}${BOLD}======================================================================${NC}"
echo -e "${RED}${BOLD}                    Uninstalling Trackora Screen Tracker              ${NC}"
echo -e "${RED}${BOLD}======================================================================${NC}"

# 1. Determine script directory (for absolute paths, if needed)
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "[INFO] Running from source directory: ${SRC_DIR}"

# 2. Determine Python target package directory robustly
# If python3 is missing/broken, USER_SITE lookup fails, so we search ~/.local/lib/
USER_SITE=""
if command -v python3 &>/dev/null; then
    USER_SITE=$(python3 -m site --user-site 2>/dev/null)
fi

if [ -z "$USER_SITE" ]; then
    echo -e "${YELLOW}[WARN] Python 3 not detected or user-site path not found. Scanning local directories...${NC}"
    # Try finding an installed trackora folder under ~/.local/lib/
    PKG_CANDIDATE=$(find "${HOME}/.local/lib" -maxdepth 3 -type d -name "trackora" 2>/dev/null | head -n 1)
    if [ -n "$PKG_CANDIDATE" ]; then
        TARGET_PKG_DIR="$PKG_CANDIDATE"
    else
        # Fall back to a default folder name
        TARGET_PKG_DIR="${HOME}/.local/lib/python3.14/site-packages/trackora"
    fi
else
    TARGET_PKG_DIR="${USER_SITE}/trackora"
fi

# Define other target paths
EXT_UUID="trackora@trackora.dev"
TARGET_EXT_DIR="${HOME}/.local/share/gnome-shell/extensions/${EXT_UUID}"
TARGET_SERVICE_FILE="${HOME}/.config/systemd/user/trackora.service"
DATA_DIR="${HOME}/.local/share/trackora"

# Check systemd command existence for safety
HAS_SYSTEMCTL=false
if command -v systemctl &>/dev/null; then
    HAS_SYSTEMCTL=true
fi

# ------------------------------------------------------------------------------
# Step 1: Stop background service
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[1/5] Stopping Trackora background service...${NC}"

if [ "$HAS_SYSTEMCTL" = true ]; then
    # Check and stop service if running
    if systemctl --user is-active --quiet trackora.service &>/dev/null; then
        echo -e "[INFO] Stopping trackora.service..."
        systemctl --user stop trackora.service
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✔ Service stopped successfully.${NC}"
        else
            echo -e "${YELLOW}Warning: Failed to stop service. Proceeding anyway.${NC}"
        fi
    else
        echo -e "[INFO] service is not active. Skipping."
    fi
else
    echo -e "[INFO] systemctl not found. Skipping service stopping phase."
fi

# ------------------------------------------------------------------------------
# Step 2: Remove systemd service files
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/5] Cleaning up systemd configurations...${NC}"

if [ "$HAS_SYSTEMCTL" = true ]; then
    # Disable manually enabled service instances to prevent stale default.target.wants symlinks
    if systemctl --user is-enabled --quiet trackora.service &>/dev/null; then
        echo -e "[INFO] Service is enabled. Disabling trackora.service to clean up symlinks..."
        systemctl --user disable trackora.service &>/dev/null
    fi
fi

if [ -f "$TARGET_SERVICE_FILE" ]; then
    echo -e "[INFO] Deleting: ${TARGET_SERVICE_FILE}"
    rm -f "$TARGET_SERVICE_FILE"
    if [ "$HAS_SYSTEMCTL" = true ]; then
        systemctl --user daemon-reload
    fi
    echo -e "${GREEN}✔ systemd service configuration removed.${NC}"
else
    echo -e "[INFO] No systemd unit file found at: ${TARGET_SERVICE_FILE}. Skipping."
fi

# ------------------------------------------------------------------------------
# Step 3: Remove GNOME Shell extension
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/5] Uninstalling GNOME Shell Extension...${NC}"
if [ -d "$TARGET_EXT_DIR" ]; then
    # Disable extension first
    if command -v gnome-extensions &> /dev/null; then
        echo -e "[INFO] Disabling extension: ${EXT_UUID}"
        gnome-extensions disable "$EXT_UUID" &>/dev/null
    fi
    echo -e "[INFO] Deleting: ${TARGET_EXT_DIR}"
    rm -rf "$TARGET_EXT_DIR"
    echo -e "${GREEN}✔ GNOME extension files removed.${NC}"
else
    echo -e "[INFO] No extension files found under: ${TARGET_EXT_DIR}. Skipping."
fi

# ------------------------------------------------------------------------------
# Step 4: Remove application package from user site-packages
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/5] Removing Trackora python package...${NC}"
if [ -d "$TARGET_PKG_DIR" ]; then
    echo -e "[INFO] Deleting: ${TARGET_PKG_DIR}"
    rm -rf "$TARGET_PKG_DIR"
    echo -e "${GREEN}✔ Deleted application package.${NC}"
else
    echo -e "[INFO] No package found at: ${TARGET_PKG_DIR}. Skipping."
fi

# ------------------------------------------------------------------------------
# Step 5: Handle User Data (History, DB, Settings)
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[5/5] Handling user configuration & database files...${NC}"

if [ -d "$DATA_DIR" ]; then
    echo -e "${YELLOW}Trackora user data (SQLite database, custom settings, and history) is located at:${NC}"
    echo -e "  ${BOLD}${DATA_DIR}${NC}"
    
    # Prompt the user to preserve or delete (Case-insensitive match, default: Preserve)
    echo -n -e "\n${RED}${BOLD}Do you want to permanently delete all tracking history and configuration? [y/N]: ${NC}"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "[INFO] Deleting data directory..."
        rm -rf "$DATA_DIR"
        echo -e "${GREEN}✔ All database and config files have been deleted.${NC}"
    else
        echo -e "${GREEN}✔ Preserved user data. Your tracking history and settings have been left intact.${NC}"
    fi
else
    echo -e "[INFO] No user data folder found. Cleanup complete."
fi

# ------------------------------------------------------------------------------
# Uninstallation Complete
# ------------------------------------------------------------------------------
echo -e "\n${GREEN}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD}             Trackora Uninstallation Completed Successfully!          ${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo -e "\nIf GNOME Shell still registers a stale reference to the extension,"
echo -e "please log out and log back in to reload your shell session.\n"
exit 0
