# c19_weekly_report.py
# Weekly conflict report with charts
# Auto-extracted from Cell 19

import os
######################################################################
# C8.5 — WEEKLY CONFLICT REPORT WITH CHARTS
#
# THREE-PHASE ARCHITECTURE:
#   Phase 1: "ما وقع" — factual recap from ALL data sources
#   Phase 2: "التوقعات" — H2O model predictions (2 weeks ahead)
#   Gemini: narrative grounded in Cell 10 intelligence patterns
#   Output: standalone HTML report with embedded Chart.js graphs
#
# READS FROM:
#   ESCALATION_ANALYSIS, POLITICAL_ANALYSIS, DIPLOMATIC_INDEX,
#   MARITIME_THREAT, JAMMING_CORRELATION, VIP_INTELLIGENCE,
#   ISR_CUEING_ANALYSIS, CONFLICT_PREDICTION  (all from Cell 10)
#   Middle_East_clean_2026.csv  (ACLED — for H2O model)
######################################################################

import os, json, re, time
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import requests
from pipeline.c13_conflict_forecast import ConflictForecastContext, H2OConflictForecastStage

print("\n" + "="*60)
print("  WEEKLY CONFLICT REPORT — WITH CHARTS")
print("="*60)

# ══════════════════════════════════════════════════════════════
# PART 0 — DETECT BOUNDARIES
# ══════════════════════════════════════════════════════════════
print("\n[0] Detecting boundaries...")

CLEAN_PATH = os.path.join(DATA_DIR, "Middle_East_clean_2026.csv")
if not os.path.exists(CLEAN_PATH):
    # Empty workspace: write a placeholder analytics page instead of failing
    _d = datetime.now().strftime("%Y-%m-%d")
    _ph = f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{WORKSPACE['analytics_name_ar']} — {SYSTEM_NAME_AR}</title>
<style>body{{font-family:'Noto Naskh Arabic',serif;background:#f5f0f2;color:#0f172a;margin:0;padding:40px 16px;text-align:center}}
.hdr{{max-width:760px;margin:0 auto 18px;background:linear-gradient(150deg,#3a0012,#7a0028);color:#fff;border-radius:12px;padding:26px 30px}}
.card{{max-width:760px;margin:0 auto;background:#fff;border:1px solid #f0e0e8;border-radius:10px;padding:40px 24px;line-height:1.9}}
a{{color:#7a0028}}</style></head><body>
<div class="hdr"><div style="font-size:22px;font-weight:700">{WORKSPACE['analytics_name_ar']}</div>
<div style="font-size:12px;opacity:.85">{SYSTEM_NAME_AR} · {_d}</div></div>
<div class="card"><div style="font-size:18px;font-weight:700;color:#7a0028">لا توجد بيانات تحليلية بعد لهذه المساحة</div>
<div style="font-size:14px;color:#8a5060">أضف ملفات البيانات إلى workspaces/{WORKSPACE_SLUG}/data ثم أعد بناء المساحة.</div>
<div style="margin-top:18px"><a href="./">← العودة إلى المساحة</a></div></div></body></html>"""
    with open(os.path.join(OUTPUT_DIR, f"weekly_prediction_{_d}.html"), "w", encoding="utf-8") as _f:
        _f.write(_ph)
    raise ModuleSkipped(f"{CLEAN_PATH} not found — placeholder analytics page written")
df = pd.read_csv(CLEAN_PATH)
df['WEEK'] = pd.to_datetime(df['WEEK'])
ACLED_CUTOFF = df['WEEK'].max()
PREDICT_START = ACLED_CUTOFF + timedelta(days=1)
PREDICT_END   = ACLED_CUTOFF + timedelta(days=14)
print(f"  ACLED → {ACLED_CUTOFF.date()} | Predict: {PREDICT_START.date()} → {PREDICT_END.date()}")

# ══════════════════════════════════════════════════════════════
# PART 1 — COLLECT CELL 10 INTELLIGENCE
# ══════════════════════════════════════════════════════════════
print("\n[1] Collecting intelligence...")

_ea  = globals().get('ESCALATION_ANALYSIS',{})
_pa  = globals().get('POLITICAL_ANALYSIS',{})
_di  = globals().get('DIPLOMATIC_INDEX',{})
_mt  = globals().get('MARITIME_THREAT',{})
_jc  = globals().get('JAMMING_CORRELATION',{})
_vi  = globals().get('VIP_INTELLIGENCE',{})
_isr = globals().get('ISR_CUEING_ANALYSIS',{})
_cp  = globals().get('CONFLICT_PREDICTION',{})

whw = []  # Removed — actor-level data not from authoritative source
cr = _ea.get('country_ranking',[])
cr_txt = "\n".join(f"  {r['country']:<20} {r['events']:>4}" for r in cr[:15])
ms = _pa.get('milestones',[])
ms_txt = "\n".join(f"  D{m['day']:>2} [{m['direction']:>14}] {m['actor'][:30]}: {m['desc'][:150]}" for m in ms[:30])
phases = _pa.get('war_phases',[])
phases_txt = "\n".join(f"  {p['phase']:<20} D{p['start_day']}-D{p['end_day']}" for p in phases)
actors = _di.get('top_actors',[])
actors_txt = "\n".join(f"  {a['actor'][:30]:<30} esc={a['esc']} deesc={a['de_esc']}" for a in actors[:12])
contras = _di.get('contradictions',[])
contras_txt = "\n".join(f"  {c['label']}" for c in contras)
coinc = _vi.get('coincidences',[])
coinc_txt = "\n".join(f"  {'SAME DAY' if c['gap_days']==0 else str(c['gap_days'])+'d'} {c['city']}: {c['actor_1'][:25]} (D{c['day_1']}) + {c['actor_2'][:25]} (D{c['day_2']})" for c in coinc)
corridors = _vi.get('shuttle_corridors',[])
corr_txt = "\n".join(f"  {c['route']:<40} {c['vip']} VIP ({', '.join(c['owners'][:2])})" for c in corridors[:10])
zones = _mt.get('zones',[])
zones_txt = "\n".join(f"  {z['name']:<30} risk={z['risk_score']} [{z['risk_level']}]" for z in zones)
hflags = _mt.get('hormuz_by_flag',[])
hflags_txt = ", ".join(f"{f['flag']}:{f['count']}" for f in hflags[:8])
jam_zones = _jc.get('zone_daily',{})
jam_summary = ""
if jam_zones:
    for zn, zd in jam_zones.items():
        jam_summary += f"  {zn:<12} {sum(1 for d in zd if d.get('avg_pct',0)>1)} days\n"
top_sats = _isr.get('top_recon_sats',[])
sats_txt = "\n".join(f"  {s['name']:<25} {s['cat']:<10} {s['days_over_me']}d" for s in top_sats[:8])

print(f"  Esc: {len(_ea.get('days',[]))} days | Pol: {len(ms)} milestones | Flt: {len(coinc)} coinc | Mar: {_mt.get('vessel_attacks',0)} atk")

# ══════════════════════════════════════════════════════════════
# PART 2 — H2O MODEL (War-period, country-level)
# ══════════════════════════════════════════════════════════════
print("\n[2] H2O model...")
forecast = H2OConflictForecastStage().run(ConflictForecastContext(
    acled_data=df,
    acled_cutoff=ACLED_CUTOFF,
    war_start=pd.Timestamp(WAR_START_STR),
))
pred_base = forecast.predictions
cp_df = forecast.country_risks
TARGET_WEEK = forecast.target_week
model_cp_txt = "\n".join(
    f"  {row.COUNTRY:<25} risk={row.risk_level}"
    for _, row in cp_df.iterrows()
)
print(f"  Training rows: {forecast.training_rows}")
print(f"  Best: {forecast.model_id} | AUC: {forecast.cross_validation_auc:.4f}")

# ══════════════════════════════════════════════════════════════
# PART 3 — GEMINI PROMPT
# ══════════════════════════════════════════════════════════════
print("\n[3] Calling Gemini...")
try:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
except:
    GEMINI_API_KEY = ''

GEMINI_MODEL = 'gemini-3.1-pro-preview'

# ── Build maritime data for Gemini ────────────────────────────
_mp = globals().get("MARITIME_PRESENCE",{})
_sc_data = globals().get("SHIP_CASUALTIES",{})
mp_countries = _mp.get("countries",{})

# Country presence text
cp_lines = []
for code in ["US","GB","CN","RU","IL"]:
    cp = mp_countries.get(code,{})
    if cp and cp.get("total",0) > 0:
        cp_lines.append(f"  {cp.get('country_name_ar','?')}: {cp.get('total',0)} سفينة ({cp.get('tanker',0)} ناقلة، {cp.get('military',0)} عسكري)")
country_presence_txt = "\n".join(cp_lines) if cp_lines else "  لا توجد بيانات"

# Hormuz tankers
_ht = _mp.get("hormuz_traffic",{})
hormuz_tankers_txt = f"{_ht.get('tankers',0)} ({_ht.get('stopped_tankers',0)} متوقفة، {_ht.get('moving_tankers',0)} متحركة — {_ht.get('tanker_flow_pct',0)}% تدفق)"

# Casualties text
cas_list = _sc_data.get("casualties",[]) if isinstance(_sc_data, dict) else []
cas_lines = []
for c in cas_list[:8]:
    cas_lines.append(f"  {c.get('date','')[:10]} — {c.get('vessel_name','?')}: {c.get('type','')} ({c.get('details','')[:80]})")
casualties_txt = f"{len(cas_list)} حادث مؤكد في المنطقة\n" + "\n".join(cas_lines) if cas_lines else "لا توجد حوادث مؤكدة"

# SAT-E text
sat_e_data = _mp.get("sat_e_results",{})
sat_e_list = list(sat_e_data.values()) if isinstance(sat_e_data, dict) else []
sat_e_lines = [f"  {s.get('name','?')} ({s.get('flag','?')}): موقع تقديري {s.get('est_lat','?')}, {s.get('est_lon','?')}" for s in sat_e_list]
sat_e_txt = f"{len(sat_e_list)} سفينة مظلمة تم تتبعها\n" + "\n".join(sat_e_lines) if sat_e_lines else "لا توجد سفن مظلمة"

# Ownership text
own_data = _mp.get("ownership_data",{})
own_lines = []
for mmsi, o in list(own_data.items())[:5]:
    if o.get("beneficial_owner"):
        own_lines.append(f"  {o.get('name','?')} (علم {o.get('flag','?')}) — المالك الحقيقي: {o.get('beneficial_owner','?')} ({o.get('owner_country','?')})")
ownership_txt = f"{_mp.get('convenience_unmasked',0)} سفينة مكشوفة من أعلام ملاءمة\n" + "\n".join(own_lines) if own_lines else "لا توجد بيانات ملكية"

# Sea routes text
_sr = _mp.get("sea_routes",{})
if _sr.get("hormuz_route") and _sr["hormuz_route"].get("distance_nm"):
    h_dist = _sr["hormuz_route"]["distance_nm"]
    c_dist = _sr.get("cape_route",{}).get("distance_nm",0) if _sr.get("cape_route") else 0
    if c_dist and h_dist:
        sea_routes_txt = f"مسار هرمز (دبي→مومباي): {h_dist} ميل بحري\nمسار رأس الرجاء الصالح: {c_dist} ميل بحري (+{c_dist-h_dist:.0f} ميل إضافي، {(c_dist-h_dist)/h_dist*100:.0f}% أطول)"
    else:
        sea_routes_txt = f"مسار هرمز: {h_dist} ميل بحري"
else:
    sea_routes_txt = "لا تتوفر بيانات المسارات"

diversions = _sr.get("diversions",[])
if diversions:
    sea_routes_txt += f"\nسفن محولة عبر رأس الرجاء: {len(diversions)}"


# ── Load analytical context (briefing document) ─────────────
ANALYTICAL_CONTEXT = ""
_ctx_path = os.path.join(DATA_DIR, "analytical-dataset.txt")
if os.path.exists(_ctx_path):
    with open(_ctx_path, "r", encoding="utf-8") as f:
        full_ctx = f.read()
    # Extract: opening + last 3 days + cumulative metrics + expert assessment
    lines = full_ctx.split("\n")
    ctx_parts = []
    # Opening (lines 1-12)
    ctx_parts.append("\n".join(lines[:12]))
    # Find last 3 days + cumulative + expert assessment
    in_recent = False
    for i, line in enumerate(lines):
        # Capture Day 34+
        if "DAY_OF_WAR: 34" in line or "DAY_OF_WAR: 35" in line or "DAY_OF_WAR: 36" in line:
            in_recent = True
        if "CUMULATIVE_METRICS:" in line:
            in_recent = True
        if "EXPERT_ASSESSMENT:" in line:
            in_recent = True
        if in_recent:
            ctx_parts.append(line)
    ANALYTICAL_CONTEXT = "\n".join(ctx_parts)
    print(f"  Analytical context loaded: {len(ANALYTICAL_CONTEXT):,} chars (from {len(full_ctx):,} full)")
else:
    print(f"  ⚠ No analytical context file at {_ctx_path}")

# ── Compute summary stats for prompt ─────────────────────────
total_events = sum(d.get('n',0) for d in _ea.get('days',[]))
total_countries = len(cr) if cr else len(set(e.get('country','') for e in globals().get('WAR_DATA',{}).get('events',[])))
peak_day = _ea.get('peak_day', max((d for d in _ea.get('days',[])), key=lambda x: x.get('n',0), default={'day':0}).get('day',0) if _ea.get('days') else 0)

# ── Build chart summaries + observations for Gemini ──────────

# Escalation chart data summary
esc_days = _ea.get('days',[])
esc_summary_lines = []
for d in esc_days:
    types_str = ", ".join(f"{k}:{v}" for k,v in sorted(d.get('types',{}).items(), key=lambda x:-x[1]) if v>0)
    esc_summary_lines.append(f"  يوم {d['day']}: {d['n']} حدث ({types_str})")
esc_chart_txt = "\n".join(esc_summary_lines[:28])

# Political chart summary
pol_days = _pa.get('days',[])
pol_summary_lines = []
for d in pol_days:
    pol_summary_lines.append(f"  يوم {d['day']}: تصعيد={d.get('esc_count',0)} تهدئة={d.get('de_esc_count',0)} تراكمي={d.get('cumulative',0):.0f}")
pol_chart_txt = "\n".join(pol_summary_lines[:28])

# Jamming chart summary
jam_daily = _jc.get('daily',[])
jam_chart_lines = []
for d in jam_daily:
    pct = d.get('me_avg_pct',0)
    if pct > 0:
        jam_chart_lines.append(f"  {d.get('date','')}: تشويش {pct:.1f}%")
jam_chart_txt = "\n".join(jam_chart_lines)

# Jamming zones summary
jam_zone_lines = []
jam_zones_data = _jc.get('zone_daily',{})
if jam_zones_data:
    for zn, zd in jam_zones_data.items():
        active = sum(1 for d in zd if d.get('avg_pct',0) > 1)
        total = len(zd)
        jam_zone_lines.append(f"  {zn}: {active}/{total} يوم نشط")
jam_zones_txt = "\n".join(jam_zone_lines)

# Coincidences with routes
coinc_lines = []
for c in coinc:
    gap = "نفس اليوم" if c['gap_days']==0 else f"خلال {c['gap_days']} أيام"
    from1 = c.get('from_1','')
    from2 = c.get('from_2','')
    actor1_txt = f"{c['actor_1']} (قادماً من {from1})" if from1 else c['actor_1']
    actor2_txt = f"{c['actor_2']} (قادماً من {from2})" if from2 else c['actor_2']
    coinc_lines.append(
        f"  {actor1_txt} و{actor2_txt} "
        f"تواجدا في {c['city']} {gap} (يوم {c['day_1']} ويوم {c['day_2']})")
coinc_txt = "\n".join(coinc_lines)

# Top corridors
corr_lines = []
for c in corridors[:8]:
    corr_lines.append(f"  {c['route']}: {c['vip']} رحلة ({', '.join(c['owners'][:2])})")
corr_txt = "\n".join(corr_lines)

# Satellites summary
sat_lines = []
for s in top_sats[:8]:
    sat_lines.append(f"  {s['name']} ({s['cat']}): {s['days_over_me']} يوم فوق المنطقة")
sat_txt = "\n".join(sat_lines)

# H2O predictions
pred_lines = []
for _,r in cp_df.iterrows():
    level_ar = {"Very High":"مرتفع جداً","High":"مرتفع","Medium":"متوسط","Low":"منخفض"}.get(str(r.risk_level), str(r.risk_level))
    pred_lines.append(f"  {r.COUNTRY}: {level_ar} ({r.mean_prob:.0%})")
pred_txt = "\n".join(pred_lines)

# Who hit whom summary
whw_txt_brief = ""

prompt = f"""اقرأ السياق التحليلي والبيانات أدناه واكتب قراءة لكل قسم.

═══ السياق التحليلي ═══
{ANALYTICAL_CONTEXT[:12000] if ANALYTICAL_CONTEXT else "لا يوجد سياق إضافي"}

⛔ قواعد:
- اقرأ الأرقام واربطها بالسياق التحليلي عند الحاجة
- لا تكتب "مما يشير إلى" أو "مما يعني" — اذكر الحقيقة مباشرة
- لا تكتب مقدمات — ابدأ بالقراءة مباشرة
- لا تكرر أي معلومة بين الأقسام
- التوقعات هي القسم الأهم — اكتب جملة واحدة واضحة لكل دولة
- يجب أن تبدأ كل قسم بالعنوان المحدد أدناه بالضبط


⛔ تنبيه حاسم عن بيانات الطيران:
- نحن نتتبع تسجيلات الطائرات (مثل HZ-ARE, OD-MRL) وليس الأشخاص
- لا نعلم من كان على متن الطائرة — قد يكون المسؤول أو وفد أو رحلة فارغة
- اكتب "طائرة القيادة السعودية" وليس "الملك سلمان"
- اكتب "طائرة الرئاسة اللبنانية" وليس "الرئيس اللبناني"
- لا تكتب "التقيا" أو "اجتمعا" — اكتب "تواجدت طائرتان في نفس المدينة"
- التقاطع الجغرافي لا يعني لقاءً — قد يكون مصادفة

═══ البيانات ═══

إجمالي: {total_events} حدث | {total_countries} دولة | ذروة: يوم {peak_day}
الأحداث موزعة على {total_countries} دولة
سياسياً: {_pa.get('escalatory_total',0)} تصعيد مقابل {_pa.get('deescalatory_total',0)} تهدئة (تراكمي {_pa.get('final_cumulative',0)})
بحرياً: تعطل هرمز {_mt.get('tanker_disruption_pct',0)}% | {_mt.get('vessel_attacks',0)} هجوم
طيران: {_vi.get('total_vip',0)} VIP | إخلاء يوم 1: +{_vi.get('evacuation_index',0)}%
تهديد: {_cp.get('score',0)}/100

رسم التصعيد:
{esc_chart_txt}

رسم المسار السياسي:
{pol_chart_txt}

رسم التشويش:
{jam_chart_txt}
المناطق:
{jam_zones_txt}

تقاطعات دبلوماسية:
{coinc_txt}

أكثر المسارات نشاطاً:
{corr_txt}

أقمار الاستطلاع:
{sat_txt}

الوضع البحري:
هرمز: {hormuz_tankers_txt}
تعطل: {_mt.get('tanker_disruption_pct',0)}% | هجمات: {_mt.get('vessel_attacks',0)} | حصار: {'مؤكد' if _mt.get('blockade_signal') else 'غير مؤكد'}
التعرض التجاري:
{country_presence_txt}
أضرار مؤكدة:
{casualties_txt}
سفن مظلمة:
{sat_e_txt}
ملكية مكشوفة:
{ownership_txt}
مسارات:
{sea_routes_txt}

توقعات النموذج ({PREDICT_START.date()} إلى {PREDICT_END.date()}):
{pred_txt}

═══ اكتب الأقسام التالية بالعناوين المحددة بالضبط ═══

# قراءة رسم التصعيد
(2-3 جمل عن نمط الضربات اليومية وأنواع الأسلحة)

# قراءة الرسم السياسي
(2-3 جمل عن التوازن بين التصعيد والتهدئة والتراكمي)

# قراءة رسم التشويش
(2-3 جمل عن مناطق التشويش ومدته)

# قراءة التقاطعات والمسارات
(جملة واحدة لكل تقاطع دبلوماسي + أهم المسارات)

# قراءة الوضع البحري
(اقرأ: التعطل، الهجمات، التعرض التجاري، الأضرار بأسماء السفن، السفن المظلمة، المسارات البديلة)

# قراءة الأقمار
(2 جمل عن أقمار الاستطلاع الأكثر نشاطاً)

# التوقعات
(لكل دولة: الاسم + النسبة + جملة واحدة. هذا أهم قسم.)

# السيناريوهات
(ثلاثة سيناريوهات بنسب مئوية. كل سيناريو يستند إلى أرقام محددة.)

# خاتمة
(جملتان فقط: أهم رقمين في التقرير.)"""




print(f"  Prompt: {len(prompt):,} chars")
print(f"  Observations: {len(coinc_lines)} coinc + {len(corr_lines)} corr + {len(jam_zone_lines)} jam")
print(f"  Predictions: {len(pred_lines)} countries")





t0 = time.time()
narrative = ""
print("  Streaming response", end="", flush=True)
gemini_url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:streamGenerateContent"
    f"?alt=sse&key={GEMINI_API_KEY}"
)
with requests.post(gemini_url,
    headers={"Content-Type":"application/json"},
    json={"contents":[{"role":"user","parts":[{"text":prompt}]}],
          # gemini-3.1-pro-preview always "thinks" — cap its budget so the
          # visible answer isn't starved of tokens
          "generationConfig":{"maxOutputTokens":24000,"thinkingConfig":{"thinkingBudget":4000}}},
    timeout=600, stream=True) as resp:
    resp.raise_for_status()
    # NOTE: iterate raw bytes, not iter_lines(decode_unicode=True) — the
    # latter can split multi-byte UTF-8 (Arabic) chars across chunk
    # boundaries and corrupt the JSON payload.
    for raw_line in resp.iter_lines():
        if not raw_line:
            continue
        chunk = raw_line.decode("utf-8", errors="replace")
        if not chunk.startswith("data: "):
            continue
        payload = chunk[6:]
        if payload == "[DONE]":
            break
        try:
            evt = json.loads(payload)
        except json.JSONDecodeError:
            continue
        candidates = evt.get("candidates",[])
        if not candidates:
            continue
        for part in candidates[0].get("content",{}).get("parts",[]):
            txt = part.get("text","")
            narrative += txt
            if len(narrative) % 500 < len(txt):
                print(".", end="", flush=True)
narrative = narrative.strip()
elapsed = round(time.time()-t0,1)
print(f"\n  Done {elapsed}s | {len(narrative):,} chars")
if not narrative:
    raise RuntimeError("Empty response from Gemini")

# ══════════════════════════════════════════════════════════════
# PART 4 — BUILD HTML WITH CHARTS
# ══════════════════════════════════════════════════════════════
print("\n[4] Building report...")
date_iso = datetime.now().strftime("%Y-%m-%d")
# Country ranking data
cr_json = json.dumps(cr[:15], ensure_ascii=False, default=str)

# Hormuz flags data
hflags_json = json.dumps(hflags[:10], ensure_ascii=False, default=str)

# Country presence data
cp_data = []
_mp_c = globals().get("MARITIME_PRESENCE",{}).get("countries",{})
for code in ["US","GB","CN","RU","IL"]:
    cp = _mp_c.get(code,{})
    if cp:
        cp_data.append({"code":code,"name_ar":cp.get("country_name_ar",""),"total":cp.get("total",0),"military":cp.get("military",0),"tanker":cp.get("tanker",0),"cargo":cp.get("cargo",0),"other":cp.get("other",0)})
cp_json = json.dumps(cp_data, ensure_ascii=False, default=str)

# Threat score
threat_score = round(_cp.get('score',0),1)
threat_level = _cp.get('level','?')

esc_days_json = json.dumps(_ea.get('days',[]), ensure_ascii=False, default=str)
pol_days_json = json.dumps(_pa.get('days',[]), ensure_ascii=False, default=str)
jam_daily_json = json.dumps(_jc.get('daily',[]), ensure_ascii=False, default=str)
jam_corr_json = json.dumps(_jc.get('correlation_days',[]), ensure_ascii=False, default=str)
isr_daily_json = json.dumps(_isr.get('daily_overflights',[]), ensure_ascii=False, default=str)
pred_map_json = json.dumps([{"lat":float(r.grid_lat),"lon":float(r.grid_lon),"prob":round(float(r.prob_conflict),3),"country":r.COUNTRY,"admin":str(r.ADMIN1),"new_em":bool(r.is_new_emergence)} for _,r in pred_base.iterrows() if float(r.prob_conflict)>0.15], ensure_ascii=False)

def parse_narrative(text):
    out=[]
    for line in text.split("\n"):
        t=line.strip()
        if not t: out.append('<div style="height:8px"></div>'); continue
        if re.match(r"^#{1,3} ",t):
            clean=re.sub(r"^#{1,3} *","",t)
            out.append(f'<h2 class="rpt-h2">{clean}</h2>'); continue
        if t.startswith("**") and t.endswith("**") and len(t)>4:
            out.append(f'<h3 class="rpt-h3">{t[2:-2]}</h3>'); continue
        out.append(f'<p class="rpt-p">{t}</p>')
    return "\n".join(out)

# narrative parsed by parse_sections()
def rc(risk):
    return {"Very High":"#dc2626","High":"#d97706","Medium":"#c0406a","Low":"#16a34a"}.get(str(risk),"#888")

risk_ar = {"Very High":"مرتفع جداً","High":"مرتفع","Medium":"متوسط","Low":"منخفض"}

model_rows = "".join(f'<tr><td style="font-weight:600;padding:8px 10px;border-bottom:1px solid #f0e0e8;">{r.COUNTRY}</td><td style="text-align:center;padding:8px;border-bottom:1px solid #f0e0e8;"><span style="background:{rc(r.risk_level)}18;color:{rc(r.risk_level)};padding:3px 10px;border-radius:8px;font-size:11px;font-weight:700;">{risk_ar.get(str(r.risk_level),str(r.risk_level))}</span></td></tr>' for _,r in cp_df.iterrows())
# whw_rows removed
coinc_rows = "".join(f'<div style="padding:8px 10px;border-bottom:1px solid #f0e0e8;direction:rtl;"><span style="background:{"#dc262618" if c["gap_days"]==0 else "#d9770618"};color:{"#dc2626" if c["gap_days"]==0 else "#d97706"};padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{"نفس اليوم" if c["gap_days"]==0 else str(c["gap_days"])+" يوم"}</span> <strong>{c["city"]}</strong><br><span style="font-size:12px;">D{c["day_1"]}: {c["actor_1"]} | D{c["day_2"]}: {c["actor_2"]}</span></div>' for c in coinc)
corr_rows = "".join(f'<tr><td style="padding:5px 8px;border-bottom:1px solid #f0e0e8;font-size:12px;">{c["route"]}</td><td style="padding:5px 8px;border-bottom:1px solid #f0e0e8;font-weight:700;text-align:center;">{c["vip"]}</td><td style="padding:5px 8px;border-bottom:1px solid #f0e0e8;font-size:11px;">{", ".join(c["owners"][:2])}</td></tr>' for c in corridors[:10])
sats_rows = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #f0e0e8;font-family:monospace;font-size:11px;">{s["name"]}</td><td style="padding:4px 8px;border-bottom:1px solid #f0e0e8;">{s["cat"]}</td><td style="padding:4px 8px;border-bottom:1px solid #f0e0e8;font-weight:700;text-align:center;">{s["days_over_me"]}</td></tr>' for s in top_sats[:10])
ms_rows = "".join(f'<div style="padding:6px 10px;border-right:3px solid {"#dc2626" if m["direction"]=="Escalatory" else "#16a34a" if m["direction"]=="De-escalatory" else "#888"};margin-bottom:4px;background:#faf5f7;border-radius:0 6px 6px 0;direction:rtl;"><span style="font-family:monospace;font-size:10px;color:#7a0028;">D{m["day"]} {m["date"]}</span> <span style="font-size:10px;font-weight:700;color:#7a0028;">{m["actor"][:35]}</span><br><span style="font-size:11px;color:#333;line-height:1.5;">{m["desc"][:200]}</span></div>' for m in ms[:25])

phase_ar = {"Pre-War":"ما قبل الحرب","Shock and Awe":"الصدمة والترويع","Early Attrition":"استنزاف مبكر","Deep Attrition":"استنزاف عميق","Collapse":"انهيار","Stabilization":"استقرار","Active War":"حرب نشطة"}
current_phase = phase_ar.get(phases[-1]['phase'], phases[-1]['phase']) if phases else "?" 
total_events = sum(d['n'] for d in _ea.get('days',[]))
total_countries = len(cr)



# ══════════════════════════════════════════════════════════════
# BUILD REPORT — data-driven explanations + Gemini findings
# ══════════════════════════════════════════════════════════════

# ── Auto-generate chart explanations from data ───────────────
total_events = sum(d['n'] for d in _ea.get('days',[]))
total_countries = len(cr)
phase_ar = {"Pre-War":"ما قبل الحرب","Shock and Awe":"الصدمة والترويع","Early Attrition":"استنزاف مبكر","Deep Attrition":"استنزاف عميق","Collapse":"انهيار","Stabilization":"استقرار","Active War":"حرب نشطة"}
current_phase = phase_ar.get(phases[-1]['phase'], phases[-1]['phase']) if phases else "?" 
peak_day = _ea.get('peak_day',0)

# Escalation explanation
top_whw = {}
trend_ar = "تراجعي" if "de-escalat" in str(_ea.get('trend','')) else "تصاعدي" if "escalat" in str(_ea.get('trend','')) else "مستقر"
esc_explain = (
    f"الرسم البياني يوضح توزيع الضربات اليومية حسب نوع السلاح منذ بداية الحرب. "
    f"بلغت الذروة في اليوم {peak_day}، ثم اتخذ الاتجاه العام منحنى {trend_ar}. "
    f"إجمالي الأحداث: {total_events} في {total_countries} دولة. "
    f"مصدر البيانات: ACLED — أحداث حركية أسبوعية."
)

# Political explanation
pol_trend_ar = "تصاعدي صافٍ" if "escalat" in str(_pa.get('trend','')) else "تهدئة" if "de-escalat" in str(_pa.get('trend','')) else "مختلط"
pol_explain = (
    f"الرسم البياني يوضح التوازن بين الأحداث التصعيدية (بالأحمر) والتهدئة (بالأخضر) يومياً، "
    f"مع خط الضغط التراكمي. "
    f"الاتجاه السياسي: {pol_trend_ar} بتراكم {_pa.get('final_cumulative',0)}. "
    f"{_pa.get('escalatory_total',0)} حدث تصعيدي مقابل {_pa.get('deescalatory_total',0)} تهدئة."
)

# Jamming explanation
jam_explain = (
    f"الرسم الأول يوضح شدة التشويش اليومية. الرسم الثاني يقارن بين التشويش والضربات العسكرية. "
    f"تعطل الناقلات في هرمز: {_mt.get('tanker_disruption_pct',0)}%. "
    f"هجمات بحرية: {_mt.get('vessel_attacks',0)}. "
    f"إشارة حصار: {'مؤكدة' if _mt.get('blockade_signal') else 'غير مؤكدة'}."
)


# ── Split Gemini narrative into sections by header ────────────
def _fmt_block(text):
    """Format a block of text as HTML."""
    html_lines = []
    for line in text.split("\n"):
        t = line.strip()
        if not t or t == "---" or t.startswith("# "): continue
        if t.startswith("## ") or t.startswith("### "):
            title = t.lstrip("#").strip()
            html_lines.append(f'<div style="font-size:14px;font-weight:800;color:#3a0012;margin:14px 0 6px;padding:8px 12px;background:#faf5f7;border-radius:6px;border-right:4px solid #c0406a;">{title}</div>')
        elif t.startswith("**") and t.endswith("**") and len(t)>4:
            html_lines.append(f'<div style="font-size:13px;font-weight:700;color:#c0406a;margin:8px 0 3px;">{t[2:-2]}</div>')
        elif t.startswith("**") and "**" in t[2:]:
            # Bold label at start: **Israel** 100%: ...
            bold_end = t.index("**", 2)
            bold_part = t[2:bold_end]
            rest = t[bold_end+2:].strip().lstrip(":").strip()
            html_lines.append(f'<p style="margin:4px 0;font-size:13.5px;line-height:1.85;"><strong style="color:#7a0028;">{bold_part}</strong> {rest}</p>')
        elif t.startswith("- "):
            html_lines.append(f'<div style="padding:2px 0 2px 14px;font-size:13px;line-height:1.8;color:#1a1a2e;">{t[2:]}</div>')
        else:
            html_lines.append(f'<p style="margin:4px 0;font-size:13.5px;line-height:1.85;color:#1a1a2e;text-align:justify;">{t}</p>')
    return "\n".join(html_lines)

def split_narrative(text):
    """Split Gemini's narrative by # headers into a dict."""
    sections = {}
    current_key = "_intro"
    current_lines = []
    for line in text.split("\n"):
        t = line.strip()
        if t.startswith("# "):
            if current_lines:
                sections[current_key] = "\n".join(current_lines)
            current_key = t[2:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections[current_key] = "\n".join(current_lines)
    return sections

nsecs = split_narrative(narrative)
print(f"  Gemini sections: {list(nsecs.keys())}")

def R(*keys):
    """Get a formatted section card by partial key match (multiple keys, first match wins)."""
    for k, v in nsecs.items():
        for key in keys:
            if key in k:
                formatted = _fmt_block(v)
                if formatted.strip():
                    return f'<div class="card" style="line-height:1.85;direction:rtl;border-right:4px solid #c0406a;margin-top:8px;">{formatted}</div>'
    return ""

# Build individual section HTMLs
reading_esc = R("التصعيد","رسم التصعيد","escalation")
reading_whw = ""
reading_pol = R("السياسي","الرسم السياسي","political")
reading_jam = R("التشويش","رسم التشويش","jamming")
reading_coinc = R("التقاطعات","المسارات","coincidence","routes")
reading_maritime = R("البحري","الوضع البحري","maritime","هرمز")
reading_predictions = R("التوقعات","predictions","النموذج")
reading_scenarios = R("السيناريو","سيناريوهات","scenarios")
reading_conclusion = R("خاتمة","conclusion")
reading_sat = R("الأقمار","أقمار","satellite","ISR")

# Fallback: everything that wasn't matched
matched_keys = set()
for search in ["التصعيد","ضرب","السياسي","التشويش","التقاطعات","المسارات","البحري","الأقمار","التوقعات","السيناريو","خاتمة"]:
    for k in nsecs:
        if search in k:
            matched_keys.add(k)
remaining_html = "\n".join(_fmt_block(v) for k,v in nsecs.items() if k not in matched_keys and k != "_intro" and v.strip())

# Full findings for any unmatched content
findings_html = remaining_html if remaining_html.strip() else ""

print(f"  Matched sections: {len(matched_keys)}")
print(f"  Remaining: {len(remaining_html)} chars")

# ── Build table rows ─────────────────────────────────────────
def rc(risk):
    return {"Very High":"#dc2626","High":"#d97706","Medium":"#c0406a","Low":"#16a34a"}.get(str(risk),"#888")

risk_ar = {"Very High":"مرتفع جداً","High":"مرتفع","Medium":"متوسط","Low":"منخفض"}

model_rows = "".join(f'<tr><td style="font-weight:600;padding:8px 10px;border-bottom:1px solid #f0e0e8;">{r.COUNTRY}</td><td style="text-align:center;padding:8px;border-bottom:1px solid #f0e0e8;"><span style="background:{rc(r.risk_level)}18;color:{rc(r.risk_level)};padding:3px 10px;border-radius:8px;font-size:11px;font-weight:700;">{risk_ar.get(str(r.risk_level),str(r.risk_level))}</span></td></tr>' for _,r in cp_df.iterrows())

# whw_rows removed

coinc_rows = "".join(
    f'<div style="padding:10px 12px;border-bottom:1px solid #f0e0e8;direction:rtl;">'
    f'<div style="margin-bottom:4px;"><span style="background:{"#dc262618" if c["gap_days"]==0 else "#d9770618"};color:{"#dc2626" if c["gap_days"]==0 else "#d97706"};padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">{"نفس اليوم" if c["gap_days"]==0 else str(c["gap_days"])+" يوم"}</span> <strong style="font-size:14px;"> {c["city"]}</strong></div>'
    f'<div style="font-size:12px;color:#333;padding:2px 0;">يوم {c["day_1"]}: <strong>{c["actor_1"]}</strong>{" (من "+c["from_1"]+")" if c.get("from_1") else ""}</div>'
    f'<div style="font-size:12px;color:#333;padding:2px 0;">يوم {c["day_2"]}: <strong>{c["actor_2"]}</strong>{" (من "+c["from_2"]+")" if c.get("from_2") else ""}</div>'
    f'</div>' for c in coinc)

corr_rows = "".join(f'<tr><td style="padding:5px 8px;border-bottom:1px solid #f0e0e8;font-size:12px;">{c["route"]}</td><td style="padding:5px 8px;border-bottom:1px solid #f0e0e8;font-weight:700;text-align:center;">{c["vip"]}</td><td style="padding:5px 8px;border-bottom:1px solid #f0e0e8;font-size:11px;">{", ".join(c["owners"][:2])}</td></tr>' for c in corridors[:10])

sats_rows = "".join(f'<tr><td style="padding:4px 8px;border-bottom:1px solid #f0e0e8;font-family:monospace;font-size:11px;">{s["name"]}</td><td style="padding:4px 8px;border-bottom:1px solid #f0e0e8;">{"استطلاع" if s["cat"]=="spy" else "عسكري"}</td><td style="padding:4px 8px;border-bottom:1px solid #f0e0e8;font-weight:700;text-align:center;">{s["days_over_me"]}</td></tr>' for s in top_sats[:10])

# ── Serialize chart data ─────────────────────────────────────
# Country ranking data
cr_json = json.dumps(cr[:15], ensure_ascii=False, default=str)

# Hormuz flags data
hflags_json = json.dumps(hflags[:10], ensure_ascii=False, default=str)

# Country presence data
cp_data = []
_mp_c = globals().get("MARITIME_PRESENCE",{}).get("countries",{})
for code in ["US","GB","CN","RU","IL"]:
    cp = _mp_c.get(code,{})
    if cp:
        cp_data.append({"code":code,"name_ar":cp.get("country_name_ar",""),"total":cp.get("total",0),"military":cp.get("military",0),"tanker":cp.get("tanker",0),"cargo":cp.get("cargo",0),"other":cp.get("other",0)})
cp_json = json.dumps(cp_data, ensure_ascii=False, default=str)

# Threat score

esc_days_json = json.dumps(_ea.get('days',[]), ensure_ascii=False, default=str)
pol_days_json = json.dumps(_pa.get('days',[]), ensure_ascii=False, default=str)
jam_daily_json = json.dumps(_jc.get('daily',[]), ensure_ascii=False, default=str)
jam_corr_json = json.dumps(_jc.get('correlation_days',[]), ensure_ascii=False, default=str)
pred_map_json = json.dumps([{"lat":float(r.grid_lat),"lon":float(r.grid_lon),"prob":round(float(r.prob_conflict),3),"country":r.COUNTRY,"admin":str(r.ADMIN1),"new_em":bool(r.is_new_emergence)} for _,r in pred_base.iterrows() if float(r.prob_conflict)>0.15], ensure_ascii=False)

HTML = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{WORKSPACE['analytics_name_ar']} — {date_iso}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Noto Naskh Arabic",serif;background:#f5f0f2;color:#0f172a;direction:rtl;font-size:15px;line-height:1.85}}
.pg{{max-width:1100px;margin:0 auto;padding:28px 24px 60px}}
.hdr{{background:linear-gradient(150deg,#3a0012,#7a0028);color:#fff;border-radius:12px;padding:26px 30px;margin-bottom:18px}}
.hdr-title{{font-size:22px;font-weight:700;margin-bottom:4px}}
.hdr-sub{{font-size:12px;color:rgba(255,255,255,.85)}}
.hdr-strip{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;background:rgba(0,0,0,.2);border-radius:8px;padding:12px;margin-top:14px;text-align:center}}
.hdr-strip .v{{font-family:"IBM Plex Mono",monospace;font-size:18px;font-weight:700}}
.hdr-strip .l{{font-size:9px;color:rgba(255,255,255,.85);margin-top:2px}}
.card{{background:#fff;border-radius:10px;padding:20px 22px;margin-bottom:14px;border:1px solid #f0e0e8}}
.sec{{font-size:17px;font-weight:800;color:#3a0012;margin:24px 0 12px;padding-right:14px;border-right:5px solid #c0406a}}
.expl{{font-size:13px;color:#444;line-height:1.7;padding:10px 14px;background:#faf5f7;border-radius:8px;margin-bottom:12px;direction:rtl}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.chart-wrap{{position:relative;height:240px}}
.mini-tbl{{width:100%;border-collapse:collapse;font-size:12px}}
.mini-tbl th{{text-align:right;padding:6px 8px;font-size:10px;font-weight:700;color:#7a0028;background:#faf5f7;border-bottom:2px solid #f0e0e8}}
.mini-tbl td{{padding:5px 8px;border-bottom:1px solid #f0e0e8}}
.ft{{margin-top:28px;padding:10px 14px;border-top:1px solid #f0e0e8;display:flex;justify-content:space-between;font-size:10px;color:#999}}
.pbtn{{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);color:#fff;padding:7px 16px;border-radius:6px;cursor:pointer;font-size:11px;font-weight:600;font-family:inherit}}
@media print{{body{{background:#fff}}.pbtn{{display:none}}}}
@media(max-width:800px){{.g2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="pg">

<div class="hdr">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div><div class="hdr-title">{WORKSPACE['analytics_name_ar']}</div>
    <div class="hdr-sub">{SYSTEM_NAME_AR} · {date_iso} · المرحلة: {"حرب نشطة" if "Active" in str(current_phase) else "استقرار" if "Stabil" in str(current_phase) else "انهيار" if "Collaps" in str(current_phase) else "استنزاف" if "Attrition" in str(current_phase) else "صدمة" if "Shock" in str(current_phase) else current_phase}</div></div>
    <div><a class="pbtn" href="./" style="text-decoration:none;display:inline-block">← المساحة</a>
    <button class="pbtn" onclick="window.print()">طباعة / PDF</button></div>
  </div>
  <div class="hdr-strip">
    <div><div class="v">{total_events}</div><div class="l">إجمالي الأحداث</div></div>
    <div><div class="v">{total_countries}</div><div class="l">دولة منخرطة</div></div>
    <div><div class="v">{_vi.get('total_vip',0)}</div><div class="l">رحلة VIP</div></div>
    <div><div class="v">{_mt.get('vessel_attacks',0)}</div><div class="l">هجوم بحري</div></div>
    <div><div class="v">{round(_cp.get('score',0))}/100</div><div class="l">درجة التهديد</div></div>
  </div>
</div>


<!-- 1. ESCALATION -->
<div class="sec">مسار التصعيد العسكري</div>
<div class="card"><div class="chart-wrap"><canvas id="ch-esc"></canvas></div></div>
<div class="expl">{esc_explain}</div>
{reading_esc}
<div class="card"><div style="font-size:12px;font-weight:700;color:#7a0028;margin-bottom:8px;">مستوى الخطر المتوقع — الأسبوعان القادمان</div>
    <table class="mini-tbl"><thead><tr><th>الدولة</th><th>المستوى</th></tr></thead><tbody>{model_rows}</tbody></table></div>

<!-- Country Ranking -->
<div class="card" style="height:220px;position:relative;"><canvas id="ch-cr"></canvas></div>

<!-- Hormuz Flags -->
<div class="g2">
  <div class="card" style="height:200px;position:relative;"><canvas id="ch-hflags"></canvas></div>
  <div class="card" style="height:200px;position:relative;"><canvas id="ch-cp"></canvas></div>
</div>

<!-- Threat Gauge -->
<div class="card" style="text-align:center;padding:20px;">
  <div style="font-size:48px;font-weight:800;font-family:monospace;color:{('#dc2626' if threat_score>=70 else '#d97706' if threat_score>=50 else '#16a34a')};">{threat_score}<span style="font-size:20px;color:#999;">/100</span></div>
  <div style="font-size:13px;color:#666;margin-top:4px;">درجة التهديد العام</div>
  <div style="margin-top:8px;height:8px;background:#f0e0e8;border-radius:4px;overflow:hidden;">
    <div style="width:{threat_score}%;height:100%;background:{('#dc2626' if threat_score>=70 else '#d97706' if threat_score>=50 else '#16a34a')};border-radius:4px;"></div>
  </div>
</div>

<!-- 2. POLITICAL -->
<div class="sec">المسار السياسي</div>
<div class="card"><div class="chart-wrap"><canvas id="ch-pol"></canvas></div></div>
<div class="expl">{pol_explain}</div>
{reading_pol}

<!-- 3. JAMMING + MARITIME -->
<div class="sec">التشويش الإلكتروني والوضع البحري</div>
<div class="g2">
  <div class="card"><div class="chart-wrap"><canvas id="ch-jam"></canvas></div></div>
  <div class="card"><div class="chart-wrap"><canvas id="ch-jam-corr"></canvas></div></div>
</div>
<div class="expl">{jam_explain}</div>
{reading_jam}

<!-- 4. FLIGHTS -->
<div class="sec">حركة كبار المسؤولين</div>
<div class="g2">
  <div class="card"><div style="font-size:12px;font-weight:700;color:#7a0028;margin-bottom:8px;">تقاطعات دبلوماسية — قادة في نفس المدينة</div>
    {coinc_rows if coinc_rows else '<div style="color:#999;font-size:12px;">لا توجد</div>'}</div>
  <div class="card"><div style="font-size:12px;font-weight:700;color:#7a0028;margin-bottom:8px;">أكثر المسارات الدبلوماسية نشاطاً</div>
    <table class="mini-tbl"><thead><tr><th>المسار</th><th>VIP</th><th>الشخصيات</th></tr></thead><tbody>{corr_rows}</tbody></table></div>
</div>

<!-- 5. MARITIME -->
{reading_coinc}

<div class="sec">الوضع البحري</div>
<div class="g2">
  <div class="card">
    <div style="text-align:center;padding:8px;">
      <div style="font-family:monospace;font-size:28px;font-weight:800;color:#cc0020;">{_mt.get('tanker_disruption_pct',0)}%</div>
      <div style="font-size:10px;color:#666;">تعطل الناقلات في هرمز</div>
    </div>
  </div>
  <div class="card">
    <div style="text-align:center;padding:8px;">
      <div style="font-family:monospace;font-size:28px;font-weight:800;color:#d97706;">{_ht.get('tanker_flow_pct',0)}%</div>
      <div style="font-size:10px;color:#666;">تدفق الناقلات (متحركة)</div>
    </div>
  </div>
</div>
{reading_maritime}
<div class="expl">هرمز: {_ht.get('tankers',0)} ناقلة ({_ht.get('stopped_tankers',0)} متوقفة، {_ht.get('moving_tankers',0)} متحركة). هجمات بحرية: {_mt.get('vessel_attacks',0)}. أضرار مؤكدة: {len(cas_list)} حادث. سفن مظلمة: {len(sat_e_list)} تم تتبعها بالقمر.</div>

<!-- 6. SATELLITES -->
<div class="sec">أقمار الاستطلاع فوق المنطقة</div>
<div class="card">
  <table class="mini-tbl"><thead><tr><th>القمر</th><th>النوع</th><th>أيام فوق المنطقة</th></tr></thead><tbody>{sats_rows}</tbody></table>
</div>

<!-- 6. PREDICTIONS MAP -->
{reading_sat}

<div class="sec">خريطة التوقعات — الأسبوعان القادمان</div>
<div class="card"><div id="pred-map" style="height:420px;border-radius:8px;overflow:hidden;border:1px solid #e0c8d0;"></div></div>

<!-- PREDICTIONS + SCENARIOS + CONCLUSION -->

<!-- PREDICTIONS -->
<div class="sec" style="border-right-color:#b80038;">التوقعات — قراءة النموذج التنبؤي</div>
{reading_predictions}

<!-- SCENARIOS -->
<div class="sec">السيناريوهات</div>
{reading_scenarios}

<!-- CONCLUSION -->
<div class="sec">خاتمة</div>
{reading_conclusion}

{findings_html}

<div class="ft">
  <span>{SYSTEM_NAME_AR} · {WORKSPACE_NAME_AR} · {date_iso}</span>
  <span style="font-family:monospace">ACLED > {ACLED_CUTOFF.date()}</span>
</div>
</div>

<script>
(function(){{
  var $=function(id){{return document.getElementById(id);}};
  var esc={esc_days_json};
  var types=['airstrike','missile_strike','drone_strike','naval_attack','ground_operation','assassination','interception'];
  var tL=['غارة','صاروخ','مسيّرة','بحري','بري','اغتيال','اعتراض'];
  var tC=['rgba(220,50,50,.8)','rgba(255,120,0,.8)','rgba(255,200,0,.8)','rgba(0,120,200,.8)','rgba(80,160,80,.8)','rgba(180,0,180,.8)','rgba(100,100,100,.5)'];
  new Chart($('ch-esc'),{{type:'bar',data:{{labels:esc.map(d=>'D'+d.day),datasets:types.map((t,i)=>({{label:tL[i],data:esc.map(d=>(d.types||{{}})[t]||0),backgroundColor:tC[i],stack:'s',borderWidth:0}}))}},options:{{responsive:true,maintainAspectRatio:false,animation:false,plugins:{{legend:{{labels:{{font:{{size:9}},boxWidth:10}}}}}},scales:{{x:{{stacked:true,ticks:{{font:{{size:7}}}},grid:{{display:false}}}},y:{{stacked:true,ticks:{{font:{{size:9}}}},grid:{{color:'rgba(0,0,0,.04)'}}}}}}}}}});

  var pol={pol_days_json};
  new Chart($('ch-pol'),{{type:'bar',data:{{labels:pol.map(d=>'D'+d.day),datasets:[
    {{label:'تصاعدي',data:pol.map(d=>d.esc_count),backgroundColor:'rgba(220,0,30,.7)',stack:'p'}},
    {{label:'تهدئة',data:pol.map(d=>-d.de_esc_count),backgroundColor:'rgba(40,120,64,.7)',stack:'p'}},
    {{label:'تراكمي',data:pol.map(d=>d.cumulative),type:'line',borderColor:'#b80038',borderWidth:2,pointRadius:1,fill:false,yAxisID:'y1'}}
  ]}},options:{{responsive:true,maintainAspectRatio:false,animation:false,plugins:{{legend:{{labels:{{font:{{size:9}},boxWidth:10}}}}}},scales:{{x:{{stacked:true,ticks:{{font:{{size:7}}}},grid:{{display:false}}}},y:{{stacked:true,ticks:{{font:{{size:9}}}},grid:{{color:'rgba(0,0,0,.04)'}}}},y1:{{type:'linear',position:'left',ticks:{{font:{{size:9}}}},grid:{{display:false}}}}}}}}}});

  var jam={jam_daily_json};
  new Chart($('ch-jam'),{{type:'bar',data:{{labels:jam.map(d=>(d.date||'').slice(5)),datasets:[{{label:'GPS %',data:jam.map(d=>d.me_avg_pct||0),backgroundColor:jam.map(d=>(d.me_avg_pct||0)>10?'rgba(255,17,68,.8)':'rgba(255,200,68,.7)'),borderWidth:0}}]}},options:{{responsive:true,maintainAspectRatio:false,animation:false,plugins:{{legend:{{display:false}},title:{{display:true,text:'شدة التشويش',font:{{size:11}},color:'#7a0028'}}}},scales:{{x:{{ticks:{{font:{{size:7}}}},grid:{{display:false}}}},y:{{beginAtZero:true,ticks:{{font:{{size:9}}}},grid:{{color:'rgba(0,0,0,.04)'}}}}}}}}}});

  var jc={jam_corr_json};
  new Chart($('ch-jam-corr'),{{type:'bar',data:{{labels:jc.map(d=>'D'+d.day),datasets:[
    {{label:'أحداث',data:jc.map(d=>d.events),backgroundColor:'rgba(184,0,56,.5)',borderWidth:0}},
    {{label:'تشويش %',data:jc.map(d=>d.jam_pct),type:'line',borderColor:'#ff8800',borderWidth:2,pointRadius:1,fill:false,yAxisID:'y1'}}
  ]}},options:{{responsive:true,maintainAspectRatio:false,animation:false,plugins:{{legend:{{labels:{{font:{{size:9}},boxWidth:10}}}},title:{{display:true,text:'تشويش مقابل ضربات',font:{{size:11}},color:'#7a0028'}}}},scales:{{x:{{ticks:{{font:{{size:7}}}},grid:{{display:false}}}},y:{{beginAtZero:true,ticks:{{font:{{size:9}}}},grid:{{color:'rgba(0,0,0,.04)'}}}},y1:{{type:'linear',position:'left',beginAtZero:true,ticks:{{font:{{size:9}}}},grid:{{display:false}}}}}}}}}});
  // Country ranking chart
  var cr={cr_json};
  if(cr.length){{
    new Chart($('ch-cr'),{{type:'bar',data:{{labels:cr.map(c=>c.country),datasets:[{{label:'أحداث',data:cr.map(c=>c.total),backgroundColor:cr.map(c=>c.total>50?'rgba(220,0,30,.8)':c.total>10?'rgba(217,119,6,.7)':'rgba(22,163,74,.6)'),borderWidth:0}}]}},options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:false,plugins:{{legend:{{display:false}},title:{{display:true,text:'الأحداث حسب الدولة',font:{{size:11}},color:'#7a0028'}}}},scales:{{x:{{beginAtZero:true,ticks:{{font:{{size:9}}}},grid:{{color:'rgba(0,0,0,.04)'}}}},y:{{ticks:{{font:{{size:9}}}},grid:{{display:false}}}}}}}}}});
  }}

  // Hormuz flags chart
  var hf={hflags_json};
  if(hf.length){{
    new Chart($('ch-hflags'),{{type:'doughnut',data:{{labels:hf.map(f=>f.flag),datasets:[{{data:hf.map(f=>f.count),backgroundColor:['#b80038','#d97706','#16a34a','#0088cc','#8b5cf6','#ec4899','#f59e0b','#6366f1','#84cc16','#06b6d4']}}]}},options:{{responsive:true,maintainAspectRatio:false,animation:false,plugins:{{legend:{{position:'right',labels:{{font:{{size:9}},boxWidth:10}}}},title:{{display:true,text:'أعلام السفن في هرمز',font:{{size:11}},color:'#7a0028'}}}}}}}});
  }}

  // Country presence chart
  var cp={cp_json};
  if(cp.length){{
    new Chart($('ch-cp'),{{type:'bar',data:{{labels:cp.map(c=>c.name_ar),datasets:[
      {{label:'ناقلات',data:cp.map(c=>c.tanker),backgroundColor:'rgba(0,120,200,.7)',stack:'s'}},
      {{label:'بضائع',data:cp.map(c=>c.cargo),backgroundColor:'rgba(80,160,80,.7)',stack:'s'}},
      {{label:'أخرى',data:cp.map(c=>c.other),backgroundColor:'rgba(150,150,150,.5)',stack:'s'}}
    ]}},options:{{responsive:true,maintainAspectRatio:false,animation:false,plugins:{{legend:{{labels:{{font:{{size:9}},boxWidth:10}}}},title:{{display:true,text:'التعرض التجاري للقوى الكبرى',font:{{size:11}},color:'#7a0028'}}}},scales:{{x:{{stacked:true,ticks:{{font:{{size:9}}}},grid:{{display:false}}}},y:{{stacked:true,beginAtZero:true,ticks:{{font:{{size:9}}}},grid:{{color:'rgba(0,0,0,.04)'}}}}}}}}}});
  }}

}})();
(function(){{
  var map=L.map("pred-map",{{zoomControl:true}}).setView([27,45],5);
  L.tileLayer("https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png",{{subdomains:"abcd",maxZoom:18}}).addTo(map);
  var cells={pred_map_json};
  cells.forEach(function(c){{var p=c.prob;var color=p>=0.75?"#7a0028":p>=0.5?"#c0406a":p>=0.25?"#d97706":"#16a34a";var op=p>=0.75?0.85:p>=0.5?0.7:p>=0.25?0.5:0.3;
    L.rectangle([[c.lat,c.lon],[c.lat+0.5,c.lon+0.5]],{{color:color,weight:0.3,fillColor:color,fillOpacity:op}}).addTo(map).bindPopup("<div style='direction:rtl'><strong>"+c.country+"</strong><br>"+Math.round(p*100)+"%"+(c.new_em?" ★":"")+"</div>");}});
}})();
</script>
</body></html>"""

HTML = HTML.encode("utf-8",errors="replace").decode("utf-8")
REPORT_TEXT = HTML
out = os.path.join(OUTPUT_DIR, f"weekly_prediction_{date_iso}.html")
with open(out,"w",encoding="utf-8") as f:
    f.write(HTML)

print(f"\n{'='*60}")
print(f"  REPORT COMPLETE")
print(f"  Charts  : escalation, political, jamming, jam-corr")
print(f"  Tables  : risk levels, coincidences, corridors, satellites")
print(f"  Map     : Leaflet prediction heatmap")
print(f"  Analysis: Gemini findings ({len(narrative):,} chars)")
print(f"  Saved   > {out}")
print(f"{'='*60}")
# webbrowser.open(f"file://{out}")  # disabled in production