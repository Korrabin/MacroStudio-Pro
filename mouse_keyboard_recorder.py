from __future__ import annotations

import ctypes
import ctypes.util
import http.server
import json
import os
import platform
import random
import shutil
import socketserver
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

try:
    from pynput import keyboard as pynput_kb, mouse as pynput_mouse
    from pynput.keyboard import Controller as PynputKbController, Key, KeyCode
    from pynput.mouse import Button, Controller as PynputMouseController
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


VK_MAP_WIN: Dict[str, int] = {
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "shift": 0x10,
    "ctrl": 0x11, "alt": 0x12, "pause": 0x13, "caps_lock": 0x14,
    "esc": 0x1B, "space": 0x20, "page_up": 0x21, "page_down": 0x22,
    "end": 0x23, "home": 0x24, "left": 0x25, "up": 0x26,
    "right": 0x27, "down": 0x28, "insert": 0x2D, "delete": 0x2E,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74,
    "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79,
    "f11": 0x7A, "f12": 0x7B,
}
for _c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    VK_MAP_WIN[_c.lower()] = ord(_c)

F_KEYS_LIST = [f"F{i}" for i in range(1, 13)]


class NativeInputBackend:
    def __init__(self):
        self.sys_name = platform.system().lower()
        self.backend_name = "Unknown"
        self._init_os_api()

    def _init_os_api(self):
        if PYNPUT_AVAILABLE:
            self.backend_name = f"pynput ({platform.system()})"
            self._m_ctrl = PynputMouseController()
            self._k_ctrl = PynputKbController()
            return

        if "windows" in self.sys_name:
            self.backend_name = "Win32 API (user32.dll)"
            self.user32 = ctypes.windll.user32
        elif "darwin" in self.sys_name:
            self.backend_name = "macOS Quartz / AppleScript"
            app_services = ctypes.util.find_library("ApplicationServices")
            self.cg = ctypes.CDLL(app_services) if app_services else None
        else:
            x11_path = ctypes.util.find_library("X11") or "libX11.so.6"
            xtst_path = ctypes.util.find_library("Xtst") or "libXtst.so.6"
            try:
                self.x11 = ctypes.CDLL(x11_path)
                self.xtst = ctypes.CDLL(xtst_path)
                self.x11.XOpenDisplay.restype = ctypes.c_void_p
                self.display = self.x11.XOpenDisplay(None)
                if self.display:
                    self.backend_name = "Linux X11 / XTest"
                else:
                    self.backend_name = "Linux CLI / xdotool"
            except Exception:
                self.x11 = None
                self.xtst = None
                self.display = None
                self.backend_name = "Linux CLI / xdotool"

    def get_mouse_pos(self) -> Tuple[int, int]:
        if PYNPUT_AVAILABLE:
            pos = self._m_ctrl.position
            return int(pos[0]), int(pos[1])

        if "windows" in self.sys_name:
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            pt = POINT()
            self.user32.GetCursorPos(ctypes.byref(pt))
            return int(pt.x), int(pt.y)

        if "darwin" in self.sys_name and getattr(self, "cg", None):
            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
            try:
                self.cg.CGEventCreate.restype = ctypes.c_void_p
                self.cg.CGEventGetLocation.argtypes = [ctypes.c_void_p]
                self.cg.CGEventGetLocation.restype = CGPoint
                ev = self.cg.CGEventCreate(None)
                loc = self.cg.CGEventGetLocation(ev)
                if ev:
                    self.cg.CFRelease(ctypes.c_void_p(ev))
                return int(loc.x), int(loc.y)
            except Exception:
                return 0, 0

        if getattr(self, "display", None):
            root_ret = ctypes.c_ulong()
            child_ret = ctypes.c_ulong()
            rx, ry, wx, wy = ctypes.c_int(), ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
            mask = ctypes.c_uint()
            root_win = self.x11.XDefaultRootWindow(ctypes.c_void_p(self.display))
            self.x11.XQueryPointer(
                ctypes.c_void_p(self.display),
                root_win,
                ctypes.byref(root_ret),
                ctypes.byref(child_ret),
                ctypes.byref(rx),
                ctypes.byref(ry),
                ctypes.byref(wx),
                ctypes.byref(wy),
                ctypes.byref(mask),
            )
            return int(rx.value), int(ry.value)

        if shutil.which("xdotool"):
            try:
                out = subprocess.check_output(["xdotool", "getmouselocation"], text=True)
                parts = dict(item.split(":") for item in out.strip().split()[:2])
                return int(parts.get("x", 0)), int(parts.get("y", 0))
            except Exception:
                pass
        return 0, 0

    def move_mouse(self, x: int, y: int):
        if PYNPUT_AVAILABLE:
            self._m_ctrl.position = (int(x), int(y))
            return

        if "windows" in self.sys_name:
            self.user32.SetCursorPos(int(x), int(y))
            return

        if "darwin" in self.sys_name and getattr(self, "cg", None):
            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
            try:
                self.cg.CGWarpMouseCursorPosition.argtypes = [CGPoint]
                self.cg.CGWarpMouseCursorPosition(CGPoint(float(x), float(y)))
                return
            except Exception:
                pass

        if getattr(self, "display", None):
            root_win = self.x11.XDefaultRootWindow(ctypes.c_void_p(self.display))
            self.x11.XWarpPointer(
                ctypes.c_void_p(self.display), 0, root_win, 0, 0, 0, 0, int(x), int(y)
            )
            self.x11.XFlush(ctypes.c_void_p(self.display))
            return

        if shutil.which("xdotool"):
            subprocess.run(["xdotool", "mousemove", str(int(x)), str(int(y))], check=False)

    def mouse_button(self, x: int, y: int, button: str = "left", pressed: bool = True):
        self.move_mouse(x, y)
        if PYNPUT_AVAILABLE:
            btn_obj = getattr(Button, button, Button.left)
            if pressed:
                self._m_ctrl.press(btn_obj)
            else:
                self._m_ctrl.release(btn_obj)
            return

        if "windows" in self.sys_name:
            flags = {
                ("left", True): 0x0002,
                ("left", False): 0x0004,
                ("right", True): 0x0008,
                ("right", False): 0x0010,
                ("middle", True): 0x0020,
                ("middle", False): 0x0040,
            }
            flag = flags.get((button, pressed), 0x0002 if pressed else 0x0004)
            self.user32.mouse_event(flag, 0, 0, 0, 0)
            return

        if "darwin" in self.sys_name and getattr(self, "cg", None):
            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
            ev_types = {
                ("left", True): (1, 0),
                ("left", False): (2, 0),
                ("right", True): (3, 1),
                ("right", False): (4, 1),
            }
            ev_type, btn_num = ev_types.get((button, pressed), (1 if pressed else 2, 0))
            try:
                self.cg.CGEventCreateMouseEvent.argtypes = [
                    ctypes.c_void_p, ctypes.c_uint32, CGPoint, ctypes.c_uint32
                ]
                self.cg.CGEventCreateMouseEvent.restype = ctypes.c_void_p
                ev = self.cg.CGEventCreateMouseEvent(
                    None, ev_type, CGPoint(float(x), float(y)), btn_num
                )
                if ev:
                    self.cg.CGEventPost(0, ctypes.c_void_p(ev))
                    self.cg.CFRelease(ctypes.c_void_p(ev))
                return
            except Exception:
                pass

        if getattr(self, "display", None) and getattr(self, "xtst", None):
            btn_idx = {"left": 1, "middle": 2, "right": 3}.get(button, 1)
            self.xtst.XTestFakeButtonEvent(
                ctypes.c_void_p(self.display), btn_idx, int(bool(pressed)), 0
            )
            self.x11.XFlush(ctypes.c_void_p(self.display))
            return

        if shutil.which("xdotool"):
            btn_idx = {"left": "1", "middle": "2", "right": "3"}.get(button, "1")
            cmd = "mousedown" if pressed else "mouseup"
            subprocess.run(["xdotool", cmd, btn_idx], check=False)

    def mouse_scroll(self, x: int, y: int, dx: int = 0, dy: int = 0):
        self.move_mouse(x, y)
        if PYNPUT_AVAILABLE:
            self._m_ctrl.scroll(int(dx), int(dy))
            return

        if "windows" in self.sys_name and dy != 0:
            self.user32.mouse_event(0x0800, 0, 0, int(dy * 120), 0)
            return

        if shutil.which("xdotool") and dy != 0:
            btn = "4" if dy > 0 else "5"
            subprocess.run(["xdotool", "click", btn], check=False)

    def key_event(self, key_name: str, pressed: bool = True):
        key_clean = str(key_name).lower().replace("key.", "")
        if PYNPUT_AVAILABLE:
            try:
                if hasattr(Key, key_clean):
                    k_obj = getattr(Key, key_clean)
                elif len(key_name) == 1:
                    k_obj = KeyCode.from_char(key_name)
                else:
                    k_obj = KeyCode.from_char(key_clean[0])
                if pressed:
                    self._k_ctrl.press(k_obj)
                else:
                    self._k_ctrl.release(k_obj)
                return
            except Exception:
                pass

        if "windows" in self.sys_name:
            vk = VK_MAP_WIN.get(key_clean, ord(key_clean[0].upper()) if key_clean else 0)
            if vk:
                flags = 0 if pressed else 0x0002
                self.user32.keybd_event(vk, 0, flags, 0)
            return

        if "darwin" in self.sys_name and pressed:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'tell application "System Events" to keystroke "{key_clean}"',
                ],
                check=False,
            )
            return

        if shutil.which("xdotool"):
            cmd = "keydown" if pressed else "keyup"
            subprocess.run(["xdotool", cmd, key_clean], check=False)

    def type_text(self, text: str):
        if PYNPUT_AVAILABLE:
            self._k_ctrl.type(text)
            return
        if "windows" in self.sys_name:
            for ch in text:
                self.key_event(ch, True)
                self.key_event(ch, False)
                time.sleep(0.01)
            return
        if "darwin" in self.sys_name:
            safe_txt = text.replace('"', '\\"')
            subprocess.run(
                ["osascript", "-e", f'tell application "System Events" to keystroke "{safe_txt}"'],
                check=False,
            )
            return
        if shutil.which("xdotool"):
            subprocess.run(["xdotool", "type", "--delay", "15", text], check=False)


TRANSLATIONS = {
    "ru": {
        "title": "MacroStudio Pro — Запись и повтор мыши и клавиатуры",
        "tab_main": "▶ Запись и Повтор",
        "tab_editor": "✎ Редактор шагов",
        "tab_hotkeys": "⌨ Горячие клавиши и Таймер",
        "tab_stats": "📊 Статистика и Лог",
        "menu_file": "Файл",
        "menu_edit": "Правка",
        "menu_tools": "Инструменты",
        "menu_help": "Справка",
        "file_new": "Создать новую запись",
        "file_open": "Импортировать запись (.rsmk / .json)...",
        "file_save_as": "Экспортировать выбранную запись...",
        "file_exit": "Выход",
        "edit_rename": "Переименовать запись",
        "edit_duplicate": "Дублировать запись",
        "edit_delete": "Удалить запись",
        "tools_lang": "Switch Language (English / Русский)",
        "tools_open_folder": "Открыть папку с макросами",
        "tools_install_pynput": "Установить/обновить драйвер pynput",
        "help_hotkeys": "Горячие клавиши и справка",
        "help_about": "О программе",
        "repeat_once": "Повторить один раз (Repeat once)",
        "repeat_times": "Повторить (Repeat)",
        "times_label": "раз(а)",
        "repeat_for": "Повторять в течение (Repeat for)",
        "time_label": "времени",
        "repeat_infinite": "Бесконечный повтор (до нажатия Стоп / {rep_hk})",
        "shutdown_after": "Действие после завершения повтора:",
        "do_not_activate": "Не активировать окно программы после остановки повтора",
        "minimize_on_run": "Сворачивать окно во время записи и воспроизведения",
        "humanize_mouse": "Плавное движение мыши и микро-отклонения (Анти-бот)",
        "delay_group": "Задержка между двумя повторами (Delay time between two repeat)",
        "set_delay": "Установить паузу между циклами повтора",
        "hour_lbl": "час",
        "min_lbl": "мин",
        "sec_lbl": "сек",
        "random_delay": "Случайная задержка (от 0 до указанного выше времени)",
        "speed_group": "Настройка скорости повтора (Repeat Speed Setting)",
        "slow": "Медленно (0.25x)",
        "normal": "Нормально (1.0x)",
        "fast": "Быстро (4.0x)",
        "btn_record": "🔴 Запись ({hk})",
        "btn_stop_record": "⏹ Стоп ({hk})",
        "btn_repeat": "▶ Повтор ({hk})",
        "btn_stop_repeat": "⏹ Стоп ({hk})",
        "col_name": "Имя записи (Record Name)",
        "col_events": "Событий",
        "col_duration": "Длит. (с)",
        "col_location": "Расположение файла (Record Location)",
        "status_ready": "Готов [{backend}]. Запись: {rec_hk} | Повтор: {rep_hk} | Координаты: {pick_hk} | Стоп: Esc",
        "status_recording": "🔴 ИДЕТ ЗАПИСЬ... Нажмите {rec_hk} для остановки (записано событий: {count})",
        "status_repeating": "▶ Воспроизведение [{name}] — цикл {cycle} (шаг {step}/{total})...",
        "status_delay": "⏳ Пауза перед следующим циклом: {sec:.1f} сек...",
        "status_stopped": "⏹ Остановлено. Всего событий в записи: {count}.",
    },
    "en": {
        "title": "MacroStudio Pro — Mouse and Keyboard Recorder",
        "tab_main": "▶ Recorder & Player",
        "tab_editor": "✎ Step Editor",
        "tab_hotkeys": "⌨ Hotkeys & Scheduler",
        "tab_stats": "📊 Statistics & Log",
        "menu_file": "File",
        "menu_edit": "Edit",
        "menu_tools": "Tools",
        "menu_help": "Help",
        "file_new": "Create New Record",
        "file_open": "Import Record (.rsmk / .json)...",
        "file_save_as": "Export Selected Record...",
        "file_exit": "Exit",
        "edit_rename": "Rename Selected Record",
        "edit_duplicate": "Duplicate Selected Record",
        "edit_delete": "Delete Selected Record",
        "tools_lang": "Переключить язык (Русский / English)",
        "tools_open_folder": "Open Records Folder",
        "tools_install_pynput": "Install/Update pynput Hook Library",
        "help_hotkeys": "Hotkeys & Instructions",
        "help_about": "About MacroStudio Pro",
        "repeat_once": "Repeat once",
        "repeat_times": "Repeat",
        "times_label": "times",
        "repeat_for": "Repeat for",
        "time_label": "time",
        "repeat_infinite": "Infinite Repeat (until Stop / {rep_hk})",
        "shutdown_after": "Post-completion action:",
        "do_not_activate": "Do not activate this window when repeating stopped",
        "minimize_on_run": "Minimize window during recording & playback",
        "humanize_mouse": "Smooth mouse movement & anti-bot micro-jitter",
        "delay_group": "Delay time between two repeat",
        "set_delay": "Set delay time between two repeat",
        "hour_lbl": "hour",
        "min_lbl": "minute",
        "sec_lbl": "second",
        "random_delay": "Delay a random time (delay 0 to the above time)",
        "speed_group": "Repeat Speed Setting",
        "slow": "Slow (0.25x)",
        "normal": "Normal (1.0x)",
        "fast": "Fast (4.0x)",
        "btn_record": "🔴 Record ({hk})",
        "btn_stop_record": "⏹ Stop ({hk})",
        "btn_repeat": "▶ Repeat ({hk})",
        "btn_stop_repeat": "⏹ Stop ({hk})",
        "col_name": "Record Name",
        "col_events": "Events",
        "col_duration": "Duration (s)",
        "col_location": "Record Location",
        "status_ready": "Ready [{backend}]. Record: {rec_hk} | Repeat: {rep_hk} | Coords: {pick_hk} | Stop: Esc",
        "status_recording": "🔴 RECORDING... Press {rec_hk} to stop (events: {count})",
        "status_repeating": "▶ Repeating [{name}] — cycle {cycle} (step {step}/{total})...",
        "status_delay": "⏳ Waiting between repeats: {sec:.1f}s...",
        "status_stopped": "⏹ Stopped. Total events in record: {count}.",
    },
}


class MacroEngine:
    def __init__(self, on_status_change: Optional[Callable[[str], None]] = None):
        self.backend = NativeInputBackend()
        self.on_status_change = on_status_change

        self.records_dir = Path.home() / "Documents" / "RobotSoft" / "Records"
        try:
            self.records_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            self.records_dir = Path.cwd() / "Records"
            self.records_dir.mkdir(parents=True, exist_ok=True)

        self.is_recording = False
        self.is_paused_recording = False
        self.is_repeating = False
        self.is_paused_repeating = False
        self.stop_event = threading.Event()

        self.recorded_events: List[Dict[str, Any]] = []
        self.record_start_time = 0.0
        self.last_move_time = 0.0

        self.stats = {
            "cycles_completed": 0,
            "clicks_sent": 0,
            "keys_sent": 0,
            "macros_recorded": 0,
            "total_play_seconds": 0.0,
        }
        self.logs: List[str] = []
        self.log(f"Инициализирован движок: {self.backend.backend_name}")
        self._ensure_sample_macro()

    def log(self, message: str):
        ts = time.strftime("%H:%M:%S")
        entry = f"[{ts}] {message}"
        self.logs.append(entry)
        if len(self.logs) > 500:
            self.logs = self.logs[-500:]
        if self.on_status_change:
            try:
                self.on_status_change(entry)
            except Exception:
                pass

    def _ensure_sample_macro(self):
        existing = list(self.records_dir.glob("*.rsmk"))
        if not existing:
            sample_path = self.records_dir / "NewRecord1.rsmk"
            sample_events = [
                {"type": "mouse_move", "time": 0.10, "x": 450, "y": 320, "comment": "Наведение курсора"},
                {"type": "mouse_click", "time": 0.35, "x": 450, "y": 320, "button": "left", "pressed": True, "comment": "Нажатие ЛКМ"},
                {"type": "mouse_click", "time": 0.45, "x": 450, "y": 320, "button": "left", "pressed": False, "comment": "Отпускание ЛКМ"},
                {"type": "wait", "time": 1.00, "duration": 0.5, "comment": "Пауза 0.5 сек"},
                {"type": "text_type", "time": 1.50, "text": "Hello from MacroStudio!", "comment": "Ввод текста"},
            ]
            self.save_macro_file(sample_path, sample_events)

    def save_macro_file(self, path: Path, events: List[Dict[str, Any]]) -> Path:
        duration = round(float(events[-1].get("time", 0.0)), 2) if events else 0.0
        payload = {
            "name": path.stem,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_count": len(events),
            "duration": duration,
            "events": events,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path

    def load_macro_file(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("events", [])
        except Exception as exc:
            self.log(f"Ошибка чтения файла {path.name}: {exc}")
            return []

    def list_macros(self) -> List[Dict[str, Any]]:
        result = []
        files = sorted(
            self.records_dir.glob("*.rsmk"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
        )
        for p in files:
            events = self.load_macro_file(p)
            dur = round(float(events[-1].get("time", 0.0)), 2) if events else 0.0
            result.append(
                {
                    "name": p.stem,
                    "events_count": len(events),
                    "duration": dur,
                    "path": str(p),
                }
            )
        return result

    def next_record_path(self) -> Path:
        idx = 1
        while True:
            p = self.records_dir / f"NewRecord{idx}.rsmk"
            if not p.exists():
                return p
            idx += 1


if TKINTER_AVAILABLE:
    class MacroStudioDesktopApp:
        def __init__(self, root: tk.Tk):
            self.root = root
            self.lang = "ru"
            self.engine = MacroEngine(on_status_change=self._on_engine_log)

            self.mouse_listener = None
            self.kb_listener = None
            self.hotkey_listener = None
            self.polling_thread = None

            self.repeat_mode_var = tk.StringVar(value="for")
            self.repeat_times_var = tk.IntVar(value=30)
            self.repeat_for_val_var = tk.IntVar(value=1)
            self.repeat_for_unit_var = tk.StringVar(value="hour")

            self.post_action_var = tk.StringVar(value="none")
            self.do_not_activate_var = tk.BooleanVar(value=False)
            self.minimize_on_run_var = tk.BooleanVar(value=False)
            self.humanize_mouse_var = tk.BooleanVar(value=False)
            self.failsafe_corner_var = tk.BooleanVar(value=True)

            self.set_delay_var = tk.BooleanVar(value=False)
            self.delay_hour_var = tk.IntVar(value=0)
            self.delay_min_var = tk.IntVar(value=0)
            self.delay_sec_var = tk.IntVar(value=0)
            self.random_delay_var = tk.BooleanVar(value=False)

            self.speed_slider_var = tk.DoubleVar(value=0.0)
            self.status_var = tk.StringVar(value="")

            self.hk_record_var = tk.StringVar(value="F9")
            self.hk_pause_rec_var = tk.StringVar(value="F7")
            self.hk_repeat_var = tk.StringVar(value="F10")
            self.hk_pick_var = tk.StringVar(value="F8")
            self.hk_panic_var = tk.StringVar(value="Esc / F12")

            self.countdown_sec_var = tk.IntVar(value=0)
            self.schedule_time_var = tk.StringVar(value="00:00:00")
            self.use_schedule_var = tk.BooleanVar(value=False)

            self.current_editing_path: Optional[Path] = None
            self.current_steps: List[Dict[str, Any]] = []
            self.live_coords_var = tk.StringVar(value="X: 0, Y: 0")

            self._setup_window()
            self._build_menu()
            self._build_notebook()
            self._apply_language()
            self._update_states()
            self._refresh_records_table()
            self._start_global_hotkeys()
            self._start_cursor_tracker()

            self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        def _setup_window(self):
            self.root.title("MacroStudio Pro — Mouse and Keyboard Recorder")
            self.root.geometry("680x640")
            self.root.minsize(640, 580)
            style = ttk.Style(self.root)
            if "vista" in style.theme_names():
                style.theme_use("vista")
            elif "clam" in style.theme_names():
                style.theme_use("clam")

        def _build_menu(self):
            self.menubar = tk.Menu(self.root)

            self.file_menu = tk.Menu(self.menubar, tearoff=0)
            self.file_menu.add_command(label="New", command=self.create_blank_record)
            self.file_menu.add_command(label="Import", command=self.import_record)
            self.file_menu.add_command(label="Export", command=self.export_record)
            self.file_menu.add_separator()
            self.file_menu.add_command(label="Exit", command=self.on_close)

            self.edit_menu = tk.Menu(self.menubar, tearoff=0)
            self.edit_menu.add_command(label="Rename", command=self.rename_selected_record)
            self.edit_menu.add_command(label="Duplicate", command=self.duplicate_selected_record)
            self.edit_menu.add_command(label="Delete", command=self.delete_selected_record)

            self.tools_menu = tk.Menu(self.menubar, tearoff=0)
            self.tools_menu.add_command(label="Language", command=self.toggle_language)
            self.tools_menu.add_command(label="Folder", command=self.open_records_folder)
            self.tools_menu.add_command(label="Install pynput", command=self.install_pynput_gui)

            self.help_menu = tk.Menu(self.menubar, tearoff=0)
            self.help_menu.add_command(label="Hotkeys", command=self.show_help)
            self.help_menu.add_command(label="About", command=self.show_about)

            self.menubar.add_cascade(label="File", menu=self.file_menu)
            self.menubar.add_cascade(label="Edit", menu=self.edit_menu)
            self.menubar.add_cascade(label="Tools", menu=self.tools_menu)
            self.menubar.add_cascade(label="Help", menu=self.help_menu)
            self.root.config(menu=self.menubar)

        def _build_notebook(self):
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(6, 4))

            self.tab_main = ttk.Frame(self.notebook, padding=10)
            self.tab_editor = ttk.Frame(self.notebook, padding=10)
            self.tab_hotkeys = ttk.Frame(self.notebook, padding=10)
            self.tab_stats = ttk.Frame(self.notebook, padding=10)

            self.notebook.add(self.tab_main, text="Recorder & Player")
            self.notebook.add(self.tab_editor, text="Step Editor")
            self.notebook.add(self.tab_hotkeys, text="Hotkeys & Scheduler")
            self.notebook.add(self.tab_stats, text="Statistics & Log")

            self._build_tab_main()
            self._build_tab_editor()
            self._build_tab_hotkeys()
            self._build_tab_stats()

            bottom_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(6, 3))
            bottom_bar.pack(side=tk.BOTTOM, fill=tk.X)
            ttk.Label(
                bottom_bar, textvariable=self.status_var, anchor="w", font=("Segoe UI", 8)
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(
                bottom_bar,
                textvariable=self.live_coords_var,
                anchor="e",
                font=("Consolas", 8, "bold"),
                foreground="#005fb8",
            ).pack(side=tk.RIGHT, padx=(8, 2))

        def _build_tab_main(self):
            top_frame = ttk.Frame(self.tab_main)
            top_frame.pack(fill=tk.X, pady=(0, 6))

            left_opts = ttk.Frame(top_frame)
            left_opts.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            right_btns = ttk.Frame(top_frame)
            right_btns.pack(side=tk.RIGHT, anchor="n", padx=(10, 0))

            row1 = ttk.Frame(left_opts)
            row1.pack(fill=tk.X, pady=3)
            self.rb_once = ttk.Radiobutton(
                row1, variable=self.repeat_mode_var, value="once", command=self._update_states
            )
            self.rb_once.pack(side=tk.LEFT)

            row2 = ttk.Frame(left_opts)
            row2.pack(fill=tk.X, pady=3)
            self.rb_times = ttk.Radiobutton(
                row2, variable=self.repeat_mode_var, value="times", command=self._update_states
            )
            self.rb_times.pack(side=tk.LEFT)
            self.spin_times = ttk.Spinbox(
                row2, from_=1, to=999999, width=7, textvariable=self.repeat_times_var
            )
            self.spin_times.pack(side=tk.LEFT, padx=(10, 6))
            self.lbl_times = ttk.Label(row2)
            self.lbl_times.pack(side=tk.LEFT)

            row3 = ttk.Frame(left_opts)
            row3.pack(fill=tk.X, pady=3)
            self.rb_for = ttk.Radiobutton(
                row3, variable=self.repeat_mode_var, value="for", command=self._update_states
            )
            self.rb_for.pack(side=tk.LEFT)
            self.spin_for_val = ttk.Spinbox(
                row3, from_=1, to=99999, width=7, textvariable=self.repeat_for_val_var
            )
            self.spin_for_val.pack(side=tk.LEFT, padx=(6, 6))
            self.combo_for_unit = ttk.Combobox(
                row3,
                textvariable=self.repeat_for_unit_var,
                state="readonly",
                width=8,
                values=["hour", "minute", "second"],
            )
            self.combo_for_unit.pack(side=tk.LEFT, padx=(0, 6))
            self.lbl_for_time = ttk.Label(row3)
            self.lbl_for_time.pack(side=tk.LEFT)

            row4 = ttk.Frame(left_opts)
            row4.pack(fill=tk.X, pady=3)
            self.rb_inf = ttk.Radiobutton(
                row4, variable=self.repeat_mode_var, value="infinite", command=self._update_states
            )
            self.rb_inf.pack(side=tk.LEFT)

            self.btn_record = tk.Button(
                right_btns,
                width=20,
                height=2,
                relief=tk.GROOVE,
                bg="#f8f9fa",
                activebackground="#e2e6ea",
                font=("Segoe UI", 9, "bold"),
                command=self.toggle_record,
            )
            self.btn_record.pack(pady=(0, 8))

            self.btn_repeat = tk.Button(
                right_btns,
                width=20,
                height=2,
                relief=tk.GROOVE,
                bg="#f8f9fa",
                activebackground="#e2e6ea",
                font=("Segoe UI", 9, "bold"),
                command=self.toggle_repeat,
            )
            self.btn_repeat.pack()

            chk_frame = ttk.Frame(self.tab_main)
            chk_frame.pack(fill=tk.X, pady=(2, 6))

            post_row = ttk.Frame(chk_frame)
            post_row.pack(fill=tk.X, pady=2)
            self.lbl_post_action = ttk.Label(post_row)
            self.lbl_post_action.pack(side=tk.LEFT)
            self.combo_post_action = ttk.Combobox(
                post_row,
                textvariable=self.post_action_var,
                state="readonly",
                width=28,
                values=[
                    "none (Ничего не делать)",
                    "shutdown (Выключить ПК)",
                    "sleep (Спящий режим)",
                    "lock (Заблокировать экран)",
                    "exit (Закрыть программу)",
                ],
            )
            self.combo_post_action.current(0)
            self.combo_post_action.pack(side=tk.LEFT, padx=(8, 0))

            self.chk_no_activate = ttk.Checkbutton(chk_frame, variable=self.do_not_activate_var)
            self.chk_no_activate.pack(anchor="w", pady=1)

            self.chk_minimize = ttk.Checkbutton(chk_frame, variable=self.minimize_on_run_var)
            self.chk_minimize.pack(anchor="w", pady=1)

            self.chk_humanize = ttk.Checkbutton(chk_frame, variable=self.humanize_mouse_var)
            self.chk_humanize.pack(anchor="w", pady=1)

            self.grp_delay = ttk.LabelFrame(self.tab_main, padding=(12, 4, 12, 6))
            self.grp_delay.pack(fill=tk.X, pady=(0, 6))

            self.chk_set_delay = ttk.Checkbutton(
                self.grp_delay, variable=self.set_delay_var, command=self._update_states
            )
            self.chk_set_delay.pack(anchor="w", pady=(0, 4))

            delay_spins = ttk.Frame(self.grp_delay)
            delay_spins.pack(fill=tk.X, pady=(0, 4))

            self.spin_delay_h = ttk.Spinbox(
                delay_spins, from_=0, to=999, width=5, textvariable=self.delay_hour_var
            )
            self.spin_delay_h.pack(side=tk.LEFT)
            self.lbl_delay_h = ttk.Label(delay_spins)
            self.lbl_delay_h.pack(side=tk.LEFT, padx=(4, 10))

            self.spin_delay_m = ttk.Spinbox(
                delay_spins, from_=0, to=59, width=5, textvariable=self.delay_min_var
            )
            self.spin_delay_m.pack(side=tk.LEFT)
            self.lbl_delay_m = ttk.Label(delay_spins)
            self.lbl_delay_m.pack(side=tk.LEFT, padx=(4, 10))

            self.spin_delay_s = ttk.Spinbox(
                delay_spins, from_=0, to=59, width=5, textvariable=self.delay_sec_var
            )
            self.spin_delay_s.pack(side=tk.LEFT)
            self.lbl_delay_s = ttk.Label(delay_spins)
            self.lbl_delay_s.pack(side=tk.LEFT, padx=(4, 0))

            self.chk_random_delay = ttk.Checkbutton(
                self.grp_delay, variable=self.random_delay_var
            )
            self.chk_random_delay.pack(anchor="w")

            self.grp_speed = ttk.LabelFrame(self.tab_main, padding=(12, 4, 12, 4))
            self.grp_speed.pack(fill=tk.X, pady=(0, 8))

            slider_container = ttk.Frame(self.grp_speed)
            slider_container.pack(fill=tk.X, padx=40)

            self.scale_speed = tk.Scale(
                slider_container,
                from_=-4,
                to=4,
                resolution=1,
                orient=tk.HORIZONTAL,
                variable=self.speed_slider_var,
                showvalue=False,
                tickinterval=1,
                bd=0,
                highlightthickness=0,
                sliderrelief=tk.FLAT,
                activebackground="#0078d7",
                troughcolor="#e0e0e0",
            )
            self.scale_speed.pack(fill=tk.X)

            speed_labels = ttk.Frame(slider_container)
            speed_labels.pack(fill=tk.X)
            self.lbl_slow = ttk.Label(speed_labels)
            self.lbl_slow.pack(side=tk.LEFT)
            self.lbl_normal = ttk.Label(speed_labels)
            self.lbl_normal.pack(side=tk.LEFT, expand=True)
            self.lbl_fast = ttk.Label(speed_labels)
            self.lbl_fast.pack(side=tk.RIGHT)

            table_frame = ttk.Frame(self.tab_main)
            table_frame.pack(fill=tk.BOTH, expand=True)

            self.tree = ttk.Treeview(
                table_frame,
                columns=("name", "events", "duration", "location"),
                show="headings",
                height=5,
                selectmode="browse",
            )
            self.tree.column("name", width=130, anchor="w", stretch=False)
            self.tree.column("events", width=65, anchor="center", stretch=False)
            self.tree.column("duration", width=70, anchor="center", stretch=False)
            self.tree.column("location", width=340, anchor="w", stretch=True)

            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
            self.tree.configure(yscrollcommand=scrollbar.set)
            self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.tree.bind("<<TreeviewSelect>>", self._on_record_selected)
            self.tree.bind("<Double-1>", lambda _e: self.open_selected_in_editor())

            quick_bar = ttk.Frame(self.tab_main)
            quick_bar.pack(fill=tk.X, pady=(6, 0))
            ttk.Button(
                quick_bar, text="✎ Редактировать шаги", command=self.open_selected_in_editor
            ).pack(side=tk.LEFT, padx=(0, 4))
            ttk.Button(
                quick_bar, text="➕ Новая запись", command=self.create_blank_record
            ).pack(side=tk.LEFT, padx=4)
            ttk.Button(
                quick_bar, text="📋 Дублировать", command=self.duplicate_selected_record
            ).pack(side=tk.LEFT, padx=4)
            ttk.Button(
                quick_bar, text="🗑 Удалить", command=self.delete_selected_record
            ).pack(side=tk.RIGHT)

        def _build_tab_editor(self):
            header = ttk.Frame(self.tab_editor)
            header.pack(fill=tk.X, pady=(0, 6))
            self.lbl_editing_file = ttk.Label(
                header, text="Макрос: (выберите запись)", font=("Segoe UI", 9, "bold")
            )
            self.lbl_editing_file.pack(side=tk.LEFT)
            ttk.Button(
                header, text="💾 Сохранить изменения", command=self.save_editor_steps
            ).pack(side=tk.RIGHT)

            ed_table_frame = ttk.Frame(self.tab_editor)
            ed_table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

            self.steps_tree = ttk.Treeview(
                ed_table_frame,
                columns=("idx", "time", "type", "coords", "param", "comment"),
                show="headings",
                height=12,
                selectmode="browse",
            )
            self.steps_tree.heading("idx", text="#")
            self.steps_tree.heading("time", text="Время (с)")
            self.steps_tree.heading("type", text="Тип действия")
            self.steps_tree.heading("coords", text="X, Y")
            self.steps_tree.heading("param", text="Клавиша / Кнопка / Текст")
            self.steps_tree.heading("comment", text="Комментарий")

            self.steps_tree.column("idx", width=40, anchor="center", stretch=False)
            self.steps_tree.column("time", width=75, anchor="center", stretch=False)
            self.steps_tree.column("type", width=110, anchor="w", stretch=False)
            self.steps_tree.column("coords", width=85, anchor="center", stretch=False)
            self.steps_tree.column("param", width=160, anchor="w", stretch=False)
            self.steps_tree.column("comment", width=150, anchor="w", stretch=True)

            ed_scroll = ttk.Scrollbar(
                ed_table_frame, orient=tk.VERTICAL, command=self.steps_tree.yview
            )
            self.steps_tree.configure(yscrollcommand=ed_scroll.set)
            self.steps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            ed_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            add_box = ttk.LabelFrame(
                self.tab_editor, text="Добавить шаг вручную (Конструктор макроса)", padding=8
            )
            add_box.pack(fill=tk.X, pady=(0, 6))

            row_a = ttk.Frame(add_box)
            row_a.pack(fill=tk.X, pady=2)

            ttk.Label(row_a, text="Действие:").pack(side=tk.LEFT)
            self.new_step_type = tk.StringVar(value="mouse_click")
            ttk.Combobox(
                row_a,
                textvariable=self.new_step_type,
                state="readonly",
                width=15,
                values=[
                    "mouse_click",
                    "mouse_move",
                    "mouse_scroll",
                    "key_tap",
                    "text_type",
                    "wait",
                    "run_cmd",
                ],
            ).pack(side=tk.LEFT, padx=(4, 10))

            ttk.Label(row_a, text="X:").pack(side=tk.LEFT)
            self.new_step_x = tk.IntVar(value=500)
            ttk.Spinbox(row_a, from_=0, to=9999, width=5, textvariable=self.new_step_x).pack(
                side=tk.LEFT, padx=(2, 6)
            )

            ttk.Label(row_a, text="Y:").pack(side=tk.LEFT)
            self.new_step_y = tk.IntVar(value=500)
            ttk.Spinbox(row_a, from_=0, to=9999, width=5, textvariable=self.new_step_y).pack(
                side=tk.LEFT, padx=(2, 8)
            )

            ttk.Label(row_a, text="Параметр / Текст:").pack(side=tk.LEFT)
            self.new_step_param = tk.StringVar(value="left")
            ttk.Entry(row_a, textvariable=self.new_step_param, width=16).pack(
                side=tk.LEFT, padx=(4, 6), fill=tk.X, expand=True
            )

            row_b = ttk.Frame(add_box)
            row_b.pack(fill=tk.X, pady=(4, 0))
            ttk.Button(row_b, text="➕ Добавить шаг", command=self.add_manual_step).pack(
                side=tk.LEFT, padx=(0, 6)
            )
            ttk.Button(
                row_b, text="🎯 Взять текущие X,Y (F8)", command=self.capture_cursor_to_editor
            ).pack(side=tk.LEFT, padx=4)
            ttk.Button(
                row_b, text="⚡ Сжать паузы (>1с → 0.5с)", command=self.compress_step_delays
            ).pack(side=tk.LEFT, padx=4)
            ttk.Button(
                row_b, text="🗑 Удалить выбранный шаг", command=self.delete_selected_step
            ).pack(side=tk.RIGHT)

        def _build_tab_hotkeys(self):
            hk_box = ttk.LabelFrame(
                self.tab_hotkeys,
                text="Настройка F-клавиш (Без конфликтов с NVIDIA Overlay / ShadowPlay)",
                padding=12,
            )
            hk_box.pack(fill=tk.X, pady=(0, 10))

            hk_combos = [
                ("Старт / Стоп записи (Record / Stop):", self.hk_record_var),
                ("Старт / Стоп повтора (Repeat / Stop):", self.hk_repeat_var),
                ("Пауза / Продолжить (Pause / Resume):", self.hk_pause_rec_var),
                ("Захват координат курсора X, Y (Pick Coords):", self.hk_pick_var),
            ]
            for label_txt, var in hk_combos:
                r = ttk.Frame(hk_box)
                r.pack(fill=tk.X, pady=4)
                ttk.Label(r, text=label_txt, width=44).pack(side=tk.LEFT)
                cb = ttk.Combobox(
                    r,
                    textvariable=var,
                    values=F_KEYS_LIST,
                    state="readonly",
                    width=16,
                )
                cb.pack(side=tk.LEFT)
                cb.bind("<<ComboboxSelected>>", lambda _e: self._apply_language())

            r_panic = ttk.Frame(hk_box)
            r_panic.pack(fill=tk.X, pady=4)
            ttk.Label(
                r_panic, text="Аварийная остановка (Emergency Panic Stop):", width=44
            ).pack(side=tk.LEFT)
            ttk.Entry(r_panic, textvariable=self.hk_panic_var, width=18, state="readonly").pack(
                side=tk.LEFT
            )

            self.chk_failsafe = ttk.Checkbutton(
                hk_box,
                text="Экстренная остановка при уводе мыши в левый верхний угол (X=0, Y=0 Fail-Safe)",
                variable=self.failsafe_corner_var,
            )
            self.chk_failsafe.pack(anchor="w", pady=(8, 0))

            sched_box = ttk.LabelFrame(
                self.tab_hotkeys, text="Таймер и Планировщик запуска (Scheduler)", padding=12
            )
            sched_box.pack(fill=tk.X, pady=(0, 10))

            r_cd = ttk.Frame(sched_box)
            r_cd.pack(fill=tk.X, pady=4)
            ttk.Label(
                r_cd, text="Задержка перед стартом повтора (Countdown, сек):", width=44
            ).pack(side=tk.LEFT)
            ttk.Spinbox(
                r_cd, from_=0, to=3600, width=10, textvariable=self.countdown_sec_var
            ).pack(side=tk.LEFT)

            r_sc = ttk.Frame(sched_box)
            r_sc.pack(fill=tk.X, pady=4)
            ttk.Checkbutton(
                r_sc,
                text="Запустить точно по времени (ЧЧ:ММ:СС):",
                variable=self.use_schedule_var,
                width=42,
            ).pack(side=tk.LEFT)
            ttk.Entry(r_sc, textvariable=self.schedule_time_var, width=12).pack(side=tk.LEFT)

        def _build_tab_stats(self):
            cards = ttk.Frame(self.tab_stats)
            cards.pack(fill=tk.X, pady=(0, 8))

            self.stat_labels: Dict[str, ttk.Label] = {}
            items = [
                ("cycles_completed", "Выполнено циклов"),
                ("clicks_sent", "Отправлено кликов"),
                ("keys_sent", "Нажатий клавиш"),
                ("macros_recorded", "Записано макросов"),
            ]
            for key, title in items:
                box = ttk.LabelFrame(cards, text=title, padding=8)
                box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)
                lbl = ttk.Label(box, text="0", font=("Segoe UI", 14, "bold"), foreground="#005fb8")
                lbl.pack(anchor="center")
                self.stat_labels[key] = lbl

            log_box = ttk.LabelFrame(self.tab_stats, text="Журнал активности (Activity Log)", padding=6)
            log_box.pack(fill=tk.BOTH, expand=True)

            self.log_text = tk.Text(
                log_box, height=14, font=("Consolas", 9), state=tk.DISABLED, bg="#f9fafb"
            )
            self.log_text.pack(fill=tk.BOTH, expand=True)
            for line in self.engine.logs:
                self._append_log_line(line)

        def _append_log_line(self, line: str):
            if not hasattr(self, "log_text"):
                return
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, line + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        def _on_engine_log(self, line: str):
            self.root.after(0, lambda: self._append_log_line(line))
            self.root.after(0, self._refresh_stat_cards)

        def _refresh_stat_cards(self):
            for k, lbl in self.stat_labels.items():
                lbl.config(text=str(self.engine.stats.get(k, 0)))

        def _apply_language(self):
            t = TRANSLATIONS[self.lang]
            rec_hk = self.hk_record_var.get()
            rep_hk = self.hk_repeat_var.get()
            pick_hk = self.hk_pick_var.get()

            self.root.title(t["title"])

            self.notebook.tab(0, text=t["tab_main"])
            self.notebook.tab(1, text=t["tab_editor"])
            self.notebook.tab(2, text=t["tab_hotkeys"])
            self.notebook.tab(3, text=t["tab_stats"])

            self.menubar.entryconfigure(1, label=t["menu_file"])
            self.menubar.entryconfigure(2, label=t["menu_edit"])
            self.menubar.entryconfigure(3, label=t["menu_tools"])
            self.menubar.entryconfigure(4, label=t["menu_help"])

            self.file_menu.entryconfigure(0, label=t["file_new"])
            self.file_menu.entryconfigure(1, label=t["file_open"])
            self.file_menu.entryconfigure(2, label=t["file_save_as"])
            self.file_menu.entryconfigure(4, label=t["file_exit"])

            self.edit_menu.entryconfigure(0, label=t["edit_rename"])
            self.edit_menu.entryconfigure(1, label=t["edit_duplicate"])
            self.edit_menu.entryconfigure(2, label=t["edit_delete"])

            self.tools_menu.entryconfigure(0, label=t["tools_lang"])
            self.tools_menu.entryconfigure(1, label=t["tools_open_folder"])
            self.tools_menu.entryconfigure(2, label=t["tools_install_pynput"])

            self.help_menu.entryconfigure(0, label=t["help_hotkeys"])
            self.help_menu.entryconfigure(1, label=t["help_about"])

            self.rb_once.config(text=t["repeat_once"])
            self.rb_times.config(text=t["repeat_times"])
            self.lbl_times.config(text=t["times_label"])
            self.rb_for.config(text=t["repeat_for"])
            self.lbl_for_time.config(text=t["time_label"])
            self.rb_inf.config(text=t["repeat_infinite"].format(rep_hk=rep_hk))

            self.lbl_post_action.config(text=t["shutdown_after"])
            self.chk_no_activate.config(text=t["do_not_activate"])
            self.chk_minimize.config(text=t["minimize_on_run"])
            self.chk_humanize.config(text=t["humanize_mouse"])

            self.grp_delay.config(text=t["delay_group"])
            self.chk_set_delay.config(text=t["set_delay"])
            self.lbl_delay_h.config(text=t["hour_lbl"])
            self.lbl_delay_m.config(text=t["min_lbl"])
            self.lbl_delay_s.config(text=t["sec_lbl"])
            self.chk_random_delay.config(text=t["random_delay"])

            self.grp_speed.config(text=t["speed_group"])
            self.lbl_slow.config(text=t["slow"])
            self.lbl_normal.config(text=t["normal"])
            self.lbl_fast.config(text=t["fast"])

            self.btn_record.config(
                text=(
                    t["btn_stop_record"].format(hk=rec_hk)
                    if self.engine.is_recording
                    else t["btn_record"].format(hk=rec_hk)
                )
            )
            self.btn_repeat.config(
                text=(
                    t["btn_stop_repeat"].format(hk=rep_hk)
                    if self.engine.is_repeating
                    else t["btn_repeat"].format(hk=rep_hk)
                )
            )

            self.tree.heading("name", text=t["col_name"], anchor="w")
            self.tree.heading("events", text=t["col_events"], anchor="center")
            self.tree.heading("duration", text=t["col_duration"], anchor="center")
            self.tree.heading("location", text=t["col_location"], anchor="w")

            if not self.engine.is_recording and not self.engine.is_repeating:
                self.status_var.set(
                    t["status_ready"].format(
                        backend=self.engine.backend.backend_name,
                        rec_hk=rec_hk,
                        rep_hk=rep_hk,
                        pick_hk=pick_hk,
                    )
                )

        def toggle_language(self):
            self.lang = "en" if self.lang == "ru" else "ru"
            self._apply_language()

        def _update_states(self):
            mode = self.repeat_mode_var.get()
            self.spin_times.config(state="normal" if mode == "times" else "disabled")
            self.spin_for_val.config(state="normal" if mode == "for" else "disabled")
            self.combo_for_unit.config(state="readonly" if mode == "for" else "disabled")

            delay_state = "normal" if self.set_delay_var.get() else "disabled"
            self.spin_delay_h.config(state=delay_state)
            self.spin_delay_m.config(state=delay_state)
            self.spin_delay_s.config(state=delay_state)
            self.chk_random_delay.config(state=delay_state)

        def _refresh_records_table(self):
            for item in self.tree.get_children():
                self.tree.delete(item)
            macros = self.engine.list_macros()
            for m in macros:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(m["name"], m["events_count"], m["duration"], m["path"]),
                )
            children = self.tree.get_children()
            if children:
                self.tree.selection_set(children[-1])
                self._on_record_selected()

        def _on_record_selected(self, _event=None):
            sel = self.tree.selection()
            if not sel:
                return
            vals = self.tree.item(sel[0], "values")
            if len(vals) >= 4:
                self._load_steps_into_editor(Path(vals[3]))

        def _start_cursor_tracker(self):
            def update_pos():
                try:
                    x, y = self.engine.backend.get_mouse_pos()
                    self.live_coords_var.set(f"X: {x}, Y: {y}")
                except Exception:
                    pass
                self.root.after(100, update_pos)

            self.root.after(100, update_pos)

        def _get_excluded_hotkey_names(self) -> set:
            return {
                self.hk_record_var.get().lower(),
                self.hk_repeat_var.get().lower(),
                self.hk_pause_rec_var.get().lower(),
                self.hk_pick_var.get().lower(),
                "esc",
                "f12",
            }

        def _start_global_hotkeys(self):
            if PYNPUT_AVAILABLE:
                def on_press(key):
                    k_name = key.name.lower() if isinstance(key, Key) else ""
                    if not k_name:
                        return
                    if k_name == self.hk_record_var.get().lower():
                        self.root.after(0, self.toggle_record)
                    elif k_name == self.hk_repeat_var.get().lower():
                        self.root.after(0, self.toggle_repeat)
                    elif k_name == self.hk_pick_var.get().lower():
                        self.root.after(0, self.capture_cursor_to_editor)
                    elif k_name in ("esc", "f12") and (
                        self.engine.is_repeating or self.engine.is_recording
                    ):
                        self.engine.stop_event.set()
                        if self.engine.is_recording:
                            self.root.after(0, self.stop_recording)

                self.hotkey_listener = pynput_kb.Listener(on_press=on_press)
                self.hotkey_listener.daemon = True
                self.hotkey_listener.start()
            elif "windows" in platform.system().lower():
                def win32_hotkey_poller():
                    user32 = ctypes.windll.user32
                    prev_state: Dict[str, bool] = {}
                    while True:
                        rec_k = self.hk_record_var.get().lower()
                        rep_k = self.hk_repeat_var.get().lower()
                        pick_k = self.hk_pick_var.get().lower()

                        for k_name, action in [
                            (rec_k, self.toggle_record),
                            (rep_k, self.toggle_repeat),
                            (pick_k, self.capture_cursor_to_editor),
                        ]:
                            vk = VK_MAP_WIN.get(k_name, 0)
                            if vk:
                                is_down = (user32.GetAsyncKeyState(vk) & 0x8000) != 0
                                if is_down and not prev_state.get(k_name, False):
                                    self.root.after(0, action)
                                prev_state[k_name] = is_down

                        esc_down = (user32.GetAsyncKeyState(0x1B) & 0x8000) != 0
                        f12_down = (user32.GetAsyncKeyState(0x7B) & 0x8000) != 0
                        if (esc_down or f12_down) and (
                            self.engine.is_repeating or self.engine.is_recording
                        ):
                            self.engine.stop_event.set()
                            if self.engine.is_recording:
                                self.root.after(0, self.stop_recording)

                        time.sleep(0.03)

                t = threading.Thread(target=win32_hotkey_poller, daemon=True)
                t.start()

        def toggle_record(self):
            if self.engine.is_repeating:
                return
            if self.engine.is_recording:
                self.stop_recording()
            else:
                self.start_recording()

        def start_recording(self):
            self.engine.is_recording = True
            self.engine.recorded_events = []
            self.engine.record_start_time = time.perf_counter()
            self.engine.last_move_time = 0.0

            if self.minimize_on_run_var.get():
                self.root.iconify()

            t = TRANSLATIONS[self.lang]
            rec_hk = self.hk_record_var.get()
            self.btn_record.config(text=t["btn_stop_record"].format(hk=rec_hk), bg="#ffcccc")
            self.btn_repeat.config(state=tk.DISABLED)
            self.status_var.set(t["status_recording"].format(rec_hk=rec_hk, count=0))
            self.engine.log(f"Начата запись (нажмите {rec_hk} для остановки)...")

            def now_dt() -> float:
                return round(time.perf_counter() - self.engine.record_start_time, 4)

            excluded_keys = self._get_excluded_hotkey_names()

            if PYNPUT_AVAILABLE:
                def on_move(x, y):
                    if not self.engine.is_recording:
                        return
                    t_cur = time.perf_counter()
                    if t_cur - self.engine.last_move_time >= 0.012:
                        self.engine.last_move_time = t_cur
                        self.engine.recorded_events.append(
                            {"type": "mouse_move", "time": now_dt(), "x": int(x), "y": int(y)}
                        )

                def on_click(x, y, button, pressed):
                    if not self.engine.is_recording:
                        return
                    self.engine.recorded_events.append(
                        {
                            "type": "mouse_click",
                            "time": now_dt(),
                            "x": int(x),
                            "y": int(y),
                            "button": button.name,
                            "pressed": bool(pressed),
                        }
                    )
                    self._update_record_status()

                def on_scroll(x, y, dx, dy):
                    if not self.engine.is_recording:
                        return
                    self.engine.recorded_events.append(
                        {
                            "type": "mouse_scroll",
                            "time": now_dt(),
                            "x": int(x),
                            "y": int(y),
                            "dx": int(dx),
                            "dy": int(dy),
                        }
                    )

                def on_key_press(key):
                    if not self.engine.is_recording:
                        return
                    k_str = key.name if isinstance(key, Key) else (key.char or str(key))
                    if str(k_str).lower() in excluded_keys:
                        return
                    self.engine.recorded_events.append(
                        {"type": "key_press", "time": now_dt(), "key": k_str}
                    )
                    self._update_record_status()

                def on_key_release(key):
                    if not self.engine.is_recording:
                        return
                    k_str = key.name if isinstance(key, Key) else (key.char or str(key))
                    if str(k_str).lower() in excluded_keys:
                        return
                    self.engine.recorded_events.append(
                        {"type": "key_release", "time": now_dt(), "key": k_str}
                    )

                self.mouse_listener = pynput_mouse.Listener(
                    on_move=on_move, on_click=on_click, on_scroll=on_scroll
                )
                self.kb_listener = pynput_kb.Listener(
                    on_press=on_key_press, on_release=on_key_release
                )
                self.mouse_listener.start()
                self.kb_listener.start()
            else:
                def native_record_loop():
                    last_x, last_y = self.engine.backend.get_mouse_pos()
                    prev_lmb, prev_rmb = False, False
                    user32 = ctypes.windll.user32 if "windows" in platform.system().lower() else None

                    while self.engine.is_recording:
                        x, y = self.engine.backend.get_mouse_pos()
                        if (x, y) != (last_x, last_y):
                            self.engine.recorded_events.append(
                                {"type": "mouse_move", "time": now_dt(), "x": x, "y": y}
                            )
                            last_x, last_y = x, y

                        if user32:
                            lmb = (user32.GetAsyncKeyState(0x01) & 0x8000) != 0
                            rmb = (user32.GetAsyncKeyState(0x02) & 0x8000) != 0
                            if lmb != prev_lmb:
                                self.engine.recorded_events.append(
                                    {
                                        "type": "mouse_click",
                                        "time": now_dt(),
                                        "x": x,
                                        "y": y,
                                        "button": "left",
                                        "pressed": lmb,
                                    }
                                )
                                prev_lmb = lmb
                                self._update_record_status()
                            if rmb != prev_rmb:
                                self.engine.recorded_events.append(
                                    {
                                        "type": "mouse_click",
                                        "time": now_dt(),
                                        "x": x,
                                        "y": y,
                                        "button": "right",
                                        "pressed": rmb,
                                    }
                                )
                                prev_rmb = rmb
                                self._update_record_status()
                        time.sleep(0.015)

                self.polling_thread = threading.Thread(target=native_record_loop, daemon=True)
                self.polling_thread.start()

        def _update_record_status(self):
            t = TRANSLATIONS[self.lang]
            rec_hk = self.hk_record_var.get()
            cnt = len(self.engine.recorded_events)
            self.root.after(
                0,
                lambda: self.status_var.set(
                    t["status_recording"].format(rec_hk=rec_hk, count=cnt)
                ),
            )

        def stop_recording(self):
            if not self.engine.is_recording:
                return
            self.engine.is_recording = False
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            if self.kb_listener:
                self.kb_listener.stop()
                self.kb_listener = None

            self.root.deiconify()
            t = TRANSLATIONS[self.lang]
            rec_hk = self.hk_record_var.get()
            self.btn_record.config(text=t["btn_record"].format(hk=rec_hk), bg="#f8f9fa")
            self.btn_repeat.config(state=tk.NORMAL)

            if self.engine.recorded_events:
                save_path = self.engine.next_record_path()
                self.engine.save_macro_file(save_path, self.engine.recorded_events)
                self.engine.stats["macros_recorded"] += 1
                self.engine.log(
                    f"Сохранена запись {save_path.name} ({len(self.engine.recorded_events)} событий)"
                )
                self._refresh_records_table()

            self.status_var.set(
                t["status_stopped"].format(count=len(self.engine.recorded_events))
            )

        def toggle_repeat(self):
            if self.engine.is_recording:
                return
            if self.engine.is_repeating:
                self.engine.stop_event.set()
            else:
                self.start_repeating()

        def _get_speed_multiplier(self) -> float:
            val = self.speed_slider_var.get()
            return float(2.0 ** (val / 2.0))

        def _get_between_repeat_delay(self) -> float:
            if not self.set_delay_var.get():
                return 0.0
            total_sec = (
                self.delay_hour_var.get() * 3600
                + self.delay_min_var.get() * 60
                + self.delay_sec_var.get()
            )
            if total_sec <= 0:
                return 0.0
            if self.random_delay_var.get():
                return random.uniform(0.0, float(total_sec))
            return float(total_sec)

        def start_repeating(self):
            sel = self.tree.selection()
            if not sel:
                messagebox.showwarning("MacroStudio", "Выберите запись в таблице!")
                return
            vals = self.tree.item(sel[0], "values")
            rec_name, rec_path = vals[0], Path(vals[3])
            events = self.engine.load_macro_file(rec_path)
            if not events:
                messagebox.showwarning("MacroStudio", "Выбранная запись пуста!")
                return

            self.engine.is_repeating = True
            self.engine.stop_event.clear()

            if self.minimize_on_run_var.get():
                self.root.iconify()

            t = TRANSLATIONS[self.lang]
            rep_hk = self.hk_repeat_var.get()
            self.btn_repeat.config(text=t["btn_stop_repeat"].format(hk=rep_hk), bg="#cfe2ff")
            self.btn_record.config(state=tk.DISABLED)

            mode = self.repeat_mode_var.get()
            max_times = max(1, self.repeat_times_var.get())
            duration_val = max(1, self.repeat_for_val_var.get())
            unit = self.repeat_for_unit_var.get()
            unit_mult = {"hour": 3600, "minute": 60, "second": 1}.get(unit, 1)
            max_duration_sec = duration_val * unit_mult

            thread = threading.Thread(
                target=self._repeat_worker,
                args=(rec_name, events, mode, max_times, max_duration_sec),
                daemon=True,
            )
            thread.start()

        def _sleep_interruptible(self, seconds: float) -> bool:
            end_time = time.perf_counter() + seconds
            while time.perf_counter() < end_time:
                if self.engine.stop_event.is_set():
                    return False
                if self.failsafe_corner_var.get():
                    mx, my = self.engine.backend.get_mouse_pos()
                    if mx <= 2 and my <= 2:
                        self.engine.log("Аварийная остановка Fail-Safe (курсор в углу 0,0)!")
                        self.engine.stop_event.set()
                        return False
                remaining = end_time - time.perf_counter()
                time.sleep(min(0.01, max(0.0, remaining)))
            return not self.engine.stop_event.is_set()

        def _repeat_worker(
            self,
            rec_name: str,
            events: List[Dict[str, Any]],
            mode: str,
            max_times: int,
            max_duration_sec: float,
        ):
            t = TRANSLATIONS[self.lang]

            cd = self.countdown_sec_var.get()
            if cd > 0:
                self.engine.log(f"Обратный отсчет перед стартом: {cd} сек...")
                if not self._sleep_interruptible(float(cd)):
                    self.root.after(0, lambda: self._on_repeat_finished(False))
                    return

            start_wall = time.perf_counter()
            cycle = 0
            total_steps = len(events)

            try:
                while not self.engine.stop_event.is_set():
                    cycle += 1
                    prev_event_time = 0.0

                    for idx, ev in enumerate(events, start=1):
                        if self.engine.stop_event.is_set():
                            break
                        if (
                            mode == "for"
                            and (time.perf_counter() - start_wall) >= max_duration_sec
                        ):
                            self.engine.stop_event.set()
                            break

                        self.root.after(
                            0,
                            lambda c=cycle, s=idx: self.status_var.set(
                                t["status_repeating"].format(
                                    name=rec_name, cycle=c, step=s, total=total_steps
                                )
                            ),
                        )

                        ev_time = float(ev.get("time", 0.0))
                        dt = max(0.0, ev_time - prev_event_time)
                        prev_event_time = ev_time

                        speed = self._get_speed_multiplier()
                        scaled_dt = dt / speed if speed > 0 else dt
                        if scaled_dt > 0 and not self._sleep_interruptible(scaled_dt):
                            break

                        ev_type = ev.get("type")
                        x = int(ev.get("x", 0))
                        y = int(ev.get("y", 0))
                        if self.humanize_mouse_var.get() and ev_type in ("mouse_move", "mouse_click"):
                            x += random.randint(-2, 2)
                            y += random.randint(-2, 2)

                        if ev_type == "mouse_move":
                            self.engine.backend.move_mouse(x, y)
                        elif ev_type == "mouse_click":
                            btn = ev.get("button", "left")
                            pressed = ev.get("pressed", True)
                            self.engine.backend.mouse_button(x, y, btn, pressed)
                            if pressed:
                                self.engine.stats["clicks_sent"] += 1
                        elif ev_type == "mouse_scroll":
                            self.engine.backend.mouse_scroll(
                                x, y, int(ev.get("dx", 0)), int(ev.get("dy", 0))
                            )
                        elif ev_type == "key_press":
                            k = ev.get("key", "")
                            if isinstance(k, dict):
                                k = k.get("value", "")
                            self.engine.backend.key_event(str(k), True)
                            self.engine.stats["keys_sent"] += 1
                        elif ev_type == "key_release":
                            k = ev.get("key", "")
                            if isinstance(k, dict):
                                k = k.get("value", "")
                            self.engine.backend.key_event(str(k), False)
                        elif ev_type == "key_tap":
                            k = str(ev.get("key", "enter"))
                            self.engine.backend.key_event(k, True)
                            time.sleep(0.02)
                            self.engine.backend.key_event(k, False)
                            self.engine.stats["keys_sent"] += 1
                        elif ev_type == "text_type":
                            txt = str(ev.get("text", ""))
                            self.engine.backend.type_text(txt)
                            self.engine.stats["keys_sent"] += len(txt)
                        elif ev_type == "wait":
                            dur = float(ev.get("duration", 1.0)) / speed
                            if not self._sleep_interruptible(dur):
                                break
                        elif ev_type == "run_cmd":
                            cmd_str = str(ev.get("cmd", ""))
                            if cmd_str:
                                subprocess.Popen(cmd_str, shell=True)

                    if self.engine.stop_event.is_set():
                        break
                    self.engine.stats["cycles_completed"] += 1
                    self.root.after(0, self._refresh_stat_cards)

                    if mode == "once":
                        break
                    if mode == "times" and cycle >= max_times:
                        break
                    if (
                        mode == "for"
                        and (time.perf_counter() - start_wall) >= max_duration_sec
                    ):
                        break

                    delay_sec = self._get_between_repeat_delay()
                    if delay_sec > 0:
                        self.root.after(
                            0,
                            lambda d=delay_sec: self.status_var.set(
                                t["status_delay"].format(sec=d)
                            ),
                        )
                        if not self._sleep_interruptible(delay_sec):
                            break
            finally:
                completed_naturally = not self.engine.stop_event.is_set()
                self.root.after(0, lambda: self._on_repeat_finished(completed_naturally))

        def _on_repeat_finished(self, completed_naturally: bool):
            self.engine.is_repeating = False
            t = TRANSLATIONS[self.lang]
            rec_hk = self.hk_record_var.get()
            rep_hk = self.hk_repeat_var.get()
            pick_hk = self.hk_pick_var.get()
            self.btn_repeat.config(text=t["btn_repeat"].format(hk=rep_hk), bg="#f8f9fa")
            self.btn_record.config(state=tk.NORMAL)
            self.status_var.set(
                t["status_ready"].format(
                    backend=self.engine.backend.backend_name,
                    rec_hk=rec_hk,
                    rep_hk=rep_hk,
                    pick_hk=pick_hk,
                )
            )
            self.engine.log("Воспроизведение завершено.")

            if not self.do_not_activate_var.get():
                self.root.deiconify()
                self.root.lift()

            if completed_naturally:
                self._execute_post_action()

        def _execute_post_action(self):
            act = self.post_action_var.get().split()[0]
            sys_name = platform.system().lower()
            if act == "none":
                return
            if act == "exit":
                self.on_close()
            elif act == "shutdown":
                if "windows" in sys_name:
                    subprocess.run(["shutdown", "/s", "/t", "5"], check=False)
                else:
                    subprocess.run(["shutdown", "-h", "+1"], check=False)
            elif act == "lock":
                if "windows" in sys_name:
                    ctypes.windll.user32.LockWorkStation()
            elif act == "sleep":
                if "windows" in sys_name:
                    subprocess.run(
                        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=False
                    )

        def _load_steps_into_editor(self, path: Path):
            self.current_editing_path = path
            self.current_steps = self.engine.load_macro_file(path)
            self.lbl_editing_file.config(text=f"Макрос: {path.name} ({len(self.current_steps)} шагов)")
            self._render_steps_tree()

        def _render_steps_tree(self):
            for item in self.steps_tree.get_children():
                self.steps_tree.delete(item)
            for i, ev in enumerate(self.current_steps, start=1):
                ev_type = ev.get("type", "")
                coords = f"{ev.get('x', '-')}, {ev.get('y', '-')}" if "x" in ev else "-"
                param = (
                    ev.get("button")
                    or ev.get("key")
                    or ev.get("text")
                    or ev.get("duration")
                    or ev.get("cmd")
                    or ""
                )
                if isinstance(param, dict):
                    param = param.get("value", "")
                comment = ev.get("comment", "")
                self.steps_tree.insert(
                    "",
                    tk.END,
                    values=(i, ev.get("time", 0.0), ev_type, coords, str(param), comment),
                )

        def open_selected_in_editor(self):
            sel = self.tree.selection()
            if not sel:
                return
            vals = self.tree.item(sel[0], "values")
            self._load_steps_into_editor(Path(vals[3]))
            self.notebook.select(1)

        def capture_cursor_to_editor(self):
            x, y = self.engine.backend.get_mouse_pos()
            self.new_step_x.set(x)
            self.new_step_y.set(y)
            self.engine.log(f"Захвачены координаты курсора: X={x}, Y={y}")

        def add_manual_step(self):
            if not self.current_editing_path:
                self.create_blank_record()
            last_t = float(self.current_steps[-1].get("time", 0.0)) if self.current_steps else 0.0
            new_t = round(last_t + 0.25, 3)
            stype = self.new_step_type.get()
            x, y = self.new_step_x.get(), self.new_step_y.get()
            param = self.new_step_param.get()

            if stype == "mouse_click":
                self.current_steps.append(
                    {
                        "type": "mouse_click",
                        "time": new_t,
                        "x": x,
                        "y": y,
                        "button": param or "left",
                        "pressed": True,
                        "comment": f"Клик ({param or 'left'})",
                    }
                )
                self.current_steps.append(
                    {
                        "type": "mouse_click",
                        "time": round(new_t + 0.05, 3),
                        "x": x,
                        "y": y,
                        "button": param or "left",
                        "pressed": False,
                        "comment": "Отпускание кнопки",
                    }
                )
            elif stype == "mouse_move":
                self.current_steps.append(
                    {"type": "mouse_move", "time": new_t, "x": x, "y": y, "comment": "Перемещение"}
                )
            elif stype == "text_type":
                self.current_steps.append(
                    {"type": "text_type", "time": new_t, "text": param, "comment": "Ввод текста"}
                )
            elif stype == "key_tap":
                self.current_steps.append(
                    {"type": "key_tap", "time": new_t, "key": param or "enter", "comment": "Нажатие клавиши"}
                )
            elif stype == "wait":
                try:
                    dur = float(param)
                except ValueError:
                    dur = 1.0
                self.current_steps.append(
                    {"type": "wait", "time": new_t, "duration": dur, "comment": f"Пауза {dur}с"}
                )
            elif stype == "run_cmd":
                self.current_steps.append(
                    {"type": "run_cmd", "time": new_t, "cmd": param, "comment": "Запуск команды"}
                )
            self._render_steps_tree()

        def compress_step_delays(self):
            if not self.current_steps:
                return
            accumulated = 0.0
            prev_orig = 0.0
            for ev in self.current_steps:
                orig_t = float(ev.get("time", 0.0))
                dt = max(0.0, orig_t - prev_orig)
                prev_orig = orig_t
                if dt > 1.0:
                    dt = 0.5
                accumulated = round(accumulated + dt, 4)
                ev["time"] = accumulated
            self._render_steps_tree()
            self.engine.log("Длинные паузы в макросе сжаты до 0.5 сек.")

        def delete_selected_step(self):
            sel = self.steps_tree.selection()
            if not sel:
                return
            idx = int(self.steps_tree.item(sel[0], "values")[0]) - 1
            if 0 <= idx < len(self.current_steps):
                self.current_steps.pop(idx)
                self._render_steps_tree()

        def save_editor_steps(self):
            if not self.current_editing_path:
                return
            self.engine.save_macro_file(self.current_editing_path, self.current_steps)
            self.engine.log(f"Сохранен макрос {self.current_editing_path.name}")
            self._refresh_records_table()

        def create_blank_record(self):
            p = self.engine.next_record_path()
            self.engine.save_macro_file(p, [])
            self._refresh_records_table()
            self._load_steps_into_editor(p)

        def import_record(self):
            fpath = filedialog.askopenfilename(
                title="Import Record",
                initialdir=str(self.engine.records_dir),
                filetypes=[("Macro Records (*.rsmk;*.json)", "*.rsmk *.json"), ("All Files", "*.*")],
            )
            if fpath:
                src = Path(fpath)
                dst = self.engine.records_dir / src.name
                if src.resolve() != dst.resolve():
                    shutil.copy2(src, dst)
                self._refresh_records_table()

        def export_record(self):
            sel = self.tree.selection()
            if not sel:
                return
            vals = self.tree.item(sel[0], "values")
            rec_name, rec_path = vals[0], vals[3]
            dest = filedialog.asksaveasfilename(
                title="Export Record",
                initialfile=f"{rec_name}.rsmk",
                defaultextension=".rsmk",
                filetypes=[("Macro Record (*.rsmk)", "*.rsmk"), ("JSON (*.json)", "*.json")],
            )
            if dest and os.path.exists(rec_path):
                shutil.copy2(rec_path, dest)

        def rename_selected_record(self):
            sel = self.tree.selection()
            if not sel:
                return
            vals = self.tree.item(sel[0], "values")
            old_name, old_path = vals[0], Path(vals[3])
            new_name = simpledialog.askstring(
                "Rename Record", "Новое имя записи:", initialvalue=old_name
            )
            if not new_name or new_name.strip() == old_name:
                return
            new_p = old_path.with_name(f"{new_name.strip()}{old_path.suffix}")
            try:
                old_path.rename(new_p)
                self._refresh_records_table()
            except OSError as exc:
                messagebox.showerror("Error", str(exc))

        def duplicate_selected_record(self):
            sel = self.tree.selection()
            if not sel:
                return
            vals = self.tree.item(sel[0], "values")
            old_path = Path(vals[3])
            new_p = self.engine.next_record_path()
            if old_path.exists():
                shutil.copy2(old_path, new_p)
                self._refresh_records_table()

        def delete_selected_record(self):
            sel = self.tree.selection()
            if not sel:
                return
            vals = self.tree.item(sel[0], "values")
            rec_name, rec_path = vals[0], vals[3]
            if messagebox.askyesno("Delete Record", f"Удалить запись '{rec_name}'?"):
                try:
                    os.remove(rec_path)
                except OSError:
                    pass
                self._refresh_records_table()

        def open_records_folder(self):
            folder = str(self.engine.records_dir)
            sys_name = platform.system().lower()
            try:
                if "windows" in sys_name:
                    os.startfile(folder)
                elif "darwin" in sys_name:
                    subprocess.Popen(["open", folder])
                else:
                    subprocess.Popen(["xdg-open", folder])
            except Exception:
                messagebox.showinfo("Records Folder", folder)

        def install_pynput_gui(self):
            if messagebox.askyesno(
                "Установка pynput",
                "Установить или обновить пакет 'pynput' через pip для расширенных глобальных хуков?",
            ):
                subprocess.Popen([sys.executable, "-m", "pip", "install", "pynput"])

        def show_help(self):
            rec_hk = self.hk_record_var.get()
            rep_hk = self.hk_repeat_var.get()
            pick_hk = self.hk_pick_var.get()
            msg = (
                "Горячие клавиши:\n"
                f"• {rec_hk} — Старт / Стоп записи\n"
                f"• {rep_hk} — Старт / Стоп повтора\n"
                f"• {pick_hk} — Захватить текущие координаты курсора X, Y в редактор\n"
                "• Esc или F12 (либо увод мыши в угол 0,0) — Аварийная остановка\n\n"
                "Вы можете сменить любую F-клавишу (F1–F12) во вкладке «⌨ Горячие клавиши и Таймер».\n\n"
                f"Активный системный движок:\n{self.engine.backend.backend_name}"
            )
            messagebox.showinfo("Справка / Hotkeys", msg)

        def show_about(self):
            messagebox.showinfo(
                "О программе",
                "MacroStudio Pro v1.0.0 — Mouse and Keyboard Recorder\n"
                "Кроссплатформенный комплекс записи, редактирования и автоматического воспроизведения действий мыши и клавиатуры.\n"
                "Лицензия: CC0 1.0 Universal (Public Domain).",
            )

        def on_close(self):
            self.engine.stop_event.set()
            if self.engine.is_recording:
                self.stop_recording()
            if self.hotkey_listener:
                self.hotkey_listener.stop()
            self.root.destroy()


WEB_UI_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>MacroStudio Pro — Web Control Panel</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f3f4f6; margin: 0; padding: 24px; color: #1f2937; }
  .card { max-width: 760px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); padding: 24px; }
  h1 { margin-top: 0; font-size: 20px; display: flex; justify-content: space-between; align-items: center; }
  .badge { font-size: 12px; background: #dbeafe; color: #1d4ed8; padding: 4px 10px; border-radius: 999px; }
  .grid { display: grid; grid-template-columns: 1fr 200px; gap: 16px; margin-bottom: 16px; }
  .btn { width: 100%; padding: 14px; font-size: 15px; font-weight: 600; border-radius: 8px; border: 1px solid #d1d5db; cursor: pointer; margin-bottom: 10px; }
  .btn-rec { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
  .btn-play { background: #dbeafe; color: #1e40af; border-color: #93c5fd; }
  table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }
  th { background: #f9fafb; }
</style>
</head>
<body>
<div class="card">
  <h1>MacroStudio Pro <span class="badge" id="backend">Ready</span></h1>
  <div class="grid">
    <div>
      <p><b>Режим повтора:</b></p>
      <label><input type="radio" name="mode" value="once"> Повторить один раз (Repeat once)</label><br><br>
      <label><input type="radio" name="mode" value="times" checked> Повторить <input type="number" id="times" value="30" style="width:60px"> раз(а)</label><br><br>
      <label><input type="radio" name="mode" value="for"> Повторять по таймеру (Repeat for 1 hour)</label>
    </div>
    <div>
      <button class="btn btn-rec" onclick="api('/api/record')">🔴 Запись (F9)</button>
      <button class="btn btn-play" onclick="api('/api/play')">▶ Повтор (F10)</button>
    </div>
  </div>
  <h3>Сохраненные макросы</h3>
  <table id="macros">
    <thead><tr><th>Имя записи</th><th>Событий</th><th>Длит. (с)</th><th>Путь</th></tr></thead>
    <tbody></tbody>
  </table>
</div>
<script>
async function refresh() {
  const res = await fetch('/api/status');
  const data = await res.json();
  document.getElementById('backend').innerText = data.backend;
  const tbody = document.querySelector('#macros tbody');
  tbody.innerHTML = data.macros.map(m => `<tr><td><b>${m.name}</b></td><td>${m.events_count}</td><td>${m.duration}</td><td>${m.path}</td></tr>`).join('');
}
async function api(path) { await fetch(path, {method:'POST'}); refresh(); }
refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""


def run_web_fallback(port: int = 8765):
    engine = MacroEngine()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.path == "/api/status":
                payload = {
                    "backend": engine.backend.backend_name,
                    "is_recording": engine.is_recording,
                    "is_repeating": engine.is_repeating,
                    "macros": engine.list_macros(),
                }
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)
                return

            body = WEB_UI_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

    url = f"http://127.0.0.1:{port}"
    print(f"MacroStudio Pro Web UI: {url}")
    webbrowser.open(url)
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    if "--web" in sys.argv or not TKINTER_AVAILABLE:
        run_web_fallback()
    else:
        root = tk.Tk()
        app = MacroStudioDesktopApp(root)
        root.mainloop()