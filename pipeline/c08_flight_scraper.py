# c08_flight_scraper.py
# Flight data scraper (AeroDataBox)
# Auto-extracted from Cell 8

######################################################################
# FLIGHT DATA SCRAPER — Complete Dataset for Cell 6
# Save as ~/Downloads/flight_data_scraper.py
# Run: python3 ~/Downloads/flight_data_scraper.py
#
# WHAT IT DOES:
#   STEP 1 — Fetches all known VIP/head-of-state aircraft (by registration)
#   STEP 2 — Queries all 18 ME airports for private jets + VIP movements
#   STEP 3 — Merges, deduplicates, filters ME-relevant only
#   STEP 4 — Saves final dataset to ~/Downloads/flight_historical.json
#
# OUTPUT: flight_historical.json
#   - All VIP/head-of-state flights during war period
#   - All private jet movements through ME airports
#   - Full route details (dep/arr lat/lon, times, runway, gate)
#   - Daily summary for timeline
#   - Ready to load in Cell 6 as FLIGHT_HIST_DATA
#
# API: AeroDataBox Mega Plan
# Cost: ~1,200 units out of 600,000
######################################################################

import requests, json, os, time, math
from datetime import datetime, timedelta
from collections import defaultdict

AERODATABOX_KEY = os.environ.get("AERODATABOX_KEY", "")
HEADERS = {
    "x-rapidapi-host": "aerodatabox.p.rapidapi.com",
    "x-rapidapi-key":  AERODATABOX_KEY,
}
OUTPUT_PATH = os.path.join(CACHE_DIR, "flight_historical.json")
WAR_START   = datetime(2026, 2, 28)
WAR_END     = datetime(2026, 3, 27)

# ══════════════════════════════════════════════════════════════════
#  ALL KNOWN VIP / HEAD-OF-STATE AIRCRAFT
# ══════════════════════════════════════════════════════════════════
VIP_AIRCRAFT = {
    # ── ISRAEL ───────────────────────────────────────────────────
    "4X-ISR":   {"label": "Netanyahu — Wing of Zion Boeing 767",        "country": "Israel",        "owner": "PM Benjamin Netanyahu"},

    # ── SAUDI ARABIA ─────────────────────────────────────────────
    "HZ-HM1":   {"label": "MBS — Boeing 747-400 Flagship",              "country": "Saudi Arabia",  "owner": "Crown Prince MBS"},
    "HZ-HM4":   {"label": "MBS — Boeing 787-8 Dreamliner",              "country": "Saudi Arabia",  "owner": "Crown Prince MBS"},
    "HZ-MF7":   {"label": "MBS — Boeing 787 BBJ",                       "country": "Saudi Arabia",  "owner": "Crown Prince MBS"},
    "HZ-MF8":   {"label": "MBS — Boeing 787 BBJ backup",                "country": "Saudi Arabia",  "owner": "Crown Prince MBS"},
    "HZ-HM1A":  {"label": "King Salman — Boeing 747-300",               "country": "Saudi Arabia",  "owner": "King Salman"},
    "HZ-HM1B":  {"label": "King Salman — Boeing 747-SP",                "country": "Saudi Arabia",  "owner": "King Salman"},
    "HZ-MF6":   {"label": "Saudi Government — Boeing 737 BBJ3",         "country": "Saudi Arabia",  "owner": "Saudi Government"},
    "HZ-ARE":   {"label": "Saudi — Saudia 787-9 Golden Leadership",     "country": "Saudi Arabia",  "owner": "King Salman / MBS"},

    # ── UAE ──────────────────────────────────────────────────────
    "A6-AUH":   {"label": "Abu Dhabi Presidential Flight",              "country": "UAE",           "owner": "Abu Dhabi Presidential Flight"},
    "A6-PFA":   {"label": "UAE Presidential — Boeing 747-8",            "country": "UAE",           "owner": "UAE Presidential Flight"},
    "A6-PFE":   {"label": "UAE Presidential — Boeing 787-9",            "country": "UAE",           "owner": "UAE Presidential Flight"},
    "A6-PFC":   {"label": "UAE Presidential — Boeing 787-9",            "country": "UAE",           "owner": "UAE Presidential Flight"},
    "A6-HEH":   {"label": "Dubai Royal Air Wing",                       "country": "UAE",           "owner": "Sheikh Mohammed bin Rashid"},
    "A6-RJY":   {"label": "Dubai Royal Air Wing",                       "country": "UAE",           "owner": "Dubai Royal Family"},
    "A6-MMM":   {"label": "UAE — MBZ Royal",                            "country": "UAE",           "owner": "Sheikh Mohammed bin Zayed"},

    # ── QATAR ────────────────────────────────────────────────────
    "A7-HHJ":   {"label": "Qatar Amiri — Boeing 747-8",                 "country": "Qatar",         "owner": "Qatar Amiri Flight"},
    "A7-HHF":   {"label": "Qatar Amiri — Boeing 747-8",                 "country": "Qatar",         "owner": "Qatar Amiri Flight"},
    "A7-HHE":   {"label": "Qatar Amiri — Boeing 747-8",                 "country": "Qatar",         "owner": "Qatar Amiri Flight"},
    "A7-HHH":   {"label": "Qatar Amiri — Airbus A340-500",              "country": "Qatar",         "owner": "Qatar Amiri Flight"},
    "A7-HBJ":   {"label": "Qatar Amiri — Boeing 747-8 (HBJ)",           "country": "Qatar",         "owner": "Sheikh Hamad bin Jassim"},
    "A7-AAG":   {"label": "Qatar Amiri Flight",                         "country": "Qatar",         "owner": "Qatar Royal Family"},
    "A7-MBK":   {"label": "Qatar Amiri — BBJ",                          "country": "Qatar",         "owner": "Qatar Royal Family"},

    # ── KUWAIT ───────────────────────────────────────────────────
    "9K-GAA":   {"label": "Kuwait Emir — Boeing 747-8",                 "country": "Kuwait",        "owner": "Emir of Kuwait"},
    "9K-GBB":   {"label": "Kuwait Amiri — Boeing 737-900",              "country": "Kuwait",        "owner": "Kuwaiti Amiri Flight"},
    "9K-AKD":   {"label": "Kuwait Government — A340-500",               "country": "Kuwait",        "owner": "Kuwait Government"},
    "9K-AKE":   {"label": "Kuwait Government — A340-500",               "country": "Kuwait",        "owner": "Kuwait Government"},

    # ── BAHRAIN ──────────────────────────────────────────────────
    "A9C-HAK":  {"label": "Bahrain Royal — Boeing 747-400",             "country": "Bahrain",       "owner": "Bahrain Royal Family"},
    "A9C-HMK":  {"label": "Bahrain Royal — Boeing 747-400",             "country": "Bahrain",       "owner": "Bahrain Royal Family"},
    "A9C-AWL":  {"label": "Bahrain Royal — Boeing 767-400ER",           "country": "Bahrain",       "owner": "Bahrain Royal Family"},
    "A9C-BAH":  {"label": "Bahrain Government Gulfstream G650",         "country": "Bahrain",       "owner": "Bahrain Government"},

    # ── JORDAN ───────────────────────────────────────────────────
    "VQ-BDD":   {"label": "Jordan Royal — Airbus A318 Elite",           "country": "Jordan",        "owner": "King Abdullah II"},
    "JY-HMH":   {"label": "Jordan Royal Hashemite Flight",              "country": "Jordan",        "owner": "King Abdullah II"},
    "JY-JAB":   {"label": "Jordan Royal — Boeing 787",                  "country": "Jordan",        "owner": "Jordan Royal Family"},

    # ── OMAN ─────────────────────────────────────────────────────
    "A4O-OMN":  {"label": "Oman Royal — Boeing 747-8",                  "country": "Oman",          "owner": "Sultan of Oman"},
    "A4O-HMS":  {"label": "Oman Royal — Boeing 747-400",                "country": "Oman",          "owner": "Sultan of Oman"},
    "A4O-OMF":  {"label": "Oman Royal Flight",                          "country": "Oman",          "owner": "Sultan of Oman"},
    "A4O-AHH":  {"label": "Oman Royal — Boeing 747-400",                "country": "Oman",          "owner": "Sultan of Oman"},
    "A4O-AA":   {"label": "Oman Royal Flight",                          "country": "Oman",          "owner": "Sultan of Oman"},

    # ── EGYPT ────────────────────────────────────────────────────
    "SU-EGY":   {"label": "Egypt Government — Boeing 747-8",            "country": "Egypt",         "owner": "President El-Sisi"},
    "SU-ADD":   {"label": "Egypt Government — Airbus A340-200",         "country": "Egypt",         "owner": "Egyptian Government"},

    # ── TURKEY ───────────────────────────────────────────────────
    "TC-TRK":   {"label": "Turkey Presidential — Boeing 747-8 BBJ",     "country": "Turkey",        "owner": "President Erdogan"},
    "TC-TUR":   {"label": "Turkey Government — Airbus A330-200",        "country": "Turkey",        "owner": "Turkish Government"},
    "TC-ANK":   {"label": "Turkey Government — Airbus A318 CJ",         "country": "Turkey",        "owner": "Turkish Government"},
    "TC-IST":   {"label": "Turkey Government — Airbus A319 CJ",         "country": "Turkey",        "owner": "Turkish Government"},
    "TC-CAN":   {"label": "Turkey Government — Airbus A340",            "country": "Turkey",        "owner": "Turkish Government"},
    "TC-CBK":   {"label": "Turkey Government — Gulfstream G550",        "country": "Turkey",        "owner": "Turkish Government"},
    "TC-DAP":   {"label": "Turkey Government — Gulfstream G550",        "country": "Turkey",        "owner": "Turkish Government"},
    "TC-GAP":   {"label": "Turkey Government — Gulfstream G-IV",        "country": "Turkey",        "owner": "Turkish Government"},
    "TC-ATA":   {"label": "Turkey Government — Gulfstream G550",        "country": "Turkey",        "owner": "Turkish Government"},

    # ── IRAN ─────────────────────────────────────────────────────
    "EP-IGA":   {"label": "Iran Government — Airbus A340-300",          "country": "Iran",          "owner": "Iranian Government"},
    "EP-AJA":   {"label": "Iran Government — Airbus A340-300 (Meraj)",  "country": "Iran",          "owner": "Iranian Government"},
    "EP-AJB":   {"label": "Iran Government — Airbus A321",              "country": "Iran",          "owner": "Iranian Government / Khamenei"},
    "EP-SHF":   {"label": "Iran Government — Dassault Falcon 50",       "country": "Iran",          "owner": "Iranian Government"},

    # ── IRAQ ─────────────────────────────────────────────────────
    "YI-APW":   {"label": "Iraq Government — Boeing 737-800",           "country": "Iraq",          "owner": "Iraqi Government"},
    "YI-AQW":   {"label": "Iraq Government BBJ",                        "country": "Iraq",          "owner": "Iraqi Government"},

    # ── SYRIA ────────────────────────────────────────────────────
    "YK-ATA":   {"label": "Syria Government — Ilyushin Il-76",          "country": "Syria",         "owner": "Syrian Government"},

    # ── YEMEN ────────────────────────────────────────────────────
    "7O-VIP":   {"label": "Yemen Government — Boeing 757-200",          "country": "Yemen",         "owner": "Yemeni Government"},
    "7O-YMN":   {"label": "Yemen Government — Boeing 747SP",            "country": "Yemen",         "owner": "Yemeni Government"},

    # ── LEBANON ──────────────────────────────────────────────────
    "OD-MRL":   {"label": "Lebanon President — MEA Airbus A320",        "country": "Lebanon",       "owner": "Lebanese President / PM"},
    "T7-MEP":   {"label": "Lebanon — MEA Airbus A319",                  "country": "Lebanon",       "owner": "Lebanese Government"},

    # ── UK ───────────────────────────────────────────────────────
    "ZZ336":    {"label": "UK RAF Voyager A330 — PM Transport",         "country": "UK",            "owner": "UK Prime Minister"},

    # ── FRANCE ───────────────────────────────────────────────────
    "F-RARF":   {"label": "France Presidential — Airbus A330-200",      "country": "France",        "owner": "French President Macron"},

    # ── UKRAINE ──────────────────────────────────────────────────
    "UR-ABA":   {"label": "Ukraine — Zelenskyy Airbus ACJ319",          "country": "Ukraine",       "owner": "President Zelenskyy"},
}

# ══════════════════════════════════════════════════════════════════
#  18 KEY MIDDLE EAST AIRPORTS
# ══════════════════════════════════════════════════════════════════
ME_AIRPORTS = {
    "LLBG": {"name": "Tel Aviv Ben Gurion",     "country": "Israel",        "city": "Tel Aviv"},
    "OERK": {"name": "Riyadh King Khalid",      "country": "Saudi Arabia",  "city": "Riyadh"},
    "OEJN": {"name": "Jeddah King Abdulaziz",   "country": "Saudi Arabia",  "city": "Jeddah"},
    "OMDB": {"name": "Dubai International",     "country": "UAE",           "city": "Dubai"},
    "OMAA": {"name": "Abu Dhabi International", "country": "UAE",           "city": "Abu Dhabi"},
    "OMDW": {"name": "Dubai Al Maktoum",        "country": "UAE",           "city": "Dubai"},
    "OTHH": {"name": "Doha Hamad",              "country": "Qatar",         "city": "Doha"},
    "OKBK": {"name": "Kuwait International",    "country": "Kuwait",        "city": "Kuwait"},
    "OBBI": {"name": "Bahrain International",   "country": "Bahrain",       "city": "Manama"},
    "OJAI": {"name": "Amman Queen Alia",        "country": "Jordan",        "city": "Amman"},
    "ORBI": {"name": "Baghdad International",   "country": "Iraq",          "city": "Baghdad"},
    "ORER": {"name": "Erbil International",     "country": "Iraq",          "city": "Erbil"},
    "OIIE": {"name": "Tehran Imam Khomeini",    "country": "Iran",          "city": "Tehran"},
    "OIII": {"name": "Tehran Mehrabad",         "country": "Iran",          "city": "Tehran"},
    "OLBA": {"name": "Beirut Rafic Hariri",     "country": "Lebanon",       "city": "Beirut"},
    "HECA": {"name": "Cairo International",     "country": "Egypt",         "city": "Cairo"},
    "LTFM": {"name": "Istanbul Airport",        "country": "Turkey",        "city": "Istanbul"},
    "OOMS": {"name": "Muscat International",    "country": "Oman",          "city": "Muscat"},
}

ME_ICAO_SET      = set(ME_AIRPORTS.keys())
KNOWN_VIP_REGS   = set(VIP_AIRCRAFT.keys())

# ── ME countries (VIP aircraft from these always kept) ────────────
ME_COUNTRIES = {
    "Israel","Saudi Arabia","UAE","Qatar","Kuwait","Bahrain",
    "Jordan","Iraq","Iran","Lebanon","Egypt","Turkey","Oman",
    "Syria","Yemen","Palestine",
}

# ── Commercial airline prefixes to DROP ───────────────────────────
COMMERCIAL_PREFIXES = {
    "EK","QR","EY","GF","MS","RJ","TK","ME","IR","IA","IY",
    "SV","FZ","G9","WY","XY","F3","LH","BA","AF","KL","IB",
    "AA","UA","DL","WN","FR","U2","VY","W6","MH","AI","SQ",
    "CX","NH","JL","KE","OZ","CA","MU","CZ","HU","ET","KQ",
    "SA","LA","AV","CM","AM","AC","QF","NZ","GA","EW","SK",
    "AY","AZ","TP","LX","OS","SN","BT","LO","OK","JU","RO",
    "HY","KC","S7","U6","SU","UT","UN","WB","XK","PC","W4",
    "HV","VN","OA","A3","BW","PK","UL","UX","TG","MF","CI",
}

# ── VIP government callsign prefixes — always KEEP ───────────────
VIP_CALLSIGN_PREFIXES = {
    "OMM","SVA","QAF","BAH","KUG","UAE","AUH","IRN",
    "IPF","EGY","TRK","RJA","OMAN","ORF",
}

# ── Private jet model keywords ────────────────────────────────────
PRIVATE_MODELS = [
    "gulfstream","global express","global 5","global 6","global 7",
    "challenger","citation","learjet","falcon","phenom","lineage",
    "hawker","pilatus","embraer legacy","embraer lineage",
    "boeing business jet","bbj","airbus corporate jet","acj",
    "g550","g650","g700","g450","g350","g280","g150","g600","g500",
    "cl300","cl350","cl600","cl604","cl605","cl650",
    "gl5000","gl6000","gl7000","gl7500",
    "f900","f7x","f8x","f2th","falcon 50","falcon 900",
    "c510","c525","c560","c680","c700","c750",
]

# ── Airport coordinates for arc drawing ───────────────────────────
AIRPORT_COORDS = {
    "LLBG":(32.0055,34.8854),"OERK":(24.9578,46.6988),"OEJN":(21.6796,39.1565),
    "OMDB":(25.2528,55.3644),"OMAA":(24.4330,54.6511),"OMDW":(24.8960,55.1614),
    "OTHH":(25.2731,51.6081),"OKBK":(29.2267,47.9689),"OBBI":(26.2708,50.6336),
    "OJAI":(31.7226,35.9932),"ORBI":(33.2625,44.2346),"ORER":(36.2376,43.9632),
    "OIIE":(35.4161,51.1522),"OIII":(35.6892,51.3151),"OLBA":(33.8208,35.4883),
    "HECA":(30.1219,31.4056),"LTFM":(41.2753,28.7519),"OOMS":(23.5933,58.2844),
    "EDDB":(52.3514,13.4939),"LIDC":(41.7994,12.5949),"LSZH":(47.4582,8.5482),
    "LSGG":(46.2370,6.1089),"EGLL":(51.4775,-0.4614),"EGSS":(51.8850,0.2350),
    "LFPG":(49.0097,2.5477),"EHAM":(52.3086,4.7639),"LEMD":(40.4936,-3.5668),
    "LEBL":(41.2971,2.0785),"LGAV":(37.9364,23.9445),"LMML":(35.8575,14.4775),
    "UUEE":(55.9726,37.4146),"ZBAA":(40.0799,116.5845),"VIDP":(28.5562,77.1000),
    "RJTT":(35.5493,139.7798),"FACT":(33.9648,18.6017),"FAOR":(-26.1367,28.2460),
    "WSSS":(1.3502,103.9943),"RKSI":(37.4602,126.4407),"LTAC":(40.1282,32.9951),
    "OKBK":(29.2267,47.9689),"OBBI":(26.2708,50.6336),"OTHH":(25.2731,51.6081),
}

def get_coords(icao):
    return AIRPORT_COORDS.get(icao, (None, None))

def day_num(date_str):
    return (datetime.strptime(date_str,"%Y-%m-%d") - WAR_START).days + 1

# ══════════════════════════════════════════════════════════════════
#  CLASSIFY AIRPORT FLIGHT
# ══════════════════════════════════════════════════════════════════
def classify_flight(flight):
    reg      = ((flight.get("aircraft") or {}).get("reg") or "").upper().strip()
    callsign = (flight.get("callSign") or "").upper().strip()
    model    = ((flight.get("aircraft") or {}).get("model") or "").lower().strip()
    is_cargo = flight.get("isCargo", False)

    if is_cargo:
        return False, None

    if reg in KNOWN_VIP_REGS:
        return True, "VIP_KNOWN"

    for prefix in VIP_CALLSIGN_PREFIXES:
        if callsign.startswith(prefix):
            return True, "VIP_CALLSIGN"

    if len(callsign) >= 2 and callsign[:2] in COMMERCIAL_PREFIXES:
        return False, None
    if len(callsign) >= 3 and callsign[:3] in COMMERCIAL_PREFIXES:
        return False, None

    for keyword in PRIVATE_MODELS:
        if keyword in model:
            return True, "PRIVATE_JET"

    return False, None

# ══════════════════════════════════════════════════════════════════
#  STEP 1 — FETCH VIP AIRCRAFT BY REGISTRATION
# ══════════════════════════════════════════════════════════════════
def step1_fetch_vip():
    print("=" * 70)
    print("STEP 1 — Fetching VIP/head-of-state flights by registration")
    print(f"         {len(VIP_AIRCRAFT)} aircraft | Full war period in one call each")
    print("=" * 70)

    flights = []
    found   = 0

    for reg, info in VIP_AIRCRAFT.items():
        url = (f"https://aerodatabox.p.rapidapi.com/flights/reg/{reg}"
               f"/2026-02-28T00:00/2026-03-27T23:59")
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200 and r.text and r.text not in ['null','']:
                raw = r.json()
                raw = raw if isinstance(raw, list) else raw.get('flights', [])
                if raw:
                    found += 1
                    for f in raw:
                        flights.append(parse_vip_flight(f, reg, info))
                    print(f"  ✓ {len(raw):2d} flights | {info['label']} ({reg})")
                else:
                    print(f"  —          | {info['label']} ({reg})")
            else:
                print(f"  —          | {info['label']} ({reg})")
        except Exception as e:
            print(f"  ✗ Error    | {reg}: {e}")
        time.sleep(0.35)

    print(f"\n  Aircraft with data : {found}/{len(VIP_AIRCRAFT)}")
    print(f"  Flights found      : {len(flights)}")
    return flights

def parse_vip_flight(f, reg, info):
    dep    = f.get('departure', {})
    arr    = f.get('arrival',   {})
    dep_ap = dep.get('airport', {})
    arr_ap = arr.get('airport', {})
    dep_loc= dep_ap.get('location', {})
    arr_loc= arr_ap.get('location', {})
    dep_time = dep.get('scheduledTime', {}).get('utc', '')
    arr_time = arr.get('scheduledTime', {}).get('utc', '')
    date_str = (arr_time or dep_time or '')[:10]

    dep_lat = dep_loc.get('lat') or get_coords(dep_ap.get('icao',''))[0]
    dep_lon = dep_loc.get('lon') or get_coords(dep_ap.get('icao',''))[1]
    arr_lat = arr_loc.get('lat') or get_coords(arr_ap.get('icao',''))[0]
    arr_lon = arr_loc.get('lon') or get_coords(arr_ap.get('icao',''))[1]

    return {
        "reg":          reg,
        "callsign":     (f.get('callSign') or '').strip(),
        "flight_num":   f.get('number',''),
        "model":        (f.get('aircraft') or {}).get('model',''),
        "category":     "VIP_KNOWN",
        "label":        info['label'],
        "owner":        info['owner'],
        "country":      info['country'],
        "status":       f.get('status',''),
        "dep_icao":     dep_ap.get('icao',''),
        "dep_name":     dep_ap.get('name',''),
        "dep_city":     dep_ap.get('municipalityName','') or dep_ap.get('name',''),
        "dep_country":  dep_ap.get('countryCode',''),
        "dep_lat":      dep_lat,
        "dep_lon":      dep_lon,
        "dep_time_utc": dep_time,
        "dep_runway":   dep.get('runway',''),
        "dep_gate":     dep.get('gate',''),
        "arr_icao":     arr_ap.get('icao',''),
        "arr_name":     arr_ap.get('name',''),
        "arr_city":     arr_ap.get('municipalityName','') or arr_ap.get('name',''),
        "arr_country":  arr_ap.get('countryCode',''),
        "arr_lat":      arr_lat,
        "arr_lon":      arr_lon,
        "arr_time_utc": arr_time,
        "arr_runway":   arr.get('runway',''),
        "arr_gate":     arr.get('gate',''),
        "date":         date_str,
        "day_of_war":   day_num(date_str) if date_str else 0,
        "source":       "vip_registration",
    }

# ══════════════════════════════════════════════════════════════════
#  STEP 2 — QUERY ALL ME AIRPORTS FOR PRIVATE JETS + VIP
# ══════════════════════════════════════════════════════════════════
def step2_fetch_airports():
    print("\n" + "=" * 70)
    print("STEP 2 — Querying all ME airports for private jets + VIP")
    print(f"         {len(ME_AIRPORTS)} airports × 28 days × 2 windows")
    print("=" * 70)

    flights = []
    cur     = WAR_START

    while cur <= WAR_END:
        date_str = cur.strftime("%Y-%m-%d")
        dn       = day_num(date_str)
        day_kept = 0

        for icao, info in ME_AIRPORTS.items():
            for window, (start_h, end_h) in [("am",("00:00","11:59")),("pm",("12:00","23:59"))]:
                url    = (f"https://aerodatabox.p.rapidapi.com/flights/airports/icao"
                          f"/{icao}/{date_str}T{start_h}/{date_str}T{end_h}")
                params = {"withLeg":"true","withCancelled":"true","direction":"Both"}
                try:
                    r    = requests.get(url, headers=HEADERS, params=params, timeout=15)
                    data = r.json() if r.status_code == 200 else {}
                    for fl in data.get("departures",[]):
                        p = parse_airport_flight(fl, icao, info, "dep", date_str)
                        if p:
                            flights.append(p)
                            day_kept += 1
                    for fl in data.get("arrivals",[]):
                        p = parse_airport_flight(fl, icao, info, "arr", date_str)
                        if p:
                            flights.append(p)
                            day_kept += 1
                except Exception as e:
                    print(f"    ⚠ {icao} {date_str} {window}: {e}")
                time.sleep(0.35)

        print(f"  D{dn:02d} {date_str}: {day_kept:4d} private/VIP flights kept")
        cur += timedelta(days=1)

    print(f"\n  Total airport flights: {len(flights)}")
    return flights

def parse_airport_flight(flight, airport_icao, airport_info, direction, date_str):
    keep, category = classify_flight(flight)
    if not keep:
        return None

    mov     = flight.get("movement", {})
    ap      = mov.get("airport", {})
    sched   = mov.get("scheduledTime", {})
    revised = mov.get("revisedTime",   {})
    loc     = ap.get("location", {})

    reg     = ((flight.get("aircraft") or {}).get("reg") or "").upper()
    model   = ((flight.get("aircraft") or {}).get("model") or "")
    cs      = (flight.get("callSign") or "").strip()
    stime   = sched.get("utc","")
    rtime   = revised.get("utc","")

    # Get known VIP info if registration matches
    vip_info = VIP_AIRCRAFT.get(reg, {})
    label    = vip_info.get("label", f"Private — {model}" if model else "Private Jet")
    owner    = vip_info.get("owner", "")
    country  = vip_info.get("country", airport_info["country"] if direction=="dep" else "")

    other_lat = loc.get("lat") or get_coords(ap.get("icao",""))[0]
    other_lon = loc.get("lon") or get_coords(ap.get("icao",""))[1]
    this_lat, this_lon = get_coords(airport_icao)

    if direction == "dep":
        dep_icao,dep_city,dep_country = airport_icao,airport_info["city"],airport_info["country"]
        dep_lat,dep_lon,dep_time      = this_lat,this_lon,stime
        dep_runway,dep_gate           = mov.get("runway",""),mov.get("gate","")
        arr_icao  = ap.get("icao","")
        arr_city  = ap.get("municipalityName","") or ap.get("name","")
        arr_country = ap.get("countryCode","")
        arr_lat,arr_lon,arr_time      = other_lat,other_lon,""
        arr_runway,arr_gate           = "","";arr_name=ap.get("name","")
        dep_name  = airport_info["name"]
    else:
        dep_icao  = ap.get("icao","")
        dep_name  = ap.get("name","")
        dep_city  = ap.get("municipalityName","") or ap.get("name","")
        dep_country = ap.get("countryCode","")
        dep_lat,dep_lon,dep_time      = other_lat,other_lon,""
        dep_runway,dep_gate           = "","";
        arr_icao,arr_city,arr_country = airport_icao,airport_info["city"],airport_info["country"]
        arr_lat,arr_lon,arr_time      = this_lat,this_lon,stime
        arr_runway = mov.get("runway",""); arr_gate=mov.get("gate","")
        arr_name   = airport_info["name"]

    dn = day_num(date_str)

    return {
        "reg":          reg,
        "callsign":     cs,
        "flight_num":   flight.get("number",""),
        "model":        model,
        "category":     category,
        "label":        label,
        "owner":        owner,
        "country":      country,
        "status":       flight.get("status",""),
        "direction":    direction,
        "airport_icao": airport_icao,
        "airport_name": airport_info["name"],
        "airport_city": airport_info["city"],
        "airport_country": airport_info["country"],
        "dep_icao":     dep_icao,
        "dep_name":     dep_name,
        "dep_city":     dep_city,
        "dep_country":  dep_country,
        "dep_lat":      dep_lat,
        "dep_lon":      dep_lon,
        "dep_time_utc": dep_time,
        "dep_runway":   dep_runway,
        "dep_gate":     dep_gate,
        "arr_icao":     arr_icao,
        "arr_name":     arr_name,
        "arr_city":     arr_city,
        "arr_country":  arr_country,
        "arr_lat":      arr_lat,
        "arr_lon":      arr_lon,
        "arr_time_utc": arr_time,
        "arr_runway":   arr_runway,
        "arr_gate":     arr_gate,
        "date":         date_str,
        "day_of_war":   dn,
        "source":       "airport_query",
    }

# ══════════════════════════════════════════════════════════════════
#  STEP 3 — MERGE, FILTER ME-RELEVANT, DEDUPLICATE
# ══════════════════════════════════════════════════════════════════
def step3_merge(vip_flights, airport_flights):
    print("\n" + "=" * 70)
    print("STEP 3 — Merging, filtering ME-relevant, deduplicating")
    print("=" * 70)

    ME_CITY_SET = {
        "Tel Aviv","Jerusalem","Riyadh","Jeddah","Dubai","Abu Dhabi",
        "Doha","Kuwait","Manama","Amman","Baghdad","Erbil","Tehran",
        "Beirut","Cairo","Istanbul","Ankara","Muscat","Salalah",
        "Sanaa","Aden","Damascus","Aleppo","Gaza","Ramallah","Mosul",
    }

    def is_me_relevant(fl):
        if fl.get("country","") in ME_COUNTRIES:
            return True
        for icao in [fl.get("dep_icao",""), fl.get("arr_icao","")]:
            if icao[:2] in {"OI","OJ","OK","OL","OM","OO","OR","OS","OT",
                            "OY","LL","HE","LT","OB"}:
                return True
        for city in [fl.get("dep_city",""), fl.get("arr_city","")]:
            if city in ME_CITY_SET:
                return True
        return False

    # Filter VIP flights for ME relevance
    vip_me   = [f for f in vip_flights if is_me_relevant(f)]
    dropped  = len(vip_flights) - len(vip_me)
    print(f"  VIP flights        : {len(vip_flights)} → {len(vip_me)} kept ({dropped} non-ME dropped)")

    all_flights = vip_me + airport_flights
    print(f"  Combined total     : {len(all_flights)}")

    # Deduplicate
    seen    = set()
    deduped = []
    for fl in all_flights:
        key = (
            fl.get("reg",""),
            fl.get("date",""),
            fl.get("dep_icao",""),
            fl.get("arr_icao",""),
            (fl.get("dep_time_utc","") or fl.get("arr_time_utc",""))[:13],
        )
        if key not in seen:
            seen.add(key)
            deduped.append(fl)

    deduped.sort(key=lambda f: (
        f.get("date",""),
        f.get("dep_time_utc","") or f.get("arr_time_utc","")
    ))
    print(f"  After dedup        : {len(deduped)}")
    return deduped

# ══════════════════════════════════════════════════════════════════
#  STEP 4 — BUILD DAILY SUMMARY AND SAVE
# ══════════════════════════════════════════════════════════════════
def step4_save(flights):
    print("\n" + "=" * 70)
    print("STEP 4 — Building daily summary and saving")
    print("=" * 70)

    by_day  = defaultdict(list)
    for fl in flights:
        d = fl.get("day_of_war", 0)
        if d > 0:
            by_day[d].append(fl)

    daily_summary = {}
    for dn in sorted(by_day.keys()):
        day_flights  = by_day[dn]
        date_str     = (WAR_START + timedelta(days=dn-1)).strftime("%Y-%m-%d")
        vip_count    = sum(1 for f in day_flights if f.get("category")=="VIP_KNOWN")
        private_count= sum(1 for f in day_flights if f.get("category")=="PRIVATE_JET")
        countries    = list({f.get("country","") for f in day_flights if f.get("country")})
        daily_summary[date_str] = {
            "day_of_war":    dn,
            "total_flights": len(day_flights),
            "vip_count":     vip_count,
            "private_count": private_count,
            "countries":     countries,
        }

    result = {
        "fetched_at":      datetime.now().isoformat(),
        "source":          "AeroDataBox Mega — VIP registrations + ME airport queries",
        "war_start":       "2026-02-28",
        "war_end":         "2026-03-27",
        "airports_queried":list(ME_AIRPORTS.keys()),
        "vip_aircraft":    VIP_AIRCRAFT,
        "total_flights":   len(flights),
        "vip_flights":     sum(1 for f in flights if f.get("category")=="VIP_KNOWN"),
        "private_flights": sum(1 for f in flights if f.get("category")=="PRIVATE_JET"),
        "flights":         flights,
        "daily_summary":   daily_summary,
        "by_day":          {str(k): v for k,v in by_day.items()},
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"✓ COMPLETE")
    print(f"  Total flights   : {len(flights)}")
    print(f"  VIP/government  : {result['vip_flights']}")
    print(f"  Private jets    : {result['private_flights']}")
    print(f"  Days covered    : {len(daily_summary)}")
    print(f"  Saved → {OUTPUT_PATH}")
    print(f"  File size       : {os.path.getsize(OUTPUT_PATH)/1024:.0f} KB")
    print()
    print("Daily summary:")
    for date_str, s in sorted(daily_summary.items()):
        print(f"  D{s['day_of_war']:02d} {date_str}: "
              f"{s['total_flights']:4d} total | "
              f"{s['vip_count']:2d} VIP | "
              f"{s['private_count']:3d} private")

# ═════════════════════════════════════════════════════════════════# ═══════════════════════════════════════════════════════════════
#  MAIN — INCREMENTAL MODE
#  First run : fetches full history, saves to OUTPUT_PATH
#  Later runs: loads file, only fetches NEW days since last save
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Load existing file if present
    existing_flights = []
    fetch_from = WAR_START

    if os.path.exists(OUTPUT_PATH):
        try:
            with open(OUTPUT_PATH, encoding="utf-8") as f:
                existing = json.load(f)
            existing_flights = existing.get("flights", [])
            dates_in_file = sorted({
                fl.get("date","") for fl in existing_flights if fl.get("date","")
            })
            if dates_in_file:
                latest_dt  = datetime.strptime(dates_in_file[-1], "%Y-%m-%d")
                fetch_from = latest_dt + timedelta(days=1)
                print(f"\nINCREMENTAL MODE — {len(existing_flights)} flights already saved")
                print(f"  Latest date in file : {dates_in_file[-1]}")
                print(f"  Fetching new days from: {fetch_from.strftime('%Y-%m-%d')}")
            if fetch_from > today:
                print("\n✓ File is already up to date — nothing to fetch")
                _SKIP_FETCH = True
        except Exception as e:
            print(f"⚠ Could not read existing file ({e}), fetching full history")
            existing_flights = []
            fetch_from = WAR_START
    else:
        print(f"\nNo existing file — fetching full history from {WAR_START.date()}")

    # Skip if already up to date
    if not globals().get('_SKIP_FETCH', False):
        # Override date range to only fetch new days
        _orig_start, _orig_end = WAR_START, WAR_END
        WAR_START = fetch_from
        WAR_END   = today

        vip_flights     = step1_fetch_vip()
        airport_flights = step2_fetch_airports()
        new_flights     = step3_merge(vip_flights, airport_flights)

        WAR_START, WAR_END = _orig_start, _orig_end  # restore

        # Merge with existing and save
        all_flights = existing_flights + new_flights
        print(f"\n  Existing: {len(existing_flights)} | New: {len(new_flights)} | Total: {len(all_flights)}")
        step4_save(all_flights)
    else:
        _SKIP_FETCH = False  # reset for next run