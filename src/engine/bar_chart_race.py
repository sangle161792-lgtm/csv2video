"""
src/engine/bar_chart_race.py
Animated bar-chart race renderer — memory-efficient frame stream.

v2 improvements:
  - 3D bar effect (highlight / shadow / specular layers)
  - Logo/image support per entity (OffsetImage)
  - Fallback letter-badge avatar when no logo is provided
  - Unit label at bottom-left
  - Watermark moved to bottom-right, very subtle
  - Much larger rank numbers
  - Title auto-populated from config
"""


import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
import pandas as pd
import colorsys
import os
from typing import Optional, Callable, Iterator, Tuple, Dict

# ---------------------------------------------------------------------------
DEFAULT_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#C3A6FF",
    "#FFD93D", "#98D8C8", "#FF9A9E", "#6C63FF", "#FDDB92",
    "#A8E6CF", "#FF8C94", "#88D8B0", "#11998E", "#F7DC6F",
]


def _adjust_lightness(hex_color: str, factor: float) -> str:
    """Lighten (factor > 1) or darken (factor < 1) a hex color."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
        hh, l, s = colorsys.rgb_to_hls(r, g, b)
        l = max(0.0, min(1.0, l * factor))
        r2, g2, b2 = colorsys.hls_to_rgb(hh, l, s)
        return f"#{int(r2*255):02x}{int(g2*255):02x}{int(b2*255):02x}"
    except Exception:
        return hex_color


# ---------------------------------------------------------------------------

class BarChartRaceRenderer:
    """
    Generates animated bar-chart race frames from a pandas DataFrame.

    DataFrame layout:
        Column 0  : time axis  (Year, Month, Season …)
        Column 1+ : entity values (numeric)

    Usage:
        r = BarChartRaceRenderer(df, config)
        for frame_bgr, pct, msg in r.iter_frames():
            writer.write(frame_bgr)
    """

    def __init__(
        self,
        df: pd.DataFrame,
        config: dict,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ):
        self.df           = df.copy()
        self.config       = config
        self.progress_cb  = progress_callback

        self.time_col: str  = str(df.columns[0])
        self.entities: list = [str(c) for c in df.columns[1:]]

        # Entity colors
        custom: Dict[str, str] = config.get("colors", {})
        self.entity_colors: Dict[str, str] = {
            e: custom.get(e, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
            for i, e in enumerate(self.entities)
        }

        # Logo paths  (entity -> file path)
        self.logos: Dict[str, str] = config.get("logos", {})

        # Render params
        w, h = config.get("resolution", (1080, 1920))
        self.width:      int   = int(w)
        self.height:     int   = int(h)
        self.dpi:        int   = 100
        self.top_n:      int   = min(int(config.get("top_n", 10)), len(self.entities))
        self.bg_color:   str   = config.get("bg_color", "#0D0D18")
        self.title:      str   = config.get("title", "Bar Chart Race")
        self.watermark:  str   = config.get("watermark", "")
        self.unit_label: str   = config.get("unit_label", "")
        self.fps:        int   = int(config.get("fps", 30))
        self.sps:        float = float(config.get("seconds_per_step", 2.0))
        self.show_logos: bool  = bool(config.get("show_logos", True))
        self.chart_style: str  = str(config.get("chart_style", "Subtle 3D"))

        # Pre-load logos into cache
        self._logo_cache: Dict[str, Optional[np.ndarray]] = {}
        self._preload_logos()

    # ------------------------------------------------------------------
    # Logo loading
    # ------------------------------------------------------------------

    def _preload_logos(self):
        for entity, path in self.logos.items():
            self._logo_cache[entity] = self._load_logo(path)

    @staticmethod
    def _load_logo(path: str) -> Optional[np.ndarray]:
        """Load image, crop to square, resize to 64×64, return RGBA array."""
        if not path or not os.path.exists(path):
            return None
        try:
            from PIL import Image
            img = Image.open(path).convert("RGBA")
            w, h = img.size
            s = min(w, h)
            img = img.crop(((w - s) // 2, (h - s) // 2,
                             (w - s) // 2 + s, (h - s) // 2 + s))
            img = img.resize((64, 64), Image.LANCZOS)
            return np.array(img)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Easing & interpolation
    # ------------------------------------------------------------------

    @staticmethod
    def _ease(t: float) -> float:
        """Cubic ease-in-out."""
        if t < 0.5:
            return 4.0 * t * t * t
        p = 2.0 * t - 2.0
        return 0.5 * p * p * p + 1.0

    def _lerp(self, a: Dict[str, float], b: Dict[str, float], t: float) -> Dict[str, float]:
        et = self._ease(t)
        return {k: a.get(k, 0.0) + (b.get(k, 0.0) - a.get(k, 0.0)) * et
                for k in set(a) | set(b)}

    # ------------------------------------------------------------------
    # 3-D bar drawing
    # ------------------------------------------------------------------

    def _draw_styled_bar(self, ax, x: float, y: float, w: float, h: float, color: str):
        """Draw a horizontal bar matching the selected visual style configuration."""
        if w <= 0:
            return

        style = self.chart_style

        if style == "Classic 2D":
            # Flat solid bar with nice thin border and rounded corners
            ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h,
                                         boxstyle="round,pad=0,rounding_size=0.015",
                                         facecolor=color, alpha=0.95,
                                         edgecolor="white", linewidth=0.5, zorder=2))

        elif style == "Retro Neon":
            # Glow effect (stacking semi-transparent wider rectangles for neon glow)
            glow_color = color
            for glow_w in [1.08, 1.04, 1.02]:
                ax.add_patch(FancyBboxPatch((x - 0.002, y - (h * glow_w) / 2), w + 0.004, h * glow_w,
                                             boxstyle="round,pad=0,rounding_size=0.015",
                                             facecolor=glow_color, alpha=0.08,
                                             linewidth=0, zorder=1))
            # Bright core
            ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h,
                                         boxstyle="round,pad=0,rounding_size=0.015",
                                         facecolor="#FFFFFF", edgecolor=color, linewidth=2.0, zorder=2))

        elif style == "Glassmorphism":
            # Glass semi-transparent look with sharp white specular accent border
            ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h,
                                         boxstyle="round,pad=0,rounding_size=0.015",
                                         facecolor=color, alpha=0.45,
                                         edgecolor="white", linewidth=0.8, zorder=2))
            # Subtle internal specular diagonal reflection
            ax.add_patch(FancyBboxPatch((x, y + h / 4), w, h / 6,
                                         boxstyle="round,pad=0,rounding_size=0.008",
                                         facecolor="white", alpha=0.15,
                                         linewidth=0, zorder=3))

        else:  # "Subtle 3D" (default)
            # ── Main body ───────────────────────────────────────────────
            ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h,
                                         boxstyle="round,pad=0,rounding_size=0.015",
                                         facecolor=color, alpha=0.92,
                                         linewidth=0, zorder=2))

            # ── Top highlight (18 % of height, subtle) ──────────────────
            hl_h = h * 0.22
            ax.add_patch(FancyBboxPatch((x, y + h / 2 - hl_h), w, hl_h,
                                         boxstyle="round,pad=0,rounding_size=0.008",
                                         facecolor="white", alpha=0.13,
                                         linewidth=0, zorder=3))

            # ── Bottom shadow (10 % of height, soft) ────────────────────
            ax.add_patch(FancyBboxPatch((x, y - h / 2), w, h * 0.10,
                                         boxstyle="round,pad=0,rounding_size=0.008",
                                         facecolor="black", alpha=0.15,
                                         linewidth=0, zorder=3))

            # ── Top-edge accent line (thin, low opacity) ─────────────────
            border_color = _adjust_lightness(color, 1.45)
            ax.add_patch(FancyBboxPatch((x, y + h / 2 - h * 0.04), w, h * 0.04,
                                         boxstyle="round,pad=0,rounding_size=0.005",
                                         facecolor=border_color, alpha=0.35,
                                         linewidth=0, zorder=3))

    # ------------------------------------------------------------------
    # Logo overlay
    # ------------------------------------------------------------------

    def _draw_logo(self, ax, img_arr: np.ndarray, x: float, y: float):
        """Render an image (logo) at the given data coordinate."""
        try:
            from matplotlib.offsetbox import OffsetImage, AnnotationBbox
            zoom = max(0.22, min(0.46, 4.0 / max(self.top_n, 1)))
            oi = OffsetImage(img_arr, zoom=zoom, interpolation="lanczos")
            oi.image.axes = ax
            ab = AnnotationBbox(oi, (x, y), frameon=False,
                                xycoords="data", boxcoords="data",
                                zorder=5, pad=0)
            ax.add_artist(ab)
        except Exception:
            pass

    def _draw_avatar_fallback(self, ax, entity: str, color: str,
                              x: float, y: float, font_size: int):
        """
        Fallback avatar when no logo image is available.
        Draws a rounded badge in the entity color with its first letter.
        Works purely with matplotlib text + bbox — no aspect-ratio maths.
        """
        letter = entity[0].upper() if entity else "?"
        ax.text(
            x, y, letter,
            ha="center", va="center",
            color="white",
            fontsize=max(7, int(font_size * 0.75)),
            fontweight="bold",
            zorder=5,
            bbox=dict(
                boxstyle="round,pad=0.28",
                facecolor=color,
                alpha=0.78,
                edgecolor="white",
                linewidth=0.9,
            ),
        )

    # ------------------------------------------------------------------
    # Frame rendering
    # ------------------------------------------------------------------

    def _render(self, values: Dict[str, float], time_label: str) -> np.ndarray:
        """Render one frame → BGR numpy array."""
        fig = plt.figure(
            figsize=(self.width / self.dpi, self.height / self.dpi),
            dpi=self.dpi,
        )
        fig.patch.set_facecolor(self.bg_color)

        # ── Mobile & TikTok/Shorts Safe Zone Margin Setup ───────────────────
        # Left/Right safe margins: 14% to 86% (X-axis co-ordinates)
        # Top/Bottom: we reserve 0.19 at the top (for title) and 0.08 at the bottom.
        # Height of chart is 0.73
        ax = fig.add_axes([0.14, 0.08, 0.72, 0.73])
        ax.set_facecolor(self.bg_color)
        ax.tick_params(left=False, bottom=False,
                       labelleft=False, labelbottom=False)
        for sp in ax.spines.values():
            sp.set_visible(False)

        # Configure high-quality modern sans-serif fonts natively supported on Windows and popular systems
        plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Inter', 'Outfit', 'Helvetica', 'Arial', 'sans-serif']
        plt.rcParams['font.family'] = 'sans-serif'

        # ── Interpolate Rank Positions for Smooth Vertical Movement ──
        all_sorted = sorted(
            [(e, float(values.get(e, 0))) for e in self.entities],
            key=lambda x: x[1], reverse=True
        )
        
        entity_target_y = {}
        for rank_idx, (entity, val) in enumerate(all_sorted):
            entity_target_y[entity] = self.top_n - 1 - rank_idx

        sorted_items = all_sorted[: self.top_n]
        n = len(sorted_items)
        if n == 0:
            plt.close(fig)
            return np.zeros((self.height, self.width, 3), dtype=np.uint8)

        max_val = max(v for _, v in sorted_items) or 1.0

        # ── Premium Safe-Zone Coordinates ──
        # Left edge of rank, logo, name and bar start exactly at BAR_L = 0.015
        # Right edge of bar and value ends exactly at BAR_L + BAR_W = 0.985
        RANK_X = 0.015
        
        if self.show_logos:
            LOGO_X = 0.080
            NAME_L = 0.140   # Shift name right to avoid overlap with rank/logo
            BAR_L  = 0.015
            BAR_W  = 0.970
        else:
            LOGO_X = None
            NAME_L = 0.015   # Aligns name exactly with left edge of bar (no logo/rank shown)
            BAR_L  = 0.015
            BAR_W  = 0.970

        # Premium typography settings matching the reference image
        font_config = {"fontweight": "semibold"}
        
        # Adaptive font sizes optimized for vertical layout readability
        nf       = max(n, 3)
        rank_fs  = max(12, min(16, int(160 / nf)))
        name_fs  = max(14, min(22, int(200 / nf)))
        val_fs   = max(14, min(22, int(200 / nf)))

        for rank, (entity, val) in enumerate(sorted_items):
            y     = entity_target_y[entity]
            color = self.entity_colors.get(entity, "#7C7CFF")
            bw    = (val / max_val) * BAR_W if max_val > 0 else 0.0

            # 1. Background Bar (Sleek dark track behind the active bar, like the image)
            # Center of the bar is at y - 0.20, height is 0.24, rounded corners
            BAR_H = 0.24
            y_bar = y - 0.20
            ax.add_patch(FancyBboxPatch((BAR_L, y_bar - BAR_H / 2), BAR_W, BAR_H,
                                         boxstyle="round,pad=0,rounding_size=0.015",
                                         facecolor="#1A1F2C", alpha=0.85,
                                         linewidth=0, zorder=1))

            # 2. Styled Active Bar (Placed perfectly centered at y_bar, matching background bar)
            self._draw_styled_bar(ax, BAR_L, y_bar, bw, BAR_H, color)

            # 3. Rank number (#1, #2...) - muted slate gray, left aligned (only if show_logos is True)
            if self.show_logos:
                ax.text(RANK_X, y + 0.16, f"#{rank + 1}",
                        ha="left", va="center",
                        color="#475569", fontsize=rank_fs, zorder=6, **font_config)

            # 4. Avatar (Only drawn if show_logos is True)
            if self.show_logos:
                logo_img = self._logo_cache.get(entity)
                if logo_img is not None:
                    self._draw_logo(ax, logo_img, LOGO_X, y + 0.16)
                else:
                    self._draw_avatar_fallback(ax, entity, color, LOGO_X, y + 0.16, name_fs)

            # 5. Entity name - left-aligned above the bar, bright white, clean sans-serif
            # Prefix with order (e.g. "1. Arsenal") when logos are disabled for an ultra clean look
            display_name = f"{rank + 1}. {entity}" if not self.show_logos else entity
            ax.text(NAME_L, y + 0.16, display_name,
                    ha="left", va="center",
                    color="#FFFFFF", fontsize=name_fs, zorder=6, **font_config)

            # 6. Value - right-aligned above the bar, bold
            val_str = f"{val:,.0f}" if val >= 1 else f"{val:.2f}"
            ax.text(BAR_L + BAR_W - 0.015, y + 0.16, val_str,
                    ha="right", va="center",
                    color="#FFFFFF", fontsize=val_fs, zorder=6, **font_config)

        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(-0.75, self.top_n - 0.25)

        # ── Premium Stacked Header (Brings title and chart closer together with perfect proportions) ──
        # Small Category subtitle - elegant light blue/cyan uppercase (Y shifted to 0.93)
        spaced_title = "   ".join(list(self.title.upper()))
        fig.text(0.50, 0.93, spaced_title,
                 ha="center", va="center",
                 color="#38BDF8", fontsize=15, fontweight="bold")

        # Big bold title: "Thứ hạng qua từng vòng" (Y shifted to 0.89)
        fig.text(0.50, 0.89, "Thứ hạng qua từng vòng",
                 ha="center", va="center",
                 color="#FFFFFF", fontsize=32, fontweight="bold")

        # Bottom dynamic subtitle: "Bảng xếp hạng sau vòng X" (Y shifted to 0.85)
        fig.text(0.50, 0.85, f"Bảng xếp hạng sau vòng {time_label}",
                 ha="center", va="center",
                 color="#94A3B8", fontsize=18, fontweight="normal")

        # ── Watermark & Unit label (bottom safe zone) ───────────────────────
        if self.unit_label:
            fig.text(0.50, 0.04, f"● {self.unit_label}",
                     ha="center", va="center",
                     color="#64748B", fontsize=11, fontweight="semibold")

        if self.watermark:
            fig.text(0.50, 0.02, self.watermark,
                     ha="center", va="center",
                     color="#334155", fontsize=9, fontweight="bold")

        # ── Convert to BGR numpy array ──────────────────────────────
        fig.canvas.draw()
        try:
            buf    = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            wp, hp = fig.canvas.get_width_height()
            img_rgb = buf.reshape(hp, wp, 3)
        except AttributeError:
            rgba   = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
            wp, hp = fig.canvas.get_width_height()
            img_rgb = rgba.reshape(hp, wp, 4)[:, :, :3]

        plt.close(fig)
        return img_rgb[:, :, ::-1].copy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def estimate_frame_count(self) -> int:
        n = len(self.df) + 1  # Add 1 for Round 0
        tf = max(1, int(self.fps * self.sps))
        return int(self.fps * 0.8) + (n - 1) * tf + int(self.fps * 1.2)

    def iter_frames(self) -> Iterator[Tuple[np.ndarray, int, str]]:
        """Yield (bgr_frame, progress_pct, status_msg) one at a time."""
        rows = []
        
        # ── Prepend 'Round 0' / 'Vòng 0' where all entities have 0 points ──
        round_0_label = "0"
        # Try to infer format of first column (if numeric, use 0. If string, "0")
        try:
            first_val = self.df.iloc[0, 0]
            if isinstance(first_val, (int, float, np.integer, np.floating)):
                round_0_label = type(first_val)(0)
        except Exception:
            pass
            
        round_0_vals = {e: 0.0 for e in self.entities}
        rows.append((round_0_label, round_0_vals))
        
        for _, row in self.df.iterrows():
            vals = {e: float(row.get(e, 0)) for e in self.entities}
            rows.append((row[self.time_col], vals))

        if len(rows) <= 1:
            return

        tf         = max(1, int(self.fps * self.sps))
        hold_start = int(self.fps * 0.8)
        hold_end   = int(self.fps * 1.2)
        total      = hold_start + (len(rows) - 1) * tf + hold_end
        done       = 0

        def _emit(frame, pct, msg):
            nonlocal done
            if self.progress_cb:
                self.progress_cb(pct, msg)
            return frame, pct, msg

        first = self._render(rows[0][1], str(rows[0][0]))
        for _ in range(hold_start):
            done += 1
            yield _emit(first, int(done / total * 100), f"Frame {done}/{total}")

        for i in range(len(rows) - 1):
            lbl_a, vals_a = rows[i]
            lbl_b, vals_b = rows[i + 1]
            for f in range(tf):
                t      = f / tf
                interp = self._lerp(vals_a, vals_b, t)
                label  = lbl_b if t >= 0.5 else lbl_a
                frame  = self._render(interp, str(label))
                done  += 1
                yield _emit(frame, int(done / total * 100), f"Frame {done}/{total}")

        last = self._render(rows[-1][1], str(rows[-1][0]))
        for _ in range(hold_end):
            done += 1
            yield _emit(last, int(done / total * 100), f"Frame {done}/{total}")
