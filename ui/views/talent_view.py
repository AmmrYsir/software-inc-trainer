"""
Software Inc. Trainer - Talent HQ View (Personnel & VIP Founder)
Unified staff management with search, team filtering, batch actions, and responsive deep inspector.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QHeaderView,
    QTableWidgetItem,
    QFrame,
    QScrollArea,
    QGridLayout,
    QLabel,
)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    TableWidget,
    SearchLineEdit,
    ComboBox,
    PushButton,
    PrimaryPushButton,
    ToolButton,
    Pivot,
    SegmentedWidget,
    CardWidget,
    HeaderCardWidget,
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    StrongBodyLabel,
    FluentIcon as FIF,
    DoubleSpinBox,
    SpinBox,
    Slider,
    InfoBar,
    InfoBarPosition,
)

from ..components.vitals_gauge import VitalsGauge
from ..components.star_rating import StarRatingWidget
from ..components.trait_chip import TraitChip
from core.memory import get_game_memory
from core.constants import (
    ROLE_NAMES,
    ROLE_ALL_SPECIALIZATIONS,
    NEED_NAMES,
    ALL_TRAITS,
    WEAKNESSES_MASK,
    MASTER_TRAITS_MASK,
)


class TalentView(QWidget):
    """
    Unified Personnel Management & Deep Employee/Founder Inspector.
    """

    def __init__(self, worker, parent=None):
        super().__init__(parent)
        self.worker = worker
        self.game = get_game_memory()

        self._all_employees: List[Dict[str, Any]] = []
        self._filtered_employees: List[Dict[str, Any]] = []
        self._selected_emp: Optional[Dict[str, Any]] = None

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(28, 20, 28, 20)
        root_layout.setSpacing(16)

        # 1. Header & Batch Action Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        self.title_lbl = TitleLabel("Talent HQ & Personnel Matrix", self)
        self.subtitle_lbl = CaptionLabel("Unified employee roster, founder profile, and deep specialization inspector.", self)
        self.subtitle_lbl.setStyleSheet("color: #A0A0A0;")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        top_bar.addLayout(title_box)

        top_bar.addStretch(1)

        # Global Batch Buttons
        batch_all_btn = PrimaryPushButton(FIF.BRUSH, "Boost All Staff", self)
        batch_all_btn.setToolTip("Restore all needs to 100% and max out all base skills for all employees")
        batch_all_btn.clicked.connect(self._batch_boost_all)
        top_bar.addWidget(batch_all_btn)

        batch_specs_btn = PushButton(FIF.TILES, "Max All Specs (3★)", self)
        batch_specs_btn.setToolTip("Elevate all employee specializations to 3 stars")
        batch_specs_btn.clicked.connect(self._batch_max_specs)
        top_bar.addWidget(batch_specs_btn)

        batch_cure_btn = PushButton(FIF.ACCEPT, "Purge Weaknesses", self)
        batch_cure_btn.setToolTip("Cure all 8 negative traits across all staff")
        batch_cure_btn.clicked.connect(self._batch_cure_weaknesses)
        top_bar.addWidget(batch_cure_btn)

        batch_free_btn = PushButton(FIF.SHOPPING_CART, "Free Salaries ($0)", self)
        batch_free_btn.setToolTip("Set all employee salaries to $0 (free labor)")
        batch_free_btn.clicked.connect(self._batch_free_salaries)
        top_bar.addWidget(batch_free_btn)

        root_layout.addLayout(top_bar)

        # 2. Main Splitter: Left Table | Right Inspector Drawer
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)

        # --- LEFT PANEL: Filter & Table ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(10)

        # Filter Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.search_box = SearchLineEdit(left_panel)
        self.search_box.setPlaceholderText("Search employee name or role...")
        self.search_box.textChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.search_box, stretch=2)

        self.role_filter = ComboBox(left_panel)
        self.role_filter.addItems(["All Roles", "Lead", "Code", "Design", "Art", "Service"])
        self.role_filter.currentTextChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.role_filter, stretch=1)

        self.team_filter = ComboBox(left_panel)
        self.team_filter.addItem("All Teams")
        self.team_filter.currentTextChanged.connect(self._apply_filters)
        filter_bar.addWidget(self.team_filter, stretch=1)

        left_layout.addLayout(filter_bar)

        # Employee Table
        self.table = TableWidget(left_panel)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Name", "Role", "Team", "Salary", "Energy", "Stress", "Traits"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(TableWidget.SelectRows)
        self.table.setSelectionMode(TableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        left_layout.addWidget(self.table)

        self.splitter.addWidget(left_panel)

        # --- RIGHT PANEL: Deep Inspector Drawer ---
        self.inspector_scroll = QScrollArea(self.splitter)
        self.inspector_scroll.setWidgetResizable(True)
        self.inspector_scroll.setFrameShape(QFrame.NoFrame)
        self.inspector_scroll.setMinimumWidth(480)

        self.inspector_widget = QWidget()
        self.inspector_layout = QVBoxLayout(self.inspector_widget)
        self.inspector_layout.setContentsMargins(12, 0, 0, 0)
        self.inspector_layout.setSpacing(12)
        self.inspector_scroll.setWidget(self.inspector_widget)

        self._build_inspector_ui()

        self.splitter.addWidget(self.inspector_scroll)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)

        root_layout.addWidget(self.splitter)

    def _build_inspector_ui(self):
        # Empty State Placeholder
        self.placeholder_card = CardWidget(self.inspector_widget)
        ph_layout = QVBoxLayout(self.placeholder_card)
        ph_layout.setContentsMargins(30, 60, 30, 60)
        ph_layout.setAlignment(Qt.AlignCenter)
        ph_icon = QLabel("👤", self.placeholder_card)
        ph_icon.setStyleSheet("font-size: 40px;")
        ph_icon.setAlignment(Qt.AlignCenter)
        ph_lbl = StrongBodyLabel("Select an employee or founder from the roster to inspect details", self.placeholder_card)
        ph_lbl.setAlignment(Qt.AlignCenter)
        ph_layout.addWidget(ph_icon)
        ph_layout.addWidget(ph_lbl)
        self.inspector_layout.addWidget(self.placeholder_card)

        # Content Card (Visible when employee selected)
        self.detail_card = HeaderCardWidget(self.inspector_widget)
        self.detail_card.setTitle("Employee Inspector")
        self.detail_card.setVisible(False)
        detail_layout = QVBoxLayout()
        self.detail_card.viewLayout.addLayout(detail_layout)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(14)

        # Header Info Row
        info_header = QHBoxLayout()
        info_header.setSpacing(12)

        self.insp_name_lbl = SubtitleLabel("Employee Name", self.detail_card)
        self.insp_badge = QLabel("ROLE", self.detail_card)
        self.insp_badge.setStyleSheet("""
            QLabel {
                background-color: #0078D4;
                color: #FFFFFF;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        info_header.addWidget(self.insp_name_lbl)
        info_header.addWidget(self.insp_badge)
        info_header.addStretch(1)

        # Godmode Single Employee Button
        self.btn_godmode_emp = PrimaryPushButton(FIF.HEART, "Godmode", self.detail_card)
        self.btn_godmode_emp.setToolTip("100% Needs, Max Skills, 3-Star Specs, Clear Weaknesses, Master Traits")
        self.btn_godmode_emp.clicked.connect(self._godmode_selected_emp)
        info_header.addWidget(self.btn_godmode_emp)

        detail_layout.addLayout(info_header)

        # Quick Actions Row
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(8)

        btn_heal = PushButton(FIF.ACCEPT, "Max Needs", self.detail_card)
        btn_heal.clicked.connect(self._max_selected_needs)
        quick_actions.addWidget(btn_heal)

        btn_skills = PushButton(FIF.BRUSH, "Max Skills", self.detail_card)
        btn_skills.clicked.connect(self._max_selected_skills)
        quick_actions.addWidget(btn_skills)

        btn_specs = PushButton(FIF.TILES, "Max Specs", self.detail_card)
        btn_specs.clicked.connect(self._max_selected_specs)
        quick_actions.addWidget(btn_specs)

        btn_cure = PushButton(FIF.ACCEPT, "Cure Weaknesses", self.detail_card)
        btn_cure.clicked.connect(self._cure_selected_weaknesses)
        quick_actions.addWidget(btn_cure)

        quick_actions.addStretch(1)
        detail_layout.addLayout(quick_actions)

        # Tabs / Pivot for: Needs, Skills, Specs, Traits
        self.pivot = Pivot(self.detail_card)
        self.pivot.addItem("needs", "Needs & Vitals")
        self.pivot.addItem("skills", "Base Skills")
        self.pivot.addItem("specs", "Specializations (25)")
        self.pivot.addItem("traits", "Traits & Perks")
        self.pivot.setCurrentItem("needs")
        self.pivot.currentItemChanged.connect(self._on_pivot_changed)
        detail_layout.addWidget(self.pivot)

        # Sub-container pages
        self.subpages = {}

        # 1. Needs Subpage
        self.page_needs = QWidget()
        page_needs_layout = QVBoxLayout(self.page_needs)
        page_needs_layout.setContentsMargins(0, 10, 0, 0)
        page_needs_layout.setSpacing(8)

        self.need_gauges = {}
        for need in NEED_NAMES:
            gauge = VitalsGauge(need, 1.0, is_stress=False, parent=self.page_needs)
            gauge.valueChanged.connect(lambda val, n=need: self._on_need_changed(n, val))
            self.need_gauges[need] = gauge
            page_needs_layout.addWidget(gauge)

        # Stress Gauge
        self.stress_gauge = VitalsGauge("Stress", 0.0, is_stress=True, parent=self.page_needs)
        self.stress_gauge.valueChanged.connect(lambda val: self._on_need_changed("Stress", val))
        page_needs_layout.addWidget(self.stress_gauge)

        self.subpages["needs"] = self.page_needs
        detail_layout.addWidget(self.page_needs)

        # 2. Base Skills Subpage
        self.page_skills = QWidget()
        self.page_skills.setVisible(False)
        page_skills_layout = QVBoxLayout(self.page_skills)
        page_skills_layout.setContentsMargins(0, 10, 0, 0)
        page_skills_layout.setSpacing(12)

        self.skill_sliders = {}
        self.skill_val_lbls = {}

        for role in ROLE_NAMES:
            row = QHBoxLayout()
            row.setSpacing(10)
            lbl = BodyLabel(f"{role} Skill:", self.page_skills)
            lbl.setFixedWidth(80)
            row.addWidget(lbl)

            slider = Slider(Qt.Horizontal, self.page_skills)
            slider.setRange(0, 100)
            slider.setValue(100)
            row.addWidget(slider, stretch=1)

            val_lbl = StrongBodyLabel("100%", self.page_skills)
            val_lbl.setFixedWidth(45)
            slider.valueChanged.connect(lambda v, r=role, vl=val_lbl: self._on_skill_slider_changed(r, v, vl))
            row.addWidget(val_lbl)

            self.skill_sliders[role] = slider
            self.skill_val_lbls[role] = val_lbl
            page_skills_layout.addWidget(QWidget())
            page_skills_layout.addLayout(row)

        self.subpages["skills"] = self.page_skills
        detail_layout.addWidget(self.page_skills)

        # 3. Specializations Subpage
        self.page_specs = QWidget()
        self.page_specs.setVisible(False)
        page_specs_layout = QVBoxLayout(self.page_specs)
        page_specs_layout.setContentsMargins(0, 10, 0, 0)
        page_specs_layout.setSpacing(10)

        # Spec points management row
        pts_row = QHBoxLayout()
        pts_row.setSpacing(8)
        pts_lbl = BodyLabel("Unspent Points / EXP:", self.page_specs)
        pts_row.addWidget(pts_lbl)

        btn_add_pts = PushButton(FIF.ADD, "+500 EXP to All Roles", self.page_specs)
        btn_add_pts.clicked.connect(self._add_selected_exp)
        pts_row.addWidget(btn_add_pts)

        btn_reset_pts = PushButton(FIF.SYNC, "Refund Capacity", self.page_specs)
        btn_reset_pts.clicked.connect(self._reset_selected_spec_used)
        pts_row.addWidget(btn_reset_pts)

        pts_row.addStretch(1)
        page_specs_layout.addLayout(pts_row)

        # Star Rating Widgets grouped by role
        self.star_widgets = {}
        for role, subfields in ROLE_ALL_SPECIALIZATIONS.items():
            role_header = CaptionLabel(f"── {role.upper()} SPECIALIZATIONS ──", self.page_specs)
            role_header.setStyleSheet("color: #0078D4; font-weight: bold; margin-top: 6px;")
            page_specs_layout.addWidget(role_header)

            for subfield in subfields:
                key = f"{role}_{subfield}"
                star_w = StarRatingWidget(subfield, level=0, parent=self.page_specs)
                star_w.levelChanged.connect(lambda lvl, r=role, sf=subfield: self._on_spec_star_changed(r, sf, lvl))
                self.star_widgets[key] = star_w
                page_specs_layout.addWidget(star_w)

        self.subpages["specs"] = self.page_specs
        detail_layout.addWidget(self.page_specs)

        # 4. Traits Subpage
        self.page_traits = QWidget()
        self.page_traits.setVisible(False)
        page_traits_layout = QVBoxLayout(self.page_traits)
        page_traits_layout.setContentsMargins(0, 10, 0, 0)
        page_traits_layout.setSpacing(10)

        trait_actions = QHBoxLayout()
        trait_actions.setSpacing(8)

        btn_master_traits = PrimaryPushButton(FIF.HEART, "Grant Master Package", self.page_traits)
        btn_master_traits.clicked.connect(self._grant_selected_master_traits)
        trait_actions.addWidget(btn_master_traits)

        btn_clear_weakness = PushButton(FIF.ACCEPT, "Purge Weaknesses Only", self.page_traits)
        btn_clear_weakness.clicked.connect(self._cure_selected_weaknesses)
        trait_actions.addWidget(btn_clear_weakness)

        trait_actions.addStretch(1)
        page_traits_layout.addLayout(trait_actions)

        # Trait Chips Grid / Flow
        self.trait_chips = {}

        # Weaknesses Group
        weakness_hdr = CaptionLabel("NEGATIVE WEAKNESSES (8):", self.page_traits)
        weakness_hdr.setStyleSheet("color: #FFB3B8; font-weight: bold; margin-top: 6px;")
        page_traits_layout.addWidget(weakness_hdr)

        weak_grid = QGridLayout()
        weak_grid.setSpacing(6)
        w_idx = 0
        for name, mask, is_w in ALL_TRAITS:
            if is_w:
                chip = TraitChip(name, mask, is_weakness=True, active=False, parent=self.page_traits)
                chip.traitToggled.connect(lambda t_name, active: self._on_trait_toggled(t_name, active))
                self.trait_chips[name] = chip
                weak_grid.addWidget(chip, w_idx // 3, w_idx % 3)
                w_idx += 1
        page_traits_layout.addLayout(weak_grid)

        # Perks Group
        perk_hdr = CaptionLabel("POSITIVE PERKS (25):", self.page_traits)
        perk_hdr.setStyleSheet("color: #60CDFF; font-weight: bold; margin-top: 10px;")
        page_traits_layout.addWidget(perk_hdr)

        perk_grid = QGridLayout()
        perk_grid.setSpacing(6)
        p_idx = 0
        for name, mask, is_w in ALL_TRAITS:
            if not is_w:
                chip = TraitChip(name, mask, is_weakness=False, active=False, parent=self.page_traits)
                chip.traitToggled.connect(lambda t_name, active: self._on_trait_toggled(t_name, active))
                self.trait_chips[name] = chip
                perk_grid.addWidget(chip, p_idx // 3, p_idx % 3)
                p_idx += 1
        page_traits_layout.addLayout(perk_grid)

        self.subpages["traits"] = self.page_traits
        detail_layout.addWidget(self.page_traits)

        self.inspector_layout.addWidget(self.detail_card)

    def _connect_signals(self):
        self.worker.employees_updated.connect(self._on_employees_updated)

    def _on_pivot_changed(self, route_key: str):
        for k, page in self.subpages.items():
            page.setVisible(k == route_key)

    def _on_employees_updated(self, employees: List[Dict[str, Any]]):
        self._all_employees = employees

        # Populate team filter dropdown uniquely
        current_team = self.team_filter.currentText()
        teams = sorted(list(set(e.get("team", "None") for e in employees if e.get("team"))))
        self.team_filter.blockSignals(True)
        self.team_filter.clear()
        self.team_filter.addItem("All Teams")
        for t in teams:
            self.team_filter.addItem(t)
        if current_team in teams:
            self.team_filter.setCurrentText(current_team)
        else:
            self.team_filter.setCurrentIndex(0)
        self.team_filter.blockSignals(False)

        self._apply_filters()

    def _apply_filters(self):
        query = self.search_box.text().strip().lower()
        role = self.role_filter.currentText()
        team = self.team_filter.currentText()

        filtered = []
        for e in self._all_employees:
            name = e.get("name", "").lower()
            e_role = e.get("role", "")
            e_team = e.get("team", "")

            if query and (query not in name and query not in e_role.lower()):
                continue
            if role != "All Roles" and e_role != role:
                continue
            if team != "All Teams" and e_team != team:
                continue
            filtered.append(e)

        self._filtered_employees = filtered
        self._populate_table()

    def _populate_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._filtered_employees))

        selected_ptr = self._selected_emp.get("ptr") if self._selected_emp else None
        target_row_to_select = -1

        for row, e in enumerate(self._filtered_employees):
            name = e.get("name", "Unknown")
            is_founder = e.get("is_founder", False) or e.get("founder", False)
            if is_founder:
                name = f"👑 {name} (Founder)"

            role = e.get("role", "Lead")
            team = e.get("team", "None")
            salary = f"${e.get('salary', 0):,}"

            vitals = e.get("vitals", {})
            energy = f"{int(vitals.get('energy', 1.0) * 100)}%"
            stress = f"{int(vitals.get('stress', 0.0) * 100)}%"

            traits_count = len(e.get("traits", []) or (e.get("goods", []) + e.get("weaknesses", [])))

            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(role))
            self.table.setItem(row, 2, QTableWidgetItem(team))
            self.table.setItem(row, 3, QTableWidgetItem(salary))
            self.table.setItem(row, 4, QTableWidgetItem(energy))
            self.table.setItem(row, 5, QTableWidgetItem(stress))
            self.table.setItem(row, 6, QTableWidgetItem(str(traits_count)))

            if selected_ptr and e.get("ptr") == selected_ptr:
                target_row_to_select = row

        self.table.blockSignals(False)

        if target_row_to_select != -1:
            self.table.selectRow(target_row_to_select)

    def _on_table_selection_changed(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._selected_emp = None
            self.placeholder_card.setVisible(True)
            self.detail_card.setVisible(False)
            return

        row_idx = rows[0].row()
        if 0 <= row_idx < len(self._filtered_employees):
            emp = self._filtered_employees[row_idx]
            self._selected_emp = emp
            self._update_inspector_with_emp(emp)

    def _update_inspector_with_emp(self, emp: dict):
        self.placeholder_card.setVisible(False)
        self.detail_card.setVisible(True)

        name = emp.get("name", "Unknown")
        is_founder = emp.get("is_founder", False) or emp.get("founder", False)
        role = emp.get("role", "Lead")

        if is_founder:
            self.insp_name_lbl.setText(f"👑 {name} (VIP Founder)")
            self.insp_badge.setText("FOUNDER")
            self.insp_badge.setStyleSheet("""
                QLabel {
                    background-color: #D88B00;
                    color: #FFFFFF;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)
        else:
            self.insp_name_lbl.setText(name)
            self.insp_badge.setText(role.upper())
            self.insp_badge.setStyleSheet("""
                QLabel {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
            """)

        # 1. Update Needs
        vitals = emp.get("vitals", {})
        for need in NEED_NAMES:
            val = vitals.get(need.lower(), 1.0)
            if need in self.need_gauges:
                self.need_gauges[need].set_value(val)
        stress_val = vitals.get("stress", 0.0)
        self.stress_gauge.set_value(stress_val)

        # 2. Update Skills
        skills = emp.get("skills_dict") or emp.get("skills", {})
        if isinstance(skills, list):
            skills = {ROLE_NAMES[i]: skills[i] for i in range(min(len(skills), len(ROLE_NAMES)))}

        for r in ROLE_NAMES:
            s_val = int(skills.get(r, 1.0) * 100)
            if r in self.skill_sliders:
                self.skill_sliders[r].blockSignals(True)
                self.skill_sliders[r].setValue(s_val)
                self.skill_val_lbls[r].setText(f"{s_val}%")
                self.skill_sliders[r].blockSignals(False)

        # 3. Update Specs Star Ratings
        specs = emp.get("specializations") or emp.get("specs", {})
        for role, subfields in ROLE_ALL_SPECIALIZATIONS.items():
            role_specs = specs.get(role, {})
            for subfield in subfields:
                key = f"{role}_{subfield}"
                lvl = role_specs.get(subfield, 0)
                if key in self.star_widgets:
                    self.star_widgets[key].set_level(lvl)

        # 4. Update Traits
        current_traits = set(emp.get("traits", []) or (emp.get("goods", []) + emp.get("weaknesses", [])))
        for name, chip in self.trait_chips.items():
            chip.blockSignals(True)
            chip.set_active(name in current_traits)
            chip.blockSignals(False)

    def select_employee_by_name(self, target_name: str):
        if not target_name:
            if self._all_employees:
                self.table.selectRow(0)
            return

        self.search_box.setText(target_name)
        for row, e in enumerate(self._filtered_employees):
            if target_name.lower() in e.get("name", "").lower():
                self.table.selectRow(row)
                break

    # --- Actions on Selected Employee ---

    def _godmode_selected_emp(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        name = self._selected_emp.get("name", "Employee")
        self.game.max_employee_needs(ptr)
        self.game.max_employee_skills(ptr)
        self.game.max_employee_specs(ptr)
        self.game.remove_employee_weaknesses(ptr)
        self.game.grant_master_traits(ptr)
        self.worker.log("SUCCESS", f"Granted full Godmode to '{name}'!")
        self._show_success(f"'{name}' fully godmoded!")
        self.worker.request_immediate_refresh()

    def _max_selected_needs(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.max_employee_needs(ptr)
        self.worker.log("SUCCESS", f"Restored all needs for '{self._selected_emp.get('name')}' to 100%")
        self._show_success("Needs restored to 100%")
        self.worker.request_immediate_refresh()

    def _max_selected_skills(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.max_employee_skills(ptr)
        self.worker.log("SUCCESS", f"Maxed out base skills for '{self._selected_emp.get('name')}'")
        self._show_success("Base skills maxed out!")
        self.worker.request_immediate_refresh()

    def _max_selected_specs(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.max_employee_specs(ptr)
        self.worker.log("SUCCESS", f"Maxed out 25 specializations to 3★ for '{self._selected_emp.get('name')}'")
        self._show_success("Specializations elevated to 3★!")
        self.worker.request_immediate_refresh()

    def _cure_selected_weaknesses(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.remove_employee_weaknesses(ptr)
        self.worker.log("SUCCESS", f"Purged all weaknesses from '{self._selected_emp.get('name')}'")
        self._show_success("All weaknesses cured!")
        self.worker.request_immediate_refresh()

    def _grant_selected_master_traits(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.grant_master_traits(ptr)
        self.worker.log("SUCCESS", f"Granted master perks pack to '{self._selected_emp.get('name')}'")
        self._show_success("Master traits granted!")
        self.worker.request_immediate_refresh()

    def _add_selected_exp(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.add_employee_spec_exp(ptr, 500.0)
        self.worker.log("SUCCESS", f"Added +500 Specialization EXP to '{self._selected_emp.get('name')}'")
        self._show_success("Added +500 Spec EXP!")
        self.worker.request_immediate_refresh()

    def _reset_selected_spec_used(self):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.reset_employee_spec_used(ptr)
        self.worker.log("SUCCESS", f"Reset spent specialization points for '{self._selected_emp.get('name')}'")
        self._show_success("Spec capacity refunded!")
        self.worker.request_immediate_refresh()

    def _on_need_changed(self, need: str, val: float):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.set_employee_need(ptr, need, val)

    def _on_skill_slider_changed(self, role: str, val: int, label: QLabel):
        label.setText(f"{val}%")
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        role_idx = ROLE_NAMES.index(role) if role in ROLE_NAMES else role
        self.game.set_employee_skill(ptr, role_idx, val / 100.0)

    def _on_spec_star_changed(self, role: str, subfield: str, level: int):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        role_idx = ROLE_NAMES.index(role) if role in ROLE_NAMES else role
        self.game.set_employee_spec_level(ptr, role_idx, subfield, level)
        self.worker.log("INFO", f"Set {role} - {subfield} to {level}★ for '{self._selected_emp.get('name')}'")

    def _on_trait_toggled(self, trait_name: str, active: bool):
        if not self._selected_emp or not self.game.is_attached():
            return
        ptr = self._selected_emp["ptr"]
        self.game.set_employee_trait_toggle(ptr, trait_name, active)
        self.worker.log("INFO", f"Set trait '{trait_name}' to {active} for '{self._selected_emp.get('name')}'")

    # --- Batch Operations on All Staff ---

    def _batch_boost_all(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        n_cnt = self.game.max_all_employees_needs()
        s_cnt = self.game.max_all_employees_skills()
        self.worker.log("SUCCESS", f"Boosted all staff: Restored needs for {n_cnt} & maxed skills for {s_cnt} employees!")
        self._show_success(f"Maxed needs & skills for all {n_cnt} staff members!")
        self.worker.request_immediate_refresh()

    def _batch_max_specs(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.max_all_employees_specs()
        self.worker.log("SUCCESS", f"Elevated 25 specializations to 3★ across {cnt} employees!")
        self._show_success(f"Elevated specs for all {cnt} staff members!")
        self.worker.request_immediate_refresh()

    def _batch_cure_weaknesses(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.remove_all_personnel_weaknesses()
        self.worker.log("SUCCESS", f"Purged all weaknesses across {cnt} employees!")
        self._show_success(f"Cured all weaknesses for {cnt} staff members!")
        self.worker.request_immediate_refresh()

    def _batch_free_salaries(self):
        if not self.game.is_attached():
            self._show_warn("Game not attached.")
            return
        cnt = self.game.set_all_employees_free_salary()
        self.worker.log("SUCCESS", f"Set $0 salaries (free labor) for {cnt} personnel!")
        self._show_success(f"Set $0 salaries for all {cnt} employees!")
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
