# Software Inc. - Memory Trainer

A safe, zero-crash external memory trainer and modification suite for **Software Inc.** (Windows 64-bit Unity Mono).
Engineered with a **native Windows 11 Fluent Design (WinUI 3)** desktop application supporting both **Light Mode** and **Dark Mode**.

---

## 🚀 Key Features

### 💻 Windows 11 Fluent Design UI
* **Light & Dark Mode**: Seamless support for Windows System theme, Dark Mode, and Light Mode with instant real-time switching.
* **WinUI 3 Design Language**: Clean SettingsCards, native navigation rail, proper Windows typography (`Segoe UI`), subtle borders, and zero clutter.
* **Windows InfoBar**: Native status notifications and telemetry pills without invasive popups.

### 👑 Player & Founder Management
* **Dedicated Founder Profile**: Direct telemetry and controls for the player character / company CEO.
* **Founder Godmode**: Instantly restores 100% Energy, 100% Hunger, 100% Social, 100% Bladder, 200% Job Satisfaction, 100% Creativity, 100% Skill Ceiling, and eliminates Stress (0%).
* **Max Founder Base Skills**: Boosts all 5 foundational roles (Lead, Code, Design, Art, Service) to 100%.
* **Max Founder Specializations**: Elevates all active specializations across all roles to 3 Stars (Level 3).
* **Founder Specialization EXP Booster**: Injects +50 Specialization EXP so you can allocate additional custom points freely.

### 👥 Staff & Team Architecture
* **Full Personnel Detection**: Aggregates all employees across all active teams (`Teams` dictionary), off-shift members (`Awaiting` roster), and dedicated `Facility Staff` (cleaning, maintenance, IT, security).
* **Team-Based Filtering**: Dropdown filtering in the GUI and grouped views in CLI (Core, Second, Support, Emergence, Marketing, Facility Staff).
* **Batch Operations**:
  * **Max All Needs**: Restores 100% Energy, 100% Hunger, 100% Social, 100% Satisfaction, and drops Stress to 0% for every single personnel.
  * **Max All Base Skills**: Boosts all 5 core roles to 100% across the entire roster.
  * **Max All Active Specializations**: Sets every active sub-specialization (System, Hardware, 2D, 3D, Audio, Network, HR, Automation, Marketing, Support, Law, Accounting) to 3 Stars.
  * **Specialization EXP Injections**: Adds +20.0 EXP per role across all employees.
  * **Lock Needs (Freeze)**: Continuous real-time lock to prevent fatigue and burnout.
* **Selected Employee Inspector & Editor**: Click any employee in the roster to view granular specializations, godmode their stats, or adjust their salary (including setting $0 for volunteer labor).

### 💰 Corporate Finances
* **Add Cash**: Instant cash injections (+$100k, +$1M, +$10M, +$100M).
* **Exact Balance Override**: Set company bank account to any specific value.
* **Reputation Maximizer**: Set Business Reputation to 100% instantly.
* **Fan Base Booster**: Add fans (+10k, +100k, +1M).
* **Bankruptcy Protection**: Clear the corporate bankruptcy flag with one click.

### 🌍 World & Gameplay Modifiers
* **Unlock All Furniture**: Unlocks the entire furniture and fixture catalog immediately (`Cheats.UnlockFurn`).
* **Force Lights Always On**: Keeps all lamps and light fixtures continuously on (`Cheats.ForceLights`).
* **Disable Darkness**: Removes darkness shaders (`Cheats.DisableDarkness`).
* **Infinite Subsidiaries**: Removes the subsidiary cap (`Cheats.InfiniteSubs`).
* **Engine Speed Multiplier**: Cycle between 1x (Normal), 2x (Fast), 5x (Turbo), and 10x (Ultra).

---

## ⌨️ Global In-Game Hotkeys

Hotkeys work seamlessly while playing Software Inc. without requiring alt-tabbing:

| Hotkey | Action | Description |
| :--- | :--- | :--- |
| **NUMPAD 1** | `+$1,000,000 Cash` | Instant cash transfer to company account |
| **NUMPAD 2** | `+$10,000,000 Cash` | Large corporate cash boost |
| **NUMPAD 3** | `Max Employee Needs` | 100% Energy/Hunger/Social, 0% Stress |
| **NUMPAD 4** | `Max Employee Skills` | 100% Base Skills across all 5 roles |
| **NUMPAD 5** | `Max Business Reputation` | Sets company business reputation to 100% |
| **NUMPAD 6** | `+50,000 Fans` | Instant fan base boost |
| **NUMPAD 7** | `Unlock All Furniture` | Instant catalog unlock |
| **NUMPAD 8** | `Force Lights ON` | Keeps all room lighting on |
| **NUMPAD 9** | `Turbo Speed (5x)` | Toggles between 1x normal and 5x speed |

*(A soft system audio beep confirms each hotkey activation.)*

---

## 🛠️ Architecture & Safety Standards

Unlike invasive DLL injection that can destabilize Unity garbage collection or trigger memory corruptions, this trainer utilizes an **external dynamic Mono symbol resolution engine**:

1. **Read-Only Symbol Walk**: Inspects `mono-2.0-bdwgc.dll`'s `loaded_assemblies` linked list and traverses `Assembly-CSharp`'s `MonoInternalHashTable` to locate the exact runtime pointers for `GameSettings`, `Company`, `Cheats`, `TimeOfDay`, `ActorManager`, and `Team`.
2. **Dynamic Pointer Chaining**: Resolves all objects dynamically at runtime:
   * Company at `GameSettings.Instance + 0x128`
   * ActorManager at `GameSettings.Instance + 0x120`
   * Active Actors at `ActorManager + 0x10`
   * Facility Staff at `ActorManager + 0x18`
   * Teams Dictionary at `ActorManager + 0x40`
   * Team Reference per Actor at `Actor + 0x270`
   * Employee Data at `Actor + 0x138`
3. **Safe Primitive Writes**: Writes only validated primitives (`double`, `float`, `uint`, `byte`) into verified heap structures via `WriteProcessMemory`, ensuring 100% game stability.

---

## 💻 How to Run

### Requirements

Python 3.10+ with `customtkinter`:

```powershell
pip install customtkinter
```

### Modern Desktop Application (GUI)

```powershell
python trainer.py
```

### Command Line Interface (CLI)

Perform quick one-liner actions directly from your terminal:

```powershell
# Check live game status, founder, and total personnel
python trainer.py --status

# List all teams, employees, facility staff, and specializations
python trainer.py --list-teams

# Enable Godmode for Founder / Player (100% Needs, 100% Skills, 3-Star Specs, +50 EXP)
python trainer.py --max-founder

# Max all needs and base skills for all employees & staff
python trainer.py --max-employees

# Elevate all active specializations across all employees to Level 3 (3 Stars)
python trainer.py --max-specs

# Add +20 Specialization EXP to all employees
python trainer.py --add-spec-exp 20.0

# Add $5,000,000 cash
python trainer.py --add-money 5000000

# Unlock entire furniture catalog
python trainer.py --unlock-furniture

# Set game speed to 5x turbo
python trainer.py --speed 5.0
```

---

## 📁 Repository Structure

```
software-inc/
├── .gitignore                     # Git ignore rules
├── README.md                      # Trainer documentation & guide
└── trainer.py                     # Windows 11 Fluent GUI & CLI Trainer
```
