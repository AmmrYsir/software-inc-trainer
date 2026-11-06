"""
Software Inc. Trainer - Core Constants & Enums
"""

from typing import Dict, List, Tuple

# Win32 Process & Virtual Key Constants
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

HOTKEY_DEFINITIONS = [
    ("Numpad 1", "Add $10,000,000 to Corporate Treasury", "add_money_10m"),
    ("Numpad 2", "Restore Founder Vitals & Max Skills", "max_founder"),
    ("Numpad 3", "Restore All Employee Needs (100%)", "max_all_needs"),
    ("Numpad 4", "Max All Employee Base Skills (100%)", "max_all_skills"),
    ("Numpad 5", "Max Company Reputation (100%)", "max_rep"),
    ("Numpad 6", "Add 50,000 Company Fans", "add_fans_50k"),
    ("Numpad 7", "Unlock All Furniture & Equipment", "unlock_furniture"),
    ("Numpad 8", "Force All Building Lights ON", "force_lights"),
    ("Numpad 9", "Toggle Simulation Turbo Speed (5.0x / 1.0x)", "toggle_turbo"),
]

# Employee Roles & Specialization Hierarchy
ROLE_NAMES: List[str] = ["Lead", "Code", "Design", "Art", "Service"]

ROLE_ALL_SPECIALIZATIONS: Dict[str, List[str]] = {
    "Lead": ["Automation", "HR", "Multitasking", "Socialization"],
    "Code": ["2D", "3D", "Audio", "Hardware", "Network", "Sub-Genre", "System"],
    "Design": ["2D", "3D", "Audio", "Hardware", "Network", "Sub-Genre", "System"],
    "Art": ["2D", "3D", "Audio"],
    "Service": ["Accounting", "Law", "Marketing", "Support"],
}

# Granular Needs List
NEED_NAMES: List[str] = [
    "Energy",
    "Hunger",
    "Social",
    "Comfort",
    "Hygiene",
    "Bladder",
]

# Complete Enum Mapping of all 33 Traits in Software Inc.
# Format: (Name, Bitmask, IsWeakness)
ALL_TRAITS: List[Tuple[str, int, bool]] = [
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
    ("Earplugs", 1 << 23, False),
    ("CoffeeLover", 1 << 24, False),
    ("Workaholic", 1 << 25, False),
    ("Nomad", 1 << 26, False),
    ("SnackLover", 1 << 27, False),
    ("SocialButterfly", 1 << 28, False),
    ("SmallBladder", 1 << 29, True),     # Weakness
    ("HeavyEater", 1 << 30, True),       # Weakness
    ("Genius", 1 << 31, False),
    ("Polymath", 1 << 32, False),
]

# Bitmask calculations
WEAKNESSES_MASK: int = sum(mask for _, mask, is_w in ALL_TRAITS if is_w)
MASTER_TRAITS_MASK: int = sum(mask for _, mask, is_w in ALL_TRAITS if not is_w)

# UI Presets
CASH_PRESETS: List[Tuple[str, float]] = [
    ("+$1M", 1_000_000.0),
    ("+$10M", 10_000_000.0),
    ("+$50M", 50_000_000.0),
    ("+$100M", 100_000_000.0),
    ("+$1B", 1_000_000_000.0),
]

FANS_PRESETS: List[Tuple[str, int]] = [
    ("+10K", 10_000),
    ("+50K", 50_000),
    ("+250K", 250_000),
    ("+1M", 1_000_000),
]

SPEED_PRESETS: List[Tuple[str, float]] = [
    ("0.5x", 0.5),
    ("1.0x", 1.0),
    ("2.0x", 2.0),
    ("5.0x", 5.0),
    ("10.0x", 10.0),
]
