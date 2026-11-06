"""
Software Inc. Trainer - Innovation & Patents HQ View
Research laboratory acceleration and patent royalty monopoly management.
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
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
    PushButton,
    PrimaryPushButton,
    ProgressBar,
    TableWidget,
    Slider,
    SpinBox,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
)

from core.memory import get_game_memory


class InnovationView(QScrollArea):
    """
    Innovation & Patents Headquarters managing laboratory breakthroughs and IP royalties.
    """

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.game = get_game_memory()

        self._active_research: List[Dict[str, Any]] = []
        self._patents: List[Dict[str, Any]] = []

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

        # 1. Header Title & Actions
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = TitleLabel("Innovation, R&D & Patent Portfolio", content)
        self.subtitle_lbl = CaptionLabel(
            "Laboratory research acceleration, tech tree breakthroughs, and 2099 patent royalty monopolies.",
            content,
        )
        self.subtitle_lbl.setStyleSheet("color: #A0A0A0;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        top_bar.addLayout(title_box)

        top_bar.addStretch(1)

        # Global Action Buttons
        btn_max_research = PrimaryPushButton(FIF.BRUSH, "Complete All Research (100%)", content)
        btn_max_research.clicked.connect(self._batch_max_research)
        top_bar.addWidget(btn_max_research)

        btn_boost_research = PushButton(FIF.SPEED_HIGH, "10x Research Speed", content)
        btn_boost_research.clicked.connect(self._batch_boost_research_speed)
        top_bar.addWidget(btn_boost_research)

        btn_monopolize_patents = PrimaryPushButton(FIF.HEART, "Monopolize All Patents (50% Royalty, Year 2099)", content)
        btn_monopolize_patents.clicked.connect(self._batch_boost_patents)
        top_bar.addWidget(btn_monopolize_patents)

        layout.addLayout(top_bar)

        # 2. Active Research Section
        self.research_card = HeaderCardWidget(content)
        self.research_card.setTitle("Active Laboratory Research Tasks")
        self.research_layout = QVBoxLayout()
        self.research_card.viewLayout.addLayout(self.research_layout)
        self.research_layout.setContentsMargins(10, 10, 10, 10)
        self.research_layout.setSpacing(12)

        self.no_research_lbl = BodyLabel("No active R&D research tasks currently running in laboratory.", self.research_card)
        self.no_research_lbl.setStyleSheet("color: #7D7D7D; font-style: italic;")
        self.research_layout.addWidget(self.no_research_lbl)

        layout.addWidget(self.research_card)

        # 3. Patent Portfolio Table
        self.patent_card = HeaderCardWidget(content)
        self.patent_card.setTitle("Owned Patent Portfolio & Royalties")
        pat_layout = QVBoxLayout()
        self.patent_card.viewLayout.addLayout(pat_layout)
        pat_layout.setContentsMargins(10, 10, 10, 10)
        pat_layout.setSpacing(12)

        self.table = TableWidget(self.patent_card)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Patent Technology", "Royalty Fee (%)", "Expiration Year", "Quick Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(240)
        pat_layout.addWidget(self.table)

        layout.addWidget(self.patent_card)
        layout.addStretch(1)

    def _connect_signals(self):
        self.worker.research_updated.connect(self._on_research_updated)

    def _on_research_updated(self, active_res: list, patents: list):
        self._active_research = active_res
        self._patents = patents

        # Rebuild Active Research Cards
        while self.research_layout.count() > 0:
            item = self.research_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not active_res:
            self.no_research_lbl = BodyLabel("No active R&D research tasks currently running in laboratory.", self.research_card)
            self.no_research_lbl.setStyleSheet("color: #7D7D7D; font-style: italic;")
            self.research_layout.addWidget(self.no_research_lbl)
        else:
            for r in active_res:
                card = CardWidget(self.research_card)
                c_layout = QVBoxLayout(card)
                c_layout.setContentsMargins(16, 12, 16, 12)
                c_layout.setSpacing(8)

                spec = r.get("specialization", "General Tech")
                year = r.get("year", 1995)
                prog = r.get("progress", 0.0)
                speed = r.get("speed", 1.0)

                hdr = QHBoxLayout()
                lbl = StrongBodyLabel(f"🔬 {spec} (Target Year: {year})", card)
                hdr.addWidget(lbl)
                hdr.addStretch(1)
                spd_lbl = CaptionLabel(f"Speed: {speed:.1f}x", card)
                spd_lbl.setStyleSheet("color: #60CDFF;")
                hdr.addWidget(spd_lbl)
                c_layout.addLayout(hdr)

                p_bar = ProgressBar(card)
                p_bar.setRange(0, 100)
                p_bar.setValue(int(prog * 100))
                p_bar.setFixedHeight(8)
                c_layout.addWidget(p_bar)

                act_row = QHBoxLayout()
                act_row.setSpacing(8)
                btn_finish = PrimaryPushButton(FIF.ACCEPT, "Instant Breakthrough (100%)", card)
                btn_finish.clicked.connect(lambda checked=False, ptr=r.get("ptr"): self._finish_research(ptr))
                act_row.addWidget(btn_finish)

                btn_speed = PushButton(FIF.SPEED_HIGH, "10x Speed", card)
                btn_speed.clicked.connect(lambda checked=False, ptr=r.get("ptr"): self._set_research_speed(ptr, 10.0))
                act_row.addWidget(btn_speed)

                act_row.addStretch(1)
                c_layout.addLayout(act_row)

                self.research_layout.addWidget(card)

        # Populate Patent Table
        self.table.blockSignals(True)
        self.table.setRowCount(len(patents))
        for row, pat in enumerate(patents):
            name = pat.get("name", "Patent IP")
            royalty = f"{pat.get('royalty', 0.1) * 100:.0f}%"
            outdates = str(pat.get("outdates", 2000))

            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(royalty))
            self.table.setItem(row, 2, QTableWidgetItem(outdates))

            # Quick button on row
            ptr = pat.get("ptr")
            btn = PushButton(FIF.ACCEPT, "Set 50% & Year 2099", self.table)
            btn.clicked.connect(lambda checked=False, p=ptr: self._boost_single_patent(p))
            self.table.setCellWidget(row, 3, btn)

        self.table.blockSignals(False)

    def _finish_research(self, ptr):
        if ptr and self.game.is_attached():
            self.game.max_research_task(ptr)
            self.worker.log("SUCCESS", "Achieved instant research breakthrough (100% completed)!")
            self._show_success("Research breakthrough unlocked!")
            self.worker.request_immediate_refresh()

    def _set_research_speed(self, ptr, speed: float):
        if ptr and self.game.is_attached():
            self.game.set_research_speed(ptr, speed)
            self.worker.log("SUCCESS", f"Boosted research task speed to {speed:.1f}x!")
            self._show_success(f"Speed boosted to {speed:.1f}x")
            self.worker.request_immediate_refresh()

    def _boost_single_patent(self, ptr):
        if ptr and self.game.is_attached():
            self.game.modify_patent(ptr, royalty=0.50, outdates=2099)
            self.worker.log("SUCCESS", "Boosted patent: Set royalties to 50% and expiration extended to 2099!")
            self._show_success("Patent monopolized to 50% royalties through Year 2099!")
            self.worker.request_immediate_refresh()

    def _batch_max_research(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.max_all_active_research()
        self.worker.log("SUCCESS", f"Completed breakthroughs for {cnt} active research tasks!")
        self._show_success(f"Unlocked breakthroughs for {cnt} research projects!")
        self.worker.request_immediate_refresh()

    def _batch_boost_research_speed(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.boost_all_active_research(multiplier=10.0)
        self.worker.log("SUCCESS", f"Boosted research speed to 10.0x for {cnt} active laboratory tasks!")
        self._show_success(f"Boosted speed to 10.0x for {cnt} tasks!")
        self.worker.request_immediate_refresh()

    def _batch_boost_patents(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.boost_all_patents(royalty=0.50, outdates=2099)
        self.worker.log("SUCCESS", f"Monopolized {cnt} patents: Set royalties to 50% and extended expiration to Year 2099!")
        self._show_success(f"Monopolized {cnt} patents through Year 2099!")
        self.worker.request_immediate_refresh()

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
