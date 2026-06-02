# RaceVideo Studio

Create **animated bar-chart race MP4 videos** from any CSV or JSON file — entirely as a local Python desktop app.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python main.py
```

Or on Windows, double-click `install.bat` then `run.bat`.

---

## Usage

| Step | Page | What to do |
|------|------|------------|
| 1 | **Import Data** | Drag & drop a CSV/JSON file, or click Browse. |
| 2 | **Settings** | Set title, resolution, FPS, colors. |
| 3 | **Render** | Click Render and watch the progress bar. |
| 4 | **Output** | Click "Open Folder" to find your MP4. |

---

## CSV Format

```
Year,Entity A,Entity B,Entity C
2019,100,80,60
2020,120,70,90
2021,130,110,95
```

- **First column** = time axis (Year, Month, Quarter, etc.)
- **Other columns** = entities to race (their values are compared each period)

A sample file is included at `assets/sample_data.csv`.

---

## Requirements

| Library | Version | Purpose |
|---------|---------|---------|
| PyQt6 | ≥ 6.6 | Desktop UI |
| pandas | ≥ 2.2 | CSV / JSON parsing |
| matplotlib | ≥ 3.8 | Frame rendering |
| opencv-python | ≥ 4.9 | MP4 encoding |
| numpy | ≥ 1.26 | Array operations |

---

## Output

- Format: **MP4** (H.264-compatible via OpenCV `mp4v`)
- Resolution: **1080×1920** (portrait, TikTok/Shorts ready) or 720×1280
- FPS: 30 or 60
- Saved to: `output/<title>_<timestamp>.mp4`

---

## Project Structure

```
race-video-studio/
├── main.py                     # Entry point
├── requirements.txt
├── assets/
│   └── sample_data.csv
├── output/                     # Generated MP4s
└── src/
    ├── models/project.py       # Shared AppState
    ├── engine/
    │   ├── data_parser.py      # CSV / JSON → DataFrame
    │   ├── validator.py        # Data validation
    │   ├── bar_chart_race.py   # Frame generator (matplotlib)
    │   └── video_encoder.py    # MP4 writer (OpenCV)
    └── ui/
        ├── main_window.py      # App shell + sidebar
        ├── styles.qss          # Dark theme
        ├── dashboard.py        # Dashboard page
        ├── import_page.py      # Data import page
        ├── settings_page.py    # Settings page
        └── render_page.py      # Render + download page
```
