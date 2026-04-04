# c11_marine_enhanced.py
# Enhanced maritime intelligence — with 6h cache
# Auto-extracted from Cell 11

import os, json, time as _time

MARINE_ENHANCED_CACHE = os.path.join(CACHE_DIR, "marine_enhanced_cache.json")
_ENHANCED_CACHE_HOURS = 6
_use_enhanced_cache = False

if os.path.exists(MARINE_ENHANCED_CACHE):
    try:
        _cache_age_h = (_time.time() - os.path.getmtime(MARINE_ENHANCED_CACHE)) / 3600
        if _cache_age_h < _ENHANCED_CACHE_HOURS:
            with open(MARINE_ENHANCED_CACHE, "r", encoding="utf-8") as _cf:
                _cached = json.load(_cf)
            for _k, _v in _cached.items():
                globals()[_k] = _v
            _use_enhanced_cache = True
            print(f"  ✓ Enhanced maritime cache fresh ({_cache_age_h:.1f}h old)")
        else:
            print(f"  Cache stale ({_cache_age_h:.1f}h) — refreshing...")
    except Exception as _e:
        print(f"  ⚠ Cache read failed ({_e}) — fetching fresh")

if not _use_enhanced_cache:
    # ── Run original Cell 11 code ─────────────────────────────
    ######################################################################
    # CELL 7.5 — Enhanced Maritime Intelligence
    #
    # RUNS AFTER: Cell 7 (MARINE_DATA must exist)
    # SOURCE:     Datalastic API (same key as Cell 7)
    #
    # FEATURES:
    #   0. Vessel Enrichment     — /vessel_pro for full specs
    #   1. Country Presence      — US/UK/CN/RU/IL vessel breakdown
    #   2. Vessel Ownership      — /maritime_reports/ownership
    #   3. Ship Casualties       — /maritime_reports/casualty
    #   4. SAT-E Tracking        — /ext/vessel_pro_est
    #   5. Vessel History        — /vessel_history (track suspicious vessels)
    #   6. Global Military Find  — /vessel_find (military vessels worldwide)
    #   7. Hormuz Traffic Change — /inradius_history (before vs now)
    #   8. Inspections/Detention — /maritime_reports/inspection
    #   9. Company Profiles      — /maritime_reports/companies
    #  10. Classification Data   — /maritime_reports/classification
    #  11. Sea Route Diversions  — /sea_routes
    #
    # OUTPUTS:
    #   MARITIME_PRESENCE  — country presence + all enriched data
    #   SHIP_CASUALTIES    — verified casualties in conflict zone
    #   MARINE_DATA        — enriched vessels (specs, ownership, SAT-E)
    ######################################################################
    
    import requests, json, os, time
    from datetime import datetime, timezone, timedelta
    from collections import defaultdict
    
    print("=" * 60)
    print("CELL 7.5 — Enhanced Maritime Intelligence")
    print("=" * 60)
    
    if 'MARINE_DATA' not in dir() or not MARINE_DATA.get('vessels'):
        raise RuntimeError("MARINE_DATA not found — run Cell 7 first")
    
    DATALASTIC_KEY = os.environ.get("DATALASTIC_KEY", "")
    if not DATALASTIC_KEY:
        raise RuntimeError("Datalastic API key not found")
    
    BASE     = "https://api.datalastic.com/api/v0"
    BASE_RPT = "https://api.datalastic.com/api/maritime_reports"
    BASE_EXT = "https://api.datalastic.com/api/ext"
    
    vessels = MARINE_DATA['vessels']
    print(f"  Starting with {len(vessels)} vessels from Cell 7")
    WAR_START = "2026-02-28"
    
    # ══════════════════════════════════════════════════════════════════
    # 0. VESSEL ENRICHMENT — Full specs from /vessel_pro
    # ══════════════════════════════════════════════════════════════════
    print("\n[0] Vessel Enrichment — full specs for key vessels...")
    
    TRACKED_FLAGS = {"US","GB","CN","RU","IL"}
    enrich_candidates = []
    for v in vessels:
        flag = str(v.get("flag","")).upper()
        cat = v.get("category","")
        if (flag in TRACKED_FLAGS or cat in ("military","warship") or
            v.get("going_dark") or v.get("zone_id") == "hormuz"):
            enrich_candidates.append(v)
    
    seen = set()
    unique_enrich = []
    for v in enrich_candidates:
        mmsi = v.get("mmsi","")
        if mmsi and mmsi not in seen:
            seen.add(mmsi); unique_enrich.append(v)
    unique_enrich = unique_enrich[:100]
    print(f"  Enriching {len(unique_enrich)} vessels...")
    
    enriched = 0
    for i, v in enumerate(unique_enrich):
        mmsi = v.get("mmsi","")
        if not mmsi: continue
        try:
            r = requests.get(f"{BASE}/vessel_pro", params={"api-key": DATALASTIC_KEY, "mmsi": mmsi}, timeout=10)
            if r.status_code == 200:
                d = r.json().get("data", {})
                if d:
                    for key, api_key in [("callsign","callsign"),("nav_status","navigational_status"),
                        ("gross_tonnage","gross_tonnage"),("deadweight","deadweight"),("teu","teu"),
                        ("length","length"),("breadth","breadth"),("year_built","year_built"),
                        ("draught","draught_avg"),("speed_max","speed_max"),("country_name","country_name"),
                        ("type_specific","type_specific")]:
                        val = d.get(api_key)
                        if val: v[key] = val
                    enriched += 1
            time.sleep(0.12)
        except: pass
        if (i+1) % 25 == 0: print(f"    {i+1}/{len(unique_enrich)}...", flush=True)
    print(f"  Enriched: {enriched} vessels")
    
    # ══════════════════════════════════════════════════════════════════
    # 1. COUNTRY PRESENCE TRACKING
    # ══════════════════════════════════════════════════════════════════
    print("\n[1] Country Presence...")
    
    TRACKED_COUNTRIES = {
        "US": {"name":"United States","name_ar":"الولايات المتحدة","mil_prefixes":["USS ","USNS "],"mid_ranges":[(338,),(303,),(368,),(369,)]},
        "GB": {"name":"United Kingdom","name_ar":"المملكة المتحدة","mil_prefixes":["HMS ","RFA "],"mid_ranges":[(232,),(233,),(234,),(235,)]},
        "CN": {"name":"China","name_ar":"الصين","mil_prefixes":["PLAN ","CNS "],"mid_ranges":[(412,),(413,),(414,)]},
        "RU": {"name":"Russia","name_ar":"روسيا","mil_prefixes":["RFS "],"mid_ranges":[(273,)]},
        "IL": {"name":"Israel","name_ar":"إسرائيل","mil_prefixes":["INS "],"mid_ranges":[(428,)]},
    }
    CONVENIENCE_FLAGS = {"PA","LR","MH","KM","HK","MT","BS","CY","BM","VU","SG","AG"}
    
    def detect_country(v):
        flag = str(v.get("flag","")).upper()
        name = str(v.get("name","")).upper()
        mmsi = str(v.get("mmsi",""))
        if flag in TRACKED_COUNTRIES: return flag
        for code, info in TRACKED_COUNTRIES.items():
            for prefix in info["mil_prefixes"]:
                if name.startswith(prefix): return code
        if len(mmsi) >= 3:
            try:
                mid = int(mmsi[:3])
                for code, info in TRACKED_COUNTRIES.items():
                    for mr in info["mid_ranges"]:
                        if mid in mr: return code
            except: pass
        return None
    
    country_vessels = {c: [] for c in TRACKED_COUNTRIES}
    convenience_vessels = []
    for v in vessels:
        det = detect_country(v)
        if det: country_vessels[det].append(v)
        elif str(v.get("flag","")).upper() in CONVENIENCE_FLAGS: convenience_vessels.append(v)
    
    presence = {}
    for code, info in TRACKED_COUNTRIES.items():
        cvs = country_vessels[code]
        by_type = defaultdict(int); by_zone = defaultdict(int); mil_vessels = []
        for v in cvs:
            cat = v.get("category","other"); by_type[cat] += 1; by_zone[v.get("zone_name","?")] += 1
            if cat in ("military","warship"):
                mil_vessels.append({"name":v.get("name",""),"mmsi":v.get("mmsi",""),"type":v.get("type_specific",v.get("type","")),"lat":v.get("lat"),"lon":v.get("lon"),"speed":v.get("speed"),"zone":v.get("zone_name",""),"destination":v.get("destination",""),"going_dark":v.get("going_dark",False)})
        presence[code] = {"country_code":code,"country_name":info["name"],"country_name_ar":info["name_ar"],
            "total":len(cvs),"military":len(mil_vessels),"tanker":by_type.get("tanker",0),"cargo":by_type.get("cargo",0),
            "other":len(cvs)-len(mil_vessels)-by_type.get("tanker",0)-by_type.get("cargo",0),
            "by_type":dict(by_type),"by_zone":dict(by_zone),"military_vessels":mil_vessels,
            "vessels":[{"name":v.get("name",""),"mmsi":v.get("mmsi",""),"flag":v.get("flag",""),"category":v.get("category",""),"type":v.get("type_specific",v.get("type","")),"zone":v.get("zone_name",""),"lat":v.get("lat"),"lon":v.get("lon"),"speed":v.get("speed"),"destination":v.get("destination",""),"going_dark":v.get("going_dark",False)} for v in cvs]}
        print(f"  {info['name']:<20} {len(cvs):>3} vessels | {len(mil_vessels):>2} military | {by_type.get('tanker',0):>3} tankers")
    
    # ══════════════════════════════════════════════════════════════════
    # 2. VESSEL OWNERSHIP
    # ══════════════════════════════════════════════════════════════════
    print("\n[2] Vessel Ownership...")
    ownership_results = {}; unmasked = 0
    for v in convenience_vessels[:50]:
        imo = v.get("imo",""); mmsi = v.get("mmsi","")
        if not imo and not mmsi: continue
        try:
            params = {"api-key": DATALASTIC_KEY}
            if imo: params["imo"] = str(imo)
            else: params["mmsi"] = str(mmsi)
            r = requests.get(f"{BASE_RPT}/ownership", params=params, timeout=10)
            if r.status_code == 200:
                recs = r.json().get("data", []); 
                if isinstance(recs, dict): recs = [recs]
                if recs and isinstance(recs[0], dict):
                    rec = recs[0]; owner = rec.get("beneficial_owner",rec.get("registered_owner",""))
                    oc = rec.get("beneficial_owner_country",rec.get("flag_name",""))
                    ownership_results[mmsi] = {"mmsi":mmsi,"name":v.get("name",""),"flag":v.get("flag",""),"beneficial_owner":owner,"owner_country":oc,"operator":rec.get("operator",""),"operator_country":rec.get("operator_country","")}
                    v["beneficial_owner"] = owner; v["owner_country"] = oc; v["operator"] = rec.get("operator","")
                    for code, info in TRACKED_COUNTRIES.items():
                        if info["name"].lower() in (oc or "").lower():
                            presence[code]["total"] += 1; presence[code]["other"] += 1; unmasked += 1; break
            time.sleep(0.15)
        except: pass
    print(f"  Ownership: {len(ownership_results)} records | {unmasked} unmasked")
    
    # ══════════════════════════════════════════════════════════════════
    # 3. SHIP CASUALTIES
    # ══════════════════════════════════════════════════════════════════
    print("\n[3] Ship Casualties...")
    SHIP_CASUALTIES = {"casualties":[],"total":0,"total_global":0,"error":None}
    try:
        r = requests.get(f"{BASE_RPT}/casualty", params={"api-key": DATALASTIC_KEY, "updated_from": WAR_START}, timeout=30)
        if r.status_code == 200:
            raw = r.json().get("data",[]); 
            if isinstance(raw, dict): raw = [raw]
            me_kw = ["hormuz","gulf","oman","iran","saudi","bahrain","qatar","kuwait","uae","emirates","red sea","yemen","aden","arabian","persian","iraq","lebanon","israel","suez","mandeb","dubai","abu dhabi","muscat","bandar","fujairah","jebel ali","ras tanura","doha","haifa","jeddah","hodeidah","houthi","irgc","missile","drone"]
            me_cas = [{"vessel_name":c.get("vessel_name",""),"imo":c.get("imo",""),"date":c.get("casualty_date",""),"type":c.get("casualty_type",""),"details":c.get("casualty_details",""),"modified":c.get("modified_at","")} for c in raw if any(kw in str(c.get("casualty_details","")).lower() for kw in me_kw)]
            SHIP_CASUALTIES = {"casualties":me_cas,"total":len(me_cas),"total_global":len(raw),"error":None}
            print(f"  Global: {len(raw)} | ME: {len(me_cas)}")
    except Exception as e: print(f"  Error: {e}")
    
    # ══════════════════════════════════════════════════════════════════
    # 4. SAT-E TRACKING
    # ══════════════════════════════════════════════════════════════════
    print("\n[4] SAT-E Tracking...")
    dark_vessels = [v for v in vessels if v.get("going_dark")]
    sat_e_results = {}
    for v in dark_vessels[:20]:
        mmsi = v.get("mmsi","")
        if not mmsi: continue
        try:
            r = requests.get(f"{BASE_EXT}/vessel_pro_est", params={"api-key": DATALASTIC_KEY, "mmsi": mmsi}, timeout=10)
            if r.status_code == 200:
                d = r.json().get("data",{})
                if d and d.get("lat") and d.get("lon"):
                    sat_e_results[mmsi] = {"mmsi":mmsi,"name":v.get("name",""),"flag":v.get("flag",""),"est_lat":d.get("lat"),"est_lon":d.get("lon"),"est_speed":d.get("speed"),"est_destination":d.get("destination",""),"last_ais_lat":v.get("lat"),"last_ais_lon":v.get("lon"),"method":"SAT-E"}
                    v["sat_e_lat"] = d.get("lat"); v["sat_e_lon"] = d.get("lon")
            time.sleep(0.15)
        except: pass
    print(f"  Dark: {len(dark_vessels)} | SAT-E found: {len(sat_e_results)}")
    
    # ══════════════════════════════════════════════════════════════════
    # 5. VESSEL HISTORY — Track suspicious vessels over 30 days
    # ══════════════════════════════════════════════════════════════════
    print("\n[5] Vessel History...")
    history_candidates = [v for v in vessels if v.get("is_military") or v.get("going_dark") or str(v.get("flag","")).upper() in ("IR","KP") or v.get("category") in ("military","warship")]
    seen_h = set(); unique_hist = []
    for v in history_candidates:
        mmsi = v.get("mmsi","")
        if mmsi and mmsi not in seen_h: seen_h.add(mmsi); unique_hist.append(v)
    unique_hist = unique_hist[:15]
    
    VESSEL_HISTORIES = {}
    d_from = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    d_to = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for v in unique_hist:
        mmsi = v.get("mmsi","")
        if not mmsi: continue
        try:
            r = requests.get(f"{BASE}/vessel_history", params={"api-key": DATALASTIC_KEY, "mmsi": mmsi, "date_from": d_from, "date_to": d_to}, timeout=15)
            if r.status_code == 200:
                data = r.json().get("data",{})
                if isinstance(data, dict):
                    pos_list = data.get("positions",[])
                elif isinstance(data, list):
                    pos_list = data
                else:
                    pos_list = []
                if pos_list:
                    positions = [{"lat":p.get("lat"),"lon":p.get("lon"),"speed":p.get("speed"),"date":p.get("last_position_UTC",p.get("date","")),"destination":p.get("destination",""),"nav_status":p.get("navigational_status","")} for p in pos_list]
                    VESSEL_HISTORIES[mmsi] = {"mmsi":mmsi,"name":data.get("name",v.get("name","")),"flag":v.get("flag",""),"imo":data.get("imo",""),"category":v.get("category",""),"positions":positions,"position_count":len(positions)}
            time.sleep(0.15)
        except: pass
    print(f"  Tracked: {len(VESSEL_HISTORIES)} vessels | {sum(h['position_count'] for h in VESSEL_HISTORIES.values())} positions")
    
    # ══════════════════════════════════════════════════════════════════
    # 6. GLOBAL MILITARY FIND
    # ══════════════════════════════════════════════════════════════════
    print("\n[6] Global Military Find...")
    GLOBAL_MILITARY = {code:{"country":code,"count":0,"vessels":[]} for code in TRACKED_COUNTRIES}
    try:
        r = requests.get(f"{BASE}/vessel_find", params={"api-key": DATALASTIC_KEY, "type": "Military Ops"}, timeout=20)
        if r.status_code == 200:
            raw = r.json().get("data",[])
            if isinstance(raw, dict): raw = list(raw.values()) if not raw.get("vessels") else raw.get("vessels",[])
            elif isinstance(raw, list): pass
            else: raw = []
            # Group by country
            for vv in raw:
                iso = str(vv.get("country_iso","")).upper()
                if iso in GLOBAL_MILITARY:
                    GLOBAL_MILITARY[iso]["count"] += 1
                    if len(GLOBAL_MILITARY[iso]["vessels"]) < 50:
                        GLOBAL_MILITARY[iso]["vessels"].append({"name":vv.get("name",""),"mmsi":vv.get("mmsi",""),"type_specific":vv.get("type_specific",""),"lat":vv.get("lat"),"lon":vv.get("lon"),"speed":vv.get("speed"),"destination":vv.get("destination",""),"country":iso})
            for code in TRACKED_COUNTRIES:
                print(f"  {TRACKED_COUNTRIES[code]['name']:<20} {GLOBAL_MILITARY[code]['count']} military vessels globally")
            print(f"  Total global military (all countries): {len(raw)}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # ══════════════════════════════════════════════════════════════════
    # 7. HORMUZ TRAFFIC SUMMARY
    # ══════════════════════════════════════════════════════════════════
    print("\n[7] Hormuz Traffic Summary...")
    current_hormuz = len([v for v in vessels if v.get("zone_id") == "hormuz"])
    hormuz_tankers = len([v for v in vessels if v.get("zone_id") == "hormuz" and v.get("is_tanker")])
    hormuz_stopped = len([v for v in vessels if v.get("zone_id") == "hormuz" and v.get("is_tanker") and (v.get("speed") or 0) <= 1.0])
    HORMUZ_TRAFFIC = {
        "current": current_hormuz,
        "tankers": hormuz_tankers,
        "stopped_tankers": hormuz_stopped,
        "moving_tankers": hormuz_tankers - hormuz_stopped,
        "tanker_flow_pct": round((hormuz_tankers - hormuz_stopped) / max(hormuz_tankers, 1) * 100, 1),
    }
    print(f"  Hormuz: {current_hormuz} vessels | {hormuz_tankers} tankers ({hormuz_stopped} stopped, {hormuz_tankers - hormuz_stopped} moving)")
    print(f"  Tanker flow: {HORMUZ_TRAFFIC['tanker_flow_pct']}% of tankers are moving")
    
    # ══════════════════════════════════════════════════════════════════
    # 8. INSPECTIONS & DETENTIONS
    # ══════════════════════════════════════════════════════════════════
    print("\n[8] Inspections & Detentions...")
    INSPECTIONS = {"records":[],"total":0,"detained":0,"error":None}
    try:
        r = requests.get(f"{BASE_RPT}/inspections", params={"api-key": DATALASTIC_KEY, "from": WAR_START}, timeout=30)
        if r.status_code == 200:
            raw = r.json().get("data",[]); 
            if isinstance(raw, dict): raw = [raw]
            me_kw = ["hormuz","gulf","oman","iran","saudi","bahrain","qatar","kuwait","uae","emirates","red sea","yemen","aden","arabian","persian","iraq","fujairah","jebel","muscat","doha","manama","dubai","abu dhabi","dammam","jeddah"]
            me_insp = []; det_count = 0
            for rec in raw:
                loc = str(rec.get("inspection_port",rec.get("port_name",rec.get("port","")))).lower()
                det = str(rec.get("deficiency_description",rec.get("inspection_details",""))).lower()
                if any(kw in loc or kw in det for kw in me_kw):
                    is_det = str(rec.get("detention","")).lower() in ("true","yes","1") or "detain" in det
                    me_insp.append({"vessel_name":rec.get("vessel_name",rec.get("name","")),"imo":rec.get("imo",""),"port":rec.get("port_name",rec.get("port","")),"date":rec.get("inspection_date",rec.get("date","")),"type":rec.get("inspection_type",rec.get("type","")),"deficiencies":rec.get("ship_deficiencies",rec.get("deficiency_count",0)),"detained":is_det,"authority":rec.get("inspection_authority",""),"deficiencies_desc":str(rec.get("deficiency_description",""))[:300]})
                    if is_det: det_count += 1
            INSPECTIONS = {"records":me_insp,"total":len(me_insp),"detained":det_count,"total_global":len(raw),"error":None}
            print(f"  Global: {len(raw)} | ME: {len(me_insp)} | Detained: {det_count}")
        else: print(f"  HTTP {r.status_code}")
    except Exception as e: print(f"  Error: {e}")
    
    # ══════════════════════════════════════════════════════════════════
    # 9. COMPANY PROFILES
    # ══════════════════════════════════════════════════════════════════
    print("\n[9] Company Profiles...")
    company_names = set()
    for mmsi, own in ownership_results.items():
        if own.get("beneficial_owner"): company_names.add(own["beneficial_owner"])
        if own.get("operator"): company_names.add(own["operator"])
    COMPANY_PROFILES = {}
    for cn in list(company_names)[:15]:
        try:
            r = requests.get(f"{BASE_RPT}/companies", params={"api-key": DATALASTIC_KEY, "company_name": cn}, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data",[]); 
                if isinstance(data, dict): data = [data]
                if data and isinstance(data[0], dict):
                    rec = data[0]
                    COMPANY_PROFILES[cn] = {"name":rec.get("company_name",cn),"country":rec.get("country_code",rec.get("country","")),"type":rec.get("company_type",""),"status":rec.get("status",""),"fleet_size":rec.get("fleet_size",rec.get("vessels_count","")),"imo_company":rec.get("imo_company_number","")}
            time.sleep(0.15)
        except: pass
    print(f"  Profiles: {len(COMPANY_PROFILES)} companies")
    
    # ══════════════════════════════════════════════════════════════════
    # 10. CLASSIFICATION DATA — skipped (endpoint returns 404)
    # ══════════════════════════════════════════════════════════════════
    print("\n[10] Classification — skipped (not available)")
    CLASSIFICATION_DATA = {}
    
    # ══════════════════════════════════════════════════════════════════
    # 11. SEA ROUTE DIVERSIONS
    # ══════════════════════════════════════════════════════════════════
    print("\n[11] Sea Route Analysis...")
    SEA_ROUTES = {"hormuz_route":None,"cape_route":None,"diversions":[],"error":None}
    try:
        r = requests.get(f"{BASE_EXT}/route", params={"api-key": DATALASTIC_KEY,"lat_from":"25.27","lon_from":"55.30","lat_to":"19.08","lon_to":"72.88"}, timeout=15)
        if r.status_code == 200:
            d = r.json().get("data",{})
            route_data = d.get("route",{}).get("properties",{}) if isinstance(d.get("route"),dict) else d
            SEA_ROUTES["hormuz_route"] = {"distance_nm":route_data.get("total_dist_nm",route_data.get("distance",d.get("total_dist_nm",0))),"from":"Dubai","to":"Mumbai","via":"Hormuz"}
            print(f"  Hormuz route: {route_data.get('total_dist_nm','?')} nm")
    except Exception as e: print(f"  Hormuz route error: {e}")
    
    try:
        r = requests.get(f"{BASE_EXT}/route", params={"api-key": DATALASTIC_KEY,"lat_from":"25.27","lon_from":"55.30","lat_to":"-29.87","lon_to":"31.05"}, timeout=15)
        if r.status_code == 200:
            leg1_data = r.json().get("data",{})
            leg1_route = leg1_data.get("route",{}).get("properties",{}) if isinstance(leg1_data.get("route"),dict) else leg1_data
            leg1 = leg1_route.get("total_dist_nm",leg1_route.get("distance",leg1_data.get("total_dist_nm",0)))
            r2 = requests.get(f"{BASE_EXT}/route", params={"api-key": DATALASTIC_KEY,"lat_from":"-29.87","lon_from":"31.05","lat_to":"19.08","lon_to":"72.88"}, timeout=15)
            if r2.status_code == 200:
                leg2_data = r2.json().get("data",{})
                leg2_route = leg2_data.get("route",{}).get("properties",{}) if isinstance(leg2_data.get("route"),dict) else leg2_data
                leg2 = leg2_route.get("total_dist_nm",leg2_route.get("distance",leg2_data.get("total_dist_nm",0)))
                total = (leg1 or 0) + (leg2 or 0)
                SEA_ROUTES["cape_route"] = {"distance_nm":total,"from":"Dubai","to":"Mumbai","via":"Cape of Good Hope","leg1_nm":leg1,"leg2_nm":leg2}
                print(f"  Cape route: {total} nm")
                if SEA_ROUTES["hormuz_route"] and SEA_ROUTES["hormuz_route"]["distance_nm"]:
                    diff = total - SEA_ROUTES["hormuz_route"]["distance_nm"]
                    print(f"  Diversion penalty: +{diff} nm ({diff/SEA_ROUTES['hormuz_route']['distance_nm']*100:.0f}% longer)")
    except Exception as e: print(f"  Cape route error: {e}")
    
    diversion_kw = ["cape town","durban","maputo","mombasa","dar es salaam","cape of good hope","good hope","south africa"]
    diversions = [{"name":v.get("name",""),"mmsi":v.get("mmsi",""),"flag":v.get("flag",""),"destination":v.get("destination",""),"category":v.get("category",""),"zone":v.get("zone_name","")} for v in vessels if any(kw in str(v.get("destination","")).lower() for kw in diversion_kw)]
    SEA_ROUTES["diversions"] = diversions
    if diversions: print(f"  Diversions detected: {len(diversions)} vessels")
    
    # ══════════════════════════════════════════════════════════════════
    # BUILD OUTPUT
    # ══════════════════════════════════════════════════════════════════
    print("\n[12] Building output...")
    
    MARITIME_PRESENCE = {
        "countries":presence, "tracked_codes":list(TRACKED_COUNTRIES.keys()),
        "convenience_checked":len(convenience_vessels[:50]), "convenience_unmasked":unmasked,
        "ownership_records":len(ownership_results), "ownership_data":ownership_results,
        "sat_e_results":sat_e_results, "sat_e_found":len(sat_e_results),
        "vessel_histories":VESSEL_HISTORIES, "global_military":GLOBAL_MILITARY,
        "hormuz_traffic":HORMUZ_TRAFFIC, "inspections":INSPECTIONS,
        "company_profiles":COMPANY_PROFILES, 
        "sea_routes":SEA_ROUTES, "timestamp_utc":datetime.now(timezone.utc).isoformat(),
    }
    
    print(f"\n{'='*60}")
    print(f"  CELL 7.5 COMPLETE")
    print(f"{'='*60}")
    for code in TRACKED_COUNTRIES:
        p = presence[code]
        print(f"  {p['country_name_ar']:<20} {p['total']:>3} total | {p['military']:>2} mil")
    print(f"  Ownership          : {len(ownership_results)} ({unmasked} unmasked)")
    print(f"  Casualties         : {SHIP_CASUALTIES['total']} ME ({SHIP_CASUALTIES.get('total_global',0)} global)")
    print(f"  SAT-E              : {len(sat_e_results)} dark vessels")
    print(f"  Vessel histories   : {len(VESSEL_HISTORIES)} tracked")
    print(f"  Global military    : {sum(g['count'] for g in GLOBAL_MILITARY.values())} vessels")
    print(f"  Hormuz traffic     : {HORMUZ_TRAFFIC.get('before_war',0)} before > {HORMUZ_TRAFFIC.get('current',0)} now ({HORMUZ_TRAFFIC.get('change_pct',0)}%)")
    print(f"  Inspections        : {INSPECTIONS.get('total',0)} ({INSPECTIONS.get('detained',0)} detained)")
    print(f"  Companies          : {len(COMPANY_PROFILES)}")
    
    print(f"  Sea routes         : Hormuz={SEA_ROUTES.get('hormuz_route',{}).get('distance_nm','?') if SEA_ROUTES.get('hormuz_route') else 'N/A'}nm")
    print(f"  Diversions         : {len(SEA_ROUTES.get('diversions',[]))}")
    print(f"{'='*60}")

    # ── Save cache ────────────────────────────────────────────
    try:
        _save = {}
        for _vn in ["MARITIME_PRESENCE", "SHIP_CASUALTIES", "VESSEL_HISTORIES",
                     "GLOBAL_MILITARY", "HORMUZ_TRAFFIC", "MARITIME_INSPECTIONS",
                     "COMPANY_PROFILES", "SEA_ROUTES", "VESSEL_ENRICHMENT",
                     "OWNERSHIP_DATA", "SATE_TRACKING"]:
            if _vn in globals():
                _save[_vn] = globals()[_vn]
        with open(MARINE_ENHANCED_CACHE, "w", encoding="utf-8") as _cf:
            json.dump(_save, _cf, ensure_ascii=False, default=str)
        print(f"  ✓ Enhanced cache saved → {MARINE_ENHANCED_CACHE}")
    except Exception as _e:
        print(f"  ⚠ Cache save failed: {_e}")
