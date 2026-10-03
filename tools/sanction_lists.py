# sanction_lists.py
# Import official sanctions lists into a room's sanctions-entities / sanctions-relationships files.
#   ofac -> US Treasury SDN list (CSV)
#   un   -> UN Security Council consolidated list (XML)
# Existing rows are never overwritten: entries already present (same entity_id) are skipped.

import csv
import io
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from tools import datastore as ds

URLS = {
    "ofac": "https://www.treasury.gov/ofac/downloads/sdn.csv",
    "un": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
}
MAX_BYTES = 80 * 1024 * 1024
_SDN_TYPES = {"individual": "individual", "vessel": "vessel", "aircraft": "aircraft"}


def _download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (data-analytics-system)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("downloaded file is too large")
    return data


def _clean(v):
    v = (v or "").strip()
    return "" if v in ("-0-", "-0- ") else v


def _parse_ofac(raw):
    """Returns (entities, relationships) from the headerless SDN.CSV."""
    now = datetime.now(timezone.utc).date().isoformat()
    ents, rels = [], []
    for row in csv.reader(io.StringIO(raw.decode("utf-8", errors="replace"))):
        if len(row) < 12:
            continue
        num, name, typ, prog = (_clean(row[0]), _clean(row[1]), _clean(row[2]).lower(), _clean(row[3]))
        flag, owner, remarks = _clean(row[9]), _clean(row[10]), _clean(row[11])
        if not num or not name:
            continue
        imo = (re.search(r"IMO\s+(\d{7})", remarks) or [None, ""])[1]
        mmsi = (re.search(r"MMSI\s+(\d{9})", remarks) or [None, ""])[1]
        aliases = "; ".join(re.findall(r"a\.k\.a\.\s+'([^']+)'", remarks))
        ents.append({"entity_id": f"OFAC-{num}", "name": name, "type": _SDN_TYPES.get(typ, "company"),
                     "country": flag, "program": prog, "authority": "OFAC", "designation_date": "",
                     "status": "designated", "aliases": aliases, "imo": imo, "mmsi": mmsi,
                     "source": "OFAC SDN (imported " + now + ")", "confidence": "A1"})
        if owner:
            rels.append({"source": owner, "target": name, "relation": "owns", "ownership_pct": "",
                         "evidence": "OFAC SDN vessel owner field", "confidence": "A2"})
        for linked in re.findall(r"Linked To:\s*([^;]+)", remarks):
            rels.append({"source": linked.strip().rstrip("."), "target": name, "relation": "affiliate",
                         "ownership_pct": "", "evidence": "OFAC SDN 'Linked To'", "confidence": "A2"})
    return ents, rels


def _txt(el, tag):
    n = el.find(tag)
    return (n.text or "").strip() if n is not None and n.text else ""


def _parse_un(raw):
    root = ET.fromstring(raw)
    now = datetime.now(timezone.utc).date().isoformat()
    ents = []
    for kind, tag in (("individual", "INDIVIDUAL"), ("company", "ENTITY")):
        for el in root.iter(tag):
            ref = _txt(el, "REFERENCE_NUMBER") or _txt(el, "DATAID")
            name = " ".join(p for p in (_txt(el, "FIRST_NAME"), _txt(el, "SECOND_NAME"), _txt(el, "THIRD_NAME")) if p)
            if not ref or not name:
                continue
            alias_tag = "INDIVIDUAL_ALIAS" if kind == "individual" else "ENTITY_ALIAS"
            aliases = "; ".join(a for a in (_txt(x, "ALIAS_NAME") for x in el.findall(alias_tag)) if a)
            country = ""
            for path in ("NATIONALITY/VALUE", "INDIVIDUAL_ADDRESS/COUNTRY", "ENTITY_ADDRESS/COUNTRY"):
                n = el.find(path)
                if n is not None and n.text:
                    country = n.text.strip()
                    break
            listed = _txt(el, "LISTED_ON")
            ents.append({"entity_id": f"UN-{ref}", "name": name, "type": kind, "country": country,
                         "program": _txt(el, "UN_LIST_TYPE"), "authority": "UN", "designation_date": listed[:10],
                         "status": "designated", "aliases": aliases, "imo": "", "mmsi": "",
                         "source": "UN consolidated list (imported " + now + ")", "confidence": "A1"})
    return ents, []


def import_list(slug, which, user):
    """Download and merge a list; returns the number of new entities added."""
    raw = _download(URLS[which])
    ents, rels = _parse_ofac(raw) if which == "ofac" else _parse_un(raw)
    cols, rows = ds.read_table(slug, "sanctions_entities")
    have = {r.get("entity_id") for r in rows}
    new = [{c: e.get(c, "") for c in cols} for e in ents if e["entity_id"] not in have]
    if new:
        ds.write_table(slug, "sanctions_entities", cols, rows + new)
    if rels:
        rcols, rrows = ds.read_table(slug, "sanctions_relationships")
        seen = {(r.get("source"), r.get("target"), r.get("relation")) for r in rrows}
        add = [{c: r.get(c, "") for c in rcols} for r in rels if (r["source"], r["target"], r["relation"]) not in seen]
        if add:
            ds.write_table(slug, "sanctions_relationships", rcols, rrows + add)
    return len(new)
