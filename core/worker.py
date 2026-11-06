"""
Software Inc. Trainer - Non-Blocking Telemetry & Hotkey Worker Thread
Runs on a dedicated QThread to prevent Tkinter/Qt main-thread UI freezing.
"""

import time
import ctypes
from datetime import datetime
from typing import Dict, Any, List, Optional
from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker

from .memory import get_game_memory, GameMemory
from .constants import (
    PROCESS_ALL_ACCESS,
    VK_NUMPAD1,
    VK_NUMPAD2,
    VK_NUMPAD3,
    VK_NUMPAD4,
    VK_NUMPAD5,
    VK_NUMPAD6,
    VK_NUMPAD7,
    VK_NUMPAD8,
    VK_NUMPAD9,
)

u32 = ctypes.windll.user32


class TelemetryWorker(QThread):
    """
    Background worker that continuously:
    1. Monitors game process connection & pointer freshness
    2. Gathers company telemetry, employee data, projects, research, and patents
    3. Executes active cheats like 'Freeze Needs' without UI stutters
    4. Listens for global Windows hotkeys (Numpad 1-9)
    """

    # Signals
    connection_changed = Signal(bool, dict)
    telemetry_updated = Signal(dict)
    employees_updated = Signal(list)
    founder_updated = Signal(dict)
    projects_updated = Signal(list, list)  # active_projects, released_products
    research_updated = Signal(list, list)  # active_research, patents
    activity_logged = Signal(str, str, str)  # timestamp, level (INFO/SUCCESS/WARN/ERROR), message
    freeze_needs_changed = Signal(bool)
    turbo_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.game: GameMemory = get_game_memory()
        self._running: bool = True
        self._mutex = QMutex()

        # Cheats & worker states
        self.freeze_needs: bool = False
        self.turbo_active: bool = False
        self.enable_hotkeys: bool = True
        self._last_attached: bool = False
        self._poll_interval: float = 1.0  # seconds

        # Throttle heavy reads (employees/projects/research)
        self._heavy_poll_counter: int = 0

    def set_freeze_needs(self, active: bool):
        with QMutexLocker(self._mutex):
            self.freeze_needs = active
        self.freeze_needs_changed.emit(active)
        level = "SUCCESS" if active else "INFO"
        self.log(level, f"Freeze Needs {'ENABLED (Automatic full recovery)' if active else 'DISABLED'}")

    def set_turbo(self, active: bool):
        with QMutexLocker(self._mutex):
            self.turbo_active = active
        if self.game.is_attached():
            self.game.set_game_speed(5.0 if active else 1.0)
        self.turbo_changed.emit(active)
        self.log("SUCCESS" if active else "INFO", f"Simulation Turbo Speed set to {'5.0x' if active else '1.0x'}")

    def log(self, level: str, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        self.activity_logged.emit(now_str, level, message)

    def request_immediate_refresh(self):
        with QMutexLocker(self._mutex):
            self._heavy_poll_counter = 999

    def stop(self):
        with QMutexLocker(self._mutex):
            self._running = False
        self.wait(2000)

    def run(self):
        self.log("INFO", "Telemetry & Memory Worker started on dedicated background thread.")

        last_hotkey_check = 0.0

        while True:
            with QMutexLocker(self._mutex):
                if not self._running:
                    break
                freeze = self.freeze_needs
                hotkeys = self.enable_hotkeys

            now = time.time()

            # Hotkey polling (every 50ms)
            if hotkeys and (now - last_hotkey_check >= 0.05):
                last_hotkey_check = now
                self._check_hotkeys()

            try:
                # Connection & Telemetry polling
                is_attached = self.game.is_attached()
                if not is_attached:
                    # Try to attach
                    attached = self.game.attach()
                    if attached != self._last_attached:
                        self._last_attached = attached
                        if attached:
                            base = getattr(self.game, "base_address", self.game.mono_base) or 0
                            info = {
                                "pid": self.game.pid,
                                "process_name": "Software Inc.exe",
                                "arch": "x64 (Unity Mono)",
                                "base_addr": hex(base),
                            }
                            self.connection_changed.emit(True, info)
                            self.log("SUCCESS", f"Attached to Software Inc. (PID: {self.game.pid}, 64-bit Unity Mono)")
                        else:
                            self.connection_changed.emit(False, {})
                else:
                    if not self._last_attached:
                        self._last_attached = True
                        base = getattr(self.game, "base_address", self.game.mono_base) or 0
                        info = {
                            "pid": self.game.pid,
                            "process_name": "Software Inc.exe",
                            "arch": "x64 (Unity Mono)",
                            "base_addr": hex(base),
                        }
                        self.connection_changed.emit(True, info)

                    # Refresh pointers safely
                    self.game.refresh_pointers()

                    # Apply active freezes
                    if freeze:
                        self.game.max_all_employees_needs()

                    # Persistent research accelerator (adds extra progress each tick)
                    self.game.apply_research_boost()

                    # Collect high-frequency telemetry
                    money = self.game.get_money()
                    fans = self.game.get_fans()
                    rep = self.game.get_business_rep()
                    speed = self.game.get_game_speed()
                    date_time = self.game.get_date_time()
                    comp_name = self.game.get_company_name()

                    telemetry_snap = {
                        "company_name": comp_name,
                        "money": money,
                        "fans": fans,
                        "reputation": rep,
                        "speed": speed,
                        "date_str": date_time.get("date_str", "Unknown Date"),
                        "time_str": date_time.get("time_str", "10:00"),
                        "raw_date": date_time,
                    }
                    self.telemetry_updated.emit(telemetry_snap)

                    # Heavy poll for employees, projects, research (every 2 seconds)
                    self._heavy_poll_counter += 1
                    if self._heavy_poll_counter >= 2:
                        self._heavy_poll_counter = 0

                        # Personnel & Founder
                        emps = self.game.get_employees()
                        self.employees_updated.emit(emps)

                        founder = self.game.get_founder()
                        if founder:
                            self.founder_updated.emit(founder)

                        # Projects
                        active_projs = self.game.get_active_projects()
                        released_prods = self.game.get_released_products()
                        self.projects_updated.emit(active_projs, released_prods)

                        # Research & Patents
                        active_res = self.game.get_active_research()
                        patents = self.game.get_patents()
                        self.research_updated.emit(active_res, patents)

            except Exception as e:
                # Process may have closed, disconnected, or hit temporary memory violation
                if not self.game.is_attached():
                    if self._last_attached:
                        self._last_attached = False
                        self.connection_changed.emit(False, {})
                        self.log("WARN", f"Connection lost to Software Inc.: {e}")
                else:
                    self.log("WARN", f"Telemetry polling error: {e}")

            time.sleep(0.5)

    def _check_hotkeys(self):
        """Polls Win32 GetAsyncKeyState for Numpad 1-9 shortcuts."""
        if not self.game.is_attached():
            return

        try:
            if u32.GetAsyncKeyState(VK_NUMPAD1) & 0x8000:
                self.game.add_money(10_000_000.0)
                u32.MessageBeep(0)
                self.log("SUCCESS", "[Hotkey Numpad 1] Injected $10,000,000 into Corporate Treasury")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD2) & 0x8000:
                f = self.game.get_founder()
                if f and f.get("ptr"):
                    self.game.max_employee_needs(f["ptr"])
                    self.game.max_employee_skills(f["ptr"])
                    self.game.max_employee_specs(f["ptr"])
                    self.game.remove_employee_weaknesses(f["ptr"])
                    u32.MessageBeep(0)
                    self.log("SUCCESS", f"[Hotkey Numpad 2] Fully restored VIP Founder: '{f.get('name')}'")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD3) & 0x8000:
                cnt = self.game.max_all_employees_needs()
                u32.MessageBeep(0)
                self.log("SUCCESS", f"[Hotkey Numpad 3] Restored all needs for {cnt} employees to 100%")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD4) & 0x8000:
                cnt = self.game.max_all_employees_skills()
                u32.MessageBeep(0)
                self.log("SUCCESS", f"[Hotkey Numpad 4] Maxed out base skills for {cnt} employees")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD5) & 0x8000:
                self.game.set_business_rep(1.0)
                u32.MessageBeep(0)
                self.log("SUCCESS", "[Hotkey Numpad 5] Business Reputation elevated to 100%")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD6) & 0x8000:
                self.game.add_fans(50000)
                u32.MessageBeep(0)
                self.log("SUCCESS", "[Hotkey Numpad 6] Added +50,000 Company Fans")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD7) & 0x8000:
                self.game.unlock_furniture(True)
                u32.MessageBeep(0)
                self.log("SUCCESS", "[Hotkey Numpad 7] Unlocked all furniture and hardware catalog")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD8) & 0x8000:
                self.game.force_lights(True)
                u32.MessageBeep(0)
                self.log("SUCCESS", "[Hotkey Numpad 8] Forced all building lights ON")
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD9) & 0x8000:
                self.set_turbo(not self.turbo_active)
                u32.MessageBeep(0)
                time.sleep(0.25)
        except Exception:
            pass
