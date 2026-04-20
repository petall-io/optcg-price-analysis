import os
import requests
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

API_KEY = os.getenv("JUSTTCG_API_KEY")
BASE_URL = "https://api.justtcg.com/v1"
headers = {"x-api-key": API_KEY}

# Query parameters per api documentation
params = {
    "game": "one-piece-card-game",
    "orderBy": "release_date",
    "order": "asc"
}

resp = requests.get(f"{BASE_URL}/sets", headers=headers, params=params, timeout=60)
print("Status:", resp.status_code)
resp.raise_for_status()

payload = resp.json()
sets = payload.get("data", payload)

print("Total sets:", len(sets))
for s in sets:
    print(s.get("id"), "|", s.get("name"), "|", s.get("release_date"))