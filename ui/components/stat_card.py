"""
Software Inc. Trainer - Metric & Stat Card Component
Renders Windows 11 Fluent elevated cards with iconography, large KPI values, and sub-labels.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from qfluentwidgets import CardWidget, TitleLabel, BodyLabel, CaptionLabel, IconWidget, FluentIconBase


class StatCard(CardWidget):
    """
    Standardized Fluent Stat Card with title, large formatted value,
    and contextual subtitle.
    """

    def __init__(self, title: str, initial_value: str = "--", subtitle: str = "", icon: FluentIconBase = None, parent=None):
        super().__init__(parent)
        self.title_text = title
        self.icon_obj = icon

        self._init_ui(subtitle, initial_value)

    def _init_ui(self, subtitle: str, initial_value: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        # Header row: Title + Optional Icon
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        if self.icon_obj:
            self.icon_widget = IconWidget(self.icon_obj, self)
            self.icon_widget.setFixedSize(16, 16)
            header_layout.addWidget(self.icon_widget)

        self.title_label = CaptionLabel(self.title_text, self)
        self.title_label.setStyleSheet("color: #A0A0A0; font-weight: 500;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        # Large KPI Value
        self.value_label = TitleLabel(initial_value, self)
        self.value_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self.value_label)

        # Subtitle / Hint
        self.subtitle_label = CaptionLabel(subtitle, self)
        self.subtitle_label.setStyleSheet("color: #7D7D7D;")
        layout.addWidget(self.subtitle_label)

    def set_value(self, val: str):
        self.value_label.setText(val)

    def set_subtitle(self, sub: str):
        self.subtitle_label.setText(sub)
