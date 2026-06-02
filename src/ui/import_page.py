"""
src/ui/import_page.py
Data import page — drag-drop / browse for CSV/JSON, preview table, validation.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QFileDialog, QScrollArea, QSizePolicy, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QMimeData, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont


# ---------------------------------------------------------------------------
# Drag-and-drop zone
# ---------------------------------------------------------------------------

class DropZone(QLabel):
    """A label that accepts file drops and emits file_dropped(path)."""

    file_dropped = pyqtSignal(str)

    _IDLE_TEXT = (
        "🗂️\n\n"
        "Drag & drop a CSV or JSON file here\n\n"
        "or click  Browse File  below"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("drop_zone")
        self.setText(self._IDLE_TEXT)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

    # ── Drag events ──────────────────────────────────────────────────
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            if any(p.lower().endswith((".csv", ".json")) for p in paths):
                event.acceptProposedAction()
                self.setProperty("drag_active", "true")
                self.style().unpolish(self)
                self.style().polish(self)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._reset_style()

    def dropEvent(self, event: QDropEvent):
        self._reset_style()
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith((".csv", ".json")):
                self.file_dropped.emit(path)
                return

    def _reset_style(self):
        self.setProperty("drag_active", "false")
        self.style().unpolish(self)
        self.style().polish(self)


# ---------------------------------------------------------------------------
# Import page
# ---------------------------------------------------------------------------

class ImportPage(QWidget):

    MAX_PREVIEW_ROWS = 50   # rows shown in the preview table

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
        title = QLabel("Import Data")
        title.setObjectName("page_title")
        vbox.addWidget(title)

        sub = QLabel(
            "Upload a CSV or JSON file.  "
            "First column = time axis  ·  Other columns = entities to race."
        )
        sub.setObjectName("page_subtitle")
        sub.setWordWrap(True)
        vbox.addWidget(sub)

        vbox.addSpacing(28)

        # ── Drop zone ─────────────────────────────────────────────────
        self._drop_zone = DropZone()
        self._drop_zone.file_dropped.connect(self.load_file)
        vbox.addWidget(self._drop_zone)

        vbox.addSpacing(14)

        # ── Browse row ────────────────────────────────────────────────
        browse_row = QHBoxLayout()
        browse_row.setSpacing(12)

        self._browse_btn = QPushButton("📂   Browse File…")
        self._browse_btn.setObjectName("action_btn")
        self._browse_btn.setMinimumHeight(46)
        self._browse_btn.setFixedWidth(200)
        self._browse_btn.clicked.connect(self._browse)
        browse_row.addWidget(self._browse_btn)

        self._file_lbl = QLabel("No file selected")
        self._file_lbl.setObjectName("hint_label")
        browse_row.addWidget(self._file_lbl)
        browse_row.addStretch()

        self._clear_btn = QPushButton("✕  Clear")
        self._clear_btn.setObjectName("action_btn_secondary")
        self._clear_btn.setFixedWidth(100)
        self._clear_btn.setMinimumHeight(46)
        self._clear_btn.clicked.connect(self._clear)
        self._clear_btn.setVisible(False)
        browse_row.addWidget(self._clear_btn)

        vbox.addLayout(browse_row)
        vbox.addSpacing(20)

        # ── Format hint ───────────────────────────────────────────────
        fmt = QLabel(
            "Expected format:  "
            "<span style='color:#7C3AED'>Year, Entity A, Entity B, …</span>"
            "   ·   Each row = one time period."
        )
        fmt.setObjectName("hint_label")
        fmt.setTextFormat(Qt.TextFormat.RichText)
        vbox.addWidget(fmt)

        vbox.addSpacing(24)

        # ── Validation messages ────────────────────────────────────────
        self._validation_widget = QWidget()
        val_vbox = QVBoxLayout(self._validation_widget)
        val_vbox.setContentsMargins(0, 0, 0, 0)
        val_vbox.setSpacing(6)
        self._val_labels: list[QLabel] = []
        vbox.addWidget(self._validation_widget)

        # ── Preview table ─────────────────────────────────────────────
        self._preview_section = QWidget()
        self._preview_section.setVisible(False)
        prev_vbox = QVBoxLayout(self._preview_section)
        prev_vbox.setContentsMargins(0, 0, 0, 0)
        prev_vbox.setSpacing(12)

        prev_header = QHBoxLayout()
        self._preview_title = QLabel("Data Preview")
        self._preview_title.setObjectName("section_title")
        prev_header.addWidget(self._preview_title)
        prev_header.addStretch()

        self._proceed_btn = QPushButton("⚙️   Configure Settings  →")
        self._proceed_btn.setObjectName("action_btn")
        self._proceed_btn.setMinimumHeight(42)
        self._proceed_btn.setFixedWidth(240)
        self._proceed_btn.clicked.connect(lambda: self.mw.navigate_to("settings"))
        prev_header.addWidget(self._proceed_btn)

        prev_vbox.addLayout(prev_header)

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.setMinimumHeight(280)
        prev_vbox.addWidget(self._table)

        vbox.addWidget(self._preview_section)
        vbox.addStretch()

    # ------------------------------------------------------------------
    # File loading
    # ------------------------------------------------------------------

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Data File",
            os.path.expanduser("~"),
            "Data Files (*.csv *.json);;CSV (*.csv);;JSON (*.json)",
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str):
        """Public entry point — also called by the dashboard 'Load Sample' button."""
        from src.engine.data_parser import load_file
        from src.engine.validator import validate, clean_data

        self._clear_validation()

        try:
            df_raw = load_file(path)
        except Exception as exc:
            self._show_error(f"❌ Could not read file: {exc}")
            return

        errors = validate(df_raw)
        df_clean = clean_data(df_raw)

        # Store in state
        self.state.data_path = path
        self.state.dataframe  = df_clean
        self.state.validation_errors = errors

        # Auto-set title from filename (only if user hasn't customised it)
        default_titles = {"Bar Chart Race", "", "bar chart race"}
        if self.state.config.get("title", "") in default_titles:
            base = os.path.splitext(os.path.basename(path))[0]
            auto_title = base.replace("_", " ").replace("-", " ").title()
            self.state.config["title"] = auto_title

        # Reset entity colors/logos whenever new data is loaded
        self.state.config["colors"] = {}
        self.state.config["logos"]  = {}

        # ── AUTO-ENRICH ENTITY LOGOS (Flags, Football Clubs, Company Logos) ──
        from src.engine.enricher import enrich_entity_logo
        entities = list(df_clean.columns[1:])
        enriched_count = 0
        for entity in entities:
            logo_path = enrich_entity_logo(entity)
            if logo_path:
                self.state.config["logos"][entity] = logo_path
                enriched_count += 1

        if enriched_count > 0:
            errors.append(f"✨ Auto-enriched {enriched_count} logo(s) matching your entities!")

        # UI updates
        self._file_lbl.setText(f"📄  {os.path.basename(path)}")
        self._clear_btn.setVisible(True)
        self._drop_zone.setText(f"✅  Loaded: {os.path.basename(path)}")

        self._show_validation(errors)
        self._populate_table(df_raw)

    def _populate_table(self, df):
        self._preview_section.setVisible(True)
        rows_to_show = min(len(df), self.MAX_PREVIEW_ROWS)

        self._table.setRowCount(rows_to_show)
        self._table.setColumnCount(len(df.columns))
        self._table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for r in range(rows_to_show):
            for c_idx, col in enumerate(df.columns):
                val = str(df.iloc[r][col])
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c_idx == 0:
                    item.setForeground(
                        self.palette().highlight().color()
                    )
                self._table.setItem(r, c_idx, item)

        self._table.resizeColumnsToContents()

        lbl_suffix = ""
        if len(df) > self.MAX_PREVIEW_ROWS:
            lbl_suffix = f"  (showing first {self.MAX_PREVIEW_ROWS} of {len(df)} rows)"
        self._preview_title.setText(
            f"Data Preview — {len(df.columns)} columns, {len(df)} rows{lbl_suffix}"
        )

    # ------------------------------------------------------------------
    # Validation display
    # ------------------------------------------------------------------

    def _clear_validation(self):
        for lbl in self._val_labels:
            lbl.deleteLater()
        self._val_labels.clear()

    def _show_validation(self, errors: list):
        layout = self._validation_widget.layout()
        for msg in errors:
            lbl = QLabel(msg)
            if msg.startswith("❌"):
                lbl.setObjectName("error_label")
            else:
                lbl.setObjectName("warn_label")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)
            self._val_labels.append(lbl)

        # Show proceed button only if no hard errors
        has_hard_error = any(m.startswith("❌") for m in errors)
        self._proceed_btn.setEnabled(not has_hard_error)

    def _show_error(self, msg: str):
        layout = self._validation_widget.layout()
        lbl = QLabel(msg)
        lbl.setObjectName("error_label")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self._val_labels.append(lbl)

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def _clear(self):
        self.state.data_path = None
        self.state.dataframe  = None
        self.state.validation_errors = []
        self._file_lbl.setText("No file selected")
        self._clear_btn.setVisible(False)
        self._drop_zone.setText(DropZone._IDLE_TEXT)
        self._preview_section.setVisible(False)
        self._clear_validation()

    def refresh(self):
        """Sync UI with current state when page becomes active."""
        if self.state.has_data() and self.state.data_path:
            self._file_lbl.setText(f"📄  {os.path.basename(self.state.data_path)}")
            self._clear_btn.setVisible(True)
            self._drop_zone.setText(f"✅  Loaded: {os.path.basename(self.state.data_path)}")
            self._show_validation(self.state.validation_errors)
            self._populate_table(self.state.dataframe)
