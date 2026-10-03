# c07_gps_jamming.py
# GPS jamming: live + historical
# Auto-extracted from Cell 7

######################################################################
# CELL 5 — GPS Jamming: Live (ADS-B Exchange) + Historical (gpsjam.org)
# Middle East Conflict Situational Room
#
# LIVE LAYER  → ADS-B Exchange API (NIC=0 detection, real-time)
# HISTORICAL  → gpsjam.org H3 data from ~/Downloads/gpsjam_historical.json
# ACCUMULATOR → OpenSky MLAT daily history (fallback)
#
# OUTPUTS:
#   JAM_DATA     — live GPS-degraded aircraft
#   GPSJAM_DATA  — jamming grid + full historical timeline
######################################################################

import requests, json, os
from datetime import datetime, timezone
from collections import defaultdict

# ── Bypass system proxy ───────────────────────────────────────────
for _k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY','all_proxy','ALL_PROXY']:
    os.environ.pop(_k, None)

JAM_HISTORY_FILE = os.path.join(CACHE_DIR, "ifs_jam_history.json")
GPSJAM_HIST_PATH = os.path.join(CACHE_DIR, "gpsjam_historical.json")

# ── ADS-B Exchange API ────────────────────────────────────────────
ADSBX_KEY  = os.environ.get("ADSBX_KEY", "")
ADSBX_HOST = "adsbexchange-com1.p.rapidapi.com"

# ── Middle East zone centres (45 zones) ───────────────────────────
JAMMING_ZONES = [
    # IRAN
    {"id": "tehran",           "label": "Tehran",           "lat": 35.5, "lon": 51.5},
    {"id": "isfahan",          "label": "Isfahan",          "lat": 32.5, "lon": 51.5},
    {"id": "bandar_abbas",     "label": "Bandar Abbas",     "lat": 27.0, "lon": 56.5},
    {"id": "shiraz",           "label": "Shiraz",           "lat": 29.5, "lon": 52.5},
    {"id": "tabriz",           "label": "Tabriz",           "lat": 38.0, "lon": 46.0},
    {"id": "bushehr",          "label": "Bushehr",          "lat": 28.9, "lon": 50.8},
    # IRAQ
    {"id": "baghdad",          "label": "Baghdad",          "lat": 33.0, "lon": 44.0},
    {"id": "erbil",            "label": "Erbil",            "lat": 36.0, "lon": 44.0},
    {"id": "basra",            "label": "Basra",            "lat": 30.5, "lon": 47.8},
    # ISRAEL / PALESTINE
    {"id": "tel_aviv",         "label": "Tel Aviv",         "lat": 32.0, "lon": 34.8},
    {"id": "haifa",            "label": "Haifa",            "lat": 32.8, "lon": 35.0},
    {"id": "jerusalem",        "label": "Jerusalem",        "lat": 31.8, "lon": 35.2},
    {"id": "gaza",             "label": "Gaza",             "lat": 31.3, "lon": 34.3},
    # LEBANON
    {"id": "beirut",           "label": "Beirut",           "lat": 33.9, "lon": 35.5},
    {"id": "south_lebanon",    "label": "South Lebanon",    "lat": 33.1, "lon": 35.4},
    # SYRIA
    {"id": "damascus",         "label": "Damascus",         "lat": 33.5, "lon": 36.3},
    {"id": "aleppo",           "label": "Aleppo",           "lat": 36.2, "lon": 37.2},
    # JORDAN
    {"id": "amman",            "label": "Amman",            "lat": 31.9, "lon": 35.9},
    # SAUDI ARABIA
    {"id": "riyadh",           "label": "Riyadh",           "lat": 24.7, "lon": 46.7},
    {"id": "ras_tanura",       "label": "Ras Tanura",       "lat": 26.6, "lon": 50.2},
    {"id": "jeddah",           "label": "Jeddah",           "lat": 21.5, "lon": 39.2},
    # YEMEN
    {"id": "sanaa",            "label": "Sanaa",            "lat": 15.4, "lon": 44.2},
    {"id": "hodeidah",         "label": "Hodeidah",         "lat": 14.8, "lon": 43.0},
    {"id": "aden",             "label": "Aden",             "lat": 12.8, "lon": 45.0},
    # UAE
    {"id": "abu_dhabi",        "label": "Abu Dhabi",        "lat": 24.5, "lon": 54.5},
    {"id": "dubai",            "label": "Dubai",            "lat": 25.2, "lon": 55.3},
    {"id": "fujairah",         "label": "Fujairah",         "lat": 25.1, "lon": 56.3},
    # KUWAIT
    {"id": "kuwait",           "label": "Kuwait City",      "lat": 29.4, "lon": 48.0},
    # BAHRAIN
    {"id": "bahrain",          "label": "Bahrain",          "lat": 26.2, "lon": 50.6},
    # QATAR
    {"id": "qatar",            "label": "Qatar",            "lat": 25.3, "lon": 51.5},
    # OMAN
    {"id": "muscat",           "label": "Muscat",           "lat": 23.6, "lon": 58.6},
    {"id": "salalah",          "label": "Salalah",          "lat": 17.0, "lon": 54.1},
    # TURKEY
    {"id": "ankara",           "label": "Ankara",           "lat": 39.9, "lon": 32.9},
    {"id": "incirlik",         "label": "Incirlik",         "lat": 37.0, "lon": 35.3},
    {"id": "hatay",            "label": "Hatay",            "lat": 36.7, "lon": 36.1},
    # EGYPT
    {"id": "cairo",            "label": "Cairo",            "lat": 30.0, "lon": 31.2},
    {"id": "sinai",            "label": "Sinai",            "lat": 29.5, "lon": 34.5},
    {"id": "suez_canal",       "label": "Suez Canal",       "lat": 30.5, "lon": 32.4},
    # STRATEGIC WATERWAYS
    {"id": "strait_of_hormuz", "label": "Strait of Hormuz","lat": 26.5, "lon": 56.5},
    {"id": "persian_gulf",     "label": "Persian Gulf",     "lat": 26.0, "lon": 50.5},
    {"id": "gulf_of_oman",     "label": "Gulf of Oman",     "lat": 24.5, "lon": 58.0},
    {"id": "red_sea",          "label": "Red Sea",          "lat": 20.0, "lon": 38.0},
    {"id": "bab_el_mandeb",    "label": "Bab el-Mandeb",    "lat": 15.0, "lon": 42.5},
    # CYPRUS / AZERBAIJAN
    {"id": "cyprus",           "label": "Cyprus",           "lat": 34.5, "lon": 33.0},
    {"id": "baku",             "label": "Baku",             "lat": 40.4, "lon": 49.9},
]

# ══════════════════════════════════════════════════════════════════
#  FUNCTION 1 — fetch_jamming() → JAM_DATA
#  Uses ADS-B Exchange API — NIC=0 means GPS integrity compromised
# ══════════════════════════════════════════════════════════════════
def fetch_jamming():
    print("[JAM] Fetching live GPS-degraded aircraft (ADS-B Exchange NIC=0)...")

    # Sample 8 Middle East zone centres
    sample_zones = [
        (26.5, 56.5, 250),   # Strait of Hormuz
        (33.0, 44.0, 250),   # Baghdad
        (32.0, 34.8, 250),   # Tel Aviv
        (33.9, 35.5, 250),   # Beirut
        (35.5, 51.5, 250),   # Tehran
        (25.3, 51.5, 250),   # Qatar
        (26.2, 50.6, 250),   # Bahrain
        (24.5, 54.5, 250),   # Abu Dhabi
    ]

    headers = {
        "x-rapidapi-host": ADSBX_HOST,
        "x-rapidapi-key":  ADSBX_KEY,
    }

    degraded  = []
    seen_icao = set()

    for lat, lon, dist in sample_zones:
        url = f"https://{ADSBX_HOST}/v2/lat/{lat}/lon/{lon}/dist/{dist}/"
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                continue
            aircraft = r.json().get("ac", [])
            for ac in aircraft:
                icao = ac.get("hex", "")
                if not icao or icao in seen_icao:
                    continue
                ac_lat = ac.get("lat")
                ac_lon = ac.get("lon")
                if ac_lat is None or ac_lon is None:
                    continue
                nic   = ac.get("nic",   99)
                nac_p = ac.get("nac_p", 99)
                # NIC=0 or nac_p<=3 = GPS degraded
                if nic > 3 and nac_p > 3:
                    continue
                seen_icao.add(icao)
                degraded.append({
                    "icao":          icao,
                    "callsign":      (ac.get("flight") or icao).strip(),
                    "lat":           round(ac_lat, 4),
                    "lon":           round(ac_lon, 4),
                    "alt_m":         ac.get("alt_baro"),
                    "alt_ft":        ac.get("alt_baro"),
                    "degraded_type": f"NIC={nic} NAC={nac_p}",
                    "source":        "ADS-B Exchange",
                    "nic":           nic,
                    "nac_p":         nac_p,
                })
        except Exception as e:
            print(f"      ⚠ Zone ({lat},{lon}): {e}")

    print(f"      ✓ {len(degraded)} GPS-degraded aircraft (NIC<=3 or NAC<=3)")
    return degraded

# ══════════════════════════════════════════════════════════════════
#  FUNCTION 2 — load_gpsjam_historical() → historical timeline data
#  Loads pre-built gpsjam.org H3 data from local JSON file
# ══════════════════════════════════════════════════════════════════
def load_gpsjam_historical():
    """
    Scrape gpsjam.org H3 data for Middle East.
    Incremental: only fetches days not already in the cache.
    Source: https://gpsjam.org/data/{date}-h3_4.csv
    """
    import csv, io
    from datetime import timedelta
    
    print("[GPSJAM-HIST] Scraping gpsjam.org for Middle East jamming data...")
    
    # Install h3 if needed
    try:
        import h3
    except ImportError:
        print("      Installing h3 library...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "h3", "-q"])
        import h3
    
    # Middle East bounding box
    ME_BOUNDS = {"lat_min": 10, "lat_max": 42, "lon_min": 25, "lon_max": 65}
    
    # Zones for regional breakdown — all conflict-relevant areas
    ZONES = {
        # Straits & Waterways
        "hormuz":   {"lat": 26.5, "lon": 56.3, "r": 2.5, "label": "مضيق هرمز"},
        "gulf":     {"lat": 26.0, "lon": 52.0, "r": 4.0, "label": "الخليج العربي"},
        "redsea":   {"lat": 18.0, "lon": 39.0, "r": 5.0, "label": "البحر الأحمر"},
        "gulf_oman":{"lat": 24.0, "lon": 58.5, "r": 3.0, "label": "خليج عمان"},
        "gulf_aden":{"lat": 12.5, "lon": 45.0, "r": 3.0, "label": "خليج عدن"},
        # Major states
        "iran":     {"lat": 33.0, "lon": 53.0, "r": 8.0, "label": "إيران"},
        "iraq":     {"lat": 33.3, "lon": 44.4, "r": 4.0, "label": "العراق"},
        "saudi":    {"lat": 24.5, "lon": 45.0, "r": 6.0, "label": "السعودية"},
        "yemen":    {"lat": 15.5, "lon": 44.0, "r": 4.0, "label": "اليمن"},
        # Levant
        "lebanon":  {"lat": 33.9, "lon": 35.8, "r": 1.5, "label": "لبنان"},
        "syria":    {"lat": 35.0, "lon": 38.0, "r": 3.0, "label": "سوريا"},
        "israel":   {"lat": 31.5, "lon": 35.0, "r": 1.5, "label": "إسرائيل"},
        "jordan":   {"lat": 31.2, "lon": 36.5, "r": 2.0, "label": "الأردن"},
        # Gulf states
        "uae":      {"lat": 24.5, "lon": 54.5, "r": 2.0, "label": "الإمارات"},
        "qatar":    {"lat": 25.3, "lon": 51.2, "r": 1.0, "label": "قطر"},
        "bahrain":  {"lat": 26.1, "lon": 50.5, "r": 0.8, "label": "البحرين"},
        "kuwait":   {"lat": 29.3, "lon": 47.9, "r": 1.5, "label": "الكويت"},
        "oman":     {"lat": 23.0, "lon": 57.0, "r": 4.0, "label": "عمان"},
        # Other
        "egypt":    {"lat": 30.0, "lon": 32.0, "r": 3.0, "label": "مصر"},
    }
    
    # Load existing cache
    existing_days = {}
    if os.path.exists(GPSJAM_HIST_PATH):
        try:
            with open(GPSJAM_HIST_PATH) as f:
                cached = json.load(f)
            for d in cached.get("days", []):
                existing_days[d["date"]] = d
            print(f"      Cache: {len(existing_days)} days loaded")
            
            # Clean up: remove days from ADS-B live (wrong source)
            # and days missing required fields — re-fetch from gpsjam.org
            stale_dates = []
            for ds, d in existing_days.items():
                cells = d.get("cells", [])
                is_adsb = any(c.get("source") == "adsbx_live" for c in cells[:5])
                missing_fields = "zones" not in d or "me_avg_pct" not in d
                too_few_cells = len(cells) < 50 and d.get("me_avg", 0) > 0.05
                if is_adsb or missing_fields or too_few_cells:
                    stale_dates.append(ds)
            for ds in stale_dates:
                del existing_days[ds]
            if stale_dates:
                print(f"      Cleaned: {len(stale_dates)} stale/ADS-B days removed → will re-fetch from gpsjam.org")
                print(f"        Removed: {', '.join(sorted(stale_dates))}")
        except:
            pass
    
    # Build list of dates to fetch
    war_start = datetime.strptime(WAR_START_STR, "%Y-%m-%d")
    today = datetime.now()
    dates_needed = []
    current = war_start
    while current <= today:
        ds = current.strftime("%Y-%m-%d")
        if ds not in existing_days:
            dates_needed.append(ds)
        current += timedelta(days=1)
    
    print(f"      New days to fetch: {len(dates_needed)}")
    
    if not dates_needed:
        print(f"      ✓ All days cached — {len(existing_days)} days total")
        days_list = sorted(existing_days.values(), key=lambda d: d["date"])
        return {"days": days_list, "source": "gpsjam.org H3 (cached)"}
    
    # Fetch each new day
    new_count = 0
    for i, ds in enumerate(dates_needed):
        try:
            url = f"https://gpsjam.org/data/{ds}-h3_4.csv"
            r = requests.get(url, timeout=15)
            if r.status_code != 200:
                print(f"      — {ds}: HTTP {r.status_code}")
                continue
            
            # Parse CSV and filter to Middle East
            reader = csv.DictReader(io.StringIO(r.text))
            me_good = 0
            me_bad = 0
            me_cells = []
            zone_stats = {z: {"good": 0, "bad": 0} for z in ZONES}
            
            for row in reader:
                hex_id = row.get("hex", "")
                good = int(row.get("count_good_aircraft", 0))
                bad = int(row.get("count_bad_aircraft", 0))
                if good + bad == 0:
                    continue
                
                try:
                    lat, lon = h3.cell_to_latlng(hex_id)
                except:
                    continue
                
                # Filter to Middle East
                if not (ME_BOUNDS["lat_min"] <= lat <= ME_BOUNDS["lat_max"] and
                        ME_BOUNDS["lon_min"] <= lon <= ME_BOUNDS["lon_max"]):
                    continue
                
                me_good += good
                me_bad += bad
                intensity = bad / (good + bad)
                
                me_cells.append({
                    "hex": hex_id, "lat": round(lat, 3), "lon": round(lon, 3),
                    "good": good, "bad": bad, "intensity": round(intensity, 4),
                })
                
                # Zone assignment
                for zname, zone in ZONES.items():
                    dlat = lat - zone["lat"]
                    dlon = lon - zone["lon"]
                    if (dlat*dlat + dlon*dlon) <= zone["r"] * zone["r"]:
                        zone_stats[zname]["good"] += good
                        zone_stats[zname]["bad"] += bad
            
            me_total = me_good + me_bad
            me_avg = me_bad / me_total if me_total > 0 else 0
            
            zones_result = {}
            for zname, zs in zone_stats.items():
                zt = zs["good"] + zs["bad"]
                zones_result[zname] = {
                    "label": ZONES[zname]["label"],
                    "good": zs["good"], "bad": zs["bad"],
                    "intensity": round(zs["bad"] / zt, 4) if zt > 0 else 0,
                    "active": zs["bad"] > 0,
                }
            
            day_data = {
                "date": ds,
                "me_total_aircraft": me_total,
                "me_good": me_good,
                "me_bad": me_bad,
                "me_avg": round(me_avg, 6),
                "me_avg_pct": round(me_avg * 100, 2),
                "cells_count": len(me_cells),
                "cells": sorted(me_cells, key=lambda c: c["intensity"], reverse=True)[:80],
                "zones": zones_result,
            }
            
            existing_days[ds] = day_data
            new_count += 1
            print(f"      ✓ {ds} | {len(me_cells)} cells | bad: {me_bad} | avg: {me_avg*100:.1f}%")
            
            time.sleep(0.3)  # Rate limit
            
        except Exception as e:
            print(f"      ✗ {ds}: {e}")
        
        if (i + 1) % 10 == 0:
            # Save checkpoint every 10 days
            _save_gpsjam_cache(existing_days)
    
    # Final save
    _save_gpsjam_cache(existing_days)
    print(f"      ✓ Done — {new_count} new days fetched, {len(existing_days)} total")
    
    days_list = sorted(existing_days.values(), key=lambda d: d["date"])
    return {"days": days_list, "source": "gpsjam.org H3 (live scrape)"}

def _save_gpsjam_cache(days_dict):
    """Save gpsjam data to cache file."""
    days_list = sorted(days_dict.values(), key=lambda d: d["date"])
    output = {
        "source": "gpsjam.org",
        "resolution": "h3_4",
        "region": "Middle East",
        "updated": datetime.now().isoformat(),
        "days": days_list,
    }
    try:
        with open(GPSJAM_HIST_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, separators=(",", ":"))
        print(f"      ✓ Cache saved → {GPSJAM_HIST_PATH}")
    except Exception as e:
        print(f"      ⚠ Cache save failed: {e}")



# ══════════════════════════════════════════════════════════════════
#  FUNCTION 3 — fetch_live_grid() → today's jamming grid
#  Uses ADS-B Exchange to build today's live jamming map
# ══════════════════════════════════════════════════════════════════
def fetch_live_grid():
    print("[GPSJAM-LIVE] Building live jamming grid (ADS-B Exchange)...")

    headers = {
        "x-rapidapi-host": ADSBX_HOST,
        "x-rapidapi-key":  ADSBX_KEY,
    }

    # Query all 45 zones
    zone_results = []
    for zone in JAMMING_ZONES:
        url = f"https://{ADSBX_HOST}/v2/lat/{zone['lat']}/lon/{zone['lon']}/dist/150/"
        try:
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                continue
            aircraft = r.json().get("ac", [])
            total = len(aircraft)
            bad   = sum(1 for ac in aircraft
                        if ac.get("nic", 99) <= 3 or ac.get("nac_p", 99) <= 3)
            intensity = round(bad / total, 3) if total >= 2 else 0.0
            if intensity > 0 or total > 0:
                zone_results.append({
                    "lat":       zone["lat"],
                    "lon":       zone["lon"],
                    "intensity": intensity,
                    "label":     zone["label"],
                    "total_ac":  total,
                    "bad_ac":    bad,
                    "source":    "adsbx_live",
                })
        except Exception:
            continue

    zone_results.sort(key=lambda c: c["intensity"], reverse=True)

    me_avg = round(sum(c["intensity"] for c in zone_results) /
                   len(zone_results), 3) if zone_results else 0.0
    me_max = zone_results[0]["intensity"] if zone_results else 0.0

    print(f"      ✓ {len(zone_results)} zones queried | "
          f"avg={me_avg:.1%} | max={me_max:.1%}")
    return zone_results, me_avg, me_max

# ══════════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════════
print("=" * 60)
print("CELL 5 — GPS Jamming")
print("=" * 60)

# 1. Live degraded aircraft
JAM_DATA = fetch_jamming()

# 2. Load historical data
GPSJAM_HISTORICAL = load_gpsjam_historical()

# 3. Live jamming grid
live_cells, live_avg, live_max = fetch_live_grid()

# 4. Build GPSJAM_DATA — what the globe and timeline consume
today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Historical timeline from gpsjam.org data
history = []
if GPSJAM_HISTORICAL:
    for day in GPSJAM_HISTORICAL.get("days", []):
        # Build cells list for this day from zone values
        day_cells = day.get("cells", [])
        # Preserve ALL fields from scraper (zones, me_bad, me_good, me_avg_pct)
        entry = dict(day)
        entry["cell_count"] = entry.get("cells_count", len(day_cells))
        if "me_avg_pct" not in entry and "me_avg" in entry:
            entry["me_avg_pct"] = round(entry["me_avg"] * 100, 2)
        # Limit cells to top 80 by intensity for memory
        if len(day_cells) > 80:
            entry["cells"] = sorted(day_cells, key=lambda c: c.get("intensity",0), reverse=True)[:80]
        history.append(entry)

# Add today's live entry
history.append({
    "date":          today_str,
    "cells":         live_cells,
    "top_intensity": live_max,
    "me_avg":        live_avg,
    "cell_count":    len(live_cells),
})

# Sort and deduplicate by date
seen_dates = set()
history_clean = []
for h in sorted(history, key=lambda x: x["date"]):
    if h["date"] not in seen_dates:
        seen_dates.add(h["date"])
        history_clean.append(h)

GPSJAM_DATA = {
    "cells":         live_cells,      # today's live grid for map
    "history":       history_clean,   # full timeline
    "top_cells":     live_cells[:10],
    "me_avg":        live_avg,
    "me_max":        live_max,
    "source":        "ADS-B Exchange (live) + gpsjam.org H3 (historical)",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
}

# ── Save updated history back to file so next run skips re-fetch ──
try:
    save_data = {
        "source":     "gpsjam.org H3 + ADS-B Exchange live",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "days":       history_clean,
    }
    with open(GPSJAM_HIST_PATH, "w") as _f:
        json.dump(save_data, _f, indent=2, ensure_ascii=False)
    print(f"[GPSJAM-HIST] ✓ Saved {len(history_clean)} days → {GPSJAM_HIST_PATH}")
except Exception as _e:
    print(f"[GPSJAM-HIST] ⚠ Could not save history: {_e}")

print()
print(f"[CELL 5] ✓ JAM_DATA     — {len(JAM_DATA)} live degraded aircraft")
print(f"         ✓ GPSJAM_DATA  — {len(live_cells)} live grid cells")
print(f"         ✓ Timeline     — {len(history_clean)} days "
      f"({history_clean[0]['date']} → {history_clean[-1]['date']})")
print(f"         ME avg (live)  : {live_avg:.1%}")
print(f"         ME max (live)  : {live_max:.1%}")
print()
print("         Run Cell 6 next")

######################################################################
# ► NEXT CELL: Cell 6 — Live Flights + Intel Sites
######################################################################