# c10_marine.py
# Marine / AIS vessel data
# Auto-extracted from Cell 10

######################################################################
# CELL 7 — Marine / AIS Vessel Data
# Middle East Conflict Situational Room
#
# SOURCE: Datalastic API (satellite + terrestrial AIS)
# KEY:    ~/Downloads/datalastic-api-key.txt
# PLAN:   Starter — 20,000 credits/month
#
# ZONES MONITORED:
#   1. Strait of Hormuz        — primary chokepoint
#   2. Persian Gulf            — Gulf state ports + US Navy
#   3. Gulf of Oman            — Hormuz approaches
#   4. Red Sea / Bab el-Mandeb — Houthi attack corridor
#   5. Arabian Sea             — open ocean transits
#
# CREDIT COST PER RUN:
#   vessel_inradius: credits = vessels found (max 500 per call)
#   5 zones × ~50-200 vessels = ~250-1000 credits per refresh
#
# OUTPUTS:
#   MARINE_DATA — all vessels, zones, chokepoint counts,
#                 military vessels, tankers, vessels going dark
######################################################################

import requests, json, os, time, math
from datetime import datetime, timezone
from collections import defaultdict

# ── Load API key ──────────────────────────────────────────────────
DATALASTIC_KEY = os.environ.get("DATALASTIC_KEY", "")
if DATALASTIC_KEY:
    print(f"[MARINE] Datalastic key loaded: {DATALASTIC_KEY[:8]}...")
else:
    print("[MARINE] ✗ DATALASTIC_KEY not set in .env")


BASE_URL = "https://api.datalastic.com/api/v0"

# ── Monitoring zones ──────────────────────────────────────────────
# Each zone: name, lat, lon, radius_km, strategic_importance
# Datalastic max radius = 50km
# Large zones are covered with multiple overlapping 50km sampling points
# Each point costs credits = vessels found (max 500 per call)

MARINE_ZONES = [
    # ── Strait of Hormuz — 3 points covering the full strait ─────
    {
        "id":"hormuz", "name":"Strait of Hormuz", "name_ar":"مضيق هرمز",
        "importance":"critical", "notes":"~21% of global oil transit. IRGC declared closed Day 1.",
        "points":[
            {"lat":26.60,"lon":55.90},  # Western Hormuz entrance
            {"lat":26.50,"lon":56.50},  # Central strait
            {"lat":26.35,"lon":57.10},  # Eastern Hormuz exit
        ],
    },
    # ── Persian Gulf — 8 points covering key ports and US bases ──
    {
        "id":"persian_gulf", "name":"Persian Gulf", "name_ar":"الخليج العربي",
        "importance":"high", "notes":"Gulf state ports, US 5th Fleet, oil terminals.",
        "points":[
            {"lat":26.20,"lon":50.60},  # Bahrain / NSA 5th Fleet
            {"lat":25.30,"lon":51.55},  # Doha Qatar / Al Udeid
            {"lat":24.50,"lon":54.40},  # Abu Dhabi / Al Dhafra
            {"lat":25.20,"lon":55.30},  # Dubai port
            {"lat":29.20,"lon":48.00},  # Kuwait / Camp Arifjan
            {"lat":26.90,"lon":49.90},  # Saudi Ras Tanura oil terminal
            {"lat":27.50,"lon":49.00},  # Saudi Eastern Province
            {"lat":24.00,"lon":52.50},  # UAE central gulf
        ],
    },
    # ── Gulf of Oman — 4 points covering Hormuz approaches ───────
    {
        "id":"gulf_of_oman", "name":"Gulf of Oman", "name_ar":"خليج عُمان",
        "importance":"high", "notes":"Hormuz southern approach. Iranian naval activity.",
        "points":[
            {"lat":24.00,"lon":57.50},  # Muscat approaches
            {"lat":22.50,"lon":59.50},  # Central Gulf of Oman
            {"lat":23.80,"lon":58.60},  # Muscat port area
            {"lat":22.00,"lon":61.00},  # Eastern approaches
        ],
    },
    # ── Red Sea / Bab el-Mandeb — 4 points ───────────────────────
    {
        "id":"red_sea", "name":"Red Sea / Bab el-Mandeb", "name_ar":"البحر الأحمر / باب المندب",
        "importance":"high", "notes":"Houthi attack corridor. Suez Canal supply chain.",
        "points":[
            {"lat":12.60,"lon":43.50},  # Bab el-Mandeb strait
            {"lat":14.00,"lon":42.70},  # Southern Red Sea
            {"lat":15.50,"lon":41.80},  # Hodeidah / Houthi waters
            {"lat":17.00,"lon":41.00},  # Northern Houthi range
        ],
    },
    # ── Arabian Sea — 3 points for open ocean tracking ───────────
    {
        "id":"arabian_sea", "name":"Arabian Sea", "name_ar":"بحر العرب",
        "importance":"medium", "notes":"Open ocean transits. US carrier strike groups.",
        "points":[
            {"lat":20.00,"lon":62.00},  # Central Arabian Sea
            {"lat":17.00,"lon":65.00},  # Eastern approaches
            {"lat":15.00,"lon":58.00},  # Western Arabian Sea
        ],
    },
]

# ── Vessel type classification ─────────────────────────────────────
TANKER_TYPES = {
    "Tanker","Tanker - Hazard A (Major)","Tanker - Hazard B",
    "Tanker - Hazard C (Minor)","Tanker - Hazard D (Recognizable)",
    "Tanker: Hazardous category A","Tanker: Hazardous category B",
    "Tanker: Hazardous category C","Tanker: Hazardous category D",
}
TANKER_SPECIFIC = {
    "Crude Oil Tanker","LNG Tanker","LPG Tanker","Oil Products Tanker",
    "Chemical Tanker","Oil or Chemical Tanker","Crude Oil","Shuttle Tanker",
    "LPG or Chemical Tanker","Floating Storage or Production",
}
MILITARY_TYPES  = {"Military Ops"}
MILITARY_SPECIFIC = {
    "Combat Vessel","Command Vessel","Naval Craft","Naval Patrol Vessel",
    "Naval Auxiliary Vessel","Naval or Naval Auxiliary Vessel",
    "Mine Hunter","Minesweeper","Troopship","Replenishment Vessel",
    "Naval Salvage Vessel","Naval Research Vessel","Logistics Naval Vessel",
    "Torpedo Recovery Vessel",
}
CARGO_TYPES = {"Cargo","Cargo - Hazard A (Major)","Cargo - Hazard B",
               "Cargo - Hazard C (Minor)","Cargo - Hazard D (Recognizable)"}

# ── Known warship MMSIs in the region ─────────────────────────────
# US Navy carrier strike groups, 5th Fleet assets
KNOWN_WARSHIPS = {
    "338500000": "USS Abraham Lincoln (CVN-72)",
    "338500001": "USS Gerald R. Ford (CVN-78)",
    "338501000": "USS George H.W. Bush (CVN-77)",
    "338600000": "USS Bainbridge (DDG-96)",
    "338700000": "USS Charlotte (SSN-773)",
}

# ── Flag country risk classification ─────────────────────────────
HIGH_INTEREST_FLAGS = {
    "IR": "Iran",
    "IL": "Israel",
    "US": "USA",
    "RU": "Russia",
    "CN": "China",
    "KP": "North Korea",
}

def classify_vessel(v):
    """Classify vessel into operational category."""
    vtype    = v.get("type","")
    vspecific= v.get("type_specific","")
    mmsi     = v.get("mmsi","")

    if mmsi in KNOWN_WARSHIPS:
        return "warship", KNOWN_WARSHIPS[mmsi]
    if vtype in MILITARY_TYPES or vspecific in MILITARY_SPECIFIC:
        return "military", "Military vessel"
    if vtype in TANKER_TYPES or vspecific in TANKER_SPECIFIC:
        return "tanker", f"{vspecific or vtype}"
    if vtype in CARGO_TYPES:
        return "cargo", f"{vspecific or vtype}"
    if vtype == "Fishing":
        return "fishing", "Fishing vessel"
    if vtype in ("Tug","Law Enforce","SAR"):
        return "support", f"{vtype}"
    return "other", f"{vspecific or vtype or 'Unknown'}"

def is_going_dark(v):
    """Flag vessels that haven't reported in >2 hours — AIS suppression signal."""
    epoch = v.get("last_position_epoch")
    if not epoch:
        return False
    age_hours = (time.time() - epoch) / 3600
    return age_hours > 2.0

def fetch_zone(zone):
    """
    Fetch all vessels in a monitoring zone.
    Large zones use multiple 50km sampling points (Datalastic max radius=50km).
    Deduplicates by MMSI across all points in the zone.
    """
    zone_vessels = {}   # mmsi → vessel (deduped within zone)
    points = zone.get("points", [{"lat": zone.get("lat"), "lon": zone.get("lon")}])

    for pt in points:
        try:
            r = requests.get(
                f"{BASE_URL}/vessel_inradius",
                params={
                    "api-key": DATALASTIC_KEY,
                    "lat":     str(pt["lat"]),
                    "lon":     str(pt["lon"]),
                    "radius":  "50",   # max allowed by Datalastic
                },
                timeout=15,
            )
            if r.status_code == 200:
                data    = r.json()
                vessels = data.get("data",{}).get("vessels",{})
                if isinstance(vessels, dict):
                    vessels = list(vessels.values())
                for v in vessels:
                    mmsi = str(v.get("mmsi",""))
                    if mmsi and mmsi not in zone_vessels:
                        zone_vessels[mmsi] = v
            else:
                body = r.json().get("meta",{}).get("message","")
                print(f"\n        ✗ pt({pt['lat']},{pt['lon']}): {r.status_code} {body}", end="")
            time.sleep(0.35)  # 600 req/min limit
        except Exception as e:
            print(f"\n        ✗ pt({pt['lat']},{pt['lon']}): {e}", end="")

    vessel_list = list(zone_vessels.values())
    return vessel_list, len(vessel_list)

def fetch_vessel_info(mmsi):
    """Get detailed info for a specific vessel by MMSI."""
    try:
        r = requests.get(
            f"{BASE_URL}/vessel",
            params={"api-key": DATALASTIC_KEY, "mmsi": mmsi},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json().get("data",{})
        return {}
    except:
        return {}

def check_credits():
    """Check remaining Datalastic credits."""
    try:
        r = requests.get(
            f"{BASE_URL}/stat",
            params={"api-key": DATALASTIC_KEY},
            timeout=10,
        )
        if r.status_code == 200:
            d = r.json().get("data",{})
            return d.get("requests_remaining", "?"), d.get("requests_made", "?")
        return "?", "?"
    except:
        return "?", "?"

# ══════════════════════════════════════════════════════════════════
#  MAIN FETCH FUNCTION
# ══════════════════════════════════════════════════════════════════
def fetch_marine_data():
    """
    Fetch all vessel data across 5 Middle East maritime zones.
    Returns MARINE_DATA dict ready for Cesium globe display.
    """
    print("[MARINE] Fetching vessel data (Datalastic)...")

    if not DATALASTIC_KEY:
        print("      ✗ No API key — skipping marine data")
        return _empty_result("No API key")

    # ── Pre-flight credit check ───────────────────────────────
    try:
        cr = requests.get(f"{BASE_URL}/stat", params={"api-key": DATALASTIC_KEY}, timeout=10)
        if cr.status_code == 200:
            cdata = cr.json().get("data",{})
            remaining = cdata.get("requests_remaining", "?")
            made = cdata.get("requests_made", "?")
            print(f"      Credits: {remaining} remaining ({made} used)")
            if isinstance(remaining, (int,float)) and remaining <= 0:
                print(f"      ✗ NO CREDITS LEFT ({remaining}) — API will return empty results!")
                print(f"        Your plan resets monthly. Wait for reset or upgrade plan.")
                return _empty_result(f"No credits remaining ({remaining})")
        else:
            print(f"      ⚠ Credit check returned HTTP {cr.status_code}")
            try:
                print(f"        Response: {cr.json()}")
            except:
                print(f"        Response: {cr.text[:200]}")
    except Exception as e:
        print(f"      ⚠ Credit check failed: {e}")

    # ── Test single API call to verify key works ──────────────
    try:
        test_r = requests.get(
            f"{BASE_URL}/vessel_inradius",
            params={"api-key": DATALASTIC_KEY, "lat": "26.56", "lon": "56.25", "radius": "10"},
            timeout=15,
        )
        if test_r.status_code != 200:
            try:
                err = test_r.json()
                err_msg = err.get("meta",{}).get("message","") or err.get("message","") or str(err)[:200]
            except:
                err_msg = test_r.text[:200]
            print(f"      ✗ API test call failed (HTTP {test_r.status_code}): {err_msg}")
            if test_r.status_code in (401, 403):
                print(f"        API key may be invalid or expired")
                return _empty_result(f"API auth error: HTTP {test_r.status_code}")
            if test_r.status_code == 402:
                print(f"        Credits exhausted or billing issue")
                return _empty_result(f"Credits exhausted: HTTP 402")
            if test_r.status_code == 429:
                print(f"        Rate limited — try again later")
                return _empty_result(f"Rate limited: HTTP 429")
        else:
            test_data = test_r.json()
            test_vessels = test_data.get("data",{}).get("vessels",{})
            if isinstance(test_vessels, dict):
                test_vessels = list(test_vessels.values())
            print(f"      ✓ API test OK — {len(test_vessels)} vessels at Hormuz test point")
    except Exception as e:
        print(f"      ⚠ API test call error: {e}")

    all_vessels  = {}   # mmsi → vessel record (deduplicated across zones)
    zone_results = []

    for zone in MARINE_ZONES:
        pts = zone.get("points", [])
        print(f"      → {zone['name']} ({len(pts)} points)...", end=" ", flush=True)

        # Fetch all points for this zone
        zone_vessels_dict = {}  # mmsi → vessel (deduped within zone)
        for pt in pts:
            try:
                r = requests.get(
                    f"{BASE_URL}/vessel_inradius",
                    params={
                        "api-key": DATALASTIC_KEY,
                        "lat":     str(pt["lat"]),
                        "lon":     str(pt["lon"]),
                        "radius":  "50",
                    },
                    timeout=15,
                )
                if r.status_code == 200:
                    data = r.json()
                    raw  = data.get("data", {}).get("vessels", {})
                    if isinstance(raw, dict):
                        raw = list(raw.values())
                    for v in raw:
                        mmsi = str(v.get("mmsi", ""))
                        if mmsi and mmsi not in zone_vessels_dict:
                            zone_vessels_dict[mmsi] = v
                else:
                    # Log the actual API error
                    try:
                        err_body = r.json()
                        err_msg = err_body.get("meta",{}).get("message","") or err_body.get("message","") or str(err_body)[:120]
                    except:
                        err_msg = r.text[:120]
                    print(f"\n        ✗ API {r.status_code} at ({pt['lat']},{pt['lon']}): {err_msg}", end="")
                time.sleep(0.35)
            except Exception as e:
                print(f"\n        Error pt({pt['lat']},{pt['lon']}): {e}", end="")

        # Process vessels for this zone
        zone_tankers  = 0
        zone_military = 0
        zone_dark     = 0

        for v in zone_vessels_dict.values():
            mmsi             = str(v.get("mmsi", ""))
            cat, cat_label   = classify_vessel(v)
            dark             = is_going_dark(v)
            flag             = v.get("country_iso", "")

            record = {
                "mmsi":          mmsi,
                "imo":           v.get("imo", ""),
                "name":          v.get("name", ""),
                "flag":          flag,
                "flag_country":  HIGH_INTEREST_FLAGS.get(flag, flag),
                "country_name":  v.get("country_name", ""),
                "type":          v.get("type", ""),
                "type_specific": v.get("type_specific", ""),
                "category":      cat,
                "category_label":cat_label,
                "callsign":      v.get("callsign", ""),
                "lat":           v.get("lat"),
                "lon":           v.get("lon"),
                "speed":         v.get("speed"),
                "speed_max":     v.get("speed_max"),
                "course":        v.get("course"),
                "heading":       v.get("heading"),
                "nav_status":    v.get("navigational_status", ""),
                "destination":   v.get("destination", ""),
                "eta_utc":       v.get("eta_UTC", ""),
                "last_pos_utc":  v.get("last_position_UTC", ""),
                "last_pos_epoch":v.get("last_position_epoch"),
                "distance_km":   v.get("distance"),
                "gross_tonnage": v.get("gross_tonnage"),
                "deadweight":    v.get("deadweight"),
                "teu":           v.get("teu"),
                "length":        v.get("length"),
                "breadth":       v.get("breadth"),
                "year_built":    v.get("year_built"),
                "draught":       v.get("draught_avg"),
                "going_dark":    dark,
                "high_interest": flag in HIGH_INTEREST_FLAGS,
                "is_tanker":     cat == "tanker",
                "is_military":   cat in ("military", "warship"),
                "zone_id":       zone["id"],
                "zone_name":     zone["name"],
                "source":        "datalastic",
            }

            if cat == "tanker":                  zone_tankers  += 1
            if cat in ("military", "warship"):   zone_military += 1
            if dark:                             zone_dark     += 1

            if mmsi not in all_vessels:
                all_vessels[mmsi] = record

        # Center point for globe display
        ctr = pts[len(pts)//2] if pts else {"lat": 0, "lon": 0}

        zone_results.append({
            "zone_id":        zone["id"],
            "zone_name":      zone["name"],
            "zone_name_ar":   zone["name_ar"],
            "lat":            ctr["lat"],
            "lon":            ctr["lon"],
            "n_points":       len(pts),
            "importance":     zone["importance"],
            "notes":          zone["notes"],
            "vessels_fetched":len(zone_vessels_dict),
            "tankers":        zone_tankers,
            "military":       zone_military,
            "going_dark":     zone_dark,
        })

        print(f"{len(zone_vessels_dict)} vessels | {zone_tankers} tankers | {zone_military} military | {zone_dark} dark")
        time.sleep(0.5)

    # ── Build final summary ───────────────────────────────────────
    vessel_list    = list(all_vessels.values())
    tankers        = [v for v in vessel_list if v["is_tanker"]]
    military       = [v for v in vessel_list if v["is_military"]]
    going_dark     = [v for v in vessel_list if v["going_dark"]]
    high_interest  = [v for v in vessel_list if v["high_interest"]]
    hormuz_vessels = [v for v in vessel_list if v["zone_id"] == "hormuz"]
    moving_tankers = [t for t in tankers if (t.get("speed") or 0) > 1.0]
    stopped_tankers= [t for t in tankers if (t.get("speed") or 0) <= 1.0]

    by_category = defaultdict(int)
    by_flag     = defaultdict(int)
    for v in vessel_list:
        by_category[v["category"]] += 1
        by_flag[v["flag"]]         += 1

    credits_left, credits_used = check_credits()

    return {
        "vessels":           vessel_list,
        "zones":             zone_results,
        "total":             len(vessel_list),
        "tankers":           tankers,
        "military":          military,
        "going_dark":        going_dark,
        "high_interest":     high_interest,
        "hormuz_vessels":    hormuz_vessels,
        "moving_tankers":    moving_tankers,
        "stopped_tankers":   stopped_tankers,
        "by_category":       dict(by_category),
        "by_flag":           dict(by_flag),
        "counts": {
            "total":          len(vessel_list),
            "tankers":        len(tankers),
            "military":       len(military),
            "going_dark":     len(going_dark),
            "high_interest":  len(high_interest),
            "hormuz":         len(hormuz_vessels),
            "moving_tankers": len(moving_tankers),
            "stopped_tankers":len(stopped_tankers),
        },
        "credits_remaining": credits_left,
        "credits_used":      credits_used,
        "timestamp_utc":     datetime.now(timezone.utc).isoformat(),
        "source":            "Datalastic satellite+terrestrial AIS",
        "error":             None,
    }


def _empty_result(reason):
    return {
        "vessels":[],"zones":[],"total":0,"tankers":[],"military":[],
        "going_dark":[],"high_interest":[],"hormuz_vessels":[],
        "moving_tankers":[],"stopped_tankers":[],"by_category":{},
        "by_flag":{},"counts":{},"credits_remaining":"?",
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "source":"Datalastic","error":reason,
    }

# ══════════════════════════════════════════════════════════════════
#  RUN — with JSON cache (saves credits)
# ══════════════════════════════════════════════════════════════════
MARINE_CACHE_PATH = os.path.join(CACHE_DIR, "marine_data.json")
CACHE_MAX_AGE_HOURS = 6  # re-fetch if older than this

print("="*60)
print("CELL 7 — Marine / AIS Vessel Data")
print("="*60)

_use_cache = False
if os.path.exists(MARINE_CACHE_PATH):
    try:
        cache_age_hours = (time.time() - os.path.getmtime(MARINE_CACHE_PATH)) / 3600
        if cache_age_hours < CACHE_MAX_AGE_HOURS:
            with open(MARINE_CACHE_PATH, "r", encoding="utf-8") as f:
                MARINE_DATA = json.load(f)
            # Rebuild list fields from cached data (JSON doesn't preserve filtering)
            vessel_list = MARINE_DATA.get("vessels", [])
            MARINE_DATA["tankers"] = [v for v in vessel_list if v.get("is_tanker")]
            MARINE_DATA["military"] = [v for v in vessel_list if v.get("is_military")]
            MARINE_DATA["going_dark"] = [v for v in vessel_list if v.get("going_dark")]
            MARINE_DATA["high_interest"] = [v for v in vessel_list if v.get("high_interest")]
            MARINE_DATA["hormuz_vessels"] = [v for v in vessel_list if v.get("zone_id") == "hormuz"]
            MARINE_DATA["moving_tankers"] = [v for v in vessel_list if v.get("is_tanker") and (v.get("speed") or 0) > 1.0]
            MARINE_DATA["stopped_tankers"] = [v for v in vessel_list if v.get("is_tanker") and (v.get("speed") or 0) <= 1.0]
            _use_cache = True
            print(f"  ✓ Loaded from cache ({cache_age_hours:.1f}h old, <{CACHE_MAX_AGE_HOURS}h limit)")
            print(f"    To force refresh: delete {MARINE_CACHE_PATH}")
        else:
            print(f"  Cache is {cache_age_hours:.1f}h old (>{CACHE_MAX_AGE_HOURS}h) — refreshing...")
    except Exception as e:
        print(f"  ⚠ Cache read failed ({e}) — fetching fresh")

if not _use_cache:
    MARINE_DATA = fetch_marine_data()
    # Save to cache
    try:
        # Save a JSON-safe copy (exclude non-serializable fields)
        cache_copy = {k: v for k, v in MARINE_DATA.items()
                      if k not in ("tankers","military","going_dark","high_interest",
                                   "hormuz_vessels","moving_tankers","stopped_tankers")}
        with open(MARINE_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache_copy, f, ensure_ascii=False, default=str)
        print(f"  ✓ Saved to {MARINE_CACHE_PATH} ({os.path.getsize(MARINE_CACHE_PATH)/1024:.0f} KB)")
    except Exception as e:
        print(f"  ⚠ Cache save failed: {e}")

print()
print(f"[CELL 7] ✓ MARINE_DATA ready")
print(f"         Source   : {MARINE_DATA.get('source','?')}")
print(f"         Total    : {MARINE_DATA.get('total',0)} vessels")
print(f"         Tankers  : {len(MARINE_DATA.get('tankers',[]))} ({len(MARINE_DATA.get('moving_tankers',[]))} moving / {len(MARINE_DATA.get('stopped_tankers',[]))} stopped)")
print(f"         Military : {len(MARINE_DATA.get('military',[]))}")
print(f"         Going dark: {len(MARINE_DATA.get('going_dark',[]))} (AIS suppressed >2hrs)")
print(f"         Hormuz   : {len(MARINE_DATA.get('hormuz_vessels',[]))} vessels in strait")
print(f"         High interest flags: {len(MARINE_DATA.get('high_interest',[]))}")
print(f"         Credits remaining: {MARINE_DATA.get('credits_remaining','cached')}")
print()
print("         Zone summary:")
for z in MARINE_DATA.get("zones",[]):
    print(f"           {z['zone_name']:<30} {z['vessels_fetched']:4d} vessels | "
          f"{z['tankers']} tankers | {z['military']} military | {z['going_dark']} dark")
print()
print("         Run Cell 8 next")

######################################################################
# ► NEXT CELL: Cell 8 — Conflict Prediction Model
######################################################################