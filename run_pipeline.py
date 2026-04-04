#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  RUN_PIPELINE.PY                                            ║
║  Middle East Conflict Situational Room                      ║
║                                                             ║
║  Runs all pipeline modules in sequence, replicating         ║
║  the Jupyter notebook execution flow.                       ║
║                                                             ║
║  Usage:                                                     ║
║    python3 run_pipeline.py              # full pipeline     ║
║    python3 run_pipeline.py --skip-scrape # skip live APIs   ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, time, argparse

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

# ── Parse args ────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Run the Situational Room pipeline")
parser.add_argument("--skip-scrape", action="store_true",
                    help="Skip flight scraper (Cell 8) — uses cached data")
args = parser.parse_args()

# ── Module execution order ────────────────────────────────────
# This matches the notebook cell execution order exactly.
# Each module runs in a SHARED namespace so globals persist
# between modules — just like in Jupyter.

modules = [
    ("config.py",                        "Configuration & API keys"),
    ("pipeline/c02_satellites.py",       "Satellite fetch + positions"),
    ("pipeline/c04_telegram.py",         "Telegram feed"),
    ("pipeline/c05_war_data.py",         "War events data"),
    ("pipeline/c07_gps_jamming.py",      "GPS jamming data"),
]

if not args.skip_scrape:
    modules.append(
        ("pipeline/c08_flight_scraper.py", "Flight data scraper (slow)")
    )

modules += [
    ("pipeline/c09_flights.py",          "Live flights + VIP jets"),
    ("pipeline/c10_marine.py",           "Marine / AIS data"),
    ("pipeline/c11_marine_enhanced.py",  "Enhanced maritime intel"),
    ("pipeline/c12_analytics.py",        "Analytics extraction"),
    ("pipeline/c14_logging.py",          "Logging"),
    ("builder/c15_html_css.py",          "HTML: CSS + head"),
    ("builder/c16_html_body.py",         "HTML: body"),
    ("builder/c17_html_js.py",           "HTML: JavaScript"),
    ("builder/c18_html_report.py",       "HTML: report + assembly"),
    ("pipeline/c19_weekly_report.py",    "Weekly report"),
    ("builder/c21_build_html.py",        "Build final HTML"),
]

# ── Shared namespace ──────────────────────────────────────────
# This dict acts as the "kernel" — all modules share it,
# so SAT_DATA defined in c02 is visible in c12, etc.
ns = {"__builtins__": __builtins__, "__name__": "__main__"}

total_start = time.time()
failed = []

for mod_path, description in modules:
    full_path = os.path.join(PROJECT_DIR, mod_path)
    if not os.path.exists(full_path):
        print(f"\n  ⚠ SKIP (file not found): {mod_path}")
        continue

    print(f"\n{'━' * 62}")
    print(f"  ▶ {description}")
    print(f"    {mod_path}")
    print(f"{'━' * 62}")

    start = time.time()
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            code = f.read()
        ns["__file__"] = full_path; ns["__file__"] = full_path; exec(compile(code, full_path, "exec"), ns)
        elapsed = time.time() - start
        print(f"  ✓ Done ({elapsed:.1f}s)")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ✗ FAILED after {elapsed:.1f}s: {e}")
        failed.append((mod_path, str(e)))
        # Continue with remaining modules — some may still work

# ── Summary ───────────────────────────────────────────────────
total = time.time() - total_start
print(f"\n{'═' * 62}")
print(f"  PIPELINE COMPLETE — {total:.0f}s total")
if failed:
    print(f"  ⚠ {len(failed)} module(s) had errors:")
    for mod, err in failed:
        print(f"    ✗ {mod}: {err}")
output = ns.get("OUTPUT_HTML", os.path.join(PROJECT_DIR, "output", "ifs_globe.html"))
if os.path.exists(output):
    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"  ✓ Output: {output} ({size_mb:.1f} MB)")
else:
    print(f"  ⚠ Output HTML not found at {output}")
print(f"{'═' * 62}")
