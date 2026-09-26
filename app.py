#!/usr/bin/env python3
"""
app.py — Serve the Situational Room dashboard

Usage:
  python3 app.py                    # start on port 5000
  python3 app.py --port 8080        # custom port
  python3 app.py --refresh          # rebuild data then serve
"""

import os, sys, argparse, subprocess, hmac
from flask import Flask, send_file, jsonify, request, Response
from dotenv import load_dotenv

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")

load_dotenv(os.path.join(PROJECT_DIR, ".env"))

# Optional access gate — set SITE_USERNAME + SITE_PASSWORD in .env to require
# a login before serving anything (recommended once the app is public).
SITE_USERNAME = os.environ.get("SITE_USERNAME", "")
SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")

app = Flask(__name__)


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
    app.run(host="0.0.0.0", port=args.port, debug=False)

