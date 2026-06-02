"""
src/ui/settings_page.py
Settings page — configure all render parameters.

v2 additions:
  - Title input (auto-populated from CSV filename)
  - Unit Label input  (e.g. "Million people", "Points")
  - Logo upload per entity (next to color picker)
  - Logo preview showing filename
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFormLayout,
    QScrollArea, QColorDialog, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


# ---------------------------------------------------------------------------
# Color picker button
# ---------------------------------------------------------------------------

class ColorButton(QPushButton):
    def __init__(self, hex_color: str = "#7C3AED", parent=None):
        super().__init__(parent)
        self.setObjectName("color_btn")
        self.setFixedSize(68, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_color(hex_color)
        self.clicked.connect(self._pick)

    def set_color(self, hex_color: str):
        self._hex = hex_color
        self.setStyleSheet(
            f"background-color: {hex_color}; border: 2px solid #3D3D52; border-radius: 6px;"
        )
        self.setToolTip(hex_color)

    def get_color(self) -> str:
        return self._hex

    def _pick(self):
        dlg = QColorDialog(QColor(self._hex), self)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        if dlg.exec():
            self.set_color(dlg.currentColor().name())


# ---------------------------------------------------------------------------
# Settings page
# ---------------------------------------------------------------------------

class SettingsPage(QWidget):

    RESOLUTIONS = {
        "1080 × 1920  (Full HD Portrait — TikTok/Shorts)": (1080, 1920),
        "720 × 1280   (HD Portrait)":                      ( 720, 1280),
        "1080 × 1080  (Square)":                           (1080, 1080),
    }
    FPS_OPTIONS = [24, 30, 60]

    def __init__(self, state, main_window):
        super().__init__()
        self.state = state
        self.mw    = main_window
        self._color_btns:    dict[str, ColorButton] = {}
        self._logo_btns:     dict[str, QPushButton] = {}
        self._logo_previews: dict[str, QLabel]      = {}
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

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
        title = QLabel("Settings")
        title.setObjectName("page_title")
        vbox.addWidget(title)

        sub = QLabel("Configure how your video will look and how long it will be.")
        sub.setObjectName("page_subtitle")
        vbox.addWidget(sub)
        vbox.addSpacing(28)

        # ── Two columns ───────────────────────────────────────────────
        cols = QHBoxLayout()
        cols.setSpacing(24)
        cols.setAlignment(Qt.AlignmentFlag.AlignTop)
        cols.addWidget(self._build_left_col(),  stretch=1)
        cols.addWidget(self._build_right_col(), stretch=1)
        vbox.addLayout(cols)
        vbox.addSpacing(24)

        # ── Save / Render row ─────────────────────────────────────────
        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾  Save Settings")
        save_btn.setObjectName("action_btn_secondary")
        save_btn.setMinimumHeight(46)
        save_btn.clicked.connect(self._save)

        render_btn = QPushButton("🎬  Go to Render  →")
        render_btn.setObjectName("action_btn")
        render_btn.setMinimumHeight(46)
        render_btn.setFixedWidth(220)
        render_btn.clicked.connect(lambda: self.mw.navigate_to("render"))

        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        btn_row.addWidget(render_btn)
        vbox.addLayout(btn_row)
        vbox.addSpacing(32)

        # ── Entity section (colors + logos) — dynamic ─────────────────
        self._entities_group = QGroupBox("Entity Colors & Logos")
        self._entities_vbox  = QVBoxLayout(self._entities_group)
        self._entities_vbox.setSpacing(8)
        self._entities_vbox.setContentsMargins(14, 18, 14, 14)

        header_row = QHBoxLayout()
        h_name  = QLabel("Entity")
        h_color = QLabel("Color")
        h_logo  = QLabel("Logo (optional)")
        for lbl in (h_name, h_color, h_logo):
            lbl.setObjectName("form_label")
        h_name.setFixedWidth(148)
        h_color.setFixedWidth(80)
        header_row.addWidget(h_name)
        header_row.addWidget(h_color)
        header_row.addSpacing(8)
        header_row.addWidget(h_logo)
        header_row.addStretch()
        self._entities_vbox.addLayout(header_row)

        sep = QFrame()
        sep.setObjectName("divider")
        self._entities_vbox.addWidget(sep)

        self._entities_placeholder = QLabel(
            "Load data first to configure per-entity colors and logos."
        )
        self._entities_placeholder.setObjectName("hint_label")
        self._entities_vbox.addWidget(self._entities_placeholder)

        vbox.addWidget(self._entities_group)
        vbox.addStretch()

    # ------------------------------------------------------------------
    def _build_left_col(self) -> QGroupBox:
        box = QGroupBox("Video & Content")
        form = QFormLayout(box)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setContentsMargins(16, 20, 16, 20)

        # Title — auto-populated from CSV filename
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("e.g. Premier League Race 1993–2026")
        form.addRow(self._make_lbl("Title"), self._title_edit)

        title_hint = QLabel("Auto-filled from CSV filename — edit freely.")
        title_hint.setObjectName("hint_label")
        form.addRow("", title_hint)

        # Unit label
        self._unit_edit = QLineEdit()
        self._unit_edit.setPlaceholderText("e.g. Million people · Points · USD Billion")
        form.addRow(self._make_lbl("Unit Label"), self._unit_edit)

        unit_hint = QLabel("Shown at bottom-left corner of video.")
        unit_hint.setObjectName("hint_label")
        form.addRow("", unit_hint)

        # Watermark
        self._watermark_edit = QLineEdit()
        self._watermark_edit.setPlaceholderText("e.g. @YourChannel  (leave blank to hide)")
        form.addRow(self._make_lbl("Watermark"), self._watermark_edit)

        # Resolution
        self._res_combo = QComboBox()
        for label in self.RESOLUTIONS:
            self._res_combo.addItem(label)
        form.addRow(self._make_lbl("Resolution"), self._res_combo)

        # FPS
        self._fps_combo = QComboBox()
        for fps in self.FPS_OPTIONS:
            self._fps_combo.addItem(f"{fps} FPS")
        form.addRow(self._make_lbl("Frame Rate"), self._fps_combo)

        # Seconds per step
        self._sps_spin = QDoubleSpinBox()
        self._sps_spin.setRange(0.5, 12.0)
        self._sps_spin.setSingleStep(0.5)
        self._sps_spin.setSuffix("  sec / step")
        self._sps_spin.setDecimals(1)
        self._sps_spin.valueChanged.connect(self._update_duration_label)
        form.addRow(self._make_lbl("Step Duration"), self._sps_spin)

        hint = QLabel("Total length ≈ (rows − 1) × step duration")
        hint.setObjectName("hint_label")
        form.addRow("", hint)

        return box

    def _build_right_col(self) -> QGroupBox:
        box = QGroupBox("Appearance")
        form = QFormLayout(box)
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setContentsMargins(16, 20, 16, 20)

        # Background color
        self._bg_btn = ColorButton("#0D0D18")
        form.addRow(self._make_lbl("Background"), self._bg_btn)

        # Top N
        self._topn_spin = QSpinBox()
        self._topn_spin.setRange(3, 20)
        self._topn_spin.setSuffix("  entries visible")
        self._topn_spin.valueChanged.connect(self._update_duration_label)
        form.addRow(self._make_lbl("Show Top"), self._topn_spin)

        # Show Logos Toggle
        from PyQt6.QtWidgets import QCheckBox
        self._logos_check = QCheckBox("Show Logos & Badges")
        self._logos_check.setCursor(Qt.CursorShape.PointingHandCursor)
        form.addRow(self._make_lbl("Avatars"), self._logos_check)

        # Chart Style Selector
        self._style_combo = QComboBox()
        self._style_options = ["Subtle 3D", "Classic 2D", "Retro Neon", "Glassmorphism"]
        for opt in self._style_options:
            self._style_combo.addItem(opt)
        form.addRow(self._make_lbl("Bar Style"), self._style_combo)

        # Estimated duration (read-only)
        self._duration_lbl = QLabel("—")
        self._duration_lbl.setObjectName("hint_label")
        form.addRow(self._make_lbl("Est. Duration"), self._duration_lbl)

        return box

    @staticmethod
    def _make_lbl(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("form_label")
        return lbl

    # ------------------------------------------------------------------
    # Entity rows  (colors + logos)
    # ------------------------------------------------------------------

    def _rebuild_entity_rows(self):
        """Recreate one row per entity with color + logo controls."""
        # 1. Properly delete and clear any previously added dynamic row widgets
        if not hasattr(self, "_dynamic_rows"):
            self._dynamic_rows = []
            
        for w in self._dynamic_rows:
            try:
                w.setParent(None)
                w.deleteLater()
            except Exception:
                pass
        self._dynamic_rows.clear()
        self._color_btns.clear()
        self._logo_btns.clear()
        self._logo_previews.clear()

        entities = self.state.get_entities()
        self._entities_placeholder.setVisible(not entities)
        if not entities:
            return

        from src.engine.bar_chart_race import DEFAULT_COLORS
        existing_colors = self.state.config.get("colors", {})
        existing_logos  = self.state.config.get("logos",  {})

        for i, entity in enumerate(entities):
            hex_color  = existing_colors.get(entity, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
            logo_path  = existing_logos.get(entity, "")

            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)

            # Entity name
            name_lbl = QLabel(entity)
            name_lbl.setFixedWidth(148)
            row.addWidget(name_lbl)

            # Color button
            color_btn = ColorButton(hex_color)
            self._color_btns[entity] = color_btn
            row.addWidget(color_btn)

            row.addSpacing(8)

            # Logo pick button
            logo_btn = QPushButton("📷  Browse…")
            logo_btn.setObjectName("action_btn_secondary")
            logo_btn.setFixedSize(100, 30)
            logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            logo_btn.clicked.connect(lambda _, e=entity: self._pick_logo(e))
            self._logo_btns[entity] = logo_btn
            row.addWidget(logo_btn)

            # Logo preview label
            logo_preview = QLabel(
                f"✅ {os.path.basename(logo_path)[:18]}" if logo_path else "—  no logo"
            )
            logo_preview.setObjectName("hint_label")
            logo_preview.setFixedWidth(160)
            self._logo_previews[entity] = logo_preview
            row.addWidget(logo_preview)

            # Clear logo button
            clear_btn = QPushButton("✕")
            clear_btn.setObjectName("action_btn_secondary")
            clear_btn.setFixedSize(28, 28)
            clear_btn.setToolTip(f"Remove logo for {entity}")
            clear_btn.clicked.connect(lambda _, e=entity: self._clear_logo(e))
            row.addWidget(clear_btn)

            row.addStretch()
            self._entities_vbox.addWidget(row_widget)
            self._dynamic_rows.append(row_widget)

    def _pick_logo(self, entity: str):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select logo for: {entity}",
            os.path.expanduser("~"),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.ico *.gif)",
        )
        if path:
            self.state.config.setdefault("logos", {})[entity] = path
            self._logo_previews[entity].setText(f"✅ {os.path.basename(path)[:18]}")

    def _clear_logo(self, entity: str):
        self.state.config.setdefault("logos", {}).pop(entity, None)
        self._logo_previews[entity].setText("—  no logo")

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load_config_to_ui(self):
        cfg = self.state.config

        self._title_edit.setText(cfg.get("title", ""))
        self._unit_edit.setText(cfg.get("unit_label", ""))
        self._watermark_edit.setText(cfg.get("watermark", ""))

        # Resolution
        w, h = cfg.get("resolution", (1080, 1920))
        for i, wh in enumerate(self.RESOLUTIONS.values()):
            if wh == (w, h):
                self._res_combo.setCurrentIndex(i)
                break

        # FPS
        fps = cfg.get("fps", 30)
        for i, f in enumerate(self.FPS_OPTIONS):
            if f == fps:
                self._fps_combo.setCurrentIndex(i)
                break

        self._sps_spin.setValue(cfg.get("seconds_per_step", 2.0))
        self._bg_btn.set_color(cfg.get("bg_color", "#0D0D18"))
        self._topn_spin.setValue(cfg.get("top_n", 10))
        self._logos_check.setChecked(cfg.get("show_logos", True))

        # Sync style combo box
        cur_style = cfg.get("chart_style", "Subtle 3D")
        if cur_style in self._style_options:
            self._style_combo.setCurrentIndex(self._style_options.index(cur_style))

        self._update_duration_label()

    def _save(self):
        cfg = self.state.config
        cfg["title"]            = self._title_edit.text().strip() or "Bar Chart Race"
        cfg["unit_label"]       = self._unit_edit.text().strip()
        cfg["watermark"]        = self._watermark_edit.text().strip()
        cfg["resolution"]       = list(self.RESOLUTIONS.values())[self._res_combo.currentIndex()]
        cfg["fps"]              = self.FPS_OPTIONS[self._fps_combo.currentIndex()]
        cfg["seconds_per_step"] = self._sps_spin.value()
        cfg["bg_color"]         = self._bg_btn.get_color()
        cfg["top_n"]            = self._topn_spin.value()
        cfg["show_logos"]       = self._logos_check.isChecked()
        cfg["chart_style"]      = self._style_options[self._style_combo.currentIndex()]
        cfg["colors"]           = {e: b.get_color() for e, b in self._color_btns.items()}
        # logos already updated in real-time by _pick_logo / _clear_logo

        self.state.save_config()
        self._update_duration_label()

        from PyQt6.QtWidgets import QToolTip
        from PyQt6.QtGui import QCursor
        QToolTip.showText(QCursor.pos(), "✅  Settings saved!", self)

    def _update_duration_label(self):
        if not self.state.has_data():
            self._duration_lbl.setText("—  (no data loaded)")
            return
        rows  = len(self.state.dataframe)
        fps   = self.FPS_OPTIONS[self._fps_combo.currentIndex()]
        sps   = self._sps_spin.value()
        total = (rows - 1) * sps + 2.0
        mins, secs = divmod(int(total), 60)
        frames = int(total * fps)
        self._duration_lbl.setText(
            f"{mins}m {secs}s  (~{frames} frames)" if mins else f"{secs}s  (~{frames} frames)"
        )

    # ------------------------------------------------------------------
    def refresh(self):
        self._load_config_to_ui()
        self._rebuild_entity_rows()
