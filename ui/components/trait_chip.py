"""
Software Inc. Trainer - Trait Chip Component
Renders an interactive tag chip for positive perks and negative weaknesses.
"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Signal


class TraitChip(QPushButton):
    """
    Fluent tag chip for traits with distinct styling for perks and weaknesses.
    Emits toggledTrait(name, active) when clicked.
    """

    traitToggled = Signal(str, bool)

    def __init__(self, name: str, mask: int, is_weakness: bool = False, active: bool = False, parent=None):
        super().__init__(parent)
        self.trait_name = name
        self.trait_mask = mask
        self.is_weakness = is_weakness
        self.is_active = active

        self.setText(f"{'⚠️ ' if is_weakness else '⚡ '}{name}")
        self.setCheckable(True)
        self.setChecked(active)
        self._update_style()

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        self.is_active = self.isChecked()
        self._update_style()
        self.traitToggled.emit(self.trait_name, self.is_active)

    def set_active(self, active: bool):
        self.is_active = active
        self.setChecked(active)
        self._update_style()

    def _update_style(self):
        if self.is_weakness:
            if self.is_active:
                # Active Weakness (Red / Warning)
                self.setStyleSheet("""
                    QPushButton {
                        background-color: #5C1518;
                        color: #FFB3B8;
                        border: 1px solid #C42B1C;
                        border-radius: 12px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #7A1C20;
                    }
                """)
            else:
                # Inactive Weakness
                self.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.04);
                        color: #7D7D7D;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 12px;
                        padding: 4px 10px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #B0B0B0;
                    }
                """)
        else:
            if self.is_active:
                # Active Perk (Teal / Blue / Success)
                self.setStyleSheet("""
                    QPushButton {
                        background-color: #0F4C81;
                        color: #BBE1FA;
                        border: 1px solid #0078D4;
                        border-radius: 12px;
                        padding: 4px 10px;
                        font-size: 11px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: #155B99;
                    }
                """)
            else:
                # Inactive Perk
                self.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(255, 255, 255, 0.04);
                        color: #7D7D7D;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 12px;
                        padding: 4px 10px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.08);
                        color: #B0B0B0;
                    }
                """)
