"""
Software Inc. Trainer - Global Header Ribbon Component
Persistent status strip displaying process health, game clock, quick-cheat toggles, and company KPIs.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    SwitchButton,
    PrimaryPushButton,
    PushButton,
    FluentIcon as FIF,
    PillPushButton,
)


class HeaderRibbon(QFrame):
    """
    Persistent global header bar providing real-time game status,
    immediate cheat switches, and live company KPIs.
    """

    freezeNeedsToggled = Signal(bool)
    turboToggled = Signal(bool)
    godmodeClicked = Signal()
    refreshRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setStyleSheet("""
            HeaderRibbon {
                background-color: #202020;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        # 1. Connection Status Badge
        self.status_pill = QLabel("🔍 Searching for Game...", self)
        self.status_pill.setStyleSheet("""
            QLabel {
                background-color: #383838;
                color: #E0E0E0;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }
        """)
        layout.addWidget(self.status_pill)

        # 2. In-Game Calendar / Clock
        self.date_label = CaptionLabel("📅 --", self)
        self.date_label.setStyleSheet("color: #A0A0A0; font-size: 12px; font-weight: 500;")
        layout.addWidget(self.date_label)

        # Divider
        div1 = QFrame(self)
        div1.setFrameShape(QFrame.VLine)
        div1.setStyleSheet("color: rgba(255, 255, 255, 0.1);")
        layout.addWidget(div1)

        # 3. Quick Cheats Bar
        # Freeze Needs Switch
        freeze_lbl = CaptionLabel("Freeze Needs:", self)
        freeze_lbl.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(freeze_lbl)

        self.freeze_switch = SwitchButton(self)
        self.freeze_switch.setToolTip("Continuously lock all employee needs to 100%")
        self.freeze_switch.checkedChanged.connect(self.freezeNeedsToggled.emit)
        layout.addWidget(self.freeze_switch)

        # Turbo Speed Switch
        turbo_lbl = CaptionLabel("Turbo 5x:", self)
        turbo_lbl.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(turbo_lbl)

        self.turbo_switch = SwitchButton(self)
        self.turbo_switch.setToolTip("Toggle simulation speed to 5.0x")
        self.turbo_switch.checkedChanged.connect(self.turboToggled.emit)
        layout.addWidget(self.turbo_switch)

        # Godmode All Personnel Button
        self.godmode_btn = PushButton(FIF.BRUSH, "Godmode Staff", self)
        self.godmode_btn.setToolTip("Max out Needs & Base Skills, and clear weaknesses for ALL personnel")
        self.godmode_btn.clicked.connect(self.godmodeClicked.emit)
        layout.addWidget(self.godmode_btn)

        layout.addStretch(1)

        # 4. Live Global KPIs
        # Treasury
        self.treasury_badge = QLabel("💰 Treasury: --", self)
        self.treasury_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(16, 124, 65, 0.2);
                color: #6CCB5F;
                border: 1px solid rgba(16, 124, 65, 0.5);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.treasury_badge)

        # Fans
        self.fans_badge = QLabel("⭐ Fans: --", self)
        self.fans_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 120, 212, 0.15);
                color: #60CDFF;
                border: 1px solid rgba(0, 120, 212, 0.4);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        layout.addWidget(self.fans_badge)

        # Business Reputation
        self.rep_badge = QLabel("📈 Rep: --%", self)
        self.rep_badge.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.05);
                color: #E0E0E0;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        layout.addWidget(self.rep_badge)

    def set_connection(self, attached: bool, info: dict = None):
        if attached and info:
            pid = info.get("pid", 0)
            self.status_pill.setText(f"🟢 Attached (PID {pid} | Mono x64)")
            self.status_pill.setStyleSheet("""
                QLabel {
                    background-color: #107C41;
                    color: #FFFFFF;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
        else:
            self.status_pill.setText("🔍 Searching for Game...")
            self.status_pill.setStyleSheet("""
                QLabel {
                    background-color: #383838;
                    color: #B0B0B0;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 600;
                }
            """)

    def update_telemetry(self, data: dict):
        # Date & Time
        date_str = data.get("date_str", "")
        time_str = data.get("time_str", "")
        if date_str:
            self.date_label.setText(f"📅 {date_str} ({time_str})")

        # Treasury
        money = data.get("money", 0.0)
        if abs(money) >= 1_000_000_000:
            formatted_cash = f"${money / 1_000_000_000:.2f}B"
        elif abs(money) >= 1_000_000:
            formatted_cash = f"${money / 1_000_000:.2f}M"
        elif abs(money) >= 1_000:
            formatted_cash = f"${money / 1_000:.1f}K"
        else:
            formatted_cash = f"${money:,.0f}"
        self.treasury_badge.setText(f"💰 {formatted_cash}")

        # Fans
        fans = data.get("fans", 0)
        if fans >= 1_000_000:
            formatted_fans = f"{fans / 1_000_000:.2f}M"
        elif fans >= 1_000:
            formatted_fans = f"{fans / 1_000:.1f}K"
        else:
            formatted_fans = f"{fans:,}"
        self.fans_badge.setText(f"⭐ {formatted_fans} Fans")

        # Reputation
        rep = data.get("reputation", 0.0)
        self.rep_badge.setText(f"📈 {rep * 100:.0f}% Rep")

    def set_freeze_state(self, active: bool):
        if self.freeze_switch.isChecked() != active:
            self.freeze_switch.setChecked(active)

    def set_turbo_state(self, active: bool):
        if self.turbo_switch.isChecked() != active:
            self.turbo_switch.setChecked(active)
