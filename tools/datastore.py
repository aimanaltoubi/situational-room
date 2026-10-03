# datastore.py
# Read / edit / query a workspace's data files, with a change log and undo.
# Every GUI edit goes through here so it is validated, logged and attributable.

import csv
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone

from tools import workspace as ws

csv.field_size_limit(10_000_000)
MAX_ROWS = 500_000
MAX_CELL = 20_000
_COL_RE = re.compile(r"^[\w\-\u0600-\u06FF ]{1,60}$")


class DataError(ValueError):
    pass


def allowed_keys(slug):
    w = ws.get_workspace(slug)
    return ws.PROFILE_FILES.get(w["analytics_profile"], ws.PROFILE_FILES["general"]) if w else []


def check_key(slug, key):
    if key not in allowed_keys(slug):
        raise DataError("Unknown data file for this workspace")


def file_path(slug, key):
    return os.path.join(ws.paths(slug)["data"], ws.DATA_FILES[key][0])


def read_table(slug, key):
    check_key(slug, key)
    path = file_path(slug, key)
    if not os.path.exists(path):
        return list(ws.SCHEMAS.get(key, [])), []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = list(reader.fieldnames or ws.SCHEMAS.get(key, []))
        rows = [{c: (r.get(c) or "") for c in cols} for r in reader]
    return cols, rows


def write_table(slug, key, cols, rows):
    if len(rows) > MAX_ROWS:
        raise DataError("Too many rows")
    path = file_path(slug, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    os.replace(tmp, path)


def _clean(cols, values):
    out = {}
    for c in cols:
        v = values.get(c, "")
        v = "" if v is None else str(v)
        if len(v) > MAX_CELL:
            raise DataError(f"Value too long in column {c}")
        out[c] = v
    return out


# ── Change log ───────────────────────────────────────────────────────────
def _log_path(slug):
    return os.path.join(ws.paths(slug)["logs"], "changes.jsonl")


def log_change(slug, user, key, op, summary, **extra):
    os.makedirs(ws.paths(slug)["logs"], exist_ok=True)
    entry = {"id": int(time.time() * 1000), "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "user": user, "file": key, "op": op, "summary": summary, **extra}
    with open(_log_path(slug), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def changes(slug, key=None, limit=200):
    path = _log_path(slug)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        items = [json.loads(l) for l in f if l.strip()]
    if key:
        items = [i for i in items if i.get("file") == key]
    return list(reversed(items))[:limit]


# ── Row operations ───────────────────────────────────────────────────────
def update_row(slug, key, i, values, user):
    cols, rows = read_table(slug, key)
    if not 0 <= i < len(rows):
        raise DataError("Row not found")
    before = dict(rows[i])
    rows[i] = _clean(cols, {**rows[i], **values})
    write_table(slug, key, cols, rows)
    changed = [c for c in cols if before.get(c) != rows[i].get(c)]
    if changed:
        log_change(slug, user, key, "update", f"تعديل السطر {i + 1}: {'، '.join(changed)}", i=i, before=before, after=rows[i])
    return rows[i]


def insert_row(slug, key, values, user, index=None):
    cols, rows = read_table(slug, key)
    row = _clean(cols, values)
    i = len(rows) if index is None else index
    rows.insert(i, row)
    write_table(slug, key, cols, rows)
    log_change(slug, user, key, "insert", f"إضافة سطر جديد ({i + 1})", i=i, after=row)
    return i


def delete_row(slug, key, i, user):
    cols, rows = read_table(slug, key)
    if not 0 <= i < len(rows):
        raise DataError("Row not found")
    before = rows.pop(i)
    write_table(slug, key, cols, rows)
    log_change(slug, user, key, "delete", f"حذف السطر {i + 1}", i=i, before=before)


def add_column(slug, key, name, user):
    name = (name or "").strip()
    if not _COL_RE.match(name):
        raise DataError("Invalid column name")
    cols, rows = read_table(slug, key)
    if name in cols:
        raise DataError("Column already exists")
    write_table(slug, key, cols + [name], rows)
    log_change(slug, user, key, "addcol", f"إضافة عمود «{name}»")


def undo_last(slug, key, user):
    """Reverse the most recent row edit of this file that has not been undone yet."""
    items = list(reversed(changes(slug, key, limit=10_000)))  # oldest -> newest
    undone = {i.get("target") for i in items if i["op"] == "undo"}
    for e in reversed(items):
        if e["op"] in ("update", "insert", "delete") and e["id"] not in undone:
            break
    else:
        raise DataError("لا توجد عمليات قابلة للتراجع")
    cols, rows = read_table(slug, key)
    i = e["i"]
    if e["op"] == "update":
        rows[i] = _clean(cols, e["before"])
    elif e["op"] == "insert":
        rows.pop(i)
    else:
        rows.insert(i, _clean(cols, e["before"]))
    write_table(slug, key, cols, rows)
    log_change(slug, user, key, "undo", f"تراجع عن: {e['summary']}", target=e["id"])
    return e["summary"]


# ── Text files ───────────────────────────────────────────────────────────
def read_text(slug, key):
    check_key(slug, key)
    p = file_path(slug, key)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def write_text(slug, key, text, user):
    check_key(slug, key)
    if len(text) > 5_000_000:
        raise DataError("Text too long")
    p = file_path(slug, key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    log_change(slug, user, key, "text", f"تعديل النص ({len(text):,} حرفاً)")


# ── Querying (editor pages and dashboard drill-down) ─────────────────────
def _nrm(v):
    return str(v).strip().lower()


def _parse_date(v):
    try:
        return datetime.fromisoformat(str(v).strip()[:10])
    except ValueError:
        return None


def _bucket(v, bucket):
    d = _parse_date(v)
    if not d:
        return ""
    if bucket == "week":
        return (d - timedelta(days=d.weekday())).date().isoformat()
    if bucket == "month":
        return d.strftime("%Y-%m-01")
    return d.date().isoformat()


def _derived(key, row, col):
    """Columns the analytics use that are computed from other columns."""
    if key == "events":
        if col == "group":
            return (row.get("actor_grouped") or row.get("actor") or "").strip() or "غير محدد"
        if col == "etype":
            return (row.get("event_type") or "").strip() or "غير محدد"
    return row.get(col, "")


def _match(key, row, f):
    if "cols" in f:
        return any(_nrm(_derived(key, row, c)) == _nrm(f["val"]) for c in f["cols"])
    v = _derived(key, row, f["col"])
    if "bucket" in f:
        return _bucket(v, f["bucket"]) == str(f["val"])
    if "contains" in f:
        return _nrm(f["contains"]) in _nrm(v)
    if "gt" in f:
        try:
            return float(v) > float(f["gt"])
        except ValueError:
            return False
    return _nrm(v) == _nrm(f["val"])


def query(slug, key, filters=None, q="", page=0, size=100, limit=None):
    cols, rows = read_table(slug, key)
    q = _nrm(q)
    out = []
    for i, r in enumerate(rows):
        if filters and not all(_match(key, r, f) for f in filters):
            continue
        if q and not any(q in _nrm(v) for v in r.values()):
            continue
        out.append({"_i": i, **r})
    total = len(out)
    if limit is not None:
        out = out[:limit]
    else:
        out = out[page * size:(page + 1) * size]
    return {"columns": cols, "total": total, "rows": out}


def annotations_for(slug, key, value):
    try:
        _, rows = read_table(slug, "annotations")
    except DataError:
        return []
    v = _nrm(value)
    return [r for r in rows if r.get("ref_file") == key and _nrm(r.get("ref_value", "")) == v]
