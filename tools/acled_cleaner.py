# acled_cleaner.py
# ACLED data cleaner
# Auto-extracted from Cell 27

import os
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
CACHE_DIR   = os.path.join(PROJECT_DIR, "cache")
OUTPUT_DIR  = os.path.join(PROJECT_DIR, "output")
LOGS_DIR    = os.path.join(PROJECT_DIR, "logs")

######################################################################
# ACLED Data Cleaner — Prepare for H2O Predictions
# 
# Input:  Middle-East_aggregated_data_up_to_week_of-2026-03-21.xlsx
# Output: ~/Downloads/Middle_East_clean_2026.csv
#
# Filters:
#   ✓ War period only (>= 2026-02-28)
#   ✓ Kinetic events only (Battles + Explosions/Remote violence)
#   ✓ Removes protests, riots, strategic developments, arrests
#   ✓ Removes Turkey (not in tracked countries)
#   ✓ Matches existing clean dataset format exactly
######################################################################

import pandas as pd

# ── Load new ACLED data ──────────────────────────────────────────
INPUT_PATH = os.path.expanduser("~/Downloads/Middle-East_aggregated_data_up_to_week_of-2026-03-21.xlsx")
OUTPUT_PATH = os.path.join(DATA_DIR, "Middle_East_clean_2026.csv")

print("=" * 60)
print("ACLED Data Cleaner — Kinetic War Events Only")
print("=" * 60)

df = pd.read_excel(INPUT_PATH)
print(f"\n[1] Raw data loaded: {len(df):,} rows | {df['WEEK'].nunique()} weeks")
print(f"    Date range: {df['WEEK'].min()} → {df['WEEK'].max()}")

# ── Filter to war period ─────────────────────────────────────────
WAR_START = pd.Timestamp("2026-02-28")
df = df[df['WEEK'] >= WAR_START].copy()
print(f"\n[2] War period (>= {WAR_START.date()}): {len(df):,} rows")
print(f"    Weeks: {sorted(df['WEEK'].dt.strftime('%Y-%m-%d').unique())}")

# ── Show what we're removing ─────────────────────────────────────
print(f"\n[3] Event types BEFORE filtering:")
for et, count in df['EVENT_TYPE'].value_counts().items():
    keep = et in ['Battles', 'Explosions/Remote violence']
    print(f"    {'✓ KEEP' if keep else '✗ DROP'}: {et} ({count:,} rows)")

# ── Filter to kinetic events only ────────────────────────────────
KINETIC_EVENT_TYPES = ['Battles', 'Explosions/Remote violence']
df = df[df['EVENT_TYPE'].isin(KINETIC_EVENT_TYPES)].copy()
print(f"\n[4] Kinetic events only: {len(df):,} rows")

# ── Show sub-event types ─────────────────────────────────────────
print(f"\n    Sub-event types kept:")
for st, count in df['SUB_EVENT_TYPE'].value_counts().items():
    print(f"      {st}: {count:,}")

# ── Remove Turkey (not in tracked countries) ─────────────────────
TRACKED_COUNTRIES = [
    'Iran', 'Iraq', 'Israel', 'Palestine', 'Lebanon', 'Syria',
    'Saudi Arabia', 'United Arab Emirates', 'Qatar', 'Bahrain',
    'Kuwait', 'Oman', 'Jordan', 'Yemen'
]
removed = df[~df['COUNTRY'].isin(TRACKED_COUNTRIES)]
if len(removed) > 0:
    print(f"\n[5] Removing non-tracked countries:")
    for c, count in removed['COUNTRY'].value_counts().items():
        print(f"      ✗ {c}: {count} rows")
df = df[df['COUNTRY'].isin(TRACKED_COUNTRIES)].copy()

# ── Format to match existing clean dataset ───────────────────────
df['WEEK'] = df['WEEK'].dt.strftime('%Y-%m-%d')

# Keep only the columns from the existing clean format
output_columns = ['WEEK', 'COUNTRY', 'ADMIN1', 'EVENT_TYPE', 'SUB_EVENT_TYPE', 
                  'EVENTS', 'ID', 'CENTROID_LATITUDE', 'CENTROID_LONGITUDE']

# Check which columns exist
missing = [c for c in output_columns if c not in df.columns]
if missing:
    print(f"\n    ⚠ Missing columns (will fill): {missing}")
    for c in missing:
        if c == 'ID':
            df['ID'] = range(1, len(df) + 1)
        else:
            df[c] = ''

df_out = df[output_columns].copy()

# ── Sort by week and country ─────────────────────────────────────
df_out = df_out.sort_values(['WEEK', 'COUNTRY', 'ADMIN1']).reset_index(drop=True)

# ── Save ─────────────────────────────────────────────────────────
df_out.to_csv(OUTPUT_PATH, index=False)

# ── Summary ──────────────────────────────────────────────────────
print(f"\n{'=' * 60}")
print(f"  OUTPUT: {OUTPUT_PATH}")
print(f"  Rows: {len(df_out):,}")
print(f"  Weeks: {sorted(df_out['WEEK'].unique())}")
print(f"  Countries: {df_out['COUNTRY'].nunique()}")
print(f"{'=' * 60}")

print(f"\n  Events per country:")
country_events = df_out.groupby('COUNTRY')['EVENTS'].sum().sort_values(ascending=False)
for country, events in country_events.items():
    print(f"    {country:<25} {events:>5} events")

print(f"\n  Events per week:")
week_events = df_out.groupby('WEEK')['EVENTS'].sum().sort_values()
for week, events in week_events.items():
    print(f"    {week}: {events:>5} events")

print(f"\n  Total kinetic events: {df_out['EVENTS'].sum():,}")

# ── Compare with old dataset ─────────────────────────────────────
old_path = os.path.join(DATA_DIR, "Middle_East_clean_2026.csv")
if os.path.exists(old_path):
    df_old = pd.read_csv(old_path)
    old_weeks = set(df_old['WEEK'].unique())
    new_weeks = set(df_out['WEEK'].unique())
    added_weeks = new_weeks - old_weeks
    print(f"\n  vs OLD dataset:")
    print(f"    Old: {len(df_old)} rows, weeks: {sorted(old_weeks)}")
    print(f"    New: {len(df_out)} rows, weeks: {sorted(new_weeks)}")
    print(f"    Added weeks: {sorted(added_weeks)}")
    
    if added_weeks:
        new_week_data = df_out[df_out['WEEK'].isin(added_weeks)]
        print(f"\n  NEW WEEK DATA (week of 2026-03-21):")
        new_country = new_week_data.groupby('COUNTRY')['EVENTS'].sum().sort_values(ascending=False)
        for country, events in new_country.items():
            print(f"    {country:<25} {events:>5} events")

print(f"\n  ✓ Ready for H2O — run Cell 5 (WAR_DATA) then Cell 19 (Report)")