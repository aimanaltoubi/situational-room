# incidents_db.py
# Simple CSV-backed store for war incidents.
# data/iran_war_clean.csv IS the database — there is no separate DB file.
# Every read/write goes straight to that CSV so the pipeline (which already
# loads it) always sees the latest edits.

import csv
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(PROJECT_DIR, "data")
CSV_PATH    = os.path.join(DATA_DIR, "iran_war_clean.csv")

TEXT_COLUMNS = [
    "date", "datetime", "time_source", "country", "location",
    "event_type", "actor", "actor_grouped", "target", "description",
    "has_casualties",
]
INT_COLUMNS = ["day_of_war", "killed", "injured", "total_casualties"]
COLUMNS = [
    "date", "datetime", "time_source", "day_of_war", "country", "location",
    "event_type", "actor", "actor_grouped", "target", "killed", "injured",
    "description", "total_casualties", "has_casualties",
]


def _to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _read_rows():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_rows(rows):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in COLUMNS})


def list_incidents():
    """Every CSV row, with its 0-based row position exposed as `id`."""
    rows = []
    for i, r in enumerate(_read_rows()):
        row = dict(r)
        row["id"] = i
        for c in INT_COLUMNS:
            row[c] = _to_int(row.get(c))
        rows.append(row)
    return rows


def get_incident(incident_id):
    rows = list_incidents()
    if 0 <= incident_id < len(rows):
        return rows[incident_id]
    return None


def _normalize(form):
    data = {c: (form.get(c, "") or "").strip() for c in TEXT_COLUMNS}
    for c in INT_COLUMNS:
        data[c] = _to_int(form.get(c))
    return data


def add_incident(form):
    rows = _read_rows()
    rows.append(_normalize(form))
    _write_rows(rows)


def update_incident(incident_id, form):
    rows = _read_rows()
    if not (0 <= incident_id < len(rows)):
        raise ValueError("Incident not found")
    rows[incident_id] = _normalize(form)
    _write_rows(rows)


def delete_incident(incident_id):
    rows = _read_rows()
    if not (0 <= incident_id < len(rows)):
        raise ValueError("Incident not found")
    rows.pop(incident_id)
    _write_rows(rows)

