# Software Inc. - Memory Trainer

A safe, zero-crash external memory trainer and modification suite for **Software Inc.** (Windows 64-bit Unity Mono).
Engineered with a **native Windows 11 Fluent Design (WinUI 3)** desktop application supporting both **Light Mode** and **Dark Mode**.

---

## 🚀 Key Features

### 💻 Windows 11 Fluent Design UI
* **Light & Dark Mode**: Seamless support for Windows System theme, Dark Mode, and Light Mode with instant real-time switching.
* **WinUI 3 Design Language**: Clean SettingsCards, native navigation rail, proper Windows typography (`Segoe UI`), subtle borders, and zero clutter.
* **Windows InfoBar**: Native status notifications and telemetry pills without invasive popups.

### 👤 Deep Personnel & Staff Inspector
Select any employee or facility staff member in the live roster to open the comprehensive 5-tab inspector:
* **Zero-Lag Architecture**: Event-driven roster caching with instant in-place card selection. The roster never flickers or resets scroll positions.
* **Point Badges in Roster**: Every personnel card displays live unspent points (`| X Pts`), energy, stress, salary, and active weaknesses directly in the list.
* **On-Demand Memory Sync**: Includes a dedicated **↻ Refresh Roster** button and automatic sync on tab switch or batch actions.

* **Tab 1: Overview**
  * Live status pill (Founder / Employee, Team assignment, Current Vitals summary).
  * **Specialization Points Card**: Displays available unspent points, allocated/spent points, per-role breakdown (Lead, Code, Design, Art, Service), and quick point buttons (**+5 Pts (All)**, **+10 Pts (All)**, **Max (50)**, **Refund Used**).
  * Direct Salary Editor (adjust salary dynamically or click **Free Labor** for $0 salary).
  * Quick Actions: **Instant Godmode** (max needs & skills, +25 points) and **Free Labor ($0)**.
* **Tab 2: Needs & Vitals**
  * Real-time sliders for individual needs: **Energy**, **Stress** (lower is better), **Satisfaction**, **Creativity**, **Hunger**, **Social**, and **Bladder**.
  * Instant **Maximize Vitals** preset.
* **Tab 3: Skills & Points (Specialization Points & EXP)**
  * Sliders for all 5 foundational role skills (0% to 100%): **Lead**, **Code**, **Design**, **Art**, and **Service**.
  * **Quick Point Bundles**: Grant **+5**, **+10**, or **+25** points to all 5 roles at once, or click **Refund Used** to reset spent point capacity.
  * **Per-Role Points Editor**:
    * Live status display: `Unspent: X.X pts | Allocated: Y`
    * Quick Presets: **+1 Pt**, **+5 Pts**, **+10 Pts**, **Max (25)**
    * **Direct Numeric Input Box**: Enter any exact number of points and click **Apply** (or click **Reset (0)**).
* **Tab 4: Subfield Specializations**
  * Live status header showing **Available Points to Spend** and **+10 Pts (All)** quick button.
  * Full interactive grid of all subfields (System, Hardware, 2D, 3D, Audio, Network, HR, Automation, Marketing, Support, Law, Accounting).
  * Clickable star-rating selector for each subfield: **0★**, **1★**, **2★**, or **3★** with immediate in-game updates.
  * Helpful guide card for unspecialized personnel explaining how to grant points and specialize.
* **Tab 5: Weaknesses & Traits Management**
  * Trait Badges: visual chips distinguishing active positive traits (teal) and negative weaknesses (red).
  * **Remove Weaknesses**: Cleanses all 8 negative traits while preserving positive perks.
  * **Grant Master Traits**: Equips top-tier traits (*FastLearner*, *BigBrain*, *SuperFocus*, *ThisIsFine*, *Clean*).
  * **Full Trait Toggle Grid**: Interactive checkable list of all 33 game traits to customize the employee's personality and work habits.

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
  * **Max All Active Specializations**: Sets every active sub-specialization to 3 Stars.
  * **Specialization EXP Injections**: Adds +20.0 EXP per role across all employees.
  * **Remove All Weaknesses**: Cleanses negative traits across the entire company roster in one click.
  * **Assign Free Labor ($0 Salary)**: Sets all employee salaries to $0.
  * **Lock Needs (Freeze)**: Continuous real-time lock to prevent fatigue and burnout.

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

## 🧬 Supported Traits & Weaknesses Reference

Software Inc. stores employee traits as a 64-bit bitmask at `Employee + 0x150`. All 33 traits are fully mapped:

| Trait | Type | Bit Position | Effect / Description |
| :--- | :---: | :---: | :--- |
| **FastLearner** | Positive | `1 << 0` | Learns and gains skill points substantially faster |
| **Independant** | Positive | `1 << 1` | Works effectively alone without supervision |
| **BigBrain** | Positive | `1 << 2` | Higher skill maximum and faster work output |
| **Humble** | Positive | `1 << 3` | Lower salary demands and humble attitude |
| **Capacitor** | Positive | `1 << 4` | Energy drains much slower |
| **WalkItOff** | Positive | `1 << 5` | Recovers quickly from minor ailments |
| **ThisIsFine** | Positive | `1 << 6` | High stress resistance under heavy workloads |
| **NightOwl** | Positive | `1 << 7` | Bonus efficiency during night shifts |
| **BornLeader** | Positive | `1 << 8` | Significant leadership and team synergy boost |
| **FirmwareInc** | Positive | `1 << 9` | Affinity for hardware and low-level code |
| **SuperFocus** | Positive | `1 << 10` | Eliminates work distractions |
| **Unphased** | Positive | `1 << 11` | Immune to office noise and environmental chatter |
| **JustTheFlu** | Positive | `1 << 12` | Resistant to illness and absenteeism |
| **Detached** | Positive | `1 << 13` | Social needs deplete much slower |
| **Stressed** | **Weakness** | `1 << 14` | High stress vulnerability and prone to breakdowns |
| **Hypochondriac** | **Weakness** | `1 << 15` | Frequently takes sick leave for trivial reasons |
| **SlowEater** | **Weakness** | `1 << 16` | Spends prolonged periods eating at meals |
| **NervousBladder** | **Weakness** | `1 << 17` | Frequent bathroom breaks |
| **BumLeg** | **Weakness** | `1 << 18` | Slower movement speed across the office |
| **Forgetful** | **Weakness** | `1 << 19` | Occasionally forgets tasks or makes mistakes |
| **Cupholder** | Positive | `1 << 20` | Always has a drink handy |
| **NeatFreak** | Positive | `1 << 21` | Keeps workstations immaculate |
| **SilentButDeadly**| Positive | `1 << 22` | Discreet social presence |
| **Watch** | Positive | `1 << 23` | Perfect punctuality |
| **WalkInstead** | Positive | `1 << 24` | Prefers walking over elevators/transit |
| **UnderTheWeather**| **Weakness** | `1 << 25` | Frequently feels sick or fatigued |
| **OldSole** | Positive | `1 << 26` | Experienced and resilient |
| **Sunshine** | Positive | `1 << 27` | Radiates positive mood to teammates |
| **Skyscraper** | Positive | `1 << 28` | High tolerance for tall office buildings |
| **RGBThumb** | Positive | `1 << 29` | Passion for art, design, and aesthetics |
| **FriendMaker** | Positive | `1 << 30` | Boosts socialization across the entire team |
| **Clean** | Positive | `1 << 31` | High hygiene and environmental cleanliness |
| **Claustrophobic** | **Weakness** | `1 << 32` | Suffers severe stress in small or crowded rooms |

---

## ⌨️ Global In-Game Hotkeys

Hotkeys work seamlessly in the background while playing Software Inc. without requiring alt-tabbing:

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

1. **Read-Only Symbol Walk**: Inspects `mono-2.0-bdwgc.dll`'s `loaded_assemblies` linked list and traverses `Assembly-CSharp`'s `MonoInternalHashTable` to locate runtime pointers for `GameSettings`, `Company`, `Cheats`, `TimeOfDay`, `ActorManager`, and `Team`.
2. **Dynamic Pointer Chaining**:
   * Company at `GameSettings.Instance + 0x128`
   * ActorManager at `GameSettings.Instance + 0x120`
   * Active Actors at `ActorManager + 0x10`
   * Facility Staff at `ActorManager + 0x18`
   * Teams Dictionary at `ActorManager + 0x40`
   * Team Reference per Actor at `Actor + 0x270`
   * Employee Data at `Actor + 0x138`
   * Specialization EXP Array at `Employee + 0x20`
   * Specializations Dict Array at `Employee + 0x18`
   * Traits Bitmask at `Employee + 0x150`
3. **Safe Primitive Writes**: Writes only validated primitives (`double`, `float`, `uint64`, `int32`, `byte`) into verified heap structures via `WriteProcessMemory`, ensuring 100% game stability.

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

Perform quick actions directly from your terminal:

```powershell
# View all available CLI options
python trainer.py --help

# Check live game status, founder, and total personnel
python trainer.py --status

# List all teams, employees, facility staff, salaries, and weaknesses
python trainer.py --list-teams

# Remove all weaknesses across all company personnel
python trainer.py --remove-weaknesses

# Enable Godmode for Founder / Player (100% Needs, 100% Skills, 3-Star Specs, +50 EXP)
python trainer.py --max-founder

# Max all needs and base skills for all employees & staff
python trainer.py --max-employees

# Elevate all active specializations across all employees to Level 3 (3 Stars)
python trainer.py --max-specs

# Add +20 Specialization points to all employees
python trainer.py --add-spec-exp 20.0

# Set exact specialization points across all roles for all employees
python trainer.py --set-spec-points 25.0

# Reset spent specialization points (refund capacity) for all employees
python trainer.py --reset-spec-used

# Set all salaries to $0 (free labor)
python trainer.py --free-salaries

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
