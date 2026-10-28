#!/usr/bin/env bash
# Copy the mod into wipeout_pc's mods folder (default ~/Games/wipeout_pc/mods).
# Usage: ./install.sh [MODS_DIR]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="${1:-${GOW3_MODS_DIR:-$HOME/Games/wipeout_pc/mods}}"
mkdir -p "$dest/Cockpit Camera"
cp -r "$here/mod/Cockpit Camera/." "$dest/Cockpit Camera/"
rm -f "$dest/Cockpit Camera/patches/.gitkeep" 2>/dev/null || true
echo "Installed to $dest/Cockpit Camera"
