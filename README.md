
# 🖱️⌨️ MacroStudio Pro

**Cross-Platform Mouse & Keyboard Recorder, Visual Step Editor, and Automation Studio**  
*Кроссплатформенная программа для записи, редактирования и воспроизведения действий мыши и клавиатуры*

[](https://creativecommons.org/publicdomain/zero/1.0/)
[](#-быстрый-старт--quick-start)
[](#-особенности--key-features)
[](#-горячие-клавиши--hotkeys)

[🇷🇺 Русский](#-русская-версия) • [🌐 English](#-english-version)



---


## 🇷🇺 Русская версия

**MacroStudio Pro** — это готовое и надежное решение для автоматизации рутинных задач на компьютере. Программа точно записывает каждый клик мыши, движение курсора, скролл и нажатие клавиш, позволяет визуально редактировать макросы в таблице и воспроизводить их с гибкими настройками скорости и задержек.

Главное преимущество — **работает из коробки на чистой ОС** без обязательной установки сторонних библиотек и пакетов Python!

### 🌟 Ключевые возможности

- 🚀 **Zero-Dependency Out-of-the-Box**:
  - **Windows**: Прямое взаимодействие с Win32 API (`user32.dll`). Включает автономный скрипт сборки нативного `.exe` через встроенный в Windows `.NET Framework` (`csc.exe`) за 1 секунду!
  - **macOS**: Прямое взаимодействие с нативным фреймворком `ApplicationServices / Quartz` и `osascript`.
  - **Linux**: Нативный доступ к `libX11.so.6` / `libXtst.so.6` + предсобранный бинарный модуль.
  - **Web-UI Fallback**: Если в системе отсутствует графическая оболочка Tkinter, автоматически поднимается локальный веб-интерфейс (`http://127.0.0.1:8765`).
- ⌨️ **Безопасные горячие клавиши (Без конфликтов с NVIDIA)**:
  - Больше никаких конфликтов с GeForce Experience / ShadowPlay (старые сочетания `Alt+F1/F2/F3` заменены на одиночные настраиваемые клавиши `F9`, `F10`, `F7`, `F8`).
- ✎ **Визуальный конструктор и редактор макросов**:
  - Просмотр каждого шага: точные тайминги, координаты $X, Y$, клавиши и кнопки.
  - Добавление действий вручную: клики, перемещения, набор текста, паузы, запуск внешних программ и bash/cmd-команд.
  - Функция **сжатия пауз** в один клик (удаление длинных простоев между действиями).
- 🔁 **Гибкие режимы повтора**:
  - Повторить 1 раз (`Repeat once`).
  - Повторить заданное число раз (`Repeat N times`).
  - Повторять заданное время: часы / минуты / секунды (`Repeat for time`).
  - Бесконечный цикл (`Infinite Loop`).
- 🛡️ **Анти-бот гуманизация и безопасность**:
  - Случайные и фиксированные задержки между циклами.
  - Плавное микро-отклонение траектории мыши (джиттер).
  - Аварийная остановка клавишей `Esc` / `F12` и аппаратная защита **Fail-Safe** (увод мыши в левый верхний угол экрана `0, 0`).
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
Просто запустите файл **`Start_Windows.bat`** двойным кликом:
- Если установлен Python: сразу откроется полная студия `mouse_keyboard_recorder.py`.
- Если на ПК **чистая Windows без Python**: батник за 1 секунду скомпилирует нативный файл **`MacroStudio.exe`** встроенным системным компилятором `.NET Framework` и запустит его.

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


## 🌐 English Version

**MacroStudio Pro** is a powerful, lightweight, cross-platform automation utility designed to record, visually edit, and flawlessly replay mouse and keyboard actions.

It is built with **zero mandatory external dependencies**, running out-of-the-box on clean installations of Windows, macOS, and Linux without requiring `pip install`.

### 🌟 Key Features

- 🚀 **Zero-Dependency Native Architecture**:
  - **Windows**: Directly accesses Win32 API (`user32.dll`) via standard library `ctypes`. Features an instant auto-compiler that builds a native standalone `MacroStudio.exe` using the Windows built-in `.NET Framework` (`csc.exe`) in under 1 second.
  - **macOS**: Native Quartz / CoreGraphics integration (`ApplicationServices`) + `osascript`.
  - **Linux**: Direct X11 / XTest dynamic loader (`libX11.so.6`, `libXtst.so.6`) with pre-compiled native engine.
  - **Web UI Fallback**: Headless environments automatically spin up a local control panel at `http://127.0.0.1:8765`.
- ⌨️ **NVIDIA-Safe Functional Hotkeys**:
  - Completely eliminates conflicts with NVIDIA GeForce Experience / ShadowPlay by replacing `Alt+F1/F2/F3` with clean, single F-keys (`F9`, `F10`, `F7`, `F8`).
- ✎ **Visual Step Editor & Macro Builder**:
  - Inspect every recorded event with precision timestamps, coordinates, keys, and buttons.
  - Manually craft macros: mouse clicks, smooth movement, text typing, delays, and shell commands.
  - One-click **delay compressor** to eliminate unnecessary idle time.
- 🔁 **Flexible Playback Engines**:
  - Repeat once, repeat $N$ times, timed repeat (hours / minutes / seconds), or infinite loop.
  - Variable speed multiplier slider ($0.25\times$ Slow to $4.0\times$ Fast).
- 🛡️ **Anti-Bot Humanization & Safety**:
  - Randomized inter-cycle delays and cursor jittering.
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
Double-click **`Start_Windows.bat`**:
- If Python is installed, the complete Studio will launch immediately.
- On a **clean Windows system without Python**, it builds and runs native **`MacroStudio.exe`** automatically in 1 second.

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

This repository includes a pre-configured CI/CD workflow (`.github/workflows/release.yml`).  
Whenever you push to `main` or trigger a release, GitHub Actions automatically builds standalone, single-file executables:
- `MacroStudio-Windows-x64.exe`
- `MacroStudio-Native-Light.exe`
- `MacroStudio-macOS`
- `MacroStudio-Linux-x64`

Download them directly from the **Releases** or **Actions Artifacts** tab!

---

## 📄 License

This project is dedicated to the public domain under the **Creative Commons Zero v1.0 Universal (CC0 1.0)** license.  
You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission. See the [CC0 1.0 Universal Summary](https://creativecommons.org/publicdomain/zero/1.0/) for details.
