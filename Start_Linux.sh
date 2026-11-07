#!/bin/bash
cd "$(dirname "$0")"
chmod +x bin/linux/macro_engine_linux_x64 2>/dev/null || true
if command -v python3 >/dev/null 2>&1; then
    python3 mouse_keyboard_recorder.py "$@"
else
    echo "Error: python3 is required."
fi
