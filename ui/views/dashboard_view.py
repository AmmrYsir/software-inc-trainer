"""
Software Inc. Trainer - Dashboard View
Executive overview of Treasury, Solvency, Market Standing, VIP Founder, and Studio Operations.
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QFrame,
    QLabel,
)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    CardWidget,
    ElevatedCardWidget,
    HeaderCardWidget,
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    PushButton,
    PrimaryPushButton,
    ToolButton,
    DoubleSpinBox,
    SpinBox,
    Slider,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
)

from ..components.stat_card import StatCard
from core.memory import get_game_memory
from core.constants import CASH_PRESETS, FANS_PRESETS


class DashboardView(QScrollArea):
    """
    Executive Studio Dashboard providing high-level telemetry and financial commands.
    """

    navigateToTalentRequested = Signal(str)  # Target employee name / pointer

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.game = get_game_memory()

        self._founder_data = {}
        self._current_money = 0.0
        self._current_fans = 0
        self._current_rep = 1.0

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background-color: transparent;")

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 28)
        layout.setSpacing(20)

        # 1. Header Title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        self.page_title = TitleLabel("Executive Studio Dashboard", content)
        self.page_subtitle = CaptionLabel(
            "High-level studio operations, treasury reserves, market standing, and executive VIP founder management.",
            content,
        )
        self.page_subtitle.setStyleSheet("color: #A0A0A0;")
        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_subtitle)
        layout.addLayout(title_layout)

        # 2. Key Metrics Row
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(16)

        self.card_treasury = StatCard("CORPORATE TREASURY", "$0.00", "Available Liquidity", FIF.TILES, content)
        self.card_fans = StatCard("TOTAL FANS", "0", "Global Brand Followers", FIF.PEOPLE, content)
        self.card_rep = StatCard("BUSINESS REPUTATION", "100%", "Market Influence & Trust", FIF.GLOBE, content)
        self.card_solvency = StatCard("SOLVENCY STATUS", "Healthy", "Zero active debt strikes", FIF.COMPLETED, content)

        kpi_grid.addWidget(self.card_treasury, 0, 0)
        kpi_grid.addWidget(self.card_fans, 0, 1)
        kpi_grid.addWidget(self.card_rep, 0, 2)
        kpi_grid.addWidget(self.card_solvency, 0, 3)
        layout.addLayout(kpi_grid)

        # 3. Financial & Solvency Command Card
        fin_card = HeaderCardWidget(content)
        fin_card.setTitle("Financial Capital & Solvency Injections")
        fin_layout = QVBoxLayout()
        fin_card.viewLayout.addLayout(fin_layout)
        fin_layout.setContentsMargins(10, 10, 10, 10)
        fin_layout.setSpacing(14)

        # Quick preset buttons row
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(10)
        preset_label = StrongBodyLabel("Quick Injections:", fin_card)
        preset_layout.addWidget(preset_label)

        for label, amt in CASH_PRESETS:
            btn = PushButton(FIF.ADD, label, fin_card)
            btn.clicked.connect(lambda checked=False, val=amt: self._inject_cash(val))
            preset_layout.addWidget(btn)

        preset_layout.addStretch(1)

        # Clear Bankruptcy Button
        clear_bankrupt_btn = PushButton(FIF.ACCEPT, "Clear Bankruptcy", fin_card)
        clear_bankrupt_btn.setToolTip("Resets debt counters, bankruptcy notices, and active auction strikes")
        clear_bankrupt_btn.clicked.connect(self._clear_bankruptcy)
        preset_layout.addWidget(clear_bankrupt_btn)

        fin_layout.addLayout(preset_layout)

        # Custom cash input row
        custom_cash_layout = QHBoxLayout()
        custom_cash_layout.setSpacing(12)
        custom_lbl = BodyLabel("Custom Treasury Amount ($):", fin_card)
        custom_cash_layout.addWidget(custom_lbl)

        self.cash_spin = DoubleSpinBox(fin_card)
        self.cash_spin.setRange(0, 100_000_000_000.0)
        self.cash_spin.setValue(50_000_000.0)
        self.cash_spin.setSingleStep(1_000_000.0)
        self.cash_spin.setFixedWidth(200)
        custom_cash_layout.addWidget(self.cash_spin)

        set_cash_btn = PrimaryPushButton(FIF.SAVE, "Set Exact Balance", fin_card)
        set_cash_btn.clicked.connect(self._set_exact_cash)
        custom_cash_layout.addWidget(set_cash_btn)

        add_custom_btn = PushButton(FIF.ADD, "Add to Treasury", fin_card)
        add_custom_btn.clicked.connect(self._add_custom_cash)
        custom_cash_layout.addWidget(add_custom_btn)

        custom_cash_layout.addStretch(1)
        fin_layout.addLayout(custom_cash_layout)

        layout.addWidget(fin_card)

        # 4. Two-Column Row: Founder VIP Spotlight & Market Standing
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(16)

        # Left: Founder VIP Spotlight
        self.founder_card = HeaderCardWidget(content)
        self.founder_card.setTitle("VIP Founder Profile & CEO Vitals")
        founder_layout = QVBoxLayout()
        self.founder_card.viewLayout.addLayout(founder_layout)
        founder_layout.setContentsMargins(10, 10, 10, 10)
        founder_layout.setSpacing(12)

        self.founder_name_label = StrongBodyLabel("Founder: Not Detected", self.founder_card)
        self.founder_vitals_label = CaptionLabel("Energy: -- | Stress: -- | Satisfaction: --", self.founder_card)
        self.founder_vitals_label.setStyleSheet("color: #A0A0A0;")
        founder_layout.addWidget(self.founder_name_label)
        founder_layout.addWidget(self.founder_vitals_label)

        founder_actions = QHBoxLayout()
        founder_actions.setSpacing(10)

        godmode_founder_btn = PrimaryPushButton(FIF.HEART, "Godmode Founder", self.founder_card)
        godmode_founder_btn.setToolTip("100% Vitals, Max All Skills, Max Specs, Erase All Weaknesses")
        godmode_founder_btn.clicked.connect(self._godmode_founder)
        founder_actions.addWidget(godmode_founder_btn)

        inspect_founder_btn = PushButton(FIF.PEOPLE, "Inspect in Talent HQ", self.founder_card)
        inspect_founder_btn.clicked.connect(self._jump_to_founder)
        founder_actions.addWidget(inspect_founder_btn)

        founder_actions.addStretch(1)
        founder_layout.addLayout(founder_actions)
        mid_layout.addWidget(self.founder_card, stretch=1)

        # Right: Fans & Reputation Controls
        fans_card = HeaderCardWidget(content)
        fans_card.setTitle("Market Dominance & Brand Influence")
        fans_layout = QVBoxLayout()
        fans_card.viewLayout.addLayout(fans_layout)
        fans_layout.setContentsMargins(10, 10, 10, 10)
        fans_layout.setSpacing(12)

        fans_btn_layout = QHBoxLayout()
        fans_btn_layout.setSpacing(8)
        fans_lbl = BodyLabel("Grant Fans:", fans_card)
        fans_btn_layout.addWidget(fans_lbl)

        for label, val in FANS_PRESETS:
            btn = PushButton(FIF.PEOPLE, label, fans_card)
            btn.clicked.connect(lambda checked=False, f_val=val: self._add_fans(f_val))
            fans_btn_layout.addWidget(btn)

        fans_btn_layout.addStretch(1)
        fans_layout.addLayout(fans_btn_layout)

        # Reputation Slider row
        rep_layout = QHBoxLayout()
        rep_layout.setSpacing(10)
        rep_lbl = BodyLabel("Reputation:", fans_card)
        rep_layout.addWidget(rep_lbl)

        self.rep_slider = Slider(Qt.Horizontal, fans_card)
        self.rep_slider.setRange(0, 100)
        self.rep_slider.setValue(100)
        self.rep_slider.setFixedWidth(200)
        rep_layout.addWidget(self.rep_slider)

        self.rep_val_lbl = StrongBodyLabel("100%", fans_card)
        self.rep_val_lbl.setFixedWidth(45)
        self.rep_slider.valueChanged.connect(lambda v: self.rep_val_lbl.setText(f"{v}%"))
        rep_layout.addWidget(self.rep_val_lbl)

        set_rep_btn = PushButton(FIF.SAVE, "Apply Rep", fans_card)
        set_rep_btn.clicked.connect(self._apply_rep)
        rep_layout.addWidget(set_rep_btn)

        rep_layout.addStretch(1)
        fans_layout.addLayout(rep_layout)

        mid_layout.addWidget(fans_card, stretch=1)
        layout.addLayout(mid_layout)

        layout.addStretch(1)

    def _connect_signals(self):
        self.worker.telemetry_updated.connect(self._on_telemetry_updated)
        self.worker.founder_updated.connect(self._on_founder_updated)

    def _on_telemetry_updated(self, data: dict):
        # Update Treasury
        self._current_money = data.get("money", 0.0)
        money_str = f"${self._current_money:,.2f}"
        self.card_treasury.set_value(money_str)

        # Solvency
        if self._current_money < 0:
            self.card_solvency.set_value("In Deficit")
            self.card_solvency.set_subtitle("Risk of bankruptcy notices")
        else:
            self.card_solvency.set_value("Solvent")
            self.card_solvency.set_subtitle("Financially liquid & stable")

        # Fans
        self._current_fans = data.get("fans", 0)
        self.card_fans.set_value(f"{self._current_fans:,}")

        # Reputation
        self._current_rep = data.get("reputation", 0.0)
        self.card_rep.set_value(f"{self._current_rep * 100:.1f}%")

    def _on_founder_updated(self, founder: dict):
        self._founder_data = founder
        name = founder.get("name", "Unknown Founder")
        role = founder.get("role", "Lead")
        vitals = founder.get("vitals", {})

        energy = int(vitals.get("energy", 1.0) * 100)
        stress = int(vitals.get("stress", 0.0) * 100)
        satisfaction = int(vitals.get("satisfaction", 1.0) * 100)

        self.founder_name_label.setText(f"Founder: {name} ({role})")
        self.founder_vitals_label.setText(
            f"⚡ Energy: {energy}%  |  ⚠️ Stress: {stress}%  |  😊 Satisfaction: {satisfaction}%"
        )

    def _inject_cash(self, amount: float):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.add_money(amount)
        self.worker.log("SUCCESS", f"Injected ${amount:,.2f} into Corporate Treasury!")
        self._show_success(f"Added ${amount:,.2f} to Treasury!")

    def _set_exact_cash(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        amt = self.cash_spin.value()
        self.game.set_money(amt)
        self.worker.log("SUCCESS", f"Set Treasury balance directly to ${amt:,.2f}")
        self._show_success(f"Treasury balance updated to ${amt:,.2f}")

    def _add_custom_cash(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        amt = self.cash_spin.value()
        self.game.add_money(amt)
        self.worker.log("SUCCESS", f"Added ${amt:,.2f} to Corporate Treasury")
        self._show_success(f"Added ${amt:,.2f} to Treasury")

    def _clear_bankruptcy(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.clear_bankruptcy()
        self.worker.log("SUCCESS", "Cleared corporate bankruptcy notices, debt strikes, and penalties!")
        self._show_success("Bankruptcy flags cleared successfully!")

    def _add_fans(self, count: int):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.add_fans(count)
        self.worker.log("SUCCESS", f"Added +{count:,} Company Fans!")
        self._show_success(f"Added {count:,} fans!")

    def _apply_rep(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        rep_val = self.rep_slider.value() / 100.0
        self.game.set_business_rep(rep_val)
        self.worker.log("SUCCESS", f"Business reputation set to {rep_val * 100:.0f}%")
        self._show_success(f"Reputation updated to {rep_val * 100:.0f}%")

    def _godmode_founder(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        f = self._founder_data if self._founder_data else self.game.get_founder()
        if not f or not f.get("ptr"):
            self._show_warn("No Founder detected in current company.")
            return
        ptr = f["ptr"]
        self.game.max_employee_needs(ptr)
        self.game.max_employee_skills(ptr)
        self.game.max_employee_specs(ptr)
        self.game.remove_employee_weaknesses(ptr)
        self.game.grant_master_traits(ptr)
        self.worker.log("SUCCESS", f"Applied full Godmode Package to Founder '{f.get('name')}'!")
        self._show_success(f"Founder '{f.get('name')}' is now fully maxed!")

    def _jump_to_founder(self):
        if self._founder_data and self._founder_data.get("name"):
            self.navigateToTalentRequested.emit(self._founder_data.get("name"))
        else:
            self.navigateToTalentRequested.emit("")

    def _show_success(self, msg: str):
        InfoBar.success(
            title="Action Successful",
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2500,
            parent=self.window(),
        )

    def _show_warn(self, msg: str):
        InfoBar.warning(
            title="Warning",
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self.window(),
        )
