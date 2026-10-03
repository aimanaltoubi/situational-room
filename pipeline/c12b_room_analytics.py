# c12b_room_analytics.py
# Subject-specific analytics for rooms that are not the conflict room.
# Builds ROOM_ANALYTICS = {"profile", "widgets": [...]} — a declarative list the
# dashboard renders generically (kpis / chart / table / insights / note).
# Profiles (workspace.json -> "analytics_profile"): conflict | terrorism | sanctions | general

import os
import hashlib
import pandas as pd

PROFILE = WORKSPACE.get("analytics_profile", "conflict")
ROOM_ANALYTICS = {"profile": PROFILE, "widgets": []}

_UNKNOWN = "غير محدد"


def _wid(kind, text):
    """Stable widget id (from its original title) so GUI layout edits survive rebuilds."""
    return kind[:1] + "-" + hashlib.md5(f"{kind}|{text}".encode("utf-8")).hexdigest()[:8]


def _kpis(items):
    out = []
    for it in items:
        d = {"label": it[0], "value": it[1]}
        if len(it) > 2 and it[2]:
            d["drill"] = it[2]
        out.append(d)
    return {"type": "kpis", "id": _wid("kpis", items[0][0]), "items": out}


def _chart(kind, title, labels, datasets, stacked=False, horizontal=False, drill=None):
    return {"type": "chart", "id": _wid("chart", title), "kind": kind, "title": title, "labels": labels,
            "datasets": datasets, "stacked": stacked, "horizontal": horizontal, "drill": drill}


def _table(title, columns, rows, drill=None):
    return {"type": "table", "id": _wid("table", title), "title": title, "columns": columns, "rows": rows,
            "drill": drill}


def _note(text):
    return {"type": "note", "id": _wid("note", text[:60]), "text": text}


def _insights(lines, scope="events"):
    return {"type": "insights", "id": _wid("insights", scope), "title": "أبرز الملاحظات",
            "items": [l for l in lines if l]}


def _confidence(n):
    """Plain confidence label from the amount of data behind a reading."""
    return "مرتفعة" if n >= 100 else "متوسطة" if n >= 30 else "منخفضة"


_ESTIMATIVE_GLOSSARY = ("مفردات التقدير (معايير التحليل الاستخباري الدولية): شبه مؤكد 95–99% · مرجّح جداً 80–95% · مرجّح 55–80% · "
                       "احتمال متساوٍ 45–55% · غير مرجّح 20–45% · غير مرجّح جداً 5–20% · شبه مستحيل 1–5%. "
                       "درجة الموثوقية لكل سجل (A–F للمصدر، 1–6 للمعلومة) تُدرَج في عمود confidence وفي ملف المصادر.")


def _load_events():
    path = os.path.join(DATA_DIR, "events.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    if df.empty or "date" not in df:
        return df.iloc[0:0]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[df["date"] >= pd.Timestamp(WAR_START_STR) - pd.Timedelta(days=1)].copy()
    for c in ("killed", "injured"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int) if c in df else 0
    for c in ("actor", "actor_grouped", "target", "country", "location", "event_type"):
        df[c] = df[c].fillna("").astype(str).str.strip() if c in df else ""
    df["group"] = df["actor_grouped"].where(df["actor_grouped"] != "", df["actor"])
    df["group"] = df["group"].where(df["group"] != "", _UNKNOWN)
    df["etype"] = df["event_type"].where(df["event_type"] != "", _UNKNOWN)
    return df


def _top_with_other(series, n):
    """Names of the n most frequent values; everything else is bucketed as 'أخرى'."""
    top = list(series.value_counts().head(n).index)
    return series.where(series.isin(top), "أخرى"), top


def _day(d):
    return str(d.date())


# ── Shared event widgets (terrorism + general) ───────────────────────────
def _event_widgets(df, noun, plural, with_lethality):
    end = df["date"].max().normalize()
    start = df["date"].min().normalize()
    last7 = df[df["date"] > end - pd.Timedelta(days=7)]
    prev7 = df[(df["date"] > end - pd.Timedelta(days=14)) & (df["date"] <= end - pd.Timedelta(days=7))]
    killed, injured = int(df["killed"].sum()), int(df["injured"].sum())
    known_groups = df[df["group"] != _UNKNOWN]["group"].nunique()

    _ev = lambda *f: {"file": "events", "filters": list(f)}
    w = [_kpis([
        (f"إجمالي {plural}", len(df), _ev()),
        ("إجمالي القتلى", killed, _ev({"col": "killed", "gt": 0})),
        ("إجمالي الجرحى", injured, _ev({"col": "injured", "gt": 0})),
        ("متوسط القتلى لكل " + noun, round(killed / len(df), 2)),
        ("الجهات الفاعلة المعروفة", known_groups),
        ("الدول المتأثرة", df[df["country"] != ""]["country"].nunique()),
        (f"{plural} آخر 7 أيام", len(last7)),
    ])]

    # Daily trend with 7-day moving average
    days = pd.date_range(start, end, freq="D")
    daily = df.groupby(df["date"].dt.normalize()).size().reindex(days, fill_value=0)
    w.append(_chart("line", f"عدد {plural} يومياً مع المتوسط المتحرك (7 أيام)",
                    [_day(d) for d in days],
                    [{"label": plural, "data": [int(v) for v in daily.values]},
                     {"label": "المتوسط المتحرك", "data": [round(float(v), 2) for v in daily.rolling(7, min_periods=1).mean().values]}],
                    drill={"file": "events", "x": {"col": "date", "bucket": "day"}}))

    # Weekly stacked by type
    df = df.assign(week=df["date"].dt.to_period("W").dt.start_time)
    grouped_type, top_types = _top_with_other(df["etype"], 6)
    wk = df.assign(tb=grouped_type).groupby(["week", "tb"]).size().unstack(fill_value=0)
    cols = top_types + (["أخرى"] if "أخرى" in wk.columns else [])
    w.append(_chart("bar", f"{plural} أسبوعياً حسب النوع", [_day(d) for d in wk.index],
                    [{"label": c, "data": [int(v) for v in wk[c].values]} for c in cols], stacked=True,
                    drill={"file": "events", "x": {"col": "date", "bucket": "week"}, "series": {"col": "etype"}}))

    # Weekly casualties
    cas = df.groupby("week")[["killed", "injured"]].sum()
    w.append(_chart("bar", "الضحايا أسبوعياً", [_day(d) for d in cas.index],
                    [{"label": "قتلى", "data": [int(v) for v in cas["killed"].values]},
                     {"label": "جرحى", "data": [int(v) for v in cas["injured"].values]}], stacked=True,
                    drill={"file": "events", "x": {"col": "date", "bucket": "week"}}))

    # Groups / actors
    g = df.groupby("group").agg(attacks=("group", "size"), killed=("killed", "sum"), injured=("injured", "sum"),
                                first=("date", "min"), last=("date", "max")).sort_values("attacks", ascending=False)
    recent_cut = end - pd.Timedelta(days=30)
    rows = []
    for name, r in g.head(15).iterrows():
        leth = round(r["killed"] / r["attacks"], 2)
        rows.append([name, int(r["attacks"]), int(r["killed"]), int(r["injured"]), leth,
                     _day(r["first"]), _day(r["last"]), "نعم" if r["last"] > recent_cut else "لا"])
    w.append(_table("الجهات الفاعلة" if not with_lethality else "الجماعات والجهات المنفذة",
                    ["الجهة", plural, "قتلى", "جرحى", "الفتك (قتلى/" + noun + ")", "أول ظهور", "آخر نشاط", "نشطة آخر 30 يوماً"], rows,
                    drill={"targets": [{"file": "events", "cols": ["group"]}], "cell": 0}))

    # Targets
    tg = df[df["target"] != ""]["target"]
    if len(tg):
        tgb, top_t = _top_with_other(tg, 8)
        counts = tgb.value_counts()
        w.append(_chart("doughnut", "الأهداف المستهدفة", [str(i) for i in counts.index],
                        [{"label": "الأهداف", "data": [int(v) for v in counts.values]}],
                        drill={"file": "events", "x": {"col": "target"}}))

    # Hotspots
    ct = df[df["country"] != ""].groupby("country").agg(n=("country", "size"), k=("killed", "sum")).sort_values("n", ascending=False).head(10)
    if len(ct):
        w.append(_chart("bar", "الدول الأكثر تأثراً", [str(i) for i in ct.index],
                        [{"label": plural, "data": [int(v) for v in ct["n"].values]},
                         {"label": "قتلى", "data": [int(v) for v in ct["k"].values]}], horizontal=True,
                        drill={"file": "events", "x": {"col": "country"}}))
    loc = df[df["location"] != ""].groupby(["location", "country"]).agg(n=("location", "size"), k=("killed", "sum")).sort_values("n", ascending=False).head(10)
    if len(loc):
        w.append(_table("البؤر الساخنة", ["الموقع", "الدولة", plural, "قتلى"],
                        [[a, b, int(r["n"]), int(r["k"])] for (a, b), r in loc.iterrows()],
                        drill={"targets": [{"file": "events", "cols": ["location"]}], "cell": 0}))

    # Newly emerged groups
    new = g[(g["first"] >= recent_cut) & (g.index != _UNKNOWN)]
    if len(new):
        w.append(_table("جهات ظهرت خلال آخر 30 يوماً", ["الجهة", plural, "قتلى", "أول ظهور"],
                        [[n, int(r["attacks"]), int(r["killed"]), _day(r["first"])] for n, r in new.iterrows()],
                        drill={"targets": [{"file": "events", "cols": ["group"]}], "cell": 0}))

    # Country severity index modelled on the Global Terrorism Index weighting
    # (incident 1, death 3, injury 0.5; recent activity weighs more). Raw weighted scores,
    # scaled 0-10 on a log scale against the worst country.
    if with_lethality:
        age = (end - df["date"]).dt.days
        wgt = pd.Series(0.25, index=df.index).mask(age <= 90, 0.5).mask(age <= 30, 1.0)
        df["_score"] = wgt * (1 + 3 * df["killed"] + 0.5 * df["injured"])
        sc = df[df["country"] != ""].groupby("country").agg(
            n=("country", "size"), k=("killed", "sum"), j=("injured", "sum"), s=("_score", "sum")).sort_values("s", ascending=False)
        if len(sc):
            import math
            top = float(sc["s"].iloc[0])
            sc["idx"] = [round(10 * math.log1p(float(v)) / math.log1p(top), 1) for v in sc["s"]]
            w.append(_table("مؤشر خطورة الإرهاب لكل دولة (مستلهم من مؤشر الإرهاب العالمي)",
                            ["الدولة", plural, "قتلى", "جرحى", "الدرجة الخام (مرجّحة بحداثة النشاط)", "المؤشر (0–10)"],
                            [[c, int(r["n"]), int(r["k"]), int(r["j"]), round(float(r["s"]), 1), r["idx"]] for c, r in sc.head(15).iterrows()],
                            drill={"targets": [{"file": "events", "cols": ["country"]}], "cell": 0}))

    # Insights
    lines = []
    a, b = len(last7), len(prev7)
    if b == 0 and a > 0:
        lines.append(f"نشاط جديد: {a} {plural} خلال آخر 7 أيام بعد أسبوع بلا تسجيل.")
    elif b > 0:
        pct = round((a - b) / b * 100)
        word = "ارتفع" if pct > 0 else "انخفض" if pct < 0 else "ثبت"
        lines.append(f"{word} عدد {plural} خلال آخر 7 أيام ({a} مقابل {b} في الأسبوع السابق)"
                     + (f" بنسبة {abs(pct)}%." if pct else "."))
    known = g[g.index != _UNKNOWN]
    if len(known):
        top = known.iloc[0]
        lines.append(f"أنشط جهة: {known.index[0]} ({int(top['attacks'])} {noun}، {int(top['killed'])} قتيلاً).")
        lethal = known[known["attacks"] >= 3].sort_values("killed", ascending=False)
        if with_lethality and len(lethal):
            lines.append(f"الأعلى فتكاً بين الجهات التي سجّلت 3 أو أكثر من {plural}: "
                         f"{lethal.index[0]} بمتوسط {round(lethal.iloc[0]['killed'] / lethal.iloc[0]['attacks'], 1)} قتيل لكل {noun}.")
    if len(ct):
        lines.append(f"أكثر الدول تأثراً: {ct.index[0]} ({int(ct.iloc[0]['n'])} {noun}).")
    dd = df.groupby(df["date"].dt.normalize())["killed"].sum()
    if len(dd) and dd.max() > 0:
        lines.append(f"أكثر الأيام دموية: {dd.idxmax().date()} ({int(dd.max())} قتيلاً).")
    lines.append(f"درجة الثقة في هذه القراءات: {_confidence(len(df))} (بناءً على {len(df)} سجلاً).")
    w.insert(1, _insights(lines))
    w.append(_note(_ESTIMATIVE_GLOSSARY))
    return w


# ── Sanctions ────────────────────────────────────────────────────────────
def _is_delisting(s):
    s = s.lower()
    return any(k in s for k in ("delist", "removal", "removed", "lift", "رفع", "إلغاء", "شطب"))


def _norm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def _vessel_widgets():
    path = os.path.join(DATA_DIR, "sanctioned-vessels.csv")
    if not os.path.exists(path):
        if os.path.exists(os.path.join(DATA_DIR, "sanctions-entities.csv")):
            return []  # vessels are covered by the entity list (type=vessel) and AIS screening
        return [_note("لمطابقة السفن الخاضعة للعقوبات مع نظام التعريف الآلي (AIS) ارفع الملف sanctioned-vessels.csv "
                      "(الأعمدة: name, imo, mmsi, flag, authority, date).")]
    listed = pd.read_csv(path, dtype=str).fillna("")
    if not FEATURES["marine"]:
        return [_note(f"تم تحميل {len(listed)} سفينة خاضعة للعقوبات، لكن وحدة الملاحة البحرية (AIS) غير مفعّلة "
                      "لهذه الغرفة — فعّلها من الإعدادات لإجراء المطابقة.")]
    vessels = _g("MARINE_DATA", {}).get("vessels", [])
    by_imo = {str(v.get("imo", "")): v for v in vessels if v.get("imo")}
    by_mmsi = {str(v.get("mmsi", "")): v for v in vessels if v.get("mmsi")}
    by_name = {_norm(v.get("name", "")): v for v in vessels if v.get("name")}
    rows, dark = [], 0
    for _, r in listed.iterrows():
        v = (by_imo.get(r.get("imo", "")) if r.get("imo") else None) \
            or (by_mmsi.get(r.get("mmsi", "")) if r.get("mmsi") else None) \
            or (by_name.get(_norm(r.get("name", ""))) if r.get("name") else None)
        if not v:
            continue
        is_dark = bool(v.get("going_dark"))
        dark += is_dark
        rows.append([r.get("name") or v.get("name", ""), r.get("imo") or v.get("imo", ""),
                     v.get("flag", ""), r.get("authority", ""), v.get("zone_name") or v.get("zone", ""),
                     f"{v.get('speed', 0)} عقدة", "نعم" if is_dark else "لا",
                     f"{v.get('lat', '')}, {v.get('lon', '')}"])
    w = [_kpis([("سفن خاضعة للعقوبات (قائمة)", len(listed)), ("مرصودة الآن في AIS", len(rows)),
                ("منها بلا إشارة AIS", dark)])]
    if rows:
        w.append(_table("السفن الخاضعة للعقوبات المرصودة", ["السفينة", "IMO", "العلم", "الجهة المُصدِرة", "المنطقة", "السرعة", "AIS مُطفأ", "الموقع"], rows))
    elif not vessels:
        w.append(_note("لا توجد بيانات سفن محمّلة من AIS حالياً — تعذّرت المطابقة (راجع «جودة البيانات»)."))
    else:
        w.append(_note("لم تُطابَق أي سفن من القائمة مع السفن المرصودة حالياً."))
    return w


def _sanctions_widgets(df):
    end = df["date"].max().normalize()
    df = df.assign(delist=df["etype"].map(_is_delisting),
                   month=df["date"].dt.to_period("M").dt.start_time)
    n_delist = int(df["delist"].sum())
    last30 = df[df["date"] > end - pd.Timedelta(days=30)]
    targets = df[df["target"] != ""]
    w = [_kpis([
        ("إجمالي الإجراءات", len(df), {"file": "events", "filters": []}),
        ("إدراجات / إجراءات تقييدية", len(df) - n_delist),
        ("رفع عقوبات", n_delist),
        ("جهات مستهدفة مختلفة", targets["target"].nunique()),
        ("الجهات المُصدِرة", df["group"].nunique()),
        ("دول مستهدفة", df[df["country"] != ""]["country"].nunique()),
        ("إجراءات آخر 30 يوماً", len(last30)),
    ])]

    auth, top_auth = _top_with_other(df["group"], 6)
    mo = df.assign(ab=auth).groupby(["month", "ab"]).size().unstack(fill_value=0)
    cols = top_auth + (["أخرى"] if "أخرى" in mo.columns else [])
    w.append(_chart("bar", "الإجراءات شهرياً حسب الجهة المُصدِرة", [_day(d) for d in mo.index],
                    [{"label": c, "data": [int(v) for v in mo[c].values]} for c in cols], stacked=True,
                    drill={"file": "events", "x": {"col": "date", "bucket": "month"}, "series": {"col": "group"}}))

    types = df["etype"].value_counts()
    w.append(_chart("doughnut", "الإجراءات حسب النوع", [str(i) for i in types.index],
                    [{"label": "النوع", "data": [int(v) for v in types.values]}],
                    drill={"file": "events", "x": {"col": "etype"}}))

    if len(targets):
        tt = targets.groupby("target").agg(n=("target", "size"), auth=("group", lambda s: "، ".join(sorted(set(s))[:3])),
                                           first=("date", "min"), last=("date", "max")).sort_values("n", ascending=False).head(15)
        w.append(_table("الجهات الأكثر استهدافاً", ["الجهة المستهدفة", "عدد الإجراءات", "الجهات المُصدِرة", "أول إجراء", "آخر إجراء"],
                        [[n, int(r["n"]), r["auth"], _day(r["first"]), _day(r["last"])] for n, r in tt.iterrows()],
                        drill={"targets": [{"file": "events", "cols": ["target"]}, {"file": "sanctions_entities", "cols": ["name"]}], "cell": 0}))

    ct = df[df["country"] != ""]["country"].value_counts().head(10)
    if len(ct):
        w.append(_chart("bar", "الدول المستهدفة", [str(i) for i in ct.index],
                        [{"label": "الإجراءات", "data": [int(v) for v in ct.values]}], horizontal=True,
                        drill={"file": "events", "x": {"col": "country"}}))

    au = df.groupby("group").agg(n=("group", "size"), d=("delist", "sum"), first=("date", "min"), last=("date", "max")).sort_values("n", ascending=False)
    w.append(_table("مقارنة الجهات المُصدِرة", ["الجهة", "الإجراءات", "رفع عقوبات", "أول إجراء", "آخر إجراء"],
                    [[n, int(r["n"]), int(r["d"]), _day(r["first"]), _day(r["last"])] for n, r in au.iterrows()],
                    drill={"targets": [{"file": "events", "cols": ["group"]}], "cell": 0}))

    w.extend(_vessel_widgets())

    lines = []
    m = df.groupby("month").size()
    if len(m) >= 2:
        a, b = int(m.iloc[-1]), int(m.iloc[-2])
        if b:
            pct = round((a - b) / b * 100)
            lines.append(f"عدد الإجراءات في آخر شهر مسجّل ({m.index[-1].strftime('%Y-%m')}): {a} مقابل {b} قبله"
                         + (f" ({'+' if pct > 0 else ''}{pct}%)." if pct else "."))
    if len(au):
        lines.append(f"أنشط جهة مُصدِرة: {au.index[0]} ({int(au.iloc[0]['n'])} إجراء).")
    if len(targets):
        rep = targets["target"].value_counts()
        if rep.iloc[0] > 1:
            lines.append(f"أكثر الجهات تكراراً في الإجراءات: {rep.index[0]} ({int(rep.iloc[0])} إجراء).")
        multi = targets.groupby("target")["group"].nunique()
        both = int((multi > 1).sum())
        if both:
            lines.append(f"{both} جهة مستهدفة بعقوبات من أكثر من جهة مُصدِرة (تنسيق دولي).")
    if len(ct):
        lines.append(f"أكثر الدول استهدافاً: {ct.index[0]} ({int(ct.iloc[0])} إجراء).")
    lines.append(f"درجة الثقة في هذه القراءات: {_confidence(len(df))} (بناءً على {len(df)} سجلاً).")
    w.insert(1, _insights(lines))
    w.append(_note(_ESTIMATIVE_GLOSSARY))
    return w


def _g(name, default):
    v = globals().get(name)
    return default if v is None else v


# ── Build ────────────────────────────────────────────────────────────────
if PROFILE != "conflict":
    _df = _load_events()
    if _df is None or _df.empty:
        ROOM_ANALYTICS["widgets"] = [_note("لا توجد أحداث بعد لهذه الغرفة — ارفع الملف events.csv من صفحة الغرفة "
                                           "ثم أعد البناء لتظهر التحليلات الخاصة بموضوعها.")]
        if PROFILE == "sanctions":
            ROOM_ANALYTICS["widgets"] += _vessel_widgets()
    elif PROFILE == "terrorism":
        ROOM_ANALYTICS["widgets"] = _event_widgets(_df, "هجوم", "الهجمات", True)
    elif PROFILE == "sanctions":
        ROOM_ANALYTICS["widgets"] = _sanctions_widgets(_df)
    else:
        ROOM_ANALYTICS["widgets"] = _event_widgets(_df, "حدث", "الأحداث", False)
    print(f"[ROOM-ANALYTICS] profile={PROFILE}: {len(ROOM_ANALYTICS['widgets'])} widgets")
else:
    print("[ROOM-ANALYTICS] conflict profile — using the built-in conflict analytics")
