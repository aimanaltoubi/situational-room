# c14_logging.py
# Logging setup
# Auto-extracted from Cell 14

######################################################################
# CELL: C7 — Logging
######################################################################

# ─────────────────────────────────────────────────────────────────────────────
# CELL 6 — Logging & CSV Snapshots  (fixed)
# ─────────────────────────────────────────────────────────────────────────────
#
# WHAT THIS CELL DOES:
#   log_satellites()  — appends SAT_DATA snapshot to ~/ifs_log_sat.csv
#   log_jamming()     — appends JAM_DATA + GPSJAM_DATA to ~/ifs_log_jam.csv
#   log_flights()     — appends FLIGHT_DATA summary to ~/ifs_log_flight.csv
#
# SAT_DATA STRUCTURE (Cell 2 output):
#   {
#     "fetched_at":  str (ISO timestamp),
#     "count":       int,
#     "cats":        { "spy": N, "leo": N, "geo": N, ... },
#     "satellites":  [ { name, norad, category, lat, lon, alt_km, ... }, ... ]
#   }
#
# CSV SCHEMAS:
#   ifs_log_sat.csv
#     timestamp_utc, total_sats, spy_count, leo_count, geo_count,
#     military_count, starlink_count, oneweb_count, over_iran_count
#
#   ifs_log_jam.csv
#     timestamp_utc, degraded_aircraft, mlat_count, no_gps_alt_count,
#     grid_cells, me_avg_intensity, me_max_intensity, accumulator_days
#
#   ifs_log_flight.csv
#     timestamp_utc, total_aircraft, commercial, military, cargo,
#     private, unknown, proximity_alerts, busiest_fir, busiest_fir_count
# ─────────────────────────────────────────────────────────────────────────────

import csv
import os
from datetime import datetime, timezone
from collections import Counter

LOG_SAT    = os.path.join(LOGS_DIR, "ifs_log_sat.csv")
LOG_JAM    = os.path.join(LOGS_DIR, "ifs_log_jam.csv")
LOG_FLIGHT = os.path.join(LOGS_DIR, "ifs_log_flight.csv")


# ─────────────────────────────────────────────────────────────────────────────
# HELPER — safe CSV append
# ─────────────────────────────────────────────────────────────────────────────
def _csv_append(filepath, headers, row):
    file_exists = os.path.exists(filepath) and os.path.getsize(filepath) > 0
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(row)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION 1 — log_satellites()
# ─────────────────────────────────────────────────────────────────────────────
def log_satellites(sat_data):
    """
    Accepts SAT_DATA in either format:
      - dict  { fetched_at, count, cats, satellites }  ← Cell 2 output
      - list  [ {name, category, ...}, ... ]           ← legacy
    """
    ts = datetime.now(timezone.utc).isoformat()

    # ── normalise input ───────────────────────────────────────────────────
    if isinstance(sat_data, dict):
        cats     = sat_data.get("cats", {})
        sat_list = sat_data.get("satellites", [])
        total    = sat_data.get("count", len(sat_list))
    elif isinstance(sat_data, list):
        sat_list = sat_data
        total    = len(sat_list)
        cats     = Counter(
            s.get("category", "unknown") if isinstance(s, dict) else "unknown"
            for s in sat_list
        )
    else:
        print(f"[LOG-SAT] Unrecognised SAT_DATA type ({type(sat_data)}) — skipping")
        return

    if total == 0:
        print("[LOG-SAT] SAT_DATA empty — skipping")
        return

    # over_iran — try list first, fall back to 0
    over_iran = 0
    for s in sat_list:
        if not isinstance(s, dict):
            continue
        # accept either key name Cell 2 might use
        if s.get("over_iran") or s.get("above_iran") or s.get("iran", False):
            over_iran += 1

    headers = [
        "timestamp_utc", "total_sats", "spy_count", "leo_count",
        "geo_count", "military_count", "starlink_count",
        "oneweb_count", "over_iran_count",
    ]
    row = [
        ts, total,
        cats.get("spy", 0),
        cats.get("leo", 0),
        cats.get("geo", 0),
        cats.get("military", 0),
        cats.get("starlink", 0),
        cats.get("oneweb", 0),
        over_iran,
    ]

    _csv_append(LOG_SAT, headers, row)
    print(f"[LOG-SAT]    ✓ {total} sats | spy={cats.get('spy',0)} | over_iran={over_iran}")


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION 2 — log_jamming()
# ─────────────────────────────────────────────────────────────────────────────
def log_jamming(jam_data, gpsjam_data):
    ts = datetime.now(timezone.utc).isoformat()

    # jam_data is a list of degraded aircraft dicts
    jam_list = jam_data if isinstance(jam_data, list) else []
    mlat_count   = sum(1 for d in jam_list
                       if isinstance(d, dict) and "MLAT" in d.get("degraded_type",""))
    no_gps_count = sum(1 for d in jam_list
                       if isinstance(d, dict) and d.get("degraded_type") == "NO_GPS_ALT")

    # gpsjam_data is a dict
    gj = gpsjam_data if isinstance(gpsjam_data, dict) else {}
    grid_cells   = len(gj.get("cells", []))
    me_avg       = gj.get("me_avg", 0.0)
    me_max       = gj.get("me_max", 0.0)
    accum_days   = len(gj.get("history", []))

    headers = [
        "timestamp_utc", "degraded_aircraft", "mlat_count",
        "no_gps_alt_count", "grid_cells", "me_avg_intensity",
        "me_max_intensity", "accumulator_days",
    ]
    row = [
        ts, len(jam_list), mlat_count, no_gps_count,
        grid_cells, round(me_avg, 4), round(me_max, 4), accum_days,
    ]

    _csv_append(LOG_JAM, headers, row)
    print(f"[LOG-JAM]    ✓ {len(jam_list)} degraded | "
          f"avg {me_avg:.1%} | {grid_cells} cells | {accum_days} accum days")


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION 3 — log_flights()
# ─────────────────────────────────────────────────────────────────────────────
def log_flights(flight_data):
    ts = datetime.now(timezone.utc).isoformat()

    fd      = flight_data if isinstance(flight_data, dict) else {}
    counts  = fd.get("counts", {})
    alerts  = len(fd.get("proximity_alerts", []))

    # busiest known FIR (skip UNKN)
    fir_summ = fd.get("fir_summary", [])
    known    = [f for f in fir_summ if f.get("fir") != "UNKN"]
    busiest  = known[0] if known else {"fir": "UNKN", "count": 0}

    headers = [
        "timestamp_utc", "total_aircraft", "commercial", "military",
        "cargo", "private", "unknown", "proximity_alerts",
        "busiest_fir", "busiest_fir_count",
    ]
    row = [
        ts,
        fd.get("total", 0),
        counts.get("commercial", 0),
        counts.get("military", 0),
        counts.get("cargo", 0),
        counts.get("private", 0),
        counts.get("unknown", 0),
        alerts,
        busiest.get("fir", "UNKN"),
        busiest.get("count", 0),
    ]

    _csv_append(LOG_FLIGHT, headers, row)
    print(f"[LOG-FLIGHT] ✓ {fd.get('total',0)} aircraft | "
          f"{alerts} alerts | busiest: {busiest.get('fir','UNKN')} "
          f"({busiest.get('count',0)})")


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION 4 — log_marine()
# ─────────────────────────────────────────────────────────────────────────────
def log_marine(marine_data):
    ts  = datetime.now(timezone.utc).isoformat()
    md  = marine_data if isinstance(marine_data, dict) else {}
    cnt = md.get("counts", {})

    headers = [
        "timestamp_utc", "total_vessels", "tankers", "military",
        "moving_tankers", "stopped_tankers", "tanker_disruption_pct",
        "hormuz_vessels", "going_dark", "high_interest", "credits_remaining",
    ]
    row = [
        ts,
        md.get("total", 0),
        cnt.get("tankers", 0),
        cnt.get("military", 0),
        cnt.get("moving_tankers", 0),
        cnt.get("stopped_tankers", 0),
        MARITIME_THREAT.get("tanker_disruption_pct", 0) if "MARITIME_THREAT" in globals() else 0,
        cnt.get("hormuz", len(md.get("hormuz_vessels", []))),
        cnt.get("going_dark", 0),
        cnt.get("high_interest", 0),
        md.get("credits_remaining", "?"),
    ]

    _csv_append(LOG_MARINE, headers, row)
    print(f"[LOG-MARINE] ✓ {md.get('total',0)} vessels | "
          f"{cnt.get('tankers',0)} tankers | "
          f"{cnt.get('going_dark',0)} going dark")


# ─────────────────────────────────────────────────────────────────────────────
# FUNCTION 5 — log_vessels()
# ─────────────────────────────────────────────────────────────────────────────
def log_vessels(av_data):
    ts  = datetime.now(timezone.utc).isoformat()
    avd = av_data if isinstance(av_data, dict) else {}

    headers = [
        "timestamp_utc", "total_attacks", "commercial", "naval",
        "confirmed", "total_killed", "total_injured", "total_missing",
        "hormuz_attacks", "gulf_attacks",
    ]

    by_zone = avd.get("by_zone", {})
    hormuz_atk = len(by_zone.get("Strait of Hormuz", []))
    gulf_atk   = len(by_zone.get("Persian Gulf", []))

    row = [
        ts,
        avd.get("count", 0),
        avd.get("commercial_count", 0),
        avd.get("naval_count", 0),
        avd.get("confirmed_count", 0),
        avd.get("total_killed", 0),
        avd.get("total_injured", 0),
        avd.get("total_missing", 0),
        hormuz_atk,
        gulf_atk,
    ]

    _csv_append(LOG_VESSELS, headers, row)
    print(f"[LOG-VESSELS] ✓ {avd.get('count',0)} attacks | "
          f"killed={avd.get('total_killed',0)} | "
          f"confirmed={avd.get('confirmed_count',0)}")


# ─────────────────────────────────────────────────────────────────────────────
# CELL EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
LOG_MARINE  = os.path.join(LOGS_DIR, "ifs_log_marine.csv")
LOG_VESSELS = os.path.join(LOGS_DIR, "ifs_log_vessels.csv")

print("=" * 60)
print("CELL 10 — Logging & CSV Snapshots")
print("=" * 60)

# Log each data source — gracefully skip if not available
_logged = []

if "SAT_DATA" in globals():
    log_satellites(SAT_DATA); _logged.append("SAT")
else:
    print("  ⚠ SAT_DATA not found — skipping")

if "JAM_DATA" in globals() and "GPSJAM_DATA" in globals():
    log_jamming(JAM_DATA, GPSJAM_DATA); _logged.append("JAM")
else:
    print("  ⚠ JAM_DATA / GPSJAM_DATA not found — skipping")

if "FLIGHT_DATA" in globals():
    log_flights(FLIGHT_DATA); _logged.append("FLIGHT")
else:
    print("  ⚠ FLIGHT_DATA not found — skipping")

if "MARINE_DATA" in globals():
    log_marine(MARINE_DATA); _logged.append("MARINE")
else:
    print("  ⚠ MARINE_DATA not found — skipping")

if "ATTACKED_VESSELS_DATA" in globals():
    log_vessels(ATTACKED_VESSELS_DATA); _logged.append("VESSELS")
else:
    print("  ⚠ ATTACKED_VESSELS_DATA not found — skipping")

print()
print(f"[CELL 10] ✓ Logged: {_logged}")
print(f"  Logs written to ~/ifs_log_*.csv")
print()
print("  Run Cell 11 next")

######################################################################
# ► NEXT CELL: Cell 11 — ML Prediction (Cell 17)
######################################################################