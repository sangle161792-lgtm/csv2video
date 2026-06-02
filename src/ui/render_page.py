"""
src/ui/render_page.py
Render page — start a render job, watch real-time progress, download the result.

The render runs in a QThread so the UI stays responsive.
Progress is streamed frame-by-frame via Qt signals.
"""

import os
import time
import datetime
import traceback

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QProgressBar, QPlainTextEdit,
    QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


# ---------------------------------------------------------------------------
# Background render thread
# ---------------------------------------------------------------------------

class RenderThread(QThread):
    """
    Runs the full render pipeline off the main thread.

    Signals:
        progress(int)       — 0–100
        status(str)         — human-readable status line
        finished(str)       — output file path
        failed(str)         — error traceback
    """
    progress = pyqtSignal(int)
    status   = pyqtSignal(str)
    finished = pyqtSignal(str)
    failed   = pyqtSignal(str)

    def __init__(self, dataframe, config: dict, output_path: str):
        super().__init__()
        self.dataframe   = dataframe
        self.config      = config
        self.output_path = output_path
        self._abort      = False

    def abort(self):
        self._abort = True

    def run(self):
        try:
            from src.engine.bar_chart_race import BarChartRaceRenderer
            from src.engine.video_encoder  import VideoEncoder

            self.status.emit("⏳  Initialising renderer…")

            renderer = BarChartRaceRenderer(
                self.dataframe,
                self.config,
            )

            w, h = self.config.get("resolution", (1080, 1920))
            fps  = int(self.config.get("fps", 30))

            encoder = VideoEncoder()

            self.status.emit("🎨  Generating frames…")

            def _on_progress(pct: int, msg: str):
                if self._abort:
                    raise InterruptedError("Render aborted by user.")
                self.progress.emit(pct)
                self.status.emit(f"🎨  {msg}")

            encoder.encode(
                frame_iter   = renderer.iter_frames(),
                output_path  = self.output_path,
                fps          = fps,
                width        = w,
                height       = h,
                on_progress  = _on_progress,
            )

            self.progress.emit(100)
            self.status.emit("✅  Render complete!")
            self.finished.emit(self.output_path)

        except InterruptedError:
            self.status.emit("🛑  Render aborted.")
            self.failed.emit("Aborted by user.")

        except Exception:
            tb = traceback.format_exc()
            self.status.emit("❌  Render failed.")
            self.failed.emit(tb)


# ---------------------------------------------------------------------------
# Render page
# ---------------------------------------------------------------------------

class RenderPage(QWidget):

    def __init__(self, state, main_window):
        super().__init__()
        self.state   = state
        self.mw      = main_window
        self._thread: RenderThread | None = None
        self._start_time: float = 0.0
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
        title = QLabel("Render Video")
        title.setObjectName("page_title")
        vbox.addWidget(title)

        sub = QLabel(
            "Review your settings below, then click Render.  "
            "The progress bar updates frame-by-frame."
        )
        sub.setObjectName("page_subtitle")
        sub.setWordWrap(True)
        vbox.addWidget(sub)

        vbox.addSpacing(28)

        # ── Summary card ──────────────────────────────────────────────
        self._summary_card = QFrame()
        self._summary_card.setObjectName("stat_card")
        sc_layout = QVBoxLayout(self._summary_card)
        sc_layout.setContentsMargins(20, 16, 20, 16)
        sc_layout.setSpacing(8)

        self._summary_lbl = QLabel("Load data and configure settings to see summary.")
        self._summary_lbl.setObjectName("hint_label")
        self._summary_lbl.setWordWrap(True)
        self._summary_lbl.setTextFormat(Qt.TextFormat.RichText)
        sc_layout.addWidget(self._summary_lbl)

        vbox.addWidget(self._summary_card)
        vbox.addSpacing(24)

        # ── Render button + abort ─────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._render_btn = QPushButton("🚀   Render Current Style")
        self._render_btn.setObjectName("render_btn")
        self._render_btn.setMinimumHeight(58)
        self._render_btn.clicked.connect(self._start_render)
        btn_row.addWidget(self._render_btn)

        self._batch_btn = QPushButton("🎬   Batch Render (All 4 Styles)")
        self._batch_btn.setObjectName("render_btn") # Green/indigo gradients styling
        self._batch_btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #3B82F6);")
        self._batch_btn.setMinimumHeight(58)
        self._batch_btn.clicked.connect(self._start_batch_render)
        btn_row.addWidget(self._batch_btn)

        self._abort_btn = QPushButton("🛑  Abort")
        self._abort_btn.setObjectName("action_btn_secondary")
        self._abort_btn.setMinimumHeight(58)
        self._abort_btn.setFixedWidth(120)
        self._abort_btn.clicked.connect(self._abort)
        self._abort_btn.setEnabled(False)
        btn_row.addWidget(self._abort_btn)

        vbox.addLayout(btn_row)
        vbox.addSpacing(20)

        # ── Progress ──────────────────────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        vbox.addWidget(self._progress_bar)

        vbox.addSpacing(8)

        self._status_lbl = QLabel("Ready.")
        self._status_lbl.setObjectName("status_label")
        vbox.addWidget(self._status_lbl)

        vbox.addSpacing(20)

        # ── Result card (hidden until done) ───────────────────────────
        self._result_card = QFrame()
        self._result_card.setObjectName("stat_card")
        self._result_card.setVisible(False)
        res_layout = QVBoxLayout(self._result_card)
        res_layout.setContentsMargins(20, 16, 20, 16)
        res_layout.setSpacing(10)

        self._result_lbl = QLabel()
        self._result_lbl.setObjectName("success_label")
        self._result_lbl.setWordWrap(True)
        self._result_lbl.setTextFormat(Qt.TextFormat.RichText)
        res_layout.addWidget(self._result_lbl)

        res_btns = QHBoxLayout()
        res_btns.setSpacing(12)

        self._open_file_btn = QPushButton("▶   Play Video")
        self._open_file_btn.setObjectName("open_btn")
        self._open_file_btn.setMinimumHeight(44)
        self._open_file_btn.clicked.connect(self._open_file)
        res_btns.addWidget(self._open_file_btn)

        self._open_folder_btn = QPushButton("📁   Open Folder")
        self._open_folder_btn.setObjectName("action_btn_secondary")
        self._open_folder_btn.setMinimumHeight(44)
        self._open_folder_btn.clicked.connect(self._open_folder)
        res_btns.addWidget(self._open_folder_btn)

        res_btns.addStretch()
        res_layout.addLayout(res_btns)
        vbox.addWidget(self._result_card)
        vbox.addSpacing(20)

        # ── Log output ────────────────────────────────────────────────
        log_lbl = QLabel("Render Log")
        log_lbl.setObjectName("section_title")
        vbox.addWidget(log_lbl)
        vbox.addSpacing(6)

        self._log = QPlainTextEdit()
        self._log.setObjectName("log_area")
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(160)
        self._log.setMaximumHeight(260)
        vbox.addWidget(self._log)

        vbox.addStretch()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _update_summary(self):
        state = self.state
        if not state.has_data():
            self._summary_lbl.setText(
                "⚠️  No data loaded. Go to <b>Import Data</b> first."
            )
            self._render_btn.setEnabled(False)
            self._batch_btn.setEnabled(False)
            return

        cfg  = state.config
        rows = len(state.dataframe)
        w, h = cfg.get("resolution", (1080, 1920))
        fps  = cfg.get("fps", 30)
        sps  = cfg.get("seconds_per_step", 2.0)
        top_n = cfg.get("top_n", 10)
        entities = state.get_entities()

        total_s = (rows - 1) * sps + 2.0
        mins, secs = divmod(int(total_s), 60)
        dur_str = f"{mins}m {secs}s" if mins else f"{secs}s"

        self._summary_lbl.setText(
            f"<b>Title:</b> {cfg.get('title', '—')}  &nbsp;·&nbsp;  "
            f"<b>Resolution:</b> {w}×{h}  &nbsp;·&nbsp;  "
            f"<b>FPS:</b> {fps}  &nbsp;·&nbsp;  "
            f"<b>Duration:</b> ~{dur_str}  &nbsp;·&nbsp;  "
            f"<b>Rows:</b> {rows}  &nbsp;·&nbsp;  "
            f"<b>Entities:</b> {len(entities)}  &nbsp;·&nbsp;  "
            f"<b>Top N:</b> {top_n}"
        )
        self._render_btn.setEnabled(True)
        self._batch_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Render control
    # ------------------------------------------------------------------

    def _output_path(self, style_suffix: str = "") -> str:
        os.makedirs("output", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        title = self.state.config.get("title", "render").replace(" ", "_")
        # Sanitise
        safe = "".join(c if c.isalnum() or c in "_-" else "" for c in title)[:30]
        suffix = f"_{style_suffix.replace(' ', '_')}" if style_suffix else ""
        return os.path.abspath(os.path.join("output", f"{safe}{suffix}_{ts}.mp4"))

    def _start_render(self):
        if not self.state.has_data():
            return

        # Save settings before render
        settings_page = self.mw._pages.get("settings")
        if settings_page and hasattr(settings_page, "_save"):
            settings_page._save()

        self._log.clear()
        self._result_card.setVisible(False)
        self._progress_bar.setValue(0)
        self._render_btn.setEnabled(False)
        self._batch_btn.setEnabled(False)
        self._abort_btn.setEnabled(True)
        self._start_time = time.time()

        out = self._output_path()
        self._log_line(f"Output: {out}")
        self._log_line(f"Started: {datetime.datetime.now().strftime('%H:%M:%S')}")
        self._log_line("─" * 50)

        self._thread = RenderThread(
            dataframe   = self.state.dataframe.copy(),
            config      = dict(self.state.config),
            output_path = out,
        )
        self._thread.progress.connect(self._on_progress)
        self._thread.status.connect(self._on_status)
        self._thread.finished.connect(self._on_finished)
        self._thread.failed.connect(self._on_failed)
        self._thread.start()

    def _start_batch_render(self):
        """Runs the queue to sequentially render all 4 visual styles in background."""
        if not self.state.has_data():
            return

        # Save settings before render
        settings_page = self.mw._pages.get("settings")
        if settings_page and hasattr(settings_page, "_save"):
            settings_page._save()

        self._log.clear()
        self._result_card.setVisible(False)
        self._progress_bar.setValue(0)
        self._render_btn.setEnabled(False)
        self._batch_btn.setEnabled(False)
        self._abort_btn.setEnabled(True)
        self._start_time = time.time()
        
        self._batch_queue = ["Subtle 3D", "Classic 2D", "Retro Neon", "Glassmorphism"]
        self._batch_outputs = []
        self._log_line("🚀   Batch Render Queue started! Preparing all 4 styles...")
        self._log_line("─" * 50)
        self._run_next_batch_item()

    def _run_next_batch_item(self):
        if not hasattr(self, "_batch_queue") or not self._batch_queue:
            # Batch render completed!
            self._on_batch_complete()
            return

        style = self._batch_queue.pop(0)
        self._log_line(f"\n🎬   [Queue] Rendering style: {style}...")
        
        # Configure temporary config for this style
        cfg = dict(self.state.config)
        cfg["chart_style"] = style
        out = self._output_path(style)
        
        self._thread = RenderThread(
            dataframe   = self.state.dataframe.copy(),
            config      = cfg,
            output_path = out,
        )
        
        # Intermediate callbacks
        self._thread.progress.connect(self._on_progress)
        self._thread.status.connect(self._on_status)
        self._thread.failed.connect(self._on_failed)
        
        # Connect finish to trigger next item
        def _on_item_finished(path: str):
            self._batch_outputs.append(path)
            self._log_line(f"✅   Finished style: {style} -> {os.path.basename(path)}")
            # Clean up current thread ref
            self._thread.disconnect()
            self._thread = None
            self._run_next_batch_item()

        self._thread.finished.connect(_on_item_finished)
        self._thread.start()

    def _on_batch_complete(self):
        elapsed = time.time() - self._start_time
        self._abort_btn.setEnabled(False)
        self._render_btn.setEnabled(True)
        self._batch_btn.setEnabled(True)
        self._progress_bar.setValue(100)

        self._result_card.setVisible(True)
        self.state.output_path = self._batch_outputs[-1] if self._batch_outputs else None
        for path in self._batch_outputs:
            self.state.recent_outputs.append(path)

        styles_rendered_html = "<br>".join([f"· <tt>{os.path.basename(p)}</tt>" for p in self._batch_outputs])
        self._result_lbl.setText(
            f"✅  <b>Batch Render complete!</b><br>"
            f"Rendered all 4 styles in {elapsed:.1f}s!<br>"
            f"Files generated:<br>{styles_rendered_html}"
        )
        self._status_lbl.setText("✅  All 4 styles rendered successfully!")
        self._log_line("─" * 50)
        self._log_line(f"🎉   All 4 styles complete! Total time: {elapsed:.1f}s.")

    def _abort(self):
        if hasattr(self, "_batch_queue"):
            self._batch_queue.clear()
        if self._thread and self._thread.isRunning():
            self._thread.abort()
            self._log_line("Abort requested…")
            self._abort_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Thread callbacks
    # ------------------------------------------------------------------

    def _on_progress(self, pct: int):
        self._progress_bar.setValue(pct)

    def _on_status(self, msg: str):
        self._status_lbl.setText(msg)
        self._log_line(msg)

    def _on_finished(self, path: str):
        elapsed = time.time() - self._start_time
        size_mb = os.path.getsize(path) / (1024 * 1024)

        self.state.output_path = path
        self.state.recent_outputs.append(path)

        self._abort_btn.setEnabled(False)
        self._render_btn.setEnabled(True)
        self._progress_bar.setValue(100)

        self._result_card.setVisible(True)
        self._result_lbl.setText(
            f"✅  <b>Render complete!</b><br>"
            f"File: <tt>{os.path.basename(path)}</tt>  &nbsp;·&nbsp;  "
            f"Size: {size_mb:.1f} MB  &nbsp;·&nbsp;  "
            f"Time: {elapsed:.1f}s"
        )

        self._log_line("─" * 50)
        self._log_line(f"Done in {elapsed:.1f}s  —  {size_mb:.1f} MB  —  {path}")

    def _on_failed(self, tb: str):
        self._abort_btn.setEnabled(False)
        self._render_btn.setEnabled(True)
        self._status_lbl.setText("❌  Render failed. See log for details.")
        self._log_line("─" * 50)
        self._log_line("ERROR:\n" + tb)

    def _log_line(self, msg: str):
        self._log.appendPlainText(msg)
        self._log.verticalScrollBar().setValue(
            self._log.verticalScrollBar().maximum()
        )

    # ------------------------------------------------------------------
    # Output actions
    # ------------------------------------------------------------------

    def _open_file(self):
        if self.state.output_path and os.path.exists(self.state.output_path):
            os.startfile(self.state.output_path)

    def _open_folder(self):
        path = os.path.abspath("output")
        os.makedirs(path, exist_ok=True)
        os.startfile(path)

    # ------------------------------------------------------------------
    def refresh(self):
        self._update_summary()
