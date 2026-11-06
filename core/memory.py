"""
Software Inc. Memory Engine & Win32 Mono Patcher
Extracted and decoupled from monolithic trainer.py.
"""

import os
import sys
import time
import ctypes
import threading
from ctypes import wintypes
from typing import Dict, List, Any, Optional

# Win32 Process Access
PROCESS_ALL_ACCESS = 0x1F0FFF

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

    @property
    def base_address(self) -> int:
        return self.mono_base

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

        pids = []
        # 1. Native Win32 Toolhelp32 snapshot (fast & zero overhead)
        try:
            TH32CS_SNAPPROCESS = 0x00000002
            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ('dwSize', wintypes.DWORD),
                    ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD),
                    ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD),
                    ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD),
                    ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD),
                    ('szExeFile', ctypes.c_char * 260)
                ]
            hSnap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if hSnap and hSnap != -1:
                pe = PROCESSENTRY32()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                if k32.Process32First(hSnap, ctypes.byref(pe)):
                    while True:
                        exe = pe.szExeFile.decode('utf-8', 'ignore').lower()
                        if 'software' in exe:
                            pids.append(pe.th32ProcessID)
                        if not k32.Process32Next(hSnap, ctypes.byref(pe)):
                            break
                k32.CloseHandle(hSnap)
        except Exception:
            pids = []

        # 2. PowerShell Fallback
        if not pids:
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
            return {"hour": 0, "day": 0, "month": 0, "year": 0, "date_str": "Unknown Date", "time_str": "00:00"}
        hr = self.read_u32(self.time_of_day_instance + 0x24)
        dy = self.read_u32(self.time_of_day_instance + 0x28)
        mo = self.read_u32(self.time_of_day_instance + 0x2C)
        yr_val = self.read_u32(self.time_of_day_instance + 0x30)
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        m_str = months[mo % 12] if mo < 12 else f"M{mo}"
        yr = 1900 + yr_val if yr_val < 1000 else yr_val
        return {
            "hour": hr,
            "day": dy,
            "month": mo,
            "year": yr_val,
            "date_str": f"{m_str} {yr}",
            "time_str": f"{hr:02d}:00",
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

            skills_dict = {}
            for r_i, r_name in enumerate(self.ROLE_NAMES):
                skills_dict[r_name] = skills[r_i] if r_i < len(skills) else 1.0

            employees.append({
                "index": idx,
                "actor_ptr": actor_ptr,
                "emp_ptr": emp_ptr,
                "ptr": emp_ptr,
                "name": name,
                "founder": founder,
                "is_founder": founder,
                "ceo": ceo,
                "role": "Founder" if founder else "Staff",
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
                "vitals": {
                    "energy": energy,
                    "stress": stress,
                    "hunger": hunger,
                    "bladder": bladder,
                    "social": social,
                    "satisfaction": satisfaction,
                    "creativity": creativity,
                    "skill_ceiling": skill_ceiling,
                },
                "skills": skills,
                "skills_dict": skills_dict,
                "spec_exp": spec_exp,
                "spec_used": spec_used,
                "total_points": int(sum(spec_exp)),
                "total_used": int(sum(spec_used)),
                "specs": specs_by_role,
                "specializations": specs_by_role,
                "traits_mask": traits_mask,
                "goods": goods,
                "weaknesses": weaknesses,
                "traits": goods + weaknesses,
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

    def set_employee_skill(self, emp_ptr: int, role_idx: Any, value: float) -> bool:
        if isinstance(role_idx, str):
            if role_idx in self.ROLE_NAMES:
                role_idx = self.ROLE_NAMES.index(role_idx)
            else:
                return False
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

    def set_employee_spec_level(self, emp_ptr: int, role_idx: Any, spec_key: str, target_level: int) -> bool:
        if isinstance(role_idx, str):
            if role_idx in self.ROLE_NAMES:
                role_idx = self.ROLE_NAMES.index(role_idx)
            else:
                return False
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

# Singleton instance
_game_instance: Optional[GameMemory] = None

def get_game_memory() -> GameMemory:
    global _game_instance
    if _game_instance is None:
        _game_instance = GameMemory()
    return _game_instance
