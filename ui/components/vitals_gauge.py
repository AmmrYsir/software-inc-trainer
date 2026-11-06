"""
Software Inc. Trainer - Vitals Gauge Component
Displays an interactive progress bar for an employee need with dynamic color thresholds.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import ProgressBar, ToolButton, FluentIcon as FIF, CaptionLabel, BodyLabel


class VitalsGauge(QWidget):
    """
    Renders a vital gauge with a label, percentage display, color-coded bar,
    and an optional 1-click restore button.
    """

    valueChanged = Signal(float)  # Emits new target value (0.0 - 1.0)

    def __init__(self, name: str, value: float = 1.0, is_stress: bool = False, parent=None):
        super().__init__(parent)
        self.name = name
        self.value = max(0.0, min(1.0, value))
        self.is_stress = is_stress

        self._init_ui()
        self.set_value(self.value)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # Label
        self.name_label = BodyLabel(self.name, self)
        self.name_label.setFixedWidth(80)
        layout.addWidget(self.name_label)

        # Progress bar
        self.bar = ProgressBar(self)
        self.bar.setRange(0, 100)
        self.bar.setFixedHeight(8)
        layout.addWidget(self.bar, stretch=1)

        # Percentage label
        self.percent_label = CaptionLabel("100%", self)
        self.percent_label.setFixedWidth(45)
        self.percent_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.percent_label)

        # Quick Max/Zero button
        self.quick_btn = ToolButton(FIF.ACCEPT if not self.is_stress else FIF.CLOSE, self)
        self.quick_btn.setFixedSize(26, 26)
        self.quick_btn.setToolTip("Restore to 100%" if not self.is_stress else "Reduce Stress to 0%")
        self.quick_btn.clicked.connect(self._on_quick_clicked)
        layout.addWidget(self.quick_btn)

    def _on_quick_clicked(self):
        target = 0.0 if self.is_stress else 1.0
        self.set_value(target)
        self.valueChanged.emit(target)

    def set_value(self, val: float):
        self.value = max(0.0, min(1.0, val))
        pct = int(self.value * 100)
        self.bar.setValue(pct)
        self.percent_label.setText(f"{pct}%")

        # Color cues based on stress or normal vitals
        if self.is_stress:
            # Low stress is good (green), high stress is bad (red)
            if pct <= 30:
                color = "#107C41"  # Fluent green
            elif pct <= 65:
                color = "#D88B00"  # Amber
            else:
                color = "#C42B1C"  # Red
        else:
            # High vital is good (green), low vital is bad (red)
            if pct >= 70:
                color = "#107C41"
            elif pct >= 35:
                color = "#D88B00"
            else:
                color = "#C42B1C"

        self.bar.setCustomBarColor(color, color)
