# c05_war_data.py
# WAR_DATA builder (events.csv)
# Auto-extracted from Cell 5

######################################################################
# CELL 4 — WAR_DATA builder
# Middle East Conflict Situational Room
# Loads events.csv and builds structured event list
# for the Cesium globe timeline
# Dynamic geocoding via Nominatim for unmatched locations
######################################################################

import pandas as pd, os, math, json, time, requests
from datetime import datetime, timezone
from collections import Counter

DATASET_PATH        = os.path.join(DATA_DIR, "events.csv")
GEOCODE_CACHE_PATH  = os.path.join(CACHE_DIR, "ifs_geocode_cache.json")

# ── Location coordinates ──────────────────────────────────────────
# Comprehensive Middle East coverage + all locations in dataset
# Any location NOT found here is auto-geocoded via Nominatim
COORDS = {
    # ── IRAN ─────────────────────────────────────────────────────
    "Iran":(32.00,53.00),
    "Iran (multiple cities)":(32.00,53.00),
    "Iran (nationwide)":(32.00,53.00),
    "Iranian territory":(36.00,45.00),
    "Tehran":(35.69,51.39),
    "Tehran, Iran":(35.69,51.39),
    "Tehran / Karaj, Iran":(35.69,51.20),
    "Tehran and Karaj":(35.69,51.20),
    "Isfahan":(32.66,51.68),
    "Isfahan, Iran":(32.66,51.68),
    "Natanz":(33.72,51.73),
    "Natanz, Isfahan":(33.72,51.73),
    "Qom":(34.64,50.88),
    "Fordow, Qom Province":(34.92,50.98),
    "Bushehr":(28.92,50.84),
    "Bushehr, Iran":(28.92,50.84),
    "South Pars gas field, Bushehr Province":(27.15,52.60),
    "Borazjan, Bushehr":(29.27,51.21),
    "Shiraz":(29.59,52.58),
    "Shiraz, Fars":(29.59,52.58),
    "Shiraz / Fars province":(29.59,52.58),
    "Tabriz":(38.08,46.30),
    "Tabriz, East Azerbaijan":(38.08,46.30),
    "Tabriz, Iran":(38.08,46.30),
    "Bandar Abbas":(27.18,56.27),
    "Bandar Abbas, Hormozgan":(27.18,56.27),
    "Bandar Abbas, Iran":(27.18,56.27),
    "Bandar Anzali, Gilan":(37.47,49.46),
    "Bandar-e Anzali / Caspian Sea":(37.47,49.46),
    "Bandar Jask, Hormozgan":(25.65,57.77),
    "Bandar Lengeh, Hormozgan":(26.56,54.88),
    "Ahvaz, Khuzestan":(31.32,48.67),
    "Ahvaz / Konarak / Arak, Iran":(31.32,48.67),
    "Khuzestan":(31.00,49.00),
    "Khorramshahr, Khuzestan":(30.43,48.18),
    "Khorramabad, Lorestan":(33.49,48.36),
    "Masjed Soleyman, Khuzestan":(31.94,49.29),
    "Andimeshk, Khuzestan":(32.46,48.35),
    "Dasht-e Azadegan, Khuzestan":(31.50,48.00),
    "Dezful, Khuzestan":(32.38,48.40),
    "Kharg Island":(29.25,50.32),
    "Kharg Island, Iran":(29.25,50.32),
    "Karaj, Alborz":(35.84,50.94),
    "Fardis, Alborz":(35.73,50.91),
    "Garmdareh, Alborz":(35.83,50.83),
    "Mehrshahr, Karaj":(35.84,50.86),
    "Mohammadshahr, Alborz":(35.74,50.87),
    "Absard, Tehran Province":(35.77,52.35),
    "Eslamshahr, Tehran Province":(35.55,51.24),
    "Shahriar, Tehran Province":(35.66,51.06),
    "Vardavard, Tehran Province":(35.69,50.90),
    "Rey, Tehran Province":(35.60,51.44),
    "Shahr-e Rey, Tehran Province":(35.60,51.44),
    "Afsariyeh, Tehran":(35.60,51.47),
    "Javadieh neighborhood, Tehran":(35.65,51.36),
    "Saadat Abad, Tehran":(35.80,51.38),
    "Sohrevardi district, Tehran":(35.73,51.42),
    "Airbases across Iran":(32.00,53.00),
    "Kerman":(30.28,57.08),
    "Kermanshah":(34.32,47.07),
    "Paveh, Kermanshah":(34.98,46.36),
    "Ravansar, Kermanshah":(34.72,46.66),
    "Salas-e Babajani, Kermanshah":(34.91,45.87),
    "Sarpol-e Zahab, Kermanshah":(34.46,45.87),
    "Ta'avon Township, Kermanshah":(34.35,47.06),
    "Zanganeh, Kermanshah":(34.32,47.10),
    "Hamadan":(34.80,48.52),
    "Joulan, Hamadan":(34.82,48.50),
    "Malayer, Hamadan":(34.30,48.83),
    "Ilam":(33.64,46.43),
    "Mehran, Ilam":(33.12,46.17),
    "Semnan":(35.57,53.40),
    "Shahmirzad, Semnan":(35.77,53.33),
    "Yazd":(31.89,54.37),
    "Qazvin":(36.27,50.00),
    "Lamerd":(27.34,53.18),
    "Lar, Fars":(27.68,54.34),
    "Minab":(27.09,57.08),
    "Minab, Hormozgan":(27.09,57.08),
    "Hormuz Island, Iran":(27.06,56.46),
    "Greater Tunb Island, Hormozgan":(26.26,55.32),
    "Qeshm Island, Hormozgan":(26.76,55.80),
    "Qeshm / Shiraz / Tehran":(26.76,55.80),
    "Abu Musa Island, Hormozgan":(25.87,55.03),
    "Chabahar, Sistan and Baluchestan":(25.29,60.64),
    "Konarak, Sistan and Baluchestan":(25.36,60.39),
    "Nikshahr, Sistan and Baluchestan":(26.22,60.22),
    "Birjand, South Khorasan":(32.86,59.22),
    "Kashan, Isfahan":(33.98,51.44),
    "Khomein, Markazi":(33.72,50.09),
    "Khomein / Bandar Lengeh / Tehran":(33.72,50.09),
    "Khomeinishahr, Isfahan":(32.69,51.52),
    "Mobarakeh, Isfahan":(32.35,51.50),
    "Najafabad, Isfahan":(32.64,51.36),
    "Nobriz, Isfahan":(32.21,51.48),
    "Aran and Bidgol, Isfahan":(34.06,51.49),
    "Zarrin Shahr, Isfahan":(32.39,51.38),
    "Shahin Shahr, Isfahan":(32.86,51.54),
    "Dashti Village, Isfahan":(32.00,51.00),
    "Azarshahr, East Azerbaijan":(37.76,45.98),
    "Mahabad, West Azerbaijan":(36.77,45.72),
    "Miandoab, West Azerbaijan":(36.97,46.10),
    "Sardasht, West Azerbaijan":(36.16,45.48),
    "Shahin Dezh, West Azerbaijan":(36.68,46.57),
    "Urmia, West Azerbaijan":(37.55,45.07),
    "Kamyaran, Kurdistan":(34.79,46.93),
    "Marivan, Kurdistan":(35.52,46.18),
    "Sanandaj, Kurdistan":(35.32,47.00),
    "Saqqez, Kurdistan":(36.25,46.27),
    "Sarab, East Azerbaijan":(37.94,47.54),
    "Caspian Sea, Iran":(37.50,50.50),
    "Falak-ol-Aflak fortress":(33.49,48.35),
    "Qom, Kermanshah, Isfahan, Karaj":(33.50,50.00),

    # ── IRAQ ─────────────────────────────────────────────────────
    "Baghdad":(33.34,44.40),
    "Baghdad, Iraq":(33.34,44.40),
    "Iraq / Erbil / Baghdad":(34.00,44.50),
    "Erbil":(36.19,44.01),
    "Basra":(30.51,47.82),
    "Mosul":(36.34,43.13),
    "Kirkuk":(35.47,44.39),
    "Sulaymaniyah":(35.56,45.44),
    "Najaf":(32.00,44.34),
    "Karbala":(32.62,44.03),
    "Fallujah":(33.35,43.79),
    "Ramadi":(33.43,43.30),
    "Jurf al-Sakhar":(32.65,44.15),
    "Mala Qara, Iraqi Kurdistan":(35.86,44.39),
    "Rabi'a, Ninewa Province":(36.97,42.09),
    "Western Iraq":(33.00,42.00),
    "Iraqi coast":(29.90,48.50),
    "US Embassy Baghdad":(33.32,44.42),

    # ── ISRAEL / PALESTINE ────────────────────────────────────────
    "Israel":(31.50,34.90),
    "Tel Aviv":(32.08,34.78),
    "Tel Aviv, Israel":(32.08,34.78),
    "Jerusalem":(31.77,35.22),
    "Jerusalem, Israel":(31.77,35.22),
    "Jerusalem Old City, Israel":(31.78,35.23),
    "Haifa":(32.82,35.00),
    "Haifa, Israel":(32.82,35.00),
    "Haifa Bay area, Northern Israel":(32.87,35.00),
    "Northern Israel":(33.00,35.50),
    "Northern Border, Israel":(33.09,35.40),
    "Upper Galilee, Northern Israel":(33.10,35.50),
    "Kiryat Shmona, Northern Israel":(33.21,35.57),
    "Mahanayim Junction, Northern Israel":(32.97,35.57),
    "Zarzir, Israel":(32.71,35.19),
    "Yehud":(32.03,34.89),
    "Beit Shemesh":(31.75,34.99),
    "Beersheba":(31.25,34.79),
    "Eilat":(29.56,34.95),
    "Arad, Israel":(31.26,35.21),
    "Arad / Dimona / Eilat / Beersheba / Kiryat Gat":(31.25,34.79),
    "Dimona, Israel":(31.07,35.03),
    "Ramat Gan, Israel":(32.08,34.81),
    "Israel, UAE, Qatar, Kuwait, Bahrain, Jordan, Saudi Arabia":(28.00,46.00),
    "Gaza Strip":(31.35,34.31),
    "Gaza":(31.35,34.31),
    "Ramallah":(31.90,35.21),
    "Jenin":(32.46,35.30),
    "Hebron":(31.53,35.10),
    "Nablus":(32.22,35.26),
    "West Bank":(31.90,35.20),
    "West Bank / Hebron / Sharon":(31.90,35.20),
    "Haris, Northern West Bank":(32.17,35.07),

    # ── LEBANON ──────────────────────────────────────────────────
    "Lebanon":(33.89,35.50),
    "Beirut":(33.89,35.50),
    "Beirut, Lebanon":(33.89,35.50),
    "Beirut / southern Lebanon":(33.50,35.50),
    "Beddawi, Lebanon":(34.46,35.83),
    "Beqaa Valley, Lebanon":(33.85,35.90),
    "Lebanon (Serghaya)":(33.62,36.13),
    "Lebanon (south)":(33.10,35.40),
    "Lebanon (southern border)":(33.07,35.35),
    "Southern Lebanon":(33.10,35.40),
    "Nabi Chit, Beqaa Valley":(33.90,35.97),
    "Qantara, Lebanon":(33.10,35.35),
    "Qasmiyeh Bridge, Southern Lebanon":(33.21,35.26),
    "Tripoli, Lebanon":(34.44,35.83),
    "Sidon":(33.56,35.37),
    "Tyre":(33.27,35.20),

    # ── SYRIA ────────────────────────────────────────────────────
    "Syria":(34.80,38.99),
    "Damascus":(33.51,36.29),
    "Aleppo":(36.20,37.16),
    "Homs":(34.74,36.72),
    "Deir ez-Zor":(35.34,40.14),
    "Idlib":(35.93,36.63),
    "Latakia":(35.52,35.79),
    "Inkhil, Syria":(32.94,36.19),

    # ── JORDAN ───────────────────────────────────────────────────
    "Jordan":(31.00,36.00),
    "Amman":(31.95,35.93),
    "Aqaba":(29.53,35.00),
    "Muwaffaq Salti Air Base, Jordan":(31.83,36.78),

    # ── SAUDI ARABIA ─────────────────────────────────────────────
    "Saudi Arabia":(24.00,45.00),
    "Riyadh":(24.69,46.72),
    "Riyadh, Saudi Arabia":(24.69,46.72),
    "Jeddah":(21.49,39.19),
    "Mecca":(21.39,39.86),
    "Medina":(24.47,39.61),
    "Dhahran":(26.31,50.13),
    "Dammam":(26.43,50.10),
    "Ras Tanura":(26.64,50.16),
    "Al-Kharj":(24.15,47.33),
    "Prince Sultan Air Base":(24.06,47.58),
    "King Khalid International Airport":(24.96,46.70),

    # ── YEMEN ────────────────────────────────────────────────────
    "Yemen":(15.55,48.52),
    "Sanaa":(15.35,44.21),
    "Hodeidah":(14.80,42.95),
    "Aden":(12.78,45.04),
    "Marib":(15.47,45.33),
    "Taiz":(13.58,44.02),
    "Mukalla":(14.54,49.13),

    # ── UAE ──────────────────────────────────────────────────────
    "UAE":(24.00,54.00),
    "Abu Dhabi":(24.47,54.37),
    "Abu Dhabi Shah oil field":(23.15,53.55),
    "Dubai":(25.20,55.27),
    "Dubai International Airport":(25.25,55.36),
    "Al Dhafra Air Base":(24.25,54.55),
    "Al Ruwais, UAE":(24.11,52.73),
    "Fujairah":(25.12,56.34),
    "Umm Al Quwain":(25.56,55.55),
    "Habshan, Abu Dhabi":(23.67,53.73),
    "Near Zayed International Airport, Abu Dhabi":(24.44,54.65),
    "Palm Jumeirah / Burj Al Arab area, Dubai":(25.12,55.18),
    "Corniche / Al Dhafra / Bateen districts, Abu Dhabi":(24.48,54.37),
    "UAE energy installation":(24.47,54.37),

    # ── KUWAIT ───────────────────────────────────────────────────
    "Kuwait":(29.37,47.98),
    "Kuwait City":(29.37,47.98),
    "Kuwait airspace":(29.50,47.80),
    "Ali Al Salem Air Base":(29.34,47.69),
    "Mina al-Ahmadi, Kuwait":(29.07,48.16),
    "Port Shuaiba":(29.04,48.17),
    "Salman Industrial City, Manama":(26.13,50.55),

    # ── BAHRAIN ──────────────────────────────────────────────────
    "Bahrain":(26.22,50.59),
    "Manama":(26.22,50.59),
    "Muharraq Island":(26.27,50.65),

    # ── QATAR ────────────────────────────────────────────────────
    "Qatar":(25.35,51.18),
    "Doha":(25.29,51.53),
    "Al Udeid Air Base":(25.12,51.31),
    "Qatar airspace":(25.50,51.20),
    "QatarEnergy (Ras Laffan)":(25.90,51.57),
    "Ras Laffan, Qatar":(25.90,51.57),

    # ── OMAN ─────────────────────────────────────────────────────
    "Oman":(21.00,57.00),
    "Muscat, Oman":(23.61,58.59),
    "Port Muscat area":(23.61,58.59),
    "Khasab, Oman":(26.18,56.25),
    "Port of Salalah, Oman":(17.01,54.09),
    "Duqm, Oman":(19.67,57.70),
    "Sohar":(24.34,56.74),

    # ── TURKEY ───────────────────────────────────────────────────
    "Turkey":(39.00,35.00),
    "Ankara":(39.93,32.86),
    "Istanbul":(41.01,28.97),
    "Adana / Incirlik":(37.00,35.32),
    "Gaziantep":(37.06,37.38),
    "Hatay, Turkey":(36.70,36.10),
    "Dörtyol, Hatay":(36.86,36.22),

    # ── EGYPT ────────────────────────────────────────────────────
    "Egypt":(26.82,30.80),
    "Cairo":(30.04,31.24),
    "Alexandria":(31.19,29.91),
    "Sinai":(29.50,34.50),
    "Sharm el-Sheikh":(27.91,34.33),
    "Suez Canal":(30.50,32.35),

    # ── STRATEGIC / MARITIME ─────────────────────────────────────
    "Strait of Hormuz":(26.59,56.47),
    "Gulf":(26.00,54.00),
    "Gulf of Oman":(24.50,58.00),
    "Gulf region":(26.00,52.00),
    "Arabian Sea":(18.00,65.00),
    "Red Sea / Gulf of Aden":(15.00,43.00),
    "Red Sea":(20.00,38.00),
    "Caspian Sea":(41.50,50.50),
    "Near Cyprus":(34.80,33.20),
    "Akrotiri, Cyprus":(34.58,32.97),
    "International":(26.00,54.00),

    # ── MILITARY BASES ───────────────────────────────────────────
    "Diego Garcia, Indian Ocean":(-7.32,72.42),

    # ── OTHER COUNTRIES ──────────────────────────────────────────
    "Baku":(40.41,49.87),
    "Nakhchivan":(39.21,45.41),
    "Near Galle, Sri Lanka":(6.03,80.22),
    "Sri Lanka waters":(7.00,80.50),
    "Kochi, India":(9.93,76.27),
    "Paris, France":(48.86,2.35),
    "Geneva, Switzerland":(46.20,6.15),
    "Washington D.C., USA":(38.90,-77.03),
    "US (cyber)":(38.90,-77.03),
    "Air Force One":(32.00,-80.00),
}

# ══════════════════════════════════════════════════════════════════
#  DYNAMIC GEOCODING — Nominatim (OpenStreetMap)
#  Auto-resolves any location not found in COORDS above
#  Results cached to ~/.ifs_geocode_cache.json (persists across runs)
# ══════════════════════════════════════════════════════════════════

def load_geocode_cache():
    if os.path.exists(GEOCODE_CACHE_PATH):
        try:
            with open(GEOCODE_CACHE_PATH) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_geocode_cache(cache):
    try:
        with open(GEOCODE_CACHE_PATH, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"      ⚠ Geocode cache write failed: {e}")

def geocode_location(loc, cache):
    if loc in cache:
        return tuple(cache[loc])
    try:
        url    = "https://nominatim.openstreetmap.org/search"
        params = {"q": loc, "format": "json", "limit": 1}
        headers = {"User-Agent": "MiddleEastSitRoom/1.0"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(1)  # Nominatim rate limit: 1 request/second
        results = r.json()
        if results:
            lat = float(results[0]["lat"])
            lon = float(results[0]["lon"])
            cache[loc] = [lat, lon]
            save_geocode_cache(cache)
            print(f"      ✓ Geocoded: {loc} → ({lat:.3f}, {lon:.3f})")
            return (lat, lon)
    except Exception as e:
        print(f"      ⚠ Geocode failed for '{loc}': {e}")
    # Fallback — centre of Middle East
    cache[loc] = [29.00, 50.00]
    save_geocode_cache(cache)
    return (29.00, 50.00)

# ── Event type → system type + colour mapping ─────────────────────
TYPE_MAP = {
    "Airstrike":        ("airstrike",    "#ff2200"),
    "Missile Strike":   ("missile",      "#ff4400"),
    "Drone Strike":     ("retaliation",  "#ff8800"),
    "Naval Attack":     ("naval",        "#0088ff"),
    "Assassination":    ("assassination","#cc0066"),
    "Interception":     ("retaliation",  "#ffaa00"),
    "Ground Operation": ("ground",       "#ff6600"),
    "Cyber Attack":     ("airstrike",    "#00e5ff"),
    "Friendly Fire":    ("retaliation",  "#aaaaaa"),
    "Rocket Attack":    ("missile",      "#ff6600"),
    "Other":            ("airstrike",    "#888888"),
}

def build_war_data(path):
    print(f"[CELL 4] Loading {path}")
    if not os.path.exists(path):
        print(f"  ✗ File not found: {path}")
        return {"events":[],"count":0,"t_start":"","t_end":""}

    df = pd.read_csv(path, parse_dates=["date","datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)
    df = df[df["date"] >= (pd.Timestamp(WAR_START_STR) - pd.Timedelta(days=1))].copy()
    print(f"  ✓ {len(df)} rows loaded")

    GEOCODE_CACHE = load_geocode_cache()
    events        = []
    geocoded      = 0
    unresolved    = []

    for i, row in df.iterrows():
        ts  = pd.Timestamp(row["datetime"]).strftime("%Y-%m-%dT%H:%M:%SZ")
        loc = str(row.get("location","Unknown")).strip()

        # 1. Exact match in COORDS
        if loc in COORDS:
            lat, lon = COORDS[loc]
        else:
            # 2. Try stripping country suffix
            loc_short = loc.split(",")[0].strip()
            if loc_short in COORDS:
                lat, lon = COORDS[loc_short]
            # 3. Check geocode cache
            elif loc in GEOCODE_CACHE:
                lat, lon = tuple(GEOCODE_CACHE[loc])
            # 4. Auto-geocode via Nominatim
            else:
                lat, lon = geocode_location(loc, GEOCODE_CACHE)
                geocoded += 1
                if (lat, lon) == (29.00, 50.00):
                    unresolved.append(loc)

        etype         = str(row.get("event_type","Other"))
        sys_type, col = TYPE_MAP.get(etype, ("airstrike","#888888"))
        day_num       = int(row.get("day_of_war", 1))

        events.append({
            "id":       f"D{day_num:03d}-{i:04d}",
            "t":        ts,
            "date":     ts[:10],
            "label":    f"[Day {day_num}] {str(row.get('description',''))[:70]}",
            "type":     sys_type,
            "col":      col,
            "lat":      lat,
            "lon":      lon,
            "location": loc,
            "actors":   str(row.get("actor","Unknown")),
            "detail":   str(row.get("description","")),
            "killed":   int(row.get("killed",0) or 0),
            "injured":  int(row.get("injured",0) or 0),
            "day":      day_num,
            "url":      "",
        })

    events.sort(key=lambda e: e["t"])

    # Jitter overlapping coordinates so dots don't stack
    coord_count = {}
    for ev in events:
        key = (round(ev["lat"],3), round(ev["lon"],3))
        coord_count[key] = coord_count.get(key,0) + 1
    coord_idx = {}
    for ev in events:
        key = (round(ev["lat"],3), round(ev["lon"],3))
        if coord_count[key] > 1:
            idx = coord_idx.get(key,0); coord_idx[key] = idx+1
            if idx > 0:
                angle = (idx-1) * 137.5 * math.pi / 180
                r = 0.018 * (0.4 + 0.15*(idx-1))
                ev["lat"] = round(ev["lat"] + r*math.cos(angle), 5)
                ev["lon"] = round(ev["lon"] + r*math.sin(angle), 5)

    # Summary
    print(f"  ✓ {len(events) - geocoded} locations matched from COORDS")
    if geocoded:
        print(f"  ✓ {geocoded} locations auto-geocoded via Nominatim")
    if unresolved:
        print(f"  ⚠ {len(unresolved)} locations could not be resolved (fallback used):")
        for u in sorted(set(unresolved)):
            print(f"    {u}")

    ts_counts = Counter(ev["t"] for ev in events)
    concurrent = sum(1 for c in ts_counts.values() if c>1)
    if concurrent:
        print(f"  ✓ {concurrent} timestamps with concurrent events — handled by jitter")
    else:
        print("  ✓ All timestamps unique")

    wd = {
        "events":  events,
        "count":   len(events),
        "t_start": events[0]["t"]  if events else "",
        "t_end":   events[-1]["t"] if events else "",
    }
    print(f"\n[CELL 4] ✓ {len(events)} events ready")
    print(f"         t_start : {wd['t_start']}")
    print(f"         t_end   : {wd['t_end']}")
    return wd

WIKI_DATA = {
    "fetched_at": datetime.now(timezone.utc).isoformat(),
    "source":     "events.csv",
    "count":      0,
    "events":     [],
}
WAR_DATA = build_war_data(DATASET_PATH)

# ── Load vessel attacks dataset ───────────────────────────────────
import csv as _csv
_avp = os.path.join(DATA_DIR, "vessels-attack-dataset.txt")
if os.path.exists(_avp):
    with open(_avp, 'r', encoding='utf-8') as _f:
        _av_list = list(_csv.DictReader(_f))
    ATTACKED_VESSELS_DATA = {
        "vessels": _av_list,
        "records": _av_list,
        "count": len(_av_list),
        "total_killed": sum(int(r.get('killed',0) or 0) for r in _av_list),
        "total_injured": sum(int(r.get('injured',0) or 0) for r in _av_list),
    }
    print(f"\n  ✓ ATTACKED_VESSELS_DATA: {len(_av_list)} vessel attacks loaded")
else:
    ATTACKED_VESSELS_DATA = {"vessels":[],"records":[],"count":0}
    print(f"\n  ⚠ vessels-attack-dataset.txt not found at {_avp}")

print("\n         Run Cell 5 next")

######################################################################
# ► NEXT CELL: Cell 5 — GPS Jamming
######################################################################