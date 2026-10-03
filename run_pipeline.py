#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  RUN_PIPELINE.PY                                            ║
║  International Data Analytics System                        ║
║                                                             ║
║  Runs all pipeline modules in sequence, replicating         ║
║  the Jupyter notebook execution flow.                       ║
║                                                             ║
║  Usage:                                                     ║
║    python3 run_pipeline.py              # full pipeline     ║
║    python3 run_pipeline.py --skip-scrape # skip live APIs   ║
║    python3 run_pipeline.py -w terrorism # pick a workspace  ║
╚══════════════════════════════════════════════════════════════╝
"""

import os, sys, time, argparse

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

# ── Parse args ────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Run the Situational Room pipeline")
parser.add_argument("--skip-scrape", action="store_true",
                    help="Skip flight scraper (Cell 8) — uses cached data")
parser.add_argument("-w", "--workspace", default=None,
                    help="Workspace slug under workspaces/ (default: middle-east-conflict)")
args = parser.parse_args()
if args.workspace:
    os.environ["WORKSPACE"] = args.workspace


class ModuleSkipped(Exception):
    """Raised by a module that has nothing to do for this workspace."""

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
    ("pipeline/c20_data_quality.py",     "Data quality report"),
    ("builder/c21_build_html.py",        "Build final HTML"),
]

# ── Per-room monitoring modules ───────────────────────────────────────
# Modules that only make sense for some subjects are skipped when the
# workspace switches that feature off (workspace.json -> "features").
sys.path.insert(0, PROJECT_DIR)
from tools import workspace as _wsmod
_room = _wsmod.get_workspace(os.environ.get("WORKSPACE", _wsmod.DEFAULT_SLUG))
if _room is None:
    raise SystemExit(f"Unknown workspace '{os.environ.get('WORKSPACE')}' — see workspaces/")
_features = _room["features"]
_module_feature = {
    "pipeline/c02_satellites.py":      "satellites",
    "pipeline/c07_gps_jamming.py":     "gps_jamming",
    "pipeline/c08_flight_scraper.py":  "flights",
    "pipeline/c10_marine.py":          "marine",
    "pipeline/c11_marine_enhanced.py": "marine",
}
modules = [(p, d) for p, d in modules if _features.get(_module_feature.get(p, ""), True)]

# Empty stand-ins for the data a disabled module would have produced.
_EMPTY_DEFAULTS = {
    "satellites": '''
SAT_DATA = {"count": 0, "satellites": [], "cats": {}, "fetched_at": datetime.now(timezone.utc).isoformat()}
HIST_SAT_DATA = {"war_start": WAR_START_STR, "days": [], "sat_count": 0}
''',
    "gps_jamming": '''
JAM_DATA = {"zones": []}
GPSJAM_DATA = {"cells": [], "history": [], "me_avg": 0, "me_max": 0, "source": "disabled"}
''',
    "marine": '''
MARINE_DATA = {"vessels": [], "total": 0, "counts": {}, "zones": [], "hormuz_vessels": [],
               "moving_tankers": [], "stopped_tankers": [], "source": "disabled"}
''',
}

# ── Shared namespace ──────────────────────────────────────────
# This dict acts as the "kernel" — all modules share it,
# so SAT_DATA defined in c02 is visible in c12, etc.
ns = {"__builtins__": __builtins__, "__name__": "__main__", "ModuleSkipped": ModuleSkipped}

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
        if mod_path == "config.py":
            from datetime import datetime, timezone
            ns.update(datetime=datetime, timezone=timezone)
            for _feat, _src in _EMPTY_DEFAULTS.items():
                if not _features[_feat]:
                    exec(_src, ns)
                    print(f"  ↷ '{_feat}' is off for this workspace — using empty data")
        elapsed = time.time() - start
        print(f"  ✓ Done ({elapsed:.1f}s)")
    except ModuleSkipped as e:
        print(f"  ↷ Skipped: {e}")
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
output = ns.get("OUTPUT_HTML")
if output and os.path.exists(output):
    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"  ✓ Output: {output} ({size_mb:.1f} MB)")
else:
    print(f"  ⚠ Output HTML not found at {output}")
print(f"{'═' * 62}")
