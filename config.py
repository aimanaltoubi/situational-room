######################################################################
# config.py — Centralized Configuration
# Middle East Conflict Situational Room
#
# All API keys loaded from .env (never hardcoded)
# All paths relative to PROJECT_DIR
######################################################################

import os, sys, json
from datetime import datetime, timezone
from dotenv import load_dotenv

# ── Load .env file ────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

# ── Directory layout ──────────────────────────────────────────
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
CACHE_DIR   = os.path.join(PROJECT_DIR, "cache")
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")
LOGS_DIR    = os.path.join(PROJECT_DIR, "logs")

for _d in [DATA_DIR, CACHE_DIR, OUTPUT_DIR, LOGS_DIR]:
    os.makedirs(_d, exist_ok=True)

# ── Compatibility aliases ─────────────────────────────────────
# These match the variable names used throughout the notebook
SCRIPT_DIR  = PROJECT_DIR
LOG_DIR     = LOGS_DIR
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "ifs_globe.html")

# ── Log files ─────────────────────────────────────────────────
LOG_SAT    = os.path.join(LOGS_DIR, "ifs_log_sat.csv")
LOG_JAM    = os.path.join(LOGS_DIR, "ifs_log_jam.csv")
LOG_FLIGHT = os.path.join(LOGS_DIR, "ifs_log_flight.csv")

# ── Cache files ───────────────────────────────────────────────
WIKI_CACHE           = os.path.join(CACHE_DIR, "ifs_wiki_events.json")
GPSJAM_CACHE         = os.path.join(CACHE_DIR, "ifs_gpsjam.json")
TLE_CACHE            = os.path.join(CACHE_DIR, "ifs_tle_cache.json")
HIST_POSITIONS_CACHE = os.path.join(CACHE_DIR, "ifs_hist_positions.json")
TELEGRAM_CACHE       = os.path.join(CACHE_DIR, "ifs_telegram_cache.json")

# ── API Keys (from .env) ──────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CESIUM_TOKEN      = os.environ.get("CESIUM_TOKEN", "")
ADSBX_KEY         = os.environ.get("ADSBX_KEY", "")
AERODATABOX_KEY   = os.environ.get("AERODATABOX_KEY", "")
DATALASTIC_KEY    = os.environ.get("DATALASTIC_KEY", "")

# ── Conflict start date ───────────────────────────────────────
WAR_START = datetime(2026, 2, 28, tzinfo=timezone.utc)

# ── Middle East bounding box ──────────────────────────────────
MIDDLE_EAST_BOX = dict(
    lat_min=12.0,   lat_max=42.0,
    lon_min=25.0,   lon_max=65.0,
)

# ── Print status ──────────────────────────────────────────────
print("=" * 60)
print("CONFIG LOADED")
print("=" * 60)
print(f"  Project dir : {PROJECT_DIR}")
print(f"  Data dir    : {DATA_DIR}")
print(f"  Cache dir   : {CACHE_DIR}")
print(f"  Output HTML : {OUTPUT_HTML}")
_keys = {
    "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
    "CESIUM_TOKEN":      CESIUM_TOKEN,
    "ADSBX_KEY":         ADSBX_KEY,
    "DATALASTIC_KEY":    DATALASTIC_KEY,
}
for name, val in _keys.items():
    status = f"SET ({len(val)} chars)" if val else "NOT SET"
    print(f"  {name:20s}: {status}")
print(f"  Conflict start : {WAR_START.date()}")
print("=" * 60)


# ══════════════════════════════════════════════════════════════════
#  SPY / ISR SATELLITE IDENTIFICATION
# ══════════════════════════════════════════════════════════════════
SPY_NORAD_IDS = {
    "37849","39232","40258","41240","43651","44390","44481","45178",
    "46110","47851","48971","27634","27635","27636","27703","27704",
    "27705","28888","28889","28890","32265","32266","32267","23712",
    "25474","26695","36395","32060","33312","37867","39177","40699",
    "41558","43421","47834","39120","44522","32456","33446","34839",
    "36110","37165","37387","38354","39363","39365","40700","40958",
    "41032","41105","41384","41788","42063","42704","43246","43886",
    "44547","44640","44709","45026","45553","46820","47607","48808",
    "49015","49870","50466","29683","33510","37217","44232","49260",
    "28220","32376","39237","37821","41724","43111","44233","46026",
    "23710","29269","43426","44469","47822","29649","29650","30793",
    "31113","33506","31598","33412","36599","37216","43000",
}

SPY_KEYWORDS = [
    "WORLDVIEW","GEOEYE","CAPELLA","UMBRA","LEGION","PLEIADES","SPOT ",
    "PLEIADES NEO","AIRBUS","ICEYE","SYNSPECTIVE","KOMPSAT","GAOFEN",
    "JILIN","YAOGAN","LUDI","PERSONA","BARS-M","KONDOR","LOTOS",
    "USA-","TOPAZ","MISTY","NOSS","HELIOS","CSO-","SAR-LUPE",
    "COSMO-SKYMED","OFEK","TECSAR","EROS-","RISAT","CARTOSAT",
    "JANSSEN","TRUMPET","MENTOR",
]

SPY_FRAGMENTS = [
    "YAOGAN-","GAOFEN-","JILIN-","OFEK-","EROS-","CSO-",
    "COSMO-SKY","SAR-LUPE","BARS-M","KOMPSAT-","CARTOSAT-","RISAT-",
]

def is_spy_satellite(name, norad):
    if norad in SPY_NORAD_IDS:
        return True
    nu = name.upper()
    if any(k in nu for k in SPY_KEYWORDS):
        return True
    if any(nu.startswith(f) for f in SPY_FRAGMENTS):
        return True
    return False

def satellite_category(name, norad, alt_km):
    if is_spy_satellite(name, norad):
        return "spy"
    nu = name.upper()
    if "STARLINK" in nu:
        return "starlink"
    if "ONEWEB" in nu:
        return "oneweb"
    if any(k in nu for k in [
        "MILITARY","MIL-","DMSP","MUOS","WGS ",
        "AEHF","SBIRS","GPS BII","GPS BIIF","GPS BIIIA"
    ]):
        return "military"
    if alt_km < 2000:
        return "leo"
    return "geo"

# ── Logging helpers ───────────────────────────────────────────────
def _war_day(ts=None):
    ts = ts or datetime.now(timezone.utc)
    return max(0, (ts - WAR_START).days)

def _csv_append(path, header, row):
    import csv
    is_new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(header)
        w.writerow(row)

# ── Done ──────────────────────────────────────────────────────────
print("[CELL 1] ✓ Config complete")
print(f"         Output HTML         : {OUTPUT_HTML}")
print(f"         Hist positions cache: {HIST_POSITIONS_CACHE}")
print(f"         API key             : {'SET (' + str(len(ANTHROPIC_API_KEY)) + ' chars)' if ANTHROPIC_API_KEY else 'NOT SET'}")
print(f"         Conflict start      : {WAR_START.date()}  (28 Feb 2026)")
print(f"         Region box          : lat {MIDDLE_EAST_BOX['lat_min']}–{MIDDLE_EAST_BOX['lat_max']}N  lon {MIDDLE_EAST_BOX['lon_min']}–{MIDDLE_EAST_BOX['lon_max']}E")
print("         Ready — run Cell 2 next")

######################################################################
# ► NEXT CELL
######################################################################
