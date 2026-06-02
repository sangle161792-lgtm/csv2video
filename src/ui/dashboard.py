"""
src/ui/dashboard.py
Dashboard page — shows stats, recent renders, and quick-action buttons.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QListWidget, QListWidgetItem,
    QScrollArea,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont


class StatCard(QFrame):
    """Small metric card showing an icon, value, and label."""

    def __init__(self, icon: str, label: str, initial: str = "—"):
        super().__init__()
        self.setObjectName("stat_card")

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(20, 18, 20, 18)
        vbox.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("stat_icon")
        vbox.addWidget(icon_lbl)

        self._val_lbl = QLabel(initial)
        self._val_lbl.setObjectName("stat_value")
        vbox.addWidget(self._val_lbl)

        lbl = QLabel(label)
        lbl.setObjectName("stat_label")
        vbox.addWidget(lbl)

    def set_value(self, text: str):
        self._val_lbl.setText(text)


class DashboardPage(QWidget):

    def __init__(self, state, main_window):
        super().__init__()
        self.state = state
        self.mw = main_window
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(44, 40, 44, 40)
        vbox.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        title = QLabel("Dashboard")
        title.setObjectName("page_title")
        vbox.addWidget(title)

        sub = QLabel(
            "Welcome to RaceVideo Studio  ·  "
            "Create animated ranking videos from your CSV or JSON data."
        )
        sub.setObjectName("page_subtitle")
        sub.setWordWrap(True)
        vbox.addWidget(sub)

        vbox.addSpacing(32)

        # ── Stats row ─────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self._renders_card = StatCard("🎬", "Total Renders", "0")
        self._data_card    = StatCard("📊", "Data Loaded",   "None")
        self._output_card  = StatCard("📁", "Output Folder", "output/")

        for card in (self._renders_card, self._data_card, self._output_card):
            stats_row.addWidget(card)
        stats_row.addStretch()

        vbox.addLayout(stats_row)
        vbox.addSpacing(36)

        # ── Quick actions ─────────────────────────────────────────────
        sec1 = QLabel("Quick Actions")
        sec1.setObjectName("section_title")
        vbox.addWidget(sec1)
        vbox.addSpacing(12)

        actions = QHBoxLayout()
        actions.setSpacing(12)

        btn_import = QPushButton("📂   Import Data")
        btn_import.setObjectName("action_btn")
        btn_import.clicked.connect(lambda: self.mw.navigate_to("import"))

        btn_render = QPushButton("🎬   Go to Render")
        btn_render.setObjectName("action_btn_secondary")
        btn_render.clicked.connect(lambda: self.mw.navigate_to("render"))

        btn_folder = QPushButton("📁   Open Output Folder")
        btn_folder.setObjectName("action_btn_secondary")
        btn_folder.clicked.connect(self._open_folder)

        btn_sample = QPushButton("🧪   Load Sample CSV")
        btn_sample.setObjectName("action_btn_secondary")
        btn_sample.clicked.connect(self._load_sample)

        for btn in (btn_import, btn_render, btn_folder, btn_sample):
            btn.setMinimumHeight(52)
            actions.addWidget(btn)

        vbox.addLayout(actions)
        vbox.addSpacing(36)

        # ── How to use ────────────────────────────────────────────────
        sec2 = QLabel("How It Works")
        sec2.setObjectName("section_title")
        vbox.addWidget(sec2)
        vbox.addSpacing(12)

        steps_row = QHBoxLayout()
        steps_row.setSpacing(12)
        steps = [
            ("1️⃣", "Import Data",    "Upload a CSV or JSON file with time-series rankings."),
            ("2️⃣", "Settings",       "Choose resolution, FPS, colors, and title."),
            ("3️⃣", "Render",         "Click Render and watch the progress bar fill up."),
            ("4️⃣", "Download",       "Open the output folder and share your MP4!"),
        ]
        for num, heading, desc in steps:
            card = self._make_step_card(num, heading, desc)
            steps_row.addWidget(card)
        vbox.addLayout(steps_row)
        vbox.addSpacing(36)

        # ── Recent renders ────────────────────────────────────────────
        sec3 = QLabel("Recent Renders")
        sec3.setObjectName("section_title")
        vbox.addWidget(sec3)
        vbox.addSpacing(12)

        self._recent_list = QListWidget()
        self._recent_list.setObjectName("recent_list")
        self._recent_list.setMaximumHeight(220)
        self._recent_list.itemDoubleClicked.connect(self._open_render)
        vbox.addWidget(self._recent_list)

        vbox.addStretch()

    def _make_step_card(self, num: str, heading: str, desc: str) -> QFrame:
        card = QFrame()
        card.setObjectName("stat_card")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 16, 18, 16)
        vbox.setSpacing(6)

        n = QLabel(num)
        n.setObjectName("stat_icon")
        vbox.addWidget(n)

        h = QLabel(heading)
        h.setObjectName("section_title")
        vbox.addWidget(h)

        d = QLabel(desc)
        d.setObjectName("hint_label")
        d.setWordWrap(True)
        vbox.addWidget(d)

        return card

    # ------------------------------------------------------------------
    def _open_folder(self):
        path = os.path.abspath("output")
        os.makedirs(path, exist_ok=True)
        os.startfile(path)

    def _open_render(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and os.path.exists(path):
            os.startfile(path)

    def _load_sample(self):
        sample = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sample_data.csv")
        sample = os.path.normpath(sample)
        if os.path.exists(sample):
            self.mw.navigate_to("import")
            import_page = self.mw._pages["import"]
            import_page.load_file(sample)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Sample Not Found",
                                f"Could not find sample file:\n{sample}")

    def refresh(self):
        """Called every time the dashboard becomes the active page."""
        n = len(self.state.recent_outputs)
        self._renders_card.set_value(str(n))

        if self.state.has_data():
            tc = self.state.get_time_col() or "?"
            rows = len(self.state.dataframe)
            self._data_card.set_value(f"{rows} rows")
        else:
            self._data_card.set_value("None")

        # Recent renders list
        self._recent_list.clear()
        if self.state.recent_outputs:
            for path in reversed(self.state.recent_outputs[-15:]):
                name = os.path.basename(path)
                size_kb = ""
                if os.path.exists(path):
                    size_kb = f"  ({os.path.getsize(path) // 1024} KB)"
                item = QListWidgetItem(f"🎬  {name}{size_kb}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                self._recent_list.addItem(item)
        else:
            placeholder = QListWidgetItem(
                "No renders yet.  Load data and click Render to create your first video."
            )
            placeholder.setFlags(placeholder.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self._recent_list.addItem(placeholder)
