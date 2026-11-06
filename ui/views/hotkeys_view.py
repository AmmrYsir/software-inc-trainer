"""
Software Inc. Trainer - Hotkeys & Live Activity Log View
Global in-game shortcuts reference and audit log of all applied memory mutations.
"""

from typing import List, Tuple
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QFrame,
    QLabel,
    QHeaderView,
    QTableWidgetItem,
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
    TableWidget,
    PushButton,
    PrimaryPushButton,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
)

from core.constants import HOTKEY_DEFINITIONS


class HotkeysView(QScrollArea):
    """
    Keybind monitor and live telemetry/audit log viewer.
    """

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self._log_entries: List[Tuple[str, str, str]] = []

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
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = TitleLabel("Global Hotkeys & Live Audit Log", content)
        self.subtitle_lbl = CaptionLabel(
            "Hardware-level global shortcuts (Numpad 1-9) and audit trail for memory mutations and background telemetry.",
            content,
        )
        self.subtitle_lbl.setStyleSheet("color: #A0A0A0;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        layout.addLayout(title_box)

        # 2. Keybinds Card
        keys_card = HeaderCardWidget(content)
        keys_card.setTitle("In-Game Global Keybinds (Numpad 1-9)")
        keys_layout = QVBoxLayout()
        keys_card.viewLayout.addLayout(keys_layout)
        keys_layout.setContentsMargins(10, 10, 10, 10)
        keys_layout.setSpacing(10)

        keys_table = TableWidget(keys_card)
        keys_table.setColumnCount(3)
        keys_table.setHorizontalHeaderLabels(["Shortcut Key", "Action Description", "System Status"])
        keys_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        keys_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        keys_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        keys_table.setRowCount(len(HOTKEY_DEFINITIONS))

        for row, (k_name, desc, _) in enumerate(HOTKEY_DEFINITIONS):
            keys_table.setItem(row, 0, QTableWidgetItem(f"⌨️ {k_name}"))
            keys_table.setItem(row, 1, QTableWidgetItem(desc))
            status_item = QTableWidgetItem("Active")
            status_item.setForeground(Qt.green)
            keys_table.setItem(row, 2, status_item)

        keys_table.setFixedHeight(270)
        keys_layout.addWidget(keys_table)
        layout.addWidget(keys_card)

        # 3. Live Event Log Card
        log_card = HeaderCardWidget(content)
        log_card.setTitle("Trainer Activity & Memory Event Log")
        log_layout = QVBoxLayout()
        log_card.viewLayout.addLayout(log_layout)
        log_layout.setContentsMargins(10, 10, 10, 10)
        log_layout.setSpacing(12)

        # Log Table
        self.log_table = TableWidget(log_card)
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Time", "Severity", "Event Details"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.log_table.setMinimumHeight(240)
        log_layout.addWidget(self.log_table)

        # Log Actions Bar
        act_row = QHBoxLayout()
        act_row.setSpacing(10)

        btn_clear = PushButton(FIF.DELETE, "Clear Activity Log", log_card)
        btn_clear.clicked.connect(self._clear_log)
        act_row.addWidget(btn_clear)

        act_row.addStretch(1)
        log_layout.addLayout(act_row)

        layout.addWidget(log_card)
        layout.addStretch(1)

    def _connect_signals(self):
        self.worker.activity_logged.connect(self._on_activity_logged)

    def _on_activity_logged(self, timestamp: str, level: str, message: str):
        self._log_entries.append((timestamp, level, message))

        # Insert into log table at row 0 (most recent first)
        self.log_table.blockSignals(True)
        self.log_table.insertRow(0)

        time_item = QTableWidgetItem(timestamp)
        level_item = QTableWidgetItem(level)
        msg_item = QTableWidgetItem(message)

        if level == "SUCCESS":
            level_item.setForeground(Qt.green)
        elif level == "WARN":
            level_item.setForeground(Qt.yellow)
        elif level == "ERROR":
            level_item.setForeground(Qt.red)
        else:
            level_item.setForeground(Qt.cyan)

        self.log_table.setItem(0, 0, time_item)
        self.log_table.setItem(0, 1, level_item)
        self.log_table.setItem(0, 2, msg_item)

        # Limit table to 100 entries
        if self.log_table.rowCount() > 100:
            self.log_table.removeRow(100)

        self.log_table.blockSignals(False)

    def _clear_log(self):
        self._log_entries.clear()
        self.log_table.setRowCount(0)
        InfoBar.info(
            title="Log Cleared",
            content="Activity audit log has been cleared.",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self.window(),
        )
