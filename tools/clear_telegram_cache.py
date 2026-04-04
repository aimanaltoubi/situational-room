# clear_telegram_cache.py
# Delete Telegram cache
# Auto-extracted from Cell 3

import os
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
CACHE_DIR   = os.path.join(PROJECT_DIR, "cache")
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")
LOGS_DIR    = os.path.join(PROJECT_DIR, "logs")

cache = os.path.join(CACHE_DIR, "ifs_telegram_cache.json")
os.remove(cache)
print("✓ Deleted")