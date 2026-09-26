#!/usr/bin/env python3
"""
app.py — Serve the Situational Room dashboard

Usage:
  python3 app.py                    # start on port 5000
  python3 app.py --port 8080        # custom port
  python3 app.py --refresh          # rebuild data then serve
"""

import os, sys, argparse, subprocess, hmac
from flask import Flask, send_file, jsonify, request, Response, render_template_string, redirect, url_for, flash
from dotenv import load_dotenv

from tools import incidents_db as db

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

# Optional access gate — set SITE_USERNAME + SITE_PASSWORD in .env to require
# a login before serving anything (recommended once the app is public).
SITE_USERNAME = os.environ.get("SITE_USERNAME", "")
SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")

app = Flask(__name__)
# only used to sign the flash-message cookie for the database pages
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)



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
            {"WWW-Authenticate": 'Basic realm="Situational Room"'}
        )
    return None

LANDING_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FusionIntell — Situational Room</title>
<style>
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    min-height:100vh;display:flex;align-items:center;justify-content:center;
    background:radial-gradient(circle at 50% 20%,#3a0012,#1a0008 70%);
    font-family:'IBM Plex Sans Arabic',Arial,sans-serif;color:#f0e8ec;
  }}
  .card{{
    max-width:640px;width:90%;padding:48px 40px;text-align:center;
    background:rgba(26,0,8,.55);border:1px solid rgba(184,134,11,.35);
    border-radius:14px;box-shadow:0 10px 40px rgba(0,0,0,.5);
  }}
  h1{{
    font-size:28px;letter-spacing:1px;color:#d4a017;margin-bottom:8px;
  }}
  .subtitle{{color:#c8a0b0;font-size:13px;margin-bottom:24px;text-transform:uppercase;letter-spacing:2px}}
  p.desc{{font-size:15px;line-height:1.7;color:#e8dce2;margin-bottom:28px}}
  .status{{font-size:12px;margin-bottom:24px;color:{status_color}}}
  .btn{{
    display:inline-block;padding:14px 36px;font-size:15px;font-weight:700;
    letter-spacing:1px;text-decoration:none;color:#1a0008;
    background:linear-gradient(135deg,#d4a017,#b8860b);
    border-radius:8px;transition:transform .15s ease,box-shadow .15s ease;
  }}
  .btn:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(212,160,23,.4)}}
  .footer{{margin-top:28px;font-size:11px;color:#9a6070}}
</style>
</head>
<body>
  <div class="card">
    <div class="subtitle">Middle East Conflict Intelligence</div>
    <h1>FusionIntell Situational Room</h1>
    <p class="desc">
      A live intelligence dashboard combining a 3D Cesium globe, satellite
      tracking, GPS jamming analysis, flight and marine vessel monitoring,
      and AI-powered analytics into a single operational picture of the
      conflict.
    </p>
    <div class="status">{status_text}</div>
    <a class="btn" href="/dashboard">Load System</a>
    <div style="margin-top:14px">
      <a href="/database" style="color:#d4a017;font-size:13px;text-decoration:underline">Manage Incidents Database</a>
    </div>
    <div class="footer">Status: <a href="/status" style="color:#9a6070">/status</a> &middot; Weekly report: <a href="/weekly" style="color:#9a6070">/weekly</a></div>
  </div>
</body>
</html>"""

@app.route("/")
def index():
    html_path = os.path.join(OUTPUT_DIR, "ifs_globe.html")
    if os.path.exists(html_path):
        status_text  = "System data is built and ready to load."
        status_color = "#22a050"
    else:
        status_text  = "Dashboard not built yet — run: python3 run_pipeline.py"
        status_color = "#ff2200"
    return LANDING_PAGE.format(status_text=status_text, status_color=status_color)

@app.route("/dashboard")
def dashboard():
    html_path = os.path.join(OUTPUT_DIR, "ifs_globe.html")
    if os.path.exists(html_path):
        return send_file(html_path)
    return (
        "<h1>Dashboard not built yet</h1>"
        "<p>Run: <code>python3 run_pipeline.py</code></p>",
        404
    )

@app.route("/status")
def status():
    html_path = os.path.join(OUTPUT_DIR, "ifs_globe.html")
    if os.path.exists(html_path):
        size = os.path.getsize(html_path)
        mtime = os.path.getmtime(html_path)
        from datetime import datetime
        built = datetime.fromtimestamp(mtime).isoformat()
        return jsonify({"status": "ready", "size_kb": size // 1024, "built_at": built})
    return jsonify({"status": "not_built"})

@app.route("/weekly")
def weekly():
    # Serve the latest weekly report if it exists
    for f in sorted(os.listdir(OUTPUT_DIR), reverse=True):
        if f.startswith("weekly_prediction_") and f.endswith(".html"):
            return send_file(os.path.join(OUTPUT_DIR, f))
    return "No weekly report found", 404

# ── Incidents database ──────────────────────────────────────────────
# Lets users add/edit/delete war incidents from the browser instead of
# hand-editing data/iran_war_clean.csv directly. The CSV itself is the
# only store — every read/write here goes straight to that file, so the
# next pipeline rebuild (see /database/rebuild) always sees the latest edits.

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
<title>Incidents Database — FusionIntell</title>
<style>{{ style }}</style></head><body>
  <h1>Incidents Database</h1>
  <div class="sub">{{ incidents|length }} incidents · stored directly in data/iran_war_clean.csv</div>
  {% with messages = get_flashed_messages() %}
    {% if messages %}{% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}{% endif %}
  {% endwith %}
  <div class="toolbar">
    <a class="btn" href="{{ url_for('new_incident') }}">+ Add Incident</a>
    <form method="post" action="{{ url_for('rebuild_dashboard') }}">
      <button class="btn secondary" type="submit">Rebuild Dashboard</button>
    </form>
    <a class="btn secondary" href="{{ url_for('index') }}">&larr; Main Page</a>
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
        <a class="btn secondary" href="{{ url_for('edit_incident', incident_id=i.id) }}">Edit</a>
        <form method="post" action="{{ url_for('delete_incident_route', incident_id=i.id) }}"
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
<title>{{ title }} — FusionIntell</title>
<style>{{ style }}</style></head><body>
  <h1>{{ title }}</h1>
  <div class="sub"><a href="{{ url_for('list_incidents_route') }}">&larr; Back to database</a></div>
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
    <a class="btn secondary" href="{{ url_for('list_incidents_route') }}">Cancel</a>
  </form>
</body></html>"""

_BLANK_INCIDENT = {c: "" for c in db.COLUMNS}
_BLANK_INCIDENT.update({"day_of_war": 0, "killed": 0, "injured": 0, "total_casualties": 0})


@app.route("/database")
def list_incidents_route():
    return render_template_string(
        DB_LIST_TEMPLATE, style=DB_STYLE, incidents=db.list_incidents()
    )


@app.route("/database/new", methods=["GET", "POST"])
def new_incident():
    if request.method == "POST":
        db.add_incident(request.form)
        flash("Incident added.")
        return redirect(url_for("list_incidents_route"))
    return render_template_string(
        DB_FORM_TEMPLATE, style=DB_STYLE, title="Add Incident", i=_BLANK_INCIDENT
    )


@app.route("/database/<int:incident_id>/edit", methods=["GET", "POST"])
def edit_incident(incident_id):
    incident = db.get_incident(incident_id)
    if not incident:
        return "Incident not found", 404
    if request.method == "POST":
        db.update_incident(incident_id, request.form)
        flash("Incident updated.")
        return redirect(url_for("list_incidents_route"))
    return render_template_string(
        DB_FORM_TEMPLATE, style=DB_STYLE, title="Edit Incident", i=incident
    )


@app.route("/database/<int:incident_id>/delete", methods=["POST"])
def delete_incident_route(incident_id):
    db.delete_incident(incident_id)
    flash("Incident deleted.")
    return redirect(url_for("list_incidents_route"))


@app.route("/database/rebuild", methods=["POST"])
def rebuild_dashboard():
    subprocess.run(
        [sys.executable, os.path.join(PROJECT_DIR, "run_pipeline.py"), "--skip-scrape"]
    )
    flash("Dashboard rebuilt from the latest incidents.")
    return redirect(url_for("list_incidents_route"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--refresh", action="store_true",
                        help="Run pipeline before starting server")
    parser.add_argument("--public", action="store_true",
                        help="Open a shareable public link via ngrok "
                             "(requires NGROK_AUTHTOKEN in .env)")
    args = parser.parse_args()

    if args.refresh:
        print("Running pipeline first...")
        subprocess.run([sys.executable, os.path.join(PROJECT_DIR, "run_pipeline.py")])

    print(f"\n  Main page: http://localhost:{args.port}")
    print(f"  Dashboard: http://localhost:{args.port}/dashboard")
    print(f"  Status:    http://localhost:{args.port}/status")
    print(f"  Weekly:    http://localhost:{args.port}/weekly")
    print(f"  Login:     {'required (SITE_USERNAME/SITE_PASSWORD)' if _auth_enabled() else 'disabled — set SITE_USERNAME/SITE_PASSWORD in .env before exposing this publicly'}")

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

