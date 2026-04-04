# Middle East Conflict Situational Room

Intelligence dashboard with 3D Cesium globe, satellite tracking,
GPS jamming analysis, flight/vessel monitoring, and AI-powered reporting.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your API keys
cp .env.example .env
# Edit .env and fill in your keys

# 3. Copy your data files into data/
#    (see Data Files section below)

# 4. Run the verification check
python3 verify_setup.py

# 5. Run the full pipeline
python3 run_pipeline.py

# 6. Start the web server
python3 app.py
# Open: http://localhost:5000
```

## Data Files

Copy these files into the `data/` directory:

| File | Description |
|------|-------------|
| `iran_war_clean.csv` | War event timeline |
| `political-events.csv` | Political trajectory data |
| `vessels-attack-dataset.txt` | Attacked vessels dataset |
| `Middle_East_clean_2026.csv` | ACLED aggregated data |
| `analytical-dataset.txt` | Analytical briefing document |

## API Keys Required

All keys are loaded from `.env` (never hardcoded):

| Key | Service | Purpose |
|-----|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic | Claude report generation |
| `CESIUM_TOKEN` | Cesium Ion | 3D globe rendering |
| `ADSBX_KEY` | RapidAPI | ADS-B flights + GPS jamming |
| `DATALASTIC_KEY` | Datalastic | Marine vessel tracking |

## Project Structure

```
situational-room/
├── config.py              # Centralized configuration
├── run_pipeline.py        # Run full data pipeline
├── app.py                 # Flask web server
├── verify_setup.py        # Pre-launch checker
├── requirements.txt       # Python dependencies
├── .env                   # API keys (git-ignored)
│
├── pipeline/              # Data fetching & processing
│   ├── c02_satellites.py  # Satellite positions
│   ├── c04_telegram.py    # Telegram intelligence feed
│   ├── c05_war_data.py    # War event builder
│   ├── c07_gps_jamming.py # GPS jamming detection
│   ├── c08_flight_scraper.py  # Historical flight data
│   ├── c09_flights.py     # Live + VIP flights
│   ├── c10_marine.py      # Marine vessel tracking
│   ├── c11_marine_enhanced.py # Enhanced maritime intel
│   ├── c12_analytics.py   # Intelligence analytics
│   ├── c14_logging.py     # Logging setup
│   └── c19_weekly_report.py   # Weekly prediction report
│
├── builder/               # HTML template assembly
│   ├── c15_html_css.py    # CSS + head
│   ├── c16_html_body.py   # HTML body
│   ├── c17_html_js.py     # JavaScript
│   ├── c18_html_report.py # Report generation
│   └── c21_build_html.py  # Final HTML builder
│
├── tools/                 # Utilities
│   ├── clear_telegram_cache.py
│   ├── clear_gpsjam_cache.py
│   └── acled_cleaner.py
│
├── data/                  # Static data files
├── cache/                 # Runtime caches (git-ignored)
├── logs/                  # Log files (git-ignored)
└── output/                # Generated HTML (git-ignored)
```

## Requirements

- Python 3.9+
- Java (required by H2O for ML predictions)
- Internet access (for live API data)
