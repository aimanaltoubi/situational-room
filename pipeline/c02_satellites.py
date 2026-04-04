# c02_satellites.py
# Satellite fetch + historical positions
# Auto-extracted from Cell 2

######################################################################
# CELL 2 — Satellite fetch + Historical Position Computation
# Middle East Conflict Situational Room
# Changes from original:
#   1. IRAN_BOX removed — uses MIDDLE_EAST_BOX from Cell 1
#   2. over_iran → over_middle_east throughout
#   3. iran_count → region_count throughout
#   4. All Iran-specific labels updated to Middle East
######################################################################

import requests, time
from skyfield.api import load, EarthSatellite, wgs84
import datetime as _dt

# ══════════════════════════════════════════════════════════════════
#  SECTION 1 — LIVE SATELLITE FETCH
# ══════════════════════════════════════════════════════════════════

def fetch_satellites():
    print("[SAT] Fetching TLEs...")

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        "curl/8.7.1",
    ]

    TLE_SOURCES = [
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
         "ctrak-active", False, False),
        ("https://celestrak.com/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
         "ctrak-active2", False, False),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json",
         "ctrak-json", False, True),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=tle",
         "visual", True, False),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
         "starlink", True, False),
        ("https://celestrak.org/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle",
         "geo", True, False),
    ]

    CACHE_FRESH_H  = 24
    CACHE_USABLE_H = 72

    def _now_utc():
        return _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)

    def save_tle_cache(tles):
        try:
            with open(TLE_CACHE, "w") as cf:
                json.dump({
                    "ts":   _now_utc().isoformat(),
                    "tles": [[n, l1, l2] for n, l1, l2 in tles]
                }, cf)
            print(f"      Cache saved → {TLE_CACHE}")
        except Exception as e:
            print(f"      Cache write failed: {e}")

    def load_tle_cache():
        try:
            if not os.path.exists(TLE_CACHE):
                return None
            with open(TLE_CACHE) as cf:
                data = json.load(cf)
            ts_str = data["ts"].split("+")[0].split("Z")[0]
            age_h  = (_now_utc() - _dt.datetime.fromisoformat(ts_str)).total_seconds() / 3600
            tles   = [(r[0], r[1], r[2]) for r in data["tles"]]
            print(f"      Cache: {len(tles):,} sats, {age_h:.1f}h old")
            return tles, age_h
        except Exception as e:
            print(f"      Cache read failed: {e}")
            return None

    def fetch_url(url, label, is_json=False, timeout=35, retries=3):
        for attempt in range(1, retries + 1):
            ua   = USER_AGENTS[(attempt - 1) % len(USER_AGENTS)]
            sess = requests.Session()
            sess.headers.update({"User-Agent": ua, "Connection": "keep-alive"})
            try:
                r = sess.get(url, timeout=timeout, verify=True, allow_redirects=True)
                if r.status_code == 200 and len(r.content) > 200:
                    return r.text, is_json
                if r.status_code == 429:
                    time.sleep(8 * attempt)
            except requests.exceptions.SSLError:
                try:
                    r = sess.get(url, timeout=timeout, verify=False)
                    if r.status_code == 200 and len(r.content) > 200:
                        return r.text, is_json
                except:
                    pass
                return None, is_json
            except requests.exceptions.ConnectionError as e:
                if "ConnectionResetError" in str(e) or "104" in str(e):
                    return None, is_json
            except:
                pass
            if attempt < retries:
                time.sleep(min(2 ** attempt, 16))
        return None, is_json

    def parse_json_tles(text):
        triples = []
        try:
            for rec in json.loads(text):
                l1 = rec.get("TLE_LINE1", "")
                l2 = rec.get("TLE_LINE2", "")
                nm = rec.get("OBJECT_NAME", rec.get("INTLDES", "UNKNOWN")).strip()
                if l1.startswith("1") and l2.startswith("2"):
                    triples.append((nm, l1, l2))
        except:
            pass
        return triples

    raw_tles         = []
    seen             = set()
    primary_ok       = False
    primary_failures = 0
    cached_result    = load_tle_cache()

    if cached_result:
        cached_tles, age_h = cached_result
        if age_h < CACHE_FRESH_H:
            print(f"      ✓ Cache fresh ({age_h:.1f}h) — skipping live fetch")
            raw_tles   = cached_tles
            for (_, l1, __) in raw_tles:
                seen.add(l1[2:7].strip())
            primary_ok = True

    for url, label, is_supp, is_json in TLE_SOURCES:
        if primary_ok:
            break
        if primary_failures >= 2:
            print("      ⚠ CelesTrak blocking — using cache")
            break
        text, _jf = fetch_url(url, label, is_json=is_json)
        if not text:
            if not is_supp:
                primary_failures += 1
            continue
        triples = parse_json_tles(text) if _jf else []
        if not _jf:
            lines = text.strip().splitlines()
            for i in range(0, len(lines) - 2, 3):
                n  = lines[i].strip()
                l1 = lines[i + 1].strip() if i + 1 < len(lines) else ""
                l2 = lines[i + 2].strip() if i + 2 < len(lines) else ""
                if l1.startswith("1") and l2.startswith("2"):
                    triples.append((n, l1, l2))
        added = 0
        for (n, l1, l2) in triples:
            norad = l1[2:7].strip()
            if norad not in seen:
                seen.add(norad)
                raw_tles.append((n, l1, l2))
                added += 1
        print(f"      + {added:5d}  ({label})")
        if not is_supp:
            primary_failures = 0
        if not is_supp and added > 3000:
            primary_ok = True
            print(f"      ✓ Primary OK ({added:,} sats)")

    if len(raw_tles) > 1000:
        save_tle_cache(raw_tles)
    elif cached_result:
        cached_tles, age_h = cached_result
        if age_h <= CACHE_USABLE_H and len(raw_tles) == 0:
            raw_tles = cached_tles
            print(f"      ✓ Using cached TLEs ({len(raw_tles):,} sats, {age_h:.1f}h)")

    if not raw_tles:
        print("      ✗ No satellite data")
        return {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "count": 0,
            "cats":  {c: 0 for c in ["spy","starlink","oneweb","military","leo","geo"]},
            "satellites": [],
        }

    print(f"      Computing positions for {len(raw_tles):,} satellites…")
    ts  = load.timescale()
    t0  = ts.now()
    cats = {c: 0 for c in ["spy","starlink","oneweb","military","leo","geo"]}
    satellites = []
    errors = 0

    for (name, l1, l2) in raw_tles:
        try:
            sat = EarthSatellite(l1, l2, name, ts)
            geo = sat.at(t0)
            lat = wgs84.latlon_of(geo)[0].degrees
            lon = wgs84.latlon_of(geo)[1].degrees
            alt = wgs84.height_of(geo).km
            if alt < 80 or alt > 60000:
                continue
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                continue
            norad = l1[2:7].strip()
            cat   = satellite_category(name, norad, alt)
            cats[cat] += 1
            satellites.append({
                "name":   name,
                "norad":  norad,
                "l1":     l1,
                "l2":     l2,
                "lat":    round(lat, 3),
                "lon":    round(lon, 3),
                "alt_km": round(alt, 1),
                "cat":    cat,
            })
        except:
            errors += 1

    print(f"      ✓ {len(satellites):,} satellites classified ({errors} errors)")
    for cat, n in cats.items():
        print(f"        {cat:<12} {n}")

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "count":      len(satellites),
        "cats":       cats,
        "satellites": satellites,
    }


# ── Run live fetch ────────────────────────────────────────────────
SAT_DATA = fetch_satellites()
print(f"\n[CELL 2] ✓ SAT_DATA ready — {SAT_DATA['count']:,} satellites")


# ══════════════════════════════════════════════════════════════════
#  SECTION 2 — HISTORICAL POSITION COMPUTATION
#
#  OUTPUT: HIST_SAT_DATA dict structure:
#    {
#      "war_start":   "2026-02-28",
#      "computed_at": "2026-03-xx T...",
#      "sat_count":   N,
#      "days": [
#        {
#          "date":         "2026-02-28",
#          "day_num":      1,
#          "satellites": [
#            {"name": "...", "norad": "...", "lat": 32.1, "lon": 51.3,
#             "alt_km": 485.2, "cat": "spy", "over_middle_east": true},
#            ...
#          ],
#          "region_count": N   # satellites over Middle East that day
#        },
#        ...
#      ]
#    }
#
#  MIDDLE EAST BOX: lat 12–42°N, lon 25–65°E (from Cell 1)
#  CACHE: ~/.ifs_hist_positions.json, 12h TTL
# ══════════════════════════════════════════════════════════════════

def compute_historical_positions():
    """
    Compute per-war-day positions of spy/military satellites.
    Returns HIST_SAT_DATA dict (see docstring above).
    Reads from cache if fresh; otherwise recomputes and saves cache.
    """
    import os, json
    import datetime as _dt

    CACHE_MAX_AGE_H = 12

    # ── Try cache ─────────────────────────────────────────────────
    if os.path.exists(HIST_POSITIONS_CACHE):
        try:
            with open(HIST_POSITIONS_CACHE) as f:
                cached = json.load(f)
            ts_str     = cached.get("computed_at", "2000-01-01T00:00:00")
            cached_dt  = _dt.datetime.fromisoformat(ts_str.split("+")[0].split("Z")[0])
            age_h      = (_dt.datetime.utcnow() - cached_dt).total_seconds() / 3600
            today_str  = _dt.datetime.utcnow().strftime("%Y-%m-%d")
            days_dates = {d["date"] for d in cached.get("days", [])}
            if age_h < CACHE_MAX_AGE_H and today_str in days_dates:
                print(f"      ✓ Historical positions cache fresh "
                      f"({age_h:.1f}h old, {len(cached['days'])} war days)")
                return cached
            else:
                print(f"      Cache stale ({age_h:.1f}h) or missing today — recomputing")
        except Exception as e:
            print(f"      Cache read failed: {e}")

    print("[HIST] Computing historical satellite positions per war day…")

    # ── Only spy + military (keeps dataset compact) ───────────────
    spy_sats = [
        s for s in SAT_DATA.get("satellites", [])
        if s.get("cat") in ("spy", "military")
    ]

    if not spy_sats:
        print("      ✗ No spy/military sats in SAT_DATA — run fetch first")
        return {
            "war_start":   WAR_START.strftime("%Y-%m-%d"),
            "computed_at": _dt.datetime.utcnow().isoformat(),
            "sat_count":   0,
            "days":        [],
        }

    print(f"      Propagating {len(spy_sats)} spy/military satellites "
          f"over each war day…")

    ts_sf           = load.timescale()
    war_start_naive = WAR_START.replace(tzinfo=None)
    today           = _dt.datetime.utcnow().replace(
                          hour=0, minute=0, second=0, microsecond=0)

    days_data    = []
    current      = war_start_naive
    day_num      = 1
    total_region = 0
    errors       = 0

    while current <= today:
        # Propagate to 12:00 UTC on this war day
        noon = current.replace(hour=12, minute=0, second=0, microsecond=0)
        t_sf = ts_sf.utc(
            noon.year, noon.month, noon.day,
            noon.hour, noon.minute, noon.second
        )

        day_sats     = []
        region_count = 0

        for s in spy_sats:
            try:
                sat_obj = EarthSatellite(s["l1"], s["l2"], s["name"], ts_sf)
                geo     = sat_obj.at(t_sf)
                lat     = wgs84.latlon_of(geo)[0].degrees
                lon     = wgs84.latlon_of(geo)[1].degrees
                alt     = wgs84.height_of(geo).km

                if alt < 80 or alt > 60000:
                    continue
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    continue

                # Middle East overflight check (LEO only)
                over_middle_east = (
                    alt < 2000
                    and MIDDLE_EAST_BOX["lat_min"] <= lat <= MIDDLE_EAST_BOX["lat_max"]
                    and MIDDLE_EAST_BOX["lon_min"] <= lon <= MIDDLE_EAST_BOX["lon_max"]
                )
                if over_middle_east:
                    region_count += 1

                day_sats.append({
                    "name":             s["name"],
                    "norad":            s["norad"],
                    "lat":              round(lat, 3),
                    "lon":              round(lon, 3),
                    "alt_km":           round(alt, 1),
                    "cat":              s["cat"],
                    "over_middle_east": over_middle_east,
                })
            except Exception:
                errors += 1

        days_data.append({
            "date":         current.strftime("%Y-%m-%d"),
            "day_num":      day_num,
            "region_count": region_count,
            "satellites":   day_sats,
        })
        total_region += region_count

        current  += _dt.timedelta(days=1)
        day_num  += 1

    result = {
        "war_start":   WAR_START.strftime("%Y-%m-%d"),
        "computed_at": _dt.datetime.utcnow().isoformat(),
        "sat_count":   len(spy_sats),
        "days":        days_data,
    }

    # ── Save cache ────────────────────────────────────────────────
    try:
        with open(HIST_POSITIONS_CACHE, "w") as f:
            json.dump(result, f, separators=(",", ":"), default=str)
        print(f"      ✓ Cache saved → {HIST_POSITIONS_CACHE}")
    except Exception as e:
        print(f"      ⚠ Cache write failed: {e}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n      ✓ {len(days_data)} war days computed  |  "
          f"{errors} propagation errors")
    print(f"      Average Middle East overflights per day: "
          f"{total_region/max(len(days_data),1):.1f}")
    print(f"\n      Sample (first 4 days):")
    for d in days_data[:4]:
        print(f"        D{d['day_num']:02d} {d['date']}  "
              f"{len(d['satellites']):3d} sats positioned  "
              f"{d['region_count']} over Middle East")

    return result


# ── Run historical computation ────────────────────────────────────
print("\n" + "=" * 60)
print("Computing historical satellite positions since conflict start…")
print("=" * 60)
HIST_SAT_DATA = compute_historical_positions()

print(f"\n[CELL 2] ✓ HIST_SAT_DATA ready — "
      f"{len(HIST_SAT_DATA.get('days', []))} war days  |  "
      f"{HIST_SAT_DATA.get('sat_count', 0)} spy/mil satellites tracked")
print("         Run Cell 3 next")

######################################################################
# ► NEXT CELL
######################################################################