# workspace.py
# Registry for situational-room workspaces.
# Each folder under workspaces/<slug>/ with a workspace.json is one workspace
# (its own data/, cache/, logs/, output/ and its own analytics report).

import json
import os
import re
from datetime import date

PROJECT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACES_DIR = os.path.join(PROJECT_DIR, "workspaces")
DEFAULT_SLUG   = "middle-east-conflict"
SUBDIRS        = ("data", "cache", "logs", "output")
SLUG_RE        = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")

SYSTEM_NAME_AR = "نظام تحليل البيانات الدولية"
SYSTEM_NAME_EN = "International Data Analytics System"


def is_valid_slug(slug):
    return bool(slug and SLUG_RE.match(slug))


def workspace_dir(slug):
    if not is_valid_slug(slug):
        raise ValueError(f"Invalid workspace slug: {slug!r}")
    return os.path.join(WORKSPACES_DIR, slug)


def paths(slug):
    base = workspace_dir(slug)
    return {name: os.path.join(base, name) for name in SUBDIRS}


def get_workspace(slug):
    """Manifest dict for a workspace, or None if it does not exist."""
    if not is_valid_slug(slug):
        return None
    manifest = os.path.join(workspace_dir(slug), "workspace.json")
    if not os.path.exists(manifest):
        return None
    with open(manifest, encoding="utf-8") as f:
        ws = json.load(f)
    ws["slug"] = slug
    ws.setdefault("name_en", slug)
    ws.setdefault("name_ar", slug)
    ws.setdefault("start_date", date.today().isoformat())
    ws.setdefault("telegram_channel", "")
    ws["analytics_name_ar"] = "تحليلات " + ws["name_ar"]
    ws["analytics_name_en"] = ws["name_en"] + " Analytics"
    return ws


def list_workspaces():
    if not os.path.isdir(WORKSPACES_DIR):
        return []
    found = [get_workspace(s) for s in sorted(os.listdir(WORKSPACES_DIR))]
    return [w for w in found if w]


def create_workspace(slug, name_ar, name_en, start_date=None, telegram_channel=""):
    """Create an empty workspace with the standard folder layout."""
    if not is_valid_slug(slug):
        raise ValueError("Slug must be 2-41 chars: lowercase letters, digits, hyphens")
    if not (name_ar or "").strip() or not (name_en or "").strip():
        raise ValueError("Arabic and English names are required")
    base = workspace_dir(slug)
    if os.path.exists(os.path.join(base, "workspace.json")):
        raise ValueError(f"Workspace '{slug}' already exists")
    start = start_date or date.today().isoformat()
    date.fromisoformat(start)  # validates format
    for sub in SUBDIRS:
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    manifest = {
        "name_ar": name_ar.strip(),
        "name_en": name_en.strip(),
        "start_date": start,
        "telegram_channel": (telegram_channel or "").strip().lstrip("@"),
    }
    with open(os.path.join(base, "workspace.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return get_workspace(slug)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Manage workspaces")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create", help="Create an empty workspace")
    c.add_argument("slug")
    c.add_argument("--name-ar", required=True)
    c.add_argument("--name-en", required=True)
    c.add_argument("--start-date", default=None, help="YYYY-MM-DD (default: today)")
    c.add_argument("--telegram-channel", default="")
    sub.add_parser("list", help="List workspaces")
    a = p.parse_args()
    if a.cmd == "create":
        w = create_workspace(a.slug, a.name_ar, a.name_en, a.start_date, a.telegram_channel)
        print(f"Created workspaces/{w['slug']}  ({w['name_ar']})")
    else:
        for w in list_workspaces():
            print(f"{w['slug']:30s} {w['name_ar']}")
