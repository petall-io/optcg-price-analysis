import os
import csv
import json
import time
import math
import random
import requests
from pathlib import Path
from dotenv import load_dotenv

""" Data Collected February 4 & 15, 2026 """

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

API_KEY = os.getenv("JUSTTCG_API_KEY")
BASE_URL = "https://api.justtcg.com/v1"
GAME_ID = "one-piece-card-game"

# Justtcg "Free Tier" plan limits
REQS_PER_MIN = 10
MIN_INTERVAL = 60.0 / REQS_PER_MIN  # 6.0 sec
SAFETY = 1.0
MIN_SECONDS_PER_REQUEST = MIN_INTERVAL + SAFETY  

# Cards per request limit
LIMIT = 20

# Output + state files
OUT_FILE = Path("raw_cards_one_piece_08.jsonl")
DONE_FILE = Path("done_sets.txt")
CHECKPOINT_FILE = Path("checkpoint_offsets.json")
STATS_FILE = Path("run_stats.json")  # tracks request counts across runs

HEADERS = {"x-api-key": API_KEY}

INCLUDE_STATISTICS = True

_last_request_ts = 0.0


def pace_request():
    """Ensures we do not exceed 10 requests/min. Call before each API request."""
    global _last_request_ts
    now = time.time()
    elapsed = now - _last_request_ts
    wait = MIN_SECONDS_PER_REQUEST - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_request_ts = time.time()

def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json_atomic(path: Path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

def load_done_sets() -> set:
    if not DONE_FILE.exists():
        return set()
    return set(x.strip() for x in DONE_FILE.read_text(encoding="utf-8").splitlines() if x.strip())

def mark_set_done(set_id: str):
    with DONE_FILE.open("a", encoding="utf-8") as f:
        f.write(set_id + "\n")

def load_checkpoints() -> dict:
    return load_json(CHECKPOINT_FILE, {})

def save_checkpoints(cp: dict):
    save_json_atomic(CHECKPOINT_FILE, cp)

def clear_checkpoint_for_set(cp: dict, set_id: str):
    if set_id in cp:
        del cp[set_id]
        save_checkpoints(cp)

def load_run_stats() -> dict:
    return load_json(STATS_FILE, {
        "total_requests": 0,
        "total_429": 0,
        "total_errors": 0,
        "last_run_unix": None,
    })

def save_run_stats(stats: dict):
    stats["last_run_unix"] = int(time.time())
    save_json_atomic(STATS_FILE, stats)


def request_with_retry(url, params, stats: dict, timeout=60, max_tries=20):
    """
    - Paces requests to your plan limit
    - Retries on 429 with smart backoff
    - Saves stats immediately (attempted vs success)
    """
    global _last_request_ts

    for attempt in range(1, max_tries + 1):
        pace_request()

        resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)

        stats["total_requests"] = stats.get("total_requests", 0) + 1

        if resp.status_code == 429:
            stats["total_429"] = stats.get("total_429", 0) + 1

            retry_after = resp.headers.get("Retry-After")
            rl_rem = resp.headers.get("X-RateLimit-Remaining")
            rl_reset = resp.headers.get("X-RateLimit-Reset")

            if retry_after and retry_after.isdigit():
                wait = int(retry_after)
            else:
                wait = min(600, 2 ** attempt)

            wait += random.randint(0, 3)

            save_run_stats(stats)

            print(f"[429] attempt {attempt}/{max_tries} | sleeping {wait}s"
                  f" | remaining={rl_rem} reset={rl_reset}")

            time.sleep(wait)

            _last_request_ts = time.time()
            continue

        if resp.status_code >= 400:
            stats["total_errors"] = stats.get("total_errors", 0) + 1
            save_run_stats(stats)

            print("ERROR STATUS:", resp.status_code)
            print("ERROR URL:", resp.url)
            print("ERROR BODY:", resp.text[:2000])
            resp.raise_for_status()

        stats["total_success"] = stats.get("total_success", 0) + 1
        save_run_stats(stats)
        return resp.json()

    raise RuntimeError(f"Too many 429s. Gave up after {max_tries} tries. Params={params}")

def read_sets_csv(path="included_sets.csv"):
    sets = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sets.append(row)
    return sets

def fetch_cards_for_set(set_id: str, start_offset: int, stats: dict):
    """
    Yields (page_data_list, pagination_dict, offset_used)
    so main() can update checkpoints after each page.
    """
    url = f"{BASE_URL}/cards"
    offset = start_offset
    page = 0

    while True:
        params = {
            "game": GAME_ID,
            "set": set_id,
            "limit": LIMIT,
            "offset": offset,
            "include_price_history": "true",
            "priceHistoryDuration": "180d",
        }

        if INCLUDE_STATISTICS:
            params["include_statistics"] = "allTime"

        payload = request_with_retry(url, params=params, stats=stats)
        data = payload.get("data", payload)

        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected payload shape for set={set_id}. data_type={type(data)} keys={list(payload)[:25]}")

        pagination = payload.get("pagination") or {}

        page += 1
        got = len(data)

        total_count = (
            pagination.get("total")
            or pagination.get("totalCount")
            or pagination.get("count")
        )
        if isinstance(total_count, int) and total_count > 0:
            total_pages = math.ceil(total_count / LIMIT)
            cur_page = (offset // LIMIT) + 1
            print(f"    page {cur_page}/{total_pages} | offset={offset} | got={got}")
        else:
            print(f"    page {page} | offset={offset} | got={got}")

        yield data, pagination, offset

        has_more = pagination.get("hasMore")
        if has_more is None:
            has_more = (got == LIMIT)

        if not has_more or got == 0:
            break

        offset += LIMIT
    
def fetch_set_release_dates(stats: dict) -> dict:
    """Returns {set_id: release_date_string} for the game."""
    url = f"{BASE_URL}/sets"
    params = {
        "game": GAME_ID,
        "orderBy": "release_date",
        "order": "asc",
    }
    payload = request_with_retry(url, params=params, stats=stats)
    data = payload.get("data", payload)

    return {s["id"]: s.get("release_date") for s in data if "id" in s}

def main():
    if not API_KEY:
        raise RuntimeError("JUSTTCG_API_KEY missing. Check your .env file.")

    start_ts = time.time()
    total_pages = 0
    total_cards_written = 0

    sets = read_sets_csv("included_sets.csv")
    done_sets = load_done_sets()
    checkpoints = load_checkpoints()
    stats = load_run_stats()
    set_release_map = fetch_set_release_dates(stats)

    print(f"Plan pacing: ~1 request every {MIN_SECONDS_PER_REQUEST:.1f}s (<= {REQS_PER_MIN}/min)")
    print(f"Stats so far: requests={stats['total_requests']} | 429s={stats['total_429']} | errors={stats['total_errors']}")
    print("----")

    with OUT_FILE.open("a", encoding="utf-8") as out:
        for i, s in enumerate(sets, start=1):
            set_id = s["set_id"]
            set_name = s["set_name"]

            if set_id in done_sets:
                print(f"[{i}/{len(sets)}] Skipping {set_name} (already done)")
                continue

            # Resume offset if we have it
            start_offset = int(checkpoints.get(set_id, {}).get("next_offset", 0))
            prev_written = int(checkpoints.get(set_id, {}).get("cards_written", 0))
            if start_offset > 0:
                print(f"[{i}/{len(sets)}] Resuming {set_name} at offset={start_offset} (prev wrote ~{prev_written})")
            else:
                print(f"[{i}/{len(sets)}] Fetching cards for set: {set_name} ({set_id})")

            wrote_this_set = 0

            for batch, pagination, offset_used in fetch_cards_for_set(set_id, start_offset=start_offset, stats=stats):
                total_pages += 1

                for card in batch:
                    record = {
                        "game": GAME_ID,
                        "set_id": set_id,
                        "set_name": set_name,
                        "set_release_date": set_release_map.get(set_id),
                        "card": card,
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    wrote_this_set += 1
                    total_cards_written += 1

                out.flush()

                next_offset = offset_used + LIMIT
                cp_entry = checkpoints.get(set_id, {"next_offset": 0, "pages_done": 0, "cards_written": 0})
                cp_entry["next_offset"] = next_offset
                cp_entry["pages_done"] = int(cp_entry.get("pages_done", 0)) + 1
                cp_entry["cards_written"] = int(cp_entry.get("cards_written", 0)) + len(batch)
                checkpoints[set_id] = cp_entry
                save_checkpoints(checkpoints)
                save_run_stats(stats)

                remaining_monthly = 1000 - stats["total_requests"]
                elapsed = time.time() - start_ts
                pages_per_min = (total_pages / elapsed) * 60 if elapsed > 0 else 0

                print(
                    f"    totals: {total_cards_written} cards | {total_pages} pages | "
                    f"{pages_per_min:.2f} pages/min | requests_used={stats['total_requests']} | remaining(approx)={remaining_monthly}"
                )
                
            print(f"  -> wrote {wrote_this_set} cards for {set_name}")
            mark_set_done(set_id)
            clear_checkpoint_for_set(checkpoints, set_id)
            save_run_stats(stats)

    print("All sets completed.")


if __name__ == "__main__":
    main()

