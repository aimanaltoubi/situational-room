# c04_telegram.py
# Telegram morning briefing feed
# Auto-extracted from Cell 4

######################################################################
# CELL 3 — Telegram Morning Briefing Feed
# Source: @iranmonitor_org
# Paginates backwards through channel to find Morning Briefings
# even when buried among Farsi posts
######################################################################

import requests, json, os, re
from datetime import datetime, timezone
from bs4 import BeautifulSoup

TELEGRAM_CACHE = os.path.join(CACHE_DIR, "ifs_telegram_cache.json")
TELEGRAM_URL   = "https://t.me/s/iranmonitor_org"
CACHE_TTL_MIN  = 30
MAX_PAGES      = 6    # ~120 posts back
MAX_BRIEFS     = 7    # keep last 7 morning briefs

def _empty_result():
    return {
        "fetched_at":   datetime.now(timezone.utc).isoformat(),
        "channel":      "iranmonitor_org",
        "channel_url":  "https://t.me/iranmonitor_org",
        "channel_name": "Iran Monitor",
        "count":        0,
        "messages":     [],
        "error":        True,
    }

def fetch_telegram_feed():
    print("[TELEGRAM] Fetching @iranmonitor_org Morning Briefings...")

    # ── Cache check ───────────────────────────────────────────────
    if os.path.exists(TELEGRAM_CACHE):
        try:
            with open(TELEGRAM_CACHE) as f:
                cached = json.load(f)
            fetched_str = cached.get("fetched_at", "2000-01-01T00:00:00")
            fetched_dt  = datetime.fromisoformat(
                fetched_str.split("+")[0].split("Z")[0]
            )
            age_min = (datetime.utcnow() - fetched_dt).total_seconds() / 60
            if age_min < CACHE_TTL_MIN:
                brief_count = len([m for m in cached.get("messages",[])
                                   if "Morning Briefing" in m.get("text","")])
                print(f"      ✓ Cache fresh ({age_min:.0f} min old, "
                      f"{brief_count} morning briefs)")
                return cached
            print(f"      Cache stale ({age_min:.0f} min) — refetching")
        except Exception as e:
            print(f"      Cache read error: {e} — refetching")

    # ── Fetch with pagination ────────────────────────────────────
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    all_briefs = []
    page_url = TELEGRAM_URL
    pages_fetched = 0

    for page_num in range(1, MAX_PAGES + 1):
        try:
            resp = requests.get(page_url, headers=headers, timeout=20)
            if resp.status_code != 200:
                print(f"      ✗ Page {page_num}: HTTP {resp.status_code}")
                break
        except Exception as e:
            print(f"      ✗ Page {page_num}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        posts = soup.select(".tgme_widget_message_wrap")
        if not posts:
            posts = soup.select(".tgme_widget_message")
        if not posts:
            break

        pages_fetched += 1
        min_id = None

        for wrap in posts:
            try:
                # Get message ID for pagination
                link_el = wrap.select_one("a.tgme_widget_message_date")
                msg_url = msg_id = ""
                if link_el:
                    msg_url = link_el.get("href", "")
                    id_match = re.search(r"/(\d+)$", msg_url)
                    if id_match:
                        msg_id = id_match.group(1)
                        mid = int(msg_id)
                        if min_id is None or mid < min_id:
                            min_id = mid

                # Get text
                text_el = wrap.select_one(".tgme_widget_message_text")
                if not text_el:
                    continue
                raw_text = text_el.get_text(separator=" ", strip=True)
                raw_text = re.sub(r"\s+", " ", raw_text).strip()

                # Only keep Morning Briefings
                if "Morning Briefing" not in raw_text and "Morning Brief" not in raw_text:
                    continue

                # Get date/time
                time_el = wrap.select_one("time")
                date_str = time_str = datetime_iso = ""
                if time_el:
                    dt_attr = time_el.get("datetime", "")
                    if dt_attr:
                        datetime_iso = dt_attr
                        try:
                            dt = datetime.fromisoformat(
                                dt_attr.replace("Z", "+00:00")
                            )
                            date_str = dt.strftime("%Y-%m-%d")
                            time_str = dt.strftime("%H:%M")
                        except Exception:
                            date_str = dt_attr[:10]
                            time_str = dt_attr[11:16]

                preview = raw_text[:150] + ("..." if len(raw_text) > 150 else "")

                all_briefs.append({
                    "id":           msg_id,
                    "date":         date_str,
                    "time":         time_str,
                    "datetime_iso": datetime_iso,
                    "text":         raw_text,
                    "preview":      preview,
                    "url":          msg_url or f"https://t.me/iranmonitor_org/{msg_id}",
                })

                print(f"      ✓ Page {page_num}: Found brief [{date_str}]")

            except Exception:
                continue

        # Stop early if we have enough briefs
        if len(all_briefs) >= MAX_BRIEFS:
            print(f"      Got {len(all_briefs)} briefs — stopping pagination")
            break

        # Next page
        if min_id:
            page_url = f"{TELEGRAM_URL}?before={min_id}"
        else:
            break

    # Sort newest first
    all_briefs.sort(
        key=lambda m: m.get("datetime_iso", ""),
        reverse=True
    )

    # Deduplicate by date
    seen_dates = set()
    unique_briefs = []
    for b in all_briefs:
        d = b.get("date", "")
        if d not in seen_dates:
            seen_dates.add(d)
            unique_briefs.append(b)
    all_briefs = unique_briefs[:MAX_BRIEFS]

    result = {
        "fetched_at":   datetime.now(timezone.utc).isoformat(),
        "channel":      "iranmonitor_org",
        "channel_url":  "https://t.me/iranmonitor_org",
        "channel_name": "Iran Monitor",
        "count":        len(all_briefs),
        "messages":     all_briefs,
        "pages_fetched": pages_fetched,
        "error":        False,
    }

    # ── Save cache ────────────────────────────────────────────────
    try:
        with open(TELEGRAM_CACHE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, separators=(",", ":"))
        print(f"      ✓ Cache saved → {TELEGRAM_CACHE}")
    except Exception as e:
        print(f"      ⚠ Cache write failed: {e}")

    print(f"\n      ✓ {len(all_briefs)} Morning Briefings found "
          f"(searched {pages_fetched} pages)")
    for b in all_briefs:
        print(f"        [{b['date']}] {b['preview'][:60]}...")
    return result


# ── Run ───────────────────────────────────────────────────────────
print("=" * 60)
print("CELL 3 — Morning Briefing (@iranmonitor_org)")
print("=" * 60)

TELEGRAM_DATA = fetch_telegram_feed()

print(f"\n[CELL 3] ✓ TELEGRAM_DATA ready")
print(f"         Briefs  : {TELEGRAM_DATA['count']}")
print(f"         Pages   : {TELEGRAM_DATA.get('pages_fetched','?')}")
print(f"         Error   : {TELEGRAM_DATA['error']}")
if TELEGRAM_DATA['count'] > 0:
    print(f"         Latest  : [{TELEGRAM_DATA['messages'][0]['date']}] "
          f"{TELEGRAM_DATA['messages'][0]['preview'][:60]}...")
print("\n         Run Cell 4 next")

######################################################################
# ► NEXT CELL: Cell 4 — WAR_DATA builder
######################################################################