"""
Software Inc. Trainer - Main Window
Hardware-accelerated Windows 11 Fluent interface (WinUI 3) hosting the persistent HUD ribbon and navigation views.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QColor
from qfluentwidgets import (
    MSFluentWindow,
    NavigationItemPosition,
    FluentIcon as FIF,
    setTheme,
    Theme,
    InfoBar,
    InfoBarPosition,
)

from .components.header_ribbon import HeaderRibbon
from .views.dashboard_view import DashboardView
from .views.talent_view import TalentView
from .views.projects_view import ProjectsView
from .views.innovation_view import InnovationView
from .views.sandbox_view import SandboxView
from .views.hotkeys_view import HotkeysView
from core.worker import TelemetryWorker
from core.memory import get_game_memory


class MainWindow(MSFluentWindow):
    """
    Main Application Window with WinUI 3 Fluent styling, Mica/Acrylic effects,
    persistent HUD ribbon, and responsive navigation views.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Software Inc. - Executive Studio Command Center")
        self.resize(1280, 820)
        self.setMinimumSize(1040, 680)

        # Enforce Windows 11 Dark Mode by default
        setTheme(Theme.DARK)

        # Initialize Memory Engine & Background Worker
        self.game = get_game_memory()
        self.worker = TelemetryWorker()

        self._init_layout_and_views()
        self._wire_signals()

        # Start background worker
        self.worker.start()

    def _init_layout_and_views(self):
        # 1. Integrate HeaderRibbon above StackedWidget
        layout = self.layout()
        layout.removeWidget(self.stackedWidget)

        self.right_container = QWidget(self)
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)

        self.header_ribbon = HeaderRibbon(self.right_container)
        self.right_layout.addWidget(self.header_ribbon)
        self.right_layout.addWidget(self.stackedWidget, stretch=1)

        layout.addWidget(self.right_container, stretch=1)

        # 2. Instantiate Primary Views
        self.dashboard_view = DashboardView(self.worker, self)
        self.dashboard_view.setObjectName("dashboardInterface")

        self.talent_view = TalentView(self.worker, self)
        self.talent_view.setObjectName("talentInterface")

        self.projects_view = ProjectsView(self.worker, self)
        self.projects_view.setObjectName("projectsInterface")

        self.innovation_view = InnovationView(self.worker, self)
        self.innovation_view.setObjectName("innovationInterface")

        self.sandbox_view = SandboxView(self.worker, self)
        self.sandbox_view.setObjectName("sandboxInterface")

        self.hotkeys_view = HotkeysView(self.worker, self)
        self.hotkeys_view.setObjectName("hotkeysInterface")

        # 3. Register Navigation Items
        self.addSubInterface(self.dashboard_view, FIF.TILES, "Dashboard")
        self.addSubInterface(self.talent_view, FIF.PEOPLE, "Talent HQ")
        self.addSubInterface(self.projects_view, FIF.CODE, "Projects")
        self.addSubInterface(self.innovation_view, FIF.BOOK_SHELF, "Innovation")
        self.addSubInterface(self.sandbox_view, FIF.GLOBE, "Sandbox")

        # Bottom items
        self.addSubInterface(
            self.hotkeys_view,
            FIF.COMMAND_PROMPT,
            "Shortcuts & Logs",
            NavigationItemPosition.BOTTOM,
        )

    def _wire_signals(self):
        # Header Ribbon Quick Toggles
        self.header_ribbon.freezeNeedsToggled.connect(self.worker.set_freeze_needs)
        self.header_ribbon.turboToggled.connect(self.worker.set_turbo)
        self.header_ribbon.godmodeClicked.connect(self._on_godmode_all_clicked)

        # Worker Signals -> Header Ribbon
        self.worker.connection_changed.connect(self.header_ribbon.set_connection)
        self.worker.telemetry_updated.connect(self.header_ribbon.update_telemetry)
        self.worker.freeze_needs_changed.connect(self.header_ribbon.set_freeze_state)
        self.worker.turbo_changed.connect(self.header_ribbon.set_turbo_state)

        # Cross-view Navigation
        self.dashboard_view.navigateToTalentRequested.connect(self._on_navigate_to_talent)

    def _on_godmode_all_clicked(self):
        if not self.game.is_attached():
            InfoBar.warning(
                title="Warning",
                content="Software Inc. process not attached.",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self,
            )
            return

        n_cnt = self.game.max_all_employees_needs()
        s_cnt = self.game.max_all_employees_skills()
        w_cnt = self.game.remove_all_personnel_weaknesses()
        self.worker.log("SUCCESS", f"Global Godmode: Maxed needs ({n_cnt}), maxed skills ({s_cnt}), and cured weaknesses ({w_cnt})!")
        InfoBar.success(
            title="Godmode Applied",
            content=f"Maxed needs, base skills, and cured weaknesses for {n_cnt} staff members!",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=3000,
            parent=self,
        )
        self.worker.request_immediate_refresh()

    def _on_navigate_to_talent(self, target_name: str):
        self.switchTo(self.talent_view)
        if target_name:
            self.talent_view.select_employee_by_name(target_name)

    def closeEvent(self, event):
        # Gracefully stop the background worker thread on exit
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.stop()
        super().closeEvent(event)
