# clear_gpsjam_cache.py
# Delete GPSJam cache
# Auto-extracted from Cell 6

import os
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
CACHE_DIR   = os.path.join(PROJECT_DIR, "cache")
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")
LOGS_DIR    = os.path.join(PROJECT_DIR, "logs")

os.remove(os.path.join(CACHE_DIR, "gpsjam_historical.json"))
print("✓ Deleted — will re-scrape all days")