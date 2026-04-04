#!/usr/bin/env python3
"""
verify_setup.py — Pre-launch verification
Checks that all files, keys, and dependencies are in place.
"""

import os, sys, importlib

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

passed = 0
warned = 0
failed = 0

def ok(msg):
    global passed
    passed += 1
    print(f"  ✓ {msg}")

def warn(msg):
    global warned
    warned += 1
    print(f"  ⚠ {msg}")

def fail(msg):
    global failed
    failed += 1
    print(f"  ✗ {msg}")

print("=" * 60)
print("  VERIFY SETUP — Pre-launch checks")
print("=" * 60)

# ── 1. Check .env exists ──────────────────────────────────────
print("\n── API Keys ──")
if os.path.exists(".env"):
    ok(".env file exists")
    from dotenv import load_dotenv
    load_dotenv()
else:
    fail(".env not found — run: cp .env.example .env")

keys = {
    "ANTHROPIC_API_KEY": ("Required", "Claude report generation"),
    "CESIUM_TOKEN":      ("Required", "3D globe rendering"),
    "ADSBX_KEY":         ("Required", "ADS-B flights + jamming"),
    "DATALASTIC_KEY":    ("Required", "Marine vessel tracking"),
}
for key, (level, purpose) in keys.items():
    val = os.environ.get(key, "")
    if val:
        ok(f"{key}: set ({len(val)} chars) — {purpose}")
    else:
        fail(f"{key}: NOT SET — needed for {purpose}")

# ── 2. Check data files ───────────────────────────────────────
print("\n── Data Files ──")
data_files = {
    "iran_war_clean.csv":       "Required — war event timeline",
    "political-events.csv":     "Required — political trajectory",
    "vessels-attack-dataset.txt":"Optional — attacked vessels",
    "Middle_East_clean_2026.csv":"Optional — ACLED predictions",
    "analytical-dataset.txt":   "Optional — analytical briefing",
}
for fname, desc in data_files.items():
    path = os.path.join("data", fname)
    if os.path.exists(path):
        size = os.path.getsize(path)
        ok(f"{fname} ({size:,} bytes) — {desc}")
    elif "Required" in desc:
        fail(f"{fname} MISSING — {desc}")
    else:
        warn(f"{fname} missing — {desc}")

# ── 3. Check Python dependencies ──────────────────────────────
print("\n── Python Packages ──")
packages = {
    "requests": "requests",
    "pandas": "pandas",
    "numpy": "numpy",
    "skyfield": "skyfield",
    "bs4": "beautifulsoup4",
    "websockets": "websockets",
    "flask": "flask",
    "dotenv": "python-dotenv",
    "scipy": "scipy",
}
for imp_name, pip_name in packages.items():
    try:
        importlib.import_module(imp_name)
        ok(f"{pip_name}")
    except ImportError:
        fail(f"{pip_name} — run: pip install {pip_name}")

# H2O + Java
try:
    import h2o
    ok("h2o")
except ImportError:
    warn("h2o not installed — weekly predictions will be skipped")

import subprocess
java_check = subprocess.run(["java", "-version"], capture_output=True, text=True)
if java_check.returncode == 0:
    ok("Java runtime found")
else:
    warn("Java not found — needed for H2O ML predictions")

# ── 4. Check pipeline files ───────────────────────────────────
print("\n── Pipeline Files ──")
pipeline_files = [
    "config.py",
    "run_pipeline.py",
    "app.py",
    "pipeline/c02_satellites.py",
    "pipeline/c04_telegram.py",
    "pipeline/c05_war_data.py",
    "pipeline/c07_gps_jamming.py",
    "pipeline/c09_flights.py",
    "pipeline/c10_marine.py",
    "pipeline/c11_marine_enhanced.py",
    "pipeline/c12_analytics.py",
    "builder/c15_html_css.py",
    "builder/c16_html_body.py",
    "builder/c17_html_js.py",
    "builder/c18_html_report.py",
    "builder/c21_build_html.py",
]
for f in pipeline_files:
    if os.path.exists(f):
        ok(f)
    else:
        fail(f"{f} MISSING")

# ── Summary ───────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"  Results: {passed} passed, {warned} warnings, {failed} failed")
if failed == 0:
    print("  ✓ Ready to run:  python3 run_pipeline.py")
else:
    print("  ✗ Fix the failures above before running the pipeline")
print(f"{'=' * 60}")

sys.exit(0 if failed == 0 else 1)
