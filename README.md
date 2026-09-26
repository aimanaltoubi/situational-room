# FusionIntell — Middle East Conflict Situational Room

A self-hosted intelligence dashboard for tracking the Middle East conflict in
real time. It fuses satellite tracking, GPS jamming detection, live flight
and marine vessel monitoring, war/political event timelines, and AI-generated
analytical reports into a single 3D Cesium globe interface.

> **New here?** The fastest way to try it is clicking **Open in Colab** in
> [Option A](#option-a--google-colab-no-install) below — no install needed.
> This is a local application, not a hosted website by default: nothing
> appears just from browsing this repository — pick one of the four ways
> to load it below.

## Table of Contents

- [Features](#features)
- [Choose How to Load the System](#choose-how-to-load-the-system)
  - [A — Google Colab](#option-a--google-colab-no-install)
  - [B — Run Locally](#option-b--run-locally)
  - [C — Public Shareable Link](#option-c--public-shareable-link)
  - [D — Deploy Online (Permanent)](#option-d--deploy-online-permanent)
- [Data Files](#data-files)
- [API Keys Required](#api-keys-required)
- [Incidents Database](#incidents-database)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)

## Features

- 🌍 **3D Cesium globe** — interactive map of the conflict zone
- 🛰️ **Satellite tracking** — live and historical satellite positions over Iran
- 📡 **GPS jamming analysis** — visualizes jammed zones and interference trends
- ✈️ **Flight monitoring** — live commercial traffic plus VIP/private jet tracking
- 🚢 **Marine/vessel tracking** — AIS shipping data and attacked-vessel markers
- 📰 **Telegram intelligence feed** — curated live updates
- 📊 **Analytics panel** — event timelines, casualty/impact stats, risk indicators
- 🤖 **AI-powered reporting** — Gemini-generated weekly prediction reports
- 🗃️ **Incidents database** — add, edit, and delete war incidents from the browser

## Choose How to Load the System

| | Option | Best for | Shareable with others? |
|---|---|---|---|
| 🧪 | [Google Colab](#option-a--google-colab-no-install) | Trying it instantly, no install | Only inside your session (unless you add a public link, see below) |
| 💻 | [Run locally](#option-b--run-locally) | Development, full control | No — localhost only |
| 🌍 | [Public link](#option-c--public-shareable-link) | Sharing with anyone right now | Yes — a temporary public URL |
| ☁️ | [Deploy online](#option-d--deploy-online-permanent) | A permanent hosted instance | Yes — a permanent public URL |

### Option A — Google Colab (no install)

Click the badge to open a ready-to-run notebook. It clones the repo, asks
for your API keys, builds the data, and displays the dashboard inline.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aimanaltoubi/situational-room/blob/main/FusionIntell_Colab.ipynb)

### Option B — Run locally

<details>
<summary>Show setup steps</summary>

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

</details>

### Option C — Public shareable link

<details>
<summary>Show setup steps</summary>

Run locally (or from the Colab notebook) with a live tunnel — no deployment
needed:

```bash
python3 app.py --public
```

Requires a free `NGROK_AUTHTOKEN` in `.env`
([get one here](https://dashboard.ngrok.com/get-started/your-authtoken)).
Prints a URL like `https://xxxx.ngrok-free.app` that **anyone** can open
while your process keeps running. Set `SITE_USERNAME`/`SITE_PASSWORD` first
(see `.env.example`) — otherwise anyone with the link has full access to a
dashboard backed by your billed API keys. The link disappears once you stop
the process; it's for temporary sharing, not permanent hosting.

</details>

### Option D — Deploy online (permanent)

<details>
<summary>Show setup steps</summary>

For a URL that stays up on its own, host it on a server. Set
`SITE_USERNAME` + `SITE_PASSWORD` here too — `/status` stays open for
platform health checks.

**Render (recommended, easiest):**
1. Push this repo to GitHub.
2. In Render, choose "New Blueprint" and point it at the repo — it reads
   [`render.yaml`](render.yaml) and builds the included [`Dockerfile`](Dockerfile)
   automatically.
3. Fill in the env vars it prompts for (`GEMINI_API_KEY`, `CESIUM_TOKEN`,
   `ADSBX_KEY`, `DATALASTIC_KEY`, `SITE_USERNAME`, `SITE_PASSWORD`).

**Any Docker host (VPS, Fly.io, ECS, etc.):**
```bash
docker build -t situational-room .
docker run -p 5000:5000 --env-file .env situational-room
```

**Any Python PaaS with a Procfile (Railway, Heroku-style):** push the repo —
it will run `gunicorn app:app` via the included [`Procfile`](Procfile). Make
sure the platform's runtime includes a JRE (needed by H2O).

</details>

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
| `GEMINI_API_KEY` | Google Gemini | AI report generation |
| `CESIUM_TOKEN` | Cesium Ion | 3D globe rendering |
| `ADSBX_KEY` | RapidAPI | ADS-B flights + GPS jamming |
| `DATALASTIC_KEY` | Datalastic | Marine vessel tracking |

## Incidents Database

From the main page, click **"Manage Incidents Database"** (or go to
`/database`) to add, edit, or delete war incidents directly in the browser
— no manual CSV editing required. There's no separate database file:
`data/iran_war_clean.csv` itself is the store, so every add/edit/delete is
written straight to that CSV.

Click **"Rebuild Dashboard"** on that page after making changes to rerun
the pipeline so the globe/timeline reflect the latest incidents.

## Project Structure

<details>
<summary>Show folder layout</summary>

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

</details>

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

