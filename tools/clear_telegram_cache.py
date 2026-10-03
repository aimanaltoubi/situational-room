# clear_telegram_cache.py
# Delete Telegram cache
# Auto-extracted from Cell 3

import os, sys
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)
from tools import workspace as _ws
# Pick the workspace with: WORKSPACE=<slug> python3 tools/clear_telegram_cache.py
_p = _ws.paths(os.environ.get("WORKSPACE", _ws.DEFAULT_SLUG))
DATA_DIR, CACHE_DIR, OUTPUT_DIR, LOGS_DIR = _p["data"], _p["cache"], _p["output"], _p["logs"]

cache = os.path.join(CACHE_DIR, "ifs_telegram_cache.json")
os.remove(cache)
print("✓ Deleted")