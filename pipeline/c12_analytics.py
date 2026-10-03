# c12_analytics.py
# Analytics intelligence extraction
# Auto-extracted from Cell 12

######################################################################
# CELL 9 — Analytics Intelligence Extraction
#
# Extracts intelligence patterns from ALL data sources:
#   A. War Escalation Arc        (iran_war_clean.csv)
#   B. Political Trajectory      (political-events.csv)
#   C. GPS Jamming Patterns      (GPSJAM_DATA)
#   D. Maritime Intelligence     (MARINE_DATA + ATTACKED_VESSELS_DATA)
#   E. Flight Intelligence       (FLIGHT_HIST_DATA)
#   F. ISR Satellite Activity    (HIST_SAT_DATA + SAT_DATA)
#   G. Composite Threat Score    (all modules)
#
# OUTPUTS: 7 global dicts consumed by Cell 14 (page) + Cell 16 (report)
######################################################################

import math, os
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

WAR_START = datetime.strptime(WAR_START_STR, "%Y-%m-%d")
WAR_DAY0  = WAR_START - timedelta(days=1)
WAR_DAY0_STR = WAR_DAY0.strftime("%Y-%m-%d")

print("=" * 60)
print("CELL 9 — Analytics Intelligence Extraction")
print("=" * 60)

# ── Helpers ──────────────────────────────────────────────────────
def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    d = math.radians
    a = math.sin(d(lat2-lat1)/2)**2 + math.cos(d(lat1))*math.cos(d(lat2))*math.sin(d(lon2-lon1)/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def _date_of_day(n):
    return (WAR_START + timedelta(days=n-1)).strftime("%Y-%m-%d")

def _day_of_date(s):
    try: return (datetime.strptime(str(s)[:10], "%Y-%m-%d") - WAR_DAY0).days
    except: return None

def _sf(v, default=0.0):
    try: return float(v)
    except: return default

EVT_W = {
    "airstrike":10, "missile_strike":10, "drone_strike":7,
    "naval_attack":8, "assassination":12, "ground_operation":9,
    "rocket_attack":6, "cyber_attack":5, "interception":3,
    "friendly_fire":2, "other":2,
}

DIR_W = {"Escalatory":+10, "De-escalatory":-8, "Neutral":0}
SIG_W = {"Critical":15, "High":10, "Medium":5, "Low":2}


# ══════════════════════════════════════════════════════════════════
# A. WAR ESCALATION ARC
# ══════════════════════════════════════════════════════════════════
print("\n[A] War Escalation Arc...")

war_events = globals().get("WAR_DATA",{}).get("events",[]) if isinstance(globals().get("WAR_DATA"),dict) else []
if not war_events:
    print("  ⚠ WAR_DATA missing — run Cell 4 first")

# ── A1: Daily breakdown by weapon type ───────────────────────────
# Parse country from location field
# WAR_DATA locations are "City, Country" or just "Country" or "Strait of Hormuz" etc
_COUNTRY_MAP = {
    "iran":"Iran","israel":"Israel","lebanon":"Lebanon","iraq":"Iraq",
    "syria":"Syria","yemen":"Yemen","bahrain":"Bahrain","kuwait":"Kuwait",
    "qatar":"Qatar","uae":"UAE","oman":"Oman","turkey":"Turkey",
    "jordan":"Jordan","saudi arabia":"Saudi Arabia","saudi":"Saudi Arabia",
    "cyprus":"Cyprus","egypt":"Egypt","uk":"UK","india":"India",
    "azerbaijan":"Azerbaijan","palestine":"Palestine","gaza":"Palestine",
    "international":"International","gulf":"Gulf",
}
# Location keywords → country
_LOC_KEYWORDS = {
    "tehran":"Iran","isfahan":"Iran","qom":"Iran","shiraz":"Iran","tabriz":"Iran",
    "bushehr":"Iran","bandar":"Iran","kharg":"Iran","karaj":"Iran","mashhad":"Iran",
    "abadan":"Iran","kermanshah":"Iran","natanz":"Iran","fordow":"Iran","arak":"Iran",
    "parchin":"Iran","iran":"Iran",
    "tel aviv":"Israel","haifa":"Israel","jerusalem":"Israel","negev":"Israel",
    "dimona":"Israel","ashdod":"Israel","eilat":"Israel","beer":"Israel",
    "beirut":"Lebanon","beqaa":"Lebanon","nabatieh":"Lebanon","sidon":"Lebanon",
    "tyre":"Lebanon","tripoli, lebanon":"Lebanon","south lebanon":"Lebanon",
    "baghdad":"Iraq","basra":"Iraq","erbil":"Iraq","anbar":"Iraq","tikrit":"Iraq",
    "mosul":"Iraq","karbala":"Iraq","najaf":"Iraq",
    "damascus":"Syria","aleppo":"Syria","homs":"Syria","deir":"Syria",
    "abu dhabi":"UAE","dubai":"UAE","fujairah":"UAE","sharjah":"UAE",
    "jebel ali":"UAE","al dhafra":"UAE",
    "riyadh":"Saudi Arabia","jeddah":"Saudi Arabia","dhahran":"Saudi Arabia",
    "aramco":"Saudi Arabia","ras tanura":"Saudi Arabia","yanbu":"Saudi Arabia",
    "manama":"Bahrain","muharraq":"Bahrain",
    "doha":"Qatar","al udeid":"Qatar",
    "kuwait city":"Kuwait","ali al salem":"Kuwait","bubiyan":"Kuwait",
    "muscat":"Oman","duqm":"Oman","masirah":"Oman",
    "hormuz":"International","strait":"International",
    "akrotiri":"Cyprus","larnaca":"Cyprus",
    "amman":"Jordan","aqaba":"Jordan",
    "sanaa":"Yemen","aden":"Yemen","hodeidah":"Yemen","marib":"Yemen",
    "mumbai":"India","new delhi":"India",
    "gaza":"Palestine",
}

# Bounding boxes for coordinate-based country detection
_COUNTRY_BOXES = [
    ("Iran",          25.0, 40.0, 44.0, 63.5),
    ("Iraq",          29.0, 37.5, 38.5, 48.5),
    ("Israel",        29.4, 33.4, 34.2, 35.9),
    ("Palestine",     31.2, 31.6, 34.2, 34.6),  # Gaza
    ("Lebanon",       33.0, 34.7, 35.0, 36.7),
    ("Syria",         32.3, 37.3, 35.7, 42.4),
    ("Jordan",        29.2, 33.4, 34.9, 39.3),
    ("Saudi Arabia",  16.0, 32.2, 34.5, 55.7),
    ("Kuwait",        28.5, 30.1, 46.5, 48.5),
    ("Bahrain",       25.8, 26.3, 50.3, 50.7),
    ("Qatar",         24.5, 26.2, 50.7, 51.7),
    ("UAE",           22.6, 26.1, 51.5, 56.4),
    ("Oman",          16.6, 26.4, 52.0, 59.8),
    ("Yemen",         12.0, 19.0, 42.0, 54.0),
    ("Turkey",        35.8, 42.1, 26.0, 44.8),
    ("Egypt",         22.0, 31.7, 24.7, 36.9),
    ("Cyprus",        34.5, 35.7, 32.2, 34.6),
    ("India",          6.7, 35.5, 68.1, 97.4),
    ("Azerbaijan",    38.4, 41.9, 44.8, 50.4),
    ("UK",            49.9, 60.9, -8.2,  1.8),
]

def _country_from_coords(lat, lon):
    """Primary: use lat/lon to determine country."""
    if lat is None or lon is None: return None
    try:
        lat, lon = float(lat), float(lon)
    except: return None
    if lat == 0 and lon == 0: return None
    for name, lat_min, lat_max, lon_min, lon_max in _COUNTRY_BOXES:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return name
    return None

def _country_from_loc(loc):
    """Fallback: parse country from location string."""
    loc_str = str(loc).strip()
    if not loc_str: return "Unknown"
    if "," in loc_str:
        after_comma = loc_str.split(",")[-1].strip().lower()
        if after_comma in _COUNTRY_MAP:
            return _COUNTRY_MAP[after_comma]
    if "(" in loc_str:
        before_paren = loc_str.split("(")[0].strip().lower()
        if before_paren in _COUNTRY_MAP:
            return _COUNTRY_MAP[before_paren]
    loc_lower = loc_str.lower()
    for keyword, country in _LOC_KEYWORDS.items():
        if keyword in loc_lower:
            return country
    if loc_lower in _COUNTRY_MAP:
        return _COUNTRY_MAP[loc_lower]
    return loc_str

def _resolve_country(ev):
    """Use coords first, then location string, then 'Unknown'."""
    c = _country_from_coords(ev.get("lat"), ev.get("lon"))
    if c: return c
    return _country_from_loc(ev.get("location",""))

war_by_day = defaultdict(list)
for ev in war_events:
    d = int(_sf(ev.get("day", _day_of_date(ev.get("date",""))), 0))
    if d >= 0:
        # Inject parsed country field for downstream use
        # Determine country: coords first, then location string
        ev["country"] = _resolve_country(ev)
        war_by_day[d].append(ev)

max_war_day = max(war_by_day.keys()) if war_by_day else 28

esc_days = []
for day in range(0, max_war_day + 1):
    evs = war_by_day.get(day, [])
    n = len(evs)
    killed  = sum(int(_sf(e.get("killed",0))) for e in evs)
    injured = sum(int(_sf(e.get("injured",0))) for e in evs)

    # Event types
    types = defaultdict(int)
    for e in evs:
        t = str(e.get("type","other")).lower().replace(" ","_")
        types[t] += 1

    # Actors
    actors = defaultdict(int)
    for e in evs:
        a = str(e.get("actors",e.get("actor","Unknown")))
        actors[a] += 1

    # Countries hit
    countries = defaultdict(int)
    for e in evs:
        c = str(e.get("country",""))
        if c: countries[c] += 1

    # Severity score
    score = sum(EVT_W.get(t, EVT_W["other"]) * cnt for t,cnt in types.items())
    score += min(killed * 2 + injured * 0.5, 50)
    score = round(score)

    esc_days.append({
        "day":       day,
        "date":      _date_of_day(day) if day > 0 else WAR_DAY0_STR,
        "n":         n,
        "killed":    killed,
        "injured":   injured,
        "score":     score,
        "types":     dict(types),
        "actors":    dict(actors),
        "countries": dict(countries),
    })

# Trend
scores = [d["score"] for d in esc_days]
counts = [d["n"] for d in esc_days]
avg_sc  = sum(scores)/len(scores) if scores else 0
peak_sc = max(scores) if scores else 0
peak_day= scores.index(peak_sc) if scores else 0

first7 = sum(scores[:7]) if len(scores)>=7 else sum(scores[:max(1,len(scores)//2)])
last7  = sum(scores[-7:]) if len(scores)>=7 else sum(scores[max(1,len(scores)//2):])
trend  = "escalating" if last7>first7*1.1 else ("de-escalating" if last7<first7*0.9 else "stable")
surge_days = [d["day"] for d in esc_days if d["n"] > (sum(counts)/max(len(counts),1))*2]

# ── A2: Who hit whom (actor → country matrix) ───────────────────
who_hit_whom = defaultdict(int)
for ev in war_events:
    actor = str(ev.get("actors",ev.get("actor","Unknown")))
    country = str(ev.get("country","Unknown"))
    if actor and country:
        who_hit_whom[(actor, country)] += 1

who_hit_whom_list = sorted(
    [{"actor":k[0], "target_country":k[1], "count":v}
     for k,v in who_hit_whom.items()],
    key=lambda x: -x["count"]
)

# ── A3: Country event ranking ────────────────────────────────────
country_totals = defaultdict(lambda:{"events":0,"killed":0,"injured":0})
for ev in war_events:
    c = str(ev.get("country","Unknown"))
    country_totals[c]["events"] += 1
    country_totals[c]["killed"] += int(_sf(ev.get("killed",0)))
    country_totals[c]["injured"] += int(_sf(ev.get("injured",0)))

country_ranking = sorted(
    [{"country":k, **v} for k,v in country_totals.items()],
    key=lambda x: -x["events"]
)

# ── A4: Country-over-time heatmap data ───────────────────────────
country_day_matrix = {}
all_war_countries = sorted(country_totals.keys(), key=lambda c: -country_totals[c]["events"])
for d in esc_days:
    for c in all_war_countries[:14]:  # top 14 countries
        if c not in country_day_matrix:
            country_day_matrix[c] = []
        country_day_matrix[c].append(d["countries"].get(c, 0))

ESCALATION_ANALYSIS = {
    "days":              esc_days,
    "max_day":           max_war_day,
    "peak_day":          peak_day,
    "peak_score":        peak_sc,
    "avg_score":         round(avg_sc,1),
    "trend":             trend,
    "surge_days":        surge_days,
    "total_killed":      sum(d["killed"] for d in esc_days),
    "total_injured":     sum(d["injured"] for d in esc_days),
    "who_hit_whom":      who_hit_whom_list[:30],
    "country_ranking":   country_ranking,
    "country_day_matrix":country_day_matrix,
    "all_countries":     all_war_countries[:14],
}

print(f"  ✓ {max_war_day} days | {len(war_events)} events | trend={trend} | peak=D{peak_day}")
print(f"    Top attacker→target: {who_hit_whom_list[0]['actor']}→{who_hit_whom_list[0]['target_country']} ({who_hit_whom_list[0]['count']})" if who_hit_whom_list else "")


# ══════════════════════════════════════════════════════════════════
# B. POLITICAL TRAJECTORY
# ══════════════════════════════════════════════════════════════════
print("\n[B] Political Trajectory...")

POL_CSV = os.path.join(DATA_DIR, "political-events.csv")
pol_events = []
try:
    pol_df = pd.read_csv(POL_CSV, encoding="utf-8")
    pol_df["escalation_direction"] = pol_df["escalation_direction"].fillna("Neutral")
    pol_df["significance"] = pol_df["significance"].fillna("Medium")
    pol_events = pol_df.to_dict(orient="records")
    print(f"  Loaded {len(pol_events)} political events")
except Exception as e:
    print(f"  ✗ {e}")

# ── B1: Daily political pressure + cumulative line ───────────────
pol_by_day = defaultdict(list)
for ev in pol_events:
    d = int(_sf(ev.get("day_of_war", _day_of_date(ev.get("date",""))), 0))
    pol_by_day[d].append(ev)

pol_days = []
cumulative = 0.0
max_pol_day = max(pol_by_day.keys()) if pol_by_day else 0

for day in range(0, max_pol_day+1):
    evs = pol_by_day.get(day, [])
    if not evs:
        pol_days.append({
            "day": day, "date": _date_of_day(day) if day>0 else WAR_DAY0_STR,
            "n": 0, "esc_count": 0, "de_esc_count": 0, "neut_count": 0,
            "day_score": 0, "cumulative": round(cumulative,1),
            "war_phase": "", "actors": [], "high_sig": [],
        })
        continue

    esc    = [e for e in evs if str(e.get("escalation_direction","")).strip()=="Escalatory"]
    de_esc = [e for e in evs if str(e.get("escalation_direction","")).strip()=="De-escalatory"]
    neut   = [e for e in evs if str(e.get("escalation_direction","")).strip()=="Neutral"]

    day_score = 0.0
    for ev in evs:
        dw = DIR_W.get(str(ev.get("escalation_direction","Neutral")).strip(), 0)
        sw = SIG_W.get(str(ev.get("significance","Medium")).strip(), 5)
        day_score += dw * (sw / 10.0)
    cumulative += day_score

    # Get war phase for this day
    phases = [str(e.get("war_phase","")) for e in evs if e.get("war_phase")]
    phase = phases[0] if phases else ""

    pol_days.append({
        "day":           day,
        "date":          _date_of_day(day) if day>0 else WAR_DAY0_STR,
        "n":             len(evs),
        "esc_count":     len(esc),
        "de_esc_count":  len(de_esc),
        "neut_count":    len(neut),
        "day_score":     round(day_score,1),
        "cumulative":    round(cumulative,1),
        "war_phase":     phase,
        "actors":        list({str(e.get("actor","")) for e in evs if e.get("actor","")}),
        "high_sig":      [{"desc": str(e.get("description",""))[:200],
                           "actor": str(e.get("actor","")),
                           "direction": str(e.get("escalation_direction","")),
                           "type": str(e.get("event_type",""))}
                          for e in evs
                          if str(e.get("significance","")).strip() in ("High","Critical")],
    })

pol_trend = ("net escalatory" if cumulative > 5 else
             "net de-escalatory" if cumulative < -5 else "mixed")

# ── B2: Key milestones (High + Critical) ────────────────────────
milestones = []
for ev in pol_events:
    if str(ev.get("significance","")).strip() in ("High","Critical"):
        milestones.append({
            "day":       int(_sf(ev.get("day_of_war",0))),
            "date":      str(ev.get("date",""))[:10],
            "actor":     str(ev.get("actor","")),
            "direction": str(ev.get("escalation_direction","")),
            "type":      str(ev.get("event_type","")),
            "desc":      str(ev.get("description",""))[:250],
            "phase":     str(ev.get("war_phase","")),
            "significance": str(ev.get("significance","")),
        })

# ── B3: Actor alignment over time ───────────────────────────────
alignment_by_day = defaultdict(lambda: defaultdict(int))
for ev in pol_events:
    d = int(_sf(ev.get("day_of_war",0)))
    alignment = str(ev.get("actor_alignment","Unknown")).strip()
    # Normalize alignments
    if "US-Israel" in alignment: alignment = "US-Israel Coalition"
    elif "Iran" in alignment and "Neutral" not in alignment: alignment = "Iran-Axis"
    elif "Neutral" in alignment or "Mediator" in alignment: alignment = "Neutral/Mediator"
    else: alignment = "International/Other"
    alignment_by_day[d][alignment] += 1

alignment_days = []
for day in range(0, max_pol_day+1):
    alignment_days.append({
        "day": day,
        "US-Israel Coalition": alignment_by_day[day].get("US-Israel Coalition",0),
        "Iran-Axis":           alignment_by_day[day].get("Iran-Axis",0),
        "Neutral/Mediator":    alignment_by_day[day].get("Neutral/Mediator",0),
        "International/Other": alignment_by_day[day].get("International/Other",0),
    })

# ── B4: Diplomatic actor ranking ────────────────────────────────
actor_stats = defaultdict(lambda:{"n":0,"esc":0,"de_esc":0,"neut":0,"domains":set(),"alignment":""})
for ev in pol_events:
    a  = str(ev.get("actor","Unknown")).strip()
    dw = str(ev.get("escalation_direction","Neutral")).strip()
    dm = str(ev.get("domain","")).strip()
    al = str(ev.get("actor_alignment","")).strip()
    actor_stats[a]["n"]     += 1
    actor_stats[a]["domains"].add(dm)
    actor_stats[a]["alignment"] = al
    if dw=="Escalatory":    actor_stats[a]["esc"]    += 1
    if dw=="De-escalatory": actor_stats[a]["de_esc"] += 1
    if dw=="Neutral":       actor_stats[a]["neut"]   += 1

top_actors = sorted(
    [{"actor":k, "n":v["n"], "esc":v["esc"], "de_esc":v["de_esc"], "neut":v["neut"],
      "domains":list(v["domains"]), "alignment":v["alignment"]}
     for k,v in actor_stats.items()],
    key=lambda x: -x["n"]
)[:20]

# ── B5: Contradiction alerts ────────────────────────────────────
contradictions = []
for pd_day in pol_days:
    day = pd_day["day"]
    if day <= 0: continue
    wd = next((d for d in esc_days if d["day"]==day), None)
    if not wd: continue
    if wd["score"] > avg_sc*1.4 and pd_day["de_esc_count"] > 0:
        contradictions.append({
            "day":       day,
            "date":      pd_day["date"],
            "war_score": wd["score"],
            "war_events":wd["n"],
            "de_esc":    pd_day["de_esc_count"],
            "esc":       pd_day["esc_count"],
            "label":     f"D{day}: {wd['n']} strikes + {pd_day['de_esc_count']} peace signals",
        })

# ── B6: Domain breakdown ────────────────────────────────────────
domain_counts = defaultdict(int)
for ev in pol_events:
    dm = str(ev.get("domain","Unknown")).strip()
    if dm and dm != "nan": domain_counts[dm] += 1

domain_breakdown = sorted(
    [{"domain":k, "count":v} for k,v in domain_counts.items()],
    key=lambda x: -x["count"]
)

# ── B7: War phase timeline ──────────────────────────────────────
phase_ranges = {}
for ev in pol_events:
    phase = str(ev.get("war_phase","")).strip()
    d = int(_sf(ev.get("day_of_war",0)))
    date = str(ev.get("date",""))[:10]
    if phase and phase != "nan":
        if phase not in phase_ranges:
            phase_ranges[phase] = {"start_day":d, "end_day":d, "start_date":date, "end_date":date, "count":0}
        phase_ranges[phase]["end_day"] = max(phase_ranges[phase]["end_day"], d)
        phase_ranges[phase]["start_day"] = min(phase_ranges[phase]["start_day"], d)
        phase_ranges[phase]["end_date"] = date if d >= phase_ranges[phase]["end_day"] else phase_ranges[phase]["end_date"]
        phase_ranges[phase]["count"] += 1

# Order phases chronologically
phase_order = ["Pre-War","Shock and Awe","Early Attrition","Deep Attrition","Collapse","Stabilization","Active War"]
war_phases = []
for p in phase_order:
    if p in phase_ranges:
        war_phases.append({"phase":p, **phase_ranges[p]})

POLITICAL_ANALYSIS = {
    "days":               pol_days,
    "total_events":       len(pol_events),
    "trend":              pol_trend,
    "final_cumulative":   round(cumulative,1),
    "escalatory_total":   sum(d["esc_count"] for d in pol_days),
    "deescalatory_total": sum(d["de_esc_count"] for d in pol_days),
    "milestones":         milestones,
    "alignment_days":     alignment_days,
    "top_actors":         top_actors,
    "contradictions":     contradictions,
    "domain_breakdown":   domain_breakdown,
    "war_phases":         war_phases,
}

DIPLOMATIC_INDEX = {
    "contradictions":      contradictions,
    "contradiction_count": len(contradictions),
    "top_actors":          top_actors,
    "most_deescalatory":   sorted(top_actors, key=lambda x: -x["de_esc"])[:5],
}

print(f"  ✓ {len(pol_events)} events | trend={pol_trend} | {len(milestones)} milestones")
print(f"    Phases: {' → '.join(p['phase'] for p in war_phases)}")
print(f"    Contradictions: {len(contradictions)} days")
print(f"    Top actors: {[a['actor'][:25] for a in top_actors[:5]]}")


# ══════════════════════════════════════════════════════════════════
# C. GPS JAMMING PATTERNS
# ══════════════════════════════════════════════════════════════════
print("\n[C] GPS Jamming Patterns...")

jam_history = globals().get("GPSJAM_DATA",{}).get("history",[]) if isinstance(globals().get("GPSJAM_DATA"),dict) else []

# ── C1: Daily jamming intensity ──────────────────────────────────
jam_avg_by_date = {}
jam_daily = []
for day_data in jam_history:
    date = str(day_data.get("date",""))[:10]
    avg  = _sf(day_data.get("me_avg",0))
    top  = _sf(day_data.get("top_intensity",0))
    cells_data = day_data.get("cells",[])
    if date:
        jam_avg_by_date[date] = round(avg*100,1)
        jam_daily.append({
            "date":      date,
            "me_avg_pct":round(avg*100,1),
            "top_pct":   round(top*100,1),
            "cell_count":len(cells_data),
        })

# ── C2: Jamming by zone (if cell-level data exists) ─────────────
ZONE_BOXES = {
    "Hormuz":  {"lat_min":25.5,"lat_max":27.5,"lon_min":55.0,"lon_max":57.5},
    "Gulf":    {"lat_min":24.0,"lat_max":30.0,"lon_min":48.0,"lon_max":55.0},
    "Iraq":    {"lat_min":30.0,"lat_max":37.0,"lon_min":42.0,"lon_max":48.0},
    "Lebanon": {"lat_min":33.0,"lat_max":34.5,"lon_min":35.0,"lon_max":36.5},
    "Red Sea": {"lat_min":12.0,"lat_max":20.0,"lon_min":38.0,"lon_max":44.0},
    "Iran":    {"lat_min":25.0,"lat_max":40.0,"lon_min":44.0,"lon_max":64.0},
}

jam_by_zone = defaultdict(lambda: defaultdict(list))
has_cell_data = False
for day_data in jam_history:
    date = str(day_data.get("date",""))[:10]
    cells = day_data.get("cells",[])
    if cells:
        has_cell_data = True
        for cell in cells:
            clat = _sf(cell.get("lat",0))
            clon = _sf(cell.get("lon",0))
            inten = _sf(cell.get("intensity",0))
            for zone_name, box in ZONE_BOXES.items():
                if (box["lat_min"] <= clat <= box["lat_max"] and
                    box["lon_min"] <= clon <= box["lon_max"]):
                    jam_by_zone[zone_name][date].append(inten)

# Build zone daily averages
jam_zone_daily = {}
if has_cell_data:
    for zone_name in ZONE_BOXES:
        jam_zone_daily[zone_name] = []
        for day_data in jam_daily:
            date = day_data["date"]
            vals = jam_by_zone[zone_name].get(date, [])
            jam_zone_daily[zone_name].append({
                "date": date,
                "avg_pct": round(sum(vals)/len(vals)*100,1) if vals else 0,
                "cell_count": len(vals),
            })

# ── C3: Jamming vs strikes correlation ───────────────────────────
jam_corr_days = []
for d in esc_days:
    jam_avg = jam_avg_by_date.get(d["date"], 0.0)
    jam_corr_days.append({
        "day":      d["day"],
        "date":     d["date"],
        "events":   d["n"],
        "score":    d["score"],
        "jam_pct":  jam_avg,
        "high_jam": jam_avg > 5,
    })

high_jam = [d for d in jam_corr_days if d["high_jam"]]
low_jam  = [d for d in jam_corr_days if not d["high_jam"]]
avg_hi   = sum(d["events"] for d in high_jam)/len(high_jam) if high_jam else 0
avg_lo   = sum(d["events"] for d in low_jam)/len(low_jam)   if low_jam  else 0
correlates = avg_hi > avg_lo * 1.2

JAMMING_CORRELATION = {
    "daily":           jam_daily,
    "correlation_days":jam_corr_days,
    "high_jam_days":   len(high_jam),
    "avg_hi_events":   round(avg_hi,1),
    "avg_lo_events":   round(avg_lo,1),
    "correlates":      correlates,
    "has_cell_data":   has_cell_data,
    "zone_daily":      jam_zone_daily,
    "interpretation":  (
        "GPS jamming correlates with higher military activity — "
        "likely used as operational cover for strikes"
        if correlates else
        "No strong correlation between jamming and strikes detected"
    ),
}

print(f"  ✓ {len(jam_daily)} days | cell-level data: {has_cell_data}")
print(f"    High-jam days: {len(high_jam)} | avg events: {avg_hi:.0f} (hi) vs {avg_lo:.0f} (lo)")
if has_cell_data:
    for z in ZONE_BOXES:
        days_active = sum(1 for d in jam_zone_daily.get(z,[]) if d["avg_pct"] > 5)
        print(f"    {z:<12} {days_active} days with jamming")


# ══════════════════════════════════════════════════════════════════
# D. MARITIME INTELLIGENCE
# ══════════════════════════════════════════════════════════════════
print("\n[D] Maritime Intelligence...")

ZONES_DEF = [
    {"id":"hormuz",     "name":"Strait of Hormuz",       "lat":26.5,"lon":56.5},
    {"id":"gulf",       "name":"Persian Gulf",            "lat":26.0,"lon":51.5},
    {"id":"oman",       "name":"Gulf of Oman",            "lat":23.5,"lon":58.5},
    {"id":"red_sea",    "name":"Red Sea / Bab el-Mandeb", "lat":14.0,"lon":43.0},
    {"id":"arabian",    "name":"Arabian Sea",             "lat":18.0,"lon":62.0},
    {"id":"iraq_north", "name":"Northern Arabian Gulf",   "lat":29.8,"lon":48.8},
]

# Live marine data
live_zones     = {z["zone_id"]:z for z in globals().get("MARINE_DATA",{}).get("zones",[])}
all_vessels    = globals().get("MARINE_DATA",{}).get("vessels",[])
tankers        = globals().get("MARINE_DATA",{}).get("counts",{}).get("tankers",0)
moving_t       = len(globals().get("MARINE_DATA",{}).get("moving_tankers",[]))
stopped_t      = len(globals().get("MARINE_DATA",{}).get("stopped_tankers",[]))
hormuz_vessels = len(globals().get("MARINE_DATA",{}).get("hormuz_vessels",[]))
total_vessels  = globals().get("MARINE_DATA",{}).get("total",0)

tanker_disruption = round(stopped_t/tankers*100) if tankers>0 else 0

# ── D1: Vessels by flag in Hormuz ────────────────────────────────
hormuz_by_flag = defaultdict(int)
hormuz_by_type = defaultdict(int)
for v in all_vessels:
    if str(v.get("zone_id","")) == "hormuz":
        flag = str(v.get("flag","Unknown"))
        vtype = str(v.get("category","other"))
        hormuz_by_flag[flag] += 1
        hormuz_by_type[vtype] += 1

hormuz_flag_ranking = sorted([{"flag":k,"count":v} for k,v in hormuz_by_flag.items()], key=lambda x:-x["count"])

# ── D2: Vessel type per zone ────────────────────────────────────
zone_type_matrix = {}
for v in all_vessels:
    zid = str(v.get("zone_id","unknown"))
    vtype = str(v.get("category","other"))
    if zid not in zone_type_matrix:
        zone_type_matrix[zid] = defaultdict(int)
    zone_type_matrix[zid][vtype] += 1

# ── D3: Vessels going dark ──────────────────────────────────────
going_dark = [v for v in all_vessels if v.get("going_dark")]
going_dark_by_flag = defaultdict(int)
for v in going_dark:
    going_dark_by_flag[str(v.get("flag","Unknown"))] += 1

# ── D4: High-interest flag vessels ──────────────────────────────
high_interest = [v for v in all_vessels if v.get("high_interest")]
hi_by_flag = defaultdict(int)
for v in high_interest:
    hi_by_flag[str(v.get("flag","Unknown"))] += 1

# ── D5: Attacked vessels analysis ───────────────────────────────
av_data = globals().get("ATTACKED_VESSELS_DATA",{})
av_records = av_data.get("vessels", av_data.get("records", []))
av_by_zone = av_data.get("by_zone", {})
av_by_attacker = av_data.get("by_attacker", {})
av_by_damage = av_data.get("by_damage", {})
av_by_category = av_data.get("by_category", {})

# Attacked by flag
av_by_flag = defaultdict(int)
for r in av_records:
    f = str(r.get("flag","Unknown"))
    av_by_flag[f] += 1
av_flag_ranking = sorted([{"flag":k,"count":v} for k,v in av_by_flag.items()], key=lambda x:-x["count"])

# Attacked vessels timeline
av_timeline = defaultdict(int)
for r in av_records:
    d = int(_sf(r.get("day_of_war",0)))
    if d > 0: av_timeline[d] += 1

# Zone risk scores
recent_jam = jam_history[-5:] if len(jam_history)>=5 else jam_history
def _zone_jam(zlat, zlon, jam_days, radius=3.0):
    vals = []
    for day_data in jam_days:
        for cell in day_data.get("cells",[]):
            clat = _sf(cell.get("lat",0))
            clon = _sf(cell.get("lon",0))
            if abs(clat-zlat)<=radius and abs(clon-zlon)<=radius:
                vals.append(_sf(cell.get("intensity",0)))
    return round(sum(vals)/len(vals)*100,1) if vals else 0.0

zone_rows = []
for z in ZONES_DEF:
    atk = sum(len(v) for k,v in (av_by_zone if isinstance(av_by_zone,dict) else {}).items()
              if any(w in k for w in z["name"].split()))
    if atk==0:
        atk = sum(1 for r in av_records
                  if any(w in str(r.get("zone","")) for w in z["name"].split()[:2]))
    jam = _zone_jam(z["lat"], z["lon"], recent_jam)
    lz = live_zones.get(z["id"],{})
    live = lz.get("vessels_fetched",0)
    ltk = lz.get("tankers",0)
    risk = min(atk*8, 40) + min(jam*0.4, 20)
    if z["id"]=="hormuz":     risk += 30
    elif z["id"] in ("gulf","oman"): risk += 15
    elif z["id"]=="iraq_north":       risk += 20
    risk = min(int(risk),100)
    lvl = ("critical" if risk>=80 else "high" if risk>=60 else "medium" if risk>=40 else "low")
    zone_rows.append({
        "id": z["id"], "name": z["name"], "lat": z["lat"], "lon": z["lon"],
        "risk_score": risk, "risk_level": lvl, "attacks": atk,
        "jam_pct": jam, "live_vessels": live, "live_tankers": ltk,
        "type_breakdown": dict(zone_type_matrix.get(z["id"],{})),
    })

MARITIME_THREAT = {
    "zones":               zone_rows,
    "total_vessels":        total_vessels,
    "hormuz_vessels":       hormuz_vessels,
    "tankers":             tankers,
    "moving_tankers":      moving_t,
    "stopped_tankers":     stopped_t,
    "tanker_disruption_pct": tanker_disruption,
    "blockade_signal":     stopped_t > moving_t*2 if moving_t>0 else False,
    "vessel_attacks":      len(av_records),
    "hormuz_by_flag":      hormuz_flag_ranking[:15],
    "hormuz_by_type":      dict(hormuz_by_type),
    "going_dark":          {"count":len(going_dark), "by_flag":dict(going_dark_by_flag)},
    "high_interest":       {"count":len(high_interest), "by_flag":dict(hi_by_flag)},
    "av_by_flag":          av_flag_ranking[:10],
    "av_by_zone":          {k:len(v) if isinstance(v,list) else v for k,v in av_by_zone.items()} if isinstance(av_by_zone,dict) else {},
    "av_by_attacker":      {k:len(v) if isinstance(v,list) else v for k,v in av_by_attacker.items()} if isinstance(av_by_attacker,dict) else {},
    "av_by_damage":        dict(av_by_damage) if isinstance(av_by_damage,dict) else {},
    "av_timeline":         dict(av_timeline),
}

print(f"  ✓ {total_vessels} live vessels | {len(av_records)} attacks | tanker disruption: {tanker_disruption}%")
print(f"    Hormuz flags: {hormuz_flag_ranking[:5]}")
print(f"    Going dark: {len(going_dark)} | High-interest: {len(high_interest)}")

# ── D6: Military Presence by Country ─────────────────────────────
_mp = globals().get("MARITIME_PRESENCE",{})
_sc = globals().get("SHIP_CASUALTIES",{})
mp_countries = _mp.get("countries",{})

country_presence = []
for code in ["US","GB","CN","RU","IL"]:
    cp = mp_countries.get(code,{})
    if cp:
        country_presence.append({
            "code": code,
            "name": cp.get("country_name",""),
            "name_ar": cp.get("country_name_ar",""),
            "total": cp.get("total",0),
            "military": cp.get("military",0),
            "tanker": cp.get("tanker",0),
            "cargo": cp.get("cargo",0),
            "other": cp.get("other",0),
            "by_zone": cp.get("by_zone",{}),
            "military_vessels": cp.get("military_vessels",[]),
        })

# Casualties summary
casualties_list = _sc.get("casualties",[]) if isinstance(_sc, dict) else []

# SAT-E dark vessels
sat_e_data = _mp.get("sat_e_results",{})
sat_e_vessels = list(sat_e_data.values()) if isinstance(sat_e_data, dict) else []

# Ownership unmasked
ownership_data = _mp.get("ownership_data",{})
unmasked_count = _mp.get("convenience_unmasked",0)

# Add to MARITIME_THREAT
MARITIME_THREAT["country_presence"] = country_presence
MARITIME_THREAT["casualties"] = casualties_list
MARITIME_THREAT["casualties_count"] = len(casualties_list)
MARITIME_THREAT["sat_e_vessels"] = sat_e_vessels
MARITIME_THREAT["sat_e_count"] = len(sat_e_vessels)
MARITIME_THREAT["ownership_unmasked"] = unmasked_count
MARITIME_THREAT["ownership_records"] = len(ownership_data)

# ── NEW: Wire vessel histories, global military, inspections, sea routes ──
_mp = globals().get("MARITIME_PRESENCE", {})

vessel_histories = _mp.get("vessel_histories", {})
MARITIME_THREAT["vessel_histories"] = vessel_histories
MARITIME_THREAT["vessel_histories_count"] = len(vessel_histories)
MARITIME_THREAT["vessel_histories_positions"] = sum(h.get("position_count",0) for h in vessel_histories.values())

global_military = _mp.get("global_military", {})
MARITIME_THREAT["global_military"] = global_military
MARITIME_THREAT["global_military_total"] = sum(g.get("count",0) for g in global_military.values())

hormuz_traffic = _mp.get("hormuz_traffic", {})
MARITIME_THREAT["hormuz_tankers"] = hormuz_traffic.get("tankers", 0)
MARITIME_THREAT["hormuz_stopped"] = hormuz_traffic.get("stopped_tankers", 0)
MARITIME_THREAT["hormuz_moving"] = hormuz_traffic.get("moving_tankers", 0)
MARITIME_THREAT["hormuz_flow_pct"] = hormuz_traffic.get("tanker_flow_pct", 0)

inspections = _mp.get("inspections", {})
MARITIME_THREAT["inspections"] = inspections.get("records", [])
MARITIME_THREAT["inspections_total"] = inspections.get("total", 0)
MARITIME_THREAT["inspections_detained"] = inspections.get("detained", 0)

company_profiles = _mp.get("company_profiles", {})
MARITIME_THREAT["company_profiles"] = company_profiles
MARITIME_THREAT["company_profiles_count"] = len(company_profiles)

sea_routes = _mp.get("sea_routes", {})
MARITIME_THREAT["sea_routes"] = sea_routes
hormuz_route = sea_routes.get("hormuz_route", {})
cape_route = sea_routes.get("cape_route", {})
MARITIME_THREAT["route_hormuz_nm"] = hormuz_route.get("distance_nm", 0) if hormuz_route else 0
MARITIME_THREAT["route_cape_nm"] = cape_route.get("distance_nm", 0) if cape_route else 0
MARITIME_THREAT["route_diversion_nm"] = (MARITIME_THREAT["route_cape_nm"] - MARITIME_THREAT["route_hormuz_nm"]) if MARITIME_THREAT["route_hormuz_nm"] else 0
MARITIME_THREAT["diversions"] = sea_routes.get("diversions", [])
MARITIME_THREAT["diversions_count"] = len(sea_routes.get("diversions", []))

print(f"  Country presence: {len(country_presence)} countries tracked")
print(f"  Vessel histories: {MARITIME_THREAT['vessel_histories_count']} tracked ({MARITIME_THREAT['vessel_histories_positions']} positions)")
print(f"  Global military : {MARITIME_THREAT['global_military_total']} vessels")
print(f"  Hormuz flow     : {MARITIME_THREAT['hormuz_tankers']} tankers ({MARITIME_THREAT['hormuz_stopped']} stopped, {MARITIME_THREAT['hormuz_moving']} moving = {MARITIME_THREAT['hormuz_flow_pct']}%)")
print(f"  Inspections     : {MARITIME_THREAT['inspections_total']} ({MARITIME_THREAT['inspections_detained']} detained)")
print(f"  Companies       : {MARITIME_THREAT['company_profiles_count']}")
print(f"  Sea routes      : Hormuz={MARITIME_THREAT['route_hormuz_nm']}nm, Cape={MARITIME_THREAT['route_cape_nm']}nm")
print(f"  Diversions      : {MARITIME_THREAT['diversions_count']}")
for cp in country_presence:
    print(f"    {cp['name']:<20} {cp['total']:>3} total | {cp['military']:>2} military")
print(f"  Casualties: {len(casualties_list)} verified in ME")
print(f"  SAT-E dark vessels: {len(sat_e_vessels)} tracked")
print(f"  Ownership unmasked: {unmasked_count}")


# ══════════════════════════════════════════════════════════════════
# E. FLIGHT INTELLIGENCE
# ══════════════════════════════════════════════════════════════════
print("\n[E] Flight Intelligence...")

flt_data = globals().get("FLIGHT_HIST_DATA",{})
all_flights = flt_data.get("flights",[])
flt_summary = flt_data.get("daily_summary",{})

vip_flights = [f for f in all_flights if f.get("category")=="VIP_KNOWN"]
priv_flights = [f for f in all_flights if f.get("category") in ("PRIVATE_JET","VIP_CALLSIGN")]

# ── E1: Evacuation index ────────────────────────────────────────
d1_key = WAR_START_STR
d1_total = _sf(flt_summary.get(d1_key,{}).get("total_flights",0))
all_totals = [_sf(s.get("total_flights",0)) for s in flt_summary.values()]
avg_total = sum(all_totals)/len(all_totals) if all_totals else 1
evac_idx = round((d1_total/avg_total*100)-100) if avg_total else 0

# ── E2: Diplomatic coincidences ─────────────────────────────────
city_visits = defaultdict(list)
for f in vip_flights:
    arr = str(f.get("arr_city","")).strip()
    day = int(_sf(f.get("day_of_war",0)))
    # Skip pre-war flights and unknown arrival cities only
    if day < 1: continue
    if not arr or arr in ("?", "", "Unknown", "unknown", "None"): continue
    city_visits[arr].append(f)

coincidences = []
seen_pairs = set()
for city, visits in city_visits.items():
    for i in range(len(visits)):
        for j in range(i+1, len(visits)):
            a, b = visits[i], visits[j]
            owner_a = str(a.get("owner","") or a.get("label",""))
            owner_b = str(b.get("owner","") or b.get("label",""))
            if owner_a == owner_b: continue
            day_a = int(_sf(a.get("day_of_war",0)))
            day_b = int(_sf(b.get("day_of_war",0)))
            if day_a < 1 or day_b < 1: continue
            gap = abs(day_a - day_b)
            if gap <= 3:
                pair_key = tuple(sorted([owner_a, owner_b])) + (city,)
                if pair_key in seen_pairs: continue
                seen_pairs.add(pair_key)
                from_a = str(a.get("dep_city","")).strip()
                from_b = str(b.get("dep_city","")).strip()
                # Show departure if known, empty string if not
                if not from_a or from_a in ("?","Unknown","unknown","None"): from_a = ""
                if not from_b or from_b in ("?","Unknown","unknown","None"): from_b = ""
                coincidences.append({
                    "city": city, "gap_days": gap,
                    "actor_1": owner_a, "day_1": day_a, "from_1": from_a,
                    "actor_2": owner_b, "day_2": day_b, "from_2": from_b,
                })
coincidences.sort(key=lambda x: x["gap_days"])

# ── E3: Shuttle diplomacy corridors ─────────────────────────────
routes = defaultdict(lambda: {"total":0, "vip":0, "owners":set(), "days":[]})
for f in all_flights:
    if int(_sf(f.get("day_of_war",0))) < 1: continue  # Skip pre-war
    dep = str(f.get("dep_city","") or f.get("dep_icao","")).strip()
    arr = str(f.get("arr_city","") or f.get("arr_icao","")).strip()
    if dep and arr and dep != arr and dep != "?" and arr != "?" and dep != "Unknown" and arr != "Unknown":
        key = f"{dep} → {arr}"
        routes[key]["total"] += 1
        if f.get("category") == "VIP_KNOWN":
            routes[key]["vip"] += 1
            routes[key]["owners"].add(str(f.get("owner","") or f.get("label","")))
        routes[key]["days"].append(int(_sf(f.get("day_of_war",0))))

# Convert sets to lists for JSON
shuttle_corridors = sorted(
    [{"route":k, "total":v["total"], "vip":v["vip"],
      "owners":list(v["owners"])[:4],
      "day_range":[min(v["days"]) if v["days"] else 0, max(v["days"]) if v["days"] else 0]}
     for k,v in routes.items() if v["vip"] > 0],
    key=lambda x: -x["vip"]
)[:20]

# ── E4: Destination timeline (VIP entity × day × city) ──────────
vip_dest_timeline = defaultdict(lambda: {})
for f in vip_flights:
    owner = str(f.get("owner","") or f.get("label","Unknown"))
    day = int(_sf(f.get("day_of_war",0)))
    arr = str(f.get("arr_city","")).strip()
    dep = str(f.get("dep_city","")).strip()
    direction = str(f.get("direction",""))
    if arr and arr not in ("?","","Unknown","unknown","None"):
        vip_dest_timeline[owner][day] = arr
    elif dep and dep not in ("?","","Unknown","unknown","None") and direction == "dep":
        vip_dest_timeline[owner][day] = f"(من {dep})"

# Convert to serialisable format
dest_timeline = []
for owner, days_map in sorted(vip_dest_timeline.items(), key=lambda x: -len(x[1])):
    dest_timeline.append({
        "owner": owner,
        "days": {str(k):v for k,v in sorted(days_map.items())},
        "total_days": len(days_map),
    })

# ── E5: Busiest airports ────────────────────────────────────────
dep_airports = defaultdict(lambda:{"total":0,"vip":0})
arr_airports = defaultdict(lambda:{"total":0,"vip":0})
for f in all_flights:
    dep = str(f.get("dep_city","") or f.get("dep_icao","")).strip()
    arr = str(f.get("arr_city","") or f.get("arr_icao","")).strip()
    is_vip = f.get("category") == "VIP_KNOWN"
    if dep and dep != "?":
        dep_airports[dep]["total"] += 1
        if is_vip: dep_airports[dep]["vip"] += 1
    if arr and arr != "?":
        arr_airports[arr]["total"] += 1
        if is_vip: arr_airports[arr]["vip"] += 1

top_dep = sorted([{"city":k,**v} for k,v in dep_airports.items()], key=lambda x:-x["total"])[:15]
top_arr = sorted([{"city":k,**v} for k,v in arr_airports.items()], key=lambda x:-x["total"])[:15]

# ── E6: VIP entity ranking ──────────────────────────────────────
owner_stats = defaultdict(lambda: {"flights":0, "cities":set(), "days":set()})
for f in vip_flights:
    owner = str(f.get("owner","") or f.get("label","Unknown"))
    owner_stats[owner]["flights"] += 1
    arr = str(f.get("arr_city","")).strip()
    dep = str(f.get("dep_city","")).strip()
    if arr and arr != "?": owner_stats[owner]["cities"].add(arr)
    if dep and dep != "?": owner_stats[owner]["cities"].add(dep)
    d = int(_sf(f.get("day_of_war",0)))
    if d > 0: owner_stats[owner]["days"].add(d)

vip_ranking = sorted(
    [{"owner":k, "flights":v["flights"], "cities":sorted(list(v["cities"]))[:8],
      "active_days":len(v["days"]),
      "day_range":[min(v["days"]) if v["days"] else 0, max(v["days"]) if v["days"] else 0]}
     for k,v in owner_stats.items()],
    key=lambda x: -x["flights"]
)

# ── E7: VIP by day (for bar chart) ──────────────────────────────
vip_by_day = []
for day in range(0, max_war_day+1):
    ds = _date_of_day(day) if day > 0 else WAR_DAY0_STR
    summ = flt_summary.get(ds, {})
    vip_by_day.append({
        "day":     day,
        "date":    ds,
        "total":   int(_sf(summ.get("total_flights",0))),
        "vip":     int(_sf(summ.get("vip_count",0))),
        "private": int(_sf(summ.get("private_count",0))),
    })

# ── E8: Flight log — chronological per VIP ──────────────────────
flight_log = defaultdict(list)
for f in vip_flights:
    owner = str(f.get("owner","") or f.get("label","Unknown"))
    day = int(_sf(f.get("day_of_war",0)))
    dep = str(f.get("dep_city","")).strip()
    arr = str(f.get("arr_city","")).strip()
    dep_icao = str(f.get("dep_icao","")).strip()
    arr_icao = str(f.get("arr_icao","")).strip()
    if dep == "?" or dep == "": dep = dep_icao if dep_icao and dep_icao not in ("?","","None") else ""
    if arr == "?" or arr == "": arr = arr_icao if arr_icao and arr_icao not in ("?","","None") else ""
    if day < 1: continue  # Skip pre-war flights
    # Skip if either dep or arr is unknown
    if not dep or dep in ("?","Unknown","unknown","None","غير محدد"): continue
    if not arr or arr in ("?","Unknown","unknown","None","غير محدد"): continue
    flight_log[owner].append({
        "day": day,
        "dep": dep,
        "arr": arr,
        "route": f"{dep} → {arr}" if dep != "غير محدد" and arr != "غير محدد" else (f"→ {arr}" if arr != "غير محدد" else f"{dep} →"),
    })

# Sort each VIP's flights by day
flight_log_list = []
for owner, flights in sorted(flight_log.items(), key=lambda x: -len(x[1])):
    flights_sorted = sorted(flights, key=lambda f: f["day"])
    flight_log_list.append({
        "owner": owner,
        "flights": flights_sorted,
        "total": len(flights_sorted),
    })

VIP_INTELLIGENCE = {
    "vip_by_day":         vip_by_day,
    "total_vip":          len(vip_flights),
    "total_flights":      len(all_flights),
    "evacuation_index":   evac_idx,
    "coincidences":       coincidences,
    "shuttle_corridors":  shuttle_corridors,
    "dest_timeline":      dest_timeline[:10],
    "flight_log":         flight_log_list[:15],
    "top_departures":     top_dep,
    "top_arrivals":       top_arr,
    "vip_ranking":        vip_ranking,
}

print(f"  ✓ {len(vip_flights)} VIP / {len(all_flights)} total flights")
print(f"    Evacuation index: +{evac_idx}%")
print(f"    Coincidences: {len(coincidences)}")
print(f"    Shuttle corridors: {len(shuttle_corridors)}")
print(f"    VIP entities: {len(vip_ranking)}")
if coincidences:
    for c in coincidences[:3]:
        gap_label = "SAME DAY" if c['gap_days']==0 else str(c['gap_days'])+"d apart"
        print(f"    [{gap_label}] {c['city']}: {c['actor_1'][:25]} + {c['actor_2'][:25]}")


# ══════════════════════════════════════════════════════════════════
# F. ISR SATELLITE ACTIVITY — RECONNAISSANCE OVER IRAN
# ══════════════════════════════════════════════════════════════════
print("\n[F] Reconnaissance Satellite Activity...")

_hsd = globals().get("HIST_SAT_DATA",{})
hist_days = _hsd.get("days",[]) if isinstance(_hsd, dict) else []
sat_count = _hsd.get("sat_count",0) if isinstance(_hsd, dict) else 0

# ── F1: Daily satellite positions over Middle East (spy vs military) ─
isr_daily = []
for d in hist_days:
    sats = d.get("satellites",[])
    spy_over = sum(1 for s in sats if s.get("over_middle_east") and s.get("cat")=="spy")
    mil_over = sum(1 for s in sats if s.get("over_middle_east") and s.get("cat")=="military")
    isr_daily.append({
        "day_num":      d.get("day_num",0),
        "date":         d.get("date",""),
        "region_count": d.get("region_count",0),
        "spy":          spy_over,
        "military":     mil_over,
    })

# ── F2: Most active reconnaissance satellites ────────────────────
# Count how many days each satellite appeared over Middle East
sat_activity = defaultdict(lambda: {"days_over_me":0, "name":"", "norad":"", "cat":"", "total_appearances":0})
for d in hist_days:
    seen_this_day = set()
    for s in d.get("satellites",[]):
        norad = s.get("norad","")
        sat_activity[norad]["name"] = s.get("name","")
        sat_activity[norad]["norad"] = norad
        sat_activity[norad]["cat"] = s.get("cat","")
        sat_activity[norad]["total_appearances"] += 1
        if s.get("over_middle_east") and norad not in seen_this_day:
            sat_activity[norad]["days_over_me"] += 1
            seen_this_day.add(norad)

# Rank by days over Middle East
top_recon_sats = sorted(
    [v for v in sat_activity.values() if v["days_over_me"] > 0],
    key=lambda x: -x["days_over_me"]
)[:15]

# ── F3: Satellite category breakdown ─────────────────────────────
cat_counts = defaultdict(int)
for v in sat_activity.values():
    if v["days_over_me"] > 0:
        cat_counts[v["cat"]] += 1

# ── F4: Average daily overflights ────────────────────────────────
total_overflights = sum(d["region_count"] for d in isr_daily)
avg_daily = round(total_overflights / max(len(isr_daily),1), 1)
peak_day = max(isr_daily, key=lambda d: d["region_count"]) if isr_daily else {}

ISR_CUEING_ANALYSIS = {
    "daily_overflights":   isr_daily,
    "top_recon_sats":      top_recon_sats,
    "sat_count":           sat_count,
    "active_over_me":      len(top_recon_sats),
    "avg_daily":           avg_daily,
    "peak_day":            peak_day.get("day_num",0) if peak_day else 0,
    "peak_count":          peak_day.get("region_count",0) if peak_day else 0,
    "cat_breakdown":       dict(cat_counts),
    "total_days":          len(isr_daily),
    "sat_data_available":  len(hist_days) > 0,
}

print(f"  ✓ {sat_count} recon sats tracked | {len(hist_days)} war days")
print(f"    Active over ME: {len(top_recon_sats)} sats")
print(f"    Avg daily overflights: {avg_daily}")
if top_recon_sats:
    print(f"    Top 5:")
    for s in top_recon_sats[:5]:
        print(f"      {s['name']:<30} {s['cat']:<10} {s['days_over_me']} days over ME")



# ══════════════════════════════════════════════════════════════════
# G. COMPOSITE THREAT SCORE
# ══════════════════════════════════════════════════════════════════
print("\n[G] Composite Threat Score...")

components = {}

# 1. Escalation momentum (0-30)
recent_sc = [d["score"] for d in esc_days[-3:]]
momentum = (sum(recent_sc)/len(recent_sc)/max(peak_sc,1))*30 if recent_sc else 0
components["Escalation momentum"] = round(momentum,1)

# 2. Political pressure (0-20)
recent_pol = [d["day_score"] for d in pol_days[-3:] if d["n"]>0]
pol_avg = sum(recent_pol)/len(recent_pol) if recent_pol else 0
pol_contrib = max(0, min(20, 10 + pol_avg*0.5))
components["Political pressure"] = round(pol_contrib,1)

# 3. Maritime threat (0-20)
hz = next((z for z in zone_rows if z["id"]=="hormuz"),{})
components["Maritime threat"] = round(hz.get("risk_score",50)*0.2,1)

# 4. Jamming signal (0-15)
recent_jam_vals = [d["jam_pct"] for d in jam_corr_days[-3:]]
jam_recent = sum(recent_jam_vals)/len(recent_jam_vals) if recent_jam_vals else 0
components["GPS jamming signal"] = round(min(jam_recent*0.5,15),1)

# 5. VIP activity (0-15)
recent_vip = vip_by_day[-3:]
vip_recent = sum(d["vip"] for d in recent_vip)/max(len(recent_vip),1)
components["VIP activity index"] = round(min(vip_recent*2,15),1)

total = sum(components.values())
level = ("critical" if total>=75 else "high" if total>=55 else
         "medium" if total>=35 else "low")

CONFLICT_PREDICTION = {
    "score":      round(total,1),
    "level":      level,
    "components": components,
    "interpretation": (
        f"Threat score {round(total,1)}/100 — "
        f"{level.upper()} probability of significant military activity"
    ),
}

print(f"  Score: {CONFLICT_PREDICTION['score']}/100 [{level.upper()}]")
for k,v in components.items():
    bar = "█"*int(v/2)
    print(f"    {k:<28} {v:5.1f}  {bar}")


# ══════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════
print(f"\n{'='*60}")
print("CELL 9 — Intelligence Extraction Complete")
print(f"{'='*60}")
print(f"  A. ESCALATION_ANALYSIS   : {max_war_day} days | {len(war_events)} events | {trend}")
print(f"     Who-hit-whom pairs    : {len(who_hit_whom_list)}")
print(f"     Countries             : {len(country_ranking)}")
print(f"  B. POLITICAL_ANALYSIS    : {len(pol_events)} events | {pol_trend}")
print(f"     Milestones            : {len(milestones)}")
print(f"     War phases            : {len(war_phases)}")
print(f"     Contradictions        : {len(contradictions)}")
print(f"     DIPLOMATIC_INDEX      : {len(top_actors)} actors")
print(f"  C. JAMMING_CORRELATION   : {len(jam_daily)} days | correlates={correlates}")
print(f"     Cell-level data       : {has_cell_data}")
print(f"  D. MARITIME_THREAT       : {total_vessels} vessels | {len(av_records)} attacks")
print(f"     Hormuz flags          : {len(hormuz_flag_ranking)}")
print(f"     Going dark            : {len(going_dark)}")
print(f"  E. VIP_INTELLIGENCE      : {len(vip_flights)} VIP | {len(coincidences)} coincidences")
print(f"     Shuttle corridors     : {len(shuttle_corridors)}")
print(f"  F. ISR_CUEING_ANALYSIS   : {sat_count} sats | {len(top_recon_sats)} active over ME | {avg_daily} avg/day")
print(f"  G. CONFLICT_PREDICTION   : {total:.1f}/100 [{level.upper()}]")
print(f"\n  Run Cell 10 next")

######################################################################
# ► NEXT CELL: Cell 10 — Logging & CSV Snapshots
######################################################################