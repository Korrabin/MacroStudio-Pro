@echo off
chcp 65001 >nul
title MacroStudio Pro — Launcher for Windows
cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    start "" pythonw mouse_keyboard_recorder.py 2>nul || python mouse_keyboard_recorder.py
    exit /b 0
)

if exist "MacroStudio.exe" (
    start "" "MacroStudio.exe"
    exit /b 0
)

set CSC_PATH=C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC_PATH%" set CSC_PATH=C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe

if exist "%CSC_PATH%" (
    "%CSC_PATH%" /target:winexe /out:MacroStudio.exe "src\windows_native\MacroStudioWin.cs" >nul
    if exist "MacroStudio.exe" (
        start "" "MacroStudio.exe"
        exit /b 0
    )
)

pause
