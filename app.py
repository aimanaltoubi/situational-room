#!/usr/bin/env python3
"""
app.py — International Data Analytics System (نظام تحليل البيانات الدولية)

Serves every workspace under workspaces/<slug>/ — each one has its own
situational room (dashboard), analytics report and incidents database.

Usage:
  python3 app.py                    # start on port 5000
  python3 app.py --port 8080        # custom port
  python3 app.py --refresh          # rebuild default workspace then serve
"""

import os, re, sys, argparse, subprocess, hmac, threading, time, json
from datetime import datetime
from flask import (Flask, send_file, jsonify, request, Response,
                   render_template_string, redirect, url_for, flash, abort)
from dotenv import load_dotenv

from tools import incidents_db as db
from tools import workspace as ws

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

# Optional access gate — set SITE_USERNAME + SITE_PASSWORD in .env to require
# a login before serving anything (recommended once the app is public).
SITE_USERNAME = os.environ.get("SITE_USERNAME", "")
SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")

app = Flask(__name__)
# only used to sign the flash-message cookie
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # uploaded data files


def _auth_enabled():
    return bool(SITE_USERNAME and SITE_PASSWORD)


def _check_credentials(username, password):
    # compare_digest avoids leaking match length via timing
    return (
        hmac.compare_digest(username or "", SITE_USERNAME)
        and hmac.compare_digest(password or "", SITE_PASSWORD)
    )


@app.before_request
def _require_login():
    if not _auth_enabled():
        return None
    if request.path == "/status":
        # left open so PaaS/container health checks (no auth header) can pass
        return None
    auth = request.authorization
    if not auth or not _check_credentials(auth.username, auth.password):
        return Response(
            "Authentication required", 401,
            {"WWW-Authenticate": 'Basic realm="International Data Analytics System"'}
        )
    return None


def _workspace_or_404(slug):
    w = ws.get_workspace(slug)
    if not w:
        abort(404)
    return w


def _dashboard_path(slug):
    return os.path.join(ws.paths(slug)["output"], "ifs_globe.html")


def _latest_report(slug):
    out = ws.paths(slug)["output"]
    if not os.path.isdir(out):
        return None
    files = sorted(
        (f for f in os.listdir(out)
         if f.startswith("weekly_prediction_") and f.endswith(".html")),
        reverse=True,
    )
    return os.path.join(out, files[0]) if files else None


def _workspace_status(slug):
    path = _dashboard_path(slug)
    building = _is_building(slug)
    if os.path.exists(path):
        return {
            "status": "ready",
            "building": building,
            "size_kb": os.path.getsize(path) // 1024,
            "built_at": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
            "analytics": _latest_report(slug) is not None,
        }
    return {"status": "not_built", "building": building,
            "analytics": _latest_report(slug) is not None}


# ── Background builds ───────────────────────────────────────────────
# A marker file (not an in-memory flag) so every gunicorn worker sees the build.
BUILD_STALE_SECONDS = 30 * 60


def _build_marker(slug):
    return os.path.join(ws.paths(slug)["logs"], ".building")


def _is_building(slug):
    marker = _build_marker(slug)
    return os.path.exists(marker) and time.time() - os.path.getmtime(marker) < BUILD_STALE_SECONDS


def _run_build(slug):
    marker = _build_marker(slug)
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    open(marker, "w").close()
    try:
        with open(os.path.join(os.path.dirname(marker), "build.log"), "w", encoding="utf-8") as log:
            subprocess.run(
                [sys.executable, os.path.join(PROJECT_DIR, "run_pipeline.py"),
                 "-w", slug, "--skip-scrape"],
                stdout=log, stderr=subprocess.STDOUT,
            )
    finally:
        if os.path.exists(marker):
            os.remove(marker)


def start_build(slug):
    """Start a rebuild in the background; returns False if one is already running."""
    if _is_building(slug):
        return False
    threading.Thread(target=_run_build, args=(slug,), daemon=True).start()
    return True


# ── Shared styling ──────────────────────────────────────────────────
BASE_STYLE = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{
  min-height:100vh;padding:32px 16px;
  background:radial-gradient(circle at 50% 20%,#3a0012,#1a0008 70%);
  font-family:'IBM Plex Sans Arabic','Noto Naskh Arabic',Arial,sans-serif;color:#f0e8ec;
}
a{color:#fff}
.wrap{max-width:980px;margin:0 auto}
.head{text-align:center;margin-bottom:28px}
.head .en{color:#e0c4cf;font-size:12px;letter-spacing:2px;text-transform:uppercase}
.head h1{font-size:30px;color:#fff;margin:6px 0}
.head p{color:#f0e8ec;font-size:14px;line-height:1.8}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}
.card{
  background:rgba(26,0,8,.55);border:1px solid rgba(255,255,255,.22);
  border-radius:14px;padding:24px;box-shadow:0 10px 40px rgba(0,0,0,.5);
}
.card h2{font-size:19px;color:#fff;margin-bottom:4px}
.card .en{color:#e0c4cf;font-size:11px;margin-bottom:14px}
.status{font-size:12px;margin-bottom:14px}
.ok{color:#5fe08a}.bad{color:#ff9a88}
.btn{
  display:inline-block;padding:10px 20px;font-size:14px;font-weight:700;
  text-decoration:none;color:#3a0012;border:none;cursor:pointer;font-family:inherit;
  background:#fff;border-radius:8px;margin:3px 0;
}
.btn:hover{background:#f3e4ea}
.btn.secondary{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.5)}
.btn.secondary:hover{background:rgba(255,255,255,.1)}
.btn.block{display:block;text-align:center;margin:8px 0}
.flash{background:rgba(34,160,80,.15);border:1px solid #22a050;color:#a8f5c4;
  padding:8px 14px;border-radius:6px;margin-bottom:16px;font-size:13px}
.field{margin-bottom:12px}
.field label{display:block;font-size:12px;color:#f0e8ec;margin-bottom:4px}
.field input{width:100%;padding:8px 10px;background:#2a0410;border:1px solid rgba(255,255,255,.3);
  color:#fff;border-radius:6px;font-size:13px;font-family:inherit}
.footer{margin-top:28px;text-align:center;font-size:11px;color:#e0c4cf}
"""

HUB_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ system_ar }}</title>
<style>{{ style }}</style></head><body><div class="wrap">
  <div class="head">
    <div class="en">{{ system_en }}</div>
    <h1>{{ system_ar }}</h1>
    <p>اختر مساحة العمل. لكل مساحة غرفة أوضاع خاصة بها وصفحة تحليلات وقاعدة أحداث مرتبطة بها.</p>
  </div>
  {% with messages = get_flashed_messages() %}
    {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
  {% endwith %}
  <div class="grid">
    {% for w in workspaces %}
    <div class="card">
      <h2>{{ w.name_ar }}</h2>
      <div class="en">{{ w.name_en }}</div>
      <div class="status {{ 'ok' if w.state.status == 'ready' else 'bad' }}">
        {{ 'الغرفة جاهزة' if w.state.status == 'ready' else 'لم تُبنَ الغرفة بعد' }}
      </div>
      <a class="btn block" href="{{ url_for('workspace_home', slug=w.slug) }}">فتح المساحة</a>
      <a class="btn secondary block" href="{{ url_for('workspace_dashboard', slug=w.slug) }}">🌍 غرفة الأوضاع</a>
      <a class="btn secondary block" href="{{ url_for('workspace_analytics', slug=w.slug) }}">📊 {{ w.analytics_name_ar }}</a>
    </div>
    {% endfor %}
    <form class="card" method="post" action="{{ url_for('create_workspace_route') }}">
      <h2>+ مساحة عمل جديدة</h2>
      <div class="en">New empty workspace — same room, same analytics</div>
      <div class="field"><label>الاسم بالعربية</label>
        <input name="name_ar" required maxlength="80"></div>
      <div class="field"><label>الاسم بالإنجليزية (يُستخدم كمعرّف المجلد)</label>
        <input name="name_en" required maxlength="80" dir="ltr"></div>
      <div class="field"><label>تاريخ البداية (YYYY-MM-DD) — اختياري</label>
        <input name="start_date" dir="ltr" placeholder="{{ today }}"></div>
      <button class="btn" type="submit">إنشاء</button>
    </form>
  </div>
  <div class="footer">الحالة: <a href="/status">/status</a></div>
</div></body></html>"""

WORKSPACE_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ w.name_ar }} — {{ system_ar }}</title>
{% if state.building %}<meta http-equiv="refresh" content="5">{% endif %}
<style>{{ style }}</style></head><body><div class="wrap">
  <div class="head">
    <div class="en">{{ system_en }} · {{ w.name_en }}</div>
    <h1>{{ w.name_ar }}</h1>
    <p>{{ system_ar }}</p>
  </div>
  {% with messages = get_flashed_messages() %}
    {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
  {% endwith %}
  {% if state.building %}<div class="flash">جارٍ بناء المساحة… تُحدّث هذه الصفحة تلقائياً عند الانتهاء.</div>{% endif %}
  <div class="grid">
    <div class="card">
      <h2>🌍 غرفة الأوضاع</h2>
      <div class="en">Situational Room</div>
      <div class="status {{ 'ok' if state.status == 'ready' else 'bad' }}">
        {{ 'البيانات مبنية وجاهزة للتحميل.' if state.status == 'ready' else 'لم تُبنَ الغرفة بعد — اضغط «إعادة البناء».' }}
      </div>
      <a class="btn block" href="{{ url_for('workspace_dashboard', slug=w.slug) }}">تحميل الغرفة</a>
    </div>
    <div class="card">
      <h2>📊 {{ w.analytics_name_ar }}</h2>
      <div class="en">{{ w.analytics_name_en }}</div>
      <div class="status {{ 'ok' if state.analytics else 'bad' }}">
        {{ 'التقرير التحليلي متوفر.' if state.analytics else 'لا يوجد تقرير تحليلي بعد.' }}
      </div>
      <a class="btn block" href="{{ url_for('workspace_analytics', slug=w.slug) }}">فتح التحليلات</a>
    </div>
    <div class="card">
      <h2>🗂 قاعدة الأحداث</h2>
      <div class="en">Incidents Database</div>
      <div class="status">workspaces/{{ w.slug }}/data/events.csv</div>
      <a class="btn block" href="{{ url_for('list_incidents_route', slug=w.slug) }}">إدارة الأحداث</a>
      <form method="post" action="{{ url_for('rebuild_workspace', slug=w.slug) }}">
        <button class="btn secondary block" style="width:100%" type="submit" {{ 'disabled' if state.building else '' }}>
          {{ 'جارٍ البناء…' if state.building else 'إعادة البناء' }}</button>
      </form>
    </div>
    <form class="card" method="post" enctype="multipart/form-data"
          action="{{ url_for('upload_data', slug=w.slug) }}">
      <h2>⬆ رفع بيانات المساحة</h2>
      <div class="en">Data files belong to this workspace only</div>
      {% for key, f in data_files.items() %}
      <div class="field"><label>{{ f.label }} —
        <span class="{{ 'ok' if f.present else 'bad' }}">{{ 'موجود' if f.present else 'غير موجود' }}</span></label>
        <input type="file" name="{{ key }}"></div>
      {% endfor %}
      <button class="btn" type="submit">رفع وإعادة البناء</button>
    </form>
    <form class="card" method="post" action="{{ url_for('edit_workspace', slug=w.slug) }}">
      <h2>⚙ إعدادات المساحة</h2>
      <div class="en">Workspace settings</div>
      <div class="field"><label>الاسم بالعربية</label>
        <input name="name_ar" value="{{ w.name_ar }}" required maxlength="80"></div>
      <div class="field"><label>الاسم بالإنجليزية</label>
        <input name="name_en" value="{{ w.name_en }}" required maxlength="80" dir="ltr"></div>
      <div class="field"><label>تاريخ البداية (YYYY-MM-DD)</label>
        <input name="start_date" value="{{ w.start_date }}" required dir="ltr"></div>
      <div class="field"><label>قناة تيليجرام (اختياري)</label>
        <input name="telegram_channel" value="{{ w.telegram_channel }}" dir="ltr"></div>
      <div class="field"><label>وحدات المراقبة المفعّلة في هذه الغرفة</label>
        {% for key, label in feature_labels.items() %}
        <label style="display:block;color:#f0e8ec"><input type="checkbox" name="feat_{{ key }}" value="1"
          style="width:auto" {{ 'checked' if w.features[key] else '' }}> {{ label }}</label>
        {% endfor %}</div>
      {% for key, label in label_fields.items() %}
      <div class="field"><label>{{ label }}</label>
        <input name="lbl_{{ key }}" value="{{ w.labels[key] }}"></div>
      {% endfor %}
      <button class="btn" type="submit">حفظ</button>
    </form>
  </div>
  {% if quality %}
  <div class="card" style="margin-top:18px">
    <h2>📋 جودة البيانات</h2>
    <div class="en">Data quality · {{ quality.generated_at[:16].replace('T', ' ') }} UTC</div>
    {% for s in quality.sources %}
    <div style="display:grid;grid-template-columns:150px 1fr;gap:10px;padding:8px 0;border-top:1px solid rgba(255,255,255,.12);font-size:13px">
      <div><span class="{{ 'ok' if s.status == 'ok' else 'bad' }}">●</span> {{ s.label }}
        <div style="font-size:11px;color:#e0c4cf">{{ status_ar[s.status] }}{% if s.count %} · {{ s.count }} {{ s.unit }}{% endif %}</div></div>
      <div style="color:#f0e8ec">{{ s.note or s.source }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}
  <div class="footer"><a href="{{ url_for('index') }}">&rarr; كل مساحات العمل</a></div>
</div></body></html>"""

# ── Incidents database pages ────────────────────────────────────────
DB_STYLE = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{
  background:#1a0008;color:#f0e8ec;min-height:100vh;
  font-family:'IBM Plex Sans Arabic',Arial,sans-serif;padding:24px;
}
a{color:#d4a017}
h1{color:#d4a017;font-size:22px;margin-bottom:4px}
.sub{color:#c8a0b0;font-size:12px;margin-bottom:20px}
.toolbar{display:flex;gap:12px;align-items:center;margin-bottom:16px;flex-wrap:wrap}
.btn{
  display:inline-block;padding:8px 18px;font-size:13px;font-weight:700;
  text-decoration:none;color:#1a0008;background:linear-gradient(135deg,#d4a017,#b8860b);
  border-radius:6px;border:none;cursor:pointer;
}
.btn.secondary{background:transparent;color:#d4a017;border:1px solid rgba(184,134,11,.5)}
.btn.danger{background:linear-gradient(135deg,#e8004a,#960030);color:#fff}
.flash{background:rgba(34,160,80,.15);border:1px solid #22a050;color:#8ef0b0;
  padding:8px 14px;border-radius:6px;margin-bottom:16px;font-size:13px}
table{width:100%;border-collapse:collapse;font-size:12px;background:rgba(255,255,255,.02)}
th,td{padding:8px 10px;border-bottom:1px solid rgba(184,134,11,.15);text-align:left;vertical-align:top}
th{color:#d4a017;text-transform:uppercase;font-size:11px;letter-spacing:.5px}
tr:hover{background:rgba(184,134,11,.05)}
.desc-cell{max-width:320px}
.actions form{display:inline}
.field{margin-bottom:14px}
.field label{display:block;font-size:12px;color:#c8a0b0;margin-bottom:4px}
.field input,.field select,.field textarea{
  width:100%;padding:8px 10px;background:#2a0410;border:1px solid rgba(184,134,11,.3);
  color:#f0e8ec;border-radius:6px;font-size:13px;font-family:inherit;
}
.field textarea{min-height:90px;resize:vertical}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:0 20px}
form.card{max-width:720px;background:rgba(26,0,8,.5);border:1px solid rgba(184,134,11,.25);
  border-radius:10px;padding:24px}
"""

DB_LIST_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Incidents Database — {{ w.name_ar }}</title>
<style>{{ style }}</style></head><body>
  <h1>Incidents Database — {{ w.name_ar }}</h1>
  <div class="sub">{{ incidents|length }} incidents · stored directly in workspaces/{{ w.slug }}/data/events.csv</div>
  {% with messages = get_flashed_messages() %}
    {% if messages %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endif %}
  {% endwith %}
  <div class="toolbar">
    <a class="btn" href="{{ url_for('new_incident', slug=w.slug) }}">+ Add Incident</a>
    <form method="post" action="{{ url_for('rebuild_workspace', slug=w.slug) }}?next=database">
      <button class="btn secondary" type="submit">Rebuild Dashboard</button>
    </form>
    <a class="btn secondary" href="{{ url_for('workspace_home', slug=w.slug) }}">&larr; Workspace</a>
  </div>
  <table>
    <tr><th>Date</th><th>Day</th><th>Country</th><th>Location</th><th>Type</th>
        <th>Actor</th><th>Killed</th><th>Injured</th><th>Description</th><th></th></tr>
    {% for i in incidents %}
    <tr>
      <td>{{ i.date }}</td>
      <td>{{ i.day_of_war }}</td>
      <td>{{ i.country }}</td>
      <td>{{ i.location }}</td>
      <td>{{ i.event_type }}</td>
      <td>{{ i.actor }}</td>
      <td>{{ i.killed }}</td>
      <td>{{ i.injured }}</td>
      <td class="desc-cell">{{ i.description }}</td>
      <td class="actions">
        <a class="btn secondary" href="{{ url_for('edit_incident', slug=w.slug, incident_id=i.id) }}">Edit</a>
        <form method="post" action="{{ url_for('delete_incident_route', slug=w.slug, incident_id=i.id) }}"
              onsubmit="return confirm('Delete this incident?');">
          <button class="btn danger" type="submit">Delete</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>
</body></html>"""

DB_FORM_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} — {{ w.name_ar }}</title>
<style>{{ style }}</style></head><body>
  <h1>{{ title }} — {{ w.name_ar }}</h1>
  <div class="sub"><a href="{{ url_for('list_incidents_route', slug=w.slug) }}">&larr; Back to database</a></div>
  <form class="card" method="post">
    <div class="grid">
      <div class="field"><label>Date (YYYY-MM-DD)</label>
        <input name="date" value="{{ i.date }}" required></div>
      <div class="field"><label>Datetime (YYYY-MM-DD HH:MM:SS)</label>
        <input name="datetime" value="{{ i.datetime }}" required></div>
      <div class="field"><label>Time source</label>
        <select name="time_source">
          <option value="known" {{ 'selected' if i.time_source=='known' else '' }}>known</option>
          <option value="inferred" {{ 'selected' if i.time_source=='inferred' else '' }}>inferred</option>
        </select></div>
      <div class="field"><label>Day of war</label>
        <input name="day_of_war" type="number" value="{{ i.day_of_war }}"></div>
      <div class="field"><label>Country</label>
        <input name="country" value="{{ i.country }}" required></div>
      <div class="field"><label>Location</label>
        <input name="location" value="{{ i.location }}" required></div>
      <div class="field"><label>Event type</label>
        <input name="event_type" value="{{ i.event_type }}" required></div>
      <div class="field"><label>Actor</label>
        <input name="actor" value="{{ i.actor }}"></div>
      <div class="field"><label>Actor grouped</label>
        <input name="actor_grouped" value="{{ i.actor_grouped }}"></div>
      <div class="field"><label>Target</label>
        <input name="target" value="{{ i.target }}"></div>
      <div class="field"><label>Killed</label>
        <input name="killed" type="number" value="{{ i.killed }}"></div>
      <div class="field"><label>Injured</label>
        <input name="injured" type="number" value="{{ i.injured }}"></div>
      <div class="field"><label>Total casualties</label>
        <input name="total_casualties" type="number" value="{{ i.total_casualties }}"></div>
      <div class="field"><label>Has casualties</label>
        <select name="has_casualties">
          <option value="True" {{ 'selected' if i.has_casualties in ('True', True) else '' }}>True</option>
          <option value="False" {{ 'selected' if i.has_casualties in ('False', False) else '' }}>False</option>
        </select></div>
    </div>
    <div class="field"><label>Description</label>
      <textarea name="description">{{ i.description }}</textarea></div>
    <button class="btn" type="submit">Save</button>
    <a class="btn secondary" href="{{ url_for('list_incidents_route', slug=w.slug) }}">Cancel</a>
  </form>
</body></html>"""

_BLANK_INCIDENT = {c: "" for c in db.COLUMNS}
_BLANK_INCIDENT.update({"day_of_war": 0, "killed": 0, "injured": 0, "total_casualties": 0})


# ── Hub ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    items = []
    for w in ws.list_workspaces():
        w["state"] = _workspace_status(w["slug"])
        items.append(w)
    return render_template_string(
        HUB_TEMPLATE, style=BASE_STYLE, workspaces=items,
        system_ar=ws.SYSTEM_NAME_AR, system_en=ws.SYSTEM_NAME_EN,
        today=datetime.now().strftime("%Y-%m-%d"),
    )


@app.route("/workspaces/new", methods=["POST"])
def create_workspace_route():
    name_ar = request.form.get("name_ar", "")
    name_en = request.form.get("name_en", "")
    slug = re.sub(r"[^a-z0-9]+", "-", name_en.lower()).strip("-")
    try:
        w = ws.create_workspace(slug, name_ar, name_en,
                                (request.form.get("start_date") or "").strip() or None)
    except ValueError as e:
        flash(f"تعذّر إنشاء المساحة: {e}")
        return redirect(url_for("index"))
    flash(f"تم إنشاء المساحة «{w['name_ar']}» — أضف بياناتها ثم اضغط «إعادة البناء».")
    return redirect(url_for("workspace_home", slug=w["slug"]))


# ── Workspace pages ─────────────────────────────────────────────────
@app.route("/w/<slug>/")
def workspace_home(slug):
    w = _workspace_or_404(slug)
    return render_template_string(
        WORKSPACE_TEMPLATE, style=BASE_STYLE, w=w, state=_workspace_status(slug),
        data_files=_data_file_info(slug),
        quality=_data_quality(slug),
        status_ar={"ok": "سليمة", "partial": "جزئية", "stale": "قديمة", "empty": "فارغة"},
        feature_labels=ws.FEATURE_LABELS, label_fields=ws.LABEL_FIELDS,
        system_ar=ws.SYSTEM_NAME_AR, system_en=ws.SYSTEM_NAME_EN,
    )


@app.route("/w/<slug>/dashboard")
def workspace_dashboard(slug):
    _workspace_or_404(slug)
    path = _dashboard_path(slug)
    if os.path.exists(path):
        return send_file(path)
    return (
        "<h1>الغرفة لم تُبنَ بعد</h1>"
        f"<p>Run: <code>python3 run_pipeline.py -w {slug}</code></p>",
        404,
    )


@app.route("/w/<slug>/analytics")
def workspace_analytics(slug):
    _workspace_or_404(slug)
    report = _latest_report(slug)
    if report:
        return send_file(report)
    return "<h1>لا يوجد تقرير تحليلي بعد لهذه المساحة</h1>", 404


@app.route("/w/<slug>/status")
def workspace_status(slug):
    _workspace_or_404(slug)
    return jsonify(_workspace_status(slug))


@app.route("/w/<slug>/rebuild", methods=["POST"])
def rebuild_workspace(slug):
    _workspace_or_404(slug)
    if start_build(slug):
        flash("بدأ بناء المساحة من أحدث البيانات.")
    else:
        flash("هناك عملية بناء جارية بالفعل.")
    if request.args.get("next") == "database":
        return redirect(url_for("list_incidents_route", slug=slug))
    return redirect(url_for("workspace_home", slug=slug))


def _data_file_info(slug):
    data_dir = ws.paths(slug)["data"]
    return {
        key: {"label": label, "present": os.path.exists(os.path.join(data_dir, name))}
        for key, (name, label) in ws.DATA_FILES.items()
    }


def _data_quality(slug):
    path = os.path.join(ws.paths(slug)["output"], "data_quality.json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.route("/w/<slug>/upload", methods=["POST"])
def upload_data(slug):
    _workspace_or_404(slug)
    data_dir = ws.paths(slug)["data"]
    os.makedirs(data_dir, exist_ok=True)
    saved = 0
    for key, (name, _label) in ws.DATA_FILES.items():
        f = request.files.get(key)
        if f and f.filename:
            f.save(os.path.join(data_dir, name))  # fixed names only — never the client's file name
            saved += 1
    if not saved:
        flash("لم يُختَر أي ملف.")
        return redirect(url_for("workspace_home", slug=slug))
    flash(f"تم رفع {saved} ملف(ات) — جارٍ إعادة بناء المساحة.")
    start_build(slug)
    return redirect(url_for("workspace_home", slug=slug))


@app.route("/w/<slug>/settings", methods=["POST"])
def edit_workspace(slug):
    _workspace_or_404(slug)
    try:
        ws.update_workspace(
            slug, request.form.get("name_ar", ""), request.form.get("name_en", ""),
            (request.form.get("start_date") or "").strip(),
            request.form.get("telegram_channel", ""),
            features={k: request.form.get(f"feat_{k}") == "1" for k in ws.FEATURE_LABELS},
            labels={k: request.form.get(f"lbl_{k}", "") for k in ws.DEFAULT_LABELS},
        )
    except ValueError as e:
        flash(f"تعذّر الحفظ: {e}")
    else:
        flash("تم حفظ الإعدادات — اضغط «إعادة البناء» لتطبيقها.")
    return redirect(url_for("workspace_home", slug=slug))


# ── Health check + legacy URLs (default workspace) ──────────────────
@app.route("/status")
def status():
    states = {w["slug"]: _workspace_status(w["slug"]) for w in ws.list_workspaces()}
    default = states.get(ws.DEFAULT_SLUG, {"status": "not_built"})
    return jsonify({**default, "workspaces": states})


@app.route("/dashboard")
def legacy_dashboard():
    return redirect(url_for("workspace_dashboard", slug=ws.DEFAULT_SLUG))


@app.route("/weekly")
def legacy_weekly():
    return redirect(url_for("workspace_analytics", slug=ws.DEFAULT_SLUG))


# ── Incidents database (per workspace) ──────────────────────────────
@app.route("/w/<slug>/database")
def list_incidents_route(slug):
    w = _workspace_or_404(slug)
    return render_template_string(
        DB_LIST_TEMPLATE, style=DB_STYLE, w=w, incidents=db.list_incidents(slug)
    )


@app.route("/w/<slug>/database/new", methods=["GET", "POST"])
def new_incident(slug):
    w = _workspace_or_404(slug)
    if request.method == "POST":
        db.add_incident(slug, request.form)
        flash("Incident added.")
        return redirect(url_for("list_incidents_route", slug=slug))
    return render_template_string(
        DB_FORM_TEMPLATE, style=DB_STYLE, w=w, title="Add Incident", i=_BLANK_INCIDENT
    )


@app.route("/w/<slug>/database/<int:incident_id>/edit", methods=["GET", "POST"])
def edit_incident(slug, incident_id):
    w = _workspace_or_404(slug)
    incident = db.get_incident(slug, incident_id)
    if not incident:
        return "Incident not found", 404
    if request.method == "POST":
        db.update_incident(slug, incident_id, request.form)
        flash("Incident updated.")
        return redirect(url_for("list_incidents_route", slug=slug))
    return render_template_string(
        DB_FORM_TEMPLATE, style=DB_STYLE, w=w, title="Edit Incident", i=incident
    )


@app.route("/w/<slug>/database/<int:incident_id>/delete", methods=["POST"])
def delete_incident_route(slug, incident_id):
    _workspace_or_404(slug)
    db.delete_incident(slug, incident_id)
    flash("Incident deleted.")
    return redirect(url_for("list_incidents_route", slug=slug))


@app.route("/database")
def legacy_database():
    return redirect(url_for("list_incidents_route", slug=ws.DEFAULT_SLUG))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--refresh", action="store_true",
                        help="Run pipeline for the default workspace before starting server")
    parser.add_argument("--public", action="store_true",
                        help="Open a shareable public link via ngrok "
                             "(requires NGROK_AUTHTOKEN in .env)")
    args = parser.parse_args()

    if args.refresh:
        print("Running pipeline first...")
        subprocess.run([sys.executable, os.path.join(PROJECT_DIR, "run_pipeline.py")])

    print(f"\n  Workspaces: http://localhost:{args.port}")
    for w in ws.list_workspaces():
        print(f"    {w['slug']:28s} http://localhost:{args.port}/w/{w['slug']}/")
    print(f"  Status:     http://localhost:{args.port}/status")
    print(f"  Login:      {'required (SITE_USERNAME/SITE_PASSWORD)' if _auth_enabled() else 'disabled — set SITE_USERNAME/SITE_PASSWORD in .env before exposing this publicly'}")

    if args.public:
        ngrok_token = os.environ.get("NGROK_AUTHTOKEN", "")
        if not ngrok_token:
            print("  Public link: skipped — set NGROK_AUTHTOKEN in .env "
                  "(free at https://dashboard.ngrok.com/get-started/your-authtoken)")
        else:
            try:
                from pyngrok import ngrok
                ngrok.set_auth_token(ngrok_token)
                public_url = ngrok.connect(args.port, "http").public_url
                print(f"  Public link: {public_url}  (anyone with this URL can reach the app)")
                if not _auth_enabled():
                    print("  WARNING: no login set — set SITE_USERNAME/SITE_PASSWORD before sharing this link.")
            except ImportError:
                print("  Public link: skipped — run: pip install pyngrok")
    print()
    app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
