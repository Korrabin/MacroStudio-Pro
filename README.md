<div align="center">

# 🖱️⌨️ MacroStudio Pro

**Cross-Platform Mouse & Keyboard Recorder, Visual Step Editor, and Automation Studio**  
*Кроссплатформенная программа для записи, редактирования и воспроизведения действий мыши и клавиатуры*

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](#-быстрый-старт--quick-start)
[![Release](https://img.shields.io/badge/Release-v1.0.0-brightgreen.svg)](#-ключевые-возможности)
[![Hotkeys](https://img.shields.io/badge/Hotkeys-F1--F12%20(No%20NVIDIA%20Conflict)-orange.svg)](#-горячие-клавиши)

[🇷🇺 Русский](#-русская-версия) • [🌐 English](#-english-version)

</div>

---

<a name="-русская-версия"></a>
## 🇷🇺 Русская версия

**MacroStudio Pro** — это комплекс для автоматизации действий на компьютере. Программа записывает клики мыши, движение курсора, прокрутку колеса и нажатия клавиш, позволяет редактировать макросы в табличном редакторе шагов и воспроизводить их с настройкой скорости, расписания и интервалов.

### 🌟 Ключевые возможности

- 🖥️ **Кроссплатформенная архитектура**:
  - **Windows**: Нативная работа через системный Win32 API (`user32.dll`) и облегченная сборка `MacroStudio.exe`.
  - **macOS**: Поддержка системного фреймворка `ApplicationServices / Quartz` и `osascript`.
  - **Linux**: Поддержка `X11 / XTest` (`libX11.so.6`, `libXtst.so.6`) и предсобранного нативного модуля.
  - **Веб-панель управления**: Встроенный локальный веб-интерфейс (`http://127.0.0.1:8765`) при запуске с параметром `--web`.
- ⌨️ **Удобные горячие клавиши F1–F12 (Без конфликтов с NVIDIA)**:
  - Управление назначено на одиночные функциональные клавиши (`F9`, `F10`, `F7`, `F8`), которые не вызывают оверлей GeForce Experience / ShadowPlay.
- ✎ **Визуальный конструктор и редактор макросов**:
  - Просмотр каждого шага: тайминги, координаты $X, Y$, клавиши и кнопки мыши.
  - Добавление действий вручную: клики, перемещения, ввод текста, паузы, запуск внешних программ и команд.
  - Сжатие длинных пауз между действиями в один клик.
- 🔁 **Гибкие режимы повтора**:
  - Повторить 1 раз (`Repeat once`).
  - Повторить заданное число раз (`Repeat N times`).
  - Повторять заданное время: часы / минуты / секунды (`Repeat for time`).
  - Бесконечный цикл (`Infinite Loop`).
- 🛡️ **Гуманизация и защита**:
  - Случайные и фиксированные задержки между циклами.
  - Плавное микро-отклонение траектории мыши (джиттер).
  - Аварийная остановка клавишей `Esc` / `F12` и защита **Fail-Safe** (увод курсора в левый верхний угол экрана `0, 0`).
- ⚡ **Действия по завершении**: автоматическое выключение ПК, переход в спящий режим, блокировка экрана или закрытие программы.

---

### ⌨️ Горячие клавиши

| Клавиша по умолчанию | Назначение | Описание |
| :---: | :--- | :--- |
| **`F9`** | **Старт / Стоп записи** | Начинает перехват действий или сохраняет макрос |
| **`F10`** | **Старт / Стоп повтора** | Запускает воспроизведение выбранной записи или останавливает цикл |
| **`F7`** | **Пауза** | Временная приостановка записи или повтора |
| **`F8`** | **Захват координат $X, Y$** | Мгновенно копирует текущее положение курсора в конструктор шагов |
| **`Esc`** или **`F12`** | **Аварийный стоп (Panic Stop)** | Немедленно прерывает выполнение макроса |

*Любую функциональную клавишу можно переназначить на `F1`–`F12` во вкладке «Горячие клавиши и Таймер».*

---

### 🚀 Быстрый запуск

#### 🪟 Windows (10 / 11)
Запустите файл **`Start_Windows.bat`** двойным кликом (или выполните `python mouse_keyboard_recorder.py`).

#### 🍏 macOS
Запустите файл **`Start_macOS.command`** двойным кликом (или выполните в терминале `python3 mouse_keyboard_recorder.py`).  
> *Примечание: при первом запуске разрешите Терминалу управление в «Системные настройки → Конфиденциальность и безопасность → Универсальный доступ».*

#### 🐧 Linux
Запустите в терминале:
```bash
chmod +x Start_Linux.sh
./Start_Linux.sh
```

---

<a name="-english-version"></a>
## 🌐 English Version

**MacroStudio Pro** is a cross-platform desktop automation suite designed to record, visually edit, and replay mouse and keyboard actions across Windows, macOS, and Linux.

### 🌟 Key Features

- 🖥️ **Multi-Platform Native Engines**:
  - **Windows**: Direct Win32 API (`user32.dll`) integration alongside a lightweight native `MacroStudio.exe` build.
  - **macOS**: Quartz / CoreGraphics (`ApplicationServices`) and `osascript` integration.
  - **Linux**: X11 / XTest dynamic loader (`libX11.so.6`, `libXtst.so.6`) with a pre-compiled native binary.
  - **Web Control Panel**: Built-in local web interface (`http://127.0.0.1:8765`) when launched with `--web`.
- ⌨️ **NVIDIA-Safe Functional Hotkeys**:
  - Eliminates conflicts with NVIDIA GeForce Experience / ShadowPlay by using customizable single F-keys (`F9`, `F10`, `F7`, `F8`).
- ✎ **Visual Step Editor & Macro Builder**:
  - Inspect every recorded event with timestamps, coordinates, keys, and mouse buttons.
  - Manually add steps: mouse clicks, cursor movement, text typing, delays, and shell commands.
  - One-click **delay compressor** to trim idle pauses.
- 🔁 **Flexible Playback Modes**:
  - Repeat once, repeat $N$ times, timed repeat (hours / minutes / seconds), or infinite loop.
  - Adjustable playback speed slider ($0.25\times$ Slow to $4.0\times$ Fast).
- 🛡️ **Humanization & Safety**:
  - Randomized inter-cycle delays and cursor micro-jittering.
  - Instant panic stops via `Esc` / `F12` and upper-left screen corner `(0, 0)` **Fail-Safe**.
- ⚡ **Automated Post-Actions**: Shutdown computer, sleep, lock workstation, or exit application upon completion.

---

### ⌨️ Default Hotkeys

| Hotkey | Action | Description |
| :---: | :--- | :--- |
| **`F9`** | **Record / Stop** | Toggle mouse and keyboard action recording |
| **`F10`** | **Repeat / Stop** | Toggle playback of the selected macro |
| **`F7`** | **Pause / Resume** | Temporarily pause active recording or replay |
| **`F8`** | **Capture $X, Y$** | Grab current cursor position into the step editor |
| **`Esc`** / **`F12`** | **Panic Stop** | Immediately terminate macro execution |

*Hotkeys can be customized to any `F1`–`F12` key in the "Hotkeys & Scheduler" tab.*

---

### 🚀 Quick Start

#### 🪟 Windows
Double-click **`Start_Windows.bat`** (or run `python mouse_keyboard_recorder.py`).

#### 🍏 macOS
Double-click **`Start_macOS.command`** (or run `python3 mouse_keyboard_recorder.py`).  
> *Note: Grant Accessibility permission under "System Settings → Privacy & Security → Accessibility" when prompted.*

#### 🐧 Linux
Run in your terminal:
```bash
chmod +x Start_Linux.sh
./Start_Linux.sh
```

---

## 🛠️ GitHub Actions Automated Releases

This repository includes a CI/CD workflow (`.github/workflows/release.yml`).  
Whenever you push to `main` or trigger a release, GitHub Actions automatically builds standalone executables:
- `MacroStudio-Windows-x64.exe`
- `MacroStudio-Native-Light.exe`
- `MacroStudio-macOS`
- `MacroStudio-Linux-x64`

---

## 📄 License

This project is dedicated to the public domain under the **Creative Commons Zero v1.0 Universal (CC0 1.0)** license.  
You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission. See the [CC0 1.0 Universal Summary](https://creativecommons.org/publicdomain/zero/1.0/) for details.
