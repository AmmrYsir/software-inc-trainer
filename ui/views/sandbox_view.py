"""
Software Inc. Trainer - Sandbox & World Rules View
World modifiers, furniture catalog unlock, environmental shaders, and simulation speed dilation.
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
from PySide6.QtCore import Qt
from qfluentwidgets import (
    CardWidget,
    ElevatedCardWidget,
    HeaderCardWidget,
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    SwitchButton,
    Slider,
    PushButton,
    PrimaryPushButton,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
)

from core.memory import get_game_memory
from core.constants import SPEED_PRESETS


class SandboxView(QScrollArea):
    """
    World Rules & Game Engine Sandbox modifiers.
    """

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.game = get_game_memory()

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background-color: transparent;")

        self._init_ui()

    def _init_ui(self):
        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 20, 28, 28)
        layout.setSpacing(20)

        # 1. Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = TitleLabel("Sandbox, World Rules & Visual Shaders", content)
        self.subtitle_lbl = CaptionLabel(
            "Hardware catalog unlocking, day/night lighting bypass, atmospheric shaders, and simulation time dilation.",
            content,
        )
        self.subtitle_lbl.setStyleSheet("color: #A0A0A0;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        layout.addLayout(title_box)

        # 2. Simulation Speed & Time Dilation Card
        speed_card = HeaderCardWidget(content)
        speed_card.setTitle("Simulation Engine Speed & Time Dilation")
        spd_layout = QVBoxLayout()
        speed_card.viewLayout.addLayout(spd_layout)
        spd_layout.setContentsMargins(10, 10, 10, 10)
        spd_layout.setSpacing(14)

        # Preset Buttons Row
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_lbl = StrongBodyLabel("Speed Presets:", speed_card)
        preset_row.addWidget(preset_lbl)

        for label, val in SPEED_PRESETS:
            btn = PushButton(FIF.SPEED_HIGH, label, speed_card)
            btn.clicked.connect(lambda checked=False, s=val: self._set_speed(s))
            preset_row.addWidget(btn)

        preset_row.addStretch(1)
        spd_layout.addLayout(preset_row)

        # Custom Slider Row
        slider_row = QHBoxLayout()
        slider_row.setSpacing(12)
        slider_lbl = BodyLabel("Engine Speed Multiplier:", speed_card)
        slider_row.addWidget(slider_lbl)

        self.speed_slider = Slider(Qt.Horizontal, speed_card)
        self.speed_slider.setRange(1, 100)  # 0.1x to 10.0x
        self.speed_slider.setValue(10)      # 1.0x
        self.speed_slider.setFixedWidth(240)
        slider_row.addWidget(self.speed_slider)

        self.speed_val_lbl = StrongBodyLabel("1.0x", speed_card)
        self.speed_val_lbl.setFixedWidth(50)
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        slider_row.addWidget(self.speed_val_lbl)

        apply_spd_btn = PrimaryPushButton(FIF.SAVE, "Apply Speed", speed_card)
        apply_spd_btn.clicked.connect(lambda: self._set_speed(self.speed_slider.value() / 10.0))
        slider_row.addWidget(apply_spd_btn)

        slider_row.addStretch(1)
        spd_layout.addLayout(slider_row)

        layout.addWidget(speed_card)

        # 3. Environment & World Rules Card
        rules_card = HeaderCardWidget(content)
        rules_card.setTitle("World Engine & Environmental Cheats")
        rules_layout = QVBoxLayout()
        rules_card.viewLayout.addLayout(rules_layout)
        rules_layout.setContentsMargins(10, 10, 10, 10)
        rules_layout.setSpacing(16)

        # Furniture Unlock Toggle
        furn_row = QHBoxLayout()
        furn_row.setSpacing(12)
        furn_info = QVBoxLayout()
        furn_info.addWidget(StrongBodyLabel("Unlock All Furniture & Hardware Catalog", rules_card))
        furn_sub = CaptionLabel("Bypasses year progression and tech-tree requirements to unlock all office equipment immediately.", rules_card)
        furn_sub.setStyleSheet("color: #A0A0A0;")
        furn_info.addWidget(furn_sub)
        furn_row.addLayout(furn_info, stretch=1)

        self.furn_switch = SwitchButton(rules_card)
        self.furn_switch.checkedChanged.connect(self._on_furniture_toggled)
        furn_row.addWidget(self.furn_switch)
        rules_layout.addLayout(furn_row)

        div1 = QFrame(rules_card)
        div1.setFrameShape(QFrame.HLine)
        div1.setStyleSheet("color: rgba(255, 255, 255, 0.08);")
        rules_layout.addWidget(div1)

        # Force Lights Toggle
        lights_row = QHBoxLayout()
        lights_row.setSpacing(12)
        lights_info = QVBoxLayout()
        lights_info.addWidget(StrongBodyLabel("Force All Building Lights Always ON", rules_card))
        lights_sub = CaptionLabel("Keeps office lighting fully active 24/7 regardless of working hours, power states, or room occupancy.", rules_card)
        lights_sub.setStyleSheet("color: #A0A0A0;")
        lights_info.addWidget(lights_sub)
        lights_row.addLayout(lights_info, stretch=1)

        self.lights_switch = SwitchButton(rules_card)
        self.lights_switch.checkedChanged.connect(self._on_lights_toggled)
        lights_row.addWidget(self.lights_switch)
        rules_layout.addLayout(lights_row)

        div2 = QFrame(rules_card)
        div2.setFrameShape(QFrame.HLine)
        div2.setStyleSheet("color: rgba(255, 255, 255, 0.08);")
        rules_layout.addWidget(div2)

        # Darkness Shader Disable
        dark_row = QHBoxLayout()
        dark_row.setSpacing(12)
        dark_info = QVBoxLayout()
        dark_info.addWidget(StrongBodyLabel("Disable Night Darkness Shader", rules_card))
        dark_sub = CaptionLabel("Disables the screen-space night darkening shader for pristine visibility around the clock.", rules_card)
        dark_sub.setStyleSheet("color: #A0A0A0;")
        dark_info.addWidget(dark_sub)
        dark_row.addLayout(dark_info, stretch=1)

        self.dark_switch = SwitchButton(rules_card)
        self.dark_switch.checkedChanged.connect(self._on_darkness_toggled)
        dark_row.addWidget(self.dark_switch)
        rules_layout.addLayout(dark_row)

        div3 = QFrame(rules_card)
        div3.setFrameShape(QFrame.HLine)
        div3.setStyleSheet("color: rgba(255, 255, 255, 0.08);")
        rules_layout.addWidget(div3)

        # Infinite Subsidiaries Toggle
        sub_row = QHBoxLayout()
        sub_row.setSpacing(12)
        sub_info = QVBoxLayout()
        sub_info.addWidget(StrongBodyLabel("Infinite Corporate Subsidiaries", rules_card))
        sub_sub = CaptionLabel("Bypasses subsidiary acquisition caps and legal limits, allowing unlimited enterprise acquisitions.", rules_card)
        sub_sub.setStyleSheet("color: #A0A0A0;")
        sub_info.addWidget(sub_sub)
        sub_row.addLayout(sub_info, stretch=1)

        self.sub_switch = SwitchButton(rules_card)
        self.sub_switch.checkedChanged.connect(self._on_subsidiaries_toggled)
        sub_row.addWidget(self.sub_switch)
        rules_layout.addLayout(sub_row)

        layout.addWidget(rules_card)
        layout.addStretch(1)

    def _on_speed_slider_changed(self, val: int):
        speed = val / 10.0
        self.speed_val_lbl.setText(f"{speed:.1f}x")

    def _set_speed(self, speed: float):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.set_game_speed(speed)
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(int(speed * 10))
        self.speed_val_lbl.setText(f"{speed:.1f}x")
        self.speed_slider.blockSignals(False)
        self.worker.log("SUCCESS", f"Set game simulation speed to {speed:.1f}x")
        self._show_success(f"Simulation speed set to {speed:.1f}x")

    def _on_furniture_toggled(self, active: bool):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.unlock_furniture(active)
        self.worker.log("SUCCESS", f"Furniture & equipment catalog unlock set to {active}")
        self._show_success(f"Furniture unlock {'enabled' if active else 'disabled'}")

    def _on_lights_toggled(self, active: bool):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.force_lights(active)
        self.worker.log("SUCCESS", f"Force lights always ON set to {active}")
        self._show_success(f"Force lights {'enabled' if active else 'disabled'}")

    def _on_darkness_toggled(self, active: bool):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.disable_darkness(active)
        self.worker.log("SUCCESS", f"Night darkness shader bypass set to {active}")
        self._show_success(f"Darkness shader bypass {'enabled' if active else 'disabled'}")

    def _on_subsidiaries_toggled(self, active: bool):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        self.game.infinite_subsidiaries(active)
        self.worker.log("SUCCESS", f"Infinite corporate subsidiaries limit set to {active}")
        self._show_success(f"Infinite subsidiaries {'enabled' if active else 'disabled'}")

    def _show_success(self, msg: str):
        InfoBar.success(
            title="Success",
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
