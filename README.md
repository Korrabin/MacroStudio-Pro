# MacroStudio Pro

Записывайте действия мыши и клавиатуры, редактируйте их по шагам и воспроизводите на Windows, macOS и Linux.  
Record mouse and keyboard actions, edit them step by step, and replay them on Windows, macOS, and Linux.

[Русский](#русский) · [English](#english)

---

## Русский

### Возможности

- **Запись и воспроизведение**: клики, движения курсора, прокрутка, нажатия клавиш.
- **Редактор шагов**: смотрите тайминги, координаты и клавиши, добавляйте клики, ввод текста, паузы и команды вручную, сжимайте лишние паузы одним кликом.
- **Режимы повтора**: один раз, N раз, по времени (часы / минуты / секунды) или бесконечно. Скорость настраивается от 0.25× до 4×.
- **Естественное поведение**: случайные задержки между циклами и лёгкий джиттер курсора.
- **Безопасность**: аварийная остановка по `Esc` / `F12` или уводом курсора в левый верхний угол экрана.
- **После завершения**: выключить ПК, уйти в сон, заблокировать экран или закрыть программу.
- **Веб-панель**: запустите с флагом `--web` и откройте `http://127.0.0.1:8765`.

### Горячие клавиши

| Клавиша | Действие |
| :---: | :--- |
| `F9` | Начать / остановить запись |
| `F10` | Запустить / остановить повтор |
| `F7` | Пауза |
| `F8` | Захватить координаты курсора |
| `Esc` / `F12` | Аварийная остановка |

Клавиши можно переназначить на любые `F1`–`F12` во вкладке «Горячие клавиши и Таймер». По умолчанию выбраны клавиши, которые не конфликтуют с оверлеем NVIDIA.

### Запуск

- **Windows**: двойной клик по `Start_Windows.bat`
- **macOS**: двойной клик по `Start_macOS.command`. При первом запуске разрешите доступ в «Системные настройки → Конфиденциальность и безопасность → Универсальный доступ».
- **Linux**:
  ```bash
  chmod +x Start_Linux.sh
  ./Start_Linux.sh
  ```

Или запустите напрямую: `python mouse_keyboard_recorder.py`

---

## English

### Features

- **Record and replay**: clicks, cursor movement, scrolling, key presses.
- **Step editor**: view timings, coordinates, and keys; add clicks, typed text, delays, and commands manually; trim idle pauses in one click.
- **Playback modes**: once, N times, for a set time (hours / minutes / seconds), or in a loop. Speed ranges from 0.25× to 4×.
- **Natural behavior**: randomized delays between cycles and slight cursor jitter.
- **Safety**: panic stop with `Esc` / `F12`, or by moving the cursor to the top-left corner of the screen.
- **After finishing**: shut down, sleep, lock the screen, or exit the app.
- **Web panel**: run with `--web` and open `http://127.0.0.1:8765`.

### Hotkeys

| Key | Action |
| :---: | :--- |
| `F9` | Start / stop recording |
| `F10` | Start / stop playback |
| `F7` | Pause / resume |
| `F8` | Capture cursor coordinates |
| `Esc` / `F12` | Panic stop |

Hotkeys can be remapped to any `F1`–`F12` key in the "Hotkeys & Scheduler" tab. The defaults avoid conflicts with the NVIDIA overlay.

### Quick start

- **Windows**: double-click `Start_Windows.bat`
- **macOS**: double-click `Start_macOS.command`. On first launch, grant access under System Settings → Privacy & Security → Accessibility.
- **Linux**:
  ```bash
  chmod +x Start_Linux.sh
  ./Start_Linux.sh
  ```

Or run directly: `python mouse_keyboard_recorder.py`

---

## Releases

GitHub Actions builds standalone executables on every push to `main`:
`MacroStudio-Windows-x64.exe`, `MacroStudio-Native-Light.exe`, `MacroStudio-macOS`, `MacroStudio-Linux-x64`.

## License

[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/): public domain, use it however you like.
