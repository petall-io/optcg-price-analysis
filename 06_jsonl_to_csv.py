import json
import csv
from datetime import datetime, timezone
from pathlib import Path

INPUT_FILE = Path("raw_cards_one_piece_08.jsonl")
VARIANTS_OUT = Path("card_variants_08.csv")
HISTORY_OUT = Path("price_history_08.csv")

def ts_to_iso(ts):
    """Convert unix seconds -> ISO string (UTC)."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None

def history_ts_to_date(ts):
    """Convert unix seconds -> YYYY-MM-DD (UTC)."""
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except Exception:
        return None

variant_rows = []
history_rows = []

with INPUT_FILE.open(encoding="utf-8") as f:
    for line_num, line in enumerate(f, start=1):
        line = line.strip()
        if not line:
            continue

        rec = json.loads(line)

        card = rec.get("card", {})
        set_id = rec.get("set_id")
        set_name = rec.get("set_name")
        game_id = rec.get("game")
        set_release_date = rec.get("set_release_date")

        card_id = card.get("id")
        card_name = card.get("name")
        card_number = card.get("number")
        rarity = card.get("rarity")
        tcgplayer_id = card.get("tcgplayerId")

        variants = card.get("variants") or []
        for v in variants:
            variant_id = v.get("id")
            condition = v.get("condition")
            printing = v.get("printing")
            language = v.get("language")
            sku = v.get("tcgplayerSkuId")

            price = v.get("price")
            last_updated = ts_to_iso(v.get("lastUpdated"))
            price_change_24hr = v.get("priceChange24hr")

            min_price = v.get("minPriceAllTime")
            min_price_date = v.get("minPriceAllTimeDate")
            max_price = v.get("maxPriceAllTime")
            max_price_date = v.get("maxPriceAllTimeDate")

            variant_rows.append({
                "game": game_id,
                "set_id": set_id,
                "set_name": set_name,
                "card_id": card_id,
                "card_name": card_name,
                "card_number": card_number,
                "rarity": rarity,
                "tcgplayer_id": tcgplayer_id,
                "variant_id": variant_id,
                "condition": condition,
                "printing": printing,
                "language": language,
                "tcgplayer_sku_id": sku,
                "current_price": price,
                "price_change_24hr": price_change_24hr,
                "last_updated_utc": last_updated,
                "min_price": min_price,
                "min_price_date": min_price_date,
                "max_price": max_price,
                "max_price_date": max_price_date,
                "set_release_date": set_release_date,
            })

            for p in (v.get("priceHistory") or []):
                history_rows.append({
                    "game": game_id,
                    "set_id": set_id,
                    "set_name": set_name,
                    "card_id": card_id,
                    "card_name": card_name,
                    "card_number": card_number,
                    "rarity": rarity,
                    "variant_id": variant_id,
                    "condition": condition,
                    "printing": printing,
                    "language": language,
                    "date": history_ts_to_date(p.get("t")),
                    "timestamp_utc": ts_to_iso(p.get("t")),
                    "price": p.get("p"),
                })

# Write variants CSV
if not variant_rows:
    raise RuntimeError("No variant rows produced. Check INPUT_FILE path and JSONL contents.")

with VARIANTS_OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(variant_rows[0].keys()))
    writer.writeheader()
    writer.writerows(variant_rows)

# Write history CSV
if history_rows:
    with HISTORY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(history_rows[0].keys()))
        writer.writeheader()
        writer.writerows(history_rows)
else:
    headers = [
        "game","set_id","set_name","card_id","card_name","card_number","rarity",
        "variant_id","condition","printing","language","date","timestamp_utc","price"
    ]
    with HISTORY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

print(f"Wrote {len(variant_rows):,} rows -> {VARIANTS_OUT}")
print(f"Wrote {len(history_rows):,} rows -> {HISTORY_OUT}")

