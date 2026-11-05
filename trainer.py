"""
Software Inc. - Memory Trainer
Native Windows 11 Fluent Design Application
Supports: All Software Inc. versions running with Unity Mono x64
Design: Windows App UI/UX (WinUI 3 / Fluent Design), Light & Dark mode support, Zero AI Slop.
Features:
  - Deep Personnel Editor: Granular Needs, Base Skills, Specialization Points (EXP),
    Subfield Star Ratings (0-3), and Weaknesses & Traits Management.
  - One-click Weakness Eraser & Master Traits Grant.
  - VIP Founder Profile with live vitals, role specializations, and godmode.
  - Treasury & Solvency Management (Cash injections, fans, reputation, bankruptcy clearing).
  - World & Rule Modifiers (Furniture unlock, force lighting, darkness shader, simulation speed).
  - Global In-Game Hotkeys (Numpad 1-9) with background listener.
"""

import os
import sys
import time
import ctypes
import threading
from ctypes import wintypes
import customtkinter as ctk

# Win32 Constants & Definitions
PROCESS_ALL_ACCESS = 0x1F0FFF
VK_NUMPAD1 = 0x61
VK_NUMPAD2 = 0x62
VK_NUMPAD3 = 0x63
VK_NUMPAD4 = 0x64
VK_NUMPAD5 = 0x65
VK_NUMPAD6 = 0x66
VK_NUMPAD7 = 0x67
VK_NUMPAD8 = 0x68
VK_NUMPAD9 = 0x69

k32 = ctypes.windll.kernel32
u32 = ctypes.windll.user32
psapi = ctypes.windll.psapi

psapi.EnumProcessModules.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_void_p),
    ctypes.c_uint,
    ctypes.POINTER(ctypes.c_uint)
]
psapi.GetModuleBaseNameA.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_char_p,
    ctypes.c_uint
]

k32.VirtualAllocEx.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_uint32,
]
k32.VirtualAllocEx.restype = ctypes.c_void_p


class GameMemory:
    """Handles external memory discovery and safe read/write operations for Software Inc."""

    ROLE_NAMES = ["Lead", "Code", "Design", "Art", "Service"]

    ROLE_ALL_SPECIALIZATIONS = {
        "Lead": ["Automation", "HR", "Multitasking", "Socialization"],
        "Code": ["2D", "3D", "Audio", "Hardware", "Network", "Sub-Genre", "System"],
        "Design": ["2D", "3D", "Audio", "Hardware", "Network", "Sub-Genre", "System"],
        "Art": ["2D", "3D", "Audio"],
        "Service": ["Accounting", "Law", "Marketing", "Support"],
    }

    # Complete enum mapping of all 33 traits in Software Inc.
    ALL_TRAITS = [
        ("FastLearner", 1 << 0, False),
        ("Independant", 1 << 1, False),
        ("BigBrain", 1 << 2, False),
        ("Humble", 1 << 3, False),
        ("Capacitor", 1 << 4, False),
        ("WalkItOff", 1 << 5, False),
        ("ThisIsFine", 1 << 6, False),
        ("NightOwl", 1 << 7, False),
        ("BornLeader", 1 << 8, False),
        ("FirmwareInc", 1 << 9, False),
        ("SuperFocus", 1 << 10, False),
        ("Unphased", 1 << 11, False),
        ("JustTheFlu", 1 << 12, False),
        ("Detached", 1 << 13, False),
        ("Stressed", 1 << 14, True),         # Weakness
        ("Hypochondriac", 1 << 15, True),    # Weakness
        ("SlowEater", 1 << 16, True),        # Weakness
        ("NervousBladder", 1 << 17, True),   # Weakness
        ("BumLeg", 1 << 18, True),           # Weakness
        ("Forgetful", 1 << 19, True),        # Weakness
        ("Cupholder", 1 << 20, False),
        ("NeatFreak", 1 << 21, False),
        ("SilentButDeadly", 1 << 22, False),
        ("Watch", 1 << 23, False),
        ("WalkInstead", 1 << 24, False),
        ("UnderTheWeather", 1 << 25, True),  # Weakness
        ("OldSole", 1 << 26, False),
        ("Sunshine", 1 << 27, False),
        ("Skyscraper", 1 << 28, False),
        ("RGBThumb", 1 << 29, False),
        ("FriendMaker", 1 << 30, False),
        ("Clean", 1 << 31, False),
        ("Claustrophobic", 1 << 32, True),   # Weakness
    ]

    BAD_TRAITS_MASK = 0x1020FC000  # Combined bitmask for all 8 weaknesses

    def __init__(self):
        self.pid = None
        self.handle = None
        self.mono_base = 0
        self.csharp_image = 0
        self.classes = {}

        # Cached pointers
        self.sdata_gs = 0
        self.instance_gs = 0
        self.company = 0
        self.sdata_cheats = 0
        self.actor_manager = 0
        self.time_of_day_instance = 0

        # Specialization insertion cache
        self._spec_metadata = {}
        self._v_buckets = 0
        self._v_entries = 0

    def is_attached(self) -> bool:
        if not self.handle or not self.pid:
            return False
        exit_code = ctypes.c_ulong()
        if k32.GetExitCodeProcess(self.handle, ctypes.byref(exit_code)):
            return exit_code.value == 259  # STILL_ACTIVE
        return False

    def close(self):
        if self.handle:
            k32.CloseHandle(self.handle)
            self.handle = None
        self.pid = None
        self._spec_metadata.clear()
        self._v_buckets = 0
        self._v_entries = 0

    def read_ptr(self, addr: int) -> int:
        if not addr or not self.handle:
            return 0
        b = (ctypes.c_ulonglong * 1)()
        if k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), b, 8, 0):
            return b[0]
        return 0

    def read_u32(self, addr: int) -> int:
        if not addr or not self.handle:
            return 0
        b = (ctypes.c_uint * 1)()
        if k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), b, 4, 0):
            return b[0]
        return 0

    def read_u8(self, addr: int) -> int:
        if not addr or not self.handle:
            return 0
        b = (ctypes.c_ubyte * 1)()
        if k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), b, 1, 0):
            return b[0]
        return 0

    def read_float(self, addr: int) -> float:
        if not addr or not self.handle:
            return 0.0
        b = (ctypes.c_float * 1)()
        if k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), b, 4, 0):
            return b[0]
        return 0.0

    def read_double(self, addr: int) -> float:
        if not addr or not self.handle:
            return 0.0
        b = (ctypes.c_double * 1)()
        if k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), b, 8, 0):
            return b[0]
        return 0.0

    def read_str_net(self, addr: int) -> str:
        if not addr or not self.handle:
            return ""
        length = self.read_u32(addr + 0x10)
        if length <= 0 or length > 500:
            return ""
        chars = (ctypes.c_wchar * length)()
        if k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr + 0x14), chars, length * 2, 0):
            return chars.value
        return ""

    def read_str_ascii(self, addr: int, maxlen: int = 64) -> str:
        if not addr or not self.handle:
            return ""
        b = (ctypes.c_char * maxlen)()
        if k32.ReadProcessMemory(self.handle, ctypes.c_void_p(addr), b, maxlen, 0):
            return b.value.decode("utf-8", "ignore")
        return ""

    def write_u8(self, addr: int, val: int) -> bool:
        if not addr or not self.handle:
            return False
        b = (ctypes.c_ubyte * 1)(val & 0xFF)
        return bool(k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), b, 1, 0))

    def write_u32(self, addr: int, val: int) -> bool:
        if not addr or not self.handle:
            return False
        b = (ctypes.c_uint * 1)(val & 0xFFFFFFFF)
        return bool(k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), b, 4, 0))

    def write_u64(self, addr: int, val: int) -> bool:
        if not addr or not self.handle:
            return False
        b = (ctypes.c_ulonglong * 1)(val & 0xFFFFFFFFFFFFFFFF)
        return bool(k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), b, 8, 0))

    def write_float(self, addr: int, val: float) -> bool:
        if not addr or not self.handle:
            return False
        b = (ctypes.c_float * 1)(val)
        return bool(k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), b, 4, 0))

    def write_double(self, addr: int, val: float) -> bool:
        if not addr or not self.handle:
            return False
        b = (ctypes.c_double * 1)(val)
        return bool(k32.WriteProcessMemory(self.handle, ctypes.c_void_p(addr), b, 8, 0))

    def attach(self, proc_name: str = "Software Inc.exe") -> bool:
        self.close()

        import subprocess
        try:
            out = subprocess.check_output(
                ['powershell', '-NoProfile', '-Command',
                 'Get-Process -Name "*Software*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id']
            ).decode().strip()
            pids = [int(p) for p in out.split() if p.isdigit()]
        except Exception:
            pids = []

        if not pids:
            return False

        target_pid = pids[0]
        h = k32.OpenProcess(PROCESS_ALL_ACCESS, False, target_pid)
        if not h:
            return False

        self.pid = target_pid
        self.handle = h

        # Locate mono-2.0-bdwgc.dll
        hMods = (ctypes.c_void_p * 1024)()
        cbNeeded = ctypes.c_uint()
        psapi.EnumProcessModules(h, hMods, ctypes.sizeof(hMods), ctypes.byref(cbNeeded))
        nMods = cbNeeded.value // 8
        modName = (ctypes.c_char * 260)()
        self.mono_base = 0
        for i in range(nMods):
            psapi.GetModuleBaseNameA(h, hMods[i], modName, 260)
            if b"mono-2.0-bdwgc.dll" in modName.value.lower():
                self.mono_base = hMods[i]
                break

        if not self.mono_base:
            self.close()
            return False

        # Locate Assembly-CSharp Image
        glist = self.read_ptr(self.mono_base + 0x494D30)
        curr = glist
        self.csharp_image = 0
        while curr:
            asm_ptr = self.read_ptr(curr)
            name = self.read_str_ascii(self.read_ptr(asm_ptr + 0x10))
            if name == "Assembly-CSharp":
                self.csharp_image = self.read_ptr(asm_ptr + 0x60)
                break
            curr = self.read_ptr(curr + 8)

        if not self.csharp_image:
            self.close()
            return False

        # Build class index from MonoInternalHashTable
        table = self.csharp_image + 0x4C0
        size = self.read_u32(table + 0x18)
        buckets = self.read_ptr(table + 0x20)
        self.classes = {}
        target_classes = {"GameSettings", "Company", "TimeOfDay", "ActorManager", "Actor", "Employee", "Team", "Cheats"}

        for i in range(size):
            node = self.read_ptr(buckets + i * 8)
            seen = set()
            while node and node not in seen:
                seen.add(node)
                name = self.read_str_ascii(self.read_ptr(node + 0x48))
                if name in target_classes:
                    self.classes[name] = node
                node = self.read_ptr(node + 0x108)

        return self.refresh_pointers()

    def _get_static_data(self, klass: int) -> int:
        if not klass:
            return 0
        rcx = self.read_ptr(klass + 0xD0)
        if not rcx:
            return 0
        vtable = self.read_ptr(rcx + 8)
        if not vtable:
            return 0
        vsize = self.read_u32(klass + 0x5C)
        return self.read_ptr(vtable + vsize * 8 + 0x40)

    def refresh_pointers(self) -> bool:
        if not self.is_attached():
            return False

        try:
            if "GameSettings" in self.classes:
                self.sdata_gs = self._get_static_data(self.classes["GameSettings"])
                self.instance_gs = self.read_ptr(self.sdata_gs + 0x20)
                if self.instance_gs:
                    self.company = self.read_ptr(self.instance_gs + 0x128)
                    self.actor_manager = self.read_ptr(self.instance_gs + 0x120)

            if "Cheats" in self.classes:
                self.sdata_cheats = self._get_static_data(self.classes["Cheats"])

            if "TimeOfDay" in self.classes:
                sdata_tod = self._get_static_data(self.classes["TimeOfDay"])
                fields_tod = self.read_ptr(self.classes["TimeOfDay"] + 0x98)
                for i in range(30):
                    f = fields_tod + i * 0x20
                    fname = self.read_str_ascii(self.read_ptr(f + 8))
                    if fname == "Instance":
                        foff = self.read_u32(f + 24)
                        self.time_of_day_instance = self.read_ptr(sdata_tod + foff)
                        break

            return bool(self.company)
        except Exception:
            return False

    # --- Live Game Data Readers & Modifiers ---

    def get_company_name(self) -> str:
        if not self.company:
            return "N/A"
        return self.read_str_net(self.read_ptr(self.company + 0x10)) or "Unnamed"

    def get_money(self) -> float:
        if not self.company:
            return 0.0
        return self.read_double(self.company + 0x150)

    def set_money(self, amount: float) -> bool:
        if not self.company:
            return False
        return self.write_double(self.company + 0x150, float(amount))

    def add_money(self, amount: float) -> bool:
        current = self.get_money()
        return self.set_money(current + amount)

    def get_fans(self) -> int:
        if not self.company:
            return 0
        return self.read_u32(self.company + 0x198)

    def set_fans(self, count: int) -> bool:
        if not self.company:
            return False
        return self.write_u32(self.company + 0x198, int(count))

    def add_fans(self, amount: int) -> bool:
        current = self.get_fans()
        return self.set_fans(current + amount)

    def get_business_rep(self) -> float:
        if not self.company:
            return 0.0
        return self.read_float(self.company + 0x1A0)

    def set_business_rep(self, rep: float) -> bool:
        if not self.company:
            return False
        rep = max(0.0, min(1.0, float(rep)))
        return self.write_float(self.company + 0x1A0, rep)

    def clear_bankruptcy(self) -> bool:
        if not self.company:
            return False
        return self.write_u8(self.company + 0x1A4, 0)

    def get_game_speed(self) -> float:
        if not self.instance_gs:
            return 1.0
        return self.read_float(self.instance_gs + 0x40)

    def set_game_speed(self, speed: float) -> bool:
        if not self.instance_gs:
            return False
        return self.write_float(self.instance_gs + 0x40, float(speed))

    def get_date_time(self) -> dict:
        if not self.time_of_day_instance:
            return {"hour": 0, "day": 0, "month": 0, "year": 0}
        return {
            "hour": self.read_u32(self.time_of_day_instance + 0x24),
            "day": self.read_u32(self.time_of_day_instance + 0x28),
            "month": self.read_u32(self.time_of_day_instance + 0x2C),
            "year": self.read_u32(self.time_of_day_instance + 0x30),
        }

    # --- Built-in Cheats ---

    def unlock_furniture(self, enable: bool = True) -> bool:
        if not self.sdata_cheats:
            return False
        return self.write_u8(self.sdata_cheats + 0x01, 1 if enable else 0)

    def force_lights(self, enable: bool = True) -> bool:
        if not self.sdata_cheats:
            return False
        return self.write_u8(self.sdata_cheats + 0x02, 1 if enable else 0)

    def disable_darkness(self, enable: bool = True) -> bool:
        if not self.sdata_cheats:
            return False
        return self.write_u8(self.sdata_cheats + 0x00, 1 if enable else 0)

    def infinite_subsidiaries(self, enable: bool = True) -> bool:
        if not self.sdata_cheats:
            return False
        return self.write_u8(self.sdata_cheats + 0x04, 1 if enable else 0)

    # --- Personnel Discovery ---

    def get_employees(self) -> list:
        if not self.actor_manager:
            return []

        actors_map = {}

        # 1. Actors (+0x10) - Active on-site employees
        act_list = self.read_ptr(self.actor_manager + 0x10)
        if act_list:
            inner = self.read_ptr(act_list + 0x20)
            if inner:
                items = self.read_ptr(inner + 0x10)
                count = self.read_u32(inner + 0x18)
                for i in range(count):
                    a = self.read_ptr(items + 0x20 + i * 8)
                    if a and a not in actors_map:
                        actors_map[a] = None

        # 2. Staff (+0x18) - Facility staff (cleaners, maintenance, IT)
        staff_list = self.read_ptr(self.actor_manager + 0x18)
        if staff_list:
            inner = self.read_ptr(staff_list + 0x20)
            if inner:
                items = self.read_ptr(inner + 0x10)
                count = self.read_u32(inner + 0x18)
                for i in range(count):
                    a = self.read_ptr(items + 0x20 + i * 8)
                    if a:
                        actors_map[a] = "Facility Staff"

        # 3. Teams (+0x40) - Team rosters
        teams_dict = self.read_ptr(self.actor_manager + 0x40)
        if teams_dict:
            entries = self.read_ptr(teams_dict + 0x18)
            if entries:
                cap = self.read_u32(entries + 0x18)
                for i in range(cap):
                    e_addr = entries + 0x20 + i * 24
                    k_ptr = self.read_ptr(e_addr + 8)
                    t_ptr = self.read_ptr(e_addr + 16)
                    if k_ptr and t_ptr:
                        t_name = self.read_str_net(k_ptr)
                        e_list = self.read_ptr(t_ptr + 0x18)
                        if e_list:
                            items = self.read_ptr(e_list + 0x10)
                            count = self.read_u32(e_list + 0x18)
                            for j in range(count):
                                a = self.read_ptr(items + 0x20 + j * 8)
                                if a:
                                    actors_map[a] = t_name

        employees = []
        idx = 0
        for actor_ptr, hint in actors_map.items():
            emp_ptr = self.read_ptr(actor_ptr + 0x138)
            if not emp_ptr:
                continue

            name = self.read_str_net(self.read_ptr(emp_ptr + 0x30)) or f"Employee #{idx+1}"
            founder = self.read_u8(emp_ptr + 0x1B0) == 1
            ceo = self.read_u8(emp_ptr + 0x1B1) == 1

            t_ptr = self.read_ptr(actor_ptr + 0x270)
            if t_ptr:
                team_name = self.read_str_net(self.read_ptr(t_ptr + 0x10))
            else:
                team_name = hint or "Facility Staff"

            energy = self.read_float(emp_ptr + 0x134)
            stress = self.read_float(emp_ptr + 0x140)
            hunger = self.read_float(emp_ptr + 0x130)
            bladder = self.read_float(emp_ptr + 0x138)
            social = self.read_float(emp_ptr + 0x13C)
            satisfaction = self.read_float(emp_ptr + 0x15C)
            creativity = self.read_float(emp_ptr + 0xC4)
            skill_ceiling = self.read_float(emp_ptr + 0x118)
            salary = self.read_float(emp_ptr + 0x160)

            # Base Skills
            skills = []
            skills_arr = self.read_ptr(emp_ptr + 0xA8)
            if skills_arr:
                scount = self.read_u32(skills_arr + 0x18)
                for r in range(min(scount, 5)):
                    skills.append(self.read_float(skills_arr + 0x20 + r * 4))

            # Specialization Exp
            spec_exp = []
            exp_arr = self.read_ptr(emp_ptr + 0x20)
            if exp_arr:
                ecount = self.read_u32(exp_arr + 0x18)
                for r in range(min(ecount, 5)):
                    spec_exp.append(self.read_float(exp_arr + 0x20 + r * 4))

            # Specialization Used
            spec_used = []
            used_arr = self.read_ptr(emp_ptr + 0x28)
            if used_arr:
                ucount = self.read_u32(used_arr + 0x18)
                for r in range(min(ucount, 5)):
                    spec_used.append(self.read_u32(used_arr + 0x20 + r * 4))

            # Specialization Levels
            specs_by_role = {}
            spec_levels_arr = self.read_ptr(emp_ptr + 0x18)
            if spec_levels_arr:
                levels_len = self.read_u32(spec_levels_arr + 0x18)
                for role_idx in range(min(levels_len, 5)):
                    rname = self.ROLE_NAMES[role_idx]
                    specs_by_role[rname] = {}
                    dict_ptr = self.read_ptr(spec_levels_arr + 0x20 + role_idx * 8)
                    if dict_ptr:
                        d_entries = self.read_ptr(dict_ptr + 0x18)
                        if d_entries:
                            d_cap = self.read_u32(d_entries + 0x18)
                            for k in range(d_cap):
                                e_addr = d_entries + 0x20 + k * 24
                                k_ptr = self.read_ptr(e_addr + 8)
                                if k_ptr:
                                    k_str = self.read_str_net(k_ptr)
                                    v_val = self.read_u32(e_addr + 16)
                                    specs_by_role[rname][k_str] = v_val

            # Traits & Weaknesses Resolution
            traits_mask = self.read_ptr(emp_ptr + 0x150)
            goods = []
            weaknesses = []
            for tname, tbit, is_bad in self.ALL_TRAITS:
                if traits_mask & tbit:
                    if is_bad:
                        weaknesses.append(tname)
                    else:
                        goods.append(tname)

            employees.append({
                "index": idx,
                "actor_ptr": actor_ptr,
                "emp_ptr": emp_ptr,
                "name": name,
                "founder": founder,
                "ceo": ceo,
                "team": team_name,
                "salary": salary,
                "energy": energy,
                "stress": stress,
                "hunger": hunger,
                "bladder": bladder,
                "social": social,
                "satisfaction": satisfaction,
                "creativity": creativity,
                "skill_ceiling": skill_ceiling,
                "skills": skills,
                "spec_exp": spec_exp,
                "spec_used": spec_used,
                "total_points": int(sum(spec_exp)),
                "total_used": int(sum(spec_used)),
                "specs": specs_by_role,
                "traits_mask": traits_mask,
                "goods": goods,
                "weaknesses": weaknesses,
            })
            idx += 1

        return employees

    def get_founder(self) -> dict:
        emps = self.get_employees()
        for e in emps:
            if e["founder"]:
                return e
        return emps[0] if emps else None

    # --- Granular Modifiers ---

    def set_employee_need(self, emp_ptr: int, need_name: str, value: float) -> bool:
        if not emp_ptr:
            return False
        offsets = {
            "energy": 0x134,
            "stress": 0x140,
            "hunger": 0x130,
            "bladder": 0x138,
            "social": 0x13C,
            "satisfaction": 0x15C,
            "creativity": 0xC4,
            "skill_ceiling": 0x118,
        }
        off = offsets.get(need_name.lower())
        if not off:
            return False
        return self.write_float(emp_ptr + off, float(value))

    def max_employee_needs(self, emp_ptr: int) -> bool:
        if not emp_ptr:
            return False
        self.write_float(emp_ptr + 0x134, 1.0)  # Energy = 100%
        self.write_float(emp_ptr + 0x130, 1.0)  # Hunger = 100%
        self.write_float(emp_ptr + 0x138, 1.0)  # Bladder = 100%
        self.write_float(emp_ptr + 0x13C, 1.0)  # Social = 100%
        self.write_float(emp_ptr + 0x140, 0.0)  # Stress = 0%
        self.write_float(emp_ptr + 0x15C, 2.0)  # Satisfaction = 200%
        self.write_float(emp_ptr + 0xC4, 1.0)   # Creativity = 100%
        self.write_float(emp_ptr + 0x118, 1.0)  # SkillCeiling = 100%
        return True

    def set_employee_skill(self, emp_ptr: int, role_idx: int, value: float) -> bool:
        if not emp_ptr or role_idx < 0 or role_idx >= 5:
            return False
        skills_arr = self.read_ptr(emp_ptr + 0xA8)
        if not skills_arr:
            return False
        scount = self.read_u32(skills_arr + 0x18)
        if role_idx >= scount:
            return False
        val = max(0.0, min(1.0, float(value)))
        return self.write_float(skills_arr + 0x20 + role_idx * 4, val)

    def max_employee_skills(self, emp_ptr: int) -> bool:
        if not emp_ptr:
            return False
        skills_arr = self.read_ptr(emp_ptr + 0xA8)
        if skills_arr:
            scount = self.read_u32(skills_arr + 0x18)
            for r in range(min(scount, 5)):
                self.write_float(skills_arr + 0x20 + r * 4, 1.0)
            return True
        return False

    def set_employee_spec_exp(self, emp_ptr: int, role_idx: int, value: float) -> bool:
        if not emp_ptr or role_idx < 0 or role_idx >= 5:
            return False
        exp_arr = self.read_ptr(emp_ptr + 0x20)
        if not exp_arr:
            return False
        ecount = self.read_u32(exp_arr + 0x18)
        if role_idx >= ecount:
            return False
        return self.write_float(exp_arr + 0x20 + role_idx * 4, max(0.0, float(value)))

    def add_employee_spec_exp(self, emp_ptr: int, delta: float = 20.0) -> bool:
        if not emp_ptr:
            return False
        exp_arr = self.read_ptr(emp_ptr + 0x20)
        if not exp_arr:
            return False
        ecount = self.read_u32(exp_arr + 0x18)
        for r in range(min(ecount, 5)):
            current = self.read_float(exp_arr + 0x20 + r * 4)
            self.write_float(exp_arr + 0x20 + r * 4, current + delta)
        return True

    def set_employee_spec_used(self, emp_ptr: int, role_idx: int, value: int) -> bool:
        if not emp_ptr or role_idx < 0 or role_idx >= 5:
            return False
        used_arr = self.read_ptr(emp_ptr + 0x28)
        if not used_arr:
            return False
        ucount = self.read_u32(used_arr + 0x18)
        if role_idx >= ucount:
            return False
        return self.write_u32(used_arr + 0x20 + role_idx * 4, max(0, int(value)))

    def set_all_employee_spec_points(self, emp_ptr: int, points: float) -> bool:
        if not emp_ptr:
            return False
        exp_arr = self.read_ptr(emp_ptr + 0x20)
        if not exp_arr:
            return False
        ecount = self.read_u32(exp_arr + 0x18)
        for r in range(min(ecount, 5)):
            self.write_float(exp_arr + 0x20 + r * 4, max(0.0, float(points)))
        return True

    def reset_employee_spec_used(self, emp_ptr: int) -> bool:
        if not emp_ptr:
            return False
        used_arr = self.read_ptr(emp_ptr + 0x28)
        if not used_arr:
            return False
        ucount = self.read_u32(used_arr + 0x18)
        for r in range(min(ucount, 5)):
            self.write_u32(used_arr + 0x20 + r * 4, 0)
        return True

    def _ensure_spec_metadata(self) -> bool:
        """Scan process memory across all employees to find canonical string pointers and Mono vtables."""
        if len(self._spec_metadata) >= 15 and self._v_buckets and self._v_entries:
            return True
        emps = self.get_employees()
        for e in emps:
            spec_arr = self.read_ptr(e["emp_ptr"] + 0x18)
            if not spec_arr:
                continue
            for r in range(5):
                d_ptr = self.read_ptr(spec_arr + 0x20 + r * 8)
                if not d_ptr:
                    continue
                b = self.read_ptr(d_ptr + 0x10)
                ent = self.read_ptr(d_ptr + 0x18)
                if b and not self._v_buckets:
                    self._v_buckets = self.read_ptr(b)
                if ent and not self._v_entries:
                    self._v_entries = self.read_ptr(ent)
                if ent:
                    cap = self.read_u32(ent + 0x18)
                    for k in range(cap):
                        ea = ent + 0x20 + k * 24
                        kp = self.read_ptr(ea + 8)
                        if kp:
                            s = self.read_str_net(kp)
                            h = self.read_u32(ea)
                            if s:
                                self._spec_metadata[s.lower()] = (kp, h)
            if len(self._spec_metadata) >= 15 and self._v_buckets and self._v_entries:
                break
        return len(self._spec_metadata) > 0

    def set_employee_spec_level(self, emp_ptr: int, role_idx: int, spec_key: str, target_level: int) -> bool:
        if not emp_ptr or role_idx < 0 or role_idx >= 5 or not self.handle:
            return False
        if not self._ensure_spec_metadata():
            return False

        key_low = spec_key.lower()
        if key_low not in self._spec_metadata:
            return False
        k_ptr, hash_code = self._spec_metadata[key_low]

        spec_levels_arr = self.read_ptr(emp_ptr + 0x18)
        if not spec_levels_arr:
            return False
        dict_ptr = self.read_ptr(spec_levels_arr + 0x20 + role_idx * 8)
        if not dict_ptr:
            return False

        d_entries = self.read_ptr(dict_ptr + 0x18)
        d_buckets = self.read_ptr(dict_ptr + 0x10)
        count = self.read_u32(dict_ptr + 0x40)

        # 1. Update existing entry if already present
        if d_entries:
            cap = self.read_u32(d_entries + 0x18)
            for k in range(cap):
                ea = d_entries + 0x20 + k * 24
                kp = self.read_ptr(ea + 8)
                if kp:
                    if self.read_str_net(kp).lower() == key_low:
                        return self.write_u32(ea + 16, int(target_level))

        # 2. Key does not exist: ensure capacity or allocate initial dictionary tables
        if not self._v_buckets or not self._v_entries:
            return False

        cur_cap = self.read_u32(d_entries + 0x18) if d_entries else 0
        if not d_entries or not d_buckets or count >= cur_cap:
            new_cap = 7 if cur_cap < 7 else 11
            b_size = 0x20 + new_cap * 4
            new_b_ptr = k32.VirtualAllocEx(self.handle, None, b_size, 0x1000 | 0x2000, 0x04)
            if not new_b_ptr:
                return False
            self.write_u64(new_b_ptr, self._v_buckets)
            self.write_u32(new_b_ptr + 0x18, new_cap)
            for i in range(new_cap):
                self.write_u32(new_b_ptr + 0x20 + i * 4, 0xFFFFFFFF)

            e_size = 0x20 + new_cap * 24
            new_e_ptr = k32.VirtualAllocEx(self.handle, None, e_size, 0x1000 | 0x2000, 0x04)
            if not new_e_ptr:
                return False
            self.write_u64(new_e_ptr, self._v_entries)
            self.write_u32(new_e_ptr + 0x18, new_cap)

            # Rehash existing entries into new buckets
            if d_entries and count > 0:
                for i in range(count):
                    old_ea = d_entries + 0x20 + i * 24
                    h = self.read_u32(old_ea)
                    old_kp = self.read_ptr(old_ea + 8)
                    val = self.read_u32(old_ea + 16)
                    tb = (h & 0x7FFFFFFF) % new_cap
                    cur_b_val = self.read_u32(new_b_ptr + 0x20 + tb * 4)
                    new_ea = new_e_ptr + 0x20 + i * 24
                    self.write_u32(new_ea, h)
                    self.write_u32(new_ea + 4, cur_b_val)
                    self.write_u64(new_ea + 8, old_kp)
                    self.write_u32(new_ea + 16, val)
                    self.write_u32(new_b_ptr + 0x20 + tb * 4, i)

            self.write_u64(dict_ptr + 0x10, new_b_ptr)
            self.write_u64(dict_ptr + 0x18, new_e_ptr)
            d_buckets = new_b_ptr
            d_entries = new_e_ptr
            cur_cap = new_cap

        # 3. Insert new entry at index `count`
        insert_idx = count
        target_bucket = (hash_code & 0x7FFFFFFF) % cur_cap
        cur_bucket_val = self.read_u32(d_buckets + 0x20 + target_bucket * 4)

        ea = d_entries + 0x20 + insert_idx * 24
        self.write_u32(ea, hash_code)
        self.write_u32(ea + 4, cur_bucket_val)
        self.write_u64(ea + 8, k_ptr)
        self.write_u32(ea + 16, int(target_level))

        self.write_u32(d_buckets + 0x20 + target_bucket * 4, insert_idx)
        self.write_u32(dict_ptr + 0x40, count + 1)
        self.write_u32(dict_ptr + 0x44, self.read_u32(dict_ptr + 0x44) + 1)
        return True

    def max_employee_specs(self, emp_ptr: int, target_level: int = 3) -> int:
        if not emp_ptr:
            return 0
        modified = 0
        for role_idx, role_name in enumerate(self.ROLE_NAMES):
            subfields = self.ROLE_ALL_SPECIALIZATIONS.get(role_name, [])
            for spec_key in subfields:
                if self.set_employee_spec_level(emp_ptr, role_idx, spec_key, target_level):
                    modified += 1
        return modified

    # --- Weaknesses & Traits Management ---

    def remove_employee_weaknesses(self, emp_ptr: int) -> int:
        if not emp_ptr:
            return 0
        mask = self.read_ptr(emp_ptr + 0x150)
        removed = 0
        for name, bit, is_bad in self.ALL_TRAITS:
            if is_bad and (mask & bit):
                removed += 1
        new_mask = mask & (~self.BAD_TRAITS_MASK)
        self.write_u64(emp_ptr + 0x150, new_mask)
        return removed

    def remove_all_personnel_weaknesses(self) -> int:
        emps = self.get_employees()
        total_removed = 0
        for e in emps:
            total_removed += self.remove_employee_weaknesses(e["emp_ptr"])
        return total_removed

    def grant_master_traits(self, emp_ptr: int) -> bool:
        if not emp_ptr:
            return False
        mask = self.read_ptr(emp_ptr + 0x150)
        # Master traits: FastLearner, BigBrain, SuperFocus, ThisIsFine, Clean
        master_set = {"FastLearner", "BigBrain", "SuperFocus", "ThisIsFine", "Clean"}
        add_mask = 0
        for name, bit, _ in self.ALL_TRAITS:
            if name in master_set:
                add_mask |= bit
        new_mask = mask | add_mask
        return self.write_u64(emp_ptr + 0x150, new_mask)

    def set_employee_trait_toggle(self, emp_ptr: int, trait_name: str, enable: bool) -> bool:
        if not emp_ptr:
            return False
        mask = self.read_ptr(emp_ptr + 0x150)
        for name, bit, _ in self.ALL_TRAITS:
            if name.lower() == trait_name.lower():
                new_mask = (mask | bit) if enable else (mask & (~bit))
                return self.write_u64(emp_ptr + 0x150, new_mask)
        return False

    def set_employee_salary(self, emp_ptr: int, salary: float) -> bool:
        if not emp_ptr:
            return False
        return self.write_float(emp_ptr + 0x160, float(salary))

    def set_all_employees_free_salary(self) -> int:
        emps = self.get_employees()
        for e in emps:
            self.set_employee_salary(e["emp_ptr"], 0.0)
        return len(emps)

    # --- Batch Operations ---

    def max_all_employees_needs(self) -> int:
        emps = self.get_employees()
        return sum(1 for e in emps if self.max_employee_needs(e["emp_ptr"]))

    def max_all_employees_skills(self) -> int:
        emps = self.get_employees()
        return sum(1 for e in emps if self.max_employee_skills(e["emp_ptr"]))

    def max_all_employees_specs(self, target_level: int = 3) -> int:
        emps = self.get_employees()
        return sum(self.max_employee_specs(e["emp_ptr"], target_level) for e in emps)

    def add_all_employees_spec_exp(self, delta: float = 20.0) -> int:
        emps = self.get_employees()
        return sum(1 for e in emps if self.add_employee_spec_exp(e["emp_ptr"], delta))


    # --- Projects & Software Management ---

    def get_active_projects(self) -> list:
        if not self.company:
            return []
        work_items_ptr = self.read_ptr(self.company + 0x108)
        if not work_items_ptr:
            return []
        p18 = self.read_ptr(work_items_ptr + 0x18)
        if not p18:
            return []
        arr_len = self.read_u32(p18 + 0x18)
        projects = []
        for i in range(arr_len):
            e_addr = p18 + 0x20 + i * 16
            item_ptr = self.read_ptr(e_addr + 8)
            if not item_ptr:
                continue
            vtable = self.read_ptr(item_ptr)
            klass = self.read_ptr(vtable) if vtable else 0
            kname = self.read_str_ascii(self.read_ptr(klass + 0x48)) if klass else ""
            if kname == "DesignDocument":
                name = self.read_str_net(self.read_ptr(item_ptr + 0xA8)) or self.read_str_net(self.read_ptr(item_ptr + 0x10)) or f"Design #{i+1}"
                progress = self.read_float(item_ptr + 0x23C)
                iteration = self.read_u32(item_ptr + 0x22C)
                lead_prog = self.read_float(item_ptr + 0x238)
                rev_acc = self.read_float(item_ptr + 0x230)
                finished = self.read_u8(item_ptr + 0x228) == 1
                followers = self.read_float(item_ptr + 0x1A0)
                max_followers = self.read_u32(item_ptr + 0x1A4)
                projects.append({
                    "ptr": item_ptr,
                    "type": "Design",
                    "name": name,
                    "progress": progress,
                    "iteration": iteration,
                    "lead_prog": lead_prog,
                    "rev_acc": rev_acc,
                    "has_finished": finished,
                    "followers": followers,
                    "max_followers": max_followers,
                })
            elif kname in ("SoftwareAlpha", "SoftwareWorkItem"):
                name = self.read_str_net(self.read_ptr(item_ptr + 0xA8)) or self.read_str_net(self.read_ptr(item_ptr + 0x10)) or f"Software #{i+1}"
                in_beta = self.read_u8(item_ptr + 0x240) == 1
                released = self.read_u8(item_ptr + 0x241) == 1
                has_finished = self.read_u8(item_ptr + 0x242) == 1
                has_code = self.read_u8(item_ptr + 0x244) == 1
                has_art = self.read_u8(item_ptr + 0x243) == 1
                bugs = self.read_float(item_ptr + 0x248)
                fixed_bugs = self.read_float(item_ptr + 0x24C)
                design_prog = self.read_float(item_ptr + 0x270)
                rev_score = self.read_float(item_ptr + 0x27C)
                followers = self.read_float(item_ptr + 0x1A0)
                max_followers = self.read_u32(item_ptr + 0x1A4)

                features_ptr = self.read_ptr(item_ptr + 0x118)
                feat_count = self.read_u32(features_ptr + 0x18) if features_ptr else 0
                tot_cp, tot_cd, tot_ap, tot_ad = 0.0, 0.0, 0.0, 0.0
                features_list = []
                for f_idx in range(feat_count):
                    fp = self.read_ptr(features_ptr + 0x20 + f_idx * 8)
                    if fp:
                        cdev = self.read_double(fp + 0x20)
                        adev = self.read_double(fp + 0x28)
                        cprog = self.read_double(fp + 0x30)
                        aprog = self.read_double(fp + 0x38)
                        tot_cd += cdev
                        tot_ad += adev
                        tot_cp += cprog
                        tot_ap += aprog
                        f_obj = self.read_ptr(fp + 0x10)
                        fname = self.read_str_net(self.read_ptr(f_obj + 0x10)) if f_obj else f"Feature #{f_idx+1}"
                        features_list.append({
                            "ptr": fp,
                            "name": fname,
                            "code_prog": cprog,
                            "code_req": cdev,
                            "art_prog": aprog,
                            "art_req": adev,
                        })

                projects.append({
                    "ptr": item_ptr,
                    "type": "Beta" if in_beta else "Alpha",
                    "name": name,
                    "in_beta": in_beta,
                    "released": released,
                    "has_finished": has_finished,
                    "has_code": has_code,
                    "has_art": has_art,
                    "bugs": bugs,
                    "fixed_bugs": fixed_bugs,
                    "design_prog": design_prog,
                    "rev_score": rev_score,
                    "followers": followers,
                    "max_followers": max_followers,
                    "tot_code_prog": tot_cp,
                    "tot_code_req": tot_cd,
                    "code_pct": (tot_cp / max(0.001, tot_cd)) * 100.0,
                    "tot_art_prog": tot_ap,
                    "tot_art_req": tot_ad,
                    "art_pct": (tot_ap / max(0.001, tot_ad)) * 100.0,
                    "features": features_list,
                })
        return projects

    def get_released_products(self) -> list:
        if not self.company:
            return []
        products_ptr = self.read_ptr(self.company + 0x110)
        if not products_ptr:
            return []
        p_items = self.read_ptr(products_ptr + 0x10)
        p_count = self.read_u32(products_ptr + 0x18)
        products = []
        for i in range(p_count):
            prod_ptr = self.read_ptr(p_items + 0x20 + i * 8)
            if not prod_ptr:
                continue
            name = self.read_str_net(self.read_ptr(prod_ptr + 0x28)) or f"Product #{i+1}"
            quality = self.read_double(prod_ptr + 0x158)
            followers = self.read_u32(prod_ptr + 0x168)
            awareness = self.read_float(prod_ptr + 0x20C)
            bugs = self.read_u32(prod_ptr + 0x1F4)
            pos_reviews = self.read_u32(prod_ptr + 0x1EC)
            neg_reviews = self.read_u32(prod_ptr + 0x1F0)
            price = self.read_float(prod_ptr + 0x214)
            userbase = self.read_u32(prod_ptr + 0x2A4)
            products.append({
                "ptr": prod_ptr,
                "name": name,
                "quality": quality,
                "followers": followers,
                "awareness": awareness,
                "bugs": bugs,
                "pos_reviews": pos_reviews,
                "neg_reviews": neg_reviews,
                "price": price,
                "userbase": userbase,
            })
        return products

    def max_design_project(self, ptr: int) -> bool:
        if not ptr:
            return False
        self.write_u32(ptr + 0x22C, 3)        # Iteration 3
        self.write_float(ptr + 0x23C, 1.0)     # _currentProgress = 100%
        self.write_float(ptr + 0x238, 1.0)     # LeadProgress = 100%
        self.write_float(ptr + 0x230, 1.0)     # ReviewAccuracy = 100%
        self.write_u8(ptr + 0x228, 1)          # HasFinished = True
        return True

    def max_dev_project(self, ptr: int) -> bool:
        if not ptr:
            return False
        features_ptr = self.read_ptr(ptr + 0x118)
        feat_count = self.read_u32(features_ptr + 0x18) if features_ptr else 0
        for f_idx in range(feat_count):
            fp = self.read_ptr(features_ptr + 0x20 + f_idx * 8)
            if fp:
                cdev = self.read_double(fp + 0x20)
                adev = self.read_double(fp + 0x28)
                self.write_double(fp + 0x30, cdev)
                self.write_double(fp + 0x38, adev)
                self.write_double(fp + 0x40, 1.0)
                self.write_double(fp + 0x48, 1.0)
                self.write_u8(fp + 0x61, 1)
                self.write_u8(fp + 0x62, 1)
        self.write_u8(ptr + 0x244, 1)          # HasFinishedCode
        self.write_u8(ptr + 0x243, 1)          # HasFinishedArt
        self.write_float(ptr + 0x27C, 1.0)     # ReviewScore = 1.0
        return True

    def clear_project_bugs(self, ptr: int) -> bool:
        if not ptr:
            return False
        cur_bugs = self.read_float(ptr + 0x248)
        cur_fixed = self.read_float(ptr + 0x24C)
        self.write_float(ptr + 0x24C, cur_fixed + cur_bugs)
        self.write_float(ptr + 0x248, 0.0)
        return True

    def set_project_followers(self, ptr: int, count: float) -> bool:
        if not ptr:
            return False
        val = max(0.0, float(count))
        self.write_float(ptr + 0x1A0, val)
        cur_max = self.read_u32(ptr + 0x1A4)
        if cur_max < int(val):
            self.write_u32(ptr + 0x1A4, int(val))
        return True

    def promote_project_to_beta(self, ptr: int) -> bool:
        if not ptr:
            return False
        return self.write_u8(ptr + 0x240, 1)

    def ready_project_for_release(self, ptr: int) -> bool:
        if not ptr:
            return False
        self.max_dev_project(ptr)
        self.clear_project_bugs(ptr)
        self.write_u8(ptr + 0x242, 1)  # HasFinished = True
        return True

    def max_all_active_designs(self) -> int:
        projs = self.get_active_projects()
        cnt = 0
        for p in projs:
            if p["type"] == "Design":
                if self.max_design_project(p["ptr"]):
                    cnt += 1
        return cnt

    def max_all_active_devs(self) -> int:
        projs = self.get_active_projects()
        cnt = 0
        for p in projs:
            if p["type"] in ("Alpha", "Beta"):
                if self.max_dev_project(p["ptr"]):
                    cnt += 1
        return cnt

    def clear_all_projects_bugs(self) -> int:
        projs = self.get_active_projects()
        cnt = 0
        for p in projs:
            if p["type"] in ("Alpha", "Beta"):
                if self.clear_project_bugs(p["ptr"]):
                    cnt += 1
        return cnt

    def add_all_projects_followers(self, delta: float = 25000.0) -> int:
        projs = self.get_active_projects()
        cnt = 0
        for p in projs:
            cur = p.get("followers", 0.0)
            if self.set_project_followers(p["ptr"], cur + delta):
                cnt += 1
        return cnt

    def modify_released_product(self, ptr: int, quality: float = None, followers: int = None, awareness: float = None, clear_bugs: bool = False) -> bool:
        if not ptr:
            return False
        if quality is not None:
            self.write_double(ptr + 0x158, float(quality))
        if followers is not None:
            self.write_u32(ptr + 0x168, int(followers))
        if awareness is not None:
            self.write_float(ptr + 0x20C, float(awareness))
        if clear_bugs:
            self.write_u32(ptr + 0x1F4, 0)
        return True


    # --- Research & Patents Management ---

    def get_active_research(self) -> list:
        if not self.company:
            return []
        work_items_ptr = self.read_ptr(self.company + 0x108)
        if not work_items_ptr:
            return []
        p18 = self.read_ptr(work_items_ptr + 0x18)
        if not p18:
            return []
        arr_len = self.read_u32(p18 + 0x18)
        tasks = []
        for i in range(arr_len):
            e_addr = p18 + 0x20 + i * 16
            item_ptr = self.read_ptr(e_addr + 8)
            if not item_ptr:
                continue
            vtable = self.read_ptr(item_ptr)
            klass = self.read_ptr(vtable) if vtable else 0
            kname = self.read_str_ascii(self.read_ptr(klass + 0x48)) if klass else ""
            if kname == "ResearchWork":
                name = self.read_str_net(self.read_ptr(item_ptr + 0x10)) or "Researching"
                spec = self.read_str_net(self.read_ptr(item_ptr + 0x0B0)) or "General"
                year = self.read_u32(item_ptr + 0x0C4)
                progress = self.read_float(item_ptr + 0x0B8)
                max_val = self.read_u32(item_ptr + 0x0BC)
                upg_factor = self.read_float(item_ptr + 0x0C0)
                finished = self.read_u8(item_ptr + 0x0C8) == 1
                done = self.read_u8(item_ptr + 0x094) == 1
                paused = self.read_u8(item_ptr + 0x09A) == 1
                priority = self.read_u32(item_ptr + 0x074)

                display_year = f"19{year:02d}" if year >= 50 else f"20{year:02d}" if year > 0 else "Base"
                pct = min(100.0, (progress / max(1, max_val)) * 100.0) if max_val > 0 else 0.0

                tasks.append({
                    "ptr": item_ptr,
                    "name": name,
                    "spec": spec,
                    "year_raw": year,
                    "year_display": display_year,
                    "progress": progress,
                    "max": max_val,
                    "pct": pct,
                    "upg_factor": upg_factor,
                    "finished": finished,
                    "done": done,
                    "paused": paused,
                    "priority": priority,
                })
        return tasks

    def max_research_task(self, ptr: int) -> bool:
        if not ptr:
            return False
        max_val = self.read_u32(ptr + 0x0BC)
        target_pts = float(max_val) if max_val > 0 else 48.0
        self.write_float(ptr + 0x0B8, target_pts)
        self.write_u8(ptr + 0x0C8, 1)  # Finished = True
        return True

    def set_research_speed(self, ptr: int, factor: float = 10.0) -> bool:
        if not ptr:
            return False
        return self.write_float(ptr + 0x0C0, max(0.1, float(factor)))

    def set_research_progress(self, ptr: int, progress: float) -> bool:
        if not ptr:
            return False
        return self.write_float(ptr + 0x0B8, max(0.0, float(progress)))

    def max_all_active_research(self) -> int:
        tasks = self.get_active_research()
        cnt = 0
        for t in tasks:
            if self.max_research_task(t["ptr"]):
                cnt += 1
        return cnt

    def boost_all_active_research(self, factor: float = 10.0) -> int:
        tasks = self.get_active_research()
        cnt = 0
        for t in tasks:
            if self.set_research_speed(t["ptr"], factor):
                cnt += 1
        return cnt

    def get_patents(self) -> list:
        if not self.company:
            return []
        patents_ptr = self.read_ptr(self.company + 0x78)
        if not patents_ptr:
            return []
        items = self.read_ptr(patents_ptr + 0x10)
        count = self.read_u32(patents_ptr + 0x18)
        if not items or count == 0:
            return []
        patents = []
        for i in range(count):
            p_ptr = self.read_ptr(items + 0x20 + i * 8)
            if not p_ptr:
                continue
            spec = self.read_str_net(self.read_ptr(p_ptr + 0x10))
            yr = self.read_u32(p_ptr + 0x28)
            can_patent = self.read_u8(p_ptr + 0x2C) == 1
            income = self.read_float(p_ptr + 0x30)
            royalty = self.read_float(p_ptr + 0x34)
            outdates = self.read_u32(p_ptr + 0x38)
            owner = self.read_u32(p_ptr + 0x3C)
            display_year = f"19{yr:02d}" if yr >= 50 else f"20{yr:02d}" if yr > 0 else "Base"

            patents.append({
                "ptr": p_ptr,
                "spec": spec,
                "year_raw": yr,
                "year_display": display_year,
                "can_patent": can_patent,
                "income": income,
                "royalty": royalty,
                "outdates": outdates,
                "owner": owner,
            })
        return patents

    def modify_patent(self, ptr: int, royalty: float = None, income: float = None, outdates: int = None) -> bool:
        if not ptr:
            return False
        if royalty is not None:
            self.write_float(ptr + 0x34, max(0.0, float(royalty)))
        if income is not None:
            self.write_float(ptr + 0x30, max(0.0, float(income)))
        if outdates is not None:
            self.write_u32(ptr + 0x38, int(outdates))
        return True

    def boost_all_patents(self, royalty: float = 0.50, outdates: int = 2099) -> int:
        patents = self.get_patents()
        cnt = 0
        for p in patents:
            if self.modify_patent(p["ptr"], royalty=royalty, outdates=outdates):
                cnt += 1
        return cnt


# Global Memory Engine Instance
game = GameMemory()


# --- CLI MODE ---

def run_cli(args):
    print("==========================================================")
    print("           SOFTWARE INC. MEMORY TRAINER (CLI)             ")
    print("==========================================================")

    if any(a in ("--help", "-h", "/?", "help") for a in args):
        print("Usage: python trainer.py [options]")
        print("\nOptions:")
        print("  --status                  Print current game, treasury, and personnel stats")
        print("  --list-teams              List all personnel grouped by team with stats & traits")
        print("  --add-money <amount>      Add funds to corporate treasury")
        print("  --set-money <amount>      Set exact corporate treasury balance")
        print("  --add-fans <count>        Add company fans")
        print("  --set-rep <0-100>         Set business reputation percentage")
        print("  --max-founder             Max out Founder vitals, skills, specs & clear weaknesses")
        print("  --max-employees           Max out all employees' needs and base skills to 100%")
        print("  --max-specs               Elevate all employee specializations to 3 stars")
        print("  --add-spec-exp <points>   Grant specialization points across all roles")
        print("  --set-spec-points <pts>   Set exact specialization points across all roles")
        print("  --reset-spec-used         Reset spent specialization points (refund capacity)")
        print("  --remove-weaknesses       Cure/remove all 8 negative traits from all personnel")
        print("  --free-salaries           Set all personnel salaries to $0 (free labor)")
        print("  --unlock-furniture        Unlock all locked furniture and equipment")
        print("  --force-lights            Force all lights on")
        print("  --speed <multiplier>      Set game simulation speed (e.g. 1.0, 5.0)")
        print("  --list-projects           List active design, alpha, and beta projects with progress")
        print("  --list-products           List released software products and metrics")
        print("  --max-design [name]       Max design phase (100% progress, Iteration 3) for project(s)")
        print("  --max-dev [name]          Complete code & art (100%) for active alpha/beta project(s)")
        print("  --clear-bugs [name]       Clear all bugs (0) on active alpha/beta project(s)")
        print("  --promote-beta [name]     Promote project(s) to Beta phase")
        print("  --ready-release [name]    Ready project(s) for release (max dev + 0 bugs + finished)")
        print("  --set-proj-fans <name> <n> Set followers for specific project")
        print("  --add-proj-fans <n>       Add followers to all active projects")
        print("  --max-product [name]      Max quality (1.5), 100% awareness & clear bugs on product(s)")
        print("  --list-research           List active research tasks, progress (pts & %), and speed factor")
        print("  --list-patents            List corporate patents, royalty percentages, and collected income")
        print("  --max-research [spec]     Instantly complete active research task(s) and trigger patent grant")
        print("  --set-research-speed <n>  Set research speed multiplier (e.g. 5.0, 10.0, 50.0) across tasks")
        print("  --set-research-prog <s <n> Set exact progress points on active research")
        print("  --boost-patents           Boost all patents to 50% royalty and extend expiration to 2099")
        return 0

    if not game.attach():
        print("[!] ERROR: Could not attach to Software Inc.exe.")
        print("    Please ensure the game is running and a save is loaded.")
        return 1

    print(f"[+] Attached to PID:       {game.pid}")
    print(f"[+] Active Company:        {game.get_company_name()}")
    print(f"[+] Bank Balance:          ${game.get_money():,.2f}")
    print(f"[+] Fans:                  {game.get_fans():,}")
    print(f"[+] Business Reputation:   {game.get_business_rep()*100:.1f}%")

    founder = game.get_founder()
    if founder:
        print(f"[+] Founder:               {founder['name']} (Team: {founder['team']})")

    i = 0
    while i < len(args):
        cmd = args[i].lower()
        if cmd == "--add-money" and i + 1 < len(args):
            amt = float(args[i+1])
            game.add_money(amt)
            print(f"[SUCCESS] Added ${amt:,.2f}! New Balance: ${game.get_money():,.2f}")
            i += 2
        elif cmd == "--set-money" and i + 1 < len(args):
            amt = float(args[i+1])
            game.set_money(amt)
            print(f"[SUCCESS] Set Balance to ${amt:,.2f}!")
            i += 2
        elif cmd == "--add-fans" and i + 1 < len(args):
            fans = int(args[i+1])
            game.add_fans(fans)
            print(f"[SUCCESS] Added {fans:,} fans! Total Fans: {game.get_fans():,}")
            i += 2
        elif cmd == "--set-rep" and i + 1 < len(args):
            rep = float(args[i+1]) / 100.0 if float(args[i+1]) > 1.0 else float(args[i+1])
            game.set_business_rep(rep)
            print(f"[SUCCESS] Business Reputation set to {game.get_business_rep()*100:.1f}%")
            i += 2
        elif cmd == "--unlock-furniture":
            game.unlock_furniture(True)
            print("[SUCCESS] All furniture unlocked!")
            i += 1
        elif cmd == "--force-lights":
            game.force_lights(True)
            print("[SUCCESS] All lights forced ON!")
            i += 1
        elif cmd == "--max-founder":
            if founder:
                p = founder["emp_ptr"]
                game.max_employee_needs(p)
                game.max_employee_skills(p)
                sp = game.max_employee_specs(p, 3)
                game.add_employee_spec_exp(p, 50.0)
                game.remove_employee_weaknesses(p)
                print(f"[SUCCESS] Maxed Founder '{founder['name']}': 100% Needs, 100% Skills, {sp} Specs Maxed, Weaknesses Removed, +50 EXP!")
            i += 1
        elif cmd == "--max-employees":
            n = game.max_all_employees_needs()
            s = game.max_all_employees_skills()
            print(f"[SUCCESS] Maxed Needs and Skills for {n} employees & facility staff!")
            i += 1
        elif cmd == "--max-specs":
            count = game.max_all_employees_specs(3)
            print(f"[SUCCESS] Elevated {count} specializations across all employees to Level 3!")
            i += 1
        elif cmd == "--add-spec-exp" and i + 1 < len(args):
            delta = float(args[i+1])
            n = game.add_all_employees_spec_exp(delta)
            print(f"[SUCCESS] Added +{delta:.1f} Specialization Points across all roles for {n} employees!")
            i += 2
        elif cmd == "--set-spec-points" and i + 1 < len(args):
            pts = float(args[i+1])
            emps = game.get_employees()
            count = sum(1 for e in emps if game.set_all_employee_spec_points(e["emp_ptr"], pts))
            print(f"[SUCCESS] Set specialization points to {pts:.1f} across all roles for {count} employees!")
            i += 2
        elif cmd == "--reset-spec-used":
            emps = game.get_employees()
            count = sum(1 for e in emps if game.reset_employee_spec_used(e["emp_ptr"]))
            print(f"[SUCCESS] Reset spent specialization points (refunded capacity) for {count} employees!")
            i += 1
        elif cmd == "--remove-weaknesses":
            rem = game.remove_all_personnel_weaknesses()
            print(f"[SUCCESS] Removed {rem} weaknesses across all company personnel!")
            i += 1
        elif cmd == "--free-salaries":
            count = game.set_all_employees_free_salary()
            print(f"[SUCCESS] Assigned $0 salary (Free Labor) to all {count} personnel!")
            i += 1
        elif cmd == "--list-teams":
            emps = game.get_employees()
            by_team = {}
            for e in emps:
                by_team.setdefault(e["team"], []).append(e)
            print(f"\n--- Total Personnel: {len(emps)} across {len(by_team)} Teams ---")
            for tname, members in by_team.items():
                print(f"\n[Team: {tname}] ({len(members)} members)")
                for m in members:
                    tag = " [FOUNDER]" if m["founder"] else ""
                    w_tag = f" | Weaknesses: {', '.join(m['weaknesses'])}" if m['weaknesses'] else ""
                    print(f"  - {m['name']}{tag}: Salary ${m['salary']:,.0f} | Energy {m['energy']*100:.0f}% | Stress {m['stress']*100:.0f}% | Points: {m['total_points']}{w_tag}")
            i += 1
        elif cmd == "--speed" and i + 1 < len(args):
            spd = float(args[i+1])
            game.set_game_speed(spd)
            print(f"[SUCCESS] Game speed set to {spd}x")
            i += 2
        elif cmd == "--status":
            emps = game.get_employees()
            projs = game.get_active_projects()
            prods = game.get_released_products()
            print(f"[+] Total Detected Personnel: {len(emps)} (Employees + Facility Staff)")
            print(f"[+] Active Projects:         {len(projs)} in development")
            print(f"[+] Released Products:       {len(prods)} products on market")
            res_tasks = game.get_active_research()
            patents = game.get_patents()
            print(f"[+] Active Research:         {len(res_tasks)} research projects")
            print(f"[+] Patents Held:            {len(patents)} technology patents")
            i += 1
        elif cmd == "--list-projects":
            projs = game.get_active_projects()
            print(f"\n--- Active Software Projects: {len(projs)} ---")
            for p in projs:
                if p["type"] == "Design":
                    fin = " [FINISHED]" if p["has_finished"] else ""
                    print(f"  [Design] {p['name']}{fin}: Iteration {p['iteration']}/3 | Prog: {p['progress']*100:.1f}% | Followers: {p['followers']:,.0f}")
                else:
                    stage = "Beta" if p["in_beta"] else "Alpha"
                    print(f"  [{stage}] {p['name']}: Code {p['code_pct']:.1f}% | Art {p['art_pct']:.1f}% | Bugs: {p['bugs']:.1f} | Followers: {p['followers']:,.0f}")
            i += 1
        elif cmd == "--list-products":
            prods = game.get_released_products()
            print(f"\n--- Released Software Catalog: {len(prods)} ---")
            for p in prods:
                print(f"  - {p['name']}: Quality {p['quality']:.2f} | Fans: {p['followers']:,} | Awareness: {p['awareness']*100:.1f}% | Bugs: {p['bugs']} | Users: {p['userbase']:,} | Price: ${p['price']:.2f}")
            i += 1
        elif cmd == "--max-design":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] == "Design" and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.max_design_project(p["ptr"])
                    print(f"[SUCCESS] Maxed design for '{p['name']}' (Iteration 3, 100% Progress, Ready for Dev)!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active design project found.")
        elif cmd == "--max-dev":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] in ("Alpha", "Beta") and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.max_dev_project(p["ptr"])
                    print(f"[SUCCESS] Completed 100% code & art programming for '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active dev project found.")
        elif cmd == "--clear-bugs":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] in ("Alpha", "Beta") and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.clear_project_bugs(p["ptr"])
                    print(f"[SUCCESS] Cleared all bugs (0) for '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active project found.")
        elif cmd == "--promote-beta":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] == "Alpha" and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.promote_project_to_beta(p["ptr"])
                    print(f"[SUCCESS] Promoted '{p['name']}' to Beta phase!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active alpha project found.")
        elif cmd == "--ready-release":
            target_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_name:
                i += 2
            else:
                i += 1
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if p["type"] in ("Alpha", "Beta") and (not target_name or target_name in p["name"].lower() or target_name == "all"):
                    game.ready_project_for_release(p["ptr"])
                    print(f"[SUCCESS] Prepared '{p['name']}' for release (Code/Art maxed, 0 bugs, ready)!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active project found.")
        elif cmd == "--set-proj-fans" and i + 2 < len(args):
            proj_name = args[i+1].lower()
            val = float(args[i+2])
            projs = game.get_active_projects()
            cnt = 0
            for p in projs:
                if proj_name in p["name"].lower() or proj_name == "all":
                    game.set_project_followers(p["ptr"], val)
                    print(f"[SUCCESS] Set followers to {val:,.0f} on '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print(f"[!] No active project matching '{proj_name}' found.")
            i += 3
        elif cmd == "--add-proj-fans" and i + 1 < len(args):
            val = float(args[i+1])
            cnt = game.add_all_projects_followers(val)
            print(f"[SUCCESS] Added +{val:,.0f} followers across {cnt} active projects!")
            i += 2
        elif cmd == "--max-product":
            prod_name = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if prod_name:
                i += 2
            else:
                i += 1
            prods = game.get_released_products()
            cnt = 0
            for p in prods:
                if not prod_name or prod_name in p["name"].lower() or prod_name == "all":
                    game.modify_released_product(p["ptr"], quality=1.5, awareness=1.0, clear_bugs=True)
                    print(f"[SUCCESS] Maxed quality (1.5), 100% awareness, and cleared bugs for '{p['name']}'!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching released product found.")
        elif cmd == "--list-research":
            tasks = game.get_active_research()
            print(f"\n--- Active Research Tasks: {len(tasks)} ---")
            if not tasks:
                print("  (No active research tasks in progress)")
            for t in tasks:
                fin = " [FINISHED]" if t["finished"] else ""
                paused = " [PAUSED]" if t["paused"] else ""
                print(f"  - [{t['spec']} - {t['year_display']}]{fin}{paused}: {t['progress']:.2f} / {t['max']} pts ({t['pct']:.1f}%) | Speed: {t['upg_factor']:.1f}x")
            i += 1
        elif cmd == "--list-patents":
            patents = game.get_patents()
            print(f"\n--- Corporate Patents Catalog: {len(patents)} ---")
            if not patents:
                print("  (No patents held yet)")
            for p in patents:
                print(f"  - [{p['spec']} - {p['year_display']}]: Royalty: {p['royalty']*100:.1f}% | Revenue: ${p['income']:,.2f} | Expires: Year {p['outdates']}")
            i += 1
        elif cmd == "--max-research":
            target_spec = args[i+1].lower() if i + 1 < len(args) and not args[i+1].startswith("--") else ""
            if target_spec:
                i += 2
            else:
                i += 1
            tasks = game.get_active_research()
            cnt = 0
            for t in tasks:
                if not target_spec or target_spec in t["spec"].lower() or target_spec == "all":
                    game.max_research_task(t["ptr"])
                    print(f"[SUCCESS] Completed research on '{t['spec']} - {t['year_display']}' (Max points awarded, Finished flag set)!")
                    cnt += 1
            if cnt == 0:
                print("[!] No matching active research task found.")
        elif cmd == "--set-research-speed" and i + 1 < len(args):
            factor = float(args[i+1])
            cnt = game.boost_all_active_research(factor)
            print(f"[SUCCESS] Set research speed multiplier to {factor:.1f}x across {cnt} active research tasks!")
            i += 2
        elif cmd == "--set-research-prog" and i + 2 < len(args):
            target_spec = args[i+1].lower()
            pts = float(args[i+2])
            tasks = game.get_active_research()
            cnt = 0
            for t in tasks:
                if target_spec in t["spec"].lower() or target_spec == "all":
                    game.set_research_progress(t["ptr"], pts)
                    print(f"[SUCCESS] Set research progress to {pts:.2f} pts on '{t['spec']} - {t['year_display']}'!")
                    cnt += 1
            if cnt == 0:
                print(f"[!] No active research task matching '{target_spec}' found.")
            i += 3
        elif cmd == "--boost-patents":
            cnt = game.boost_all_patents(royalty=0.50, outdates=2099)
            print(f"[SUCCESS] Boosted {cnt} patents: Set royalties to 50% and extended expiration to Year 2099!")
            i += 1
        else:
            i += 1

    return 0


# --- WINDOWS 11 FLUENT DESIGN GUI ---

def run_gui():
    # Windows 11 Fluent Color Palette (Light, Dark)
    C_WIN_BG = ("#F3F3F3", "#202020")
    C_SIDEBAR_BG = ("#EAEAEA", "#1B1B1B")
    C_CARD_BG = ("#FFFFFF", "#2B2B2B")
    C_CARD_ALT = ("#F9F9F9", "#242424")
    C_CARD_HOVER = ("#F0F0F0", "#303030")
    C_BORDER = ("#E5E5E5", "#383838")
    C_BORDER_SUBTLE = ("#ECECEC", "#323232")
    C_TEXT_PRI = ("#1F1F1F", "#FFFFFF")
    C_TEXT_SEC = ("#5C5C5C", "#A0A0A0")
    C_TEXT_MUTED = ("#767676", "#7D7D7D")
    C_ACCENT = ("#0067C0", "#0078D4")
    C_ACCENT_HOVER = ("#1975C5", "#2488D8")
    C_ACCENT_TEXT = "#FFFFFF"
    C_BTN_SEC = ("#F0F0F0", "#333333")
    C_BTN_SEC_HOVER = ("#E4E4E4", "#3D3D3D")
    C_SUCCESS = ("#0E700E", "#6CCB5F")
    C_SUCCESS_BG = ("#DFF6DD", "#153315")
    C_ERROR = ("#A80000", "#F1707A")
    C_ERROR_BG = ("#FDE7E9", "#3D1719")
    C_BADGE_WEAK = ("#FFF1F0", "#3E1E1E")
    C_BADGE_GOOD = ("#E6FFFB", "#112F2D")

    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Software Inc. Trainer")
    root.geometry("1080x780")
    root.minsize(980, 680)
    root.configure(fg_color=C_WIN_BG)

    # State Variables
    freeze_needs_var = ctk.BooleanVar(value=False)
    turbo_speed_var = ctk.BooleanVar(value=False)
    hotkeys_enabled_var = ctk.BooleanVar(value=True)
    selected_team_filter = ctk.StringVar(value="All Teams")
    search_query_var = ctk.StringVar(value="")
    current_selected_emp = [None]
    insp_subtab = ["overview"]

    # --- TOP APP BAR ---
    top_bar = ctk.CTkFrame(root, height=48, corner_radius=0, fg_color=C_CARD_BG,
                           border_width=1, border_color=C_BORDER)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)

    lbl_app_title = ctk.CTkLabel(top_bar, text="Software Inc. Trainer",
                                 font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                                 text_color=C_TEXT_PRI)
    lbl_app_title.pack(side="left", padx=(16, 12), pady=10)

    # Status Info Badge
    status_badge = ctk.CTkFrame(top_bar, fg_color=C_ERROR_BG, corner_radius=4, height=26)
    status_badge.pack(side="left", padx=4, pady=10)
    lbl_status_text = ctk.CTkLabel(status_badge, text="● Not attached to game",
                                   font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                   text_color=C_ERROR)
    lbl_status_text.pack(padx=8, pady=2)

    # Theme Mode Selector
    def on_theme_change(choice: str):
        ctk.set_appearance_mode(choice.lower())

    theme_selector = ctk.CTkOptionMenu(top_bar, values=["System", "Dark", "Light"], command=on_theme_change,
                                       width=95, height=26, font=ctk.CTkFont(family="Segoe UI", size=11),
                                       fg_color=C_BTN_SEC, text_color=C_TEXT_PRI,
                                       button_color=C_BTN_SEC, button_hover_color=C_BTN_SEC_HOVER)
    theme_selector.set("System")
    theme_selector.pack(side="right", padx=(6, 16), pady=10)

    lbl_theme = ctk.CTkLabel(top_bar, text="Theme:", font=ctk.CTkFont(family="Segoe UI", size=11),
                             text_color=C_TEXT_SEC)
    lbl_theme.pack(side="right", padx=(12, 4))

    lbl_calendar = ctk.CTkLabel(top_bar, text="Calendar: Loading...",
                                font=ctk.CTkFont(family="Segoe UI", size=11),
                                text_color=C_TEXT_SEC)
    lbl_calendar.pack(side="right", padx=(12, 16))

    # --- NATIVE WINDOWS 11 INFOBAR (TOAST) ---
    infobar = ctk.CTkFrame(root, height=36, corner_radius=0, fg_color=C_CARD_BG,
                           border_width=1, border_color=C_BORDER)
    infobar.pack(fill="x")
    infobar.pack_propagate(False)

    lbl_info_msg = ctk.CTkLabel(infobar, text="Ready. Attach Software Inc. to begin memory operations.",
                                font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC)
    lbl_info_msg.pack(side="left", padx=16, pady=6)

    def show_infobar(msg: str, is_success: bool = True):
        bg = C_SUCCESS_BG if is_success else C_ERROR_BG
        fg = C_SUCCESS if is_success else C_ERROR
        infobar.configure(fg_color=bg)
        lbl_info_msg.configure(text=msg, text_color=fg)
        root.after(3500, lambda: (infobar.configure(fg_color=C_CARD_BG),
                                   lbl_info_msg.configure(text="Ready.", text_color=C_TEXT_SEC)))

    # --- BODY (SIDEBAR + MAIN CONTENT) ---
    main_body = ctk.CTkFrame(root, corner_radius=0, fg_color=C_WIN_BG)
    main_body.pack(fill="both", expand=True)

    sidebar = ctk.CTkFrame(main_body, width=200, corner_radius=0, fg_color=C_SIDEBAR_BG,
                           border_width=1, border_color=C_BORDER)
    sidebar.pack(fill="y", side="left")
    sidebar.pack_propagate(False)

    content_viewport = ctk.CTkFrame(main_body, corner_radius=0, fg_color=C_WIN_BG)
    content_viewport.pack(fill="both", expand=True, padx=20, pady=16)

    pages = {
        "finances": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "founder": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "personnel": ctk.CTkFrame(content_viewport, fg_color="transparent"),
        "projects": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "research": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "world": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "hotkeys": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
    }

    current_page = ["finances"]
    nav_buttons = {}
    page_switch_callbacks = {}

    def switch_page(target: str):
        current_page[0] = target
        for p_name, frame in pages.items():
            if p_name == target:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

        for p_name, btn in nav_buttons.items():
            if p_name == target:
                btn.configure(fg_color=C_CARD_BG, text_color=C_ACCENT, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=C_TEXT_PRI, font=ctk.CTkFont(family="Segoe UI", size=12))

        if target in page_switch_callbacks:
            page_switch_callbacks[target]()

    lbl_nav = ctk.CTkLabel(sidebar, text="Navigation", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                           text_color=C_TEXT_MUTED)
    lbl_nav.pack(anchor="w", padx=16, pady=(16, 6))

    nav_items = [
        ("finances", "Finances"),
        ("founder", "Founder Profile"),
        ("personnel", "Personnel & Teams"),
        ("projects", "Projects & Software"),
        ("research", "Research & Patents"),
        ("world", "World & Rules"),
        ("hotkeys", "Hotkeys"),
    ]

    for key, label in nav_items:
        btn = ctk.CTkButton(sidebar, text=label, anchor="w", font=ctk.CTkFont(family="Segoe UI", size=12),
                            height=34, corner_radius=6, fg_color="transparent", text_color=C_TEXT_PRI,
                            hover_color=C_CARD_HOVER, command=lambda k=key: switch_page(k))
        btn.pack(fill="x", padx=8, pady=1)
        nav_buttons[key] = btn

    # Sidebar Quick Toggles
    lbl_toggles = ctk.CTkLabel(sidebar, text="Quick Controls", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                               text_color=C_TEXT_MUTED)
    lbl_toggles.pack(anchor="w", padx=16, pady=(24, 6))

    def on_freeze_toggle():
        if freeze_needs_var.get():
            show_infobar("Personnel needs lock active (100% Energy / 0% Stress)")
        else:
            show_infobar("Personnel needs lock disabled")

    sw_freeze = ctk.CTkSwitch(sidebar, text="Freeze Needs", font=ctk.CTkFont(family="Segoe UI", size=11),
                              variable=freeze_needs_var, command=on_freeze_toggle, progress_color=C_ACCENT)
    sw_freeze.pack(anchor="w", padx=16, pady=4)

    def on_turbo_toggle():
        spd = 5.0 if turbo_speed_var.get() else 1.0
        game.set_game_speed(spd)
        show_infobar(f"Simulation speed set to {spd:g}x")

    sw_turbo = ctk.CTkSwitch(sidebar, text="Turbo Speed (5x)", font=ctk.CTkFont(family="Segoe UI", size=11),
                             variable=turbo_speed_var, command=on_turbo_toggle, progress_color=C_ACCENT)
    sw_turbo.pack(anchor="w", padx=16, pady=4)

    btn_quick_god = ctk.CTkButton(sidebar, text="Boost All Personnel", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                  height=32, corner_radius=6, fg_color=C_BTN_SEC, text_color=C_TEXT_PRI,
                                  hover_color=C_BTN_SEC_HOVER,
                                  command=lambda: (game.max_all_employees_needs(), game.max_all_employees_skills(), game.max_all_employees_specs(3), game.remove_all_personnel_weaknesses(), show_infobar("Restored needs, skills, and stripped weaknesses for all personnel"), update_telemetry()))
    btn_quick_god.pack(fill="x", padx=12, pady=(16, 12))

    # =========================================================
    # PAGE 1: FINANCES
    # =========================================================
    p_fin = pages["finances"]

    ctk.CTkLabel(p_fin, text="Finances", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_fin, text="Manage company capital, valuation, fans, and market reputation.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    grid_metrics = ctk.CTkFrame(p_fin, fg_color="transparent")
    grid_metrics.pack(fill="x", pady=(0, 12))
    grid_metrics.columnconfigure((0, 1, 2), weight=1, uniform="metrics")

    # Card: Treasury
    c_money = ctk.CTkFrame(grid_metrics, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    c_money.grid(row=0, column=0, padx=4, sticky="nsew", ipady=8)
    ctk.CTkLabel(c_money, text="Company Treasury", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_SEC).pack(anchor="w", padx=14, pady=(10, 0))
    lbl_fin_money = ctk.CTkLabel(c_money, text="$0.00", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI)
    lbl_fin_money.pack(anchor="w", padx=14, pady=(2, 6))
    row_m_btns = ctk.CTkFrame(c_money, fg_color="transparent")
    row_m_btns.pack(fill="x", padx=10, pady=(0, 6))
    ctk.CTkButton(row_m_btns, text="+$1M", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.add_money(1000000), show_infobar("Added $1,000,000 to treasury"), update_telemetry())).pack(side="left", padx=2, expand=True, fill="x")
    ctk.CTkButton(row_m_btns, text="+$10M", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.add_money(10000000), show_infobar("Added $10,000,000 to treasury"), update_telemetry())).pack(side="left", padx=2, expand=True, fill="x")
    ctk.CTkButton(row_m_btns, text="+$100M", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER,
                  command=lambda: (game.add_money(100000000), show_infobar("Added $100,000,000 to treasury"), update_telemetry())).pack(side="left", padx=2, expand=True, fill="x")

    # Card: Fans
    c_fans = ctk.CTkFrame(grid_metrics, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    c_fans.grid(row=0, column=1, padx=4, sticky="nsew", ipady=8)
    ctk.CTkLabel(c_fans, text="Community Fans", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_SEC).pack(anchor="w", padx=14, pady=(10, 0))
    lbl_fin_fans = ctk.CTkLabel(c_fans, text="0", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI)
    lbl_fin_fans.pack(anchor="w", padx=14, pady=(2, 6))
    row_f_btns = ctk.CTkFrame(c_fans, fg_color="transparent")
    row_f_btns.pack(fill="x", padx=10, pady=(0, 6))
    ctk.CTkButton(row_f_btns, text="+10,000", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.add_fans(10000), show_infobar("Added 10,000 fans"), update_telemetry())).pack(side="left", padx=2, expand=True, fill="x")
    ctk.CTkButton(row_f_btns, text="+100,000", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.add_fans(100000), show_infobar("Added 100,000 fans"), update_telemetry())).pack(side="left", padx=2, expand=True, fill="x")
    ctk.CTkButton(row_f_btns, text="+1,000,000", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.add_fans(1000000), show_infobar("Added 1,000,000 fans"), update_telemetry())).pack(side="left", padx=2, expand=True, fill="x")

    # Card: Reputation
    c_rep = ctk.CTkFrame(grid_metrics, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    c_rep.grid(row=0, column=2, padx=4, sticky="nsew", ipady=8)
    ctk.CTkLabel(c_rep, text="Business Reputation", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_SEC).pack(anchor="w", padx=14, pady=(10, 0))
    lbl_fin_rep = ctk.CTkLabel(c_rep, text="0.0%", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI)
    lbl_fin_rep.pack(anchor="w", padx=14, pady=(2, 6))
    bar_rep = ctk.CTkProgressBar(c_rep, height=6, progress_color=C_ACCENT)
    bar_rep.set(0.75)
    bar_rep.pack(fill="x", padx=14, pady=(0, 6))
    ctk.CTkButton(c_rep, text="Set 100% Reputation", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.set_business_rep(1.0), show_infobar("Business reputation set to 100%"), update_telemetry())).pack(fill="x", padx=12, pady=(0, 6))

    # Exact Balance Override
    sc_custom = ctk.CTkFrame(p_fin, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_custom.pack(fill="x", pady=6, ipady=8)

    ctk.CTkLabel(sc_custom, text="Exact Balance Override", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=16, pady=(10, 2))
    ctk.CTkLabel(sc_custom, text="Directly assign an exact monetary figure to the primary corporate account.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w", padx=16, pady=(0, 8))

    row_entry = ctk.CTkFrame(sc_custom, fg_color="transparent")
    row_entry.pack(fill="x", padx=16, pady=(0, 8))

    entry_custom_money = ctk.CTkEntry(row_entry, height=34, font=ctk.CTkFont(family="Segoe UI", size=12), placeholder_text="Enter cash balance (e.g. 50000000)")
    entry_custom_money.insert(0, "50000000")
    entry_custom_money.pack(side="left", fill="x", expand=True, padx=(0, 10))

    def on_set_custom_money():
        try:
            val = float(entry_custom_money.get().replace(",", "").replace("$", ""))
            game.set_money(val)
            show_infobar(f"Bank balance set to ${val:,.2f}")
            update_telemetry()
        except ValueError:
            show_infobar("Invalid numerical amount entered.", is_success=False)

    ctk.CTkButton(row_entry, text="Set Balance", width=120, height=34, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER,
                  command=on_set_custom_money).pack(side="right")

    # Solvency & Presets
    sc_solvency = ctk.CTkFrame(p_fin, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_solvency.pack(fill="x", pady=6, ipady=8)

    ctk.CTkLabel(sc_solvency, text="Corporate Solvency & Presets", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=16, pady=(10, 2))
    ctk.CTkLabel(sc_solvency, text="Clear bankruptcy flags or allocate standard enterprise capital reserves.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w", padx=16, pady=(0, 8))

    row_preset_btns = ctk.CTkFrame(sc_solvency, fg_color="transparent")
    row_preset_btns.pack(fill="x", padx=16, pady=(0, 8))

    ctk.CTkButton(row_preset_btns, text="Clear Bankruptcy Status", height=32, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.clear_bankruptcy(), show_infobar("Bankruptcy status cleared"), update_telemetry())).pack(side="left", expand=True, fill="x", padx=4)
    ctk.CTkButton(row_preset_btns, text="$250,000,000 Reserve", height=32, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.set_money(250000000), show_infobar("Assigned $250,000,000 corporate reserve"), update_telemetry())).pack(side="left", expand=True, fill="x", padx=4)
    ctk.CTkButton(row_preset_btns, text="$1,000,000,000 Reserve", height=32, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.set_money(1000000000), show_infobar("Assigned $1,000,000,000 enterprise reserve"), update_telemetry())).pack(side="left", expand=True, fill="x", padx=4)

    # =========================================================
    # PAGE 2: FOUNDER PROFILE
    # =========================================================
    p_fnd = pages["founder"]

    ctk.CTkLabel(p_fnd, text="Founder Profile", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_fnd, text="Inspect and enhance company founder attributes, needs, skills, and specializations.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    sc_fnd_hdr = ctk.CTkFrame(p_fnd, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_fnd_hdr.pack(fill="x", pady=(0, 10), ipady=8)

    row_fnd_info = ctk.CTkFrame(sc_fnd_hdr, fg_color="transparent")
    row_fnd_info.pack(fill="x", padx=16, pady=(10, 4))

    lbl_fnd_name = ctk.CTkLabel(row_fnd_info, text="Founder: N/A", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), text_color=C_TEXT_PRI)
    lbl_fnd_name.pack(side="left")

    lbl_fnd_sub = ctk.CTkLabel(sc_fnd_hdr, text="Chief Executive Officer | Team: Core", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC)
    lbl_fnd_sub.pack(anchor="w", padx=16, pady=(0, 8))

    row_fnd_actions = ctk.CTkFrame(sc_fnd_hdr, fg_color="transparent")
    row_fnd_actions.pack(fill="x", padx=16, pady=(0, 8))

    def on_founder_godmode():
        f = game.get_founder()
        if f:
            game.max_employee_needs(f["emp_ptr"])
            game.max_employee_skills(f["emp_ptr"])
            game.remove_employee_weaknesses(f["emp_ptr"])
            show_infobar(f"Restored 100% needs, skills, and removed weaknesses for Founder '{f['name']}'")
            update_telemetry()

    def on_founder_max_specs():
        f = game.get_founder()
        if f:
            count = game.max_employee_specs(f["emp_ptr"], 3)
            show_infobar(f"Elevated {count} specializations to Level 3 for Founder '{f['name']}'")
            update_telemetry()

    def on_founder_add_exp():
        f = game.get_founder()
        if f:
            game.add_employee_spec_exp(f["emp_ptr"], 50.0)
            show_infobar(f"Added +50 Specialization EXP for Founder '{f['name']}'")
            update_telemetry()

    ctk.CTkButton(row_fnd_actions, text="Restore Needs & Skills", height=32, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER,
                  command=on_founder_godmode).pack(side="left", expand=True, fill="x", padx=3)
    ctk.CTkButton(row_fnd_actions, text="Elevate All Specs (3 Stars)", height=32, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=on_founder_max_specs).pack(side="left", expand=True, fill="x", padx=3)
    ctk.CTkButton(row_fnd_actions, text="Add +50 Spec EXP", height=32, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=on_founder_add_exp).pack(side="left", expand=True, fill="x", padx=3)

    # Founder Vitals Card
    sc_fnd_vitals = ctk.CTkFrame(p_fnd, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_fnd_vitals.pack(fill="x", pady=6, ipady=8)

    ctk.CTkLabel(sc_fnd_vitals, text="Vitals & Wellbeing", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=16, pady=(10, 8))

    grid_vitals = ctk.CTkFrame(sc_fnd_vitals, fg_color="transparent")
    grid_vitals.pack(fill="x", padx=16, pady=(0, 6))
    grid_vitals.columnconfigure((0, 1), weight=1, uniform="vitals")

    lbl_f_energy = ctk.CTkLabel(grid_vitals, text="Energy: 100%", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI)
    lbl_f_energy.grid(row=0, column=0, sticky="w", pady=2)
    bar_f_energy = ctk.CTkProgressBar(grid_vitals, height=6, progress_color=C_ACCENT)
    bar_f_energy.set(1.0)
    bar_f_energy.grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(0, 8))

    lbl_f_stress = ctk.CTkLabel(grid_vitals, text="Stress: 0%", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI)
    lbl_f_stress.grid(row=0, column=1, sticky="w", pady=2)
    bar_f_stress = ctk.CTkProgressBar(grid_vitals, height=6, progress_color=C_ERROR)
    bar_f_stress.set(0.0)
    bar_f_stress.grid(row=1, column=1, sticky="ew", pady=(0, 8))

    lbl_f_sat = ctk.CTkLabel(grid_vitals, text="Satisfaction: 200%", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI)
    lbl_f_sat.grid(row=2, column=0, sticky="w", pady=2)
    bar_f_sat = ctk.CTkProgressBar(grid_vitals, height=6, progress_color=C_ACCENT)
    bar_f_sat.set(1.0)
    bar_f_sat.grid(row=3, column=0, sticky="ew", padx=(0, 12), pady=(0, 8))

    lbl_f_creativity = ctk.CTkLabel(grid_vitals, text="Creativity: 100%", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI)
    lbl_f_creativity.grid(row=2, column=1, sticky="w", pady=2)
    bar_f_creativity = ctk.CTkProgressBar(grid_vitals, height=6, progress_color=C_ACCENT)
    bar_f_creativity.set(1.0)
    bar_f_creativity.grid(row=3, column=1, sticky="ew", pady=(0, 8))

    # Founder Role Specializations Card
    sc_fnd_specs = ctk.CTkFrame(p_fnd, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_fnd_specs.pack(fill="both", expand=True, pady=6, ipady=8)

    ctk.CTkLabel(sc_fnd_specs, text="Specializations by Role", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=16, pady=(10, 8))

    f_roles_container = ctk.CTkFrame(sc_fnd_specs, fg_color="transparent")
    f_roles_container.pack(fill="both", expand=True, padx=16, pady=(0, 8))

    f_role_widgets = {}
    for rname in GameMemory.ROLE_NAMES:
        r_card = ctk.CTkFrame(f_roles_container, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
        r_card.pack(fill="x", pady=2, ipady=3)
        lbl_r_title = ctk.CTkLabel(r_card, text=f"{rname} (Base Skill: 100%)", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI)
        lbl_r_title.pack(anchor="w", padx=10, pady=(3, 1))
        lbl_r_specs = ctk.CTkLabel(r_card, text="No active specializations", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
        lbl_r_specs.pack(anchor="w", padx=10, pady=(0, 4))
        f_role_widgets[rname] = (lbl_r_title, lbl_r_specs)

    # =========================================================
    # PAGE 3: PERSONNEL & TEAMS (DEEP PERSONNEL EDITOR)
    # =========================================================
    p_emp = pages["personnel"]

    # Header Toolbar
    toolbar = ctk.CTkFrame(p_emp, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    toolbar.pack(fill="x", pady=(0, 8), ipady=6)

    row_tb_top = ctk.CTkFrame(toolbar, fg_color="transparent")
    row_tb_top.pack(fill="x", padx=14, pady=(6, 4))

    entry_search = ctk.CTkEntry(row_tb_top, height=32, width=220, font=ctk.CTkFont(family="Segoe UI", size=11),
                                placeholder_text="Search personnel...", textvariable=search_query_var)
    entry_search.pack(side="left", padx=(0, 8))

    ctk.CTkLabel(row_tb_top, text="Team:", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(side="left", padx=(4, 4))
    opt_team = ctk.CTkOptionMenu(row_tb_top, variable=selected_team_filter, height=32, width=140,
                                 font=ctk.CTkFont(family="Segoe UI", size=11),
                                 fg_color=C_BTN_SEC, text_color=C_TEXT_PRI,
                                 button_color=C_BTN_SEC, button_hover_color=C_BTN_SEC_HOVER,
                                 values=["All Teams"])
    opt_team.pack(side="left", padx=(0, 10))

    lbl_emp_count_badge = ctk.CTkLabel(row_tb_top, text="0 Personnel",
                                       font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                       fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, corner_radius=4, padx=8, pady=3)
    lbl_emp_count_badge.pack(side="left")

    btn_refresh = ctk.CTkButton(row_tb_top, text="↻ Refresh Roster", width=120, height=32,
                                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER)
    btn_refresh.pack(side="right")

    # Global Batch Actions Row
    row_batch = ctk.CTkFrame(toolbar, fg_color="transparent")
    row_batch.pack(fill="x", padx=14, pady=(4, 6))

    ctk.CTkButton(row_batch, text="Restore All Needs", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_employees_needs(), show_infobar("Restored needs for all personnel"), refresh_personnel_data())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="Max All Skills", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_employees_skills(), show_infobar("Maxed base skills for all personnel"), refresh_personnel_data())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="Elevate All Specs (3★)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_employees_specs(3), show_infobar("Elevated specializations to Level 3 for all personnel"), refresh_personnel_data())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="+10 Points to All", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.add_all_employees_spec_exp(10.0), show_infobar("Added +10 specialization points across all roles for all personnel"), refresh_personnel_data())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="Remove All Weaknesses", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (show_infobar(f"Removed {game.remove_all_personnel_weaknesses()} weaknesses across company personnel"), refresh_personnel_data())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="Free Labor ($0)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.set_all_employees_free_salary(), show_infobar("Assigned $0 salary to all personnel"), refresh_personnel_data())).pack(side="left", expand=True, fill="x", padx=2)

    # Master-Detail Split Container
    row_master_detail = ctk.CTkFrame(p_emp, fg_color="transparent")
    row_master_detail.pack(fill="both", expand=True)

    # Left: Roster List
    frame_roster = ctk.CTkScrollableFrame(row_master_detail, fg_color=C_CARD_BG, corner_radius=8,
                                          border_width=1, border_color=C_BORDER)
    frame_roster.pack(side="left", fill="both", expand=True, padx=(0, 8))

    # Right: Personnel Inspector & Editor Panel
    frame_inspector = ctk.CTkFrame(row_master_detail, width=420, fg_color=C_CARD_BG, corner_radius=8,
                                   border_width=1, border_color=C_BORDER)
    frame_inspector.pack(side="right", fill="both")
    frame_inspector.pack_propagate(False)

    # Inspector Header
    ctk.CTkLabel(frame_inspector, text="Personnel Editor & Inspector", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_SEC).pack(anchor="w", padx=14, pady=(10, 2))
    lbl_insp_name = ctk.CTkLabel(frame_inspector, text="Select an employee", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color=C_TEXT_PRI)
    lbl_insp_name.pack(anchor="w", padx=14)
    lbl_insp_team = ctk.CTkLabel(frame_inspector, text="Team: N/A | Salary: $0", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC)
    lbl_insp_team.pack(anchor="w", padx=14, pady=(0, 6))

    # Subtab Segmented Switcher inside Inspector
    subtab_bar = ctk.CTkSegmentedButton(frame_inspector, values=["Overview", "Needs", "Skills & Points", "Specializations", "Traits"],
                                        height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"))
    subtab_bar.pack(fill="x", padx=12, pady=(0, 8))
    subtab_bar.set("Overview")

    # Inspector Sub-Frames
    insp_views = {
        "overview": ctk.CTkScrollableFrame(frame_inspector, fg_color="transparent"),
        "needs": ctk.CTkScrollableFrame(frame_inspector, fg_color="transparent"),
        "skills": ctk.CTkScrollableFrame(frame_inspector, fg_color="transparent"),
        "specs": ctk.CTkScrollableFrame(frame_inspector, fg_color="transparent"),
        "traits": ctk.CTkScrollableFrame(frame_inspector, fg_color="transparent"),
    }

    subtab_map = {
        "overview": "overview",
        "needs": "needs",
        "skills & points": "skills",
        "skills & exp": "skills",
        "skills": "skills",
        "specializations": "specs",
        "specialization": "specs",
        "specs": "specs",
        "traits": "traits",
    }

    def switch_insp_subtab(tab_name: str):
        target = subtab_map.get(tab_name.lower().strip(), "overview")
        insp_subtab[0] = target
        for k, v in insp_views.items():
            if k == target:
                v.pack(fill="both", expand=True, padx=8, pady=(0, 6))
            else:
                v.pack_forget()

    subtab_bar.configure(command=switch_insp_subtab)

    # 1. Sub-Frame: Overview
    f_ov = insp_views["overview"]
    f_ov.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    row_ov_actions = ctk.CTkFrame(f_ov, fg_color="transparent")
    row_ov_actions.pack(fill="x", pady=2)

    # Personnel State & Cache
    cached_employees = []
    card_widgets = {}
    spec_btn_cache = {}
    trait_sw_cache = {}
    exp_labels = {}
    exp_entries = {}
    lbl_ov_pts_summary = None
    lbl_ov_pts_breakdown = None
    lbl_sp_avail_pts = None

    def update_points_display_in_inspector(e: dict):
        if not e:
            return
        tot_pts = int(sum(e.get("spec_exp", [])))
        tot_used = int(sum(e.get("spec_used", [])))
        e["total_points"] = tot_pts
        e["total_used"] = tot_used

        # Inspector Header
        lbl_insp_team.configure(text=f"Team: {e['team']} | Salary: ${e['salary']:,.0f}/mo | {tot_pts} Pts Available")

        # Overview Points card
        if lbl_ov_pts_summary:
            lbl_ov_pts_summary.configure(text=f"Available: {tot_pts} Pts | Allocated: {tot_used}")
        if lbl_ov_pts_breakdown:
            roles_str = "  ".join(f"{GameMemory.ROLE_NAMES[i][:4]}: {e['spec_exp'][i]:.0f}" for i in range(min(5, len(e.get('spec_exp', [])))))
            lbl_ov_pts_breakdown.configure(text=roles_str)

        # Tab 3: Skills & Points
        for r_idx, lbl in exp_labels.items():
            val = e["spec_exp"][r_idx] if r_idx < len(e["spec_exp"]) else 0.0
            used = e["spec_used"][r_idx] if r_idx < len(e["spec_used"]) else 0
            lbl.configure(text=f"Unspent: {val:.1f} pts  |  Allocated: {used}")
            if r_idx in exp_entries:
                try:
                    if frame_inspector.focus_get() != exp_entries[r_idx]:
                        exp_entries[r_idx].delete(0, "end")
                        exp_entries[r_idx].insert(0, f"{val:.0f}")
                except Exception:
                    pass

        # Tab 4: Specializations
        if lbl_sp_avail_pts:
            lbl_sp_avail_pts.configure(text=f"Available Points to Spend: {tot_pts}  (Allocated: {tot_used})")

        # Update Roster Card vitals
        if e["actor_ptr"] in card_widgets:
            w_count = len(e["weaknesses"])
            w_text = f" | {w_count} Weak" if w_count > 0 else ""
            w_col = C_ERROR if w_count > 0 else C_TEXT_SEC
            pts_text = f" | {tot_pts} Pts" if tot_pts > 0 else ""
            card_widgets[e["actor_ptr"]]["vitals"].configure(
                text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}% | ${e['salary']:,.0f}{w_text}{pts_text}",
                text_color=w_col
            )

    def on_ov_add_pts(delta: float):
        e = current_selected_emp[0]
        if not e:
            show_infobar("Select an employee first", is_success=False)
            return
        game.add_employee_spec_exp(e["emp_ptr"], delta)
        for i in range(len(e["spec_exp"])):
            e["spec_exp"][i] += delta
        update_points_display_in_inspector(e)
        show_infobar(f"Added +{delta:.0f} points across all roles to {e['name']}")

    def on_ov_max_pts():
        e = current_selected_emp[0]
        if not e:
            show_infobar("Select an employee first", is_success=False)
            return
        game.set_all_employee_spec_points(e["emp_ptr"], 50.0)
        for i in range(len(e["spec_exp"])):
            e["spec_exp"][i] = 50.0
        update_points_display_in_inspector(e)
        show_infobar(f"Maxed points (50 pts per role) for {e['name']}")

    def on_ov_refund_used():
        e = current_selected_emp[0]
        if not e:
            show_infobar("Select an employee first", is_success=False)
            return
        game.reset_employee_spec_used(e["emp_ptr"])
        for i in range(len(e["spec_used"])):
            e["spec_used"][i] = 0
        update_points_display_in_inspector(e)
        show_infobar(f"Reset allocated points for {e['name']} (unlocked capacity)")

    def on_insp_godmode():
        e = current_selected_emp[0]
        if not e:
            show_infobar("Select an employee first", is_success=False)
            return
        game.max_employee_needs(e["emp_ptr"])
        game.max_employee_skills(e["emp_ptr"])
        game.max_employee_specs(e["emp_ptr"], 3)
        game.remove_employee_weaknesses(e["emp_ptr"])
        game.add_employee_spec_exp(e["emp_ptr"], 25.0)

        # Update in-memory state
        e["energy"] = 1.0
        e["stress"] = 0.0
        e["satisfaction"] = 2.0
        e["creativity"] = 1.0
        e["hunger"] = 1.0
        e["social"] = 1.0
        e["bladder"] = 1.0
        e["skills"] = [1.0] * 5
        e["traits_mask"] &= ~GameMemory.BAD_TRAITS_MASK
        e["weaknesses"] = []
        for r_idx in range(len(e["spec_exp"])):
            e["spec_exp"][r_idx] += 25.0
        for rname in GameMemory.ROLE_NAMES:
            if rname in e["specs"]:
                for sk in e["specs"][rname]:
                    e["specs"][rname][sk] = 3

        select_employee_for_inspector(e, full_rebuild=False)
        update_points_display_in_inspector(e)
        show_infobar(f"Restored needs, skills, and added +25 points for {e['name']}")

    def on_insp_salary_toggle():
        e = current_selected_emp[0]
        if not e:
            show_infobar("Select an employee first", is_success=False)
            return
        new_sal = 0.0 if e["salary"] > 0 else 1000.0
        game.set_employee_salary(e["emp_ptr"], new_sal)
        e["salary"] = new_sal
        update_points_display_in_inspector(e)
        entry_sal.delete(0, "end")
        entry_sal.insert(0, f"{new_sal:.0f}")
        show_infobar(f"Assigned ${new_sal:,.0f} salary to {e['name']}")

    ctk.CTkButton(row_ov_actions, text="Restore Needs & Skills", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=on_insp_godmode).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_ov_actions, text="Free Labor ($0)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=on_insp_salary_toggle).pack(side="left", expand=True, fill="x", padx=2)

    # Overview Quick Summary Card
    c_ov_vitals = ctk.CTkFrame(f_ov, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
    c_ov_vitals.pack(fill="x", pady=6, ipady=4)
    lbl_ov_v1 = ctk.CTkLabel(c_ov_vitals, text="Energy: 100% | Stress: 0%", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI)
    lbl_ov_v1.pack(anchor="w", padx=10, pady=2)
    lbl_ov_v2 = ctk.CTkLabel(c_ov_vitals, text="Satisfaction: 150% | Creativity: 100%", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
    lbl_ov_v2.pack(anchor="w", padx=10, pady=2)

    # Overview Specialization Points Card
    c_ov_pts = ctk.CTkFrame(f_ov, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
    c_ov_pts.pack(fill="x", pady=4, ipady=4)
    row_ov_pts_hdr = ctk.CTkFrame(c_ov_pts, fg_color="transparent")
    row_ov_pts_hdr.pack(fill="x", padx=10, pady=(4, 2))
    ctk.CTkLabel(row_ov_pts_hdr, text="Specialization Points", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")
    lbl_ov_pts_summary = ctk.CTkLabel(row_ov_pts_hdr, text="Available: 0 Pts | Allocated: 0", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_ACCENT)
    lbl_ov_pts_summary.pack(side="right")

    lbl_ov_pts_breakdown = ctk.CTkLabel(c_ov_pts, text="Lead: 0  Code: 0  Des: 0  Art: 0  Serv: 0", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
    lbl_ov_pts_breakdown.pack(anchor="w", padx=10, pady=(1, 4))

    row_ov_pts_btns = ctk.CTkFrame(c_ov_pts, fg_color="transparent")
    row_ov_pts_btns.pack(fill="x", padx=8, pady=(0, 4))

    ctk.CTkButton(row_ov_pts_btns, text="+5 Pts (All)", height=24, font=ctk.CTkFont(family="Segoe UI", size=9),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=lambda: on_ov_add_pts(5.0)).pack(side="left", expand=True, fill="x", padx=1)
    ctk.CTkButton(row_ov_pts_btns, text="+10 Pts (All)", height=24, font=ctk.CTkFont(family="Segoe UI", size=9),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=lambda: on_ov_add_pts(10.0)).pack(side="left", expand=True, fill="x", padx=1)
    ctk.CTkButton(row_ov_pts_btns, text="Max (50)", height=24, font=ctk.CTkFont(family="Segoe UI", size=9),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=on_ov_max_pts).pack(side="left", expand=True, fill="x", padx=1)
    ctk.CTkButton(row_ov_pts_btns, text="Refund Used", height=24, font=ctk.CTkFont(family="Segoe UI", size=9),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=on_ov_refund_used).pack(side="left", expand=True, fill="x", padx=1)

    # Overview Traits & Weaknesses Preview
    c_ov_traits = ctk.CTkFrame(f_ov, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
    c_ov_traits.pack(fill="x", pady=4, ipady=4)
    ctk.CTkLabel(c_ov_traits, text="Traits & Weaknesses", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=10, pady=(4, 2))
    lbl_ov_goods = ctk.CTkLabel(c_ov_traits, text="Good Traits: None", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
    lbl_ov_goods.pack(anchor="w", padx=10, pady=1)
    lbl_ov_bads = ctk.CTkLabel(c_ov_traits, text="Weaknesses: None", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_ERROR)
    lbl_ov_bads.pack(anchor="w", padx=10, pady=(1, 4))

    # Overview Salary Editor
    c_ov_sal = ctk.CTkFrame(f_ov, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
    c_ov_sal.pack(fill="x", pady=4, ipady=4)
    ctk.CTkLabel(c_ov_sal, text="Custom Monthly Salary", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=10, pady=(4, 2))
    row_sal_edit = ctk.CTkFrame(c_ov_sal, fg_color="transparent")
    row_sal_edit.pack(fill="x", padx=10, pady=(0, 4))
    entry_sal = ctk.CTkEntry(row_sal_edit, height=28, font=ctk.CTkFont(family="Segoe UI", size=11), placeholder_text="Enter salary (e.g. 1000)")
    entry_sal.pack(side="left", fill="x", expand=True, padx=(0, 6))

    def on_apply_salary():
        e = current_selected_emp[0]
        if not e:
            return
        try:
            val = float(entry_sal.get().replace(",", "").replace("$", ""))
            game.set_employee_salary(e["emp_ptr"], val)
            e["salary"] = val
            lbl_insp_team.configure(text=f"Team: {e['team']} | Salary: ${val:,.0f}/mo")
            if e["actor_ptr"] in card_widgets:
                w_count = len(e["weaknesses"])
                w_text = f" | {w_count} Weak" if w_count > 0 else ""
                w_col = C_ERROR if w_count > 0 else C_TEXT_SEC
                card_widgets[e["actor_ptr"]]["vitals"].configure(
                    text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}% | ${val:,.0f}{w_text}",
                    text_color=w_col
                )
            show_infobar(f"Assigned ${val:,.0f} salary to {e['name']}")
        except ValueError:
            show_infobar("Invalid numerical amount entered", is_success=False)

    ctk.CTkButton(row_sal_edit, text="Apply Salary", width=90, height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=on_apply_salary).pack(side="right")

    # 2. Sub-Frame: Needs & Vitals Editor
    f_needs = insp_views["needs"]
    needs_sliders = {}
    needs_labels = {}

    def make_need_slider(parent, need_key, display_name, max_val=1.0):
        c = ctk.CTkFrame(parent, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
        c.pack(fill="x", pady=3, ipady=3)
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(2, 0))
        lbl_n = ctk.CTkLabel(row, text=display_name, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI)
        lbl_n.pack(side="left")
        lbl_v = ctk.CTkLabel(row, text="100%", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
        lbl_v.pack(side="right")
        needs_labels[need_key] = lbl_v

        def on_slide(val, k=need_key, mv=max_val, lv=lbl_v):
            pct = int((val / mv) * 100)
            lv.configure(text=f"{pct}%")
            e = current_selected_emp[0]
            if e:
                e[k] = val
                game.set_employee_need(e["emp_ptr"], k, val)
                if k in ("energy", "stress") and e["actor_ptr"] in card_widgets:
                    w_count = len(e["weaknesses"])
                    w_text = f" | {w_count} Weak" if w_count > 0 else ""
                    w_col = C_ERROR if w_count > 0 else C_TEXT_SEC
                    card_widgets[e["actor_ptr"]]["vitals"].configure(
                        text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}% | ${e['salary']:,.0f}{w_text}",
                        text_color=w_col
                    )

        sl = ctk.CTkSlider(c, from_=0.0, to=max_val, command=on_slide, progress_color=C_ACCENT, height=14)
        sl.pack(fill="x", padx=10, pady=(2, 6))
        needs_sliders[need_key] = sl

    make_need_slider(f_needs, "energy", "Energy (Stamina)", 1.0)
    make_need_slider(f_needs, "stress", "Stress (Fatigue Level)", 1.0)
    make_need_slider(f_needs, "satisfaction", "Job Satisfaction", 2.0)
    make_need_slider(f_needs, "creativity", "Creativity & Inspiration", 1.0)
    make_need_slider(f_needs, "hunger", "Hunger / Nutrition", 1.0)
    make_need_slider(f_needs, "social", "Social Need", 1.0)
    make_need_slider(f_needs, "bladder", "Bladder Need", 1.0)

    # 3. Sub-Frame: Base Skills & EXP Editor
    f_skills = insp_views["skills"]
    skill_sliders = {}
    skill_labels = {}
    exp_labels = {}

    ctk.CTkLabel(f_skills, text="Foundational Base Skills (0% - 100%)", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=4, pady=(2, 4))
    for r_idx, rname in enumerate(GameMemory.ROLE_NAMES):
        c_sk = ctk.CTkFrame(f_skills, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
        c_sk.pack(fill="x", pady=2, ipady=2)
        row = ctk.CTkFrame(c_sk, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(2, 0))
        ctk.CTkLabel(row, text=rname, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")
        lbl_sv = ctk.CTkLabel(row, text="100%", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
        lbl_sv.pack(side="right")
        skill_labels[r_idx] = lbl_sv

        def on_skill_slide(val, idx=r_idx, lv=lbl_sv):
            pct = int(val * 100)
            lv.configure(text=f"{pct}%")
            e = current_selected_emp[0]
            if e:
                if idx < len(e["skills"]):
                    e["skills"][idx] = val
                game.set_employee_skill(e["emp_ptr"], idx, val)

        sl_sk = ctk.CTkSlider(c_sk, from_=0.0, to=1.0, command=on_skill_slide, progress_color=C_ACCENT, height=14)
        sl_sk.pack(fill="x", padx=10, pady=(2, 4))
        skill_sliders[r_idx] = sl_sk

    # Bulk points actions for current employee
    c_bulk_pts = ctk.CTkFrame(f_skills, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
    c_bulk_pts.pack(fill="x", pady=(10, 4), ipady=3)
    row_bp_hdr = ctk.CTkFrame(c_bulk_pts, fg_color="transparent")
    row_bp_hdr.pack(fill="x", padx=10, pady=(2, 2))
    ctk.CTkLabel(row_bp_hdr, text="Quick Points to All 5 Roles", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")
    row_bp_btns = ctk.CTkFrame(c_bulk_pts, fg_color="transparent")
    row_bp_btns.pack(fill="x", padx=8, pady=(2, 4))

    ctk.CTkButton(row_bp_btns, text="+5 All", height=24, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=lambda: on_ov_add_pts(5.0)).pack(side="left", expand=True, fill="x", padx=1)
    ctk.CTkButton(row_bp_btns, text="+10 All", height=24, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=lambda: on_ov_add_pts(10.0)).pack(side="left", expand=True, fill="x", padx=1)
    ctk.CTkButton(row_bp_btns, text="+25 All", height=24, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=lambda: on_ov_add_pts(25.0)).pack(side="left", expand=True, fill="x", padx=1)
    ctk.CTkButton(row_bp_btns, text="Refund Used", height=24, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=on_ov_refund_used).pack(side="left", expand=True, fill="x", padx=1)

    ctk.CTkLabel(f_skills, text="Specialization Points by Role", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=4, pady=(8, 4))
    for r_idx, rname in enumerate(GameMemory.ROLE_NAMES):
        c_exp = ctk.CTkFrame(f_skills, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
        c_exp.pack(fill="x", pady=2, ipady=3)
        row = ctk.CTkFrame(c_exp, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(2, 0))
        ctk.CTkLabel(row, text=f"■ {rname}", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")
        lbl_ev = ctk.CTkLabel(row, text="Unspent: 0.0 pts  |  Allocated: 0", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
        lbl_ev.pack(side="right")
        exp_labels[r_idx] = lbl_ev

        row_qbtns = ctk.CTkFrame(c_exp, fg_color="transparent")
        row_qbtns.pack(fill="x", padx=8, pady=(2, 2))

        def make_exp_adder(idx=r_idx, delta=5.0):
            def handler():
                e = current_selected_emp[0]
                if e:
                    cur = e["spec_exp"][idx] if idx < len(e["spec_exp"]) else 0.0
                    new_val = cur + delta
                    game.set_employee_spec_exp(e["emp_ptr"], idx, new_val)
                    if idx < len(e["spec_exp"]):
                        e["spec_exp"][idx] = new_val
                    update_points_display_in_inspector(e)
                    show_infobar(f"Added +{delta:g} pts to {GameMemory.ROLE_NAMES[idx]}")
            return handler

        ctk.CTkButton(row_qbtns, text="+1 Pt", height=22, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_exp_adder(r_idx, 1.0)).pack(side="left", expand=True, fill="x", padx=1)
        ctk.CTkButton(row_qbtns, text="+5 Pts", height=22, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_exp_adder(r_idx, 5.0)).pack(side="left", expand=True, fill="x", padx=1)
        ctk.CTkButton(row_qbtns, text="+10 Pts", height=22, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_exp_adder(r_idx, 10.0)).pack(side="left", expand=True, fill="x", padx=1)
        ctk.CTkButton(row_qbtns, text="Max (25)", height=22, font=ctk.CTkFont(family="Segoe UI", size=9), fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_exp_adder(r_idx, 25.0)).pack(side="left", expand=True, fill="x", padx=1)

        row_exact = ctk.CTkFrame(c_exp, fg_color="transparent")
        row_exact.pack(fill="x", padx=8, pady=(2, 4))
        ctk.CTkLabel(row_exact, text="Set Exact:", font=ctk.CTkFont(family="Segoe UI", size=9), text_color=C_TEXT_MUTED).pack(side="left", padx=(2, 4))
        ent_p = ctk.CTkEntry(row_exact, width=65, height=22, font=ctk.CTkFont(family="Segoe UI", size=10), placeholder_text="Points")
        ent_p.pack(side="left", padx=2)
        exp_entries[r_idx] = ent_p

        def make_exact_setter(idx=r_idx, ent=ent_p):
            def handler():
                e = current_selected_emp[0]
                if not e:
                    return
                try:
                    val = float(ent.get().strip())
                    if val < 0:
                        val = 0.0
                    game.set_employee_spec_exp(e["emp_ptr"], idx, val)
                    if idx < len(e["spec_exp"]):
                        e["spec_exp"][idx] = val
                    update_points_display_in_inspector(e)
                    show_infobar(f"Set {GameMemory.ROLE_NAMES[idx]} points to {val:.1f}")
                except ValueError:
                    show_infobar("Enter a valid number of points", is_success=False)
            return handler

        def make_zero_setter(idx=r_idx):
            def handler():
                e = current_selected_emp[0]
                if not e:
                    return
                game.set_employee_spec_exp(e["emp_ptr"], idx, 0.0)
                if idx < len(e["spec_exp"]):
                    e["spec_exp"][idx] = 0.0
                update_points_display_in_inspector(e)
                show_infobar(f"Reset {GameMemory.ROLE_NAMES[idx]} points to 0")
            return handler

        ctk.CTkButton(row_exact, text="Apply", width=55, height=22, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                      fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=make_exact_setter(r_idx, ent_p)).pack(side="left", padx=2)
        ctk.CTkButton(row_exact, text="Reset (0)", width=60, height=22, font=ctk.CTkFont(family="Segoe UI", size=9),
                      fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_zero_setter(r_idx)).pack(side="right", padx=2)

    # 4. Sub-Frame: Specializations Granular Editor
    f_specs = insp_views["specs"]

    row_sp_top = ctk.CTkFrame(f_specs, fg_color="transparent")
    row_sp_top.pack(fill="x", pady=(2, 4))
    ctk.CTkLabel(row_sp_top, text="Subfield Specializations", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")

    def on_elevate_selected_specs():
        e = current_selected_emp[0]
        if e:
            cnt = game.max_employee_specs(e["emp_ptr"], 3)
            for rname in GameMemory.ROLE_NAMES:
                r_dict = e["specs"].setdefault(rname, {})
                for sk in GameMemory.ROLE_ALL_SPECIALIZATIONS.get(rname, []):
                    r_dict[sk] = 3
            for (ridx, skey), btns in spec_btn_cache.items():
                for s_star, b in btns.items():
                    is_active = (s_star == 3)
                    b.configure(fg_color=C_ACCENT if is_active else C_BTN_SEC,
                                text_color=C_ACCENT_TEXT if is_active else C_TEXT_PRI)
            show_infobar(f"Elevated all 25 specializations to 3★ for {e['name']}")

    ctk.CTkButton(row_sp_top, text="Elevate All to 3★", height=26, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=on_elevate_selected_specs).pack(side="right")

    # Status card with available unspent points right at top of Specializations tab
    c_sp_status = ctk.CTkFrame(f_specs, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
    c_sp_status.pack(fill="x", pady=(0, 6), ipady=2)
    row_sps = ctk.CTkFrame(c_sp_status, fg_color="transparent")
    row_sps.pack(fill="x", padx=10, pady=3)
    lbl_sp_avail_pts = ctk.CTkLabel(row_sps, text="Available Points to Spend: 0", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_ACCENT)
    lbl_sp_avail_pts.pack(side="left")

    ctk.CTkButton(row_sps, text="+10 Pts (All)", width=90, height=22, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=lambda: on_ov_add_pts(10.0)).pack(side="right")

    frame_specs_grid = ctk.CTkFrame(f_specs, fg_color="transparent")
    frame_specs_grid.pack(fill="both", expand=True)

    # 5. Sub-Frame: Weaknesses & Traits Manager
    f_traits = insp_views["traits"]

    row_tr_top = ctk.CTkFrame(f_traits, fg_color="transparent")
    row_tr_top.pack(fill="x", pady=(2, 6))

    def on_strip_selected_weaknesses():
        e = current_selected_emp[0]
        if e:
            rem = game.remove_employee_weaknesses(e["emp_ptr"])
            e["traits_mask"] &= ~GameMemory.BAD_TRAITS_MASK
            e["weaknesses"] = []
            for tname, tbit, is_bad in GameMemory.ALL_TRAITS:
                if is_bad and tname in trait_sw_cache:
                    trait_sw_cache[tname][0].set(False)
            lbl_ov_bads.configure(text="Weaknesses: None (Clear)", text_color=C_SUCCESS)
            if e["actor_ptr"] in card_widgets:
                card_widgets[e["actor_ptr"]]["vitals"].configure(
                    text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}% | ${e['salary']:,.0f}",
                    text_color=C_TEXT_SEC
                )
            show_infobar(f"Removed {rem} weaknesses from {e['name']}")

    def on_grant_master_traits():
        e = current_selected_emp[0]
        if e:
            game.grant_master_traits(e["emp_ptr"])
            e["traits_mask"] = game.read_u64(e["emp_ptr"] + 0x150)
            e["goods"] = [t[0] for t in GameMemory.ALL_TRAITS if not t[2] and (e["traits_mask"] & t[1])]
            e["weaknesses"] = [t[0] for t in GameMemory.ALL_TRAITS if t[2] and (e["traits_mask"] & t[1])]
            for tname, tbit, is_bad in GameMemory.ALL_TRAITS:
                if tname in trait_sw_cache:
                    trait_sw_cache[tname][0].set(bool(e["traits_mask"] & tbit))
            goods_txt = ", ".join(e["goods"]) if e["goods"] else "None"
            lbl_ov_goods.configure(text=f"Good Traits: {goods_txt}")
            show_infobar(f"Granted master positive traits to {e['name']}")

    ctk.CTkButton(row_tr_top, text="Remove Weaknesses", height=26, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=on_strip_selected_weaknesses).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_tr_top, text="Grant Master Traits", height=26, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=on_grant_master_traits).pack(side="left", expand=True, fill="x", padx=2)

    ctk.CTkLabel(f_traits, text="All Available Traits (Toggle)", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(6, 4))
    frame_traits_checklist = ctk.CTkFrame(f_traits, fg_color="transparent")
    frame_traits_checklist.pack(fill="both", expand=True)

    # Rebuilding grids on demand (only when selecting a new employee)
    def rebuild_specs_grid(e: dict):
        for w in frame_specs_grid.winfo_children():
            w.destroy()
        spec_btn_cache.clear()

        for r_idx, rname in enumerate(GameMemory.ROLE_NAMES):
            specs = e["specs"].get(rname, {})
            all_fields = GameMemory.ROLE_ALL_SPECIALIZATIONS.get(rname, [])

            ctk.CTkLabel(frame_specs_grid, text=f"■ {rname} Specializations", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_ACCENT).pack(anchor="w", pady=(6, 2))

            for spec_key in all_fields:
                row_s = ctk.CTkFrame(frame_specs_grid, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
                row_s.pack(fill="x", pady=2, ipady=2)

                cur_lvl = specs.get(spec_key, 0)
                ctk.CTkLabel(row_s, text=spec_key, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(side="left", padx=8)

                row_stars = ctk.CTkFrame(row_s, fg_color="transparent")
                row_stars.pack(side="right", padx=6)

                spec_btn_cache[(r_idx, spec_key)] = {}

                for target_star in [0, 1, 2, 3]:
                    is_active = (cur_lvl == target_star)
                    b_col = C_ACCENT if is_active else C_BTN_SEC
                    t_col = C_ACCENT_TEXT if is_active else C_TEXT_PRI
                    btn_label = f"{target_star}★"

                    def make_spec_setter(ridx=r_idx, skey=spec_key, tlvl=target_star):
                        def handler():
                            emp = current_selected_emp[0]
                            if emp:
                                ok = game.set_employee_spec_level(emp["emp_ptr"], ridx, skey, tlvl)
                                if ok:
                                    emp["specs"].setdefault(GameMemory.ROLE_NAMES[ridx], {})[skey] = tlvl
                                    btns = spec_btn_cache.get((ridx, skey), {})
                                    for s_idx, b in btns.items():
                                        is_act = (s_idx == tlvl)
                                        b.configure(fg_color=C_ACCENT if is_act else C_BTN_SEC,
                                                    text_color=C_ACCENT_TEXT if is_act else C_TEXT_PRI)
                                    show_infobar(f"Set {skey} ({GameMemory.ROLE_NAMES[ridx]}) to {tlvl}★ for {emp['name']}")
                                else:
                                    show_infobar(f"Failed to update {skey} for {emp['name']}", is_success=False)
                        return handler

                    b = ctk.CTkButton(row_stars, text=btn_label, width=32, height=22, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                                      fg_color=b_col, text_color=t_col, hover_color=C_ACCENT_HOVER, command=make_spec_setter())
                    b.pack(side="left", padx=1)
                    spec_btn_cache[(r_idx, spec_key)][target_star] = b

        c_tip = ctk.CTkFrame(frame_specs_grid, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
        c_tip.pack(fill="x", pady=(10, 4), padx=2, ipady=4)
        ctk.CTkLabel(c_tip, text="💡 Direct Specialization Elevation (All 25 Subfields Unlocked)", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=10, pady=(4, 2))
        ctk.CTkLabel(c_tip, text="All disciplines (including 3D, Network, HR, Automation, etc.) can be directly set to any star rating (0★ to 3★) with zero in-game wait time or education courses required. Click 'Elevate All to 3★' above to instantly grant max level across all 25 subfields.",
                     font=ctk.CTkFont(family="Segoe UI", size=9), text_color=C_TEXT_SEC, justify="left", wraplength=370).pack(anchor="w", padx=10, pady=(2, 6))

    def rebuild_traits_grid(e: dict):
        for w in frame_traits_checklist.winfo_children():
            w.destroy()
        trait_sw_cache.clear()

        for tname, tbit, is_bad in GameMemory.ALL_TRAITS:
            is_enabled = bool(e["traits_mask"] & tbit)
            row_tr = ctk.CTkFrame(frame_traits_checklist, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
            row_tr.pack(fill="x", pady=1, ipady=1)

            type_tag = "[Weakness] " if is_bad else ""
            t_col = C_ERROR if is_bad else C_TEXT_PRI
            lbl_tr = ctk.CTkLabel(row_tr, text=f"{type_tag}{tname}", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold" if is_bad else "normal"), text_color=t_col)
            lbl_tr.pack(side="left", padx=8)

            var_tr = ctk.BooleanVar(value=is_enabled)

            def make_tr_toggler(t_name=tname, v=var_tr, bit=tbit, bad=is_bad):
                def handler():
                    emp = current_selected_emp[0]
                    if emp:
                        new_val = v.get()
                        game.set_employee_trait_toggle(emp["emp_ptr"], t_name, new_val)
                        if new_val:
                            emp["traits_mask"] |= bit
                        else:
                            emp["traits_mask"] &= ~bit

                        emp["goods"] = [t[0] for t in GameMemory.ALL_TRAITS if not t[2] and (emp["traits_mask"] & t[1])]
                        emp["weaknesses"] = [t[0] for t in GameMemory.ALL_TRAITS if t[2] and (emp["traits_mask"] & t[1])]

                        goods_txt = ", ".join(emp["goods"]) if emp["goods"] else "None"
                        bads_txt = ", ".join(emp["weaknesses"]) if emp["weaknesses"] else "None (Clear)"
                        lbl_ov_goods.configure(text=f"Good Traits: {goods_txt}")
                        lbl_ov_bads.configure(text=f"Weaknesses: {bads_txt}", text_color=C_ERROR if emp["weaknesses"] else C_SUCCESS)

                        if emp["actor_ptr"] in card_widgets:
                            w_count = len(emp["weaknesses"])
                            w_text = f" | {w_count} Weak" if w_count > 0 else ""
                            w_col = C_ERROR if w_count > 0 else C_TEXT_SEC
                            card_widgets[emp["actor_ptr"]]["vitals"].configure(
                                text=f"Energy: {emp['energy']*100:.0f}% | Stress: {emp['stress']*100:.0f}% | ${emp['salary']:,.0f}{w_text}",
                                text_color=w_col
                            )
                return handler

            sw = ctk.CTkSwitch(row_tr, text="", variable=var_tr, command=make_tr_toggler(), progress_color=C_ERROR if is_bad else C_ACCENT, width=36)
            sw.pack(side="right", padx=6)
            trait_sw_cache[tname] = (var_tr, sw)

    def reset_inspector_view():
        lbl_insp_name.configure(text="Select an employee")
        lbl_insp_team.configure(text="Team: N/A | Salary: $0 | 0 Pts Available")
        lbl_ov_v1.configure(text="Energy: 100% | Stress: 0%")
        lbl_ov_v2.configure(text="Satisfaction: 100% | Creativity: 100%")
        if lbl_ov_pts_summary:
            lbl_ov_pts_summary.configure(text="Available: 0 Pts | Allocated: 0")
        if lbl_ov_pts_breakdown:
            lbl_ov_pts_breakdown.configure(text="Lead: 0  Code: 0  Des: 0  Art: 0  Serv: 0")
        if lbl_sp_avail_pts:
            lbl_sp_avail_pts.configure(text="Available Points to Spend: 0")
        lbl_ov_goods.configure(text="Good Traits: None")
        lbl_ov_bads.configure(text="Weaknesses: None (Clear)", text_color=C_SUCCESS)
        entry_sal.delete(0, "end")
        for ent in exp_entries.values():
            ent.delete(0, "end")
        for w in frame_specs_grid.winfo_children():
            w.destroy()
        ctk.CTkLabel(frame_specs_grid, text="Select an employee to view specializations.", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_MUTED).pack(pady=10)
        for w in frame_traits_checklist.winfo_children():
            w.destroy()
        ctk.CTkLabel(frame_traits_checklist, text="Select an employee to view traits.", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_MUTED).pack(pady=10)

    # Function to update all inspector widgets when an employee is selected
    def select_employee_for_inspector(e: dict, full_rebuild: bool = True):
        current_selected_emp[0] = e
        tag = " [Founder]" if e["founder"] else ""
        lbl_insp_name.configure(text=f"{e['name']}{tag}")

        # Overview
        lbl_ov_v1.configure(text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}%")
        lbl_ov_v2.configure(text=f"Satisfaction: {e['satisfaction']*100:.0f}% | Creativity: {e['creativity']*100:.0f}%")

        goods_txt = ", ".join(e["goods"]) if e["goods"] else "None"
        bads_txt = ", ".join(e["weaknesses"]) if e["weaknesses"] else "None (Clear)"
        lbl_ov_goods.configure(text=f"Good Traits: {goods_txt}")
        lbl_ov_bads.configure(text=f"Weaknesses: {bads_txt}", text_color=C_ERROR if e["weaknesses"] else C_SUCCESS)

        if full_rebuild:
            entry_sal.delete(0, "end")
            entry_sal.insert(0, f"{e['salary']:.0f}")

        # Needs Sliders
        for k, sl in needs_sliders.items():
            val = e.get(k, 1.0)
            sl.set(val)
            pct = int(val * 100) if k != "satisfaction" else int(val * 50)
            if k in needs_labels:
                needs_labels[k].configure(text=f"{pct}%")

        # Base Skills Sliders
        for r_idx, sl in skill_sliders.items():
            val = e["skills"][r_idx] if r_idx < len(e["skills"]) else 0.0
            sl.set(val)
            if r_idx in skill_labels:
                skill_labels[r_idx].configure(text=f"{int(val*100)}%")

        # Points & Allocation across all tabs
        update_points_display_in_inspector(e)

        # Rebuild or sync grids in-place
        if full_rebuild:
            rebuild_specs_grid(e)
            rebuild_traits_grid(e)
        else:
            for (ridx, skey), btns in spec_btn_cache.items():
                cur_lvl = e["specs"].get(GameMemory.ROLE_NAMES[ridx], {}).get(skey, 0)
                for s_star, b in btns.items():
                    is_active = (s_star == cur_lvl)
                    b.configure(fg_color=C_ACCENT if is_active else C_BTN_SEC,
                                text_color=C_ACCENT_TEXT if is_active else C_TEXT_PRI)
            for tname, tbit, is_bad in GameMemory.ALL_TRAITS:
                if tname in trait_sw_cache:
                    trait_sw_cache[tname][0].set(bool(e["traits_mask"] & tbit))

    def on_employee_card_clicked(emp_data: dict):
        old_emp = current_selected_emp[0]
        # In-place styling update for selected card without rebuilding
        if old_emp and old_emp["actor_ptr"] in card_widgets:
            card_widgets[old_emp["actor_ptr"]]["card"].configure(fg_color=C_CARD_BG, border_color=C_BORDER_SUBTLE)

        if emp_data["actor_ptr"] in card_widgets:
            card_widgets[emp_data["actor_ptr"]]["card"].configure(fg_color=C_CARD_ALT, border_color=C_ACCENT)

        is_new = (old_emp is None or old_emp["actor_ptr"] != emp_data["actor_ptr"])
        select_employee_for_inspector(emp_data, full_rebuild=is_new)

    def render_roster_list():
        q = search_query_var.get().strip().lower()
        t_filter = selected_team_filter.get()

        filtered = []
        for e in cached_employees:
            if t_filter != "All Teams" and e["team"] != t_filter:
                continue
            if q and (q not in e["name"].lower() and q not in e["team"].lower()):
                continue
            filtered.append(e)

        for w in frame_roster.winfo_children():
            w.destroy()
        card_widgets.clear()

        if not filtered:
            ctk.CTkLabel(frame_roster, text="No matching personnel found.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=20)
            return

        for e in filtered:
            is_sel = (current_selected_emp[0] is not None and current_selected_emp[0]["actor_ptr"] == e["actor_ptr"])
            bg_col = C_CARD_ALT if is_sel else C_CARD_BG
            border_col = C_ACCENT if is_sel else C_BORDER_SUBTLE

            card = ctk.CTkFrame(frame_roster, fg_color=bg_col, corner_radius=6, border_width=1, border_color=border_col)
            card.pack(fill="x", pady=2, padx=2)

            row_c = ctk.CTkFrame(card, fg_color="transparent")
            row_c.pack(fill="x", padx=10, pady=5)

            tag = " [Founder]" if e["founder"] else ""
            lbl_name = ctk.CTkLabel(row_c, text=f"{e['name']}{tag}", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI)
            lbl_name.pack(side="left")

            pill_team = ctk.CTkLabel(row_c, text=e["team"], font=ctk.CTkFont(family="Segoe UI", size=9),
                                     fg_color=C_BTN_SEC, text_color=C_TEXT_SEC, corner_radius=4, padx=6, pady=1)
            pill_team.pack(side="left", padx=8)

            w_count = len(e["weaknesses"])
            w_text = f" | {w_count} Weak" if w_count > 0 else ""
            w_col = C_ERROR if w_count > 0 else C_TEXT_SEC

            pts_count = e.get("total_points", 0)
            pts_text = f" | {pts_count} Pts" if pts_count > 0 else ""

            lbl_vitals = ctk.CTkLabel(row_c, text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}% | ${e['salary']:,.0f}{w_text}{pts_text}",
                                      font=ctk.CTkFont(family="Segoe UI", size=10), text_color=w_col)
            lbl_vitals.pack(side="right")

            card_widgets[e["actor_ptr"]] = {
                "card": card,
                "vitals": lbl_vitals,
                "data": e
            }

            def make_click_handler(emp_data=e):
                def handler(event=None):
                    on_employee_card_clicked(emp_data)
                return handler

            card.bind("<Button-1>", make_click_handler())
            row_c.bind("<Button-1>", make_click_handler())
            lbl_name.bind("<Button-1>", make_click_handler())
            lbl_vitals.bind("<Button-1>", make_click_handler())

    def refresh_personnel_data(show_message: bool = False):
        if not game.is_attached():
            return
        emps = game.get_employees()
        cached_employees.clear()
        cached_employees.extend(emps)

        lbl_emp_count_badge.configure(text=f"{len(emps)} Personnel")
        teams_set = sorted(list({e["team"] for e in emps if e["team"]}))
        all_options = ["All Teams"] + teams_set
        if opt_team.cget("values") != all_options:
            opt_team.configure(values=all_options)

        render_roster_list()

        if current_selected_emp[0]:
            found = False
            for e in emps:
                if e["actor_ptr"] == current_selected_emp[0]["actor_ptr"]:
                    select_employee_for_inspector(e, full_rebuild=False)
                    found = True
                    break
            if not found:
                current_selected_emp[0] = None
                reset_inspector_view()

        if show_message:
            show_infobar(f"Loaded {len(emps)} personnel from game memory")

    btn_refresh.configure(command=lambda: refresh_personnel_data(show_message=True))
    opt_team.configure(command=lambda v: render_roster_list())
    search_query_var.trace_add("write", lambda *args: render_roster_list())
    page_switch_callbacks["personnel"] = lambda: (not cached_employees and refresh_personnel_data())

    # =========================================================
    # PAGE 4: PROJECTS & SOFTWARE
    # =========================================================
    p_proj = pages["projects"]

    ctk.CTkLabel(p_proj, text="Projects & Software", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_proj, text="Accelerate software design, programming, beta bug fixing, and market follower metrics.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    # Top Toolbar Card
    sc_proj_tb = ctk.CTkFrame(p_proj, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_proj_tb.pack(fill="x", pady=(0, 10), ipady=6)

    row_ptb_top = ctk.CTkFrame(sc_proj_tb, fg_color="transparent")
    row_ptb_top.pack(fill="x", padx=14, pady=(6, 4))

    lbl_proj_badge = ctk.CTkLabel(row_ptb_top, text="0 Active Projects | 0 Released Products",
                                  font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, corner_radius=4, padx=8, pady=3)
    lbl_proj_badge.pack(side="left")

    btn_proj_refresh = ctk.CTkButton(row_ptb_top, text="↻ Refresh Projects", width=130, height=30,
                                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                     fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER)
    btn_proj_refresh.pack(side="right")

    row_ptb_batch = ctk.CTkFrame(sc_proj_tb, fg_color="transparent")
    row_ptb_batch.pack(fill="x", padx=14, pady=(4, 6))

    ctk.CTkButton(row_ptb_batch, text="Max All Active Designs", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_active_designs(), show_infobar("Maxed all active design documents (100% / Iteration 3)"), refresh_projects_ui())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_ptb_batch, text="Complete All Programming", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_active_devs(), show_infobar("Completed 100% code & art for all active development projects"), refresh_projects_ui())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_ptb_batch, text="Clear All Project Bugs", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.clear_all_projects_bugs(), show_infobar("Cleared all bugs across all active projects"), refresh_projects_ui())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_ptb_batch, text="+50,000 Followers (All)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER,
                  command=lambda: (game.add_all_projects_followers(50000.0), show_infobar("Added +50,000 followers across all active projects"), refresh_projects_ui())).pack(side="left", expand=True, fill="x", padx=2)

    # --- SECTION 1: ACTIVE PROJECTS IN DEVELOPMENT ---
    ctk.CTkLabel(p_proj, text="Active Projects in Development", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(8, 2))
    ctk.CTkLabel(p_proj, text="Manage projects currently advancing through Design, Alpha, and Beta development.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 6))

    frame_proj_list = ctk.CTkFrame(p_proj, fg_color="transparent")
    frame_proj_list.pack(fill="x", pady=(0, 16))

    # --- SECTION 2: RELEASED SOFTWARE CATALOG ---
    ctk.CTkLabel(p_proj, text="Released Software Catalog & Commercial Metrics", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(12, 2))
    ctk.CTkLabel(p_proj, text="Manage quality, market awareness, customer reviews, and post-launch bugs for released software.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 6))

    frame_prod_list = ctk.CTkFrame(p_proj, fg_color="transparent")
    frame_prod_list.pack(fill="x", pady=(0, 16))

    def render_projects_ui():
        for w in frame_proj_list.winfo_children():
            w.destroy()
        for w in frame_prod_list.winfo_children():
            w.destroy()

        if not game.is_attached():
            ctk.CTkLabel(frame_proj_list, text="Attach to game to view active projects.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=12)
            ctk.CTkLabel(frame_prod_list, text="Attach to game to view released products.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=12)
            return

        projs = game.get_active_projects()
        prods = game.get_released_products()
        lbl_proj_badge.configure(text=f"{len(projs)} Active Projects | {len(prods)} Released Products")

        # 1. Render Active Projects
        if not projs:
            ctk.CTkLabel(frame_proj_list, text="No active software projects or design documents detected.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=10)
        else:
            for p in projs:
                card = ctk.CTkFrame(frame_proj_list, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
                card.pack(fill="x", pady=4, ipady=6)

                row_top = ctk.CTkFrame(card, fg_color="transparent")
                row_top.pack(fill="x", padx=14, pady=(6, 4))

                lbl_pname = ctk.CTkLabel(row_top, text=p["name"], font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI)
                lbl_pname.pack(side="left")

                if p["type"] == "Design":
                    pill_text = "🎨 Design Phase"
                    pill_col = C_BTN_SEC
                    pill_fg = C_ACCENT
                elif p["in_beta"]:
                    pill_text = "🐛 Beta (Debugging)"
                    pill_col = C_BADGE_WEAK
                    pill_fg = C_ERROR
                else:
                    pill_text = "💻 Alpha (Dev)"
                    pill_col = C_BADGE_GOOD
                    pill_fg = C_SUCCESS

                ctk.CTkLabel(row_top, text=pill_text, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                             fg_color=pill_col, text_color=pill_fg, corner_radius=4, padx=8, pady=2).pack(side="left", padx=8)

                # Right side badges
                row_badges = ctk.CTkFrame(row_top, fg_color="transparent")
                row_badges.pack(side="right")

                if p["type"] != "Design":
                    bug_col = C_ERROR if p["bugs"] > 0 else C_SUCCESS
                    ctk.CTkLabel(row_badges, text=f"Bugs: {p['bugs']:.1f}", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                 fg_color=C_BTN_SEC, text_color=bug_col, corner_radius=4, padx=6, pady=2).pack(side="left", padx=4)

                ctk.CTkLabel(row_badges, text=f"👥 {p['followers']:,.0f} Followers", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                             fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, corner_radius=4, padx=6, pady=2).pack(side="left", padx=4)

                # Progress Bars Row
                row_bars = ctk.CTkFrame(card, fg_color="transparent")
                row_bars.pack(fill="x", padx=14, pady=(2, 6))

                if p["type"] == "Design":
                    row_prog_lbl = ctk.CTkFrame(row_bars, fg_color="transparent")
                    row_prog_lbl.pack(fill="x")
                    ctk.CTkLabel(row_prog_lbl, text=f"Design Progress: {p['progress']*100:.1f}%  |  Iteration: {p['iteration']}/3  |  Finished: {'Yes' if p['has_finished'] else 'No'}",
                                 font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC).pack(side="left")
                    bar_des = ctk.CTkProgressBar(row_bars, height=6, progress_color=C_ACCENT)
                    bar_des.set(max(0.0, min(1.0, p["progress"])))
                    bar_des.pack(fill="x", pady=(2, 4))
                else:
                    row_prog_lbl = ctk.CTkFrame(row_bars, fg_color="transparent")
                    row_prog_lbl.pack(fill="x")
                    ctk.CTkLabel(row_prog_lbl, text=f"Code: {p['code_pct']:.1f}% ({p['tot_code_prog']:.1f}/{p['tot_code_req']:.1f})   |   Art: {p['art_pct']:.1f}% ({p['tot_art_prog']:.1f}/{p['tot_art_req']:.1f})   |   Design Alignment: {p['design_prog']*100:.0f}%",
                                 font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC).pack(side="left")
                    bar_code = ctk.CTkProgressBar(row_bars, height=6, progress_color=C_ACCENT)
                    bar_code.set(max(0.0, min(1.0, p["code_pct"] / 100.0)))
                    bar_code.pack(fill="x", pady=(2, 4))

                # Actions Row
                row_act = ctk.CTkFrame(card, fg_color="transparent")
                row_act.pack(fill="x", padx=14, pady=(4, 6))

                if p["type"] == "Design":
                    def make_max_design(ptr=p["ptr"], name=p["name"]):
                        def handler():
                            game.max_design_project(ptr)
                            show_infobar(f"Maxed design for '{name}' (Iteration 3, 100% Progress, Finished)")
                            render_projects_ui()
                        return handler

                    def make_add_fans(ptr=p["ptr"], cur=p["followers"], name=p["name"], delta=10000.0):
                        def handler():
                            game.set_project_followers(ptr, cur + delta)
                            show_infobar(f"Added +{delta:,.0f} followers to '{name}'")
                            render_projects_ui()
                        return handler

                    ctk.CTkButton(row_act, text="Max Design (100% / Iter 3)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=make_max_design()).pack(side="left", expand=True, fill="x", padx=2)
                    ctk.CTkButton(row_act, text="+10,000 Followers", height=28, font=ctk.CTkFont(family="Segoe UI", size=10),
                                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_add_fans(delta=10000.0)).pack(side="left", expand=True, fill="x", padx=2)
                    ctk.CTkButton(row_act, text="+50,000 Followers", height=28, font=ctk.CTkFont(family="Segoe UI", size=10),
                                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_add_fans(delta=50000.0)).pack(side="left", expand=True, fill="x", padx=2)
                else:
                    def make_max_dev(ptr=p["ptr"], name=p["name"]):
                        def handler():
                            game.max_dev_project(ptr)
                            show_infobar(f"Completed 100% code & art programming for '{name}'")
                            render_projects_ui()
                        return handler

                    def make_clear_bugs(ptr=p["ptr"], name=p["name"]):
                        def handler():
                            game.clear_project_bugs(ptr)
                            show_infobar(f"Cleared all bugs (0) for '{name}'")
                            render_projects_ui()
                        return handler

                    def make_promote_beta(ptr=p["ptr"], name=p["name"]):
                        def handler():
                            game.promote_project_to_beta(ptr)
                            show_infobar(f"Promoted '{name}' to Beta phase")
                            render_projects_ui()
                        return handler

                    def make_ready_release(ptr=p["ptr"], name=p["name"]):
                        def handler():
                            game.ready_project_for_release(ptr)
                            show_infobar(f"'{name}' is now 100% completed, bug-free, and ready for release!")
                            render_projects_ui()
                        return handler

                    def make_add_fans_dev(ptr=p["ptr"], cur=p["followers"], name=p["name"], delta=50000.0):
                        def handler():
                            game.set_project_followers(ptr, cur + delta)
                            show_infobar(f"Added +{delta:,.0f} followers to '{name}'")
                            render_projects_ui()
                        return handler

                    ctk.CTkButton(row_act, text="Complete Code & Art", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=make_max_dev()).pack(side="left", expand=True, fill="x", padx=2)
                    ctk.CTkButton(row_act, text="Clear Bugs (0)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_clear_bugs()).pack(side="left", expand=True, fill="x", padx=2)
                    if not p["in_beta"]:
                        ctk.CTkButton(row_act, text="Promote to Beta", height=28, font=ctk.CTkFont(family="Segoe UI", size=10),
                                      fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_promote_beta()).pack(side="left", expand=True, fill="x", padx=2)
                    ctk.CTkButton(row_act, text="Ready for Release", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_ready_release()).pack(side="left", expand=True, fill="x", padx=2)
                    ctk.CTkButton(row_act, text="+50k Followers", height=28, font=ctk.CTkFont(family="Segoe UI", size=10),
                                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_add_fans_dev()).pack(side="left", expand=True, fill="x", padx=2)

                # Custom Follower Override row
                row_fol = ctk.CTkFrame(card, fg_color="transparent")
                row_fol.pack(fill="x", padx=14, pady=(2, 6))
                ctk.CTkLabel(row_fol, text="Exact Followers:", font=ctk.CTkFont(family="Segoe UI", size=9), text_color=C_TEXT_MUTED).pack(side="left", padx=(0, 6))
                ent_fol = ctk.CTkEntry(row_fol, width=90, height=24, font=ctk.CTkFont(family="Segoe UI", size=10), placeholder_text="Followers")
                ent_fol.insert(0, f"{p['followers']:.0f}")
                ent_fol.pack(side="left", padx=(0, 6))

                def make_fol_setter(ptr=p["ptr"], ent=ent_fol, name=p["name"]):
                    def handler():
                        try:
                            val = float(ent.get().replace(",", "").replace(" ", "").strip())
                            game.set_project_followers(ptr, val)
                            show_infobar(f"Set followers to {val:,.0f} on '{name}'")
                            render_projects_ui()
                        except ValueError:
                            show_infobar("Enter a valid follower count", is_success=False)
                    return handler

                ctk.CTkButton(row_fol, text="Apply Followers", width=100, height=24, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_fol_setter()).pack(side="left")

        # 2. Render Released Products
        if not prods:
            ctk.CTkLabel(frame_prod_list, text="No released software products detected.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=10)
        else:
            for p in prods:
                card = ctk.CTkFrame(frame_prod_list, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
                card.pack(fill="x", pady=4, ipady=6)

                row_top = ctk.CTkFrame(card, fg_color="transparent")
                row_top.pack(fill="x", padx=14, pady=(6, 2))

                lbl_pname = ctk.CTkLabel(row_top, text=p["name"], font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=C_TEXT_PRI)
                lbl_pname.pack(side="left")

                # Quality pill
                q_text = "Outstanding" if p["quality"] >= 1.0 else ("Great" if p["quality"] >= 0.7 else "Normal")
                q_col = C_SUCCESS if p["quality"] >= 1.0 else C_TEXT_PRI
                ctk.CTkLabel(row_top, text=f"Quality: {p['quality']:.2f} ({q_text})", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                             fg_color=C_BTN_SEC, text_color=q_col, corner_radius=4, padx=6, pady=2).pack(side="left", padx=8)

                ctk.CTkLabel(row_top, text=f"${p['price']:.2f}", font=ctk.CTkFont(family="Segoe UI", size=10),
                             fg_color=C_BTN_SEC, text_color=C_TEXT_SEC, corner_radius=4, padx=6, pady=2).pack(side="left", padx=2)

                ctk.CTkLabel(row_top, text=f"{p['userbase']:,} Active Users", font=ctk.CTkFont(family="Segoe UI", size=10),
                             fg_color=C_BTN_SEC, text_color=C_TEXT_SEC, corner_radius=4, padx=6, pady=2).pack(side="left", padx=2)

                ctk.CTkLabel(row_top, text=f"👍 +{p['pos_reviews']:,}  👎 -{p['neg_reviews']:,}", font=ctk.CTkFont(family="Segoe UI", size=10),
                             fg_color=C_BTN_SEC, text_color=C_TEXT_SEC, corner_radius=4, padx=6, pady=2).pack(side="right")

                # Sub info
                row_sub = ctk.CTkFrame(card, fg_color="transparent")
                row_sub.pack(fill="x", padx=14, pady=(2, 4))
                bug_col = C_ERROR if p["bugs"] > 0 else C_SUCCESS
                ctk.CTkLabel(row_sub, text=f"Market Awareness: {p['awareness']*100:.1f}%   |   Fans: {p['followers']:,}   |   Bugs: {p['bugs']}",
                             font=ctk.CTkFont(family="Segoe UI", size=10), text_color=bug_col if p["bugs"] > 0 else C_TEXT_SEC).pack(side="left")

                # Actions row
                row_act = ctk.CTkFrame(card, fg_color="transparent")
                row_act.pack(fill="x", padx=14, pady=(4, 6))

                def make_prod_clear_bugs(ptr=p["ptr"], name=p["name"]):
                    def handler():
                        game.modify_released_product(ptr, clear_bugs=True)
                        show_infobar(f"Cleared all post-launch bugs for '{name}'")
                        render_projects_ui()
                    return handler

                def make_prod_max_aware(ptr=p["ptr"], name=p["name"]):
                    def handler():
                        game.modify_released_product(ptr, awareness=1.0)
                        show_infobar(f"Set 100% market awareness for '{name}'")
                        render_projects_ui()
                    return handler

                def make_prod_add_fans(ptr=p["ptr"], cur=p["followers"], name=p["name"], delta=50000):
                    def handler():
                        game.modify_released_product(ptr, followers=cur + delta)
                        show_infobar(f"Added +{delta:,} fans for '{name}'")
                        render_projects_ui()
                    return handler

                def make_prod_max_qual(ptr=p["ptr"], name=p["name"]):
                    def handler():
                        game.modify_released_product(ptr, quality=1.5)
                        show_infobar(f"Set Outstanding Quality (1.50) for '{name}'")
                        render_projects_ui()
                    return handler

                ctk.CTkButton(row_act, text="Clear Bugs (0)", height=26, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_prod_clear_bugs()).pack(side="left", expand=True, fill="x", padx=2)
                ctk.CTkButton(row_act, text="Max Awareness (100%)", height=26, font=ctk.CTkFont(family="Segoe UI", size=9),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_prod_max_aware()).pack(side="left", expand=True, fill="x", padx=2)
                ctk.CTkButton(row_act, text="+50k Fans", height=26, font=ctk.CTkFont(family="Segoe UI", size=9),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=make_prod_add_fans()).pack(side="left", expand=True, fill="x", padx=2)
                ctk.CTkButton(row_act, text="Outstanding Quality", height=26, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                              fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=make_prod_max_qual()).pack(side="left", expand=True, fill="x", padx=2)

    def refresh_projects_ui(show_message: bool = False):
        render_projects_ui()
        if show_message:
            show_infobar("Refreshed projects and software catalog from game memory")

    btn_proj_refresh.configure(command=lambda: refresh_projects_ui(show_message=True))
    page_switch_callbacks["projects"] = lambda: refresh_projects_ui()

    # =========================================================
    # PAGE 5: RESEARCH & PATENTS
    # =========================================================
    p_res = pages["research"]

    ctk.CTkLabel(p_res, text="Research & Patents", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_res, text="Accelerate active research projects, control research speed multipliers, maximize patent royalties, and extend technology monopolies.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    # Top Toolbar Card
    sc_res_tb = ctk.CTkFrame(p_res, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_res_tb.pack(fill="x", pady=(0, 10), ipady=6)

    row_rtb_top = ctk.CTkFrame(sc_res_tb, fg_color="transparent")
    row_rtb_top.pack(fill="x", padx=14, pady=(6, 4))

    lbl_res_badge = ctk.CTkLabel(row_rtb_top, text="0 Active Research | 0 Patents Held",
                                 font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                 fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, corner_radius=4, padx=8, pady=3)
    lbl_res_badge.pack(side="left")

    btn_res_refresh = ctk.CTkButton(row_rtb_top, text="↻ Refresh Research", width=140, height=30,
                                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                    fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER)
    btn_res_refresh.pack(side="right")

    row_rtb_batch = ctk.CTkFrame(sc_res_tb, fg_color="transparent")
    row_rtb_batch.pack(fill="x", padx=14, pady=(4, 6))

    ctk.CTkButton(row_rtb_batch, text="Complete All Active Research", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER,
                  command=lambda: (game.max_all_active_research(), show_infobar("Maxed and completed all active research tasks (Patent granted on next tick)"), refresh_research_ui())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_rtb_batch, text="Set 25x Speed Multiplier (All)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.boost_all_active_research(25.0), show_infobar("Supercharged research speed to 25x across all active tasks"), refresh_research_ui())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_rtb_batch, text="Boost All Patents (50% / 2099)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.boost_all_patents(royalty=0.50, outdates=2099), show_infobar("Boosted all patents: 50% royalty rate and expiration extended to Year 2099"), refresh_research_ui())).pack(side="left", expand=True, fill="x", padx=2)

    # --- SECTION 1: ACTIVE RESEARCH OPERATIONS ---
    ctk.CTkLabel(p_res, text="Active Research Operations", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(8, 2))
    ctk.CTkLabel(p_res, text="Monitor active laboratory research tasks, advance points, and configure speed factors.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 6))

    frame_res_list = ctk.CTkFrame(p_res, fg_color="transparent")
    frame_res_list.pack(fill="x", pady=(0, 16))

    # --- SECTION 2: PATENTS & ROYALTY MONOPOLIES ---
    ctk.CTkLabel(p_res, text="Corporate Patents & Royalty Streams", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(12, 2))
    ctk.CTkLabel(p_res, text="Manage company-owned technology patents, royalty fee percentages, and monopoly expirations.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 6))

    frame_pat_list = ctk.CTkFrame(p_res, fg_color="transparent")
    frame_pat_list.pack(fill="x", pady=(0, 16))

    def render_research_ui():
        for w in frame_res_list.winfo_children():
            w.destroy()
        for w in frame_pat_list.winfo_children():
            w.destroy()

        if not game.is_attached():
            ctk.CTkLabel(frame_res_list, text="Attach to game to view active research.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=12)
            ctk.CTkLabel(frame_pat_list, text="Attach to game to view patents.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=12)
            return

        tasks = game.get_active_research()
        patents = game.get_patents()
        lbl_res_badge.configure(text=f"{len(tasks)} Active Research | {len(patents)} Patents Held")

        # Render Active Research
        if not tasks:
            empty_card = ctk.CTkFrame(frame_res_list, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
            empty_card.pack(fill="x", pady=4, ipady=12)
            ctk.CTkLabel(empty_card, text="No active research tasks in progress.", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=C_TEXT_PRI).pack()
            ctk.CTkLabel(empty_card, text="Start a research project (System, 2D, 3D, Audio, Hardware, Network) in Software Inc. to manipulate it here.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(pady=(2, 0))
        else:
            for t in tasks:
                card = ctk.CTkFrame(frame_res_list, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
                card.pack(fill="x", pady=4, ipady=8)

                # Header
                hdr = ctk.CTkFrame(card, fg_color="transparent")
                hdr.pack(fill="x", padx=14, pady=(6, 4))

                title_box = ctk.CTkFrame(hdr, fg_color="transparent")
                title_box.pack(side="left")

                ctk.CTkLabel(title_box, text=f"{t['spec']} - {t['year_display']}", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")

                badge_spec = ctk.CTkLabel(title_box, text=t['spec'], font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                          fg_color=("#E0F2FE", "#0369A1"), text_color=("#0369A1", "#F0F9FF"), corner_radius=4, padx=6, pady=1)
                badge_spec.pack(side="left", padx=6)

                badge_spd = ctk.CTkLabel(title_box, text=f"Speed: {t['upg_factor']:.1f}x", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                         fg_color=("#FEF3C7", "#92400E"), text_color=("#92400E", "#FFFBEB"), corner_radius=4, padx=6, pady=1)
                badge_spd.pack(side="left", padx=2)

                if t["finished"]:
                    badge_fin = ctk.CTkLabel(title_box, text="COMPLETED", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                             fg_color=("#D1FAE5", "#065F46"), text_color=("#065F46", "#ECFDF5"), corner_radius=4, padx=6, pady=1)
                    badge_fin.pack(side="left", padx=4)

                if t["paused"]:
                    badge_pause = ctk.CTkLabel(title_box, text="PAUSED", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                               fg_color=("#FEE2E2", "#991B1B"), text_color=("#991B1B", "#FEF2F2"), corner_radius=4, padx=6, pady=1)
                    badge_pause.pack(side="left", padx=4)

                # Progress Bar
                p_row = ctk.CTkFrame(card, fg_color="transparent")
                p_row.pack(fill="x", padx=14, pady=(4, 6))

                bar_box = ctk.CTkFrame(p_row, fg_color="transparent")
                bar_box.pack(fill="x")

                pb = ctk.CTkProgressBar(bar_box, height=8, corner_radius=4, progress_color=C_ACCENT, fg_color=C_CARD_ALT)
                pb.set(min(1.0, t["pct"] / 100.0))
                pb.pack(fill="x", pady=(2, 2))

                lbl_pts = ctk.CTkLabel(bar_box, text=f"Research Points: {t['progress']:.2f} / {t['max']} pts ({t['pct']:.1f}%)",
                                       font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
                lbl_pts.pack(anchor="w")

                # Action Controls
                act_row = ctk.CTkFrame(card, fg_color="transparent")
                act_row.pack(fill="x", padx=14, pady=(4, 4))

                def make_complete_cb(ptr=t['ptr'], name=f"{t['spec']} - {t['year_display']}"):
                    return lambda: (game.max_research_task(ptr), show_infobar(f"Maxed research for '{name}'! Patent will register on next tick."), refresh_research_ui())

                ctk.CTkButton(act_row, text="Instant Complete", width=120, height=26,
                              font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                              fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER,
                              command=make_complete_cb()).pack(side="left", padx=(0, 4))

                def make_speed_cb(factor, ptr=t['ptr'], name=f"{t['spec']} - {t['year_display']}"):
                    return lambda: (game.set_research_speed(ptr, factor), show_infobar(f"Set speed to {factor:.0f}x for '{name}'"), refresh_research_ui())

                ctk.CTkButton(act_row, text="10x Speed", width=80, height=26,
                              font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                              command=make_speed_cb(10.0)).pack(side="left", padx=2)

                ctk.CTkButton(act_row, text="50x Speed", width=80, height=26,
                              font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                              command=make_speed_cb(50.0)).pack(side="left", padx=2)

                # Set custom points
                ent_pts = ctk.CTkEntry(act_row, width=65, height=26, font=ctk.CTkFont(family="Segoe UI", size=10),
                                       fg_color=C_CARD_ALT, border_color=C_BORDER, text_color=C_TEXT_PRI)
                ent_pts.insert(0, str(int(t['max'])))
                ent_pts.pack(side="left", padx=(8, 2))

                def make_pts_cb(e=ent_pts, ptr=t['ptr'], name=f"{t['spec']} - {t['year_display']}"):
                    def _apply():
                        try:
                            val = float(e.get().strip())
                            game.set_research_progress(ptr, val)
                            show_infobar(f"Set progress to {val:.1f} pts for '{name}'")
                            refresh_research_ui()
                        except ValueError:
                            pass
                    return _apply

                ctk.CTkButton(act_row, text="Set Points", width=75, height=26,
                              font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                              command=make_pts_cb()).pack(side="left", padx=2)

        # Render Corporate Patents
        if not patents:
            empty_pat = ctk.CTkFrame(frame_pat_list, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
            empty_pat.pack(fill="x", pady=4, ipady=12)
            ctk.CTkLabel(empty_pat, text="No corporate patents currently held.", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=C_TEXT_PRI).pack()
            ctk.CTkLabel(empty_pat, text="When an active research task completes, its patented technology level is registered here with royalty revenue streams.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(pady=(2, 0))
        else:
            for p in patents:
                card = ctk.CTkFrame(frame_pat_list, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
                card.pack(fill="x", pady=4, ipady=8)

                hdr = ctk.CTkFrame(card, fg_color="transparent")
                hdr.pack(fill="x", padx=14, pady=(6, 4))

                title_box = ctk.CTkFrame(hdr, fg_color="transparent")
                title_box.pack(side="left")

                ctk.CTkLabel(title_box, text=f"Patent: {p['spec']} ({p['year_display']})", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")

                badge_stat = ctk.CTkLabel(title_box, text="ACTIVE PATENT", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                                          fg_color=("#D1FAE5", "#065F46"), text_color=("#065F46", "#ECFDF5"), corner_radius=4, padx=6, pady=1)
                badge_stat.pack(side="left", padx=6)

                # Metrics row
                m_row = ctk.CTkFrame(card, fg_color="transparent")
                m_row.pack(fill="x", padx=14, pady=(2, 6))

                ctk.CTkLabel(m_row, text=f"Royalty Rate: {p['royalty']*100:.1f}%  |  Collected Revenue: ${p['income']:,.2f}  |  Expires: Year {p['outdates']}",
                             font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w")

                # Action Controls
                act_row = ctk.CTkFrame(card, fg_color="transparent")
                act_row.pack(fill="x", padx=14, pady=(4, 4))

                def make_royalty_cb(ptr=p['ptr'], spec=p['spec']):
                    return lambda: (game.modify_patent(ptr, royalty=0.50), show_infobar(f"Set royalty to 50% for patent '{spec}'"), refresh_research_ui())

                ctk.CTkButton(act_row, text="Set 50% Royalty", width=120, height=26,
                              font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                              command=make_royalty_cb()).pack(side="left", padx=(0, 4))

                def make_extend_cb(ptr=p['ptr'], spec=p['spec']):
                    return lambda: (game.modify_patent(ptr, outdates=2099), show_infobar(f"Extended patent '{spec}' expiration to Year 2099"), refresh_research_ui())

                ctk.CTkButton(act_row, text="Extend to Year 2099", width=130, height=26,
                              font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                              fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                              command=make_extend_cb()).pack(side="left", padx=2)

                def make_add_inc_cb(ptr=p['ptr'], cur=p['income'], spec=p['spec']):
                    return lambda: (game.modify_patent(ptr, income=cur + 100000.0), show_infobar(f"Added +$100,000 royalty revenue to '{spec}'"), refresh_research_ui())

                ctk.CTkButton(act_row, text="+$100k Royalty Cash", width=130, height=26,
                              font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                              fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER,
                              command=make_add_inc_cb()).pack(side="left", padx=2)

    def refresh_research_ui(show_message: bool = False):
        render_research_ui()
        if show_message:
            show_infobar("Refreshed research operations and corporate patents from game memory")

    btn_res_refresh.configure(command=lambda: refresh_research_ui(show_message=True))
    page_switch_callbacks["research"] = lambda: refresh_research_ui()

    # =========================================================
    # PAGE 6: WORLD & RULES
    # =========================================================
    p_wrld = pages["world"]

    ctk.CTkLabel(p_wrld, text="World & Rules", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_wrld, text="Modify simulation speed, furniture availability, and fixture lighting.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    def make_setting_switch(parent, title, desc, on_toggle, default_state=False):
        card = ctk.CTkFrame(parent, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
        card.pack(fill="x", pady=4, ipady=6)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)

        left_box = ctk.CTkFrame(row, fg_color="transparent")
        left_box.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(left_box, text=title, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w")
        ctk.CTkLabel(left_box, text=desc, font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w")

        var = ctk.BooleanVar(value=default_state)
        sw = ctk.CTkSwitch(row, text="", variable=var, command=lambda: on_toggle(var.get()), progress_color=C_ACCENT, width=40)
        sw.pack(side="right")
        return var

    make_setting_switch(p_wrld, "Unlock Furniture Catalog",
                        "Instantly access all furniture, electronics, and room fixtures regardless of year or research.",
                        lambda on: (game.unlock_furniture(on), show_infobar(f"Furniture catalog unlock set to {on}")))

    make_setting_switch(p_wrld, "Force Room Lighting On",
                        "Forces continuous illumination on all light fixtures regardless of power or time of day.",
                        lambda on: (game.force_lights(on), show_infobar(f"Force lighting set to {on}")))

    make_setting_switch(p_wrld, "Disable Darkness Shader",
                        "Removes the nighttime ambient darkness overlay across the 3D office environment.",
                        lambda on: (game.disable_darkness(on), show_infobar(f"Darkness shader set to {not on}")))

    make_setting_switch(p_wrld, "Infinite Subsidiaries Limit",
                        "Removes the cap restricting the number of corporate subsidiaries your company can hold.",
                        lambda on: (game.infinite_subsidiaries(on), show_infobar(f"Infinite subsidiaries set to {on}")))

    # Simulation Speed Multiplier Card
    sc_spd = ctk.CTkFrame(p_wrld, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_spd.pack(fill="x", pady=6, ipady=8)

    ctk.CTkLabel(sc_spd, text="Simulation Clock Rate Multiplier", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", padx=16, pady=(10, 2))
    ctk.CTkLabel(sc_spd, text="Accelerate or decelerate the background simulation rate of the Unity engine.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(anchor="w", padx=16, pady=(0, 6))

    lbl_spd_val = ctk.CTkLabel(sc_spd, text="Current Multiplier: 1.0x", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=C_TEXT_PRI)
    lbl_spd_val.pack(anchor="w", padx=16, pady=(0, 6))

    def on_spd_slider(val):
        game.set_game_speed(float(val))
        lbl_spd_val.configure(text=f"Current Multiplier: {float(val):.1f}x")

    slider_spd = ctk.CTkSlider(sc_spd, from_=0.5, to=10.0, number_of_steps=19, command=on_spd_slider, progress_color=C_ACCENT)
    slider_spd.set(1.0)
    slider_spd.pack(fill="x", padx=16, pady=(0, 10))

    row_spd_presets = ctk.CTkFrame(sc_spd, fg_color="transparent")
    row_spd_presets.pack(fill="x", padx=16, pady=(0, 6))
    for s_val, s_name in [(1.0, "1x (Normal)"), (2.0, "2x (Fast)"), (5.0, "5x (Turbo)"), (10.0, "10x (Ultra)")]:
        ctk.CTkButton(row_spd_presets, text=s_name, height=30, font=ctk.CTkFont(family="Segoe UI", size=11),
                      fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                      command=lambda v=s_val: (game.set_game_speed(v), slider_spd.set(v), lbl_spd_val.configure(text=f"Current Multiplier: {v:.1f}x"), show_infobar(f"Simulation speed set to {v}x"))).pack(side="left", expand=True, fill="x", padx=2)

    # =========================================================
    # PAGE 5: HOTKEYS
    # =========================================================
    p_hk = pages["hotkeys"]

    ctk.CTkLabel(p_hk, text="Hotkeys", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_hk, text="Trigger in-game memory modifications using global keyboard shortcuts.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    sc_hk_switch = ctk.CTkFrame(p_hk, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    sc_hk_switch.pack(fill="x", pady=(0, 8), ipady=6)

    row_hk_sw = ctk.CTkFrame(sc_hk_switch, fg_color="transparent")
    row_hk_sw.pack(fill="x", padx=16, pady=8)
    ctk.CTkLabel(row_hk_sw, text="Enable Global Hotkeys", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=C_TEXT_PRI).pack(side="left")
    ctk.CTkSwitch(row_hk_sw, text="", variable=hotkeys_enabled_var, progress_color=C_ACCENT, width=40).pack(side="right")

    hotkeys_info = [
        ("Numpad 1", "Add $1,000,000 Cash", "Direct cash transfer to corporate treasury"),
        ("Numpad 2", "Add $10,000,000 Cash", "Major enterprise reserve injection"),
        ("Numpad 3", "Restore Personnel Needs", "Sets 100% Energy, Hunger, Social, and 0% Stress"),
        ("Numpad 4", "Max Personnel Skills", "Sets 100% Base Skills across all 5 roles"),
        ("Numpad 5", "Max Business Reputation", "Elevates company reputation to 100%"),
        ("Numpad 6", "Add 50,000 Fans", "Expands active consumer fan base"),
        ("Numpad 7", "Unlock Furniture Catalog", "Unlocks complete furniture catalog"),
        ("Numpad 8", "Force Room Lighting On", "Keeps all light fixtures illuminated"),
        ("Numpad 9", "Toggle Turbo Speed (5x)", "Toggles between 1x normal and 5x simulation speed"),
    ]

    for key, action, desc in hotkeys_info:
        row_hk = ctk.CTkFrame(p_hk, fg_color=C_CARD_BG, corner_radius=6, border_width=1, border_color=C_BORDER)
        row_hk.pack(fill="x", pady=2, ipady=3)
        lbl_k = ctk.CTkLabel(row_hk, text=key, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                             fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, corner_radius=4, width=90, padx=6, pady=3)
        lbl_k.pack(side="left", padx=10)
        lbl_a = ctk.CTkLabel(row_hk, text=action, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_PRI)
        lbl_a.pack(side="left", padx=4)
        lbl_d = ctk.CTkLabel(row_hk, text=f"— {desc}", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
        lbl_d.pack(side="left", padx=8)

    # --- TELEMETRY TIMER LOOP ---

    def update_telemetry():
        if not game.is_attached():
            attached = game.attach()
            if not attached:
                status_badge.configure(fg_color=C_ERROR_BG)
                lbl_status_text.configure(text="● Not attached to game", text_color=C_ERROR)
                lbl_fin_money.configure(text="$0.00")
                lbl_fin_fans.configure(text="0")
                lbl_fin_rep.configure(text="0.0%")
                bar_rep.set(0.0)
                lbl_calendar.configure(text="Calendar: Not attached")
                return
            else:
                status_badge.configure(fg_color=C_SUCCESS_BG)
                lbl_status_text.configure(text=f"● Connected: PID {game.pid} ({game.get_company_name()})", text_color=C_SUCCESS)

        game.refresh_pointers()
        c_name = game.get_company_name()
        c_money = game.get_money()
        c_fans = game.get_fans()
        c_rep = game.get_business_rep()
        dt = game.get_date_time()

        status_badge.configure(fg_color=C_SUCCESS_BG)
        lbl_status_text.configure(text=f"● Connected: PID {game.pid} ({c_name})", text_color=C_SUCCESS)
        lbl_fin_money.configure(text=f"${c_money:,.2f}")
        lbl_fin_fans.configure(text=f"{c_fans:,}")
        lbl_fin_rep.configure(text=f"{c_rep*100:.1f}%")
        bar_rep.set(max(0.0, min(1.0, c_rep)))

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        m_str = months[dt["month"] % 12] if dt["month"] < 12 else f"M{dt['month']}"
        yr = 1900 + dt["year"] if dt["year"] < 1000 else dt["year"]
        lbl_calendar.configure(text=f"Calendar: {m_str} {yr} - {dt['hour']:02d}:00")

        # Founder Profile Updates (Only updated when Founder tab is active)
        if current_page[0] == "founder":
            founder = game.get_founder()
            if founder:
                lbl_fnd_name.configure(text=f"{founder['name']} (CEO)")
                lbl_fnd_sub.configure(text=f"Team: {founder['team']} | Salary: ${founder['salary']:,.0f}/mo | Skill Ceiling: {founder['skill_ceiling']*100:.0f}%")
                lbl_f_energy.configure(text=f"Energy: {founder['energy']*100:.0f}%")
                bar_f_energy.set(max(0.0, min(1.0, founder['energy'])))
                lbl_f_stress.configure(text=f"Stress: {founder['stress']*100:.0f}%")
                bar_f_stress.set(max(0.0, min(1.0, founder['stress'])))
                lbl_f_sat.configure(text=f"Satisfaction: {founder['satisfaction']*100:.0f}%")
                bar_f_sat.set(max(0.0, min(1.0, founder['satisfaction'] / 2.0)))
                lbl_f_creativity.configure(text=f"Creativity: {founder['creativity']*100:.0f}%")
                bar_f_creativity.set(max(0.0, min(1.0, founder['creativity'])))

                for r_idx, r_name in enumerate(GameMemory.ROLE_NAMES):
                    bskill = f"{founder['skills'][r_idx]*100:.0f}%" if r_idx < len(founder['skills']) else "0%"
                    specs = founder["specs"].get(r_name, {})
                    specs_desc = ", ".join([f"{k} (Lvl {lvl})" for k, lvl in specs.items()]) if specs else "No active specializations"
                    if r_name in f_role_widgets:
                        lbl_t, lbl_s = f_role_widgets[r_name]
                        lbl_t.configure(text=f"{r_name} (Base Skill: {bskill})")
                        lbl_s.configure(text=specs_desc)

        if freeze_needs_var.get():
            game.max_all_employees_needs()

    def telemetry_timer():
        update_telemetry()
        root.after(1000, telemetry_timer)

    # --- BACKGROUND HOTKEY LISTENER ---

    def hotkey_thread():
        turbo_active = False
        while True:
            time.sleep(0.08)
            try:
                if not hotkeys_enabled_var.get() or not game.is_attached():
                    continue
            except Exception:
                break

            if u32.GetAsyncKeyState(VK_NUMPAD1) & 0x8000:
                game.add_money(1000000.0)
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD2) & 0x8000:
                game.add_money(10000000.0)
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD3) & 0x8000:
                game.max_all_employees_needs()
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD4) & 0x8000:
                game.max_all_employees_skills()
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD5) & 0x8000:
                game.set_business_rep(1.0)
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD6) & 0x8000:
                game.add_fans(50000)
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD7) & 0x8000:
                game.unlock_furniture(True)
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD8) & 0x8000:
                game.force_lights(True)
                u32.MessageBeep(0)
                time.sleep(0.25)
            elif u32.GetAsyncKeyState(VK_NUMPAD9) & 0x8000:
                turbo_active = not turbo_active
                game.set_game_speed(5.0 if turbo_active else 1.0)
                u32.MessageBeep(0)
                time.sleep(0.25)

    th = threading.Thread(target=hotkey_thread, daemon=True)
    th.start()

    switch_page("finances")
    root.after(100, telemetry_timer)
    root.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(run_cli(sys.argv[1:]))
    else:
        run_gui()
