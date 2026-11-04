"""
Software Inc. - Memory Trainer
Native Windows 11 Fluent Design Application
Supports: All Software Inc. versions running with Unity Mono x64
Design: Windows App UI/UX (WinUI 3 / Fluent Design), Light & Dark mode support, Zero AI Slop.
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


class GameMemory:
    """Handles external memory discovery and safe read/write operations for Software Inc."""

    ROLE_NAMES = ["Lead", "Code", "Design", "Art", "Service"]

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

    def get_cheat_states(self) -> dict:
        if not self.sdata_cheats:
            return {"unlock_furn": False, "force_lights": False, "disable_darkness": False, "infinite_subs": False}
        return {
            "unlock_furn": bool(self.read_u8(self.sdata_cheats + 0x01)),
            "force_lights": bool(self.read_u8(self.sdata_cheats + 0x02)),
            "disable_darkness": bool(self.read_u8(self.sdata_cheats + 0x00)),
            "infinite_subs": bool(self.read_u8(self.sdata_cheats + 0x04)),
        }

    # --- Personnel Discovery ---

    def get_employees(self) -> list:
        if not self.actor_manager:
            return []

        actors_map = {}

        # 1. Actors (+0x10)
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

        # 2. Staff (+0x18)
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

        # 3. Teams (+0x40)
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
                "specs": specs_by_role
            })
            idx += 1

        return employees

    def get_founder(self) -> dict:
        emps = self.get_employees()
        for e in emps:
            if e["founder"]:
                return e
        return emps[0] if emps else None

    # --- Modifiers ---

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

    def max_employee_specs(self, emp_ptr: int, target_level: int = 3) -> int:
        if not emp_ptr:
            return 0
        spec_levels_arr = self.read_ptr(emp_ptr + 0x18)
        if not spec_levels_arr:
            return 0
        levels_len = self.read_u32(spec_levels_arr + 0x18)
        modified = 0
        for role_idx in range(min(levels_len, 5)):
            dict_ptr = self.read_ptr(spec_levels_arr + 0x20 + role_idx * 8)
            if not dict_ptr:
                continue
            d_entries = self.read_ptr(dict_ptr + 0x18)
            if not d_entries:
                continue
            d_cap = self.read_u32(d_entries + 0x18)
            for k in range(d_cap):
                e_addr = d_entries + 0x20 + k * 24
                k_ptr = self.read_ptr(e_addr + 8)
                if k_ptr:
                    self.write_u32(e_addr + 16, int(target_level))
                    modified += 1
        return modified

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

    def set_employee_salary(self, emp_ptr: int, salary: float) -> bool:
        if not emp_ptr:
            return False
        return self.write_float(emp_ptr + 0x160, float(salary))

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


# Global Memory Engine Instance
game = GameMemory()


# --- CLI MODE ---

def run_cli(args):
    print("==========================================================")
    print("           SOFTWARE INC. MEMORY TRAINER (CLI)             ")
    print("==========================================================")

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
                print(f"[SUCCESS] Maxed Founder '{founder['name']}': 100% Needs, 100% Skills, {sp} Specs Maxed, +50 EXP!")
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
            print(f"[SUCCESS] Added +{delta:.1f} Specialization EXP across all roles for {n} employees!")
            i += 2
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
                    print(f"  - {m['name']}{tag}: Salary ${m['salary']:,.0f} | Energy {m['energy']*100:.0f}% | Stress {m['stress']*100:.0f}% | Sat {m['satisfaction']*100:.0f}%")
            i += 1
        elif cmd == "--speed" and i + 1 < len(args):
            spd = float(args[i+1])
            game.set_game_speed(spd)
            print(f"[SUCCESS] Game speed set to {spd}x")
            i += 2
        elif cmd == "--status":
            emps = game.get_employees()
            print(f"[+] Total Detected Personnel: {len(emps)} (Employees + Facility Staff)")
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

    # Set system appearance by default
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Software Inc. Trainer")
    root.geometry("1000x740")
    root.minsize(920, 660)
    root.configure(fg_color=C_WIN_BG)

    # State Variables
    freeze_needs_var = ctk.BooleanVar(value=False)
    turbo_speed_var = ctk.BooleanVar(value=False)
    hotkeys_enabled_var = ctk.BooleanVar(value=True)
    selected_team_filter = ctk.StringVar(value="All Teams")
    search_query_var = ctk.StringVar(value="")
    current_selected_emp = [None]

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

    # Theme Mode Selector (Right)
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

    # Navigation Sidebar
    sidebar = ctk.CTkFrame(main_body, width=200, corner_radius=0, fg_color=C_SIDEBAR_BG,
                           border_width=1, border_color=C_BORDER)
    sidebar.pack(fill="y", side="left")
    sidebar.pack_propagate(False)

    content_viewport = ctk.CTkFrame(main_body, corner_radius=0, fg_color=C_WIN_BG)
    content_viewport.pack(fill="both", expand=True, padx=20, pady=16)

    # Tab Pages
    pages = {
        "finances": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "founder": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "personnel": ctk.CTkFrame(content_viewport, fg_color="transparent"),
        "world": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
        "hotkeys": ctk.CTkScrollableFrame(content_viewport, fg_color="transparent"),
    }

    current_page = ["finances"]
    nav_buttons = {}

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

    lbl_nav = ctk.CTkLabel(sidebar, text="Navigation", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                           text_color=C_TEXT_MUTED)
    lbl_nav.pack(anchor="w", padx=16, pady=(16, 6))

    nav_items = [
        ("finances", "Finances"),
        ("founder", "Founder Profile"),
        ("personnel", "Personnel & Teams"),
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
                                  command=lambda: (game.max_all_employees_needs(), game.max_all_employees_skills(), game.max_all_employees_specs(3), show_infobar("Restored needs, skills, and specializations for all personnel"), update_telemetry()))
    btn_quick_god.pack(fill="x", padx=12, pady=(16, 12))

    # =========================================================
    # PAGE 1: FINANCES
    # =========================================================
    p_fin = pages["finances"]

    # Page Header
    ctk.CTkLabel(p_fin, text="Finances", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_fin, text="Manage company capital, valuation, fans, and market reputation.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    # Metric Cards Grid
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

    # SettingsCard: Exact Treasury Balance Override
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

    # SettingsCard: Preset Allocations & Solvency
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

    # Founder Header Card
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
            show_infobar(f"Restored 100% needs and skills for Founder '{f['name']}'")
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

    # Founder Vitals Card (2x2 Grid)
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
    # PAGE 3: PERSONNEL & TEAMS
    # =========================================================
    p_emp = pages["personnel"]

    # Header & Search Toolbar
    toolbar = ctk.CTkFrame(p_emp, fg_color=C_CARD_BG, corner_radius=8, border_width=1, border_color=C_BORDER)
    toolbar.pack(fill="x", pady=(0, 8), ipady=6)

    row_tb_top = ctk.CTkFrame(toolbar, fg_color="transparent")
    row_tb_top.pack(fill="x", padx=14, pady=(6, 4))

    entry_search = ctk.CTkEntry(row_tb_top, height=32, width=220, font=ctk.CTkFont(family="Segoe UI", size=11),
                                placeholder_text="Search personnel...", textvariable=search_query_var)
    entry_search.pack(side="left", padx=(0, 8))

    def on_search_update(*args):
        update_roster_view()

    search_query_var.trace_add("write", on_search_update)

    ctk.CTkLabel(row_tb_top, text="Team:", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC).pack(side="left", padx=(4, 4))
    opt_team = ctk.CTkOptionMenu(row_tb_top, variable=selected_team_filter, height=32, width=140,
                                 font=ctk.CTkFont(family="Segoe UI", size=11),
                                 fg_color=C_BTN_SEC, text_color=C_TEXT_PRI,
                                 button_color=C_BTN_SEC, button_hover_color=C_BTN_SEC_HOVER,
                                 values=["All Teams"], command=lambda v: update_roster_view())
    opt_team.pack(side="left", padx=(0, 10))

    lbl_emp_count_badge = ctk.CTkLabel(row_tb_top, text="33 Personnel",
                                       font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                       fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, corner_radius=4, padx=8, pady=3)
    lbl_emp_count_badge.pack(side="left")

    # Batch Actions Row
    row_batch = ctk.CTkFrame(toolbar, fg_color="transparent")
    row_batch.pack(fill="x", padx=14, pady=(4, 6))

    ctk.CTkButton(row_batch, text="Restore All Needs", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_employees_needs(), show_infobar("Restored needs for all personnel"), update_telemetry())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="Max All Skills", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_employees_skills(), show_infobar("Maxed base skills for all personnel"), update_telemetry())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="Elevate Specs (3 Stars)", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.max_all_employees_specs(3), show_infobar("Elevated specializations to Level 3 for all personnel"), update_telemetry())).pack(side="left", expand=True, fill="x", padx=2)
    ctk.CTkButton(row_batch, text="Add +20 Spec EXP", height=28, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER,
                  command=lambda: (game.add_all_employees_spec_exp(20.0), show_infobar("Added +20 Specialization EXP to all personnel"), update_telemetry())).pack(side="left", expand=True, fill="x", padx=2)

    # Master-Detail Container
    row_master_detail = ctk.CTkFrame(p_emp, fg_color="transparent")
    row_master_detail.pack(fill="both", expand=True)

    # Left: Personnel Roster List
    frame_roster = ctk.CTkScrollableFrame(row_master_detail, fg_color=C_CARD_BG, corner_radius=8,
                                          border_width=1, border_color=C_BORDER)
    frame_roster.pack(side="left", fill="both", expand=True, padx=(0, 8))

    # Right: Personnel Inspector Panel
    frame_inspector = ctk.CTkFrame(row_master_detail, width=320, fg_color=C_CARD_BG, corner_radius=8,
                                   border_width=1, border_color=C_BORDER)
    frame_inspector.pack(side="right", fill="both")
    frame_inspector.pack_propagate(False)

    ctk.CTkLabel(frame_inspector, text="Personnel Inspector", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=C_TEXT_SEC).pack(anchor="w", padx=14, pady=(12, 2))
    lbl_insp_name = ctk.CTkLabel(frame_inspector, text="Select an employee", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), text_color=C_TEXT_PRI)
    lbl_insp_name.pack(anchor="w", padx=14)
    lbl_insp_team = ctk.CTkLabel(frame_inspector, text="Team: N/A | Salary: $0", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_SEC)
    lbl_insp_team.pack(anchor="w", padx=14, pady=(0, 8))

    row_insp_btns = ctk.CTkFrame(frame_inspector, fg_color="transparent")
    row_insp_btns.pack(fill="x", padx=12, pady=4)

    def on_insp_boost():
        e = current_selected_emp[0]
        if not e:
            show_infobar("Select an employee first", is_success=False)
            return
        game.max_employee_needs(e["emp_ptr"])
        game.max_employee_skills(e["emp_ptr"])
        game.max_employee_specs(e["emp_ptr"], 3)
        game.add_employee_spec_exp(e["emp_ptr"], 25.0)
        show_infobar(f"Restored needs, skills, and specializations for {e['name']}")
        update_telemetry()

    def on_insp_salary_toggle():
        e = current_selected_emp[0]
        if not e:
            show_infobar("Select an employee first", is_success=False)
            return
        new_sal = 0.0 if e["salary"] > 0 else 1000.0
        game.set_employee_salary(e["emp_ptr"], new_sal)
        show_infobar(f"Assigned ${new_sal:,.0f} salary to {e['name']}")
        update_telemetry()

    btn_insp_boost = ctk.CTkButton(row_insp_btns, text="Restore Needs & Skills", height=30, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                   fg_color=C_ACCENT, text_color=C_ACCENT_TEXT, hover_color=C_ACCENT_HOVER, command=on_insp_boost)
    btn_insp_boost.pack(fill="x", pady=2)

    btn_insp_free = ctk.CTkButton(row_insp_btns, text="Assign $0 Salary (Free Labor)", height=30, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                  fg_color=C_BTN_SEC, text_color=C_TEXT_PRI, hover_color=C_BTN_SEC_HOVER, command=on_insp_salary_toggle)
    btn_insp_free.pack(fill="x", pady=2)

    # Inspector Vitals
    c_insp_vitals = ctk.CTkFrame(frame_inspector, fg_color=C_CARD_ALT, corner_radius=6, border_width=1, border_color=C_BORDER_SUBTLE)
    c_insp_vitals.pack(fill="x", padx=12, pady=8, ipady=4)
    lbl_insp_v1 = ctk.CTkLabel(c_insp_vitals, text="Energy: 100% | Stress: 0%", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_PRI)
    lbl_insp_v1.pack(anchor="w", padx=10, pady=2)
    lbl_insp_v2 = ctk.CTkLabel(c_insp_vitals, text="Satisfaction: 150% | Creativity: 100%", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
    lbl_insp_v2.pack(anchor="w", padx=10, pady=2)

    ctk.CTkLabel(frame_inspector, text="Active Specializations", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_TEXT_SEC).pack(anchor="w", padx=14, pady=(4, 2))
    frame_insp_specs = ctk.CTkScrollableFrame(frame_inspector, fg_color=C_CARD_ALT, corner_radius=6, height=180)
    frame_insp_specs.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def select_employee_for_inspector(e: dict):
        current_selected_emp[0] = e
        tag = " [Founder]" if e["founder"] else ""
        lbl_insp_name.configure(text=f"{e['name']}{tag}")
        lbl_insp_team.configure(text=f"Team: {e['team']} | Salary: ${e['salary']:,.0f}/mo")
        lbl_insp_v1.configure(text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}%")
        lbl_insp_v2.configure(text=f"Satisfaction: {e['satisfaction']*100:.0f}% | Creativity: {e['creativity']*100:.0f}%")

        for w in frame_insp_specs.winfo_children():
            w.destroy()

        has_specs = False
        for rname in GameMemory.ROLE_NAMES:
            specs = e["specs"].get(rname, {})
            if specs:
                has_specs = True
                ctk.CTkLabel(frame_insp_specs, text=f"{rname}", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=C_ACCENT).pack(anchor="w", pady=(3, 1))
                spec_line = ", ".join([f"{k} (Lvl {lvl})" for k, lvl in specs.items()])
                ctk.CTkLabel(frame_insp_specs, text=f"  {spec_line}", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC).pack(anchor="w")

        if not has_specs:
            ctk.CTkLabel(frame_insp_specs, text="No active specializations", font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_MUTED).pack(anchor="w", pady=6)

    def update_roster_view():
        emps = game.get_employees()
        q = search_query_var.get().strip().lower()
        t_filter = selected_team_filter.get()

        filtered = []
        for e in emps:
            if t_filter != "All Teams" and e["team"] != t_filter:
                continue
            if q and (q not in e["name"].lower() and q not in e["team"].lower()):
                continue
            filtered.append(e)

        for w in frame_roster.winfo_children():
            w.destroy()

        if not filtered:
            ctk.CTkLabel(frame_roster, text="No matching personnel found.", font=ctk.CTkFont(family="Segoe UI", size=11), text_color=C_TEXT_MUTED).pack(pady=20)
            return

        for e in filtered:
            is_sel = current_selected_emp[0] and current_selected_emp[0]["actor_ptr"] == e["actor_ptr"]
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

            lbl_vitals = ctk.CTkLabel(row_c, text=f"Energy: {e['energy']*100:.0f}% | Stress: {e['stress']*100:.0f}% | ${e['salary']:,.0f}",
                                      font=ctk.CTkFont(family="Segoe UI", size=10), text_color=C_TEXT_SEC)
            lbl_vitals.pack(side="right")

            def make_click_handler(emp_data=e):
                def handler(event=None):
                    select_employee_for_inspector(emp_data)
                    update_roster_view()
                return handler

            card.bind("<Button-1>", make_click_handler())
            row_c.bind("<Button-1>", make_click_handler())
            lbl_name.bind("<Button-1>", make_click_handler())
            lbl_vitals.bind("<Button-1>", make_click_handler())

    # =========================================================
    # PAGE 4: WORLD & RULES
    # =========================================================
    p_wrld = pages["world"]

    ctk.CTkLabel(p_wrld, text="World & Rules", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), text_color=C_TEXT_PRI).pack(anchor="w", pady=(0, 2))
    ctk.CTkLabel(p_wrld, text="Modify simulation speed, furniture availability, and fixture lighting.", font=ctk.CTkFont(family="Segoe UI", size=12), text_color=C_TEXT_SEC).pack(anchor="w", pady=(0, 14))

    # Setting Card: Furniture Unlock
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

    # Setting Card: Simulation Speed Multiplier
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

        # Founder Profile Updates
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
                    lbl_t.configure(text=f"{rname} (Base Skill: {bskill})")
                    lbl_s.configure(text=specs_desc)

        # Team Filter Options
        emps = game.get_employees()
        lbl_emp_count_badge.configure(text=f"{len(emps)} Personnel")
        teams_set = sorted(list({e["team"] for e in emps if e["team"]}))
        all_options = ["All Teams"] + teams_set
        if opt_team.cget("values") != all_options:
            opt_team.configure(values=all_options)

        update_roster_view()

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
