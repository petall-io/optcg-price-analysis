import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JUSTTCG_API_KEY")
BASE_URL = "https://api.justtcg.com/v1"
headers = {"x-api-key":API_KEY}

# Find OPTCG game id
resp = requests.get(f"{BASE_URL}/games", headers=headers, timeout=30)
resp.raise_for_status()

payload = resp.json()
games = payload.get("data",payload)

for g in games:
    print(
        f"id: {g['id']} | "
        f"name: {g['name']}"
    )

# Found id: one-piece-card-game
