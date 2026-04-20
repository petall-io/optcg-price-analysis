import os
import csv
import re
import requests
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

API_KEY = os.getenv("JUSTTCG_API_KEY")
BASE_URL = "https://api.justtcg.com/v1"
headers = {"x-api-key": API_KEY}

params = {
    "game": "one-piece-card-game",
    "orderBy": "release_date",
    "order": "asc"
}

resp = requests.get(f"{BASE_URL}/sets", headers=headers, params=params, timeout=60)
resp.raise_for_status()

payload = resp.json()
all_sets = payload.get("data", payload)

def norm(s: str) -> str:
    return (s or "").strip().lower()

EXCLUDE_SUBSTRINGS = [
    "starter deck",
    "super pre-release starter deck",
    "promotion cards",
    "pre-release cards",
    "release event cards",
    "tournament cards",
    "revision pack cards",
    "demo deck",
    "ultra deck",
    "learn together deck set",
    "collection sets",
]

INCLUDE_KEYWORDS = [
    "romance dawn",
    "paramount war",
    "pillars of strength",
    "kingdoms of intrigue",
    "awakening of the new era",
    "wings of the captain",
    "500 years in the future",
    "two legends",
    "emperors in the new world",
    "royal blood",
    "a fist of divine speed",
    "legacy of the master",
    "carrying on his will",
    "extra booster",
    "premium booster",
    "the azure sea's seven",
]

# Only include up to EB03
CUTOFF = datetime(2026, 2, 20, tzinfo=timezone.utc)

def parse_dt(dt_str: str):
    if not dt_str:
        return None
    try: 
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

def is_excluded(name: str, set_id: str) -> bool:
    text = norm(name) + " " + norm(set_id)
    return any(x in text for x in EXCLUDE_SUBSTRINGS)

def is_included(name: str) -> bool:
    text = norm(name)
    return any(k in text for k in INCLUDE_KEYWORDS)

# Normalize id to compare duplicated sets
def norm_key(name: str, set_id: str) -> str:
   t = f"{norm(name)} {norm(set_id)}"
   t = re.sub(r"\s+", " ", t)
   t = re.sub(r"-+", "-", t)
   return t.strip()

best_by_key = {}

for s in all_sets:
    sid=s.get("id")
    name = s.get("name")
    if not sid or not name:
        continue
    if is_excluded(name, sid):
        continue
    if not is_included(name):
        continue

    dt = parse_dt(s.get("release_date"))
    if dt is not None and dt > CUTOFF:
        continue

    key = norm_key(name, sid)
    existing = best_by_key.get(key)
    if existing is None:
        best_by_key[key] = s
    else: # id already exists so compare dates
        current_dt = parse_dt(s.get("release_date"))
        old_dt = parse_dt(existing.get("release_date"))

        current_has_date = current_dt is not None
        old_has_date = old_dt is not None

        if current_has_date and not old_has_date: # If the current id has a date but not the old one, then keep the current id
            best_by_key[key] = s
        elif current_has_date and old_has_date: # If both the current and old id has a date, then keep the id with the earlier date
            if current_dt < old_dt:
                best_by_key[key] = s

keep = list(best_by_key.values())
keep.sort(key=lambda x: x.get("release_date") or "9999")

print("Total sets from API:", len(all_sets))
print("Included sets:", len(keep))
for s in keep:
    print(s.get("id"), "|", s.get("name"), "|", s.get("release_date"))

with open("included_sets.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["set_id", "set_name", "release_date"])
    for s in keep:
        w.writerow([s.get("id"), s.get("name"), s.get("release_date")])
