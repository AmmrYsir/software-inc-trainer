"""
Software Inc. Trainer - Projects & Software Pipeline View
Kanban progress tracking for Design, Alpha, Beta stages, and Released Products.
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
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
)

from core.memory import get_game_memory


class ProjectCard(CardWidget):
    """
    Renders an active software project card with dual progress bars and 1-click stage actions.
    """

    def __init__(self, proj: dict, game, worker, parent=None):
        super().__init__(parent)
        self.proj = proj
        self.game = game
        self.worker = worker

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header: Name + Phase Badge
        header = QHBoxLayout()
        header.setSpacing(8)

        name = self.proj.get("name", "Untitled Software")
        p_type = self.proj.get("type", "Alpha")

        name_lbl = StrongBodyLabel(name, self)
        header.addWidget(name_lbl)

        badge_color = "#0078D4" if p_type == "Alpha" else ("#107C41" if p_type == "Design" else "#D88B00")
        badge = QLabel(p_type.upper(), self)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {badge_color};
                color: #FFFFFF;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)
        header.addWidget(badge)
        header.addStretch(1)

        followers = self.proj.get("followers", 0)
        followers_lbl = CaptionLabel(f"⭐ {followers:,} Fans", self)
        followers_lbl.setStyleSheet("color: #60CDFF;")
        header.addWidget(followers_lbl)
        layout.addLayout(header)

        # Progress Bars
        if p_type == "Design":
            iter_num = self.proj.get("iteration", 1)
            prog = self.proj.get("progress", 0.0)
            iter_lbl = CaptionLabel(f"Design Iteration: {iter_num}/3 ({int(prog * 100)}%)", self)
            layout.addWidget(iter_lbl)

            bar = ProgressBar(self)
            bar.setRange(0, 100)
            bar.setValue(int(prog * 100))
            bar.setFixedHeight(8)
            layout.addWidget(bar)
        else:
            # Alpha / Beta (Code & Art)
            code_prog = self.proj.get("code_progress", 0.0)
            art_prog = self.proj.get("art_progress", 0.0)
            bugs = self.proj.get("bugs", 0)

            prog_lbl = CaptionLabel(f"Code: {int(code_prog * 100)}% | Art: {int(art_prog * 100)}% | 🐛 Bugs: {bugs}", self)
            layout.addWidget(prog_lbl)

            # Code Progress Bar
            code_bar = ProgressBar(self)
            code_bar.setRange(0, 100)
            code_bar.setValue(int(code_prog * 100))
            code_bar.setFixedHeight(6)
            code_bar.setCustomBarColor("#0078D4", "#0078D4")
            layout.addWidget(code_bar)

            # Art Progress Bar
            art_bar = ProgressBar(self)
            art_bar.setRange(0, 100)
            art_bar.setValue(int(art_prog * 100))
            art_bar.setFixedHeight(6)
            art_bar.setCustomBarColor("#D88B00", "#D88B00")
            layout.addWidget(art_bar)

        # Action Buttons Row
        actions = QHBoxLayout()
        actions.setSpacing(6)

        if p_type == "Design":
            btn_max = PrimaryPushButton(FIF.ACCEPT, "Max Design", self)
            btn_max.clicked.connect(self._max_design)
            actions.addWidget(btn_max)
        else:
            btn_max = PrimaryPushButton(FIF.BRUSH, "100% Code & Art", self)
            btn_max.clicked.connect(self._max_dev)
            actions.addWidget(btn_max)

            btn_zero_bugs = PushButton(FIF.ACCEPT, "Zero Bugs", self)
            btn_zero_bugs.clicked.connect(self._clear_bugs)
            actions.addWidget(btn_zero_bugs)

            if p_type == "Alpha":
                btn_beta = PushButton(FIF.RIGHT_ARROW, "Promote to Beta", self)
                btn_beta.clicked.connect(self._promote_beta)
                actions.addWidget(btn_beta)
            elif p_type == "Beta":
                btn_release = PushButton(FIF.SEND, "Ready for Release", self)
                btn_release.clicked.connect(self._ready_release)
                actions.addWidget(btn_release)

        btn_fans = PushButton(FIF.PEOPLE, "+10k Fans", self)
        btn_fans.clicked.connect(self._add_fans)
        actions.addWidget(btn_fans)

        actions.addStretch(1)
        layout.addLayout(actions)

    def _max_design(self):
        ptr = self.proj.get("ptr")
        if ptr and self.game.is_attached():
            self.game.max_design_project(ptr)
            self.worker.log("SUCCESS", f"Maxed design for '{self.proj.get('name')}' (Iter 3, 100%)")
            self.worker.request_immediate_refresh()

    def _max_dev(self):
        ptr = self.proj.get("ptr")
        if ptr and self.game.is_attached():
            self.game.max_dev_project(ptr)
            self.worker.log("SUCCESS", f"Set 100% Code & Art for '{self.proj.get('name')}'")
            self.worker.request_immediate_refresh()

    def _clear_bugs(self):
        ptr = self.proj.get("ptr")
        if ptr and self.game.is_attached():
            self.game.clear_project_bugs(ptr)
            self.worker.log("SUCCESS", f"Cleared all active bugs for '{self.proj.get('name')}'")
            self.worker.request_immediate_refresh()

    def _promote_beta(self):
        ptr = self.proj.get("ptr")
        if ptr and self.game.is_attached():
            self.game.promote_project_to_beta(ptr)
            self.worker.log("SUCCESS", f"Promoted '{self.proj.get('name')}' to Beta stage!")
            self.worker.request_immediate_refresh()

    def _ready_release(self):
        ptr = self.proj.get("ptr")
        if ptr and self.game.is_attached():
            self.game.ready_project_for_release(ptr)
            self.worker.log("SUCCESS", f"Prepped '{self.proj.get('name')}' for immediate Release (0 bugs, 100% Quality)!")
            self.worker.request_immediate_refresh()

    def _add_fans(self):
        ptr = self.proj.get("ptr")
        if ptr and self.game.is_attached():
            cur = self.proj.get("followers", 0)
            self.game.set_project_followers(ptr, cur + 10000)
            self.worker.log("SUCCESS", f"Added +10,000 Fans / Followers to '{self.proj.get('name')}'")
            self.worker.request_immediate_refresh()


class ProjectsView(QScrollArea):
    """
    Software Pipeline view managing ongoing developments and live catalog products.
    """

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.game = get_game_memory()

        self._active_projects: List[Dict[str, Any]] = []
        self._released_products: List[Dict[str, Any]] = []

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

        # 1. Header & Batch Actions
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = TitleLabel("Software & Project Pipeline", content)
        self.subtitle_lbl = CaptionLabel(
            "Visual tracking and stage acceleration for Design, Alpha, Beta, and Released software catalog.",
            content,
        )
        self.subtitle_lbl.setStyleSheet("color: #A0A0A0;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        top_bar.addLayout(title_box)

        top_bar.addStretch(1)

        # Global Batch Accelerators
        btn_max_all_dev = PrimaryPushButton(FIF.BRUSH, "100% All Code & Art", content)
        btn_max_all_dev.clicked.connect(self._batch_max_devs)
        top_bar.addWidget(btn_max_all_dev)

        btn_clear_all_bugs = PushButton(FIF.ACCEPT, "Zero All Bugs", content)
        btn_clear_all_bugs.clicked.connect(self._batch_clear_bugs)
        top_bar.addWidget(btn_clear_all_bugs)

        btn_max_designs = PushButton(FIF.ACCEPT, "Max All Designs", content)
        btn_max_designs.clicked.connect(self._batch_max_designs)
        top_bar.addWidget(btn_max_designs)

        layout.addLayout(top_bar)

        # 2. Active Projects Section
        self.active_card = HeaderCardWidget(content)
        self.active_card.setTitle("Active Projects in Development")
        self.active_layout = QVBoxLayout()
        self.active_card.viewLayout.addLayout(self.active_layout)
        self.active_layout.setContentsMargins(10, 10, 10, 10)
        self.active_layout.setSpacing(12)

        self.no_projects_lbl = BodyLabel("No active software projects detected in production.", self.active_card)
        self.no_projects_lbl.setStyleSheet("color: #7D7D7D; font-style: italic;")
        self.active_layout.addWidget(self.no_projects_lbl)

        layout.addWidget(self.active_card)

        # 3. Released Products Catalog Table
        self.released_card = HeaderCardWidget(content)
        self.released_card.setTitle("Released Software Catalog & Marketed IP")
        rel_layout = QVBoxLayout()
        self.released_card.viewLayout.addLayout(rel_layout)
        rel_layout.setContentsMargins(10, 10, 10, 10)
        rel_layout.setSpacing(10)

        self.table = TableWidget(self.released_card)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Software Title", "Quality", "Awareness", "Active Users", "Fans / Hype", "Price", "Bugs"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setMinimumHeight(240)
        rel_layout.addWidget(self.table)

        # Catalog Batch Buttons
        cat_btn_row = QHBoxLayout()
        cat_btn_row.setSpacing(8)
        btn_boost_catalog = PrimaryPushButton(FIF.HEART, "Boost All Catalog Quality (100% Quality, 100% Awareness)", self.released_card)
        btn_boost_catalog.clicked.connect(self._boost_all_catalog)
        cat_btn_row.addWidget(btn_boost_catalog)
        cat_btn_row.addStretch(1)
        rel_layout.addLayout(cat_btn_row)

        layout.addWidget(self.released_card)
        layout.addStretch(1)

    def _connect_signals(self):
        self.worker.projects_updated.connect(self._on_projects_updated)

    def _on_projects_updated(self, active_projs: list, released_prods: list):
        self._active_projects = active_projs
        self._released_products = released_prods

        # Rebuild Active Project Cards
        # Clear existing card widgets
        while self.active_layout.count() > 0:
            item = self.active_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not active_projs:
            self.no_projects_lbl = BodyLabel("No active software projects detected in production.", self.active_card)
            self.no_projects_lbl.setStyleSheet("color: #7D7D7D; font-style: italic;")
            self.active_layout.addWidget(self.no_projects_lbl)
        else:
            for p in active_projs:
                card = ProjectCard(p, self.game, self.worker, self.active_card)
                self.active_layout.addWidget(card)

        # Populate Released Products Table
        self.table.blockSignals(True)
        self.table.setRowCount(len(released_prods))
        for row, prod in enumerate(released_prods):
            name = prod.get("name", "Unknown")
            qual = f"{prod.get('quality', 1.0) * 100:.1f}%"
            aware = f"{prod.get('awareness', 1.0) * 100:.1f}%"
            users = f"{prod.get('userbase', 0):,}"
            fans = f"{prod.get('followers', 0):,}"
            price = f"${prod.get('price', 0.0):.2f}"
            bugs = str(prod.get("bugs", 0))

            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(qual))
            self.table.setItem(row, 2, QTableWidgetItem(aware))
            self.table.setItem(row, 3, QTableWidgetItem(users))
            self.table.setItem(row, 4, QTableWidgetItem(fans))
            self.table.setItem(row, 5, QTableWidgetItem(price))
            self.table.setItem(row, 6, QTableWidgetItem(bugs))
        self.table.blockSignals(False)

    def _batch_max_devs(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.max_all_active_devs()
        self.worker.log("SUCCESS", f"Elevated Code & Art to 100% for all {cnt} development projects!")
        self._show_success(f"Maxed Code & Art for {cnt} projects!")
        self.worker.request_immediate_refresh()

    def _batch_clear_bugs(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.clear_all_projects_bugs()
        self.worker.log("SUCCESS", f"Cleared all active bugs to 0 across {cnt} development projects!")
        self._show_success(f"Cleared bugs for {cnt} projects!")
        self.worker.request_immediate_refresh()

    def _batch_max_designs(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.max_all_active_designs()
        self.worker.log("SUCCESS", f"Maxed out design iteration and progress across {cnt} design projects!")
        self._show_success(f"Maxed {cnt} design projects (Ready for Dev)!")
        self.worker.request_immediate_refresh()

    def _boost_all_catalog(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = 0
        for p in self._released_products:
            ptr = p.get("ptr")
            if ptr:
                self.game.modify_released_product(ptr, quality=1.0, awareness=1.0, bugs=0)
                cnt += 1
        self.worker.log("SUCCESS", f"Boosted catalog: Set 100% Quality & 100% Awareness for {cnt} released products!")
        self._show_success(f"Boosted {cnt} released software titles!")
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
