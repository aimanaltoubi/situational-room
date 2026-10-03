# c21_build_html.py
# Build final HTML file
# Auto-extracted from Cell 21

######################################################################
# CELL: C9 — Build HTML  [FIXED]
# Fix applied: _escape_script() applied to all injected JSON blobs
# to prevent </script> in Telegram/flight/war text from breaking
# the HTML script block and causing "unmatched ) in regex" error
######################################################################

import json, os
from datetime import datetime, timezone

def build_html():
    required = [
        "HTML_TEMPLATE","CESIUM_TOKEN","WAR_START","WAR_START_STR","OUTPUT_HTML",
        "SAT_DATA","JAM_DATA","GPSJAM_DATA",
        "INTEL_DATA","WAR_DATA","HIST_SAT_DATA","TELEGRAM_DATA",
    ]
    missing = [v for v in required if v not in globals()]
    if missing:
        print(f"[BUILD] Missing variables: {missing}")
        print("        Run Cells C2 → C9 in order then re-run this cell")
        return None

    now_utc  = datetime.now(timezone.utc)
    build_ts = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    # Fix: ensure WAR_START is timezone-aware for subtraction
    _ws = WAR_START if WAR_START.tzinfo else WAR_START.replace(tzinfo=timezone.utc)
    war_day  = max(0, (now_utc - _ws).days)

    # ── API key ───────────────────────────────────────────────────
    api_key = ""
    if "GEMINI_API_KEY" in globals() and GEMINI_API_KEY:
        api_key = GEMINI_API_KEY
        # API key loaded from .env via config.py
    if not api_key:
        print("      WARNING: No API key found — report button will show error")

    # ── Sanitize: strip surrogates + newlines/tabs ─────────────────
    # bool/int/float/None returned explicitly to avoid TypeError
    # when HIST_SAT_DATA contains Python booleans (over_iran: True)
    def _san(obj):
        if obj is None:
            return None
        if isinstance(obj, bool):
            return obj
        if isinstance(obj, (int, float)):
            return obj
        if isinstance(obj, str):
            return (obj.encode("utf-8", errors="replace")
                       .decode("utf-8")
                       .replace("\r\n", " ")
                       .replace("\n",   " ")
                       .replace("\r",   " ")
                       .replace("\t",   " "))
        if isinstance(obj, dict):
            return {_san(k): _san(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_san(v) for v in obj]
        return str(obj)

    # ── Script-tag escaping ────────────────────────────────────────
    # Any JSON blob injected inside a <script> block must not contain
    # the literal string </script> (or variants) — if it does, the
    # browser HTML parser terminates the script block early, causing
    # a "unmatched ) in regular expression" SyntaxError.
    # Telegram message text is the most likely source but war event
    # descriptions and flight callsigns can also contain HTML.
    def _escape_script(s):
        return (s
            .replace("</script>", "<\\/script>")
            .replace("</Script>", "<\\/Script>")
            .replace("</SCRIPT>", "<\\/SCRIPT>")
            .replace("<!--",      "<\\!--")
            .replace("]]>",       "]\\]>"))

    # ── SAT_DATA ──────────────────────────────────────────────────
    sat_json = _escape_script(
        json.dumps(_san(SAT_DATA), ensure_ascii=False, separators=(",", ":"))
    )

    # ── JAM_DATA ──────────────────────────────────────────────────
    if isinstance(JAM_DATA, dict):
        jam_list = []
        for z in JAM_DATA.get("zones", []):
            jam_list.append({
                "icao":          z.get("label_en", "JAM")[:8],
                "callsign":      z.get("label_ar", ""),
                "lat":           z.get("lat", 0),
                "lon":           z.get("lon", 0),
                "alt_m":         8000,
                "alt_ft":        26000,
                "degraded_type": "baseline zone",
                "source":        z.get("source", "baseline"),
            })
        jam_json = _escape_script(
            json.dumps(_san(jam_list), ensure_ascii=False, separators=(",", ":"))
        )
    else:
        jam_json = _escape_script(
            json.dumps(_san(JAM_DATA), ensure_ascii=False, separators=(",", ":"))
        )

    # ── GPSJAM_DATA ───────────────────────────────────────────────
    if isinstance(GPSJAM_DATA, dict):
        if "history" in GPSJAM_DATA:
            gpsjam_json = _escape_script(
                json.dumps(_san(GPSJAM_DATA), ensure_ascii=False, separators=(",", ":"))
            )
        elif "daily" in GPSJAM_DATA:
            history = []
            for date_str, val in sorted(
                (GPSJAM_DATA.get("daily") or {}).items()
            ):
                if val:
                    history.append({
                        "date":          date_str,
                        "me_avg":        val.get("avg", 0),
                        "top_intensity": val.get("max", 0),
                        "cell_count":    val.get("n", 0),
                    })
            adapted = {
                "cells":   [],
                "history": history,
                "me_avg":  GPSJAM_DATA.get("avg_overall", 0),
                "me_max":  max(
                    (v.get("max", 0)
                     for v in (GPSJAM_DATA.get("daily") or {}).values()
                     if v),
                    default=0,
                ),
                "source": GPSJAM_DATA.get("source", ""),
            }
            gpsjam_json = _escape_script(
                json.dumps(_san(adapted), ensure_ascii=False, separators=(",", ":"))
            )
        else:
            gpsjam_json = _escape_script(
                json.dumps(_san(GPSJAM_DATA), ensure_ascii=False, separators=(",", ":"))
            )
    else:
        gpsjam_json = json.dumps(
            {"cells": [], "history": [], "me_avg": 0, "me_max": 0, "source": "none"},
            separators=(",", ":"),
        )

    # ── FLIGHT_DATA ───────────────────────────────────────────────
    flight_json = _escape_script(
        json.dumps(_san(FLIGHT_DATA), ensure_ascii=False, separators=(",", ":"))
    )

    # ── INTEL_DATA ────────────────────────────────────────────────
    if isinstance(INTEL_DATA, dict):
        intel_norm = dict(INTEL_DATA)
        if "counts_by_cat" in intel_norm and "counts" not in intel_norm:
            intel_norm["counts"] = intel_norm["counts_by_cat"]
        intel_json = _escape_script(
            json.dumps(_san(intel_norm), ensure_ascii=False, separators=(",", ":"))
        )
    else:
        intel_json = _escape_script(
            json.dumps(_san(INTEL_DATA), ensure_ascii=False, separators=(",", ":"))
        )

    # ── WAR_DATA ──────────────────────────────────────────────────
    TYPE_COL = {
        "strike": "#ff2200", "airstrike": "#ff2200", "military": "#ff8800",
        "retaliation": "#ff4400", "political": "#4488ff",
        "diplomatic": "#4488ff", "humanitarian": "#44cc88",
        "missile": "#ff2200", "naval": "#0088ff",
    }
    if isinstance(WAR_DATA, list):
        war_list = []
        for ev in WAR_DATA:
            e = dict(ev)
            if "col" not in e:
                e["col"] = TYPE_COL.get(e.get("category", "military"), "#ff8800")
            war_list.append(e)
        war_json = _escape_script(
            json.dumps(_san(war_list), ensure_ascii=False, separators=(",", ":"))
        )
    elif isinstance(WAR_DATA, dict) and "events" in WAR_DATA:
        war_json = _escape_script(
            json.dumps(_san(WAR_DATA["events"]), ensure_ascii=False, separators=(",", ":"))
        )
    else:
        war_json = json.dumps([], separators=(",", ":"))

    # ── HIST_SAT_DATA ─────────────────────────────────────────────
    if isinstance(HIST_SAT_DATA, dict):
        hist_lean = {
            "war_start":   HIST_SAT_DATA.get("war_start", WAR_START_STR),
            "computed_at": HIST_SAT_DATA.get("computed_at", ""),
            "sat_count":   HIST_SAT_DATA.get("sat_count", 0),
            "days": [
                {
                    "date":       d["date"],
                    "day_num":    d["day_num"],
                    "iran_count": d.get("iran_count", 0),
                    "satellites": [
                        {k: v for k, v in s.items() if k not in ("l1", "l2")}
                        for s in d.get("satellites", [])
                    ],
                }
                for d in HIST_SAT_DATA.get("days", [])
            ],
        }
        hist_json = _escape_script(
            json.dumps(_san(hist_lean), ensure_ascii=False, separators=(",", ":"))
        )
    else:
        hist_json = json.dumps(
            {"war_start": WAR_START_STR, "days": [], "sat_count": 0},
            separators=(",", ":"),
        )

    # ── TELEGRAM_DATA ─────────────────────────────────────────────
    if isinstance(TELEGRAM_DATA, dict):
        telegram_json = _escape_script(
            json.dumps(_san(TELEGRAM_DATA), ensure_ascii=False, separators=(",", ":"))
        )
    else:
        telegram_json = json.dumps(
            {"channel": TELEGRAM_CHANNEL, "count": 0,
             "messages": [], "error": True},
            separators=(",", ":"),
        )

    # ── MARINE_DATA ──────────────────────────────────────────────────
    marine_json = _escape_script(
        json.dumps(_san(MARINE_DATA), ensure_ascii=False, separators=(",", ":"))
    )

    # ── Token replacement ─────────────────────────────────────────
    html = HTML_TEMPLATE
    # Attacked vessels JSON
    try:
        attacked_json = _escape_script(
            json.dumps(ATTACKED_VESSELS_DATA,
                       ensure_ascii=False, separators=(",",":"))
        )
    except NameError:
        attacked_json = '{"vessels":[],"count":0,"total_killed":0,"total_injured":0}'

    html = html.replace("__TOKEN__",          CESIUM_TOKEN)
    html = html.replace("__GEMINI_KEY__",     api_key)
    html = html.replace("__WAR_DAY__",        str(war_day))
    html = html.replace("__WAR_START__",      WAR_START_STR)
    html = html.replace("__TELEGRAM_CHANNEL__", TELEGRAM_CHANNEL)
    html = html.replace("__SYSTEM_NAME__",    SYSTEM_NAME_AR)
    html = html.replace("__WORKSPACE_NAME__", WORKSPACE_NAME_AR)
    html = html.replace("__ANALYTICS_NAME__", WORKSPACE["analytics_name_ar"])
    import html as _htmllib
    html = html.replace("__LBL_EVENTS__",     _htmllib.escape(LABELS["events_layer"]))
    html = html.replace("__LBL_TIMELINE__",   _htmllib.escape(LABELS["timeline_cat"]))
    html = html.replace("__LBL_ESCALATION__", _htmllib.escape(LABELS["escalation_title"]))
    html = html.replace("__FEATURES_JSON__", _escape_script(json.dumps(
        {**FEATURES, "telegram": bool(TELEGRAM_CHANNEL)}, separators=(",", ":"))))
    html = html.replace("__DATA_QUALITY_JSON__", _escape_script(json.dumps(
        globals().get("DATA_QUALITY") or {"sources": [], "issues": 0},
        ensure_ascii=False, separators=(",", ":"))))
    html = html.replace("__BUILD_TIME__",     build_ts)
    html = html.replace("__SAT_JSON__",       sat_json)
    html = html.replace("__JAM_JSON__",       jam_json)
    html = html.replace("__GPSJAM_JSON__",    gpsjam_json)
    html = html.replace("__FLIGHT_JSON__",    flight_json)
    html = html.replace("__INTEL_JSON__",     intel_json)
    html = html.replace("__WAR_JSON__",       war_json)
    html = html.replace("__HIST_SAT_JSON__",  hist_json)
    html = html.replace("__TELEGRAM_JSON__",  telegram_json)
    html = html.replace("__MARINE_JSON__",    marine_json)
    html = html.replace("__ATTACKED_JSON__", attacked_json)

    # ── Analytics pre-computed data ───────────────────────────────
    try:
        escalation_json = _escape_script(
            json.dumps(ESCALATION_ANALYSIS, ensure_ascii=False,
                       separators=(",", ":"))
        )
    except NameError:
        escalation_json = '{"days":[],"total_events":0}'

    try:
        isr_cueing_json = _escape_script(
            json.dumps(ISR_CUEING_ANALYSIS, ensure_ascii=False,
                       separators=(",",":"), default=str)
        )
    except Exception as _e:
        print(f"  ⚠ ISR_CUEING_ANALYSIS: {_e}")
        isr_cueing_json = '{}'

    try:
        attack_patterns_json = _escape_script(
            json.dumps(MARITIME_THREAT, ensure_ascii=False,
                       separators=(",", ":"), default=str)
        )
    except NameError:
        attack_patterns_json = '{"zones":[],"tanker_disruption_pct":0}'

    html = html.replace("__ESCALATION_JSON__",     escalation_json)
    html = html.replace("__ISR_CUEING_JSON__",      isr_cueing_json)
    html = html.replace("__ATTACK_PATTERNS_JSON__", attack_patterns_json)

    # ── New Cell 9 analytics ──────────────────────────────────────
    def _safe_json(var_name, fallback='{}'):
        try:
            return _escape_script(
                json.dumps(globals()[var_name], ensure_ascii=False, separators=(',', ':'))
            )
        except (KeyError, NameError):
            return fallback

    html = html.replace('__POLITICAL_JSON__',   _safe_json('POLITICAL_ANALYSIS',   '{"days":[],"total_events":0}'))
    html = html.replace('__DIPLOMATIC_JSON__',  _safe_json('DIPLOMATIC_INDEX',     '{"contradictions":[]}'))
    html = html.replace('__MARITIME_JSON__',    _safe_json('MARITIME_THREAT',      '{"zones":[]}'))
    html = html.replace('__JAM_CORR_JSON__',    _safe_json('JAMMING_CORRELATION',  '{"daily":[]}'))
    html = html.replace('__VIP_JSON__',         _safe_json('VIP_INTELLIGENCE',     '{"vip_by_day":[]}'))
    html = html.replace('__PREDICTION_JSON__',  _safe_json('CONFLICT_PREDICTION',  '{"score":0,"level":"unknown"}'))
    html = html.replace('__FLIGHT_HIST_JSON__', _safe_json('FLIGHT_HIST_DATA',     '{"flights":[],"daily_summary":{}}'))
    html = html.replace('__POL_EVENTS_JSON__',  _safe_json('POLITICAL_ANALYSIS',   '{"days":[]}'))

    # ── Report text (from C8.5) ───────────────────────────────────
    if "REPORT_TEXT" in globals() and REPORT_TEXT and len(str(REPORT_TEXT)) > 500:
        _report_html = str(REPORT_TEXT)
        print(f"      \u2713 Report from C8.5 injected ({len(_report_html):,} chars)")
    else:
        _report_html = (
            "<div style='text-align:center;padding:60px 24px;direction:rtl;"
            "font-family:Noto Naskh Arabic,serif;color:#0f172a'>"
            "<div style='font-size:44px;margin-bottom:18px'>&#128301;</div>"
            "<div style='font-size:19px;font-weight:700;color:#7a0028;margin-bottom:12px'>"
            "\u0627\u0644\u062a\u0642\u0631\u064a\u0631 \u0644\u0645 \u064a\u064f\u0648\u0644\u062f \u0628\u0639\u062f"
            "</div>"
            "<div style='font-size:14px;color:#8a5060;line-height:1.9;max-width:460px;margin:0 auto'>"
            "\u0634\u063a\u0651\u0644 Cell C8.5 \u062b\u0645 \u0623\u0639\u062f \u062a\u0634\u063a\u064a\u0644 C9"
            "</div></div>"
        )
        print("      \u26a0 REPORT_TEXT not set \u2014 run C8.5 first, then C9")

    # Strip raw newlines from report HTML — they break JS string literals
    _report_html = _report_html.replace("\n", " ").replace("\r", " ")
    # Escape for safe injection into JS single-quoted string (const _C85_REPORT='...')
    _report_html = _report_html.replace("\\", "\\\\")   # backslashes first
    _report_html = _report_html.replace("'", "\\'")        # single quotes
    _report_html = _escape_script(_report_html)              # </script> tags
    html = html.replace("__REPORT_TEXT__", _report_html)


    # ── Unreplaced token check ────────────────────────────────────
    remaining = [t for t in [
        "__TOKEN__", "__GEMINI_KEY__", "__WAR_DAY__", "__WAR_START__", "__BUILD_TIME__",
        "__SAT_JSON__", "__JAM_JSON__", "__GPSJAM_JSON__", "__FLIGHT_JSON__",
        "__INTEL_JSON__", "__WAR_JSON__", "__HIST_SAT_JSON__",
        "__TELEGRAM_JSON__", "__MARINE_JSON__", "__POLITICAL_JSON__", "__PREDICTION_JSON__", "__REPORT_TEXT__",
    ] if t in html]
    if remaining:
        print(f"      WARNING: Unreplaced tokens: {remaining}")

    # ── Write output ──────────────────────────────────────────────
    # Replace bare NaN/Infinity — invalid JSON in browsers.
    import re as _re
    html = _re.sub(r'\bNaN\b',      'null', html)
    html = _re.sub(r'\bInfinity\b',  'null', html)
    html = _re.sub(r'-Infinity',       'null', html)

    html_clean = html.encode("utf-8", errors="surrogatepass").decode(
        "utf-8", errors="replace"
    )
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_clean)

    size_kb   = os.path.getsize(OUTPUT_HTML) / 1024
    hist_days = len(HIST_SAT_DATA.get("days", [])) \
                if isinstance(HIST_SAT_DATA, dict) else 0
    tg_count  = TELEGRAM_DATA.get("count", 0) \
                if isinstance(TELEGRAM_DATA, dict) else 0
    tg_error  = TELEGRAM_DATA.get("error", True) \
                if isinstance(TELEGRAM_DATA, dict) else True

    print(f"      Output     : {OUTPUT_HTML}")
    print(f"      Size       : {size_kb:.0f} KB")
    print(f"      War day    : {war_day}  (start: {WAR_START_STR})")
    print(f"      Build time : {build_ts}")
    print(f"      API key    : {'present' if api_key else 'MISSING'}")
    print(f"      Satellites : {SAT_DATA.get('count', 0)}")
    print(f"      Hist days  : {hist_days}  ← war-day sat positions injected")
    marine_count = MARINE_DATA.get("total", 0) if isinstance(MARINE_DATA, dict) else 0
    marine_src   = MARINE_DATA.get("source", "?") if isinstance(MARINE_DATA, dict) else "?"
    print(f"      Marine     : {marine_count} vessels ({marine_src})")
    print(f"      Telegram   : {tg_count} messages  "
          f"{'✓' if not tg_error else '⚠ fetch failed — fallback link shown'}")
    if isinstance(JAM_DATA, list):
        print(f"      JAM items  : {len(JAM_DATA)}")
    else:
        print(f"      JAM items  : {len(JAM_DATA.get('zones', []))}")
    print(f"      Flights    : {FLIGHT_DATA.get('total', 0)}")
    if isinstance(WAR_DATA, list):
        print(f"      War events : {len(WAR_DATA)}")
    else:
        print(f"      War events : {len(WAR_DATA.get('events', []))}")
    # ── Data source summary ────────────────────────────────────
    print()
    print("      ━━━ Data Source Summary ━━━")
    _marine_ok = isinstance(MARINE_DATA, dict) and len(MARINE_DATA.get("vessels",[])) > 0
    _flight_ok = isinstance(FLIGHT_DATA, dict) and FLIGHT_DATA.get("total",0) > 0
    _flthist_ok= isinstance(FLIGHT_HIST_DATA, dict) and len(FLIGHT_HIST_DATA.get("flights",[])) > 0
    print(f"      {'✓' if _marine_ok else '✗'} Marine AIS    : {len(MARINE_DATA.get('vessels',[])) if isinstance(MARINE_DATA,dict) else 0} vessels")
    print(f"      {'✓' if _flight_ok else '✗'} Live Flights  : {FLIGHT_DATA.get('total',0) if isinstance(FLIGHT_DATA,dict) else 0} aircraft")
    print(f"      {'✓' if _flthist_ok else '✗'} Flight History: {len(FLIGHT_HIST_DATA.get('flights',[])) if isinstance(FLIGHT_HIST_DATA,dict) else 0} flights")
    if not _marine_ok:
        print("        ↳ Run Cell 7 to load marine vessel data")
    if not _flight_ok:
        print("        ↳ Run Cell 6 to load live flight radar")
    if not _flthist_ok:
        print("        ↳ Run the Flight Scraper cell to load historical flights")
    return OUTPUT_HTML


print("=" * 56)
print("  CELL 18 — Build HTML")
print("=" * 56)

import os
from datetime import datetime, timezone

# ── Ensure required globals are set ──────────────────────
if "CESIUM_TOKEN" not in dir():
    try:    CESIUM_TOKEN = globals()["CESIUM_TOKEN"]
    except KeyError:
        CESIUM_TOKEN = ""
        print("  ⚠ CESIUM_TOKEN fallback used")

if "WAR_START" not in dir():
    try:    WAR_START = globals()["WAR_START"]
    except KeyError:
        WAR_START = datetime(2026, 2, 28, tzinfo=timezone.utc)
        print("  ⚠ WAR_START fallback used")

if "OUTPUT_HTML" not in dir():
    OUTPUT_HTML = os.path.join(OUTPUT_DIR, "ifs_globe.html")
    print(f"  ⚠ OUTPUT_HTML fallback: {OUTPUT_HTML}")

if "FLIGHT_DATA" not in dir():
    try:    FLIGHT_DATA = globals()["FLIGHT_DATA"]
    except KeyError:
        FLIGHT_DATA = {"aircraft":[], "total":0, "counts":{}, "fir_summary":[]}
        print("  \u2718 FLIGHT_DATA not found — Cell 6 (Live Flights) was NOT run!")
        print("    \u2192 Live flight radar will NOT appear on the globe")

if "MARINE_DATA" not in dir():
    try:    MARINE_DATA = globals()["MARINE_DATA"]
    except KeyError:
        MARINE_DATA = {"vessels":[], "total":0, "counts":{}, "zones":[],
                       "hormuz_vessels":[], "moving_tankers":[], "stopped_tankers":[],
                       "source":"fallback — Cell 7 not run", "error":"not loaded"}
        print("  \u2718 MARINE_DATA not found — Cell 7 (Marine AIS) was NOT run!")
        print("    \u2192 Marine vessels will NOT appear on the globe")
        print("    \u2192 Run Cell 7 first, then re-run this cell")

if "FLIGHT_HIST_DATA" not in dir():
    try:    FLIGHT_HIST_DATA = globals()["FLIGHT_HIST_DATA"]
    except KeyError:
        FLIGHT_HIST_DATA = {"flights":[], "daily_summary":{}, "by_day":{}}
        print("  \u2718 FLIGHT_HIST_DATA not found — Cell 6 flight scraper was NOT run!")
        print("    \u2192 Flight timeline and VIP brief cards will be empty")

result = build_html()

if result:
    fname = os.path.basename(result)
    port  = os.environ.get("JUPYTER_PORT", "8888")
    url   = f"http://localhost:{port}/files/{fname}"
    print(f"\n  Ready: {url}")
    try:
        from IPython.display import display, HTML as IHTML
        display(IHTML(f'''
        <div style="font-family:Inter,sans-serif;background:#3a0012;color:#fff;
                    padding:14px 20px;border-radius:6px;display:inline-block;
                    margin-top:10px;line-height:2.2">
          <b style="font-size:14px">{SYSTEM_NAME_AR} — {SYSTEM_NAME_EN}</b><br>
          <a href="{url}" target="_blank"
             style="color:#ffd700;font-size:13px">{url}</a><br>
          <span style="color:rgba(255,255,255,.4);font-size:12px">
            Re-run Cell 9 to rebuild with fresh data.
          </span>
        </div>'''))
    except ImportError:
        pass
else:
    print("\n  Build failed — check errors above")

######################################################################
# ► END
######################################################################