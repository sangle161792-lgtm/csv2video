"""
src/models/project.py
Shared application state passed between all UI pages.
"""
from typing import Optional
import json
import os


class AppState:
    """
    Central state object shared across all pages.
    Holds the loaded dataset, render configuration, and output history.
    """

    def __init__(self):
        self.data_path: Optional[str] = None
        self.dataframe = None              # pandas DataFrame, None until loaded
        self.validation_errors: list = []  # list of warning/error strings
        self.config: dict = self._default_config()
        self.output_path: Optional[str] = None
        self.recent_outputs: list = []     # list of output file paths

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------

    def _default_config(self) -> dict:
        return {
            "title": "Bar Chart Race",
            "watermark": "",
            "unit_label": "",           # e.g. "Million people", "Points", "USD Billion"
            "resolution": (1080, 1920),
            "fps": 30,
            "seconds_per_step": 2.0,
            "top_n": 10,
            "bg_color": "#0D0D18",
            "show_logos": True,        # Toggle to show or hide logos/badges entirely
            "colors": {},              # entity -> hex color string
            "logos": {},               # entity -> image file path
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def has_data(self) -> bool:
        return self.dataframe is not None and not self.dataframe.empty

    def get_entities(self) -> list:
        """Return column names excluding the first (time) column."""
        if self.dataframe is None:
            return []
        return list(self.dataframe.columns[1:])

    def get_time_col(self) -> Optional[str]:
        if self.dataframe is None:
            return None
        return str(self.dataframe.columns[0])

    def get_time_values(self) -> list:
        if self.dataframe is None:
            return []
        return list(self.dataframe.iloc[:, 0])

    # ------------------------------------------------------------------
    # Persistence (lightweight JSON)
    # ------------------------------------------------------------------

    def save_config(self, path: str = "config.json") -> None:
        data = dict(self.config)
        if isinstance(data.get("resolution"), tuple):
            data["resolution"] = list(data["resolution"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_config(self, path: str = "config.json") -> None:
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved.get("resolution"), list):
            saved["resolution"] = tuple(saved["resolution"])
        self.config.update(saved)
