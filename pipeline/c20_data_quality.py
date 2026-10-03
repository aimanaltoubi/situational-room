# c20_data_quality.py
# Builds DATA_QUALITY: one honest status line per data source for this room
# (what is loaded, how fresh it is, what is missing). Shown on the room page and
# in the dashboard, and saved to output/data_quality.json.

import os, json
from datetime import datetime, timezone

_now = datetime.now(timezone.utc)


def _mtime(path):
    if not os.path.exists(path):
        return None
    return datetime.fromtimestamp(os.path.getmtime(path), timezone.utc)


def _parse(ts):
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _age_h(dt):
    return None if dt is None else (_now - dt).total_seconds() / 3600


def _row(key, label, status, count, unit, source, fetched, note):
    return {
        "key": key, "label": label, "status": status,
        "count": count, "unit": unit, "source": source,
        "updated_at": fetched.isoformat() if fetched else None,
        "note": note,
    }


def _g(name, default):
    v = globals().get(name)
    return default if v is None else v


_rows = []
_data = lambda f: os.path.join(DATA_DIR, f)

# ── Events (core) ─────────────────────────────────────────────
_wd = _g("WAR_DATA", {})
_events = _wd if isinstance(_wd, list) else _wd.get("events", [])
_t_end = _parse(_wd.get("t_end")) if isinstance(_wd, dict) else None
_ev_file = _mtime(_data("events.csv"))
if not _events:
    _rows.append(_row("events", "الأحداث", "empty", 0, "حدث", "events.csv", _ev_file,
                      "لا توجد أحداث — ارفع الملف events.csv من صفحة الغرفة."))
elif _t_end and (_now - _t_end).days > 14:
    _rows.append(_row("events", "الأحداث", "stale", len(_events), "حدث", "events.csv", _ev_file,
                      f"آخر حدث مسجّل بتاريخ {_t_end.date()} — البيانات قد لا تعكس الوضع الحالي."))
else:
    _rows.append(_row("events", "الأحداث", "ok", len(_events), "حدث", "events.csv", _ev_file,
                      f"آخر حدث: {_t_end.date()}" if _t_end else ""))

# ── Political trajectory (core) ───────────────────────────────
_pol_n = len(_g("pol_events", []))
_pol_file = _mtime(_data("political-events.csv"))
_rows.append(_row("political", "المسار السياسي",
                  "ok" if _pol_n else "empty", _pol_n, "حدث", "political-events.csv", _pol_file,
                  "" if _pol_n else "لا توجد أحداث سياسية — ارفع الملف political-events.csv."))

# ── Telegram ──────────────────────────────────────────────────
if TELEGRAM_CHANNEL:
    _tg = _g("TELEGRAM_DATA", {})
    _tg_n = _tg.get("count", 0) if isinstance(_tg, dict) else 0
    _tg_at = _parse(_tg.get("fetched_at")) if isinstance(_tg, dict) else None
    if not _tg_n or (isinstance(_tg, dict) and _tg.get("error")):
        _rows.append(_row("telegram", "نشرة تيليجرام", "empty", _tg_n, "نشرة", "@" + TELEGRAM_CHANNEL, _tg_at,
                          "تعذّر جلب النشرات من القناة."))
    else:
        _rows.append(_row("telegram", "نشرة تيليجرام", "ok", _tg_n, "نشرة", "@" + TELEGRAM_CHANNEL, _tg_at, ""))

# ── Satellites ────────────────────────────────────────────────
if FEATURES["satellites"]:
    _s = _g("SAT_DATA", {})
    _s_n = _s.get("count", 0) if isinstance(_s, dict) else 0
    _s_at = _parse(_s.get("fetched_at")) if isinstance(_s, dict) else None
    _h = _age_h(_s_at)
    _hist_days = len(_g("HIST_SAT_DATA", {}).get("days", []))
    if not _s_n:
        _rows.append(_row("satellites", "الأقمار الاصطناعية", "empty", 0, "قمر", "TLE", _s_at,
                          "لم تُحمَّل بيانات المدارات."))
    elif _h is not None and _h > 48:
        _rows.append(_row("satellites", "الأقمار الاصطناعية", "stale", _s_n, "قمر", "TLE", _s_at,
                          f"عمر بيانات المدارات {int(_h)} ساعة."))
    else:
        _rows.append(_row("satellites", "الأقمار الاصطناعية", "ok", _s_n, "قمر", "TLE", _s_at,
                          f"المواقع التاريخية: {_hist_days} يوم."))

# ── GPS jamming ───────────────────────────────────────────────
if FEATURES["gps_jamming"]:
    _gj = _g("GPSJAM_DATA", {})
    _hist = _gj.get("history", []) if isinstance(_gj, dict) else []
    _span = max(1, (_now.date() - WAR_START.date()).days + 1)
    _have = len({h.get("date") for h in _hist if h.get("date")})
    _last = _parse(_hist[-1]["date"]) if _hist else None
    _gj_file = _mtime(os.path.join(CACHE_DIR, "gpsjam_historical.json"))
    if not _have:
        _rows.append(_row("gps_jamming", "تشويش GPS", "empty", 0, "يوم", "gpsjam.org + ADS-B", _gj_file,
                          "لا يوجد سجل تاريخي — الأيام الناقصة تظهر فارغة ولا تُقدَّر."))
    elif _have < _span * 0.7:
        _rows.append(_row("gps_jamming", "تشويش GPS", "partial", _have, "يوم", "gpsjam.org + ADS-B", _gj_file,
                          f"سجل فعلي لـ {_have} من {_span} يوماً — الأيام الناقصة تظهر فارغة ولا تُقدَّر."))
    elif _last and (_now - _last).days > 2:
        _rows.append(_row("gps_jamming", "تشويش GPS", "stale", _have, "يوم", "gpsjam.org + ADS-B", _gj_file,
                          f"آخر يوم مسجّل {_last.date()}."))
    else:
        _rows.append(_row("gps_jamming", "تشويش GPS", "ok", _have, "يوم", "gpsjam.org + ADS-B", _gj_file,
                          f"تغطية {_have} من {_span} يوماً."))

# ── Flights ───────────────────────────────────────────────────
if FEATURES["flights"]:
    _fl = _g("FLIGHT_DATA", {})
    _fh = _g("FLIGHT_HIST_DATA", {})
    _live = _fl.get("total", 0) if isinstance(_fl, dict) else 0
    _histn = len(_fh.get("flights", [])) if isinstance(_fh, dict) else 0
    _fh_file = _mtime(os.path.join(CACHE_DIR, "flight_historical.json"))
    if not _live and not _histn:
        _rows.append(_row("flights", "الرحلات الجوية", "empty", 0, "رحلة", "ADS-B Exchange + AeroDataBox", _fh_file,
                          "لا رحلات حية ولا سجل تاريخي."))
    elif not _live or not _histn:
        _rows.append(_row("flights", "الرحلات الجوية", "partial", _live or _histn, "رحلة",
                          "ADS-B Exchange + AeroDataBox", _fh_file,
                          "الرحلات الحية فقط." if _live else "السجل التاريخي فقط — لا رحلات حية الآن."))
    else:
        _rows.append(_row("flights", "الرحلات الجوية", "ok", _live, "رحلة حية",
                          "ADS-B Exchange + AeroDataBox", _fh_file, f"السجل التاريخي: {_histn} رحلة."))

# ── Marine ────────────────────────────────────────────────────
if FEATURES["marine"]:
    _m = _g("MARINE_DATA", {})
    _m_n = len(_m.get("vessels", [])) if isinstance(_m, dict) else 0
    _m_file = _mtime(os.path.join(CACHE_DIR, "marine_data.json"))
    _h = _age_h(_m_file)
    if not _m_n:
        _rows.append(_row("marine", "الملاحة البحرية", "empty", 0, "سفينة", "Datalastic AIS", _m_file,
                          "لم تُحمَّل أي سفن — تحقّق من مفتاح Datalastic ورصيده."))
    elif _h is not None and _h > 24:
        _rows.append(_row("marine", "الملاحة البحرية", "stale", _m_n, "سفينة", "Datalastic AIS", _m_file,
                          f"المواقع عمرها {int(_h)} ساعة."))
    else:
        _rows.append(_row("marine", "الملاحة البحرية", "ok", _m_n, "سفينة", "Datalastic AIS", _m_file, ""))

# ── Attacked vessels ──────────────────────────────────────────
if FEATURES["attacked_vessels"]:
    _av_n = _g("ATTACKED_VESSELS_DATA", {}).get("count", 0)
    _rows.append(_row("attacked_vessels", "السفن المهاجمة",
                      "ok" if _av_n else "empty", _av_n, "هجوم", "vessels-attack-dataset.txt",
                      _mtime(_data("vessels-attack-dataset.txt")),
                      "" if _av_n else "ارفع الملف vessels-attack-dataset.txt."))

# ── ACLED forecast input ──────────────────────────────────────
_acled_path = _data("Middle_East_clean_2026.csv")
_acled_file = _mtime(_acled_path)
if _acled_file is None:
    if WORKSPACE["analytics_profile"] == "conflict":
        _rows.append(_row("acled", "بيانات ACLED للتوقعات", "empty", 0, "", "Middle_East_clean_2026.csv", None,
                          "غير متوفرة — لن يُنتَج التقرير التحليلي الأسبوعي."))
else:
    _last_week = None
    try:
        import pandas as _pd
        _last_week = _pd.to_datetime(_pd.read_csv(_acled_path, usecols=["WEEK"])["WEEK"]).max()
    except Exception:
        pass
    _stale = _last_week is not None and (_now.replace(tzinfo=None) - _last_week.to_pydatetime()).days > 21
    _rows.append(_row("acled", "بيانات ACLED للتوقعات", "stale" if _stale else "ok", 0, "",
                      "Middle_East_clean_2026.csv", _acled_file,
                      (f"آخر أسبوع في البيانات {_last_week.date()}" if _last_week is not None else "")
                      + (" — قديمة، التوقعات لا تغطي الفترة الأخيرة." if _stale else "")))

if WORKSPACE["analytics_profile"] == "sanctions":
    for _key, _fname, _lbl, _hint in (
        ("sanctions_entities", "sanctions-entities.csv", "الجهات المُدرجة", "لا تمكن تحليلات الشبكات والمخاطر بدونها."),
        ("sanctions_relationships", "sanctions-relationships.csv", "علاقات الملكية والسيطرة", "لا تُحسب قاعدة 50% والشبكات بدونها."),
    ):
        _p = _data(_fname)
        _n = 0
        if os.path.exists(_p):
            with open(_p, encoding="utf-8") as _f:
                _n = max(0, sum(1 for _ in _f) - 1)
        _rows.append(_row(_key, _lbl, "ok" if _n else "empty", _n, "سجل", _fname, _mtime(_p),
                          "" if _n else f"ارفع الملف {_fname} — {_hint}"))
    _sv = _data("sanctioned-vessels.csv")
    _sv_n = 0
    if os.path.exists(_sv):
        with open(_sv, encoding="utf-8") as _f:
            _sv_n = max(0, sum(1 for _ in _f) - 1)
    if _sv_n:
        _rows.append(_row("sanctioned_vessels", "السفن الخاضعة للعقوبات", "ok", _sv_n, "سفينة",
                          "sanctioned-vessels.csv", _mtime(_sv), ""))

_EDIT = {"events": "events", "political": "political", "attacked_vessels": "vessels", "acled": "acled",
         "sanctions_entities": "sanctions_entities", "sanctions_relationships": "sanctions_relationships",
         "sanctioned_vessels": "sanctioned_vessels"}
_grades = {}
_src_path = _data("sources.csv")
if os.path.exists(_src_path):
    import csv as _csv
    with open(_src_path, newline="", encoding="utf-8-sig") as _f:
        for _s in _csv.DictReader(_f):
            if _s.get("dataset") and (_s.get("reliability") or _s.get("credibility")):
                _grades[_s["dataset"]] = (_s.get("reliability", "") + _s.get("credibility", "")).strip()
for _r in _rows:
    _r["edit"] = _EDIT.get(_r["key"])
    _r["grade"] = _grades.get(_r["edit"] or _r["key"], "")

_issues = [r for r in _rows if r["status"] != "ok"]
DATA_QUALITY = {
    "generated_at": _now.isoformat(),
    "workspace": WORKSPACE_SLUG,
    "sources": _rows,
    "issues": len(_issues),
}

with open(os.path.join(OUTPUT_DIR, "data_quality.json"), "w", encoding="utf-8") as _f:
    json.dump(DATA_QUALITY, _f, ensure_ascii=False, indent=2)

print(f"[DATA-QUALITY] {len(_rows)} sources, {len(_issues)} need attention")
for _r in _issues:
    print(f"   ⚠ {_r['label']}: {_r['status']} — {_r['note']}")
