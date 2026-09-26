# FusionIntell — Middle East Conflict Situational Room

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aimanaltoubi/situational-room/blob/main/FusionIntell_Colab.ipynb)

A self-hosted intelligence dashboard for tracking the Middle East conflict in
real time. It fuses satellite tracking, GPS jamming detection, live flight
and marine vessel monitoring, war/political event timelines, and AI-generated
analytical reports into a single 3D Cesium globe interface.

> **Note:** This is a local application, not a hosted website. After you
> install and launch it (see below), a **main page** opens in your browser
> with a description of the system and a **"Load System"** button that
> opens the live dashboard. Nothing will appear until you run the server —
> simply browsing the GitHub repository will not show the button.
>
> Don't want to install anything? Click **"Open in Colab"** above — it
> clones the repo, asks for your API keys, builds the data, and loads the
> dashboard inline inside the notebook. No local Python setup required.

## Features

- 🌍 **3D Cesium globe** — interactive map of the conflict zone
- 🛰️ **Satellite tracking** — live and historical satellite positions over Iran
- 📡 **GPS jamming analysis** — visualizes jammed zones and interference trends
- ✈️ **Flight monitoring** — live commercial traffic plus VIP/private jet tracking
- 🚢 **Marine/vessel tracking** — AIS shipping data and attacked-vessel markers
- 📰 **Telegram intelligence feed** — curated live updates
- 📊 **Analytics panel** — event timelines, casualty/impact stats, risk indicators
- 🤖 **AI-powered reporting** — Claude-generated weekly prediction reports

## Launch the System

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up your API keys
cp .env.example .env
# Edit .env and fill in your keys (see "API Keys Required" below)

# 3. Copy your data files into data/
#    (see "Data Files" section below)

# 4. Run the verification check
python3 verify_setup.py

# 5. Build the dashboard data
python3 run_pipeline.py

# 6. Start the web server
python3 app.py
```

Then open **http://localhost:5000** in your browser. You'll land on the
system's main page — read the description, check the build status, and
click **"Load System"** to open the live dashboard.

| Route | Purpose |
|-------|---------|
| `/` | Main page — description + "Load System" button |
| `/dashboard` | The live Cesium globe dashboard |
| `/status` | JSON build status of the dashboard |
| `/weekly` | Latest AI-generated weekly prediction report |

Use `python3 app.py --refresh` to rebuild the pipeline before serving, or
`python3 app.py --port 8080` to use a different port.

## Deploying Online

The dashboard uses billed API keys, so if you host it publicly, set
`SITE_USERNAME` + `SITE_PASSWORD` (see `.env.example`) to require a login —
`/status` stays open for platform health checks.

**Render (recommended, easiest):**
1. Push this repo to GitHub.
2. In Render, choose "New Blueprint" and point it at the repo — it reads
   [`render.yaml`](render.yaml) and builds the included [`Dockerfile`](Dockerfile)
   automatically.
3. Fill in the env vars it prompts for (`ANTHROPIC_API_KEY`, `CESIUM_TOKEN`,
   `ADSBX_KEY`, `DATALASTIC_KEY`, `SITE_USERNAME`, `SITE_PASSWORD`).

**Any Docker host (VPS, Fly.io, ECS, etc.):**
```bash
docker build -t situational-room .
docker run -p 5000:5000 --env-file .env situational-room
```

**Any Python PaaS with a Procfile (Railway, Heroku-style):** push the repo —
it will run `gunicorn app:app` via the included [`Procfile`](Procfile). Make
sure the platform's runtime includes a JRE (needed by H2O).

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
├── app.py                 # Flask web server (main page + dashboard)
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

## Troubleshooting

- **No "Load System" button / blank page** — the app must be running
  locally; open `http://localhost:5000` after `python3 app.py`. This is not
  visible from the GitHub repository page.
- **"Dashboard not built yet" status** — run `python3 run_pipeline.py`
  first to generate `output/ifs_globe.html`.
- **Missing API key errors** — run `python3 verify_setup.py` to confirm
  which keys/data files are missing.
