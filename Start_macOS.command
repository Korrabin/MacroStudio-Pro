#!/bin/bash
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
    python3 mouse_keyboard_recorder.py
else
    xcode-select --install
fi
