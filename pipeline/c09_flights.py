# c09_flights.py
# Live flights + historical VIP jets
# Auto-extracted from Cell 9

######################################################################
# CELL 6 — Live Flights + Historical VIP/Private Jets + Intel Sites
# Middle East Conflict Situational Room
#
# LIVE    → ADS-B Exchange API (all aircraft, real-time)
# HISTORY → ~/Downloads/flight_historical.json
# INTEL   → Strategic sites database
#
# OUTPUTS:
#   FLIGHT_DATA      — live aircraft over Middle East
#   FLIGHT_HIST_DATA — historical VIP + private jet movements
#   INTEL_DATA       — strategic sites
######################################################################

import requests, json, os, math
from datetime import datetime, timezone
from collections import defaultdict

ADSBX_KEY  = os.environ.get("ADSBX_KEY", "")
ADSBX_HOST = "adsbexchange-com1.p.rapidapi.com"
ADSBX_HDR  = {
    "x-rapidapi-host": ADSBX_HOST,
    "x-rapidapi-key":  ADSBX_KEY,
}

FLIGHT_HIST_PATH = os.path.join(CACHE_DIR, "flight_historical.json")

ME_LAT_MIN, ME_LAT_MAX = 12.0, 42.0
ME_LON_MIN, ME_LON_MAX = 29.0, 63.0
PROXIMITY_KM = 150

# ── Known VIP registrations for live flagging ─────────────────────
LIVE_VIP_REGS = {
    "4X-ISR","HZ-MF7","HZ-MF8","HZ-HM1","HZ-HM4","HZ-ARE",
    "A6-AUH","A6-PFA","A6-PFE","A6-PFC","A6-HEH","A6-RJY",
    "A7-HHJ","A7-HHF","A7-HHE","A7-HHH","A7-HBJ","A7-AAG",
    "9K-GAA","9K-GBB","A9C-HAK","A9C-HMK","A9C-AWL",
    "VQ-BDD","JY-HMH","JY-JAB","TC-TRK","TC-TUR","TC-CBK",
    "TC-DAP","TC-GAP","SU-EGY","EP-IGA","EP-AJA","OD-MRL",
    "A4O-OMN","A4O-HMS","UR-ABA","ZZ336","F-RARF","B-2479",
}
LIVE_VIP_REGS = (set(workspace_reference("vip_aircraft.json", {}, {}))
                 or (LIVE_VIP_REGS if WORKSPACE.get("builtin_reference_data") else set()))

# ══════════════════════════════════════════════════════════════════
#  INTEL SITES DATABASE (unchanged from original)
# ══════════════════════════════════════════════════════════════════
_INTEL_SITES = [
    {"name_ar":"منشأة فوردو للتخصيب","name_en":"Fordow Fuel Enrichment Plant","lat":34.8849,"lon":50.9928,"country":"Iran","category":"nuclear","notes":"Deep underground enrichment facility near Qom. Hardened against airstrikes."},
    {"name_ar":"منشأة نطنز النووية","name_en":"Natanz Nuclear Facility","lat":33.7237,"lon":51.7267,"country":"Iran","category":"nuclear","notes":"Primary uranium enrichment site. Above and below-ground centrifuge halls."},
    {"name_ar":"مفاعل أراك للمياه الثقيلة","name_en":"Arak IR-40 Heavy Water Reactor","lat":34.0701,"lon":49.2311,"country":"Iran","category":"nuclear","notes":"Heavy water reactor. Modified under JCPOA but remains operational."},
    {"name_ar":"مركز بوشهر النووي","name_en":"Bushehr Nuclear Power Plant","lat":28.8310,"lon":50.8886,"country":"Iran","category":"nuclear","notes":"Russia-built civilian reactor on Persian Gulf coast."},
    {"name_ar":"منشأة إسفهان النووية","name_en":"Isfahan Nuclear Technology Centre","lat":32.6314,"lon":51.7208,"country":"Iran","category":"nuclear","notes":"Uranium conversion facility."},
    {"name_ar":"موقع بارشين العسكري","name_en":"Parchin Military Complex","lat":35.5197,"lon":51.7675,"country":"Iran","category":"nuclear","notes":"Suspected conventional explosive and nuclear weapons development testing."},
    {"name_ar":"مفاعل ديمونة","name_en":"Negev Nuclear Research Centre (Dimona)","lat":30.9967,"lon":35.1472,"country":"Israel","category":"nuclear","notes":"Israel's undeclared nuclear weapons production reactor."},
    {"name_ar":"مستودع الكيمياء السوري","name_en":"Masyaf Chemical Weapons Site","lat":35.0694,"lon":36.3419,"country":"Syria","category":"nuclear","notes":"CERS facility. Suspected residual CW production."},
    {"name_ar":"قاعدة العديد الجوية","name_en":"Al Udeid Air Base","lat":25.1173,"lon":51.3150,"country":"Qatar","category":"usbase","notes":"CENTCOM forward HQ. Largest US air base in Middle East."},
    {"name_ar":"قاعدة علي السالم الجوية","name_en":"Ali Al Salem Air Base","lat":29.3467,"lon":47.5200,"country":"Kuwait","category":"usbase","notes":"USAF rotational fighter and tanker operations."},
    {"name_ar":"معسكر عريفجان","name_en":"Camp Arifjan","lat":29.1986,"lon":48.1322,"country":"Kuwait","category":"usbase","notes":"US Army forward logistics and pre-positioned equipment hub."},
    {"name_ar":"قاعدة NSA البحرية البحرين","name_en":"NSA Bahrain — 5th Fleet HQ","lat":26.2041,"lon":50.5933,"country":"Bahrain","category":"usbase","notes":"US Naval Forces Central Command."},
    {"name_ar":"قاعدة الظفرة الجوية","name_en":"Al Dhafra Air Base","lat":24.2416,"lon":54.5477,"country":"UAE","category":"usbase","notes":"USAF. F-22, U-2, RQ-4 Global Hawk operations."},
    {"name_ar":"قاعدة عين الأسد","name_en":"Ain al-Asad Air Base","lat":33.7856,"lon":42.4414,"country":"Iraq","category":"usbase","notes":"Largest US base in Iraq."},
    {"name_ar":"قاعدة أربيل الجوية","name_en":"Erbil Air Base","lat":36.2376,"lon":43.9632,"country":"Iraq","category":"usbase","notes":"US/Coalition SOF and air operations in Kurdish region."},
    {"name_ar":"قاعدة مفرق الجوية","name_en":"Muwaffaq Salti Air Base (Azraq)","lat":31.8258,"lon":36.7883,"country":"Jordan","category":"usbase","notes":"USAF rotational presence."},
    {"name_ar":"قاعدة الأمير سلطان الجوية","name_en":"Prince Sultan Air Base","lat":24.0625,"lon":47.5806,"country":"Saudi Arabia","category":"usbase","notes":"USAF redeployed 2019. F-15, Patriot batteries, THAAD assets."},
    {"name_ar":"معسكر ليمونييه","name_en":"Camp Lemonnier — Djibouti","lat":11.5463,"lon":43.1591,"country":"Djibouti","category":"usbase","notes":"Primary US base in Horn of Africa."},
    {"name_ar":"قاعدة التنف","name_en":"Al-Tanf Garrison","lat":33.5059,"lon":38.6503,"country":"Syria","category":"usbase","notes":"US SOF garrison at Syria-Iraq-Jordan tri-border."},
    {"name_ar":"مضيق هرمز","name_en":"Strait of Hormuz","lat":26.5944,"lon":56.4500,"country":"Iran/Oman","category":"chokepoint","notes":"~21% of global oil transit."},
    {"name_ar":"باب المندب","name_en":"Bab el-Mandeb Strait","lat":12.5833,"lon":43.3333,"country":"Yemen/Djibouti","category":"chokepoint","notes":"Red Sea entry. Houthi attack corridor."},
    {"name_ar":"قناة السويس","name_en":"Suez Canal","lat":30.4549,"lon":32.5498,"country":"Egypt","category":"chokepoint","notes":"~12% of global trade."},
    {"name_ar":"مضيق تيران","name_en":"Strait of Tiran","lat":27.9833,"lon":34.5500,"country":"Saudi Arabia/Egypt","category":"chokepoint","notes":"Gulf of Aqaba entry."},
    {"name_ar":"ميناء الحديدة","name_en":"Hudaydah Port","lat":14.7975,"lon":42.9511,"country":"Yemen","category":"chokepoint","notes":"Yemen's primary humanitarian import port."},
    {"name_ar":"طهران","name_en":"Tehran","lat":35.6892,"lon":51.3890,"country":"Iran","category":"city","notes":"Capital. IRGC HQ and government ministries."},
    {"name_ar":"بغداد","name_en":"Baghdad","lat":33.3152,"lon":44.3661,"country":"Iraq","category":"city","notes":"Capital. Green Zone hosts US Embassy."},
    {"name_ar":"دمشق","name_en":"Damascus","lat":33.5138,"lon":36.2765,"country":"Syria","category":"city","notes":"Capital."},
    {"name_ar":"بيروت","name_en":"Beirut","lat":33.8886,"lon":35.4955,"country":"Lebanon","category":"city","notes":"Capital. Hezbollah HQ in southern suburbs."},
    {"name_ar":"غزة","name_en":"Gaza City","lat":31.5017,"lon":34.4668,"country":"Palestine","category":"city","notes":"Active conflict zone."},
    {"name_ar":"صنعاء","name_en":"Sanaa","lat":15.3694,"lon":44.1910,"country":"Yemen","category":"city","notes":"Houthi-controlled capital."},
    {"name_ar":"الرياض","name_en":"Riyadh","lat":24.6877,"lon":46.7219,"country":"Saudi Arabia","category":"city","notes":"Capital."},
    {"name_ar":"تل أبيب","name_en":"Tel Aviv","lat":32.0853,"lon":34.7818,"country":"Israel","category":"city","notes":"Primary urban centre. IDF HQ."},
    {"name_ar":"القدس","name_en":"Jerusalem","lat":31.7683,"lon":35.2137,"country":"Israel","category":"city","notes":"Contested capital."},
    {"name_ar":"عدن","name_en":"Aden","lat":12.7797,"lon":45.0095,"country":"Yemen","category":"city","notes":"Internationally recognised Yemeni government seat."},
    {"name_ar":"الموصل","name_en":"Mosul","lat":36.3400,"lon":43.1300,"country":"Iraq","category":"city","notes":"Former ISIS capital."},
    {"name_ar":"حلب","name_en":"Aleppo","lat":36.2021,"lon":37.1343,"country":"Syria","category":"city","notes":"Syria's second city."},
]
_INTEL_SITES = workspace_reference("intel_sites.json", _INTEL_SITES, [])

_FIRS = [
    ("LLLL","Israel/Palestine",29.4,33.3,34.2,35.9),
    ("LCCC","Cyprus/Lebanon",33.0,36.5,32.0,37.0),
    ("OSDI","Syria",32.5,37.3,35.7,42.5),
    ("OJAC","Jordan",29.2,33.4,34.9,39.3),
    ("ORBB","Iraq",29.0,37.5,38.8,48.8),
    ("OIIX","Iran",25.0,40.0,44.0,63.5),
    ("OEDF","Saudi Arabia",16.0,32.2,34.5,55.7),
    ("OBBB","Bahrain/Qatar",24.0,27.0,50.0,52.5),
    ("OKAC","Kuwait",28.5,30.1,46.5,49.0),
    ("OMAE","UAE/Oman",22.0,26.5,51.5,60.0),
    ("OYZZ","Yemen",11.8,18.5,42.5,53.2),
    ("HECA","Egypt",22.0,31.7,24.7,37.0),
]

_MILITARY_PREFIXES = ["RCH","JAKE","PACK","REACH","SWIFT","KNIFE","SPAR","SAM ","USAF","NAVY","ARMY","USMC","MAGIC","TOPAZ","SOLAR","BOXER","IRON","UAV","MQ-","RQ-","OMM","QAF","BAH","KUG","SVA","IPF","EGY","ORF"]
_CARGO_PREFIXES    = ["UPS","FDX","GTI","ABX","CAL","DHL","TNT","FED","VDA"]

def _classify_aircraft(callsign):
    cs = (callsign or "").strip().upper()
    if not cs: return "unknown"
    if any(cs.startswith(p) for p in _MILITARY_PREFIXES): return "military"
    if any(cs.startswith(p) for p in _CARGO_PREFIXES):    return "cargo"
    if len(cs)>=4 and cs[:3].isalpha() and cs[3:].strip().lstrip("0").isdigit(): return "commercial"
    if len(cs)<=6 and cs.replace("-","").isalnum(): return "private"
    return "unknown"

def _assign_fir(lat, lon):
    for fir_id, name, la_min, la_max, lo_min, lo_max in _FIRS:
        if la_min<=lat<=la_max and lo_min<=lon<=lo_max:
            return fir_id, name
    return "UNKN", "Unknown"

def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    d_lat = math.radians(lat2-lat1)
    d_lon = math.radians(lon2-lon1)
    a = (math.sin(d_lat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(d_lon/2)**2)
    return R*2*math.atan2(math.sqrt(a), math.sqrt(1-a))

# ══════════════════════════════════════════════════════════════════
#  FUNCTION 1 — fetch_flights() → FLIGHT_DATA (LIVE)
# ══════════════════════════════════════════════════════════════════
def fetch_flights():
    print("[FLIGHTS] Fetching live aircraft (ADS-B Exchange)...")
    url = f"https://{ADSBX_HOST}/v2/lat/27.0/lon/45.0/dist/2500/"
    try:
        r = requests.get(url, headers=ADSBX_HDR, timeout=15)
        raw_ac = r.json().get("ac",[]) if r.status_code==200 else []
        print(f"      ADS-B Exchange: {len(raw_ac)} aircraft received")
    except Exception as e:
        print(f"      ADS-B Exchange error: {e}")
        raw_ac = []

    aircraft  = []
    counts    = defaultdict(int)
    fir_counts= defaultdict(int)
    alerts    = []

    for ac in raw_ac:
        lat = ac.get("lat"); lon = ac.get("lon")
        if lat is None or lon is None: continue
        if not (ME_LAT_MIN<=lat<=ME_LAT_MAX and ME_LON_MIN<=lon<=ME_LON_MAX): continue

        reg      = (ac.get("r") or "").strip().upper()
        callsign = (ac.get("flight") or "").strip()
        ac_type  = (ac.get("t") or "").strip()
        is_vip   = reg in LIVE_VIP_REGS
        ac_cat   = "vip" if is_vip else _classify_aircraft(callsign)
        fir_id, fir_name = _assign_fir(lat, lon)
        counts[ac_cat]    += 1
        fir_counts[fir_id]+= 1

        rec = {
            "icao":     ac.get("hex",""),
            "reg":      reg,
            "callsign": callsign,
            "type":     ac_type,
            "category": ac_cat,
            "is_vip":   is_vip,
            "lat":      round(lat,4),
            "lon":      round(lon,4),
            "alt_ft":   ac.get("alt_baro"),
            "alt_geom": ac.get("alt_geom"),
            "speed_kts":ac.get("gs"),
            "heading":  ac.get("track"),
            "squawk":   ac.get("squawk",""),
            "fir_id":   fir_id,
            "fir_name": fir_name,
            "nic":      ac.get("nic",99),
            "nac_p":    ac.get("nac_p",99),
            "source":   "adsbx_live",
        }

        for site in _INTEL_SITES:
            dist = _haversine_km(lat, lon, site["lat"], site["lon"])
            if dist <= PROXIMITY_KM:
                alerts.append({**rec, "site_name":site["name_en"], "site_country":site["country"], "site_cat":site["category"], "dist_km":round(dist,1)})
                break

        aircraft.append(rec)

    fir_summary = [{"fir_id":fid,"name":nm,"count":fir_counts.get(fid,0)} for fid,nm,*_ in _FIRS]
    vip_live    = [a for a in aircraft if a["is_vip"]]
    print(f"      ✓ {len(aircraft)} aircraft in Middle East airspace")
    print(f"      ✓ {len(vip_live)} known VIP aircraft live")
    print(f"      ✓ {len(alerts)} proximity alerts")

    return {
        "aircraft":         aircraft,
        "counts":           dict(counts),
        "fir_summary":      fir_summary,
        "proximity_alerts": alerts,
        "vip_aircraft":     vip_live,
        "total":            len(aircraft),
        "timestamp_utc":    datetime.now(timezone.utc).isoformat(),
        "source":           "ADS-B Exchange",
    }

# ══════════════════════════════════════════════════════════════════
#  FUNCTION 2 — load_flight_history() → FLIGHT_HIST_DATA
# ══════════════════════════════════════════════════════════════════
def load_flight_history():
    print("[FLIGHTS-HIST] Loading historical flight data...")
    if not os.path.exists(FLIGHT_HIST_PATH):
        print(f"      ✗ Not found: {FLIGHT_HIST_PATH}")
        print("        Run flight_data_scraper.py from terminal first")
        return {"flights":[],"daily_summary":{},"by_day":{},"total_flights":0,"vip_flights":0,"private_flights":0}

    try:
        with open(FLIGHT_HIST_PATH, encoding="utf-8") as f:
            data = json.load(f)

        flights = data.get("flights", [])
        summary = data.get("daily_summary", {})

        vip_count     = sum(1 for f in flights if f.get("category")=="VIP_KNOWN")
        private_count = sum(1 for f in flights if f.get("category") in ("PRIVATE_JET","VIP_CALLSIGN"))
        other_count   = len(flights) - vip_count - private_count

        # Build by_day lookup
        by_day = defaultdict(list)
        for fl in flights:
            day = fl.get("day_of_war", 0)
            if day > 0:
                by_day[day].append(fl)

        print(f"      ✓ {len(flights):,} total flights loaded")
        print(f"      ✓ {vip_count} VIP/government | {private_count} private/charter | {other_count} other")
        print(f"      ✓ {len(summary)} war days covered")
        print(f"      ✓ Day 1 spike: {summary.get('2026-02-28',{}).get('total_flights',0)} flights (evacuation)")

        return {
            "flights":         flights,
            "daily_summary":   summary,
            "by_day":          dict(by_day),
            "total_flights":   len(flights),
            "vip_flights":     vip_count,
            "private_flights": private_count,
            "source":          data.get("source",""),
            "fetched_at":      data.get("fetched_at",""),
            "airports":        data.get("airports_queried",[]),
        }
    except Exception as e:
        print(f"      ✗ Load failed: {e}")
        return {"flights":[],"daily_summary":{},"by_day":{},"total_flights":0}

# ══════════════════════════════════════════════════════════════════
#  FUNCTION 3 — build_intel_data() → INTEL_DATA
# ══════════════════════════════════════════════════════════════════
def build_intel_data():
    sites_by_country  = defaultdict(list)
    sites_by_category = defaultdict(list)
    for site in _INTEL_SITES:
        sites_by_country[site["country"]].append(site)
        sites_by_category[site["category"]].append(site)
    return {
        "sites":              _INTEL_SITES,
        "sites_by_country":   dict(sites_by_country),
        "sites_by_category":  dict(sites_by_category),
        "counts_by_category": {k:len(v) for k,v in sites_by_category.items()},
        "total":              len(_INTEL_SITES),
    }

# ══════════════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════════════
print("="*60)
print("CELL 6 — Flights + Intel Sites")
print("="*60)

if FEATURES["flights"]:
    FLIGHT_DATA      = fetch_flights()
    FLIGHT_HIST_DATA = load_flight_history()
else:
    FLIGHT_DATA      = {"aircraft": [], "total": 0, "counts": {}, "fir_summary": [], "proximity_alerts": []}
    FLIGHT_HIST_DATA = {"flights": [], "daily_summary": {}, "by_day": {},
                        "total_flights": 0, "vip_flights": 0, "private_flights": 0}
INTEL_DATA       = build_intel_data()

print()
print(f"[CELL 6] ✓ FLIGHT_DATA      — {FLIGHT_DATA['total']} live aircraft")
print(f"         ✓ FLIGHT_HIST_DATA — {FLIGHT_HIST_DATA['total_flights']:,} historical flights")
print(f"                              {FLIGHT_HIST_DATA['vip_flights']} VIP | {FLIGHT_HIST_DATA['private_flights']} private")
print(f"         ✓ INTEL_DATA       — {INTEL_DATA['total']} strategic sites")
print(f"         ✓ Proximity alerts — {len(FLIGHT_DATA['proximity_alerts'])}")
print()
print("         Run Cell 7 next")

######################################################################
# ► NEXT CELL: Cell 7 — Marine / AIS Data
######################################################################