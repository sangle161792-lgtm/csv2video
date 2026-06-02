"""
src/ui/main_window.py
Application shell: sidebar navigation + stacked page content area.
"""

import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from src.models.project import AppState
from src.ui.dashboard import DashboardPage
from src.ui.import_page import ImportPage
from src.ui.settings_page import SettingsPage
from src.ui.render_page import RenderPage


# ---------------------------------------------------------------------------
# Sidebar navigation button
# ---------------------------------------------------------------------------

class NavButton(QPushButton):
    """Checkable sidebar navigation button."""

    def __init__(self, emoji: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {emoji}   {label}")
        self.setCheckable(True)
        self.setObjectName("nav_btn")
        self.setMinimumHeight(46)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):

    PAGE_ORDER = ["dashboard", "import", "settings", "render"]

    NAV_ITEMS = [
        ("🏠", "Dashboard",    "dashboard"),
        ("📂", "Import Data",  "import"),
        ("⚙️",  "Settings",    "settings"),
        ("🎬", "Render",       "render"),
    ]

    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.state.load_config()           # restore last-used config if present

        self._nav_btns: dict[str, NavButton] = {}
        self._pages:    dict[str, QWidget]   = {}

        self._build_ui()
        self._navigate("dashboard")

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        self.setWindowTitle("🎬  RaceVideo Studio")
        self.setMinimumSize(1050, 680)
        self.resize(1280, 820)

        root = QWidget()
        self.setCentralWidget(root)

        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar())

        sep = QFrame()
        sep.setObjectName("sidebar_separator")
        sep.setFixedWidth(1)
        layout.addWidget(sep)

        layout.addWidget(self._build_content())

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)

        vbox = QVBoxLayout(sidebar)
        vbox.setContentsMargins(12, 22, 12, 18)
        vbox.setSpacing(2)

        # ── Logo ──────────────────────────────────────────────────────
        logo = QLabel("🎬 RaceVideo")
        logo.setObjectName("app_logo")
        vbox.addWidget(logo)

        sub = QLabel("STUDIO")
        sub.setObjectName("app_subtitle")
        vbox.addWidget(sub)

        vbox.addSpacing(20)

        # Section label
        sec = QLabel("NAVIGATION")
        sec.setObjectName("section_title")
        sec.setContentsMargins(4, 0, 0, 0)
        vbox.addWidget(sec)
        vbox.addSpacing(6)

        # ── Nav buttons ────────────────────────────────────────────────
        for emoji, label, key in self.NAV_ITEMS:
            btn = NavButton(emoji, label)
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            self._nav_btns[key] = btn
            vbox.addWidget(btn)

        vbox.addStretch()

        # ── Footer ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setObjectName("divider")
        sep.setFixedHeight(1)
        vbox.addWidget(sep)
        vbox.addSpacing(10)

        ver = QLabel("v1.0.0")
        ver.setObjectName("version_label")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(ver)

        return sidebar

    def _build_content(self) -> QStackedWidget:
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")

        self._pages["dashboard"] = DashboardPage(self.state, self)
        self._pages["import"]    = ImportPage(self.state, self)
        self._pages["settings"]  = SettingsPage(self.state, self)
        self._pages["render"]    = RenderPage(self.state, self)

        for page in self._pages.values():
            self.stack.addWidget(page)

        return self.stack

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, key: str):
        """Switch to the named page, refreshing it first."""
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)

        page = self._pages.get(key)
        if page and hasattr(page, "refresh"):
            page.refresh()

        self.stack.setCurrentWidget(self._pages[key])

    def navigate_to(self, key: str):
        """Public API for pages to trigger navigation."""
        self._navigate(key)
