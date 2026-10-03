# c12c_sanctions_network.py
# Sanctions-risk analytics in the style of illicit-finance intelligence providers (e.g. Kharon):
# ownership / control networks around designated parties, 50%-rule exposure, entity risk
# scoring, evasion hubs and AIS screening of vessels linked to designated parties.
#
# Inputs (data/):
#   sanctions-entities.csv       entity_id,name,type,country,program,authority,designation_date,status,aliases,imo,mmsi
#   sanctions-relationships.csv  source,target,relation,ownership_pct   (source = owner/controller of target)
# Adds widgets to the front of ROOM_ANALYTICS (built by c12b) for sanctions rooms.

import os
from collections import defaultdict, deque
import pandas as pd

_PROFILE = WORKSPACE.get("analytics_profile", "conflict")

_REL_AR = {
    "owns": "يملك", "controls": "يسيطر على", "manages": "يدير", "operates": "يشغّل",
    "director": "عضو مجلس إدارة في", "front": "واجهة لـ", "affiliate": "مرتبط بـ", "partner": "شريك لـ",
}
_OWN_RELS = {"owns", "own", "owner", "ownership", "shareholder", "parent"}
_REL_SCORE = {"front": 85, "controls": 70, "manages": 70, "operates": 70, "director": 50, "affiliate": 50, "partner": 50}


def _nrm(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def _rel(r):
    r = str(r).strip().lower()
    return "owns" if r in _OWN_RELS else r


def _pct(v):
    try:
        return float(str(v).replace("%", "").strip())
    except ValueError:
        return None


def _heading(text):
    return {"type": "heading", "id": _wid("heading", text), "text": text}


_ENT_DRILL = {"targets": [{"file": "sanctions_entities", "cols": ["name", "entity_id"]},
                           {"file": "sanctions_relationships", "cols": ["source", "target"]}], "cell": 0}


def _build_sanctions_network():
    ent_path = os.path.join(DATA_DIR, "sanctions-entities.csv")
    rel_path = os.path.join(DATA_DIR, "sanctions-relationships.csv")
    if not os.path.exists(ent_path):
        return [_heading("مخاطر الجهات والشبكات"),
                _note("لتحليل الشبكات ومخاطر الجهات (الملكية والسيطرة وقاعدة 50% وغيرها) ارفع الملفين: "
                      "sanctions-entities.csv (الأعمدة: entity_id, name, type, country, program, authority, designation_date, "
                      "status, aliases, imo, mmsi) وsanctions-relationships.csv (الأعمدة: source, target, relation, ownership_pct "
                      "— حيث source هو المالك/المسيطر). العلاقات المدعومة: owns, controls, manages, operates, director, front, affiliate, partner.")]

    ents = pd.read_csv(ent_path, dtype=str).fillna("")
    rels = pd.read_csv(rel_path, dtype=str).fillna("") if os.path.exists(rel_path) else pd.DataFrame(
        columns=["source", "target", "relation", "ownership_pct"])

    nodes, index = {}, {}

    def _register(key, node, *names):
        for n in names:
            if n:
                index.setdefault(_nrm(n), key)

    for i, r in ents.iterrows():
        key = f"e{i}"
        status = (r.get("status") or "designated").strip().lower()
        status = status if status in ("designated", "delisted", "undesignated") else "designated"
        aliases = [a.strip() for a in (r.get("aliases") or "").split(";") if a.strip()]
        node = {"name": r.get("name", "").strip() or r.get("entity_id", key), "type": (r.get("type") or "").strip().lower() or "company",
                "country": r.get("country", "").strip(), "program": r.get("program", "").strip(),
                "authority": r.get("authority", "").strip(), "date": r.get("designation_date", "").strip(),
                "status": status, "imo": r.get("imo", "").strip(), "mmsi": r.get("mmsi", "").strip()}
        nodes[key] = node
        _register(key, node, r.get("entity_id", ""), node["name"], node["imo"], node["mmsi"], *aliases)

    def _resolve(ref):
        ref = str(ref).strip()
        if not ref:
            return None
        k = index.get(_nrm(ref))
        if k:
            return k
        key = f"u{len(nodes)}"
        nodes[key] = {"name": ref, "type": "company", "country": "", "program": "", "authority": "", "date": "",
                      "status": "undesignated", "imo": "", "mmsi": ""}
        index[_nrm(ref)] = key
        return key

    edges = []  # (source, target, relation, pct)
    owners = defaultdict(list)
    for _, r in rels.iterrows():
        s, t = _resolve(r.get("source", "")), _resolve(r.get("target", ""))
        if not s or not t or s == t:
            continue
        rel = _rel(r.get("relation", ""))
        pct = _pct(r.get("ownership_pct", ""))
        edges.append((s, t, rel, pct))
        if rel == "owns":
            owners[t].append((s, pct))

    designated = {k for k, n in nodes.items() if n["status"] == "designated"}
    adj = defaultdict(set)
    inc = defaultdict(list)  # node -> edges touching it
    for e in edges:
        s, t = e[0], e[1]
        adj[s].add(t)
        adj[t].add(s)
        inc[s].append(e)
        inc[t].append(e)

    # ── Aggregate ownership by designated parties (50% rule) ──────────────
    def shares(node, depth=0, path=()):
        out = defaultdict(float)
        if depth > 6:
            return out
        for owner, pct in owners.get(node, []):
            if pct is None or owner in path:
                continue
            f = pct / 100.0
            if owner in designated:
                out[owner] += f
            else:
                for d, v in shares(owner, depth + 1, path + (node,)).items():
                    out[d] += f * v
        return out

    # ── Link distance to designated parties ───────────────────────────────
    hop = {}
    q = deque()
    for d in designated:
        hop[d] = 0
        q.append(d)
    while q:
        cur = q.popleft()
        if hop[cur] >= 2:
            continue
        for nb in adj[cur]:
            if nb not in hop:
                hop[nb] = hop[cur] + 1
                q.append(nb)

    # ── Risk scoring of non-designated nodes ──────────────────────────────
    risk = {}
    for k, n in nodes.items():
        if k in designated or k not in adj:
            continue
        sh = shares(k)
        exposure = min(1.0, sum(sh.values()))
        score, reasons = 0, []
        if exposure >= 0.5:
            score = 100
            reasons.append(f"مملوكة بنسبة {round(exposure * 100)}% لجهات مُدرجة (قاعدة 50%)")
        elif exposure >= 0.25:
            score = 75
            reasons.append(f"ملكية مُدرجة بنسبة {round(exposure * 100)}% (أقل من حد 50%)")
        direct = []
        for s, t, rel, pct in inc[k]:
            other = s if t == k else t
            if other not in designated:
                continue
            if s == k:
                text = f"{n['name']} {_REL_AR.get(rel, rel)} {nodes[other]['name']}"
            else:
                text = f"{nodes[other]['name']} {_REL_AR.get(rel, rel)} {n['name']}"
            if rel == "owns":
                text += f" ({pct:g}%)" if pct is not None else " (نسبة غير محددة)"
                base = 45 if (pct is not None and pct < 25) else 55
            else:
                base = _REL_SCORE.get(rel, 40)
            direct.append((other, base, text))
        if direct:
            score = max(score, max(b for _, b, _ in direct))
            reasons += [t for _, _, t in direct[:3]]
            n_des = len({o for o, _, _ in direct})
            if n_des > 1:
                score = min(100, score + min(10, 3 * (n_des - 1)))
                reasons.append(f"مرتبطة بـ {n_des} جهات مُدرجة")
        elif hop.get(k) == 2:
            score = max(score, 30)
            reasons.append("على بعد خطوتين من جهة مُدرجة")
        if score:
            tier = "حرج" if score >= 90 else "مرتفع" if score >= 70 else "متوسط" if score >= 45 else "منخفض"
            risk[k] = {"score": score, "tier": tier, "reasons": reasons, "exposure": exposure, "shares": sh}

    # ── Analyst overrides from annotations.csv (tag high_risk / cleared) ───────────────────────────
    ann_path = os.path.join(DATA_DIR, "annotations.csv")
    if os.path.exists(ann_path):
        for _, a in pd.read_csv(ann_path, dtype=str).fillna("").iterrows():
            if a.get("ref_file") != "sanctions_entities" or a.get("tag") not in ("high_risk", "cleared"):
                continue
            k = index.get(_nrm(a.get("ref_value", "")))
            if k is None or k in designated:
                continue
            if a["tag"] == "cleared":
                risk.pop(k, None)
            else:
                old = risk.get(k, {})
                note = a.get("note", "")
                risk[k] = {"score": 100, "tier": "حرج",
                           "reasons": ["تقييم المحلل: عالي المخاطر" + (f" — {note}" if note else "")],
                           "exposure": old.get("exposure", 0), "shares": old.get("shares", {})}

    # ── Connected clusters ─────────────────────────────────────────────────
    seen, clusters = set(), []
    for k in nodes:
        if k in seen or k not in adj:
            continue
        comp, dq = [], deque([k])
        seen.add(k)
        while dq:
            c = dq.popleft()
            comp.append(c)
            for nb in adj[c]:
                if nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
        clusters.append(comp)

    def _top(vals, n=3):
        c = defaultdict(int)
        for v in vals:
            if v:
                c[v] += 1
        return "، ".join(x for x, _ in sorted(c.items(), key=lambda kv: -kv[1])[:n])

    cl_rows = []
    for comp in clusters:
        d = [c for c in comp if c in designated]
        u = [c for c in comp if c not in designated]
        if not d or not u:
            continue
        lead = max(d, key=lambda c: len(adj[c]))
        cl_rows.append((len(u), [nodes[lead]["name"], len(comp), len(d), len(u),
                                 _top(nodes[c]["country"] for c in comp), _top(nodes[c]["program"] for c in d),
                                 max((risk[c]["score"] for c in u if c in risk), default=0)], comp))
    cl_rows.sort(key=lambda x: (-x[0], -x[1][1]))

    scored = sorted(risk.items(), key=lambda kv: -kv[1]["score"])
    high = [(k, v) for k, v in scored if v["score"] >= 70]
    rule50 = [(k, v) for k, v in scored if v["exposure"] >= 0.5]
    vessels = [k for k, n in nodes.items() if n["type"] == "vessel"]
    active = [k for k in designated]
    delisted = [k for k, n in nodes.items() if n["status"] == "delisted"]

    w = [_heading("مخاطر الجهات والشبكات"),
         _kpis([("جهات مُدرجة (سارية)", len(active), {"file": "sanctions_entities", "filters": []}), ("رُفع إدراجها", len(delisted)),
                ("جهات غير مدرجة مرتبطة", len(risk)), ("عالية المخاطر (≥70)", len(high)),
                ("مشمولة بقاعدة 50%", len(rule50)), ("شبكات بها جهات غير مدرجة", len(cl_rows)),
                ("سفن في القائمة", len(vessels))])]

    # Insights
    lines = []
    if rule50:
        lines.append(f"{len(rule50)} جهة غير مدرجة مملوكة بنسبة 50% أو أكثر لجهات مُدرجة — تُعدّ محظورة بحكم قاعدة 50% "
                     f"(الأعلى: {nodes[rule50[0][0]]['name']}).")
    if high:
        lines.append(f"{len(high)} جهة غير مدرجة بدرجة مخاطر 70 أو أكثر تستحق مراجعة عناية واجبة معززة.")
    if cl_rows:
        top = cl_rows[0]
        lines.append(f"أكبر شبكة قائمة على «{top[1][0]}»: {top[1][1]} عقدة، منها {top[1][2]} مُدرجة و{top[1][3]} غير مدرجة.")
    hub = defaultdict(int)
    for k in risk:
        if nodes[k]["country"]:
            hub[nodes[k]["country"]] += 1
    if hub:
        c, n = max(hub.items(), key=lambda kv: kv[1])
        lines.append(f"أكثر ولاية قضائية احتضاناً لجهات غير مدرجة مرتبطة بجهات مدرجة: {c} ({n} جهة) — مركز التفاف محتمل.")
    fronts = [e for e in edges if e[2] == "front"]
    if fronts:
        lines.append(f"{len(fronts)} علاقة موصوفة كواجهة (front) لجهات مُدرجة.")
    w.append(_insights(lines, "network"))

    # Designations over time by program
    dated = [(pd.to_datetime(nodes[k]["date"], errors="coerce"), nodes[k]) for k in designated]
    dated = [(d, n) for d, n in dated if pd.notna(d)]
    if dated:
        df = pd.DataFrame({"month": [d.to_period("M").start_time for d, _ in dated],
                           "program": [n["program"] or "غير محدد" for _, n in dated]})
        prog, top_p = _top_with_other(df["program"], 6)
        mo = df.assign(pb=prog).groupby(["month", "pb"]).size().unstack(fill_value=0)
        cols = top_p + (["أخرى"] if "أخرى" in mo.columns else [])
        w.append(_chart("bar", "الإدراجات شهرياً حسب البرنامج", [str(d.date()) for d in mo.index],
                        [{"label": c, "data": [int(v) for v in mo[c].values]} for c in cols], stacked=True,
                        drill={"file": "sanctions_entities", "x": {"col": "designation_date", "bucket": "month"},
                               "series": {"col": "program"}}))
        last = max(d for d, _ in dated)
        recent = sorted([(d, n) for d, n in dated if d > last - pd.Timedelta(days=30)], key=lambda x: x[0], reverse=True)[:15]
        if recent:
            w.append(_table("إدراجات آخر 30 يوماً", ["الجهة", "النوع", "الدولة", "البرنامج", "الجهة المُصدِرة", "التاريخ"],
                            [[n["name"], n["type"], n["country"], n["program"], n["authority"], str(d.date())] for d, n in recent], drill=_ENT_DRILL))

    # Highest-risk non-designated parties
    if scored:
        w.append(_table("الجهات غير المدرجة الأعلى مخاطر", ["الجهة", "النوع", "الدولة", "الدرجة", "المستوى", "الأسباب"],
                        [[nodes[k]["name"], nodes[k]["type"], nodes[k]["country"], v["score"], v["tier"], "؛ ".join(v["reasons"][:3])]
                         for k, v in scored[:20]], drill=_ENT_DRILL))
    if rule50:
        w.append(_table("قاعدة 50% — ملكية مجمّعة لجهات مُدرجة",
                        ["الجهة", "نسبة الملكية المجمّعة", "المالكون المُدرجون"],
                        [[nodes[k]["name"], f"{round(v['exposure'] * 100)}%",
                          "، ".join(f"{nodes[d]['name']} ({round(f * 100)}%)" for d, f in sorted(v["shares"].items(), key=lambda kv: -kv[1]))]
                         for k, v in rule50[:15]], drill=_ENT_DRILL))

    # Evasion hubs
    if hub:
        top_h = sorted(hub.items(), key=lambda kv: -kv[1])[:10]
        w.append(_chart("bar", "ولايات قضائية — جهات غير مدرجة مرتبطة بجهات مدرجة", [c for c, _ in top_h],
                        [{"label": "جهات مرتبطة", "data": [n for _, n in top_h]}], horizontal=True,
                        drill={"file": "sanctions_entities", "x": {"col": "country"}}))

    # Clusters + network picture
    if cl_rows:
        w.append(_table("الشبكات الأكبر", ["الجهة المحورية", "العقد", "مُدرجة", "غير مدرجة", "الدول", "البرامج", "أعلى درجة مخاطر"],
                        [r[1] for r in cl_rows[:12]], drill=_ENT_DRILL))
        comp = cl_rows[0][2]
        if len(comp) > 60:
            comp = sorted(comp, key=lambda c: (c not in designated, -len(adj[c])))[:60]
        cs = set(comp)
        w.append({"type": "network", "id": _wid("network", "net"), "drill": _ENT_DRILL,
                  "title": f"خريطة الشبكة — {cl_rows[0][1][0]}",
                  "nodes": [{"id": c, "label": nodes[c]["name"],
                             "group": "designated" if c in designated else ("risk" if risk.get(c, {}).get("score", 0) >= 70 else "other"),
                             "kind": nodes[c]["type"]} for c in comp],
                  "edges": [{"s": s, "t": t, "label": _REL_AR.get(rel, rel) + (f" {pct:g}%" if pct is not None else "")}
                            for s, t, rel, pct in edges if s in cs and t in cs]})

    # ── AIS screening ──────────────────────────────────────────────────────
    ais = _g("MARINE_DATA", {}).get("vessels", []) if FEATURES["marine"] else []
    if ais:
        d_names = {_nrm(nodes[k]["name"]): k for k in designated}
        h_names = {_nrm(nodes[k]["name"]): k for k, v in high}
        by_id = {}
        for k in designated:
            for fld in ("imo", "mmsi"):
                if nodes[k][fld]:
                    by_id[nodes[k][fld]] = k
        rows, dark = [], 0
        for v in ais:
            reasons, score = [], 0
            vid = by_id.get(str(v.get("imo", ""))) or by_id.get(str(v.get("mmsi", "")))
            if vid:
                reasons.append("السفينة مُدرجة"); score = 100
            for fld in ("beneficial_owner", "operator", "owner"):
                nm = _nrm(v.get(fld, ""))
                if nm and nm in d_names:
                    reasons.append(f"{fld}: جهة مُدرجة ({nodes[d_names[nm]]['name']})"); score = max(score, 95)
                elif nm and nm in h_names:
                    reasons.append(f"{fld}: جهة عالية المخاطر ({nodes[h_names[nm]]['name']})"); score = max(score, 80)
            if not reasons:
                continue
            if v.get("going_dark"):
                reasons.append("AIS مُطفأ"); score = min(100, score + 5); dark += 1
            rows.append((score, [v.get("name", ""), v.get("imo", ""), v.get("flag", ""),
                                 v.get("beneficial_owner") or v.get("operator") or "", "؛ ".join(reasons), score,
                                 f"{v.get('lat', '')}, {v.get('lon', '')}"]))
        rows.sort(key=lambda x: -x[0])
        w.append(_heading("فحص السفن المرصودة (AIS)"))
        w.append(_kpis([("سفن مرصودة", len(ais)), ("مرتبطة بجهات مُدرجة/عالية المخاطر", len(rows)), ("منها بلا إشارة AIS", dark)]))
        if rows:
            w.append(_table("سفن مرتبطة بعقوبات", ["السفينة", "IMO", "العلم", "المالك/المشغّل", "الأسباب", "الدرجة", "الموقع"], [r[1] for r in rows[:25]]))
        else:
            w.append(_note("لم تُطابَق أي سفينة مرصودة مع جهة مُدرجة أو عالية المخاطر في القوائم المحمّلة."))
    elif FEATURES["marine"]:
        w.append(_heading("فحص السفن المرصودة (AIS)"))
        w.append(_note("لا توجد بيانات سفن محمّلة من AIS حالياً — تعذّر الفحص (راجع «جودة البيانات»)."))
    return w


if _PROFILE == "sanctions":
    _head = _build_sanctions_network()
    _tail = ROOM_ANALYTICS["widgets"]
    ROOM_ANALYTICS["widgets"] = _head + ([_heading("نشاط الإجراءات (من ملف الأحداث)")] + _tail if _tail else [])
    print(f"[SANCTIONS-NETWORK] {len(_head)} network widgets")
