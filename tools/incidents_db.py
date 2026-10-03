# incidents_db.py
# Simple CSV-backed store for incidents, one store per workspace.
# workspaces/<slug>/data/events.csv IS the database — there is no separate DB
# file. Every read/write goes straight to that CSV so the pipeline (which
# already loads it) always sees the latest edits.

import csv
import os

from tools import workspace as ws

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


def csv_path(slug):
    return os.path.join(ws.paths(slug)["data"], "events.csv")


def _to_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _read_rows(slug):
    path = csv_path(slug)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_rows(slug, rows):
    path = csv_path(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: r.get(c, "") for c in COLUMNS})


def list_incidents(slug):
    """Every CSV row, with its 0-based row position exposed as `id`."""
    rows = []
    for i, r in enumerate(_read_rows(slug)):
        row = dict(r)
        row["id"] = i
        for c in INT_COLUMNS:
            row[c] = _to_int(row.get(c))
        rows.append(row)
    return rows


def get_incident(slug, incident_id):
    rows = list_incidents(slug)
    if 0 <= incident_id < len(rows):
        return rows[incident_id]
    return None


def _normalize(form):
    data = {c: (form.get(c, "") or "").strip() for c in TEXT_COLUMNS}
    for c in INT_COLUMNS:
        data[c] = _to_int(form.get(c))
    return data


def add_incident(slug, form):
    rows = _read_rows(slug)
    rows.append(_normalize(form))
    _write_rows(slug, rows)


def update_incident(slug, incident_id, form):
    rows = _read_rows(slug)
    if not (0 <= incident_id < len(rows)):
        raise ValueError("Incident not found")
    rows[incident_id] = _normalize(form)
    _write_rows(slug, rows)


def delete_incident(slug, incident_id):
    rows = _read_rows(slug)
    if not (0 <= incident_id < len(rows)):
        raise ValueError("Incident not found")
    rows.pop(incident_id)
    _write_rows(slug, rows)

