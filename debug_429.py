import os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")
API_KEY = os.getenv("JUSTTCG_API_KEY")

BASE_URL = "https://api.justtcg.com/v1"
HEADERS = {"x-api-key": API_KEY}

r = requests.get(f"{BASE_URL}/games", headers=HEADERS, timeout=30)
print("Status:", r.status_code)
print("Headers:", {k:v for k,v in r.headers.items() if "rate" in k.lower() or "retry" in k.lower()})
print("Body:", r.text[:300])
