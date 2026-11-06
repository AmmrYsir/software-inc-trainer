"""
Software Inc. Trainer - Fluent Star Rating Widget
Modern rating selector for Employee Specializations and Skills (0 to 3 stars).
Replaces the cramped 100-button stack from the legacy trainer with clean, responsive controls.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import BodyLabel, CaptionLabel, ToolButton, FluentIcon as FIF


class StarRatingWidget(QWidget):
    """
    Compact 0-3 star rating selector.
    Emits levelChanged(int) when the user clicks 0, 1, 2, or 3.
    """

    levelChanged = Signal(int)

    def __init__(self, title: str, level: int = 0, max_stars: int = 3, parent=None):
        super().__init__(parent)
        self.title = title
        self.level = max(0, min(max_stars, level))
        self.max_stars = max_stars
        self.star_buttons = []

        self._init_ui()
        self.set_level(self.level)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        # Title / Subfield label
        self.label = BodyLabel(self.title, self)
        self.label.setMinimumWidth(90)
        layout.addWidget(self.label, stretch=1)

        # Reset / 0-Star Button
        self.btn_zero = QPushButton("0★", self)
        self.btn_zero.setFixedSize(28, 24)
        self.btn_zero.setToolTip("Set to 0 Stars (Unspecialized)")
        self.btn_zero.clicked.connect(lambda: self._select_level(0))
        self._apply_btn_style(self.btn_zero, is_active=False)
        layout.addWidget(self.btn_zero)

        # Star buttons (1, 2, 3)
        for i in range(1, self.max_stars + 1):
            btn = QPushButton(f"★{i}", self)
            btn.setFixedSize(32, 24)
            btn.setToolTip(f"Set to {i} Star{'s' if i > 1 else ''}")
            btn.clicked.connect(lambda checked=False, lvl=i: self._select_level(lvl))
            self.star_buttons.append(btn)
            layout.addWidget(btn)

    def _select_level(self, lvl: int):
        self.set_level(lvl)
        self.levelChanged.emit(lvl)

    def set_level(self, lvl: int):
        self.level = max(0, min(self.max_stars, lvl))

        # Update 0-star button style
        self._apply_btn_style(self.btn_zero, is_active=(self.level == 0))

        # Update star buttons
        for i, btn in enumerate(self.star_buttons, start=1):
            is_active = (i <= self.level)
            self._apply_btn_style(btn, is_active=is_active)

    def _apply_btn_style(self, btn: QPushButton, is_active: bool):
        if is_active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 11px;
                    border: 1px solid #005A9E;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1084D9;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #A0A0A0;
                    font-size: 11px;
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.15);
                    color: #FFFFFF;
                }
            """)
