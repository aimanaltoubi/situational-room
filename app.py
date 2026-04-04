#!/usr/bin/env python3
"""
app.py — Serve the Situational Room dashboard

Usage:
  python3 app.py                    # start on port 5000
  python3 app.py --port 8080        # custom port
  python3 app.py --refresh          # rebuild data then serve
"""

import os, sys, argparse, subprocess
from flask import Flask, send_file, jsonify

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")

app = Flask(__name__)

@app.route("/")
def index():
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
    args = parser.parse_args()

    if args.refresh:
        print("Running pipeline first...")
        subprocess.run([sys.executable, os.path.join(PROJECT_DIR, "run_pipeline.py")])

    print(f"\n  Dashboard: http://localhost:{args.port}")
    print(f"  Status:    http://localhost:{args.port}/status")
    print(f"  Weekly:    http://localhost:{args.port}/weekly\n")
    app.run(host="0.0.0.0", port=args.port, debug=False)
